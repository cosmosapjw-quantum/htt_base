import Mathlib

/-!
# G09-A — source-bound definitions for CAS-09 components C01–C04

Source: `statistics/NATIVE_INFERENCE_THEOREMS.md`
(sha256 e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322),
§§1–3, 6–7; `gr/OPTICAL_THEOREMS.md` (6)–(8); `gr/FINITE_DISTANCE_THEOREM.md`.
See `SOURCE_RECOVERY.md` for the symbol-by-symbol source map.

Claim ceiling: finite/elementary mathematical components only.  Scientific admission: HOLD.
The physically realizable remainder set is deliberately *not* defined; only the enlarged
outer domain `Omega5` (source eq. (5)) and the latent-distance domain `Omega6` (eq. (6)) are.
-/

namespace G09A

open Filter Topology

/-! ## Shared types and source formulas (NATIVE (1), OPTICAL (6)–(7)) -/

/-- Spatial components in the declared observer tetrad. -/
abbrev V3 := Fin 3 → ℝ

/-- Declared Euclidean component dot product. -/
def dot3 (a b : V3) : ℝ := a 0 * b 0 + a 1 * b 1 + a 2 * b 2

/-- Unit sourceward direction. -/
def IsUnitDir (n : V3) : Prop := dot3 n n = 1

/-- Unconstrained intercept coefficients `(a0, a⃗)`: the four columns of `E4`. -/
abbrev IPar := ℝ × V3

/-- Slope coefficients `(h0, h1, q)`; `q` are the coordinates of the STF tensor `h2 = stf q`. -/
abbrev HPar := ℝ × V3 × (Fin 5 → ℝ)

/-- Physical 12-dimensional chart `x = (ζ, h)`. -/
abbrev PhysPar := V3 × HPar

/-- Coordinates of a symmetric trace-free 3×3 tensor. -/
def stf (q : Fin 5 → ℝ) : Matrix (Fin 3) (Fin 3) ℝ :=
  !![q 0, q 1, q 2; q 1, q 3, q 4; q 2, q 4, -q 0 - q 3]

/-- Inverse coordinate map on STF tensors. -/
def stfCoords (M : Matrix (Fin 3) (Fin 3) ℝ) : Fin 5 → ℝ :=
  ![M 0 0, M 0 1, M 0 2, M 1 1, M 1 2]

/-- `h2 : n n` written out in the STF coordinates. -/
def quad (q : Fin 5 → ℝ) (n : V3) : ℝ :=
  q 0 * n 0 ^ 2 + 2 * q 1 * n 0 * n 1 + 2 * q 2 * n 0 * n 2 + q 3 * n 1 ^ 2
    + 2 * q 4 * n 1 * n 2 + (-q 0 - q 3) * n 2 ^ 2

/-- Degree ≤ 1 polynomial with `E4` row `(1, nᵀ)`. -/
def ipoly (a : IPar) (n : V3) : ℝ := a.1 + dot3 a.2 n

/-- `H(h, n) = h0 + h1·n + h2:nn`. -/
def Hval (h : HPar) (n : V3) : ℝ := h.1 + dot3 h.2.1 n + quad h.2.2 n

/-- Future (positive) mass-shell branch `ζ0 = √(1+|ζ|²)`. -/
noncomputable def zeta0 (ζ : V3) : ℝ := Real.sqrt (1 + dot3 ζ ζ)

/-- `Z0(ζ, n) = ζ0 + ζ·n`. -/
noncomputable def Z0 (ζ n : V3) : ℝ := zeta0 ζ + dot3 ζ n

/-- Mass-shell embedding of the 12-dim physical chart into the 13-dim intercept chart. -/
noncomputable def massShell (ζ : V3) : IPar := (zeta0 ζ, ζ)

/-! ## Linear design maps (NATIVE (10)) -/

section Design

variable {ι : Type*}

/-- `E4`: rows `(1, n_iᵀ)`. -/
def E4 (dir : ι → V3) : IPar →ₗ[ℝ] (ι → ℝ) where
  toFun a := fun i => ipoly a (dir i)
  map_add' a b := by
    funext i; simp only [ipoly, dot3, Prod.fst_add, Prod.snd_add, Pi.add_apply]; ring
  map_smul' t a := by
    funext i
    simp only [ipoly, dot3, Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, smul_eq_mul,
      RingHom.id_apply]
    ring

/-- `E9`: evaluation of the 9 degree ≤ 2 coefficients (basis `h0, h1, STF coordinates`). -/
def E9 (dir : ι → V3) : HPar →ₗ[ℝ] (ι → ℝ) where
  toFun h := fun i => Hval h (dir i)
  map_add' a b := by
    funext i
    simp only [Hval, quad, dot3, Prod.fst_add, Prod.snd_add, Pi.add_apply]; ring
  map_smul' t a := by
    funext i
    simp only [Hval, quad, dot3, Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, smul_eq_mul,
      RingHom.id_apply]
    ring

/-- `D = diag(r_i / c)`. -/
def Dmap (r : ι → ℝ) (c : ℝ) : (ι → ℝ) →ₗ[ℝ] (ι → ℝ) where
  toFun v := fun i => (r i / c) * v i
  map_add' a b := by funext i; simp only [Pi.add_apply]; ring
  map_smul' t a := by
    funext i; simp only [Pi.smul_apply, smul_eq_mul, RingHom.id_apply]; ring

/-- `X = [E4, D E9]` on the 13-variable unconstrained chart. -/
def Xmap (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : IPar × HPar →ₗ[ℝ] (ι → ℝ) :=
  (E4 dir).coprod ((Dmap r c).comp (E9 dir))

/-- Derivative of the mass-shell embedding: `δζ ↦ ((ζ·δζ)/ζ0, δζ)`. -/
noncomputable def dEmb (ζ : V3) : V3 →ₗ[ℝ] IPar where
  toFun δ := (dot3 ζ δ / zeta0 ζ, δ)
  map_add' a b := by
    ext
    · simp only [dot3, Pi.add_apply, Prod.fst_add]; ring
    · simp
  map_smul' t a := by
    ext
    · simp only [dot3, Pi.smul_apply, smul_eq_mul, Prod.smul_fst, RingHom.id_apply]; ring
    · simp

/-- Chart derivative `(δζ, δh) ↦ (dEmb δζ, δh)`. -/
noncomputable def chartDeriv (ζ : V3) : PhysPar →ₗ[ℝ] IPar × HPar :=
  (dEmb ζ).prodMap LinearMap.id

/-- Physical Jacobian `Jphys = [Ndir + 1(ζ/ζ0)ᵀ, D E9]` (NATIVE (14)). -/
noncomputable def Jphys (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (ζ : V3) :
    PhysPar →ₗ[ℝ] (ι → ℝ) :=
  (Xmap dir r c).comp (chartDeriv ζ)

/-- Zero-remainder oracle redshift mean in the physical chart. -/
noncomputable def physMean (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) : ι → ℝ :=
  fun i => Z0 x.1 (dir i) + (r i / c) * Hval x.2 (dir i)

/-- Two-radius layout: nine directions at `R1`, four of them repeated (via `σ`) at `R2`. -/
def twoRadiusDir (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) : Fin 9 ⊕ Fin 4 → V3 :=
  Sum.elim dir9 (dir9 ∘ σ)

def twoRadiusR (R1 R2 : ℝ) : Fin 9 ⊕ Fin 4 → ℝ :=
  Sum.elim (fun _ => R1) (fun _ => R2)

/-- Radial alias radius `R / (1 + ε n_z)` (NATIVE (13)). -/
noncomputable def aliasRadius (R ε : ℝ) (n : V3) : ℝ := R / (1 + ε * n 2)

end Design

/-! ## Native means, ρ-transform and remainder domains (NATIVE (3), (5), (6)) -/

section Native

variable {ι : Type*}

/-- `Z_i = Z0(x, n_i) + (r_i/c) H(x, n_i) + ρ_i`. -/
noncomputable def nativeZ (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) (ρ : ι → ℝ) :
    ι → ℝ :=
  fun i => Z0 x.1 (dir i) + (r i / c) * Hval x.2 (dir i) + ρ i

/-- Native redshift mean `m_z = Z - 1`. -/
def meanZ (Z : ι → ℝ) : ι → ℝ := fun i => Z i - 1

/-- Native modulus mean `m_μ = 5 log10 (r Z² / 10pc)` (`tenpc` in the unit of `r`). -/
noncomputable def meanMu (r Z : ι → ℝ) (tenpc : ℝ) : ι → ℝ :=
  fun i => 5 * Real.logb 10 (r i * Z i ^ 2 / tenpc)

/-- Native positivity domain `r_i > 0`, `Z_i > 0`. -/
def NativeDomain (r Z : ι → ℝ) : Prop := ∀ i, 0 < r i ∧ 0 < Z i

/-- Supplied remainder transformation `ρ_i(x) = Z_i - Z0(x,n_i) - (r_i/c) H(x,n_i)`. -/
noncomputable def rhoOf (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (Z : ι → ℝ) (x : PhysPar) :
    ι → ℝ :=
  fun i => Z i - Z0 x.1 (dir i) - (r i / c) * Hval x.2 (dir i)

/-- `η(s) = sinh(√Kc s)/(√Kc s) - 1`, `η = 0` when `Kc = 0` (used only at `s > 0`). -/
noncomputable def eta (Kc s : ℝ) : ℝ :=
  if Kc = 0 then 0 else Real.sinh (Real.sqrt Kc * s) / (Real.sqrt Kc * s) - 1

/-- External full-segment bounds `Kc ≥ 0`, `M2 ≥ 0`, `L > 0`, `η(L) < 1`. -/
structure EnvelopeParams where
  Kc : ℝ
  M2 : ℝ
  L : ℝ
  hKc : 0 ≤ Kc
  hM2 : 0 ≤ M2
  hL : 0 < L
  hetaL : eta Kc L < 1

noncomputable def EnvelopeParams.etaL (P : EnvelopeParams) : ℝ := eta P.Kc P.L

/-- Envelope `E_i(x, r_i)` of eq. (5); `Hn = H(x, n_i)`. -/
noncomputable def E5 (P : EnvelopeParams) (c Hn r : ℝ) : ℝ :=
  P.M2 * r ^ 2 / (2 * (1 - P.etaL) ^ 2) + |Hn| * r * P.etaL / (c * (1 - P.etaL))

/-- Enlarged (outer) admissible remainder domain Ω of eq. (5). -/
def Omega5 (P : EnvelopeParams) (c : ℝ) (dir : ι → V3) (x : PhysPar) (r ρ : ι → ℝ) : Prop :=
  ∀ i, 0 < r i ∧ r i ≤ P.L * (1 + P.etaL) ∧ |ρ i| ≤ E5 P c (Hval x.2 (dir i)) (r i)

/-- Tighter latent-distance domain of eq. (6). -/
def Omega6 (P : EnvelopeParams) (c : ℝ) (dir : ι → V3) (x : PhysPar) (r ρ : ι → ℝ) : Prop :=
  ∃ s : ι → ℝ, ∀ i, 0 < s i ∧ s i ≤ P.L ∧
    s i * (1 - eta P.Kc (s i)) ≤ r i ∧ r i ≤ s i * (1 + eta P.Kc (s i)) ∧
    |ρ i| ≤ P.M2 * s i ^ 2 / 2 + |Hval x.2 (dir i)| * s i * eta P.Kc (s i) / c

end Native

/-! ## Basis lemmas -/

theorem stf_transpose (q : Fin 5 → ℝ) : (stf q).transpose = stf q := by
  ext i j; fin_cases i <;> fin_cases j <;> rfl

theorem stf_trace (q : Fin 5 → ℝ) : Matrix.trace (stf q) = 0 := by
  simp [stf, Matrix.trace, Fin.sum_univ_three]

theorem stf_injective : Function.Injective stf := by
  intro q q' h
  have h00 := congrFun (congrFun h 0) 0
  have h01 := congrFun (congrFun h 0) 1
  have h02 := congrFun (congrFun h 0) 2
  have h11 := congrFun (congrFun h 1) 1
  have h12 := congrFun (congrFun h 1) 2
  simp [stf] at h00 h01 h02 h11 h12
  funext k; fin_cases k <;> simp [*]

theorem stf_stfCoords (M : Matrix (Fin 3) (Fin 3) ℝ) (hM : M.transpose = M)
    (htr : Matrix.trace M = 0) : stf (stfCoords M) = M := by
  have hs : ∀ i j, M j i = M i j := fun i j => by
    have := congrFun (congrFun hM i) j; simpa [Matrix.transpose_apply] using this
  have ht : M 0 0 + M 1 1 + M 2 2 = 0 := by
    simpa [Matrix.trace, Fin.sum_univ_three] using htr
  ext i j
  fin_cases i <;> fin_cases j <;> simp [stf, stfCoords, hs] <;> linarith

theorem quad_eq (q : Fin 5 → ℝ) (n : V3) :
    quad q n = dotProduct n ((stf q).mulVec n) := by
  simp [quad, stf, dotProduct, Matrix.mulVec, Fin.sum_univ_three]; ring

theorem finrank_IPar : Module.finrank ℝ IPar = 4 := by simp [IPar, V3]

theorem finrank_HPar : Module.finrank ℝ HPar = 9 := by simp [HPar, V3]

theorem finrank_PhysPar : Module.finrank ℝ PhysPar = 12 := by
  simp [PhysPar, HPar, V3]

/-! ## C01 — rank identity (Theorem N3) and the two-radius design -/

section C01

variable {ι : Type*} [Fintype ι]

theorem Dmap_injective (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) :
    Function.Injective (Dmap r c) := by
  intro v w h
  funext i
  have := congrFun h i
  simp only [Dmap, LinearMap.coe_mk, AddHom.coe_mk] at this
  have hne : r i / c ≠ 0 := (div_pos (hr i) hc).ne'
  exact mul_left_cancel₀ hne this

theorem finrank_range_DE9 (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i)
    (hc : 0 < c) :
    Module.finrank ℝ (LinearMap.range ((Dmap r c).comp (E9 dir))) =
      Module.finrank ℝ (LinearMap.range (E9 dir)) := by
  rw [LinearMap.range_comp]
  exact (Submodule.equivMapOfInjective _ (Dmap_injective r c hr hc) _).finrank_eq.symm

/-- C01(a): `rank X + dim(col E4 ∩ col DE9) = rank E4 + rank E9`. -/
theorem rank_concat_identity (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i)
    (hc : 0 < c) :
    Module.finrank ℝ (LinearMap.range (Xmap dir r c)) +
        Module.finrank ℝ
          (LinearMap.range (E4 dir) ⊓ LinearMap.range ((Dmap r c).comp (E9 dir)) :
            Submodule ℝ (ι → ℝ)) =
      Module.finrank ℝ (LinearMap.range (E4 dir)) +
        Module.finrank ℝ (LinearMap.range (E9 dir)) := by
  rw [← finrank_range_DE9 dir r c hr hc, Xmap, LinearMap.range_coprod]
  exact Submodule.finrank_sup_add_finrank_inf_eq _ _

/-- C01(b), Theorem N3: rank 13 iff rank E4 = 4, rank E9 = 9 and the intersection is zero. -/
theorem rank13_iff (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) :
    Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13 ↔
      Module.finrank ℝ (LinearMap.range (E4 dir)) = 4 ∧
        Module.finrank ℝ (LinearMap.range (E9 dir)) = 9 ∧
        (LinearMap.range (E4 dir) ⊓ LinearMap.range ((Dmap r c).comp (E9 dir)) :
            Submodule ℝ (ι → ℝ)) = ⊥ := by
  have hid := rank_concat_identity dir r c hr hc
  have h4 : Module.finrank ℝ (LinearMap.range (E4 dir)) ≤ 4 :=
    finrank_IPar ▸ LinearMap.finrank_range_le (E4 dir)
  have h9 : Module.finrank ℝ (LinearMap.range (E9 dir)) ≤ 9 :=
    finrank_HPar ▸ LinearMap.finrank_range_le (E9 dir)
  rw [← Submodule.finrank_eq_zero]
  omega

/-- N3 corollary: rank 13 needs at least 13 observations. -/
theorem rank13_needs_N (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (h : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13) : 13 ≤ Fintype.card ι := by
  have := Submodule.finrank_le (LinearMap.range (Xmap dir r c))
  simp only [Module.finrank_fintype_fun_eq_card] at this
  omega

theorem Hval_add (h k : HPar) (n : V3) : Hval (h + k) n = Hval h n + Hval k n := by
  simp only [Hval, quad, dot3, Prod.fst_add, Prod.snd_add, Pi.add_apply]; ring

theorem Hval_smul (t : ℝ) (h : HPar) (n : V3) : Hval (t • h) n = t * Hval h n := by
  simp only [Hval, quad, dot3, Prod.smul_fst, Prod.smul_snd, Pi.smul_apply, smul_eq_mul]; ring

/-- The degree ≤ 1 slope element with the same polynomial as `a`. -/
def liftLin (a : IPar) : HPar := (a.1, a.2, 0)

theorem Hval_liftLin (a : IPar) (n : V3) : Hval (liftLin a) n = ipoly a n := by
  simp [Hval, liftLin, ipoly, quad]

/-- C01(c): nine unisolvent directions at `R1` plus four repeated directions with
nonsingular `E4` block at `R2 ≠ R1` give an injective `X` (coefficient elimination). -/
theorem two_radius_injective (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ)
    (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2)
    (huni : Function.Injective (E9 dir9)) (hE4 : Function.Injective (E4 (dir9 ∘ σ))) :
    Function.Injective (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c) := by
  rw [← LinearMap.ker_eq_bot, LinearMap.ker_eq_bot']
  rintro ⟨a, h⟩ hX
  have hrow : ∀ j, ipoly a (twoRadiusDir dir9 σ j) +
      (twoRadiusR R1 R2 j / c) * Hval h (twoRadiusDir dir9 σ j) = 0 := by
    intro j
    have := congrFun hX j
    simpa [Xmap, E4, E9, Dmap] using this
  -- first nine rows: the combined degree ≤ 2 polynomial vanishes
  have hk : h + (c / R1) • liftLin a = 0 := by
    apply huni
    rw [map_zero]
    funext j
    have := hrow (Sum.inl j)
    simp only [twoRadiusDir, twoRadiusR, Sum.elim_inl] at this
    simp only [E9, LinearMap.coe_mk, AddHom.coe_mk, Pi.zero_apply, Hval_add, Hval_smul,
      Hval_liftLin]
    field_simp at this ⊢
    linarith
  have hh : h = -((c / R1) • liftLin a) := eq_neg_of_add_eq_zero_left hk
  -- repeated four rows at R2
  have ha : a = 0 := by
    apply hE4
    rw [map_zero]
    funext k
    have := hrow (Sum.inr k)
    simp only [twoRadiusDir, twoRadiusR, Sum.elim_inr, Function.comp_apply] at this
    rw [hh, show -((c / R1) • liftLin a) = (-(c / R1)) • liftLin a by rw [neg_smul],
      Hval_smul, Hval_liftLin] at this
    simp only [E4, LinearMap.coe_mk, AddHom.coe_mk, Pi.zero_apply, Function.comp_apply]
    have hfac : ipoly a (dir9 (σ k)) * (1 - R2 / R1) = 0 := by
      field_simp at this ⊢; linarith
    have h1 : (1 - R2 / R1) ≠ 0 := by
      intro h0
      have : R2 / R1 = 1 := by linarith
      rw [div_eq_one_iff_eq hR1.ne'] at this
      exact hne this.symm
    exact (mul_eq_zero.mp hfac).resolve_right h1
  subst ha
  have : h = 0 := by simpa [liftLin] using hh
  simp [this]

theorem finrank_range_of_injective_13 {ι : Type*} [Fintype ι] (dir : ι → V3) (r : ι → ℝ)
    (c : ℝ) (h : Function.Injective (Xmap dir r c)) :
    Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13 := by
  rw [LinearMap.finrank_range_of_inj h, Module.finrank_prod, finrank_IPar, finrank_HPar]

/-- C01(c) in rank form. -/
theorem two_radius_rank13 (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ)
    (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2)
    (huni : Function.Injective (E9 dir9)) (hE4 : Function.Injective (E4 (dir9 ∘ σ))) :
    Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c)) =
      13 :=
  finrank_range_of_injective_13 _ _ _
    (two_radius_injective dir9 σ R1 R2 c hR1 hR2 hc hne huni hE4)

theorem finrank_range_lt_13_of_not_injective {ι : Type*} [Fintype ι] (dir : ι → V3)
    (r : ι → ℝ) (c : ℝ) (h : ¬ Function.Injective (Xmap dir r c)) :
    Module.finrank ℝ (LinearMap.range (Xmap dir r c)) < 13 := by
  have hrn := LinearMap.finrank_range_add_finrank_ker (Xmap dir r c)
  rw [Module.finrank_prod, finrank_IPar, finrank_HPar] at hrn
  have hker : LinearMap.ker (Xmap dir r c) ≠ ⊥ := fun hb => h (LinearMap.ker_eq_bot.mp hb)
  have : 0 < Module.finrank ℝ (LinearMap.ker (Xmap dir r c)) := by
    rw [Nat.pos_iff_ne_zero, Ne, Submodule.finrank_eq_zero]; exact hker
  omega

/-- Negative control DESIGN-ANGULAR: a rank-deficient repeated `E4` block destroys rank 13
(for any positive `R1`, `R2`, and without unisolvency). -/
theorem two_radius_fails_of_E4_deficient (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9)
    (R1 R2 c : ℝ) (hR1 : 0 < R1) (hc : 0 < c)
    (hE4 : ¬ Function.Injective (E4 (dir9 ∘ σ))) :
    Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c)) <
      13 := by
  apply finrank_range_lt_13_of_not_injective
  intro hinj
  apply hE4
  rw [← LinearMap.ker_eq_bot, LinearMap.ker_eq_bot']
  intro a ha
  have hz : Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c
      (a, (-(c / R1)) • liftLin a) = 0 := by
    funext j
    rcases j with j | k
    · simp only [Xmap, LinearMap.coprod_apply, LinearMap.comp_apply, E4, E9, Dmap,
        LinearMap.coe_mk, AddHom.coe_mk, Pi.add_apply, Pi.zero_apply, twoRadiusDir,
        twoRadiusR, Sum.elim_inl, Hval_smul, Hval_liftLin]
      field_simp; ring
    · have hk := congrFun ha k
      simp only [E4, LinearMap.coe_mk, AddHom.coe_mk, Pi.zero_apply,
        Function.comp_apply] at hk
      simp only [Xmap, LinearMap.coprod_apply, LinearMap.comp_apply, E4, E9, Dmap,
        LinearMap.coe_mk, AddHom.coe_mk, Pi.add_apply, Pi.zero_apply, twoRadiusDir,
        twoRadiusR, Sum.elim_inr, Function.comp_apply, Hval_smul, Hval_liftLin, hk]
      ring
  have := hinj (hz.trans (map_zero _).symm)
  exact (Prod.mk.inj this).1

/-! ### Exact rational witness (non-vacuity) -/

/-- Nine rational unit directions: `±e1, ±e2, ±e3, (3/5,4/5,0), (3/5,0,4/5), (0,3/5,4/5)`. -/
noncomputable def dirStar : Fin 9 → V3 :=
  ![![1, 0, 0], ![-1, 0, 0], ![0, 1, 0], ![0, -1, 0], ![0, 0, 1], ![0, 0, -1],
    ![3/5, 4/5, 0], ![3/5, 0, 4/5], ![0, 3/5, 4/5]]

/-- Repeated rows `e1, -e1, e2, e3`. -/
def σStar : Fin 4 → Fin 9 := ![0, 1, 2, 4]

theorem dirStar_unit : ∀ j, IsUnitDir (dirStar j) := by
  intro j; fin_cases j <;> simp [IsUnitDir, dot3, dirStar] <;> norm_num

theorem dirStar_unisolvent : Function.Injective (E9 dirStar) := by
  rw [← LinearMap.ker_eq_bot, LinearMap.ker_eq_bot']
  rintro ⟨h0, h1, q⟩ hz
  have e : ∀ j, Hval (h0, h1, q) (dirStar j) = 0 := fun j => congrFun hz j
  have e0 := e 0; have e1 := e 1; have e2 := e 2; have e3 := e 3; have e4 := e 4
  have e5 := e 5; have e6 := e 6; have e7 := e 7; have e8 := e 8
  simp [Hval, quad, dot3, dirStar] at e0 e1 e2 e3 e4 e5 e6 e7 e8
  have a0 : h0 = 0 := by linarith
  have b0 : h1 0 = 0 := by linarith
  have b1 : h1 1 = 0 := by linarith
  have b2 : h1 2 = 0 := by linarith
  have c0 : q 0 = 0 := by linarith
  have c3 : q 3 = 0 := by linarith
  have c1 : q 1 = 0 := by linarith
  have c2 : q 2 = 0 := by linarith
  have c4 : q 4 = 0 := by linarith
  refine Prod.ext a0 (Prod.ext ?_ ?_)
  · funext k; fin_cases k <;> simp [b0, b1, b2]
  · funext k; fin_cases k <;> simp [c0, c1, c2, c3, c4]

theorem σStar_E4 : Function.Injective (E4 (dirStar ∘ σStar)) := by
  rw [← LinearMap.ker_eq_bot, LinearMap.ker_eq_bot']
  rintro ⟨a0, a⟩ hz
  have e : ∀ k, ipoly (a0, a) (dirStar (σStar k)) = 0 := fun k => congrFun hz k
  have e0 := e 0; have e1 := e 1; have e2 := e 2; have e3 := e 3
  simp [ipoly, dot3, dirStar, σStar] at e0 e1 e2 e3
  have x0 : a0 = 0 := by linarith
  have y0 : a 0 = 0 := by linarith
  have y1 : a 1 = 0 := by linarith
  have y2 : a 2 = 0 := by linarith
  refine Prod.ext x0 ?_
  funext k; fin_cases k <;> simp [y0, y1, y2]

/-- Non-vacuity: the explicit design with `R1 = 1`, `R2 = 2`, `c = 1` has rank 13. -/
theorem witness_rank13 :
    Module.finrank ℝ
      (LinearMap.range (Xmap (twoRadiusDir dirStar σStar) (twoRadiusR 1 2) 1)) = 13 :=
  two_radius_rank13 dirStar σStar 1 2 1 one_pos two_pos one_pos (by norm_num)
    dirStar_unisolvent σStar_E4

end C01

/-! ## C02 — mass-shell intercept chart and physical Jacobian -/

section C02

theorem one_le_one_add_dot3 (ζ : V3) : 1 ≤ 1 + dot3 ζ ζ := by
  simp only [dot3]; nlinarith [sq_nonneg (ζ 0), sq_nonneg (ζ 1), sq_nonneg (ζ 2)]

theorem one_le_zeta0 (ζ : V3) : 1 ≤ zeta0 ζ := by
  unfold zeta0
  rw [show (1 : ℝ) = Real.sqrt 1 by simp]
  exact Real.sqrt_le_sqrt (one_le_one_add_dot3 ζ)

theorem zeta0_pos (ζ : V3) : 0 < zeta0 ζ := lt_of_lt_of_le one_pos (one_le_zeta0 ζ)

/-- The image of the chart lies on the future unit hyperboloid `ζ0² - |ζ|² = 1`, `ζ0 ≥ 1`. -/
theorem massShell_hyperboloid (ζ : V3) :
    (massShell ζ).1 ^ 2 - dot3 (massShell ζ).2 (massShell ζ).2 = 1 ∧ 1 ≤ (massShell ζ).1 := by
  refine ⟨?_, one_le_zeta0 ζ⟩
  simp only [massShell, zeta0]
  rw [Real.sq_sqrt (le_trans zero_le_one (one_le_one_add_dot3 ζ))]
  ring

theorem massShell_injective : Function.Injective massShell := by
  intro ζ ζ' h; exact (Prod.mk.inj h).2

variable {ι : Type*} [Fintype ι]

/-- The physical mean is the 13-variable design composed with the mass-shell chart. -/
theorem physMean_eq_X (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) :
    physMean dir r c x = Xmap dir r c (massShell x.1, x.2) := by
  funext i
  simp [physMean, Xmap, E4, E9, Dmap, massShell, ipoly, Z0]

/-- Canonical form (14): `Jphys = Ndir + 1(ζ/ζ0)ᵀ` on `δζ`, `D E9` on `δh`. -/
theorem Jphys_apply (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (ζ : V3) (δζ : V3) (δh : HPar)
    (i : ι) :
    Jphys dir r c ζ (δζ, δh) i =
      dot3 δζ (dir i) + dot3 ζ δζ / zeta0 ζ + (r i / c) * Hval δh (dir i) := by
  simp [Jphys, chartDeriv, dEmb, Xmap, E4, E9, Dmap, ipoly]
  ring

/-- Derivative of `ζ ↦ ζ0(ζ)`. -/
noncomputable def zeta0Deriv (ζ : V3) : V3 →ₗ[ℝ] ℝ where
  toFun δ := dot3 ζ δ / zeta0 ζ
  map_add' a b := by simp only [dot3, Pi.add_apply]; ring
  map_smul' t a := by simp only [dot3, Pi.smul_apply, smul_eq_mul, RingHom.id_apply]; ring

theorem hasFDerivAt_zeta0 (ζ : V3) :
    HasFDerivAt zeta0 (LinearMap.toContinuousLinearMap (zeta0Deriv ζ)) ζ := by
  have p : ∀ k : Fin 3, HasFDerivAt (fun y : V3 => y k)
      (ContinuousLinearMap.proj (R := ℝ) (φ := fun _ : Fin 3 => ℝ) k) ζ :=
    fun k => hasFDerivAt_apply k ζ
  have hf := ((((p 0).mul (p 0)).add ((p 1).mul (p 1))).add ((p 2).mul (p 2))).const_add 1
  have hpos : 0 < 1 + (ζ 0 * ζ 0 + ζ 1 * ζ 1 + ζ 2 * ζ 2) :=
    lt_of_lt_of_le one_pos (one_le_one_add_dot3 ζ)
  have hs := hf.sqrt hpos.ne'
  have hfun : zeta0 = fun y : V3 => Real.sqrt (1 + (y 0 * y 0 + y 1 * y 1 + y 2 * y 2)) := by
    funext y; rfl
  rw [hfun]
  convert hs using 1
  refine ContinuousLinearMap.ext fun δ => ?_
  have hsq : 0 < Real.sqrt (1 + (ζ 0 * ζ 0 + ζ 1 * ζ 1 + ζ 2 * ζ 2)) := Real.sqrt_pos.mpr hpos
  simp only [LinearMap.coe_toContinuousLinearMap', zeta0Deriv, LinearMap.coe_mk, AddHom.coe_mk,
    ContinuousLinearMap.coe_smul', ContinuousLinearMap.add_apply, Pi.smul_apply,
    ContinuousLinearMap.coe_smul', ContinuousLinearMap.proj_apply, smul_eq_mul, zeta0, dot3]
  field_simp
  ring

/-- C02: the oracle physical mean has Fréchet derivative `Jphys` at every chart point. -/
theorem hasFDerivAt_physMean (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) :
    HasFDerivAt (physMean dir r c) (LinearMap.toContinuousLinearMap (Jphys dir r c x.1)) x := by
  have h1 : HasFDerivAt (fun y : PhysPar => zeta0 y.1)
      ((LinearMap.toContinuousLinearMap (zeta0Deriv x.1)).comp
        (ContinuousLinearMap.fst ℝ V3 HPar)) x :=
    (hasFDerivAt_zeta0 x.1).comp x hasFDerivAt_fst
  have hemb := (h1.prodMk hasFDerivAt_fst).prodMk hasFDerivAt_snd
  have hX := (LinearMap.toContinuousLinearMap (Xmap dir r c)).hasFDerivAt.comp x hemb
  have hfun : physMean dir r c =
      (LinearMap.toContinuousLinearMap (Xmap dir r c)) ∘
        (fun y : PhysPar => ((zeta0 y.1, y.1), y.2)) := by
    funext y
    rw [physMean_eq_X]
    rfl
  rw [hfun]
  convert hX using 1
  refine ContinuousLinearMap.ext fun v => ?_
  rfl

theorem dEmb_injective (ζ : V3) : Function.Injective (dEmb ζ) := by
  intro a b h
  have := congrArg Prod.snd h
  simpa [dEmb] using this

theorem chartDeriv_injective (ζ : V3) : Function.Injective (chartDeriv ζ) := by
  rintro ⟨a, h⟩ ⟨b, k⟩ hab
  have h1 := congrArg (fun p => p.1.2) hab
  have h2 := congrArg Prod.snd hab
  simp [chartDeriv, dEmb] at h1 h2
  rw [h1, h2]

/-- The intercept-chart derivative has rank three. -/
theorem dEmb_rank3 (ζ : V3) : Module.finrank ℝ (LinearMap.range (dEmb ζ)) = 3 := by
  rw [LinearMap.finrank_range_of_inj (dEmb_injective ζ)]
  simp [V3]

theorem Xmap_injective_of_rank13 (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (h : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13) :
    Function.Injective (Xmap dir r c) := by
  have hrn := LinearMap.finrank_range_add_finrank_ker (Xmap dir r c)
  rw [Module.finrank_prod, finrank_IPar, finrank_HPar, h] at hrn
  have h0 : Module.finrank ℝ (LinearMap.ker (Xmap dir r c)) = 0 := by omega
  rw [Submodule.finrank_eq_zero] at h0
  exact LinearMap.ker_eq_bot.mp h0

/-- C02: unconstrained rank 13 implies physical rank 12 at every chart point. -/
theorem rank12_of_rank13 (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (h : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13) (ζ : V3) :
    Module.finrank ℝ (LinearMap.range (Jphys dir r c ζ)) = 12 := by
  have hinj : Function.Injective (Jphys dir r c ζ) := by
    simp only [Jphys, LinearMap.coe_comp]
    exact (Xmap_injective_of_rank13 dir r c h).comp (chartDeriv_injective ζ)
  rw [LinearMap.finrank_range_of_inj hinj, finrank_PhysPar]

/-- Non-vacuity for C02: the explicit witness design has physical rank 12 at every `ζ`. -/
theorem witness_rank12 (ζ : V3) :
    Module.finrank ℝ
      (LinearMap.range (Jphys (twoRadiusDir dirStar σStar) (twoRadiusR 1 2) 1 ζ)) = 12 :=
  rank12_of_rank13 _ _ _ witness_rank13 ζ

end C02

/-! ## C03 — constant radius and radial alias -/

section C03

variable {ι : Type*} [Fintype ι]

theorem aliasDenom_pos (n : V3) (ε : ℝ) (hn : IsUnitDir n) (hε : |ε| < 1) :
    0 < 1 + ε * n 2 := by
  unfold IsUnitDir dot3 at hn
  have hsq : n 2 ^ 2 ≤ 1 := by nlinarith [sq_nonneg (n 0), sq_nonneg (n 1)]
  have habs : |n 2| ≤ 1 := by
    rw [← abs_one, ← sq_le_sq]; simpa using hsq
  have hprod : |ε * n 2| < 1 := by
    rw [abs_mul]
    calc |ε| * |n 2| ≤ |ε| * 1 := mul_le_mul_of_nonneg_left habs (abs_nonneg ε)
      _ < 1 := by simpa using hε
  have := neg_abs_le (ε * n 2)
  linarith

theorem aliasRadius_pos (R ε : ℝ) (n : V3) (hR : 0 < R) (hn : IsUnitDir n) (hε : |ε| < 1) :
    0 < aliasRadius R ε n :=
  div_pos hR (aliasDenom_pos n ε hn hε)

theorem scale_cancel (R c p : ℝ) (hR : 0 < R) (hc : 0 < c) : R / c * (c / R * p) = p := by
  field_simp

/-- Constant radius: `col(E4) ⊆ col(D E9)`. -/
theorem const_radius_range_le (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) :
    LinearMap.range (E4 dir) ≤ LinearMap.range ((Dmap (fun _ => R) c).comp (E9 dir)) := by
  rintro y ⟨a, rfl⟩
  refine ⟨(c / R) • liftLin a, ?_⟩
  funext i
  simp only [LinearMap.comp_apply, Dmap, E9, E4, LinearMap.coe_mk, AddHom.coe_mk, Hval_smul,
    Hval_liftLin]
  exact scale_cancel R c _ hR hc

theorem range_X_of_le (dir : ι → V3) (r : ι → ℝ) (c : ℝ)
    (hle : LinearMap.range (E4 dir) ≤ LinearMap.range ((Dmap r c).comp (E9 dir))) :
    LinearMap.range (Xmap dir r c) = LinearMap.range ((Dmap r c).comp (E9 dir)) := by
  rw [Xmap, LinearMap.range_coprod, sup_eq_right.mpr hle]

/-- Constant radius: `rank X = rank E9`. -/
theorem const_radius_rank (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) :
    Module.finrank ℝ (LinearMap.range (Xmap dir (fun _ => R) c)) =
      Module.finrank ℝ (LinearMap.range (E9 dir)) := by
  rw [range_X_of_le dir _ c (const_radius_range_le dir R c hR hc)]
  exact finrank_range_DE9 dir _ c (fun _ => hR) hc

/-- Constant radius: `rank X ≤ 9`. -/
theorem const_radius_rank_le9 (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) :
    Module.finrank ℝ (LinearMap.range (Xmap dir (fun _ => R) c)) ≤ 9 := by
  rw [const_radius_rank dir R c hR hc]
  exact finrank_HPar ▸ LinearMap.finrank_range_le (E9 dir)

/-- Constant radius with unisolvent directions: `rank X = 9`. -/
theorem const_radius_rank9 (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c)
    (huni : Function.Injective (E9 dir)) :
    Module.finrank ℝ (LinearMap.range (Xmap dir (fun _ => R) c)) = 9 := by
  rw [const_radius_rank dir R c hR hc, LinearMap.finrank_range_of_inj huni, finrank_HPar]

/-- Constant radius with unisolvent directions: `rank Jphys = 9` at every `ζ`. -/
theorem const_radius_Jphys_rank9 (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c)
    (huni : Function.Injective (E9 dir)) (ζ : V3) :
    Module.finrank ℝ (LinearMap.range (Jphys dir (fun _ => R) c ζ)) = 9 := by
  have hle := const_radius_range_le dir R c hR hc
  have heq : LinearMap.range (Jphys dir (fun _ => R) c ζ) =
      LinearMap.range ((Dmap (fun _ => R) c).comp (E9 dir)) := by
    apply le_antisymm
    · rw [← range_X_of_le dir _ c hle, Jphys]
      exact LinearMap.range_comp_le_range _ _
    · rintro y ⟨h, rfl⟩
      refine ⟨(0, h), ?_⟩
      simp [Jphys, chartDeriv, Xmap]
  rw [heq, finrank_range_DE9 dir _ c (fun _ => hR) hc, LinearMap.finrank_range_of_inj huni,
    finrank_HPar]

/-- Exact constant-radius degeneracy (12): any intercept change is compensated by a degree ≤ 2
slope change, leaving every redshift mean at radius `R` unchanged. -/
theorem const_radius_exact_degeneracy (R c : ℝ) (hR : 0 < R) (hc : 0 < c) (ζ ζ' : V3)
    (h : HPar) :
    ∃ h' : HPar, ∀ n : V3, Z0 ζ' n + (R / c) * Hval h' n = Z0 ζ n + (R / c) * Hval h n := by
  refine ⟨h + (c / R) • liftLin (zeta0 ζ - zeta0 ζ', ζ - ζ'), fun n => ?_⟩
  rw [Hval_add, Hval_smul, Hval_liftLin, mul_add, scale_cancel R c _ hR hc]
  simp only [Z0, ipoly, dot3, Pi.sub_apply]
  ring

/-- The constant-radius degeneracy in terms of the oracle physical mean. -/
theorem const_radius_physMean_degeneracy (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c)
    (ζ ζ' : V3) (h : HPar) :
    ∃ h' : HPar, physMean dir (fun _ => R) c (ζ', h') = physMean dir (fun _ => R) c (ζ, h) := by
  obtain ⟨h', hh'⟩ := const_radius_exact_degeneracy R c hR hc ζ ζ' h
  exact ⟨h', funext fun i => hh' (dir i)⟩

/-- Negative control DESIGN-R1R2: equal radii in the two-radius layout give rank ≤ 9. -/
theorem two_radius_equal_fails (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R c : ℝ)
    (hR : 0 < R) (hc : 0 < c) :
    Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R R) c)) ≤ 9 := by
  have : twoRadiusR R R = fun _ => R := by funext j; cases j <;> rfl
  rw [this]
  exact const_radius_rank_le9 _ R c hR hc

/-- Slope element realizing `(c/R)(1 + ε n_z) p(n)` on the unit sphere. -/
noncomputable def aliasLift (R ε c : ℝ) (a : IPar) : HPar :=
  (c / R) • ((a.1 + ε * a.2 2 / 3, ![a.2 0, a.2 1, a.2 2 + ε * a.1],
    ![-(ε * a.2 2) / 3, 0, ε * a.2 0 / 2, -(ε * a.2 2) / 3, ε * a.2 1 / 2]) : HPar)

theorem Hval_aliasLift (R ε c : ℝ) (a : IPar) (n : V3) (hn : IsUnitDir n) :
    Hval (aliasLift R ε c a) n = (c / R) * ((1 + ε * n 2) * ipoly a n) := by
  unfold aliasLift
  rw [Hval_smul]
  unfold IsUnitDir dot3 at hn
  simp only [Hval, quad, ipoly, dot3, Matrix.cons_val_zero, Matrix.cons_val_one,
    Matrix.cons_val_two, Matrix.cons_val_three, Matrix.cons_val_four, Matrix.head_cons,
    Matrix.tail_cons]
  linear_combination (-(c / R) * (ε * a.2 2 / 3)) * hn

/-- Radial alias (13): `col(E4) ⊆ col(D E9)` for `r_i = R/(1+ε n_iz)`, `0<|ε|<1`. -/
theorem radial_alias_range_le (dir : ι → V3) (R ε c : ℝ) (hunit : ∀ i, IsUnitDir (dir i))
    (hR : 0 < R) (hc : 0 < c) (hε0 : 0 < |ε|) (hε1 : |ε| < 1) :
    LinearMap.range (E4 dir) ≤
      LinearMap.range ((Dmap (fun i => aliasRadius R ε (dir i)) c).comp (E9 dir)) := by
  rintro y ⟨a, rfl⟩
  refine ⟨aliasLift R ε c a, ?_⟩
  funext i
  have hd := aliasDenom_pos (dir i) ε (hunit i) hε1
  simp only [LinearMap.comp_apply, Dmap, E9, E4, LinearMap.coe_mk, AddHom.coe_mk]
  rw [Hval_aliasLift R ε c a (dir i) (hunit i), aliasRadius]
  field_simp

/-- Radial alias: `rank X = rank E9 ≤ 9`. -/
theorem radial_alias_rank (dir : ι → V3) (R ε c : ℝ) (hunit : ∀ i, IsUnitDir (dir i))
    (hR : 0 < R) (hc : 0 < c) (hε0 : 0 < |ε|) (hε1 : |ε| < 1) :
    Module.finrank ℝ (LinearMap.range (Xmap dir (fun i => aliasRadius R ε (dir i)) c)) =
      Module.finrank ℝ (LinearMap.range (E9 dir)) := by
  rw [range_X_of_le dir _ c (radial_alias_range_le dir R ε c hunit hR hc hε0 hε1)]
  exact finrank_range_DE9 dir _ c (fun i => aliasRadius_pos R ε (dir i) hR (hunit i) hε1) hc

/-- Radial alias with unisolvent directions: still `rank X = 9`. -/
theorem radial_alias_rank9 (dir : ι → V3) (R ε c : ℝ) (hunit : ∀ i, IsUnitDir (dir i))
    (hR : 0 < R) (hc : 0 < c) (hε0 : 0 < |ε|) (hε1 : |ε| < 1)
    (huni : Function.Injective (E9 dir)) :
    Module.finrank ℝ (LinearMap.range (Xmap dir (fun i => aliasRadius R ε (dir i)) c)) = 9 := by
  rw [radial_alias_rank dir R ε c hunit hR hc hε0 hε1, LinearMap.finrank_range_of_inj huni,
    finrank_HPar]

/-- Non-vacuity for the alias: on the explicit unisolvent witness, `ε = 1/2` gives rank 9
with strictly positive, direction-dependent radii. -/
theorem witness_radial_alias_rank9 :
    Module.finrank ℝ
      (LinearMap.range (Xmap dirStar (fun i => aliasRadius 1 (1/2) (dirStar i)) 1)) = 9 :=
  radial_alias_rank9 dirStar 1 (1/2) 1 dirStar_unit one_pos one_pos (by norm_num) (by norm_num
    [abs_of_pos]) dirStar_unisolvent

end C03

/-! ## C04 — ρ-transform, native means, remainder domain (N4) -/

section C04

variable {ι : Type*}

/-- Substituting the supplied `ρ_i(x)` reproduces the given `Z` exactly. -/
theorem nativeZ_rhoOf (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (Z : ι → ℝ) (x : PhysPar) :
    nativeZ dir r c x (rhoOf dir r c Z x) = Z := by
  funext i; simp only [nativeZ, rhoOf]; ring

/-- C04: both native means are unchanged by the ρ-substitution, for every `x`. -/
theorem rhoOf_native_means (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (Z : ι → ℝ) (x : PhysPar)
    (tenpc : ℝ) :
    meanZ (nativeZ dir r c x (rhoOf dir r c Z x)) = meanZ Z ∧
      meanMu r (nativeZ dir r c x (rhoOf dir r c Z x)) tenpc = meanMu r Z tenpc := by
  rw [nativeZ_rhoOf]; exact ⟨rfl, rfl⟩

/-- At the generating parameter the transformation returns the true remainder. -/
theorem rhoOf_true (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) (ρ : ι → ℝ) :
    rhoOf dir r c (nativeZ dir r c x ρ) x = ρ := by
  funext i; simp only [rhoOf, nativeZ]; ring

/-- Positivity of the logarithm argument on the native domain. -/
theorem meanMu_arg_pos (r Z : ι → ℝ) (tenpc : ℝ) (hD : NativeDomain r Z) (ht : 0 < tenpc)
    (i : ι) : 0 < r i * Z i ^ 2 / tenpc :=
  div_pos (mul_pos (hD i).1 (pow_pos (hD i).2 2)) ht

theorem eta_nonneg (Kc s : ℝ) (hKc : 0 ≤ Kc) (hs : 0 < s) : 0 ≤ eta Kc s := by
  unfold eta
  split_ifs with h
  · exact le_rfl
  · have hpos : 0 < Real.sqrt Kc * s :=
      mul_pos (Real.sqrt_pos.mpr (lt_of_le_of_ne hKc (Ne.symm h))) hs
    have hsinh := Real.self_le_sinh_iff.mpr hpos.le
    rw [sub_nonneg, le_div_iff₀ hpos, one_mul]
    exact hsinh

/-- Denominator positivity in eq. (5). -/
theorem one_sub_etaL_pos (P : EnvelopeParams) : 0 < 1 - P.etaL := by
  have := P.hetaL; unfold EnvelopeParams.etaL; linarith

theorem E5_nonneg (P : EnvelopeParams) (c Hn r : ℝ) (hc : 0 < c) (hr : 0 ≤ r) :
    0 ≤ E5 P c Hn r := by
  have h1 := one_sub_etaL_pos P
  have he : 0 ≤ P.etaL := eta_nonneg _ _ P.hKc P.hL
  unfold E5
  apply add_nonneg
  · apply div_nonneg (mul_nonneg P.hM2 (sq_nonneg r)); positivity
  · exact div_nonneg (mul_nonneg (mul_nonneg (abs_nonneg _) hr) he) (mul_pos hc h1).le

@[fun_prop]
theorem continuous_zeta0 : Continuous zeta0 := by
  unfold zeta0 dot3; fun_prop

@[fun_prop]
theorem continuous_Hval (n : V3) : Continuous fun h : HPar => Hval h n := by
  unfold Hval quad dot3; fun_prop

/-- N4 (within the enlarged domain Ω only): strict slack gives a neighbourhood of `x*` in the
physical chart on which the supplied ρ-transform stays in Ω and all native means are unchanged.
`S` is any further physical restriction having `x*` as an interior point. -/
theorem strict_slack_local_identification [Fintype ι] (P : EnvelopeParams) (c : ℝ)
    (dir : ι → V3) (r : ι → ℝ) (xstar : PhysPar) (ρstar : ι → ℝ) (S : Set PhysPar)
    (hS : S ∈ 𝓝 xstar) (hr : ∀ i, 0 < r i ∧ r i ≤ P.L * (1 + P.etaL))
    (hslack : ∀ i, |ρstar i| < E5 P c (Hval xstar.2 (dir i)) (r i)) :
    ∀ᶠ x in 𝓝 xstar, x ∈ S ∧
      Omega5 P c dir x r (rhoOf dir r c (nativeZ dir r c xstar ρstar) x) ∧
      nativeZ dir r c x (rhoOf dir r c (nativeZ dir r c xstar ρstar) x) =
        nativeZ dir r c xstar ρstar := by
  have hi : ∀ i, ∀ᶠ x in 𝓝 xstar,
      |rhoOf dir r c (nativeZ dir r c xstar ρstar) x i| < E5 P c (Hval x.2 (dir i)) (r i) := by
    intro i
    have hf : Continuous fun x : PhysPar =>
        |rhoOf dir r c (nativeZ dir r c xstar ρstar) x i| := by
      unfold rhoOf Z0 dot3; fun_prop
    have hg : Continuous fun x : PhysPar => E5 P c (Hval x.2 (dir i)) (r i) := by
      unfold E5; fun_prop
    have h0 : |rhoOf dir r c (nativeZ dir r c xstar ρstar) xstar i| <
        E5 P c (Hval xstar.2 (dir i)) (r i) := by
      rw [rhoOf_true]; exact hslack i
    exact hf.continuousAt.eventually_lt hg.continuousAt h0
  filter_upwards [hS, Filter.eventually_all.mpr hi] with x hxS hx
  exact ⟨hxS, fun i => ⟨(hr i).1, (hr i).2, (hx i).le⟩, nativeZ_rhoOf _ _ _ _ _⟩

/-! ### Negative control SLACK-BOUNDARY -/

/-- `Kc = 0`, `M2 = 0`, `L = 1`, so `η(L) = 0` and the envelope vanishes. -/
noncomputable def P0 : EnvelopeParams where
  Kc := 0
  M2 := 0
  L := 1
  hKc := le_rfl
  hM2 := le_rfl
  hL := one_pos
  hetaL := by simp [eta]

noncomputable def dir0 : Fin 1 → V3 := fun _ => ![0, 0, 1]
def r0 : Fin 1 → ℝ := fun _ => 1
def x0 : PhysPar := 0
def ρ0 : Fin 1 → ℝ := 0

/-- With zero slack (`|ρ*| = E`), no neighbourhood conclusion holds. -/
theorem slack_boundary_no_neighbourhood :
    (∀ i, |ρ0 i| = E5 P0 1 (Hval x0.2 (dir0 i)) (r0 i)) ∧
      ¬ (∀ᶠ x in 𝓝 x0, Omega5 P0 1 dir0 x r0 (rhoOf dir0 r0 1 (nativeZ dir0 r0 1 x0 ρ0) x)) := by
  have hE : ∀ Hn r : ℝ, E5 P0 1 Hn r = 0 := by
    intro Hn r; simp [E5, P0, EnvelopeParams.etaL, eta]
  refine ⟨fun i => by simp [hE, ρ0], ?_⟩
  intro hev
  let γ : ℝ → PhysPar := fun t => (0, (t, 0, 0))
  have hγ : Continuous γ := by fun_prop
  have hγ0 : γ 0 = x0 := rfl
  have ht : Tendsto γ (𝓝 0) (𝓝 x0) := hγ0 ▸ hγ.tendsto 0
  obtain ⟨ε, hε, hball⟩ := Metric.eventually_nhds_iff.mp (ht.eventually hev)
  have hdist : dist (ε / 2) (0 : ℝ) < ε := by
    rw [Real.dist_eq, sub_zero, abs_of_pos (half_pos hε)]; linarith
  have hm := (hball hdist 0).2.2
  have hval : rhoOf dir0 r0 1 (nativeZ dir0 r0 1 x0 ρ0) (γ (ε / 2)) 0 = -(ε / 2) := by
    simp [rhoOf, nativeZ, Z0, zeta0, dot3, Hval, quad, γ, x0, ρ0, dir0, r0]
  rw [hval, hE, abs_neg, abs_of_pos (half_pos hε)] at hm
  linarith

end C04

end G09A
