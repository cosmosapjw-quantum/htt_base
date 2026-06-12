# Claim Ledger

**Status**: generated-authority index.

The canonical DAG claim ledger is generated at
`docs/generated/claim_ledger.json` from the same `pr_backlog.yaml` and
`pr_status.yaml` inputs as `docs/generated/status_snapshot.json`. Do not
hand-maintain claim-tier counts or public status rows in this file.

Regenerate the public status sidecars with:

```bash
PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json
```

The generated DAG ledger is diagnostic-only project bookkeeping. It is not
solver validation, transfer validation, posterior evidence, MIO certification,
morphology compatibility, or family-ID evidence. Artifact/result claims still
need their own manifests, transfer provenance, null/mock status, sky-support
metadata when directional, caveats, and validation evidence before use in
reports or manuscripts.
