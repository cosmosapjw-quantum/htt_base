/-
P06-A (PORT-CAS-06): endpoint optical invariants of ONE physical ray under a
change of observer at the same event.

Sources (see SOURCE_RECOVERY.md): T5_WU010 local-observer response pack §1-2,
tilt_boost_loop observations_findings.md §2, prior_stats_findings.md §3.3,
CLAIMS TBO-06/TBO-07, and htt/src/common/relativistic_kinematics.py
(`endpoint_boost`, `inverse_temperature_boost`).

Reused unchanged (compiled into raw/imports):
  * PortCas01               -- boost matrix, gamma, h, four-velocity, e0
  * PassiveTensorBridge     -- CAS17C04.minkowski metric (GR-17 passive bridge)
  * EndpointScalarInvariant -- zNew, dANew, dLNew and the product identity

Model: components in the OLD observer's orthonormal frame, g = diag(-1,1,1,1),
c = 1.  The photon is ONE fixed future null vector k = E (1, -n) with n the
sourceward unit direction (T5 §1: p = (ε/c)(u - n)).  The new observer is
u' = fourVelocity β = γ(1, β).  Its tetrad components of the same k are
Binv β · k (the passive inverse of the PORT-CAS-01 boost).

Not modelled: polarization, spin-2 transfer, frequency-dependent intensity,
distinct rays, curved-spacetime propagation.  Reciprocity is a hypothesis.
-/
import Mathlib
import PortCas01
import PassiveTensorBridge
import EndpointScalarInvariant

open PortCas01 Set
open scoped Real Interval Matrix
open PORTCAS06EndpointScalarInvariant (zNew dANew dLNew endpoint_product_invariant)

namespace P06AOptics

abbrev V := Fin 4 → ℝ

/-! ## Definitions -/

/-- Metric `g = diag(-1,1,1,1)`: the reviewed GR-17 definition, reused. -/
def mink (x y : V) : ℝ := CAS17C04.minkowski x y

/-- Euclidean dot product of two 3-vectors. -/
def dot3 (a1 a2 a3 x1 x2 x3 : ℝ) : ℝ := a1 * x1 + a2 * x2 + a3 * x3

/-- Photon momentum of the ray, old-observer frame: `k = E (1, -n)`,
    `n` the sourceward direction (spatial vectors point toward sources). -/
def photon (E n1 n2 n3 : ℝ) : V := ![E, -(E * n1), -(E * n2), -(E * n3)]

/-- Energy measured by observer `u`: `E_u(k) = -g(k, u)`. -/
def energy (u k : V) : ℝ := -mink k u

/-- Source/implementation Doppler convention `D = γ (1 + β·n)`, `n` sourceward. -/
noncomputable def doppler (b1 b2 b3 n1 n2 n3 : ℝ) : ℝ :=
  gamma b1 b2 b3 * (1 + dot3 b1 b2 b3 n1 n2 n3)

/-- PORT-CAS-01 boost sending `e0` to `γ(1, β)`. -/
noncomputable def Bst (b1 b2 b3 : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  boost (gamma b1 b2 b3) (h b1 b2 b3) b1 b2 b3

/-- PORT-CAS-01 inverse boost. -/
noncomputable def Binv (b1 b2 b3 : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  boostNeg (gamma b1 b2 b3) (h b1 b2 b3) b1 b2 b3

/-- Components of a FIXED vector in the new observer's tetrad `e'_μ = Bst e_μ`. -/
noncomputable def newComp (b1 b2 b3 : ℝ) (k : V) : V := Binv b1 b2 b3 *ᵥ k

/-- Sourceward direction read off from frame components of a photon momentum. -/
noncomputable def dirOf (k : V) (i : Fin 3) : ℝ := -(k i.succ) / k 0

/-- Closed-form aberrated sourceward direction (new frame) of the ray with
    old sourceward direction `n`. -/
noncomputable def aberr (b1 b2 b3 n1 n2 n3 : ℝ) (i : Fin 3) : ℝ :=
  (![n1, n2, n3] i + gamma b1 b2 b3 * ![b1, b2, b3] i
      + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * ![b1, b2, b3] i)
    / doppler b1 b2 b3 n1 n2 n3

/-- Polar chart with axis `β̂`, speed `b`, `μ = cos θ`: Doppler factor. -/
noncomputable def D1 (b μ : ℝ) : ℝ := gamma 0 0 b * (1 + b * μ)

/-- Polar chart aberration map `μ ↦ μ'` (azimuth unchanged, see `chart_link`). -/
noncomputable def ab (b μ : ℝ) : ℝ := (μ + b) / (1 + b * μ)

/-- Area distance `d_A = sqrt(dS / dΩ)`: source screen area per observed solid angle. -/
noncomputable def areaDist (dS dΩ : ℝ) : ℝ := Real.sqrt (dS / dΩ)

/-- Redshift from source-frame emitted energy `Es` and observed energy `E`:
    `1 + z = Es / E`. -/
noncomputable def redshiftOf (Es E : ℝ) : ℝ := Es / E - 1

/-- Planck (Bose-Einstein, zero chemical potential) occupation number. -/
noncomputable def planckOcc (x : ℝ) : ℝ := 1 / (Real.exp x - 1)

/-! ## Algebraic core (re-derived; the PORT-CAS-01 version is private) -/

theorem core (x y z : ℝ) (hs : s x y z < 1) :
    0 < gamma x y z ∧ gamma x y z ^ 2 * (1 - s x y z) = 1 ∧
      h x y z * s x y z = gamma x y z - 1 := by
  have hp : 0 < 1 - s x y z := by linarith
  have hroot : 0 < Real.sqrt (1 - s x y z) := Real.sqrt_pos.2 hp
  have hroot2 : Real.sqrt (1 - s x y z) ^ 2 = 1 - s x y z := Real.sq_sqrt hp.le
  have hg : 0 < gamma x y z := by unfold gamma; positivity
  have hgsq : gamma x y z ^ 2 * (1 - s x y z) = 1 := by
    unfold gamma; field_simp; nlinarith
  have hgn : gamma x y z + 1 ≠ 0 := by positivity
  have hsquared : gamma x y z ^ 2 * s x y z = gamma x y z ^ 2 - 1 := by nlinarith [hgsq]
  have hhs : h x y z * s x y z = gamma x y z - 1 := by
    calc h x y z * s x y z = gamma x y z ^ 2 * s x y z / (gamma x y z + 1) := by
          unfold h; ring
      _ = (gamma x y z ^ 2 - 1) / (gamma x y z + 1) := by rw [hsquared]
      _ = gamma x y z - 1 := by field_simp; ring
  exact ⟨hg, hgsq, hhs⟩

theorem s_neg (x y z : ℝ) : s (-x) (-y) (-z) = s x y z := by unfold s; ring

theorem gamma_neg (x y z : ℝ) : gamma (-x) (-y) (-z) = gamma x y z := by
  unfold gamma; rw [s_neg]

theorem h_neg (x y z : ℝ) : h (-x) (-y) (-z) = h x y z := by
  unfold h; rw [gamma_neg]

theorem dot_bound (b1 b2 b3 n1 n2 n3 : ℝ) :
    dot3 b1 b2 b3 n1 n2 n3 ^ 2 ≤ s b1 b2 b3 * s n1 n2 n3 := by
  have hid : s b1 b2 b3 * s n1 n2 n3 - dot3 b1 b2 b3 n1 n2 n3 ^ 2 =
      (b1 * n2 - b2 * n1) ^ 2 + (b1 * n3 - b3 * n1) ^ 2 + (b2 * n3 - b3 * n2) ^ 2 := by
    unfold s dot3; ring
  nlinarith [sq_nonneg (b1 * n2 - b2 * n1), sq_nonneg (b1 * n3 - b3 * n1),
    sq_nonneg (b2 * n3 - b3 * n2)]

theorem dot_sq_lt_one {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    dot3 b1 b2 b3 n1 n2 n3 ^ 2 < 1 := by
  have := dot_bound b1 b2 b3 n1 n2 n3
  rw [hn, mul_one] at this
  linarith

theorem one_add_dot_pos {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    0 < 1 + dot3 b1 b2 b3 n1 n2 n3 := by
  have := dot_sq_lt_one hb hn
  nlinarith

theorem one_sub_dot_pos {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    0 < 1 - dot3 b1 b2 b3 n1 n2 n3 := by
  have := dot_sq_lt_one hb hn
  nlinarith

/-! ## T1: null tangent, measured energies, Doppler factor, frame change -/

theorem photon_null (E n1 n2 n3 : ℝ) (hn : s n1 n2 n3 = 1) :
    mink (photon E n1 n2 n3) (photon E n1 n2 n3) = 0 := by
  unfold s at hn
  simp [mink, CAS17C04.minkowski, photon]
  linear_combination E ^ 2 * hn

theorem photon_future {E : ℝ} (hE : 0 < E) (n1 n2 n3 : ℝ) : 0 < photon E n1 n2 n3 0 := by
  simpa [photon] using hE

theorem energy_e0 (k : V) : energy e0 k = k 0 := by
  simp [energy, mink, CAS17C04.minkowski, e0]

theorem energy_old (E n1 n2 n3 : ℝ) : energy e0 (photon E n1 n2 n3) = E := by
  rw [energy_e0]; simp [photon]

theorem energy_new (b1 b2 b3 E n1 n2 n3 : ℝ) :
    energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) = doppler b1 b2 b3 n1 n2 n3 * E := by
  rw [fourVelocity_components]
  simp [energy, mink, CAS17C04.minkowski, photon, doppler, dot3]
  ring

theorem doppler_pos {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    0 < doppler b1 b2 b3 n1 n2 n3 :=
  mul_pos (core b1 b2 b3 hb).1 (one_add_dot_pos hb hn)

/-- Doppler factor is the ratio of the two observers' energies of the same ray,
    independent of the positive scale `E` of the null tangent. -/
theorem doppler_eq_energy_ratio (b1 b2 b3 n1 n2 n3 : ℝ) {E : ℝ} (hE : 0 < E) :
    energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) / energy e0 (photon E n1 n2 n3) =
      doppler b1 b2 b3 n1 n2 n3 := by
  rw [energy_new, energy_old]; field_simp

theorem mink_eq (x y : V) : mink x y = x ⬝ᵥ (eta *ᵥ y) := by
  simp [mink, CAS17C04.minkowski, dotProduct, Matrix.mulVec, Fin.sum_univ_four, eta]

theorem mink_boost {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (x y : V) :
    mink (Bst b1 b2 b3 *ᵥ x) (Bst b1 b2 b3 *ᵥ y) = mink x y := by
  have hM := metric_identity b1 b2 b3 hb
  rw [mink_eq, mink_eq, Matrix.mulVec_mulVec, Matrix.dotProduct_mulVec,
    ← Matrix.vecMul_transpose (Bst b1 b2 b3) x, Matrix.vecMul_vecMul, ← Matrix.mul_assoc]
  unfold Bst
  rw [hM, ← Matrix.dotProduct_mulVec]

theorem Binv_eq (b1 b2 b3 : ℝ) : Binv b1 b2 b3 = Bst (-b1) (-b2) (-b3) := by
  simp only [Binv, Bst, boostNeg, gamma_neg, h_neg]

theorem Bst_mul_Binv {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Bst b1 b2 b3 * Binv b1 b2 b3 = 1 := inverse_identity b1 b2 b3 hb

theorem Binv_mul_Bst {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Binv b1 b2 b3 * Bst b1 b2 b3 = 1 := by
  have h1 := inverse_identity (-b1) (-b2) (-b3) (by rw [s_neg]; exact hb)
  simp only [gamma_neg, h_neg, boostNeg, neg_neg] at h1
  simpa [Binv, Bst, boostNeg] using h1

theorem mink_newComp {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (x y : V) :
    mink (newComp b1 b2 b3 x) (newComp b1 b2 b3 y) = mink x y := by
  unfold newComp; rw [Binv_eq]; exact mink_boost (by rw [s_neg]; exact hb) x y

/-- Passive frame change: measured energy is the same contraction in either frame. -/
theorem energy_frame_independent {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (u k : V) :
    energy (newComp b1 b2 b3 u) (newComp b1 b2 b3 k) = energy u k ∧
    energy (Bst b1 b2 b3 *ᵥ u) (Bst b1 b2 b3 *ᵥ k) = energy u k := by
  unfold energy; rw [mink_newComp hb, mink_boost hb]; exact ⟨rfl, rfl⟩

theorem newComp_observer {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    newComp b1 b2 b3 (fourVelocity b1 b2 b3) = e0 := by
  show Binv b1 b2 b3 *ᵥ (Bst b1 b2 b3 *ᵥ e0) = e0
  rw [Matrix.mulVec_mulVec, Binv_mul_Bst hb, Matrix.one_mulVec]

/-- Same physical ray: the new-frame components describe the same vector `k`. -/
theorem same_ray_components {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (k : V) :
    Bst b1 b2 b3 *ᵥ newComp b1 b2 b3 k = k := by
  rw [newComp, Matrix.mulVec_mulVec, Bst_mul_Binv hb, Matrix.one_mulVec]

theorem newComp_energy {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (k : V) :
    newComp b1 b2 b3 k 0 = energy (fourVelocity b1 b2 b3) k := by
  rw [← energy_e0 (newComp b1 b2 b3 k), ← newComp_observer hb,
    (energy_frame_independent hb _ _).1]

theorem newComp_photon (b1 b2 b3 E n1 n2 n3 : ℝ) :
    newComp b1 b2 b3 (photon E n1 n2 n3) =
      ![doppler b1 b2 b3 n1 n2 n3 * E,
        -(E * (n1 + gamma b1 b2 b3 * b1 + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * b1)),
        -(E * (n2 + gamma b1 b2 b3 * b2 + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * b2)),
        -(E * (n3 + gamma b1 b2 b3 * b3 + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * b3))] := by
  funext i
  fin_cases i <;>
    simp [newComp, Binv, boostNeg, boost, Matrix.mulVec, dotProduct, Fin.sum_univ_four,
      photon, doppler, dot3] <;> ring

theorem newDir_formula {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1)
    {E : ℝ} (hE : 0 < E) (i : Fin 3) :
    dirOf (newComp b1 b2 b3 (photon E n1 n2 n3)) i = aberr b1 b2 b3 n1 n2 n3 i := by
  have hD := (doppler_pos hb hn).ne'
  have hE' := hE.ne'
  rw [newComp_photon]
  fin_cases i <;> simp [dirOf, aberr] <;> field_simp

theorem oldDir (n1 n2 n3 : ℝ) {E : ℝ} (hE : 0 < E) (i : Fin 3) :
    dirOf (photon E n1 n2 n3) i = ![n1, n2, n3] i := by
  have hE' := hE.ne'
  fin_cases i <;> simp [dirOf, photon] <;> field_simp

theorem dir_unit {k : V} (hk : mink k k = 0) (h0 : k 0 ≠ 0) :
    s (dirOf k 0) (dirOf k 1) (dirOf k 2) = 1 := by
  simp [mink, CAS17C04.minkowski] at hk
  simp [s, dirOf]
  field_simp
  nlinarith [hk]

theorem dir_photon {k : V} (h0 : k 0 ≠ 0) :
    photon (k 0) (dirOf k 0) (dirOf k 1) (dirOf k 2) = k := by
  funext i
  fin_cases i <;> simp [photon, dirOf] <;> field_simp

theorem aberr_unit {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    s (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2) = 1 := by
  have hnull : mink (newComp b1 b2 b3 (photon 1 n1 n2 n3))
      (newComp b1 b2 b3 (photon 1 n1 n2 n3)) = 0 := by
    rw [mink_newComp hb]; exact photon_null 1 n1 n2 n3 hn
  have h0 : newComp b1 b2 b3 (photon 1 n1 n2 n3) 0 ≠ 0 := by
    rw [newComp_photon]; simpa using (doppler_pos hb hn).ne'
  have hu := dir_unit hnull h0
  rwa [newDir_formula hb hn one_pos 0, newDir_formula hb hn one_pos 1,
    newDir_formula hb hn one_pos 2] at hu

theorem aberr_dot {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
        (aberr b1 b2 b3 n1 n2 n3 2) * doppler b1 b2 b3 n1 n2 n3 =
      dot3 b1 b2 b3 n1 n2 n3 + gamma b1 b2 b3 * s b1 b2 b3
        + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * s b1 b2 b3 := by
  have hD := (doppler_pos hb hn).ne'
  simp only [aberr, dot3, s, Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two,
    Matrix.tail_cons, Matrix.head_cons]
  field_simp
  ring

/-- Reciprocal Doppler form in the new-frame direction:
    `D = 1 / (γ (1 - β·n'))` (T5 §2). -/
theorem doppler_reciprocal {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    doppler b1 b2 b3 n1 n2 n3 *
      (gamma b1 b2 b3 * (1 - dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0)
        (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2))) = 1 := by
  obtain ⟨_, hg2, hqs⟩ := core b1 b2 b3 hb
  have hX := aberr_dot hb hn
  set X := dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
    (aberr b1 b2 b3 n1 n2 n3 2)
  calc doppler b1 b2 b3 n1 n2 n3 * (gamma b1 b2 b3 * (1 - X))
      = gamma b1 b2 b3 * (doppler b1 b2 b3 n1 n2 n3 - X * doppler b1 b2 b3 n1 n2 n3) := by ring
    _ = 1 := by
      rw [hX]; unfold doppler
      linear_combination hg2 - gamma b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * hqs

/-- Aberration is onto the new-frame unit sphere. -/
theorem aberr_surjective {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {m1 m2 m3 : ℝ}
    (hm : s m1 m2 m3 = 1) :
    ∃ n1 n2 n3 : ℝ, s n1 n2 n3 = 1 ∧ aberr b1 b2 b3 n1 n2 n3 0 = m1 ∧
      aberr b1 b2 b3 n1 n2 n3 1 = m2 ∧ aberr b1 b2 b3 n1 n2 n3 2 = m3 := by
  set k : V := Bst b1 b2 b3 *ᵥ photon 1 m1 m2 m3 with hk
  have hnull : mink k k = 0 := by rw [hk, mink_boost hb]; exact photon_null 1 m1 m2 m3 hm
  have hk0 : k 0 = gamma b1 b2 b3 * (1 - dot3 b1 b2 b3 m1 m2 m3) := by
    simp [hk, Bst, boost, Matrix.mulVec, dotProduct, Fin.sum_univ_four, photon, dot3]; ring
  have hk0pos : 0 < k 0 := by
    rw [hk0]; exact mul_pos (core b1 b2 b3 hb).1 (one_sub_dot_pos hb hm)
  have hunit := dir_unit hnull hk0pos.ne'
  have hph : photon (k 0) (dirOf k 0) (dirOf k 1) (dirOf k 2) = k := dir_photon hk0pos.ne'
  have hnc : newComp b1 b2 b3 k = photon 1 m1 m2 m3 := by
    rw [hk, newComp, Matrix.mulVec_mulVec, Binv_mul_Bst hb, Matrix.one_mulVec]
  have key : ∀ i, aberr b1 b2 b3 (dirOf k 0) (dirOf k 1) (dirOf k 2) i =
      dirOf (photon 1 m1 m2 m3) i := by
    intro i
    rw [← newDir_formula hb hunit hk0pos i, hph, hnc]
  refine ⟨dirOf k 0, dirOf k 1, dirOf k 2, hunit, ?_, ?_, ?_⟩
  · rw [key 0]; simp [dirOf, photon]
  · rw [key 1]; simp [dirOf, photon]
  · rw [key 2]; simp [dirOf, photon]

/-! ## T2: aberration sphere Jacobian in the polar chart with axis `β̂` -/

theorem gamma1_core {b : ℝ} (hb : b ^ 2 < 1) :
    0 < gamma 0 0 b ∧ gamma 0 0 b ^ 2 * (1 - b ^ 2) = 1 := by
  have hs : s 0 0 b = b ^ 2 := by simp [s]
  obtain ⟨h1, h2, -⟩ := core 0 0 b (by rw [hs]; exact hb)
  rw [hs] at h2
  exact ⟨h1, h2⟩

theorem one_add_pos_of_mem {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    0 < 1 + b * μ := by
  obtain ⟨h1, h2⟩ := hμ
  have hb1 : -1 < b := by nlinarith
  have hb2 : b < 1 := by nlinarith
  rcases le_or_gt 0 b with hb0 | hb0 <;> nlinarith

theorem D1_pos {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) : 0 < D1 b μ :=
  mul_pos (gamma1_core hb).1 (one_add_pos_of_mem hb hμ)

theorem ab_hasDerivAt {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : 1 + b * μ ≠ 0) :
    HasDerivAt (ab b) ((D1 b μ ^ 2)⁻¹) μ := by
  have hd : HasDerivAt (fun x => (x + b) / (1 + b * x))
      ((1 * (1 + b * μ) - (μ + b) * (b * 1)) / (1 + b * μ) ^ 2) μ :=
    ((hasDerivAt_id' μ).add_const b).div (((hasDerivAt_id' μ).const_mul b).const_add 1) hμ
  apply hd.congr_deriv
  obtain ⟨hg, hg2⟩ := gamma1_core hb
  have hγ : gamma 0 0 b ≠ 0 := hg.ne'
  have h1 : 1 - b ^ 2 = (gamma 0 0 b ^ 2)⁻¹ := by
    field_simp
    linear_combination hg2
  rw [show (1 * (1 + b * μ) - (μ + b) * (b * 1)) = 1 - b ^ 2 by ring, h1, D1, mul_pow, mul_inv,
    div_eq_mul_inv]

theorem solid_angle_jacobian {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    deriv (ab b) μ = (D1 b μ ^ 2)⁻¹ :=
  (ab_hasDerivAt hb (one_add_pos_of_mem hb hμ).ne').deriv

theorem ab_endpoints {b : ℝ} (hb : b ^ 2 < 1) : ab b (-1) = -1 ∧ ab b 1 = 1 := by
  have hb1 : 1 - b ≠ 0 := by intro h0; nlinarith
  have hb2 : 1 + b ≠ 0 := by intro h0; nlinarith
  constructor
  · unfold ab
    rw [show (1 : ℝ) + b * -1 = 1 - b by ring, div_eq_iff hb1]; ring
  · unfold ab
    rw [show (1 : ℝ) + b * 1 = 1 + b by ring, show (1 : ℝ) + b = 1 + b from rfl,
      div_eq_iff hb2]; ring

theorem ab_mem {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    ab b μ ∈ Icc (-1 : ℝ) 1 := by
  have hpos := one_add_pos_of_mem hb hμ
  have hb1 : -1 < b := by nlinarith
  have hb2 : b < 1 := by nlinarith
  obtain ⟨h1, h2⟩ := hμ
  constructor
  · rw [ab, le_div_iff₀ hpos]
    nlinarith [mul_nonneg (show (0 : ℝ) ≤ 1 + b by linarith) (show (0 : ℝ) ≤ 1 + μ by linarith)]
  · rw [ab, div_le_iff₀ hpos]
    nlinarith [mul_nonneg (show (0 : ℝ) ≤ 1 - b by linarith) (show (0 : ℝ) ≤ 1 - μ by linarith)]

theorem ab_strictMonoOn {b : ℝ} (hb : b ^ 2 < 1) : StrictMonoOn (ab b) (Icc (-1 : ℝ) 1) := by
  intro x hx y hy hxy
  have hpx := one_add_pos_of_mem hb hx
  have hpy := one_add_pos_of_mem hb hy
  unfold ab
  rw [div_lt_div_iff₀ hpx hpy]
  nlinarith [mul_pos (show (0 : ℝ) < 1 - b ^ 2 by linarith) (show (0 : ℝ) < y - x by linarith)]

/-- The chart map is a bijection of `[-1,1]` with explicit inverse `ab (-b)`. -/
theorem ab_inverse {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    ab (-b) (ab b μ) = μ ∧ ab b (ab (-b) μ) = μ := by
  have hb' : (-b) ^ 2 < 1 := by simpa using hb
  have hp := one_add_pos_of_mem hb hμ
  have hp' := one_add_pos_of_mem hb' hμ
  have hp0 : 1 + b * μ ≠ 0 := hp.ne'
  have hp0' : 1 + -b * μ ≠ 0 := hp'.ne'
  have hq0 : 1 - b ^ 2 ≠ 0 := by intro h0; nlinarith
  constructor
  · have e1 : ab b μ + -b = μ * (1 - b ^ 2) / (1 + b * μ) := by
      unfold ab; rw [div_add' _ _ _ hp0, div_eq_div_iff hp0 hp0]; ring
    have e2 : 1 + -b * ab b μ = (1 - b ^ 2) / (1 + b * μ) := by
      unfold ab; rw [mul_div_assoc', add_div' _ _ _ hp0, div_eq_div_iff hp0 hp0]; ring
    show (ab b μ + -b) / (1 + -b * ab b μ) = μ
    rw [e1, e2, div_div_div_cancel_right₀ hp0, mul_div_assoc, div_self hq0, mul_one]
  · have e1 : ab (-b) μ + b = μ * (1 - b ^ 2) / (1 + -b * μ) := by
      unfold ab; rw [div_add' _ _ _ hp0', div_eq_div_iff hp0' hp0']; ring
    have e2 : 1 + b * ab (-b) μ = (1 - b ^ 2) / (1 + -b * μ) := by
      unfold ab; rw [mul_div_assoc', add_div' _ _ _ hp0', div_eq_div_iff hp0' hp0']; ring
    show (ab (-b) μ + b) / (1 + b * ab (-b) μ) = μ
    rw [e1, e2, div_div_div_cancel_right₀ hp0', mul_div_assoc, div_self hq0, mul_one]

theorem D1_inv_sq_continuousOn {b : ℝ} (hb : b ^ 2 < 1) {S : Set ℝ} (hS : S ⊆ Icc (-1 : ℝ) 1) :
    ContinuousOn (fun x => (D1 b x ^ 2)⁻¹) S := by
  apply ContinuousOn.inv₀
  · unfold D1; fun_prop
  · intro x hx; exact pow_ne_zero 2 (D1_pos hb (hS hx)).ne'

/-- Explicit change of variables on the polar coordinate `μ = cos θ`:
    `dμ' = D^{-2} dμ` as an identity of integrals over `[-1,1]`. -/
theorem solid_angle_change_of_variables {b : ℝ} (hb : b ^ 2 < 1) {g : ℝ → ℝ}
    (hg : ContinuousOn g (Icc (-1 : ℝ) 1)) :
    ∫ μ in (-1 : ℝ)..1, g (ab b μ) * (D1 b μ ^ 2)⁻¹ = ∫ μ' in (-1 : ℝ)..1, g μ' := by
  have hI : uIcc (-1 : ℝ) 1 = Icc (-1) 1 := uIcc_of_le (by norm_num)
  have hderiv : ∀ x ∈ uIcc (-1 : ℝ) 1, HasDerivAt (ab b) ((D1 b x ^ 2)⁻¹) x := by
    intro x hx; rw [hI] at hx; exact ab_hasDerivAt hb (one_add_pos_of_mem hb hx).ne'
  have hcont : ContinuousOn (fun x => (D1 b x ^ 2)⁻¹) (uIcc (-1 : ℝ) 1) :=
    D1_inv_sq_continuousOn hb (by rw [hI])
  have hgi : ContinuousOn g (ab b '' uIcc (-1 : ℝ) 1) := by
    apply hg.mono
    rintro _ ⟨x, hx, rfl⟩
    rw [hI] at hx
    exact ab_mem hb hx
  have hcv := intervalIntegral.integral_comp_mul_deriv' hderiv hcont hgi
  rw [(ab_endpoints hb).1, (ab_endpoints hb).2] at hcv
  simpa [Function.comp] using hcv

/-- Solid-angle form `dΩ = dμ dφ` with azimuth unchanged: `dΩ' = D^{-2} dΩ`. -/
theorem sphere_chart_change_of_variables {b : ℝ} (hb : b ^ 2 < 1) {g : ℝ → ℝ → ℝ}
    (hg : ∀ φ, ContinuousOn (fun μ => g μ φ) (Icc (-1 : ℝ) 1)) :
    ∫ φ in (0 : ℝ)..2 * π, ∫ μ in (-1 : ℝ)..1, g (ab b μ) φ * (D1 b μ ^ 2)⁻¹ =
      ∫ φ in (0 : ℝ)..2 * π, ∫ μ' in (-1 : ℝ)..1, g μ' φ := by
  congr 1
  funext φ
  exact solid_angle_change_of_variables hb (hg φ)

theorem total_solid_angle {b : ℝ} (hb : b ^ 2 < 1) :
    ∫ φ in (0 : ℝ)..2 * π, ∫ μ in (-1 : ℝ)..1, (D1 b μ ^ 2)⁻¹ = 4 * π := by
  have hcv := sphere_chart_change_of_variables hb (g := fun _ _ => (1 : ℝ))
    (fun _ => continuousOn_const)
  simp only [one_mul] at hcv
  rw [hcv]
  simp
  ring

theorem band_solid_angle {b μ1 μ2 : ℝ} (hb : b ^ 2 < 1) (h1 : μ1 ∈ Icc (-1 : ℝ) 1)
    (h2 : μ2 ∈ Icc (-1 : ℝ) 1) (φ1 φ2 : ℝ) :
    (ab b μ2 - ab b μ1) * (φ2 - φ1) = (∫ μ in μ1..μ2, (D1 b μ ^ 2)⁻¹) * (φ2 - φ1) := by
  have hsub : uIcc μ1 μ2 ⊆ Icc (-1 : ℝ) 1 := uIcc_subset_Icc h1 h2
  rw [intervalIntegral.integral_eq_sub_of_hasDerivAt (f := ab b)]
  · intro x hx; exact ab_hasDerivAt hb (one_add_pos_of_mem hb (hsub hx)).ne'
  · exact (D1_inv_sq_continuousOn hb hsub).intervalIntegrable

/-- Same source screen area `dS`, observed solid angle scaled by the Jacobian:
    `d_A' = D d_A`. -/
theorem areaDist_aberration {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1)
    (dS dΩ : ℝ) :
    areaDist dS (deriv (ab b) μ * dΩ) = D1 b μ * areaDist dS dΩ := by
  rw [solid_angle_jacobian hb hμ]
  have hD := D1_pos hb hμ
  unfold areaDist
  have hrw : dS / ((D1 b μ ^ 2)⁻¹ * dΩ) = D1 b μ ^ 2 * (dS / dΩ) := by
    rw [div_mul_eq_div_div, div_inv_eq_mul]; ring
  rw [hrw, Real.sqrt_mul (by positivity), Real.sqrt_sq hD.le]

/-- Link of the general-β closed form to the polar chart with axis `β̂ = β/ℓ`:
    Doppler factor, polar cosine map, and unchanged azimuth (the component
    perpendicular to `β̂` is rescaled by the positive factor `1/D`). -/
theorem chart_link {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hb0 : 0 < s b1 b2 b3)
    (hn : s n1 n2 n3 = 1) {ℓ μ : ℝ} (hℓ : ℓ = Real.sqrt (s b1 b2 b3))
    (hμ : μ = dot3 b1 b2 b3 n1 n2 n3 / ℓ) :
    ℓ ^ 2 < 1 ∧ μ ∈ Icc (-1 : ℝ) 1 ∧
    doppler b1 b2 b3 n1 n2 n3 = D1 ℓ μ ∧
    dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
        (aberr b1 b2 b3 n1 n2 n3 2) / ℓ = ab ℓ μ ∧
    ∀ i : Fin 3, aberr b1 b2 b3 n1 n2 n3 i - ab ℓ μ * (![b1, b2, b3] i / ℓ) =
      (![n1, n2, n3] i - μ * (![b1, b2, b3] i / ℓ)) / doppler b1 b2 b3 n1 n2 n3 := by
  obtain ⟨hg, _, hqs⟩ := core b1 b2 b3 hb
  have hℓ2 : ℓ ^ 2 = s b1 b2 b3 := by rw [hℓ]; exact Real.sq_sqrt hb0.le
  have hℓpos : 0 < ℓ := by rw [hℓ]; exact Real.sqrt_pos.2 hb0
  have hℓne := hℓpos.ne'
  have hgam : gamma 0 0 ℓ = gamma b1 b2 b3 := by
    have hs0 : s 0 0 ℓ = s b1 b2 b3 := by rw [← hℓ2]; simp [s]
    unfold gamma; rw [hs0]
  have ht2 := dot_bound b1 b2 b3 n1 n2 n3
  rw [hn, mul_one, ← hℓ2] at ht2
  have hpos := one_add_dot_pos hb hn
  have hD := (doppler_pos hb hn).ne'
  have hX := aberr_dot hb hn
  set t := dot3 b1 b2 b3 n1 n2 n3 with ht
  set γ := gamma b1 b2 b3 with hγ
  set q := h b1 b2 b3 with hq
  set S := s b1 b2 b3 with hS
  have hDdef : doppler b1 b2 b3 n1 n2 n3 = γ * (1 + t) := rfl
  refine ⟨by rw [hℓ2]; exact hb, ?_, ?_, ?_, ?_⟩
  · rw [hμ]
    constructor
    · rw [le_div_iff₀ hℓpos]; nlinarith
    · rw [div_le_iff₀ hℓpos]; nlinarith
  · rw [hDdef, D1, hgam, hμ]; field_simp
  · have hdot : dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
        (aberr b1 b2 b3 n1 n2 n3 2) = (γ * t + γ * S) / (γ * (1 + t)) := by
      rw [← hDdef, eq_div_iff hD, hX]
      linear_combination t * hqs
    rw [hdot, ab, hμ, ← hℓ2]
    have hγne : γ ≠ 0 := hg.ne'
    have h1t : 1 + t ≠ 0 := hpos.ne'
    field_simp
  · have hqv : q = (γ - 1) / ℓ ^ 2 := by
      rw [hℓ2, eq_div_iff hb0.ne']; exact hqs
    have hab : ab ℓ μ = (t + ℓ ^ 2) / ((1 + t) * ℓ) := by
      rw [ab, hμ]
      have h1t : 1 + t ≠ 0 := hpos.ne'
      field_simp
    intro i
    have hγne : γ ≠ 0 := hg.ne'
    have h1t : 1 + t ≠ 0 := hpos.ne'
    rw [hab, hμ]
    fin_cases i <;> simp only [aberr, hDdef, Fin.zero_eta, Fin.mk_one, Fin.reduceFinMk,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two, Matrix.head_cons] <;>
      rw [← hq, ← ht, ← hγ, hqv] <;> field_simp <;> ring

/-! ## T3: redshift and area distance of the same ray -/

theorem redshift_endpoint {Es E D : ℝ} (hE : 0 < E) (hD : 0 < D) :
    redshiftOf Es (D * E) = zNew (redshiftOf Es E) D := by
  unfold redshiftOf zNew
  field_simp
  ring

/-- Composite same-ray endpoint law: measured energies give `z'`, the
    aberration Jacobian gives `d_A'`, and `(1+z') d_A' = (1+z) d_A`. -/
theorem endpoint_optical_same_ray {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1)
    (hb0 : 0 < s b1 b2 b3) (hn : s n1 n2 n3 = 1) {E Es dS dΩ ℓ μ : ℝ} (hE : 0 < E)
    (hℓ : ℓ = Real.sqrt (s b1 b2 b3)) (hμ : μ = dot3 b1 b2 b3 n1 n2 n3 / ℓ) :
    redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3)) =
        zNew (redshiftOf Es (energy e0 (photon E n1 n2 n3))) (doppler b1 b2 b3 n1 n2 n3) ∧
    areaDist dS (deriv (ab ℓ) μ * dΩ) =
        dANew (areaDist dS dΩ) (doppler b1 b2 b3 n1 n2 n3) ∧
    (1 + redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3))) *
        areaDist dS (deriv (ab ℓ) μ * dΩ) =
      (1 + redshiftOf Es (energy e0 (photon E n1 n2 n3))) * areaDist dS dΩ := by
  obtain ⟨hℓ1, hμI, hDeq, -, -⟩ := chart_link hb hb0 hn hℓ hμ
  have hD := doppler_pos hb hn
  have hz : redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3)) =
      zNew (redshiftOf Es (energy e0 (photon E n1 n2 n3))) (doppler b1 b2 b3 n1 n2 n3) := by
    rw [energy_new, energy_old]; exact redshift_endpoint hE hD
  have hA : areaDist dS (deriv (ab ℓ) μ * dΩ) =
      dANew (areaDist dS dΩ) (doppler b1 b2 b3 n1 n2 n3) := by
    rw [areaDist_aberration hℓ1 hμI, hDeq]; rfl
  refine ⟨hz, hA, ?_⟩
  rw [hz, hA]
  exact endpoint_product_invariant _ _ _ hD

/-! ## T4: luminosity distance under explicit reciprocity -/

/-- Etherington reciprocity `d_L = (1+z)^2 d_A` is a HYPOTHESIS in each frame. -/
theorem luminosity_from_reciprocity {z dA dL dL' D : ℝ} (hD : 0 < D)
    (hrecOld : dL = (1 + z) ^ 2 * dA)
    (hrecNew : dL' = (1 + zNew z D) ^ 2 * dANew dA D) :
    dL' = dL / D ∧ dL' = dLNew dL D := by
  have hmain : dL' = dL / D := by
    rw [hrecNew, hrecOld]
    unfold zNew dANew
    field_simp
    ring
  exact ⟨hmain, hmain⟩

theorem distance_ratio_invariant {z dA dL dL' D : ℝ} (hD : 0 < D) (hz : 1 + z ≠ 0)
    (hrecOld : dL = (1 + z) ^ 2 * dA)
    (hrecNew : dL' = (1 + zNew z D) ^ 2 * dANew dA D) :
    dL' / (1 + zNew z D) = dL / (1 + z) := by
  have hz' : 1 + zNew z D = (1 + z) / D := by unfold zNew; ring
  rw [hrecNew, hrecOld, hz']
  unfold dANew
  field_simp

/-- Same-ray composite luminosity law (reciprocity assumed in both frames). -/
theorem endpoint_luminosity_same_ray {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1)
    (hb0 : 0 < s b1 b2 b3) (hn : s n1 n2 n3 = 1) {E Es dS dΩ ℓ μ dL dL' : ℝ} (hE : 0 < E)
    (hℓ : ℓ = Real.sqrt (s b1 b2 b3)) (hμ : μ = dot3 b1 b2 b3 n1 n2 n3 / ℓ)
    (hrecOld : dL = (1 + redshiftOf Es (energy e0 (photon E n1 n2 n3))) ^ 2 * areaDist dS dΩ)
    (hrecNew : dL' = (1 + redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3))) ^ 2
        * areaDist dS (deriv (ab ℓ) μ * dΩ)) :
    dL' = dL / doppler b1 b2 b3 n1 n2 n3 := by
  obtain ⟨hz, hA, -⟩ := endpoint_optical_same_ray (Es := Es) (dS := dS) (dΩ := dΩ)
    hb hb0 hn hE hℓ hμ
  rw [hz, hA] at hrecNew
  exact (luminosity_from_reciprocity (doppler_pos hb hn) hrecOld hrecNew).1

/-! ## T5: scalar blackbody inverse-temperature affine law -/

theorem planckOcc_injOn : InjOn planckOcc (Ioi 0) := by
  intro x hx y hy hxy
  have hx' : 0 < Real.exp x - 1 := by
    have := Real.one_lt_exp_iff.mpr (show 0 < x from hx); linarith
  have hy' : 0 < Real.exp y - 1 := by
    have := Real.one_lt_exp_iff.mpr (show 0 < y from hy); linarith
  unfold planckOcc at hxy
  rw [one_div, one_div, inv_inj] at hxy
  exact Real.exp_injective (by linarith)

/-- Invariance of the Planck occupation number along the same ray gives
    `T' = T0 E'/E` (scalar, d = 1 only). -/
theorem temperature_transform {E E' T0 T' : ℝ} (hE : 0 < E) (hE' : 0 < E') (hT0 : 0 < T0)
    (hT' : 0 < T') (hocc : planckOcc (E' / T') = planckOcc (E / T0)) :
    T' = T0 * (E' / E) := by
  have hq := planckOcc_injOn (show E' / T' ∈ Ioi 0 from div_pos hE' hT')
    (show E / T0 ∈ Ioi 0 from div_pos hE hT0) hocc
  field_simp at hq ⊢
  nlinarith [hq]

theorem inverse_temperature_affine {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1)
    (hn : s n1 n2 n3 = 1) {E T0 T' : ℝ} (hE : 0 < E) (hT0 : 0 < T0) (hT' : 0 < T')
    (hocc : planckOcc (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) / T') =
      planckOcc (energy e0 (photon E n1 n2 n3) / T0)) :
    T' = doppler b1 b2 b3 n1 n2 n3 * T0 ∧
    1 / T' = gamma b1 b2 b3 / T0 +
      dot3 (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
        (-(gamma b1 b2 b3 * b3 / T0))
        (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2) := by
  have hD := doppler_pos hb hn
  rw [energy_new, energy_old] at hocc
  have hT := temperature_transform hE (mul_pos hD hE) hT0 hT' hocc
  have hT2 : T' = doppler b1 b2 b3 n1 n2 n3 * T0 := by
    rw [hT]; field_simp
  refine ⟨hT2, ?_⟩
  have hr := doppler_reciprocal hb hn
  set P := dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
    (aberr b1 b2 b3 n1 n2 n3 2) with hP
  have key : gamma b1 b2 b3 / T0 +
      dot3 (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
        (-(gamma b1 b2 b3 * b3 / T0))
        (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2) =
      gamma b1 b2 b3 * (1 - P) / T0 := by
    rw [hP]; unfold dot3; field_simp; ring
  rw [key, hT2]
  have hDne := hD.ne'
  have hT0ne := hT0.ne'
  calc 1 / (doppler b1 b2 b3 n1 n2 n3 * T0)
      = (doppler b1 b2 b3 n1 n2 n3 * (gamma b1 b2 b3 * (1 - P))) /
          (doppler b1 b2 b3 n1 n2 n3 * T0) := by rw [hr]
    _ = gamma b1 b2 b3 * (1 - P) / T0 := by field_simp

theorem affine_coeff_domain {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {T0 : ℝ} (hT0 : 0 < T0) :
    0 < gamma b1 b2 b3 / T0 ∧
    s (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
        (-(gamma b1 b2 b3 * b3 / T0)) < (gamma b1 b2 b3 / T0) ^ 2 ∧
    (gamma b1 b2 b3 / T0) ^ 2 -
        s (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
          (-(gamma b1 b2 b3 * b3 / T0)) = 1 / T0 ^ 2 := by
  obtain ⟨hg, hg2, -⟩ := core b1 b2 b3 hb
  have hs : s (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
      (-(gamma b1 b2 b3 * b3 / T0)) = gamma b1 b2 b3 ^ 2 * s b1 b2 b3 / T0 ^ 2 := by
    unfold s; field_simp
  have hdiff : (gamma b1 b2 b3 / T0) ^ 2 - gamma b1 b2 b3 ^ 2 * s b1 b2 b3 / T0 ^ 2
      = 1 / T0 ^ 2 := by
    rw [← hg2]; field_simp
  refine ⟨div_pos hg hT0, ?_, by rw [hs]; exact hdiff⟩
  rw [hs]
  have : 0 < 1 / T0 ^ 2 := by positivity
  linarith

/-- Inversion used by `inverse_temperature_boost`: `β = -b/a`, `T0 = γ/a`. -/
theorem inverse_temperature_inversion {a c1 c2 c3 : ℝ} (ha : 0 < a)
    (hc : s c1 c2 c3 < a ^ 2) :
    s (-c1 / a) (-c2 / a) (-c3 / a) < 1 ∧
    gamma (-c1 / a) (-c2 / a) (-c3 / a) / a = 1 / Real.sqrt (a ^ 2 - s c1 c2 c3) ∧
    ∀ m1 m2 m3 : ℝ, a + dot3 c1 c2 c3 m1 m2 m3 =
      gamma (-c1 / a) (-c2 / a) (-c3 / a) * (1 - dot3 (-c1 / a) (-c2 / a) (-c3 / a) m1 m2 m3) /
        (gamma (-c1 / a) (-c2 / a) (-c3 / a) / a) := by
  have hsβ : s (-c1 / a) (-c2 / a) (-c3 / a) = s c1 c2 c3 / a ^ 2 := by
    unfold s; field_simp
  have ha2 : 0 < a ^ 2 := by positivity
  have hlt : s (-c1 / a) (-c2 / a) (-c3 / a) < 1 := by
    rw [hsβ, div_lt_one ha2]; exact hc
  obtain ⟨hg, hg2, -⟩ := core _ _ _ hlt
  refine ⟨hlt, ?_, ?_⟩
  · have hX : 0 < a ^ 2 - s c1 c2 c3 := by linarith
    have hr : 0 < Real.sqrt (a ^ 2 - s c1 c2 c3) := Real.sqrt_pos.2 hX
    rw [← sq_eq_sq₀ (div_pos hg ha).le (by positivity)]
    rw [div_pow, div_pow, Real.sq_sqrt hX.le, hsβ] at *
    rw [hsβ] at hg2
    field_simp
    field_simp at hg2
    linear_combination hg2
  · intro m1 m2 m3
    set G := gamma (-c1 / a) (-c2 / a) (-c3 / a) with hG
    have hgne : G ≠ 0 := hg.ne'
    have hane := ha.ne'
    unfold dot3
    field_simp
    ring

/-- TBO-07 criterion: the absolute scalar blackbody sky is one boost of an
    isotropic blackbody iff its inverse temperature is affine with `a > |b|`. -/
theorem isotropic_blackbody_criterion (invT : ℝ → ℝ → ℝ → ℝ) :
    (∃ T0 b1 b2 b3 : ℝ, 0 < T0 ∧ s b1 b2 b3 < 1 ∧ ∀ m1 m2 m3 : ℝ, s m1 m2 m3 = 1 →
        invT m1 m2 m3 = gamma b1 b2 b3 * (1 - dot3 b1 b2 b3 m1 m2 m3) / T0) ↔
    (∃ a c1 c2 c3 : ℝ, 0 < a ∧ s c1 c2 c3 < a ^ 2 ∧ ∀ m1 m2 m3 : ℝ, s m1 m2 m3 = 1 →
        invT m1 m2 m3 = a + dot3 c1 c2 c3 m1 m2 m3) := by
  constructor
  · rintro ⟨T0, b1, b2, b3, hT0, hb, hinv⟩
    obtain ⟨ha, hlt, -⟩ := affine_coeff_domain hb hT0
    refine ⟨gamma b1 b2 b3 / T0, -(gamma b1 b2 b3 * b1 / T0), -(gamma b1 b2 b3 * b2 / T0),
      -(gamma b1 b2 b3 * b3 / T0), ha, hlt, ?_⟩
    intro m1 m2 m3 hm
    rw [hinv m1 m2 m3 hm]
    unfold dot3; field_simp; ring
  · rintro ⟨a, c1, c2, c3, ha, hc, hinv⟩
    obtain ⟨hlt, -, hform⟩ := inverse_temperature_inversion ha hc
    obtain ⟨hg, -, -⟩ := core _ _ _ hlt
    refine ⟨gamma (-c1 / a) (-c2 / a) (-c3 / a) / a, -c1 / a, -c2 / a, -c3 / a,
      div_pos hg ha, hlt, ?_⟩
    intro m1 m2 m3 hm
    rw [hinv m1 m2 m3 hm]
    exact hform m1 m2 m3

/-- Sky form of the forward law: every new-frame direction `m` is the aberrated
    direction of a ray, and on that ray `1/T' = a + b·m`. -/
theorem boosted_isotropic_sky {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {T0 : ℝ} (hT0 : 0 < T0)
    {m1 m2 m3 : ℝ} (hm : s m1 m2 m3 = 1) :
    ∃ n1 n2 n3 : ℝ, s n1 n2 n3 = 1 ∧ aberr b1 b2 b3 n1 n2 n3 0 = m1 ∧
      aberr b1 b2 b3 n1 n2 n3 1 = m2 ∧ aberr b1 b2 b3 n1 n2 n3 2 = m3 ∧
      ∀ E T' : ℝ, 0 < E → 0 < T' →
        planckOcc (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) / T') =
          planckOcc (energy e0 (photon E n1 n2 n3) / T0) →
        1 / T' = gamma b1 b2 b3 / T0 +
          dot3 (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
            (-(gamma b1 b2 b3 * b3 / T0)) m1 m2 m3 := by
  obtain ⟨n1, n2, n3, hn, h0, h1, h2⟩ := aberr_surjective hb hm
  refine ⟨n1, n2, n3, hn, h0, h1, h2, ?_⟩
  intro E T' hE hT' hocc
  have := (inverse_temperature_affine hb hn hE hT0 hT' hocc).2
  rwa [h0, h1, h2] at this

/-! ## Boundary cases -/

theorem gamma_zero : gamma 0 0 0 = 1 := by norm_num [gamma, s]

theorem ab_zero : ab 0 = id := by funext μ; simp [ab]

theorem boundary_beta_zero (n1 n2 n3 μ : ℝ) (k : V) :
    doppler 0 0 0 n1 n2 n3 = 1 ∧ newComp 0 0 0 k = k ∧
    (∀ i, aberr 0 0 0 n1 n2 n3 i = ![n1, n2, n3] i) ∧
    ab 0 μ = μ ∧ D1 0 μ = 1 ∧ deriv (ab 0) μ = 1 ∧
    (∀ z, zNew z 1 = z) ∧ (∀ dA, dANew dA 1 = dA) ∧ (∀ dL, dLNew dL 1 = dL) := by
  have hdop : doppler 0 0 0 n1 n2 n3 = 1 := by simp [doppler, dot3, gamma_zero]
  refine ⟨hdop, ?_, ?_, by simp [ab], by simp [D1, gamma_zero], ?_, ?_, ?_, ?_⟩
  · simp [newComp, Binv, boostNeg, zero_boost]
  · intro i; fin_cases i <;> simp [aberr, hdop]
  · rw [ab_zero]; exact deriv_id μ
  · intro z; simp [zNew]
  · intro dA; simp [dANew]
  · intro dL; simp [dLNew]

theorem temperature_beta_zero {n1 n2 n3 E T0 T' : ℝ} (hn : s n1 n2 n3 = 1) (hE : 0 < E)
    (hT0 : 0 < T0) (hT' : 0 < T')
    (hocc : planckOcc (energy (fourVelocity 0 0 0) (photon E n1 n2 n3) / T') =
      planckOcc (energy e0 (photon E n1 n2 n3) / T0)) :
    T' = T0 := by
  have := (inverse_temperature_affine (by norm_num [s]) hn hE hT0 hT' hocc).1
  rw [this, (boundary_beta_zero n1 n2 n3 0 0).1, one_mul]

theorem boundary_z_zero {dA D : ℝ} (hD : 0 < D) : (1 + zNew 0 D) * dANew dA D = dA := by
  have := endpoint_product_invariant 0 dA D hD
  simpa using this

/-! ## Negative controls and non-vacuity -/

theorem gamma_three_fifths : gamma 0 0 (3 / 5) = 5 / 4 := by
  unfold gamma s
  rw [show (1 : ℝ) - ((0 : ℝ) ^ 2 + 0 ^ 2 + (3 / 5) ^ 2) = (4 / 5) ^ 2 by norm_num,
    Real.sqrt_sq (by norm_num)]
  norm_num

/-- Non-vacuity: the composite hypotheses are jointly satisfiable. -/
theorem nonvacuity_witness :
    s 0 0 (3 / 5) < 1 ∧ 0 < s 0 0 (3 / 5) ∧ s 0 0 1 = 1 ∧ doppler 0 0 (3 / 5) 0 0 1 = 2 := by
  refine ⟨by norm_num [s], by norm_num [s], by norm_num [s], ?_⟩
  simp only [doppler, dot3, gamma_three_fifths]; norm_num

/-- Negative control: the same ray measured by two different observers gives
    different energies (observer replacement is not a passive relabelling), and
    mixing Doppler factors of two DISTINCT rays breaks the product law. -/
theorem distinct_ray_counterexample :
    energy e0 (photon 1 0 0 1) = 1 ∧
    energy (fourVelocity 0 0 (3 / 5)) (photon 1 0 0 1) = 2 ∧
    doppler 0 0 (3 / 5) 0 0 (-1) = 1 / 2 ∧
    (1 + zNew 0 (doppler 0 0 (3 / 5) 0 0 (-1))) * dANew 1 (doppler 0 0 (3 / 5) 0 0 1) ≠
      (1 + 0) * 1 := by
  have h1 : doppler 0 0 (3 / 5) 0 0 1 = 2 := nonvacuity_witness.2.2.2
  have h2 : doppler 0 0 (3 / 5) 0 0 (-1) = 1 / 2 := by
    simp only [doppler, dot3, gamma_three_fifths]; norm_num
  refine ⟨energy_old 1 0 0 1, ?_, h2, ?_⟩
  · rw [energy_new, h1]; norm_num
  · rw [h1, h2]; norm_num [zNew, dANew]

end P06AOptics
