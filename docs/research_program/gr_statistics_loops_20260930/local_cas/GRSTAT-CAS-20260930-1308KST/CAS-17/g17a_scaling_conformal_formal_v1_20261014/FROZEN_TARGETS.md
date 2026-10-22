# G17-A frozen targets (written before any proof compile)

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/G17-A.json` (scope: resolve the
CAS17-C02/C03 input-definition blocker from repository sources, then the
successor obligation of `c02_c03_source_definition_freeze_v1_20261011`: bind the
recovered interface to a formal chart-level Lorentz/connection/affine-endpoint
representation and prove C02 and C03 **separately**, without assuming the target
transformations).

Contract statements (CAS-17.json:119-120):

* C02 — "Verify constant metric/velocity scaling of normalized contractions, B, A,
  local optical slope, dA, calibration offset, Kc,M2,L. Optical distance scaling
  presumes the specified affine normalization."
* C03 — "Derive the conformal connection-difference identity and
  A_prime=exp(-2phi)(A+c^2 h gradphi); derive endpoint redshift scaling from the
  declared null and observer rescalings."

Scope declared up front: **frame/chart level**. A metric is a field
`g : Pt n → Arr2 n` on one coordinate chart with length-valued coordinates;
Christoffel symbols are *defined* by the Levi-Civita (Christoffel) formula from
`fderiv` of `g`; covariant derivatives, Riemann tensor, acceleration and `B` are
*defined* from them. No transformation law of `Γ`, `A`, `B`, `ν`, `1+z`, `d_A`,
`Kc`, `M2`, `L`, `κ` is assumed anywhere; each is a theorem. No global manifold,
atlas, existence of null geodesics, or caustic structure is formalized.

Domains: constant scale `lam > 0` (some algebraic items hold for `lam ≠ 0`,
which is a weaker hypothesis and is stated as such); general `φ` is any function
differentiable at the point. `Z` is `1+z` (see SOURCE_RECOVERY.md).

## Definitions (module `G17ACore`, namespace `G17A`)

```lean
abbrev Pt (n : ℕ) := Fin n → ℝ                 -- length-valued chart components (x⁰ = c t)
abbrev Arr2 (n : ℕ) := Fin n → Fin n → ℝ        -- 2-index component array
def chartPoint (c t : ℝ) (xs : Fin 3 → ℝ) : Pt 4 := Fin.cons (c * t) xs
def pd (f : Pt n → E) (x : Pt n) (b : Fin n) : E := fderiv ℝ f x (Pi.single b 1)     -- ∂_b
def ginv (g : Pt n → Arr2 n) (x : Pt n) : Matrix (Fin n) (Fin n) ℝ := (Matrix.of (g x))⁻¹  -- g^{ab}
def chris g x a b c := (1/2) * ∑ d, ginv g x a d * (pd g x b d c + pd g x c d b - pd g x d b c) -- Γ^a_bc
def covVec g (V : Pt n → Pt n) x b a := pd V x b a + ∑ c, chris g x a b c * V x c            -- ∇_b V^a
def selfCov g V x a := ∑ b, V x b * covVec g V x b a                                         -- V^b ∇_b V^a
def lower g V : Pt n → Pt n := fun y b => ∑ a, g y b a * V y a                                -- U_b
def covCov g (ω : Pt n → Pt n) x a b := pd ω x a b - ∑ c, chris g x c a b * ω x c             -- ∇_a ω_b
def Bcov g U x a b := (covCov g (lower g U) x a b + covCov g (lower g U) x b a) / 2           -- B_ab = ∇_(a U_b)
def Acov g U x b := ∑ a, U x a * covCov g (lower g U) x a b                                  -- A_b = U^a ∇_a U_b
def riemann g x a b c d := pd (fun y => chris g y a d b) x c - pd (fun y => chris g y a c b) x d
    + ∑ e, (chris g x a c e * chris g x e d b - chris g x a d e * chris g x e c b)          -- COMMON_SPEC:23
def contr (G : Arr2 n) (V W : Pt n) : ℝ := ∑ a, ∑ b, G a b * V a * W b                      -- g(V,W)
def covNorm (Gi : Matrix (Fin n) (Fin n) ℝ) (k : Pt n) : ℝ := ∑ a, ∑ b, Gi a b * k a * k b    -- g^{ab}k_a k_b
def hinv g U c x a b := ginv g x a b + U x a * U x b / c ^ 2                                 -- h^{ab}
def conf (φ : Pt n → ℝ) g : Pt n → Arr2 n := fun y => Real.exp (2 * φ y) • g y              -- e^{2φ} g
def physVel (c : ℝ) (u : Pt n → Pt n) : Pt n → Pt n := fun y => c • u y                      -- U = c u
-- typed outputs (separate types for separate index positions)
structure Contra (n) where comp : Fin n → ℝ     -- contravariant coordinate components
structure Cov (n) where comp : Fin n → ℝ        -- covariant coordinate components
structure Measured (n) where comp : Fin n → ℝ   -- orthonormal-tetrad (measured) components
def accelContra g U x : Contra n := ⟨selfCov g U x⟩
def accelCov g U x : Cov n := ⟨Acov g U x⟩
def Orthonormal (G : Arr2 n) (E : Fin n → Pt n) (η : Fin n → ℝ) : Prop :=
  ∀ α β, contr G (E α) (E β) = if α = β then η α else 0
def tet2 (T : Arr2 n) (E : Fin n → Pt n) (α β : Fin n) : ℝ := ∑ a, ∑ b, T a b * E α a * E β b
def tetVec (G : Arr2 n) (E : Fin n → Pt n) (η : Fin n → ℝ) (V : Pt n) : Measured n := ⟨fun α => η α * contr G (E α) V⟩
def measNorm (m : Measured n) : ℝ := Real.sqrt (∑ α, m.comp α ^ 2)    -- declared Euclidean component norm
def freq (k U : Pt n) : ℝ := -(∑ a, k a * U a) / (2 * Real.pi)        -- ν = -k_a U^a / 2π
def onePlusZ (ke Ue ko Uo : Pt n) : ℝ := freq ke Ue / freq ko Uo     -- Z = 1+z = ν_e/ν_o
def zOf (Z : ℝ) : ℝ := Z - 1
-- frame-level contractions reuse CAS17C01 (Vec, lorentz, scale, gamma, relativeSpatial, betaSq, beta)
def scaledLorentz (lam : ℝ) (a b : CAS17C01.Vec) : ℝ := lam ^ 2 * CAS17C01.lorentz a b
def Kvec (o n : CAS17C01.Vec) : CAS17C01.Vec := ⟨-o.t + n.t, -o.x + n.x, -o.y + n.y, -o.z + n.z⟩
def gammaW (B : Vec → Vec → ℝ) (u o : Vec) : ℝ := -B u o
def relW B u o : Vec := ⟨u.t - gammaW B u o * o.t, u.x - gammaW B u o * o.x, u.y - gammaW B u o * o.y, u.z - gammaW B u o * o.z⟩
def betaSqW B u o : ℝ := B (relW B u o) (relW B u o) / (gammaW B u o) ^ 2
```

## Module `G17AOptics` (imports `G17ACore`, `G01AJacobiVertex`)

```lean
def tidalMat (G : Arr2 n) (Rm : Fin n → Fin n → Fin n → Fin n → ℝ) (E : Fin 2 → Pt n) (K : Pt n) :
    Matrix (Fin 2) (Fin 2) ℝ := fun A B => ∑ a, ∑ e, G a e * E A a * (∑ b, ∑ c, ∑ d, Rm e b c d * K b * E B c * K d)
def remBound (M2 H c r ηL : ℝ) : ℝ := M2 * r ^ 2 / (2 * (1 - ηL) ^ 2) + |H| * r * ηL / (c * (1 - ηL))
def Dom5 (Kc M2 L c H r ρ : ℝ) : Prop := 0 < r ∧ r ≤ L * (1 + CAS07M01.eta Kc L) ∧ |ρ| ≤ remBound M2 H c r (CAS07M01.eta Kc L)
def Dom6 (Kc M2 L c H r s ρ : ℝ) : Prop := 0 < s ∧ s ≤ L ∧ s * (1 - CAS07M01.eta Kc s) ≤ r ∧ r ≤ s * (1 + CAS07M01.eta Kc s)
    ∧ |ρ| ≤ M2 * s ^ 2 / 2 + |H| * s * CAS07M01.eta Kc s / c
def modulus (r Z ℓ κ : ℝ) : ℝ := 5 * Real.logb 10 (r * Z ^ 2 / ℓ) + κ      -- ℓ = 10 pc in r's unit
def zMean (Z0 r c H ρ : ℝ) : ℝ := Z0 + (r / c) * H + ρ
```

## Targets (exact signatures; implicit `{n : ℕ}` where `n` appears)

### C02 — constant scale (separate from C03)

* **T1 normalized contractions** (frame level, reuses `CAS17C01`):
  * `unit_preserved (lam : ℝ) (hlam : lam ≠ 0) (a b : Vec) : scaledLorentz lam (scale lam⁻¹ a) (scale lam⁻¹ b) = lorentz a b`
  * `null_normalization_scale (lam μ : ℝ) (hlam : 0 < lam) (o n : Vec) (hoo : lorentz o o = -1) (hon : lorentz o n = 0) (hnn : lorentz n n = 1) :
      scaledLorentz lam (scale μ (Kvec o n)) (scale μ (Kvec o n)) = 0 ∧ (scaledLorentz lam (scale lam⁻¹ o) (scale μ (Kvec o n)) = 1 ↔ μ = lam⁻¹)`
  * `intercept_invariant (lam : ℝ) (hlam : lam ≠ 0) (o n u : Vec) : scaledLorentz lam (scale lam⁻¹ (Kvec o n)) (scale lam⁻¹ u) = lorentz (Kvec o n) u`
  * `intercept_formula (n u : Vec) : lorentz (Kvec ⟨1,0,0,0⟩ n) u = u.t + n.x*u.x + n.y*u.y + n.z*u.z` (I = Z0 = ζ0 + ζ·n for `n.t = 0`)
    — stated with hypothesis `(hn : n.t = 0)`.
  * `gamma_scale (lam) (hlam : lam ≠ 0) (u o) : gammaW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o) = CAS17C01.gamma u o`
  * `betaSqW_lorentz (u o) : betaSqW lorentz u o = CAS17C01.betaSq u o`
  * `betaSq_scale (lam) (hlam : lam ≠ 0) (u o) : betaSqW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o) = CAS17C01.betaSq u o`
  * `beta_scale (lam) (hlam : lam ≠ 0) (u o) : Real.sqrt (betaSqW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o)) = CAS17C01.beta u o`
* **T2 connection, B, A at chart level**:
  * `chris_scale (g) (x) (lam) (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det) (a b c) : chris (fun y => lam ^ 2 • g y) x a b c = chris g x a b c`
  * `physVel_scale (c lam) (u : Pt n → Pt n) : physVel c (fun y => lam⁻¹ • u y) = fun y => lam⁻¹ • physVel c u y`
  * `velocity_norm_scale (G : Arr2 n) (U : Pt n) (lam) (hlam : lam ≠ 0) : contr (lam ^ 2 • G) (lam⁻¹ • U) (lam⁻¹ • U) = contr G U U`
  * `accelContra_scale (g U x lam) (hlam : lam ≠ 0) (hdet) (a) : (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp a = (lam⁻¹) ^ 2 * (accelContra g U x).comp a`
  * `Bcov_scale (g U x lam) (hlam : lam ≠ 0) (hdet) (a b) : Bcov (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x a b = lam * Bcov g U x a b`
  * `accelCov_scale (g U x lam) (hlam : lam ≠ 0) (hdet) (b) : (accelCov (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp b = (accelCov g U x).comp b`
  * `orthonormal_scale (G E η lam) (hlam : lam ≠ 0) (h : Orthonormal G E η) : Orthonormal (lam ^ 2 • G) (fun α => lam⁻¹ • E α) η`
  * `B_measured_scale (g U x E lam) (hlam : lam ≠ 0) (hdet) (α β) : tet2 (Bcov (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x) (fun γ => lam⁻¹ • E γ) α β = lam⁻¹ * tet2 (Bcov g U x) E α β`
  * `A_measured_scale (g U x E η lam) (hlam : lam ≠ 0) (hdet) (α) : (tetVec (lam ^ 2 • g x) (fun γ => lam⁻¹ • E γ) η (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp).comp α = lam⁻¹ * (tetVec (g x) E η (accelContra g U x).comp).comp α`
  * `A_measNorm_scale (...) (hlam : 0 < lam) (hdet) : measNorm (tetVec (lam ^ 2 • g x) (fun γ => lam⁻¹ • E γ) η (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp) = lam⁻¹ * measNorm (tetVec (g x) E η (accelContra g U x).comp)`
  * `riemann_scale (g x lam) (hlam : lam ≠ 0) (hdet : ∀ y, IsUnit (Matrix.of (g y)).det) (a b c d) : riemann (fun y => lam ^ 2 • g y) x a b c d = riemann g x a b c d`
* **T3 affine normalization, redshift, slope**:
  * `chart_null_normalization (G : Arr2 n) (o K : Pt n) (lam μ : ℝ) (hlam : 0 < lam) (hoK : contr G o K = 1) : contr (lam ^ 2 • G) (lam⁻¹ • o) (μ • K) = 1 ↔ μ = lam⁻¹`
  * `affine_reparam (g) (γ : ℝ → Pt n) (lam s : ℝ) (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g (γ s))).det)
      (hgeo : ∀ a, deriv (deriv γ) s a + ∑ b, ∑ c, chris g (γ s) a b c * deriv γ s b * deriv γ s c = 0) :
      (fun t => γ (lam⁻¹ * t)) (lam * s) = γ s ∧ deriv (fun t => γ (lam⁻¹ * t)) (lam * s) = lam⁻¹ • deriv γ s ∧
      ∀ a, deriv (deriv (fun t => γ (lam⁻¹ * t))) (lam * s) a + ∑ b, ∑ c, chris (fun y => lam ^ 2 • g y) (γ s) a b c *
          deriv (fun t => γ (lam⁻¹ * t)) (lam * s) b * deriv (fun t => γ (lam⁻¹ * t)) (lam * s) c = 0`
    (observer-normalized affine length `r_λ = λ r`: the event at `g`-parameter `s` sits at `g_λ`-parameter `λ s`,
    the tangent there is `λ⁻¹ K`, and the affine geodesic equation of `λ²g` holds.)
  * `redshift_const_scale (ke Ue ko Uo : Pt n) (lam) (hlam : lam ≠ 0) : onePlusZ ke (lam⁻¹ • Ue) ko (lam⁻¹ • Uo) = onePlusZ ke Ue ko Uo`
  * `slope_scale (zf zl : ℝ → ℝ) (lam H c : ℝ) (hlam : 0 < lam) (hrel : ∀ D, 0 ≤ D → zl (lam * D) = zf D)
      (hz : HasDerivWithinAt zf (H / c) (Set.Ici 0) 0) : HasDerivWithinAt zl (lam⁻¹ * H / c) (Set.Ici 0) 0`
* **T4 dA, Kc, M2, L, calibration offset** (module `G17AOptics`, reuses `G01A`, `CAS07M05`, `CAS07M01`):
  * `tidal_scale (G Rm E K lam) (hlam : lam ≠ 0) (A B : Fin 2) : tidalMat (lam ^ 2 • G) Rm (fun A => lam⁻¹ • E A) (lam⁻¹ • K) A B = (lam⁻¹) ^ 2 * tidalMat G Rm E K A B`
  * `tidal_op_scale {Kc L Kc' L' : ℝ} (J : JacobiPremises Kc L) (Jl : JacobiPremises Kc' L') (lam) (hlam : lam ≠ 0)
      (G : ℝ → Arr2 n) (Rm : ℝ → Fin n → Fin n → Fin n → Fin n → ℝ) (E : ℝ → Fin 2 → Pt n) (K : ℝ → Pt n)
      (hJ : ∀ s, CAS07M05.matrixOf (J.R s) = tidalMat (G s) (Rm s) (E s) (K s))
      (hJl : ∀ σ, CAS07M05.matrixOf (Jl.R σ) = tidalMat (lam ^ 2 • G (lam⁻¹ * σ)) (Rm (lam⁻¹ * σ)) (fun A => lam⁻¹ • E (lam⁻¹ * σ) A) (lam⁻¹ • K (lam⁻¹ * σ))) :
      ∀ σ, Jl.R σ = (lam⁻¹) ^ 2 • J.R (lam⁻¹ * σ)`
  * `dA_scale {Kc L : ℝ} (lam) (hlam : 0 < lam) (J : JacobiPremises Kc L) (Jl : JacobiPremises ((lam⁻¹) ^ 2 * Kc) (L / lam⁻¹))
      (hR : ∀ σ ∈ Set.Icc 0 (L / lam⁻¹), Jl.R σ = (lam⁻¹) ^ 2 • J.R (lam⁻¹ * σ)) :
      ∀ s ∈ Set.Icc 0 L, Jl.D (lam * s) = lam • J.D s ∧
        Real.sqrt (Matrix.det (CAS07M05.matrixOf (Jl.D (lam * s)))) = lam * Real.sqrt (Matrix.det (CAS07M05.matrixOf (J.D s)))`
  * `bound_indices (Kc L lam) (hlam : lam ≠ 0) : (lam⁻¹) ^ 2 * Kc = Kc / lam ^ 2 ∧ L / lam⁻¹ = lam * L`  (`Kc'=λ⁻²Kc`, `L'=λL`)
  * `M2_identity (Z : ℝ → ℝ) (lam t : ℝ) : deriv (deriv (fun t => Z (lam⁻¹ * t))) t = (lam⁻¹) ^ 2 * deriv (deriv Z) (lam⁻¹ * t)`
  * `M2_scale (Z : ℝ → ℝ) (lam L M2 : ℝ) (hlam : 0 < lam) (hM : ∀ s ∈ Set.Icc 0 L, |deriv (deriv Z) s| ≤ M2) :
      ∀ t ∈ Set.Icc 0 (lam * L), |deriv (deriv (fun t => Z (lam⁻¹ * t))) t| ≤ M2 / lam ^ 2`
  * `eta_scale (Kc s lam) (hK : 0 ≤ Kc) (hlam : 0 < lam) : CAS07M01.eta (Kc / lam ^ 2) (lam * s) = CAS07M01.eta Kc s`
  * `remBound_scale (M2 H c r ηL lam) (hlam : lam ≠ 0) : remBound (M2 / lam ^ 2) (H / lam) c (lam * r) ηL = remBound M2 H c r ηL`  (requires `0 < lam` for `|H/lam|`; stated with `hlam : 0 < lam`)
  * `dom5_scale (Kc M2 L c H r ρ lam) (hK : 0 ≤ Kc) (hlam : 0 < lam) : Dom5 (Kc / lam ^ 2) (M2 / lam ^ 2) (lam * L) c (H / lam) (lam * r) ρ ↔ Dom5 Kc M2 L c H r ρ`
  * `dom6_scale (Kc M2 L c H r s ρ lam) (hK : 0 ≤ Kc) (hlam : 0 < lam) : Dom6 (Kc / lam ^ 2) (M2 / lam ^ 2) (lam * L) c (H / lam) (lam * r) (lam * s) ρ ↔ Dom6 Kc M2 L c H r s ρ`
  * `modulus_offset_invariant (lam r Z ℓ κ) (hlam : 0 < lam) (hr : 0 < r) (hZ : Z ≠ 0) (hℓ : 0 < ℓ) : modulus (lam * r) Z ℓ (κ - 5 * Real.logb 10 lam) = modulus r Z ℓ κ`
  * `zMean_invariant (Z0 r c H ρ lam) (hlam : lam ≠ 0) : zMean Z0 (lam * r) c (H / lam) ρ = zMean Z0 r c H ρ`

### C03 — general conformal factor (separate from C02)

* **T5 connection-difference identity**:
  * `ginv_conf (g φ x) (hdet : IsUnit (Matrix.of (g x)).det) : ginv (conf φ g) x = Real.exp (-(2 * φ x)) • ginv g x`
  * `conformal_christoffel (g φ x) (hg : DifferentiableAt ℝ g x) (hφ : DifferentiableAt ℝ φ x) (hdet : IsUnit (Matrix.of (g x)).det) (a b c) :
      chris (conf φ g) x a b c = chris g x a b c + (1 : Matrix (Fin n) (Fin n) ℝ) a c * pd φ x b + (1 : Matrix (Fin n) (Fin n) ℝ) a b * pd φ x c
        - g x b c * ∑ d, ginv g x a d * pd φ x d`
* **T6 acceleration and null rescaling**:
  * `conformal_selfCov (g φ V x m) (hg) (hφ) (hV : DifferentiableAt ℝ V x) (hdet) (a) :
      selfCov (conf φ g) (fun y => Real.exp (m * φ y) • V y) x a = Real.exp (2 * m * φ x) * (selfCov g V x a
        + (m + 2) * (∑ b, V x b * pd φ x b) * V x a - contr (g x) (V x) (V x) * ∑ d, ginv g x a d * pd φ x d)`
  * `conformal_accel (g φ U x c) (hg) (hφ) (hU : DifferentiableAt ℝ U x) (hdet) (hc : c ≠ 0) (hnorm : contr (g x) (U x) (U x) = -c ^ 2) (a) :
      (accelContra (conf φ g) (fun y => Real.exp (-φ y) • U y) x).comp a
        = Real.exp (-(2 * φ x)) * ((accelContra g U x).comp a + c ^ 2 * ∑ d, hinv g U c x a d * pd φ x d)`
  * `conformal_velocity_norm (g φ U x) : contr (conf φ g x) (Real.exp (-φ x) • U x) (Real.exp (-φ x) • U x) = contr (g x) (U x) (U x)`
  * `conformal_null_affine (g φ k x) (hg) (hφ) (hk : DifferentiableAt ℝ k x) (hdet) (hnull : contr (g x) (k x) (k x) = 0) (a) :
      selfCov (conf φ g) (fun y => Real.exp (-2 * φ y) • k y) x a = Real.exp (-4 * φ x) * selfCov g k x a`
* **T7 endpoint redshift from declared null/observer rescalings**:
  * `conformal_covector_null (g φ x k) (hdet) : covNorm (ginv (conf φ g) x) k = Real.exp (-(2 * φ x)) * covNorm (ginv g x) k`
  * `conformal_freq (k U φ0) : freq k (Real.exp (-φ0) • U) = Real.exp (-φ0) * freq k U`
  * `conformal_redshift (ke Ue ko Uo : Pt n) (φe φo : ℝ) : onePlusZ ke (Real.exp (-φe) • Ue) ko (Real.exp (-φo) • Uo) = Real.exp (φo - φe) * onePlusZ ke Ue ko Uo`
  * `conformal_redshift_z (…) : zOf (onePlusZ ke (exp(-φe)•Ue) ko (exp(-φo)•Uo)) + 1 = Real.exp (φo - φe) * (zOf (onePlusZ ke Ue ko Uo) + 1)`

### Negative controls and non-vacuity witnesses

* `minkowski_witness (c) (hc : c ≠ 0)` : with `eta4 : Arr2 4 := fun a b => if a = b then (if a = 0 then -1 else 1) else 0`,
  `IsUnit (Matrix.of eta4).det ∧ contr eta4 (c • e0) (c • e0) = -c ^ 2` (hypotheses of T5/T6 satisfiable).
* `conf_grad_counterexample (c) (hc : c ≠ 0)` (CONF-GRAD): with `g = fun _ => eta4`, `U = fun _ => c • e0`, `φ = fun x => x 1`:
  `φ 0 = 0 ∧ (accelContra g U 0).comp 1 = 0 ∧ (accelContra (conf φ g) (fun y => exp (-φ y) • U y) 0).comp 1 = c ^ 2`
  — `φ(p)=0` yet `A' ≠ A`; so general φ is not the constant case.
* `scale_inf_no_floor (N) (hN : 0 < N) : ∀ ε > 0, ∃ lam > 0, 0 < lam⁻¹ * N ∧ lam⁻¹ * N < ε` (SCALE-INF: no scale-independent positive |A| floor).
* `fixed_bound_breaks_domain : Dom5 0 0 1 1 0 1 0 ∧ ¬ Dom5 0 0 1 1 0 (2 * 1) 0` (SCALE-FIXEDBOUND: with FIXED `Kc,M2,L` the domain is not scale invariant).
* `redshift_const_is_special_case (…)` : the C02 redshift statement equals T7 with `φe = φo = log lam`.

## Not targeted (stated in advance)

Existence of the null geodesic / Jacobi field on a manifold; parallelism of the
rescaled screen frame as an ODE statement; reciprocity/transparency for `D_L`;
`A_cov = 2c B u`; metric compatibility `∇g = 0` as a separate lemma; any
general-conformal same-calibrated-data claim (excluded by CAS-17.json:80);
historical four-axis adjudication; scientific admission.
