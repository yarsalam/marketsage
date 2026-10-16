# Iranian-source candidate acceptance notes

This document records the current safety boundary for Iranian market-data work. The TSETMC and CODAL adapters are candidate ingestion/parsing prototypes, not approved feeds. The CODAL search shape (https://search.codal.ir/api/search/v2/q) is based on community-maintained, reverse-engineered references rather than a guaranteed vendor contract. Review access terms and target-host connectivity before scheduling requests. See the [community endpoint reference](https://github.com/amirziveh/codal-skill) for the endpoint and reported XML response shape.

## CODAL candidate adapter

- Parses XML CodalLetterHeaderDto entries with Python's standard-library XML parser.
- Validates TracingNo, title, issuer-symbol identity, duplicate IDs, and timezone-aware retrieval time.
- Retains source-provided PublishDateTime and SentDateTime strings for audit, but does not treat either as a verified timestamp.
- The dates commonly appear in a Persian/Jalali representation. Until calendar conversion, timezone semantics, amendments, and publication/update behavior are verified against known reports, published_at stays null.
- Uses retrieval time only as an observation/storage anchor, explicitly marks records candidate_quarantined, and does not change the source scoring gate.
- Network fetching is explicit opt-in, one page at a time, with a timeout. No scheduler, retries, bulk crawler, or scoring integration is enabled.

## Evidence required before any Iranian source is approved

1. Documented access/use/redistribution permission and successful connection from the intended production host.
2. Stable issuer/instrument identity mapped to a verified reference list; preserve historical symbol changes.
3. Timestamp semantics validated against primary-source examples, including Jalali calendar, timezone, publication versus sent/updated time, and corrections.
4. Historical coverage and amendment/revision behavior measured over a representative sample.
5. Unit/currency and adjustment semantics reconciled independently; for TSETMC this includes Rial/Toman and adjusted versus unadjusted prices.
6. Deterministic fixtures from captured, permitted samples; parser-version and raw-response checksum lineage.
7. Tests for missing, duplicated, stale, malformed, amended, and out-of-order records.
8. Walk-forward replay proving that no record is visible before both its verified publication time and capture time.

No source becomes production-eligible merely because parsing succeeds. The registry approval flag, status, timestamp quality, legal review, and research release gates must all be explicitly satisfied. No Iranian source is currently approved for production scoring.
