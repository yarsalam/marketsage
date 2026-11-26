"""Fail-closed gate; raw PA/SC values are never accepted as authority."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable, Tuple
from .contracts import (ApprovedPriceFactor, ApprovedVolumeFactor, CorporateActionEvent,
    DecisionDimension, DecisionOutcome, DecisionRecord, EvidenceReference, SourceKind, SourceObservation)

@dataclass(frozen=True, slots=True)
class GateResult:
    approved: bool
    subject_id: str
    dimension: DecisionDimension
    reasons: Tuple[str,...]
    factor: Decimal | None = None
    decision_id: str | None = None

class EvidenceGate:
    COMMON=(DecisionDimension.EVENT_CLASSIFICATION,DecisionDimension.SOURCE_LINK,
            DecisionDimension.LEGAL_DATE_MAPPING,DecisionDimension.EVIDENCE_QUALITY)

    @staticmethod
    def _active(records: Iterable[DecisionRecord], subject: str, dimension: DecisionDimension):
        selected=[r for r in records if r.subject_id==subject and r.dimension is dimension]
        superseded={target for r in selected for target in r.supersedes}
        return [r for r in selected if r.decision_id not in superseded]

    def _check(self, records, subject, dimension):
        active=self._active(records,subject,dimension)
        if not active: return None,[f"MISSING_DECISION:{dimension.value}"]
        if len(active)!=1: return None,[f"AMBIGUOUS_ACTIVE_DECISIONS:{dimension.value}"]
        record=active[0]
        if record.outcome is not DecisionOutcome.MANUALLY_VERIFIED:
            return None,[f"NOT_MANUALLY_VERIFIED:{dimension.value}:{record.outcome.value}"]
        if not record.evidence_ids: return None,[f"MISSING_EVIDENCE:{dimension.value}"]
        return record,[]

    def approve_price_factor(self,event,observation,records,evidence_refs=()):
        return self._approve(event,observation,records,evidence_refs,SourceKind.PA,DecisionDimension.PRICE_FACTOR,ApprovedPriceFactor)

    def approve_volume_factor(self,event,observation,records,evidence_refs=()):
        return self._approve(event,observation,records,evidence_refs,SourceKind.SC,DecisionDimension.VOLUME_FACTOR,ApprovedVolumeFactor)

    def _approve(self,event: CorporateActionEvent,observation: SourceObservation,records,evidence_refs,
                 source_kind: SourceKind,factor_dimension: DecisionDimension,output_type):
        records=tuple(records); evidence_by_id={e.evidence_id:e for e in evidence_refs}; reasons=[]
        if observation.source_kind is not source_kind: reasons.append(f"WRONG_SOURCE_KIND:EXPECTED_{source_kind.value}")
        if observation.observation_id not in event.source_observation_ids: reasons.append("OBSERVATION_NOT_LINKED_TO_EVENT")
        if observation.instrument!=event.instrument: reasons.append("INSTRUMENT_IDENTITY_MISMATCH")
        accepted={}
        for dimension in (*self.COMMON,factor_dimension):
            decision,errors=self._check(records,event.event_id,dimension)
            reasons.extend(errors)
            if decision is not None:
                missing_refs=[ref for ref in decision.evidence_ids if ref not in evidence_by_id]
                if missing_refs:
                    reasons.append(f"UNRESOLVED_EVIDENCE_REFERENCES:{dimension.value}")
                else:
                    accepted[dimension]=decision
        factor_decision=accepted.get(factor_dimension); factor=None
        if factor_decision is not None:
            try:
                factor=Decimal(str(factor_decision.payload["factor"]))
                if not factor.is_finite() or factor<=0: raise ValueError
            except (KeyError,InvalidOperation,TypeError,ValueError):
                reasons.append(f"INVALID_OR_MISSING_FACTOR:{factor_dimension.value}"); factor=None
        if reasons or factor_decision is None or factor is None:
            return GateResult(False,event.event_id,factor_dimension,tuple(reasons))
        # Constructing the typed output enforces positive finite factor and instrument provenance.
        output=output_type(event.event_id,factor,factor_decision.decision_id,event.instrument.identity_hash)
        return GateResult(True,event.event_id,factor_dimension,(),output.factor,output.decision_id)
