import Mathlib
import BoostedKernelMembership
import BoostedKernelSpan

/-! Finite-coordinate future-unit uniqueness for the explicit boosted covariant family. -/

namespace G03BFutureUnitUniqueness

open G03BBoostedKernelMembership
open G03BBoostedKernelSpan

def lorentzNormSq (v : FourVector) : Real :=
  -((v 0)^2) + (v 1)^2 + (v 2)^2 + (v 3)^2

def FutureUnit (v : FourVector) : Prop :=
  lorentzNormSq v = -1 ∧ 0 < v 0

theorem uChi_futureUnit (chi : Real) : FutureUnit (uChi chi) := by
  constructor
  · simp [lorentzNormSq, uChi]
    nlinarith [Real.cosh_sq_sub_sinh_sq chi]
  · simpa [uChi] using Real.cosh_pos chi

theorem boostedB_futureUnit_iff (epsilon chi b2 b3 : Real)
    (he : 0 < epsilon) (h2 : 0 < b2) (h3 : 0 < b3) (v : FourVector) :
    ((boostedB epsilon chi b2 b3).mulVec v = 0 ∧ FutureUnit v) ↔
      v = uChi chi := by
  constructor
  · rintro ⟨hker, hfuture⟩
    obtain ⟨t, rfl⟩ :=
      (boostedB_mulVec_eq_zero_iff epsilon chi b2 b3 he h2 h3 v).mp hker
    have hnorm : lorentzNormSq (t • uChi chi) =
        t^2 * lorentzNormSq (uChi chi) := by
      simp [lorentzNormSq, uChi, Pi.smul_apply, smul_eq_mul]
      ring
    have ht2 : t^2 = 1 := by
      rw [(uChi_futureUnit chi).1] at hnorm
      nlinarith [hfuture.1]
    have htpos : 0 < t := by
      have htime : 0 < t * Real.cosh chi := by
        simpa [uChi, Pi.smul_apply, smul_eq_mul] using hfuture.2
      nlinarith [Real.cosh_pos chi]
    have ht : t = 1 := by nlinarith
    simp [ht]
  · intro hv
    subst v
    exact ⟨boostedB_mulVec_uChi_zero epsilon chi b2 b3,
      uChi_futureUnit chi⟩

end G03BFutureUnitUniqueness

#print axioms G03BFutureUnitUniqueness.uChi_futureUnit
#print axioms G03BFutureUnitUniqueness.boostedB_futureUnit_iff
