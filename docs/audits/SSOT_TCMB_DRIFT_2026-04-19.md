# SSOT drift audit — T_CMB dual-definition

**Date**: 2026-04-19
**Track**: SSOT-01 (INDEPENDENT_TRACKS_PLAN.md §2.1)
**Scope**: audit + `htt`-side anti-regression guard only; `bass`-side **untouched** (deferred to bass_py session)

---

## 1. Finding

Two numerically distinct `T_CMB` constants coexist in the repository, both citing Fixsen (2009, ApJ 707, 916):

| Location | Symbol | Value | Citation string |
|---|---|---|---|
| `bass_py/bass/observational/planck_mes_bounds.py:58` | `T_CMB_K` | `2.7255` | "Fixsen, ApJ 707, 916 (2009)" |
| `bass_py/bass/observational/planck_mes_bounds.py:61` | `T_CMB_MICROK` | `2.7255e6` | same |
| `bass_py/htt/htt/core/ssot.py:53` | `C.T0_K` | `2.72548` | (implicit — see `docs/` or `obs_defaults.json`) |
| `bass_py/htt/htt/core/ssot.py:54` | `C.T0_uK` | `2.7255e6` | **inconsistent with `T0_K` within the same class** |

Fixsen (2009) reports **T_CMB = 2.72548 ± 0.00057 K**. Therefore:
- `htt.core.ssot.C.T0_K = 2.72548` ← matches the published Fixsen central value exactly.
- `bass.observational.planck_mes_bounds.T_CMB_K = 2.7255` ← uses the conventional three-significant-figure rounding (common in CMB literature, but *not* the Fixsen central value).
- `htt.core.ssot.C.T0_uK = 2.7255e6` ← intra-class inconsistency; should be `2.72548e6`.

Relative drift: `Δ = (2.72548 − 2.7255)/2.72548 = −1.83 × 10⁻⁵`.

## 2. Numerical impact

`D_ℓ ∝ T_CMB²`, so the propagated drift is `≈ 3.67 × 10⁻⁵` (relative) across observables using `D_ℓ`.

At the BASS primary anchor `D_2(Σ²=1e-8) = 0.174112 μK²` this is `≈ 6.4 × 10⁻⁶ μK²` — far below the Planck error bar (`σ(D_2) = 96.6 μK²`) and below the 1 μK² display resolution of the gallery plots. **No existing test fails.**

However: SSOT principle demands one canonical numerical value. Two values with the same citation is a latent bug waiting to surface when later tests tighten tolerances.

## 3. Where each value is consumed

`T_CMB_K = 2.7255` (bass path):
- `bass/spectrum/cl_assembly.py` — `compute_dl`, `ClAssemblyConfig.T_CMB_K`
- `bass/spectrum/test_cl_assembly.py` — anchor tests
- `bass/recombination/test_reionization.py` — fixture
- `bass/species/test_constants.py:19` — re-exports through `C.T0_K`
- `bass/recombination/fixtures/recombination_ref_planck2018.csv` (comment)

`C.T0_K = 2.72548` (htt path):
- `htt/tests/test_legacy_core.py:185` — asserts `C.T0_K == pytest.approx(2.72548, rel=1e-4)` (existing anchor; rel=1e-4 is loose enough to pass either value).

`C.T0_uK = 2.7255e6` (htt path):
- `htt/core/ssot.py::eps_ell` — divides by `C.T0_uK` in dimensionless ΔT/T conversion.
- `htt/core/ssot.py::D_ell_from_eps` — multiplies by `C.T0_uK²`.

Note that `bass/species/constants.py:44` imports `T_GAMMA_0_K = _ssot.C.T0_K` — i.e. species uses the **htt** value (2.72548). So downstream of species, there is *another* quiet drift: species thinks T_γ,0 = 2.72548 but the cl_assembly pipeline uses 2.7255. Both values have the "Fixsen 2009" citation.

## 4. Recommendation (unilateral from SSOT-01)

**Canonical**: `T_CMB = 2.72548 K` (Fixsen 2009 central value).

**Action plan** (deferred — see §5 for what SSOT-01 does *now*):

1. **bass side**: change `bass/observational/planck_mes_bounds.py` to
   ```python
   T_CMB_K: float = 2.72548
   T_CMB_MICROK: float = 2.72548e6
   ```
   and update all cross-reference tests (`test_cl_assembly.py:450`, `test_cl_assembly.py:465-466`, `test_reionization.py:59, 77, 125, 134, 147`, `test_planck_mes_bounds.py:59`).

   Regression: `D_2(Σ²=1e-8) = 0.174112 μK²` anchor will shift by `≈ 6.4 × 10⁻⁶ μK²`. The anchor test uses `rel=1e-4` tolerance in the neighbouring cl_assembly suite (verify before changing). If the anchor is exact-match, the update must be paired with an anchor re-calibration commit.

2. **htt side**: fix internal inconsistency by setting
   ```python
   T0_uK = 2.72548e6
   ```
   (or derive it programmatically: `T0_uK = T0_K * 1e6`).
   Check `eps_ell` / `D_ell_from_eps` consumers — numerical drift is 3.67e-5 (relative), should be absorbed by existing tolerances but must be verified.

3. **docstrings**: the bass-side docstring at `planck_mes_bounds.py:35` says `T₀ = 2.7255 K ... (Fixsen ApJ 707, 916, 2009)`. After the numeric update, change the docstring text to `2.72548 K` to keep documentation and code aligned.

## 5. What this track commits now

SSOT-01 is a **diagnostic + guard** track. It does **not** modify `bass/`, because the bass_py session has the hierarchy module active (see `INDEPENDENT_TRACKS_PLAN.md` §0.1 conflict-avoidance rule). It also does not yet fix the htt-internal `T0_uK` inconsistency — that needs a dedicated commit with regression verification.

Commits under this track:

- This document (`docs/audits/SSOT_TCMB_DRIFT_2026-04-19.md`).
- `bass_py/htt/tests/test_ssot_drift.py` — single test asserting `C.T0_K == 2.72548` byte-exact, so any silent future change triggers a regression failure.

The `T0_uK` fix and the bass-side `2.7255 → 2.72548` migration are recorded here as **recommendations for a later coordinated commit**, gated on user approval and on bass_py session quiescence.

## 6. Sign-off gate

- [x] bass-side constants located and cross-referenced
- [x] htt-side constants located and cross-referenced
- [x] numerical impact quantified
- [x] htt-side anti-regression guard test drafted (`test_ssot_drift.py`)
- [ ] user approval on recommendation in §4 (required before any code change to `bass/` or to `htt.core.ssot.C.T0_uK`)
