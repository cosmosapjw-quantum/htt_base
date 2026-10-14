import SquaredCoefficientError
import FutureUnitUniqueness

/-! An interior positive sequence and its source-bound coefficient error. -/

namespace G03BPositiveSequence

open G03BBoostedKernelMembership G03BCanonicalSlopeRepresentative
  G03BSquaredCoefficientError G03BFutureUnitUniqueness Filter

noncomputable section

def epsilonSeq (epsilon0 : Real) (n : Nat) : Real := epsilon0 / ((n : Real) + 1)

noncomputable def coefficientError (epsilon chi b2 b3 : Real) : Real :=
  Real.sqrt (frobeniusSq (slopeRepresentative (boostedB epsilon chi b2 b3) -
    slopeRepresentative (boostedB epsilon 0 b2 b3)))

theorem epsilonSeq_pos (epsilon0 : Real) (he0 : 0 < epsilon0) (n : Nat) :
    0 < epsilonSeq epsilon0 n := by
  unfold epsilonSeq
  positivity

theorem epsilonSeq_tendsto_zero (epsilon0 : Real) :
    Filter.Tendsto (epsilonSeq epsilon0) Filter.atTop (nhds 0) := by
  change Filter.Tendsto (fun n : Nat => epsilon0 / ((n : Real) + 1))
    Filter.atTop (nhds 0)
  simpa [div_eq_mul_inv] using
    (tendsto_one_div_add_atTop_nhds_zero_nat (𝕜 := Real)).const_mul epsilon0

theorem epsilonSeq_futureUnit_iff (epsilon0 chi b2 b3 : Real)
    (he0 : 0 < epsilon0) (h2 : 0 < b2) (h3 : 0 < b3)
    (n : Nat) (v : FourVector) :
    ((boostedB (epsilonSeq epsilon0 n) chi b2 b3).mulVec v = 0 ∧ FutureUnit v) ↔
      v = uChi chi := by
  exact boostedB_futureUnit_iff (epsilonSeq epsilon0 n) chi b2 b3
    (epsilonSeq_pos epsilon0 he0 n) h2 h3 v

theorem coefficientError_tendsto_zero (epsilon0 chi b2 b3 : Real) :
    Filter.Tendsto (fun n : Nat => coefficientError (epsilonSeq epsilon0 n) chi b2 b3)
      Filter.atTop (nhds 0) := by
  let C : Real := (22/9 : Real) * Real.sinh chi^4 +
    2 * Real.sinh chi^2 * Real.cosh chi^2
  have hs : Filter.Tendsto (fun n : Nat => epsilonSeq epsilon0 n ^ 2 * C)
      Filter.atTop (nhds 0) := by
    simpa using ((epsilonSeq_tendsto_zero epsilon0).pow 2).mul_const C
  have hroot := hs.sqrt
  simpa [coefficientError, C, slopeRepresentative_difference_frobeniusSq] using hroot

theorem uChi_ne_uChi_zero (chi : Real) (hchi : 0 < chi) : uChi chi ≠ uChi 0 := by
  intro h
  have h1 : Real.sinh chi = 0 := by
    have hc := congrFun h (1 : Fin 4)
    simpa [uChi] using hc
  exact (ne_of_gt ((Real.sinh_pos_iff).2 hchi)) h1

end
end G03BPositiveSequence

#print axioms G03BPositiveSequence.epsilonSeq_pos
#print axioms G03BPositiveSequence.epsilonSeq_tendsto_zero
#print axioms G03BPositiveSequence.epsilonSeq_futureUnit_iff
#print axioms G03BPositiveSequence.coefficientError_tendsto_zero
#print axioms G03BPositiveSequence.uChi_ne_uChi_zero
