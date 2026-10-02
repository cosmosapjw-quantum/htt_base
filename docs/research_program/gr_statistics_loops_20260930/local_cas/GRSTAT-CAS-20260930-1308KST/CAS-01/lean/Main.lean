import Mathlib

/- Necessary scalar contraction identities for C01. These do not prove the
   null-cone kernel or any complete CAS-01 component. -/
theorem grstat_cas01_Buu (suu guu : ℝ) (h : guu = -1) :
    suu + suu * guu = 0 := by
  rw [h]
  ring

theorem grstat_cas01_gauge (suu guu a : ℝ) (h : guu = -1) :
    (suu + a * guu) + (suu + a * guu) * guu =
      suu + suu * guu := by
  rw [h]
  ring

#print axioms grstat_cas01_Buu
#print axioms grstat_cas01_gauge
