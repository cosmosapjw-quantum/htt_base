# AUDIT_PRM-05_TARGETED_PHYSICS_2026-04-22

## Scope

- authority: `docs/ver2_upgrade/*`
- packet: `PRM-05-TARGETED-PHYSICS`
- bounded target: open the cheapest representative tilted runtime path without widening claim ceilings

## Current DAG state

- completed prerequisite nodes:
  - `PRM-01-BASS-INTEROP`
  - `PRM-02-BASS-FAMILY-SWEEP`
  - `PRM-03-PRELIM-RESULT-PACKS`
  - `PRM-04-HTT-MIO-HANDOFF`
- chosen substep:
  - representative `Type V` tilted runtime
- forbidden in this packet:
  - non-Type-I exact propagator promotion
  - direction-resolved reionization microphysics
  - exporter/manuscript regeneration

## CoVe / metacognitive audit

### Reconstructed mismatch

- `build_tilted_initial_conditions(...)` for `Type V` already admits the all-species global-tilt state.
- the shipped blocker was not S1 background construction itself.
- the blocker sat in the BF-02 seed path:
  - `Ver2TierBIntegrator._build_seeded_initial_state()`
  - `project_packed_regular_seed(...)`
  - `build_constraint_projection(...)`
- the seed projection was re-imposing an orthogonal-style symbolic momentum target instead of reusing the runtime background's actual Codazzi target.

### Equation-to-code consistency check

- SDD authority remains the 1+3 PSTF/tetrad constraint path.
- for a tilted branch, the seed insertion should remain compatible with the already-admitted background Codazzi surface.
- re-projecting an already-admissible `sigma_ab` through a large-scale pseudoinverse solve was an implementation artifact, not a required physics step.

## Applied repair

### 1. Runtime-target-aware seed projection

- file:
  - `htt/bass/hierarchy/seed_compatibility.py`
- change:
  - `build_constraint_projection(...)` and `project_packed_regular_seed(...)` now accept an optional `target_q`.
  - when `sigma_ab` already lies on the requested Codazzi surface, the seed projection reuses it directly instead of numerically re-projecting it.

### 2. Seed injection now uses the actual admitted S1 initial surface

- file:
  - `htt/bass/hierarchy/ver2_native_integrator.py`
- change:
  - seed projection now uses:
    - `background_monitor.initial_conditions.sigma_ab`
    - `background_monitor.initial_conditions.matter.q`
  - instead of the drifted post-evolution first-sample `sigma_tensor[0]`.

### 3. Representative sweep semantics upgraded honestly

- files:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py`
  - `htt/bass/validation/ver2_campaign_evidence.py`
  - `htt/bass/validation/test_ver2_campaign_evidence.py`
  - `htt/workspace/contracts/validation_registry.py`
  - `htt/workspace/contracts/tests/test_ver2_validation_registry.py`
- change:
  - `Type V` tilted now executes as a bounded representative runtime branch.
  - `I`, `VII_0`, and `VIII` remain explicit controlled blockers.
  - campaign / theorem / no-claim vocabulary now says:
    - `representative_tilted_runtime_partial_only`
  - not the old all-blocked wording.

## What is genuinely fixed

- representative `Type V` tilted runtime no longer fails in the BF-02 seed projection path.
- the representative family sweep now matches code reality:
  - orthogonal `I/V/VII_0/VIII`: executable
  - tilted `V`: executable
  - tilted `I/VII_0/VIII`: explicit blockers

## What remains uncertain

- `VII_0` and `VIII` tilted runtime are still blocked.
- non-Type-I exact propagator remains unresolved.
- direction-resolved microphysics remains unresolved.

## Verification

- `venv/bin/python -m py_compile ...` on touched files: pass
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/hierarchy/test_ver2_seed_compatibility.py -q`
  - `7 passed`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime/test_ver2_tier_b_execution.py -q`
  - `15 passed`, known recombination early-`z` warning only
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/validation/test_ver2_campaign_evidence.py -q`
  - `8 passed`, known recombination early-`z` warning only
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/workspace/contracts/tests/test_ver2_validation_registry.py -q`
  - `14 passed`
- `PYTHONPATH=htt:htt/src venv/bin/python htt/scripts/ver2_bass_validation.py --family-sweep-check`
  - `PASS`

## Narrowed claim

- allowed:
  - representative preliminary family sweep includes bounded `Type V` tilted runtime
- still blocked:
  - representative tilted runtime as a full set
  - non-Type-I exact geometry claim
