import SkyContraction

/-!
# Canonical spatial-trace-zero representative of the finite boosted slope

The metric has signature `(-,+,+,+)`.  Its null contraction is used only on
the unit sky; no norm or convergence assertion is made here.
-/

namespace G03BCanonicalSlopeRepresentative

open scoped BigOperators Matrix
open G03BBoostedKernelMembership G03BSkyContraction

noncomputable section

def observerMetric : FourMatrix := Matrix.diagonal ![-1, 1, 1, 1]

def spatialTrace (A : FourMatrix) : Real := A 1 1 + A 2 2 + A 3 3

def slopeRepresentative (A : FourMatrix) : FourMatrix :=
  A - (spatialTrace A / 3) • observerMetric

theorem observerMetric_sky_contraction_zero (n1 n2 n3 : Real)
    (hn : n1^2 + n2^2 + n3^2 = 1) :
    (∑ i : Fin 4, skyVector n1 n2 n3 i *
      (observerMetric.mulVec (skyVector n1 n2 n3)) i) = 0 := by
  simp [skyVector, observerMetric, Matrix.mulVec, dotProduct, Fin.sum_univ_succ]
  nlinarith

theorem spatialTrace_slopeRepresentative (A : FourMatrix) :
    spatialTrace (slopeRepresentative A) = 0 := by
  simp [spatialTrace, slopeRepresentative, observerMetric]
  ring

theorem slopeRepresentative_sky_contraction
    (epsilon chi b2 b3 n1 n2 n3 : Real)
    (hn : n1^2 + n2^2 + n3^2 = 1) :
    (∑ i : Fin 4, skyVector n1 n2 n3 i *
      ((slopeRepresentative (boostedB epsilon chi b2 b3)).mulVec
        (skyVector n1 n2 n3)) i) =
      Cas03C02.familyEvaluation epsilon b2 b3 chi n1 n2 n3 := by
  rw [slopeRepresentative, Matrix.sub_mulVec, Matrix.smul_mulVec]
  simp only [Pi.sub_apply, Pi.smul_apply, smul_eq_mul, mul_sub]
  rw [Finset.sum_sub_distrib]
  rw [boostedB_sky_contraction]
  have hz :
      (∑ x : Fin 4, skyVector n1 n2 n3 x *
        (spatialTrace (boostedB epsilon chi b2 b3) / 3 *
          (observerMetric.mulVec (skyVector n1 n2 n3)) x)) = 0 := by
    calc
      _ = (spatialTrace (boostedB epsilon chi b2 b3) / 3) *
          (∑ x : Fin 4, skyVector n1 n2 n3 x *
            (observerMetric.mulVec (skyVector n1 n2 n3)) x) := by
              rw [Finset.mul_sum]
              apply Finset.sum_congr rfl
              intro x _
              ring
      _ = 0 := by rw [observerMetric_sky_contraction_zero n1 n2 n3 hn]; ring
  rw [hz]
  ring

theorem slopeRepresentative_boostedB_symmetric
    (epsilon chi b2 b3 : Real) (i j : Fin 4) :
    slopeRepresentative (boostedB epsilon chi b2 b3) i j =
      slopeRepresentative (boostedB epsilon chi b2 b3) j i := by
  simp only [slopeRepresentative, Matrix.sub_apply, Matrix.smul_apply,
    smul_eq_mul]
  have hB : boostedB epsilon chi b2 b3 i j =
      boostedB epsilon chi b2 b3 j i := by
    simp [boostedB, covOuter, mul_comm]
  have hg : observerMetric i j = observerMetric j i := by
    by_cases hij : i = j
    · subst j
      rfl
    · have hji : j ≠ i := Ne.symm hij
      simp [observerMetric, hij, hji]
  rw [hB, hg]

end
end G03BCanonicalSlopeRepresentative

#print axioms G03BCanonicalSlopeRepresentative.observerMetric_sky_contraction_zero
#print axioms G03BCanonicalSlopeRepresentative.spatialTrace_slopeRepresentative
#print axioms G03BCanonicalSlopeRepresentative.slopeRepresentative_sky_contraction
#print axioms G03BCanonicalSlopeRepresentative.slopeRepresentative_boostedB_symmetric
