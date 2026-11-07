"""Durable, single-host SQLite task coordinator.

SQLite WAL provides process-safe transactions on one host. This module is not a
multi-host distributed database and must not be placed on an arbitrary network
filesystem. All transitions are fenced by monotonically increasing lease tokens.
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


class SQLiteCoordinator:
    """Persistent single-host coordinator with atomic claims and fenced results.

    Use a local persistent filesystem. Each operation opens its own connection,
    so multiple processes can coordinate through SQLite's transactional locks.
    """

    SCHEMA_VERSION = 1

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

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, self.SCHEMA_VERSION):
                raise RuntimeError("unsupported coordinator database schema version")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        input_digest TEXT NOT NULL,
                        state TEXT NOT NULL CHECK (
                            state IN ('queued','leased','recoverable','succeeded','failed')
                        ),
                        owner TEXT,
                        fencing_token INTEGER NOT NULL DEFAULT 0 CHECK (fencing_token >= 0),
                        lease_expires_at REAL,
                        result TEXT,
                        failure_class TEXT,
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        CHECK (
                            (state = 'leased' AND owner IS NOT NULL AND lease_expires_at IS NOT NULL)
                            OR
                            (state <> 'leased' AND owner IS NULL AND lease_expires_at IS NULL)
                        )
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS tasks_state_expiry ON tasks(state, lease_expires_at)"
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
        self,
        *,
        task_id: str,
        owner: str,
        lease_seconds: int = 300,
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
        self, *, lease: Lease, failure_class: str, now: Optional[float] = None
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
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id=?", (task_id,)
            ).fetchone()
        if row is None:
            raise KeyError(task_id)
        return self._snapshot(row)
