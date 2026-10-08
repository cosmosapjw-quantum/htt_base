import Mathlib

/-! Exact finite CAS-10-C01 component. Coordinates are in the admitted
orthonormal frame with signature (-,+,+,+). All scalars are real. -/

namespace CAS10C01

abbrev V4 := Fin 4 → ℝ
abbrev V3 := Fin 3 → ℝ

noncomputable def u : V4 := ![(5:ℝ)/4, 3/4, 0, 0]
noncomputable def B1 (H : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  !![H*9/16, -H*15/16, 0, 0;
     -H*15/16, H*25/16, 0, 0;
     0, 0, H, 0;
     0, 0, 0, H]
noncomputable def B2 (H : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  !![-153*H/128, 0, -120*H/128, 0;
     0, 425*H/128, 0, 0;
     -120*H/128, 0, 353*H/128, 0;
     0, 0, 0, 353*H/128]

def action (B : Matrix (Fin 4) (Fin 4) ℝ) (v : V4) : V4 := B.mulVec v
noncomputable def b2Expected (H : ℝ) : V4 := ![-765*H/512, 1275*H/512, -600*H/512, 0]
def lorentz (v : V4) : ℝ := -(v 0)^2 + (v 1)^2 + (v 2)^2 + (v 3)^2
def componentPair (v w : V4) : ℝ := (v 0)*(w 0) + (v 1)*(w 1) + (v 2)*(w 2) + (v 3)*(w 3)

theorem u_unit : lorentz u = -1 := by
  change (-(5/4:ℝ)^2 + (3/4)^2 + (0:ℝ)^2 + (0:ℝ)^2) = -1
  norm_num

theorem B1_u_zero (H : ℝ) : action (B1 H) u = 0 := by
  funext i
  fin_cases i <;> norm_num [action, B1, u, Matrix.mulVec, dotProduct, Fin.sum_univ_succ] <;> ring

theorem B2_u (H : ℝ) : action (B2 H) u = b2Expected H := by
  funext i
  fin_cases i <;> norm_num [action, B2, u, b2Expected, Matrix.mulVec, dotProduct, Fin.sum_univ_succ] <;> ring

theorem b2_orthogonal (H : ℝ) : componentPair u (action (B2 H) u) = 0 := by
  rw [B2_u]
  dsimp [componentPair, u, b2Expected]
  ring

theorem b2_norm (H : ℝ) : lorentz (action (B2 H) u) = 87525*H^2/16384 := by
  rw [B2_u]
  dsimp [lorentz, b2Expected]
  ring

theorem b2_norm_pos (H : ℝ) (h : H ≠ 0) : 0 < lorentz (action (B2 H) u) := by
  rw [b2_norm]
  have hs : 0 < H^2 := sq_pos_of_ne_zero h
  positivity

theorem b2_nonzero (H : ℝ) (h : H ≠ 0) : action (B2 H) u ≠ 0 := by
  intro hz
  have hp := b2_norm_pos H h
  rw [hz] at hp
  norm_num [lorentz] at hp

noncomputable def Tdiag (H : ℝ) : V3 := ![3*H/8, -3*H/16, -3*H/16]
noncomputable def p1 (H : ℝ) : V3 := ![15*H/8, 0, 0]
noncomputable def p2 (H : ℝ) : V3 := ![0, 15*H/8, 0]
def power3 (v : V3) : ℝ := (v 0)^2 + (v 1)^2 + (v 2)^2
noncomputable def powers (H : ℝ) (p : V3) : V4 × ℝ :=
  (![((5:ℝ)/4)^2, ((3:ℝ)/4)^2, (7*H/4)^2, power3 p], power3 (Tdiag H))
noncomputable def expectedPowers (H : ℝ) : V4 × ℝ :=
  (![(25:ℝ)/16, 9/16, 49*H^2/16, 225*H^2/64], 27*H^2/128)

theorem tuple1_powers (H : ℝ) : powers H (p1 H) = expectedPowers H := by
  apply Prod.ext
  · funext i
    fin_cases i <;> simp [powers, expectedPowers, p1, power3] <;> ring
  · simp [powers, expectedPowers, Tdiag, power3]
    ring

theorem tuple2_powers (H : ℝ) : powers H (p2 H) = expectedPowers H := by
  apply Prod.ext
  · funext i
    fin_cases i <;> simp [powers, expectedPowers, p2, power3] <;> ring
  · simp [powers, expectedPowers, Tdiag, power3]
    ring

theorem H_zero_polynomial_controls :
    action (B1 0) u = 0 ∧
    action (B2 0) u = 0 ∧
    lorentz (action (B2 0) u) = 0 ∧
    powers 0 (p1 0) = expectedPowers 0 ∧
    powers 0 (p2 0) = expectedPowers 0 := by
  constructor
  · exact B1_u_zero 0
  constructor
  · rw [B2_u]
    funext i
    fin_cases i <;> norm_num [b2Expected]
  constructor
  · rw [b2_norm]
    norm_num
  constructor
  · exact tuple1_powers 0
  · exact tuple2_powers 0

theorem H_zero_not_strict : ¬ 0 < lorentz (action (B2 0) u) := by
  rw [b2_norm]
  norm_num

theorem H_one_b2_explicit :
    action (B2 1) u = ![-(765:ℝ)/512, 1275/512, -600/512, 0] := by
  rw [B2_u]
  funext i
  fin_cases i <;> norm_num [b2Expected]

theorem H_one_control :
    action (B1 1) u = 0 ∧
    action (B2 1) u = b2Expected 1 ∧
    lorentz (action (B2 1) u) = 87525/16384 ∧
    0 < lorentz (action (B2 1) u) ∧
    powers 1 (p1 1) = expectedPowers 1 ∧
    powers 1 (p2 1) = expectedPowers 1 := by
  constructor
  · exact B1_u_zero 1
  constructor
  · exact B2_u 1
  constructor
  · simpa using b2_norm 1
  constructor
  · exact b2_norm_pos 1 (by norm_num)
  constructor
  · exact tuple1_powers 1
  · exact tuple2_powers 1

#print axioms CAS10C01.u_unit
#print axioms CAS10C01.B1_u_zero
#print axioms CAS10C01.B2_u
#print axioms CAS10C01.b2_orthogonal
#print axioms CAS10C01.b2_norm
#print axioms CAS10C01.b2_norm_pos
#print axioms CAS10C01.b2_nonzero
#print axioms CAS10C01.tuple1_powers
#print axioms CAS10C01.tuple2_powers
#print axioms CAS10C01.H_zero_polynomial_controls
#print axioms CAS10C01.H_zero_not_strict
#print axioms CAS10C01.H_one_b2_explicit
#print axioms CAS10C01.H_one_control

end CAS10C01
