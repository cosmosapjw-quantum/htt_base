# AUDIT_BF-04B-COV_2026-04-21

## Packet

- `BF-04B-COV`
- Lane: `B`
- Commit prefix: `V2-B4:`
- SSOT: `docs/ver2_upgrade/*`

## Scope

- `htt/bass/observational/*`
- `htt/bass/spectrum/off_diagonal_covariance.py`
- selected `htt/workspace/contracts/*`
- related tests only

## RE2 Summary

Two RE2 passes were applied against:

1. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_03_BASS_COMPLETION.md`
2. `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
3. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
4. `docs/ver2_upgrade/BASS_HTT_MIO_TSC_observable_atlas_SDD_WBS_PR_plan.md`
5. `docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md`

The target was narrow and explicit: reduce the O-lane `sparse_mode_block_proxy` footprint where live angular reconstruction now exists, without pretending that a full BiPoSH inversion has already been validated.

## Three Verification Lanes

### 1. Internal docs + local code

- confirmed that `BF-03B-ANG` now provides live PSTF sphere reconstruction payloads
- confirmed that the old O-lane still classified live morphology as `sparse_mode_block_proxy`
- confirmed that the right packet-level move is to introduce an explicit low-`ell` harmonic sparse basis reduction, not to overclaim full BiPoSH

### 2. Web CRAG

- not needed for this packet
- no new external theorem or literature-dependent physics claim was introduced beyond the already-frozen observable-atlas and MES notes

### 3. Integrated phys-math-code audit

- contract reconstruction:
  - covariance/morphology summaries must be built from live angular/PSTF content when available
  - basis reduction may still remain no-claim if it is not a validated full BiPoSH inversion
- mapping audit:
  - old `build_sparse_covariance_proxy(...)` exposed only `mode`-block sparse rows
  - live `SolverCoreOutput.alm_T` now carries enough reconstruction metadata to support a stronger reduction

## Divergence -> Verification -> Convergence

Candidate layouts considered:

1. keep `sparse_mode_block_proxy` everywhere and only change caveat wording
2. promote the current mode-block sparse rows directly to full `BiPoSH`
3. convert live covariance into an explicit `(ell,m; ell',m')` sparse harmonic basis when angular reconstruction support is present, while keeping full-BiPoSH claims blocked

Converged choice: **3**

Why:

- narrows the proxy region materially
- preserves equation-form/live-output dependence from `BF-03B-ANG`
- avoids a false claim that a validated invariant BiPoSH inversion already exists

## Implemented Closure

- `htt/bass/spectrum/off_diagonal_covariance.py`
  - adds `build_sparse_harmonic_entries(...)`
  - converts the dense low-`ell` covariance view into unique explicit harmonic sparse entries `(ell,m; ell',m')`
- `htt/bass/observational/covariance_sparse.py`
  - adds an angular reconstruction guard keyed to the live sphere-reconstruction payload
  - upgrades live outputs from `sparse_mode_block_proxy` to `low_ell_harmonic_sparse_basis` when the guard passes
  - keeps `supports_full_biposh=False` and records `basis_reduced_not_full_biposh`
- `htt/bass/observational/observable_vector_builder.py`
  - passes the live angular payload into covariance/morphology reduction
  - narrows the old proxy caveat to a basis-reduced no-claim caveat when appropriate
- `htt/bass/observational/atlas_entry_lite_builder.py`
  - propagates `basis_reduction_status` and `angular_reconstruction_guard`
- `htt/workspace/contracts/validation_registry.py`
  - teaches the validation registry about the new no-claim vocabulary

## What This Packet Does Not Claim

- no full BiPoSH inversion
- no validated local/global overlap calibration
- no validated nuisance/noise covariance model
- no promotion from basis-reduced morphology to science-grade geometry evidence

## Verification

- `venv/bin/python -m py_compile htt/bass/observational/covariance_sparse.py htt/bass/spectrum/off_diagonal_covariance.py htt/bass/observational/observable_vector_builder.py htt/bass/observational/atlas_entry_lite_builder.py htt/bass/observational/test_ver2_observable_atlas.py htt/workspace/contracts/validation_registry.py`
- `venv/bin/python -m pytest htt/bass/observational/test_ver2_observable_atlas.py htt/bass/observational/test_ver2_mes_departure.py htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py -q`
  - `39 passed, 1 warning`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check`
  - `PASS`
- `venv/bin/python -m pytest htt/workspace/contracts/tests -q`
  - `44 passed`
- `venv/bin/python -m pytest htt/bass/observational -q`
  - `88 passed, 1 warning`
- `venv/bin/python -m pytest htt/bass/test_ver2_public_surface.py htt/bass/spectrum/test_fb72_off_diagonal_covariance_skeleton.py -q`
  - `33 passed`

Known warning left unchanged:

- recombination-table early-`z` coverage warning from `bass/species/registry.py`

## Carry-forward After This Packet

- `BF-05B-VAL`: validate the new basis-reduced covariance path against nulls/injections/cutoff campaigns
- `BF-06B-LIKE`: bind observer/likelihood/inference only after those validation ceilings are discharged
- local/global discrimination and full BiPoSH promotion remain blocked pending later evidence
