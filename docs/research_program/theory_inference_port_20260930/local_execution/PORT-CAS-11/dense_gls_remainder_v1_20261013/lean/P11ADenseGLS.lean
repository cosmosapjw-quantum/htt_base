import Mathlib
import G08AWhitening

/-!
P11-A (parent PORT-CAS-11, CAS_CONTRACT `CAS-11`): dense Gaussian GLS and deterministic
remainder, over real matrices indexed by `Fin n` (observations) / `Fin k` (coefficients).

Scope carried by the theorem types:
* `C` is a fixed, KNOWN, dense SPD covariance (`C.PosDef`; every cross-covariance allowed).
  Nothing here estimates `C`.
* `X` is a fixed design (fixed distances/selection), full column rank `X.rank = k`; the
  contract's rank 13 is the instance `rank13_instance`. Rank deficiency is not regularized
  (no ridge / jitter); it is a negative control.
* the remainder `r` is deterministic and enters the Gaussian mean, not the covariance.

Norm convention for `|M r| ≤ |M| b`: primary = componentwise bound matching the owning
code `np.abs(influence) @ bounds`; corollaries for the ℓ∞ and ℓ2 operator norms.
-/

noncomputable section

namespace P11ADenseGLS

open Matrix MeasureTheory ProbabilityTheory

variable {n k : ℕ}

/-- Gram (Fisher) matrix `Xᵀ C⁻¹ X`. -/
def gram (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) :
    Matrix (Fin k) (Fin k) ℝ := Xᵀ * C⁻¹ * X

/-- GLS estimator matrix `M = (Xᵀ C⁻¹ X)⁻¹ Xᵀ C⁻¹`. -/
def glsM (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) :
    Matrix (Fin k) (Fin n) ℝ := (gram C X)⁻¹ * Xᵀ * C⁻¹

/-- `C⁻¹`-weighted residual sum of squares. -/
def wrss (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) (y : Fin n → ℝ)
    (θ : Fin k → ℝ) : ℝ := (y - X *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - X *ᵥ θ))

/-- A rectangular matrix as a continuous linear map between Euclidean spaces. -/
def linCLM (M : Matrix (Fin k) (Fin n) ℝ) :
    EuclideanSpace ℝ (Fin n) →L[ℝ] EuclideanSpace ℝ (Fin k) :=
  LinearMap.toContinuousLinearMap (Matrix.toEuclideanLin M)

/-! ### Helpers -/

theorem posDef_transpose_eq (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosDef) : Cᵀ = C := by
  have h := hC.isHermitian
  unfold IsHermitian at h
  rwa [conjTranspose_eq_transpose_of_trivial] at h

theorem inv_transpose_eq (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosDef) : (C⁻¹)ᵀ = C⁻¹ := by
  rw [transpose_nonsing_inv, posDef_transpose_eq C hC]

theorem det_isUnit_of_posDef (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosDef) : IsUnit C.det :=
  (isUnit_iff_isUnit_det C).mp hC.isUnit

/-- `(X d) ⬝ (S v) = d ⬝ (Xᵀ (S v))`. -/
theorem dot_mulVec_left (X : Matrix (Fin n) (Fin k) ℝ) (d : Fin k → ℝ) (w : Fin n → ℝ) :
    (X *ᵥ d) ⬝ᵥ w = d ⬝ᵥ (Xᵀ *ᵥ w) := by
  rw [dotProduct_comm, dotProduct_mulVec, ← mulVec_transpose, dotProduct_comm]

/-! ### R0: full column rank gives injectivity -/

theorem mulVec_injective_of_rank_eq (X : Matrix (Fin n) (Fin k) ℝ) (hX : X.rank = k) :
    Function.Injective X.mulVec := by
  have h := LinearMap.finrank_range_add_finrank_ker X.mulVecLin
  have hr : Module.finrank ℝ (LinearMap.range X.mulVecLin) = k := hX
  rw [hr, Module.finrank_fin_fun] at h
  have hk : Module.finrank ℝ (LinearMap.ker X.mulVecLin) = 0 := by omega
  have hker : LinearMap.ker X.mulVecLin = ⊥ := Submodule.finrank_eq_zero.mp hk
  have hinj := LinearMap.ker_eq_bot.mp hker
  exact hinj

/-! ### R1: Gram positivity, unbiasedness, minimization -/

theorem gram_posDef (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : (gram C X).PosDef := by
  have h := hC.inv.conjTranspose_mul_mul_same (mulVec_injective_of_rank_eq X hX)
  rwa [conjTranspose_eq_transpose_of_trivial] at h

theorem gram_isUnit_det (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : IsUnit (gram C X).det :=
  det_isUnit_of_posDef _ (gram_posDef C X hC hX)

theorem gls_unbiased (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : glsM C X * X = 1 := by
  calc glsM C X * X = (gram C X)⁻¹ * gram C X := by
        simp only [glsM, gram, Matrix.mul_assoc]
    _ = 1 := nonsing_inv_mul _ (gram_isUnit_det C X hC hX)

theorem gram_mul_glsM (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : gram C X * glsM C X = Xᵀ * C⁻¹ := by
  simp only [glsM]
  rw [← Matrix.mul_assoc, ← Matrix.mul_assoc, mul_nonsing_inv _ (gram_isUnit_det C X hC hX),
    Matrix.one_mul]

theorem gls_normal_eq (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) :
    Xᵀ *ᵥ (C⁻¹ *ᵥ (y - X *ᵥ (glsM C X *ᵥ y))) = 0 := by
  have h : Xᵀ * C⁻¹ * X * glsM C X = Xᵀ * C⁻¹ := gram_mul_glsM C X hC hX
  calc Xᵀ *ᵥ (C⁻¹ *ᵥ (y - X *ᵥ (glsM C X *ᵥ y)))
      = (Xᵀ * C⁻¹) *ᵥ y - (Xᵀ * C⁻¹ * X * glsM C X) *ᵥ y := by
        simp only [mulVec_sub, mulVec_mulVec, Matrix.mul_assoc]
    _ = 0 := by rw [h, sub_self]

/-- Exact Pythagorean split of the weighted RSS around the GLS estimate. -/
theorem wrss_split (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ) :
    wrss C X y θ = wrss C X y (glsM C X *ᵥ y) +
      (X *ᵥ (glsM C X *ᵥ y - θ)) ⬝ᵥ (C⁻¹ *ᵥ (X *ᵥ (glsM C X *ᵥ y - θ))) := by
  set e := y - X *ᵥ (glsM C X *ᵥ y) with he
  set d := glsM C X *ᵥ y - θ with hd
  have hsplit : y - X *ᵥ θ = e + X *ᵥ d := by
    rw [he, hd, mulVec_sub]
    abel
  have hn : Xᵀ *ᵥ (C⁻¹ *ᵥ e) = 0 := gls_normal_eq C X hC hX y
  have hsym : ∀ a b : Fin n → ℝ, a ⬝ᵥ (C⁻¹ *ᵥ b) = b ⬝ᵥ (C⁻¹ *ᵥ a) := by
    intro a b
    rw [dotProduct_mulVec, ← mulVec_transpose, inv_transpose_eq C hC, dotProduct_comm]
  have hc1 : (X *ᵥ d) ⬝ᵥ (C⁻¹ *ᵥ e) = 0 := by
    rw [dot_mulVec_left, hn, dotProduct_zero]
  have hc2 : e ⬝ᵥ (C⁻¹ *ᵥ (X *ᵥ d)) = 0 := by rw [hsym, hc1]
  unfold wrss
  rw [hsplit, mulVec_add, add_dotProduct, dotProduct_add, dotProduct_add, hc1, hc2]
  ring

theorem gls_minimizes (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ) :
    wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ := by
  rw [wrss_split C X hC hX y θ]
  have h := hC.inv.posSemidef.dotProduct_mulVec_nonneg (X *ᵥ (glsM C X *ᵥ y - θ))
  rw [star_trivial] at h
  linarith

theorem gls_minimizer_unique (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ)
    (h : wrss C X y θ = wrss C X y (glsM C X *ᵥ y)) : θ = glsM C X *ᵥ y := by
  by_contra hne
  have hd : glsM C X *ᵥ y - θ ≠ 0 := fun h0 => hne (sub_eq_zero.mp h0).symm
  have hXd : X *ᵥ (glsM C X *ᵥ y - θ) ≠ 0 := by
    intro h0
    apply hd
    apply mulVec_injective_of_rank_eq X hX
    rw [h0, mulVec_zero]
  have hpos := hC.inv.dotProduct_mulVec_pos hXd
  rw [star_trivial] at hpos
  rw [wrss_split C X hC hX y θ] at h
  linarith

/-- Link to reviewed G08-A: with any whitening `W` (e.g. from `G08AWhitening.whitening_exists`),
`M W⁻¹` is the Moore-Penrose inverse of the whitened design `W X`, and it reproduces `M y`
on whitened data; hence `G08AWhitening.gls_minimum` applies to the GLS estimate. -/
theorem gls_moorePenrose_link (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (W : Matrix (Fin n) (Fin n) ℝ)
    (hW : IsUnit W ∧ W * C * Wᵀ = 1) :
    G08AWhitening.IsMoorePenrose (W * X) (glsM C X * W⁻¹) ∧
      ∀ y : Fin n → ℝ, (glsM C X * W⁻¹) *ᵥ (W *ᵥ y) = glsM C X *ᵥ y := by
  have hWdet : IsUnit W.det := (isUnit_iff_isUnit_det W).mp hW.1
  have h1 : Wᵀ * (W * C) = 1 := mul_eq_one_comm.mp hW.2
  have hinv : C⁻¹ = Wᵀ * W := inv_eq_left_inv (by rw [Matrix.mul_assoc]; exact h1)
  have hGdet := gram_isUnit_det C X hC hX
  have hG : gram C X = (W * X)ᵀ * (W * X) := by
    rw [gram, hinv, transpose_mul]
    simp only [Matrix.mul_assoc]
  have hGt : (gram C X)ᵀ = gram C X := by
    rw [hG, transpose_mul, transpose_transpose]
  have hGinvT : ((gram C X)⁻¹)ᵀ = (gram C X)⁻¹ := by
    rw [transpose_nonsing_inv, hGt]
  have hXp : glsM C X * W⁻¹ = (gram C X)⁻¹ * (W * X)ᵀ := by
    simp only [glsM, hinv, transpose_mul, Matrix.mul_assoc, mul_nonsing_inv W hWdet,
      Matrix.mul_one]
  have hGG : (gram C X)⁻¹ * ((W * X)ᵀ * (W * X)) = 1 := by
    rw [← hG]; exact nonsing_inv_mul _ hGdet
  refine ⟨⟨?_, ?_, ?_, ?_⟩, fun y => ?_⟩
  · rw [hXp]
    calc W * X * ((gram C X)⁻¹ * (W * X)ᵀ) * (W * X)
        = W * X * ((gram C X)⁻¹ * ((W * X)ᵀ * (W * X))) := by simp only [Matrix.mul_assoc]
      _ = W * X := by rw [hGG, Matrix.mul_one]
  · rw [hXp]
    calc (gram C X)⁻¹ * (W * X)ᵀ * (W * X) * ((gram C X)⁻¹ * (W * X)ᵀ)
        = ((gram C X)⁻¹ * ((W * X)ᵀ * (W * X))) * ((gram C X)⁻¹ * (W * X)ᵀ) := by
          simp only [Matrix.mul_assoc]
      _ = (gram C X)⁻¹ * (W * X)ᵀ := by rw [hGG, Matrix.one_mul]
  · rw [hXp, transpose_mul, transpose_mul, hGinvT, transpose_transpose, Matrix.mul_assoc]
  · rw [hXp, Matrix.mul_assoc, hGG, transpose_one]
  · rw [mulVec_mulVec, Matrix.mul_assoc, nonsing_inv_mul W hWdet, Matrix.mul_one]

/-! ### R2: covariance identity -/

theorem gls_covariance (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹ := by
  have hCdet := det_isUnit_of_posDef C hC
  have hGdet := gram_isUnit_det C X hC hX
  have hGt : (gram C X)ᵀ = gram C X := posDef_transpose_eq _ (gram_posDef C X hC hX)
  have hGinvT : ((gram C X)⁻¹)ᵀ = (gram C X)⁻¹ := by rw [transpose_nonsing_inv, hGt]
  have hCinvT := inv_transpose_eq C hC
  calc glsM C X * C * (glsM C X)ᵀ
      = (gram C X)⁻¹ * (Xᵀ * (C⁻¹ * C) * C⁻¹ * X) * (gram C X)⁻¹ := by
        simp only [glsM, transpose_mul, hCinvT, hGinvT, transpose_transpose, Matrix.mul_assoc]
    _ = (gram C X)⁻¹ * gram C X * (gram C X)⁻¹ := by
        rw [nonsing_inv_mul C hCdet, Matrix.mul_one]
        rfl
    _ = (gram C X)⁻¹ := by rw [nonsing_inv_mul _ hGdet, Matrix.one_mul]

/-! ### R3: deterministic remainder -/

theorem remainder_componentwise (M : Matrix (Fin k) (Fin n) ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) (i : Fin k) : |(M *ᵥ r) i| ≤ ∑ j, |M i j| * b j := by
  simp only [mulVec, dotProduct]
  calc |∑ j, M i j * r j| ≤ ∑ j, |M i j * r j| := Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ j, |M i j| * b j := Finset.sum_le_sum fun j _ => by
        rw [abs_mul]
        exact mul_le_mul_of_nonneg_left (hr j) (abs_nonneg _)

section LinftyOp
attribute [local instance] Matrix.linftyOpNormedAddCommGroup

theorem remainder_linfty (M : Matrix (Fin k) (Fin n) ℝ) (r : Fin n → ℝ) (β : ℝ)
    (hβ : 0 ≤ β) (hr : ∀ j, |r j| ≤ β) : ‖M *ᵥ r‖ ≤ ‖M‖ * β := by
  have hrn : ‖r‖ ≤ β := (pi_norm_le_iff_of_nonneg hβ).mpr fun j => by
    rw [Real.norm_eq_abs]; exact hr j
  exact (linfty_opNorm_mulVec M r).trans (mul_le_mul_of_nonneg_left hrn (norm_nonneg M))

end LinftyOp

section L2Op
open scoped Matrix.Norms.L2Operator

theorem remainder_l2 (M : Matrix (Fin k) (Fin n) ℝ) (r : EuclideanSpace ℝ (Fin n)) (β : ℝ)
    (hr : ‖r‖ ≤ β) : ‖(EuclideanSpace.equiv (Fin k) ℝ).symm (M *ᵥ r)‖ ≤ ‖M‖ * β :=
  (l2_opNorm_mulVec M r).trans (mul_le_mul_of_nonneg_left hr (norm_nonneg M))

end L2Op

theorem gls_decomposition (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r e : Fin n → ℝ) :
    glsM C X *ᵥ (X *ᵥ θ + r + e) = θ + glsM C X *ᵥ r + glsM C X *ᵥ e := by
  rw [mulVec_add, mulVec_add, mulVec_mulVec, gls_unbiased C X hC hX, one_mulVec]

theorem gls_bias_bound (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) (i : Fin k) :
    |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j := by
  rw [mulVec_add, mulVec_mulVec, gls_unbiased C X hC hX, one_mulVec, Pi.add_apply,
    add_sub_cancel_left]
  exact remainder_componentwise _ r b hr i

/-! ### R4: negative controls (rank deficiency is not regularized) -/

theorem gram_det_zero_of_rank_lt (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (h : X.rank < k) : (gram C X).det = 0 := by
  by_contra hdet
  have hu : IsUnit (gram C X) := (isUnit_iff_isUnit_det _).mpr (isUnit_iff_ne_zero.mpr hdet)
  have h1 := rank_of_isUnit _ hu
  rw [Fintype.card_fin] at h1
  have h2 : (gram C X).rank ≤ X.rank := rank_mul_le_right (Xᵀ * C⁻¹) X
  omega

theorem no_left_inverse_of_rank_lt (X : Matrix (Fin n) (Fin k) ℝ) (h : X.rank < k) :
    ¬ ∃ M : Matrix (Fin k) (Fin n) ℝ, M * X = 1 := by
  rintro ⟨M, hM⟩
  have h1 := rank_mul_le_right M X
  rw [hM, rank_one, Fintype.card_fin] at h1
  omega

def Xbad : Matrix (Fin 2) (Fin 2) ℝ := !![1, 1; 1, 1]

theorem Xbad_rank_lt : Xbad.rank < 2 := by
  by_contra h
  have h2 : Xbad.rank = 2 := le_antisymm (rank_le_width _) (not_lt.mp h)
  have hinj := mulVec_injective_of_rank_eq Xbad h2
  have hv : Xbad *ᵥ ![1, -1] = Xbad *ᵥ 0 := by
    ext i
    fin_cases i <;> simp [Xbad, mulVec, dotProduct, Fin.sum_univ_two]
  have h0 := congrFun (hinj hv) 0
  simp at h0

theorem negative_control :
    Xbad.rank < 2 ∧ (gram (1 : Matrix (Fin 2) (Fin 2) ℝ) Xbad).det = 0 ∧
      ¬ ∃ M : Matrix (Fin 2) (Fin 2) ℝ, M * Xbad = 1 :=
  ⟨Xbad_rank_lt, gram_det_zero_of_rank_lt _ _ Xbad_rank_lt,
    no_left_inverse_of_rank_lt _ Xbad_rank_lt⟩

/-! ### R5: actual Gaussian law of the GLS estimate -/

theorem linCLM_adjoint (M : Matrix (Fin k) (Fin n) ℝ) :
    (linCLM M).adjoint = linCLM Mᵀ := by
  unfold linCLM
  rw [← LinearMap.adjoint_toContinuousLinearMap, ← Matrix.toEuclideanLin_conjTranspose_eq_adjoint,
    conjTranspose_eq_transpose_of_trivial]

theorem linCLM_apply (M : Matrix (Fin k) (Fin n) ℝ) (v : EuclideanSpace ℝ (Fin n)) :
    WithLp.ofLp (linCLM M v) = M *ᵥ WithLp.ofLp v := rfl

theorem gaussian_linear_pushforward (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosSemidef)
    (m : EuclideanSpace ℝ (Fin n)) (M : Matrix (Fin k) (Fin n) ℝ) :
    (multivariateGaussian m C).map (linCLM M) =
      multivariateGaussian (linCLM M m) (M * C * Mᵀ) := by
  have hS : (M * C * Mᵀ).PosSemidef := by
    have h := hC.mul_mul_conjTranspose_same M
    rwa [conjTranspose_eq_transpose_of_trivial] at h
  apply IsGaussian.ext
  · simp only [id_eq, integral_id_multivariateGaussian]
    rw [ContinuousLinearMap.integral_id_map IsGaussian.integrable_id,
      integral_id_multivariateGaussian]
  · ext u v
    rw [covarianceBilin_map IsGaussian.memLp_two_id, covarianceBilin_multivariateGaussian hC,
      covarianceBilin_multivariateGaussian hS, linCLM_adjoint, linCLM_apply, linCLM_apply,
      ← mulVec_mulVec, ← mulVec_mulVec, dotProduct_mulVec (WithLp.ofLp u) M,
      ← mulVec_transpose]

theorem gls_estimator_law (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r : Fin n → ℝ) :
    (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
      multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹ := by
  rw [gaussian_linear_pushforward C hC.posSemidef _ (glsM C X), gls_covariance C X hC hX]
  congr 1
  apply WithLp.ofLp_injective
  rw [linCLM_apply, WithLp.ofLp_toLp, WithLp.ofLp_toLp, mulVec_add, mulVec_mulVec,
    gls_unbiased C X hC hX, one_mulVec]

/-! ### R6: the contract's rank-13 instance -/

theorem rank13_instance (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin 13) ℝ)
    (hC : C.PosDef) (hX : X.rank = 13) (θ : Fin 13 → ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) :
    (gram C X).PosDef ∧ glsM C X * X = 1 ∧
      (∀ y θ', wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ') ∧
      glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹ ∧
      (∀ i, |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j) ∧
      (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
        multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹ :=
  ⟨gram_posDef C X hC hX, gls_unbiased C X hC hX, gls_minimizes C X hC hX,
    gls_covariance C X hC hX, gls_bias_bound C X hC hX θ r b hr,
    gls_estimator_law C X hC hX θ r⟩

end P11ADenseGLS
