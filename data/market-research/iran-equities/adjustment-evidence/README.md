# Iranian equity adjustment evidence store

Status: research-only, evidence collection and validation; no factor or series is approved by this directory.

## Instruments
- `vaghdir/` — وغدیر
- `foolad/` — فولاد
- `parsian/` — پارسیان

## Per-symbol layout
Each symbol directory keeps these evidence classes separate:
- `raw/`: immutable TSETMC/TSE Client source payloads and daily history snapshots
- `codal/`: original CODAL notices, attachments, amendments and extracted text
- `other_sources/`: issuer notices, official publications, exchange notices and clearly-labelled secondary locators
- `calculations/`: reproducible event-term calculations and factor direction/units
- `outputs/`: candidate price-basis and total-return series, never overwriting raw series
- `validation/`: manifests, hashes, coverage, chart comparisons and test reports

Large raw datasets and binary CODAL attachments should remain in the owner-controlled data store until a reviewed storage policy exists. This Git directory contains indexes, manifests, source references and reproducible code; do not commit secrets or overwrite raw snapshots.

## Source-of-truth boundary
A provider adjustment row or a price gap is a discovery lead, not proof of event type or terms. CODAL/issuer primary evidence establishes economic terms; actual market records establish the first affected trading session; calculations are independent; provider and external chart data are reconciliation targets, not economic authority.

Keep separate:
1. raw market prices;
2. corporate-action price-basis adjusted prices;
3. total-return series.

Never apply an unresolved factor. Unknown, conflicting or incomplete events must remain quarantined.

## Local source store
Previously recorded owner-side source root:
`/home/nima/marketsage-data/tsetmc-three-adjusted`

This local path is not automatically available to GitHub or this remote session. The manifests in each symbol folder record expected source artifacts and their current evidence state. Import data only with SHA-256, retrieval metadata and original filenames preserved.

## Acceptance
An interval can be considered only after security identity, event terms, chronology/effective session, independent calculation, provider reconciliation and official-chart comparison have all passed. This directory does not itself approve investment use, scoring, ranking, backtesting or production.



## Controlled import and repository visibility

This repository is **public**. Commit only source material that is approved for public redistribution. Never copy credentials, private keys, local configuration, personal files or unrelated Downloads into this evidence store.

Use `scripts/research/import_iran_equity_evidence.py` from a local clone of this branch to copy selected owner-side evidence into this directory. The importer:
- copies rather than moves the source files;
- preserves the three exact TSETMC instrument-search records and raw snapshots;
- preserves `insCode2`–`insCode4` as unverified related identifiers and does not use them for matching;
- archives the two original acceptance-review CSVs as deterministic `.csv.gz` files;
- emits per-symbol primary-InsCode-only, deduplicated evidence extracts with source CSV row references;
- copies the selected shared chart, diagnostic, audit and TSE Client folders under `_shared/`, whether they are directly under the TSETMC folder or its parent data folder;
- writes an import manifest and SHA-256 checksums;
- refuses to overwrite an existing raw file with different bytes and flags single stored files over the configured 95 MiB limit.

Example, from the repository root after checking out the research branch:

```bash
python3 scripts/research/import_iran_equity_evidence.py \
  --repo-root . \
  --source-root "$HOME/marketsage-data/tsetmc-three-adjusted" \
  --evidence-root "$HOME/marketsage-data" \
  --acceptance-review-root "$HOME/marketsage-data/acceptance-review/20261023T193750Z" \
  --confirm-public-repo
```

The importer does not alter the source store. Review oversized-file reports before choosing Git LFS or another storage method; do not silently omit them.

## Codespaces and automated checks

The `.devcontainer/devcontainer.json` environment provides Python 3.12 for this research branch. No forwarded service port is needed for data-processing tests. The `Iran Equity Evidence Integrity` workflow verifies the importer and checks every imported file against its manifest on branch pushes and pull requests.


## Research operating standards

The research branch now defines the cross-symbol workflow and ten-tab release gates:
- \`docs/research/MARKETSAGE_RESEARCH_OPERATING_STANDARD.md\`
- \`docs/research/MARKETSAGE_TEN_TAB_PRODUCT_AND_API_ROADMAP.md\`

The full Iranian instrument count remains unknown until a complete, permissioned, as-of instrument-master snapshot has been imported and deduplicated by canonical instrument identity. The three folders here are pilot instruments, not the full market universe.

## TSETMC event-feed identity audit

The event-feed InsCode is checked against the exact ticker record's primary InsCode. Related fields insCode2/3/4 are reported but are not automatically treated as aliases. A mismatched feed ID remains unresolved until source/identity history proves the relationship.


## Instrument identity audit update — 2026-11-15

The feed-level identifier audit found unresolved price-adjust InsCode mismatches for وغدیر and پارسیان. Their event rows remain quarantined; related/legacy identifiers are not assumed aliases. فولاد's two TSETMC event feeds match its exact ticker record primary InsCode. See _shared/identity_integrity/tsetmc_event_feed_identity_audit_2026-11-15.json and the per-symbol source-register/README updates.


**Checksum scope:** `SHA256SUMS.txt` contains exactly the immutable imported payloads in `import_manifest.json`. Editable README, identity and source-register metadata are reviewed through Git commits and are not part of that immutable source-payload checksum list. The CI verifier requires the checksum list to match the manifest exactly.
