import unittest
from datetime import date, datetime, timezone
from decimal import Decimal

from marketsage_adjustment_engine_v7.contracts import (
    CorporateActionEvent, DecisionDimension, DecisionOutcome, DecisionRecord,
    EventDateKind, EvidenceReference, InstrumentIdentity, SourceKind,
    SourceObservation, TypedEventDate, VerifiedCashflow, canonical_hash,
)
from marketsage_adjustment_engine_v7.gate import EvidenceGate


class V7ContractsTests(unittest.TestCase):
    def setUp(self):
        self.instrument = InstrumentIdentity("فولاد", "46348559193224090")
        self.evidence = [
            EvidenceReference("evidence-1", SourceKind.CODAL, "codal://evidence-1", "e" * 64,
                              datetime(2026, 11, 26, tzinfo=timezone.utc)),
            EvidenceReference("evidence-date", SourceKind.CODAL, "codal://date", "f" * 64,
                              datetime(2026, 11, 26, tzinfo=timezone.utc)),
        ]
        self.event = CorporateActionEvent(
            "evt-1", self.instrument, "CASH_DIVIDEND", ("pa-1",),
            (TypedEventDate(date(2024, 1, 3), EventDateKind.FIRST_AFFECTED_SESSION, ("evidence-date",)),),
        )
        self.pa = SourceObservation("pa-1", SourceKind.PA, self.instrument, date(2024, 1, 2),
                                    "a" * 64, "raw/pa.json")

    def decisions(self, factor="0.8"):
        specs = (
            (DecisionDimension.EVENT_CLASSIFICATION, {"event_type": "CASH_DIVIDEND"}, ("evidence-1",)),
            (DecisionDimension.SOURCE_LINK, {"event_id": "evt-1", "observation_id": "pa-1"}, ("evidence-1",)),
            (DecisionDimension.LEGAL_DATE_MAPPING,
             {"date_kind": "FIRST_AFFECTED_SESSION", "effective_date": "2024-01-03"},
             ("evidence-1", "evidence-date")),
            (DecisionDimension.EVIDENCE_QUALITY, {"quality_status": "ACCEPTED", "quarantined": False}, ("evidence-1",)),
            (DecisionDimension.PRICE_FACTOR, {"factor": factor}, ("evidence-1",)),
        )
        return [
            DecisionRecord(f"d{i}", "evt-1", dimension, DecisionOutcome.MANUALLY_VERIFIED,
                           "reviewer", "reviewed evidence", refs, payload)
            for i, (dimension, payload, refs) in enumerate(specs)
        ]

    def test_gate_requires_all_dimensions_and_returns_provenance(self):
        result = EvidenceGate().approve_price_factor(self.event, self.pa, self.decisions(), self.evidence)
        self.assertTrue(result.approved)
        self.assertEqual(result.factor, Decimal("0.8"))
        self.assertEqual(result.approved_output.observation_id, "pa-1")
        self.assertEqual(result.approved_output.effective_date, date(2024, 1, 3))
        self.assertEqual(result.approved_output.evidence_ids, ("evidence-1", "evidence-date"))
        self.assertEqual(len(result.approved_output.evidence_hashes), 2)
        self.assertEqual(result.approved_output.policy_version, "v7.1")

    def test_missing_date_mapping_fails(self):
        rows = [r for r in self.decisions() if r.dimension is not DecisionDimension.LEGAL_DATE_MAPPING]
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("MISSING_DECISION:LEGAL_DATE_MAPPING", result.reasons)

    def test_unverified_outcome_fails(self):
        rows = self.decisions()
        rows[-1] = DecisionRecord("d4", "evt-1", DecisionDimension.PRICE_FACTOR,
                                  DecisionOutcome.INSUFFICIENT_EVIDENCE, "reviewer", "not enough",
                                  ("evidence-1",), {"factor": "0.8"})
        self.assertFalse(EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence).approved)

    def test_pa_sc_not_interchangeable(self):
        sc = SourceObservation("sc-1", SourceKind.SC, self.instrument, date(2024, 1, 2),
                               "b" * 64, "raw/sc.json")
        result = EvidenceGate().approve_price_factor(self.event, sc, self.decisions(), self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("WRONG_SOURCE_KIND:EXPECTED_PA", result.reasons)

    def test_multiple_active_approvals_fail(self):
        rows = self.decisions()
        rows.append(DecisionRecord("d-extra", "evt-1", DecisionDimension.PRICE_FACTOR,
                                   DecisionOutcome.MANUALLY_VERIFIED, "reviewer2", "second approval",
                                   ("evidence-1",), {"factor": "0.9"}))
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("AMBIGUOUS_ACTIVE_DECISIONS:PRICE_FACTOR", result.reasons)

    def test_missing_evidence_object_fails(self):
        result = EvidenceGate().approve_price_factor(self.event, self.pa, self.decisions(), ())
        self.assertFalse(result.approved)
        self.assertIn("UNRESOLVED_EVIDENCE_REFERENCES:PRICE_FACTOR", result.reasons)

    def test_typed_date_requires_evidence(self):
        self.assertEqual(TypedEventDate(date(2024, 1, 2), EventDateKind.EX_DATE, ("doc-1",)).kind,
                         EventDateKind.EX_DATE)
        with self.assertRaises(ValueError):
            TypedEventDate(date(2024, 1, 2), EventDateKind.EX_DATE, ())

    def test_evidence_hash_and_timezone_required(self):
        EvidenceReference("doc-1", SourceKind.CODAL, "codal://1", "d" * 64,
                          datetime(2024, 1, 2, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            EvidenceReference("doc-2", SourceKind.CODAL, "codal://2", "bad",
                              datetime(2024, 1, 2, tzinfo=timezone.utc))

    def test_cashflow_direction_required(self):
        flow = VerifiedCashflow("evt-1", Decimal("500"), "IRR", "TO_INVESTOR",
                                date(2024, 2, 1), "d1", ("doc-1",))
        self.assertEqual(flow.direction, "TO_INVESTOR")
        with self.assertRaises(ValueError):
            VerifiedCashflow("evt-1", Decimal("500"), "IRR", "UNKNOWN",
                             date(2024, 2, 1), "d1", ("doc-1",))

    def test_volume_factor_requires_sc_and_separate_decision_dimension(self):
        event = CorporateActionEvent(
            "evt-volume", self.instrument, "CAPITAL_INCREASE", ("sc-1",),
            (TypedEventDate(date(2024, 1, 3), EventDateKind.FIRST_AFFECTED_SESSION, ("evidence-date",)),),
        )
        sc = SourceObservation("sc-1", SourceKind.SC, self.instrument, date(2024, 1, 2),
                               "b" * 64, "raw/sc.json")
        specs = (
            (DecisionDimension.EVENT_CLASSIFICATION, {"event_type": "CAPITAL_INCREASE"}, ("evidence-1",)),
            (DecisionDimension.SOURCE_LINK, {"event_id": "evt-volume", "observation_id": "sc-1"}, ("evidence-1",)),
            (DecisionDimension.LEGAL_DATE_MAPPING,
             {"date_kind": "FIRST_AFFECTED_SESSION", "effective_date": "2024-01-03"},
             ("evidence-1", "evidence-date")),
            (DecisionDimension.EVIDENCE_QUALITY, {"quality_status": "ACCEPTED", "quarantined": False}, ("evidence-1",)),
            (DecisionDimension.VOLUME_FACTOR, {"factor": "1.25"}, ("evidence-1",)),
        )
        rows = [DecisionRecord(f"v{i}", "evt-volume", d, DecisionOutcome.MANUALLY_VERIFIED,
                               "reviewer", "reviewed evidence", refs, payload)
                for i, (d, payload, refs) in enumerate(specs)]
        result = EvidenceGate().approve_volume_factor(event, sc, rows, self.evidence)
        self.assertTrue(result.approved)
        self.assertEqual(result.factor, Decimal("1.25"))
        self.assertFalse(EvidenceGate().approve_price_factor(event, sc, rows, self.evidence).approved)

    def test_instrument_identity_mismatch_fails(self):
        other = InstrumentIdentity("فولاد", "99999999999999999")
        observation = SourceObservation("pa-1", SourceKind.PA, other, date(2024, 1, 2),
                                        "a" * 64, "raw/pa.json")
        result = EvidenceGate().approve_price_factor(self.event, observation, self.decisions(), self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("INSTRUMENT_IDENTITY_MISMATCH", result.reasons)

    def test_source_link_payload_must_match_exact_observation(self):
        rows = self.decisions()
        rows[1] = DecisionRecord("d1", "evt-1", DecisionDimension.SOURCE_LINK,
                                 DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "bad link",
                                 ("evidence-1",), {"event_id": "evt-1", "observation_id": "other-pa"})
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("SOURCE_LINK_PAYLOAD_MISMATCH", result.reasons)

    def test_event_classification_payload_must_match(self):
        rows = self.decisions()
        rows[0] = DecisionRecord("d0", "evt-1", DecisionDimension.EVENT_CLASSIFICATION,
                                 DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "wrong type",
                                 ("evidence-1",), {"event_type": "CAPITAL_INCREASE"})
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("EVENT_CLASSIFICATION_PAYLOAD_MISMATCH", result.reasons)

    def test_legal_date_must_match_typed_first_affected_session(self):
        rows = self.decisions()
        rows[2] = DecisionRecord("d2", "evt-1", DecisionDimension.LEGAL_DATE_MAPPING,
                                 DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "wrong date",
                                 ("evidence-1", "evidence-date"),
                                 {"date_kind": "EX_DATE", "effective_date": "2024-01-02"})
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("LEGAL_DATE_DECISION_DOES_NOT_MATCH_TYPED_EVENT_DATE", result.reasons)

    def test_date_evidence_must_be_bound_to_date_decision(self):
        rows = self.decisions()
        rows[2] = DecisionRecord("d2", "evt-1", DecisionDimension.LEGAL_DATE_MAPPING,
                                 DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "unbound date evidence",
                                 ("evidence-1",),
                                 {"date_kind": "FIRST_AFFECTED_SESSION", "effective_date": "2024-01-03"})
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("LEGAL_DATE_DECISION_MISSING_TYPED_DATE_EVIDENCE", result.reasons)

    def test_two_first_affected_dates_fail_closed(self):
        event = CorporateActionEvent(
            "evt-1", self.instrument, "CASH_DIVIDEND", ("pa-1",),
            (TypedEventDate(date(2024, 1, 3), EventDateKind.FIRST_AFFECTED_SESSION, ("evidence-date",)),
             TypedEventDate(date(2024, 1, 4), EventDateKind.FIRST_AFFECTED_SESSION, ("evidence-1",))),
        )
        result = EvidenceGate().approve_price_factor(event, self.pa, self.decisions(), self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("REQUIRES_EXACTLY_ONE_FIRST_AFFECTED_SESSION_DATE", result.reasons)

    def test_supersession_unknown_target_fails(self):
        rows = self.decisions()
        rows.append(DecisionRecord("d-new", "evt-1", DecisionDimension.PRICE_FACTOR,
                                   DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "unknown target",
                                   ("evidence-1",), {"factor": "0.7"}, ("missing-id",)))
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("UNKNOWN_SUPERSESSION_TARGET:missing-id", result.reasons)

    def test_supersession_cross_dimension_fails(self):
        rows = self.decisions()
        rows.append(DecisionRecord("d-new", "evt-1", DecisionDimension.PRICE_FACTOR,
                                   DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "cross dimension",
                                   ("evidence-1",), {"factor": "0.7"}, ("d0",)))
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("CROSS_SUBJECT_OR_DIMENSION_SUPERSESSION:d0", result.reasons)

    def test_supersession_cycle_fails(self):
        rows = self.decisions()
        rows[-1] = DecisionRecord("d4", "evt-1", DecisionDimension.PRICE_FACTOR,
                                  DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "cycle A",
                                  ("evidence-1",), {"factor": "0.8"}, ("d5",))
        rows.append(DecisionRecord("d5", "evt-1", DecisionDimension.PRICE_FACTOR,
                                   DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "cycle B",
                                   ("evidence-1",), {"factor": "0.9"}, ("d4",)))
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("SUPERSESSION_CYCLE", result.reasons)

    def test_supersession_fork_fails(self):
        rows = self.decisions()
        rows.extend([
            DecisionRecord("d5", "evt-1", DecisionDimension.PRICE_FACTOR,
                           DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "replacement one",
                           ("evidence-1",), {"factor": "0.7"}, ("d4",)),
            DecisionRecord("d6", "evt-1", DecisionDimension.PRICE_FACTOR,
                           DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "replacement two",
                           ("evidence-1",), {"factor": "0.6"}, ("d4",)),
        ])
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("SUPERSESSION_FORK", result.reasons)

    def test_supersession_valid_linear_chain_selects_latest(self):
        rows = self.decisions()
        rows.extend([
            DecisionRecord("d5", "evt-1", DecisionDimension.PRICE_FACTOR,
                           DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "replace factor",
                           ("evidence-1",), {"factor": "0.75"}, ("d4",)),
        ])
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertTrue(result.approved)
        self.assertEqual(result.factor, Decimal("0.75"))
        self.assertEqual(result.decision_id, "d5")

    def test_nested_payload_is_deeply_immutable(self):
        nested = {"factor": "0.8", "audit": {"tags": ["one", "two"]}}
        record = DecisionRecord("immutable", "evt", DecisionDimension.PRICE_FACTOR,
                                DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "rationale",
                                ("evidence-1",), nested)
        nested["audit"]["tags"].append("mutated")
        self.assertEqual(record.payload["audit"]["tags"], ("one", "two"))
        with self.assertRaises(TypeError):
            record.payload["audit"]["new"] = "no"

    def test_canonical_hash_supports_frozen_payload(self):
        record = DecisionRecord("immutable", "evt", DecisionDimension.PRICE_FACTOR,
                                DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "rationale",
                                ("evidence-1",), {"factor": "0.8", "nested": {"x": [1, 2]}})
        self.assertEqual(len(canonical_hash(record.payload)), 64)

    def test_duplicate_decision_ids_fail(self):
        rows = self.decisions()
        rows.append(rows[-1])
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("DUPLICATE_DECISION_IDS", result.reasons)

    def test_evidence_quality_must_be_accepted(self):
        rows = self.decisions()
        rows[3] = DecisionRecord("d3", "evt-1", DecisionDimension.EVIDENCE_QUALITY,
                                 DecisionOutcome.MANUALLY_VERIFIED, "reviewer", "quarantined",
                                 ("evidence-1",), {"quality_status": "REJECTED", "quarantined": True})
        result = EvidenceGate().approve_price_factor(self.event, self.pa, rows, self.evidence)
        self.assertFalse(result.approved)
        self.assertIn("EVIDENCE_QUALITY_NOT_ACCEPTED", result.reasons)


if __name__ == "__main__":
    unittest.main()
