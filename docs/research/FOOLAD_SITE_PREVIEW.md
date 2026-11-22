# پیش‌نمایش پژوهشی قیمت تعدیل‌شده فولاد در رابط بازارها

- Work ID: `MS-FOOLAD-SITE-TABS-20261122-01`
- Status: `CORRECTED_CANDIDATE_REVIEW_REQUIRED`
- Instrument: فولاد مبارکه اصفهان، `insCode=46348559193224090`
- Daily candidate source period: 2007-03-11 through 2026-11-11
- Daily candidate rows: 4,680
- Site preview: 80 quarter-end observations sampled from the daily candidate; this is a display preview, not the complete daily file.
- Candidate SHA-256: `2ab88633b63026f5ff4ab326cc981264014da59d5862d2944aee2f17e5eac8a3`
- Source archive SHA-256: `81c4e831fcc3fd4fe7767f71f58c57b40bbf2b5bd9cd12ba241ae4513551baea`

## Adjustment correction shown in the preview

The separate 2022-08-09 share-count change (293bn to 530bn shares) is retained independently from the 2022-08-03 1,700-Rial DPS adjustment. The prior +/-7-calendar-day suppression rule incorrectly treated these distinct events as one. The corrected candidate applies both events separately.

## Known limitations

- 285 close-vs-OHLC violations are inherited from the raw input.
- 414 daily rows have zero volume.
- Arithmetic identity `close_adjusted = close_raw × adjustment_factor` has zero mismatches; this does not prove economic correctness.
- Corporate-action completeness, full independent chart reconciliation and the official trading calendar are not verified.
- The complete daily candidate CSV is not included in this site preview; only the 80-point quarterly display sample is committed here.
- The instrument and source remain quarantined. Scoring, ranking, allocation and backtesting are disabled.

## UI behavior

The market-family tabs separate Iranian equities, gold/coins, FX, fixed income/funds, local crypto and global proxies. Only the equities tab currently shows the Foolad preview. Other tabs expose their registered source/readiness state and do not fabricate prices.
