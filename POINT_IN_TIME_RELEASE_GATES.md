# Point-in-time release gate checklist

Use this checklist as a finite acceptance gate for each data-source integration batch. A batch is complete when all applicable checks pass; adding more tests is not itself a release objective.

## Required automated checks

- [ ] Parsing rejects malformed, duplicate, non-finite, or identity-incomplete records.
- [ ] All timestamps are timezone-aware; unknown source publication times remain null.
- [ ] Captured replay uses only records retrieved by the cutoff.
- [ ] Source-vintage replay excludes records with unknown publication time and uses only publisher vintages available by the cutoff.
- [ ] Revisions remain append-only and retries are idempotent.
- [ ] Every candidate or unregistered source remains blocked by the production scoring gate.
- [ ] Data units, source rights, historical coverage, corrections, and production-host connectivity are documented before approval.
- [ ] The full CI workflow, including production image builds, passes on the exact candidate commit.

## Batch and stop policy

Group related parser, validation, lineage, and regression tests into one commit and let CI run the full suite once. If a check fails, fix the failing batch and rerun CI; do not add unrelated experiments to the same change. Once all checks pass, record the evidence and move to the next defined release gate. Do not enable production scoring solely because CI is green: CI validates code behavior, not provider rights, data truth, or investment performance.
