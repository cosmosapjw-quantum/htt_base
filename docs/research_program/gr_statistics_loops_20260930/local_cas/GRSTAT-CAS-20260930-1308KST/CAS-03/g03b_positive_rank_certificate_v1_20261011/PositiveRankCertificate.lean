import Mathlib
import Cas03C02

/-!
# Positive-diagonal rank certificate for CAS-03-C02

This finite-dimensional result only specializes the frozen C02 diagonal-kernel
count to strictly positive diagonal entries.  It neither extends the frozen C02
source nor establishes the broader G03-B countersequence or any scientific claim.
-/

namespace Cas03PositiveRankCertificate

theorem positive_diagonal_kernel_zero
    (epsilon b2 b3 : Real) (he : 0 < epsilon) (h2 : 0 < b2) (h3 : 0 < b3) :
    Module.finrank Real (LinearMap.ker (Cas03C02.restAction epsilon b2 b3)) = 0 := by
  rw [Cas03C02.kernel_finrank_eq_zeroCount]
  have he0 : epsilon ≠ 0 := ne_of_gt he
  have h20 : b2 ≠ 0 := ne_of_gt h2
  have h30 : b3 ≠ 0 := ne_of_gt h3
  unfold Cas03C02.zeroCount
  rw [Fintype.card_eq_zero_iff]
  constructor
  rintro ⟨i, hi⟩
  fin_cases i
  · exact he0 (by simpa [Cas03C02.restCoefficients] using hi)
  · exact h20 (by simpa [Cas03C02.restCoefficients] using hi)
  · exact h30 (by simpa [Cas03C02.restCoefficients] using hi)

#print axioms positive_diagonal_kernel_zero

end Cas03PositiveRankCertificate
