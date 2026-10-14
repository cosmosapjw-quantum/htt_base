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

private def chartInverseDiagonal (ν F r θ : ℝ) (a : Fin 4) : ℝ :=
  if a = 0 then -(Real.exp (2 * ν))⁻¹ else
  if a = 1 then F else
  if a = 2 then (r ^ 2)⁻¹ else (r ^ 2 * Real.sin θ ^ 2)⁻¹

private theorem chartContravariant_diagonal (ν F r θ : ℝ) :
    chartContravariant ν F r θ =
      Matrix.diagonal (chartInverseDiagonal ν F r θ) := by
  ext a b
  fin_cases a <;> fin_cases b <;>
    simp [chartContravariant, CAS06Adopted.chartInverse,
      chartInverseDiagonal, Matrix.diagonal_apply]

theorem chartContravariant_det_neg (ν F r θ : ℝ)
    (hF : 0 < F) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    Matrix.det (chartContravariant ν F r θ) < 0 := by
  rw [chartContravariant_diagonal, Matrix.det_diagonal, Fin.prod_univ_four]
  simp only [chartInverseDiagonal, show (0 : Fin 4) ≠ 1 by decide,
    show (0 : Fin 4) ≠ 2 by decide,
    show (0 : Fin 4) ≠ 3 by decide,
    show (1 : Fin 4) ≠ 0 by decide,
    show (1 : Fin 4) ≠ 2 by decide,
    show (1 : Fin 4) ≠ 3 by decide,
    show (2 : Fin 4) ≠ 0 by decide,
    show (2 : Fin 4) ≠ 1 by decide,
    show (2 : Fin 4) ≠ 3 by decide,
    show (3 : Fin 4) ≠ 0 by decide,
    show (3 : Fin 4) ≠ 1 by decide,
    show (3 : Fin 4) ≠ 2 by decide,
    ↓reduceIte]
  have hr2 : 0 < r ^ 2 := sq_pos_of_ne_zero hr
  have hs2 : 0 < Real.sin θ ^ 2 := sq_pos_of_ne_zero hs
  have hden : 0 < r ^ 2 * Real.sin θ ^ 2 := mul_pos hr2 hs2
  have hE : 0 < (Real.exp (2 * ν))⁻¹ := inv_pos.mpr (Real.exp_pos _)
  have hprod : 0 < (Real.exp (2 * ν))⁻¹ * F * (r ^ 2)⁻¹ *
      (r ^ 2 * Real.sin θ ^ 2)⁻¹ := by positivity
  nlinarith

def volumeDensity (G : Mat4) : ℝ := Real.sqrt (-(Matrix.det G)⁻¹)

theorem volumeDensity_hasDerivAt
    (G g H : Mat4) (hGg : G * g = 1) (hD : Matrix.det G < 0) :
    HasDerivAt (fun t : ℝ => volumeDensity (G + t • H))
      (-volumeDensity G * Matrix.trace (g * H) / 2) 0 := by
  let d := Matrix.det G
  let k := Matrix.trace (g * H)
  have hd0 : d ≠ 0 := ne_of_lt hD
  have hx : 0 < -d⁻¹ := neg_pos.mpr (inv_lt_zero.mpr hD)
  have hw : 0 < volumeDensity G := Real.sqrt_pos.2 hx
  have hsq : volumeDensity G ^ 2 = -d⁻¹ := Real.sq_sqrt hx.le
  have hrel : d * volumeDensity G ^ 2 = -1 := by
    rw [hsq]
    field_simp [hd0]
  have hdet := det_inverse_metric_variation G g H hGg
  have hd0' : Matrix.det (G + (0 : ℝ) • H) ≠ 0 := by simpa using hd0
  have hx' : 0 < (-(fun t : ℝ => Matrix.det (G + t • H))⁻¹) 0 := by
    simpa using hx
  have hraw := ((hdet.inv hd0').neg).sqrt (ne_of_gt hx')
  simp only [Pi.neg_apply, Pi.inv_apply, zero_smul, add_zero] at hraw
  change HasDerivAt (fun t : ℝ => volumeDensity (G + t • H))
    ((-(-(d * k) / d ^ 2)) / (2 * volumeDensity G)) 0 at hraw
  have hcoeff : (-(-(d * k) / d ^ 2)) / (2 * volumeDensity G) =
      -volumeDensity G * k / 2 := by
    field_simp [hd0, hw.ne']
    nlinarith [congrArg (fun x : ℝ => x * k) hrel]
  rw [hcoeff] at hraw
  exact hraw

def kinetic (G : Mat4) (ψ : Fin 4 → ℝ) : ℝ :=
  -(∑ a : Fin 4, ∑ b : Fin 4, G a b * ψ a * ψ b) / 2

theorem kinetic_affine (G H : Mat4) (ψ : Fin 4 → ℝ) (t : ℝ) :
    kinetic (G + t • H) ψ = kinetic G ψ + t * kinetic H ψ := by
  unfold kinetic
  have hterm (a b : Fin 4) :
      (G + t • H) a b * ψ a * ψ b =
        G a b * ψ a * ψ b + t * (H a b * ψ a * ψ b) := by
    simp [Matrix.add_apply, Matrix.smul_apply]
    ring
  simp_rw [hterm, Finset.sum_add_distrib]
  simp only [← Finset.mul_sum]
  ring

theorem kinetic_hasDerivAt (G H : Mat4) (ψ : Fin 4 → ℝ) :
    HasDerivAt (fun t : ℝ => kinetic (G + t • H) ψ) (kinetic H ψ) 0 := by
  have hfun : (fun t : ℝ => kinetic (G + t • H) ψ) =
      (fun t : ℝ => kinetic G ψ + t * kinetic H ψ) := by
    funext t
    exact kinetic_affine G H ψ t
  rw [hfun]
  convert (hasDerivAt_const (0 : ℝ) (kinetic G ψ)).add
    ((hasDerivAt_id (0 : ℝ)).mul_const (kinetic H ψ)) using 1 <;>
    first | rfl | (funext t; rfl) | simp

def actionPressure (Pstar s x : ℝ) : ℝ := Pstar * x ^ s
def actionFirst (Pstar s x : ℝ) : ℝ := Pstar * s * x ^ (s - 1)

theorem actionPressure_hasDerivAt (Pstar s x : ℝ) (hx : 0 < x) :
    HasDerivAt (actionPressure Pstar s) (actionFirst Pstar s x) x := by
  change HasDerivAt (fun y : ℝ => Pstar * y ^ s)
    (Pstar * s * x ^ (s - 1)) x
  simpa only [mul_assoc] using
    (Real.hasDerivAt_rpow_const (p := s) (Or.inl hx.ne')).const_mul Pstar

def actionDensity (Pstar s : ℝ) (G : Mat4) (ψ : Fin 4 → ℝ) : ℝ :=
  volumeDensity G * actionPressure Pstar s (kinetic G ψ)

theorem actionDensity_metric_hasDerivAt
    (Pstar s : ℝ) (G g H : Mat4) (ψ : Fin 4 → ℝ)
    (hGg : G * g = 1) (hD : Matrix.det G < 0)
    (hX : 0 < kinetic G ψ) :
    HasDerivAt
      (fun t : ℝ => actionDensity Pstar s (G + t • H) ψ)
      ((-volumeDensity G * Matrix.trace (g * H) / 2) *
          actionPressure Pstar s (kinetic G ψ) +
        volumeDensity G *
          (actionFirst Pstar s (kinetic G ψ) * kinetic H ψ)) 0 := by
  have hV := volumeDensity_hasDerivAt G g H hGg hD
  have hK := kinetic_hasDerivAt G H ψ
  have hP := (actionPressure_hasDerivAt Pstar s (kinetic G ψ) hX).comp 0 hK
  have hA := hV.mul hP
  convert hA using 1 <;> first | rfl | simp | ring

#print axioms det_one_add_hasDerivAt
#print axioms det_inverse_metric_variation
#print axioms chartInverse_matrix_mul
#print axioms chart_det_variation
#print axioms chartContravariant_det_neg
#print axioms volumeDensity_hasDerivAt
#print axioms kinetic_affine
#print axioms kinetic_hasDerivAt
#print axioms actionPressure_hasDerivAt
#print axioms actionDensity_metric_hasDerivAt

end
end CAS06Action
