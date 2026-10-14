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

/-- The Frobenius-metric topology on `CMat`, made the preferred instance so that every
`MemLp`/`eLpNorm`/`Lp` statement uses the Frobenius normed structure consistently. It is
definitionally (default transparency) the product topology. -/
@[reducible] def frobTop : TopologicalSpace CMat :=
  @UniformSpace.toTopologicalSpace CMat (@PseudoMetricSpace.toUniformSpace CMat
    (@SeminormedAddCommGroup.toPseudoMetricSpace CMat
      (@NormedAddCommGroup.toSeminormedAddCommGroup CMat Matrix.frobeniusNormedAddCommGroup)))
attribute [local instance high] frobTop

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


/-! ## Abstract finite-measure layer -/
section Abstract
variable {X : Type*} [MeasurableSpace X]

def gainField (μ : Measure X) (c : ℝ) (P : X → CMat) (J : X → CMat) : X → CMat :=
  fun x => c • (P x * (∫ y, J y ∂μ) * P x)

def collisionField (μ : Measure X) (Γ c : ℝ) (P : X → CMat) (J : X → CMat) : X → CMat :=
  fun x => Γ • (-(J x) + gainField μ c P J x)

theorem enorm_integral_le_sqrt_mass (μ : Measure X) (J : X → CMat)
    (hJ : AEStronglyMeasurable J μ) :
    ‖∫ y, J y ∂μ‖ₑ ≤ μ Set.univ ^ (1 / 2 : ℝ) * eLpNorm J 2 μ := by
  calc ‖∫ y, J y ∂μ‖ₑ ≤ ∫⁻ y, ‖J y‖ₑ ∂μ := enorm_integral_le_lintegral_enorm _
    _ = eLpNorm J 1 μ := eLpNorm_one_eq_lintegral_enorm.symm
    _ ≤ eLpNorm J 2 μ * μ Set.univ ^ (1 / (1 : ℝ≥0∞).toReal - 1 / (2 : ℝ≥0∞).toReal) :=
        eLpNorm_le_eLpNorm_mul_rpow_measure_univ (by norm_num) hJ
    _ = _ := by rw [mul_comm]; norm_num

theorem gain_abstract (μ : Measure X) [IsFiniteMeasure μ] (c : ℝ) (P : X → CMat)
    (hP : ∀ x A, ‖P x * A * P x‖ ≤ ‖A‖)
    (hPm : ∀ A, AEStronglyMeasurable (fun x => P x * A * P x) μ)
    (J : X → CMat) (hJ : AEStronglyMeasurable J μ) :
    MemLp (gainField μ c P J) 2 μ ∧
      eLpNorm (gainField μ c P J) 2 μ ≤ ENNReal.ofReal |c| * μ Set.univ * eLpNorm J 2 μ := by
  set A := ∫ y, J y ∂μ with hA
  have hb : ∀ x, ‖gainField μ c P J x‖ ≤ |c| * ‖A‖ := fun x => by
    simp only [gainField, norm_smul, Real.norm_eq_abs]
    exact mul_le_mul_of_nonneg_left (hP x A) (abs_nonneg c)
  have hm : AEStronglyMeasurable (gainField μ c P J) μ := (hPm A).const_smul c
  refine ⟨MemLp.of_bound hm _ (Filter.Eventually.of_forall hb), ?_⟩
  calc eLpNorm (gainField μ c P J) 2 μ
        ≤ μ Set.univ ^ (2 : ℝ≥0∞).toReal⁻¹ * ENNReal.ofReal (|c| * ‖A‖) :=
        eLpNorm_le_of_ae_bound (Filter.Eventually.of_forall hb)
    _ = μ Set.univ ^ (1 / 2 : ℝ) * (ENNReal.ofReal |c| * ‖A‖ₑ) := by
        rw [ENNReal.ofReal_mul (abs_nonneg c), ofReal_norm]; norm_num
    _ ≤ μ Set.univ ^ (1 / 2 : ℝ) * (ENNReal.ofReal |c| *
          (μ Set.univ ^ (1 / 2 : ℝ) * eLpNorm J 2 μ)) := by
        gcongr; exact enorm_integral_le_sqrt_mass μ J hJ
    _ = ENNReal.ofReal |c| * (μ Set.univ ^ (1 / 2 : ℝ) * μ Set.univ ^ (1 / 2 : ℝ)) *
          eLpNorm J 2 μ := by ring
    _ = _ := by
        rw [← ENNReal.rpow_add_of_nonneg _ _ (by norm_num) (by norm_num)]; norm_num

theorem collision_abstract (μ : Measure X) [IsFiniteMeasure μ] (Γ c : ℝ) (P : X → CMat)
    (hP : ∀ x A, ‖P x * A * P x‖ ≤ ‖A‖)
    (hPm : ∀ A, AEStronglyMeasurable (fun x => P x * A * P x) μ)
    (J : X → CMat) (hJ : MemLp J 2 μ) :
    MemLp (collisionField μ Γ c P J) 2 μ ∧
      eLpNorm (collisionField μ Γ c P J) 2 μ ≤
        ENNReal.ofReal |Γ| * (1 + ENNReal.ofReal |c| * μ Set.univ) * eLpNorm J 2 μ := by
  obtain ⟨hG, hGb⟩ := gain_abstract μ c P hP hPm J hJ.1
  have hfun : collisionField μ Γ c P J = Γ • (-J + gainField μ c P J) := rfl
  rw [hfun]
  refine ⟨(hJ.neg.add hG).const_smul Γ, ?_⟩
  rw [eLpNorm_const_smul, Real.enorm_eq_ofReal_abs]
  calc ENNReal.ofReal |Γ| * eLpNorm (-J + gainField μ c P J) 2 μ
      ≤ ENNReal.ofReal |Γ| * (eLpNorm (-J) 2 μ + eLpNorm (gainField μ c P J) 2 μ) := by
        gcongr; exact eLpNorm_add_le hJ.1.neg hG.1 (by norm_num)
    _ ≤ ENNReal.ofReal |Γ| * (eLpNorm J 2 μ + ENNReal.ofReal |c| * μ Set.univ * eLpNorm J 2 μ) := by
        rw [eLpNorm_neg]; gcongr
    _ = _ := by ring
end Abstract

/-! ## Rest-electron Thomson instance on (S², dΩ) -/

def thomsonP (e : S2) : CMat := Pc (vecOf e)
def thomsonGain (J : S2 → CMat) : S2 → CMat := gainField dΩ (3 / (8 * Real.pi)) thomsonP J
def thomsonCollision (Γ : ℝ) (J : S2 → CMat) : S2 → CMat :=
  collisionField dΩ Γ (3 / (8 * Real.pi)) thomsonP J

theorem thomsonP_contract (e : S2) (A : CMat) : ‖thomsonP e * A * thomsonP e‖ ≤ ‖A‖ :=
  pointwise_complex_contraction (vecOf e) (vecOf_unit e) A

theorem thomsonP_apply (e : S2) (i j : Fin 3) :
    thomsonP e i j = (((1 : CAS16Projector.Mat) i j - vecOf e i * vecOf e j : ℝ) : ℂ) := by
  simp [thomsonP, Pc, CAS16Projector.projector]

theorem continuous_thomsonP : Continuous thomsonP := by
  have hc : ∀ i, Continuous fun e : S2 => vecOf e i := fun i => by
    unfold vecOf; fun_prop
  have h : @Continuous S2 CMat _ instTopologicalSpaceMatrix thomsonP := by
    refine continuous_pi fun i => continuous_pi fun j => ?_
    simp only [thomsonP_apply]
    exact Complex.continuous_ofReal.comp (continuous_const.sub ((hc i).mul (hc j)))
  exact h

theorem thomsonP_meas {μ : Measure S2} (A : CMat) :
    AEStronglyMeasurable (fun e => thomsonP e * A * thomsonP e) μ :=
  ((continuous_thomsonP.matrix_mul continuous_const).matrix_mul continuous_thomsonP).aestronglyMeasurable

theorem integral_cauchy (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    ‖∫ e, J e ∂dΩ‖ ≤ Real.sqrt (4 * Real.pi) * (eLpNorm J 2 dΩ).toReal := by
  have h := enorm_integral_le_sqrt_mass dΩ J hJ.1
  rw [sphere_mass, ← ofReal_norm, ENNReal.ofReal_rpow_of_nonneg (by positivity) (by norm_num),
    ← Real.sqrt_eq_rpow] at h
  have := ENNReal.toReal_mono (ENNReal.mul_ne_top ENNReal.ofReal_ne_top hJ.eLpNorm_ne_top) h
  rwa [ENNReal.toReal_ofReal (norm_nonneg _), ENNReal.toReal_mul,
    ENNReal.toReal_ofReal (Real.sqrt_nonneg _)] at this

theorem gain_coeff : ENNReal.ofReal |3 / (8 * Real.pi)| * dΩ Set.univ = ENNReal.ofReal (3 / 2) := by
  rw [sphere_mass, ← ENNReal.ofReal_mul (abs_nonneg _), abs_of_pos (by positivity)]
  congr 1; field_simp; ring

theorem gain_L2_bound (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    MemLp (thomsonGain J) 2 dΩ ∧
      eLpNorm (thomsonGain J) 2 dΩ ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩ := by
  obtain ⟨h1, h2⟩ := gain_abstract dΩ (3 / (8 * Real.pi)) thomsonP thomsonP_contract
    (fun A => thomsonP_meas A) J hJ.1
  exact ⟨h1, by rwa [gain_coeff] at h2⟩

theorem five_halves (Γ : ℝ) (hΓ : 0 ≤ Γ) :
    ENNReal.ofReal |Γ| * (1 + ENNReal.ofReal (3 / 2)) = ENNReal.ofReal (5 / 2 * Γ) := by
  rw [← ENNReal.ofReal_one, ← ENNReal.ofReal_add (by norm_num) (by norm_num),
    ← ENNReal.ofReal_mul (abs_nonneg _), abs_of_nonneg hΓ]
  congr 1; ring

theorem collision_L2_bound (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    MemLp (thomsonCollision Γ J) 2 dΩ ∧
      eLpNorm (thomsonCollision Γ J) 2 dΩ ≤ ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩ := by
  obtain ⟨h1, h2⟩ := collision_abstract dΩ Γ (3 / (8 * Real.pi)) thomsonP thomsonP_contract
    (fun A => thomsonP_meas A) J hJ
  exact ⟨h1, by rwa [gain_coeff, five_halves Γ hΓ] at h2⟩

end G16ACoherency
