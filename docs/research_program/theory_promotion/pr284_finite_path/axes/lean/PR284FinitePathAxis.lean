/-
  Exact proof for the registered PR-284 four-atom fixture only.

  This file proves no convergence or optional-stopping theorem and does not
  infer a filtration from nested sky support. It verifies the exact finite
  law, partitions, threshold, event mass, and bound frozen in the contract.
-/

import Mathlib

namespace PR284FinitePath

def centeredMean : ℚ := ((-3 : ℚ) + (-1) + 1 + 3) / 4

def secondMoment : ℚ :=
  (((-3 : ℚ) ^ 2) + ((-1 : ℚ) ^ 2) + 1 ^ 2 + 3 ^ 2) / 4

def thresholdSquared : ℚ := (6 / 5 : ℚ) ^ 2 * secondMoment

def eventMass : ℚ := (1 / 4 : ℚ) + 1 / 4

def doobBound : ℚ := 1 / (6 / 5 : ℚ) ^ 2

theorem commonTargetCentered : centeredMean = 0 := by
  norm_num [centeredMean]

theorem registeredSecondMoment : secondMoment = 5 := by
  norm_num [secondMoment]

theorem fineToMiddleConditionalExpectation :
    (((-3 : ℚ) + (-1)) / 2 = -2) ∧
    (((1 : ℚ) + 3) / 2 = 2) := by
  norm_num

theorem middleToCoarseConditionalExpectation :
    (((-2 : ℚ) + (-2) + 2 + 2) / 4 = 0) := by
  norm_num

theorem reverseTowerOnAllAtoms :
    (((-3 : ℚ) + (-1)) / 2 = -2) ∧
    (((1 : ℚ) + 3) / 2 = 2) ∧
    (((-2 : ℚ) + (-2) + 2 + 2) / 4 = 0) := by
  norm_num

theorem pathMaximumSquares :
    max ((-3 : ℚ) ^ 2) (max ((-2 : ℚ) ^ 2) 0) = 9 ∧
    max ((-1 : ℚ) ^ 2) (max ((-2 : ℚ) ^ 2) 0) = 4 ∧
    max ((1 : ℚ) ^ 2) (max ((2 : ℚ) ^ 2) 0) = 4 ∧
    max ((3 : ℚ) ^ 2) (max ((2 : ℚ) ^ 2) 0) = 9 := by
  norm_num [max_def]

theorem thresholdSquaredExact : thresholdSquared = 36 / 5 := by
  norm_num [thresholdSquared, secondMoment]

theorem inclusiveEventSelection :
    thresholdSquared ≤ 9 ∧ 4 < thresholdSquared ∧
    4 < thresholdSquared ∧ thresholdSquared ≤ 9 := by
  norm_num [thresholdSquared, secondMoment]

theorem inclusiveEventMass : eventMass = 1 / 2 := by
  norm_num [eventMass]

theorem doobBoundExact : doobBound = 25 / 36 := by
  norm_num [doobBound]

theorem eventWithinDoobBound : eventMass ≤ doobBound := by
  norm_num [eventMass, doobBound]

theorem boundSlackExact : doobBound - eventMass = 7 / 36 := by
  norm_num [doobBound, eventMass]

structure AxisProofBundle : Prop where
  centered : centeredMean = 0
  secondMomentProof : secondMoment = 5
  fineMiddle :
    (((-3 : ℚ) + (-1)) / 2 = -2) ∧ (((1 : ℚ) + 3) / 2 = 2)
  middleCoarse : (((-2 : ℚ) + (-2) + 2 + 2) / 4 = 0)
  tower :
    (((-3 : ℚ) + (-1)) / 2 = -2) ∧
    (((1 : ℚ) + 3) / 2 = 2) ∧
    (((-2 : ℚ) + (-2) + 2 + 2) / 4 = 0)
  maxima :
    max ((-3 : ℚ) ^ 2) (max ((-2 : ℚ) ^ 2) 0) = 9 ∧
    max ((-1 : ℚ) ^ 2) (max ((-2 : ℚ) ^ 2) 0) = 4 ∧
    max ((1 : ℚ) ^ 2) (max ((2 : ℚ) ^ 2) 0) = 4 ∧
    max ((3 : ℚ) ^ 2) (max ((2 : ℚ) ^ 2) 0) = 9
  threshold : thresholdSquared = 36 / 5
  selectedAtoms :
    thresholdSquared ≤ 9 ∧ 4 < thresholdSquared ∧
    4 < thresholdSquared ∧ thresholdSquared ≤ 9
  event : eventMass = 1 / 2
  bound : doobBound = 25 / 36
  bounded : eventMass ≤ doobBound
  slack : doobBound - eventMass = 7 / 36

theorem axisProofBundle : AxisProofBundle := by
  constructor
  · exact commonTargetCentered
  · exact registeredSecondMoment
  · exact fineToMiddleConditionalExpectation
  · exact middleToCoarseConditionalExpectation
  · exact reverseTowerOnAllAtoms
  · exact pathMaximumSquares
  · exact thresholdSquaredExact
  · exact inclusiveEventSelection
  · exact inclusiveEventMass
  · exact doobBoundExact
  · exact eventWithinDoobBound
  · exact boundSlackExact

#check PR284FinitePath.axisProofBundle

end PR284FinitePath
