# MarketSage — Current Project State

**Snapshot date:** 2026-11-02  
**Repository:** `yarsalam/marketsage`  
**Default branch:** `main`  
**Main HEAD at snapshot:** `597e74d126b509188c7fa7d80eb765eb6c80238b`  
**Status:** Governance bootstrap pending; no new product implementation authorized by this snapshot.

## Immediate status

This is a read-only snapshot of GitHub state observed while preparing the execution constitution. It is not a complete audit of the owner's laptop, local uncommitted files, private data stores, or every historical PR diff.

- Repository visibility was `public` at the time of inspection. The owner has instructed that it be changed to private; the visibility change is still pending.
- The repository connection reports admin permissions, but the currently available GitHub operations can manage code/branches/PRs and read repository metadata; they do not expose the repository-visibility administration action.
- No repository rulesets were returned.
- The `main` branch and the listed branches were reported as unprotected.
- The recursive tree of `main` contained no `.github/workflows/` path.
- Root of `main` contained `.gitignore`, `admin-panel/`, and `user/`; no governance documentation directory existed on this branch at snapshot time.
- The governance branch for this document is `governance/execution-constitution-v1`.

## Open PRs observed

| PR | State | Subject | Snapshot note |
|---|---|---|---|
| #14 | Open | Integrated offline TSETMC acceptance pipeline | 277 analysis tests reported in PR description; owner's full 1,220-instrument local corpus not run |
| #13 | Open | Free dataset discovery and acceptance workflow | Live probes and source acceptance remain separate from CI |
| #9 | Open | Iranian market dashboard and Tindex ingestion | Candidate data remain fail-closed |
| #8 | Open | Bounded TSETMC live smoke | Smoke test, not source acceptance |
| #7 | Open | GDELT/FRED/Tindex acceptance fixes | Live connectivity and source validation remain separate |
| #6 | Open | Conservative Tindex free-tier connector | Production scoring remains disabled |
| #1 | Open, Draft | User-stack deployment preparation | Draft PR |

## Merged PRs observed

| PR | State | Subject |
|---|---|---|
| #12 | Merged | Tindex historical candle ingestion |
| #11 | Merged | StreamData CSV audit and normalization |
| #10 | Merged | TSETMC adjusted-history validation probe |
| #5 | Merged | Point-in-time data-lineage foundation |
| #4 | Merged | Admin workspace CI and strategy implementation audit |
| #3 | Merged | Iranian market data contracts |
| #2 | Merged | Leakage-aware backtest baseline |

This is the recent-PR inventory returned by the current GitHub listing, not an assertion that these are the only PRs ever created.

## Confirmed repository-level blockers

1. Repository must be made private before a self-hosted runner is registered.
2. Branch protection/rulesets are not configured.
3. A trusted CI workflow and a separately controlled local-runner workflow must be established.
4. The existing PR graph must be audited before choosing the single active integration path.
5. Existing local evidence and data must be inventoried by manifest/hash before any prior data work is repeated.

## Strategic evidence already known from prior project records

These are inherited project facts from earlier handoff/context and have not been re-audited against local files in this snapshot:

- TSETMC historical data for فولاد were examined with 4,250 raw rows; the raw series showed 285 OHLC violations and the adjusted candidate showed 41. Twenty-three adjustment events were examined. This is an anomaly investigation, not a certified adjusted-history dataset.
- TSETMC and CODAL were reachable in a prior no-VPN probe, but endpoint access does not establish data acceptance. CODAL publication timestamp semantics remained unresolved.
- Tindex candle ingestion was implemented with a provider history cap of about 100 days in the candidate endpoint; that endpoint alone is insufficient for a six-month historical test.
- Seller-provided StreamData CSV exports were audited for AYAR, BTCUSDT, 18K gold, and free-market USD. Unit, time, timezone, venue semantics and longer history remain unresolved.
- Yahoo Finance global proxy data and an initial momentum/backtest foundation exist in code, but the data were not certified as a complete, tradable, or point-in-time Iranian investment universe.
- Investment scoring/ranking remains fail-closed; no profitability or future-return guarantee has been established.

## Next authorized work

**Phase 1 — governance only**
1. Complete repository privatization.
2. Adopt and merge the execution constitution and current-state records.
3. Configure main-branch rulesets.
4. Reconcile open PRs into one canonical integration plan without merging unrelated feature work.

**Phase 2 — local execution**
1. Install a repository-scoped, least-privilege self-hosted runner.
2. Validate that only trusted reviewed code can execute on it.
3. Establish a durable local data root, run manifests, and artifact/report return path.

**Phase 3 — product execution**
Begin only after Phases 1 and 2 are complete. The first work item must be the broad candidate-data screen, not another code/test loop.

## Current single next action

Owner changes `yarsalam/marketsage` visibility to Private in GitHub Settings. After confirmation, continue with repository rulesets and runner setup.
