import Mathlib

/-!
CAS-13-C01, positive-real power response only.
The derivative lemmas below are obtained from Mathlib's `Real.deriv_rpow_const`;
no derivative formula is introduced as a hypothesis.
-/

namespace Cas13C01

noncomputable section

def psi (p y : ℝ) : ℝ := y ^ p
def c0 (p : ℝ) : ℝ := (p - 3) * (p - 4) / 12
def c3 (p : ℝ) : ℝ := p * (4 - p) / 3
def c4 (p : ℝ) : ℝ := p * (p - 3) / 4
def q (p y : ℝ) : ℝ := c0 p + c3 p * y ^ 3 + c4 p * y ^ 4

def dpsi1 (p y : ℝ) : ℝ := p * y ^ (p - 1)
def dpsi2 (p y : ℝ) : ℝ := p * (p - 1) * y ^ (p - 2)
def dpsi3 (p y : ℝ) : ℝ := p * (p - 1) * (p - 2) * y ^ (p - 3)
def dq1 (p y : ℝ) : ℝ := 3 * c3 p * y ^ 2 + 4 * c4 p * y ^ 3
def dq2 (p y : ℝ) : ℝ := 6 * c3 p * y + 12 * c4 p * y ^ 2
def dq3 (p y : ℝ) : ℝ := 6 * c3 p + 24 * c4 p * y

theorem psi_positive_branch (p y : ℝ) (hy : 0 < y) :
    psi p y = Real.exp (Real.log y * p) := by
  exact Real.rpow_def_of_pos hy p

theorem deriv_psi (p y : ℝ) : deriv (psi p) y = dpsi1 p y := by
  exact Real.deriv_rpow_const y p

theorem deriv_dpsi1 (p y : ℝ) : deriv (dpsi1 p) y = dpsi2 p y := by
  change deriv (fun z : ℝ => p * z ^ (p - 1)) y = _
  rw [deriv_const_mul_field, Real.deriv_rpow_const]
  dsimp [dpsi2]
  ring

theorem deriv_dpsi2 (p y : ℝ) : deriv (dpsi2 p) y = dpsi3 p y := by
  change deriv (fun z : ℝ => (p * (p - 1)) * z ^ (p - 2)) y = _
  rw [deriv_const_mul_field, Real.deriv_rpow_const]
  dsimp [dpsi3]
  ring

theorem deriv2_psi (p y : ℝ) :
    deriv (fun z => deriv (psi p) z) y = dpsi2 p y := by
  simp only [deriv_psi]
  exact deriv_dpsi1 p y

theorem deriv3_psi (p y : ℝ) :
    deriv (fun z => deriv (fun w => deriv (psi p) w) z) y = dpsi3 p y := by
  simp only [deriv2_psi]
  exact deriv_dpsi2 p y

theorem deriv_q (p y : ℝ) : deriv (q p) y = dq1 p y := by
  have h : HasDerivAt (q p) (dq1 p y) y := by
    unfold q dq1
    convert ((hasDerivAt_const y (c0 p)).add
      (((hasDerivAt_pow 3 y).const_mul (c3 p)).add
        ((hasDerivAt_pow 4 y).const_mul (c4 p)))) using 1 <;>
      try { rfl } <;> try { ext z; simp only [Pi.add_apply]; ring } <;> ring
  exact h.deriv

theorem deriv_dq1 (p y : ℝ) : deriv (dq1 p) y = dq2 p y := by
  have h : HasDerivAt (dq1 p) (dq2 p y) y := by
    unfold dq1 dq2
    convert (((hasDerivAt_pow 2 y).const_mul (3 * c3 p)).add
      ((hasDerivAt_pow 3 y).const_mul (4 * c4 p))) using 1 <;>
      try { rfl } <;> try { ext z; simp only [Pi.add_apply]; ring } <;> ring
  exact h.deriv

theorem deriv_dq2 (p y : ℝ) : deriv (dq2 p) y = dq3 p y := by
  have h : HasDerivAt (dq2 p) (dq3 p y) y := by
    unfold dq2 dq3
    convert (((hasDerivAt_id y).const_mul (6 * c3 p)).add
      ((hasDerivAt_pow 2 y).const_mul (12 * c4 p))) using 1 <;>
      try { rfl } <;> try { ext z; simp only [Pi.add_apply]; ring } <;> ring
  exact h.deriv

theorem deriv2_q (p y : ℝ) :
    deriv (fun z => deriv (q p) z) y = dq2 p y := by
  simp only [deriv_q]
  exact deriv_dq1 p y

theorem deriv3_q (p y : ℝ) :
    deriv (fun z => deriv (fun w => deriv (q p) w) z) y = dq3 p y := by
  simp only [deriv2_q]
  exact deriv_dq2 p y

theorem q_at_one (p : ℝ) : q p 1 = 1 := by
  dsimp [q, c0, c3, c4]
  norm_num
  ring

theorem dq1_at_one (p : ℝ) : dq1 p 1 = p := by
  dsimp [dq1, c3, c4]
  norm_num
  ring

theorem dq2_at_one (p : ℝ) : dq2 p 1 = p * (p - 1) := by
  dsimp [dq2, c3, c4]
  norm_num
  ring

theorem jets_at_one (p : ℝ) :
    q p 1 = psi p 1 ∧
    deriv (q p) 1 = deriv (psi p) 1 ∧
    deriv (fun z => deriv (q p) z) 1 =
      deriv (fun z => deriv (psi p) z) 1 := by
  constructor
  · simp [q_at_one, psi]
  constructor
  · rw [deriv_q, deriv_psi, dq1_at_one]
    simp [dpsi1]
  · rw [deriv2_q, deriv2_psi, dq2_at_one]
    simp [dpsi2]

theorem dq3_formula (p y : ℝ) :
    dq3 p y = 2 * p * (4 - p) + 6 * p * (p - 3) * y := by
  dsimp [dq3, c3, c4]
  ring

theorem third_mismatch (p y : ℝ) (_hy : 0 < y) :
    deriv (fun z => deriv (fun w => deriv (psi p) w) z) y -
      deriv (fun z => deriv (fun w => deriv (q p) w) z) y =
      p * (p - 1) * (p - 2) * y ^ (p - 3) -
      2 * p * (4 - p) - 6 * p * (p - 3) * y := by
  rw [deriv3_psi, deriv3_q, dq3_formula]
  dsimp [dpsi3]
  ring

theorem unit_mismatch (p : ℝ) (hp : 4 < p) :
    deriv (fun z => deriv (fun w => deriv (psi p) w) z) 1 -
      deriv (fun z => deriv (fun w => deriv (q p) w) z) 1 =
      p * (p - 3) * (p - 4) ∧ 0 < p * (p - 3) * (p - 4) := by
  constructor
  · rw [third_mismatch p 1 (by norm_num)]
    norm_num
    ring
  · have hp0 : 0 < p := by linarith
    have hp3 : 0 < p - 3 := by linarith
    have hp4 : 0 < p - 4 := by linarith
    positivity

#print axioms Cas13C01.psi_positive_branch
#print axioms Cas13C01.deriv3_psi
#print axioms Cas13C01.deriv3_q
#print axioms Cas13C01.jets_at_one
#print axioms Cas13C01.third_mismatch
#print axioms Cas13C01.unit_mismatch

end
end Cas13C01
