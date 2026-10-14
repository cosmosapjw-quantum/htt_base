import Mathlib
-- P12-A statement elaboration check: frozen signatures with `sorry` bodies (elaboration only).
namespace P12GaussianLaw.Stmt
open MeasureTheory ProbabilityTheory Matrix
open scoped MatrixOrder
variable {n : ℕ}
theorem law_eq_iff {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef) :
    multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2 := sorry
theorem rank_eq_of_law_eq {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef)
    (h : multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2) : S1.rank = S2.rank := sorry
theorem mean_of_law (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ) :
    ∫ x, x ∂(multivariateGaussian μ S) = μ := sorry
theorem mean_coord_of_law (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ)
    (i : Fin n) : ∫ x, x i ∂(multivariateGaussian μ S) = μ i := sorry
theorem covariance_of_law (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (i j : Fin n) :
    cov[fun x ↦ x i, fun x ↦ x j; multivariateGaussian μ S] = S i j := sorry
theorem covarianceBilin_of_law (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (x y : EuclideanSpace ℝ (Fin n)) :
    covarianceBilin (multivariateGaussian μ S) x y = x ⬝ᵥ S *ᵥ y := sorry
theorem centered_second_moment_of_law (μ : EuclideanSpace ℝ (Fin n))
    {S : Matrix (Fin n) (Fin n) ℝ} (hS : S.PosSemidef) (i j : Fin n) :
    ∫ x, (x i - μ i) * (x j - μ j) ∂(multivariateGaussian μ S) = S i j := sorry
theorem zero_covariance (μ : EuclideanSpace ℝ (Fin n)) :
    multivariateGaussian μ (0 : Matrix (Fin n) (Fin n) ℝ) = Measure.dirac μ := sorry
noncomputable def Sa : Matrix (Fin 2) (Fin 2) ℝ := Matrix.diagonal ![1, 0]
noncomputable def Sb : Matrix (Fin 2) (Fin 2) ℝ := Matrix.diagonal ![0, 1]
noncomputable def e1 : EuclideanSpace ℝ (Fin 2) := EuclideanSpace.single 1 1
theorem Sa_posSemidef : Sa.PosSemidef := sorry
theorem Sb_posSemidef : Sb.PosSemidef := sorry
theorem Sa_rank : Sa.rank = 1 := sorry
theorem Sb_rank : Sb.rank = 1 := sorry
theorem singular_example :
    multivariateGaussian 0 Sa ≠ multivariateGaussian e1 Sa ∧
    multivariateGaussian 0 Sa ≠ multivariateGaussian 0 Sb ∧
    multivariateGaussian (0 : EuclideanSpace ℝ (Fin 2)) Sa ≠ multivariateGaussian 0 0 := sorry
theorem mean_only_comparison_insufficient :
    ∃ (μ : EuclideanSpace ℝ (Fin 2)) (S1 S2 : Matrix (Fin 2) (Fin 2) ℝ),
      S1.PosSemidef ∧ S2.PosSemidef ∧ S1.rank = 1 ∧ S2.rank = 1 ∧
      multivariateGaussian μ S1 ≠ multivariateGaussian μ S2 := sorry
theorem covariance_only_comparison_insufficient :
    ∃ (μ1 μ2 : EuclideanSpace ℝ (Fin 2)) (S : Matrix (Fin 2) (Fin 2) ℝ),
      S.PosSemidef ∧ S.rank = 1 ∧ multivariateGaussian μ1 S ≠ multivariateGaussian μ2 S := sorry
theorem non_psd_eq_dirac (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : ¬ S.PosSemidef) : multivariateGaussian μ S = Measure.dirac μ := sorry
noncomputable def N1 : Matrix (Fin 1) (Fin 1) ℝ := Matrix.diagonal (fun _ ↦ -1)
theorem non_psd_caveat :
    ¬ N1.PosSemidef ∧ N1 ≠ 0 ∧
      multivariateGaussian (0 : EuclideanSpace ℝ (Fin 1)) N1 = multivariateGaussian 0 0 := sorry
theorem law_eq_iff_needs_psd :
    ¬ ∀ (μ1 μ2 : EuclideanSpace ℝ (Fin 1)) (S1 S2 : Matrix (Fin 1) (Fin 1) ℝ),
      (multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2) := sorry
end P12GaussianLaw.Stmt
