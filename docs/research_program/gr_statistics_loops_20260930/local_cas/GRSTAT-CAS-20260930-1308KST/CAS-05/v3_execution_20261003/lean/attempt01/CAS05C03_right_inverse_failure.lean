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
noncomputable def formalHessian (b : ℝ) (k : I → I → ℝ)
    (a c e f : I) (X : I → ℝ) : ℝ :=
  sum4 (fun d => J b k a c d e f * X d)

theorem j2H_origin (b : ℝ) (k : I → I → ℝ) (a c e f : I) :
    formalHessian b k a c e f origin = 0 := by
  simp [formalHessian, sum4, origin]

#print axioms j2H_origin

noncomputable def cubicFromJ (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : ℝ :=
  (1/6 : ℝ)*sum4 (fun d => sum4 (fun e =>
    sum4 (fun f => J b k a c d e f * X d * X e * X f)))

theorem H_from_third_jet (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : H b k a c X = cubicFromJ b k a c X := by
  fin_cases a <;> fin_cases c <;>
    simp [H, cubicFromJ, J, J0i, Jii, Sxx, WX, r2,
      sum4, sdelta, delta, S, W] <;> ring

#print axioms H_from_third_jet

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
  ring

theorem right_inverse_M (b : ℝ) (qTarget : I → ℝ)
    (MTarget : I → I → ℝ) (hb : 0 < b) (i j : I)
    (hi : i ≠ 0) (hj : j ≠ 0) :
    M b (kRight b qTarget MTarget) i j = MTarget i j := by
  simp [M, kRight, hi, hj]
  field_simp
  ring

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
#print axioms normalizedEigenvectorJet_eq_k
#print axioms normalized_differentiated_eigen_equation

end CAS05C03
