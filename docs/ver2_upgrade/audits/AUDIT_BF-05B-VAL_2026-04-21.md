# AUDIT_BF-05B-VAL_2026-04-21

## Scope

- `htt/bass/hierarchy/contractions.py`
- `htt/bass/validation/ver2_campaign_evidence.py`
- `htt/bass/validation/test_ver2_campaign_evidence.py`
- `htt/scripts/ver2_bass_validation.py`
- `htt/workspace/contracts/validation_registry.py`
- related tests and VER2 validation docs/ledgers

## Intent

Close the BASS-centered validation gap by promoting validation from registry-only state to executable evidence where the shipped physics path is actually closed, without overpromoting the still-open science-facing surfaces.

## RE2 Reconstruction

### Physical / algorithmic target

1. Validate the shipped native Tier-B route, not a surrogate.
2. Bind null recovery, seed/startup persistence, Tier-A↔Tier-B comparison, cutoff behaviour, and live hook consumption to one executable evidence surface.
3. Keep non-Type-I exact propagation and full BiPoSH science claims outside the promoted envelope.

### Divergence

1. Promote the existing `warn` campaigns directly to `pass`.
2. Add a new bounded BASS-only executable campaign and keep the broader science-facing campaigns at `warn`.
3. Defer BF-05 entirely until a full non-Type-I exact propagator exists.

### Convergence

Option 2 was selected.

- Option 1 would have overclaimed observable/morphology/injection/MES validation that still depends on unresolved propagator and nuisance-model work.
- Option 3 would have left the now-closed Type-I native runtime path without executable campaign-grade evidence.

## Findings

### P0 false cutoff blocker

- The shipped `L=8` cutoff path was not actually executable because STF unpack hit a hard eager-cache ceiling in `bass.hierarchy.contractions`.
- This was not a physics limitation; it was an implementation artifact. The hierarchy requests intermediate higher-rank tensors even when the public development cutoff is `L <= 8`.
- Fix: `stf_basis(ell)` now builds higher-rank STF bases on demand instead of throwing `NotImplementedError` above `L_MAX_CACHED`.

### P1 validation gap

- The registry already contained machine-resolved campaign links, but no bounded executable `pass` campaign existed for the shipped native Tier-B physics path.
- Fix: added `validation.bass_native_runtime_bridge`, plus a new theorem, null manifest, injection manifest, and hostile-audit runbook.

### P1 overpromotion risk

- The broader observable/null/injection/MES campaigns still do not justify `pass`.
- Fix: those campaigns remain `warn`; only the bounded Type-I native runtime bridge is promoted.

## Implemented Surfaces

- `bass.validation.build_type_i_runtime_validation_evidence`
- `bass.validation.type_i_runtime_validation_payload`
- `htt/scripts/ver2_bass_validation.py`
- registry additions:
  - `V8_bass_native_runtime_bridge`
  - `validation.bass_native_runtime_bridge`
  - `null.bass.type_i_native_runtime`
  - `validation.injection.native_seed_startup`
  - `runbook.bass_native_runtime`

## Contract / Mapping Audit

| Claim | Executable path | Status |
|---|---|---|
| Type-I native observable null recovery | `execute_tier_b_solver` -> `build_observable_vector_from_solver_output` | passed |
| Seed survives without startup manifold | `execute_tier_b_solver` with lowered `Gamma_T/H` gate | passed |
| Tier-A↔Tier-B bounded agreement | `execute_tier_a_validation_solver` + `compare_tier_a_to_tier_b` | passed |
| Cutoff campaign is executable | `run_executed_cutoff_campaign` through native Tier-B route | passed for default `L=4,6`; `L=8` now unblocked structurally and remains opt-in extended evidence |
| Live hook ownership preserved | native Tier-B trace / propagator metadata | passed |

## Verification

- `venv/bin/python -m py_compile htt/bass/validation/ver2_campaign_evidence.py htt/bass/validation/test_ver2_campaign_evidence.py htt/scripts/ver2_bass_validation.py htt/workspace/contracts/validation_registry.py htt/bass/hierarchy/contractions.py htt/bass/hierarchy/test_contractions.py`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/validation/test_ver2_campaign_evidence.py htt/bass/runtime/test_ver2_tier_a_validation.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/hierarchy/test_contractions.py htt/workspace/contracts/tests/test_ver2_validation_registry.py -q`
  - `66 passed, 1 warning`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_validation_registry.py --check`
  - passed
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_hostile_audit.py --check`
  - passed
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --check`
  - passed

## Carry-Forward

1. The new `pass` campaign is intentionally limited to the shipped Type-I native route.
2. The default BF-05 cutoff gate uses `L=4,6`; a heavier `L=8` sweep remains explicit extended validation rather than the default check path.
3. Observable/morphology/injection/MES science-facing campaigns remain `warn`.
