# AUDIT_PRM-05_TILTED_FAMILY_EXTENSION_2026-04-22

## Scope

- authority: `docs/ver2_upgrade/*`
- packet: `PRM-05-TARGETED-PHYSICS`
- bounded target: close the cheapest remaining representative tilted-family openings without widening science claims

## Current DAG state

- completed prerequisite nodes:
  - `PRM-01-BASS-INTEROP`
  - `PRM-02-BASS-FAMILY-SWEEP`
  - `PRM-03-PRELIM-RESULT-PACKS`
  - `PRM-04-HTT-MIO-HANDOFF`
  - earlier `PRM-05` substep opening representative `Type V` tilted runtime
- chosen substep:
  - re-audit representative `VII_0` tilted blocker against the SDD Codazzi/divergence equations
- forbidden in this packet:
  - non-Type-I exact propagator promotion
  - direction-resolved reionization microphysics
  - exporter/manuscript regeneration

## CoVe / metacognitive audit

### Reconstructed mismatch

- `VII_0` and `VIII` tilted runtime were still failing at the S1 Codazzi stage.
- direct operator inspection showed a contradiction:
  - the SDD `div_rank2` formula predicts a nontrivial class-A helical/semisimple Codazzi operator,
  - but the shipped `div_pstf2(...)` implementation produced a zero-rank operator for `VII_0` / `VIII`.

### Equation-to-code consistency check

- SDD authority:
  - `D_gamma X_{alpha beta} = -Gamma^mu_{gamma alpha} X_{mu beta} - Gamma^mu_{gamma beta} X_{alpha mu}`
  - `div_rank2(X)_alpha = sum_beta D[beta, alpha, beta]`
- shipped code had the first lower-index pair in `Gamma` transposed inside `div_pstf2(...)` and `curl_pstf2(...)`.
- this was not a model/closure choice; it was an equation-to-code mismatch.

## Applied repair

### 1. Restore the SDD rank-2 derivative ordering

- file:
  - `htt/bass/background/geometry.py`
- change:
  - added `covariant_derivative_rank2_homogeneous(...)`
  - rewired `div_pstf2(...)` and `curl_pstf2(...)` to use the SDD index order directly

### 2. Guard the restored operator with geometry tests

- file:
  - `htt/bass/background/test_ver2_algebra_geometry_skeleton.py`
- change:
  - added explicit derivative-definition tests for `VII_0` / `VIII`
  - added a Codazzi-operator nontriviality regression for the class-A helical/semisimple representative families

### 3. Keep Codazzi acceptance numerically honest at large momentum scale

- file:
  - `htt/bass/background/initial_conditions.py`
- change:
  - `project_shear_to_codazzi(...)` / `project_tilted_codazzi(...)` now use an absolute-plus-relative acceptance criterion
  - this preserves the old bounded `Type V` executable path under the corrected geometry operator while still rejecting genuinely unsupported targets such as the `VIII` x-axis tilt

### 4. Promote the newly opened representative tilted subset

- files:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py`
  - `htt/bass/validation/ver2_campaign_evidence.py`
  - `htt/bass/validation/test_ver2_campaign_evidence.py`
  - `htt/workspace/contracts/validation_registry.py`
  - `htt/workspace/contracts/tests/test_ver2_validation_registry.py`
- change:
  - representative executable tilted subset is now:
    - `V`
    - `VII_0`
    - `VIII` with algebra-aware representative tilt axis
  - remaining controlled blocker is now:
    - `I`

## What is genuinely fixed

- `VII_0` tilted no longer fails because of a geometry index-order bug.
- representative `VIII` tilted runtime is also executable once the representative sweep uses an algebra-aware admissible tilt axis instead of the old blanket x-axis default.
- the representative family sweep now matches current code reality:
  - orthogonal `I/V/VII_0/VIII`: executable
  - tilted `V/VII_0/VIII`: executable
  - tilted `I`: explicit blocker

## What remains uncertain

- `Type I` tilted still does not run under the current all-species common-velocity construction.
- non-Type-I exact propagator remains unresolved.
- direction-resolved microphysics remains unresolved.

## Verification

- `venv/bin/python -m py_compile` on touched files: pass
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/background/test_ver2_algebra_geometry_skeleton.py -q`
  - `46 passed`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime/test_ver2_tier_b_execution.py::test_representative_tilted_family_sweep_is_controlledly_blocked htt/bass/runtime/test_ver2_tier_b_execution.py::test_representative_tilted_executable_families_execute_with_bounded_runtime_contracts htt/bass/validation/test_ver2_campaign_evidence.py::test_representative_family_sweep_evidence_passes_with_bounded_orthogonal_subset htt/bass/validation/test_ver2_campaign_evidence.py::test_representative_family_sweep_payload_is_json_ready htt/workspace/contracts/tests/test_ver2_validation_registry.py::test_bass_representative_family_sweep_records_tilted_runtime_blocker -q`
  - `7 passed`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --family-sweep-check`
  - `PASS`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check`
  - `PASS`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_hostile_audit.py --check`
  - `PASS`

## Narrowed claim

- allowed:
  - representative preliminary family sweep now includes executable tilted `V/VII_0/VIII`
- still blocked:
  - representative `Type I` tilted runtime
  - full all-type tilted closure
  - non-Type-I exact propagator promotion
