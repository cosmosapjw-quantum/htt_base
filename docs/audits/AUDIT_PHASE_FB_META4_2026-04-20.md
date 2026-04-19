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

## §FB-4.3
