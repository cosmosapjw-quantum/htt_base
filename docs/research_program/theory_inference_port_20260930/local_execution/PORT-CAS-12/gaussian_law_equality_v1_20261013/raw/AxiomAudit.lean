import P12GaussianLaw
-- P12-A axiom audit: each frozen statement restated verbatim and closed by the compiled theorem.
open MeasureTheory ProbabilityTheory Matrix P12GaussianLaw
open scoped MatrixOrder
section
variable {n : ℕ}
example {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef) :
    multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2 :=
  law_eq_iff h1 h2
example {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef)
    (h : multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2) : S1.rank = S2.rank :=
  rank_eq_of_law_eq h1 h2 h
example (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ) :
    ∫ x, x ∂(multivariateGaussian μ S) = μ := mean_of_law μ S
example (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ)
    (i : Fin n) : ∫ x, x i ∂(multivariateGaussian μ S) = μ i := mean_coord_of_law μ S i
example (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (i j : Fin n) :
    cov[fun x ↦ x i, fun x ↦ x j; multivariateGaussian μ S] = S i j := covariance_of_law μ hS i j
example (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (x y : EuclideanSpace ℝ (Fin n)) :
    covarianceBilin (multivariateGaussian μ S) x y = x ⬝ᵥ S *ᵥ y := covarianceBilin_of_law μ hS x y
example (μ : EuclideanSpace ℝ (Fin n))
    {S : Matrix (Fin n) (Fin n) ℝ} (hS : S.PosSemidef) (i j : Fin n) :
    ∫ x, (x i - μ i) * (x j - μ j) ∂(multivariateGaussian μ S) = S i j :=
  centered_second_moment_of_law μ hS i j
example (μ : EuclideanSpace ℝ (Fin n)) :
    multivariateGaussian μ (0 : Matrix (Fin n) (Fin n) ℝ) = Measure.dirac μ := zero_covariance μ
example (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : ¬ S.PosSemidef) : multivariateGaussian μ S = Measure.dirac μ := non_psd_eq_dirac μ hS
end
example : Sa = Matrix.diagonal ![1, 0] := rfl
example : Sb = Matrix.diagonal ![0, 1] := rfl
example : e1 = EuclideanSpace.single 1 1 := rfl
example : N1 = Matrix.diagonal (fun _ ↦ -1) := rfl
example : Sa.PosSemidef := Sa_posSemidef
example : Sb.PosSemidef := Sb_posSemidef
example : Sa.rank = 1 := Sa_rank
example : Sb.rank = 1 := Sb_rank
example :
    multivariateGaussian 0 Sa ≠ multivariateGaussian e1 Sa ∧
    multivariateGaussian 0 Sa ≠ multivariateGaussian 0 Sb ∧
    multivariateGaussian (0 : EuclideanSpace ℝ (Fin 2)) Sa ≠ multivariateGaussian 0 0 :=
  singular_example
example :
    ∃ (μ : EuclideanSpace ℝ (Fin 2)) (S1 S2 : Matrix (Fin 2) (Fin 2) ℝ),
      S1.PosSemidef ∧ S2.PosSemidef ∧ S1.rank = 1 ∧ S2.rank = 1 ∧
      multivariateGaussian μ S1 ≠ multivariateGaussian μ S2 := mean_only_comparison_insufficient
example :
    ∃ (μ1 μ2 : EuclideanSpace ℝ (Fin 2)) (S : Matrix (Fin 2) (Fin 2) ℝ),
      S.PosSemidef ∧ S.rank = 1 ∧ multivariateGaussian μ1 S ≠ multivariateGaussian μ2 S :=
  covariance_only_comparison_insufficient
example :
    ¬ N1.PosSemidef ∧ N1 ≠ 0 ∧
      multivariateGaussian (0 : EuclideanSpace ℝ (Fin 1)) N1 = multivariateGaussian 0 0 :=
  non_psd_caveat
example :
    ¬ ∀ (μ1 μ2 : EuclideanSpace ℝ (Fin 1)) (S1 S2 : Matrix (Fin 1) (Fin 1) ℝ),
      (multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2) :=
  law_eq_iff_needs_psd
#print axioms P12GaussianLaw.law_eq_iff
#print axioms P12GaussianLaw.rank_eq_of_law_eq
#print axioms P12GaussianLaw.mean_of_law
#print axioms P12GaussianLaw.mean_coord_of_law
#print axioms P12GaussianLaw.covariance_of_law
#print axioms P12GaussianLaw.covarianceBilin_of_law
#print axioms P12GaussianLaw.centered_second_moment_of_law
#print axioms P12GaussianLaw.zero_covariance
#print axioms P12GaussianLaw.Sa_posSemidef
#print axioms P12GaussianLaw.Sb_posSemidef
#print axioms P12GaussianLaw.Sa_rank
#print axioms P12GaussianLaw.Sb_rank
#print axioms P12GaussianLaw.singular_example
#print axioms P12GaussianLaw.mean_only_comparison_insufficient
#print axioms P12GaussianLaw.covariance_only_comparison_insufficient
#print axioms P12GaussianLaw.non_psd_eq_dirac
#print axioms P12GaussianLaw.N1_not_posSemidef
#print axioms P12GaussianLaw.non_psd_caveat
#print axioms P12GaussianLaw.law_eq_iff_needs_psd
