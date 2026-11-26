"""Immutable contracts for the MarketSage corporate-action evidence pipeline."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
import hashlib, json, re
from typing import Any, Mapping, Tuple

_SHA = re.compile(r"^[0-9a-f]{64}$")

def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()

def _hash(value: str, name: str = "sha256") -> str:
    value = _text(value, name).lower()
    if not _SHA.fullmatch(value):
        raise ValueError(f"{name} must be a 64-character SHA-256 hex digest")
    return value

def _decimal(value: Any, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{name} must be a finite decimal") from None
    if not result.is_finite():
        raise ValueError(f"{name} must be finite")
    return result

def canonical_json(value: Any) -> str:
    def default(obj: Any) -> Any:
        if isinstance(obj, Decimal): return format(obj, "f")
        if isinstance(obj, (date, datetime)): return obj.isoformat()
        if isinstance(obj, Enum): return obj.value
        if hasattr(obj, "to_dict"): return obj.to_dict()
        raise TypeError(f"Unsupported canonical JSON value: {type(obj).__name__}")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=default)

def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

class SourceKind(str, Enum):
    A0="A0"; PA="PA"; SC="SC"; LEDGER="LEDGER"; CODAL="CODAL"
    ISSUER_NOTICE="ISSUER_NOTICE"; PRESS_ARCHIVE="PRESS_ARCHIVE"; MANUAL="MANUAL"

class EventDateKind(str, Enum):
    PUBLICATION_DATE="PUBLICATION_DATE"; MEETING_DATE="MEETING_DATE"
    RECORD_DATE="RECORD_DATE"; EX_DATE="EX_DATE"; FIRST_AFFECTED_SESSION="FIRST_AFFECTED_SESSION"
    RIGHTS_START_DATE="RIGHTS_START_DATE"; RIGHTS_END_DATE="RIGHTS_END_DATE"
    SUBSCRIPTION_DEADLINE="SUBSCRIPTION_DEADLINE"; REGISTRATION_DATE="REGISTRATION_DATE"
    PAYMENT_DATE="PAYMENT_DATE"; PROVIDER_D_EVEN="PROVIDER_D_EVEN"

class DecisionDimension(str, Enum):
    EVENT_CLASSIFICATION="EVENT_CLASSIFICATION"; SOURCE_LINK="SOURCE_LINK"
    LEGAL_DATE_MAPPING="LEGAL_DATE_MAPPING"; PRICE_FACTOR="PRICE_FACTOR"
    VOLUME_FACTOR="VOLUME_FACTOR"; CASHFLOW="CASHFLOW"; EVIDENCE_QUALITY="EVIDENCE_QUALITY"

class DecisionOutcome(str, Enum):
    MANUALLY_VERIFIED="MANUALLY_VERIFIED"; REJECTED="REJECTED"; CONFLICT="CONFLICT"
    INSUFFICIENT_EVIDENCE="INSUFFICIENT_EVIDENCE"; QUARANTINED="QUARANTINED"

class EventRelationshipType(str, Enum):
    SAME_EVENT="SAME_EVENT"; COMPONENT_OF="COMPONENT_OF"; AMENDS="AMENDS"
    SUPERSEDES="SUPERSEDES"; REVERSES_OR_WITHDRAWS="REVERSES_OR_WITHDRAWS"
    ROUND_TRIP_OR_TEMPORARY="ROUND_TRIP_OR_TEMPORARY"; INDEPENDENT_EVENT="INDEPENDENT_EVENT"
    UNRELATED="UNRELATED"; UNRESOLVED="UNRESOLVED"

@dataclass(frozen=True, slots=True)
class InstrumentIdentity:
    symbol: str
    ins_code: str
    exchange: str = "TSE"
    currency: str = "IRR"
    def __post_init__(self):
        for n in ("symbol","exchange","currency"):
            object.__setattr__(self,n,_text(getattr(self,n),n))
        object.__setattr__(self,"ins_code",_text(str(self.ins_code),"ins_code"))
    @property
    def identity_hash(self):
        return canonical_hash({"symbol":self.symbol,"ins_code":self.ins_code,"exchange":self.exchange,"currency":self.currency})

@dataclass(frozen=True, slots=True)
class EvidenceReference:
    evidence_id: str
    source_kind: SourceKind
    locator: str
    sha256: str
    retrieved_at: datetime
    publisher: str = ""
    def __post_init__(self):
        object.__setattr__(self,"evidence_id",_text(self.evidence_id,"evidence_id"))
        object.__setattr__(self,"locator",_text(self.locator,"locator"))
        object.__setattr__(self,"sha256",_hash(self.sha256))
        if not isinstance(self.source_kind,SourceKind): object.__setattr__(self,"source_kind",SourceKind(self.source_kind))
        if not isinstance(self.retrieved_at,datetime) or self.retrieved_at.tzinfo is None:
            raise ValueError("retrieved_at must be timezone-aware")
        object.__setattr__(self,"publisher",self.publisher.strip())

@dataclass(frozen=True, slots=True)
class SourceObservation:
    observation_id: str
    source_kind: SourceKind
    instrument: InstrumentIdentity
    provider_date: date | None
    payload_sha256: str
    source_locator: str
    native_key: str = ""
    native_id_usable: bool = True
    def __post_init__(self):
        object.__setattr__(self,"observation_id",_text(self.observation_id,"observation_id"))
        object.__setattr__(self,"payload_sha256",_hash(self.payload_sha256,"payload_sha256"))
        object.__setattr__(self,"source_locator",_text(self.source_locator,"source_locator"))
        if not isinstance(self.source_kind,SourceKind): object.__setattr__(self,"source_kind",SourceKind(self.source_kind))
        if self.provider_date is not None and not isinstance(self.provider_date,date): raise ValueError("provider_date must be a date or None")
        object.__setattr__(self,"native_key",self.native_key.strip())

@dataclass(frozen=True, slots=True)
class TypedEventDate:
    value: date
    kind: EventDateKind
    evidence_ids: Tuple[str,...]
    notes: str = ""
    def __post_init__(self):
        if not isinstance(self.value,date): raise ValueError("value must be a date")
        if not isinstance(self.kind,EventDateKind): object.__setattr__(self,"kind",EventDateKind(self.kind))
        refs=tuple(_text(x,"evidence_id") for x in self.evidence_ids)
        if not refs: raise ValueError("typed event dates require evidence references")
        object.__setattr__(self,"evidence_ids",refs)

@dataclass(frozen=True, slots=True)
class EventRelationship:
    left_event_id: str
    right_event_id: str
    relationship: EventRelationshipType
    decision_id: str
    def __post_init__(self):
        for n in ("left_event_id","right_event_id","decision_id"): object.__setattr__(self,n,_text(getattr(self,n),n))
        if self.left_event_id==self.right_event_id: raise ValueError("event cannot relate to itself")
        if not isinstance(self.relationship,EventRelationshipType): object.__setattr__(self,"relationship",EventRelationshipType(self.relationship))

@dataclass(frozen=True, slots=True)
class CorporateActionEvent:
    event_id: str
    instrument: InstrumentIdentity
    event_type: str
    source_observation_ids: Tuple[str,...]
    typed_dates: Tuple[TypedEventDate,...] = field(default_factory=tuple)
    def __post_init__(self):
        object.__setattr__(self,"event_id",_text(self.event_id,"event_id"))
        object.__setattr__(self,"event_type",_text(self.event_type,"event_type").upper())
        object.__setattr__(self,"source_observation_ids",tuple(_text(x,"source_observation_id") for x in self.source_observation_ids))
        object.__setattr__(self,"typed_dates",tuple(self.typed_dates))
        if not self.source_observation_ids: raise ValueError("event must reference source observations")

@dataclass(frozen=True, slots=True)
class DecisionRecord:
    decision_id: str
    subject_id: str
    dimension: DecisionDimension
    outcome: DecisionOutcome
    actor: str
    rationale: str
    evidence_ids: Tuple[str,...]
    payload: Mapping[str,Any] = field(default_factory=dict)
    supersedes: Tuple[str,...] = field(default_factory=tuple)
    def __post_init__(self):
        for n in ("decision_id","subject_id","actor","rationale"): object.__setattr__(self,n,_text(getattr(self,n),n))
        if not isinstance(self.dimension,DecisionDimension): object.__setattr__(self,"dimension",DecisionDimension(self.dimension))
        if not isinstance(self.outcome,DecisionOutcome): object.__setattr__(self,"outcome",DecisionOutcome(self.outcome))
        object.__setattr__(self,"evidence_ids",tuple(_text(x,"evidence_id") for x in self.evidence_ids))
        object.__setattr__(self,"supersedes",tuple(_text(x,"supersedes") for x in self.supersedes))
        if self.outcome is DecisionOutcome.MANUALLY_VERIFIED and not self.evidence_ids:
            raise ValueError("MANUALLY_VERIFIED decisions require evidence_ids")
        if not isinstance(self.payload,Mapping): raise ValueError("payload must be a mapping")
        object.__setattr__(self,"payload",dict(self.payload))

@dataclass(frozen=True, slots=True)
class ApprovedPriceFactor:
    event_id: str
    factor: Decimal
    decision_id: str
    instrument_hash: str
    def __post_init__(self):
        object.__setattr__(self,"event_id",_text(self.event_id,"event_id"))
        object.__setattr__(self,"factor",_decimal(self.factor,"factor"))
        if self.factor<=0: raise ValueError("price factor must be positive")
        object.__setattr__(self,"decision_id",_text(self.decision_id,"decision_id"))
        object.__setattr__(self,"instrument_hash",_hash(self.instrument_hash,"instrument_hash"))

@dataclass(frozen=True, slots=True)
class ApprovedVolumeFactor:
    event_id: str
    factor: Decimal
    decision_id: str
    instrument_hash: str
    def __post_init__(self):
        object.__setattr__(self,"event_id",_text(self.event_id,"event_id"))
        object.__setattr__(self,"factor",_decimal(self.factor,"factor"))
        if self.factor<=0: raise ValueError("volume factor must be positive")
        object.__setattr__(self,"decision_id",_text(self.decision_id,"decision_id"))
        object.__setattr__(self,"instrument_hash",_hash(self.instrument_hash,"instrument_hash"))

@dataclass(frozen=True, slots=True)
class VerifiedCashflow:
    event_id: str
    amount: Decimal
    currency: str
    direction: str
    payment_date: date
    decision_id: str
    evidence_ids: Tuple[str,...]
    def __post_init__(self):
        object.__setattr__(self,"event_id",_text(self.event_id,"event_id"))
        object.__setattr__(self,"amount",_decimal(self.amount,"amount"))
        if self.amount<0: raise ValueError("amount must be non-negative; direction carries sign")
        object.__setattr__(self,"currency",_text(self.currency,"currency"))
        direction=_text(self.direction,"direction").upper()
        if direction not in {"TO_INVESTOR","FROM_INVESTOR"}: raise ValueError("invalid cashflow direction")
        object.__setattr__(self,"direction",direction)
        if not isinstance(self.payment_date,date): raise ValueError("payment_date must be a date")
        object.__setattr__(self,"decision_id",_text(self.decision_id,"decision_id"))
        refs=tuple(_text(x,"evidence_id") for x in self.evidence_ids)
        if not refs: raise ValueError("cashflow requires evidence references")
        object.__setattr__(self,"evidence_ids",refs)
