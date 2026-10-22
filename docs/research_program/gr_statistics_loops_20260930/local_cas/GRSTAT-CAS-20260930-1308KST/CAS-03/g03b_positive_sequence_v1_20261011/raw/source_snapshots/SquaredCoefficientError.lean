import CanonicalSlopeRepresentative

/-!
# Finite squared Euclidean coefficient error

Only the finite component identity and the source-bound canonical family are
considered here.  The sum is positive Euclidean, not a Lorentz contraction.
-/

namespace G03BSquaredCoefficientError

open scoped BigOperators Matrix
open G03BBoostedKernelMembership G03BCanonicalSlopeRepresentative

noncomputable section

def frobeniusSq (A : FourMatrix) : Real :=
  ∑ i : Fin 4, ∑ j : Fin 4, (A i j)^2

theorem frobeniusSq_eq_coefficient_error_sq (A : FourMatrix)
    (hA : ∀ i j : Fin 4, A i j = A j i) :
    frobeniusSq A = (A 0 0)^2 +
      (1/2 : Real) * (∑ i : Fin 3, (-2 * A 0 i.succ)^2) +
      (∑ i : Fin 3, ∑ j : Fin 3, (A i.succ j.succ)^2) := by
  simp [frobeniusSq, Fin.sum_univ_succ]
  rw [← hA 0 1, ← hA 0 2, ← hA 0 3]
  ring

theorem slopeRepresentative_difference_frobeniusSq
    (epsilon chi b2 b3 : Real) :
    frobeniusSq (slopeRepresentative (boostedB epsilon chi b2 b3) -
      slopeRepresentative (boostedB epsilon 0 b2 b3)) =
      epsilon^2 * ((22/9 : Real) * Real.sinh chi^4 +
        2 * Real.sinh chi^2 * Real.cosh chi^2) := by
  simp [frobeniusSq, Fin.sum_univ_succ, slopeRepresentative, spatialTrace,
    observerMetric, boostedB, covOuter, rflat, e2flat, e3flat]
  have hc : Real.cosh chi ^ 2 = 1 + Real.sinh chi ^ 2 := by
    nlinarith [Real.cosh_sq_sub_sinh_sq chi]
  have h4 : Real.cosh chi ^ 4 = (1 + Real.sinh chi ^ 2)^2 := by
    calc
      _ = (Real.cosh chi ^ 2)^2 := by ring
      _ = _ := by rw [hc]
  ring_nf
  rw [h4, hc]
  ring

end
end G03BSquaredCoefficientError

#print axioms G03BSquaredCoefficientError.frobeniusSq_eq_coefficient_error_sq
#print axioms G03BSquaredCoefficientError.slopeRepresentative_difference_frobeniusSq
