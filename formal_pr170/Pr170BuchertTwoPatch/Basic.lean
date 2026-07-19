/-
Copyright (c) 2026 HTT contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: HTT contributors
-/

import Mathlib

/-!
# PR-170 exact rational Buchert and two-patch scalar identities

These externally attributed scalar identities do not construct a matched
Bianchi spacetime and do not establish physical admissibility.
-/

namespace Pr170BuchertTwoPatch

def hD (w h1 h2 : ℚ) : ℚ := w * h1 + (1 - w) * h2
def varTheta (w h1 h2 : ℚ) : ℚ := 9 * w * (1 - w) * (h1 - h2) ^ 2
def meanSigmaSq (w s1 s2 : ℚ) : ℚ := w * s1 + (1 - w) * s2
def qB (w h1 h2 s1 s2 : ℚ) : ℚ :=
  (2 / 3) * varTheta w h1 h2 - 2 * meanSigmaSq w s1 s2
def omegaQ (w h1 h2 s1 s2 : ℚ) : ℚ :=
  -qB w h1 h2 s1 s2 / (6 * (hD w h1 h2) ^ 2)
def sigma2Rms (w h1 h2 s1 s2 : ℚ) : ℚ :=
  meanSigmaSq w s1 s2 / (3 * (hD w h1 h2) ^ 2)

theorem qBReduction (w h1 h2 s1 s2 : ℚ) :
    qB w h1 h2 s1 s2 =
      6 * w * (1 - w) * (h1 - h2) ^ 2 - 2 * meanSigmaSq w s1 s2 := by
  simp [qB, varTheta]
  ring

theorem generalBridgeResidual (w h1 h2 s1 s2 : ℚ)
    (h : hD w h1 h2 ≠ 0) :
    omegaQ w h1 h2 s1 s2 - sigma2Rms w h1 h2 s1 s2 =
      -varTheta w h1 h2 / (9 * (hD w h1 h2) ^ 2) := by
  simp [omegaQ, sigma2Rms, qB]
  field_simp
  ring

theorem constantExpansionBridge (w h s1 s2 : ℚ) (h0 : h ≠ 0) :
    omegaQ w h h s1 s2 = sigma2Rms w h h s1 s2 := by
  have hd : hD w h h = h := by simp [hD]; ring
  have variance : varTheta w h h = 0 := by simp [varTheta]
  have residual := generalBridgeResidual w h h s1 s2 (by simpa [hd] using h0)
  have zeroResidual :
      omegaQ w h h s1 s2 - sigma2Rms w h h s1 s2 = 0 := by
    simpa [variance] using residual
  linarith

theorem cancellationCondition (variance shear : ℚ) (h : variance = 3 * shear) :
    (2 / 3) * variance - 2 * shear = 0 := by
  rw [h]
  ring

theorem patchExchangeHD (w h1 h2 : ℚ) :
    hD w h1 h2 = hD (1 - w) h2 h1 := by
  simp [hD]
  ring

theorem patchExchangeVariance (w h1 h2 : ℚ) :
    varTheta w h1 h2 = varTheta (1 - w) h2 h1 := by
  simp [varTheta]
  ring

def qBT (variance meanSq meanMagnitude : ℚ) : ℚ :=
  (2 / 3) * variance - 2 * (meanSq - meanMagnitude ^ 2)

theorem barrowBuchertSeparation (variance meanSq meanMagnitude : ℚ) :
    qBT variance meanSq meanMagnitude =
      ((2 / 3) * variance - 2 * meanSq) + 2 * meanMagnitude ^ 2 := by
  simp [qBT]
  ring

inductive BianchiType
  | I | II | III | IV | V | VI0 | VIh | VII0 | VIIh | VIII | IX
  deriving DecidableEq, Fintype

theorem registeredTypeCount : Fintype.card BianchiType = 11 := by decide

end Pr170BuchertTwoPatch
