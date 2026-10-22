import Mathlib
import G08AWhitening

/-! Statement-elaboration check ONLY (pre-freeze). Proofs are `sorry` here on purpose;
this file is never a proof artifact. The proof file is lean/P11ADenseGLS.lean. -/

noncomputable section
namespace P11ADenseGLSStmt
open Matrix MeasureTheory ProbabilityTheory
variable {n k : ℕ}

def gram (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) :
    Matrix (Fin k) (Fin k) ℝ := Xᵀ * C⁻¹ * X
def glsM (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) :
    Matrix (Fin k) (Fin n) ℝ := (gram C X)⁻¹ * Xᵀ * C⁻¹
def wrss (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) (y : Fin n → ℝ)
    (θ : Fin k → ℝ) : ℝ := (y - X *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - X *ᵥ θ))
def linCLM (M : Matrix (Fin k) (Fin n) ℝ) :
    EuclideanSpace ℝ (Fin n) →L[ℝ] EuclideanSpace ℝ (Fin k) :=
  LinearMap.toContinuousLinearMap (Matrix.toEuclideanLin M)

theorem mulVec_injective_of_rank_eq (X : Matrix (Fin n) (Fin k) ℝ) (hX : X.rank = k) :
    Function.Injective X.mulVec := sorry
theorem gram_posDef (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : (gram C X).PosDef := sorry
theorem gram_isUnit_det (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : IsUnit (gram C X).det := sorry
theorem gls_unbiased (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : glsM C X * X = 1 := sorry
theorem gls_normal_eq (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) :
    Xᵀ *ᵥ (C⁻¹ *ᵥ (y - X *ᵥ (glsM C X *ᵥ y))) = 0 := sorry
theorem gls_minimizes (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ) :
    wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ := sorry
theorem gls_minimizer_unique (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ)
    (h : wrss C X y θ = wrss C X y (glsM C X *ᵥ y)) : θ = glsM C X *ᵥ y := sorry
theorem gls_moorePenrose_link (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (W : Matrix (Fin n) (Fin n) ℝ)
    (hW : IsUnit W ∧ W * C * Wᵀ = 1) :
    G08AWhitening.IsMoorePenrose (W * X) (glsM C X * W⁻¹) ∧
      ∀ y : Fin n → ℝ, (glsM C X * W⁻¹) *ᵥ (W *ᵥ y) = glsM C X *ᵥ y := sorry
theorem gls_covariance (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹ := sorry
theorem remainder_componentwise (M : Matrix (Fin k) (Fin n) ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) (i : Fin k) : |(M *ᵥ r) i| ≤ ∑ j, |M i j| * b j := sorry

section LinftyOp
attribute [local instance] Matrix.linftyOpNormedAddCommGroup
theorem remainder_linfty (M : Matrix (Fin k) (Fin n) ℝ) (r : Fin n → ℝ) (β : ℝ)
    (hβ : 0 ≤ β) (hr : ∀ j, |r j| ≤ β) : ‖M *ᵥ r‖ ≤ ‖M‖ * β := sorry
end LinftyOp

section L2Op
open scoped Matrix.Norms.L2Operator
theorem remainder_l2 (M : Matrix (Fin k) (Fin n) ℝ) (r : EuclideanSpace ℝ (Fin n)) (β : ℝ)
    (hr : ‖r‖ ≤ β) : ‖(EuclideanSpace.equiv (Fin k) ℝ).symm (M *ᵥ r)‖ ≤ ‖M‖ * β := sorry
end L2Op

theorem gls_decomposition (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r e : Fin n → ℝ) :
    glsM C X *ᵥ (X *ᵥ θ + r + e) = θ + glsM C X *ᵥ r + glsM C X *ᵥ e := sorry
theorem gls_bias_bound (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) (i : Fin k) :
    |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j := sorry
theorem gram_det_zero_of_rank_lt (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (h : X.rank < k) : (gram C X).det = 0 := sorry
theorem no_left_inverse_of_rank_lt (X : Matrix (Fin n) (Fin k) ℝ) (h : X.rank < k) :
    ¬ ∃ M : Matrix (Fin k) (Fin n) ℝ, M * X = 1 := sorry
def Xbad : Matrix (Fin 2) (Fin 2) ℝ := !![1, 1; 1, 1]
theorem negative_control :
    Xbad.rank < 2 ∧ (gram (1 : Matrix (Fin 2) (Fin 2) ℝ) Xbad).det = 0 ∧
      ¬ ∃ M : Matrix (Fin 2) (Fin 2) ℝ, M * Xbad = 1 := sorry
theorem gaussian_linear_pushforward (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosSemidef)
    (m : EuclideanSpace ℝ (Fin n)) (M : Matrix (Fin k) (Fin n) ℝ) :
    (multivariateGaussian m C).map (linCLM M) =
      multivariateGaussian (linCLM M m) (M * C * Mᵀ) := sorry
theorem gls_estimator_law (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r : Fin n → ℝ) :
    (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
      multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹ := sorry
theorem rank13_instance (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin 13) ℝ)
    (hC : C.PosDef) (hX : X.rank = 13) (θ : Fin 13 → ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) :
    (gram C X).PosDef ∧ glsM C X * X = 1 ∧
      (∀ y θ', wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ') ∧
      glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹ ∧
      (∀ i, |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j) ∧
      (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
        multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹ := sorry

end P11ADenseGLSStmt
