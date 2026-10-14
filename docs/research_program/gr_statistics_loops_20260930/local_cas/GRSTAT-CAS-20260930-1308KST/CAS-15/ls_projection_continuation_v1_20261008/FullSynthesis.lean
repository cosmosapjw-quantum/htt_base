import Synthesis
import CoercivityBridge
import OrderedMatchingBridge

/-!
The final CAS15-C03 composition.  The supplied `Q` and `lamb` are an actual
real orthogonal diagonalization of the observed symmetric matrix; importantly,
the least-squares conclusion takes no coercivity or eigenvalue-matching premise.
`ordered_gap_from_input` uses mathlib's decreasing eigenvalue enumeration,
whereas `hgap` is the basis-independent pairwise lower gap needed by the
commutator proof.  No positivity of the gap lower bound from perturbation is
asserted here; division in the error theorem uses the separately observed
positive gap `hdelta` only.
-/
noncomputable section
namespace CAS15FullSynthesis

open CAS15Frobenius
open CAS15Synthesis

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ

/-- The original-input least-squares bound, with rotated coercivity derived
from an orthogonal diagonalization rather than supplied as `hcoerc`. -/
theorem perturbation_from_symmetric_input
    (M Mhat R Rhat : E) (W What : skew)
    (delta epsR epsM Wstar : ℝ) (Q : M3) (lamb : Fin 3 → ℝ)
    (hMhat : (CAS15Coercivity.mat Mhat).IsSymm)
    (hQtQ : Q.transpose * Q = 1) (hQQt : Q * Q.transpose = 1)
    (hdiag : Q.transpose * CAS15Coercivity.mat Mhat * Q = Matrix.diagonal lamb)
    (hdelta : 0 < delta)
    (hgap : ∀ i j : Fin 3, i ≠ j → delta ≤ |lamb i - lamb j|)
    (hepsM : 0 ≤ epsM)
    (hR : R = CAS15Frobenius.comm M W.1)
    (hmin : ∀ X : skew,
      ‖Rhat - CAS15Frobenius.comm Mhat What.1‖ ≤
        ‖Rhat - CAS15Frobenius.comm Mhat X.1‖)
    (hnoise : ‖Rhat - R‖ ≤ epsR)
    (hM : CAS15Mixed.opNorm (CAS15Mixed.matrixOf (Mhat - M)) ≤ epsM)
    (hW : ‖W.1‖ ≤ Wstar) :
    ‖(What - W).1‖ ≤ (epsR + 2 * epsM * Wstar) / delta := by
  apply CAS15Synthesis.perturbation_given_coercivity M Mhat R Rhat W What
    delta epsR epsM Wstar hdelta hepsM hR hmin hnoise hM hW
  intro X
  exact CAS15Coercivity.rotated_coercivity Mhat Q lamb delta hMhat hQtQ hQQt
    hdiag hdelta.le hgap X

/-- Same-index matching and the two-epsilon ordered-gap loss from the original
matrix operator-norm input.  Repeated eigenvalues are allowed. -/
theorem ordered_gap_from_input (M Mhat : E) (epsM : ℝ)
    (hM : (CAS15Coercivity.mat M).IsSymm)
    (hMhat : (CAS15Coercivity.mat Mhat).IsSymm)
    (hpert : CAS15Mixed.opNorm (CAS15Mixed.matrixOf (Mhat - M)) ≤ epsM) :
    CAS15Spectral.orderedGap
        (CAS15OrderedMatching.orderedSpectrum (CAS15Coercivity.mat M) hM) - 2 * epsM ≤
      CAS15Spectral.orderedGap
        (CAS15OrderedMatching.orderedSpectrum (CAS15Coercivity.mat Mhat) hMhat) := by
  apply CAS15OrderedMatching.matrix_ordered_gap_bound
    (CAS15Coercivity.mat M) (CAS15Coercivity.mat Mhat) hM hMhat epsM
  change ‖CAS15OrderedMatching.matrixOperator
    (CAS15Coercivity.mat Mhat - CAS15Coercivity.mat M)‖ ≤ epsM
  exact hpert

/-- The two requested conclusions from the original matrix inputs.  The first
uses an observed positive spectral gap; the second remains valid even when its
right-hand side is negative and therefore supplies no positivity by itself. -/
theorem full_symmetric_synthesis
    (M Mhat R Rhat : E) (W What : skew)
    (delta epsR epsM Wstar : ℝ) (Q : M3) (lamb : Fin 3 → ℝ)
    (hM : (CAS15Coercivity.mat M).IsSymm)
    (hMhat : (CAS15Coercivity.mat Mhat).IsSymm)
    (hQtQ : Q.transpose * Q = 1) (hQQt : Q * Q.transpose = 1)
    (hdiag : Q.transpose * CAS15Coercivity.mat Mhat * Q = Matrix.diagonal lamb)
    (hdelta : 0 < delta)
    (hgap : ∀ i j : Fin 3, i ≠ j → delta ≤ |lamb i - lamb j|)
    (hepsM : 0 ≤ epsM)
    (hR : R = CAS15Frobenius.comm M W.1)
    (hmin : ∀ X : skew,
      ‖Rhat - CAS15Frobenius.comm Mhat What.1‖ ≤
        ‖Rhat - CAS15Frobenius.comm Mhat X.1‖)
    (hnoise : ‖Rhat - R‖ ≤ epsR)
    (hpert : CAS15Mixed.opNorm (CAS15Mixed.matrixOf (Mhat - M)) ≤ epsM)
    (hW : ‖W.1‖ ≤ Wstar) :
    ‖(What - W).1‖ ≤ (epsR + 2 * epsM * Wstar) / delta ∧
    CAS15Spectral.orderedGap
        (CAS15OrderedMatching.orderedSpectrum (CAS15Coercivity.mat M) hM) - 2 * epsM ≤
      CAS15Spectral.orderedGap
        (CAS15OrderedMatching.orderedSpectrum (CAS15Coercivity.mat Mhat) hMhat) := by
  constructor
  · exact perturbation_from_symmetric_input M Mhat R Rhat W What delta epsR epsM Wstar Q lamb
      hMhat hQtQ hQQt hdiag hdelta hgap hepsM hR hmin hnoise hpert hW
  · exact ordered_gap_from_input M Mhat epsM hM hMhat hpert

#print axioms perturbation_from_symmetric_input
#print axioms ordered_gap_from_input
#print axioms full_symmetric_synthesis

end CAS15FullSynthesis
