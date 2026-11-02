# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage` (**Private**)  
**Default branch:** `main`  
**Main HEAD:** `07f2e968257ef868a5efbab36f379ee487658577`  
**Status:** PR #1 baseline is in main. Tindex/FRED fixes, Iranian dashboard, free-dataset discovery, integrated TSETMC acceptance and evidence/Stage 4 corrections are consolidated in open PR #6. Post-#17 CI run `41406540206` passed all five required job types; data-source acceptance and strategy validation remain incomplete.

## Verified repository state

- Repository visibility is `private`.
- PR #1 integrated the application baseline into `main`; no deployment occurred.
- PR #6 remains open and unmerged to `main` under the explicit owner boundary. Its current head is `c821f6423ee5734590b4852eb5fab307834f0b51`; post-#17 merge CI run `41406540206` completed successfully with all five required job types green.
- PR #7 was merged into #6; PR #9 was merged into #6; PR #13 was merged into #6.
- PR #14 was merged into #6 on 2026-11-02 after all five required CI job types passed on exact head `4bd179263f55b90854d00f1ea3b1287da0393b03`; merge commit is `f267c49efcbf72e7ddc17099ff93f38ade269a7b`.
- PR #13 passed all five required CI job types on its exact pre-merge head and was merged into #6.
- All inspected branches remain unprotected. The connected GitHub integration cannot configure repository settings or branch protection.
- No local Runner is registered. The local data directory has not been inspected in this GitHub-only pass. A least-privilege trust-boundary design is recorded in `docs/governance/LOCAL_RUNNER_TRUST_BOUNDARY.md`; owner-side branch protection and host setup are required before activation.

## Current integration graph

```text
main
  └─ #6 feat/tindex-free-data-connector [open; never merge to main without explicit owner approval]
       ├─ #7 priority-source fixes               [merged]
       ├─ #9 Iranian market dashboard            [merged]
       ├─ #13 free-dataset discovery             [merged]
       ├─ #14 TSETMC acceptance pipeline         [merged; CI green]
       ├─ #16 source-evidence reconciliation     [merged; CI green]
       ├─ #17 Stage 4 cost sensitivity fix       [merged; CI green]
       └─ #18 monthly calendar validation       [merged; CI green]

#8 research/iran-free-data-smoke — parked network diagnostic
#15 governance — documentation PR, Draft
```

## PR status — observed 2026-11-02

| PR | Base ← head | State | Checks / handling |
|---|---|---|---|
| [#1](https://github.com/yarsalam/marketsage/pull/1) | `main` ← `deploy/production-readiness` | Merged | Application baseline integrated; no deployment. |
| [#6](https://github.com/yarsalam/marketsage/pull/6) | `main` ← `feat/tindex-free-data-connector` | Open, unmerged | Current head `c821f6423ee5734590b4852eb5fab307834f0b51`; latest run `41406540206` completed successfully with all five required job types green. Keep open at main boundary. |
| [#7](https://github.com/yarsalam/marketsage/pull/7) | #6 branch | Merged | Tindex documented route/history updates, safe FRED network diagnostics, regression tests and strict 1/minute + 100/day client guard. |
| [#8](https://github.com/yarsalam/marketsage/pull/8) | old fix branch ← `research/iran-free-data-smoke` | Open, parked | Standard CI passed; separate live TSETMC probe timed out from GitHub-hosted runner. Do not repeat from same network. |
| [#9](https://github.com/yarsalam/marketsage/pull/9) | #6 branch | Merged | Iranian market dashboard and research-only readiness/staging configuration; all five unique required CI job types passed before merge. |
| [#13](https://github.com/yarsalam/marketsage/pull/13) | #6 branch | Merged | Free-dataset discovery, source catalog, candidate audit/ingestion tools; all five required CI job types passed on exact head before merge. |
| [#14](https://github.com/yarsalam/marketsage/pull/14) | #6 branch ← `feature/tsetmc-integrated-acceptance-pipeline` | Merged | Exact-head run `41401668921` completed successfully; all five required job types passed. Merge commit `f267c49efcbf72e7ddc17099ff93f38ade269a7b`. |
| [#15](https://github.com/yarsalam/marketsage/pull/15) | `main` ← `governance/execution-constitution-v1` | Open, Draft | Updated constitution allows independent work in parallel. Keep Draft until governance adoption/enforcement decision. |
| [#18](https://github.com/yarsalam/marketsage/pull/18) | #6 branch ← `fix/stage4-monthly-calendar-validation` | Merged | Exact-head CI run `41406678452` passed all five required job types; merge commit `d468d06eb0fb4adcc90f04be38a61f4f1164ad57`. |

CI results apply only to exact head commits. PR #14 passed all five required job types before merge. PR #6 stays open and unmerged to main; there is no deployment or scoring authorization.

## Changes made in this execution pass

1. PR #1 merged into `main` as a code-baseline integration; no deployment.
2. PR #6 retargeted to `main` and kept open/unmerged.
3. PR #7 reconciled with the conservative Tindex quota implementation and merged into #6.
4. CI triggers expanded to run on feature/fix branches and relevant PR targets.
5. PR #9 rebased and merged into #6 after green CI.
6. PR #13 rebased and merged into #6 after green CI.
7. PR #14 passed all five required CI job types on its exact head and was merged into #6; #6 advanced to `f267c49efcbf72e7ddc17099ff93f38ade269a7b`.
8. PR #16 reconciled Nerkhsanj and Binance evidence; all five CI job types passed on exact head `420ede0476fbd9a6abe444b397fd9d4fcea91dff`, then it was merged into #6 at `77d25986627664b6482e515fbd4bd9791a041797`.
9. Post-#16 merge CI run `41405927116` passed all five required job types.
10. PR #17 fixed cost-sensitivity scenario deduplication; all five CI job types passed on exact head `74bf96ff1607e213ee9abdf259a7059ceca454da`, then it was merged into #6 at `c821f6423ee5734590b4852eb5fab307834f0b51`.
11. PR #18 added the monthly calendar integrity gate; all five required CI job types passed on exact head `f4754cfce3a4ccba5d177a44c8b2b6850671ff31`, then it was merged into #6 at `d468d06eb0fb4adcc90f04be38a61f4f1164ad57`.

## Parallel work policy

A dependency blocker does not freeze independent work. These tasks can progress in parallel with integration:

- audit existing data manifests and sanitized evidence without repeating previous probes;
- screen candidate data sources across Iranian and global assets;
- review rights, units, timestamps, historical coverage and independent reconciliation;
- prepare the six-month monthly-decision evaluation protocol, risk/cost assumptions and baselines;
- perform separately scoped engineering that does not conflict with current integration changes.

Local dataset inventory remains unverified because this session has no access to the owner's local data directory and there is no trusted local Runner. Do not claim it was audited.

## Operating constraints

- Investment scoring/ranking remains fail-closed; no real-money trades or portfolio allocation.
- Reachability and green CI do not constitute data-source acceptance or strategy validation.
- Merging to `main` does not authorize deployment.
- PR #6 must not be merged into `main` without explicit owner approval.
- No local Runner registration before trusted-workflow and least-privilege data-access controls are reviewed.
- Keep raw datasets, credentials and private captures outside Git.

## Next actions

1. Complete post-#18 merge CI run `41407020273` on #6; it is queued at this snapshot.
2. Complete CI on PR #18; if its exact head passes, merge it into #6 and refresh the state.
2. Continue independent source-evidence screening and resolve the specific Nerkhsanj anomalies/rights and TSETMC event-window reconciliation.
3. Execute the integrated TSETMC pipeline and Stage 4 evaluation only through a trusted least-privilege local runner; the owner's full local corpus remains inaccessible here.
4. Fix only demonstrated defects; do not repeat the parked GitHub-hosted TSETMC live probe.
5. Evaluate the investment objective on pinned, permissioned data using locked chronological holdout, walk-forward controls, realistic costs/slippage, drawdown and baseline comparisons.
6. Keep #6 at the main boundary pending explicit owner authorization. No deployment is implied.


## Independent data-evidence screening — 2026-11-02

This is a review of existing committed documentation and owner-reported sanitized summaries; no local raw files were accessed or re-audited in this pass.

### Iran candidates

- **TSETMC equities/funds:** candidate adapter and the new offline integrated acceptance runner are now in #6. The runner is intentionally network-free and requires a local corpus. Earlier one-instrument evidence for فولاد is not full-universe acceptance; the reported adjusted-history mismatch and unresolved corporate-action/independent-reference evidence remain gates. The local 1,220-instrument corpus has not been run through the new pipeline.
- **CODAL:** bounded disclosure search and fixtures exist. Publication time, original-versus-amended filing linkage, history coverage and automated-use rights remain unknown; retrieval time must not be substituted for publication time.
- **Nerkhsanj archive:** owner-reported 2026-10-22 capture/normalization covered 28 candidate keys and 91,245 rows; the 2026-10-23 local audit reported no invalid dates, non-positive values or duplicate-date conflicts. This is useful structural evidence, not source acceptance. The same audit flagged 182 adjacent changes >=20%, including 48 >=100%. The concentrated outliers were IQD (44 >=100%, a 373-day maximum gap and inconsistent multi-hundred-fold scale changes), silver (three large scale changes around 9.9x–26x), and Tether (a one-day sentinel-like value of 1 followed by reversion); Bitcoin also has an 84-day gap. Keep IQD, silver and Tether out of feature generation; retain Bitcoin as a coverage warning. No rescaling, row deletion or forward-fill is approved. Source lineage, attribution, reuse/model/commercial rights, key identity, quote convention, Toman/Rial units, daily-value semantics, calendar, stale values, revisions and independent reconciliation remain open.
- **Tindex:** free-tier contract is conservatively capped at 1 request/minute and 100 successful requests/day; documented candle history is about 100 days, shorter than the six-month target. Toman documentation is not enough to certify each account series; payload-unit reconciliation, exact enabled slugs, rights and independent reference remain open.
- **TGJU:** discovery only. Automated collection rights, stable API contract, free-versus-official FX convention, units and history remain unverified.
- **Iran official macro:** Central Bank/Statistical Center are candidates, but machine-readable historical coverage, release times, revisions and definitions are not accepted. World Bank Iran CPI is a separate annual macro series, not a daily local market feed.

### Global and cross-market candidates

- **World Bank Indicators:** existing report says 26 annual Iran CPI observations for 2000–2025. Annual observation year is not publication time; revisions, series definition, units, terms and point-in-time availability must be captured before use.
- **Binance Spot:** owner-reported Iran-network attempts returned HTTP 451 for BTCUSDT, ETHUSDT and SOLUSDT. Keep those routes blocked; do not try alternate hosts to bypass the restriction. A separate earlier foreign probe reported reachability for these pairs but only 18 rows across eight series, which does not establish multi-year coverage or rights. Venue/pair/quote identity, terms, history continuity, partial candles, fees and slippage remain unaccepted.
- **Yahoo Finance:** an earlier owner-reported collection contains selected five-year proxy histories; one EURUSD=X TLS probe timed out. Reuse existing captures rather than repeating successful downloads. This remains unofficial research-only data with terms, adjustment, currency, survivorship and point-in-time caveats; it is not a representative Iranian universe.
- **FRED/ALFRED:** key/access was previously unavailable. Observation period and vintage date are not exact intraday release time; no live probe is repeated.
- **GDELT/news:** previous HTTP 429 remains in cooldown. seendate is first-seen/index time, not publisher publication time. No sentiment benchmark is accepted; the keyword baseline is prototype-only.
- **StreamData:** seller-provided, not free. Rights/contract, units, time semantics and independent reconciliation remain unresolved; the known AYAR OHLC anomaly must remain flagged, not repaired.

### Research readiness

The Stage 4 protocol and evaluation runner are present, including cash, equal-weight and monthly momentum baselines, chronological folds, a locked holdout, cost/slippage scenarios and report-integrity checks. No empirical result from a permissioned, representative, point-in-time dataset has been accepted. The full local corpus and local evaluation files are unavailable to this GitHub-only execution; local audit and strategy evaluation are therefore **BLOCKED pending a trusted, least-privilege runner and local data access**. The connected GitHub integration cannot configure or verify repository rulesets; owner-side branch protection, dedicated OS account/directories and repository-scoped ephemeral Runner registration are required as described in `LOCAL_RUNNER_TRUST_BOUNDARY.md`. CI and parser fixtures are not investment evidence.
