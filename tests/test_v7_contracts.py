import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from marketsage_adjustment_engine_v7.contracts import CorporateActionEvent, DecisionDimension, DecisionOutcome, DecisionRecord, EventDateKind, EvidenceReference, InstrumentIdentity, SourceKind, SourceObservation, TypedEventDate, VerifiedCashflow
from marketsage_adjustment_engine_v7.gate import EvidenceGate

class V7ContractsTests(unittest.TestCase):
    def setUp(self):
        self.instrument=InstrumentIdentity('فولاد','46348559193224090')
        self.event=CorporateActionEvent('evt-1',self.instrument,'CASH_DIVIDEND',('pa-1',))
        self.pa=SourceObservation('pa-1',SourceKind.PA,self.instrument,date(2024,1,2),'a'*64,'raw/pa.json')
    def decisions(self,factor='0.8'):
        dims=(DecisionDimension.EVENT_CLASSIFICATION,DecisionDimension.SOURCE_LINK,DecisionDimension.LEGAL_DATE_MAPPING,DecisionDimension.EVIDENCE_QUALITY,DecisionDimension.PRICE_FACTOR)
        return [DecisionRecord(f'd{i}','evt-1',d,DecisionOutcome.MANUALLY_VERIFIED,'reviewer','reviewed evidence',('evidence-1',),{'factor':factor} if d is DecisionDimension.PRICE_FACTOR else {}) for i,d in enumerate(dims)]
    def test_gate_requires_all_dimensions(self):
        self.assertTrue(EvidenceGate().approve_price_factor(self.event,self.pa,self.decisions()).approved)
    def test_missing_date_mapping_fails(self):
        rows=[r for r in self.decisions() if r.dimension is not DecisionDimension.LEGAL_DATE_MAPPING]
        result=EvidenceGate().approve_price_factor(self.event,self.pa,rows)
        self.assertFalse(result.approved); self.assertIn('MISSING_DECISION:LEGAL_DATE_MAPPING',result.reasons)
    def test_unverified_outcome_fails(self):
        rows=self.decisions(); rows[-1]=DecisionRecord('d4','evt-1',DecisionDimension.PRICE_FACTOR,DecisionOutcome.INSUFFICIENT_EVIDENCE,'reviewer','not enough',(),{'factor':'0.8'})
        self.assertFalse(EvidenceGate().approve_price_factor(self.event,self.pa,rows).approved)
    def test_pa_sc_not_interchangeable(self):
        sc=SourceObservation('sc-1',SourceKind.SC,self.instrument,date(2024,1,2),'b'*64,'raw/sc.json')
        self.assertFalse(EvidenceGate().approve_price_factor(self.event,sc,self.decisions()).approved)
    def test_multiple_active_approvals_fail(self):
        rows=self.decisions(); rows.append(DecisionRecord('d-extra','evt-1',DecisionDimension.PRICE_FACTOR,DecisionOutcome.MANUALLY_VERIFIED,'reviewer2','second approval',('evidence-2',),{'factor':'0.9'}))
        self.assertFalse(EvidenceGate().approve_price_factor(self.event,self.pa,rows).approved)
    def test_typed_date_requires_evidence(self):
        self.assertEqual(TypedEventDate(date(2024,1,2),EventDateKind.EX_DATE,('doc-1',)).kind,EventDateKind.EX_DATE)
        with self.assertRaises(ValueError): TypedEventDate(date(2024,1,2),EventDateKind.EX_DATE,())
    def test_evidence_hash_and_timezone_required(self):
        EvidenceReference('doc-1',SourceKind.CODAL,'codal://1','d'*64,datetime(2024,1,2,tzinfo=timezone.utc))
        with self.assertRaises(ValueError): EvidenceReference('doc-2',SourceKind.CODAL,'codal://2','bad',datetime(2024,1,2,tzinfo=timezone.utc))
    def test_cashflow_direction_required(self):
        self.assertEqual(VerifiedCashflow('evt-1',Decimal('500'),'IRR','TO_INVESTOR',date(2024,2,1),'d1',('doc-1',)).direction,'TO_INVESTOR')
        with self.assertRaises(ValueError): VerifiedCashflow('evt-1',Decimal('500'),'IRR','UNKNOWN',date(2024,2,1),'d1',('doc-1',))

if __name__=='__main__': unittest.main()
