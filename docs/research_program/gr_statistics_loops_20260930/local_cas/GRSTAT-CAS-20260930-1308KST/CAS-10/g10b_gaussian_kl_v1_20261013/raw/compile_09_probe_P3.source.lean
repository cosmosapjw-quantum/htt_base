import Mathlib

namespace G10BGaussianKL

open MeasureTheory ProbabilityTheory InformationTheory Matrix
open scoped ENNReal NNReal

section Generic

variable {J : Type*} [Fintype J] [DecidableEq J] (d : J → ℕ)

abbrev Idx := Σ j : J, Fin (d j)

noncomputable def coordVar (σ : J → ℝ) (i : Idx d) : ℝ≥0 := ⟨σ i.1 ^ 2, sq_nonneg _⟩

noncomputable def coordLaw {ι : Type*} [Fintype ι] (μ : ι → ℝ) (w : ι → ℝ≥0) :
    Measure (ι → ℝ) :=
  Measure.pi fun i => gaussianReal (μ i) (w i)

noncomputable def obsLaw (μ : Idx d → ℝ) (σ : J → ℝ) : Measure (Idx d → ℝ) :=
  coordLaw μ (coordVar d σ)

def powers (x : Idx d → ℝ) : J → ℝ := fun j => ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2

def blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) (x : Idx d → ℝ) : Idx d → ℝ :=
  fun i => (R i.1 *ᵥ fun k => x ⟨i.1, k⟩) i.2

instance {ι : Type*} [Fintype ι] (μ : ι → ℝ) (w : ι → ℝ≥0) :
    IsProbabilityMeasure (coordLaw μ w) := by
  unfold coordLaw; infer_instance

instance (μ : Idx d → ℝ) (σ : J → ℝ) : IsProbabilityMeasure (obsLaw d μ σ) := by
  unfold obsLaw; infer_instance

theorem coordVar_coe (σ : J → ℝ) (i : Idx d) : (coordVar d σ i : ℝ) = σ i.1 ^ 2 := rfl

theorem measurable_toLp : Measurable (WithLp.toLp 2 : (Idx d → ℝ) → EuclideanSpace ℝ (Idx d)) :=
  (MeasurableEquiv.toLp 2 (Idx d → ℝ)).measurable

theorem measurable_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) :
    Measurable (blockMap d R) := by
  unfold blockMap
  apply measurable_pi_lambda
  intro i
  simp only [Matrix.mulVec, dotProduct]
  fun_prop

theorem measurable_powers : Measurable (powers d) := by
  unfold powers
  fun_prop

/-- Adjoint identity for the blockwise map. -/
theorem sum_blockMap_mul (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ) (x t : Idx d → ℝ) :
    ∑ i, blockMap d R x i * t i = ∑ i, x i * blockMap d (fun j => (R j)ᵀ) t i := by
  simp only [blockMap, Fintype.sum_sigma]
  refine Finset.sum_congr rfl fun j _ => ?_
  have h := (Matrix.dotProduct_mulVec (fun k => x ⟨j, k⟩) (R j)ᵀ (fun k => t ⟨j, k⟩))
  rw [Matrix.vecMul_transpose] at h
  simpa [dotProduct] using h.symm

theorem sum_sq_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (x : Idx d → ℝ) (j : J) :
    ∑ k : Fin (d j), blockMap d R x ⟨j, k⟩ ^ 2 = ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2 := by
  set y : Fin (d j) → ℝ := fun k => x ⟨j, k⟩
  have h1 : ∑ k : Fin (d j), blockMap d R x ⟨j, k⟩ ^ 2 = (R j *ᵥ y) ⬝ᵥ (R j *ᵥ y) := by
    simp [blockMap, dotProduct, sq, y]
  have h2 : ∑ k : Fin (d j), x ⟨j, k⟩ ^ 2 = y ⬝ᵥ y := by simp [dotProduct, sq, y]
  rw [h1, h2, Matrix.dotProduct_mulVec, ← Matrix.vecMul_transpose, Matrix.vecMul_vecMul, hR j,
    Matrix.vecMul_one]


theorem obsLaw_map_blockMap (R : (j : J) → Matrix (Fin (d j)) (Fin (d j)) ℝ)
    (hR : ∀ j, (R j)ᵀ * R j = 1) (μ : Idx d → ℝ) (σ : J → ℝ) :
    (obsLaw d μ σ).map (blockMap d R) = obsLaw d (blockMap d R μ) σ := by
  have hRt : ∀ j, (R j)ᵀᵀ * (R j)ᵀ = 1 := fun j => by
    rw [Matrix.transpose_transpose]; exact Matrix.mul_eq_one_comm.mp (hR j)
  haveI : IsProbabilityMeasure ((obsLaw d μ σ).map (blockMap d R)) :=
    Measure.isProbabilityMeasure_map (measurable_blockMap d R).aemeasurable
  have hin : ∀ (y : Idx d → ℝ) (u : EuclideanSpace ℝ (Idx d)),
      inner ℝ (WithLp.toLp 2 y) u = ∑ i, y i * u i := by
    intro y u
    simp [PiLp.inner_apply, mul_comm]
  unfold obsLaw coordLaw
  refine (charFun_eq_pi_iff).1 (fun t => ?_)
  set s : Idx d → ℝ := blockMap d (fun j => (R j)ᵀ) (fun i => t i) with hs
  have h1 : charFun (((Measure.pi fun i => gaussianReal (μ i) (coordVar d σ i)).map
        (blockMap d R)).map (WithLp.toLp 2)) t =
      charFun ((Measure.pi fun i => gaussianReal (μ i) (coordVar d σ i)).map (WithLp.toLp 2))
        (WithLp.toLp 2 s) := by
    rw [Measure.map_map (measurable_toLp d) (measurable_blockMap d R)]
    simp only [charFun_apply]
    rw [integral_map ((measurable_toLp d).comp (measurable_blockMap d R)).aemeasurable
      (by fun_prop), integral_map (measurable_toLp d).aemeasurable (by fun_prop)]
    congr 1
    funext x
    simp only [Function.comp_apply, hin]
    rw [sum_blockMap_mul d R x (fun i => t i)]
  rw [h1, charFun_pi]
  simp only [charFun_gaussianReal, ← Complex.exp_sum]
  congr 1
  have hlin : ∑ i, s i * μ i = ∑ i, t i * blockMap d R μ i := by
    calc ∑ i, s i * μ i = ∑ i, μ i * s i := Finset.sum_congr rfl fun i _ => mul_comm _ _
      _ = ∑ i, blockMap d R μ i * t i := (sum_blockMap_mul d R μ (fun i => t i)).symm
      _ = ∑ i, t i * blockMap d R μ i := Finset.sum_congr rfl fun i _ => mul_comm _ _
  have hquad : ∑ i, (coordVar d σ i : ℝ) * s i ^ 2 = ∑ i, (coordVar d σ i : ℝ) * t i ^ 2 := by
    simp only [coordVar_coe, Fintype.sum_sigma]
    refine Finset.sum_congr rfl fun j _ => ?_
    rw [← Finset.mul_sum, ← Finset.mul_sum]
    congr 1
    exact sum_sq_blockMap d (fun j => (R j)ᵀ) hRt (fun i => t i) j
  have e1 : ∑ i, ((↑(s i) : ℂ) * ↑(μ i) * Complex.I - ↑(coordVar d σ i : ℝ) * ↑(s i) ^ 2 / 2) =
      ↑(∑ i, s i * μ i) * Complex.I - ↑(∑ i, (coordVar d σ i : ℝ) * s i ^ 2) / 2 := by
    push_cast
    rw [Finset.sum_sub_distrib, Finset.sum_mul, Finset.sum_div]
  have e2 : ∑ i, ((↑(t i) : ℂ) * ↑(blockMap d R μ i) * Complex.I -
        ↑(coordVar d σ i : ℝ) * ↑(t i) ^ 2 / 2) =
      ↑(∑ i, t i * blockMap d R μ i) * Complex.I -
        ↑(∑ i, (coordVar d σ i : ℝ) * t i ^ 2) / 2 := by
    push_cast
    rw [Finset.sum_sub_distrib, Finset.sum_mul, Finset.sum_div]
  convert e1.trans ?_ using 1
  · rw [e2, hlin, hquad]

end Generic

end G10BGaussianKL
