#!/usr/bin/env python3
"""Coordinate the existing CODAL/TSETMC collectors and adjustment engine. No formulas live here."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

SCHEMA = 1
VOLATILE = {"manifest.json", "run_manifest.json", "summary.json", "download_report.json",
            "status.json", "run.json"}


class PipelineError(RuntimeError):
    pass


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_run_id() -> str:
    return datetime.now(ZoneInfo("Asia/Tehran")).strftime("%Y%m%d")


def safe_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", value):
        raise PipelineError(f"Unsafe run id or symbol slug: {value!r}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(root: Path) -> dict:
    if not root.is_dir():
        raise PipelineError(f"Missing collector output: {root}")
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise PipelineError(f"Symlink found in immutable capture: {path}")
        if not path.is_file():
            continue
        name = path.name.lower()
        if name in VOLATILE or name.endswith((".lock", ".log", ".tmp", ".part")):
            continue
        if "manifest" in name and name.endswith(".json"):
            continue
        if "transport" in name and name.endswith(".json"):
            continue
        rel = path.relative_to(root).as_posix()
        files[rel] = {"sha256": sha256(path), "size": path.stat().st_size}
    if not files:
        raise PipelineError(f"No payload files found under {root}")
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return {"sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "file_count": len(files), "files": files}


def file_diff(old: dict | None, new: dict) -> dict:
    a = (old or {}).get("files", {})
    b = new.get("files", {})
    return {
        "added": sorted(set(b) - set(a)),
        "removed": sorted(set(a) - set(b)),
        "modified": sorted(k for k in set(a) & set(b) if a[k]["sha256"] != b[k]["sha256"]),
    }


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    os.replace(tmp, path)


def append_event(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


@contextmanager
def run_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PipelineError(f"Orchestrator lock exists: {path}. Verify no run is active.") from exc
    try:
        os.write(fd, f"pid={os.getpid()} at={now()}\n".encode())
        os.fsync(fd)
        yield
    finally:
        os.close(fd)
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def read_config(path: Path) -> dict:
    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Cannot read config: {exc}") from exc
    if cfg.get("schema_version") != SCHEMA or not cfg.get("symbols"):
        raise PipelineError("Invalid config schema or empty symbol list")
    slugs = set()
    for symbol in cfg["symbols"]:
        if any(not str(symbol.get(k, "")).strip() for k in ("symbol", "slug", "ins_code")):
            raise PipelineError("Each symbol needs symbol, slug and ins_code")
        safe_id(symbol["slug"])
        if symbol["slug"] in slugs:
            raise PipelineError(f"Duplicate symbol slug: {symbol['slug']}")
        slugs.add(symbol["slug"])
    for name in ("codal", "tsetmc"):
        if not cfg.get("collectors", {}).get(name, {}).get("argv"):
            raise PipelineError(f"collectors.{name}.argv is required")
    return cfg


def render(argv: list[str], ctx: dict) -> list[str]:
    try:
        return [str(part).format_map(ctx) for part in argv]
    except KeyError as exc:
        raise PipelineError(f"Unknown command placeholder: {exc.args[0]}") from exc


def execute(argv: list[str], cwd: Path, timeout: int, dry: bool = False) -> dict:
    if dry:
        return {"status": "DRY_RUN", "argv": argv}
    try:
        result = subprocess.run(argv, cwd=cwd, timeout=timeout, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "FAILED", "error": str(exc), "argv": argv}

    def tail(value: str) -> str:
        value = re.sub(r"(?i)(token|password|secret|authorization)(\s*[:=]\s*)[^\s,;]+",
                       r"\1\2[REDACTED]", value or "")
        return value[-1200:]

    return {"status": "SUCCEEDED" if result.returncode == 0 else "FAILED",
            "exit_code": result.returncode, "argv": argv,
            "stdout_tail": tail(result.stdout), "stderr_tail": tail(result.stderr)}


def run_stage(manifest: dict, name: str, argv: list[str], output: Path, root: Path,
              manifest_path: Path, history: Path, timeout: int, resume_safe: bool,
              resume: bool, dry: bool) -> None:
    previous = manifest.setdefault("stages", {}).get(name)
    if previous and previous.get("status") == "SUCCEEDED":
        if not output.is_dir():
            raise PipelineError(f"{name} stage says SUCCEEDED but output is missing")
        if not (resume and resume_safe):
            return
    if output.exists() and not resume_safe and not dry:
        raise PipelineError(f"{name} output exists but is incomplete; use a new run id")
    if not dry:
        output.parent.mkdir(parents=True, exist_ok=True)
        manifest["stages"][name] = {"status": "STARTED", "started_at": now(),
                                    "output_dir": str(output)}
        atomic_json(manifest_path, manifest)
        append_event(history, {"at": now(), "run_id": manifest["run_id"],
                               "stage": name, "state": "STARTED"})
    result = execute(argv, root, timeout, dry)
    if dry:
        manifest["stages"][name] = result
        return
    manifest["stages"][name].update(result)
    atomic_json(manifest_path, manifest)
    append_event(history, {"at": now(), "run_id": manifest["run_id"],
                           "stage": name, "state": result["status"]})
    if result["status"] != "SUCCEEDED":
        manifest.update({"state": "FAILED", "failed_stage": name, "completed_at": now()})
        atomic_json(manifest_path, manifest)
        raise PipelineError(f"{name} collector failed: {result.get('stderr_tail', result.get('error', ''))}")
    if not output.is_dir():
        raise PipelineError(f"{name} reported success but did not create {output}")


def latest_approval(path: Path) -> dict:
    if not path.is_file():
        return {}
    last = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PipelineError(f"Invalid review approval line {number}: {exc}") from exc
        if not item.get("reviewer") or not item.get("reviewed_at"):
            raise PipelineError(f"Review approval line {number} needs reviewer and reviewed_at")
        last = item
    return last


def json_records(path: Path, array_path: str, key_field: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PipelineError(f"Cannot parse record source {path}: {exc}") from exc
    for part in array_path.split(".") if array_path else []:
        if not isinstance(value, dict) or part not in value:
            raise PipelineError(f"JSON path {array_path!r} missing in {path}")
        value = value[part]
    if not isinstance(value, list):
        raise PipelineError(f"JSON path {array_path!r} is not an array in {path}")
    indexed = {}
    for row in value:
        if not isinstance(row, dict) or row.get(key_field) in (None, ""):
            raise PipelineError(f"Record is missing key {key_field!r} in {path}")
        key = str(row[key_field])
        if key in indexed:
            raise PipelineError(f"Duplicate {key_field}={key!r} in {path}")
        indexed[key] = row
    return indexed


def compare_records(old_path: Path | None, new_path: Path, rule: dict) -> dict:
    old = json_records(old_path, rule.get("array_path", ""), rule["key_field"]) if old_path else {}
    new = json_records(new_path, rule.get("array_path", ""), rule["key_field"])
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    modified = []
    for key in sorted(set(old) & set(new)):
        fields = sorted(set(old[key]) | set(new[key]))
        changed = [field for field in fields if old[key].get(field) != new[key].get(field)]
        if changed:
            modified.append({"key": key, "changed_fields": changed})
    return {"old_records": len(old), "new_records": len(new),
            "added": added, "removed": removed, "modified": modified}


def previous_run(run_root: Path, current_id: str) -> dict:
    candidates = []
    for path in run_root.glob("*/run_manifest.json"):
        if path.parent.name == current_id:
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if item.get("source_fingerprints") and item.get("state") != "RUNNING":
            candidates.append(item)
    return max(candidates, key=lambda x: x.get("completed_at", x.get("created_at", ""))) if candidates else {}


def run(config_path: Path, run_id: str | None = None, resume: bool = False,
        dry_run: bool = False) -> dict:
    config_path = config_path.resolve()
    cfg = read_config(config_path)
    run_id = safe_id(run_id or default_run_id())
    root_value = Path(cfg.get("repo_root", "."))
    root = (config_path.parent / root_value).resolve() if not root_value.is_absolute() else root_value
    evidence_value = Path(cfg.get("evidence_root", "data/market-research/iran-equities/adjustment-evidence"))
    evidence = (root / evidence_value).resolve() if not evidence_value.is_absolute() else evidence_value
    run_root_value = Path(cfg.get("run_root", evidence / "_shared/orchestrator/runs"))
    run_root = (root / run_root_value).resolve() if not run_root_value.is_absolute() else run_root_value
    run_dir = run_root / run_id
    manifest_path = run_dir / "run_manifest.json"
    history = run_root / "history.jsonl"

    if manifest_path.exists() and not resume:
        raise PipelineError(f"Run {run_id} already exists; use --resume or choose a new id")
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("state") == "COMPLETED":
            return manifest
    else:
        manifest = {"schema_version": SCHEMA, "run_id": run_id, "created_at": now(), "stages": {}}

    if dry_run:
        lock_context = _no_lock()
    else:
        run_dir.mkdir(parents=True, exist_ok=True)
        lock_context = run_lock(run_root / ".orchestrator.lock")

    with lock_context:
        manifest["state"] = "RUNNING"
        if not dry_run:
            atomic_json(manifest_path, manifest)
            append_event(history, {"at": now(), "run_id": run_id, "state": "RUNNING"})
        timeout = int(cfg.get("timeout_seconds", 7200))
        symbols = cfg["symbols"]
        collectors = cfg["collectors"]
        codal_output = run_dir / "sources" / "codal"
        codal = collectors["codal"]
        symbols_file = (root / codal.get("symbols_file", "")).resolve()
        common = {"repo_root": str(root), "run_id": run_id, "run_dir": str(run_dir),
                  "output_dir": str(codal_output), "symbols_file": str(symbols_file)}
        run_stage(manifest, "codal", render(codal["argv"], common), codal_output, root,
                  manifest_path, history, int(codal.get("timeout_seconds", timeout)),
                  bool(codal.get("resume_safe", True)), resume, dry_run)

        source_dirs = {"codal": str(codal_output)}
        for symbol in symbols:
            slug = safe_id(symbol["slug"])
            output = run_dir / "sources" / "tsetmc" / slug
            tsetmc = collectors["tsetmc"]
            ctx = {**common, "output_dir": str(output), "symbol": symbol["symbol"],
                   "slug": slug, "ins_code": symbol["ins_code"],
                   "symbol_dir": str(evidence / slug)}
            run_stage(manifest, f"tsetmc:{slug}", render(tsetmc["argv"], ctx), output, root,
                      manifest_path, history, int(tsetmc.get("timeout_seconds", timeout)),
                      bool(tsetmc.get("resume_safe", False)), resume, dry_run)
            source_dirs[f"tsetmc:{slug}"] = str(output)

        if dry_run:
            manifest["state"] = "DRY_RUN"
            return manifest

        sources = {key: fingerprint(Path(directory)) for key, directory in source_dirs.items()}
        previous = previous_run(run_root, run_id)
        old_sources = previous.get("source_fingerprints", {})
        source_changes = {key: file_diff(old_sources.get(key), value)
                          for key, value in sources.items()}

        record_changes = {}
        for rule in cfg.get("record_comparison", []):
            for symbol in symbols:
                key = rule["source_key"].format(**symbol)
                new_matches = sorted(Path(source_dirs[key]).rglob(rule["glob"]))
                if len(new_matches) != 1:
                    raise PipelineError(f"Expected one {rule['glob']!r} under {source_dirs[key]}, found {len(new_matches)}")
                old_matches = []
                old_dir = previous.get("source_directories", {}).get(key)
                if old_dir and Path(old_dir).is_dir():
                    old_matches = sorted(Path(old_dir).rglob(rule["glob"]))
                if len(old_matches) > 1:
                    raise PipelineError(f"Multiple prior files match {rule['glob']!r} under {old_dir}")
                record_changes[f"{key}:{new_matches[0].name}"] = compare_records(
                    old_matches[0] if old_matches else None, new_matches[0], rule)

        adjustment_inputs = {}
        for symbol in symbols:
            for template in cfg.get("adjustment_input_files", ["{slug}/event-ledger.csv"]):
                rel = template.format(**symbol)
                path = evidence / rel
                adjustment_inputs[f"{symbol['slug']}:{Path(rel).name}"] = sha256(path) if path.is_file() else None
        old_inputs = previous.get("adjustment_input_fingerprints", {})
        input_changes = {key: {"old": old_inputs.get(key), "new": value}
                         for key, value in adjustment_inputs.items() if old_inputs.get(key) != value}

        identity_hashes = {}
        for symbol in symbols:
            slug = symbol["slug"]
            canonical = evidence / slug / "identity.json"
            captured_dir = Path(source_dirs[f"tsetmc:{slug}"])
            captured = sorted(captured_dir.rglob(cfg.get("identity_glob", "*identity*.json")))
            if not canonical.is_file() or len(captured) != 1:
                raise PipelineError(f"Identity mismatch: canonical={canonical.is_file()}, captured_matches={len(captured)} for {slug}")
            material = {"canonical": sha256(canonical), "captured": sha256(captured[0])}
            identity_hashes[slug] = hashlib.sha256(
                json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        old_identities = previous.get("identity_fingerprints", {})
        identity_changes = {slug: {"old": old_identities.get(slug), "new": value}
                            for slug, value in identity_hashes.items()
                            if old_identities.get(slug) != value}

        codal_hash = sources["codal"]["sha256"]
        approval_path = Path(cfg.get("review_approvals_file",
                                    evidence / "_shared/orchestrator/review_approvals.jsonl"))
        approval_path = (root / approval_path).resolve() if not approval_path.is_absolute() else approval_path
        approval = latest_approval(approval_path)
        codal_unapproved = approval.get("codal_snapshot_sha256") != codal_hash
        approved_ids = approval.get("identity_sha256", {})
        identity_unapproved = any(approved_ids.get(slug) != value
                                  for slug, value in identity_hashes.items())

        codal_changed = any(source_changes["codal"].values())
        tsetmc_changed = any(any(source_changes[key].values())
                             for key in source_changes if key.startswith("tsetmc:"))
        input_changed = bool(input_changes)
        identity_changed = bool(identity_changes)
        pending = bool(previous.get("change_plan", {}).get("recalculation_required")
                       and not previous.get("adjustment_completed", False))
        recalculate = codal_changed or tsetmc_changed or input_changed or identity_changed or pending
        blocked = codal_unapproved or identity_unapproved

        plan = {
            "codal_changed": codal_changed, "tsetmc_changed": tsetmc_changed,
            "adjustment_ledger_changed": input_changed, "identity_changed": identity_changed,
            "source_file_changes": source_changes, "daily_record_changes": record_changes,
            "adjustment_input_changes": input_changes, "identity_changes": identity_changes,
            "recalculation_required": recalculate, "previous_recalculation_pending": pending,
            "human_review_required": codal_changed or identity_changed or blocked,
            "review_acknowledged": not blocked, "recalculation_blocked_by_review": blocked,
        }
        manifest.update({"source_fingerprints": sources, "source_directories": source_dirs,
                         "adjustment_input_fingerprints": adjustment_inputs,
                         "identity_fingerprints": identity_hashes,
                         "review_approval_file": str(approval_path), "change_plan": plan})

        if blocked:
            manifest.update({"state": "BLOCKED_REVIEW_REQUIRED",
                             "blocked_reason": "Review the exact CODAL snapshot and instrument identity; append an owner acknowledgement. No adjustment was run.",
                             "completed_at": now()})
            atomic_json(manifest_path, manifest)
            append_event(history, {"at": now(), "run_id": run_id, "state": manifest["state"]})
            return manifest

        if recalculate:
            reconcile = cfg.get("reconcile", {})
            adjustment = cfg.get("adjustment", {})
            if not reconcile.get("argv") or not adjustment.get("argv"):
                manifest.update({"state": "BLOCKED_RECONCILIATION_NOT_CONFIGURED",
                                 "blocked_reason": "A tested immutable-snapshot reconciler and versioned adjustment command are required. No stale canonical input was used.",
                                 "completed_at": now()})
                atomic_json(manifest_path, manifest)
                append_event(history, {"at": now(), "run_id": run_id, "state": manifest["state"]})
                return manifest
            workspace = run_dir / "adjustment-input"
            output = run_dir / "adjustment-output"
            ctx = {**common, "evidence_root": str(evidence), "workspace_dir": str(workspace),
                   "output_dir": str(output), "manifest_path": str(manifest_path)}
            rec = execute(render(reconcile["argv"], ctx), root, int(reconcile.get("timeout_seconds", timeout)))
            manifest["stages"]["reconcile"] = rec
            if rec["status"] != "SUCCEEDED" or not workspace.is_dir():
                manifest.update({"state": "FAILED_RECONCILIATION", "completed_at": now()})
                atomic_json(manifest_path, manifest)
                raise PipelineError("Reconciler failed or did not create the isolated workspace")
            adj = execute(render(adjustment["argv"], ctx), root, int(adjustment.get("timeout_seconds", timeout)))
            manifest["stages"]["adjustment"] = adj
            if adj["status"] != "SUCCEEDED" or not output.is_dir():
                manifest.update({"state": "FAILED_ADJUSTMENT", "completed_at": now()})
                atomic_json(manifest_path, manifest)
                raise PipelineError("Adjustment failed or did not create versioned output")
            manifest["adjustment_output_fingerprint"] = fingerprint(output)

        manifest.update({"adjustment_completed": bool(recalculate), "state": "COMPLETED",
                         "completed_at": now()})
        atomic_json(manifest_path, manifest)
        append_event(history, {"at": now(), "run_id": run_id, "state": "COMPLETED",
                               "recalculation_required": recalculate})
        return manifest


@contextmanager
def _no_lock():
    yield


def status(run_root: Path, run_id: str | None = None) -> dict:
    if run_id:
        path = run_root / safe_id(run_id) / "run_manifest.json"
    else:
        manifests = list(run_root.glob("*/run_manifest.json"))
        if not manifests:
            raise PipelineError(f"No run manifests under {run_root}")
        path = max(manifests, key=lambda item: item.stat().st_mtime)
    if not path.is_file():
        raise PipelineError(f"Run manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--config", type=Path, required=True)
    run_parser.add_argument("--run-id")
    run_parser.add_argument("--resume", action="store_true")
    run_parser.add_argument("--dry-run", action="store_true")
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--run-root", type=Path, required=True)
    status_parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    try:
        result = (run(args.config, args.run_id, args.resume, args.dry_run)
                  if args.action == "run" else status(args.run_root, args.run_id))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 3 if result.get("state", "").startswith("BLOCKED_") else 0
    except PipelineError as exc:
        print(f"ORCHESTRATOR_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
