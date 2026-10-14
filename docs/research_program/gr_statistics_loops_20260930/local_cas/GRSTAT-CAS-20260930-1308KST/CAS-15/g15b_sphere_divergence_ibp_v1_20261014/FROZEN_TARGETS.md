# G15-B frozen targets (frozen before any proof compile)

Frozen 2026-10-14, before the first compile of the G15-B module. Namespace
`G15B`, file `lean/G15BSphere.lean`. It imports `Mathlib` and the reviewed
G15-A module `G15APhoton`, unchanged and compiled into `raw/imports`. Any later
change to a statement below must be recorded as a deviation in
AUTHOR_RETURN.json. Source bindings are listed in SOURCE_RECOVERY.md.

Card G15-B (`HTT_ALL_OBLIGATIONS_20261011/tasks/G15-B.json`) has five
lean_steps. Each is mapped to a target block below:

| card step | content | target block |
|---|---|---|
| 1 | define the S² tangent gradient, divergence and measure, and the tangency of F | S |
| 2 | derive the pointwise divergence weights for eeᵀ, F·grad and We·grad | W |
| 3 | prove the closed-sphere divergence theorem under stated regularity | M, D, N |
| 4 | integrate by parts componentwise for the matrix-valued integrals | I |
| 5 | show the actual weak quadrupole needs angular polynomial degree ≤ 4 | G |
| (requires G15-A) | link F and R to the reviewed G15-A definitions | B |

## Model and route (declared)

* The sphere is `S2 := Metric.sphere (0 : E3) 1` with
  `E3 := EuclideanSpace ℝ (Fin 3)`. These are the rest-space unit propagation
  directions `e`.
* Scalar fields (brightness `I`) and vector fields (`Y`, `F`, `We`) are given
  as ambient maps `E3 → ℝ` or `E3 → E3`. The regularity is `ContDiff ℝ 1`.
  Every C¹ function on S² has such an ambient extension, for example
  χ(|x|)·f(x/|x|) with a radial bump χ. That fact is classical and is NOT
  formalized. Target S1 proves that the tangential operators depend only on
  the restriction to S², so the choice of extension is invisible.
* The tangential gradient and divergence are coordinate-free: they use the
  projector `P_e v = v − ⟪v,e⟫e` and the ambient Fréchet derivative only along
  tangent vectors. There are no polar or azimuthal coordinates, so there is no
  pole artifact.
* Measure: the core theorems hold for every finite measure `μ` on S2 that is
  invariant under all linear isometries of E3 (`RotInv μ`).
  `σS := volume.toSphere` is Mathlib's cone surface measure, with total mass
  3·vol(B³) = 4π. It is proved to satisfy `RotInv` and is the dΩ
  instantiation. Identifying `σS` with the Hausdorff surface measure is
  classical and NOT formalized; every identity is linear in μ.
* Divergence theorem route (stated as the prompt requires): "rotation
  invariance + Killing-field decomposition". This is neither the radial
  extension nor monomial moments.
  (i) For skew W, `exp(tW)` is a unitary flow mapping S² onto itself and
  preserving μ. Differentiating `t ↦ ∫ f(exp(tW)e) dμ` under the integral
  sign (dominated by a compact-sphere bound on `‖Df‖`) gives
  `∫ Df(e)(We) dμ = 0`.
  (ii) On S², a tangent field Y equals Σ_k h_k K_k e, where
  h_k = (x×Y)_k and K_k e = b_k × e. Pointwise,
  div_S Y = Σ_k Dh_k(e)(K_k e). Boundarylessness enters only in (i): the
  flow maps the closed surface S² onto itself and μ is invariant, so no
  boundary flux appears. Regularity (C¹) enters in the dominated
  differentiation and in the continuity/integrability on compact S².

## Definitions

```lean
abbrev E3 := EuclideanSpace ℝ (Fin 3)
abbrev S2 := Metric.sphere (0 : E3) 1
noncomputable def σS : Measure S2 := (volume : Measure E3).toSphere
noncomputable def bas (i : Fin 3) : E3 := EuclideanSpace.single i 1
noncomputable def Pt (e v : E3) : E3 := v - ⟪v, e⟫ • e                         -- P_e v
noncomputable def dS (f : E3 → ℝ) (e v : E3) : ℝ := fderiv ℝ f e (Pt e v)     -- (∇_S f)·v
noncomputable def gradS (f : E3 → ℝ) (e : E3) : E3 := ∑ i, dS f e (bas i) • bas i  -- ∇_S f = P_e ∇f
noncomputable def divS (Y : E3 → E3) (e : E3) : ℝ :=
  ∑ i, (fderiv ℝ Y e (Pt e (bas i))) i                                          -- tr(DY ∘ P_e)
def IsSkew (W : E3 →L[ℝ] E3) : Prop := ∀ x y, ⟪W x, y⟫ = -⟪x, W y⟫
noncomputable def trL (σ : E3 →L[ℝ] E3) : ℝ := ∑ i, (σ (bas i)) i
noncomputable def Ffield (a : E3) (σ : E3 →L[ℝ] E3) (x : E3) : E3 := Pt x (a + σ x)  -- F = P_e(a+σe)
noncomputable def Rrate3 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) : ℝ :=
  H + ⟪a, e⟫ + ⟪e, σ e⟫                                                         -- R = H_u + a·e + σ:ee
def sphMap (L : E3 ≃ₗᵢ[ℝ] E3) (e : S2) : S2 := ⟨L e, _⟩
def RotInv (μ : Measure S2) : Prop := ∀ L : E3 ≃ₗᵢ[ℝ] E3, MeasurePreserving (sphMap L) μ μ
noncomputable def Mmom (μ : Measure S2) (I : E3 → ℝ) (i j : Fin 3) : ℝ :=
  ∫ e : S2, I e * (e : E3) i * (e : E3) j ∂μ                                    -- M = ∫ I eeᵀ
noncomputable def Wm (W : E3 →L[ℝ] E3) (i j : Fin 3) : ℝ := (W (bas j)) i     -- matrix of W
noncomputable def wB5 (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) (i j : Fin 3) : ℝ :=
  (4 * H - ⟪e, σ e⟫) * e i * e j + a i * e j + e i * a j + (σ e) i * e j + e i * (σ e) j
```

`(4H − σ:ee)eeᵀ + aeᵀ + eaᵀ + (σe)eᵀ + e(σe)ᵀ` is the (B5) bracket, with
`H = H_u = θ/3`. Here σ is any linear map. The source's σ is symmetric and
trace-free; symmetry is never needed, and trace-freeness is assumed exactly
where the source uses it (`trL σ = 0`).

## S — definitions, intrinsic character, tangency

```lean
theorem Pt_tangent {e : E3} (he : ‖e‖ = 1) (v : E3) : ⟪Pt e v, e⟫ = 0
theorem gradS_inner (f : E3 → ℝ) (e v : E3) : ⟪gradS f e, v⟫ = dS f e v
theorem gradS_tangent (f : E3 → ℝ) {e : E3} (he : ‖e‖ = 1) : ⟪gradS f e, e⟫ = 0
theorem fderiv_eq_of_eqOn_sphere {F : Type*} [NormedAddCommGroup F] [NormedSpace ℝ F]
    {f g : E3 → F} {e v : E3} (hf : DifferentiableAt ℝ f e) (hg : DifferentiableAt ℝ g e)
    (hfg : ∀ x ∈ sphere (0 : E3) 1, f x = g x) (he : ‖e‖ = 1) (hv : ⟪v, e⟫ = 0) :
    fderiv ℝ f e v = fderiv ℝ g e v
theorem dS_eq_of_eqOn_sphere {f g : E3 → ℝ} {e : E3} (hf : DifferentiableAt ℝ f e)
    (hg : DifferentiableAt ℝ g e) (hfg : ∀ x ∈ sphere (0 : E3) 1, f x = g x) (he : ‖e‖ = 1) :
    dS f e = dS g e
theorem divS_eq_of_eqOn_sphere {Y Z : E3 → E3} {e : E3} (hY : DifferentiableAt ℝ Y e)
    (hZ : DifferentiableAt ℝ Z e) (hYZ : ∀ x ∈ sphere (0 : E3) 1, Y x = Z x) (he : ‖e‖ = 1) :
    divS Y e = divS Z e
theorem dS_eq_fderiv_of_tangent (f : E3 → ℝ) {e X : E3} (he : ‖e‖ = 1) (hX : ⟪X, e⟫ = 0) :
    dS f e X = fderiv ℝ f e X
theorem Ffield_tangent (a : E3) (σ : E3 →L[ℝ] E3) {e : E3} (he : ‖e‖ = 1) :
    ⟪Ffield a σ e, e⟫ = 0
theorem skew_tangent {W : E3 →L[ℝ] E3} (hW : IsSkew W) (e : E3) : ⟪W e, e⟫ = 0
```

## W — pointwise divergence weights

```lean
theorem divS_eq_trace (Y : E3 → E3) (e : E3) :
    divS Y e = ∑ i, (fderiv ℝ Y e (bas i)) i - ⟪e, fderiv ℝ Y e e⟫
theorem divS_skew {W : E3 →L[ℝ] E3} (hW : IsSkew W) (e : E3) : divS (fun x => W x) e = 0
theorem divS_Ffield (a : E3) (σ : E3 →L[ℝ] E3) {e : E3} (he : ‖e‖ = 1) :
    divS (Ffield a σ) e = trL σ - 2 * ⟪a, e⟫ - 3 * ⟪e, σ e⟫
theorem divS_Ffield_tracefree (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0) {e : E3}
    (he : ‖e‖ = 1) : divS (Ffield a σ) e = -2 * ⟪a, e⟫ - 3 * ⟪e, σ e⟫
theorem fderiv_quadWeight (i j : Fin 3) (e v : E3) :
    fderiv ℝ (fun x : E3 => x i * x j) e v = v i * e j + e i * v j
theorem divS_smul {g : E3 → ℝ} {Y : E3 → E3} {e : E3} (hg : DifferentiableAt ℝ g e)
    (hY : DifferentiableAt ℝ Y e) :
    divS (fun x => g x • Y x) e = dS g e (Y e) + g e * divS Y e
```

## M — invariant measure

```lean
theorem σS_rotInv : RotInv σS
```

## D — closed-sphere divergence theorem

```lean
theorem integral_fderiv_skew (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {f : E3 → ℝ} (hf : ContDiff ℝ 1 f) {W : E3 →L[ℝ] E3} (hW : IsSkew W) :
    ∫ e : S2, fderiv ℝ f e (W e) ∂μ = 0
theorem divergence_theorem (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {Y : E3 → E3} (hY : ContDiff ℝ 1 Y) (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) :
    ∫ e : S2, divS Y e ∂μ = 0
theorem divergence_theorem_σS {Y : E3 → E3} (hY : ContDiff ℝ 1 Y)
    (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) : ∫ e : S2, divS Y e ∂σS = 0
```

## N — negative control and non-vacuity

```lean
-- the tangency hypothesis cannot be dropped: radial field, div_S = 2 on S², integral ≠ 0
theorem divS_radial {e : E3} (he : ‖e‖ = 1) : divS (fun x => x) e = 2
theorem radial_negative_control : ∫ e : S2, divS (fun x => x) e ∂σS ≠ 0
-- non-vacuity: a concrete nonzero skew generator, and a nontrivial consequence of D+W
theorem skew_witness : IsSkew Kz ∧ Kz ≠ 0      -- Kz x = x₀ b₁ − x₁ b₀ (rotation about axis 2)
theorem witness_first_moment (a : E3) : ∫ e : S2, ⟪a, (e : E3)⟫ ∂σS = 0
```

`Kz : E3 →L[ℝ] E3` is defined in the source as
`Kuw (bas 0) (bas 1)`, where
`Kuw u w := (innerSL ℝ u).smulRight w - (innerSL ℝ w).smulRight u`.

## I — integration by parts and the matrix-valued componentwise identities

```lean
theorem ibp (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ) {f : E3 → ℝ}
    (hf : ContDiff ℝ 1 f) {Y : E3 → E3} (hY : ContDiff ℝ 1 Y)
    (htan : ∀ x ∈ sphere (0 : E3) 1, ⟪Y x, x⟫ = 0) :
    ∫ e : S2, fderiv ℝ f e (Y e) ∂μ = -∫ e : S2, f e * divS Y e ∂μ
-- (B4) R = [M,W]
theorem commutator_moments (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) {W : E3 →L[ℝ] E3} (hW : IsSkew W) (i j : Fin 3) :
    ∫ e : S2, fderiv ℝ I e (W e) * (e : E3) i * (e : E3) j ∂μ =
      ∑ k, (Mmom μ I i k * Wm W k j - Wm W i k * Mmom μ I k j)
-- (B5) angular part
theorem angular_B5 (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (H : ℝ) (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0)
    (i j : Fin 3) :
    ∫ e : S2, (fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e) * (e : E3) i * (e : E3) j ∂μ
      = -∫ e : S2, I e * wB5 H a σ e i j ∂μ
-- (B5) full weak residual, with C2 and T2 the supplied rank-2 moments
theorem weak_residual_B5 (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (H : ℝ) (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0)
    {Cc DI : E3 → ℝ} (i j : Fin 3)
    (hC : Integrable (fun e : S2 => Cc e * (e : E3) i * (e : E3) j) μ)
    (hD : Integrable (fun e : S2 => DI e * (e : E3) i * (e : E3) j) μ) :
    ∫ e : S2, (Cc e - DI e + fderiv ℝ I e (Ffield a σ e) - 4 * Rrate3 H a σ e * I e)
        * (e : E3) i * (e : E3) j ∂μ
      = ∫ e : S2, Cc e * (e : E3) i * (e : E3) j ∂μ - ∫ e : S2, DI e * (e : E3) i * (e : E3) j ∂μ
        - ∫ e : S2, I e * wB5 H a σ e i j ∂μ
-- (B2) ⇒ (B4)=(B5): conditional on the transport equation (B2) holding on S² (an INPUT, not proved here)
theorem weak_quadrupole_commutator (μ : Measure S2) [IsFiniteMeasure μ] (hμ : RotInv μ)
    {I : E3 → ℝ} (hI : ContDiff ℝ 1 I) (H : ℝ) (a : E3) {σ : E3 →L[ℝ] E3} (hσ : trL σ = 0)
    {W : E3 →L[ℝ] E3} (hW : IsSkew W) {Cc DI : E3 → ℝ} (i j : Fin 3)
    (hC : Integrable (fun e : S2 => Cc e * (e : E3) i * (e : E3) j) μ)
    (hD : Integrable (fun e : S2 => DI e * (e : E3) i * (e : E3) j) μ)
    (hB2 : ∀ e : S2, DI e + fderiv ℝ I e (W e - Ffield a σ e) + 4 * Rrate3 H a σ e * I e = Cc e) :
    ∫ e : S2, Cc e * (e : E3) i * (e : E3) j ∂μ - ∫ e : S2, DI e * (e : E3) i * (e : E3) j ∂μ
        - ∫ e : S2, I e * wB5 H a σ e i j ∂μ
      = ∑ k, (Mmom μ I i k * Wm W k j - Wm W i k * Mmom μ I k j)
```

## G — angular polynomial degree ≤ 4 (rank ≤ 4 brightness moments)

```lean
theorem wB5_degree_le_four (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      ∀ e : E3, MvPolynomial.eval (fun k => e k) p = wB5 H a σ e i j
theorem B5_rank_le_four_moments (μ : Measure S2) [IsFiniteMeasure μ] {I : E3 → ℝ}
    (hI : Continuous I) (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      (∀ m ∈ p.support, (m.sum fun _ n => n) ≤ 4) ∧
      ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
        ∑ m ∈ p.support, MvPolynomial.coeff m p * ∫ e : S2, I e * ∏ k, (e : E3) k ^ m k ∂μ
```

## B — bridge to the reviewed G15-A definitions (imported unchanged)

```lean
def emb3 (x : E3) : G15A.V := ![0, x 0, x 1, x 2]           -- rest-frame spatial embedding
noncomputable def sig4 (σ : E3 →L[ℝ] E3) : LinearMap.BilinForm ℝ G15A.V  -- σ4(X,Y) = ⟪σ(spatial X), spatial Y⟫
theorem bridge_Fcov {c : ℝ} (hc : c ≠ 0) (a : E3) (σ : E3 →L[ℝ] E3) (e y : E3) :
    G15A.Fcov c (sig4 σ) (emb3 (c • a)) (emb3 e) (emb3 y) = ⟪Ffield a σ e, y⟫
theorem bridge_Rrate {c : ℝ} (hc : c ≠ 0) (θ : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (e : E3) :
    G15A.Rrate c θ (sig4 σ) (emb3 (c • a)) (emb3 e) = Rrate3 (θ / 3) a σ e
```

(The rest frame is U = (c,0,0,0) and A = (0, c a), so `accel c A = (0, a)` as
in G15-A.)

## Scope boundary (not claimed)

* (B2) itself, i.e. Liouville/energy integration and the horizontal
  derivative 𝒟. It is an explicit hypothesis of `weak_quadrupole_commutator`
  only.
* The existence of C¹ ambient extensions of C¹ sphere functions.
* The identification of `σS` with the Hausdorff surface measure, and the
  total mass 4π.
* Sharpness of the degree bound. Distinct-eigenvalue inversion, gap bounds,
  stacked commutant (C03/C04) and quadrature (C3) are out of scope.
* Scientific admission.
