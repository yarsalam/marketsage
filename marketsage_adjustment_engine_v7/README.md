# MarketSage Adjustment Engine V7 — contracts and evidence gate

Status: research foundation only. This package is not a price, volume, or total-return engine and is not production-approved.

The package defines immutable contracts for instrument identity, source observations, evidence references, typed event dates, corporate-action events, event relationships, decision records, separately approved price and volume factors, and verified cashflows.

Price-factor approval requires manually verified decisions for EVENT_CLASSIFICATION, SOURCE_LINK, LEGAL_DATE_MAPPING, EVIDENCE_QUALITY, and PRICE_FACTOR, plus a PA observation linked to the event and matching instrument identity. Volume-factor approval requires the common dimensions plus VOLUME_FACTOR and an SC observation. PA and SC are never interchangeable.

Only MANUALLY_VERIFIED passes. Missing, rejected, conflicting, insufficient, or quarantined decisions fail closed. Multiple active decisions are ambiguous; the gate does not use last-write-wins. Supersession-chain integrity must be validated by the append-only decision-log reader before records are supplied to this gate.

No legal-date inference, same-date PA/SC linking, raw tuple factor derivation, adjusted OHLCV calculation, Total Return calculation, or publication approval is implemented.

Run:

    python3 -m unittest tests.test_v7_contracts -v
    python3 -m compileall -q marketsage_adjustment_engine_v7
