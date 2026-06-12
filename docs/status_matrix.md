# Status Matrix

**Status**: generated-authority index.

The canonical public status matrix is generated at
`docs/generated/status_matrix.md` from `docs/generated/status_snapshot.json`.
Do not hand-edit module, test, PR, validation, or readiness counts here.

Regenerate the public status sidecars with:

```bash
PYTHONPATH=htt/src python -m common.status_snapshot --write docs/generated/status_snapshot.json
```

This index is diagnostic DAG bookkeeping only. It is not solver validation,
transfer validation, posterior evidence, MIO certification, morphology
compatibility, or family-ID evidence.
