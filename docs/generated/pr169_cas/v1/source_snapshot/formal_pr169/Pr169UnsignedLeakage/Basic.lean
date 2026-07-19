/-
Copyright (c) 2026 HTT contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: HTT contributors
-/

import Mathlib

/-!
# PR-169 exact rational unsigned comparator leakage

These are comparator-carrier theorems only. They do not construct an
Einstein-matter solution or identify a Bianchi family.
-/

namespace Pr169UnsignedLeakage

def xC (sigma2 v2 omegaTilt deltaOmegaK : ℚ) : ℚ :=
  sigma2 - v2 + omegaTilt + deltaOmegaK

def mUnsigned (sigma2 v2 omegaTilt deltaOmegaK : ℚ) : ℚ :=
  sigma2 + v2 + omegaTilt + |deltaOmegaK|

/-- Four component caps certify the full 4B upper bound. -/
theorem fullCeilingUpperBound
    (B sigma2 v2 omegaTilt deltaOmegaK : ℚ)
    (hs0 : 0 ≤ sigma2) (hv0 : 0 ≤ v2) (ht0 : 0 ≤ omegaTilt)
    (hs : sigma2 ≤ B) (hv : v2 ≤ B) (ht : omegaTilt ≤ B)
    (hd : |deltaOmegaK| ≤ B) :
    mUnsigned sigma2 v2 omegaTilt deltaOmegaK ≤ 4 * B := by
  unfold mUnsigned
  linarith

/-- The full point (B,B,B,-B) cancels and attains 4B for B>=0. -/
theorem fullCeilingAttained (B : ℚ) (hB : 0 ≤ B) :
    xC B B B (-B) = 0 ∧ mUnsigned B B B (-B) = 4 * B := by
  constructor
  · unfold xC
    ring
  · unfold mUnsigned
    rw [abs_of_nonpos (neg_nonpos.mpr hB)]
    ring

/-- On the registered shear-vorticity slice the cap gives 2B. -/
theorem sliceCeilingUpperBound
    (B sigma2 v2 : ℚ) (hs0 : 0 ≤ sigma2) (hv0 : 0 ≤ v2)
    (hs : sigma2 ≤ B) (hv : v2 ≤ B) (hx : xC sigma2 v2 0 0 = 0) :
    mUnsigned sigma2 v2 0 0 ≤ 2 * B := by
  unfold mUnsigned
  simp only [abs_zero, add_zero]
  linarith

/-- The slice point (B,B,0,0) cancels and attains 2B. -/
theorem sliceCeilingAttained (B : ℚ) :
    xC B B 0 0 = 0 ∧ mUnsigned B B 0 0 = 2 * B := by
  constructor <;> simp [xC, mUnsigned] <;> ring

/-- Without the cap, every a>0 gives cancellation with unsigned size 2a. -/
theorem uncappedFamily (a : ℚ) :
    xC a a 0 0 = 0 ∧ mUnsigned a a 0 0 = 2 * a := by
  constructor <;> simp [xC, mUnsigned] <;> ring

inductive QuadraticSectorSymbol
  | vorticityV2
  | nilssonWeylWN2
  deriving DecidableEq

theorem nilssonSymbolDistinct :
    QuadraticSectorSymbol.nilssonWeylWN2 ≠
      QuadraticSectorSymbol.vorticityV2 := by
  decide

inductive ReceiptState
  | pass
  | fail
  | missing
  deriving DecidableEq

def missingBundle : Fin 8 → ReceiptState := fun _ => .missing

def physicalPromotion (bundle : Fin 8 → ReceiptState) : Prop :=
  ∀ i, bundle i = .pass

theorem missingPhysicalReceiptBlocksPromotion :
    ¬ physicalPromotion missingBundle := by
  intro h
  have impossible := h 0
  simp [missingBundle] at impossible

end Pr169UnsignedLeakage

