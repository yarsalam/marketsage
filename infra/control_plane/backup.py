"""Consistent, integrity-checked SQLite backup and restore helpers.

The coordinator and dispatch outbox share a SQLite database. Backups use
SQLite's online backup API (so committed WAL transactions are included) and
are published atomically without replacing an existing file. Restore always
writes to a new path; it never overwrites a live database.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackupReport:
    sha256: str
    size_bytes: int
    page_count: int
    integrity: str = "ok"

    def sanitized_dict(self) -> dict[str, object]:
        return {
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "page_count": self.page_count,
            "integrity": self.integrity,
        }


def _existing_database_path(value: str | Path) -> Path:
    if str(value) == ":memory:":
        raise ValueError("a file-backed SQLite database is required")
    path = Path(value).expanduser()
    if not path.is_file():
        raise FileNotFoundError("SQLite source database does not exist")
    return path.resolve(strict=True)


def _new_destination_path(value: str | Path, source: Path) -> Path:
    if str(value) == ":memory:":
        raise ValueError("a file-backed destination is required")
    raw = Path(value).expanduser()
    parent = raw.parent.resolve(strict=True)
    destination = parent / raw.name
    if destination == source:
        raise ValueError("source and destination must differ")
    if os.path.lexists(destination):
        raise FileExistsError("destination already exists; refusing to overwrite")
    return destination


def _integrity_and_pages(connection: sqlite3.Connection) -> int:
    rows = connection.execute("PRAGMA integrity_check").fetchall()
    if len(rows) != 1 or rows[0][0] != "ok":
        raise sqlite3.DatabaseError("SQLite integrity check failed")
    return int(connection.execute("PRAGMA page_count").fetchone()[0])


def _digest(path: Path) -> BackupReport:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if size <= 0:
        raise sqlite3.DatabaseError("SQLite backup is empty")
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        pages = _integrity_and_pages(connection)
    finally:
        connection.close()
    return BackupReport(
        sha256=digest.hexdigest(),
        size_bytes=size,
        page_count=pages,
    )


def _copy_and_publish(source: Path, destination: Path) -> BackupReport:
    destination.parent.mkdir(parents=False, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".sqlite-tmp",
        dir=destination.parent,
    )
    os.close(fd)
    temporary = Path(temporary_name)
    source_db: sqlite3.Connection | None = None
    target_db: sqlite3.Connection | None = None
    try:
        source_db = sqlite3.connect(str(source), timeout=5.0)
        source_db.execute("PRAGMA busy_timeout=5000")
        target_db = sqlite3.connect(str(temporary), timeout=5.0)
        source_db.backup(target_db, pages=256, sleep=0.05)
        _integrity_and_pages(target_db)
        target_db.close()
        target_db = None
        source_db.close()
        source_db = None

        os.chmod(temporary, 0o600)
        # The temporary file is in the destination directory. hard-link
        # creation is atomic and fails rather than replacing a concurrent file.
        os.link(temporary, destination)
        directory_fd = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return _digest(destination)
    finally:
        if target_db is not None:
            target_db.close()
        if source_db is not None:
            source_db.close()
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def create_backup(
    source_path: str | Path,
    backup_path: str | Path,
) -> BackupReport:
    """Create a consistent SQLite snapshot without overwriting an existing file."""
    source = _existing_database_path(source_path)
    destination = _new_destination_path(backup_path, source)
    return _copy_and_publish(source, destination)


def restore_backup(
    backup_path: str | Path,
    destination_path: str | Path,
) -> BackupReport:
    """Restore a verified snapshot to a new database path; never replace live data."""
    source = _existing_database_path(backup_path)
    destination = _new_destination_path(destination_path, source)
    # Validate the backup before copying it into a restore target.
    _digest(source)
    return _copy_and_publish(source, destination)
