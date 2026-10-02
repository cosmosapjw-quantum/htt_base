import Mathlib
/- Scalar three-point Bregman cancellation; finite Gram/PSD claim remains open. -/
theorem grstat_cas11_bregman (fp fq fr gp gq p q r : ℝ) :
    (fp-fr-gp*(p-r)) - (fp-fq-gq*(p-q)) - (fq-fr-gq*(q-r))
      = (gq-gp)*(p-r) := by ring
#print axioms grstat_cas11_bregman
