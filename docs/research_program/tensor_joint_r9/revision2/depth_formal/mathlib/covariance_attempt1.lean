import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Probability.Moments.Covariance
import Mathlib.MeasureTheory.Integral.Bochner.Basic

/- D1: actual real finite-dimensional covariance, arbitrary linear maps and PSD.
   The index types need not be equal; no diagonal covariance or independence
   premise is imposed. This file does not assert D2/D4 Gaussian results. -/

open MeasureTheory ProbabilityTheory
open scoped BigOperators Matrix

namespace R9Depth

variable {Ω n m : Type*} [MeasurableSpace Ω]
variable [Fintype n] [Fintype m]
variable {μ : Measure Ω} [IsProbabilityMeasure μ]

def meanVector (Y : Ω → n → ℝ) (μ : Measure Ω) : n → ℝ :=
  fun i => ∫ ω, Y ω i ∂μ

def covarianceMatrix (Y : Ω → n → ℝ) (μ : Measure Ω) : Matrix n n ℝ :=
  fun i j => covariance (fun ω => Y ω i) (fun ω => Y ω j) μ

theorem mean_linear_map (Y : Ω → n → ℝ) (H : Matrix m n ℝ)
    (hY : ∀ i, MemLp (fun ω => Y ω i) 2 μ) :
    meanVector (fun ω => H *ᵥ Y ω) μ = H *ᵥ meanVector Y μ := by
  classical
  funext i
  simp only [meanVector, Matrix.mulVec, dotProduct]
  rw [integral_finsetSum]
  · simp only [integral_const_mul]
  · intro j _
    exact ((hY j).integrable (by norm_num)).const_mul _

theorem covariance_linear_map (Y : Ω → n → ℝ) (H : Matrix m n ℝ)
    (hY : ∀ i, MemLp (fun ω => Y ω i) 2 μ) :
    covarianceMatrix (fun ω => H *ᵥ Y ω) μ =
      H * covarianceMatrix Y μ * H.transpose := by
  classical
  ext i j
  change covariance (fun ω => ∑ a, H i a * Y ω a)
    (fun ω => ∑ b, H j b * Y ω b) μ = _
  rw [covariance_fun_sum_fun_sum
    (fun a => (hY a).const_mul (H i a))
    (fun b => (hY b).const_mul (H j b))]
  simp only [covariance_const_mul_left, covariance_const_mul_right,
    Matrix.mul_apply, Matrix.transpose_apply, covarianceMatrix]
  simp_rw [Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro a _
  apply Finset.sum_congr rfl
  intro b _
  ring

theorem covariance_pullback_psd (C : Matrix n n ℝ) (H : Matrix m n ℝ)
    (hC : C.PosSemidef) : (H * C * H.transpose).PosSemidef := by
  simpa only [Matrix.conjTranspose_eq_transpose_of_trivial] using
    hC.mul_mul_conjTranspose_same H

end R9Depth

#print axioms R9Depth.mean_linear_map
#print axioms R9Depth.covariance_linear_map
#print axioms R9Depth.covariance_pullback_psd
