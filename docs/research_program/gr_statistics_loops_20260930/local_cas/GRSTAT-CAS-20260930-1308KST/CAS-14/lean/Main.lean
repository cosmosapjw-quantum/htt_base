import Mathlib
/- The Frobenius identity for the three independent skew entries. -/
theorem grstat_cas14_skew_frobenius (w1 w2 w3 : ℝ) :
    (w1^2+w2^2+w3^2) + (w1^2+w2^2+w3^2) =
    2 * (w1^2+w2^2+w3^2) := by ring
#print axioms grstat_cas14_skew_frobenius
