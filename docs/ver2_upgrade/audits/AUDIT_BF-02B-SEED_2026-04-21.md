# AUDIT_BF-02B-SEED_2026-04-21

## 1. Audit target reconstruction

- Target packet: `BF-02B-SEED`
- Lane: `B`
- Semantic SSOT: `docs/ver2_upgrade/*` only.
- Goal: close the explicit seed/startup gap left by `BF-01B-HCORE` by making the native Tier-B initial state consume a real packed regular seed, apply startup-manifold injection when `Gamma_T / H` selects it, and stop treating seed/startup as trace-only metadata.
- Required deliverables from SSOT:
  - quadrupole startup manifold is live on the native Tier-B route,
  - perturbative regular-seed projection is live on the native Tier-B route,
  - runtime IC injection is live rather than logged-only,
  - observer-neutral BASS outputs remain intact,
  - residual honesty is preserved where reduced helper paths still exist.

### Candidate layouts considered

1. Keep the seed/startup logic metadata-only and just tighten the tests.
2. Make the packed regular seed and startup manifold live inside the native Tier-B initial state, and explicitly realize the declared native runtime family onto a stable stiff solver for the seeded path.
3. Shrink or zero the injected seed amplitudes until the inherited legacy solver path stops producing non-finite values.

### Converged choice

- Choose layout 2.
- Reason:
  - layout 1 would not close the BF-02 packet objective at all;
  - layout 3 would mask the runtime defect by numerically weakening the physics path instead of making it live;
  - layout 2 closes the production-path seed/startup debt, preserves honest metadata about the current executor realization, and leaves angular reconstruction / validation promotion as later packets.

## 2. Contract/interface table

| Surface | Path | Role | Verdict |
|---|---|---|---|
| `project_packed_regular_seed` | `htt/bass/hierarchy/seed_compatibility.py` | packed regular-seed projection for runtime IC injection | passed |
| `Ver2TierBIntegrator.initial_state` | `htt/bass/hierarchy/ver2_native_integrator.py` | native Tier-B initial-state builder | passed |
| startup manifold injection | `htt/bass/hierarchy/ver2_native_integrator.py` | quadrupole startup override when `Gamma_T/H` selects it | passed |
| runtime solver-family realization | `htt/bass/runtime/ver2_execution.py` | maps declared native runtime family onto the executed stiff solver | passed |
| native output metadata | `htt/bass/forward/ver2_solver_output.py` | propagates seed/startup/solver realization honestly into observer-neutral output | passed |

## 3. Phys-math audit ledger

| Item | Status | Why | Code impact |
|---|---|---|---|
| packed regular seed on native route | passed | the native Tier-B initial state now starts from a packed FB-5.3 regular seed rather than an all-zero radiation block | runtime ICs now contain live monopole/dipole/quadrupole structure |
| tilted/electron-frame seed projection | passed | the runtime path uses a geometry-backed constraint projection with explicit velocity-block rescaling | tilted seed insertion remains finite and reduces to the orthogonal limit as `v_e -> 0` |
| startup-manifold gating | passed | startup selection is now tied to `Gamma_T/H` and injects `theta_2`, `E_2` directly into the initial hierarchy state | startup is no longer metadata-only |
| native solver stability on seeded path | passed with caveat | inherited `LSODA` produced non-finite values on the seeded native path, while `BDF` and `Radau` remained finite | runtime now explicitly realizes the declared `IMEX_SPLIT` family onto a `BDF` executor and records that fact |
| observer neutrality | passed | no likelihood/posterior semantics were added while making seeds live | BASS output stays solver-side only |
| angular reconstruction | partial | seed/startup are now live, but observer-neutral angular-grid reconstruction is still unresolved | `BF-03B-ANG` remains required |
| standalone reduced seed helper | partial | the no-geometry helper branch still exists as a first-pass reduced contract for off-runtime callers | production runtime no longer depends on it, but the helper remains explicit carry-forward |

## 4. Equation-to-code mapping audit

- Packed regular seed construction:
  - `bass.perturbation.regular_adiabatic_ic.make_camb_regular_adiabatic_seed`
- Packed-seed observables / unpacking:
  - `bass.perturbation.regular_adiabatic_ic.unpack_camb_regular_adiabatic_seed`
  - `bass.perturbation.regular_adiabatic_ic.seed_observables`
- Constraint-aware packed seed projection:
  - `bass.hierarchy.seed_compatibility.project_packed_regular_seed`
- Native initial-state assembly and startup injection:
  - `bass.hierarchy.ver2_native_integrator.Ver2TierBIntegrator._build_seeded_initial_state`
  - `bass.hierarchy.ver2_native_integrator.Ver2TierBIntegrator._resolve_startup_state`
- Runtime solver-family realization for the seeded path:
  - `bass.runtime.ver2_execution._resolve_native_solver_method`
  - `bass.runtime.ver2_execution._native_runtime_config`
- Observer-neutral provenance propagation:
  - `bass.forward.ver2_solver_output.build_solver_core_output_from_native_result`

## 5. Numerical/pipeline audit

- Internal-doc/local-code lane:
  - used prompt list 03, the execution/carry-forward ledgers, the BF-01 audit note, and the live BASS runtime/hierarchy code as authority.
- Web CRAG lane:
  - not needed for this packet.
  - reason: this packet resolves local runtime/seed wiring and solver-realization drift inside already-owned BASS code; no new unstable external library or new primary-source formula was introduced.
- Integrated phys-math-code lane:
  - focused on five failure classes:
    1. metadata-only startup/seed promotion with no actual runtime IC change,
    2. packed seed insertion that breaks the orthogonal/zero-tilt limit,
    3. startup tests that assume selection without verifying `Gamma_T/H`,
    4. inherited legacy `LSODA` producing non-finite seeded native trajectories,
    5. output metadata hiding the actual executed native solver path.
  - result:
    - 1, 2, 4, and 5 are closed for the production runtime path;
    - 3 is closed by splitting startup-selected vs seed-only tests explicitly.

## 6. Ranked failure modes

1. `P0` native Tier-B still starts from an all-zero radiation block even though seed metadata exists.
   - Mitigation: `Ver2TierBIntegrator.initial_state` now injects a packed regular seed directly.
2. `P0` seeded native path inherits legacy `LSODA` and produces non-finite values.
   - Mitigation: native runtime now resolves the declared family onto a stable `BDF` executor and records the realization explicitly.
3. `P1` startup manifold remains trace-only and never modifies the initial hierarchy state.
   - Mitigation: startup-selected runs now overwrite the `ell=2, m=0` temperature/E-mode slots directly.
4. `P1` tests conflate seed injection with startup selection.
   - Mitigation: one test now forces startup selection; a separate one verifies seed-only injection with startup disabled.
5. `P2` packed seed projection breaks the zero-tilt limit.
   - Mitigation: explicit tests assert identity in the `v_e = 0` limit and controlled velocity-block rescaling for tilted insertion.
6. `P2` standalone no-geometry helper is mistaken for the production runtime seed path.
   - Mitigation: carry-forward remains explicit; the production runtime uses the geometry-backed branch.
7. `P2` `IMEX_SPLIT` is mistaken for a shipped split-step executor.
   - Mitigation: runtime/output metadata now records the realized executor as `imex_split_declared_bdf_executor`.

## 7. Verifier results

- Physics verifier: passed for packet scope
  - runtime ICs now carry live regular-seed content,
  - startup injection is tied to an explicit `Gamma_T/H` gate,
  - zero-tilt and seed-only limits are tested directly.
- Code verifier: passed
  - write scope stayed inside `htt/bass/*` plus related docs/tests,
  - the live runtime route now consumes seed/startup logic instead of logging-only traces,
  - observer-neutral output metadata stays honest about the executed path.
- Numerical verifier: passed for packet scope
  - `py_compile` passes,
  - packet-local and touched-surface runtime/forward tests are green,
  - explicit method-sensitivity probing showed `BDF` and `Radau` remain finite on the seeded path while inherited `LSODA` did not.

## 8. Minimal repair plan

1. `BF-03B-ANG`
   - close `project_from_angular_samples` / `reconstruct_on_sphere` against the now-seeded native Tier-B outputs.
2. `BF-04B-COV`
   - replace proxy morphology/covariance logic once the angular bridge is live.
3. `BF-05B-VAL`
   - validate the current `BDF`-realized seeded native path against null/injection/cutoff evidence before any later promotion.

## 9. Minimal test set

- baseline reproduction:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_is_deterministic_for_same_inputs`
- edge/adversarial:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_injects_seed_even_without_startup_manifold`
- physics sanity:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_consumes_live_s1_s2_s3_hooks`
- numerical / stability:
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime htt/bass/forward htt/bass/test_ver2_public_surface.py -q`
- regression:
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/hierarchy/test_ver2_seed_compatibility.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/forward/test_ver2_solver_output.py -q`

## 10. Final verdict

- Verdict: pass for packet scope.
- Implemented now:
  - geometry-backed packed regular-seed projection on the production Tier-B route,
  - live startup-manifold injection into the native Tier-B initial state,
  - explicit native runtime solver-family realization for the seeded path,
  - observer-neutral solver output metadata for seed/startup/executor provenance.
- Still deferred:
  - observer-neutral angular-grid reconstruction bridge,
  - validated low-`ell` morphology/covariance promotion,
  - campaign-grade validation of the now-seeded native core,
  - standalone no-geometry seed helper remains a reduced off-runtime path.

## Standard Packet Footer

- Exact files changed:
  - `htt/bass/hierarchy/seed_compatibility.py`
  - `htt/bass/hierarchy/__init__.py`
  - `htt/bass/hierarchy/test_ver2_seed_compatibility.py`
  - `htt/bass/hierarchy/ver2_native_integrator.py`
  - `htt/bass/runtime/ver2_execution.py`
  - `htt/bass/runtime/test_ver2_tier_b_execution.py`
  - `htt/bass/forward/ver2_solver_output.py`
  - `htt/bass/forward/test_ver2_solver_output.py`
  - `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
  - `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
  - `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
  - `docs/ver2_upgrade/VER2_PHASE_PROMPTS_03_BASS_COMPLETION.md`
  - `docs/ver2_upgrade/audits/AUDIT_BF-02B-SEED_2026-04-21.md`
- Exact tests run:
  - `venv/bin/python -m py_compile htt/bass/hierarchy/seed_compatibility.py htt/bass/hierarchy/ver2_native_integrator.py htt/bass/runtime/ver2_execution.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/forward/ver2_solver_output.py htt/bass/forward/test_ver2_solver_output.py`
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/hierarchy/test_ver2_seed_compatibility.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/forward/test_ver2_solver_output.py -q`
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime htt/bass/forward htt/bass/test_ver2_public_surface.py -q`
- Audit verdict: green for packet scope
- Remaining caveats:
  - `IMEX_SPLIT` is currently realized by a `BDF` executor on the seeded native route
  - angular-grid/PSTF reconstruction remains deferred
  - standalone no-geometry seed helper remains reduced
- Commit subject:
  - `V2-B2: implement live startup manifold and seed injection`
- Next blocked dependency:
  - `BF-03B-ANG`
