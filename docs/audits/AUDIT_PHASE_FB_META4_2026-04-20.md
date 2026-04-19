# AUDIT_PHASE_FB_META4_2026-04-20

**Banner**: META pre-flight — no physics; 3-channel verification only

## Pre-flight scan

- Required reading completed for:
  `docs/lowell_bianchi/extended_coverage/PROJECT_MEMORY_EXPLICIT.md`,
  `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4`,
  `docs/lowell_bianchi/extended_coverage/SELF_AUDIT_AUTOMATION.md`,
  `docs/audits/AUDIT_PROMPT.md`,
  `htt/bass/collision/thomson_pstf.py` plus
  `htt/bass/collision/test_thomson_pstf.py`,
  `htt/bass/collision/tilted_visibility.py` plus
  `htt/bass/collision/test_tilted_visibility.py`.
- One-sentence summaries recorded in-session before any edits.
- Regression gate executed exactly as requested:
  `cd htt_base/htt && PYTHONPATH=. ../venv/bin/python -m pytest bass/ tsc/ -q`
  → `3403 passed, 1 skipped`.
- Source-of-work rule pinned for this phase: `htt/` may receive local
  skeleton plants but must never be staged; committed artifacts are the
  audit, development log, and `NEXT_SESSION_PROMPT.md` only.

## §FB-4.1

### §FB-4.1 — full-Lorentz PSTF collision skeleton
**Channel A**: 6 checked / 4 verified / 2 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4`, `docs/lowell_bianchi/04_thomson_collision_spec.md §8.2`, `htt/bass/collision/thomson_pstf.py` (LB-4 orthogonal scope), and `htt/bass/collision/tilted_visibility.py` (Layer A Lorentz-factor surface). Broken: the named on-disk path `docs/lowell_bianchi/lowell_bianchi_solver_reference.md §11.3` does not exist in this worktree; the historical text is only recoverable via `git show HEAD:lowell_bianchi_solver_reference.md`. Broken: no prior tracked `Dodelson §5.2` citation was found, so the skeleton docstring excludes Dodelson claims.
**Channel B**: 1 query / 1 verified / 0 unverified. Evidence: prompt-supplied `astro-ph/0006237` resolves on arXiv to an unrelated WFPC2 calibration paper, so the FB-4.1 anchor was corrected to `astro-ph/9911481` (`"Under changes of frame, multipoles with different l mix because of Doppler beaming effects."`).
**Channel C** (prose, 6-10 lines): The skeleton contract is a future collision-side analogue of `TiltedVisibility`: it takes the LB-4 orthogonal state and an optional tilted-electron overlay and returns one rank-`ell` PSTF tensor. Keeping `tilted_electron=None` as the default is the only safe pre-implementation choice because that is the natural `β = 0` short-circuit. At `β = 0` the future body must reduce byte-for-byte to `ThomsonPSTFCollisionOperator.evaluate`, so the null-tilt path cannot carry any new algebra. `Gamma_T` remains the only rate-like quantity, so the return tensor keeps the existing LB-4 `[Mpc^-1] × brightness-moment` dimensions. The sign contract remains dissipative because the orthogonal `ell >= 3` branch is `-Gamma_T * Π_ell`, and every boosted extension must collapse back to that sign as tilt vanishes. Known-limit recovery is therefore defined by the simultaneous checks `tilted_electron is None` and `tilted_electron.beta == 0.0`. Because the boost acts through frame mixing, a separate helper-function skeleton is less risky than mutating `ThomsonAux` before the literature surface is fully sealed.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `evaluate_tilted_thomson_pstf_collision(ell, temperature_state, polarization_state, eta, *, v_b_real_sph, Gamma_T, tilted_electron=None) -> PSTFTensor` | Reuses `TiltedSpeciesBackground` SSOT; keeps a `None` default for the β=0 short-circuit; avoids mutating LB-4 aux types before implementation. | Adds one new helper surface that the future operator must call explicitly. | ✅ |
| 2 | `evaluate_tilted_thomson_pstf_collision(ell, temperature_state, polarization_state, eta, *, v_b_real_sph, Gamma_T, beta=0.0, v_hat_e=V_HAT_E_DEFAULT) -> PSTFTensor` | Primitive inputs are explicit and avoid a wrapper dependency. | Re-literals tilt validation already centralized in `TiltedSpeciesBackground`; easier to drift from FB-3.5 rapidity / admissibility SSOT. | — |
**Core principles**: external-code policy; PSTF SSOT; β=0 byte-identity against the LB-4 orthogonal Thomson kernel and the FB-2.4 driver anchor `d7d25da`; no silent fallback; deterministic; inline citations per §6.
**Skeleton path**: `htt/bass/collision/tilted_thomson_layer_b.py::evaluate_tilted_thomson_pstf_collision`
**Test path**: `htt/bass/collision/test_fb41_tilted_thomson_skeleton.py::test_tilted_thomson_layer_b_skeleton_contract`
**Guard rails** (yes/no): citations verified? yes; imports exist? yes; ≥ 2 alternatives? yes; β=0 anchor documented? yes
**Regression after plant**: 3,403 passed + 2 skipped.

## §FB-4.2

### §FB-4.2 — E↔B mixing skeleton under tilted LOS
**Channel A**: 5 checked / 5 verified / 0 broken. Details: verified `htt/bass/collision/polarization.py` (current E-only storage), `htt/bass/collision/thomson_pstf.py` (B-mode tracked separately note), `docs/lowell_bianchi/04_thomson_collision_spec.md` (`B ≡ 0` scope pin and LB-4c defer), `htt/bass/los/bianchi_propagator.py` (Type I `ψ' = 0` B-mode floor), and `htt/docs/packets/WEEK9_02_PACKET.md` (orthogonal Type I block-diagonal propagator with no E↔B mixing).
**Channel B**: 1 query / 1 verified / 0 unverified. Evidence: `astro-ph/9611125` (`"for scalar metric perturbations one set is identically zero"`) confirms the clean-zero branch used as the β=0 / no-rotation anchor.
**Channel C** (prose, 6-10 lines): The skeleton contract has to expose both E and B outputs because once the polarization basis rotates, the coupling is intrinsically two-channel. Keeping `b_state=None` as the default is the safest META choice because the current production storage is explicitly E-only and the `β = 0` path must not disturb that surface. At `β = 0` or when no tilted-electron surface is supplied, the future body must collapse to the existing `E_mode_collision_source` contract and an identically zero B tensor. `Gamma_T` remains the only rate scale, so both returned tensors stay in the same collision-source units as LB-4. The sign check is asymmetric in the known limit: E keeps the existing damping and quadrupole-coupling signs, while B must vanish rather than damp from a nonexistent source. The Type I LOS floor in `bianchi_propagator.py` is the practical sanity pin that no rotation means no generated B power.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `evaluate_tilted_polarization_eb_collision(ell, e_state, eta, *, Pi_2_packed, Gamma_T, b_state=None, tilted_electron=None) -> tuple[PSTFTensor, PSTFTensor]` | Keeps the current E-only storage untouched; symmetric future E/B output; preserves a `None` default for the zero-B anchor. | Future callers must explicitly wire both returned tensors. | ✅ |
| 2 | `build_tilted_polarization_state_eb(E, B, *, tilted_electron=None) -> PolarizationHierarchyStateEB` | Makes the future two-field state explicit in one place. | Forces a new storage container before the literature and sign convention are sealed; larger blast radius across current LB-4 code. | — |
**Core principles**: external-code policy; PSTF SSOT; β=0 byte-identity against the existing E-mode collision source and the Type I `ψ' = 0` B-mode floor; no silent fallback; deterministic; inline citations per §6.
**Skeleton path**: `htt/bass/collision/tilted_eb_mixing.py::evaluate_tilted_polarization_eb_collision`
**Test path**: `htt/bass/collision/test_fb42_eb_mixing_skeleton.py::test_tilted_polarization_eb_collision_skeleton_contract`
**Guard rails** (yes/no): citations verified? yes; imports exist? yes; ≥ 2 alternatives? yes; β=0 anchor documented? yes
**Regression after plant**: 3,403 passed + 3 skipped.

## §FB-4.3

### §FB-4.3 — explicit `v_e²` Doppler skeleton
**Channel A**: 6 checked / 6 verified / 0 broken. Details: verified `docs/lowell_bianchi/FULL_BIANCHI_COVERAGE_PLAN.md §4 Phase FB-4` names FB-4.3 as the explicit `v_e²` sub-phase; `docs/lowell_bianchi/04_thomson_collision_spec.md §1` records `O(v_e²)` Thomson terms as deferred at LB-4 scope; `docs/lowell_bianchi/04_thomson_collision_spec.md §8.2` pins Layer B as additive PSTF-boost territory; `htt/bass/species/tilted.py` exposes exact `gamma_sq`, `v_vector`, and `β²` thermodynamic surfaces; `htt/bass/hierarchy/tilt_kinematics.py` already uses the additive-helper + `β = 0` short-circuit pattern; `docs/lowell_bianchi/extended_coverage/SCOPE_DECISIONS.md §4` discards production `v_e²` Thomson terms, so the planted surface is restricted to a contract-only additive placeholder and does not reopen shipped physics scope.
**Channel B**: 2 queries / 1 verified / 1 unverified. Evidence: `arXiv:0706.2075` is verifiable on arXiv and, despite the prompt's `2009` label, its arXiv record shows submission on June 14, 2007; quote: `"power in B-mode polarisation is predicted to be similar to the E-mode power"` (`arXiv:0706.2075`). `arXiv:1104.0420` could not be verified on arXiv in this session and is demoted to `# TODO: citation needed`.
**Channel C** (prose, 6-10 lines): The contract is deliberately additive: it represents only the `O(v_e²)` remainder and never the full FB-4.1 kernel itself.
If no tilted-electron wrapper is supplied, the only consistent value of the remainder is zero because the orthogonal LB-4 operator already exhausts the collision source.
At `β = 0`, `TiltedSpeciesBackground.gamma_sq = 1` and `v_vector(η) = 0`, so any quadratic Doppler factor built from `v_e` or `γ² - 1` vanishes identically.
That establishes the byte-identity invariant: `K^(0) + ΔK_(v²)` must reduce to the existing orthogonal `K^(0)` with no new floating-point work on the zero-tilt path.
The correction has the same dimensional form as the underlying collision source, namely `Γ_T` times a rank-`ℓ` brightness moment, so the helper returns one `PSTFTensor`.
The sign cannot be fixed from fully verified literature in this session, so the skeleton stays additive rather than hard-coding damping or sourcing semantics.
The known-limit sanity pin is therefore strict zero at `β = 0` and strict confinement to the future tilted path when `β > 0`.
**Alternatives**:
| # | signature | Pros | Cons | Picked |
|---|---|---|---|---|
| 1 | `evaluate_tilted_second_order_doppler_correction(ell, temperature_state, eta, *, v_b_real_sph, Gamma_T, tilted_electron=None) -> PSTFTensor` | Small additive blast radius; mirrors the FB-4.1 call surface; keeps the `None` / `β = 0` zero-correction anchor explicit. | Future callers must sum the returned tensor onto the linear FB-4.1 source explicitly. | ✅ |
| 2 | `evaluate_tilted_thomson_pstf_collision(..., include_second_order=False) -> PSTFTensor` | One public entry point for all Layer-B collision pieces. | Pushes a discarded production-scope question directly into the FB-4.1 operator surface; larger regression and semantics blast radius. | — |
**Core principles**: external-code policy; PSTF SSOT; β=0 byte-identity against the LB-4 orthogonal Thomson kernel and the FB-4.1 linear anchor; no silent fallback; deterministic; inline citations per §6.
**Skeleton path**: `htt/bass/collision/tilted_doppler_second_order.py::evaluate_tilted_second_order_doppler_correction`
**Test path**: `htt/bass/collision/test_fb43_second_order_doppler_skeleton.py::test_tilted_second_order_doppler_correction_skeleton_contract`
**Guard rails** (yes/no): citations verified? yes; imports exist? yes; ≥ 2 alternatives? yes; β=0 anchor documented? yes
**Regression after plant**: 3,403 passed + 4 skipped.

## Phase close

FB-META-4 closed on 2026-04-20 with three local-only skeleton plants
and no staged `htt/` changes. The audited regression anchor remains
`3403 passed, 4 skipped`, and `NEXT_SESSION_PROMPT.md §2` now points
to the generic `FB-META-5` placeholder rather than another FB-4 task.
