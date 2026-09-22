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
open scoped NNReal ENNReal

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
    simpa [he] using hp
  · rintro ⟨x, rfl⟩ U hx hU
    rw [Measure.map_apply hf.measurable hU.measurableSet]
    exact (hU.preimage hf).measure_pos P ⟨x, hx⟩

theorem stdGaussian_openPos {ι : Type*} [Fintype ι] :
    (stdGaussian (EuclideanSpace ℝ ι)).IsOpenPosMeasure := by
  letI : (gaussianReal 0 1).IsOpenPosMeasure :=
    (gaussianReal_absolutelyContinuous' 0 (by norm_num : (1 : ℝ≥0) ≠ 0)).isOpenPosMeasure
  rw [← map_pi_eq_stdGaussian]
  exact (PiLp.continuous_toLp 2 (fun _ : ι => ℝ)).isOpenPosMeasure_map
    (Measure.pi (fun _ : ι => gaussianReal 0 1)) (WithLp.toLp_surjective 2)

/-- Finite-dimensional affine ranges are closed even when the map is singular. -/
theorem affine_range_closed {ι : Type*} [Fintype ι]
    (m : EuclideanSpace ℝ ι)
    (A : EuclideanSpace ℝ ι →L[ℝ] EuclideanSpace ℝ ι) :
    IsClosed (Set.range (fun x => m + A x)) := by
  have he : Set.range (fun x => m + A x) =
      (Homeomorph.addLeft m) '' (LinearMap.range A.toLinearMap : Set _) := by
    ext y
    simp only [Set.mem_range, Set.mem_image, LinearMap.mem_range,
      Homeomorph.addLeft_apply, ContinuousLinearMap.coe_coe]
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
  exact congrArg (fun S : Submodule ℝ (EuclideanSpace ℝ ι) => (S : Set _)) hr.symm

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
  rw [support_multivariateGaussian m 0 (by simp)]
  simp

end R9Gaussian

#print axioms R9Gaussian.support_multivariateGaussian
#print axioms R9Gaussian.support_zero_covariance
