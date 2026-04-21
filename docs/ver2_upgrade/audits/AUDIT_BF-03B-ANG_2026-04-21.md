# AUDIT_BF-03B-ANG_2026-04-21

## Packet

- `BF-03B-ANG`
- Lane: `B`
- Commit prefix: `V2-B3:`
- SSOT: `docs/ver2_upgrade/*`

## Scope

- `htt/bass/forward/*`
- `htt/bass/runtime/*`
- `htt/bass/observational/*`
- related tests only

## RE2 Summary

Two RE2 passes were applied against:

1. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_03_BASS_COMPLETION.md`
2. `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
3. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
4. `docs/ver2_upgrade/lowell_bianchi_solver_SDD_PR_WBS_pstf_tetrad.md`

The convergence target was narrow and load-bearing: stop reporting the observer-side PSTF bridge as pending, and replace final-slice-only neutral exports with live equation-form PSTF sphere reconstruction.

## Three Verification Lanes

### 1. Internal docs + local code

- confirmed that `project_from_angular_samples(...)` and `reconstruct_on_sphere(...)` were already live in `htt/bass/hierarchy/pstf_radiation.py`
- confirmed that the remaining debt sat in `htt/bass/forward/ver2_solver_output.py` and `htt/bass/observational/observable_vector_builder.py`
- confirmed that O-lane still reported `final_slice_only_no_sphere_reconstruction`

### 2. Web CRAG

- not needed for this packet
- no new external physics claim, normalization, or citation was introduced beyond the already-frozen SDD equation contract

### 3. Integrated phys-math-code audit

- target reconstruction: final PSTF towers must be reconstructed on a unit-sphere quadrature rule exact enough to recover the same polynomial content up to retained `L`
- contract check: observer-neutral export may carry angular samples, but must not silently promote proxy morphology/covariance or posterior semantics
- mapping check: O-lane status must be derived from live reconstructed angular payloads, not stale proxy metadata

## Divergence -> Verification -> Convergence

Candidate layouts considered:

1. keep `alm_*` as final-slice-only payloads and just relabel O-lane status
2. move reconstructed samples into `map_T/Q/U`
3. keep coefficient payloads in `alm_*`, add exact quadrature sphere samples beside them, and let O-lane read the live reconstruction payload

Converged choice: **3**

Why:

- preserves existing observer-neutral coefficient payloads and determinism checks
- avoids misusing `map_Q/U` as if they were already calibrated Stokes-field exports
- closes the SDD reconstruction bridge with minimal write scope

## Implemented Closure

- `htt/bass/forward/ver2_solver_output.py`
  - adds deterministic tensor-product sphere quadrature
  - reconstructs `{I,E,B}` samples from the final PSTF state
  - exports coefficient values plus exact quadrature sphere samples together in the neutral `alm_*` payloads
- `htt/bass/observational/observable_vector_builder.py`
  - recognizes live sphere-reconstructed payloads
  - promotes `observer_reconstruction_status` to `sphere_reconstructed_from_pstf`
  - records quadrature metadata in `alm_features`
- tests updated in:
  - `htt/bass/forward/test_ver2_solver_output.py`
  - `htt/bass/runtime/test_ver2_tier_b_execution.py`
  - `htt/bass/observational/test_ver2_observable_atlas.py`

## What This Packet Does Not Claim

- no promotion of `sparse_mode_block_proxy` into validated morphology
- no claim that non-Type-I source propagation is exact
- no claim that covariance/noise/nuisance handling is fully validated
- no promotion of observer-neutral angular samples into interpreted sky maps or posteriors

## Verification

- `venv/bin/python -m py_compile htt/bass/forward/ver2_solver_output.py htt/bass/observational/observable_vector_builder.py htt/bass/forward/test_ver2_solver_output.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/observational/test_ver2_observable_atlas.py`
- `venv/bin/python -m pytest htt/bass/forward/test_ver2_solver_output.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/observational/test_ver2_observable_atlas.py -q`
  - `15 passed, 1 warning`
- `venv/bin/python -m pytest htt/bass/observational/test_ver2_mes_departure.py -q`
  - `4 passed`
- `venv/bin/python -m pytest htt/bass/forward htt/bass/runtime htt/bass/observational -q`
  - `258 passed, 1 warning`
- `venv/bin/python -m pytest htt/bass/test_ver2_public_surface.py -q`
  - `2 passed`

Known warning left unchanged:

- recombination-table early-`z` coverage warning from `bass/species/registry.py`

## Carry-forward After This Packet

- `BF-04B-COV`: covariance/morphology promotion still remains explicit proxy/no-claim territory
- `BF-05B-VAL`: validation campaigns still need executable evidence beyond current warn/registry status
- exact non-Type-I source propagation remains outside this packet
