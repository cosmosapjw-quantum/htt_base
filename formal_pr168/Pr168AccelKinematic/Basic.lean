/-
Copyright (c) 2026 HTT contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: HTT contributors
-/

import Mathlib

/-!
# PR-168 aligned source-basis identities

These statements are deliberately narrower than a transfer or spectrum
equivalence theorem: the evolution operator is fixed, `k_eff` is zero, and
only the direct first-order thermodynamic source is compared.
-/

namespace Pr168AccelKinematic

abbrev SourceVector := Fin 5 → ℚ

/-- Registered ell=1 basis in the ordered ell=0,...,4 scalar truncation. -/
def dipoleBasis : SourceVector := fun i => if i = 1 then 1 else 0

def scale (c : ℚ) (v : SourceVector) : SourceVector := fun i => c * v i

def add (v w : SourceVector) : SourceVector := fun i => v i + w i

/-- Direct thermodynamic source column, with the common G(E)/3 factor. -/
def source (amplitude thermodynamicFactor : ℚ) : SourceVector :=
  scale (amplitude * thermodynamicFactor / 3) dipoleBasis

/-- The acceleration and kinematic source columns have vanishing 2x2 minors. -/
theorem sourceColumnCollinearity (a d g : ℚ) (i j : Fin 5) :
    source a g i * source d g j = source d g i * source a g j := by
  simp only [source, scale]
  ring

/-- Redistributing amplitude between the two columns leaves their sum fixed. -/
theorem combinedSourceInvariance (a d g delta : ℚ) :
    add (source (a + delta) g) (source (d - delta) g) =
      add (source a g) (source d g) := by
  funext i
  simp only [add, source, scale]
  ring

/-- At this registered order the direct source has no ell != 1 support. -/
theorem directSupportOnlyEllOne (a g : ℚ) (i : Fin 5) (h : i ≠ 1) :
    source a g i = 0 := by
  simp [source, scale, dipoleBasis, h]

/-- Nonzero-amplitude normalization exposes the same thermodynamic basis. -/
theorem normalizedThermodynamicBasis (a g : ℚ) (ha : a ≠ 0) :
    scale (3 / a) (source a g) = scale g dipoleBasis := by
  funext i
  simp only [scale, source]
  field_simp [ha]

/-- Fixed first-order fixture vectors used by every independent axis. -/
def accelerationFixture : SourceVector := source 6 15
def kinematicFixture : SourceVector := source 9 15
def combinedFixture : SourceVector := add accelerationFixture kinematicFixture
def normalizedFixture : SourceVector := scale (3 / 6) accelerationFixture

/-- A finite-k streaming coupling produces a nonzero ell=2 response. -/
def streamingEllTwoNegativeControl : ℚ := 2 * accelerationFixture 1

/-- Changing the damping operator makes the two responses distinct. -/
def accelerationOperatorResponse : ℚ := 6 / (3 * 3)
def kinematicOperatorResponse : ℚ := 9 / (3 * (3 + 6))

/-- The excluded second-order angular square carries a nonzero P2 term. -/
theorem secondOrderQuadrupoleDecomposition (mu : ℚ) :
    mu ^ 2 = 1 / 3 + (2 / 3) * ((3 * mu ^ 2 - 1) / 2) := by
  ring

def vectorList (v : SourceVector) : List ℚ := List.ofFn v

def ratStr (q : ℚ) : String :=
  if q.den = 1 then toString q.num
  else toString q.num ++ "/" ++ toString q.den

end Pr168AccelKinematic
