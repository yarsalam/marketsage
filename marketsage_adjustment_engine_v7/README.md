# MarketSage Adjustment Engine V7 — contracts and evidence gate

Status: research foundation only. This package is not a price, volume, or total-return engine and is not production-approved.

## V7.1 integrity hardening

The gate requires a PA observation for price factors and an SC observation for volume factors. The two source kinds are independent and are never interchangeable.

Approval requires manually verified decisions for EVENT_CLASSIFICATION, SOURCE_LINK, LEGAL_DATE_MAPPING, EVIDENCE_QUALITY, and the relevant factor dimension. Decision payloads are checked against the exact event type and source observation. The legal-date decision must point to exactly one typed FIRST_AFFECTED_SESSION date, and its evidence references must include the evidence attached to that typed date. Other legal dates (publication, meeting, record, ex-date, rights dates, registration and payment) remain distinct and are not silently substituted.

Decision supersession is validated for duplicate IDs, unknown targets, cross-subject/dimension references, unverified superseding decisions, forks and cycles. Last-write-wins is never used. Decision payloads are recursively frozen. Evidence IDs must resolve to hashed evidence objects.

Approved factor outputs retain event ID, instrument identity hash, exact source observation ID, approved first affected session, evidence hashes, decision ID and policy version. Raw provider tuples do not directly enter calculation engines.

## Explicit limitations

- The gate does not establish authenticity of the human reviewer or legal authenticity of a document; SHA-256 establishes byte identity/integrity only.
- It does not calculate provider factors or infer event relationships.
- It does not yet provide a separate approved cashflow gate.
- It does not calculate adjusted OHLCV, normalized volume, Total Return, or publish production data.
- A manually verified decision is still only as sound as its cited evidence and review process.

Run:

    python3 -m unittest tests.test_v7_contracts -v
    python3 -m compileall -q marketsage_adjustment_engine_v7
