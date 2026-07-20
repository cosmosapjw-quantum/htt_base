/-
PR-182 solver-free parity identities over ℚ (Lean 4 core, no mathlib).

Registry-level mechanics only: no data enters, no Bianchi family is
adjudicated, nothing here is an Einstein solution or an observable claim.
All facts are closed decidable statements over concrete rationals; the
symbolic nullspace/series computations live on the SymPy, Sage, and
Wolfram axes of the same contract.
-/

namespace Pr182Parity

abbrev Mat2 := (Rat × Rat) × (Rat × Rat)
abbrev Vec3 := Rat × Rat × Rat
abbrev Mat3 := Vec3 × Vec3 × Vec3

def mul2 (a b : Mat2) : Mat2 :=
  (((a.1.1 * b.1.1 + a.1.2 * b.2.1), (a.1.1 * b.1.2 + a.1.2 * b.2.2)),
   ((a.2.1 * b.1.1 + a.2.2 * b.2.1), (a.2.1 * b.1.2 + a.2.2 * b.2.2)))

def app2 (a : Mat2) (v : Rat × Rat) : Rat × Rat :=
  ((a.1.1 * v.1 + a.1.2 * v.2), (a.2.1 * v.1 + a.2.2 * v.2))

def id2 : Mat2 := ((1, 0), (0, 1))

/-- Reflection parity on the (E, B) doublet in the m = 0 sector. -/
def parityEB : Mat2 := ((1, 0), (0, -1))

def row (m : Mat3) (i : Nat) : Vec3 :=
  match i with
  | 0 => m.1
  | 1 => m.2.1
  | _ => m.2.2

def entry (m : Mat3) (i j : Nat) : Rat :=
  let r := row m i
  match j with
  | 0 => r.1
  | 1 => r.2.1
  | _ => r.2.2

def mul3 (a b : Mat3) : Mat3 :=
  let e := fun i j =>
    entry a i 0 * entry b 0 j + entry a i 1 * entry b 1 j +
      entry a i 2 * entry b 2 j
  (((e 0 0), (e 0 1), (e 0 2)),
   ((e 1 0), (e 1 1), (e 1 2)),
   ((e 2 0), (e 2 1), (e 2 2)))

def scale3 (c : Rat) (m : Mat3) : Mat3 :=
  let e := fun i j => c * entry m i j
  (((e 0 0), (e 0 1), (e 0 2)),
   ((e 1 0), (e 1 1), (e 1 2)),
   ((e 2 0), (e 2 1), (e 2 2)))

def neg3 (m : Mat3) : Mat3 := scale3 (-1) m

/-- Reflection diag(1, 1, -1) on the (T, E, B) triple. -/
def reflectTEB : Mat3 := ((1, 0, 0), (0, 1, 0), (0, 0, -1))

/-- Rational correlation fixture: TT=1, TE=1/4, TB=3/7, EE=2/3, EB=-2/5, BB=1/9. -/
def fixture : Mat3 :=
  ((1, 1/4, 3/7), (1/4, 2/3, -2/5), (3/7, -2/5, 1/9))

def reflectedFixture : Mat3 := mul3 (mul3 reflectTEB fixture) reflectTEB

/-- Bianchi VII_h structure tensor fixture n = diag(0, 1, 1). -/
def nVIIh : Mat3 := ((0, 0, 0), (0, 1, 0), (0, 0, 1))

/-- Improper transform Lambda = diag(-1, 1, 1), det = -1. -/
def lamImproper : Mat3 := ((-1, 0, 0), (0, 1, 0), (0, 0, 1))

def detLam : Rat := -1

def nPrime : Mat3 := scale3 detLam (mul3 (mul3 lamImproper nVIIh) lamImproper)

def aVec : Vec3 := (1/2, 0, 0)

def aDotN (m : Mat3) : Vec3 :=
  (aVec.1 * entry m 0 0 + aVec.2.1 * entry m 1 0 + aVec.2.2 * entry m 2 0,
   aVec.1 * entry m 0 1 + aVec.2.1 * entry m 1 1 + aVec.2.2 * entry m 2 1,
   aVec.1 * entry m 0 2 + aVec.2.1 * entry m 1 2 + aVec.2.2 * entry m 2 2)

/-- gamma^{-1} = sqrt(1-b^2) truncated coefficients [b^0..b^3]. -/
def gammaInvCoeffs : List Rat := [1, 0, -1/2, 0]

/-- Convolution square of the truncation, orders b^0..b^3 (must equal 1 - b^2). -/
def convSquareCoeff (n : Nat) : Rat :=
  (List.range (n + 1)).foldl
    (fun acc k =>
      acc + gammaInvCoeffs.getD k 0 * gammaInvCoeffs.getD (n - k) 0)
    0

/-- Boost kernel coefficient of b^n mu^j: convolution of gamma^{-1} with the
    geometric series in (b*mu), so it is gammaInvCoeffs[n-j] for j <= n. -/
def kernelCoeff (n j : Nat) : Rat :=
  if j > n then 0 else gammaInvCoeffs.getD (n - j) 0

def kernelOrder (n : Nat) : List Rat :=
  (List.range (n + 1)).map (kernelCoeff n)

theorem parity_involution : mul2 parityEB parityEB = id2 := by native_decide

/-- Pure-E basis vector is parity-fixed. -/
theorem pure_E_fixed : app2 parityEB (1, 0) = (1, 0) := by native_decide

/-- Pure-B basis vector is parity-odd (so a mirror-fixed axisymmetric
    doublet has zero B component). -/
theorem pure_B_odd : app2 parityEB (0, 1) = (0, -1) := by native_decide

theorem reflection_flips_TB :
    entry reflectedFixture 0 2 = -(entry fixture 0 2) := by native_decide

theorem reflection_flips_EB :
    entry reflectedFixture 1 2 = -(entry fixture 1 2) := by native_decide

theorem reflection_preserves_TT_EE_BB_TE :
    entry reflectedFixture 0 0 = entry fixture 0 0 ∧
    entry reflectedFixture 1 1 = entry fixture 1 1 ∧
    entry reflectedFixture 2 2 = entry fixture 2 2 ∧
    entry reflectedFixture 0 1 = entry fixture 0 1 := by native_decide

theorem viih_improper_flips_n : nPrime = neg3 nVIIh := by native_decide

theorem viih_constraint_both :
    aDotN nVIIh = (0, 0, 0) ∧ aDotN nPrime = (0, 0, 0) := by native_decide

theorem gamma_inv_truncation_grounded :
    convSquareCoeff 0 = 1 ∧ convSquareCoeff 1 = 0 ∧
    convSquareCoeff 2 = -1 ∧ convSquareCoeff 3 = 0 := by native_decide

theorem boost_kernel_orders :
    kernelOrder 0 = [1] ∧ kernelOrder 1 = [0, 1] ∧
    kernelOrder 2 = [-1/2, 0, 1] ∧ kernelOrder 3 = [0, -1/2, 0, 1] := by
  native_decide

end Pr182Parity
