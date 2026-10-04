import Mathlib

set_option maxHeartbeats 2000000

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

def ricciFromConnection (p : I → ℝ) (h : I → I → ℝ)
    (a b : I) : ℝ :=
  sum4 (fun c =>
    conformalDChristoffel h c c b a - conformalDChristoffel h b c c a +
    sum4 (fun e =>
      conformalChristoffel p c c e * conformalChristoffel p e b a -
      conformalChristoffel p c b e * conformalChristoffel p e c a))

def boxH (h : I → I → ℝ) : ℝ := sum4 (fun c => sig c * h c c)
def normP (p : I → ℝ) : ℝ := sum4 (fun c => sig c * p c * p c)

def conformalRicci (p : I → ℝ) (h : I → I → ℝ) (a b : I) : ℝ :=
  -2 * h a b + 2 * p a * p b - eta a b * (boxH h + 2 * normP p)

theorem ricci_from_connection (p : I → ℝ) (h : I → I → ℝ)
    (hsym : ∀ a b, h a b = h b a) (a b : I) :
    ricciFromConnection p h a b = conformalRicci p h a b := by
  have hs : h b a = h a b := hsym b a
  fin_cases a <;> fin_cases b <;>
    simp [ricciFromConnection, conformalRicci, conformalChristoffel,
      conformalDChristoffel, boxH, normP, sum4, eta, delta, sig] <;>
    simp at hs <;> nlinarith [hs]

#print axioms ricci_from_connection

noncomputable def ricciMetric (E : ℝ) (p : I → ℝ)
    (h : I → I → ℝ) (a b : I) : ℝ :=
  sum4 (fun c =>
    dChristoffel E p h c c b a - dChristoffel E p h b c c a +
    sum4 (fun e =>
      christoffel E p c c e * christoffel E p e b a -
      christoffel E p c b e * christoffel E p e c a))

theorem ricciMetric_eq (E : ℝ) (p : I → ℝ) (h : I → I → ℝ)
    (hE : E ≠ 0) (hsym : ∀ a b, h a b = h b a) (a b : I) :
    ricciMetric E p h a b = conformalRicci p h a b := by
  calc
    ricciMetric E p h a b = ricciFromConnection p h a b := by
      simp [ricciMetric, ricciFromConnection, sum4,
        dChristoffel_from_metric E p h hE, christoffel_from_metric E p hE]
    _ = conformalRicci p h a b := ricci_from_connection p h hsym a b

def conformalEinstein (p : I → ℝ) (h : I → I → ℝ) (a b : I) : ℝ :=
  -2 * h a b + 2 * p a * p b + 2 * eta a b * boxH h + eta a b * normP p

noncomputable def scalarMetric (E : ℝ) (p : I → ℝ)
    (h : I → I → ℝ) : ℝ :=
  sum4 (fun c => inverseMetric E c c * ricciMetric E p h c c)

noncomputable def einsteinMetric (E : ℝ) (p : I → ℝ)
    (h : I → I → ℝ) (a b : I) : ℝ :=
  ricciMetric E p h a b - metric E a b * scalarMetric E p h / 2

theorem ricci_trace (p : I → ℝ) (h : I → I → ℝ) :
    sum4 (fun c => sig c * conformalRicci p h c c) =
      -6 * boxH h - 6 * normP p := by
  simp [sum4, conformalRicci, boxH, normP, eta, delta, sig]
  ring

theorem einstein_from_metric (E : ℝ) (p : I → ℝ) (h : I → I → ℝ)
    (hE : E ≠ 0) (hsym : ∀ a b, h a b = h b a) (a b : I) :
    einsteinMetric E p h a b = conformalEinstein p h a b := by
  have hRic := ricciMetric_eq E p h hE hsym
  fin_cases a <;> fin_cases b <;>
    simp [einsteinMetric, scalarMetric, metric, inverseMetric, sum4,
      conformalEinstein, conformalRicci, boxH, normP, eta, delta, sig, hRic] <;>
    field_simp <;> ring

#print axioms einstein_from_metric

/- The following exact polynomial Taylor identity binds pPhi and hPhi to the
   neutral φλ.  Its cubic remainder is explicit; no smoothness premise is used. -/
def phi (b lam : ℝ) (X : I → ℝ) : ℝ :=
  -b * X 0 ^ 2 - b / 2 * (X 1 ^ 2 + X 2 ^ 2 + X 3 ^ 2) +
    lam / 2 * X 0 ^ 2 * X 1

def pPhi (b lam : ℝ) (X : I → ℝ) (a : I) : ℝ :=
  (-2*b*X 0 + lam*X 0*X 1)*delta a 0 +
  (-b*X 1 + lam/2*X 0^2)*delta a 1 -
  b*X 2*delta a 2 - b*X 3*delta a 3

def hPhi (b lam : ℝ) (X : I → ℝ) (a c : I) : ℝ :=
  (-2*b+lam*X 1)*delta a 0*delta c 0 -
  b*(delta a 1*delta c 1 + delta a 2*delta c 2 + delta a 3*delta c 3) +
  lam*X 0*(delta a 0*delta c 1 + delta a 1*delta c 0)

theorem hPhi_sym (b lam : ℝ) (X : I → ℝ) (a c : I) :
    hPhi b lam X a c = hPhi b lam X c a := by
  unfold hPhi
  ring

theorem phi_exact_taylor (b lam : ℝ) (X V : I → ℝ) :
    phi b lam (fun a => X a + V a) =
      phi b lam X + sum4 (fun a => pPhi b lam X a * V a) +
      (1/2 : ℝ)*sum4 (fun a => sum4 (fun c => hPhi b lam X a c * V a * V c)) +
      lam/2*V 0^2*V 1 := by
  simp [phi, pPhi, hPhi, sum4, delta]
  ring

#print axioms phi_exact_taylor

end CAS05Finite
