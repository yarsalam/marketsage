# Repository cleanup — Iranian equity evidence branch

Date: 2026-11-26

This branch is the focused evidence and orchestration base for the Iranian equity adjustment workstream.

## Preserved

- Original raw TSETMC captures for فولاد، پارسیان and وغدیر, including daily history and corporate-action endpoints.
- Original CODAL primary documents, attachments, HTML/text captures and per-run acquisition records.
- Canonical event ledgers, identity files, source registers, acceptance summaries and import/run manifests.
- Original TSETMC official-chart transport responses and transport metadata; decoded comparison exports can be regenerated from those captures.
- Focused research scripts, event investigation notes, the inherited SHA-256 inventory and the Foolad orchestration pilot.

## Excluded from the delivery diff

- Vendored `node_modules` files; package manifests remain for reproducible installation.
- Nine byte-identical nested audit outputs.
- Large generated diagnostics and comparison CSVs, prior derived adjusted/total-return series, and duplicated review exports.
- Generated chart-decoding CSVs and the large zipped factor-diagnostic bundle. Original binary chart responses and transport metadata remain.

The prior notebook branch and its complete history remain available for recovery. Original raw TSETMC payloads and primary CODAL documents are retained. The SHA-256 inventory contains the inherited hash entries that apply to retained files; per-run manifests remain preserved for their source artifacts.
