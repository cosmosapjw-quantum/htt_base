# Legacy Theorem-To-Test Audit Map

PR-032 retains a legacy theorem-to-test audit map for `TSC_LEGACY`
reproducibility. The generated artifact is
`docs/generated/theorem_to_test_map_legacy_tsc.json`.

## Purpose

The map is audit only. It links legacy TSC/Teff theorem labels to historical
test witnesses and validation obligations so reviewers can see why the
trace/source chart diagnostics were deprecated as active science ownership
without losing the audit trail.

The strongest allowed claim is diagnostic-only status: the repository preserves a
manifest-backed audit map from legacy theorem labels to test witnesses. This is
not production validation, not HTT evidence, not a MIO certificate, not transfer
validation, not native solver validation, and not family identification.

## Boundary

Legacy theorem labels remain `TSC_LEGACY` provenance. They do not establish
observable adequacy, null calibration, mask or covariance support, response-rank
support, morphology compatibility, or geometry/family evidence.

The active replacement for reusable guard behavior is `common.semantic_guards`,
which keeps source status, propagation status, and observable status separate.
The audit map does not override those guards and cannot promote a trace/source
diagnostic into an observable or spin-2 production claim.

## Regeneration

Regenerate the JSON artifact with:

```bash
venv/bin/python scripts/codex_harness/generate_theorem_to_test_map.py --write docs/generated/theorem_to_test_map_legacy_tsc.json
```

Validate the boundary with:

```bash
venv/bin/python -m pytest tests/contracts/test_theorem_to_test_map.py -q
```
