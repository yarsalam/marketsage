# Stage 4 — Evaluation and Backtest Protocol

**Status:** protocol draft; no empirical strategy result has been accepted.
**Branch:** `feat/tindex-free-data-connector`
**Release posture:** research-only; investment ranking and source scoring remain disabled.

This protocol is intended to be fixed before inspecting comparative performance. Changes to the protocol must be versioned and explained; test results must not be used to quietly redesign the evaluation and then be reported as untouched out-of-sample evidence.

## 1. Decision question and scope

- **Product question:** compare eligible assets for a forward holding horizon of approximately six months, with risk and uncertainty visible. This is a research question, not a return promise or individualized investment advice.
- **Current strategy under test:** the existing monthly, long-only momentum baseline in `research/backtest.py`. It is a baseline to challenge, not an approved MarketSage model.
- **Decision cadence:** monthly, at a documented month-end decision point. Signals must use only information available at that point; orders are simulated no earlier than the next eligible period.
- **Holding horizon:** six months is the product target to evaluate. The current backtest implementation's rebalance cadence is monthly; a six-month forward-return label and a monthly rebalanced strategy are different experiments and must be reported separately.
- **Universe:** only instruments with an explicit source, symbol identity, quote currency, units, date convention, price definition and usable history. The current known Yahoo Finance experiment universe (BTC-USD, ETH-USD, SOL-USD, GLD, SPY, QQQ, TLT, UUP, USO, XLF, XLE) is mixed US-listed funds/equities and crypto; it is **not** a representative Iranian-market universe. Do not infer Tehran stock, free FX, coin or Iranian gold-fund performance from it.
- **Ranking:** disabled. No composite investment ranking, calibrated probability, or live recommendation may be emitted from this evaluation until data-source and model acceptance gates are passed.

## 2. Required data audit (before any performance comparison)

For every file and series, record its path, format, byte size, row count, schema, date range, missingness, duplicate timestamps, non-positive/non-finite prices, frequency, source/provider, symbol, currency, units, and any known transformations. Never print credentials or raw data values in audit logs.

The audit must explicitly classify each criterion as **pass**, **fail**, or **unknown**:

1. Provenance and permission to use/store the data.
2. Price field meaning: close, adjusted close, total-return series, or other.
3. Corporate-action and dividend treatment for equities/funds; token redenomination or symbol migration for crypto where relevant.
4. Timestamp timezone, market calendar, observation time versus availability time, and treatment of month-end bars.
5. Missing intervals, duplicate observations, stale values, bad values, and how alignment is performed.
6. Universe selection and survivorship bias, including unavailable/delisted instruments.
7. Point-in-time revisions or corrected observations, where applicable.
8. Quote currency and units, including USD/local currency conversion conventions.
9. Whether the dataset is sufficiently long for the planned windows and the six-month target.
10. Data-source approval state. Reachability alone is not approval.

A missing field is **unknown**, not an implicit pass. Synthetic fixtures can test plumbing but cannot qualify as historical market evidence.

## 3. Chronological evaluation design

Do not random-split time-series observations. After the data inventory determines the actual date range and sample size:

1. Reserve the latest contiguous period as a locked final holdout. Its dates and contents must not be used for feature, parameter, or strategy selection.
2. Use earlier observations for training/development and a later validation segment for limited model/parameter choices.
3. Use rolling or expanding walk-forward folds whose training windows always precede each test window. The forward-label overlap must be purged/embargoed where it can leak across boundaries.
4. Publish exact date boundaries, observations per split, asset coverage and exclusions before looking at the results.
5. If the sample is too short for meaningful six-month labels, report **insufficient history** instead of shortening the horizon after seeing results.
6. Keep a run manifest: dataset hashes, data cut-off, source versions, code commit, config, feature/label definitions, cost assumptions, random seeds, and output artifact hashes.

No universal percentage split is prescribed before the data audit. The exact split must be justified by the available history and fixed before comparative metrics are reviewed.

## 4. Baselines and execution assumptions

At minimum, compare like-for-like over the same dates and eligible universe:

- Cash / zero-return baseline, clearly labelled as a simplified reference if no suitable cash-rate series is approved.
- Equal-weight buy-and-hold or asset-level buy-and-hold where the instrument and currency make that comparison meaningful.
- The existing monthly momentum baseline.
- A simple momentum-only or no-selection baseline only if specified before the holdout is opened.

Costs must be explicit and configurable: commissions/fees, spread and slippage. Include turnover and state whether costs are charged on one-way or gross traded-weight turnover. The current code charges costs on L1 turnover (buys plus sells), not half-turnover. Avoid assuming execution at a price that was not yet observable. For a mixed asset universe, do not compare nominal local-currency and USD returns without an explicit FX conversion policy and FX data accepted for the same dates.

The current implementation has transaction-cost and slippage knobs but still needs a reviewed, reproducible benchmark comparison and a data-specific cost policy before it can support conclusions.

## 5. Metrics and uncertainty

Report the full evaluation period and each walk-forward fold, not just the best run:

- cumulative/net total return and CAGR where the horizon supports it;
- annualized volatility, maximum drawdown, and Sharpe only with its risk-free assumption stated;
- downside risk (Sortino and/or VaR/expected shortfall) only with conventions and limitations stated;
- turnover, estimated costs, exposure/cash fraction, number of rebalance periods and asset coverage;
- benchmark-relative results and results by calendar period/regime;
- sensitivity to higher costs/slippage, missing/stale observations and reasonable predeclared parameter variations;
- confidence intervals or uncertainty estimates where methodologically justified, plus failure cases.

A historical return is not a forecast. Do not advertise a 50% target, probability of profit, or "lowest risk" as validated without held-out evidence and calibrated uncertainty. Avoid selecting the winner based on the locked holdout.

## 6. Existing-code review notes

The existing `research/backtest.py`:

- validates that the supplied monthly price matrix is positive, finite, sorted and has unique dates;
- computes a monthly long-only momentum selection and deducts configurable transaction-cost and slippage fractions;
- has a future-perturbation regression test for earlier outputs.

These checks do **not** establish that input prices are real, adjusted correctly, point-in-time valid, complete, permissioned, or representative. Before using it for a strategy conclusion, review at least:

- whether input prices are total-return/adjusted series and the implications for signals and execution;
- whether the zero risk-free rate implicit in the current Sharpe calculation is appropriate;
- benchmark construction and cost conventions;
- whether every asset's next-period return and history requirements are handled without survivorship or selection leakage;
- the difference between a six-month forward prediction target and a monthly-rebalanced portfolio result.

## 7. Exit criteria

Stage 4 is not complete until a reviewer can reproduce the result from a pinned dataset and code commit; replay each historical decision using only information available at that time; compare against predeclared baselines on locked out-of-sample periods; inspect net-of-cost and risk results; and see documented failure cases and data limitations.

Passing Stage 4 does not close Stage 2 source acceptance, authorize production ranking, or guarantee future performance.

## 8. First execution step

Run the local inventory script from the repository root:

```bash
cd ~/projects/marketsage-acceptance
git status --short --branch
git log -1 --oneline
python user/analysis-engine/scripts/audit_research_data.py --root user/analysis-engine --output /tmp/marketsage-data-audit.json
```

Review the generated report locally. Share the summary output only; do not paste secrets or raw licensed datasets. The script is an inventory aid, not a source-approval decision.


## 9. Implemented evaluation runner (pending local/CI confirmation)

The repository now includes:

- `research/evaluation.py`: full-period comparison of the fixed momentum strategy, a zero-return cash reference, an all-asset equal-weight buy-and-hold reference (initial costs only), and an all-asset equal-weight monthly-rebalanced reference (same configured cost basis).
- `scripts/run_stage4_evaluation.py`: command-line runner that writes a JSON report with the input CSV SHA-256, sample dates, strategy configuration, full-period metrics, a final locked holdout, pre-holdout chronological folds, and a six-month forward-label inventory.
- `tests/test_research_evaluation.py`: deterministic fixture tests for holdout boundaries, fold boundaries, baseline presence, and label-inventory scope.
- The backtest summary now reports transaction-cost, slippage, and total-cost fractions separately. The backward-compatible `sum_of_period_cost_fractions` key now means the sum of all charged cost fractions.
- Sharpe uses a configurable annual risk-free assumption (`risk_free_rate_annual`, default 0.0) and records that assumption in the output.

Example local command (run from `user/analysis-engine`):

```bash
.venv/bin/python scripts/run_stage4_evaluation.py \
  --input /tmp/marketsage-monthly-stage4/monthly_prices.csv \
  --output /tmp/marketsage-stage4-evaluation.json \
  --holdout-months 12 \
  --min-train-months 24 \
  --fold-months 6 \
  --transaction-cost-bps 10 \
  --slippage-bps 25 \
  --risk-free-rate-annual 0
```

Do not inspect the holdout and then change settings while still calling it locked. The default CLI slippage of 25 bps is a sensitivity assumption, not an estimate of actual execution cost. The report includes zero-cost, configured-cost, and higher-cost stress scenarios; any additional scenarios must be declared before inspecting the locked holdout. This runner does not tune parameters, train a predictive model, calculate calibrated probabilities, or prove the strategy is suitable for Iranian markets. Six-month forward labels are counted for data-availability planning only; they are not prediction scores.

**Acceptance remains pending** until the local command, focused tests, and full analysis-engine suite pass on the intended commit, the report is reviewed, and source/provenance/rights and point-in-time limitations are resolved or explicitly bounded. A successful script exit alone is not Stage 4 approval.


## 10. Stage 5 report-integrity gate

After producing the report, run the structural validator:

```bash
.venv/bin/python scripts/validate_stage4_report.py /tmp/marketsage-stage4-evaluation.json
.venv/bin/python -m pytest -q tests/test_stage4_report_validator.py
```

The validator fails if the report does not explicitly keep ranking/source scoring disabled, the holdout is marked as used for tuning, walk-forward folds overlap the holdout, required baselines or cost scenarios are absent, or the dataset hash is malformed. This is a structural guardrail, not proof that source data are accurate, licensed, point-in-time correct, or economically tradable. It does not assess whether strategy metrics are good.
