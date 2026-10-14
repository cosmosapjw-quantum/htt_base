# P06-A frozen targets (frozen before the first proof compile)

Frozen 2026-10-13T21:42:46.033123+00:00 (UTC), before any
compile of `lean/P06AOptics.lean`.  Namespace `P06AOptics`.  Imports (unchanged,
compiled into `raw/imports`): `Mathlib`, `PortCas01`, `PassiveTensorBridge`
(`CAS17C04`), `EndpointScalarInvariant` (`PORTCAS06EndpointScalarInvariant`).
`s`, `gamma`, `h`, `boost`, `boostNeg`, `e0`, `fourVelocity`, `eta`,
`metric_identity`, `inverse_identity`, `zero_boost`, `fourVelocity_components`
are the PORT-CAS-01 objects; `zNew`, `dANew`, `dLNew`,
`endpoint_product_invariant` are the reviewed prior P06 objects.
Any later change to a statement below is a deviation and must be recorded in
`AUTHOR_RETURN.json`.

## Card step -> target map

| Card lean_step / acceptance | Frozen target(s) | Scope / quantifiers |
|---|---|---|
| S1 null tangent, two observers' measured energies, Doppler direction convention | `photon_null`, `photon_future`, `energy_old`, `energy_new`, `doppler_pos`, `doppler_eq_energy_ratio`, `energy_frame_independent`, `newComp_observer`, `same_ray_components`, `newComp_energy`, `newDir_formula`, `oldDir`, `aberr_unit`, `doppler_reciprocal`, `aberr_surjective` | all real `E>0`, unit sourceward `n` (`s n = 1`), all `β` with `s β < 1`; ONE fixed vector `k = photon E n`; old observer `e0`, new observer `fourVelocity β`; `D = E'/E = γ(1+β·n)` |
| S2 aberration sphere Jacobian, source area / observer solid angle | `ab_hasDerivAt`, `solid_angle_jacobian`, `ab_endpoints`, `ab_mem`, `ab_strictMonoOn`, `ab_inverse`, `solid_angle_change_of_variables`, `sphere_chart_change_of_variables`, `total_solid_angle`, `band_solid_angle`, `areaDist_aberration`, `chart_link` | polar chart with axis `β̂` (speed `b`, `b^2<1`; `μ=cos θ ∈ [-1,1]`; azimuth unchanged, proved in `chart_link` for general `β≠0`); `dΩ = dμ dφ`; measure statement = interval-integral change of variables for every `g` continuous on `[-1,1]`; `d_A = sqrt(dS/dΩ)` |
| S3 `(1+z_new) dA_new = (1+z) dA` | `redshift_endpoint`, `endpoint_optical_same_ray` (uses imported `endpoint_product_invariant`) | same ray, `1+z = Es/E` with the SAME source energy `Es`; general `β` with `0 < s β < 1` (β=0 handled by `boundary_beta_zero`) |
| S4 reciprocity explicit -> `dL_new = dL/D`; scalar blackbody inverse-T affine law | `luminosity_from_reciprocity`, `distance_ratio_invariant`, `endpoint_luminosity_same_ray`; `planckOcc_injOn`, `temperature_transform`, `inverse_temperature_affine`, `affine_coeff_domain`, `inverse_temperature_inversion`, `isotropic_blackbody_criterion`, `boosted_isotropic_sky` | reciprocity `d_L=(1+z)^2 d_A` is a HYPOTHESIS in each frame; temperature: scalar Planck occupation invariance hypothesis only (no polarization/spin-2) |
| Acceptance: boundaries `z=0`, `β=0` | `boundary_beta_zero`, `temperature_beta_zero`, `boundary_z_zero` | |
| Negative control / non-vacuity | `distinct_ray_counterexample`, `nonvacuity_witness`, `gamma_three_fifths`; plus reused `CAS17C04.physical_observer_replacement_counterexample` (#check only) | |

## Honest scope limits fixed at freeze time

* The sphere Jacobian is proved as an explicit change of variables in the polar
  chart whose axis is `β̂`; the general-β closed form is linked to that chart
  by `chart_link` (polar cosine map and azimuth preservation).  A
  chart-free surface-measure statement on `S^2 ⊂ ℝ^3` (Mathlib
  `Measure.toSphere`) is NOT a frozen target.
* Flat tangent space at the observer event only; no propagation, no curved
  geometry, no source-frame motion (`Es` is a fixed source quantity).
* Reciprocity and transparency are hypotheses, never derived.
* Temperature results are the scalar `d=1` blackbody law only.

## Exact frozen Lean definitions and statements

```lean
abbrev V := Fin 4 → ℝ

def mink (x y : V) : ℝ := CAS17C04.minkowski x y

def dot3 (a1 a2 a3 x1 x2 x3 : ℝ) : ℝ := a1 * x1 + a2 * x2 + a3 * x3

def photon (E n1 n2 n3 : ℝ) : V := ![E, -(E * n1), -(E * n2), -(E * n3)]

def energy (u k : V) : ℝ := -mink k u

noncomputable def doppler (b1 b2 b3 n1 n2 n3 : ℝ) : ℝ :=
  gamma b1 b2 b3 * (1 + dot3 b1 b2 b3 n1 n2 n3)

noncomputable def Bst (b1 b2 b3 : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  boost (gamma b1 b2 b3) (h b1 b2 b3) b1 b2 b3

noncomputable def Binv (b1 b2 b3 : ℝ) : Matrix (Fin 4) (Fin 4) ℝ :=
  boostNeg (gamma b1 b2 b3) (h b1 b2 b3) b1 b2 b3

noncomputable def newComp (b1 b2 b3 : ℝ) (k : V) : V := Binv b1 b2 b3 *ᵥ k

noncomputable def dirOf (k : V) (i : Fin 3) : ℝ := -(k i.succ) / k 0

noncomputable def aberr (b1 b2 b3 n1 n2 n3 : ℝ) (i : Fin 3) : ℝ :=
  (![n1, n2, n3] i + gamma b1 b2 b3 * ![b1, b2, b3] i
      + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * ![b1, b2, b3] i)
    / doppler b1 b2 b3 n1 n2 n3

noncomputable def D1 (b μ : ℝ) : ℝ := gamma 0 0 b * (1 + b * μ)

noncomputable def ab (b μ : ℝ) : ℝ := (μ + b) / (1 + b * μ)

noncomputable def areaDist (dS dΩ : ℝ) : ℝ := Real.sqrt (dS / dΩ)

noncomputable def redshiftOf (Es E : ℝ) : ℝ := Es / E - 1

noncomputable def planckOcc (x : ℝ) : ℝ := 1 / (Real.exp x - 1)

theorem core (x y z : ℝ) (hs : s x y z < 1) :
    0 < gamma x y z ∧ gamma x y z ^ 2 * (1 - s x y z) = 1 ∧
      h x y z * s x y z = gamma x y z - 1

theorem s_neg (x y z : ℝ) : s (-x) (-y) (-z) = s x y z

theorem gamma_neg (x y z : ℝ) : gamma (-x) (-y) (-z) = gamma x y z

theorem h_neg (x y z : ℝ) : h (-x) (-y) (-z) = h x y z

theorem dot_bound (b1 b2 b3 n1 n2 n3 : ℝ) :
    dot3 b1 b2 b3 n1 n2 n3 ^ 2 ≤ s b1 b2 b3 * s n1 n2 n3

theorem dot_sq_lt_one {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    dot3 b1 b2 b3 n1 n2 n3 ^ 2 < 1

theorem one_add_dot_pos {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    0 < 1 + dot3 b1 b2 b3 n1 n2 n3

theorem one_sub_dot_pos {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    0 < 1 - dot3 b1 b2 b3 n1 n2 n3

theorem photon_null (E n1 n2 n3 : ℝ) (hn : s n1 n2 n3 = 1) :
    mink (photon E n1 n2 n3) (photon E n1 n2 n3) = 0

theorem photon_future {E : ℝ} (hE : 0 < E) (n1 n2 n3 : ℝ) : 0 < photon E n1 n2 n3 0

theorem energy_e0 (k : V) : energy e0 k = k 0

theorem energy_old (E n1 n2 n3 : ℝ) : energy e0 (photon E n1 n2 n3) = E

theorem energy_new (b1 b2 b3 E n1 n2 n3 : ℝ) :
    energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) = doppler b1 b2 b3 n1 n2 n3 * E

theorem doppler_pos {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    0 < doppler b1 b2 b3 n1 n2 n3

theorem doppler_eq_energy_ratio (b1 b2 b3 n1 n2 n3 : ℝ) {E : ℝ} (hE : 0 < E) :
    energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) / energy e0 (photon E n1 n2 n3) =
      doppler b1 b2 b3 n1 n2 n3

theorem mink_eq (x y : V) : mink x y = x ⬝ᵥ (eta *ᵥ y)

theorem mink_boost {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (x y : V) :
    mink (Bst b1 b2 b3 *ᵥ x) (Bst b1 b2 b3 *ᵥ y) = mink x y

theorem Binv_eq (b1 b2 b3 : ℝ) : Binv b1 b2 b3 = Bst (-b1) (-b2) (-b3)

theorem Bst_mul_Binv {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Bst b1 b2 b3 * Binv b1 b2 b3 = 1

theorem Binv_mul_Bst {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    Binv b1 b2 b3 * Bst b1 b2 b3 = 1

theorem mink_newComp {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (x y : V) :
    mink (newComp b1 b2 b3 x) (newComp b1 b2 b3 y) = mink x y

theorem energy_frame_independent {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (u k : V) :
    energy (newComp b1 b2 b3 u) (newComp b1 b2 b3 k) = energy u k ∧
    energy (Bst b1 b2 b3 *ᵥ u) (Bst b1 b2 b3 *ᵥ k) = energy u k

theorem newComp_observer {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) :
    newComp b1 b2 b3 (fourVelocity b1 b2 b3) = e0

theorem same_ray_components {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (k : V) :
    Bst b1 b2 b3 *ᵥ newComp b1 b2 b3 k = k

theorem newComp_energy {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) (k : V) :
    newComp b1 b2 b3 k 0 = energy (fourVelocity b1 b2 b3) k

theorem newComp_photon (b1 b2 b3 E n1 n2 n3 : ℝ) :
    newComp b1 b2 b3 (photon E n1 n2 n3) =
      ![doppler b1 b2 b3 n1 n2 n3 * E,
        -(E * (n1 + gamma b1 b2 b3 * b1 + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * b1)),
        -(E * (n2 + gamma b1 b2 b3 * b2 + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * b2)),
        -(E * (n3 + gamma b1 b2 b3 * b3 + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * b3))]

theorem newDir_formula {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1)
    {E : ℝ} (hE : 0 < E) (i : Fin 3) :
    dirOf (newComp b1 b2 b3 (photon E n1 n2 n3)) i = aberr b1 b2 b3 n1 n2 n3 i

theorem oldDir (n1 n2 n3 : ℝ) {E : ℝ} (hE : 0 < E) (i : Fin 3) :
    dirOf (photon E n1 n2 n3) i = ![n1, n2, n3] i

theorem dir_unit {k : V} (hk : mink k k = 0) (h0 : k 0 ≠ 0) :
    s (dirOf k 0) (dirOf k 1) (dirOf k 2) = 1

theorem dir_photon {k : V} (h0 : k 0 ≠ 0) :
    photon (k 0) (dirOf k 0) (dirOf k 1) (dirOf k 2) = k

theorem aberr_unit {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    s (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2) = 1

theorem aberr_dot {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
        (aberr b1 b2 b3 n1 n2 n3 2) * doppler b1 b2 b3 n1 n2 n3 =
      dot3 b1 b2 b3 n1 n2 n3 + gamma b1 b2 b3 * s b1 b2 b3
        + h b1 b2 b3 * dot3 b1 b2 b3 n1 n2 n3 * s b1 b2 b3

theorem doppler_reciprocal {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hn : s n1 n2 n3 = 1) :
    doppler b1 b2 b3 n1 n2 n3 *
      (gamma b1 b2 b3 * (1 - dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0)
        (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2))) = 1

theorem aberr_surjective {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {m1 m2 m3 : ℝ}
    (hm : s m1 m2 m3 = 1) :
    ∃ n1 n2 n3 : ℝ, s n1 n2 n3 = 1 ∧ aberr b1 b2 b3 n1 n2 n3 0 = m1 ∧
      aberr b1 b2 b3 n1 n2 n3 1 = m2 ∧ aberr b1 b2 b3 n1 n2 n3 2 = m3

theorem gamma1_core {b : ℝ} (hb : b ^ 2 < 1) :
    0 < gamma 0 0 b ∧ gamma 0 0 b ^ 2 * (1 - b ^ 2) = 1

theorem one_add_pos_of_mem {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    0 < 1 + b * μ

theorem D1_pos {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) : 0 < D1 b μ

theorem ab_hasDerivAt {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : 1 + b * μ ≠ 0) :
    HasDerivAt (ab b) ((D1 b μ ^ 2)⁻¹) μ

theorem solid_angle_jacobian {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    deriv (ab b) μ = (D1 b μ ^ 2)⁻¹

theorem ab_endpoints {b : ℝ} (hb : b ^ 2 < 1) : ab b (-1) = -1 ∧ ab b 1 = 1

theorem ab_mem {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    ab b μ ∈ Icc (-1 : ℝ) 1

theorem ab_strictMonoOn {b : ℝ} (hb : b ^ 2 < 1) : StrictMonoOn (ab b) (Icc (-1 : ℝ) 1)

theorem ab_inverse {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1) :
    ab (-b) (ab b μ) = μ ∧ ab b (ab (-b) μ) = μ

theorem D1_inv_sq_continuousOn {b : ℝ} (hb : b ^ 2 < 1) {S : Set ℝ} (hS : S ⊆ Icc (-1 : ℝ) 1) :
    ContinuousOn (fun x => (D1 b x ^ 2)⁻¹) S

theorem solid_angle_change_of_variables {b : ℝ} (hb : b ^ 2 < 1) {g : ℝ → ℝ}
    (hg : ContinuousOn g (Icc (-1 : ℝ) 1)) :
    ∫ μ in (-1 : ℝ)..1, g (ab b μ) * (D1 b μ ^ 2)⁻¹ = ∫ μ' in (-1 : ℝ)..1, g μ'

theorem sphere_chart_change_of_variables {b : ℝ} (hb : b ^ 2 < 1) {g : ℝ → ℝ → ℝ}
    (hg : ∀ φ, ContinuousOn (fun μ => g μ φ) (Icc (-1 : ℝ) 1)) :
    ∫ φ in (0 : ℝ)..2 * π, ∫ μ in (-1 : ℝ)..1, g (ab b μ) φ * (D1 b μ ^ 2)⁻¹ =
      ∫ φ in (0 : ℝ)..2 * π, ∫ μ' in (-1 : ℝ)..1, g μ' φ

theorem total_solid_angle {b : ℝ} (hb : b ^ 2 < 1) :
    ∫ φ in (0 : ℝ)..2 * π, ∫ μ in (-1 : ℝ)..1, (D1 b μ ^ 2)⁻¹ = 4 * π

theorem band_solid_angle {b μ1 μ2 : ℝ} (hb : b ^ 2 < 1) (h1 : μ1 ∈ Icc (-1 : ℝ) 1)
    (h2 : μ2 ∈ Icc (-1 : ℝ) 1) (φ1 φ2 : ℝ) :
    (ab b μ2 - ab b μ1) * (φ2 - φ1) = (∫ μ in μ1..μ2, (D1 b μ ^ 2)⁻¹) * (φ2 - φ1)

theorem areaDist_aberration {b μ : ℝ} (hb : b ^ 2 < 1) (hμ : μ ∈ Icc (-1 : ℝ) 1)
    (dS dΩ : ℝ) :
    areaDist dS (deriv (ab b) μ * dΩ) = D1 b μ * areaDist dS dΩ

theorem chart_link {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1) (hb0 : 0 < s b1 b2 b3)
    (hn : s n1 n2 n3 = 1) {ℓ μ : ℝ} (hℓ : ℓ = Real.sqrt (s b1 b2 b3))
    (hμ : μ = dot3 b1 b2 b3 n1 n2 n3 / ℓ) :
    ℓ ^ 2 < 1 ∧ μ ∈ Icc (-1 : ℝ) 1 ∧
    doppler b1 b2 b3 n1 n2 n3 = D1 ℓ μ ∧
    dot3 b1 b2 b3 (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1)
        (aberr b1 b2 b3 n1 n2 n3 2) / ℓ = ab ℓ μ ∧
    ∀ i : Fin 3, aberr b1 b2 b3 n1 n2 n3 i - ab ℓ μ * (![b1, b2, b3] i / ℓ) =
      (![n1, n2, n3] i - μ * (![b1, b2, b3] i / ℓ)) / doppler b1 b2 b3 n1 n2 n3

theorem redshift_endpoint {Es E D : ℝ} (hE : 0 < E) (hD : 0 < D) :
    redshiftOf Es (D * E) = zNew (redshiftOf Es E) D

theorem endpoint_optical_same_ray {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1)
    (hb0 : 0 < s b1 b2 b3) (hn : s n1 n2 n3 = 1) {E Es dS dΩ ℓ μ : ℝ} (hE : 0 < E)
    (hℓ : ℓ = Real.sqrt (s b1 b2 b3)) (hμ : μ = dot3 b1 b2 b3 n1 n2 n3 / ℓ) :
    redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3)) =
        zNew (redshiftOf Es (energy e0 (photon E n1 n2 n3))) (doppler b1 b2 b3 n1 n2 n3) ∧
    areaDist dS (deriv (ab ℓ) μ * dΩ) =
        dANew (areaDist dS dΩ) (doppler b1 b2 b3 n1 n2 n3) ∧
    (1 + redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3))) *
        areaDist dS (deriv (ab ℓ) μ * dΩ) =
      (1 + redshiftOf Es (energy e0 (photon E n1 n2 n3))) * areaDist dS dΩ

theorem luminosity_from_reciprocity {z dA dL dL' D : ℝ} (hD : 0 < D)
    (hrecOld : dL = (1 + z) ^ 2 * dA)
    (hrecNew : dL' = (1 + zNew z D) ^ 2 * dANew dA D) :
    dL' = dL / D ∧ dL' = dLNew dL D

theorem distance_ratio_invariant {z dA dL dL' D : ℝ} (hD : 0 < D) (hz : 1 + z ≠ 0)
    (hrecOld : dL = (1 + z) ^ 2 * dA)
    (hrecNew : dL' = (1 + zNew z D) ^ 2 * dANew dA D) :
    dL' / (1 + zNew z D) = dL / (1 + z)

theorem endpoint_luminosity_same_ray {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1)
    (hb0 : 0 < s b1 b2 b3) (hn : s n1 n2 n3 = 1) {E Es dS dΩ ℓ μ dL dL' : ℝ} (hE : 0 < E)
    (hℓ : ℓ = Real.sqrt (s b1 b2 b3)) (hμ : μ = dot3 b1 b2 b3 n1 n2 n3 / ℓ)
    (hrecOld : dL = (1 + redshiftOf Es (energy e0 (photon E n1 n2 n3))) ^ 2 * areaDist dS dΩ)
    (hrecNew : dL' = (1 + redshiftOf Es (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3))) ^ 2
        * areaDist dS (deriv (ab ℓ) μ * dΩ)) :
    dL' = dL / doppler b1 b2 b3 n1 n2 n3

theorem planckOcc_injOn : InjOn planckOcc (Ioi 0)

theorem temperature_transform {E E' T0 T' : ℝ} (hE : 0 < E) (hE' : 0 < E') (hT0 : 0 < T0)
    (hT' : 0 < T') (hocc : planckOcc (E' / T') = planckOcc (E / T0)) :
    T' = T0 * (E' / E)

theorem inverse_temperature_affine {b1 b2 b3 n1 n2 n3 : ℝ} (hb : s b1 b2 b3 < 1)
    (hn : s n1 n2 n3 = 1) {E T0 T' : ℝ} (hE : 0 < E) (hT0 : 0 < T0) (hT' : 0 < T')
    (hocc : planckOcc (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) / T') =
      planckOcc (energy e0 (photon E n1 n2 n3) / T0)) :
    T' = doppler b1 b2 b3 n1 n2 n3 * T0 ∧
    1 / T' = gamma b1 b2 b3 / T0 +
      dot3 (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
        (-(gamma b1 b2 b3 * b3 / T0))
        (aberr b1 b2 b3 n1 n2 n3 0) (aberr b1 b2 b3 n1 n2 n3 1) (aberr b1 b2 b3 n1 n2 n3 2)

theorem affine_coeff_domain {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {T0 : ℝ} (hT0 : 0 < T0) :
    0 < gamma b1 b2 b3 / T0 ∧
    s (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
        (-(gamma b1 b2 b3 * b3 / T0)) < (gamma b1 b2 b3 / T0) ^ 2 ∧
    (gamma b1 b2 b3 / T0) ^ 2 -
        s (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
          (-(gamma b1 b2 b3 * b3 / T0)) = 1 / T0 ^ 2

theorem inverse_temperature_inversion {a c1 c2 c3 : ℝ} (ha : 0 < a)
    (hc : s c1 c2 c3 < a ^ 2) :
    s (-c1 / a) (-c2 / a) (-c3 / a) < 1 ∧
    gamma (-c1 / a) (-c2 / a) (-c3 / a) / a = 1 / Real.sqrt (a ^ 2 - s c1 c2 c3) ∧
    ∀ m1 m2 m3 : ℝ, a + dot3 c1 c2 c3 m1 m2 m3 =
      gamma (-c1 / a) (-c2 / a) (-c3 / a) * (1 - dot3 (-c1 / a) (-c2 / a) (-c3 / a) m1 m2 m3) /
        (gamma (-c1 / a) (-c2 / a) (-c3 / a) / a)

theorem isotropic_blackbody_criterion (invT : ℝ → ℝ → ℝ → ℝ) :
    (∃ T0 b1 b2 b3 : ℝ, 0 < T0 ∧ s b1 b2 b3 < 1 ∧ ∀ m1 m2 m3 : ℝ, s m1 m2 m3 = 1 →
        invT m1 m2 m3 = gamma b1 b2 b3 * (1 - dot3 b1 b2 b3 m1 m2 m3) / T0) ↔
    (∃ a c1 c2 c3 : ℝ, 0 < a ∧ s c1 c2 c3 < a ^ 2 ∧ ∀ m1 m2 m3 : ℝ, s m1 m2 m3 = 1 →
        invT m1 m2 m3 = a + dot3 c1 c2 c3 m1 m2 m3)

theorem boosted_isotropic_sky {b1 b2 b3 : ℝ} (hb : s b1 b2 b3 < 1) {T0 : ℝ} (hT0 : 0 < T0)
    {m1 m2 m3 : ℝ} (hm : s m1 m2 m3 = 1) :
    ∃ n1 n2 n3 : ℝ, s n1 n2 n3 = 1 ∧ aberr b1 b2 b3 n1 n2 n3 0 = m1 ∧
      aberr b1 b2 b3 n1 n2 n3 1 = m2 ∧ aberr b1 b2 b3 n1 n2 n3 2 = m3 ∧
      ∀ E T' : ℝ, 0 < E → 0 < T' →
        planckOcc (energy (fourVelocity b1 b2 b3) (photon E n1 n2 n3) / T') =
          planckOcc (energy e0 (photon E n1 n2 n3) / T0) →
        1 / T' = gamma b1 b2 b3 / T0 +
          dot3 (-(gamma b1 b2 b3 * b1 / T0)) (-(gamma b1 b2 b3 * b2 / T0))
            (-(gamma b1 b2 b3 * b3 / T0)) m1 m2 m3

theorem gamma_zero : gamma 0 0 0 = 1

theorem ab_zero : ab 0 = id

theorem boundary_beta_zero (n1 n2 n3 μ : ℝ) (k : V) :
    doppler 0 0 0 n1 n2 n3 = 1 ∧ newComp 0 0 0 k = k ∧
    (∀ i, aberr 0 0 0 n1 n2 n3 i = ![n1, n2, n3] i) ∧
    ab 0 μ = μ ∧ D1 0 μ = 1 ∧ deriv (ab 0) μ = 1 ∧
    (∀ z, zNew z 1 = z) ∧ (∀ dA, dANew dA 1 = dA) ∧ (∀ dL, dLNew dL 1 = dL)

theorem temperature_beta_zero {n1 n2 n3 E T0 T' : ℝ} (hn : s n1 n2 n3 = 1) (hE : 0 < E)
    (hT0 : 0 < T0) (hT' : 0 < T')
    (hocc : planckOcc (energy (fourVelocity 0 0 0) (photon E n1 n2 n3) / T') =
      planckOcc (energy e0 (photon E n1 n2 n3) / T0)) :
    T' = T0

theorem boundary_z_zero {dA D : ℝ} (hD : 0 < D) : (1 + zNew 0 D) * dANew dA D = dA

theorem gamma_three_fifths : gamma 0 0 (3 / 5) = 5 / 4

theorem nonvacuity_witness :
    s 0 0 (3 / 5) < 1 ∧ 0 < s 0 0 (3 / 5) ∧ s 0 0 1 = 1 ∧ doppler 0 0 (3 / 5) 0 0 1 = 2

theorem distinct_ray_counterexample :
    energy e0 (photon 1 0 0 1) = 1 ∧
    energy (fourVelocity 0 0 (3 / 5)) (photon 1 0 0 1) = 2 ∧
    doppler 0 0 (3 / 5) 0 0 (-1) = 1 / 2 ∧
    (1 + zNew 0 (doppler 0 0 (3 / 5) 0 0 (-1))) * dANew 1 (doppler 0 0 (3 / 5) 0 0 1) ≠
      (1 + 0) * 1

```
