import Mathlib
abbrev I := Fin 4
def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3
def sig (a : I) : ℝ := if a = 0 then -1 else 1
def delta (a b : I) : ℝ := if a = b then 1 else 0
def eta (a b : I) : ℝ := delta a b * sig a
theorem eta_contraction (a b : I) :
    sum4 (fun d => eta a d * eta d b) = delta a b := by
fin_cases a <;> fin_cases b <;> simp [sum4, sig, delta, eta, eta_contraction]
#print axioms eta_contraction
