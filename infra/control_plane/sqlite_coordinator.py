"""Durable, single-host SQLite task coordinator with fenced execution lifecycle.

SQLite WAL coordinates processes on one host only. Use a local persistent
filesystem, not shared NFS. Every lease mutation is fenced by a monotonic token.
"""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional

from .lifecycle import IdempotencyConflict, Lease


@dataclass(frozen=True)
class TaskSnapshot:
    task_id: str
    idempotency_key: str
    input_digest: str
    state: str
    owner: Optional[str]
    fencing_token: int
    lease_expires_at: Optional[float]
    result: Optional[str]
    failure_class: Optional[str]
    provider_id: Optional[str]
    external_run_id: Optional[str]
    heartbeat_at: Optional[float]


class SQLiteCoordinator:
    """Persistent, transactional task intake, dispatch, lease and result ledger."""

    SCHEMA_VERSION = 2
    _STATES = "'queued','leased','recoverable','submitted','running','succeeded','failed','cancelled'"

    def __init__(self, database_path: str | Path, *, busy_timeout_ms: int = 5000) -> None:
        self.database_path = str(database_path)
        if self.database_path == ":memory:":
            raise ValueError("a persistent database path is required")
        if busy_timeout_ms < 1:
            raise ValueError("busy_timeout_ms must be positive")
        self.busy_timeout_ms = busy_timeout_ms
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=self.busy_timeout_ms / 1000,
            isolation_level=None,
        )
        connection.row_factory = sqlite3.Row
        connection.execute(f"PRAGMA busy_timeout={self.busy_timeout_ms}")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    @classmethod
    def _create_tasks_table(cls, connection: sqlite3.Connection, table: str = "tasks") -> None:
        if table not in {"tasks", "tasks_v2"}:
            raise ValueError("invalid internal table name")
        connection.execute(
            f"""
            CREATE TABLE {table} (
                task_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                input_digest TEXT NOT NULL,
                state TEXT NOT NULL CHECK (state IN ({cls._STATES})),
                owner TEXT,
                fencing_token INTEGER NOT NULL DEFAULT 0 CHECK (fencing_token >= 0),
                lease_expires_at REAL,
                result TEXT,
                failure_class TEXT,
                provider_id TEXT,
                external_run_id TEXT,
                heartbeat_at REAL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                CHECK (
                    (state = 'leased' AND owner IS NOT NULL AND lease_expires_at IS NOT NULL)
                    OR
                    (state <> 'leased' AND owner IS NULL AND lease_expires_at IS NULL)
                ),
                CHECK (
                    (provider_id IS NULL AND external_run_id IS NULL)
                    OR
                    (provider_id IS NOT NULL AND external_run_id IS NOT NULL)
                )
            )
            """
        )

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, self.SCHEMA_VERSION):
                raise RuntimeError("unsupported coordinator database schema version")
            connection.execute("BEGIN IMMEDIATE")
            try:
                if version == 0:
                    self._create_tasks_table(connection)
                elif version == 1:
                    # Rebuild because SQLite cannot widen the v1 CHECK constraint.
                    connection.execute("DROP INDEX IF EXISTS tasks_state_expiry")
                    connection.execute("ALTER TABLE tasks RENAME TO tasks_v1")
                    self._create_tasks_table(connection)
                    connection.execute(
                        """
                        INSERT INTO tasks (
                            task_id,idempotency_key,input_digest,state,owner,fencing_token,
                            lease_expires_at,result,failure_class,created_at,updated_at
                        )
                        SELECT task_id,idempotency_key,input_digest,state,owner,fencing_token,
                               lease_expires_at,result,failure_class,created_at,updated_at
                        FROM tasks_v1
                        """
                    )
                    connection.execute("DROP TABLE tasks_v1")
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS tasks_state_expiry ON tasks(state, lease_expires_at)"
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS tasks_provider_run ON tasks(provider_id, external_run_id)"
                )
                connection.execute(f"PRAGMA user_version={self.SCHEMA_VERSION}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _snapshot(row: sqlite3.Row) -> TaskSnapshot:
        return TaskSnapshot(
            task_id=row["task_id"],
            idempotency_key=row["idempotency_key"],
            input_digest=row["input_digest"],
            state=row["state"],
            owner=row["owner"],
            fencing_token=row["fencing_token"],
            lease_expires_at=row["lease_expires_at"],
            result=row["result"],
            failure_class=row["failure_class"],
            provider_id=row["provider_id"],
            external_run_id=row["external_run_id"],
            heartbeat_at=row["heartbeat_at"],
        )

    def enqueue(self, *, task_id: str, idempotency_key: str, input_digest: str) -> TaskSnapshot:
        if not task_id or not idempotency_key or not input_digest:
            raise ValueError("task identity fields are required")
        now = time.time()
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM tasks WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if row is not None:
                    if row["input_digest"] != input_digest:
                        raise IdempotencyConflict("idempotency key/input mismatch")
                    connection.commit()
                    return self._snapshot(row)
                row = connection.execute(
                    "SELECT * FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone()
                if row is not None:
                    raise IdempotencyConflict("task id reused for different identity")
                connection.execute(
                    """
                    INSERT INTO tasks (
                        task_id,idempotency_key,input_digest,state,created_at,updated_at
                    ) VALUES (?,?,?,'queued',?,?)
                    """,
                    (task_id, idempotency_key, input_digest, now, now),
                )
                row = connection.execute(
                    "SELECT * FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone()
                connection.commit()
                return self._snapshot(row)
            except Exception:
                connection.rollback()
                raise

    def claim(
        self, *, task_id: str, owner: str, lease_seconds: int = 300,
        now: Optional[float] = None,
    ) -> Optional[Lease]:
        if not owner or lease_seconds < 1:
            raise ValueError("owner and positive lease_seconds are required")
        current = time.time() if now is None else float(now)
        expires = current + lease_seconds
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT state, lease_expires_at FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone()
                if row is None:
                    raise KeyError(task_id)
                if row["state"] == "leased" and row["lease_expires_at"] <= current:
                    connection.execute(
                        """
                        UPDATE tasks SET state='recoverable', owner=NULL,
                            lease_expires_at=NULL, updated_at=?
                        WHERE task_id=? AND state='leased' AND lease_expires_at<=?
                        """,
                        (current, task_id, current),
                    )
                    row = {"state": "recoverable"}
                if row["state"] not in ("queued", "recoverable"):
                    connection.commit()
                    return None
                connection.execute(
                    """
                    UPDATE tasks SET state='leased', owner=?, fencing_token=fencing_token+1,
                        lease_expires_at=?, updated_at=?
                    WHERE task_id=? AND state IN ('queued','recoverable')
                    """,
                    (owner, expires, current, task_id),
                )
                updated = connection.execute(
                    "SELECT fencing_token FROM tasks WHERE task_id=?", (task_id,)
                ).fetchone()
                connection.commit()
                return Lease(task_id, owner, updated["fencing_token"])
            except Exception:
                connection.rollback()
                raise

    def renew_lease(
        self, *, lease: Lease, lease_seconds: int = 300, now: Optional[float] = None,
    ) -> bool:
        """Extend a live lease without changing its fencing token."""
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        current = time.time() if now is None else float(now)
        expires = current + lease_seconds
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks SET lease_expires_at=MAX(lease_expires_at, ?), updated_at=?
                    WHERE task_id=? AND state='leased' AND owner=? AND fencing_token=?
                        AND lease_expires_at>?
                    """,
                    (expires, current, lease.task_id, lease.owner, lease.fencing_token, current),
                )
                connection.commit()
                return cursor.rowcount == 1
            except Exception:
                connection.rollback()
                raise

    def release_for_reconciliation(
        self, *, lease: Lease, now: Optional[float] = None,
    ) -> bool:
        """Release an active dispatch lease while preserving the outbox's retry gate."""
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            cursor = connection.execute(
                """
                UPDATE tasks SET state='recoverable', owner=NULL, lease_expires_at=NULL,
                    updated_at=?
                WHERE task_id=? AND state='leased' AND owner=? AND fencing_token=?
                    AND lease_expires_at>?
                """,
                (current, lease.task_id, lease.owner, lease.fencing_token, current),
            )
            return cursor.rowcount == 1

    def mark_submitted(
        self, *, lease: Lease, provider_id: str, external_run_id: str,
        now: Optional[float] = None,
    ) -> bool:
        """Attach the accepted backend run and release the dispatch lease atomically."""
        if not provider_id or not external_run_id:
            raise ValueError("provider and external run identity are required")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks SET state='submitted', owner=NULL, lease_expires_at=NULL,
                        provider_id=?, external_run_id=?, heartbeat_at=?, updated_at=?
                    WHERE task_id=? AND state='leased' AND owner=? AND fencing_token=?
                        AND lease_expires_at>?
                    """,
                    (
                        provider_id, external_run_id, current, current,
                        lease.task_id, lease.owner, lease.fencing_token, current,
                    ),
                )
                connection.commit()
                return cursor.rowcount == 1
            except Exception:
                connection.rollback()
                raise

    def replace_provider_run_after_no_effect_failure(
        self, *, task_id: str, previous_provider_id: str,
        previous_external_run_id: str, provider_id: str, external_run_id: str,
        no_side_effects_confirmed: bool, now: Optional[float] = None,
    ) -> bool:
        """Bind a failover run only after the prior run's no-effect failure is proven."""
        if not no_side_effects_confirmed:
            raise ValueError("provider failover requires a no-side-effects attestation")
        if not all((previous_provider_id, previous_external_run_id, provider_id, external_run_id)):
            raise ValueError("provider run identities are required")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks SET state='submitted', provider_id=?, external_run_id=?,
                        heartbeat_at=?, result=NULL, failure_class=NULL, updated_at=?
                    WHERE task_id=? AND provider_id=? AND external_run_id=?
                        AND state IN ('submitted','running')
                    """,
                    (
                        provider_id, external_run_id, current, current,
                        task_id, previous_provider_id, previous_external_run_id,
                    ),
                )
                connection.commit()
                return cursor.rowcount == 1
            except Exception:
                connection.rollback()
                raise

    def mark_provider_running(
        self, *, task_id: str, provider_id: str, external_run_id: str,
        now: Optional[float] = None,
    ) -> bool:
        return self.record_provider_heartbeat(
            task_id=task_id, provider_id=provider_id,
            external_run_id=external_run_id, running=True, now=now,
        )

    def record_provider_heartbeat(
        self, *, task_id: str, provider_id: str, external_run_id: str,
        running: bool = False, now: Optional[float] = None,
    ) -> bool:
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                states = ("submitted", "running")
                row = connection.execute(
                    "SELECT state FROM tasks WHERE task_id=? AND provider_id=? AND external_run_id=?",
                    (task_id, provider_id, external_run_id),
                ).fetchone()
                if row is None or row["state"] not in states:
                    connection.commit()
                    return False
                target = "running" if running else row["state"]
                connection.execute(
                    """
                    UPDATE tasks SET state=?, heartbeat_at=?, updated_at=?
                    WHERE task_id=? AND provider_id=? AND external_run_id=?
                        AND state IN ('submitted','running')
                    """,
                    (target, current, current, task_id, provider_id, external_run_id),
                )
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise

    def publish_provider_result(
        self, *, task_id: str, provider_id: str, external_run_id: str,
        state: str, result: Optional[str] = None,
        failure_class: Optional[str] = None, now: Optional[float] = None,
    ) -> bool:
        """Persist a provider terminal state only for its bound external run."""
        if state not in {"succeeded", "failed", "cancelled"}:
            raise ValueError("provider result must be terminal")
        if state == "failed" and failure_class not in {
            "test_failure", "code_failure", "provider_failure", "worker_timeout"
        }:
            raise ValueError("failure_class is not allowlisted")
        if state != "failed" and failure_class is not None:
            raise ValueError("failure_class is only valid for failed tasks")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    """
                    SELECT state,result,failure_class FROM tasks
                    WHERE task_id=? AND provider_id=? AND external_run_id=?
                    """,
                    (task_id, provider_id, external_run_id),
                ).fetchone()
                if row is None:
                    connection.commit()
                    return False
                if row["state"] in {"succeeded", "failed", "cancelled"}:
                    identical = (
                        row["state"] == state
                        and row["result"] == result
                        and row["failure_class"] == failure_class
                    )
                    connection.commit()
                    return identical
                if row["state"] not in {"submitted", "running"}:
                    connection.commit()
                    return False
                connection.execute(
                    """
                    UPDATE tasks SET state=?, result=?, failure_class=?,
                        heartbeat_at=?, updated_at=?
                    WHERE task_id=? AND provider_id=? AND external_run_id=?
                        AND state IN ('submitted','running')
                    """,
                    (
                        state, result, failure_class, current, current,
                        task_id, provider_id, external_run_id,
                    ),
                )
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise

    def recover_expired(self, *, now: Optional[float] = None) -> int:
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks SET state='recoverable', owner=NULL,
                        lease_expires_at=NULL, updated_at=?
                    WHERE state='leased' AND lease_expires_at<=?
                    """,
                    (current, current),
                )
                count = cursor.rowcount
                connection.commit()
                return count
            except Exception:
                connection.rollback()
                raise

    def publish_result(self, *, lease: Lease, result: str, now: Optional[float] = None) -> bool:
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks SET state='succeeded', owner=NULL, lease_expires_at=NULL,
                        result=?, failure_class=NULL, updated_at=?
                    WHERE task_id=? AND state='leased' AND owner=? AND fencing_token=?
                        AND lease_expires_at>?
                    """,
                    (result, current, lease.task_id, lease.owner, lease.fencing_token, current),
                )
                connection.commit()
                return cursor.rowcount == 1
            except Exception:
                connection.rollback()
                raise

    def mark_failed(
        self, *, lease: Lease, failure_class: str, now: Optional[float] = None,
    ) -> bool:
        if failure_class not in {"test_failure", "code_failure"}:
            raise ValueError("only terminal task failures are accepted here")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                cursor = connection.execute(
                    """
                    UPDATE tasks SET state='failed', owner=NULL, lease_expires_at=NULL,
                        failure_class=?, updated_at=?
                    WHERE task_id=? AND state='leased' AND owner=? AND fencing_token=?
                        AND lease_expires_at>?
                    """,
                    (failure_class, current, lease.task_id, lease.owner, lease.fencing_token, current),
                )
                connection.commit()
                return cursor.rowcount == 1
            except Exception:
                connection.rollback()
                raise

    def get(self, task_id: str) -> TaskSnapshot:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(task_id)
        return self._snapshot(row)

    def get_by_idempotency_key(self, idempotency_key: str) -> TaskSnapshot:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
        if row is None:
            raise KeyError(idempotency_key)
        return self._snapshot(row)
