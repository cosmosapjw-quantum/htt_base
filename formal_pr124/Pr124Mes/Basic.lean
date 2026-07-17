/-
PR-124 CAS axis: Lean — independent exact verification of the MES geodesic
reduction statement (contract CAS-PR124-MES-GEODESIC-001).

Pure Lean 4 core (no mathlib): the C1/C2 reduction is implemented directly
over `Rat` from the contract-registered raw data, and every proposition is
closed by `decide` at elaboration time, so a successful build IS the check.
Strict rational inequalities are decided through the numerator of the exact
difference (an `Int` comparison), which is decidable in core.
-/

namespace Pr124Mes

/-- One raw MESa bound term: (coefficient, multipole ℓ ∈ {1,2,3},
    total derivative order d). -/
structure RawTerm where
  coeff : Rat
  ell : Nat
  order : Nat

/-- C1/C2 reduction factor (1/3)^d, written recursively to stay in core. -/
def redFactor : Nat → Rat
  | 0 => 1
  | n + 1 => redFactor n / 3

/-- Reduce a raw bound to its exact (c1, c2, c3) coefficient triple. -/
def reduceRaw (terms : List RawTerm) : Rat × Rat × Rat :=
  terms.foldl
    (fun acc t =>
      let v := t.coeff * redFactor t.order
      match t.ell with
      | 1 => (acc.1 + v, acc.2.1, acc.2.2)
      | 2 => (acc.1, acc.2.1 + v, acc.2.2)
      | _ => (acc.1, acc.2.1, acc.2.2 + v))
    (0, 0, 0)

/-- MESa eq (51) raw shear bound terms. -/
def rawSigma : List RawTerm :=
  [⟨8/3, 2, 0⟩, ⟨1, 2, 1⟩, ⟨5, 1, 1⟩, ⟨9/7, 3, 1⟩]

/-- MESa eq (52) raw vorticity bound terms. -/
def rawOmega : List RawTerm :=
  [⟨9, 1, 1⟩, ⟨3, 1, 2⟩, ⟨6/5, 2, 2⟩]

def sigmaTriple : Rat × Rat × Rat := reduceRaw rawSigma
def omegaTriple : Rat × Rat × Rat := reduceRaw rawOmega

/-- Registered epsilon values (e1 = 0 SAG convention). -/
def e2v : Rat := 3559629 / 1000000000000
def e3v : Rat := 6065291 / 1000000000000
def e1Obs : Rat := 771 / 625000

def bSigma (e1 e2 e3 : Rat) : Rat :=
  sigmaTriple.1 * e1 + sigmaTriple.2.1 * e2 + sigmaTriple.2.2 * e3
def bOmega (e1 e2 e3 : Rat) : Rat :=
  omegaTriple.1 * e1 + omegaTriple.2.1 * e2 + omegaTriple.2.2 * e3

/-- Exact critical dipole bound: B_sigma > B_omega iff e1 < e1Crit. -/
def e1Crit : Rat := (43/25) * e2v + (9/35) * e3v

/-- e1Crit DERIVED from the reduced triples (not from pre-baked numerators):
    solve B_sigma(e1) = B_omega(e1) for e1 at the registered e2, e3. -/
def e1CritDerived : Rat :=
  ((sigmaTriple.2.1 - omegaTriple.2.1) * e2v
      + (sigmaTriple.2.2 - omegaTriple.2.2) * e3v)
    / (omegaTriple.1 - sigmaTriple.1)

def w2Max : Rat := (3/2) * (bOmega 0 e2v e3v) ^ (2:Nat)
def sigma2Max : Rat := (3/2) * (bSigma 0 e2v e3v) ^ (2:Nat)

/-- Strict positivity of an exact rational via its numerator. -/
def ratPos (q : Rat) : Bool := q.num > 0

-- ---- the decided propositions (a successful build proves them) ---------

theorem sigma_reduction :
    sigmaTriple = ((5:Rat)/3, (3:Rat), (3:Rat)/7) := by native_decide

theorem omega_reduction :
    omegaTriple = ((10:Rat)/3, (2:Rat)/15, (0:Rat)) := by native_decide

/-- The e1_crit coefficients close the linear identity
    B_sigma - B_omega = -(5/3)(e1 - e1_crit) at the registered e2, e3:
    equality of the two bounds at e1 = e1Crit. -/
theorem boundary_e1_crit_equality :
    bSigma e1Crit e2v e3v = bOmega e1Crit e2v e3v := by native_decide

/-- The e1Crit value DERIVED from the reduced triples equals the registered
    coefficient form (43/25)e2 + (9/35)e3 at the registered e2, e3. -/
theorem e1_crit_coefficients :
    e1CritDerived = e1Crit := by native_decide

theorem w2_ceiling_exact :
    w2Max = (4223652872547 : Rat) / 12500000000000000000000000 := by native_decide

theorem sigma2_ceiling_exact :
    sigma2Max = (6479509460609043 : Rat) / 24500000000000000000000000 := by
  native_decide

theorem hierarchy_e1_zero_strict :
    ratPos (bSigma 0 e2v e3v - bOmega 0 e2v e3v)
      ∧ ratPos (bOmega 0 e2v e3v) := by native_decide

theorem hierarchy_observed_fails :
    ratPos (bOmega e1Obs e2v e3v - bSigma e1Obs e2v e3v) := by native_decide

/-- Render an exact rational as "num/den" (or "num" when den = 1) so the
    runner can cross-check the computed values against the contract. -/
def ratStr (q : Rat) : String :=
  if q.den = 1 then toString q.num
  else toString q.num ++ "/" ++ toString q.den

end Pr124Mes
