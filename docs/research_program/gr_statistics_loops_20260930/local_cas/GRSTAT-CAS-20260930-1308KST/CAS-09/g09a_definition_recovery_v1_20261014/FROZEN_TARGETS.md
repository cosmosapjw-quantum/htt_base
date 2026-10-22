# G09-A frozen targets (written before any proof compile)

Module `lean/G09ADefinitions.lean`, namespace `G09A`. Toolchain: Lean 4.31.0, Mathlib
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f` (Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`).
Section variables: in sections `C01`, `C02`, `C03` every declaration mentioning `ι` carries
`{ι : Type*} [Fintype ι]`; in `Design`/`Native`/`C04` `{ι : Type*}` (and `[Fintype ι]` only where written).
Scientific admission: HOLD. Source map: `SOURCE_RECOVERY.md`.

## Fidelity to the card / contract

* Domains kept exactly as the source states them: `r_i > 0`, `c > 0`, `R, R1, R2 > 0`, `R1 ≠ R2`,
  unit directions where the source uses the sphere (alias family), `0 < |ε| < 1`, `Kc ≥ 0`,
  `M2 ≥ 0`, `L > 0`, `η(L) < 1`, future branch `ζ0 = +√(1+|ζ|²)`.
  Where a proof does not need a source hypothesis (e.g. unit norm in the two-radius theorem,
  `R2 > 0` in the angular negative control, `c > 0` in N4) the theorem is stated *without* it, i.e.
  more generally; no hypothesis is added that the source does not state.
* "Declared nonzero determinants" (C01) = injectivity of the 9×9 `E9` block (unisolvency) and of the
  4×4 repeated `E4` block; these are hypotheses of the source theorem (NATIVE l.150), not conclusions.
* "Rank" = `Module.finrank ℝ (LinearMap.range _)` of the coefficient-to-observation linear map, i.e.
  the matrix rank in the declared coordinate basis. E9's basis is left free by the source; the basis
  used here contains the degree≤1 basis and `stf` is proved bijective onto STF tensors.
* C04 is the algebraic substitution (contract wording); N4 (strict-slack neighbourhood) is proved
  separately and ONLY for the enlarged outer domain `Omega5`. No physical-realizability predicate is
  defined (pitfall: realizable remainder domain ≠ enlarged admissible space).

## Primary targets

| id | component | Lean name | intended status |
|---|---|---|---|
| T-BASIS-1 | E9 basis = STF coordinates (bijective onto symmetric trace-free 3×3) | `stf_transpose`, `stf_trace`, `stf_injective`, `stf_stfCoords`, `quad_eq` | prove |
| T-BASIS-2 | chart dimensions 4 / 9 / 12 | `finrank_IPar`, `finrank_HPar`, `finrank_PhysPar` | prove |
| T-C01-a | rank-of-concatenation identity | `rank_concat_identity` | prove |
| T-C01-b | Theorem N3 criterion (11) | `rank13_iff`, `rank13_needs_N` | prove |
| T-C01-c | two-radius 9+4 design by coefficient elimination | `two_radius_injective`, `two_radius_rank13` | prove |
| T-C01-w | exact rational sphere-direction witness (non-vacuity) | `dirStar_unit`, `dirStar_unisolvent`, `σStar_E4`, `witness_rank13` | prove |
| T-C01-n | DESIGN-ANGULAR negative control | `two_radius_fails_of_E4_deficient` | prove |
| T-C02-a | mass-shell chart: future branch, hyperboloid, injective, rank-3 derivative | `one_le_zeta0`, `zeta0_pos`, `massShell_hyperboloid`, `massShell_injective`, `dEmb_injective`, `dEmb_rank3`, `chartDeriv_injective` | prove |
| T-C02-b | 12→13 composition and canonical Jacobian (14) | `physMean_eq_X`, `Jphys_apply` | prove |
| T-C02-c | `Jphys` is the Fréchet derivative of the physical mean | `hasFDerivAt_zeta0`, `hasFDerivAt_physMean` | prove |
| T-C02-d | rank 13 ⇒ physical rank 12 | `Xmap_injective_of_rank13`, `rank12_of_rank13`, `witness_rank12` | prove |
| T-C03-a | positive alias denominator | `aliasDenom_pos`, `aliasRadius_pos` | prove |
| T-C03-b | constant radius: inclusion, rank = rank E9 ≤ 9, = 9 if unisolvent; rank Jphys = 9 | `const_radius_range_le`, `const_radius_rank`, `const_radius_rank_le9`, `const_radius_rank9`, `const_radius_Jphys_rank9` | prove |
| T-C03-c | exact degeneracy (12) | `const_radius_exact_degeneracy`, `const_radius_physMean_degeneracy` | prove |
| T-C03-d | radial alias (13): inclusion via exact basis identity, rank 9 | `Hval_aliasLift`, `radial_alias_range_le`, `radial_alias_rank`, `radial_alias_rank9`, `witness_radial_alias_rank9` | prove |
| T-C03-n | DESIGN-R1R2 negative control | `two_radius_equal_fails` | prove |
| T-C04-a | ρ substitution reproduces Z and both native means | `nativeZ_rhoOf`, `rhoOf_native_means`, `rhoOf_true` | prove |
| T-C04-b | domain well-definedness: log argument, η ≥ 0, 1−ηL > 0, E ≥ 0 | `meanMu_arg_pos`, `eta_nonneg`, `one_sub_etaL_pos`, `E5_nonneg` | prove |
| T-C04-c | N4 strict slack neighbourhood in Ω (5) | `strict_slack_local_identification` | prove |
| T-C04-n | SLACK-BOUNDARY negative control | `slack_boundary_no_neighbourhood` | prove |

## Explicitly not targeted (no claim)

* IFT local injectivity from rank 12; converse "rank Jphys = 12 ⇒ rank X = 13" (source says false in general).
* Equivalent projector form `rank[(I−P4) D E9] = 9`.
* `Omega6 ⊆ Omega5` (needs η monotonicity, CAS-07 material), membership of true catalogues in Ω
  (GR-FD), physical realizability of any Ω point.
* N1/N2 coverage, N-SCALE, nuisance projection `rank(PWJphys)`, any precision/conditioning statement.
* Global nonlinear (non)identifiability; "three-dimensional hyperboloid" as a manifold-dimension statement.

## Exact frozen Lean signatures (auto-extracted from the source before compiling)

```lean
abbrev V3
def dot3 (a b : V3) : ℝ
def IsUnitDir (n : V3) : Prop
abbrev IPar
abbrev HPar
abbrev PhysPar
def stf (q : Fin 5 → ℝ) : Matrix (Fin 3) (Fin 3) ℝ
def stfCoords (M : Matrix (Fin 3) (Fin 3) ℝ) : Fin 5 → ℝ
def quad (q : Fin 5 → ℝ) (n : V3) : ℝ
def ipoly (a : IPar) (n : V3) : ℝ
def Hval (h : HPar) (n : V3) : ℝ
noncomputable def zeta0 (ζ : V3) : ℝ
noncomputable def Z0 (ζ n : V3) : ℝ
noncomputable def massShell (ζ : V3) : IPar
def E4 (dir : ι → V3) : IPar →ₗ[ℝ] (ι → ℝ)
def E9 (dir : ι → V3) : HPar →ₗ[ℝ] (ι → ℝ)
def Dmap (r : ι → ℝ) (c : ℝ) : (ι → ℝ) →ₗ[ℝ] (ι → ℝ)
def Xmap (dir : ι → V3) (r : ι → ℝ) (c : ℝ) : IPar × HPar →ₗ[ℝ] (ι → ℝ)
noncomputable def dEmb (ζ : V3) : V3 →ₗ[ℝ] IPar
noncomputable def chartDeriv (ζ : V3) : PhysPar →ₗ[ℝ] IPar × HPar
noncomputable def Jphys (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (ζ : V3) : PhysPar →ₗ[ℝ] (ι → ℝ)
noncomputable def physMean (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) : ι → ℝ
def twoRadiusDir (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) : Fin 9 ⊕ Fin 4 → V3
def twoRadiusR (R1 R2 : ℝ) : Fin 9 ⊕ Fin 4 → ℝ
noncomputable def aliasRadius (R ε : ℝ) (n : V3) : ℝ
noncomputable def nativeZ (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) (ρ : ι → ℝ) : ι → ℝ
def meanZ (Z : ι → ℝ) : ι → ℝ
noncomputable def meanMu (r Z : ι → ℝ) (tenpc : ℝ) : ι → ℝ
def NativeDomain (r Z : ι → ℝ) : Prop
noncomputable def rhoOf (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (Z : ι → ℝ) (x : PhysPar) : ι → ℝ
noncomputable def eta (Kc s : ℝ) : ℝ
structure EnvelopeParams
noncomputable def EnvelopeParams.etaL (P : EnvelopeParams) : ℝ
noncomputable def E5 (P : EnvelopeParams) (c Hn r : ℝ) : ℝ
def Omega5 (P : EnvelopeParams) (c : ℝ) (dir : ι → V3) (x : PhysPar) (r ρ : ι → ℝ) : Prop
def Omega6 (P : EnvelopeParams) (c : ℝ) (dir : ι → V3) (x : PhysPar) (r ρ : ι → ℝ) : Prop
theorem stf_transpose (q : Fin 5 → ℝ) : (stf q).transpose = stf q
theorem stf_trace (q : Fin 5 → ℝ) : Matrix.trace (stf q) = 0
theorem stf_injective : Function.Injective stf
theorem stf_stfCoords (M : Matrix (Fin 3) (Fin 3) ℝ) (hM : M.transpose = M) (htr : Matrix.trace M = 0) : stf (stfCoords M) = M
theorem quad_eq (q : Fin 5 → ℝ) (n : V3) : quad q n = dotProduct n ((stf q).mulVec n)
theorem finrank_IPar : Module.finrank ℝ IPar = 4
theorem finrank_HPar : Module.finrank ℝ HPar = 9
theorem finrank_PhysPar : Module.finrank ℝ PhysPar = 12
theorem Dmap_injective (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : Function.Injective (Dmap r c)
theorem finrank_range_DE9 (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : Module.finrank ℝ (LinearMap.range ((Dmap r c).comp (E9 dir))) = Module.finrank ℝ (LinearMap.range (E9 dir))
theorem rank_concat_identity (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) + Module.finrank ℝ (LinearMap.range (E4 dir) ⊓ LinearMap.range ((Dmap r c).comp (E9 dir)) : Submodule ℝ (ι → ℝ)) = Module.finrank ℝ (LinearMap.range (E4 dir)) + Module.finrank ℝ (LinearMap.range (E9 dir))
theorem rank13_iff (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hr : ∀ i, 0 < r i) (hc : 0 < c) : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13 ↔ Module.finrank ℝ (LinearMap.range (E4 dir)) = 4 ∧ Module.finrank ℝ (LinearMap.range (E9 dir)) = 9 ∧ (LinearMap.range (E4 dir) ⊓ LinearMap.range ((Dmap r c).comp (E9 dir)) : Submodule ℝ (ι → ℝ)) = ⊥
theorem rank13_needs_N (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (h : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13) : 13 ≤ Fintype.card ι
theorem Hval_add (h k : HPar) (n : V3) : Hval (h + k) n = Hval h n + Hval k n
theorem Hval_smul (t : ℝ) (h : HPar) (n : V3) : Hval (t • h) n = t * Hval h n
def liftLin (a : IPar) : HPar
theorem Hval_liftLin (a : IPar) (n : V3) : Hval (liftLin a) n = ipoly a n
theorem two_radius_injective (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2) (huni : Function.Injective (E9 dir9)) (hE4 : Function.Injective (E4 (dir9 ∘ σ))) : Function.Injective (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c)
theorem finrank_range_of_injective_13 {ι : Type*} [Fintype ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (h : Function.Injective (Xmap dir r c)) : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13
theorem two_radius_rank13 (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hR2 : 0 < R2) (hc : 0 < c) (hne : R1 ≠ R2) (huni : Function.Injective (E9 dir9)) (hE4 : Function.Injective (E4 (dir9 ∘ σ))) : Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c)) = 13
theorem finrank_range_lt_13_of_not_injective {ι : Type*} [Fintype ι] (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (h : ¬ Function.Injective (Xmap dir r c)) : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) < 13
theorem two_radius_fails_of_E4_deficient (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R1 R2 c : ℝ) (hR1 : 0 < R1) (hc : 0 < c) (hE4 : ¬ Function.Injective (E4 (dir9 ∘ σ))) : Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R1 R2) c)) < 13
noncomputable def dirStar : Fin 9 → V3
def σStar : Fin 4 → Fin 9
theorem dirStar_unit : ∀ j, IsUnitDir (dirStar j)
theorem dirStar_unisolvent : Function.Injective (E9 dirStar)
theorem σStar_E4 : Function.Injective (E4 (dirStar ∘ σStar))
theorem witness_rank13 : Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dirStar σStar) (twoRadiusR 1 2) 1)) = 13
theorem one_le_one_add_dot3 (ζ : V3) : 1 ≤ 1 + dot3 ζ ζ
theorem one_le_zeta0 (ζ : V3) : 1 ≤ zeta0 ζ
theorem zeta0_pos (ζ : V3) : 0 < zeta0 ζ
theorem massShell_hyperboloid (ζ : V3) : (massShell ζ).1 ^ 2 - dot3 (massShell ζ).2 (massShell ζ).2 = 1 ∧ 1 ≤ (massShell ζ).1
theorem massShell_injective : Function.Injective massShell
theorem physMean_eq_X (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) : physMean dir r c x = Xmap dir r c (massShell x.1, x.2)
theorem Jphys_apply (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (ζ : V3) (δζ : V3) (δh : HPar) (i : ι) : Jphys dir r c ζ (δζ, δh) i = dot3 δζ (dir i) + dot3 ζ δζ / zeta0 ζ + (r i / c) * Hval δh (dir i)
noncomputable def zeta0Deriv (ζ : V3) : V3 →ₗ[ℝ] ℝ
theorem hasFDerivAt_zeta0 (ζ : V3) : HasFDerivAt zeta0 (LinearMap.toContinuousLinearMap (zeta0Deriv ζ)) ζ
theorem hasFDerivAt_physMean (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) : HasFDerivAt (physMean dir r c) (LinearMap.toContinuousLinearMap (Jphys dir r c x.1)) x
theorem dEmb_injective (ζ : V3) : Function.Injective (dEmb ζ)
theorem chartDeriv_injective (ζ : V3) : Function.Injective (chartDeriv ζ)
theorem dEmb_rank3 (ζ : V3) : Module.finrank ℝ (LinearMap.range (dEmb ζ)) = 3
theorem Xmap_injective_of_rank13 (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (h : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13) : Function.Injective (Xmap dir r c)
theorem rank12_of_rank13 (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (h : Module.finrank ℝ (LinearMap.range (Xmap dir r c)) = 13) (ζ : V3) : Module.finrank ℝ (LinearMap.range (Jphys dir r c ζ)) = 12
theorem witness_rank12 (ζ : V3) : Module.finrank ℝ (LinearMap.range (Jphys (twoRadiusDir dirStar σStar) (twoRadiusR 1 2) 1 ζ)) = 12
theorem aliasDenom_pos (n : V3) (ε : ℝ) (hn : IsUnitDir n) (hε : |ε| < 1) : 0 < 1 + ε * n 2
theorem aliasRadius_pos (R ε : ℝ) (n : V3) (hR : 0 < R) (hn : IsUnitDir n) (hε : |ε| < 1) : 0 < aliasRadius R ε n
theorem scale_cancel (R c p : ℝ) (hR : 0 < R) (hc : 0 < c) : R / c * (c / R * p) = p
theorem const_radius_range_le (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) : LinearMap.range (E4 dir) ≤ LinearMap.range ((Dmap (fun _ => R) c).comp (E9 dir))
theorem range_X_of_le (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (hle : LinearMap.range (E4 dir) ≤ LinearMap.range ((Dmap r c).comp (E9 dir))) : LinearMap.range (Xmap dir r c) = LinearMap.range ((Dmap r c).comp (E9 dir))
theorem const_radius_rank (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) : Module.finrank ℝ (LinearMap.range (Xmap dir (fun _ => R) c)) = Module.finrank ℝ (LinearMap.range (E9 dir))
theorem const_radius_rank_le9 (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) : Module.finrank ℝ (LinearMap.range (Xmap dir (fun _ => R) c)) ≤ 9
theorem const_radius_rank9 (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) (huni : Function.Injective (E9 dir)) : Module.finrank ℝ (LinearMap.range (Xmap dir (fun _ => R) c)) = 9
theorem const_radius_Jphys_rank9 (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) (huni : Function.Injective (E9 dir)) (ζ : V3) : Module.finrank ℝ (LinearMap.range (Jphys dir (fun _ => R) c ζ)) = 9
theorem const_radius_exact_degeneracy (R c : ℝ) (hR : 0 < R) (hc : 0 < c) (ζ ζ' : V3) (h : HPar) : ∃ h' : HPar, ∀ n : V3, Z0 ζ' n + (R / c) * Hval h' n = Z0 ζ n + (R / c) * Hval h n
theorem const_radius_physMean_degeneracy (dir : ι → V3) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) (ζ ζ' : V3) (h : HPar) : ∃ h' : HPar, physMean dir (fun _ => R) c (ζ', h') = physMean dir (fun _ => R) c (ζ, h)
theorem two_radius_equal_fails (dir9 : Fin 9 → V3) (σ : Fin 4 → Fin 9) (R c : ℝ) (hR : 0 < R) (hc : 0 < c) : Module.finrank ℝ (LinearMap.range (Xmap (twoRadiusDir dir9 σ) (twoRadiusR R R) c)) ≤ 9
noncomputable def aliasLift (R ε c : ℝ) (a : IPar) : HPar
theorem Hval_aliasLift (R ε c : ℝ) (a : IPar) (n : V3) (hn : IsUnitDir n) : Hval (aliasLift R ε c a) n = (c / R) * ((1 + ε * n 2) * ipoly a n)
theorem radial_alias_range_le (dir : ι → V3) (R ε c : ℝ) (hunit : ∀ i, IsUnitDir (dir i)) (hR : 0 < R) (hc : 0 < c) (hε0 : 0 < |ε|) (hε1 : |ε| < 1) : LinearMap.range (E4 dir) ≤ LinearMap.range ((Dmap (fun i => aliasRadius R ε (dir i)) c).comp (E9 dir))
theorem radial_alias_rank (dir : ι → V3) (R ε c : ℝ) (hunit : ∀ i, IsUnitDir (dir i)) (hR : 0 < R) (hc : 0 < c) (hε0 : 0 < |ε|) (hε1 : |ε| < 1) : Module.finrank ℝ (LinearMap.range (Xmap dir (fun i => aliasRadius R ε (dir i)) c)) = Module.finrank ℝ (LinearMap.range (E9 dir))
theorem radial_alias_rank9 (dir : ι → V3) (R ε c : ℝ) (hunit : ∀ i, IsUnitDir (dir i)) (hR : 0 < R) (hc : 0 < c) (hε0 : 0 < |ε|) (hε1 : |ε| < 1) (huni : Function.Injective (E9 dir)) : Module.finrank ℝ (LinearMap.range (Xmap dir (fun i => aliasRadius R ε (dir i)) c)) = 9
theorem witness_radial_alias_rank9 : Module.finrank ℝ (LinearMap.range (Xmap dirStar (fun i => aliasRadius 1 (1/2) (dirStar i)) 1)) = 9
theorem nativeZ_rhoOf (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (Z : ι → ℝ) (x : PhysPar) : nativeZ dir r c x (rhoOf dir r c Z x) = Z
theorem rhoOf_native_means (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (Z : ι → ℝ) (x : PhysPar) (tenpc : ℝ) : meanZ (nativeZ dir r c x (rhoOf dir r c Z x)) = meanZ Z ∧ meanMu r (nativeZ dir r c x (rhoOf dir r c Z x)) tenpc = meanMu r Z tenpc
theorem rhoOf_true (dir : ι → V3) (r : ι → ℝ) (c : ℝ) (x : PhysPar) (ρ : ι → ℝ) : rhoOf dir r c (nativeZ dir r c x ρ) x = ρ
theorem meanMu_arg_pos (r Z : ι → ℝ) (tenpc : ℝ) (hD : NativeDomain r Z) (ht : 0 < tenpc) (i : ι) : 0 < r i * Z i ^ 2 / tenpc
theorem eta_nonneg (Kc s : ℝ) (hKc : 0 ≤ Kc) (hs : 0 < s) : 0 ≤ eta Kc s
theorem one_sub_etaL_pos (P : EnvelopeParams) : 0 < 1 - P.etaL
theorem E5_nonneg (P : EnvelopeParams) (c Hn r : ℝ) (hc : 0 < c) (hr : 0 ≤ r) : 0 ≤ E5 P c Hn r
theorem continuous_zeta0 : Continuous zeta0
theorem continuous_Hval (n : V3) : Continuous fun h : HPar => Hval h n
theorem strict_slack_local_identification [Fintype ι] (P : EnvelopeParams) (c : ℝ) (dir : ι → V3) (r : ι → ℝ) (xstar : PhysPar) (ρstar : ι → ℝ) (S : Set PhysPar) (hS : S ∈ 𝓝 xstar) (hr : ∀ i, 0 < r i ∧ r i ≤ P.L * (1 + P.etaL)) (hslack : ∀ i, |ρstar i| < E5 P c (Hval xstar.2 (dir i)) (r i)) : ∀ᶠ x in 𝓝 xstar, x ∈ S ∧ Omega5 P c dir x r (rhoOf dir r c (nativeZ dir r c xstar ρstar) x) ∧ nativeZ dir r c x (rhoOf dir r c (nativeZ dir r c xstar ρstar) x) = nativeZ dir r c xstar ρstar
noncomputable def P0 : EnvelopeParams
noncomputable def dir0 : Fin 1 → V3
def r0 : Fin 1 → ℝ
def x0 : PhysPar
def ρ0 : Fin 1 → ℝ
theorem slack_boundary_no_neighbourhood : (∀ i, |ρ0 i| = E5 P0 1 (Hval x0.2 (dir0 i)) (r0 i)) ∧ ¬ (∀ᶠ x in 𝓝 x0, Omega5 P0 1 dir0 x r0 (rhoOf dir0 r0 1 (nativeZ dir0 r0 1 x0 ρ0) x))
```

## Addendum after compile (no statement change)

Compile attempt `raw/compile_01_main` failed on proofs and on computability only. The only
declaration-header change before the passing compile `raw/compile_06_main` was marking `Dmap` and
`Xmap` as `noncomputable` (real division); all theorem statements above are unchanged
(verified by re-extracting and diffing the signatures).
