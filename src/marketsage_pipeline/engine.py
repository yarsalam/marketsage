from __future__ import annotations

import hashlib
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Protocol


class Status(str, Enum):
    ACQUIRED = "ACQUIRED"
    SCHEMA_VALIDATED = "SCHEMA_VALIDATED"
    ADJUSTMENT_NOT_REQUIRED = "ADJUSTMENT_NOT_REQUIRED"
    ADJUSTED_VERIFIED = "ADJUSTED_VERIFIED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SOURCE_FAILED = "SOURCE_FAILED"
    VALIDATION_FAILED = "VALIDATION_FAILED"


class AdjustmentState(str, Enum):
    VENDOR_ADJUSTED_CONFIRMED = "VENDOR_ADJUSTED_CONFIRMED"
    UNADJUSTED_CONFIRMED = "UNADJUSTED_CONFIRMED"
    MIXED_OR_PARTIAL = "MIXED_OR_PARTIAL"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Asset:
    asset_id: str
    asset_class: str
    source_id: str
    source_symbol: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RawPayload:
    body: bytes
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedData:
    rows: list[dict[str, Any]]
    schema: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjustmentAssessment:
    state: AdjustmentState
    evidence: list[str]
    event_coverage_complete: bool = False
    adjustment_type: str | None = None


@dataclass
class AssetResult:
    asset_id: str
    asset_class: str
    source_id: str
    status: Status
    raw_sha256: str | None = None
    normalized_sha256: str | None = None
    adjusted_sha256: str | None = None
    adjustment_state: str | None = None
    adjustment_type: str | None = None
    evidence: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    reused_raw: bool = False


class SourceAdapter(Protocol):
    def request_fingerprint(self, asset: Asset) -> str: ...
    def fetch_history(self, asset: Asset) -> RawPayload: ...
    def normalize(self, asset: Asset, payload: RawPayload) -> NormalizedData: ...
    def assess_adjustment(
        self, asset: Asset, payload: RawPayload, data: NormalizedData
    ) -> AdjustmentAssessment: ...
    def fetch_events(self, asset: Asset) -> list[dict[str, Any]]: ...
    def apply_adjustment(
        self, asset: Asset, data: NormalizedData, events: list[dict[str, Any]]
    ) -> NormalizedData: ...
    def validate(self, asset: Asset, data: NormalizedData) -> list[str]: ...


def _safe(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    if not value:
        raise ValueError("empty or unsafe path component")
    return value[:120]


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        default=str
    ).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_once(path: Path, content: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = _sha(content)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        existing = path.read_bytes()
        if _sha(existing) != digest:
            raise RuntimeError(f"IMMUTABLE_CONFLICT: {path}")
        return digest
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return digest


class BatchEngine:
    """Batch orchestrator. Source-specific logic remains inside adapters."""

    def __init__(
        self,
        root: str | Path,
        adapters: dict[str, SourceAdapter],
        max_workers: int = 4,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self.root = Path(root)
        self.adapters = adapters
        self.max_workers = max_workers

    def _raw_for(self, asset: Asset, adapter: SourceAdapter) -> tuple[RawPayload, str, bool]:
        request_key = adapter.request_fingerprint(asset)
        if not re.fullmatch(r"[a-f0-9]{64}", request_key):
            raise ValueError("adapter request_fingerprint must be a SHA-256 hex digest")

        index_path = self.root / "cache" / "requests" / f"{request_key}.json"
        if index_path.exists():
            record = json.loads(index_path.read_text("utf-8"))
            raw_path = self.root / record["raw_path"]
            body = raw_path.read_bytes()
            actual = _sha(body)
            if actual != record["raw_sha256"]:
                raise RuntimeError(f"RAW_HASH_MISMATCH: {raw_path}")
            return RawPayload(body, record.get("metadata", {})), actual, True

        payload = adapter.fetch_history(asset)
        digest = _sha(payload.body)
        rel = Path("raw") / _safe(asset.source_id) / _safe(asset.asset_id) / f"{digest}.bin"
        _write_once(self.root / rel, payload.body)
        record = {
            "request_fingerprint": request_key,
            "asset_id": asset.asset_id,
            "source_id": asset.source_id,
            "raw_path": rel.as_posix(),
            "raw_sha256": digest,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "metadata": payload.metadata,
        }
        _write_once(index_path, _json_bytes(record))
        return payload, digest, False

    def _process_one(self, asset: Asset) -> AssetResult:
        result = AssetResult(
            asset_id=asset.asset_id,
            asset_class=asset.asset_class,
            source_id=asset.source_id,
            status=Status.SOURCE_FAILED,
        )
        adapter = self.adapters.get(asset.source_id)
        if adapter is None:
            result.errors.append(f"NO_ADAPTER_REGISTERED: {asset.source_id}")
            return result

        try:
            payload, raw_hash, reused = self._raw_for(asset, adapter)
            result.raw_sha256 = raw_hash
            result.reused_raw = reused
            result.status = Status.ACQUIRED

            data = adapter.normalize(asset, payload)
            result.normalized_sha256 = _write_once(
                self.root / "normalized" / _safe(asset.asset_id) /
                f"{_sha(_json_bytes(data.rows))}.json",
                _json_bytes({"schema": data.schema, "rows": data.rows}),
            )
            errors = adapter.validate(asset, data)
            if errors:
                result.status = Status.VALIDATION_FAILED
                result.errors.extend(errors)
                return result
            result.status = Status.SCHEMA_VALIDATED

            assessment = adapter.assess_adjustment(asset, payload, data)
            result.adjustment_state = assessment.state.value
            result.adjustment_type = assessment.adjustment_type
            result.evidence.extend(assessment.evidence)

            if assessment.state == AdjustmentState.VENDOR_ADJUSTED_CONFIRMED:
                result.status = Status.ADJUSTMENT_NOT_REQUIRED
                return result

            if assessment.state != AdjustmentState.UNADJUSTED_CONFIRMED:
                result.status = Status.REVIEW_REQUIRED
                result.errors.append("ADJUSTMENT_STATUS_NOT_PROVEN")
                return result

            events = adapter.fetch_events(asset)
            if not assessment.event_coverage_complete:
                result.status = Status.REVIEW_REQUIRED
                result.errors.append("EVENT_COVERAGE_INCOMPLETE")
                return result

            if not events:
                result.status = Status.ADJUSTMENT_NOT_REQUIRED
                result.evidence.append("No applicable events found in complete event coverage.")
                return result

            adjusted = adapter.apply_adjustment(asset, data, events)
            adjusted_errors = adapter.validate(asset, adjusted)
            if adjusted_errors:
                result.status = Status.VALIDATION_FAILED
                result.errors.extend([f"ADJUSTED_OUTPUT: {e}" for e in adjusted_errors])
                return result

            adjusted_bytes = _json_bytes({
                "schema": adjusted.schema,
                "rows": adjusted.rows,
                "raw_sha256": raw_hash,
                "adjustment_type": assessment.adjustment_type,
                "events": events,
            })
            result.adjusted_sha256 = _write_once(
                self.root / "adjusted" / _safe(asset.asset_id) /
                f"{_sha(adjusted_bytes)}.json",
                adjusted_bytes,
            )
            result.status = Status.ADJUSTED_VERIFIED
            return result

        except Exception as exc:
            result.status = Status.SOURCE_FAILED
            result.errors.append(f"{type(exc).__name__}: {exc}")
            return result

    def run(self, assets: list[Asset], run_id: str) -> dict[str, Any]:
        run_id = _safe(run_id)
        results: list[AssetResult] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = {pool.submit(self._process_one, asset): asset for asset in assets}
            for future in as_completed(futures):
                results.append(future.result())

        results.sort(key=lambda item: item.asset_id)
        counts = {status.value: 0 for status in Status}
        for item in results:
            counts[item.status.value] += 1

        report = {
            "run_id": run_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "asset_count": len(assets),
            "status_counts": counts,
            "results": [
                {
                    **asdict(item),
                    "status": item.status.value,
                }
                for item in results
            ],
        }
        _write_once(
            self.root / "runs" / run_id / "summary.json",
            _json_bytes(report),
        )
        return report
