import Mathlib
/- Polynomial idempotence for the complementary projector. -/
theorem grstat_cas08_complement_idempotent (p : ℝ) (hp : p*p=p) :
    (1-p)*(1-p)=1-p := by
  nlinarith
#print axioms grstat_cas08_complement_idempotent
