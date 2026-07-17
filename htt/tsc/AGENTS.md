# TSC Package Guidelines

This file supplements the repo-root `AGENTS.md` for work under `htt/tsc/`.
All commands below assume the repository root.

## Scope
- `htt/tsc/` retains legacy Paper I `T_eff` chart mathematics, admissibility criteria, diagnostics, and explicit cross-check-only integration helpers for reproducibility.
- Keep chart transforms, realizability logic, filling-fraction diagnostics, and related mathematical mirrors here rather than in `bass/` or `htt/htt/`.
- New claim-bearing framework artifacts must treat this package as `TSC_LEGACY` with `tsc_legacy` implementation scope and legacy-reproduction-only bundle authority.

## Ownership Map
- `charts`: forward/inverse chart transforms, perturbative coefficients, basis utilities, and frozen mirrors such as the Michaelis-Menten export.
- `diagnostics`: tangency, entropy invariants, spherical quadrature, filling fraction, and related report helpers.
- `admissibility`: realizability tests and the three-bound hierarchy.
- `integration`: explicit cross-check channels such as `ff_htt_mc_cross_check`; these are comparisons, not merged estimators.

## Boundary Rules
- TSC legacy retains chart meaning and physical-realizability reproduction surfaces. It does not own runtime allow/block decisions, `CanonicalDecision`, or `ValidationLabel` construction.
- TSC legacy does not own HTT posterior/evidence, MIO certificates, BASS transfer/native-solver validation, OBSSTAT features, or Bianchi family identification.
- Production code under `tsc/` must not import `bass.runtime`, `bass.tilt`, or `bass.validation`. Preserve the ownership freeze without ad hoc whitelists.
- Prefer TSC-local mirrors for shared coefficients or chart-level constants instead of reaching into forbidden BASS runtime or validation modules.
- Cross-package links must remain explicit cross-checks, for example `compare_against_htt_bounds`, `assert_mirror_matches_bass_ssot`, and `ff_htt_mc_cross_check`. Never export merged HTT+TSC or BASS+TSC scores.
- Preserve frozen dataclasses and `is_cross_check=True` semantics on TSC report types. Combined interpretation belongs in documentation or a separate comparison layer, not in the report schema.

## Change Checklist
Before committing TSC changes, verify:
1. chart meaning and admissibility remain legacy reproduction surfaces;
2. no runtime allow/block semantics leaked in from BASS;
3. cross-check helpers still report comparisons rather than verdict fusion;
4. mirror constants were not imported from forbidden runtime/validation modules.

## Testing
Run the narrowest relevant battery first, then widen only as needed.

- Normal TSC changes:
  - `venv/bin/python -m pytest htt/tsc -q`
- Ownership / package-boundary changes:
  - `venv/bin/python -m pytest htt/test_ownership_freeze.py -q`
- Cross-check or SSOT-mirror surfaces:
  - `venv/bin/python -m pytest htt/tsc/integration/test_htt_bridge.py -q`
  - `venv/bin/python -m pytest htt/tsc/admissibility/test_three_bound_hierarchy.py -q`
  - `venv/bin/python -m pytest htt/tsc/charts/test_michaelis_menten_export.py -q`

## Stop Conditions
Stop and write a decision note if:
- a change appears to require `CanonicalDecision` or `ValidationLabel` construction inside TSC;
- a TSC report wants to expose merged HTT/TSC or BASS/TSC scalar results;
- a mirror constant can only be obtained by importing forbidden BASS runtime/validation code;
- a cross-check helper is starting to behave like a production gate.
- a new artifact wants `owner="TSC"` without canonical normalization to `TSC_LEGACY`.
