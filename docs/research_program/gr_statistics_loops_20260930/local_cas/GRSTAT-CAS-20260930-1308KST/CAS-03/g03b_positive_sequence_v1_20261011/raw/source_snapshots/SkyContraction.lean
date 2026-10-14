import BoostedKernelMembership
import Cas03C02

/-!
# Exact finite sky contraction of the imported covariant boosted family

This is an algebraic coordinate identity for arbitrary real sky coordinates.
It does not select a norm or assert a full-sky convergence result.
-/

namespace G03BSkyContraction

open scoped BigOperators Matrix
open G03BBoostedKernelMembership

/-- The source sky vector `K = (-1, n₁, n₂, n₃)`. -/
def skyVector (n1 n2 n3 : ℝ) : FourVector := ![-1, n1, n2, n3]

/-- The covariant boosted matrix contracts against the source sky vector to
the frozen scalar family evaluation, without a sphere hypothesis. -/
theorem boostedB_sky_contraction (epsilon chi b2 b3 n1 n2 n3 : ℝ) :
    (∑ i : Fin 4, skyVector n1 n2 n3 i *
      ((boostedB epsilon chi b2 b3).mulVec (skyVector n1 n2 n3)) i) =
        Cas03C02.familyEvaluation epsilon b2 b3 chi n1 n2 n3 := by
  simp [skyVector, boostedB, covOuter, rflat, e2flat, e3flat,
    Cas03C02.familyEvaluation, Cas03C02.radialEvaluation,
    Matrix.mulVec, dotProduct, Fin.sum_univ_succ]
  ring

end G03BSkyContraction

#print axioms G03BSkyContraction.boostedB_sky_contraction
