import Mathlib.LinearAlgebra.Matrix.PosDef

namespace Egs3V8Mathlib.ReportAConvention

/-- Scalar contraction in `p.p` after `u.u=-1`, `u.e=0`, and `e.e=1`. -/
theorem photon_null_decomposition :
    ((-1 : ℝ) + 2 * 0 + 1) = 0 := by
  norm_num

/-- Scalar contraction in `-c p.u / E_gamma`. -/
theorem observer_measured_photon_energy :
    (-((-1 : ℝ) + 0) - 1) = 0 := by
  norm_num

/-- The Lorentz-factor identity gives unit normalization of the boosted observer. -/
theorem boosted_observer_unit_timelike
    (gamma2 beta2 : ℝ)
    (hgamma : gamma2 * (1 - beta2) = 1) :
    gamma2 * (-1 + beta2) = -1 := by
  nlinarith

/-- Strictly positive identity regularization upgrades a PSD matrix to a PD matrix. -/
theorem regularized_error_envelope_posDef
    {n : Type*}
    [DecidableEq n]
    (P : Matrix n n ℝ)
    (hP : Matrix.PosSemidef P)
    (lambdaReg : ℝ)
    (hlambda : 0 < lambdaReg) :
    Matrix.PosDef (P + (lambdaReg ^ 2) • (1 : Matrix n n ℝ)) := by
  have hOne : Matrix.PosDef (1 : Matrix n n ℝ) := Matrix.PosDef.one
  have hSquare : 0 < lambdaReg ^ 2 := by
    positivity
  have hRegularizer :
      Matrix.PosDef ((lambdaReg ^ 2) • (1 : Matrix n n ℝ)) :=
    Matrix.PosDef.smul hOne hSquare
  exact Matrix.PosDef.posSemidef_add hP hRegularizer

end Egs3V8Mathlib.ReportAConvention
