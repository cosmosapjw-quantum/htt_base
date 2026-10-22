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

section Abstract
variable {X : Type*} [MeasurableSpace X]
def gainField (μ : Measure X) (c : ℝ) (P : X → CMat) (J : X → CMat) : X → CMat :=
  fun x => c • (P x * (∫ y, J y ∂μ) * P x)
def collisionField (μ : Measure X) (Γ c : ℝ) (P : X → CMat) (J : X → CMat) : X → CMat :=
  fun x => Γ • (-(J x) + gainField μ c P J x)
end Abstract

def thomsonP (e : S2) : CMat := Pc (vecOf e)
def thomsonGain (J : S2 → CMat) : S2 → CMat := gainField dΩ (3 / (8 * Real.pi)) thomsonP J
def thomsonCollision (Γ : ℝ) (J : S2 → CMat) : S2 → CMat :=
  collisionField dΩ Γ (3 / (8 * Real.pi)) thomsonP J

theorem T1 (v : CAS16Projector.Vec) (hv : ∑ i, v i * v i = 1) (A : CMat) :
    ‖Pc v * A * Pc v‖ ≤ ‖A‖ := sorry
theorem T2 : dΩ Set.univ = ENNReal.ofReal (4 * Real.pi) := sorry
instance : IsFiniteMeasure dΩ := sorry
theorem T3 (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    ‖∫ e, J e ∂dΩ‖ ≤ Real.sqrt (4 * Real.pi) * (eLpNorm J 2 dΩ).toReal := sorry
theorem T4 (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    MemLp (thomsonGain J) 2 dΩ ∧
      eLpNorm (thomsonGain J) 2 dΩ ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩ := sorry
theorem T5 (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    MemLp (thomsonCollision Γ J) 2 dΩ ∧
      eLpNorm (thomsonCollision Γ J) 2 dΩ ≤ ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩ := sorry
def gainCLM : Lp CMat 2 dΩ →L[ℝ] Lp CMat 2 dΩ := sorry
def collisionCLM (Γ : ℝ) : Lp CMat 2 dΩ →L[ℝ] Lp CMat 2 dΩ := Γ • (gainCLM - ContinuousLinearMap.id ℝ _)
theorem T6a (J : Lp CMat 2 dΩ) : (gainCLM J : S2 → CMat) =ᵐ[dΩ] thomsonGain (J : S2 → CMat) := sorry
theorem T6b : ‖gainCLM‖ ≤ 3 / 2 := sorry
theorem T6c (Γ : ℝ) (J : Lp CMat 2 dΩ) :
    (collisionCLM Γ J : S2 → CMat) =ᵐ[dΩ] thomsonCollision Γ (J : S2 → CMat) := sorry
theorem T6d (Γ : ℝ) (hΓ : 0 ≤ Γ) : ‖collisionCLM Γ‖ ≤ 5 / 2 * Γ := sorry
def dΩnorm : Measure S2 := (ENNReal.ofReal (4 * Real.pi))⁻¹ • dΩ
theorem T7a : dΩnorm Set.univ = 1 := sorry
theorem T7b (Γ : ℝ) (J : S2 → CMat) (hJ : MemLp J 2 dΩ) :
    collisionField dΩnorm Γ (3 / 2) thomsonP J = thomsonCollision Γ J := sorry
theorem T7c (Γ : ℝ) (hΓ : 0 ≤ Γ) (J : S2 → CMat) (hJ : MemLp J 2 dΩnorm) :
    eLpNorm (gainField dΩnorm (3 / 2) thomsonP J) 2 dΩnorm ≤ ENNReal.ofReal (3 / 2) * eLpNorm J 2 dΩnorm ∧
    eLpNorm (collisionField dΩnorm Γ (3 / 2) thomsonP J) 2 dΩnorm ≤
      ENNReal.ofReal (5 / 2 * Γ) * eLpNorm J 2 dΩnorm := sorry
theorem T7d (f : S2 → CMat) :
    eLpNorm f 2 dΩnorm = (ENNReal.ofReal (4 * Real.pi))⁻¹ ^ (1 / 2 : ℝ) * eLpNorm f 2 dΩ := sorry
theorem N1 : ¬ (‖Pc ![2, 0, 0] * Matrix.single 0 0 1 * Pc ![2, 0, 0]‖ ≤ ‖(Matrix.single 0 0 1 : CMat)‖) := sorry
theorem N2 (e : S2) : thomsonGain (fun _ => (1 : CMat)) e = ((3 / 2 : ℝ) : ℂ) • thomsonP e := sorry
end G16ACoherency
