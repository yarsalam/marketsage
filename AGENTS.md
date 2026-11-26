# MarketSage Agent & Developer Instructions

These instructions are mandatory for every contributor, coding agent, and automated workflow working in this repository.

## Adjustment-engine source of truth

Before changing any adjustment, corporate-action, TSETMC, CODAL, event-ledger, historical-price, volume, or total-return code, read:

- `docs/ADJUSTMENT_ENGINE_MASTER_SPEC_FA.md` — authoritative architecture and acceptance requirements.
- `docs/research/ADJUSTMENT_RESEARCH_STANDARD.md` — active research protocol and historical constraints.
- `docs/research/IRAN_EQUITY_ADJUSTMENT_STANDARD_DRAFT.md` — event taxonomy, evidence workflow and unresolved research decisions.
- The relevant Foolad audit and V6 documents available in the current branch/worktree.

If a referenced file is absent from the current checkout, do not invent its contents; report the missing path and continue only with verified material.

## Non-negotiable rules

1. Build a symbol-independent system for the full instrument universe and full available history. Never hard-code Foolad, InsCode, event counts, date cutoffs, or materiality thresholds in core logic.
2. Preserve raw source payloads and original documents as immutable, versioned evidence. Never overwrite, normalize in place, or fabricate a hash for an unavailable file.
3. Separate acquisition, adapters, identity, event discovery, evidence reconciliation, calculation, validation, and publication.
4. CODAL-first event research is required. Then reconcile with trading calendar/status and independent TSETMC PA, SC and Daily feeds. If CODAL evidence is missing, perform and record fallback searches in issuer notices, official publications and newspaper archives.
5. PA and SC are separate source feeds and separate evidence dimensions. Never multiply PA and SC factors or deduplicate them using date alone. `SC.idn=0` is not unique; preserve it and use a validated composite identity plus SHA-256 record fingerprint.
6. Price adjustment, share/volume normalization and total return are separate engines with separate inputs, policies, ledgers and tests. Do not infer funding source from old/new share counts alone.
7. Proximity, same-day timestamps, price gaps, provider tuples and chart similarity create candidates only; they do not prove event identity, legal dates, or economic terms.
8. Keep publication, meeting, record, ex-date, first affected trading session, rights lifecycle, registration, provider date and retrieval time distinct.
9. All manual review and exceptions must be recorded in the append-only Evidence Ledger with evidence references, reviewer, timestamp, reason, input hashes and decision dimensions. Never leave decisions only in chat or outside the system.
10. Use fail-closed behavior for unknown, conflicting, stale or insufficient evidence. Quarantine affected events/ranges; do not silently skip or guess.
11. READY, AUTO_VALIDATED or MANUALLY_VERIFIED alone never grants publication approval. Respect G0–G5.
12. Never tune factors merely to match A1 or an independent chart. Provider data is a comparison source, not unquestionable economic truth.
13. Preserve the Foolad audit lessons: 285 pClosing-outside-price-limit flags are not automatically factor errors; investigate pClosing/pDrCotVal/last-trade/no-trade semantics; the 2020–2022 residual must be traced to its factor/feed/anchor/rounding step; normalized volume is not proven by raw-volume agreement; Total Return remains separate until dividends and rights cashflows are evidenced; the four mixed increases' 1000 Rial subscription-price assumption requires event-specific proof.
14. The five previously validated PA/SC cases are validated only within their documented scope; they do not imply production approval or validate the seven SC-only events.
15. Every engine must provide versioned contracts, deterministic and idempotent behavior, replay/resume, provenance, lineage, unit/integration/regression/negative tests, cross-symbol tests and explicit acceptance gates.
16. Before editing, inspect the current worktree and relevant files. Never use destructive Git cleanup/reset/checkout commands. Preserve user changes and untracked files.
17. Make narrow, reviewable changes. Run focused tests before and after; report exact commands, outcomes, changed files, unresolved blockers and whether the result is research-only or approved.
18. Do not claim code was built, tested, committed, deployed or accepted unless the operation actually succeeded and its result was verified.

## Required implementation order

Audit existing code first. Then stabilize canonical contracts and immutable manifests; complete adapters; implement the orchestrator; connect V6 discovery and evidence decisions; implement CODAL-first reconciliation; build independent price and share-basis handlers; implement cashflow/total-return; then validation/publication gates and cross-symbol acceptance.

Foolad is the pilot, not the architecture. After its evidence and tests, use Vaghdir and Parsian to prove generalization before broad-universe execution.
