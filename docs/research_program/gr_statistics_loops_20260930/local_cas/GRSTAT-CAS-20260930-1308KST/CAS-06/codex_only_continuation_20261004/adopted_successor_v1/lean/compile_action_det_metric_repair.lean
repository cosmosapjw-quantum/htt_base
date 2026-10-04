import Mathlib
import CAS06Foundation

/-! Variations of the admitted fixed action. The determinant lemma is obtained
from mathlib's polynomial expansion and does not assume a stress tensor. -/

namespace CAS06Action
noncomputable section
open Polynomial Matrix

abbrev Mat4 := Matrix (Fin 4) (Fin 4) ℝ

private def detPolynomial (H : Mat4) : Polynomial ℝ :=
  Matrix.det (1 + (Polynomial.X : Polynomial ℝ) • H.map Polynomial.C)

private theorem detPolynomial_eval (H : Mat4) (t : ℝ) :
    (detPolynomial H).eval t = Matrix.det (1 + t • H) := by
  unfold detPolynomial
  rw [← coe_evalRingHom, RingHom.map_det]
  congr 1
  ext i j
  simp [Matrix.map_apply, Matrix.add_apply, Matrix.smul_apply,
    Matrix.one_apply]
  split_ifs <;> simp [add_comm, mul_comm]

theorem det_one_add_hasDerivAt (H : Mat4) :
    HasDerivAt (fun t : ℝ => Matrix.det (1 + t • H)) (Matrix.trace H) 0 := by
  have h := (detPolynomial H).hasDerivAt 0
  have hder : (detPolynomial H).derivative.eval 0 = Matrix.trace H := by
    exact Matrix.derivative_det_one_add_X_smul H
  have hEq : (fun t : ℝ => Matrix.det (1 + t • H)) =
      (fun t : ℝ => (detPolynomial H).eval t) := by
    funext t
    exact (detPolynomial_eval H t).symm
  rw [hEq, ← hder]
  exact h

theorem det_inverse_metric_variation
    (G g H : Mat4) (hGg : G * g = 1) :
    HasDerivAt (fun t : ℝ => Matrix.det (G + t • H))
      (Matrix.det G * Matrix.trace (g * H)) 0 := by
  have hmatrix (t : ℝ) :
      G + t • H = G * (1 + t • (g * H)) := by
    have h : G * (g * H) = H := by
      rw [← Matrix.mul_assoc, hGg, Matrix.one_mul]
    simp [Matrix.mul_add, h]
  have hfun : (fun t : ℝ => Matrix.det (G + t • H)) =
      (fun t : ℝ => Matrix.det G * Matrix.det (1 + t • (g * H))) := by
    funext t
    rw [hmatrix, Matrix.det_mul]
  rw [hfun]
  exact (det_one_add_hasDerivAt (g * H)).const_mul (Matrix.det G)

def chartContravariant (ν F r θ : ℝ) : Mat4 :=
  CAS06Adopted.chartInverse ν F r θ

def chartCovariant (ν F r θ : ℝ) : Mat4 :=
  CAS06Adopted.chartMetric ν F r θ

theorem chartInverse_matrix_mul (ν F r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartContravariant ν F r θ * chartCovariant ν F r θ = 1 := by
  ext a b
  simpa [chartContravariant, chartCovariant, Matrix.mul_apply,
    Matrix.one_apply] using
    CAS06Adopted.chartInverse_left_identity ν F r θ hF hr hs a b

theorem chart_det_variation (ν F r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (H : Mat4) :
    HasDerivAt
      (fun t : ℝ => Matrix.det (chartContravariant ν F r θ + t • H))
      (Matrix.det (chartContravariant ν F r θ) *
        Matrix.trace (chartCovariant ν F r θ * H)) 0 := by
  exact det_inverse_metric_variation _ _ _
    (chartInverse_matrix_mul ν F r θ hF hr hs)

#print axioms det_one_add_hasDerivAt
#print axioms det_inverse_metric_variation
#print axioms chartInverse_matrix_mul
#print axioms chart_det_variation

end
end CAS06Action
