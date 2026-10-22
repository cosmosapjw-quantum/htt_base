import FullSynthesis
import OrderedWitness

/-!
Final symmetric-input wrapper for CAS15-C03.  The spectral witness is built
from mathlib's decreasing eigenbasis, so the diagonalization and the gap used
by rotated coercivity share the same index convention as the existing ordered
matching bridge.
-/

noncomputable section
namespace CAS15WrapperIntegration

open CAS15Frobenius
open CAS15Synthesis

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ

private theorem orderedSpectrum_agrees (A : M3) (hA : A.IsSymm) :
    CAS15OrderedWitness.orderedSpectrum A hA =
      CAS15OrderedMatching.orderedSpectrum A hA := by
  rfl

/-- `full_symmetric_synthesis` with its diagonalizer and pairwise-gap inputs
constructed from the symmetric observed matrix itself. -/
theorem full_symmetric_synthesis_from_ordered_gap
    (M Mhat R Rhat : E) (W What : skew)
    (delta epsR epsM Wstar : ℝ)
    (hM : (CAS15Coercivity.mat M).IsSymm)
    (hMhat : (CAS15Coercivity.mat Mhat).IsSymm)
    (hdelta : 0 < delta)
    (hgap : delta ≤ CAS15Spectral.orderedGap
      (CAS15OrderedMatching.orderedSpectrum (CAS15Coercivity.mat Mhat) hMhat))
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
  let A : M3 := CAS15Coercivity.mat Mhat
  have hA : A.IsSymm := hMhat
  have hspectrum : CAS15OrderedWitness.orderedSpectrum A hA =
      CAS15OrderedMatching.orderedSpectrum A hA := orderedSpectrum_agrees A hA
  have hgap' : delta ≤ CAS15OrderedWitness.orderedGap A hA := by
    rw [CAS15OrderedWitness.orderedGap, orderedSpectrum_agrees A hA]
    exact hgap
  obtain ⟨Q, hQtQ, hQQt, hdiag, hpair⟩ :=
    CAS15OrderedWitness.ordered_witness A hA delta hgap'
  have hfull := CAS15FullSynthesis.full_symmetric_synthesis
    M Mhat R Rhat W What delta epsR epsM Wstar Q
      (CAS15OrderedWitness.orderedSpectrum A hA)
      hM hMhat hQtQ hQQt hdiag hdelta hpair hepsM hR hmin hnoise hpert hW
  simpa [A, hspectrum] using hfull

#print axioms full_symmetric_synthesis_from_ordered_gap

end CAS15WrapperIntegration
