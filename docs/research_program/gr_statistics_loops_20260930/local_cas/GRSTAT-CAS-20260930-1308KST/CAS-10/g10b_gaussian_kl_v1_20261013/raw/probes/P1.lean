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

end Generic

end G10BGaussianKL
