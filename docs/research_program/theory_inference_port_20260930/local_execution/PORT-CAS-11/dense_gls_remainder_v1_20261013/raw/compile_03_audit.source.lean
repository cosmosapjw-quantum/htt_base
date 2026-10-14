import P11ADenseGLS

open Matrix MeasureTheory ProbabilityTheory P11ADenseGLS

/-! Frozen-statement conformance: each `example` restates the FROZEN_TARGETS.md type verbatim
and is closed by the compiled theorem, so a drifted statement fails to compile. -/

section Conformance
variable {n k : ℕ}

example (X : Matrix (Fin n) (Fin k) ℝ) (hX : X.rank = k) : Function.Injective X.mulVec :=
  mulVec_injective_of_rank_eq X hX
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : (gram C X).PosDef := gram_posDef C X hC hX
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : IsUnit (gram C X).det := gram_isUnit_det C X hC hX
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : glsM C X * X = 1 := gls_unbiased C X hC hX
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) :
    Xᵀ *ᵥ (C⁻¹ *ᵥ (y - X *ᵥ (glsM C X *ᵥ y))) = 0 := gls_normal_eq C X hC hX y
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ) :
    wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ := gls_minimizes C X hC hX y θ
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (y : Fin n → ℝ) (θ : Fin k → ℝ)
    (h : wrss C X y θ = wrss C X y (glsM C X *ᵥ y)) : θ = glsM C X *ᵥ y :=
  gls_minimizer_unique C X hC hX y θ h
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (W : Matrix (Fin n) (Fin n) ℝ)
    (hW : IsUnit W ∧ W * C * Wᵀ = 1) :
    G08AWhitening.IsMoorePenrose (W * X) (glsM C X * W⁻¹) ∧
      ∀ y : Fin n → ℝ, (glsM C X * W⁻¹) *ᵥ (W *ᵥ y) = glsM C X *ᵥ y :=
  gls_moorePenrose_link C X hC hX W hW
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) : glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹ :=
  gls_covariance C X hC hX
example (M : Matrix (Fin k) (Fin n) ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) (i : Fin k) : |(M *ᵥ r) i| ≤ ∑ j, |M i j| * b j :=
  remainder_componentwise M r b hr i
section
attribute [local instance] Matrix.linftyOpNormedAddCommGroup
example (M : Matrix (Fin k) (Fin n) ℝ) (r : Fin n → ℝ) (β : ℝ)
    (hβ : 0 ≤ β) (hr : ∀ j, |r j| ≤ β) : ‖M *ᵥ r‖ ≤ ‖M‖ * β := remainder_linfty M r β hβ hr
end
section
open scoped Matrix.Norms.L2Operator
example (M : Matrix (Fin k) (Fin n) ℝ) (r : EuclideanSpace ℝ (Fin n)) (β : ℝ)
    (hr : ‖r‖ ≤ β) : ‖(EuclideanSpace.equiv (Fin k) ℝ).symm (M *ᵥ r)‖ ≤ ‖M‖ * β :=
  remainder_l2 M r β hr
end
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r e : Fin n → ℝ) :
    glsM C X *ᵥ (X *ᵥ θ + r + e) = θ + glsM C X *ᵥ r + glsM C X *ᵥ e :=
  gls_decomposition C X hC hX θ r e
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) (i : Fin k) :
    |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j :=
  gls_bias_bound C X hC hX θ r b hr i
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (h : X.rank < k) : (gram C X).det = 0 := gram_det_zero_of_rank_lt C X h
example (X : Matrix (Fin n) (Fin k) ℝ) (h : X.rank < k) :
    ¬ ∃ M : Matrix (Fin k) (Fin n) ℝ, M * X = 1 := no_left_inverse_of_rank_lt X h
example : Xbad = !![1, 1; 1, 1] := rfl
example :
    Xbad.rank < 2 ∧ (gram (1 : Matrix (Fin 2) (Fin 2) ℝ) Xbad).det = 0 ∧
      ¬ ∃ M : Matrix (Fin 2) (Fin 2) ℝ, M * Xbad = 1 := negative_control
example (C : Matrix (Fin n) (Fin n) ℝ) (hC : C.PosSemidef)
    (m : EuclideanSpace ℝ (Fin n)) (M : Matrix (Fin k) (Fin n) ℝ) :
    (multivariateGaussian m C).map (linCLM M) =
      multivariateGaussian (linCLM M m) (M * C * Mᵀ) := gaussian_linear_pushforward C hC m M
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ)
    (hC : C.PosDef) (hX : X.rank = k) (θ : Fin k → ℝ) (r : Fin n → ℝ) :
    (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
      multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹ :=
  gls_estimator_law C X hC hX θ r
example (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin 13) ℝ)
    (hC : C.PosDef) (hX : X.rank = 13) (θ : Fin 13 → ℝ) (r b : Fin n → ℝ)
    (hr : ∀ j, |r j| ≤ b j) :
    (gram C X).PosDef ∧ glsM C X * X = 1 ∧
      (∀ y θ', wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ') ∧
      glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹ ∧
      (∀ i, |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j) ∧
      (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
        multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹ :=
  rank13_instance C X hC hX θ r b hr
end Conformance

#check @P11ADenseGLS.gram
#check @P11ADenseGLS.glsM
#check @P11ADenseGLS.wrss
#check @P11ADenseGLS.linCLM
#check @P11ADenseGLS.mulVec_injective_of_rank_eq
#check @P11ADenseGLS.gram_posDef
#check @P11ADenseGLS.gram_isUnit_det
#check @P11ADenseGLS.gls_unbiased
#check @P11ADenseGLS.gls_normal_eq
#check @P11ADenseGLS.wrss_split
#check @P11ADenseGLS.gls_minimizes
#check @P11ADenseGLS.gls_minimizer_unique
#check @P11ADenseGLS.gls_moorePenrose_link
#check @P11ADenseGLS.gls_covariance
#check @P11ADenseGLS.remainder_componentwise
#check @P11ADenseGLS.remainder_linfty
#check @P11ADenseGLS.remainder_l2
#check @P11ADenseGLS.gls_decomposition
#check @P11ADenseGLS.gls_bias_bound
#check @P11ADenseGLS.gram_det_zero_of_rank_lt
#check @P11ADenseGLS.no_left_inverse_of_rank_lt
#check @P11ADenseGLS.negative_control
#check @P11ADenseGLS.linCLM_adjoint
#check @P11ADenseGLS.gaussian_linear_pushforward
#check @P11ADenseGLS.gls_estimator_law
#check @P11ADenseGLS.rank13_instance

#print axioms P11ADenseGLS.mulVec_injective_of_rank_eq
#print axioms P11ADenseGLS.gram_posDef
#print axioms P11ADenseGLS.gram_isUnit_det
#print axioms P11ADenseGLS.gls_unbiased
#print axioms P11ADenseGLS.gls_normal_eq
#print axioms P11ADenseGLS.wrss_split
#print axioms P11ADenseGLS.gls_minimizes
#print axioms P11ADenseGLS.gls_minimizer_unique
#print axioms P11ADenseGLS.gls_moorePenrose_link
#print axioms P11ADenseGLS.gls_covariance
#print axioms P11ADenseGLS.remainder_componentwise
#print axioms P11ADenseGLS.remainder_linfty
#print axioms P11ADenseGLS.remainder_l2
#print axioms P11ADenseGLS.gls_decomposition
#print axioms P11ADenseGLS.gls_bias_bound
#print axioms P11ADenseGLS.gram_det_zero_of_rank_lt
#print axioms P11ADenseGLS.no_left_inverse_of_rank_lt
#print axioms P11ADenseGLS.Xbad_rank_lt
#print axioms P11ADenseGLS.negative_control
#print axioms P11ADenseGLS.linCLM_adjoint
#print axioms P11ADenseGLS.gaussian_linear_pushforward
#print axioms P11ADenseGLS.gls_estimator_law
#print axioms P11ADenseGLS.rank13_instance
