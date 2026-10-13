import Mathlib
import CAS06Foundation
import CAS06ScalarAccepted

/-! Variations of the admitted fixed action. The determinant lemma is obtained
from mathlib's polynomial expansion and does not assume a stress tensor. -/

namespace CAS06Action
noncomputable section
open Polynomial Matrix
open scoped Topology

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

theorem actionPressure_eq_scalar (Pstar s x : ℝ) :
    actionPressure Pstar s x = CAS06Scalar.pressure Pstar s x := rfl

theorem actionFirst_eq_scalar (Pstar s x : ℝ) :
    actionFirst Pstar s x = CAS06Scalar.first Pstar s x := rfl

def actionEnergy (Pstar s x : ℝ) : ℝ :=
  2 * x * actionFirst Pstar s x - actionPressure Pstar s x

theorem actionEnergy_eq_scalar (Pstar s x : ℝ) :
    actionEnergy Pstar s x = CAS06Scalar.energy Pstar s x := rfl

theorem action_energy_pressure_identity (Pstar s x : ℝ) (hx : 0 < x) :
    actionEnergy Pstar s x = (2 * s - 1) * actionPressure Pstar s x := by
  simpa [actionEnergy_eq_scalar, actionPressure_eq_scalar] using
    CAS06Scalar.energy_identity Pstar s x hx

theorem action_barotropic_identity (Pstar α x : ℝ)
    (hx : 0 < x) (hα : 0 < α) :
    actionPressure Pstar (CAS06Scalar.exponent α) x =
      α * actionEnergy Pstar (CAS06Scalar.exponent α) x := by
  rw [action_energy_pressure_identity Pstar (CAS06Scalar.exponent α) x hx]
  have hα0 : α ≠ 0 := ne_of_gt hα
  have heq : α * (2 * CAS06Scalar.exponent α - 1) = 1 := by
    unfold CAS06Scalar.exponent
    field_simp
    ring
  rw [← mul_assoc, heq, one_mul]

theorem action_sound_ratio (Pstar α x : ℝ)
    (hP : 0 < Pstar) (hx : 0 < x) (hα : 0 < α) (hα1 : α < 1) :
    0 < deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) x +
      2 * x * deriv (deriv (CAS06Scalar.pressure Pstar
        (CAS06Scalar.exponent α))) x ∧
    deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) x /
      (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)) x +
        2 * x * deriv (deriv (CAS06Scalar.pressure Pstar
          (CAS06Scalar.exponent α))) x) = α := by
  exact ⟨CAS06Scalar.deriv_denominator_pos Pstar α x hP hx hα hα1,
    CAS06Scalar.deriv_ratio_identity Pstar α x hP hx hα hα1⟩

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
  have hK0 : kinetic (G + (0 : ℝ) • H) ψ = kinetic G ψ := by simp
  have hP0 := actionPressure_hasDerivAt Pstar s (kinetic G ψ) hX
  rw [← hK0] at hP0
  have hP := hP0.comp 0 hK
  have hA := hV.mul hP
  convert hA using 1 <;> first | rfl | simp | ring

theorem trace_contract_symmetric (g H : Mat4)
    (hH : ∀ a b : Fin 4, H a b = H b a) :
    Matrix.trace (g * H) =
      ∑ a : Fin 4, ∑ b : Fin 4, g a b * H a b := by
  simp only [Matrix.trace, Matrix.diag_apply, Matrix.mul_apply]
  apply Finset.sum_congr rfl
  intro a _
  apply Finset.sum_congr rfl
  intro b _
  rw [hH b a]

def actionStress (Pstar s : ℝ) (G g : Mat4) (ψ : Fin 4 → ℝ) : Mat4 :=
  fun a b =>
    actionFirst Pstar s (kinetic G ψ) * ψ a * ψ b +
      actionPressure Pstar s (kinetic G ψ) * g a b

theorem actionStress_contraction
    (Pstar s : ℝ) (G g H : Mat4) (ψ : Fin 4 → ℝ) :
    (∑ a : Fin 4, ∑ b : Fin 4,
      actionStress Pstar s G g ψ a b * H a b) =
      actionFirst Pstar s (kinetic G ψ) *
        (∑ a : Fin 4, ∑ b : Fin 4, H a b * ψ a * ψ b) +
      actionPressure Pstar s (kinetic G ψ) *
        (∑ a : Fin 4, ∑ b : Fin 4, g a b * H a b) := by
  unfold actionStress
  simp_rw [add_mul, Finset.sum_add_distrib]
  simp only [Finset.mul_sum]
  have hterm (a b : Fin 4) :
      actionFirst Pstar s (kinetic G ψ) * ψ a * ψ b * H a b =
        actionFirst Pstar s (kinetic G ψ) * H a b * ψ a * ψ b := by ring
  simp_rw [hterm]
  simp only [mul_assoc]

theorem actionDensity_metric_stress_variation
    (Pstar s : ℝ) (G g H : Mat4) (ψ : Fin 4 → ℝ)
    (hGg : G * g = 1) (hD : Matrix.det G < 0)
    (hX : 0 < kinetic G ψ)
    (hH : ∀ a b : Fin 4, H a b = H b a) :
    HasDerivAt
      (fun t : ℝ => actionDensity Pstar s (G + t • H) ψ)
      (-(volumeDensity G / 2) *
        ∑ a : Fin 4, ∑ b : Fin 4,
          actionStress Pstar s G g ψ a b * H a b) 0 := by
  have hA := actionDensity_metric_hasDerivAt Pstar s G g H ψ hGg hD hX
  have hT := trace_contract_symmetric g H hH
  have hcoeff :
      (-volumeDensity G * Matrix.trace (g * H) / 2) *
          actionPressure Pstar s (kinetic G ψ) +
        volumeDensity G *
          (actionFirst Pstar s (kinetic G ψ) * kinetic H ψ) =
        -(volumeDensity G / 2) *
          ∑ a : Fin 4, ∑ b : Fin 4,
            actionStress Pstar s G g ψ a b * H a b := by
    rw [hT, actionStress_contraction]
    rw [show kinetic H ψ =
        -(∑ a : Fin 4, ∑ b : Fin 4, H a b * ψ a * ψ b) / 2 by rfl]
    ring
  rw [hcoeff] at hA
  exact hA

def kineticGradientLinear (G : Mat4) (ψ η : Fin 4 → ℝ) : ℝ :=
  -(∑ a : Fin 4, ∑ b : Fin 4,
      G a b * (η a * ψ b + ψ a * η b)) / 2

theorem kinetic_gradient_polynomial
    (G : Mat4) (ψ η : Fin 4 → ℝ) (t : ℝ) :
    kinetic G (fun a => ψ a + t * η a) =
      kinetic G ψ + t * kineticGradientLinear G ψ η +
        t ^ 2 * kinetic G η := by
  simp [kinetic, kineticGradientLinear, Fin.sum_univ_four]
  ring

theorem kinetic_gradient_hasDerivAt
    (G : Mat4) (ψ η : Fin 4 → ℝ) :
    HasDerivAt (fun t : ℝ => kinetic G (fun a => ψ a + t * η a))
      (kineticGradientLinear G ψ η) 0 := by
  have hfun : (fun t : ℝ => kinetic G (fun a => ψ a + t * η a)) =
      (fun t : ℝ => kinetic G ψ + t * kineticGradientLinear G ψ η +
        t ^ 2 * kinetic G η) := by
    funext t
    exact kinetic_gradient_polynomial G ψ η t
  rw [hfun]
  have hsq : HasDerivAt (fun t : ℝ => t ^ 2) 0 0 := by
    convert (hasDerivAt_id (0 : ℝ)).pow 2 using 1 <;>
      first | rfl | (funext t; rfl) | simp
  have hlin : HasDerivAt (fun t : ℝ =>
      kinetic G ψ + t * kineticGradientLinear G ψ η)
      (kineticGradientLinear G ψ η) 0 := by
    convert (hasDerivAt_const (0 : ℝ) (kinetic G ψ)).add
      ((hasDerivAt_id (0 : ℝ)).mul_const (kineticGradientLinear G ψ η))
      using 1 <;> first | rfl | (funext t; rfl) | simp
  convert hlin.add (hsq.mul_const (kinetic G η)) using 1 <;>
    first | rfl | (funext t; rfl) | simp

theorem gradient_cross_symmetric
    (G : Mat4) (ψ η : Fin 4 → ℝ)
    (hG : ∀ a b : Fin 4, G a b = G b a) :
    (∑ a : Fin 4, ∑ b : Fin 4, G a b * ψ a * η b) =
      ∑ a : Fin 4, ∑ b : Fin 4, G a b * η a * ψ b := by
  calc
    _ = ∑ a : Fin 4, ∑ b : Fin 4, G b a * ψ b * η a := by
      rw [Finset.sum_comm]
    _ = _ := by
      apply Finset.sum_congr rfl
      intro a _
      apply Finset.sum_congr rfl
      intro b _
      rw [hG b a]
      ring

def actionCurrent (Pstar s : ℝ) (G : Mat4) (ψ : Fin 4 → ℝ)
    (a : Fin 4) : ℝ :=
  actionFirst Pstar s (kinetic G ψ) *
    ∑ b : Fin 4, G a b * ψ b

theorem kinetic_gradient_current
    (G : Mat4) (ψ η : Fin 4 → ℝ)
    (hG : ∀ a b : Fin 4, G a b = G b a) :
    kineticGradientLinear G ψ η =
      -(∑ a : Fin 4, (∑ b : Fin 4, G a b * ψ b) * η a) := by
  unfold kineticGradientLinear
  simp_rw [mul_add, Finset.sum_add_distrib]
  have hcross := gradient_cross_symmetric G ψ η hG
  have hcross' :
      (∑ a : Fin 4, ∑ b : Fin 4, G a b * (ψ a * η b)) =
        ∑ a : Fin 4, ∑ b : Fin 4, G a b * (η a * ψ b) := by
    simpa only [mul_assoc] using hcross
  rw [hcross']
  have hterm (a b : Fin 4) :
      G a b * (η a * ψ b) = (G a b * ψ b) * η a := by ring
  simp_rw [hterm, ← Finset.sum_mul]
  ring

theorem actionCurrent_contraction
    (Pstar s : ℝ) (G : Mat4) (ψ η : Fin 4 → ℝ) :
    (∑ a : Fin 4, actionCurrent Pstar s G ψ a * η a) =
      actionFirst Pstar s (kinetic G ψ) *
        ∑ a : Fin 4, (∑ b : Fin 4, G a b * ψ b) * η a := by
  unfold actionCurrent
  rw [Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro a _
  ring

theorem actionDensity_scalar_hasDerivAt
    (Pstar s : ℝ) (G : Mat4) (ψ η : Fin 4 → ℝ)
    (hX : 0 < kinetic G ψ)
    (hG : ∀ a b : Fin 4, G a b = G b a) :
    HasDerivAt
      (fun t : ℝ => actionDensity Pstar s G (fun a => ψ a + t * η a))
      (-volumeDensity G *
        ∑ a : Fin 4, actionCurrent Pstar s G ψ a * η a) 0 := by
  have hK := kinetic_gradient_hasDerivAt G ψ η
  have hK0 : kinetic G (fun a => ψ a + (0 : ℝ) * η a) =
      kinetic G ψ := by simp
  have hP0 := actionPressure_hasDerivAt Pstar s (kinetic G ψ) hX
  rw [← hK0] at hP0
  have hP := hP0.comp 0 hK
  have hA := hP.const_mul (volumeDensity G)
  have hcoeff :
      volumeDensity G *
        (actionFirst Pstar s (kinetic G ψ) *
          kineticGradientLinear G ψ η) =
        -volumeDensity G *
          ∑ a : Fin 4, actionCurrent Pstar s G ψ a * η a := by
    rw [kinetic_gradient_current G ψ η hG,
      actionCurrent_contraction]
    ring
  rw [← hcoeff]
  convert hA using 1 <;> first | rfl | simp | ring

def scalarGradient (q : ℝ) (a : Fin 4) : ℝ := if a = 0 then q else 0

theorem chartContravariant_symmetric (ν F r θ : ℝ) :
    ∀ a b : Fin 4,
      chartContravariant ν F r θ a b =
        chartContravariant ν F r θ b a := by
  intro a b
  fin_cases a <;> fin_cases b <;>
    simp [chartContravariant, CAS06Adopted.chartInverse]

theorem chart_scalar_kinetic (ν F r θ q : ℝ) :
    kinetic (chartContravariant ν F r θ) (scalarGradient q) =
      q ^ 2 / (2 * Real.exp (2 * ν)) := by
  simp [kinetic, scalarGradient, chartContravariant,
    CAS06Adopted.chartInverse, Fin.sum_univ_four]
  field_simp [Real.exp_ne_zero]

theorem chart_scalar_current_spatial_zero
    (Pstar s ν F r θ q : ℝ) (a : Fin 4) (ha : a ≠ 0) :
    actionCurrent Pstar s (chartContravariant ν F r θ)
      (scalarGradient q) a = 0 := by
  fin_cases a <;> simp_all [actionCurrent, scalarGradient,
    chartContravariant, CAS06Adopted.chartInverse, Fin.sum_univ_four]

def chartCurrentDensityOnLine (Pstar s q : ℝ) (ν F : ℝ → ℝ)
    (r θ : ℝ) (dir : Fin 4) (x : ℝ) : ℝ :=
  let rr := if dir = 1 then x else r
  let tt := if dir = 2 then x else θ
  volumeDensity (chartContravariant (ν rr) (F rr) rr tt) *
    actionCurrent Pstar s (chartContravariant (ν rr) (F rr) rr tt)
      (scalarGradient q) dir

theorem chart_scalar_current_density_line_deriv_zero
    (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ)
    (dir : Fin 4) (x : ℝ) :
    deriv (chartCurrentDensityOnLine Pstar s q ν F r θ dir) x = 0 := by
  by_cases h0 : dir = 0
  · subst dir
    have hc : chartCurrentDensityOnLine Pstar s q ν F r θ 0 =
        fun _ : ℝ => chartCurrentDensityOnLine Pstar s q ν F r θ 0 0 := by
      funext y
      simp [chartCurrentDensityOnLine]
    rw [hc]
    exact deriv_const _ _
  · have hz : chartCurrentDensityOnLine Pstar s q ν F r θ dir =
        fun _ : ℝ => 0 := by
      funext y
      simp [chartCurrentDensityOnLine,
        chart_scalar_current_spatial_zero Pstar s (ν _) (F _) _ _ q dir h0]
    rw [hz]
    exact deriv_const _ _

def chartScalarCurrentDivergence (Pstar s q : ℝ)
    (ν F : ℝ → ℝ) (r θ : ℝ) : ℝ :=
  (∑ dir : Fin 4,
    deriv (chartCurrentDensityOnLine Pstar s q ν F r θ dir)
      (if dir = 1 then r else if dir = 2 then θ else 0)) /
    volumeDensity (chartContravariant (ν r) (F r) r θ)

theorem chart_scalar_current_divergence_zero
    (Pstar s q : ℝ) (ν F : ℝ → ℝ) (r θ : ℝ) :
    chartScalarCurrentDivergence Pstar s q ν F r θ = 0 := by
  simp [chartScalarCurrentDivergence,
    chart_scalar_current_density_line_deriv_zero]

theorem chart_scalar_kinetic_matched (F r θ q : ℝ) :
    kinetic (chartContravariant 0 F r θ) (scalarGradient q) = q ^ 2 / 2 := by
  rw [chart_scalar_kinetic]
  norm_num

theorem matched_action_thermodynamics
    (Pstar α ε₀ p₀ q : ℝ)
    (hα : 0 < α) (hε : 0 < ε₀)
    (hp : p₀ = α * ε₀)
    (hN : actionPressure Pstar (CAS06Scalar.exponent α) (q ^ 2 / 2) = p₀)
    (hq : q ≠ 0) :
    actionEnergy Pstar (CAS06Scalar.exponent α) (q ^ 2 / 2) = ε₀ ∧
    actionPressure Pstar (CAS06Scalar.exponent α) (q ^ 2 / 2) = p₀ := by
  have hx : 0 < q ^ 2 / 2 := by positivity
  have hbar := action_barotropic_identity Pstar α (q ^ 2 / 2) hx hα
  constructor
  · rw [hN, hp] at hbar
    exact (mul_left_cancel₀ (ne_of_gt hα) hbar.symm)
  · exact hN

theorem matched_action_stress_coordinate
    (Pstar α ε₀ p₀ q F r θ : ℝ)
    (hα : 0 < α) (hε : 0 < ε₀)
    (hp : p₀ = α * ε₀)
    (hN : actionPressure Pstar (CAS06Scalar.exponent α) (q ^ 2 / 2) = p₀)
    (hq : q ≠ 0) :
    ∀ a b : Fin 4,
      actionStress Pstar (CAS06Scalar.exponent α)
        (chartContravariant 0 F r θ) (chartCovariant 0 F r θ)
        (scalarGradient q) a b =
      (if a = 0 then if b = 0 then ε₀ + p₀ else 0 else 0) +
        p₀ * chartCovariant 0 F r θ a b := by
  have htherm := matched_action_thermodynamics Pstar α ε₀ p₀ q
    hα hε hp hN hq
  have hfirst :
      actionFirst Pstar (CAS06Scalar.exponent α) (q ^ 2 / 2) * q ^ 2 =
        ε₀ + p₀ := by
    have he := htherm.1
    unfold actionEnergy at he
    nlinarith
  intro a b
  unfold actionStress
  rw [chart_scalar_kinetic_matched]
  rw [hN]
  fin_cases a <;> fin_cases b <;>
    simp [scalarGradient, chartCovariant,
      CAS06Adopted.chartMetric] <;> nlinarith [hfirst]

def actionRadialX (ν : ℝ → ℝ) (q r : ℝ) : ℝ :=
  (q ^ 2 / 2) * Real.exp (-2 * ν r)

theorem actionRadialX_eq_chart
    (ν F : ℝ → ℝ) (q r θ : ℝ) :
    actionRadialX ν q r =
      kinetic (chartContravariant (ν r) (F r) r θ) (scalarGradient q) := by
  rw [chart_scalar_kinetic]
  unfold actionRadialX
  rw [show -2 * ν r = -(2 * ν r) by ring, Real.exp_neg]
  ring

theorem actionRadialX_pos (ν : ℝ → ℝ) (q r : ℝ) (hq : q ≠ 0) :
    0 < actionRadialX ν q r := by
  unfold actionRadialX
  have hq2 : 0 < q ^ 2 := sq_pos_of_ne_zero hq
  positivity

theorem actionRadialX_hasDerivAt
    (ν : ℝ → ℝ) (q r : ℝ) (hν : DifferentiableAt ℝ ν r) :
    HasDerivAt (actionRadialX ν q)
      (-2 * actionRadialX ν q r * deriv ν r) r := by
  have hν' := hν.hasDerivAt
  have hneg : HasDerivAt (fun y : ℝ => -2 * ν y)
      (-2 * deriv ν r) r := hν'.const_mul (-2)
  have hE := hneg.exp
  have hX := hE.const_mul (q ^ 2 / 2)
  convert hX using 1 <;> first | rfl | (funext y; rfl) |
    (simp only [actionRadialX]; ring)

def actionRadialPressure (Pstar s : ℝ) (ν : ℝ → ℝ) (q r : ℝ) : ℝ :=
  actionPressure Pstar s (actionRadialX ν q r)

def actionRadialEnergy (Pstar s : ℝ) (ν : ℝ → ℝ) (q r : ℝ) : ℝ :=
  actionEnergy Pstar s (actionRadialX ν q r)

theorem actionRadialPressure_hasDerivAt
    (Pstar s q r : ℝ) (ν : ℝ → ℝ)
    (hq : q ≠ 0) (hν : DifferentiableAt ℝ ν r) :
    HasDerivAt (actionRadialPressure Pstar s ν q)
      (-(actionRadialEnergy Pstar s ν q r +
        actionRadialPressure Pstar s ν q r) * deriv ν r) r := by
  have hX := actionRadialX_hasDerivAt ν q r hν
  have hP := (actionPressure_hasDerivAt Pstar s
    (actionRadialX ν q r) (actionRadialX_pos ν q r hq)).comp r hX
  have hcoeff :
      actionFirst Pstar s (actionRadialX ν q r) *
          (-2 * actionRadialX ν q r * deriv ν r) =
        -(actionRadialEnergy Pstar s ν q r +
          actionRadialPressure Pstar s ν q r) * deriv ν r := by
    unfold actionRadialEnergy actionRadialPressure actionEnergy
    ring
  rw [hcoeff] at hP
  exact hP

theorem actionRadialPressure_conservation
    (Pstar s q r : ℝ) (ν : ℝ → ℝ)
    (hq : q ≠ 0) (hν : DifferentiableAt ℝ ν r) :
    deriv (actionRadialPressure Pstar s ν q) r =
      -(actionRadialEnergy Pstar s ν q r +
        actionRadialPressure Pstar s ν q r) * deriv ν r :=
  (actionRadialPressure_hasDerivAt Pstar s q r ν hq hν).deriv

theorem actionRadialEnergy_conservation
    (Pstar α q r : ℝ) (ν : ℝ → ℝ)
    (hα : 0 < α) (hq : q ≠ 0)
    (hν : DifferentiableAt ℝ ν r) :
    α * deriv (actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q) r =
      -(1 + α) *
        actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r * deriv ν r := by
  let s := CAS06Scalar.exponent α
  have hfun : (fun y : ℝ => α * actionRadialEnergy Pstar s ν q y) =
      actionRadialPressure Pstar s ν q := by
    funext y
    exact (action_barotropic_identity Pstar α (actionRadialX ν q y)
      (actionRadialX_pos ν q y hq) hα).symm
  have hder := congrArg (fun f : ℝ → ℝ => deriv f r) hfun
  have hPdiff : DifferentiableAt ℝ (actionRadialPressure Pstar s ν q) r :=
    (actionRadialPressure_hasDerivAt Pstar s q r ν hq hν).differentiableAt
  have hEfun : actionRadialEnergy Pstar s ν q =
      fun y => α⁻¹ * actionRadialPressure Pstar s ν q y := by
    funext y
    calc
      actionRadialEnergy Pstar s ν q y =
          α⁻¹ * (α * actionRadialEnergy Pstar s ν q y) := by
        field_simp [hα.ne']
      _ = α⁻¹ * actionRadialPressure Pstar s ν q y := by
        rw [congrFun hfun y]
  have hEdiff : DifferentiableAt ℝ (actionRadialEnergy Pstar s ν q) r := by
    rw [hEfun]
    exact hPdiff.const_mul _
  rw [deriv_const_mul] at hder
  all_goals try exact hEdiff
  have hval : actionRadialPressure Pstar s ν q r =
      α * actionRadialEnergy Pstar s ν q r :=
    action_barotropic_identity Pstar α (actionRadialX ν q r)
      (actionRadialX_pos ν q r hq) hα
  calc
    α * deriv (actionRadialEnergy Pstar s ν q) r =
        deriv (actionRadialPressure Pstar s ν q) r := hder
    _ = -(actionRadialEnergy Pstar s ν q r +
        actionRadialPressure Pstar s ν q r) * deriv ν r :=
      actionRadialPressure_conservation Pstar s q r ν hq hν
    _ = -(1 + α) * actionRadialEnergy Pstar s ν q r * deriv ν r := by
      rw [hval]
      ring

theorem matched_action_tov_derivative_jet
    (Pstar α ε₀ p₀ q μ κ Λ r F : ℝ) (ν : ℝ → ℝ)
    (hα : 0 < α) (hε : 0 < ε₀) (hq : 0 < q)
    (hp : p₀ = α * ε₀)
    (hN : Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = p₀)
    (hν₀ : ν r = 0) (hνdiff : DifferentiableAt ℝ ν r)
    (hνjet : deriv ν r =
      CAS06Adopted.tovNuJet (μ * r ^ 3) κ α ε₀ Λ r F) :
    actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε₀ ∧
    actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = p₀ ∧
    deriv (actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q) r =
      -(ε₀ + p₀) *
        CAS06Adopted.tovNuJet (μ * r ^ 3) κ α ε₀ Λ r F ∧
    deriv (actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q) r =
      -(1 + α) * ε₀ *
        CAS06Adopted.tovNuJet (μ * r ^ 3) κ α ε₀ Λ r F / α := by
  have hq0 : q ≠ 0 := ne_of_gt hq
  have hX : actionRadialX ν q r = q ^ 2 / 2 := by
    unfold actionRadialX
    rw [hν₀]
    norm_num
  have hN' : actionPressure Pstar (CAS06Scalar.exponent α) (q ^ 2 / 2) = p₀ :=
    hN
  have htherm := matched_action_thermodynamics Pstar α ε₀ p₀ q
    hα hε hp hN' hq0
  have hE : actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε₀ := by
    unfold actionRadialEnergy
    rw [hX]
    exact htherm.1
  have hP : actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = p₀ := by
    unfold actionRadialPressure
    rw [hX]
    exact htherm.2
  have hPd := actionRadialPressure_conservation Pstar
    (CAS06Scalar.exponent α) q r ν hq0 hνdiff
  rw [hE, hP, hνjet] at hPd
  have hEd := actionRadialEnergy_conservation Pstar α q r ν hα hq0 hνdiff
  rw [hE, hνjet] at hEd
  refine ⟨hE, hP, hPd, ?_⟩
  have hα0 : α ≠ 0 := ne_of_gt hα
  apply (eq_div_iff hα0).2
  nlinarith [hEd]

def chartActionStressHat (Pstar s q F r θ : ℝ) (a b : Fin 4) : ℝ :=
  CAS06Adopted.chartFrameScale 0 F r θ a *
    CAS06Adopted.chartFrameScale 0 F r θ b *
    actionStress Pstar s (chartContravariant 0 F r θ)
      (chartCovariant 0 F r θ) (scalarGradient q) a b

theorem matched_action_stress_frame
    (Pstar α ε₀ p₀ q F r θ : ℝ)
    (hα : 0 < α) (hε : 0 < ε₀) (hq : 0 < q)
    (hp : p₀ = α * ε₀)
    (hN : Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = p₀)
    (hF : 0 < F) (hr : 0 < r) (hθ : Real.sin θ ≠ 0) :
    ∀ a b : Fin 4,
      chartActionStressHat Pstar (CAS06Scalar.exponent α) q F r θ a b =
        if a = b then (if a = 0 then ε₀ else p₀) else 0 := by
  intro a b
  rw [chartActionStressHat,
    matched_action_stress_coordinate Pstar α ε₀ p₀ q F r θ
      hα hε hp hN (ne_of_gt hq) a b]
  fin_cases a <;> fin_cases b <;>
    simp [CAS06Adopted.chartFrameScale, chartCovariant,
      CAS06Adopted.chartMetric] <;>
    field_simp [hF.ne', hr.ne', hθ] <;>
    first | (rw [Real.sq_sqrt hF.le]; ring) | ring

theorem matched_action_tov_second_lapse_jet
    (Pstar q α ε₀ p₀ κ Λ μ r : ℝ) (ν m : ℝ → ℝ)
    (hα : 0 < α) (hε : 0 < ε₀) (hq : 0 < q) (hr : 0 < r)
    (hF : 0 < CAS06Adopted.massLapse m Λ r)
    (hp : p₀ = α * ε₀)
    (hN : Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = p₀)
    (hν₀ : ν r = 0) (hm₀ : m r = μ * r ^ 3)
    (hνdiff : DifferentiableAt ℝ ν r)
    (hm : HasDerivAt m
      (κ * r ^ 2 *
        actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r / 2) r)
    (hνnear : deriv ν =ᶠ[𝓝 r]
      CAS06Adopted.tovNuFunction m
        (actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q)
        (CAS06Adopted.massLapse m Λ) κ Λ) :
    HasDerivAt (deriv ν)
      (CAS06Adopted.tovNuSecondJet
        (μ * r ^ 3) (κ * r ^ 2 * ε₀ / 2) κ p₀
        (-(ε₀ + p₀) * CAS06Adopted.tovNuJet
          (μ * r ^ 3) κ α ε₀ Λ r (CAS06Adopted.massLapse m Λ r))
        Λ (CAS06Adopted.massLapse m Λ r)
        (CAS06Adopted.massLapseJet
          (μ * r ^ 3) (κ * r ^ 2 * ε₀ / 2) Λ r) r) r := by
  have hq0 : q ≠ 0 := hq.ne'
  have hX : actionRadialX ν q r = q ^ 2 / 2 := by
    unfold actionRadialX
    rw [hν₀]
    norm_num
  have htherm := matched_action_thermodynamics Pstar α ε₀ p₀ q
    hα hε hp hN hq0
  have hE0 : actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε₀ := by
    unfold actionRadialEnergy
    rw [hX]
    exact htherm.1
  have hP0 : actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = p₀ := by
    unfold actionRadialPressure
    rw [hX]
    exact htherm.2
  have hνder : deriv ν r = CAS06Adopted.tovNuJet
      (μ * r ^ 3) κ α ε₀ Λ r (CAS06Adopted.massLapse m Λ r) := by
    rw [hνnear.self_of_nhds]
    unfold CAS06Adopted.tovNuFunction CAS06Adopted.tovNuJet
    rw [hm₀, hP0, hp]
    ring
  have hPder := actionRadialPressure_hasDerivAt Pstar
    (CAS06Scalar.exponent α) q r ν hq0 hνdiff
  have hPder' : HasDerivAt
      (actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q)
      (-(ε₀ + p₀) * CAS06Adopted.tovNuJet
        (μ * r ^ 3) κ α ε₀ Λ r (CAS06Adopted.massLapse m Λ r)) r := by
    simpa only [hE0, hP0, hνder] using hPder
  have hFder := CAS06Adopted.massLapse_derivative (Λ := Λ) hr.ne' hm
  have hνrr := CAS06Adopted.local_tov_second_derivative
    hνnear hm hPder' hFder hr.ne' hF.ne'
  simpa only [hE0, hP0, hm₀] using hνrr

theorem C03_action_event_bundle
    (Pstar q α ε₀ p₀ κ Λ μ r θ : ℝ) (ν m : ℝ → ℝ)
    (hPstar : 0 < Pstar) (hq : 0 < q)
    (hα : 0 < α) (hα1 : α < 1) (hε : 0 < ε₀)
    (hκ : 0 < κ) (hr : 0 < r)
    (hF : 0 < CAS06Adopted.massLapse m Λ r)
    (hθpos : 0 < θ) (hθlt : θ < Real.pi)
    (hp : p₀ = α * ε₀)
    (hN : Pstar * (q ^ 2 / 2) ^ CAS06Scalar.exponent α = p₀)
    (hν₀ : ν r = 0) (hm₀ : m r = μ * r ^ 3)
    (hν : HasDerivAt ν
      (CAS06Adopted.tovNuFunction m (fun s => α * ε₀)
        (CAS06Adopted.massLapse m Λ) κ Λ r) r) :
    (∀ H : Mat4, (∀ a b : Fin 4, H a b = H b a) →
      HasDerivAt
        (fun t : ℝ => actionDensity Pstar (CAS06Scalar.exponent α)
          (chartContravariant 0 (CAS06Adopted.massLapse m Λ r) r θ + t • H)
          (scalarGradient q))
        (-(volumeDensity (chartContravariant 0
          (CAS06Adopted.massLapse m Λ r) r θ) / 2) *
          ∑ a : Fin 4, ∑ b : Fin 4,
            actionStress Pstar (CAS06Scalar.exponent α)
              (chartContravariant 0 (CAS06Adopted.massLapse m Λ r) r θ)
              (chartCovariant 0 (CAS06Adopted.massLapse m Λ r) r θ)
              (scalarGradient q) a b * H a b) 0) ∧
    (∀ η : Fin 4 → ℝ,
      HasDerivAt
        (fun t : ℝ => actionDensity Pstar (CAS06Scalar.exponent α)
          (chartContravariant 0 (CAS06Adopted.massLapse m Λ r) r θ)
          (fun a => scalarGradient q a + t * η a))
        (-volumeDensity (chartContravariant 0
          (CAS06Adopted.massLapse m Λ r) r θ) *
          ∑ a : Fin 4,
            actionCurrent Pstar (CAS06Scalar.exponent α)
              (chartContravariant 0 (CAS06Adopted.massLapse m Λ r) r θ)
              (scalarGradient q) a * η a) 0) ∧
    (∀ a b : Fin 4,
      chartActionStressHat Pstar (CAS06Scalar.exponent α) q
        (CAS06Adopted.massLapse m Λ r) r θ a b =
      if a = b then (if a = 0 then ε₀ else p₀) else 0) ∧
    chartScalarCurrentDivergence Pstar (CAS06Scalar.exponent α) q ν
      (CAS06Adopted.massLapse m Λ) r θ = 0 ∧
    (0 < deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α))
      (q ^ 2 / 2) + 2 * (q ^ 2 / 2) *
      deriv (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)))
        (q ^ 2 / 2)) ∧
    (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α))
      (q ^ 2 / 2) /
      (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α))
        (q ^ 2 / 2) + 2 * (q ^ 2 / 2) *
        deriv (deriv (CAS06Scalar.pressure Pstar (CAS06Scalar.exponent α)))
          (q ^ 2 / 2)) = α) ∧
    (actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q r = ε₀ ∧
      actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q r = p₀ ∧
      deriv (actionRadialPressure Pstar (CAS06Scalar.exponent α) ν q) r =
        -(ε₀ + p₀) * CAS06Adopted.tovNuJet
          (μ * r ^ 3) κ α ε₀ Λ r (CAS06Adopted.massLapse m Λ r) ∧
      deriv (actionRadialEnergy Pstar (CAS06Scalar.exponent α) ν q) r =
        -(1 + α) * ε₀ * CAS06Adopted.tovNuJet
          (μ * r ^ 3) κ α ε₀ Λ r (CAS06Adopted.massLapse m Λ r) / α) := by
  have hs : Real.sin θ ≠ 0 :=
    (Real.sin_pos_of_pos_of_lt_pi hθpos hθlt).ne'
  have hX : 0 < kinetic
      (chartContravariant 0 (CAS06Adopted.massLapse m Λ r) r θ)
      (scalarGradient q) := by
    rw [chart_scalar_kinetic_matched]
    have hq2 : 0 < q ^ 2 := sq_pos_of_ne_zero hq.ne'
    positivity
  have hGg := chartInverse_matrix_mul 0 (CAS06Adopted.massLapse m Λ r)
    r θ hF.ne' hr.ne' hs
  have hD := chartContravariant_det_neg 0 (CAS06Adopted.massLapse m Λ r)
    r θ hF hr.ne' hs
  have hνjet : deriv ν r = CAS06Adopted.tovNuJet
      (μ * r ^ 3) κ α ε₀ Λ r (CAS06Adopted.massLapse m Λ r) := by
    rw [hν.deriv]
    convert CAS06Adopted.tovNuFunction_eq_tovNuJet m (fun _ => ε₀)
      κ Λ α r using 1 <;> simp [hm₀]
  have hsound := action_sound_ratio Pstar α (q ^ 2 / 2) hPstar
    (by have hq2 : 0 < q ^ 2 := sq_pos_of_ne_zero hq.ne'; positivity)
    hα hα1
  refine ⟨?_, ?_, ?_, ?_, hsound.1, hsound.2, ?_⟩
  · intro H hH
    exact actionDensity_metric_stress_variation Pstar
      (CAS06Scalar.exponent α) _ _ H _ hGg hD hX hH
  · intro η
    exact actionDensity_scalar_hasDerivAt Pstar
      (CAS06Scalar.exponent α) _ _ η hX
      (chartContravariant_symmetric 0 (CAS06Adopted.massLapse m Λ r) r θ)
  · exact matched_action_stress_frame Pstar α ε₀ p₀ q
      (CAS06Adopted.massLapse m Λ r) r θ hα hε hq hp hN hF hr hs
  · exact chart_scalar_current_divergence_zero Pstar
      (CAS06Scalar.exponent α) q ν (CAS06Adopted.massLapse m Λ) r θ
  · exact matched_action_tov_derivative_jet Pstar α ε₀ p₀ q μ κ Λ r
      (CAS06Adopted.massLapse m Λ r) ν hα hε hq hp hN hν₀
      hν.differentiableAt hνjet

#print axioms det_one_add_hasDerivAt
#print axioms det_inverse_metric_variation
#print axioms chartInverse_matrix_mul
#print axioms chart_det_variation
#print axioms chartContravariant_det_neg
#print axioms volumeDensity_hasDerivAt
#print axioms kinetic_affine
#print axioms kinetic_hasDerivAt
#print axioms actionPressure_hasDerivAt
#print axioms action_energy_pressure_identity
#print axioms action_barotropic_identity
#print axioms action_sound_ratio
#print axioms actionDensity_metric_hasDerivAt
#print axioms trace_contract_symmetric
#print axioms actionStress_contraction
#print axioms actionDensity_metric_stress_variation
#print axioms kinetic_gradient_polynomial
#print axioms kinetic_gradient_hasDerivAt
#print axioms gradient_cross_symmetric
#print axioms kinetic_gradient_current
#print axioms actionCurrent_contraction
#print axioms actionDensity_scalar_hasDerivAt
#print axioms chartContravariant_symmetric
#print axioms chart_scalar_kinetic
#print axioms chart_scalar_current_spatial_zero
#print axioms chart_scalar_current_density_line_deriv_zero
#print axioms chart_scalar_current_divergence_zero
#print axioms matched_action_thermodynamics
#print axioms matched_action_stress_coordinate
#print axioms actionRadialX_eq_chart
#print axioms actionRadialX_hasDerivAt
#print axioms actionRadialPressure_conservation
#print axioms actionRadialEnergy_conservation
#print axioms matched_action_tov_derivative_jet
#print axioms matched_action_stress_frame
#print axioms matched_action_tov_second_lapse_jet
#print axioms C03_action_event_bundle

end
end CAS06Action
