import Mathlib

namespace HTTReportA.R4A1NF

/-- Scalar contraction factor in p.p after u.u=-1, u.e=0, e.e=1. -/
theorem photon_null_factor : ((-1 : ℝ) + 2 * 0 + 1) = 0 := by
  norm_num

/-- Scalar contraction factor in -c p.u / E_gamma. -/
theorem measured_energy_factor : (-((-1 : ℝ) + 0) - 1) = 0 := by
  norm_num

/-- The Lorentz-factor identity implies unit normalisation of the boosted observer. -/
theorem boosted_observer_unit
    (gamma2 beta2 : ℝ)
    (hgamma : gamma2 * (1 - beta2) = 1) :
    gamma2 * (-1 + beta2) = -1 := by
  nlinarith

/-- A non-negative error contribution plus strictly positive regularisation is positive. -/
theorem positive_regularisation
    (q lambdaReg : ℝ)
    (hq : 0 ≤ q)
    (hlambda : 0 < lambdaReg) :
    0 < q + lambdaReg ^ 2 := by
  have hsquare : 0 < lambdaReg * lambdaReg := mul_pos hlambda hlambda
  nlinarith [hsquare]

end HTTReportA.R4A1NF
