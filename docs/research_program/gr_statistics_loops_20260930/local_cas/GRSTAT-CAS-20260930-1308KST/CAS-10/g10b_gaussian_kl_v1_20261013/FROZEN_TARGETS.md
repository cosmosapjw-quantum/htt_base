# G10-B frozen targets (written before any proof compile)

Origin: authored fresh in this run. Directory T did not exist when this author process
started (no partial files from the interrupted earlier process were present; nothing was
inherited or overwritten). Frozen 2026-10-13 before the first compile of
`lean/G10BGaussianKL.lean`. Only the three reused import modules had been compiled
(compile_01..03, unchanged sources) when this file was written.

## Original statement (card G10-B, CAS-10 contract, theory source)

* Card `tasks/G10-B.json` scope_original: "C01/C03 morphology counterexample와 actual Gaussian
  pushforward/equal-law/KL." lean_steps: (1) define the original Gaussian observation law,
  covariance blocks, compression map and fixed conditioning exactly; (2) prove orthogonal
  block-rotation pushforward invariance as a measure equality; (3) derive compressed
  observation-law equality for the counterexample tuples and apply a full-data Gaussian KL
  theorem; (4) connect the finite KL expression to the actual relative-entropy definition.
  Pitfalls: singular covariance must not be substituted into the SPD formula; blockwise
  marginal invariance must not be inflated to joint-law invariance.
* Contract CAS-10 (`cas/contracts/CAS-10.json`) C03: "Verify the finite Gaussian
  equal-covariance KL expression 225 H^2/(64 sigma_p^2) and blockwise rotation invariance of
  the compression; probability-law conclusions must cite/prove their separate
  measure-theoretic step." Assumption: "Independent isotropic Gaussian blocks for equal-law
  benchmark". Uncontracted target: "Compressed Gaussian laws equal; fullKL225H^2/(64sigma_p^2)".
* Theory (`statistics/INFORMATION_LIMIT_THEOREMS.md` §4, (I9)-(I10), Theorem II):
  `X_j ~ N(mu_j, sigma_j^2 I_{d_j})` independent, `d_j = (1,3,1,3,5)`, `sigma_j > 0`, in
  orthonormal sector coordinates; `P_j = |X_j|^2`; the joint law of `(P_j)` is identical under
  the two means of Theorem I; every powers-only randomized test has equal rejection
  probability; `D_KL(P_mu || P_mu') = (1/2) sum_j |mu_j - mu'_j|^2 / sigma_j^2 = 225 H^2/(64 sigma_p^2) > 0`.

## Encoding decisions (stated, not hidden)

* Data space: `Idx d → ℝ` with `Idx d := Σ j : J, Fin (d j)` (coordinate k of sector j).
* "Independent isotropic Gaussian blocks": `obsLaw d μ σ := Measure.pi (fun i => gaussianReal
  (μ i) (σ_{i.1}^2))`, i.e. all coordinates independent, variance σ_j² inside sector j. This
  is the literal product law of (I9). Its identification with Mathlib's
  `multivariateGaussian` with block-diagonal covariance is a separate target (B1).
* "Fixed conditioning": the law depends only on the fixed mean vector and fixed σ; there is
  no auxiliary/conditioning variable (fixed observer, fixed coordinates). No conditioning
  operator is formalized.
* Compression: `powers d x j := ∑ k, x ⟨j,k⟩^2` (separate-sector powers, no calibration
  factors; any fixed positive calibration is a measurable post-composition, covered by T4).
* Block rotation: `blockMap d R x ⟨j,k⟩ := (R j *ᵥ x_j) k`, with hypothesis
  `∀ j, (R j)ᵀ * R j = 1` (orthogonal in every sector, identity allowed).
* KL: Mathlib `InformationTheory.klDiv` (actual measure-theoretic relative entropy,
  `ℝ≥0∞`-valued, defined through `llr = log rnDeriv`).
* The T-sector coordinate of the explicit tuple is `(3√6 H/16, 0,0,0,0)` with respect to
  an orthonormal basis of trace-free symmetric 3×3 matrices (Frobenius) whose first element
  is `E1 = diag(2,-1,-1)/√6`; target X3 proves `diag(T) = (3√6H/16)•E1` and that `E1` is
  symmetric, trace-free and Frobenius-unit. Completion of `E1` to a full orthonormal basis
  is not formalized; all law/KL targets hold for an arbitrary common T-sector mean.

## Lean signatures (module `G10BGaussianKL`, namespace `G10BGaussianKL`)

```lean
import Mathlib
import CAS10C01
import CAS10C03
import P12GaussianLaw

open MeasureTheory ProbabilityTheory InformationTheory Matrix
open scoped ENNReal NNReal

variable {J : Type*} [Fintype J] [DecidableEq J] (d : J → ℕ)
abbrev Idx := Σ j : J, Fin (d j)
noncomputable def coordVar (σ : J → ℝ) (i : Idx d) : ℝ≥0 := ⟨σ i.1 ^ 2, sq_nonneg _⟩
noncomputable def coordLaw {ι : Type*} [Fintype ι] (μ : ι → ℝ) (w : ι → ℝ≥0) : Measure (ι → ℝ) :=
  Measure.pi fun i => gaussianReal (μ i) (w i)
noncomputable def obsLaw (μ : Idx d → ℝ) (σ : J → ℝ) : Measure (Idx d → ℝ) := coordLaw μ (coordVar d σ)
def powers (x : Idx d → ℝ) : J → ℝ := fun j => ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2
def blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) (x : Idx d → ℝ) : Idx d → ℝ :=
  fun i => (R i.1 *ᵥ fun k => x ⟨i.1, k⟩) i.2
```

### Generic targets (any finite sector set J, any dimensions d)

| id | name | statement |
|---|---|---|
| T1 | `obsLaw_map_blockMap` | `(hR : ∀ j, (R j)ᵀ * R j = 1) (μ) (σ : J → ℝ) : (obsLaw d μ σ).map (blockMap d R) = obsLaw d (blockMap d R μ) σ` (joint-law pushforward; no positivity of σ needed, degenerate σ_j = 0 allowed since the statement is a law identity, not an SPD formula) |
| T1b | `obsLaw_zero_map_blockMap` | `(hR) (σ) : (obsLaw d 0 σ).map (blockMap d R) = obsLaw d 0 σ` (isotropic noise invariance) |
| T2 | `powers_blockMap` | `(hR) (x) : powers d (blockMap d R x) = powers d x` |
| T3 | `compressed_law_eq` | `(hR) (μ σ) : (obsLaw d (blockMap d R μ) σ).map (powers d) = (obsLaw d μ σ).map (powers d)` (joint law of all J powers) |
| T4 | `powersOnly_integral_eq` | `(hR) (μ σ) (φ : (J → ℝ) → ℝ) (hφ : Measurable φ) : ∫ x, φ (powers d x) ∂(obsLaw d (blockMap d R μ) σ) = ∫ x, φ (powers d x) ∂(obsLaw d μ σ)` (covers every measurable randomized test φ with values in [0,1]) |
| T4b | `powersOnly_power_le_size` | `(hR) (μ σ) (φ) (hφ) (α : ℝ) (hsize : ∫ x, φ (powers d x) ∂(obsLaw d μ σ) ≤ α) : ∫ x, φ (powers d x) ∂(obsLaw d (blockMap d R μ) σ) ≤ α` |
| K1 | `klDiv_gaussianReal_same_var` | `(a b : ℝ) {v : ℝ≥0} (hv : v ≠ 0) : klDiv (gaussianReal a v) (gaussianReal b v) = ENNReal.ofReal ((a - b) ^ 2 / (2 * v))` |
| K2 | `klDiv_coordLaw` | `{ι} [Fintype ι] (μ ν : ι → ℝ) (w : ι → ℝ≥0) (hw : ∀ i, w i ≠ 0) : klDiv (coordLaw μ w) (coordLaw ν w) = ENNReal.ofReal (∑ i, (μ i - ν i) ^ 2 / (2 * w i))` |
| K3 | `klDiv_obsLaw` | `(μ ν : Idx d → ℝ) (σ : J → ℝ) (hσ : ∀ j, 0 < σ j) : klDiv (obsLaw d μ σ) (obsLaw d ν σ) = ENNReal.ofReal ((1 / 2) * ∑ i : Idx d, (μ i - ν i) ^ 2 / σ i.1 ^ 2)` |
| B1 | `obsLaw_toLp_eq_multivariateGaussian` | `(μ σ) : (obsLaw d μ σ).map (WithLp.toLp 2) = multivariateGaussian (WithLp.toLp 2 μ) (Matrix.diagonal fun i : Idx d => σ i.1 ^ 2)` |
| B2 | `obsLaw_eq_iff` | `(μ ν σ) : obsLaw d μ σ = obsLaw d ν σ ↔ μ = ν` (via P12 `law_eq_iff`; any σ, including singular) |

### Application to the C01/C03 counterexample (J = Fin 5)

```lean
def blockDim (j : Fin 5) : ℕ := match j.val with | 0 => 1 | 1 => 3 | 2 => 1 | 3 => 3 | _ => 5
abbrev Obs := Idx blockDim → ℝ
def meanOf (z0 : ℝ) (z1 : Fin 3 → ℝ) (m : ℝ) (p : Fin 3 → ℝ) (t : Fin 5 → ℝ) : Obs  -- sector-wise
def ofMean (u : CAS10C03.Mean) : Obs := meanOf u.z0 u.z1 u.m u.p u.t
def rotP : (j : Fin 5) → Matrix (Fin (blockDim j)) (Fin (blockDim j)) ℝ  -- CAS10C03.R on sector 3, 1 elsewhere
```

| id | name | statement |
|---|---|---|
| A1 | `rotP_orthogonal` | `∀ j, (rotP j)ᵀ * rotP j = 1` |
| A2 | `blockMap_rotP_first` | `(H z0 m z1 t) : blockMap blockDim rotP (ofMean (CAS10C03.first H z0 m z1 t)) = ofMean (CAS10C03.second H z0 m z1 t)` |
| A3 | `compressed_laws_equal` | `(H z0 m z1 t) (σ : Fin 5 → ℝ) : (obsLaw blockDim (ofMean (CAS10C03.second H z0 m z1 t)) σ).map (powers blockDim) = (obsLaw blockDim (ofMean (CAS10C03.first H z0 m z1 t)) σ).map (powers blockDim)` |
| A4 | `powersOnly_tests_agree` | `(H z0 m z1 t σ) (φ : (Fin 5 → ℝ) → ℝ) (hφ : Measurable φ) : ∫ x, φ (powers blockDim x) ∂(obsLaw blockDim (ofMean (second ..)) σ) = ∫ x, φ (powers blockDim x) ∂(obsLaw blockDim (ofMean (first ..)) σ)` |
| A5 | `full_kl_eq` | `(H z0 m z1 t σ) (hσ : ∀ j, 0 < σ j) : klDiv (obsLaw blockDim (ofMean (first ..)) σ) (obsLaw blockDim (ofMean (second ..)) σ) = ENNReal.ofReal (225 * H ^ 2 / (64 * σ 3 ^ 2))` |
| A5b | `full_kl_eq_C03` | same hypotheses: `klDiv (..first..) (..second..) = ENNReal.ofReal (CAS10C03.KLQuadratic (σ 0) (σ 1) (σ 2) (σ 3) (σ 4) (first ..) (second ..))` |
| A6 | `full_kl_pos` | `(hσ) (hH : H ≠ 0) : 0 < klDiv (..first..) (..second..)` and `full_kl_ne_top : (hσ) → klDiv (..first..) (..second..) ≠ ∞` |
| A7 | `full_laws_ne` | `(σ) (hH : H ≠ 0) : obsLaw blockDim (ofMean (first ..)) σ ≠ obsLaw blockDim (ofMean (second ..)) σ` (non-vacuity: the compressed equality is not a full-law equality) |
| A8 | `full_kl_singular_branch` | `(σ) (hσ3 : σ 3 = 0) (hH : H ≠ 0) : klDiv (..first..) (..second..) = ∞` (boundary: singular slope covariance; the SPD formula is NOT used) |
| X1 | `slope_vectors_agree` | `CAS10C01.p1 H = CAS10C03.p H ∧ CAS10C01.p2 H = CAS10C03.pPrime H` |
| X2 | `powers_explicit_first` / `powers_explicit_second` | for `explicitFirst H := CAS10C03.first H (5/4) (7*H/4) ![3/4,0,0] (tCoord H)` (resp. `second`), `tCoord H := ![3 * √6 * H / 16, 0, 0, 0, 0]`: `powers blockDim (ofMean (explicitFirst H)) = ![25/16, 9/16, 49*H^2/16, 225*H^2/64, 27*H^2/128]`, and `powers_explicit_matches_C01`: `(∀ j : Fin 4, powers blockDim (ofMean (explicitFirst H)) j.castSucc = (CAS10C01.expectedPowers H).1 j) ∧ powers blockDim (ofMean (explicitFirst H)) 4 = (CAS10C01.expectedPowers H).2` |
| X3 | `tDiag_eq_coord_E1`, `E1_symm`, `E1_trace`, `E1_frobenius` | `Matrix.diagonal (CAS10C01.Tdiag H) = (3 * √6 * H / 16) • E1`, `E1ᵀ = E1`, `E1.trace = 0`, `∑ i, ∑ j, E1 i j ^ 2 = 1`, with `E1 := (√6)⁻¹ • Matrix.diagonal ![2, -1, -1]` |
| N1 | `anisotropic_rotation_changes_law` | `∃ (μ : Obs) (w : Idx blockDim → ℝ≥0), (coordLaw μ w).map (blockMap blockDim rotP) ≠ coordLaw (blockMap blockDim rotP μ) w` (proof-route negative control: without isotropy the rotation step fails; it does NOT assert that anisotropic compressed laws differ) |

Negative controls / non-vacuity: A7, A6 (KL>0), A8 (singular branch = ∞), N1.

## Not targeted (explicitly out of scope)

* Whether anisotropic noise actually makes the compressed laws differ (only N1 proof-route
  failure is targeted); masks, cross-block errors, priors, real-survey estimators.
* Uniform consistency, minimax statements, the Φ(-|Δ|/(2σ_p)) consistency remark.
* Physical admissibility of the tuples (C01/C02/G10-A own that); scientific admission.
* Construction of a complete orthonormal basis of trace-free symmetric matrices.
