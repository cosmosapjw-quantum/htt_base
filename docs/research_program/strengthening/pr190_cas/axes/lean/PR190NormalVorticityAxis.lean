/-
  PR-190 Lean/mathlib axis.

  The declared coordinate reduction is the homogeneous chart adapted to the
  hypersurface normal: every spatial component n_i and spatial derivative of
  the lapse is zero.  The spatial antisymmetric derivative, its dual norm,
  and W2 therefore vanish exactly.  This contradicts the registered lower
  target W2=1/25 and prevents a conjunctive sharpness promotion.
-/

import Mathlib

namespace PR190NormalVorticity

def normalSpatialCovector : Fin 3 → ℚ := fun _ => 0

def spatialDerivative : Fin 3 → Fin 3 → ℚ := fun _ _ => 0

def vorticityTwoForm (i j : Fin 3) : ℚ :=
  (spatialDerivative i j - spatialDerivative j i) / 2

def normalOmegaSquared : ℚ :=
  ∑ i : Fin 3, ∑ j : Fin 3, (vorticityTwoForm i j) ^ 2

def normalW2 : ℚ := 3 * normalOmegaSquared

def registeredLowerW2 : ℚ := 1 / 25

def registeredInteriorW2 : ℚ := 3 / 100

theorem normalSpatialVorticityZero (i j : Fin 3) :
    vorticityTwoForm i j = 0 := by
  simp [vorticityTwoForm, spatialDerivative]

theorem normalOmegaSquaredZero : normalOmegaSquared = 0 := by
  simp [normalOmegaSquared, normalSpatialVorticityZero]

theorem normalW2Zero : normalW2 = 0 := by
  simp [normalW2, normalOmegaSquaredZero]

theorem registeredLowerW2Positive : 0 < registeredLowerW2 := by
  norm_num [registeredLowerW2]

theorem lowerEndpointSameFrameContradiction :
    normalW2 ≠ registeredLowerW2 := by
  norm_num [normalW2, normalOmegaSquared, vorticityTwoForm,
    spatialDerivative, registeredLowerW2]

theorem registeredInteriorW2Positive : 0 < registeredInteriorW2 := by
  norm_num [registeredInteriorW2]

theorem interiorEndpointSameFrameContradiction :
    normalW2 ≠ registeredInteriorW2 := by
  norm_num [normalW2, normalOmegaSquared, vorticityTwoForm,
    spatialDerivative, registeredInteriorW2]

theorem refutedConstraintCannotPromote
    (constraint localClaim globalClaim : Prop)
    (hConstraint : ¬ constraint) :
    ¬ (constraint ∧ localClaim ∧ globalClaim) := by
  intro h
  exact hConstraint h.1

structure AxisProofBundle : Prop where
  normalVorticityProof : ∀ i j, vorticityTwoForm i j = 0
  normalW2Proof : normalW2 = 0
  lowerPositiveProof : 0 < registeredLowerW2
  lowerContradictionProof : normalW2 ≠ registeredLowerW2
  interiorPositiveProof : 0 < registeredInteriorW2
  interiorContradictionProof : normalW2 ≠ registeredInteriorW2
  nonpromotionProof : ∀ constraint localClaim globalClaim : Prop,
    ¬ constraint → ¬ (constraint ∧ localClaim ∧ globalClaim)

theorem axisProofBundle : AxisProofBundle := by
  constructor
  · exact normalSpatialVorticityZero
  · exact normalW2Zero
  · exact registeredLowerW2Positive
  · exact lowerEndpointSameFrameContradiction
  · exact registeredInteriorW2Positive
  · exact interiorEndpointSameFrameContradiction
  · exact refutedConstraintCannotPromote

#check PR190NormalVorticity.axisProofBundle

end PR190NormalVorticity
