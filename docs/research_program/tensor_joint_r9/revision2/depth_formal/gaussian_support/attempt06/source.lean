import Mathlib.Probability.Distributions.Gaussian.Multivariate
import Mathlib.MeasureTheory.Measure.Support
import Mathlib.Analysis.InnerProductSpace.Adjoint
import Mathlib.Topology.Algebra.Module.FiniteDimension

/-!
D2 support component for a fixed, specified finite-dimensional Gaussian law.
No positive-definiteness assumption; zero covariance and empty index sets are allowed.
This does not prove the pseudoinverse chi-square law, D4, or FORMAL_DEPTH admission.
-/

set_option autoImplicit false
open MeasureTheory ProbabilityTheory Matrix
open scoped NNReal ENNReal MatrixOrder

namespace R9Gaussian

/-- A continuous map with closed range transports full support onto its range. -/
theorem support_map_of_closed_range {X Y : Type*}
    [TopologicalSpace X] [MeasurableSpace X] [BorelSpace X]
    [TopologicalSpace Y] [MeasurableSpace Y] [BorelSpace Y]
    (P : Measure X) [P.IsOpenPosMeasure] (f : X → Y)
    (hf : Continuous f) (hc : IsClosed (Set.range f)) :
    (P.map f).support = Set.range f := by
  ext y
  rw [Measure.support_eq_forall_isOpen]
  constructor
  · intro hy
    by_contra hn
    have hp := hy (Set.range f)ᶜ hn hc.isOpen_compl
    rw [Measure.map_apply hf.measurable hc.measurableSet.compl] at hp
    have he : f ⁻¹' (Set.range f)ᶜ = ∅ := by ext x; simp
    simp [he] at hp
  · rintro ⟨x, rfl⟩ U hx hU
    rw [Measure.map_apply hf.measurable hU.measurableSet]
    exact (hU.preimage hf).measure_pos P ⟨x, hx⟩

theorem stdGaussian_openPos {ι : Type*} [Fintype ι] :
    (stdGaussian (EuclideanSpace ℝ ι)).IsOpenPosMeasure := by
  letI : (gaussianReal 0 1).IsOpenPosMeasure :=
    (gaussianReal_absolutelyContinuous' 0 (by norm_num : (1 : ℝ≥0) ≠ 0)).isOpenPosMeasure
  rw [← map_pi_eq_stdGaussian]
  exact (PiLp.continuous_toLp 2 (fun _ : ι => ℝ)).isOpenPosMeasure_map
    (WithLp.toLp_surjective 2)

/-- Finite-dimensional affine ranges are closed even when the map is singular. -/
theorem affine_range_closed {ι κ : Type*} [Fintype ι] [Fintype κ]
    (m : EuclideanSpace ℝ κ)
    (A : EuclideanSpace ℝ ι →L[ℝ] EuclideanSpace ℝ κ) :
    IsClosed (Set.range (fun x => m + A x)) := by
  have he : Set.range (fun x => m + A x) =
      (Homeomorph.addLeft m) '' (LinearMap.range A.toLinearMap : Set _) := by
    ext y
    change (∃ x, m + A x = y) ↔ ∃ z, (∃ x, A x = z) ∧ m + z = y
    constructor
    · rintro ⟨x, rfl⟩; exact ⟨A x, ⟨x, rfl⟩, rfl⟩
    · rintro ⟨z, ⟨x, rfl⟩, rfl⟩; exact ⟨x, rfl⟩
  rw [he]
  exact (Homeomorph.addLeft m).isClosed_image.mpr
    (LinearMap.range A.toLinearMap).closed_of_finiteDimensional

/-- The PSD square root and the covariance have exactly the same image. -/
theorem range_sqrt {ι : Type*} [Fintype ι] [DecidableEq ι]
    (C : Matrix ι ι ℝ) (hC : C.PosSemidef) :
    Set.range (toEuclideanCLM (𝕜 := ℝ) (CFC.sqrt C)) =
      Set.range (toEuclideanCLM (𝕜 := ℝ) C) := by
  let A := toEuclideanCLM (𝕜 := ℝ) (CFC.sqrt C)
  have ha : IsSelfAdjoint A := (CFC.sqrt_nonneg C).isSelfAdjoint.map _
  have hs : A * A = toEuclideanCLM (𝕜 := ℝ) C := by
    dsimp [A]
    rw [← map_mul, CFC.sqrt_mul_sqrt_self C hC.nonneg]
  have hr := LinearMap.range_self_comp_adjoint A.toLinearMap
  rw [ContinuousLinearMap.adjoint_toLinearMap, ha.adjoint_eq] at hr
  have he : A.toLinearMap ∘ₗ A.toLinearMap =
      (toEuclideanCLM (𝕜 := ℝ) C).toLinearMap := by
    change (A * A).toLinearMap = _
    rw [hs]
  rw [he] at hr
  exact congrArg (fun S : Submodule ℝ (EuclideanSpace ℝ ι) => (S : Set (EuclideanSpace ℝ ι))) hr.symm

/-- Topological support of N(m,C) is m + Im(C), including singular and zero C. -/
theorem support_multivariateGaussian {ι : Type*} [Fintype ι] [DecidableEq ι]
    (m : EuclideanSpace ℝ ι) (C : Matrix ι ι ℝ) (hC : C.PosSemidef) :
    (multivariateGaussian m C).support =
      Set.range (fun x => m + toEuclideanCLM (𝕜 := ℝ) C x) := by
  letI := stdGaussian_openPos (ι := ι)
  rw [multivariateGaussian, support_map_of_closed_range _ _ (by fun_prop)
    (affine_range_closed m _)]
  have hr := range_sqrt C hC
  ext y
  constructor
  · rintro ⟨x, rfl⟩
    obtain ⟨z, hz⟩ := hr ▸ (show toEuclideanCLM (𝕜 := ℝ) (CFC.sqrt C) x ∈
      Set.range (toEuclideanCLM (𝕜 := ℝ) (CFC.sqrt C)) from ⟨x, rfl⟩)
    exact ⟨z, congrArg (m + ·) hz⟩
  · rintro ⟨x, rfl⟩
    obtain ⟨z, hz⟩ := hr.symm ▸ (show toEuclideanCLM (𝕜 := ℝ) C x ∈
      Set.range (toEuclideanCLM (𝕜 := ℝ) C) from ⟨x, rfl⟩)
    exact ⟨z, congrArg (m + ·) hz⟩

theorem support_zero_covariance {ι : Type*} [Fintype ι] [DecidableEq ι]
    (m : EuclideanSpace ℝ ι) :
    (multivariateGaussian m (0 : Matrix ι ι ℝ)).support = {m} := by
  rw [support_multivariateGaussian m 0 (Matrix.PosSemidef.zero)]
  simp

/-- Coordinate form matches the D2 affine set; the mean is specified, never zero-filled. -/
theorem mem_support_iff {ι : Type*} [Fintype ι] [DecidableEq ι]
    (m y : EuclideanSpace ℝ ι) (C : Matrix ι ι ℝ) (hC : C.PosSemidef) :
    y ∈ (multivariateGaussian m C).support ↔
      ∃ u : ι → ℝ, WithLp.ofLp y = WithLp.ofLp m + C *ᵥ u := by
  rw [support_multivariateGaussian m C hC]
  constructor
  · rintro ⟨x, rfl⟩
    exact ⟨WithLp.ofLp x, rfl⟩
  · rintro ⟨u, hu⟩
    refine ⟨WithLp.toLp 2 u, ?_⟩
    exact (WithLp.ofLp_injective 2 hu).symm

/-- A point outside the affine support cannot be rescued by a small quadratic score. -/
theorem measure_outside_affine_support {ι : Type*} [Fintype ι] [DecidableEq ι]
    (m : EuclideanSpace ℝ ι) (C : Matrix ι ι ℝ) (hC : C.PosSemidef) :
    multivariateGaussian m C
      (Set.range (fun x => m + toEuclideanCLM (𝕜 := ℝ) C x))ᶜ = 0 := by
  rw [← support_multivariateGaussian m C hC]
  exact Measure.measure_compl_support

/-- Zero covariance is a Dirac law at the supplied mean, with no stochastic residual. -/
theorem zero_covariance_law {ι : Type*} [Fintype ι] [DecidableEq ι]
    (m : EuclideanSpace ℝ ι) :
    multivariateGaussian m (0 : Matrix ι ι ℝ) = Measure.dirac m := by
  simp [multivariateGaussian]

/-- Connect the concrete Gaussian construction to any Gaussian with the stated moments.
The covariance premise is an equality of the actual full covariance bilinear form,
not a support or whitening premise. -/
theorem gaussian_eq_of_moments {ι : Type*} [Fintype ι] [DecidableEq ι]
    (P : Measure (EuclideanSpace ℝ ι)) [IsGaussian P]
    (m : EuclideanSpace ℝ ι) (C : Matrix ι ι ℝ) (hC : C.PosSemidef)
    (hm : P[id] = m)
    (hc : ∀ x y : EuclideanSpace ℝ ι, covarianceBilin P x y = x ⬝ᵥ C *ᵥ y) :
    P = multivariateGaussian m C := by
  apply IsGaussian.ext
  · simpa using hm
  · ext x y
    exact (hc x y).trans (covarianceBilin_multivariateGaussian hC x y).symm

theorem support_gaussian_of_moments {ι : Type*} [Fintype ι] [DecidableEq ι]
    (P : Measure (EuclideanSpace ℝ ι)) [IsGaussian P]
    (m : EuclideanSpace ℝ ι) (C : Matrix ι ι ℝ) (hC : C.PosSemidef)
    (hm : P[id] = m)
    (hc : ∀ x y : EuclideanSpace ℝ ι, covarianceBilin P x y = x ⬝ᵥ C *ᵥ y) :
    P.support = Set.range (fun x => m + toEuclideanCLM (𝕜 := ℝ) C x) := by
  rw [gaussian_eq_of_moments P m C hC hm hc]
  exact support_multivariateGaussian m C hC

/-- The residual map may be rectangular or singular. Its covariance operator is
L C L*, i.e. H C Hᵀ in the real orthonormal coordinates. -/
theorem support_map_gaussian {ι κ : Type*} [Fintype ι] [Fintype κ] [DecidableEq ι]
    (m : EuclideanSpace ℝ ι) (C : Matrix ι ι ℝ) (hC : C.PosSemidef)
    (L : EuclideanSpace ℝ ι →L[ℝ] EuclideanSpace ℝ κ) :
    ((multivariateGaussian m C).map L).support =
      Set.range (fun x => L m + (L ∘L toEuclideanCLM (𝕜 := ℝ) C ∘L L.adjoint) x) := by
  let A := toEuclideanCLM (𝕜 := ℝ) (CFC.sqrt C)
  let B := L ∘L A
  have ha : IsSelfAdjoint A := (CFC.sqrt_nonneg C).isSelfAdjoint.map _
  have hs : A ∘L A = toEuclideanCLM (𝕜 := ℝ) C := by
    change A * A = _
    dsimp [A]
    rw [← map_mul, CFC.sqrt_mul_sqrt_self C hC.nonneg]
  have hb : B ∘L B.adjoint = L ∘L toEuclideanCLM (𝕜 := ℝ) C ∘L L.adjoint := by
    dsimp [B]
    rw [ContinuousLinearMap.adjoint_comp, ha.adjoint_eq]
    simp only [ContinuousLinearMap.comp_assoc]
    rw [← ContinuousLinearMap.comp_assoc A A, hs]
  have hr := LinearMap.range_self_comp_adjoint B.toLinearMap
  rw [ContinuousLinearMap.adjoint_toLinearMap] at hr
  have he : B.toLinearMap ∘ₗ B.adjoint.toLinearMap =
      (L ∘L toEuclideanCLM (𝕜 := ℝ) C ∘L L.adjoint).toLinearMap := by
    change (B ∘L B.adjoint).toLinearMap = _
    rw [hb]
  rw [he] at hr
  have hrange : Set.range B = Set.range
      (L ∘L toEuclideanCLM (𝕜 := ℝ) C ∘L L.adjoint) :=
    congrArg (fun S : Submodule ℝ (EuclideanSpace ℝ κ) =>
      (S : Set (EuclideanSpace ℝ κ))) hr.symm
  letI := stdGaussian_openPos (ι := ι)
  rw [multivariateGaussian, Measure.map_map (by fun_prop) (by fun_prop)]
  have hf : L ∘ (fun x => m + toEuclideanCLM (𝕜 := ℝ) (CFC.sqrt C) x) =
      (fun x => L m + B x) := by ext x; simp [B, A]
  rw [hf, support_map_of_closed_range _ _ (by fun_prop) (affine_range_closed _ B)]
  have hleft : Set.range (fun x => L m + B x) = (fun z => L m + z) '' Set.range B := by
    exact (Set.range_comp _ _).symm
  rw [hleft, hrange]
  exact Set.range_comp _ _

end R9Gaussian

#print axioms R9Gaussian.support_multivariateGaussian
#print axioms R9Gaussian.support_zero_covariance
#print axioms R9Gaussian.mem_support_iff
#print axioms R9Gaussian.measure_outside_affine_support
#print axioms R9Gaussian.zero_covariance_law
#print axioms R9Gaussian.support_gaussian_of_moments
#print axioms R9Gaussian.support_map_gaussian
