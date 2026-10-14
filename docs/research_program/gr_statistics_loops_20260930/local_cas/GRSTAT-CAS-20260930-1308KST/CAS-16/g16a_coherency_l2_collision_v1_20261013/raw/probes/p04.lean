import Mathlib
import ProjectorBridge

noncomputable section
open MeasureTheory Metric
open scoped ENNReal

namespace G16ACoherency

attribute [local instance] Matrix.frobeniusNormedAddCommGroup Matrix.frobeniusNormedSpace
  Matrix.frobeniusNormSMulClass Matrix.frobeniusIsBoundedSMul

abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := sphere (0 : E3) 1
abbrev CMat := Matrix (Fin 3) (Fin 3) ℂ

def dΩ : Measure S2 := (volume : Measure E3).toSphere
def vecOf (e : S2) : CAS16Projector.Vec := fun i => (e : E3) i
def Pc (v : CAS16Projector.Vec) : CMat := (CAS16Projector.projector v).map (fun r : ℝ => (r : ℂ))

theorem frob_sq (A : CMat) : ‖A‖ ^ 2 = ∑ i, ∑ j, ‖A i j‖ ^ 2 := by
  rw [Matrix.frobenius_norm_def, ← Real.sqrt_eq_rpow, Real.sq_sqrt (by positivity)]
  simp_rw [Real.rpow_two]

def reM (A : CMat) : CAS16Projector.Mat := A.map Complex.re
def imM (A : CMat) : CAS16Projector.Mat := A.map Complex.im

theorem decomp (A : CMat) :
    A = (reM A).map Complex.ofRealHom + Complex.I • (imM A).map Complex.ofRealHom := by
  ext i j
  apply Complex.ext <;> simp [reM, imM]

theorem frob_sq_split (A : CMat) :
    ‖A‖ ^ 2 = CAS16Projector.frobeniusSquare (reM A) + CAS16Projector.frobeniusSquare (imM A) := by
  rw [frob_sq, CAS16Projector.frobeniusSquare, CAS16Projector.frobeniusSquare, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl (fun i _ => ?_)
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl (fun j _ => ?_)
  rw [Complex.sq_norm, Complex.normSq_apply]
  simp [reM, imM]; ring

theorem sandwich_re (v : CAS16Projector.Vec) (A : CMat) :
    reM (Pc v * A * Pc v) = CAS16Projector.projector v * reM A * CAS16Projector.projector v ∧
    imM (Pc v * A * Pc v) = CAS16Projector.projector v * imM A * CAS16Projector.projector v := by
  set P := CAS16Projector.projector v
  have hP : Pc v = P.map Complex.ofRealHom := rfl
  have key : Pc v * A * Pc v = (P * reM A * P).map Complex.ofRealHom
      + Complex.I • (P * imM A * P).map Complex.ofRealHom := by
    conv_lhs => rw [decomp A]
    rw [hP, Matrix.map_mul, Matrix.map_mul, Matrix.map_mul, Matrix.map_mul, Matrix.mul_add,
      Matrix.add_mul, Matrix.mul_smul, Matrix.smul_mul]
  constructor
  · ext i j
    show ((Pc v * A * Pc v) i j).re = _
    rw [key]
    simp only [Matrix.add_apply, Matrix.smul_apply, Matrix.map_apply, smul_eq_mul, Complex.add_re,
      Complex.mul_re, Complex.I_re, Complex.I_im, Complex.ofRealHom_eq_coe, Complex.ofReal_re,
      Complex.ofReal_im]
    ring
  · ext i j
    show ((Pc v * A * Pc v) i j).im = _
    rw [key]
    simp only [Matrix.add_apply, Matrix.smul_apply, Matrix.map_apply, smul_eq_mul, Complex.add_im,
      Complex.mul_im, Complex.I_re, Complex.I_im, Complex.ofRealHom_eq_coe, Complex.ofReal_re,
      Complex.ofReal_im]
    ring

theorem pointwise_complex_contraction (v : CAS16Projector.Vec) (hv : ∑ i, v i * v i = 1)
    (A : CMat) : ‖Pc v * A * Pc v‖ ≤ ‖A‖ := by
  have hv' : CAS16Projector.dot v v = 1 := hv
  obtain ⟨h1, h2⟩ := sandwich_re v A
  have hsq : ‖Pc v * A * Pc v‖ ^ 2 ≤ ‖A‖ ^ 2 := by
    rw [frob_sq_split, frob_sq_split, h1, h2]
    exact add_le_add (CAS16Projector.sandwich_frobenius_le v _ hv')
      (CAS16Projector.sandwich_frobenius_le v _ hv')
  exact (sq_le_sq₀ (norm_nonneg _) (norm_nonneg _)).mp hsq

theorem sphere_mass : dΩ Set.univ = ENNReal.ofReal (4 * Real.pi) := by
  rw [dΩ, Measure.toSphere_apply_univ, EuclideanSpace.volume_ball_fin_three]
  simp only [finrank_euclideanSpace, Fintype.card_fin, ENNReal.ofReal_one, one_pow, one_mul]
  rw [show ((3 : ℕ) : ℝ≥0∞) = ENNReal.ofReal 3 by simp, ← ENNReal.ofReal_mul (by norm_num)]
  congr 1; ring

instance : IsFiniteMeasure dΩ := ⟨by rw [sphere_mass]; exact ENNReal.ofReal_lt_top⟩

theorem vecOf_unit (e : S2) : ∑ i, vecOf e i * vecOf e i = 1 := by
  have h1 : ‖(e : E3)‖ = 1 := by simp
  have h2 := EuclideanSpace.norm_sq_eq (e : E3)
  rw [h1] at h2
  simp only [vecOf, Real.norm_eq_abs, sq_abs, one_pow] at h2 ⊢
  rw [h2]; simp [sq]

end G16ACoherency
