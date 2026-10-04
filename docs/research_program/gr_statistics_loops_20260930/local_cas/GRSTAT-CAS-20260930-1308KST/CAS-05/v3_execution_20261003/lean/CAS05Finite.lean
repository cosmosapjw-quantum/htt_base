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
noncomputable def phi (b lam : ℝ) (X : I → ℝ) : ℝ :=
  -b * X 0 ^ 2 - b / 2 * (X 1 ^ 2 + X 2 ^ 2 + X 3 ^ 2) +
    lam / 2 * X 0 ^ 2 * X 1

noncomputable def pPhi (b lam : ℝ) (X : I → ℝ) (a : I) : ℝ :=
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

def rayX (s : ℝ) : I → ℝ := fun a => if a = 1 then s else 0
noncomputable def rayE (b s : ℝ) : ℝ := Real.exp (-b*s^2)

theorem ray_phi (b lam s : ℝ) :
    2 * phi b lam (rayX s) = -b*s^2 := by
  simp [phi, rayX]
  ring

theorem ray_metric_scale (b lam s : ℝ) :
    rayE b s = Real.exp (2*phi b lam (rayX s)) := by
  rw [ray_phi]
  rfl

noncomputable def stress (E Λ κ : ℝ) (p : I → ℝ)
    (h : I → I → ℝ) (a c : I) : ℝ :=
  (einsteinMetric E p h a c + Λ * metric E a c) / κ

theorem frame_pair (E Λ κ : ℝ) (p : I → ℝ) (h : I → I → ℝ)
    (hE : E ≠ 0) (hκ : κ ≠ 0) (hsym : ∀ a c, h a c = h c a) :
    κ * E⁻¹ * (stress E Λ κ p h 0 0 + stress E Λ κ p h 2 2) =
    E⁻¹ * (-2 * (h 0 0 + h 2 2) + 2 * (p 0^2 + p 2^2)) := by
  simp [stress, einstein_from_metric E p h hE hsym, conformalEinstein,
    metric, eta, delta, sig, boxH, normP]
  field_simp
  ring

theorem ray_frame_gap (b lam Λ κ s : ℝ) (hκ : κ ≠ 0) :
    κ * (rayE b s)⁻¹ *
      (stress (rayE b s) Λ κ (pPhi b lam (rayX s)) (hPhi b lam (rayX s)) 0 0 +
       stress (rayE b s) Λ κ (pPhi b lam (rayX s)) (hPhi b lam (rayX s)) 2 2) =
    Real.exp (b*s^2) * (6*b-2*lam*s) := by
  have hE : rayE b s ≠ 0 := Real.exp_ne_zero _
  rw [frame_pair (rayE b s) Λ κ (pPhi b lam (rayX s))
    (hPhi b lam (rayX s)) hE hκ (hPhi_sym b lam (rayX s))]
  simp [rayE, pPhi, hPhi, rayX, eta, delta, sig, Real.exp_neg]
  ring

theorem ray_lambda_zero (b Λ κ s : ℝ) (hκ : κ ≠ 0) :
    κ * (rayE b s)⁻¹ *
      (stress (rayE b s) Λ κ (pPhi b 0 (rayX s)) (hPhi b 0 (rayX s)) 0 0 +
       stress (rayE b s) Λ κ (pPhi b 0 (rayX s)) (hPhi b 0 (rayX s)) 2 2) =
    Real.exp (b*s^2) * (6*b) := by
  simpa using ray_frame_gap b 0 Λ κ s hκ

theorem ray_conditional_root (b lam : ℝ) (hlam : lam ≠ 0) :
    6*b-2*lam*(3*b/lam) = 0 := by
  field_simp
  ring

#print axioms ray_frame_gap
#print axioms ray_conditional_root

def originX : I → ℝ := fun _ => 0

theorem phi_origin (b lam : ℝ) : phi b lam originX = 0 := by
  simp [phi, originX]

theorem origin_G (b lam : ℝ) (a c : I) :
    einsteinMetric 1 (pPhi b lam originX) (hPhi b lam originX) a c =
      (if a = 0 ∧ c = 0 then 6*b else 0) := by
  rw [einstein_from_metric 1 (pPhi b lam originX) (hPhi b lam originX)
    (by norm_num) (hPhi_sym b lam originX)]
  fin_cases a <;> fin_cases c <;>
    simp [conformalEinstein, pPhi, hPhi, originX, boxH, normP,
      sum4, eta, delta, sig] <;> ring

theorem origin_stress00 (b lam Λ κ : ℝ) (hκ : κ ≠ 0) :
    stress 1 Λ κ (pPhi b lam originX) (hPhi b lam originX) 0 0 =
      (6*b-Λ)/κ := by
  simp [stress, origin_G, metric, eta, delta, sig]
  ring

theorem origin_stressii (b lam Λ κ : ℝ) (hκ : κ ≠ 0)
    (i : I) (hi : i ≠ 0) :
    stress 1 Λ κ (pPhi b lam originX) (hPhi b lam originX) i i = Λ/κ := by
  simp [stress, origin_G, metric, eta, delta, sig, hi]

theorem origin_gap (b lam Λ κ : ℝ) (hκ : κ ≠ 0) :
    (6*b-Λ)/κ + Λ/κ = 6*b/κ := by
  ring

theorem origin_gap_pos (b κ : ℝ) (hb : 0 < b) (hκ : 0 < κ) :
    0 < 6*b/κ := by positivity

#print axioms origin_G
#print axioms origin_stress00
#print axioms origin_gap_pos

def jPhi (lam : ℝ) (d a c : I) : ℝ :=
  lam * (delta d 0*delta a 0*delta c 1 +
         delta d 0*delta a 1*delta c 0 +
         delta d 1*delta a 0*delta c 0)

theorem jPhi_cubic (lam : ℝ) (V : I → ℝ) :
    (1/6 : ℝ)*sum4 (fun d => sum4 (fun a =>
      sum4 (fun c => jPhi lam d a c * V d * V a * V c))) =
      lam/2*V 0^2*V 1 := by
  simp [sum4, jPhi, delta]
  ring

def dGOrigin (lam : ℝ) (d a c : I) : ℝ :=
  -2*jPhi lam d a c +
    2*eta a c*sum4 (fun e => sig e*jPhi lam d e e)

theorem origin_dG_full (lam : ℝ) (d a c : I) :
    dGOrigin lam d a c =
      (if d = 0 ∧ ((a = 0 ∧ c = 1) ∨ (a = 1 ∧ c = 0)) then -2*lam
       else if d = 1 ∧ a = c ∧ a ≠ 0 then -2*lam else 0) := by
  fin_cases d <;> fin_cases a <;> fin_cases c <;>
    simp [dGOrigin, jPhi, sum4, eta, delta, sig] <;> ring

#print axioms jPhi_cubic
#print axioms origin_dG_full

def scaledX (t : ℝ) (V : I → ℝ) : I → ℝ := fun a => t*V a

noncomputable def pScaled (b lam t : ℝ) (V : I → ℝ) (a : I) : ℝ :=
  (-2*b*V 0 + lam*t*V 0*V 1)*delta a 0 +
  (-b*V 1 + lam/2*t*V 0^2)*delta a 1 -
  b*V 2*delta a 2 - b*V 3*delta a 3

theorem pPhi_scaled (b lam t : ℝ) (V : I → ℝ) (a : I) :
    pPhi b lam (scaledX t V) a = t*pScaled b lam t V a := by
  fin_cases a <;> simp [pPhi, pScaled, scaledX, delta] <;> ring

theorem origin_G_exact_first_jet (b lam t : ℝ) (V : I → ℝ)
    (a c : I) :
    conformalEinstein (pPhi b lam (scaledX t V))
      (hPhi b lam (scaledX t V)) a c =
    conformalEinstein (pPhi b lam originX) (hPhi b lam originX) a c +
      t*sum4 (fun d => dGOrigin lam d a c * V d) +
      t^2*(2*pScaled b lam t V a*pScaled b lam t V c +
           eta a c*normP (pScaled b lam t V)) := by
  fin_cases a <;> fin_cases c <;>
    simp [conformalEinstein, pPhi, pScaled, hPhi, scaledX, originX,
      dGOrigin, jPhi, boxH, normP, sum4, eta, delta, sig] <;> ring

#print axioms origin_G_exact_first_jet

theorem dMetric_origin_zero (b lam E : ℝ) (mu a c : I) :
    dMetric E (pPhi b lam originX) mu a c = 0 := by
  fin_cases mu <;> simp [dMetric, pPhi, originX, delta]

noncomputable def dStressOrigin (b lam Λ κ : ℝ) (mu a c : I) : ℝ :=
  (dGOrigin lam mu a c + Λ*dMetric 1 (pPhi b lam originX) mu a c)/κ

theorem dStressOrigin_eq (b lam Λ κ : ℝ) (mu a c : I) :
    dStressOrigin b lam Λ κ mu a c = dGOrigin lam mu a c/κ := by
  simp [dStressOrigin, dMetric_origin_zero]

noncomputable def eigenvectorJet (b lam : ℝ) (mu a : I) : ℝ :=
  if a = 0 then 0 else lam/(3*b)*delta mu 0*delta a 1

theorem eigenvector_normalization_jet (b lam : ℝ) (mu : I) :
    eigenvectorJet b lam mu 0 = 0 := by simp [eigenvectorJet]

theorem eigenvector_differentiated_equation
    (b lam Λ κ : ℝ) (hb : 0 < b) (hκ : 0 < κ)
    (mu i : I) (hi : i ≠ 0) :
    dStressOrigin b lam Λ κ mu i 0 +
      ((6*b-Λ)/κ + Λ/κ)*eigenvectorJet b lam mu i = 0 := by
  fin_cases mu <;> fin_cases i <;>
    simp_all [dStressOrigin_eq, origin_dG_full, eigenvectorJet, delta] <;>
    field_simp <;> ring

theorem origin_acceleration (b lam c : ℝ) (hb : 0 < b) :
    c^2*eigenvectorJet b lam 0 1 = c^2*lam/(3*b) := by
  simp [eigenvectorJet, delta]
  ring

theorem other_eigenvector_rates_zero (b lam : ℝ) (mu a : I)
    (h : ¬ (mu = 0 ∧ a = 1)) : eigenvectorJet b lam mu a = 0 := by
  fin_cases mu <;> fin_cases a <;> simp_all [eigenvectorJet, delta]

theorem density_first_jet_zero (b lam Λ κ : ℝ) (mu : I) :
    dStressOrigin b lam Λ κ mu 0 0 = 0 := by
  fin_cases mu <;> simp [dStressOrigin_eq, origin_dG_full]

theorem pressure_first_jet (b lam Λ κ : ℝ) (i : I) (hi : i ≠ 0) :
    dStressOrigin b lam Λ κ 1 i i = -2*lam/κ := by
  fin_cases i <;> simp_all [dStressOrigin_eq, origin_dG_full]

theorem nonEOS_pressure_gradient (b lam Λ κ : ℝ)
    (hlam : lam ≠ 0) (hκ : κ ≠ 0) :
    dStressOrigin b lam Λ κ 1 1 1 ≠ 0 := by
  rw [pressure_first_jet b lam Λ κ 1 (by norm_num)]
  exact div_ne_zero (mul_ne_zero (by norm_num) hlam) hκ

theorem origin_strictDEC (b Λ κ : ℝ)
    (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ) :
    |Λ/κ| < (6*b-Λ)/κ := by
  rw [abs_lt]
  constructor
  · have hgap : 0 < 6*b/κ := origin_gap_pos b κ hb hκ
    have heq : (6*b-Λ)/κ + Λ/κ = 6*b/κ := by ring
    linarith
  · have hdiff : 0 < (6*b-2*Λ)/κ := div_pos (by linarith) hκ
    have heq : (6*b-Λ)/κ - Λ/κ = (6*b-2*Λ)/κ := by ring
    linarith

#print axioms eigenvector_differentiated_equation
#print axioms origin_acceleration
#print axioms nonEOS_pressure_gradient
#print axioms origin_stressii
#print axioms other_eigenvector_rates_zero
#print axioms density_first_jet_zero
#print axioms origin_strictDEC
#print axioms ray_phi
#print axioms ray_metric_scale
#print axioms ray_lambda_zero

end CAS05Finite
