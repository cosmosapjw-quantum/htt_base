# G15-C frozen targets (frozen before any proof compile)

Frozen 2026-10-14, before the first compile of the G15-C module. Before this freeze
only the two reviewed imports were compiled (attempts 1-2, unchanged G15-A/G15-B
sources). Namespace `G15C`, file `lean/G15CBand.lean`. It imports `Mathlib`, the
reviewed `G15APhoton` and the reviewed `G15BSphere`, both unchanged and compiled into
`raw/imports`. Any later change to a statement below must be recorded as a deviation
in AUTHOR_RETURN.json. Source bindings are in SOURCE_RECOVERY.md.

## Card lean_steps → target blocks

| card step | content | blocks |
|---|---|---|
| 1 | recover brightness normalization and energy weight | definitions `bandI`, `bolI`, `bandC`, `bolC`, `bandD`, `bolD` |
| 2 | domination/regularity for exchanging transport derivative and energy integral | L1-L6 |
| 3 | finite-band endpoint flux kept in energy IBP | E1, E4, K1, K2, K5, M1, M2 |
| 4 | bolometric endpoint vanishing from IR/UV assumptions, separate from the band correction | E2, E3, E5, E6, E7, K3, K4, M3 |
| 5 | r=C−DI+F·∇I−4𝓡I=(We)·∇I with every term an actual moment | K2, M1, M2, M3, plus the transport link T1-T4 |

## Model (declared)

* `f : ℝ → ℝ → E3 → ℝ`, `f s E x` is the occupation in a horizontal chart. `s` is the
  parameter along L=U+ce, with dt/ds=1 in the rest frame. `E` is the u-measured energy.
  `x ∈ E3` is the ambient rest-direction variable, and directions are `x ∈ S²`. Fixed
  (E,x) along s is the source's horizontal comparison (DOSSIER:86), so 𝒟f := ∂_s f.
  Chart existence is NOT formalized.
* Angular derivatives use the ambient Fréchet derivative along tangent vectors, as in
  G15-B. `Wx − F(x)` is tangent on S².
* The finite band is [E1,E2] with E1 ≤ E2. The bolometric range is (0,∞) =
  `Ioi 0`, with Lebesgue measure.
* `Rrate3 H a σ e = H + ⟪a,e⟫ + ⟪e,σe⟫` (H = θ/3) and `Ffield a σ e = P_e(a+σe)` come
  from G15-B, unchanged.

## Definitions

```lean
def F3 (f : ℝ → ℝ → E3 → ℝ) : ℝ × ℝ × E3 → ℝ := fun q => f q.1 q.2.1 q.2.2
noncomputable def bandI (α E1 E2 : ℝ) (f : ℝ → ℝ → E3 → ℝ) (s : ℝ) (x : E3) : ℝ :=
  α * ∫ E in E1..E2, E ^ 3 * f s E x
noncomputable def bandD (α E1 E2 : ℝ) (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  α * ∫ E in E1..E2, E ^ 3 * deriv (fun s => f s E x) t
noncomputable def bandC (α E1 E2 : ℝ) (Ct : ℝ → E3 → ℝ) (x : E3) : ℝ :=
  α * ∫ E in E1..E2, E ^ 3 * Ct E x
noncomputable def bandFlux (α E1 E2 : ℝ) (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  α * (E2 ^ 4 * f t E2 x - E1 ^ 4 * f t E1 x)
noncomputable def bolI (α : ℝ) (f : ℝ → ℝ → E3 → ℝ) (s : ℝ) (x : E3) : ℝ :=
  α * ∫ E in Ioi (0 : ℝ), E ^ 3 * f s E x
noncomputable def bolD (α : ℝ) (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  α * ∫ E in Ioi (0 : ℝ), E ^ 3 * deriv (fun s => f s E x) t
noncomputable def bolC (α : ℝ) (Ct : ℝ → E3 → ℝ) (x : E3) : ℝ :=
  α * ∫ E in Ioi (0 : ℝ), E ^ 3 * Ct E x
-- expanded Liouville (photon-trajectory) operator with the (B1) rates
noncomputable def liouville (H : ℝ) (a : E3) (σ W : E3 →L[ℝ] E3) (f : ℝ → ℝ → E3 → ℝ)
    (t E : ℝ) (x : E3) : ℝ :=
  deriv (fun s => f s E x) t + -(Rrate3 H a σ x * E) * deriv (fun E' => f t E' x) E
    + fderiv ℝ (f t E) x (W x - Ffield a σ x)
-- band residual r_band = C − 𝒟I + F·∇I − 4𝓡I + 𝓡·flux   (flux kept)
noncomputable def bandResidual (α E1 E2 H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3)
    (f : ℝ → ℝ → E3 → ℝ) (Ct : ℝ → E3 → ℝ) (t : ℝ) (x : E3) : ℝ :=
  bandC α E1 E2 Ct x - bandD α E1 E2 f t x + fderiv ℝ (bandI α E1 E2 f t) x (Ffield a σ x)
    - 4 * Rrate3 H a σ x * bandI α E1 E2 f t x + Rrate3 H a σ x * bandFlux α E1 E2 f t x
-- bolometric regularity package (all fields are stated assumptions)
structure BolHyp (f : ℝ → ℝ → E3 → ℝ) (t : ℝ) (x : E3) where
  δ : ℝ
  bound : ℝ → ℝ
  hδ : 0 < δ
  c1 : ∀ E ∈ Ioi (0 : ℝ), ContDiff ℝ 1 (fun p : ℝ × E3 => f p.1 E p.2)
  dE : ∀ E ∈ Ioi (0 : ℝ), DifferentiableAt ℝ (fun E' => f t E' x) E
  meas : ∀ p ∈ ball ((t, x) : ℝ × E3) δ,
    AEStronglyMeasurable (fun E => E ^ 3 * f p.1 E p.2) (volume.restrict (Ioi 0))
  meas' : AEStronglyMeasurable
    (fun E => fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) (t, x)) (volume.restrict (Ioi 0))
  dom : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball ((t, x) : ℝ × E3) δ,
    ‖fderiv ℝ (fun p : ℝ × E3 => E ^ 3 * f p.1 E p.2) p‖ ≤ bound E
  domInt : IntegrableOn bound (Ioi 0)
  int3 : IntegrableOn (fun E => E ^ 3 * f t E x) (Ioi 0)
  int4 : IntegrableOn (fun E => E ^ 4 * deriv (fun E' => f t E' x) E) (Ioi 0)
  IR : Tendsto (fun E => E ^ 4 * f t E x) (𝓝[>] 0) (𝓝 0)
  UV : Tendsto (fun E => E ^ 4 * f t E x) atTop (𝓝 0)
-- G15-A lifts
noncomputable def U0 (c : ℝ) : G15A.V := ![c, 0, 0, 0]
noncomputable def w4 (W : E3 →L[ℝ] E3) : LinearMap.BilinForm ℝ G15A.V  -- w4 W X Y = ⟪sp X, W (sp Y)⟫
```

## E — energy integration by parts

```lean
theorem band_energy_ibp {g g' : ℝ → ℝ} {E1 E2 : ℝ}
    (hg : ∀ E ∈ uIcc E1 E2, HasDerivAt g (g' E) E) (hg' : IntervalIntegrable g' volume E1 E2) :
    ∫ E in E1..E2, E ^ 4 * g' E = (E2 ^ 4 * g E2 - E1 ^ 4 * g E1) - 4 * ∫ E in E1..E2, E ^ 3 * g E
theorem bolometric_energy_ibp_limits {g g' : ℝ → ℝ} {LIR LUV : ℝ}
    (hg : ∀ E ∈ Ioi (0 : ℝ), HasDerivAt g (g' E) E)
    (h4 : IntegrableOn (fun E => E ^ 4 * g' E) (Ioi 0)) (h3 : IntegrableOn (fun E => E ^ 3 * g E) (Ioi 0))
    (hIR : Tendsto (fun E => E ^ 4 * g E) (𝓝[>] 0) (𝓝 LIR))
    (hUV : Tendsto (fun E => E ^ 4 * g E) atTop (𝓝 LUV)) :
    ∫ E in Ioi (0 : ℝ), E ^ 4 * g' E = (LUV - LIR) - 4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * g E
theorem bolometric_energy_ibp {g g' : ℝ → ℝ}
    (hg : ∀ E ∈ Ioi (0 : ℝ), HasDerivAt g (g' E) E)
    (h4 : IntegrableOn (fun E => E ^ 4 * g' E) (Ioi 0)) (h3 : IntegrableOn (fun E => E ^ 3 * g E) (Ioi 0))
    (hIR : Tendsto (fun E => E ^ 4 * g E) (𝓝[>] 0) (𝓝 0))
    (hUV : Tendsto (fun E => E ^ 4 * g E) atTop (𝓝 0)) :
    ∫ E in Ioi (0 : ℝ), E ^ 4 * g' E = -4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * g E
-- E4: negative control; dropping the band flux is false (g ≡ 1 on [1,2], flux = 15)
theorem band_flux_negative_control :
    (∫ E in (1 : ℝ)..2, E ^ 4 * (0 : ℝ)) ≠ -4 * ∫ E in (1 : ℝ)..2, E ^ 3 * (1 : ℝ) ∧
    (∫ E in (1 : ℝ)..2, E ^ 4 * (0 : ℝ)) =
      ((2 : ℝ) ^ 4 * 1 - 1 ^ 4 * 1) - 4 * ∫ E in (1 : ℝ)..2, E ^ 3 * (1 : ℝ)
-- E5: IR/UV envelopes imply endpoint vanishing
theorem endpoint_vanishing_of_envelopes {g : ℝ → ℝ}
    (hIR : ∃ K δ : ℝ, 0 < δ ∧ ∀ E ∈ Ioo 0 δ, |E ^ 3 * g E| ≤ K)
    (hUV : ∃ K R : ℝ, ∀ E, R ≤ E → |E ^ 5 * g E| ≤ K) :
    Tendsto (fun E => E ^ 4 * g E) (𝓝[>] 0) (𝓝 0) ∧ Tendsto (fun E => E ^ 4 * g E) atTop (𝓝 0)
-- E6: BE/Planck shape (dimensionless E/kT) satisfies the envelopes
theorem planck_envelopes :
    (∃ K δ : ℝ, 0 < δ ∧ ∀ E ∈ Ioo 0 δ, |E ^ 3 * (1 / (Real.exp E - 1))| ≤ K) ∧
    (∃ K R : ℝ, ∀ E, R ≤ E → |E ^ 5 * (1 / (Real.exp E - 1))| ≤ K)
-- E7: non-vacuity of the bolometric hypotheses (g = e^{-E}) with its conclusion
theorem bolometric_witness :
    (∀ E ∈ Ioi (0 : ℝ), HasDerivAt (fun E => Real.exp (-E)) (-Real.exp (-E)) E) ∧
    IntegrableOn (fun E : ℝ => E ^ 4 * -Real.exp (-E)) (Ioi 0) ∧
    IntegrableOn (fun E : ℝ => E ^ 3 * Real.exp (-E)) (Ioi 0) ∧
    Tendsto (fun E : ℝ => E ^ 4 * Real.exp (-E)) (𝓝[>] 0) (𝓝 0) ∧
    Tendsto (fun E : ℝ => E ^ 4 * Real.exp (-E)) atTop (𝓝 0) ∧
    ∫ E in Ioi (0 : ℝ), E ^ 4 * -Real.exp (-E) = -4 * ∫ E in Ioi (0 : ℝ), E ^ 3 * Real.exp (-E)
```

## L — Leibniz interchange (domination and regularity)

```lean
theorem param_band {P : Type*} [NormedAddCommGroup P] [NormedSpace ℝ P] [ProperSpace P]
    {g : P → ℝ → ℝ} (hg : ContDiff ℝ 1 (fun q : P × ℝ => g q.1 q.2)) (a b : ℝ) :
    (∀ p₀ : P, HasFDerivAt (fun p => ∫ E in a..b, g p E)
        (∫ E in a..b, fderiv ℝ (fun p => g p E) p₀) p₀) ∧
    Continuous (fun q : P × ℝ => fderiv ℝ (fun p => g p q.2) q.1) ∧
    ContDiff ℝ 1 (fun p => ∫ E in a..b, g p E)
theorem band_hasDerivAt_s {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ) (x : E3) :
    HasDerivAt (fun s => bandI α E1 E2 f s x) (bandD α E1 E2 f t x) t
theorem band_contDiff_x {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ) :
    ContDiff ℝ 1 (bandI α E1 E2 f t)
theorem band_fderiv_x {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ) (x v : E3) :
    fderiv ℝ (bandI α E1 E2 f t) x v = α * ∫ E in E1..E2, E ^ 3 * fderiv ℝ (f t E) x v
theorem band_continuous_D {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) (α E1 E2 t : ℝ) :
    Continuous (bandD α E1 E2 f t)
theorem param_Ioi {P : Type*} [NormedAddCommGroup P] [NormedSpace ℝ P]
    {g : P → ℝ → ℝ} {p₀ : P} {δ : ℝ} {bound : ℝ → ℝ} (hδ : 0 < δ)
    (hmeas : ∀ p ∈ ball p₀ δ, AEStronglyMeasurable (g p) (volume.restrict (Ioi 0)))
    (hint : IntegrableOn (g p₀) (Ioi 0))
    (hdiff : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball p₀ δ, DifferentiableAt ℝ (fun p => g p E) p)
    (hmeas' : AEStronglyMeasurable (fun E => fderiv ℝ (fun p => g p E) p₀) (volume.restrict (Ioi 0)))
    (hbound : ∀ E ∈ Ioi (0 : ℝ), ∀ p ∈ ball p₀ δ, ‖fderiv ℝ (fun p => g p E) p‖ ≤ bound E)
    (hbint : IntegrableOn bound (Ioi 0)) :
    Integrable (fun E => fderiv ℝ (fun p => g p E) p₀) (volume.restrict (Ioi 0)) ∧
    HasFDerivAt (fun p => ∫ E in Ioi (0 : ℝ), g p E)
      (∫ E in Ioi (0 : ℝ), fderiv ℝ (fun p => g p E) p₀) p₀
```

## K — brightness equations (pointwise in x)

```lean
-- K1 band (B2) with explicit band-edge flux
theorem band_brightness_equation {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f))
    {α E1 E2 : ℝ} (hE : E1 ≤ E2) {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {Ct : ℝ → E3 → ℝ} {t : ℝ} {x : E3}
    (hkin : ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x) :
    HasDerivAt (fun s => bandI α E1 E2 f s x) (bandD α E1 E2 f t x) t ∧
    bandD α E1 E2 f t x + fderiv ℝ (bandI α E1 E2 f t) x (W x - Ffield a σ x)
      + 4 * Rrate3 H a σ x * bandI α E1 E2 f t x
      - Rrate3 H a σ x * bandFlux α E1 E2 f t x = bandC α E1 E2 Ct x
-- K2 r_band = (We)·∇I_band
theorem band_residual_eq {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f))
    {α E1 E2 : ℝ} (hE : E1 ≤ E2) {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {Ct : ℝ → E3 → ℝ} {t : ℝ} {x : E3}
    (hkin : ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x) :
    bandResidual α E1 E2 H a σ f Ct t x = fderiv ℝ (bandI α E1 E2 f t) x (W x)
-- K3 bolometric (B2), no flux; endpoint vanishing from h.IR / h.UV
theorem bol_brightness_equation {f : ℝ → ℝ → E3 → ℝ} {t : ℝ} {x : E3} (h : BolHyp f t x)
    {α H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3} {Ct : ℝ → E3 → ℝ}
    (hkin : ∀ E ∈ Ioi (0 : ℝ), liouville H a σ W f t E x = Ct E x) :
    HasDerivAt (fun s => bolI α f s x) (bolD α f t x) t ∧
    bolD α f t x + fderiv ℝ (bolI α f t) x (W x - Ffield a σ x)
      + 4 * Rrate3 H a σ x * bolI α f t x = bolC α Ct x
-- K4 non-vacuity of BolHyp
theorem bolHyp_witness (t : ℝ) (x : E3) : Nonempty (BolHyp (fun _ E _ => Real.exp (-E)) t x)
-- K5 COMM-BAND negative control at the brightness-equation level
def fone : ℝ → ℝ → E3 → ℝ := fun _ _ _ => 1
theorem band_flux_required :
    ContDiff ℝ 1 (F3 fone) ∧
    (∀ E ∈ Icc (1 : ℝ) 2, liouville 1 0 0 0 fone 0 E (bas 0) = (fun _ _ => (0 : ℝ)) E (bas 0)) ∧
    Rrate3 1 0 0 (bas 0) * bandFlux 1 1 2 fone 0 (bas 0) = 15 ∧
    bandD 1 1 2 fone 0 (bas 0) + fderiv ℝ (bandI 1 1 2 fone 0) (bas 0) (0 (bas 0) - Ffield 0 0 (bas 0))
      + 4 * Rrate3 1 0 0 (bas 0) * bandI 1 1 2 fone 0 (bas 0)
      ≠ bandC 1 1 2 (fun _ _ => (0 : ℝ)) (bas 0)
```

## M — moments (rank-two residual, band B5 with flux moment, bolometric B5)

```lean
theorem band_residual_moment (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) {α E1 E2 : ℝ} (hE : E1 ≤ E2)
    {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3} (hW : IsSkew W) {Ct : ℝ → E3 → ℝ} {t : ℝ}
    (hkin : ∀ x ∈ sphere (0 : E3) 1, ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x)
    (i j : Fin 3) :
    ∫ e : S2, bandResidual α E1 E2 H a σ f Ct t e * (e : E3) i * (e : E3) j ∂μ =
      ∑ k, (Mmom μ (bandI α E1 E2 f t) i k * Wm W k j - Wm W i k * Mmom μ (bandI α E1 E2 f t) k j)
theorem band_weak_quadrupole (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : ℝ → ℝ → E3 → ℝ} (hf : ContDiff ℝ 1 (F3 f)) {α E1 E2 : ℝ} (hE : E1 ≤ E2)
    {H : ℝ} {a : E3} {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0) {W : E3 →L[ℝ] E3} (hW : IsSkew W)
    {Ct : ℝ → E3 → ℝ} {t : ℝ}
    (hkin : ∀ x ∈ sphere (0 : E3) 1, ∀ E ∈ Icc E1 E2, liouville H a σ W f t E x = Ct E x)
    (i j : Fin 3) :
    Integrable (fun e : S2 => bandC α E1 E2 Ct e * (e : E3) i * (e : E3) j) μ ∧
    Integrable (fun e : S2 => bandD α E1 E2 f t e * (e : E3) i * (e : E3) j) μ ∧
    Integrable (fun e : S2 => Rrate3 H a σ e * bandFlux α E1 E2 f t e * (e : E3) i * (e : E3) j) μ ∧
    ∫ e : S2, bandC α E1 E2 Ct e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bandD α E1 E2 f t e * (e : E3) i * (e : E3) j ∂μ
      + ∫ e : S2, Rrate3 H a σ e * bandFlux α E1 E2 f t e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bandI α E1 E2 f t e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ (bandI α E1 E2 f t) i k * Wm W k j - Wm W i k * Mmom μ (bandI α E1 E2 f t) k j)
theorem bol_weak_quadrupole (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : ℝ → ℝ → E3 → ℝ} {t : ℝ} (h : ∀ x ∈ sphere (0 : E3) 1, BolHyp f t x)
    {α : ℝ} (hI : ContDiff ℝ 1 (bolI α f t))
    {H : ℝ} {a : E3} {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0) {W : E3 →L[ℝ] E3} (hW : IsSkew W)
    {Ct : ℝ → E3 → ℝ}
    (hkin : ∀ x ∈ sphere (0 : E3) 1, ∀ E ∈ Ioi (0 : ℝ), liouville H a σ W f t E x = Ct E x)
    (i j : Fin 3)
    (hC : Integrable (fun e : S2 => bolC α Ct e * (e : E3) i * (e : E3) j) μ)
    (hD : Integrable (fun e : S2 => bolD α f t e * (e : E3) i * (e : E3) j) μ) :
    ∫ e : S2, bolC α Ct e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bolD α f t e * (e : E3) i * (e : E3) j ∂μ
      - ∫ e : S2, bolI α f t e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ (bolI α f t) i k * Wm W k j - Wm W i k * Mmom μ (bolI α f t) k j)
```

## T — transport link to (B1) and G15-A

```lean
theorem liouville_chain {f : ℝ → ℝ → E3 → ℝ} {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {t : ℝ} {Eγ : ℝ → ℝ} {eγ : ℝ → E3}
    (hf : DifferentiableAt ℝ (F3 f) (t, Eγ t, eγ t))
    (hE : HasDerivAt Eγ (-(Rrate3 H a σ (eγ t) * Eγ t)) t)
    (he : HasDerivAt eγ (W (eγ t) - Ffield a σ (eγ t)) t) :
    HasDerivAt (fun s => f s (Eγ s) (eγ s)) (liouville H a σ W f t (Eγ t) (eγ t)) t
theorem liouville_of_transport {f : ℝ → ℝ → E3 → ℝ} {H : ℝ} {a : E3} {σ W : E3 →L[ℝ] E3}
    {Ct : ℝ → E3 → ℝ} {t : ℝ} {Eγ : ℝ → ℝ} {eγ : ℝ → E3}
    (hf : DifferentiableAt ℝ (F3 f) (t, Eγ t, eγ t))
    (hE : HasDerivAt Eγ (-(Rrate3 H a σ (eγ t) * Eγ t)) t)
    (he : HasDerivAt eγ (W (eγ t) - Ffield a σ (eγ t)) t)
    (hcoll : HasDerivAt (fun s => f s (Eγ s) (eγ s)) (Ct (Eγ t) (eγ t)) t) :
    liouville H a σ W f t (Eγ t) (eγ t) = Ct (Eγ t) (eγ t)
theorem energy_rate_of_G15A {c θ : ℝ} (hc : c ≠ 0) {a : E3} {σ : E3 →L[ℝ] E3} {e : E3}
    {Eγ : ℝ → ℝ} {t E' : ℝ} (hpos : 0 < Eγ t) (hEd : HasDerivAt Eγ E' t)
    (hlog : HasDerivAt (fun s => Real.log (Eγ s))
      (-G15A.Rrate c θ (sig4 σ) (emb3 (c • a)) (emb3 e)) t) :
    HasDerivAt Eγ (-(Rrate3 (θ / 3) a σ e * Eγ t)) t
theorem direction_rate_of_G15A {c : ℝ} (hc : c ≠ 0) (a : E3) (σ W : E3 →L[ℝ] E3) (e : E3)
    (e' : G15A.V)
    (h3 : ∀ Y, G15A.mink (G15A.hproj c (U0 c) e') Y =
      -G15A.Fcov c (sig4 σ) (emb3 (c • a)) (emb3 e) Y + w4 W Y (emb3 e)) :
    sp e' = W e - Ffield a σ e
```

## Negative controls / non-vacuity

* E4 `band_flux_negative_control` and K5 `band_flux_required`: COMM-BAND, dropping the
  band-edge flux is false on concrete admissible data.
* E6 `planck_envelopes`: the IR/UV envelope hypotheses hold for the BE/Planck shape.
* E7 `bolometric_witness`, K4 `bolHyp_witness`: the bolometric hypotheses are satisfiable.

## Explicit non-strengthening notes

* Band theorems need only C¹ of f on ℝ×ℝ×E3 (no positivity of E1, no decay).
  Domination is constructed, not assumed.
* Bolometric theorems allow an IR singularity of f at E=0 (BE-like). Regularity is
  required only for E>0, and domination is an explicit hypothesis. The moment-level
  bolometric theorem assumes smooth brightness (contract "Smoothbrightness") and moment
  integrability. These are explicit.
* No W is fitted; T_2 comes from the supplied f only.
