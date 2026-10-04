import Mathlib

/-!
CAS-05 V3 blind Lean axis.  Coordinates are indexed 0,1,2,3, with x0 a
length coordinate.  All sums below explicitly enumerate those four indices.
The finite arrays are local metric jets; no neighborhood conclusion is made.
-/

namespace CAS05Finite

abbrev I := Fin 4

def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3
def sig (a : I) : ℝ := if a = 0 then -1 else 1
def delta (a b : I) : ℝ := if a = b then 1 else 0
def eta (a b : I) : ℝ := delta a b * sig a

def metric (E : ℝ) (a b : I) : ℝ := E * eta a b
noncomputable def inverseMetric (E : ℝ) (a b : I) : ℝ := E⁻¹ * eta a b
def dMetric (E : ℝ) (p : I → ℝ) (c a b : I) : ℝ :=
  2 * E * p c * eta a b
noncomputable def dInverseMetric (E : ℝ) (p : I → ℝ) (d a b : I) : ℝ :=
  -2 * E⁻¹ * p d * eta a b
def ddMetric (E : ℝ) (p : I → ℝ) (h : I → I → ℝ)
    (d c a b : I) : ℝ :=
  (4 * E * p d * p c + 2 * E * h d c) * eta a b

noncomputable def christoffel (E : ℝ) (p : I → ℝ) (a b c : I) : ℝ :=
  (1 / 2 : ℝ) * sum4 (fun d =>
    inverseMetric E a d *
      (dMetric E p b c d + dMetric E p c b d - dMetric E p d b c))

def conformalChristoffel (p : I → ℝ) (a b c : I) : ℝ :=
  delta a b * p c + delta a c * p b - eta b c * sig a * p a

noncomputable def dChristoffel (E : ℝ) (p : I → ℝ)
    (h : I → I → ℝ) (d a b c : I) : ℝ :=
  (1 / 2 : ℝ) * sum4 (fun e =>
    dInverseMetric E p d a e *
      (dMetric E p b c e + dMetric E p c b e - dMetric E p e b c) +
    inverseMetric E a e *
      (ddMetric E p h d b c e + ddMetric E p h d c b e - ddMetric E p h d e b c))

def conformalDChristoffel (h : I → I → ℝ) (d a b c : I) : ℝ :=
  delta a b * h d c + delta a c * h d b - eta b c * sig a * h d a

theorem christoffel_from_metric (E : ℝ) (p : I → ℝ) (hE : E ≠ 0)
    (a b c : I) : christoffel E p a b c = conformalChristoffel p a b c := by
  fin_cases a <;> fin_cases b <;> fin_cases c <;>
    simp [christoffel, conformalChristoffel, sum4, inverseMetric, dMetric,
      eta, delta, sig, hE] <;> field_simp <;> ring

#print axioms christoffel_from_metric

theorem dChristoffel_from_metric (E : ℝ) (p : I → ℝ)
    (h : I → I → ℝ) (hE : E ≠ 0) (d a b c : I) :
    dChristoffel E p h d a b c = conformalDChristoffel h d a b c := by
  fin_cases d <;> fin_cases a <;> fin_cases b <;> fin_cases c <;>
    simp [dChristoffel, conformalDChristoffel, sum4, dInverseMetric,
      inverseMetric, dMetric, ddMetric, eta, delta, sig] <;>
    field_simp <;> ring

#print axioms dChristoffel_from_metric

end CAS05Finite
