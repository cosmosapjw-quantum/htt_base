import CAS15Frobenius
import CAS15Mixed
import CAS15Spectral

noncomputable section
namespace CAS15Synthesis
open CAS15Frobenius

/-- Both concrete encodings use exactly the same nine Frobenius coordinates. -/
theorem comm_bridge (A X : E) :
    CAS15Frobenius.comm A X = CAS15Mixed.comm (CAS15Mixed.matrixOf A) X := by
  ext ⟨i,j⟩
  simp [CAS15Frobenius.comm_apply, CAS15Mixed.comm, CAS15Mixed.leftMul,
    CAS15Mixed.rightMul, CAS15Mixed.matrixOf, Finset.sum_sub_distrib]

/-- The arbitrary-data least-squares and mixed-norm bridges are formal.
Rotated spectral coercivity is explicitly supplied here; its analytical derivation
is in SPECTRAL_NOTES.md and is not silently claimed as kernel checked. -/
theorem perturbation_given_coercivity
    (M Mhat R Rhat : E) (W What : skew) (delta epsR epsM Wstar : ℝ)
    (hdelta : 0 < delta) (hepsM : 0 ≤ epsM)
    (hR : R = CAS15Frobenius.comm M W.1)
    (hmin : ∀ X : skew,
      ‖Rhat - CAS15Frobenius.comm Mhat What.1‖ ≤
      ‖Rhat - CAS15Frobenius.comm Mhat X.1‖)
    (hnoise : ‖Rhat - R‖ ≤ epsR)
    (hM : CAS15Mixed.opNorm (CAS15Mixed.matrixOf (Mhat - M)) ≤ epsM)
    (hW : ‖W.1‖ ≤ Wstar)
    (hcoerc : ∀ X : skew, delta * ‖X.1‖ ≤ ‖CAS15Frobenius.comm Mhat X.1‖) :
    ‖(What - W).1‖ ≤ (epsR + 2 * epsM * Wstar) / delta := by
  have hcomm : ‖CAS15Frobenius.comm (Mhat - M) W.1‖ ≤ 2 * epsM * Wstar := by
    rw [comm_bridge]
    calc
      ‖CAS15Mixed.comm (CAS15Mixed.matrixOf (Mhat - M)) W.1‖ ≤
          2 * CAS15Mixed.opNorm (CAS15Mixed.matrixOf (Mhat - M)) * ‖W.1‖ :=
        CAS15Mixed.norm_flat_comm_le (Mhat - M) W.1
      _ ≤ 2 * epsM * ‖W.1‖ := by
        exact mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hM (by norm_num)) (norm_nonneg _)
      _ ≤ 2 * epsM * Wstar := mul_le_mul_of_nonneg_left hW (by positivity)
  have he : ‖CAS15Frobenius.comm Mhat (What - W).1‖ ≤ epsR + 2 * epsM * Wstar := by
    calc
      ‖CAS15Frobenius.comm Mhat (What - W).1‖ ≤
          ‖(Rhat - R) - CAS15Frobenius.comm (Mhat - M) W.1‖ :=
        skew_least_squares_perturbation_residual M Mhat R Rhat W What hR hmin
      _ ≤ ‖Rhat - R‖ + ‖CAS15Frobenius.comm (Mhat - M) W.1‖ := norm_sub_le _ _
      _ ≤ epsR + 2 * epsM * Wstar := add_le_add hnoise hcomm
  apply (le_div_iff₀ hdelta).mpr
  calc
    ‖(What - W).1‖ * delta = delta * ‖(What - W).1‖ := mul_comm _ _
    _ ≤ ‖CAS15Frobenius.comm Mhat (What - W).1‖ := hcoerc _
    _ ≤ epsR + 2 * epsM * Wstar := he

#print axioms comm_bridge
#print axioms perturbation_given_coercivity
end CAS15Synthesis
