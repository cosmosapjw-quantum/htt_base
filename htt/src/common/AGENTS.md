# Common Package Guidelines

This file supplements the repo-root `AGENTS.md` for work under `htt/src/common/`.
All commands below assume the repository root.

## Scope
- `htt/src/common/` is the shared low-level Python utility layer used by multiple active packages in `htt/`.
- It owns cross-cutting frozen contracts and reusable helpers such as sky geometry, selection handling, bulk-flow estimation, posterior summarization, and mock calibration.
- Only place code here when it is genuinely shared and package-agnostic.

## Ownership Map
- `contracts.py`: shared wire-format surface for frozen dataclasses such as `PreferredAxis`, `SkySelectionConfig`, `DirectionalSummary`, `DynestyResult`, and `MockCalibrationReport`.
- `sky_geometry.py`, `healpix_selection.py`, `mock_calibration.py`: shared geometry and selection utilities.
- `bulkflow_estimator.py`, `bulkflow_likelihood.py`, `posterior_summary.py`: shared inference helpers that are intentionally package-agnostic.

## Boundary Rules
- Promote code into `common/` only when the semantics are genuinely shared across multiple active packages and no single domain should own them.
- If the logic is solver-specific, posterior-specific, report-specific, or realizability-specific, keep it in `bass/`, `htt/htt/`, `mio/`, or `tsc/`.
- Keep `common/` dependency-light and import-safe. Avoid importing high-level package-specific modules back into `common/`.
- Treat `common.contracts` as a public contract surface. Frozen dataclasses, validation rules, field names, and invariants require coordinated consumer updates and regression coverage.
- Preserve `PreferredAxis.production_allowed`, selection fallback guards, and mock-calibration invariants. These are relied on by downstream HTT and MIO code.
- Prefer extending an existing shared helper over creating a second implementation of the same geometry or selection rule elsewhere.

## Change Checklist
Before committing `common/` changes, verify:
1. the code is genuinely shared and not merely convenient to centralize;
2. no high-level package dependency has been pulled back into `common/`;
3. contract changes have direct unit coverage here and downstream smoke coverage where needed;
4. a second implementation is not being introduced for an already-shared rule.

## Testing
Run the narrowest relevant battery first, then widen only as needed.

- Direct `common/` changes:
  - `venv/bin/python -m pytest htt/src/common -q`
- Contract or shared-helper behavior changes:
  - also run affected downstream suites, typically
    `venv/bin/python -m pytest htt/htt/tests htt/mio/tests -q`
- Every new helper or invariant introduced here must have at least one direct unit test under `htt/src/common/`; consumer-only coverage is not sufficient.

## Stop Conditions
Stop and escalate if:
- the only reason to move code into `common/` is convenience;
- a change would introduce a reverse dependency from `common/` into package-specific modules;
- a public contract change lacks coordinated downstream updates;
- a supposedly shared helper is actually carrying package-specific semantics.
