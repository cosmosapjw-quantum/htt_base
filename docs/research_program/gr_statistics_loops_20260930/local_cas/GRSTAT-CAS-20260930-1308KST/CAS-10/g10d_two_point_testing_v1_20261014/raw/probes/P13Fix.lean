import Mathlib
import G10CSmoothCutoff
open MeasureTheory Real Set Filter Topology
open scoped ENNReal NNReal
namespace P13
abbrev E3 := EuclideanSpace ℝ (Fin 3)
noncomputable def chi (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) : ℝ :=
  δ * G10C.smoothCutoff a ρ ‖x‖
noncomputable def u1 (a : ℝ) (ρ : ℝ → ℝ) (δ : ℝ) (x : E3) : Fin 4 → ℝ :=
  ![cosh (chi a ρ δ x), sinh (chi a ρ δ x), 0, 0]
variable {a : ℝ} {ρ : ℝ → ℝ}
theorem chi_contDiff (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    ContDiff ℝ (⊤ : ℕ∞) (chi a ρ δ) :=
  contDiff_const.mul (G10C.radial_contDiff ha hρ)
theorem u1_contDiff (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ : ℝ) :
    ContDiff ℝ (⊤ : ℕ∞) (u1 a ρ δ) := by
  have hc := chi_contDiff ha hρ δ
  rw [contDiff_pi]
  intro i
  fin_cases i
  · exact Real.contDiff_cosh.comp hc
  · exact Real.contDiff_sinh.comp hc
  · exact contDiff_const
  · exact contDiff_const
noncomputable def prof (a : ℝ) (ρ : ℝ → ℝ) (δ c s : ℝ) : ℝ :=
  cosh (δ * G10C.smoothCutoff a ρ s) + c * sinh (δ * G10C.smoothCutoff a ρ s)
noncomputable def prof1 (a : ℝ) (ρ : ℝ → ℝ) (δ c s : ℝ) : ℝ :=
  (sinh (δ * G10C.smoothCutoff a ρ s) + c * cosh (δ * G10C.smoothCutoff a ρ s)) *
    (δ * deriv (G10C.smoothCutoff a ρ) s)
noncomputable def prof2 (a : ℝ) (ρ : ℝ → ℝ) (δ c s : ℝ) : ℝ :=
  (cosh (δ * G10C.smoothCutoff a ρ s) + c * sinh (δ * G10C.smoothCutoff a ρ s)) *
      (δ * deriv (G10C.smoothCutoff a ρ) s) * (δ * deriv (G10C.smoothCutoff a ρ) s) +
    (sinh (δ * G10C.smoothCutoff a ρ s) + c * cosh (δ * G10C.smoothCutoff a ρ s)) *
      (δ * deriv (deriv (G10C.smoothCutoff a ρ)) s)
theorem smoothCutoff_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (s : ℝ) :
    HasDerivAt (G10C.smoothCutoff a ρ) (deriv (G10C.smoothCutoff a ρ) s) s :=
  ((G10C.smoothCutoff_contDiff ha hρ).differentiable (by simp)).differentiableAt.hasDerivAt
theorem deriv_smoothCutoff_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (s : ℝ) :
    HasDerivAt (deriv (G10C.smoothCutoff a ρ)) (deriv (deriv (G10C.smoothCutoff a ρ)) s) s := by
  have h : ContDiff ℝ (⊤ : ℕ∞) (G10C.smoothCutoff a ρ) := G10C.smoothCutoff_contDiff ha hρ
  have h' : ContDiff ℝ (⊤ : ℕ∞) (deriv (G10C.smoothCutoff a ρ)) := (contDiff_infty_iff_deriv.mp h).2
  exact (h'.differentiable (by simp)).differentiableAt.hasDerivAt
theorem prof_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ c s : ℝ) :
    HasDerivAt (prof a ρ δ c) (prof1 a ρ δ c s) s := by
  have hq := (smoothCutoff_hasDerivAt ha hρ s).const_mul δ
  have h := hq.cosh.add (hq.sinh.const_mul c)
  unfold prof prof1
  convert h using 1
  trace_state
  sorry
theorem prof1_hasDerivAt (ha : 0 < a) (hρ : G10C.IsMollifier a ρ) (δ c s : ℝ) :
    HasDerivAt (prof1 a ρ δ c) (prof2 a ρ δ c s) s := by
  have hq := (smoothCutoff_hasDerivAt ha hρ s).const_mul δ
  have hq' := (deriv_smoothCutoff_hasDerivAt ha hρ s).const_mul δ
  have hA := hq.sinh.add (hq.cosh.const_mul c)
  have h := hA.mul hq'
  unfold prof1 prof2
  convert h using 1
  trace_state
  sorry
example : (Measure.dirac (0:ℝ)).real {ω : ℝ | (0:ℝ) ∈ ({ω} : Set ℝ)} = 1 := by
  have : {ω : ℝ | (0:ℝ) ∈ ({ω} : Set ℝ)} = {0} := by ext ω; simp [eq_comm]
  rw [this]
  simp [measureReal_def]
example : (Measure.dirac (1:ℝ)).real {ω : ℝ | (1:ℝ) ∈ ({ω} : Set ℝ)} = 1 := by
  have : {ω : ℝ | (1:ℝ) ∈ ({ω} : Set ℝ)} = {1} := by ext ω; simp [eq_comm]
  rw [this]
  simp [measureReal_def]
end P13
