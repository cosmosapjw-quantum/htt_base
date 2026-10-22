import Mathlib

/-!
# P12-A (PORT-CAS-12): equality of finite-dimensional Gaussian laws

Two multivariate Gaussian laws on the same finite measurement space `EuclideanSpace ℝ (Fin n)`
are equal iff their means and positive semidefinite covariance matrices are equal. Singular
(rank-deficient) and zero covariances are included. The law is Mathlib's
`ProbabilityTheory.multivariateGaussian μ S`, the pushforward of the standard Gaussian under
`x ↦ μ + √S x`.

Scope: two supplied laws on one fixed space. Not claimed: global physical injectivity,
different conditioning or measurement spaces, non-Gaussian laws.
-/

namespace P12GaussianLaw

open MeasureTheory ProbabilityTheory Matrix
open scoped MatrixOrder

variable {n : ℕ}

/-! ## G2: moments of the law -/

/-- G2 mean (no PSD premise needed). -/
theorem mean_of_law (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ) :
    ∫ x, x ∂(multivariateGaussian μ S) = μ :=
  integral_id_multivariateGaussian

/-- G2 coordinatewise mean (no PSD premise needed). -/
theorem mean_coord_of_law (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ)
    (i : Fin n) : ∫ x, x i ∂(multivariateGaussian μ S) = μ i := by
  have h := ContinuousLinearMap.integral_comp_id_comm
    (IsGaussian.integrable_id (μ := multivariateGaussian μ S)) (EuclideanSpace.proj (𝕜 := ℝ) i)
  rw [mean_of_law] at h
  simpa using h

/-- G2 covariance of coordinates. -/
theorem covariance_of_law (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (i j : Fin n) :
    cov[fun x ↦ x i, fun x ↦ x j; multivariateGaussian μ S] = S i j :=
  covariance_eval_multivariateGaussian hS i j

/-- G2 covariance bilinear form. -/
theorem covarianceBilin_of_law (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (x y : EuclideanSpace ℝ (Fin n)) :
    covarianceBilin (multivariateGaussian μ S) x y = x ⬝ᵥ S *ᵥ y :=
  covarianceBilin_multivariateGaussian hS x y

/-- G2 explicit centered second moments. -/
theorem centered_second_moment_of_law (μ : EuclideanSpace ℝ (Fin n))
    {S : Matrix (Fin n) (Fin n) ℝ} (hS : S.PosSemidef) (i j : Fin n) :
    ∫ x, (x i - μ i) * (x j - μ j) ∂(multivariateGaussian μ S) = S i j := by
  rw [← covariance_of_law μ hS i j]
  simp only [covariance, mean_coord_of_law]

/-! ## G1: law equality iff mean and covariance equality -/

/-- G1. -/
theorem law_eq_iff {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef) :
    multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2 := by
  constructor
  · intro h
    refine ⟨?_, ?_⟩
    · calc μ1 = ∫ x, x ∂(multivariateGaussian μ1 S1) := (mean_of_law μ1 S1).symm
        _ = ∫ x, x ∂(multivariateGaussian μ2 S2) := by rw [h]
        _ = μ2 := mean_of_law μ2 S2
    · ext i j
      calc S1 i j = cov[fun x ↦ x i, fun x ↦ x j; multivariateGaussian μ1 S1] :=
            (covariance_of_law μ1 h1 i j).symm
        _ = cov[fun x ↦ x i, fun x ↦ x j; multivariateGaussian μ2 S2] := by rw [h]
        _ = S2 i j := covariance_of_law μ2 h2 i j
  · rintro ⟨rfl, rfl⟩
    rfl

/-- G1 corollary: equal laws lie in the same covariance rank stratum. -/
theorem rank_eq_of_law_eq {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef)
    (h : multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2) : S1.rank = S2.rank := by
  rw [((law_eq_iff h1 h2).1 h).2]

/-! ## G3: zero covariance -/

/-- G3. -/
theorem zero_covariance (μ : EuclideanSpace ℝ (Fin n)) :
    multivariateGaussian μ (0 : Matrix (Fin n) (Fin n) ℝ) = Measure.dirac μ := by
  rw [multivariateGaussian, CFC.sqrt_zero, map_zero]
  simp only [_root_.zero_apply, add_zero]
  rw [Measure.map_const, measure_univ, one_smul]

/-! ## G4: singular examples -/

/-- Rank-one PSD covariance supported on coordinate 0. -/
noncomputable def Sa : Matrix (Fin 2) (Fin 2) ℝ := Matrix.diagonal ![1, 0]
/-- Rank-one PSD covariance supported on coordinate 1. -/
noncomputable def Sb : Matrix (Fin 2) (Fin 2) ℝ := Matrix.diagonal ![0, 1]
/-- Unit mean shift along coordinate 1 (the null direction of `Sa`). -/
noncomputable def e1 : EuclideanSpace ℝ (Fin 2) := EuclideanSpace.single 1 1

theorem Sa_posSemidef : Sa.PosSemidef := by
  unfold Sa
  rw [posSemidef_diagonal_iff]
  intro i
  fin_cases i <;> simp

theorem Sb_posSemidef : Sb.PosSemidef := by
  unfold Sb
  rw [posSemidef_diagonal_iff]
  intro i
  fin_cases i <;> simp

theorem Sa_rank : Sa.rank = 1 := by
  classical
  unfold Sa
  rw [rank_diagonal, Fintype.card_eq_one_iff]
  refine ⟨⟨0, by simp⟩, ?_⟩
  rintro ⟨i, hi⟩
  fin_cases i
  · rfl
  · simp at hi

theorem Sb_rank : Sb.rank = 1 := by
  classical
  unfold Sb
  rw [rank_diagonal, Fintype.card_eq_one_iff]
  refine ⟨⟨1, by simp⟩, ?_⟩
  rintro ⟨i, hi⟩
  fin_cases i
  · simp at hi
  · rfl

/-- G4. -/
theorem singular_example :
    multivariateGaussian 0 Sa ≠ multivariateGaussian e1 Sa ∧
    multivariateGaussian 0 Sa ≠ multivariateGaussian 0 Sb ∧
    multivariateGaussian (0 : EuclideanSpace ℝ (Fin 2)) Sa ≠ multivariateGaussian 0 0 := by
  refine ⟨?_, ?_, ?_⟩
  · intro h
    have hμ := ((law_eq_iff Sa_posSemidef Sa_posSemidef).1 h).1
    have h1 := congrArg (fun v : EuclideanSpace ℝ (Fin 2) ↦ v 1) hμ
    simp [e1] at h1
  · intro h
    have hS := ((law_eq_iff Sa_posSemidef Sb_posSemidef).1 h).2
    have h1 := congrArg (fun M : Matrix (Fin 2) (Fin 2) ℝ ↦ M 0 0) hS
    simp [Sa, Sb] at h1
  · intro h
    have hS := ((law_eq_iff Sa_posSemidef PosSemidef.zero).1 h).2
    have h1 := congrArg (fun M : Matrix (Fin 2) (Fin 2) ℝ ↦ M 0 0) hS
    simp [Sa] at h1

theorem mean_only_comparison_insufficient :
    ∃ (μ : EuclideanSpace ℝ (Fin 2)) (S1 S2 : Matrix (Fin 2) (Fin 2) ℝ),
      S1.PosSemidef ∧ S2.PosSemidef ∧ S1.rank = 1 ∧ S2.rank = 1 ∧
      multivariateGaussian μ S1 ≠ multivariateGaussian μ S2 :=
  ⟨0, Sa, Sb, Sa_posSemidef, Sb_posSemidef, Sa_rank, Sb_rank, singular_example.2.1⟩

theorem covariance_only_comparison_insufficient :
    ∃ (μ1 μ2 : EuclideanSpace ℝ (Fin 2)) (S : Matrix (Fin 2) (Fin 2) ℝ),
      S.PosSemidef ∧ S.rank = 1 ∧ multivariateGaussian μ1 S ≠ multivariateGaussian μ2 S :=
  ⟨0, e1, Sa, Sa_posSemidef, Sa_rank, singular_example.1⟩

/-! ## G5: non-PSD caveat -/

/-- G5: at this Mathlib pin a non-PSD `S` gives `CFC.sqrt S = 0`, hence the Dirac law. -/
theorem non_psd_eq_dirac (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : ¬ S.PosSemidef) : multivariateGaussian μ S = Measure.dirac μ :=
  multivariateGaussian_of_not_posSemidef μ hS

/-- A non-PSD `1 × 1` "covariance". -/
noncomputable def N1 : Matrix (Fin 1) (Fin 1) ℝ := Matrix.diagonal (fun _ ↦ -1)

theorem N1_not_posSemidef : ¬ N1.PosSemidef := by
  unfold N1
  rw [posSemidef_diagonal_iff]
  intro h
  have := h 0
  norm_num at this

theorem non_psd_caveat :
    ¬ N1.PosSemidef ∧ N1 ≠ 0 ∧
      multivariateGaussian (0 : EuclideanSpace ℝ (Fin 1)) N1 = multivariateGaussian 0 0 := by
  refine ⟨N1_not_posSemidef, ?_, ?_⟩
  · intro h
    have h1 := congrArg (fun M : Matrix (Fin 1) (Fin 1) ℝ ↦ M 0 0) h
    simp [N1] at h1
  · rw [non_psd_eq_dirac _ N1_not_posSemidef, zero_covariance]

theorem law_eq_iff_needs_psd :
    ¬ ∀ (μ1 μ2 : EuclideanSpace ℝ (Fin 1)) (S1 S2 : Matrix (Fin 1) (Fin 1) ℝ),
      (multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2) := by
  intro H
  obtain ⟨_, hne, heq⟩ := non_psd_caveat
  exact hne ((H 0 0 N1 0).1 heq).2

end P12GaussianLaw
