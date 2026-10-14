import Mathlib
noncomputable section

def metric00 (ν : ℝ → ℝ) (r : ℝ) : ℝ := -Real.exp (2 * ν r)
def chartMetric (ν F r θ : ℝ) (a b : Fin 4) : ℝ :=
  if a != b then 0 else
  if a = 0 then -Real.exp (2 * ν) else
  if a = 1 then F⁻¹ else
  if a = 2 then r ^ 2 else r ^ 2 * Real.sin θ ^ 2

def chartMetricCoordinateLine (ν F : ℝ → ℝ) (r θ : ℝ)
    (dir a b : Fin 4) (s : ℝ) : ℝ :=
  if dir = 1 then chartMetric (ν s) (F s) s θ a b else
  if dir = 2 then chartMetric (ν r) (F r) r s a b else
  chartMetric (ν r) (F r) r θ a b

example (ν F : ℝ → ℝ) (r θ νr : ℝ) (hν : HasDerivAt ν νr r) :
    HasDerivAt (chartMetricCoordinateLine ν F r θ 1 0 0)
      (-2 * Real.exp (2 * ν r) * νr) r := by
  change HasDerivAt (metric00 ν) (-2 * Real.exp (2 * ν r) * νr) r
  convert ((Real.hasDerivAt_exp (2 * ν r)).comp r
    ((hasDerivAt_const r (2 : ℝ)).mul hν)).neg using 1 <;>
    try { ext x; rfl } <;> ring
