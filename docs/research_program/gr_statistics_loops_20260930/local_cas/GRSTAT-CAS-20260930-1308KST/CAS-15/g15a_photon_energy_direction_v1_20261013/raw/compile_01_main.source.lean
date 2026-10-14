/-
G15-A (GR-CAS-15, C01): photon energy and rest direction from the normalized
velocity jet, source-forward L = U + c e, derivative-first W.

Source: supplements/DOSSIER_POSITIVE_BRIDGE.md (P0) and (B1); conventions
cas/COMMON_SPEC.md.  See SOURCE_RECOVERY.md and FROZEN_TARGETS.md.

Model: components in a parallel-propagated orthonormal frame along the ray,
metric diag(-1,1,1,1); covariant derivative along the ray = derivative of
components in the ray parameter s (tangent L).
-/
import Mathlib

open Filter Topology

namespace G15A

abbrev V := Fin 4 → ℝ

/-- Minkowski metric, signature (-,+,+,+), orthonormal-frame components. -/
def mink (x y : V) : ℝ := -(x 0 * y 0) + x 1 * y 1 + x 2 * y 2 + x 3 * y 3

/-- Unit observer `u = U / c`. -/
noncomputable def uvec (c : ℝ) (U : V) : V := c⁻¹ • U

/-- Rest metric `h_ab X^a Y^b`, `h_ab = g_ab + u_a u_b`. -/
noncomputable def hform (c : ℝ) (U X Y : V) : ℝ :=
  mink X Y + mink (uvec c U) X * mink (uvec c U) Y

/-- Rest projection `h^a_b X^b = X + (u·X) u`. -/
noncomputable def hproj (c : ℝ) (U X : V) : V :=
  X + mink (uvec c U) X • uvec c U

/-- (P0) derivative-first normalized velocity jet: `Qjet X Y = X^a Y^b ∇_a U_b`,
`∇_a U_b = (θ/3) h_ab + σ_ab + W_ab - u_a A_b / c`. -/
noncomputable def Qjet (c θ : ℝ) (σ W : LinearMap.BilinForm ℝ V) (A U X Y : V) : ℝ :=
  θ / 3 * hform c U X Y + σ X Y + W X Y - mink (uvec c U) X * mink A Y / c

/-- Source-forward null direction `L = U + c e`. -/
def Lvec (c : ℝ) (U e : V) : V := U + c • e

/-- Photon momentum `p = (E / c²) L`. -/
noncomputable def pvec (c E : ℝ) (U e : V) : V := (E / c ^ 2) • Lvec c U e

/-- `a = A / c`. -/
noncomputable def accel (c : ℝ) (A : V) : V := c⁻¹ • A

/-- `R(e) = θ/3 + a·e + σ:ee`. -/
noncomputable def Rrate (c θ : ℝ) (σ : LinearMap.BilinForm ℝ V) (A e : V) : ℝ :=
  θ / 3 + mink (accel c A) e + σ e e

/-- Covector `F·Y` of `F = P_e (a + σ e)`, `P_e = I - e eᵀ`. -/
noncomputable def Fcov (c : ℝ) (σ : LinearMap.BilinForm ℝ V) (A e Y : V) : ℝ :=
  mink (accel c A) Y + σ e Y - (mink (accel c A) e + σ e e) * mink e Y

/-- Rest direction recovered from a photon momentum. -/
noncomputable def restDir (c E : ℝ) (U p : V) : V := (c / E) • p - c⁻¹ • U

/-! ### Metric algebra -/

lemma mink_comm (x y : V) : mink x y = mink y x := by unfold mink; ring

lemma mink_add_left (x y z : V) : mink (x + y) z = mink x z + mink y z := by
  simp only [mink, Pi.add_apply]; ring

lemma mink_add_right (x y z : V) : mink z (x + y) = mink z x + mink z y := by
  simp only [mink, Pi.add_apply]; ring

lemma mink_sub_left (x y z : V) : mink (x - y) z = mink x z - mink y z := by
  simp only [mink, Pi.sub_apply]; ring

lemma mink_sub_right (x y z : V) : mink z (x - y) = mink z x - mink z y := by
  simp only [mink, Pi.sub_apply]; ring

lemma mink_smul_left (r : ℝ) (x z : V) : mink (r • x) z = r * mink x z := by
  simp only [mink, Pi.smul_apply, smul_eq_mul]; ring

lemma mink_smul_right (r : ℝ) (x z : V) : mink z (r • x) = r * mink z x := by
  simp only [mink, Pi.smul_apply, smul_eq_mul]; ring

lemma mink_zero_left (z : V) : mink 0 z = 0 := by
  simp only [mink, Pi.zero_apply]; ring

lemma bil_add_left (B : LinearMap.BilinForm ℝ V) (x y z : V) :
    B (x + y) z = B x z + B y z := by
  simp only [map_add, LinearMap.add_apply]

lemma bil_smul_left (B : LinearMap.BilinForm ℝ V) (r : ℝ) (x z : V) :
    B (r • x) z = r * B x z := by
  simp only [map_smul, LinearMap.smul_apply, smul_eq_mul]

lemma bil_add_right (B : LinearMap.BilinForm ℝ V) (x y z : V) :
    B z (x + y) = B z x + B z y := by
  simp only [map_add]

lemma bil_smul_right (B : LinearMap.BilinForm ℝ V) (r : ℝ) (x z : V) :
    B z (r • x) = r * B z x := by
  simp only [map_smul, smul_eq_mul]

/-- Product rule for the (constant-component) metric along the ray. -/
theorem hasDerivAt_mink {f k : ℝ → V} {f' k' : V} {t : ℝ}
    (hf : HasDerivAt f f' t) (hk : HasDerivAt k k' t) :
    HasDerivAt (fun s => mink (f s) (k s)) (mink f' (k t) + mink (f t) k') t := by
  have hf' := hasDerivAt_pi.1 hf
  have hk' := hasDerivAt_pi.1 hk
  have H := ((((hf' 0).mul (hk' 0)).neg.add ((hf' 1).mul (hk' 1))).add
    ((hf' 2).mul (hk' 2))).add ((hf' 3).mul (hk' 3))
  convert H using 1
  simp only [mink]; ring

/-! ### H1: definitions and null property -/

theorem H1_null_L {c : ℝ} {U e : V}
    (hUU : mink U U = -c ^ 2) (heU : mink e U = 0) (hee : mink e e = 1) :
    mink (Lvec c U e) (Lvec c U e) = 0 ∧ mink (Lvec c U e) U = -c ^ 2 := by
  have hUe : mink U e = 0 := by rw [mink_comm]; exact heU
  refine ⟨?_, ?_⟩
  · simp only [Lvec, mink_add_left, mink_add_right, mink_smul_left, mink_smul_right,
      hUU, heU, hUe, hee]
    ring
  · simp only [Lvec, mink_add_left, mink_smul_left, hUU, heU]
    ring

theorem H1_photon_energy {c E : ℝ} {U e : V} (hc : 0 < c)
    (hUU : mink U U = -c ^ 2) (heU : mink e U = 0) (hee : mink e e = 1) :
    mink (pvec c E U e) (pvec c E U e) = 0 ∧ -mink (pvec c E U e) U = E ∧
      hproj c U (pvec c E U e) = (E / c) • e := by
  obtain ⟨hLL, hLU⟩ := H1_null_L (c := c) hUU heU hee
  have hc0 : c ≠ 0 := hc.ne'
  refine ⟨?_, ?_, ?_⟩
  · simp only [pvec, mink_smul_left, mink_smul_right, hLL]; ring
  · simp only [pvec, mink_smul_left, hLU]; field_simp
  · have hpu : mink (uvec c U) (pvec c E U e) = -(E / c) := by
      simp only [uvec, pvec, mink_smul_left, mink_comm U (Lvec c U e), hLU]
      field_simp
    rw [hproj, hpu]
    funext i
    simp only [pvec, Lvec, uvec, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    field_simp
    ring

theorem H1_photon_decomposition {c E : ℝ} {U p : V} (hc : 0 < c) (hE : 0 < E)
    (hUU : mink U U = -c ^ 2) (hpp : mink p p = 0) (hpU : -mink p U = E) :
    mink (restDir c E U p) U = 0 ∧ mink (restDir c E U p) (restDir c E U p) = 1 ∧
      p = pvec c E U (restDir c E U p) := by
  have hc0 : c ≠ 0 := hc.ne'
  have hE0 : E ≠ 0 := hE.ne'
  have hUp : mink U p = -E := by rw [mink_comm]; linarith
  have hpU' : mink p U = -E := by linarith
  refine ⟨?_, ?_, ?_⟩
  · simp only [restDir, mink_sub_left, mink_smul_left, hpU', hUU]
    field_simp
    ring
  · simp only [restDir, mink_sub_left, mink_sub_right, mink_smul_left, mink_smul_right,
      hpU', hUp, hUU, hpp]
    field_simp
    ring
  · funext i
    simp only [pvec, Lvec, restDir, Pi.add_apply, Pi.sub_apply, Pi.smul_apply, smul_eq_mul]
    field_simp
    ring

/-! ### Pointwise core: geodesic contraction with the (P0) jet -/

/-- Pointwise core.  Inputs: the event data, the (P0) jet contracted with `L`
(`hjet`), the derivative of the constraint `e·U = 0` (`hconstr`), and the
expanded geodesic equation `∇_L p = 0` (`hgeo`). -/
theorem core
    {c θ E E' : ℝ} {σ W : LinearMap.BilinForm ℝ V} {U e A U' e' : V}
    (hc : 0 < c) (hE : E ≠ 0)
    (hUU : mink U U = -c ^ 2) (heU : mink e U = 0) (hee : mink e e = 1)
    (hσ_symm : ∀ X Y, σ X Y = σ Y X) (hσ_U : ∀ Y, σ U Y = 0)
    (hW_skew : ∀ X Y, W X Y = -W Y X) (hW_U : ∀ X, W X U = 0)
    (hA_U : mink A U = 0)
    (hjet : ∀ Y, mink U' Y = Qjet c θ σ W A U (Lvec c U e) Y)
    (hconstr : mink e' U + mink e U' = 0)
    (hgeo : (E / c ^ 2) • (U' + c • e') + (E' / c ^ 2) • Lvec c U e = 0) :
    E' / E = -Rrate c θ σ A e ∧
      ∀ Y, mink (hproj c U e') Y = -Fcov c σ A e Y + W Y e := by
  have hc0 : c ≠ 0 := hc.ne'
  -- the jet contracted with L, expanded
  have hUe : mink U e = 0 := by rw [mink_comm]; exact heU
  have hjetY : ∀ Y, mink U' Y =
      mink A Y + c * (θ / 3 * mink e Y + σ e Y + W e Y) := by
    intro Y
    rw [hjet Y]
    have hWUY : W U Y = 0 := by rw [hW_skew]; simp [hW_U]
    simp only [Qjet, hform, uvec, Lvec, mink_add_right, mink_smul_left, mink_smul_right,
      mink_add_left, bil_add_left, bil_smul_left, hσ_U, hWUY, hUU, hUe, heU]
    field_simp
    ring
  have hσeU : σ e U = 0 := by rw [hσ_symm]; exact hσ_U e
  have hWee : W e e = 0 := by have := hW_skew e e; linarith
  have hU'U : mink U' U = 0 := by
    rw [hjetY U, hA_U, mink_comm e U, hUe, hσeU, hW_U]; ring
  have hU'e : mink U' e = mink A e + c * (θ / 3 + σ e e) := by
    rw [hjetY e, hee, hWee]; ring
  have he'U : mink e' U = -(mink A e + c * (θ / 3 + σ e e)) := by
    rw [mink_comm e U'] at hconstr
    linarith
  -- contract the geodesic equation with U and with Y
  have gY : ∀ Y, E / c ^ 2 * (mink U' Y + c * mink e' Y) +
      E' / c ^ 2 * (mink U Y + c * mink e Y) = 0 := by
    intro Y
    have := congrArg (fun v => mink v Y) hgeo
    simpa only [Lvec, mink_add_left, mink_smul_left, mink_zero_left] using this
  have gU := gY U
  rw [hU'U, he'U, hUU, heU] at gU
  -- energy
  have hEn : E' = -E * (θ / 3 + mink A e / c + σ e e) := by
    field_simp at gU ⊢
    linear_combination gU
  have hR : E' / E = -Rrate c θ σ A e := by
    rw [hEn, Rrate, accel, mink_smul_left]
    field_simp
    ring
  refine ⟨hR, ?_⟩
  intro Y
  have hY := gY Y
  rw [hjetY Y, hEn] at hY
  have hWYe : W Y e = -W e Y := hW_skew Y e
  simp only [hproj, uvec, mink_add_left, mink_smul_left, mink_comm e' U, he'U,
    Fcov, accel, hWYe]
  rw [mink_comm U Y] at hY ⊢
  field_simp at hY ⊢
  linear_combination hY

/-! ### H2 / H3 on the ray -/

section ray

variable {c θ : ℝ} {σ W : LinearMap.BilinForm ℝ V} {A : V}
  {U e : ℝ → V} {E : ℝ → ℝ} {t : ℝ} {U' e' : V} {E' : ℝ}

/-- Shared derivation: the core applied to genuine derivatives along the ray. -/
theorem ray_core
    (hc : 0 < c) (hE : 0 < E t)
    (hUU : mink (U t) (U t) = -c ^ 2)
    (heU : ∀ᶠ s in 𝓝 t, mink (e s) (U s) = 0)
    (hee : mink (e t) (e t) = 1)
    (hσ_symm : ∀ X Y, σ X Y = σ Y X) (hσ_U : ∀ Y, σ (U t) Y = 0)
    (hW_skew : ∀ X Y, W X Y = -W Y X) (hW_U : ∀ X, W X (U t) = 0)
    (hA_U : mink A (U t) = 0)
    (hUd : HasDerivAt U U' t) (hed : HasDerivAt e e' t) (hEd : HasDerivAt E E' t)
    (hjet : ∀ Y, mink U' Y = Qjet c θ σ W A (U t) (Lvec c (U t) (e t)) Y)
    (hgeo : HasDerivAt (fun s => pvec c (E s) (U s) (e s)) 0 t) :
    E' / E t = -Rrate c θ σ A (e t) ∧
      ∀ Y, mink (hproj c (U t) e') Y = -Fcov c σ A (e t) Y + W Y (e t) := by
  -- derivative of the constraint e·U = 0 along the ray
  have h1 := hasDerivAt_mink hed hUd
  have h2 : HasDerivAt (fun s => mink (e s) (U s)) 0 t :=
    (hasDerivAt_const t (0 : ℝ)).congr_of_eventuallyEq heU
  have hconstr : mink e' (U t) + mink (e t) U' = 0 := h1.unique h2
  -- product rule for p = (E/c²)(U + c e), then the geodesic hypothesis
  have hp : HasDerivAt (fun s => pvec c (E s) (U s) (e s))
      ((E t / c ^ 2) • (U' + c • e') + (E' / c ^ 2) • Lvec c (U t) (e t)) t := by
    have := (hEd.div_const (c ^ 2)).smul (hUd.add (hed.const_smul c))
    simpa only [pvec, Lvec] using this
  have hg := hp.unique hgeo
  have heU0 : mink (e t) (U t) = 0 := heU.self_of_nhds
  exact core hc hE.ne' hUU heU0 hee hσ_symm hσ_U hW_skew hW_U hA_U hjet hconstr hg

theorem H2_energy_derivative
    (hc : 0 < c) (hE : 0 < E t)
    (hUU : mink (U t) (U t) = -c ^ 2)
    (heU : ∀ᶠ s in 𝓝 t, mink (e s) (U s) = 0)
    (hee : mink (e t) (e t) = 1)
    (hσ_symm : ∀ X Y, σ X Y = σ Y X) (hσ_U : ∀ Y, σ (U t) Y = 0)
    (hW_skew : ∀ X Y, W X Y = -W Y X) (hW_U : ∀ X, W X (U t) = 0)
    (hA_U : mink A (U t) = 0)
    (hUd : HasDerivAt U U' t) (hed : HasDerivAt e e' t) (hEd : HasDerivAt E E' t)
    (hjet : ∀ Y, mink U' Y = Qjet c θ σ W A (U t) (Lvec c (U t) (e t)) Y)
    (hgeo : HasDerivAt (fun s => pvec c (E s) (U s) (e s)) 0 t) :
    HasDerivAt (fun s => Real.log (E s)) (-Rrate c θ σ A (e t)) t := by
  have h := (ray_core hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U hUd hed hEd
    hjet hgeo).1
  rw [← h]
  exact hEd.log hE.ne'

theorem H3_direction_derivative
    (hc : 0 < c) (hE : 0 < E t)
    (hUU : mink (U t) (U t) = -c ^ 2)
    (heU : ∀ᶠ s in 𝓝 t, mink (e s) (U s) = 0)
    (hee : mink (e t) (e t) = 1)
    (hσ_symm : ∀ X Y, σ X Y = σ Y X) (hσ_U : ∀ Y, σ (U t) Y = 0)
    (hW_skew : ∀ X Y, W X Y = -W Y X) (hW_U : ∀ X, W X (U t) = 0)
    (hA_U : mink A (U t) = 0)
    (hUd : HasDerivAt U U' t) (hed : HasDerivAt e e' t) (hEd : HasDerivAt E E' t)
    (hjet : ∀ Y, mink U' Y = Qjet c θ σ W A (U t) (Lvec c (U t) (e t)) Y)
    (hgeo : HasDerivAt (fun s => pvec c (E s) (U s) (e s)) 0 t) :
    ∀ Y, mink (hproj c (U t) e') Y = -Fcov c σ A (e t) Y + W Y (e t) :=
  (ray_core hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U hUd hed hEd hjet hgeo).2

/-! ### H4: negative controls -/

theorem H4_W_convention_flip
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
    (hWe : ∃ Y, W Y (e t) ≠ 0) :
    ¬ ∀ Y, mink (hproj c (U t) e') Y = -Fcov c σ A (e t) Y - W Y (e t) := by
  intro hflip
  obtain ⟨Y, hY⟩ := hWe
  have h3 := H3_direction_derivative hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U
    hUd hed hEd hjet hgeo Y
  have := hflip Y
  apply hY
  linarith

theorem H4_direction_flip
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
    (hAe : mink A (e t) ≠ 0) :
    ¬ HasDerivAt (fun s => Real.log (E s)) (-Rrate c θ σ A (-(e t))) t := by
  intro hflip
  have h2 := H2_energy_derivative hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U
    hUd hed hEd hjet hgeo
  have heq := h2.unique hflip
  simp only [Rrate, accel, mink_smul_left, mink_smul_right, bil_smul_left,
    bil_smul_right, neg_smul, one_smul] at heq
  have hc0 : c ≠ 0 := hc.ne'
  apply hAe
  have : c⁻¹ * mink A (e t) = 0 := by
    have h' : mink A (-(e t)) = -mink A (e t) := by
      simpa using mink_smul_right (-1) (e t) A
    have hs : σ (-(e t)) (-(e t)) = σ (e t) (e t) := by
      simp only [map_neg, LinearMap.neg_apply, neg_neg]
    rw [h', hs] at heq
    linarith
  rcases mul_eq_zero.1 this with h | h
  · exact absurd h (inv_ne_zero hc0)
  · exact h

end ray

/-! ### H4(c): concrete non-vacuity witness -/

/-- `W X Y = X₂ Y₁ - X₁ Y₂` (derivative-first, spatial, skew). -/
def Ww : LinearMap.BilinForm ℝ V :=
  LinearMap.mk₂ ℝ (fun X Y => X 2 * Y 1 - X 1 * Y 2)
    (fun _ _ _ => by simp only [Pi.add_apply]; ring)
    (fun _ _ _ => by simp only [Pi.smul_apply, smul_eq_mul]; ring)
    (fun _ _ _ => by simp only [Pi.add_apply]; ring)
    (fun _ _ _ => by simp only [Pi.smul_apply, smul_eq_mul]; ring)

def Uw : ℝ → V := fun _ => ![1, 0, 0, 0]
def ew : ℝ → V := fun _ => ![0, 1, 0, 0]
def Ew : ℝ → ℝ := fun _ => 1
def Aw : V := ![0, -1, 1, 0]

lemma Ww_apply (X Y : V) : Ww X Y = X 2 * Y 1 - X 1 * Y 2 := rfl

theorem H4_concrete_controls :
    HasDerivAt (fun s : ℝ => Real.log (Ew s)) (-Rrate 1 3 0 Aw (ew 0)) 0 ∧
    (∀ Y, mink (hproj 1 (Uw 0) 0) Y = -Fcov 1 0 Aw (ew 0) Y + Ww Y (ew 0)) ∧
    (¬ ∀ Y, mink (hproj 1 (Uw 0) 0) Y = -Fcov 1 0 Aw (ew 0) Y - Ww Y (ew 0)) ∧
    ¬ HasDerivAt (fun s : ℝ => Real.log (Ew s)) (-Rrate 1 3 0 Aw (-(ew 0))) 0 := by
  have hc : (0 : ℝ) < 1 := one_pos
  have hE : 0 < Ew 0 := by simp [Ew]
  have hUU : mink (Uw 0) (Uw 0) = -(1 : ℝ) ^ 2 := by simp [mink, Uw]
  have heU : ∀ᶠ s in 𝓝 (0 : ℝ), mink (ew s) (Uw s) = 0 :=
    Filter.Eventually.of_forall (fun _ => by simp [mink, ew, Uw])
  have hee : mink (ew 0) (ew 0) = 1 := by simp [mink, ew]
  have hσ_symm : ∀ X Y : V, (0 : LinearMap.BilinForm ℝ V) X Y = (0 : LinearMap.BilinForm ℝ V) Y X := by
    intro X Y; simp
  have hσ_U : ∀ Y, (0 : LinearMap.BilinForm ℝ V) (Uw 0) Y = 0 := by intro Y; simp
  have hW_skew : ∀ X Y, Ww X Y = -Ww Y X := by intro X Y; simp only [Ww_apply]; ring
  have hW_U : ∀ X, Ww X (Uw 0) = 0 := by intro X; simp [Ww_apply, Uw]
  have hA_U : mink Aw (Uw 0) = 0 := by simp [mink, Aw, Uw]
  have hUd : HasDerivAt Uw 0 0 := hasDerivAt_const 0 _
  have hed : HasDerivAt ew 0 0 := hasDerivAt_const 0 _
  have hEd : HasDerivAt Ew 0 0 := hasDerivAt_const 0 _
  have hjet : ∀ Y, mink 0 Y = Qjet 1 3 0 Ww Aw (Uw 0) (Lvec 1 (Uw 0) (ew 0)) Y := by
    intro Y
    simp [mink, Qjet, hform, uvec, Lvec, Ww_apply, Uw, ew, Aw, Fin.sum_univ_four]
    ring
  have hgeo : HasDerivAt (fun s => pvec 1 (Ew s) (Uw s) (ew s)) 0 0 :=
    hasDerivAt_const 0 _
  have hWe : ∃ Y, Ww Y (ew 0) ≠ 0 := ⟨![0, 0, 1, 0], by simp [Ww_apply, ew]⟩
  have hAe : mink Aw (ew 0) ≠ 0 := by simp [mink, Aw, ew]
  refine ⟨?_, ?_, ?_, ?_⟩
  · exact H2_energy_derivative hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U
      hUd hed hEd hjet hgeo
  · exact H3_direction_derivative hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U
      hUd hed hEd hjet hgeo
  · exact H4_W_convention_flip hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U
      hUd hed hEd hjet hgeo hWe
  · exact H4_direction_flip hc hE hUU heU hee hσ_symm hσ_U hW_skew hW_U hA_U
      hUd hed hEd hjet hgeo hAe

end G15A
