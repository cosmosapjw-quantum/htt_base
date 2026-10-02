import Mathlib
/- Algebraic rest-frame acceleration scaling, not a complete stress-conservation derivation. -/
theorem grstat_cas04_accel_scale (c dp ep : ℝ) (h : ep ≠ 0) :
    -c * (c * dp / ep) = -(c^2 * dp / ep) := by ring
#print axioms grstat_cas04_accel_scale
