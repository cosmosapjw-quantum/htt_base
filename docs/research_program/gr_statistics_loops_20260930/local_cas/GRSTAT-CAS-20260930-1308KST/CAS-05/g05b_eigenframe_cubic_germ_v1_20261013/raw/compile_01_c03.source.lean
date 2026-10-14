import Mathlib

set_option maxHeartbeats 3000000
set_option maxRecDepth 2048

/-! Finite cubic metric jets for CAS-05 C03.  S and W here are symmetric and
skew coefficient matrices, not kinematic shear or vorticity. -/
namespace CAS05C03

abbrev I := Fin 4
def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3
def sig (a : I) : ℝ := if a = 0 then -1 else 1
def delta (a b : I) : ℝ := if a = b then 1 else 0
def eta (a b : I) : ℝ := delta a b * sig a
def sdelta (a b : I) : ℝ := if a = 0 then 0 else delta a b

def q (b : ℝ) (k : I → I → ℝ) (i : I) : ℝ :=
  if i = 0 then 0 else -6*b*k 0 i
def M (b : ℝ) (k : I → I → ℝ) (i j : I) : ℝ :=
  if i = 0 ∨ j = 0 then 0 else -6*b*k j i
noncomputable def S (b : ℝ) (k : I → I → ℝ) (i j : I) : ℝ :=
  (M b k i j + M b k j i)/2
noncomputable def W (b : ℝ) (k : I → I → ℝ) (i j : I) : ℝ :=
  (M b k i j - M b k j i)/2

theorem S_symmetric (b : ℝ) (k : I → I → ℝ) (i j : I) :
    S b k i j = S b k j i := by
  unfold S
  ring

theorem W_skew (b : ℝ) (k : I → I → ℝ) (i j : I) :
    W b k i j = -W b k j i := by
  unfold W
  ring

def r2 (X : I → ℝ) : ℝ := X 1^2 + X 2^2 + X 3^2
noncomputable def Sxx (b : ℝ) (k : I → I → ℝ) (X : I → ℝ) : ℝ :=
  sum4 (fun i => sum4 (fun j => S b k i j * X i * X j))
noncomputable def WX (b : ℝ) (k : I → I → ℝ) (X : I → ℝ) (i : I) : ℝ :=
  sum4 (fun j => W b k i j * X j)

noncomputable def H (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : ℝ :=
  if a = 0 then
    if c = 0 then 0 else -X 0*r2 X*q b k c/2 - r2 X*WX b k X c/5
  else if c = 0 then
    -X 0*r2 X*q b k a/2 - r2 X*WX b k X a/5
  else -delta a c*X 0*Sxx b k X/2

theorem H_symmetric (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : H b k a c X = H b k c a X := by
  fin_cases a <;> fin_cases c <;>
    simp [H, delta]

theorem H00_zero (b : ℝ) (k : I → I → ℝ) (X : I → ℝ) :
    H b k 0 0 X = 0 := by simp [H]

#print axioms S_symmetric
#print axioms W_skew
#print axioms H_symmetric
#print axioms H00_zero

noncomputable def J0i (b : ℝ) (k : I → I → ℝ)
    (i d e f : I) : ℝ :=
  -q b k i*(delta d 0*sdelta e f + delta e 0*sdelta d f +
            delta f 0*sdelta d e) -
  (2/5 : ℝ)*(sdelta d e*W b k i f + sdelta d f*W b k i e +
             sdelta e f*W b k i d)

noncomputable def Jii (b : ℝ) (k : I → I → ℝ)
    (d e f : I) : ℝ :=
  -(delta d 0*S b k e f + delta e 0*S b k d f + delta f 0*S b k d e)

noncomputable def J (b : ℝ) (k : I → I → ℝ)
    (a c d e f : I) : ℝ :=
  if a = 0 then if c = 0 then 0 else J0i b k c d e f
  else if c = 0 then J0i b k a d e f
  else delta a c * Jii b k d e f

def origin : I → ℝ := fun _ => 0
noncomputable def formalFirst (b : ℝ) (k : I → I → ℝ)
    (a c d : I) (X : I → ℝ) : ℝ :=
  (1/2 : ℝ)*sum4 (fun e => sum4 (fun f =>
    J b k a c d e f * X e * X f))
noncomputable def formalHessian (b : ℝ) (k : I → I → ℝ)
    (a c e f : I) (X : I → ℝ) : ℝ :=
  sum4 (fun d => J b k a c d e f * X d)

theorem j2H_origin (b : ℝ) (k : I → I → ℝ) (a c e f : I) :
    formalHessian b k a c e f origin = 0 := by
  simp [formalHessian, sum4, origin]

theorem H_origin_zero (b : ℝ) (k : I → I → ℝ) (a c : I) :
    H b k a c origin = 0 := by
  simp [H, origin, r2, Sxx, WX, sum4]

theorem j1H_origin (b : ℝ) (k : I → I → ℝ) (a c d : I) :
    formalFirst b k a c d origin = 0 := by
  simp [formalFirst, sum4, origin]

#print axioms j2H_origin
#print axioms H_origin_zero
#print axioms j1H_origin

noncomputable def cubicFromJ (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : ℝ :=
  (1/6 : ℝ)*sum4 (fun d => sum4 (fun e =>
    sum4 (fun f => J b k a c d e f * X d * X e * X f)))

theorem H_from_third_jet (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : H b k a c X = cubicFromJ b k a c X := by
  fin_cases a <;> fin_cases c <;>
    simp [H, cubicFromJ, J, J0i, Jii, Sxx, WX, r2,
      sum4, sdelta, delta, S, W] <;> ring

theorem H_homogeneous_cubic (b t : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) :
    H b k a c (fun d => t*X d) = t^3*H b k a c X := by
  fin_cases a <;> fin_cases c <;>
    simp [H, r2, Sxx, WX, sum4, delta] <;> ring

#print axioms H_from_third_jet
#print axioms H_homogeneous_cubic

/- With g(0)=eta, dg(0)=0 and j2 H(0)=0, the change in the second
   connection jet is the metric-third-jet term below.  The quadratic
   connection terms have zero first variation at the origin. -/
noncomputable def ddGamma (Jt : I → I → I → I → I → ℝ)
    (mu nu a c e : I) : ℝ :=
  (1/2 : ℝ)*sum4 (fun r => sig a*delta a r *
    (Jt e r mu nu c + Jt c r mu nu e - Jt c e mu nu r))

noncomputable def dRicci (Jt : I → I → I → I → I → ℝ)
    (mu a c : I) : ℝ :=
  sum4 (fun e =>
    ddGamma Jt mu e e c a - ddGamma Jt mu c e e a)

noncomputable def dEinstein (Jt : I → I → I → I → I → ℝ)
    (mu a c : I) : ℝ :=
  dRicci Jt mu a c -
    eta a c/2*sum4 (fun e => sig e*dRicci Jt mu e e)

noncomputable def dG (b : ℝ) (k : I → I → ℝ)
    (mu a c : I) : ℝ := dEinstein (J b k) mu a c

theorem dG_0i (b : ℝ) (k : I → I → ℝ) (mu i : I) (hi : i ≠ 0) :
    dG b k mu 0 i =
      (if mu = 0 then q b k i else M b k i mu) := by
  fin_cases mu <;> fin_cases i <;>
    simp_all [dG, dEinstein, dRicci, ddGamma, J, J0i, Jii,
      q, M, S, W, sum4, sig, delta, eta, sdelta] <;> ring

#print axioms dG_0i

def trM (b : ℝ) (k : I → I → ℝ) : ℝ :=
  M b k 1 1 + M b k 2 2 + M b k 3 3

noncomputable def closedDG (b : ℝ) (k : I → I → ℝ)
    (mu a c : I) : ℝ :=
  if mu = 0 then
    if a = 0 then if c = 0 then trM b k else q b k c
    else if c = 0 then q b k a
    else S b k a c/2 - delta a c*trM b k/2
  else
    if a = 0 then if c = 0 then 0 else M b k c mu
    else if c = 0 then M b k a mu
    else (delta a mu*q b k c + delta c mu*q b k a)/2 -
      delta a c*q b k mu

theorem full40_first_Einstein_coefficients (b : ℝ) (k : I → I → ℝ)
    (mu a c : I) : dG b k mu a c = closedDG b k mu a c := by
  fin_cases mu <;> fin_cases a <;> fin_cases c <;>
    simp [dG, dEinstein, dRicci, ddGamma, J, J0i, Jii,
      closedDG, trM, q, M, S, W, sum4, sig, delta, eta, sdelta] <;> ring

theorem origin_bianchi_four (b : ℝ) (k : I → I → ℝ) (c : I) :
    sum4 (fun a => sig a*dG b k a a c) = 0 := by
  simp [full40_first_Einstein_coefficients, sum4]
  fin_cases c <;>
    simp [closedDG, trM, q, M, S, delta, sig] <;> ring

#print axioms full40_first_Einstein_coefficients
#print axioms origin_bianchi_four

noncomputable def kRight (b : ℝ) (qTarget : I → ℝ)
    (MTarget : I → I → ℝ) (row col : I) : ℝ :=
  if col = 0 then 0 else
    if row = 0 then -qTarget col/(6*b) else -MTarget col row/(6*b)

theorem right_inverse_q (b : ℝ) (qTarget : I → ℝ)
    (MTarget : I → I → ℝ) (hb : 0 < b) (i : I) (hi : i ≠ 0) :
    q b (kRight b qTarget MTarget) i = qTarget i := by
  simp [q, kRight, hi]
  field_simp

theorem right_inverse_M (b : ℝ) (qTarget : I → ℝ)
    (MTarget : I → I → ℝ) (hb : 0 < b) (i j : I)
    (hi : i ≠ 0) (hj : j ≠ 0) :
    M b (kRight b qTarget MTarget) i j = MTarget i j := by
  simp [M, kRight, hi, hj]
  field_simp

theorem universal_right_inverse_0i (b : ℝ) (qTarget : I → ℝ)
    (MTarget : I → I → ℝ) (hb : 0 < b) (mu i : I) (hi : i ≠ 0) :
    dG b (kRight b qTarget MTarget) mu 0 i =
      (if mu = 0 then qTarget i else MTarget i mu) := by
  rw [dG_0i b (kRight b qTarget MTarget) mu i hi]
  by_cases hmu : mu = 0
  · simp [hmu, right_inverse_q b qTarget MTarget hb i hi]
  · simp [hmu, right_inverse_M b qTarget MTarget hb i mu hi hmu]

def kBasis (row col : I) : I → I → ℝ :=
  fun r i => if r = row ∧ i = col then 1 else 0

theorem all_twelve_basis_0i (b : ℝ) (row col mu i : I)
    (hcol : col ≠ 0) (hi : i ≠ 0) :
    dG b (kBasis row col) mu 0 i =
      (if mu = row ∧ i = col then -6*b else 0) := by
  rw [dG_0i b (kBasis row col) mu i hi]
  by_cases hmu : mu = 0
  · simp [hmu, q, kBasis, hi]
  · simp [hmu, M, kBasis, hi]

theorem full40_for_each_of_twelve_basis (b : ℝ) (row col mu a c : I)
    (hcol : col ≠ 0) :
    dG b (kBasis row col) mu a c =
      closedDG b (kBasis row col) mu a c :=
  full40_first_Einstein_coefficients b (kBasis row col) mu a c

noncomputable def normalizedEigenvectorJet (b : ℝ)
    (k : I → I → ℝ) (mu a : I) : ℝ :=
  if a = 0 then 0 else -dG b k mu 0 a/(6*b)

theorem normalizedEigenvectorJet_eq_k (b : ℝ) (k : I → I → ℝ)
    (hb : 0 < b) (mu i : I) (hi : i ≠ 0) :
    normalizedEigenvectorJet b k mu i = k mu i := by
  rw [normalizedEigenvectorJet, if_neg hi, dG_0i b k mu i hi]
  fin_cases mu <;> simp [q, M, hi] <;> field_simp <;> ring

theorem normalizedEigenvectorJet_time (b : ℝ) (k : I → I → ℝ)
    (mu : I) : normalizedEigenvectorJet b k mu 0 = 0 := by
  simp [normalizedEigenvectorJet]

theorem normalized_differentiated_eigen_equation
    (b κ : ℝ) (k : I → I → ℝ) (hb : 0 < b) (hκ : 0 < κ)
    (mu i : I) (hi : i ≠ 0) :
    dG b k mu 0 i/κ + (6*b/κ)*normalizedEigenvectorJet b k mu i = 0 := by
  simp [normalizedEigenvectorJet, hi]
  field_simp
  ring

#print axioms universal_right_inverse_0i
#print axioms all_twelve_basis_0i
#print axioms full40_for_each_of_twelve_basis
#print axioms normalizedEigenvectorJet_eq_k
#print axioms normalized_differentiated_eigen_equation

/- Generic finite metric-jet product rule for the second connection jet.
   At the origin dg=0 and d(g⁻¹)=0.  Thus the background second metric
   derivative and second inverse derivative drop out of the H variation;
   the remaining g⁻¹*d³H term is ddGamma, derived below. -/
def flatInverse : I → I → ℝ := fun a r => sig a*delta a r
def zero3 : I → I → I → ℝ := fun _ _ _ => 0

noncomputable def ddGammaFromMetricJet
    (gInv : I → I → ℝ)
    (dInv : I → I → I → ℝ)
    (ddInv : I → I → I → I → ℝ)
    (dg : I → I → I → ℝ)
    (ddg : I → I → I → I → ℝ)
    (dddg : I → I → I → I → I → ℝ)
    (mu nu a c e : I) : ℝ :=
  (1/2 : ℝ)*sum4 (fun r =>
    ddInv mu nu a r*(dg c e r + dg e c r - dg r c e) +
    dInv mu a r*(ddg nu c e r + ddg nu e c r - ddg nu r c e) +
    dInv nu a r*(ddg mu c e r + ddg mu e c r - ddg mu r c e) +
    gInv a r*(dddg mu nu e r c + dddg mu nu c r e - dddg mu nu c e r))

theorem ddGamma_derived_from_metric3jet
    (ddInv ddg : I → I → I → I → ℝ)
    (Jt : I → I → I → I → I → ℝ) (mu nu a c e : I) :
    ddGammaFromMetricJet flatInverse zero3 ddInv zero3 ddg
      (fun m n x y d => Jt x y m n d) mu nu a c e =
      ddGamma Jt mu nu a c e := by
  simp [ddGammaFromMetricJet, ddGamma, flatInverse, zero3]

noncomputable def dRicciFromConnectionJet
    (Gamma0 : I → I → I → ℝ)
    (dGamma0 : I → I → I → I → ℝ)
    (ddGamma0 : I → I → I → I → I → ℝ)
    (mu a c : I) : ℝ :=
  sum4 (fun e =>
    ddGamma0 mu e e c a - ddGamma0 mu c e e a +
    sum4 (fun f =>
      dGamma0 mu e e f*Gamma0 f c a +
      Gamma0 e e f*dGamma0 mu f c a -
      dGamma0 mu e c f*Gamma0 f e a -
      Gamma0 e c f*dGamma0 mu f e a))

theorem dRicci_derived_from_connection_jet
    (dGamma0 : I → I → I → I → ℝ)
    (Jt : I → I → I → I → I → ℝ) (mu a c : I) :
    dRicciFromConnectionJet zero3 dGamma0 (ddGamma Jt) mu a c =
      dRicci Jt mu a c := by
  simp [dRicciFromConnectionJet, dRicci, zero3, sum4]

noncomputable def dEinsteinFromMetricJet
    (g0 : I → I → ℝ) (dg0 : I → I → I → ℝ)
    (inv0 : I → I → ℝ) (dinv0 : I → I → I → ℝ)
    (R0 : ℝ) (Ricci0 : I → I → ℝ)
    (dRicci0 : I → I → I → ℝ) (mu a c : I) : ℝ :=
  dRicci0 mu a c -
    (dg0 mu a c*R0 + g0 a c*
      sum4 (fun e => dinv0 mu e e*Ricci0 e e +
        inv0 e e*dRicci0 mu e e))/2

theorem dEinstein_derived_from_metric3jet
    (R0 : ℝ) (Ricci0 : I → I → ℝ)
    (Jt : I → I → I → I → I → ℝ) (mu a c : I) :
    dEinsteinFromMetricJet eta zero3 eta zero3 R0 Ricci0
      (dRicci Jt) mu a c = dEinstein Jt mu a c := by
  fin_cases a <;> fin_cases c <;>
    simp [dEinsteinFromMetricJet, dEinstein, zero3, sum4, eta, delta, sig] <;> ring

#print axioms ddGamma_derived_from_metric3jet
#print axioms dRicci_derived_from_connection_jet
#print axioms dEinstein_derived_from_metric3jet

end CAS05C03
