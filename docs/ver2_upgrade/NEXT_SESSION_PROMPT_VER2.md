# NEXT_SESSION_PROMPT_VER2

## 1. Read First

1. `docs/ver2_upgrade/VER2_SSoT_PARALLEL_EXECUTION_PLAN.md`
2. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_01_SKELETON_PREIMPLANT.md`
3. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_02_IMPLEMENTATION_FIGURES_MANUSCRIPT.md`
4. `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
5. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
6. `docs/ver2_upgrade/VER2_PHASE_PLACEHOLDER_INDEX.md`
7. `docs/ver2_upgrade/audits/AUDIT_SK-00_2026-04-20.md`
8. `docs/ver2_upgrade/audits/AUDIT_SK-01C_2026-04-21.md`
9. `docs/ver2_upgrade/audits/AUDIT_SK-05T_2026-04-21.md`
10. `docs/ver2_upgrade/audits/AUDIT_SK-09D_2026-04-21.md`
11. `docs/ver2_upgrade/audits/AUDIT_SK-07M_2026-04-21.md`
12. `docs/ver2_upgrade/audits/AUDIT_SK-06H_2026-04-21.md`
13. `docs/ver2_upgrade/audits/AUDIT_SK-01S1_2026-04-21.md`
14. `docs/ver2_upgrade/audits/AUDIT_SK-02S2_2026-04-21.md`
15. `docs/ver2_upgrade/audits/AUDIT_SK-03S3_2026-04-21.md`
16. `docs/ver2_upgrade/audits/AUDIT_SK-04O_2026-04-21.md`
17. `docs/ver2_upgrade/audits/AUDIT_SK-08V_2026-04-21.md`
18. `docs/ver2_upgrade/audits/AUDIT_IM-06H_2026-04-21.md`
19. `docs/ver2_upgrade/audits/AUDIT_IM-07M_2026-04-21.md`
20. `docs/ver2_upgrade/audits/AUDIT_IM-01S1_2026-04-21.md`

## 2. Current State

- `SK-00` barrier docs, ledgers, audit note, and schema/owner drift tests are in place.
- Canonical shared schema now lives in `htt/src/common/contracts.py` and `htt/src/common/departure_contracts.py`.
- `workspace/contracts` wrappers accept a canonical `ArtifactManifest` hook and enforce owner consistency when manifest is present.
- Canonical VER2 contract coverage now includes `AtlasEntryLite`, `DepartureReport`, `FullCovMESReport`, `TscAdequacyOverlay`, `ClaimLedgerEntry`, and thin workspace aliases/hooks.
- `SK-05T` is now closed: `htt/tsc/*` contains domain-guard, no-overclaim, overlay-builder, advisory-adapter, and theorem-map skeletons backed by common manifests and TSC-owned reports.
- `SK-09D` is now closed: `scripts/ver2_artifact_export.py` generates placeholder D-lane outputs under `docs/ver2_upgrade/generated/*` and `docs/manuscript/generated/*`, and `figures/paper/VER2_MANIFEST_INDEX.md` now blocks legacy paper figures without manifests.
- The exporter currently reports `83` paper-figure bases and `83` missing manifests. That is the expected blocked skeleton state before `IM-09D-FIG`.
- `SK-07M` is now closed: touched MIO certificate producers attach VER2 manifest-backed production status, explicit covariance/atlas/null-mock caveats, and JSON-ready manifest payloads; `htt/mio/diagnostics/predictive_residuals.py` exists as a blocked residual-atlas shell.
- Targeted MIO verification is green: `venv/bin/python -m pytest htt/mio/tests -q` -> `155 passed`.
- `SK-06H` is now closed: HTT owns a solver-free directional shell under `htt/htt/htt/infer/*`, with explicit production-axis gating, matched-complexity/null-competition hooks, local-boost/global-tilt discrimination scaffolds, and a closed-fail bridge promotion gate.
- HTT verification is green for the packet scope: targeted `SK-06H` tests passed (`39 passed`) and `py_compile` passed.
- `SK-01S1` is now closed: BASS owns a canonical `BianchiAlgebra`, tetrad connection / curvature operators, machine-readable Gauss/Codazzi/Jacobi residuals, orthogonal/tilted IC-builder shells, a 1+3 background RHS shell, and Weyl diagnostic hooks under `htt/bass/background/*`.
- BASS S1 verification is green for the packet scope: targeted pytest `174 passed`, touched-surface pytest `696 passed`, and `py_compile` passed.
- `SK-02S2` is now closed: BASS owns canonical S2 shells for frame split, photon geodesics, low-`ell` `{I,E,B}` PSTF radiation state/truncation metadata, electron-frame Thomson projection ownership, scalar-history-first-pass visibility/reionization wiring, quadrupole-aware startup metadata, and FLRW-limit seed compatibility under `htt/bass/{hierarchy,transport,collision,recombination,closure}/*`.
- BASS S2 verification is green for the packet scope: targeted pytest `22 passed`, touched-surface pytest `1742 passed`, and `py_compile` passed.
- A minimal numerical repair also landed inside the existing collision path: `ThomsonAux` and `EModeThomsonAux` clip tiny negative interpolation noise in `Gamma_T` (`|Gamma_T| < 1e-7`) to zero so the legacy integrator remains stable at the recombination-table edge without redefining Thomson-rate semantics.
- `SK-03S3` is now closed: BASS owns canonical S3 shells for Tier A / Tier B execution planning, runtime/checkpoint/constraint-projection metadata, anisotropic propagator metadata, cutoff/convergence campaign hooks, and manifest-backed observer-neutral `SolverCoreOutput` construction under `htt/bass/{runtime,los,spectrum,forward}/*`.
- BASS S3 verification is green for the packet scope: targeted pytest `13 passed`, selected touched-surface pytest `437 passed`, and `py_compile` passed.
- `SK-04O` is now closed: BASS owns canonical O-lane producer shells for manifest-backed `ObservableVector`, sparse covariance/BiPoSH proxy export, `AtlasEntryLite`, rank-gated `FullCovMESReport`, and descriptive xQPiFG `DepartureReport` plumbing under `htt/bass/observational/*`, plus thin workspace aliases for `ObservableVector` and `FullCovMESReport`.
- BASS O-lane verification is green for the packet scope: targeted pytest `103 passed`, touched-surface pytest `65 passed`, and `py_compile` passed.
- The O-lane explicitly records proxy-vs-production boundaries: diagonal-only compression is never treated as sufficient, rank-deficient covariance upgrades return no-claim, uncertified filling remains descriptive/proxy-only, and FB-7 `m`-block sparse exports are labeled `sparse_mode_block_proxy` rather than full BiPoSH.
- `SK-08V` is now closed: `workspace/contracts` carries a package-neutral theorem-to-test map, validation campaign registry, null/injection manifests, and hostile-audit runbook contracts; `htt/scripts` now exposes machine-readable registry/runbook checks.
- Validation V-lane verification is green for the packet scope: targeted pytest `9 passed`, touched-surface pytest `40 passed`, `py_compile` passed, and both `htt/scripts/ver2_validation_registry.py --check` and `htt/scripts/ver2_hostile_audit.py --check` pass.
- `IM-06H` is now green in the local workspace: HTT directional shells accept live matched-complexity/null-competition/PPC/LOOCV hooks, directional output surfaces auto-materialize HTT-owned manifests/readiness metadata, and `htt.integration.to_mio.build_posterior_bundle` can synthesize a cross-check-only HTT manifest when one is not supplied explicitly.
- `IM-06H` verification is green for the touched H-lane scope: targeted pytest `20 passed`, full `htt/htt/tests` `271 passed`, and `py_compile` passed.
- `IM-06H` has not been committed yet; the local packet is ready for a `V2-H1:` commit if the user wants history updated.
- `IM-07M` is now green in the local workspace: `htt/mio/diagnostics/predictive_residuals.py` can build live model×channel residual slices from `ObservableVector` + `HttForwardOutput`, and IM-07M MIO certificate producer surfaces now accept live `TscAdequacyOverlay` attachment without reopening ownership or evidence semantics.
- `IM-07M` verification is green for the touched M-lane scope: targeted pytest `11 passed`, full `htt/mio/tests` `155 passed`, and `py_compile` passed.
- `IM-07M` has not been committed yet; the local packet is ready for a `V2-M1:` commit if the user wants history updated.
- `IM-01S1` is now closed: BASS S1 owns live all-type Codazzi projection, Hamiltonian closure policies (`solve_H`, `hold_H`, `solve_curvature_scale`, `project_shear_amplitude`), explicit orthogonal/tilted admissibility metadata, barotropic matter closures, and a canonical executable background evolution path under `htt/bass/background/evolution.py`.
- `IM-01S1` verification is green for the touched S1 scope: targeted pytest `63 passed`, full `htt/bass/background` `329 passed`, runtime wiring `6 passed`, `htt/bass/species/test_tilted.py` `24 passed`, and `py_compile` passed.
- The pre-existing `bass.background` ↔ `bass.tilt` package-import cycle surfaced by `SK-03S3` is now closed for the runtime wiring path; `htt/bass/runtime/test_end_to_end_wiring.py` collects and passes again.
- The reduced `einstein_bianchi` route still exists for compatibility, but the VER2 background implementation anchor is now `htt/bass/background/evolution.py` plus the S1 IC/geometry/RHS modules.
- Prompt list 01 is now complete: every skeleton lane has an audit note, machine-readable carry-forward, and a frozen write-scope boundary.
- Full manifest propagation is still not wired through every producer outside the M lane. That is expected at this stage.

## 3. Next Recommended Packet

`SK-00`, `SK-01C`, `SK-01S1`, `SK-02S2`, `SK-03S3`, `SK-04O`, `SK-05T`, `SK-06H`, `SK-07M`, `SK-08V`, and `SK-09D` are closed. Move to prompt list 02.

If working in one thread, start the solver critical path:

1. `IM-02S2`
2. `IM-03S3A`
3. `IM-04O`
4. `IM-08V`

If parallel threads are available, start these side lanes immediately while the solver path begins:

- `IM-05T`

## 4. Hard Reminders

- `docs/ver2_upgrade/*` is the only semantic SSOT.
- Do not widen write scopes.
- Do not redefine base enums or manifests outside `htt/src/common/*`.
- Do not let TSC own runtime allow/block.
- Do not merge MIO certificate semantics into HTT or BASS.
- Do not generate figures or manuscript claims from non-manifest artifacts.
- Do not route new VER2 work back onto the reduced `einstein_bianchi` background engine; `htt/bass/background/evolution.py` and the S1 IC/geometry/RHS modules are now the implementation anchor.
- Do not silently treat the new S2 shells as executable solver completions; the real runtime binding still belongs to `SK-03S3` and later implementation packets.
- Do not silently treat the new S3 shells as executable solver completion either; they freeze runtime/output ownership, but Tier A/Tier B numerics and observable extraction still require later implementation packets.
- Do not silently promote `sparse_mode_block_proxy` into a full BiPoSH claim surface; executable O-lane work must replace or discharge that caveat explicitly.
- Do not treat rank-blocked `FullCovMESReport` artifacts as weak covariance evidence; they are explicit no-claim outputs.
- Do not treat `warn` campaigns in the V-lane registry as validated science gates; they are explicit placeholders until executable implementation packets discharge them.
- Do not silently treat `diagnostic_only` H-lane manifests as production-ready; `IM-06H` now requires live solver/null/PPC/LOOCV hooks before candidate promotion.
- Do not treat IM-07M predictive residual outputs as final heatmap/validation artifacts yet; the live shared-schema slice path exists, but campaign/export promotion still belongs to later V/D packets.
- Rerun `venv/bin/python scripts/ver2_artifact_export.py` after any D-lane change touching generated manuscript/export surfaces.
