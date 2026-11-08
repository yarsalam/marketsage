"""Durable provider-dispatch ledger for conservative, idempotent failover.

The outbox is a single-host SQLite component. It records the intent to submit
before calling a provider and blocks a second provider while the first
submission is ambiguous. A process crash after entering SUBMITTING is treated
as UNKNOWN; callers must reconcile by the immutable idempotency key. A missing
reconciliation result is not proof of non-acceptance and never unlocks failover.

This module does not contact providers or execute tasks. It is the durable
state boundary that a future orchestrator must use around provider calls.
"""
from __future__ import annotations

import re
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional

from .lifecycle import IdempotencyConflict, RunState, TERMINAL_STATES

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_PROVIDER_ATTEMPTS = 3


class DispatchState(str, Enum):
    PREPARED = "prepared"
    SUBMITTING = "submitting"
    UNKNOWN = "unknown"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DispatchSnapshot:
    idempotency_key: str
    input_digest: str
    state: DispatchState
    current_attempt: int
    current_provider_id: Optional[str]
    external_run_id: Optional[str]
    failure_class: Optional[str]
    no_side_effects: bool
    created_at: float
    updated_at: float


@dataclass(frozen=True)
class DispatchAttempt:
    idempotency_key: str
    attempt_no: int
    provider_id: str
    state: DispatchState
    external_run_id: Optional[str]
    failure_class: Optional[str]
    no_side_effects: bool
    created_at: float
    updated_at: float


class SQLiteDispatchOutbox:
    """Persistent dispatch ledger; use a local disk path, never shared NFS."""

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
                raise RuntimeError("unsupported dispatch outbox schema version")
            connection.execute("BEGIN IMMEDIATE")
            try:
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS dispatches (
                        idempotency_key TEXT PRIMARY KEY,
                        input_digest TEXT NOT NULL,
                        state TEXT NOT NULL CHECK (state IN (
                            'prepared','submitting','unknown','accepted','rejected',
                            'succeeded','failed','cancelled'
                        )),
                        current_attempt INTEGER NOT NULL DEFAULT 0 CHECK (current_attempt >= 0),
                        current_provider_id TEXT,
                        external_run_id TEXT,
                        failure_class TEXT,
                        no_side_effects INTEGER NOT NULL DEFAULT 0 CHECK (no_side_effects IN (0,1)),
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL
                    )"""
                )
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS dispatch_attempts (
                        idempotency_key TEXT NOT NULL REFERENCES dispatches(idempotency_key),
                        attempt_no INTEGER NOT NULL CHECK (attempt_no >= 1),
                        provider_id TEXT NOT NULL,
                        state TEXT NOT NULL CHECK (state IN (
                            'submitting','unknown','accepted','rejected',
                            'succeeded','failed','cancelled'
                        )),
                        external_run_id TEXT,
                        failure_class TEXT,
                        no_side_effects INTEGER NOT NULL DEFAULT 0 CHECK (no_side_effects IN (0,1)),
                        created_at REAL NOT NULL,
                        updated_at REAL NOT NULL,
                        PRIMARY KEY (idempotency_key, attempt_no),
                        UNIQUE (provider_id, external_run_id)
                    )"""
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS dispatch_attempts_state ON dispatch_attempts(state, updated_at)"
                )
                connection.execute(f"PRAGMA user_version={self.SCHEMA_VERSION}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _snapshot(row: sqlite3.Row) -> DispatchSnapshot:
        return DispatchSnapshot(
            idempotency_key=row["idempotency_key"],
            input_digest=row["input_digest"],
            state=DispatchState(row["state"]),
            current_attempt=row["current_attempt"],
            current_provider_id=row["current_provider_id"],
            external_run_id=row["external_run_id"],
            failure_class=row["failure_class"],
            no_side_effects=bool(row["no_side_effects"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _attempt(row: sqlite3.Row) -> DispatchAttempt:
        return DispatchAttempt(
            idempotency_key=row["idempotency_key"],
            attempt_no=row["attempt_no"],
            provider_id=row["provider_id"],
            state=DispatchState(row["state"]),
            external_run_id=row["external_run_id"],
            failure_class=row["failure_class"],
            no_side_effects=bool(row["no_side_effects"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def prepare(
        self, *, idempotency_key: str, input_digest: str, now: Optional[float] = None
    ) -> DispatchSnapshot:
        if not idempotency_key or len(idempotency_key) > 256:
            raise ValueError("idempotency_key is required and must be bounded")
        if not isinstance(input_digest, str) or not _SHA256.fullmatch(input_digest):
            raise ValueError("input_digest must be a lowercase SHA-256 digest")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if row is not None:
                    if row["input_digest"] != input_digest:
                        raise IdempotencyConflict("idempotency key/input mismatch")
                    connection.commit()
                    return self._snapshot(row)
                connection.execute(
                    """INSERT INTO dispatches (
                        idempotency_key,input_digest,state,created_at,updated_at
                    ) VALUES (?,?,'prepared',?,?)""",
                    (idempotency_key, input_digest, current, current),
                )
                row = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                connection.commit()
                return self._snapshot(row)
            except Exception:
                connection.rollback()
                raise

    def begin_attempt(
        self, *, idempotency_key: str, provider_id: str, now: Optional[float] = None
    ) -> Optional[DispatchAttempt]:
        """Persist SUBMITTING before a provider call; never duplicate an uncertain call."""
        if not provider_id or len(provider_id) > 128:
            raise ValueError("provider_id is required and must be bounded")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                dispatch = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if dispatch is None:
                    raise KeyError(idempotency_key)
                state = DispatchState(dispatch["state"])
                allowed = state == DispatchState.PREPARED or (
                    state == DispatchState.REJECTED
                ) or (state == DispatchState.FAILED and bool(dispatch["no_side_effects"]))
                if not allowed:
                    connection.commit()
                    return None
                previous = connection.execute(
                    "SELECT provider_id FROM dispatch_attempts WHERE idempotency_key=?",
                    (idempotency_key,),
                ).fetchall()
                if any(row["provider_id"] == provider_id for row in previous):
                    connection.commit()
                    return None
                attempt_no = int(dispatch["current_attempt"]) + 1
                if attempt_no > _MAX_PROVIDER_ATTEMPTS:
                    connection.commit()
                    return None
                connection.execute(
                    """INSERT INTO dispatch_attempts (
                        idempotency_key,attempt_no,provider_id,state,created_at,updated_at
                    ) VALUES (?,?,?,'submitting',?,?)""",
                    (idempotency_key, attempt_no, provider_id, current, current),
                )
                connection.execute(
                    """UPDATE dispatches SET state='submitting', current_attempt=?,
                        current_provider_id=?, external_run_id=NULL, failure_class=NULL,
                        no_side_effects=0, updated_at=? WHERE idempotency_key=?""",
                    (attempt_no, provider_id, current, idempotency_key),
                )
                row = connection.execute(
                    "SELECT * FROM dispatch_attempts WHERE idempotency_key=? AND attempt_no=?",
                    (idempotency_key, attempt_no),
                ).fetchone()
                connection.commit()
                return self._attempt(row)
            except Exception:
                connection.rollback()
                raise

    def mark_accepted(self, *, receipt: object, now: Optional[float] = None) -> DispatchSnapshot:
        provider_id = str(getattr(receipt, "provider_id"))
        external_run_id = str(getattr(receipt, "external_run_id"))
        idempotency_key = str(getattr(receipt, "idempotency_key"))
        input_digest = str(getattr(receipt, "input_digest"))
        provider_state = getattr(receipt, "state")
        state_value = str(getattr(provider_state, "value", provider_state))
        if state_value not in {RunState.QUEUED.value, RunState.RUNNING.value}:
            raise ValueError("an accepted non-terminal provider receipt is required")
        if not provider_id or not external_run_id:
            raise ValueError("provider receipt identity is incomplete")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                dispatch = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if dispatch is None:
                    raise KeyError(idempotency_key)
                if dispatch["input_digest"] != input_digest:
                    raise IdempotencyConflict("provider receipt input mismatch")
                attempt_no = dispatch["current_attempt"]
                attempt = connection.execute(
                    "SELECT * FROM dispatch_attempts WHERE idempotency_key=? AND attempt_no=?",
                    (idempotency_key, attempt_no),
                ).fetchone()
                if attempt is None or attempt["provider_id"] != provider_id:
                    raise ValueError("provider receipt does not match active dispatch attempt")
                if attempt["state"] == DispatchState.ACCEPTED.value:
                    if attempt["external_run_id"] != external_run_id:
                        raise IdempotencyConflict("provider returned conflicting run identity")
                    connection.commit()
                    return self._snapshot(dispatch)
                if attempt["state"] not in {DispatchState.SUBMITTING.value, DispatchState.UNKNOWN.value}:
                    raise ValueError("provider attempt is not awaiting reconciliation")
                connection.execute(
                    """UPDATE dispatch_attempts SET state='accepted', external_run_id=?,
                        updated_at=? WHERE idempotency_key=? AND attempt_no=?""",
                    (external_run_id, current, idempotency_key, attempt_no),
                )
                connection.execute(
                    """UPDATE dispatches SET state='accepted', external_run_id=?,
                        failure_class=NULL, no_side_effects=0, updated_at=?
                        WHERE idempotency_key=?""",
                    (external_run_id, current, idempotency_key),
                )
                updated = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                connection.commit()
                return self._snapshot(updated)
            except Exception:
                connection.rollback()
                raise

    def mark_unknown(
        self, *, idempotency_key: str, provider_id: str, reason_code: str = "response_unknown",
        now: Optional[float] = None,
    ) -> bool:
        if reason_code not in {"response_unknown", "transport_timeout", "process_interrupted"}:
            raise ValueError("unknown dispatch reason code")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                dispatch = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if dispatch is None:
                    raise KeyError(idempotency_key)
                attempt_no = dispatch["current_attempt"]
                if dispatch["current_provider_id"] != provider_id or dispatch["state"] not in {
                    DispatchState.SUBMITTING.value, DispatchState.UNKNOWN.value
                }:
                    connection.commit()
                    return False
                connection.execute(
                    """UPDATE dispatch_attempts SET state='unknown', failure_class=?,
                        updated_at=? WHERE idempotency_key=? AND attempt_no=?""",
                    (reason_code, current, idempotency_key, attempt_no),
                )
                connection.execute(
                    """UPDATE dispatches SET state='unknown', failure_class=?, updated_at=?
                        WHERE idempotency_key=?""",
                    (reason_code, current, idempotency_key),
                )
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise

    def mark_rejected(
        self, *, idempotency_key: str, provider_id: str, reason_code: str = "capacity_unavailable",
        now: Optional[float] = None,
    ) -> bool:
        """Record a definitive pre-acceptance rejection that permits another provider."""
        if reason_code not in {"capacity_unavailable", "pre_acceptance_rejected"}:
            raise ValueError("rejection must be a known pre-acceptance outcome")
        current = time.time() if now is None else float(now)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                dispatch = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if dispatch is None:
                    raise KeyError(idempotency_key)
                attempt_no = dispatch["current_attempt"]
                if dispatch["current_provider_id"] != provider_id or dispatch["state"] != DispatchState.SUBMITTING.value:
                    connection.commit()
                    return False
                connection.execute(
                    """UPDATE dispatch_attempts SET state='rejected', failure_class=?,
                        no_side_effects=1, updated_at=?
                        WHERE idempotency_key=? AND attempt_no=?""",
                    (reason_code, current, idempotency_key, attempt_no),
                )
                connection.execute(
                    """UPDATE dispatches SET state='rejected', failure_class=?,
                        no_side_effects=1, updated_at=? WHERE idempotency_key=?""",
                    (reason_code, current, idempotency_key),
                )
                connection.commit()
                return True
            except Exception:
                connection.rollback()
                raise

    def mark_terminal(
        self, *, receipt: object, no_side_effects_on_failure: bool = False,
        now: Optional[float] = None,
    ) -> DispatchSnapshot:
        provider_id = str(getattr(receipt, "provider_id"))
        external_run_id = str(getattr(receipt, "external_run_id"))
        idempotency_key = str(getattr(receipt, "idempotency_key"))
        input_digest = str(getattr(receipt, "input_digest"))
        provider_state = getattr(receipt, "state")
        state_value = str(getattr(provider_state, "value", provider_state))
        if state_value not in {item.value for item in TERMINAL_STATES}:
            raise ValueError("terminal provider state is required")
        current = time.time() if now is None else float(now)
        target = DispatchState(state_value)
        no_effects = bool(no_side_effects_on_failure) if target == DispatchState.FAILED else False
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                dispatch = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if dispatch is None:
                    raise KeyError(idempotency_key)
                if dispatch["input_digest"] != input_digest:
                    raise IdempotencyConflict("provider receipt input mismatch")
                attempt_no = dispatch["current_attempt"]
                attempt = connection.execute(
                    "SELECT * FROM dispatch_attempts WHERE idempotency_key=? AND attempt_no=?",
                    (idempotency_key, attempt_no),
                ).fetchone()
                if attempt is None or attempt["provider_id"] != provider_id:
                    raise ValueError("provider receipt does not match active dispatch attempt")
                if attempt["state"] not in {DispatchState.ACCEPTED.value, DispatchState.UNKNOWN.value, DispatchState.SUBMITTING.value}:
                    if attempt["state"] == target.value and attempt["external_run_id"] == external_run_id:
                        connection.commit()
                        return self._snapshot(dispatch)
                    raise ValueError("provider attempt cannot transition to terminal state")
                if attempt["external_run_id"] not in (None, external_run_id):
                    raise IdempotencyConflict("provider returned conflicting run identity")
                connection.execute(
                    """UPDATE dispatch_attempts SET state=?, external_run_id=?,
                        no_side_effects=?, failure_class=NULL, updated_at=?
                        WHERE idempotency_key=? AND attempt_no=?""",
                    (target.value, external_run_id, int(no_effects), current, idempotency_key, attempt_no),
                )
                connection.execute(
                    """UPDATE dispatches SET state=?, external_run_id=?,
                        no_side_effects=?, failure_class=NULL, updated_at=?
                        WHERE idempotency_key=?""",
                    (target.value, external_run_id, int(no_effects), current, idempotency_key),
                )
                updated = connection.execute(
                    "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                connection.commit()
                return self._snapshot(updated)
            except Exception:
                connection.rollback()
                raise

    def get(self, idempotency_key: str) -> DispatchSnapshot:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM dispatches WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
        if row is None:
            raise KeyError(idempotency_key)
        return self._snapshot(row)

    def attempts(self, idempotency_key: str) -> tuple[DispatchAttempt, ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM dispatch_attempts WHERE idempotency_key=? ORDER BY attempt_no",
                (idempotency_key,),
            ).fetchall()
        return tuple(self._attempt(row) for row in rows)
