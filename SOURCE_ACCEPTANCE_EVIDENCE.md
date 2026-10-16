# Data-source acceptance evidence

The source registry describes the checks required for each provider. This file
defines the companion evidence format and a finite review procedure.

## Run the evaluator

From `user/analysis-engine`:

```bash
python source_acceptance.py path/to/source-evidence.json
```

Exit codes: `0` means the evidence is complete **and** the independent registry
gate already allows scoring; `1` means the evidence is incomplete/invalid or
the registry still blocks scoring; `2` means required evidence is missing or
failed; `3` means the input file/JSON/CLI is invalid. The JSON report is the
source of detail; a complete evidence checklist does not imply production approval.

## Evidence contract

Each evidence JSON object must include:

- `source_id`: an exact registered source ID.
- `reviewer`: non-empty reviewer identifier.
- `reviewed_at`: ISO-8601 timestamp with timezone.
- `rights_review`, `host_connectivity`, `timestamp_quality`,
  `historical_coverage`, and `unit_reconciliation`: each `passed`,
  `failed`, or `pending`.
- `checks`: one entry for every source-specific `required_checks` item in the
  registry and no unknown check names. Each entry contains a status and a
  non-empty evidence reference (for example, a path to a review note or fixture).

Never place credentials, tokens, personal data, or licensed raw datasets in the
evidence file. Evidence references should point to appropriately access-controlled
review artifacts.

## Review and stop policy

1. Run the evaluator and address only the reported missing/failed items.
2. Have a human review source rights, identity, timestamps/revisions, units,
   history, and production-host access against primary evidence.
3. Keep the source blocked until the registry status, timestamp quality, and
   production approval are deliberately reviewed in a separate change.
4. Re-run the complete CI suite on that exact candidate commit.

This evaluator is intentionally advisory: it cannot edit registry approval flags,
and does not fetch providers or certify investment performance. CI success only
proves tested code behavior, not source truth, legal rights, or profitable signals.
