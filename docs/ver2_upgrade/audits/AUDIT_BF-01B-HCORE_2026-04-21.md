# AUDIT_BF-01B-HCORE_2026-04-21

## 1. Audit target reconstruction

- Target packet: `BF-01B-HCORE`
- Lane: `B`
- Semantic SSOT: `docs/ver2_upgrade/*` only.
- Goal: close the highest-priority post-VER2 BASS debt by removing the shipped Lowell Tier-B hierarchy/integrator from the production Tier-B route and replacing it with an S1/S2-native executable hierarchy/RHS path.
- Required deliverables from SSOT:
  - Tier-B production runtime is physically owned by the VER2 S1/S2 stack,
  - S1 background evolution remains the runtime owner,
  - S2 transport/collision/visibility surfaces remain the hierarchy owner,
  - retained compatibility routes do not sit on the production path,
  - observer-neutral BASS outputs remain intact.

### Candidate layouts considered

1. Keep the existing `IM-03S3A` runtime and only relabel provenance/metadata away from Lowell.
2. Retarget the production Tier-B route onto a native radiation-sector integrator fed by S1 background evolution plus S2 transport/collision/history surfaces, while retaining Lowell only for validation/compatibility routes.
3. Rewrite the full coupled background+radiation solver inside one packet and retire every Lowell-facing surface immediately.

### Converged choice

- Choose layout 2.
- Reason:
  - layout 1 would leave the main load-bearing debt unresolved behind renamed metadata;
  - layout 3 is too wide for a single bounded BASS-follow-up packet and would blur seed/angular/validation ownership that prompt list 03 keeps serial;
  - layout 2 closes the production-route debt now, preserves an honest validation/compatibility boundary, and hands clean residual work to `BF-02B-SEED` and `BF-03B-ANG`.

## 2. Contract/interface table

| Surface | Path | Role | Verdict |
|---|---|---|---|
| `Ver2TierBIntegrator` | `htt/bass/hierarchy/ver2_native_integrator.py` | native Tier-B radiation-sector executable core | passed |
| `execute_tier_b_solver` | `htt/bass/runtime/ver2_execution.py` | canonical production Tier-B runtime/orchestrator | passed |
| `execute_tier_b_lowell_solver` | `htt/bass/runtime/ver2_execution.py` | compatibility alias only, not production owner | passed |
| `build_solver_core_output_from_native_result` | `htt/bass/forward/ver2_solver_output.py` | observer-neutral native Tier-B output builder | passed |
| runtime/forward public exports | `htt/bass/runtime/__init__.py`, `htt/bass/forward/__init__.py` | package-facing production access points | passed |

## 3. Phys-math audit ledger

| Item | Status | Why | Code impact |
|---|---|---|---|
| production Tier-B ownership | passed | the production route no longer instantiates `LowellBianchiIntegrator` | the main Tier-B path is now genuinely S1/S2-owned rather than Lowell-owned |
| S1 background ownership | passed | the native integrator consumes `BackgroundEvolutionResult` and a background-table adapter derived from the S1 path | the runtime background owner stays `background.evolution` |
| S2 hierarchy ownership | passed | photon/geodesic/collision/history closures feed the native radiation RHS directly | collision/history hooks are no longer trace-only on the production Tier-B path |
| observer neutrality | passed | the native builder still emits neutral `SolverCoreOutput` without likelihood/posterior semantics | BASS scope remains solver-side only |
| startup/seed closure | partial | startup gates and first-pass seed projections are consumed, but no full perturbative manifold injection has landed yet | `BF-02B-SEED` remains required |
| angular reconstruction | partial | native Tier-B now produces final-slice PSTF outputs with honest provenance, but angular-grid/PSTF reconstruction remains open | `BF-03B-ANG` remains required |
| Tier-A independence | failed by design | the validation route still reuses the Lowell core | this remains an explicit carry-forward item, not a hidden regression |

## 4. Equation-to-code mapping audit

- S1 background executable owner:
  - `htt/bass/background/evolution.py`
  - consumed by `Ver2TierBIntegrator` via `BackgroundEvolutionResult`.
- S2 transport/collision/history executable owners:
  - `htt/bass/transport/geodesics.py`
  - `htt/bass/collision/electron_frame.py`
  - `htt/bass/recombination/history_visibility.py`
  - `htt/bass/closure/stiff_closure.py`
  - adapted inside `htt/bass/hierarchy/ver2_native_integrator.py`.
- Tier-B runtime/orchestrator:
  - `htt/bass/runtime/ver2_execution.py`
  - production entrypoint is now `execute_tier_b_solver`.
- Observer-neutral output route:
  - `htt/bass/forward/ver2_solver_output.py`
  - production entrypoint is now `build_solver_core_output_from_native_result`.

## 5. Numerical/pipeline audit

- Internal-doc/local-code lane:
  - used `VER2` prompt list 03 plus the execution/carry-forward ledgers and prior BASS audit notes as authority.
- Web CRAG lane:
  - not needed for this packet.
  - reason: the packet rewires already-owned local BASS physics/code surfaces and does not introduce a new unstable external formula/library dependency.
- Integrated phys-math-code lane:
  - focused on four failure classes:
    1. relabelled Lowell ownership with no real production-path change,
    2. import-cycle regressions while introducing the native integrator,
    3. native output builder drift that still stamps Lowell provenance,
    4. Tier-A/B comparison tests that falsely assume exact equality after removing the shared Tier-B core.
  - result:
    - 1, 2, and 3 are closed for packet scope;
    - 4 is made explicit via relaxed bounded-comparison tests and a still-open Tier-A carry-forward item.

## 6. Ranked failure modes

1. `P0` production Tier-B path still instantiates the Lowell core under a renamed wrapper.
   - Mitigation: native `Ver2TierBIntegrator` now owns the production Tier-B path; compatibility alias tests guard against regression.
2. `P0` native output builder still stamps Lowell provenance.
   - Mitigation: `build_solver_core_output_from_native_result` writes explicit native provenance and metadata.
3. `P1` new hierarchy import path reopens package cycles.
   - Mitigation: native integrator stays out of eager `hierarchy.__init__` exports; runtime imports remain local.
4. `P1` Tier-A/B validation overfits exact equality and fails once Tier-B stops sharing the same core.
   - Mitigation: comparison tests now enforce bounded agreement rather than identity.
5. `P1` production Tier-B route becomes native but startup manifold injection remains absent.
   - Risk stays explicit for `BF-02B-SEED`.
6. `P1` observer-side angular reconstruction is mistaken as solved because final-slice native provenance now exists.
   - Risk stays explicit for `BF-03B-ANG`.
7. `P2` table-edge `Gamma_T` floor is mistaken for a full numerical repair.
   - Risk remains explicit as a later numerical-quality follow-up, not a BF-01 deliverable.

## 7. Verifier results

- Physics verifier: passed for packet scope
  - production Tier-B ownership is genuinely transferred away from Lowell,
  - S1/S2 runtime ownership remains explicit,
  - no observer/likelihood semantics leaked into BASS.
- Code verifier: passed
  - write scope stayed inside `htt/bass/*` plus related tests/docs,
  - public surfaces expose the native Tier-B route,
  - compatibility alias remains non-owning and tested.
- Numerical verifier: passed for packet scope
  - `py_compile` passes,
  - packet-local and touched-surface tests are green,
  - deterministic Tier-B rerun checks still pass.

## 8. Minimal repair plan

1. `BF-02B-SEED`
   - inject a real startup manifold / perturbative seed path into the native Tier-B initial state.
2. `BF-03B-ANG`
   - close `project_from_angular_samples` / `reconstruct_on_sphere` against the native Tier-B outputs.
3. `BF-05B-VAL`
   - revisit the Tier-A validation bridge so cross-checks do not depend on the Lowell core indefinitely.

## 9. Minimal test set

- baseline reproduction:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_solver_is_deterministic_for_same_inputs`
- edge/adversarial:
  - `htt/bass/runtime/test_ver2_tier_b_execution.py::test_execute_tier_b_lowell_solver_is_a_compatibility_alias`
- physics sanity:
  - `htt/bass/forward/test_ver2_solver_output.py::test_build_solver_core_output_from_native_result_attaches_native_provenance`
- numerical / stability:
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime htt/bass/forward htt/bass/test_ver2_public_surface.py -q`
- regression:
  - packet-local runtime/forward pytest (`11 passed`)
  - touched-surface runtime/forward/public-surface pytest (`168 passed`)

## 10. Final verdict

- Verdict: pass for packet scope.
- Implemented now:
  - native Tier-B production integrator bound to S1 background + S2 transport/collision/history ownership,
  - native observer-neutral Tier-B output provenance,
  - compatibility alias retained without production ownership,
  - deterministic and bounded Tier-A/B comparison expectations updated to the new split.
- Still deferred:
  - perturbative seed/startup manifold injection,
  - observer-neutral angular reconstruction bridge,
  - independent non-Lowell Tier-A validation core.

## Standard Packet Footer

- Exact files changed:
  - `htt/bass/hierarchy/ver2_native_integrator.py`
  - `htt/bass/runtime/ver2_execution.py`
  - `htt/bass/runtime/__init__.py`
  - `htt/bass/forward/ver2_solver_output.py`
  - `htt/bass/forward/__init__.py`
  - `htt/bass/runtime/test_ver2_tier_b_execution.py`
  - `htt/bass/runtime/test_ver2_tier_a_validation.py`
  - `htt/bass/forward/test_ver2_solver_output.py`
  - `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
  - `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
  - `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`
  - `docs/ver2_upgrade/VER2_PHASE_PROMPTS_03_BASS_COMPLETION.md`
  - `docs/ver2_upgrade/audits/AUDIT_BF-01B-HCORE_2026-04-21.md`
- Exact tests run:
  - `venv/bin/python -m py_compile htt/bass/hierarchy/ver2_native_integrator.py htt/bass/runtime/ver2_execution.py htt/bass/runtime/__init__.py htt/bass/forward/ver2_solver_output.py htt/bass/forward/__init__.py htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/runtime/test_ver2_tier_a_validation.py htt/bass/forward/test_ver2_solver_output.py`
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime/test_ver2_tier_b_execution.py htt/bass/runtime/test_ver2_tier_a_validation.py htt/bass/forward/test_ver2_solver_output.py -q`
  - `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/bass/runtime htt/bass/forward htt/bass/test_ver2_public_surface.py -q`
- Audit verdict: green for packet scope
- Remaining caveats:
  - Tier-A validation still reuses Lowell
  - startup/seed injection is still partial
  - angular-grid/PSTF reconstruction remains deferred
- Commit subject:
  - `V2-B1: retarget Tier-B runtime to native S1/S2 core`
- Next blocked dependency:
  - `BF-02B-SEED`
