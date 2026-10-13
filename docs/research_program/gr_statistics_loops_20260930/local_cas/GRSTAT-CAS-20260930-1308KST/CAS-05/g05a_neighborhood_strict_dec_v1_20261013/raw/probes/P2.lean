import Mathlib
abbrev I := Fin 4
def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3

theorem contDiff_det {n : WithTop ℕ∞} (M : (I → ℝ) → Matrix I I ℝ)
    (h : ∀ i j, ContDiff ℝ n fun y => M y i j) : ContDiff ℝ n fun y => (M y).det := by
  simp only [Matrix.det_apply']
  apply ContDiff.sum
  intro σ _
  exact contDiff_const.mul (contDiff_prod fun i _ => h (σ i) i)

theorem contDiff_adj {n : WithTop ℕ∞} (M : (I → ℝ) → Matrix I I ℝ)
    (h : ∀ i j, ContDiff ℝ n fun y => M y i j) (i j : I) :
    ContDiff ℝ n fun y => (M y).adjugate i j := by
  simp only [Matrix.adjugate_apply]
  apply contDiff_det
  intro k l
  simp only [Matrix.updateRow_apply]
  split_ifs
  · exact contDiff_const
  · exact h k l

theorem contDiffAt_inv_entry {n : WithTop ℕ∞} (M : (I → ℝ) → Matrix I I ℝ)
    (h : ∀ i j, ContDiff ℝ n fun y => M y i j) (x : I → ℝ) (hx : (M x).det ≠ 0)
    (a b : I) : ContDiffAt ℝ n (fun y => (M y)⁻¹ a b) x := by
  have : (fun y => (M y)⁻¹ a b) = fun y => ((M y).det)⁻¹ * (M y).adjugate a b := by
    funext y
    rw [Matrix.inv_def]
    simp [Ring.inverse_eq_inv']
  rw [this]
  exact ((contDiff_det M h).contDiffAt.inv hx).mul (contDiff_adj M h a b).contDiffAt

example (F : I → (I → ℝ) → ℝ) (h : ∀ i, DifferentiableAt ℝ (F i) 0) (G : (I→ℝ) → ℝ) (hG : DifferentiableAt ℝ G 0):
    DifferentiableAt ℝ (fun y => F 0 y * G y + F 2 y) 0 := by fun_prop

example (F : I → I → (I → ℝ) → ℝ) (h : ∀ i j, ContinuousAt (F i j) 0) :
    ContinuousAt (fun y => sum4 (fun i => F i 0 y * F 1 i y)) 0 := by
  unfold sum4; fun_prop

example (F : I → I → (I → ℝ) → ℝ) (h : ∀ i j, ContinuousAt (fun y => F i j y) 0) :
    ContinuousAt (fun y => sum4 (fun i => F i 0 y * F 1 i y)) 0 := by
  unfold sum4; fun_prop
