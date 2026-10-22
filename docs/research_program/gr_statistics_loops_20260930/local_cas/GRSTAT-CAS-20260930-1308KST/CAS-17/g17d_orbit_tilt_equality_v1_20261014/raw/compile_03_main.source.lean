import C01
import PassiveTensorBridge
import Mathlib.Tactic

/-!
G17-D: orbit-normal tilt equality branch, typed independent-orbit input,
passive common coordinate change versus physical observer replacement, and the
AB-T6 calibration operational witness.

Imports the accepted CAS17-C01 (`C01.lean`, sha256 934e6a96…09de) and CAS17-C04
(`PassiveTensorBridge.lean`, sha256 49f37140…a8fb) unchanged. Signature (-,+,+,+),
orthonormal coordinates, one event. Orbit generators are a TYPED INPUT: nothing
here infers an orbit or a Bianchi identification. The u/N tilt is never replaced
by a coordinate tilt or by a u/o tilt. Calibration availability is recorded data,
not a theorem.
-/

namespace G17D
open CAS17C01

noncomputable section

/-! ## T1 equality branch -/

theorem vec_ext {v w : Vec} (ht : v.t = w.t) (hx : v.x = w.x) (hy : v.y = w.y)
    (hz : v.z = w.z) : v = w := by
  cases v; cases w; simp_all

/-- Reverse Lorentz Cauchy-Schwarz equality case: a null vector Lorentz-orthogonal
to a future unit timelike vector is zero. -/
theorem null_orthogonal_future_eq_zero (r N : Vec) (hN : FutureUnit N)
    (hrN : lorentz r N = 0) (hrr : lorentz r r = 0) : r = ⟨0, 0, 0, 0⟩ := by
  obtain ⟨hNt, hNn⟩ := hN
  have hcs := spatial_cauchy r N
  have hrs : spatial r N = r.t * N.t := by
    dsimp [lorentz, spatial] at hrN ⊢; linarith
  have hrr' : spatial r r = r.t ^ 2 := by
    dsimp [lorentz, spatial] at hrr ⊢; linarith
  have hNN : spatial N N = N.t ^ 2 - 1 := by
    dsimp [lorentz, spatial] at hNn ⊢; linarith
  rw [hrs, hrr', hNN] at hcs
  have ht2 : r.t ^ 2 ≤ 0 := by nlinarith
  have ht : r.t = 0 := by nlinarith [sq_nonneg r.t]
  have hsp : r.x ^ 2 + r.y ^ 2 + r.z ^ 2 = 0 := by
    have := hrr'; dsimp [spatial] at this; rw [ht] at this; nlinarith
  have hx : r.x = 0 := by nlinarith [sq_nonneg r.x, sq_nonneg r.y, sq_nonneg r.z]
  have hy : r.y = 0 := by nlinarith [sq_nonneg r.x, sq_nonneg r.y, sq_nonneg r.z]
  have hz : r.z = 0 := by nlinarith [sq_nonneg r.x, sq_nonneg r.y, sq_nonneg r.z]
  exact vec_ext ht hx hy hz

theorem gamma_self (N : Vec) (hN : FutureUnit N) : gamma N N = 1 := by
  unfold gamma; rw [hN.2]; norm_num

theorem gamma_eq_one_iff (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    gamma u N = 1 ↔ u = N := by
  constructor
  · intro hg
    have hid := relativeSpatial_identities u N hu hN
    have hrr : lorentz (relativeSpatial u N) (relativeSpatial u N) = 0 := by
      rw [hid.2, hg]; norm_num
    have h0 := null_orthogonal_future_eq_zero _ N hN hid.1 hrr
    have ht := congrArg Vec.t h0
    have hx := congrArg Vec.x h0
    have hy := congrArg Vec.y h0
    have hz := congrArg Vec.z h0
    simp only [relativeSpatial, hg, one_mul] at ht hx hy hz
    exact vec_ext (by linarith) (by linarith) (by linarith) (by linarith)
  · rintro rfl; exact gamma_self u hu

theorem betaSq_eq_zero_iff (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    betaSq u N = 0 ↔ u = N := by
  have hg := gamma_ge_one u N hu hN
  have hgpos : 0 < gamma u N := by linarith
  have hr := (relativeSpatial_identities u N hu hN).2
  have hsq : gamma u N ^ 2 ≠ 0 := pow_ne_zero 2 (ne_of_gt hgpos)
  rw [← gamma_eq_one_iff u N hu hN]
  unfold betaSq
  rw [hr, div_eq_zero_iff]
  constructor
  · rintro (h | h)
    · nlinarith
    · exact absurd h hsq
  · intro h; left; rw [h]; norm_num

theorem beta_eq_zero_iff (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N) :
    beta u N = 0 ↔ u = N := by
  have hb := beta_formula u N hu hN
  unfold beta
  rw [Real.sqrt_eq_zero hb.2.1]
  exact betaSq_eq_zero_iff u N hu hN

theorem betaSq_pos_of_ne (u N : Vec) (hu : FutureUnit u) (hN : FutureUnit N)
    (h : u ≠ N) : 0 < betaSq u N := by
  have hb := beta_formula u N hu hN
  rcases lt_or_eq_of_le hb.2.1 with hlt | heq
  · exact hlt
  · exact absurd ((betaSq_eq_zero_iff u N hu hN).1 heq.symm) h

/-- Equality branch for the C01-constructed orbit normal. -/
theorem orbit_tilt_zero_iff (a b c u : Vec) (hG : (gram a b c).PosDef)
    (hu : FutureUnit u) :
    (gamma u (normal a b c) = 1 ↔ u = normal a b c) ∧
    (betaSq u (normal a b c) = 0 ↔ u = normal a b c) ∧
    (beta u (normal a b c) = 0 ↔ u = normal a b c) := by
  have hn := normal_future_unit a b c hG
  exact ⟨gamma_eq_one_iff u _ hu hn, betaSq_eq_zero_iff u _ hu hn,
    beta_eq_zero_iff u _ hu hn⟩

/-- Negative control: drop the future condition on `u` (keep the unit norm) and the
equivalence fails: `u = -N` has zero `betaSq` but `u ≠ N`. -/
theorem past_branch_counterexample :
    ∃ u N : Vec, FutureUnit N ∧ lorentz u u = -1 ∧ betaSq u N = 0 ∧ u ≠ N := by
  refine ⟨⟨-1, 0, 0, 0⟩, ⟨1, 0, 0, 0⟩, ⟨by norm_num, by norm_num [lorentz]⟩,
    by norm_num [lorentz], ?_, ?_⟩
  · norm_num [betaSq, relativeSpatial, gamma, lorentz]
  · intro h; have := congrArg Vec.t h; norm_num at this

/-! ## T2 typed independent-orbit input -/

/-- Independently supplied orbit generators and recovered source velocity at one
event. A typed INPUT: no orbit/Bianchi identification is inferred here. -/
structure IndependentOrbitInput where
  X1 : Vec
  X2 : Vec
  X3 : Vec
  gram_posDef : (gram X1 X2 X3).PosDef
  u : Vec
  u_future : FutureUnit u

def IndependentOrbitInput.N (I : IndependentOrbitInput) : Vec :=
  normal I.X1 I.X2 I.X3

theorem gram_posDef_spacelike (a b c : Vec) (hG : (gram a b c).PosDef) :
    0 < lorentz a a ∧ 0 < lorentz b b ∧ 0 < lorentz c c := by
  have h0 := hG.diag_pos (i := 0)
  have h1 := hG.diag_pos (i := 1)
  have h2 := hG.diag_pos (i := 2)
  simp [gram, triple] at h0 h1 h2
  exact ⟨h0, h1, h2⟩

theorem lorentz_symm (a b : Vec) : lorentz a b = lorentz b a := by
  dsimp [lorentz]; ring

theorem wedge_swap12 (a b c : Vec) :
    wedge b a c = ⟨-(wedge a b c).t, -(wedge a b c).x, -(wedge a b c).y,
      -(wedge a b c).z⟩ := by
  apply vec_ext <;> dsimp [wedge, det3] <;> ring

theorem gram_det_swap12 (a b c : Vec) : (gram b a c).det = (gram a b c).det := by
  rw [Matrix.det_fin_three, Matrix.det_fin_three]
  simp [gram, triple]
  rw [lorentz_symm b a, lorentz_symm c a, lorentz_symm c b]
  ring

/-- The future choice of the normal does not depend on the epsilon orientation
(ordering) of the supplied generators. -/
theorem normal_swap12 (a b c : Vec) (hG : (gram a b c).PosDef) :
    normal b a c = normal a b c := by
  have hd : 0 < (gram a b c).det := hG.det_pos
  have hv : lorentz (wedge a b c) (wedge a b c) < 0 := by
    rw [wedge_norm]; exact neg_neg_of_pos hd
  have ht : (wedge a b c).t ≠ 0 := by
    intro ht
    dsimp [lorentz] at hv
    rw [ht] at hv
    nlinarith [sq_nonneg (wedge a b c).x, sq_nonneg (wedge a b c).y,
      sq_nonneg (wedge a b c).z]
  have hfs : futureSign (wedge b a c) = -futureSign (wedge a b c) := by
    rw [wedge_swap12]
    unfold futureSign
    dsimp only
    rcases lt_or_gt_of_ne ht with hlt | hgt
    · rw [if_pos (by linarith), if_neg (by linarith)]; norm_num
    · rw [if_neg (by linarith), if_pos hgt]
  unfold normal
  rw [hfs, gram_det_swap12, wedge_swap12]
  apply vec_ext <;> dsimp [scale] <;> ring

theorem orbit_input_tilt (I : IndependentOrbitInput) :
    (0 < lorentz I.X1 I.X1 ∧ 0 < lorentz I.X2 I.X2 ∧ 0 < lorentz I.X3 I.X3) ∧
    FutureUnit I.N ∧
    lorentz I.N I.X1 = 0 ∧ lorentz I.N I.X2 = 0 ∧ lorentz I.N I.X3 = 0 ∧
    1 ≤ gamma I.u I.N ∧ betaSq I.u I.N = 1 - (gamma I.u I.N)⁻¹ ^ 2 ∧
    0 ≤ betaSq I.u I.N ∧ betaSq I.u I.N < 1 ∧
    (betaSq I.u I.N = 0 ↔ I.u = I.N) := by
  have hc := c01_gram_tilt_bridge I.X1 I.X2 I.X3 I.u I.gram_posDef I.u_future
  have hn := normal_future_unit I.X1 I.X2 I.X3 I.gram_posDef
  have hd : 0 < (gram I.X1 I.X2 I.X3).det := I.gram_posDef.det_pos
  have hs : Real.sqrt (gram I.X1 I.X2 I.X3).det ≠ 0 :=
    ne_of_gt (Real.sqrt_pos.mpr hd)
  have horth : ∀ X : Vec, lorentz (wedge I.X1 I.X2 I.X3) X = 0 →
      lorentz I.N X = 0 := by
    intro X hX
    have : lorentz I.N X = (futureSign (wedge I.X1 I.X2 I.X3) /
        Real.sqrt (gram I.X1 I.X2 I.X3).det) * lorentz (wedge I.X1 I.X2 I.X3) X := by
      dsimp [IndependentOrbitInput.N, normal, scale, lorentz]; ring
    rw [this, hX, mul_zero]
  exact ⟨gram_posDef_spacelike _ _ _ I.gram_posDef, hn, horth _ hc.1,
    horth _ hc.2.1, horth _ hc.2.2.1, hc.2.2.2.2.2.1, hc.2.2.2.2.2.2.2.2.1,
    hc.2.2.2.2.2.2.2.2.2.1, hc.2.2.2.2.2.2.2.2.2.2,
    betaSq_eq_zero_iff I.u I.N I.u_future hn⟩

/-! ### Explicit witnesses -/

def e0 : Vec := ⟨1, 0, 0, 0⟩
def ex : Vec := ⟨0, 1, 0, 0⟩
def ey : Vec := ⟨0, 0, 1, 0⟩
def ez : Vec := ⟨0, 0, 0, 1⟩
/-- Boosted spacelike unit generator. -/
def bx : Vec := ⟨4/3, 5/3, 0, 0⟩
def boostedU : Vec := ⟨5/3, 4/3, 0, 0⟩

theorem gram_std : gram ex ey ez = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [gram, triple, lorentz, ex, ey, ez]

theorem gram_boosted : gram bx ey ez = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [gram, triple, lorentz, bx, ey, ez] <;> norm_num

theorem e0_future : FutureUnit e0 := ⟨by norm_num [e0], by norm_num [lorentz, e0]⟩
theorem boostedU_future : FutureUnit boostedU :=
  ⟨by norm_num [boostedU], by norm_num [lorentz, boostedU]⟩

theorem normal_std : normal ex ey ez = e0 := by
  unfold normal
  rw [gram_std, Matrix.det_one, Real.sqrt_one]
  apply vec_ext <;> simp [futureSign, wedge, det3, scale, ex, ey, ez, e0]

theorem normal_boosted : normal bx ey ez = boostedU := by
  unfold normal
  rw [gram_boosted, Matrix.det_one, Real.sqrt_one]
  apply vec_ext <;> norm_num [futureSign, wedge, det3, scale, bx, ey, ez, boostedU]

def stdInput : IndependentOrbitInput :=
  ⟨ex, ey, ez, by rw [gram_std]; exact Matrix.PosDef.one, e0, e0_future⟩

def boostedInput : IndependentOrbitInput :=
  ⟨bx, ey, ez, by rw [gram_boosted]; exact Matrix.PosDef.one, e0, e0_future⟩

theorem orbit_input_nonvacuous_equality :
    ∃ I : IndependentOrbitInput, I.u = I.N ∧ betaSq I.u I.N = 0 := by
  refine ⟨stdInput, ?_, ?_⟩
  · show e0 = normal ex ey ez; rw [normal_std]
  · show betaSq e0 (normal ex ey ez) = 0
    rw [normal_std]
    exact (betaSq_eq_zero_iff e0 e0 e0_future e0_future).2 rfl

/-- TILT-BOOST negative control: the coordinate time axis `e0` (also a valid
physical observer `o`) gives tilt 0 relative to `u = e0`, while the orbit-normal
tilt u/N is nonzero. Neither may replace the u/N tilt. -/
theorem tilt_boost_negative_control :
    ∃ I : IndependentOrbitInput, ∃ o : Vec, FutureUnit o ∧
      gamma I.u I.N = 5/3 ∧ betaSq I.u I.N = 16/25 ∧
      gamma I.u o = 1 ∧ betaSq I.u o = 0 ∧ gamma I.u o ≠ gamma I.u I.N := by
  have hN : boostedInput.N = boostedU := normal_boosted
  have hg : gamma e0 boostedU = 5/3 := by norm_num [gamma, lorentz, e0, boostedU]
  refine ⟨boostedInput, e0, e0_future, ?_, ?_, ?_, ?_, ?_⟩
  · show gamma e0 boostedInput.N = 5/3; rw [hN, hg]
  · show betaSq e0 boostedInput.N = 16/25
    rw [hN, (beta_formula e0 boostedU e0_future boostedU_future).1, hg]; norm_num
  · exact gamma_self e0 e0_future
  · exact (betaSq_eq_zero_iff e0 e0 e0_future e0_future).2 rfl
  · show gamma e0 e0 ≠ gamma e0 boostedInput.N
    rw [hN, hg, gamma_self e0 e0_future]; norm_num

/-! ## T3 passive common coordinate change vs physical observer replacement -/

section Maps
variable {V : Type} [AddCommGroup V] [Module ℝ V]

/-- Metric components, source velocity, orbit normal: all fields at one event. -/
structure TiltConfig (V : Type) [AddCommGroup V] [Module ℝ V] where
  g : V →ₗ[ℝ] V →ₗ[ℝ] ℝ
  u : V
  N : V

def tilt (c : TiltConfig V) : ℝ := -(c.g c.u c.N)

/-- Passive common coordinate change: ALL fields (metric components, u, N) are
re-expressed by the same invertible linear map. -/
def passiveChange (L : V ≃ₗ[ℝ] V) (c : TiltConfig V) : TiltConfig V :=
  ⟨c.g.compl₁₂ L.symm.toLinearMap L.symm.toLinearMap, L c.u, L c.N⟩

/-- Physical observer replacement: the velocity field is replaced by a different
physical vector; metric and orbit normal are unchanged. A different map. -/
def observerReplacement (u' : V) (c : TiltConfig V) : TiltConfig V := ⟨c.g, u', c.N⟩

theorem passive_tilt_invariant (L : V ≃ₗ[ℝ] V) (c : TiltConfig V) :
    tilt (passiveChange L c) = tilt c := by
  simp [tilt, passiveChange]

/-- The two vector arguments of a type-(0,2) tensor in C04's slot convention. -/
def pairArgs (u N : V) : ∀ i : Fin 0 ⊕ Fin 2, CAS17C04.Slot V i
  | .inl j => j.elim0
  | .inr j => ![u, N] j

/-- Same invariance obtained from the accepted C04 tensor theorem, for an arbitrary
type-(0,2) tensor in place of the metric. -/
theorem tensor_tilt_invariant_C04 (L : V ≃ₗ[ℝ] V) (T : CAS17C04.Tensor V 0 2)
    (u N : V) :
    -(CAS17C04.tensorChange L T (pairArgs (L u) (L N))) = -(T (pairArgs u N)) := by
  have h : pairArgs (L u) (L N) = CAS17C04.argumentChange L (pairArgs u N) := by
    funext i
    cases i with
    | inl j => exact j.elim0
    | inr j => fin_cases j <;> rfl
  rw [h, CAS17C04.mixed_tensor_contraction_invariant]

end Maps

def minkowskiBilin : (Fin 4 → ℝ) →ₗ[ℝ] (Fin 4 → ℝ) →ₗ[ℝ] ℝ :=
  LinearMap.mk₂ ℝ CAS17C04.minkowski
    (by intros; simp [CAS17C04.minkowski]; ring)
    (by intros; simp [CAS17C04.minkowski]; ring)
    (by intros; simp [CAS17C04.minkowski]; ring)
    (by intros; simp [CAS17C04.minkowski]; ring)

def toFin (v : Vec) : Fin 4 → ℝ := ![v.t, v.x, v.y, v.z]

/-- The C01 tilt `gamma` is the generic `tilt` evaluated on Minkowski components. -/
theorem gamma_eq_tilt (u N : Vec) :
    gamma u N = tilt ⟨minkowskiBilin, toFin u, toFin N⟩ := by
  simp [gamma, tilt, minkowskiBilin, CAS17C04.minkowski, toFin, lorentz]
  ring

def obsCfg : TiltConfig (Fin 4 → ℝ) :=
  ⟨minkowskiBilin, CAS17C04.observer, CAS17C04.observer⟩

theorem observer_replacement_changes_tilt :
    ∃ (c : TiltConfig (Fin 4 → ℝ)) (u' : Fin 4 → ℝ),
      c.g = minkowskiBilin ∧ CAS17C04.minkowski c.u c.u = -1 ∧ 0 < c.u 0 ∧
      CAS17C04.minkowski u' u' = -1 ∧ 0 < u' 0 ∧
      tilt (observerReplacement u' c) ≠ tilt c := by
  refine ⟨obsCfg, CAS17C04.replacedObserver, rfl, ?_, ?_, ?_, ?_, ?_⟩ <;>
    norm_num [obsCfg, tilt, observerReplacement, minkowskiBilin, CAS17C04.minkowski,
      CAS17C04.observer, CAS17C04.replacedObserver]

theorem observer_replacement_not_passive :
    ∃ (c : TiltConfig (Fin 4 → ℝ)) (u' : Fin 4 → ℝ),
      ∀ L : (Fin 4 → ℝ) ≃ₗ[ℝ] (Fin 4 → ℝ),
        passiveChange L c ≠ observerReplacement u' c := by
  obtain ⟨c, u', -, -, -, -, -, hne⟩ := observer_replacement_changes_tilt
  refine ⟨c, u', fun L hL => hne ?_⟩
  rw [← hL, passive_tilt_invariant]

/-! ## T4 AB-T6 operational witness (recorded data, not a theorem identity) -/

inductive SupplyStatus
  | supplied
  | notSupplied
  deriving DecidableEq

structure OperationalWitness where
  abT6Calibration : SupplyStatus

/-- Actual status for this run: no calibrated metric/clock/distance input supplied. -/
def g17dOperationalWitness : OperationalWitness := ⟨.notSupplied⟩

structure G17DApplication where
  input : IndependentOrbitInput
  ops : OperationalWitness

end
end G17D
