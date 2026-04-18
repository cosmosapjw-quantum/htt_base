# AUDIT — Phase LB-2b (PSTF RHS driver + T4/T5/T6/T7)

**Date**: 2026-04-19
**Phase**: LB-2b — ``bass/hierarchy/hierarchy_rhs.py`` driver plus
full implementations of T4 (accel × divergence), T5 (accel × gradient),
T6 (vorticity × stays-at-ℓ) and T7 (shear → ℓ+2). Orthogonal Bianchi I
/ V / VII₀ target — default ``A_a = ω_a = 0`` renders T4/T5/T6 exactly
zero; T7 is active whenever shear and Π_{ℓ+2} are both non-zero.
**Baseline commit**: `19d02b5` (pre-session, LB-2a)
**Baseline test count**: 2,295 passing (post LB-2a)
**Post-audit test count**: 2,322 passing (27 new)
**Verdict**: **통과** (no P0/P1; three P2/P3 items documented below).

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics / math source | Ellis §4.6; lowell §6; Pontzen-Challinor 2007 (C4) | Nine-term 1+3 covariant PSTF hierarchy |
| Term functions (algebra) | `bass/hierarchy/terms.py` T4–T7 | Pure PSTF contractions for acceleration, vorticity and shear-up couplings |
| Driver | `bass/hierarchy/hierarchy_rhs.py` | Sums T1..T9 + K, converts overdot → η-prime, handles Σ → σ units |
| Σ → σ conversion | `proper_shear_at_eta` | Divides `TetradBackgroundState.sigma_tensor` by `a(η)` (F1 audit of LB-2a) |
| Interfaces consumed | `ClosureStrategy` (HardCut), `CollisionOperator` (Zero / test Doppler) | Supply Π_{L+1}, Π_{L+2}, K_{A_ℓ} |
| Tests | `test_hierarchy_rhs.py` (14) + extended `test_terms.py` (new T4/T5/T6/T7 coverage) | H-18..H-26 + orthogonal-zero guardrails |

Source of truth: `02_multipole_hierarchy_spec.md §1` (formula) and §11.4/§11.5 (test criteria). Code generates values; hand-worked low-ℓ cases (T4 ℓ=0 scalar, T5 ℓ=1 vector, T6 ℓ=1 via explicit ε_{bca}, T7 ℓ=2 via σ⊗σ construction) pin the contraction paths.

## 2. Contract / interface table

| API | Input contract | Output | Units |
|---|---|---|---|
| `T4_accel_divergence(ell, Π_{ℓ+1}, A)` | `Π.ndim=ℓ+1`; `A.shape=(3,)` | rank-ℓ PSTF | A [1/Mpc] |
| `T5_accel_gradient(ell, Π_{ℓ−1}, A)` | `Π.ndim=ℓ−1`; ℓ≥1; `A.shape=(3,)` | rank-ℓ PSTF | A [1/Mpc] |
| `T6_vorticity(ell, Π_ℓ, ω)` | `Π.ndim=ℓ`; ℓ≥1; `ω.shape=(3,)` | rank-ℓ PSTF | ω [1/Mpc] |
| `T7_shear_up(ell, Π_{ℓ+2}, σ)` | `Π.ndim=ℓ+2`; `σ.shape=(3,3)` | rank-ℓ PSTF | σ proper [1/Mpc] |
| `hierarchy_rhs_photon(η, y, *, L_max, bg_table, tetrad_state, closure, collision, …)` | `y.shape=((L_max+1)²,)`; `bg_table` has `interp_a`, `interp_Theta`; optional `tetrad_state` supplies `.eta`, `.sigma_tensor` | same shape dy/dη | Π'(η) [unitless × 1/Mpc ⋅ Mpc = unitless/Mpc] |
| `proper_shear_at_eta(η, tetrad, a)` | tetrad may be None; `a > 0` | (3,3) proper σ | 1/Mpc |

Invariants preserved: every term returns a PSTF (symmetric + trace-free) tensor of the output rank; driver's `pstf_pack` on the sum implicitly re-projects (idempotent on a PSTF input to ε_mach). All shape-validation raises `ValueError`; unknown Bianchi type / missing `tetrad_state` path returns zero σ rather than silently failing.

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| T4 prefactor `−(ℓ+1)(ℓ−2)/(2ℓ+3)` | ✅ | `terms.py:T4_accel_divergence`; hand-worked ℓ=0 scalar `+2/3 A·Π_1` |
| T4 vanishing at ℓ=2 by `(ℓ−2)` | ✅ | `test_T4_ell_2_prefactor_zero` |
| T5 prefactor `(ℓ+3)` | ✅ | hand-worked ℓ=1 gives `4 A Π_0` vector |
| T5 ℓ=0 = 0 (no Π_{-1}) | ✅ | `test_T5_ell_0_returns_zero` |
| T6 input rank = ℓ (not ℓ−1!) | ✅ | spec §1 notation `Π_{A_{ℓ-1}}^c` = rank-ℓ; confirmed against Ellis §4.6 derivation |
| T6 `ε_{bca}` sign convention | ✅ | `_levi_civita_3` matches Arfken Ch 3 orientation; tested via explicit einsum cross-product |
| T6 prefactor `ℓ` (vanishes at ℓ=0) | ✅ | `test_T6_ell_0_returns_zero` |
| T7 prefactor `−(ℓ−1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5))` | ✅ | hand-worked ℓ=2 → −4/21 |
| T7 at ℓ=1 vanishes by `(ℓ−1)` | ✅ | `test_h14_T7_ell_1_is_zero_by_prefactor` |
| T7 at ℓ=0 non-zero (`+2/15 σ:Π_2`) | ✅ | prefactor −(−1)(1)(2)/(3·5) = +2/15 correctly computed |
| σ → proper conversion applied before feeding T7/T8/T9 | ✅ | `proper_shear_at_eta` divides by `a(η)`; `test_proper_shear_divides_by_a` |
| FLRW limit (σ=0, ω=0, A=0, K=0, zero ∇̃): dy/dη = −a × (4/3) Θ × y | ✅ | H-19 exact to 1e-11 |
| Zero state → zero dy/dη | ✅ | H-18 to 1e-15 |
| Orthogonal Bianchi: T4 = T5 = T6 = 0 at A = ω = 0 | ✅ | 15 guardrail tests at ℓ = 0..4 |
| PSTF invariants preserved under ``solve_ivp`` | ✅ | H-26 tested at 6 snapshots through the window |

## 4. Equation-to-code mapping

| Spec formula | Code path | Hand-verification |
|---|---|---|
| `Π̇ + T1 + … + T9 = K` | `hierarchy_rhs_photon`: `Π'(η) = a · (K − Σ T_n)` | LHS–RHS sign convention matches spec §4.1 (``Π̇ = Π'(η)/a`` → multiply by a) |
| `−((ℓ+1)(ℓ−2)/(2ℓ+3)) A^b Π_{A_ℓ b}` | `np.tensordot(Π, A, axes=([-1],[0]))` then PSTF, × prefactor | ℓ=0: `(2/3) A·Π_1` scalar |
| `(ℓ+3) A_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}` | outer product `A ⊗ Π_{ℓ−1}` → PSTF, × (ℓ+3) | ℓ=1: `4 A Π_0` vector |
| `ℓ ω^b ε_{bc a_ℓ} Π^c_{A_{ℓ−1}}` | `εω := ε_{bca} ω^b`; `εω_{ca}` contracted on axis 0 of `Π_ell_full` | ℓ=1: cross-product formula reproduced |
| `−((ℓ−1)(ℓ+1)(ℓ+2)/((2ℓ+3)(2ℓ+5))) σ^{bc} Π_{A_ℓ bc}` | `np.tensordot(Π_{ℓ+2}, σ, axes=([-2,-1],[0,1]))` then PSTF | ℓ=2: `−4/21 · σ:Π_4` matches test |
| `σ = Σ / a` (F1) | `proper_shear_at_eta` applies `1/a(η)` before T7/T8/T9 use | `test_proper_shear_divides_by_a` to 1e-10 |

No dead code; no silent fallbacks inside LB-2b scope. The closure interface remains a Protocol so T3/T7 at the top of the tower call through LB-3's eventual strategy selection. The collision interface remains a Protocol; LB-2b ships only `ZeroCollisionOperator` (production) plus a tiny test-only Doppler operator.

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| Solver suitability | Algebraic layer (no ODE within the driver call). `solve_ivp` in tests uses default RK45 — non-stiff at the LB-2b non-collisional regime. LB-5 will switch to LSODA for the full tilted + Thomson case. |
| Tolerance sensitivity | H-18..H-23 all atol ≤ 1e-11; H-26 PSTF-invariants 1e-10. H-25 relaxed to 2 % (forward-Euler cross-check). |
| Overflow / underflow | No exp/log at this layer; contraction magnitudes are O(‖σ‖·‖Π‖) which stays well inside float64 for any physically-sensible cosmology. |
| σ interpolation artifact | `proper_shear_at_eta` uses nearest-grid-point lookup (matches `tetrad_state.shear_at`); quantisation error `O(Δη_grid · ∂σ/∂η)`. Acceptable for orthogonal Bianchi I (constant proper-time Σ_+ after early transient); LB-5 will spline. |
| Warm-start / state leakage | Pure-function driver — reads `y_flat`, emits `dy`; no hidden state. `HardCutClosure` does a defensive `copy()` of within-tower tensors to prevent aliasing. |
| Determinism | No RNG in production; tests use fixed seeds. |
| Baseline reproduction | All LB-2a tests unchanged (154 → still 154 in the T1/T2/T3/T8/T9 + storage suite). |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| F1 | testing | P2 | `test_h25_shear_injection_slope_matches_T9` uses a forward-Euler self-consistency cross-check rather than the spec's "4 a σ Δη absolute slope (2 %)". Reason: at `a ≈ 1e−4` the monopole damping rate `(4/3) a Θ ≈ 0.1/Mpc` makes a 5-grid-step window violate the small-cΔη assumption (`cΔη ≈ 0.8` observed). A short 1-step window with forward-Euler reference satisfies the spirit of the integration smoke (driver ≡ RHS) while keeping the tolerance honest. Direct coefficient verification at t=0 is delivered by H-22 (1e-11 absolute match against `4 a σ_ab`). | Documented; not repaired — H-22 + H-25 jointly cover the original spec intent. |
| F2 | numerical | P2 | `proper_shear_at_eta` uses nearest-neighbor lookup on the tetrad_state grid (spec §8 acknowledges). Quantisation error at mid-grid ~2% of σ magnitude when the driver is called between grid points. | Left as-is; LB-5 will upgrade to spline per spec §8 explicitly. |
| F3 | doc | P3 | LB-2b driver docstring does not point at the eventual LB-2c plan for `accel_vector` / `vorticity_vector` non-zero paths. | Inline comment mentions "orthogonal Bianchi: vectors are 0"; sufficient for now. |
| F4 | interface | P3 | ``_DopplerCollisionAtEll1`` in `test_hierarchy_rhs.py` duplicates the eventual LB-4 Thomson-drag K_1 source; when LB-4 lands that test-only operator should migrate to using the real `ThomsonCollisionOperator` with zero polarisation. | Flagged for LB-4 session. |

No P0 / P1 items.

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (formula + limits) | **PASSED** | T4/T5/T6/T7 formulas + prefactor signs confirmed by hand; FLRW / orthogonal / zero-state limits reproduced to 1e-11..1e-15 |
| Code (contract satisfaction) | **PASSED** | shape validation enforced; Σ → σ conversion explicit (F1 audit discharged); docstrings cite Ellis §4.6, lowell §6, Pontzen-Challinor 2007, 00_conventions.md §3 |
| Numerical (stability + regression) | **PASSED** | 2,322 / 2,322 green (baseline 2,295 + 27 new); PSTF invariants preserved under integration; no stiffness blow-up in H-24/H-25/H-26 |

## 8. Minimal repair plan — applied in-session

No P0 / P1 repairs needed. Items documented for future phases (F2 → LB-5 spline upgrade; F4 → LB-4 migration).

The one in-session **doc-level** tightening applied:

| Patch | Target | Status |
|---|---|---|
| A | `terms.py` header docstring: re-describe T4/T5/T6/T7 as LB-2b deliverables (was "deferred to LB-2b"); cite orthogonal-Bianchi activation surface | ✅ `bass/hierarchy/terms.py:1-37` |

## 9. Minimal test set (delivered — 27 new tests)

Baseline reproduction: `test_h18_zero_state_flrw_gives_zero_derivative`, `test_h22_shear_injection_populates_quadrupole`, `test_T4_ell_0_scalar_output`, `test_T5_ell_1_is_A_times_monopole`, `test_T6_ell_1_is_cross_product`, `test_h14_T7_ell_2_hand_computed` — pass criterion `atol = 1e-13..1e-11`.

Edge / adversarial: `test_T4_ell_2_prefactor_zero`, `test_h14_T7_ell_1_is_zero_by_prefactor`, `test_T5_ell_0_returns_zero`, `test_T6_ell_0_returns_zero`, `test_rhs_wrong_state_length_raises`, `test_*_wrong_shape_raises` (×3).

Physics sanity: `test_T4_vanishes_at_orthogonal_background`, `test_T5_vanishes_at_orthogonal_background`, `test_T6_vanishes_at_orthogonal_background`, `test_h14_T7_vanishes_for_zero_shear`, `test_h19_flrw_reduces_to_T1_damping`, `test_h20_dipole_only_leaves_quadrupole_zero_at_background`.

Numerical stability: `test_h24_free_streaming_integration_is_finite`, `test_h25_shear_injection_slope_matches_T9`, `test_h26_integration_preserves_pstf_structure`.

Regression: full bass+tsc run — **2,322 green** (baseline 2,295 + 27 new).

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (no P0/P1; three documented P2/P3 items)
* **지금 당장 구현/수정한 1개**: doc-level tightening of `terms.py` header to reflect LB-2b's T4/T5/T6/T7 activation. No numeric change.
* **지금 손대면 안 되는 1개**: rewriting `proper_shear_at_eta` to use a spline interpolator. Nearest-grid-point is a deliberate parallel to `tetrad_state.shear_at`; both will rotate to splines together at LB-5 integrator setup, where one coherent interpolation policy governs every background quantity.

## Gallery refresh

`plots/physics_gallery/09_pstf_hierarchy/` extended by 4 LB-2b plots
(12 total): `09_T7_shear_up_sweep.png`, `10_orthogonal_T4_T5_T6_vanishing.png`, `11_rhs_driver_shear_injection.png`,  `12_sigma_vs_Sigma_conversion.png`.
All four were visually inspected; physical behaviour matches
expectation (T7 norm even-symmetric in Σ_+; T4/T5/T6 at 1e-17 floor
for orthogonal; even-ℓ shear cascade Π_0 → Π_2 → Π_4 in the
integration trajectory; Σ/(aσ) = 1 identity for the conversion
self-consistency panel).

## Outstanding items carried forward

* **F1** (P2): H-25 tolerance strategy — delegated to H-22 for exact-coefficient coverage.
* **F2** (P2): σ spline interpolation — reassess at LB-5 integrator setup.
* **F3** (P3): driver docstring / LB-2c cross-reference — add when LB-2c spec is drafted.
* **F4** (P3): `_DopplerCollisionAtEll1` test fixture migration — flagged for LB-4.
