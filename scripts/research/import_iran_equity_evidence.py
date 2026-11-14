#!/usr/bin/env python3
"""Copy an approved, immutable subset of local Iran-equity research evidence into this repo.

The source tree is never modified or deleted. The script intentionally copies only
three pilot instruments and a small allowlist of shared audit folders. It preserves
original CSV review files as deterministic gzip archives and creates per-symbol,
primary-InsCode-only, deduplicated review extracts with source-row provenance.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SYMBOLS = {
    "vaghdir": {"ticker": "وغدیر", "primary_inscode": "26014913469567886"},
    "foolad": {"ticker": "فولاد", "primary_inscode": "46348559193224090"},
    "parsian": {"ticker": "پارسیان", "primary_inscode": "9481703061634967"},
}
SHARED_DIRS = (
    "official_chart_validation",
    "adjustment_factor_diagnostics",
    "three_symbol_audit_runs",
    "tse_client_validation",
)
REVIEW_FILES = (
    "corporate_action_evidence_review.csv",
    "date_gap_evidence_review.csv",
)
MAX_FILE_BYTES = 95 * 1024 * 1024
DEST_REL = Path("data/market-research/iran-equities/adjustment-evidence")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalized(value: Any) -> str:
    return str(value or "").strip().replace("ي", "ی").replace("ك", "ک")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def excluded(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith("."):
        return True
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx", ".sqlite", ".db"}:
        return True
    if path.suffix.lower() in {".log", ".bak", ".swp"}:
        return True
    if any(word in name for word in ("secret", "credential", "password", "private_key", "token")):
        return True
    return False


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def walk_inscode_paths(value: Any, primary: str, path: str = "$") -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if "inscode" in str(key).lower().replace("_", "") and normalized(item) == primary:
                matches.append(child)
            matches.extend(walk_inscode_paths(item, primary, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            matches.extend(walk_inscode_paths(item, primary, f"{path}[{index}]"))
    return matches


class Importer:
    def __init__(self, source_root: Path, review_root: Path, repo_root: Path, max_file_bytes: int):
        self.source_root = source_root.resolve()
        self.review_root = review_root.resolve()
        self.repo_root = repo_root.resolve()
        self.destination = self.repo_root / DEST_REL
        self.max_file_bytes = max_file_bytes
        self.entries: list[dict[str, Any]] = []
        self.skipped: list[dict[str, Any]] = []

    def add_file(self, source: Path, relative_dest: Path, *, compress: bool = False) -> None:
        if source.is_symlink() or not source.is_file() or excluded(source):
            return
        size = source.stat().st_size
        source_hash = sha256_file(source)
        payload = gzip.compress(source.read_bytes(), compresslevel=9, mtime=0) if compress else None
        stored_candidate_size = len(payload) if payload is not None else size
        if stored_candidate_size > self.max_file_bytes:
            try:
                source_rel = str(source.relative_to(self.source_root))
            except ValueError:
                source_rel = str(source.relative_to(self.review_root))
            self.skipped.append({
                "source_relative": source_rel,
                "destination_relative": str(relative_dest),
                "bytes": size,
                "stored_candidate_bytes": stored_candidate_size,
                "reason": f"stored file exceeds configured limit ({self.max_file_bytes} bytes)",
                "source_sha256": source_hash,
            })
            return

        final_rel = Path(str(relative_dest) + ".gz") if compress else relative_dest
        target = self.destination / final_rel
        target.parent.mkdir(parents=True, exist_ok=True)

        if compress:
            assert payload is not None
            if target.exists() and target.read_bytes() != payload:
                raise RuntimeError(f"Refusing to replace existing immutable archive: {target}")
            if not target.exists():
                target.write_bytes(payload)
            output_hash = hashlib.sha256(payload).hexdigest()
            output_size = len(payload)
        else:
            if target.exists():
                existing_hash = sha256_file(target)
                if existing_hash != source_hash:
                    raise RuntimeError(
                        f"Refusing to overwrite different raw content: {target}; "
                        "preserve the older version under a new filename first."
                    )
            else:
                shutil.copy2(source, target)
            output_hash = source_hash
            output_size = target.stat().st_size

        try:
            source_rel = str(source.relative_to(self.source_root))
        except ValueError:
            source_rel = str(source.relative_to(self.review_root))

        self.entries.append({
            "source_relative": source_rel,
            "destination_relative": str(final_rel),
            "source_bytes": size,
            "stored_bytes": output_size,
            "source_sha256": source_hash,
            "stored_sha256": output_hash,
            "compression": "gzip" if compress else "none",
        })

    def copy_tree(self, source: Path, dest_rel: Path) -> None:
        if not source.exists() or not source.is_dir():
            return
        for item in sorted(source.rglob("*")):
            if item.is_symlink() or not item.is_file() or excluded(item):
                continue
            rel = item.relative_to(source)
            self.add_file(item, dest_rel / rel)

    def load_identity(self, symbol: str) -> dict[str, Any]:
        path = self.source_root / "raw_provider_snapshots" / f"{symbol}_instrument_search.json"
        if not path.is_file():
            raise FileNotFoundError(f"Missing exact TSETMC instrument search snapshot: {path}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        records = raw.get("instrumentSearch", [])
        ticker = SYMBOLS[symbol]["ticker"]
        exact = [r for r in records if normalized(r.get("lVal18AFC")) == ticker]
        if len(exact) != 1:
            raise RuntimeError(f"{symbol}: expected exactly one exact ticker record, got {len(exact)}")
        record = exact[0]
        primary = normalized(record.get("insCode"))
        expected = SYMBOLS[symbol]["primary_inscode"]
        if primary != expected:
            raise RuntimeError(
                f"{symbol}: primary InsCode mismatch; expected {expected}, found {primary}"
            )
        return {
            "symbol": symbol,
            "ticker": ticker,
            "issuer_or_instrument_name": record.get("lVal30"),
            "primary_insCode": primary,
            "cIsin": record.get("cIsin"),
            "instrumentID": record.get("instrumentID"),
            "related_ids": {
                key: record.get(key) for key in ("insCode2", "insCode3", "insCode4")
            },
            "related_id_status": "unverified_aliases_not_used_for_matching",
            "identity_source": f"raw_provider_snapshots/{symbol}_instrument_search.json",
            "exact_ticker_record": record,
            "identity_checked_at_utc": utc_now(),
        }

    def extract_review(self, csv_path: Path, symbol: str) -> None:
        primary = SYMBOLS[symbol]["primary_inscode"]
        groups: dict[str, dict[str, Any]] = {}
        with csv_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            for row_number, row in enumerate(reader, start=2):
                try:
                    record = json.loads(row.get("record_json") or "{}")
                except (TypeError, json.JSONDecodeError):
                    continue
                paths = walk_inscode_paths(record, primary)
                if not paths:
                    continue
                record_text = canonical_json(record)
                group = groups.setdefault(record_text, {
                    "record": record,
                    "paths": set(),
                    "source_refs": [],
                    "metadata": set(),
                })
                group["paths"].update(paths)
                group["source_refs"].append({
                    "review_csv": csv_path.name,
                    "row_number": row_number,
                    "evidence_file": row.get("evidence_file", ""),
                })
                group["metadata"].add(canonical_json({
                    key: value for key, value in row.items() if key != "record_json"
                }))

        output_name = csv_path.stem.replace("_evidence_review", "") + "_deduplicated.csv"
        target = self.destination / symbol / "validation" / "acceptance-review" / output_name
        target.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "symbol", "primary_insCode", "record_sha256", "matching_identity_paths",
            "source_refs_json", "row_metadata_variants_json", "record_json",
        ]
        with target.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            for record_text, group in sorted(groups.items(), key=lambda item: item[0]):
                record_hash = hashlib.sha256(record_text.encode("utf-8")).hexdigest()
                writer.writerow({
                    "symbol": symbol,
                    "primary_insCode": primary,
                    "record_sha256": record_hash,
                    "matching_identity_paths": canonical_json(sorted(group["paths"])),
                    "source_refs_json": canonical_json(group["source_refs"]),
                    "row_metadata_variants_json": canonical_json(sorted(group["metadata"])),
                    "record_json": record_text,
                })
        self.entries.append({
            "source_relative": str(csv_path.relative_to(self.review_root)),
            "destination_relative": str(target.relative_to(self.destination)),
            "source_bytes": csv_path.stat().st_size,
            "stored_bytes": target.stat().st_size,
            "source_sha256": sha256_file(csv_path),
            "stored_sha256": sha256_file(target),
            "compression": "deduplicated_primary_inscode_extract",
            "unique_records": len(groups),
        })

    def run(self) -> int:
        if not self.source_root.is_dir():
            raise FileNotFoundError(f"Source root not found: {self.source_root}")
        if not self.review_root.is_dir():
            raise FileNotFoundError(f"Acceptance-review root not found: {self.review_root}")
        if not (self.repo_root / ".git").exists():
            raise RuntimeError(f"repo-root does not look like a Git working tree: {self.repo_root}")

        raw_dir = self.source_root / "raw_provider_snapshots"
        for symbol in SYMBOLS:
            identity = self.load_identity(symbol)
            write_json(self.destination / symbol / "identity.json", identity)

            prefix_files = sorted(raw_dir.glob(f"{symbol}_*"))
            copied_before = len(self.entries)
            for item in prefix_files:
                if item.is_file():
                    self.add_file(item, Path(symbol) / "raw" / "tsetmc" / item.name)
            if len(self.entries) == copied_before:
                raise RuntimeError(f"{symbol}: no raw provider files were imported")

            for codal_dir in sorted(self.source_root.glob(f"codal_{symbol}_*")):
                if codal_dir.is_dir():
                    self.copy_tree(codal_dir, Path(symbol) / "codal" / codal_dir.name)

            for review_name in REVIEW_FILES:
                review_csv = self.review_root / review_name
                if review_csv.is_file():
                    self.extract_review(review_csv, symbol)

        for shared_name in SHARED_DIRS:
            self.copy_tree(self.source_root / shared_name, Path("_shared") / shared_name)

        for review_name in REVIEW_FILES:
            source = self.review_root / review_name
            if source.is_file():
                self.add_file(
                    source,
                    Path("_shared") / "archive" / "acceptance-review" / review_name,
                    compress=True,
                )

        manifest = {
            "schema_version": 1,
            "generated_at_utc": utc_now(),
            "repository_visibility_note": "This repository is public; commit only material approved for public redistribution.",
            "source_root_label": "marketsage-data/tsetmc-three-adjusted",
            "acceptance_review_label": "marketsage-data/acceptance-review/20261023T193750Z",
            "source_files_mutated": False,
            "matching_policy": "primary InsCode only; related InsCode2-4 are preserved but never used as aliases",
            "symbols": SYMBOLS,
            "files": sorted(self.entries, key=lambda entry: entry["destination_relative"]),
            "skipped": self.skipped,
        }
        write_json(self.destination / "import_manifest.json", manifest)

        sums = []
        for item in sorted(self.destination.rglob("*")):
            if item.is_file() and item.name != "SHA256SUMS.txt":
                sums.append(f"{sha256_file(item)}  {item.relative_to(self.destination)}")
        (self.destination / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")

        print("IMPORT COMPLETE")
        print(f"Destination: {self.destination}")
        print(f"Files recorded: {len(self.entries)}")
        print(f"Oversized files not copied: {len(self.skipped)}")
        for item in self.skipped:
            print(f"OVERSIZED {item['bytes']} bytes: {item['source_relative']}")
        print("Source files were copied; none were deleted or modified.")
        return 2 if self.skipped else 0


def verify_existing(repo_root: Path) -> int:
    bundle = repo_root.resolve() / DEST_REL
    manifest_path = bundle / "import_manifest.json"
    if not manifest_path.is_file():
        print("No import_manifest.json yet; repository scaffold only.")
        return 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for entry in manifest.get("files", []):
        target = bundle / entry["destination_relative"]
        if not target.is_file():
            errors.append(f"missing: {entry['destination_relative']}")
            continue
        if sha256_file(target) != entry["stored_sha256"]:
            errors.append(f"hash mismatch: {entry['destination_relative']}")
    sums_path = bundle / "SHA256SUMS.txt"
    if sums_path.is_file():
        for line_number, line in enumerate(sums_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                expected_hash, relative_path = line.split("  ", 1)
            except ValueError:
                errors.append(f"malformed SHA256SUMS.txt line {line_number}")
                continue
            target = bundle / relative_path
            if not target.is_file():
                errors.append(f"checksum target missing: {relative_path}")
            elif sha256_file(target) != expected_hash:
                errors.append(f"checksum mismatch: {relative_path}")
    else:
        errors.append("missing SHA256SUMS.txt")
    for symbol, expected in SYMBOLS.items():
        identity_path = bundle / symbol / "identity.json"
        if identity_path.is_file():
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            if identity.get("primary_insCode") != expected["primary_inscode"]:
                errors.append(f"{symbol}: wrong primary InsCode in identity.json")
    if errors:
        print("INTEGRITY CHECK FAILED")
        for error in errors:
            print(error)
        return 1
    print(
        f"Integrity OK: {len(manifest.get('files', []))} manifest entries; "
        f"{len(manifest.get('skipped', []))} source files still oversized/unimported."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--source-root", type=Path,
        default=Path.home() / "marketsage-data" / "tsetmc-three-adjusted",
    )
    parser.add_argument(
        "--acceptance-review-root", type=Path,
        default=Path.home() / "marketsage-data" / "acceptance-review" / "20261023T193750Z",
    )
    parser.add_argument("--max-file-mib", type=int, default=95)
    parser.add_argument("--confirm-public-repo", action="store_true")
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()

    if args.verify_existing:
        return verify_existing(args.repo_root)
    if not args.confirm_public_repo:
        parser.error(
            "This repository is public. Review redistribution/privacy and rerun with "
            "--confirm-public-repo only after approving the selected evidence for public commit."
        )
    importer = Importer(
        args.source_root,
        args.acceptance_review_root,
        args.repo_root,
        args.max_file_mib * 1024 * 1024,
    )
    return importer.run()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
