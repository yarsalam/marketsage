# Repository cleanup — Iranian equity evidence branch

Date: 2026-11-26

This is a focused replacement for the oversized Iranian-equity research notebook PR.

## Retained

- Original TSETMC raw captures, source transport records, identity records and instrument histories.
- Original CODAL documents, attachments, extracted text, candidate lookups and manifests.
- Event ledgers, identity files, evidence registers, run manifests, SHA-256 inventories and validation summaries.
- Focused adjustment research documents, the evidence importer, TSETMC history/identity audits, comparison tools and tests.

## Excluded from this branch

- Vendored `node_modules` files under the TSE Client validation environment. The `package.json` and `package-lock.json` remain for reproducible installation.
- Nine byte-identical duplicate outputs under `three_symbol_audit_results/`; the canonical copies remain at the parent audit-run paths.
- The general ten-tab product roadmap and stale project-governance snapshots unrelated to the adjustment evidence pipeline.

The original notebook branch remains available for recovery. No raw TSETMC payload, primary CODAL document, event ledger, identity record or canonical run manifest was removed from this focused branch.
