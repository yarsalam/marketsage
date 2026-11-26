"""Fail-closed evidence gate with decision-chain, evidence and legal-date validation."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Tuple
from .contracts import (
    ApprovedPriceFactor, ApprovedVolumeFactor, CorporateActionEvent,
    DecisionDimension, DecisionOutcome, DecisionRecord, EvidenceReference,
    EventDateKind, SourceKind, SourceObservation,
)

@dataclass(frozen=True, slots=True)
class GateResult:
    approved: bool
    subject_id: str
    dimension: DecisionDimension
    reasons: Tuple[str, ...]
    factor: Decimal | None = None
    decision_id: str | None = None
    approved_output: ApprovedPriceFactor | ApprovedVolumeFactor | None = None

class EvidenceGate:
    """Approves only fully evidenced, uniquely resolved decisions for one observation."""
    COMMON = (
        DecisionDimension.EVENT_CLASSIFICATION,
        DecisionDimension.SOURCE_LINK,
        DecisionDimension.LEGAL_DATE_MAPPING,
        DecisionDimension.EVIDENCE_QUALITY,
    )
    POLICY_VERSION = "v7.1"

    @staticmethod
    def _decision_index(records):
        index = {}
        duplicates = set()
        for record in records:
            if not isinstance(record, DecisionRecord):
                raise TypeError("records must contain DecisionRecord values")
            if record.decision_id in index:
                duplicates.add(record.decision_id)
            index[record.decision_id] = record
        return index, duplicates

    @classmethod
    def _active(cls, records, subject, dimension):
        """Return active decisions only after validating the complete local supersession graph."""
        selected = [r for r in records if r.subject_id == subject and r.dimension is dimension]
        index, duplicates = cls._decision_index(records)
        errors = []
        if duplicates:
            errors.append("DUPLICATE_DECISION_IDS")
        selected_ids = {r.decision_id for r in selected}
        superseded = set()
        successor_count = {}
        graph = {}
        for record in selected:
            graph[record.decision_id] = []
            for target_id in record.supersedes:
                target = index.get(target_id)
                if target is None:
                    errors.append(f"UNKNOWN_SUPERSESSION_TARGET:{target_id}")
                    continue
                if target.subject_id != subject or target.dimension is not dimension:
                    errors.append(f"CROSS_SUBJECT_OR_DIMENSION_SUPERSESSION:{target_id}")
                    continue
                if target_id == record.decision_id:
                    errors.append("SELF_SUPERSESSION")
                    continue
                if record.outcome is not DecisionOutcome.MANUALLY_VERIFIED:
                    errors.append(f"UNVERIFIED_DECISION_SUPERSEDES:{record.decision_id}")
                    continue
                graph[record.decision_id].append(target_id)
                superseded.add(target_id)
                successor_count[target_id] = successor_count.get(target_id, 0) + 1
        if any(count > 1 for count in successor_count.values()):
            errors.append("SUPERSESSION_FORK")
        visiting, visited = set(), set()
        def visit(node):
            if node in visiting:
                errors.append("SUPERSESSION_CYCLE")
                return
            if node in visited:
                return
            visiting.add(node)
            for target in graph.get(node, ()):
                if target in selected_ids:
                    visit(target)
            visiting.remove(node)
            visited.add(node)
        for node in graph:
            visit(node)
        active = [r for r in selected if r.decision_id not in superseded]
        return active, tuple(dict.fromkeys(errors))

    def _check(self, records, subject, dimension, evidence_by_id):
        active, integrity_errors = self._active(records, subject, dimension)
        errors = list(integrity_errors)
        if not active:
            errors.append(f"MISSING_DECISION:{dimension.value}")
            return None, errors
        if len(active) != 1:
            errors.append(f"AMBIGUOUS_ACTIVE_DECISIONS:{dimension.value}")
            return None, errors
        record = active[0]
        if record.outcome is not DecisionOutcome.MANUALLY_VERIFIED:
            errors.append(f"NOT_MANUALLY_VERIFIED:{dimension.value}:{record.outcome.value}")
            return None, errors
        if not record.evidence_ids:
            errors.append(f"MISSING_EVIDENCE:{dimension.value}")
        missing = [ref for ref in record.evidence_ids if ref not in evidence_by_id]
        if missing:
            errors.append(f"UNRESOLVED_EVIDENCE_REFERENCES:{dimension.value}")
        return (record if not errors else None), errors

    @staticmethod
    def _effective_date(event, decision, evidence_by_id, reasons):
        dates = [d for d in event.typed_dates if d.kind is EventDateKind.FIRST_AFFECTED_SESSION]
        if len(dates) != 1:
            reasons.append("REQUIRES_EXACTLY_ONE_FIRST_AFFECTED_SESSION_DATE")
            return None
        typed = dates[0]
        payload = decision.payload
        expected = {
            "date_kind": EventDateKind.FIRST_AFFECTED_SESSION.value,
            "effective_date": typed.value.isoformat(),
        }
        if payload.get("date_kind") != expected["date_kind"] or payload.get("effective_date") != expected["effective_date"]:
            reasons.append("LEGAL_DATE_DECISION_DOES_NOT_MATCH_TYPED_EVENT_DATE")
        if not set(typed.evidence_ids).issubset(set(decision.evidence_ids)):
            reasons.append("LEGAL_DATE_DECISION_MISSING_TYPED_DATE_EVIDENCE")
        if any(ref not in evidence_by_id for ref in typed.evidence_ids):
            reasons.append("UNRESOLVED_TYPED_DATE_EVIDENCE")
        return typed.value

    @staticmethod
    def _validate_decision_payloads(accepted, event, observation, reasons):
        classification = accepted.get(DecisionDimension.EVENT_CLASSIFICATION)
        if classification and classification.payload.get("event_type") != event.event_type:
            reasons.append("EVENT_CLASSIFICATION_PAYLOAD_MISMATCH")
        source_link = accepted.get(DecisionDimension.SOURCE_LINK)
        if source_link:
            if source_link.payload.get("event_id") != event.event_id or source_link.payload.get("observation_id") != observation.observation_id:
                reasons.append("SOURCE_LINK_PAYLOAD_MISMATCH")
        quality = accepted.get(DecisionDimension.EVIDENCE_QUALITY)
        if quality:
            if quality.payload.get("quality_status") != "ACCEPTED" or quality.payload.get("quarantined", False) is not False:
                reasons.append("EVIDENCE_QUALITY_NOT_ACCEPTED")

    def approve_price_factor(self, event, observation, records, evidence_refs=()):
        return self._approve(event, observation, records, evidence_refs, SourceKind.PA,
                             DecisionDimension.PRICE_FACTOR, ApprovedPriceFactor)

    def approve_volume_factor(self, event, observation, records, evidence_refs=()):
        return self._approve(event, observation, records, evidence_refs, SourceKind.SC,
                             DecisionDimension.VOLUME_FACTOR, ApprovedVolumeFactor)

    def _approve(self, event: CorporateActionEvent, observation: SourceObservation,
                 records: Iterable[DecisionRecord], evidence_refs: Iterable[EvidenceReference],
                 source_kind: SourceKind, factor_dimension: DecisionDimension, output_type):
        records, evidence_refs = tuple(records), tuple(evidence_refs)
        reasons = []
        if not isinstance(event, CorporateActionEvent) or not isinstance(observation, SourceObservation):
            return GateResult(False, getattr(event, "event_id", ""), factor_dimension, ("INVALID_EVENT_OR_OBSERVATION_TYPE",))
        evidence_by_id = {}
        for evidence in evidence_refs:
            if not isinstance(evidence, EvidenceReference):
                reasons.append("INVALID_EVIDENCE_REFERENCE_TYPE")
                continue
            if evidence.evidence_id in evidence_by_id:
                reasons.append(f"DUPLICATE_EVIDENCE_ID:{evidence.evidence_id}")
            evidence_by_id[evidence.evidence_id] = evidence
        if observation.source_kind is not source_kind:
            reasons.append(f"WRONG_SOURCE_KIND:EXPECTED_{source_kind.value}")
        if observation.observation_id not in event.source_observation_ids:
            reasons.append("OBSERVATION_NOT_LINKED_TO_EVENT")
        if observation.instrument != event.instrument:
            reasons.append("INSTRUMENT_IDENTITY_MISMATCH")

        accepted = {}
        for dimension in (*self.COMMON, factor_dimension):
            decision, errors = self._check(records, event.event_id, dimension, evidence_by_id)
            reasons.extend(errors)
            if decision is not None:
                accepted[dimension] = decision

        self._validate_decision_payloads(accepted, event, observation, reasons)
        effective_date = None
        date_decision = accepted.get(DecisionDimension.LEGAL_DATE_MAPPING)
        if date_decision:
            effective_date = self._effective_date(event, date_decision, evidence_by_id, reasons)

        factor_decision = accepted.get(factor_dimension)
        factor = None
        if factor_decision is not None:
            try:
                factor = Decimal(str(factor_decision.payload["factor"]))
                if not factor.is_finite() or factor <= 0:
                    raise ValueError
            except (KeyError, InvalidOperation, TypeError, ValueError):
                reasons.append(f"INVALID_OR_MISSING_FACTOR:{factor_dimension.value}")
                factor = None

        if reasons or factor_decision is None or factor is None or effective_date is None:
            return GateResult(False, event.event_id, factor_dimension, tuple(dict.fromkeys(reasons)))
        evidence_ids = set()
        for dimension in (*self.COMMON, factor_dimension):
            evidence_ids.update(accepted[dimension].evidence_ids)
        evidence_hashes = tuple(sorted({evidence_by_id[eid].sha256 for eid in evidence_ids}))
        output = output_type(
            event.event_id, factor, factor_decision.decision_id, event.instrument.identity_hash,
            observation.observation_id, effective_date, evidence_hashes, self.POLICY_VERSION,
        )
        return GateResult(True, event.event_id, factor_dimension, (), output.factor,
                          output.decision_id, output)
