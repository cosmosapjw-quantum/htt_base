# G15-A frozen targets (frozen before any proof attempt)

Frozen 2026-10-13, before the first compile.  Namespace `G15A`, file
`lean/G15APhoton.lean`, `import Mathlib` only.  Any later change to a
statement below must be recorded as a deviation in AUTHOR_RETURN.json.

## Definitions (source binding in SOURCE_RECOVERY.md)

```lean
abbrev V := Fin 4 → ℝ
-- g = diag(-1,1,1,1), parallel orthonormal frame components (COMMON_SPEC l.4-5)
def mink (x y : V) : ℝ := -(x 0 * y 0) + x 1 * y 1 + x 2 * y 2 + x 3 * y 3
noncomputable def uvec (c : ℝ) (U : V) : V := c⁻¹ • U                    -- u = U/c
noncomputable def hform (c : ℝ) (U X Y : V) : ℝ :=                        -- h_ab X^a Y^b
  mink X Y + mink (uvec c U) X * mink (uvec c U) Y
noncomputable def hproj (c : ℝ) (U X : V) : V :=                          -- h^a_b X^b
  X + mink (uvec c U) X • uvec c U
-- (P0) derivative-first jet: Qjet X Y = X^a Y^b ∇_a U_b
noncomputable def Qjet (c θ : ℝ) (σ W : LinearMap.BilinForm ℝ V) (A U X Y : V) : ℝ :=
  θ / 3 * hform c U X Y + σ X Y + W X Y - mink (uvec c U) X * mink A Y / c
def Lvec (c : ℝ) (U e : V) : V := U + c • e                                -- L = U + c e
noncomputable def pvec (c E : ℝ) (U e : V) : V := (E / c ^ 2) • Lvec c U e -- p = (E/c²) L
noncomputable def accel (c : ℝ) (A : V) : V := c⁻¹ • A                    -- a = A/c
noncomputable def Rrate (c θ : ℝ) (σ : LinearMap.BilinForm ℝ V) (A e : V) : ℝ :=
  θ / 3 + mink (accel c A) e + σ e e                                      -- R(e)
noncomputable def Fcov (c : ℝ) (σ : LinearMap.BilinForm ℝ V) (A e Y : V) : ℝ :=
  mink (accel c A) Y + σ e Y - (mink (accel c A) e + σ e e) * mink e Y     -- F·Y, F=P_e(a+σe)
noncomputable def restDir (c E : ℝ) (U p : V) : V := (c / E) • p - c⁻¹ • U
```

Common jet/ray hypothesis block `JetRay` (used verbatim in H2, H3, H4a, H4b):

```lean
{c θ : ℝ} {σ W : LinearMap.BilinForm ℝ V} {A : V}
{U e : ℝ → V} {E : ℝ → ℝ} {t : ℝ} {U' e' : V} {E' : ℝ}
(hc : 0 < c) (hE : 0 < E t)
(hUU : mink (U t) (U t) = -c ^ 2)
(heU : ∀ᶠ s in 𝓝 t, mink (e s) (U s) = 0)
(hee : mink (e t) (e t) = 1)
(hσ_symm : ∀ X Y, σ X Y = σ Y X) (hσ_U : ∀ Y, σ (U t) Y = 0)
(hW_skew : ∀ X Y, W X Y = -W Y X) (hW_U : ∀ X, W X (U t) = 0)
(hA_U : mink A (U t) = 0)
(hUd : HasDerivAt U U' t) (hed : HasDerivAt e e' t) (hEd : HasDerivAt E E' t)
(hjet : ∀ Y, mink U' Y = Qjet c θ σ W A (U t) (Lvec c (U t) (e t)) Y)
(hgeo : HasDerivAt (fun s => pvec c (E s) (U s) (e s)) 0 t)
```

## H1 — definitions and null property

```lean
theorem H1_null_L {c : ℝ} {U e : V}
    (hUU : mink U U = -c ^ 2) (heU : mink e U = 0) (hee : mink e e = 1) :
    mink (Lvec c U e) (Lvec c U e) = 0 ∧ mink (Lvec c U e) U = -c ^ 2

theorem H1_photon_energy {c E : ℝ} {U e : V} (hc : 0 < c)
    (hUU : mink U U = -c ^ 2) (heU : mink e U = 0) (hee : mink e e = 1) :
    mink (pvec c E U e) (pvec c E U e) = 0 ∧ -mink (pvec c E U e) U = E ∧
      hproj c U (pvec c E U e) = (E / c) • e

theorem H1_photon_decomposition {c E : ℝ} {U p : V} (hc : 0 < c) (hE : 0 < E)
    (hUU : mink U U = -c ^ 2) (hpp : mink p p = 0) (hpU : -mink p U = E) :
    mink (restDir c E U p) U = 0 ∧ mink (restDir c E U p) (restDir c E U p) = 1 ∧
      p = pvec c E U (restDir c E U p)
```

## H2 — energy derivative (derived from geodesic + jet)

```lean
theorem H2_energy_derivative JetRay :
    HasDerivAt (fun s => Real.log (E s)) (-Rrate c θ σ A (e t)) t
```

## H3 — rest-direction derivative

```lean
theorem H3_direction_derivative JetRay :
    ∀ Y, mink (hproj c (U t) e') Y = -Fcov c σ A (e t) Y + W Y (e t)
```

(Covector form of the rest-space vector identity h∇_L e = −F + W e; Y ranges
over all of V, and the u-component of both sides vanishes.)

## H4 — sign / convention negative controls

```lean
-- (a) flipping the derivative-first W convention (W ↦ −W) breaks H3
theorem H4_W_convention_flip JetRay (hWe : ∃ Y, W Y (e t) ≠ 0) :
    ¬ ∀ Y, mink (hproj c (U t) e') Y = -Fcov c σ A (e t) Y - W Y (e t)

-- (b) replacing the source-forward e by the sourceward n = −e breaks H2
theorem H4_direction_flip JetRay (hAe : mink A (e t) ≠ 0) :
    ¬ HasDerivAt (fun s => Real.log (E s)) (-Rrate c θ σ A (-(e t))) t
```

(c) Non-vacuity witness `H4_concrete_controls`: c=1, t=0, θ=3, σ=0,
U ≡ (1,0,0,0), e ≡ (0,1,0,0), E ≡ 1, A=(0,−1,1,0),
W X Y = X 2 * Y 1 − X 1 * Y 2, U'=e'=0, E'=0.  The theorem proves that every
JetRay hypothesis holds for this instance (so H2/H3 apply and are
non-vacuous) and that both H4(a) and H4(b) premises hold, hence both flipped
formulas are false there while H2/H3 hold:

```lean
theorem H4_concrete_controls :
    HasDerivAt (fun s : ℝ => Real.log (Ew s)) (-Rrate 1 3 0 Aw (ew 0)) 0 ∧
    (∀ Y, mink (hproj 1 (Uw 0) 0) Y = -Fcov 1 0 Aw (ew 0) Y + Ww Y (ew 0)) ∧
    (¬ ∀ Y, mink (hproj 1 (Uw 0) 0) Y = -Fcov 1 0 Aw (ew 0) Y - Ww Y (ew 0)) ∧
    ¬ HasDerivAt (fun s : ℝ => Real.log (Ew s)) (-Rrate 1 3 0 Aw (-(ew 0))) 0
```

where `Uw ew : ℝ → V`, `Ew : ℝ → ℝ`, `Aw : V`, `Ww : LinearMap.BilinForm ℝ V`
are the constants above, and the proof must go through H2/H3/H4a/H4b (not by
direct evaluation alone), so that it certifies satisfiability of JetRay.

## Scope boundary

Single direction e at a single event; no claim about all directions
simultaneously as a tensor field, no geodesic existence, no frame existence,
no Liouville/brightness (B2) step.
