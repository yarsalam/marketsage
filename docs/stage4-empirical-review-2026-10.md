# Stage 4 — Empirical Review (2026-10)

**Decision:** exploratory evidence only; Stage 4 is not accepted as predictive validation.  
**Ranking/source scoring:** remain disabled.  
**Input report:** `/tmp/marketsage-stage4-evaluation.json` (local artifact; do not commit the raw report or dataset).  
**Dataset SHA-256:** `1e71d898b18b4a6db74aba4826c86a4982efad934ee30aa82ff354883f01d878`

## Dataset and protocol

- 78 monthly rows from 2020-04-30 through 2026-09-30, covering 11 assets.
- Final 12-month holdout: 2025-10-31 through 2026-09-30.
- Seven chronological six-month evaluation folds before the holdout.
- Baselines: monthly-rebalanced equal weight, equal-weight buy-and-hold, and zero-return cash.
- Configured strategy costs: 10 bps transaction cost and 25 bps slippage; annual risk-free rate set to 0%.
- The input universe is global proxies/US ETFs and crypto. It does not establish performance for Iranian equities, gold, coin, FX, or other locally traded instruments.
- The report validator passed and confirms the report is exploratory, with both ranking and source scoring disabled. The validation result is structural, not proof that the data or strategy is valid.

## Recorded results

### Full period

| Strategy | Total return | CAGR | Annualized volatility | Sharpe | Maximum drawdown |
|---|---:|---:|---:|---:|---:|
| Momentum, net | 285.95% | 28.32% | 45.65% | 0.77 | -40.15% |
| Equal weight, monthly rebalanced, net | 175.79% | 20.60% | 25.38% | 0.86 | -33.74% |
| Equal-weight buy-and-hold, net | 96.93% | 13.33% | 26.04% | 0.61 | -38.05% |
| Zero-return cash | 0.00% | 0.00% | 0.00% | undefined | 0.00% |

Momentum had the highest recorded total return, but also the largest maximum drawdown of these three investable strategies and a lower Sharpe ratio than the monthly-rebalanced equal-weight baseline. The result therefore does not support a universal “best risk-adjusted strategy” claim.

### Final 12-month holdout

| Strategy | Total return | Annualized volatility | Sharpe | Maximum drawdown |
|---|---:|---:|---:|---:|
| Momentum, net | 30.57% | 22.36% | 1.30 | -9.30% |
| Equal weight, monthly rebalanced, net | 6.41% | 18.27% | 0.42 | -9.88% |
| Equal-weight buy-and-hold, net | 1.34% | 18.61% | 0.16 | -11.77% |
| Zero-return cash | 0.00% | 0.00% | undefined | 0.00% |

Momentum outperformed these baselines in this one holdout window. One year is too short to establish stable expected performance, and this holdout result must not be used to tune parameters.

### Cost sensitivity for momentum

| Scenario | Transaction cost | Slippage | Full-period total return | Holdout total return |
|---|---:|---:|---:|---:|
| Zero-cost reference | 0 bps | 0 bps | 354.43% | 34.19% |
| Configured costs | 10 bps | 25 bps | 285.95% | 30.57% |
| Higher-cost stress | 25 bps | 50 bps | 219.95% | 26.54% |

The stress case remains positive in this historical sample, but the slippage values are assumptions rather than measured execution costs. Reported period cost fractions are turnover-based cost inputs and must not be described as the same thing as portfolio return loss.

## Material anomaly requiring investigation

The fold from 2023-10-31 through 2024-03-31 reports momentum total return of approximately **240.89% in six months** and annualized CAGR of approximately **1,062%**. The annualized figure is a mathematical extrapolation from that six-month interval, not a forecast. The fold's extreme result may dominate the full-period aggregate and must be attributed to individual assets/trades before the strategy can pass review.

The seven six-month momentum fold returns were approximately:
- 2022-04 to 2022-09: -2.32%
- 2022-10 to 2023-03: +21.69%
- 2023-04 to 2023-09: +13.99%
- 2023-10 to 2024-03: +240.89%
- 2024-04 to 2024-09: -16.12%
- 2024-10 to 2025-03: -17.96%
- 2025-04 to 2025-09: +18.79%

This dispersion is material. The results are not a stable monthly income stream and include multiple losing six-month windows.

## Reproducible attribution follow-up

A local diagnostic was added at `user/analysis-engine/scripts/analyze_stage4_fold.py`. It reuses the same momentum backtest implementation/configuration, lists selected assets and each selected asset's monthly return, reconciles equal-weight gross contributions to the recorded gross strategy return, and flags selected-asset monthly moves whose absolute return meets a configurable threshold. It writes a hash-bearing JSON diagnostic and does not approve ranking.

Run it locally against the same CSV used for the Stage 4 report:

```bash
cd ~/projects/marketsage-acceptance/user/analysis-engine
.venv/bin/python scripts/analyze_stage4_fold.py \
  --input /tmp/marketsage-monthly-stage4/monthly_prices.csv \
  --output /tmp/marketsage-stage4-fold-attribution.json \
  --start-date 2023-10-31 \
  --end-date 2024-03-31 \
  --outlier-return-threshold 1.0
```

The local dataset is not committed, so this repository change cannot truthfully claim that asset-level attribution has already been executed. Review the output's SHA-256 against the Stage 4 report before comparing results. The script's cross-period contribution sums are explicitly additive diagnostics, not compounded P&L attribution.

## Acceptance gaps before any model/strategy approval

1. Attribute each fold and the extreme fold's return to assets and monthly holdings; verify no symbol/price anomaly or portfolio-weight discontinuity.
2. Audit monthly resampling, asset-specific calendars, corporate-action adjustment conventions, missing observations, and whether assumed month-end execution was actually possible.
3. Check survivorship/universe-selection effects and point-in-time availability. A historical price row is not proof that the observation was available to a decision-maker at that time.
4. Report turnover, actual or defensible transaction/slippage assumptions, downside risk, and performance by market regime.
5. Reproduce from a pinned commit and immutable, legally usable dataset. Do not inspect the holdout to tune parameters.
6. Evaluate Iranian-market data separately after source contracts, units, timestamps, historical depth, and rights are approved.
7. Do not describe the current momentum backtest as an AI prediction model or calibrated probability system; no calibrated predictive model has been validated by this report.

## Decision

**Stage 4 remains open.** This report is a transparent record of the observed experiment and follow-up questions, not a pass/fail certification of expected returns. Stage 5 can proceed with operational hardening and staging-readiness work, but neither Stage 5 checklist completion nor CI success enables investment ranking or production release by itself.
