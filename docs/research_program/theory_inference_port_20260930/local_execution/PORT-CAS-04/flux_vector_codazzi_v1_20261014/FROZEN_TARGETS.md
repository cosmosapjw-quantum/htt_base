# P04-A frozen targets (written before the first proof compile)

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/P04-A.json` (extracted sha256
`5444498ebb7b68aed6eee431a730d079f05cdd52ba7aa44c19b43c1206d1430c`).
Source obligation: `CAS_CONTRACT.json` CAS-04 (sha256 `904d95fe…3c389fad`):
identity `J=w gamma^2 beta; beta=2r/(1+sqrt(1+4r^2)); D_bK^b_a-D_aK=kappa J_a`,
assumptions `single fluid w>0; K=-hh nabla n; inverse length; no multi-fluid converse`,
signature `-+++`, `u=U/c`. Conventions recovered verbatim in `SOURCE_RECOVERY.md`.

Module `FluxVectorCodazzi`, namespace `PORTCAS04FluxVectorCodazzi`.
Imports (unchanged, reviewed): `PortCas01`, `VelocityJetRest`, `VelocityJetDecomposition`
(P03-A), `FluxScalarInverse` (P04 scalar unit).
Abbreviations: `M := Matrix (Fin 4) (Fin 4) ℝ`, `V := Fin 4 → ℝ`; `projDown g n = δ_a^b + n_a n^b`,
`projUp g n = δ^a_b + n^a n_b`, `hDown g n = g_ab + n_a n_b`, `spatialJet g n D = projDown·D·projDownᵀ`
(all from P03-A); `betaOfRatio r = 2r/(1+sqrt(1+4r²))` (from the scalar unit).

## Definitions

```lean
def perfectFluid (g : M) (w p : ℝ) (u : V) : M := w • vecMulVec (g *ᵥ u) (g *ᵥ u) + p • g
                                  -- T_ab = (ε+p) u_a u_b + p g_ab, w = ε+p
def normalFlux (g : M) (n : V) (T : M) : V := -((projDown g n * T) *ᵥ n)   -- J_a = -h_a^b T_bc n^c
def normalEnergy (n : V) (T : M) : ℝ := n ⬝ᵥ (T *ᵥ n)                      -- E_N = T_ab n^a n^b
def normalStress (g : M) (n : V) (T : M) : M := projDown g n * T * (projDown g n)ᵀ  -- S = hhT
noncomputable def fluxNorm (ginv : M) (J : V) : ℝ := Real.sqrt (J ⬝ᵥ (ginv *ᵥ J))  -- sqrt(J_a J^a)
noncomputable def betaVector (ginv : M) (w : ℝ) (J : V) : V :=
  if J = 0 then 0 else (betaOfRatio (fluxNorm ginv J / w) / fluxNorm ginv J) • J
```
Chart level (`Pt := Fin 4 → ℝ`, `pd f x a := fderiv ℝ f x (Pi.single a 1)` from P03-A):
```lean
noncomputable def christoffel (g ginv : Pt → M) (y : Pt) (a b c : Fin 4) : ℝ :=
  (1/2) * ∑ d, ginv y a d * (pd (fun z => g z d c) y b + pd (fun z => g z d b) y c
                              - pd (fun z => g z b c) y d)                  -- Γ^a_{bc}, Levi-Civita
noncomputable def ricci (Γ : Pt → Fin 4 → Fin 4 → Fin 4 → ℝ) (x : Pt) (b d : Fin 4) : ℝ :=
  ∑ a, pd (fun y => Γ y a d b) x a - ∑ a, pd (fun y => Γ y a a b) x d
  + ∑ a, ∑ e, Γ x a a e * Γ x e d b - ∑ a, ∑ e, Γ x a d e * Γ x e a b      -- R_bd = R^a_{bad}
noncomputable def scalarCurvature Γ ginv x := ∑ b, ∑ d, ginv x b d * ricci Γ x b d
noncomputable def einstein Γ g ginv x b d := ricci Γ x b d - (1/2) * scalarCurvature Γ ginv x * g x b d
noncomputable def sliceNormal (ginv : Pt → M) (y : Pt) : V :=
  fun a => -ginv y a 0 / Real.sqrt (-ginv y 0 0)          -- n^a = g^{ab}n_b, n_b = -δ_b^0/sqrt(-g^00)
noncomputable def extrinsicDown g ginv y : M :=
  -spatialJet (g y) (sliceNormal ginv y) (velJetMatrix (christoffel g ginv) g (sliceNormal ginv) y)
                                                          -- K_ab = -h_a^c h_b^d ∇_c n_d
noncomputable def extrinsicMixed g ginv y : M := ginv y * extrinsicDown g ginv y   -- K^b_a
noncomputable def meanCurvature g ginv y : ℝ := trace (extrinsicMixed g ginv y)    -- K
noncomputable def nablaMixed Γ Km x r p q : ℝ :=
  pd (fun y => Km y p q) x r + ∑ s, Γ x p r s * Km x s q - ∑ s, Γ x s r q * Km x p s  -- ∇_r K^p_q
noncomputable def codazziDiv g ginv x a : ℝ :=      -- D_b K^b_a = h^b_p h^q_a h^r_b ∇_r K^p_q
  ∑ b, ∑ p, ∑ q, ∑ r, P b p * P q a * P r b * nablaMixed (christoffel g ginv) (extrinsicMixed g ginv) x r p q
  -- with P := projUp (g x) (sliceNormal ginv x)
noncomputable def codazziGrad g ginv x a : ℝ := ∑ r, P r a * pd (meanCurvature g ginv) x r  -- D_a K
noncomputable def codazziLHS g ginv x a : ℝ := codazziDiv g ginv x a - codazziGrad g ginv x a
structure GaussianChart (g ginv : Pt → M) (U : Set Pt) : Prop where
  isOpen : IsOpen U
  symm : ∀ y ∈ U, (g y)ᵀ = g y
  inv : ∀ y ∈ U, g y * ginv y = 1
  g00 : ∀ y ∈ U, g y 0 0 = -1
  g0i : ∀ y ∈ U, ∀ i : Fin 4, i ≠ 0 → g y 0 i = 0
```

## Frozen theorem signatures

Pointwise hypotheses used below: `hg : gᵀ = g`, `hinv : g * ginv = 1`,
`hn : n ⬝ᵥ (g *ᵥ n) = -1`, `hβ : n ⬝ᵥ (g *ᵥ β) = 0`,
`hu : (γ • (n + β)) ⬝ᵥ (g *ᵥ (γ • (n + β))) = -1` (normalization `u·u=-1` of `u=γ(n+β)`),
`hpos : β ≠ 0 → 0 < β ⬝ᵥ (g *ᵥ β)` (β spacelike; discharged for Minkowski in C4).

**A. Perfect-fluid normal projection (exact γ² coefficient)**
```lean
A1 normalFlux_perfectFluid (hg hn hβ) (w p γ) :
    normalFlux g n (perfectFluid g w p (γ • (n + β))) = (w * γ ^ 2) • (g *ᵥ β)
A2 normalEnergy_perfectFluid (hg hn hβ) (w p γ) :
    normalEnergy n (perfectFluid g w p (γ • (n + β))) = w * γ ^ 2 - p
A3 normalStress_perfectFluid (hg hn hβ) (w p γ) :
    normalStress g n (perfectFluid g w p (γ • (n + β))) =
      p • hDown g n + (w * γ ^ 2) • vecMulVec (g *ᵥ β) (g *ᵥ β)
A4 gamma_sq_of_normalized (hg hn hβ hu) :
    β ⬝ᵥ (g *ᵥ β) < 1 ∧ γ ^ 2 = 1 / (1 - β ⬝ᵥ (g *ᵥ β))
A5 flux_exact_coefficient (hg hn hβ hu) (w p) :
    normalFlux g n (perfectFluid g w p (γ • (n + β))) = (w / (1 - β ⬝ᵥ (g *ᵥ β))) • (g *ᵥ β)
A6 beta_eq_flux_div_enthalpy (hg hn hβ hu) (hw : w ≠ 0) (p) :
    g *ᵥ β = (normalEnergy n T + p)⁻¹ • normalFlux g n T      -- T := perfectFluid g w p (γ•(n+β))
A7 normalStress_rank_one (hg hn hβ hu) (hw : w ≠ 0) (p) :
    normalStress g n T = p • hDown g n + (normalEnergy n T + p)⁻¹ • vecMulVec (normalFlux g n T) (normalFlux g n T)
```
**B. Scalar inverse `r = |J|/w`**
```lean
B1 betaOfRatio_denominator_pos (r : ℝ) : 0 < 1 + Real.sqrt (1 + 4 * r ^ 2)
B2 betaOfRatio_zero : betaOfRatio 0 = 0
B3 betaOfRatio_mem (hr : 0 ≤ r) : 0 ≤ betaOfRatio r ∧ betaOfRatio r < 1
B4 betaOfRatio_solves (hr : 0 ≤ r) : betaOfRatio r / (1 - betaOfRatio r ^ 2) = r
B5 betaOfRatio_unique (hb0 : 0 ≤ b) (hb1 : b < 1) (h : b / (1 - b ^ 2) = r) : b = betaOfRatio r
B6 fluxNorm_perfectFluid (hg hinv hn hβ hu) (hw : 0 ≤ w) (p) :
    fluxNorm ginv (normalFlux g n T) = w * γ ^ 2 * Real.sqrt (β ⬝ᵥ (g *ᵥ β))
B7 scalar_flux_inverse (hg hinv hn hβ hu) (hw : 0 < w) (hβnn : 0 ≤ β ⬝ᵥ (g *ᵥ β)) (p) :
    betaOfRatio (fluxNorm ginv (normalFlux g n T) / w) = Real.sqrt (β ⬝ᵥ (g *ᵥ β))
B8 flux_zero_iff (hg hinv hn hβ hu) (hw : w ≠ 0) (p) : normalFlux g n T = 0 ↔ β = 0
```
**C. Vector inverse (zero / nonzero direction branches)**
```lean
C1 betaVector_zero (ginv w) : betaVector ginv w 0 = 0
C2 betaVector_of_ne (hJ : J ≠ 0) :
    betaVector ginv w J = (betaOfRatio (fluxNorm ginv J / w) / fluxNorm ginv J) • J
C3 vector_flux_inverse (hg hinv hn hβ hu) (hw : 0 < w) (hpos) (p) :
    betaVector ginv w (normalFlux g n T) = g *ᵥ β ∧ ginv *ᵥ betaVector ginv w (normalFlux g n T) = β
C4 minkowski_flux_inverse (x y z) (hs : PortCas01.s x y z < 1) (hw : 0 < w) (p) :
    PortCas01.fourVelocity x y z = PortCas01.gamma x y z • (PortCas01.e0 + ![0, x, y, z]) ∧
    normalFlux eta e0 (perfectFluid eta w p (fourVelocity x y z)) = (w * gamma x y z ^ 2) • ![0, x, y, z] ∧
    betaVector eta w (normalFlux …) = ![0, x, y, z] ∧
    betaOfRatio (fluxNorm eta (normalFlux …) / w) = Real.sqrt (PortCas01.s x y z)
```
**D. Multi-fluid negative control (no J=0 ⇒ untilted converse)**
```lean
D1 normalFlux_add : normalFlux g n (T₁ + T₂) = normalFlux g n T₁ + normalFlux g n T₂
D2 counterflow_control :   -- b = ![0,1/2,0,0], γ = 2/√3, w₁=w₂=1, p=0, Minkowski, n=e0
    both components normalized ∧ total normalFlux = 0 ∧ b ≠ 0 ∧ component normalFlux ≠ 0
D3 not_total_flux_zero_implies_untilted :
    ¬ ∀ (w₁ w₂ p₁ p₂ γ₁ γ₂ : ℝ) (β₁ β₂ : V), 0 < w₁ → 0 < w₂ →
      e0 ⬝ᵥ (eta *ᵥ β₁) = 0 → e0 ⬝ᵥ (eta *ᵥ β₂) = 0 →
      (γ₁ • (e0 + β₁)) ⬝ᵥ (eta *ᵥ (γ₁ • (e0 + β₁))) = -1 →
      (γ₂ • (e0 + β₂)) ⬝ᵥ (eta *ᵥ (γ₂ • (e0 + β₂))) = -1 →
      normalFlux eta e0 (perfectFluid eta w₁ p₁ (γ₁ • (e0 + β₁)) + perfectFluid eta w₂ p₂ (γ₂ • (e0 + β₂))) = 0 →
      β₁ = 0
```
**E. Chart-level contracted Codazzi (Gaussian normal chart, explicit Einstein hypothesis)**

`hG : GaussianChart g ginv U`, `hx : x ∈ U`,
`hdiff : ∀ a b c, DifferentiableAt ℝ (fun y => christoffel g ginv y a b c) x` (C¹ connection at x),
`n := sliceNormal ginv`, `Γ := christoffel g ginv`.
```lean
E1 sliceNormal_unit (hinv : g y * ginv y = 1) (h00 : ginv y 0 0 < 0) :
    sliceNormal ginv y ⬝ᵥ (g y *ᵥ sliceNormal ginv y) = -1 ∧ 0 < sliceNormal ginv y 0
E1' sliceNormal_gaussian (hG) (hy : y ∈ U) : sliceNormal ginv y = Pi.single 0 1
E2 extrinsic_gaussian (hG) (hy : y ∈ U) (a b) :
    extrinsicDown g ginv y a b = -(1/2) * pd (fun z => g z a b) y 0        -- K_ij = -½ ∂_0 h_ij
E3 einstein_mixed_gaussian (hG hx hdiff) (i) (hi : i ≠ 0) :
    einstein Γ g ginv x 0 i = -codazziLHS g ginv x i                      -- G_0i = -D_jK^j_i + D_iK
E4 contracted_codazzi_gaussian (hG hx hdiff) (a) :
    codazziLHS g ginv x a = -∑ b, projDown (g x) (n x) a b * ∑ c, n x c * ricci Γ x c b
E5 momentum_constraint (hG hx hdiff) (κ Λ : ℝ) (T : M) (hT : Tᵀ = T)
    (hE : ∀ b d, einstein Γ g ginv x b d + Λ * g x b d = κ * T b d) (a) :
    codazziLHS g ginv x a = κ * normalFlux (g x) (n x) T a                 -- D_bK^b_a - D_aK = κ J_a
E6 codazzi_perfect_fluid_tilt (hG hx hdiff) (hκ : κ ≠ 0) (Λ) (hw : 0 < w) (p γ β)
    (hβ : n x ⬝ᵥ (g x *ᵥ β) = 0) (hu : normalized at x) (hpos)
    (hE : Einstein at x with T := perfectFluid (g x) w p (γ • (n x + β))) :
    codazziLHS g ginv x = (κ * (w * γ ^ 2)) • (g x *ᵥ β) ∧
    betaVector (ginv x) w (κ⁻¹ • codazziLHS g ginv x) = g x *ᵥ β ∧
    betaOfRatio (fluxNorm (ginv x) (κ⁻¹ • codazziLHS g ginv x) / w) = Real.sqrt (β ⬝ᵥ (g x *ᵥ β))
E7 codazzi_homogeneous_reduction (hG hx)
    (hK : ∀ r, r ≠ 0 → ∀ p q, pd (fun y => extrinsicMixed g ginv y p q) x r = 0)
    (hH : ∀ r, r ≠ 0 → pd (meanCurvature g ginv) x r = 0) (i) (hi : i ≠ 0) :
    codazziLHS g ginv x i = ∑ b, ∑ d, Γ x b b d * extrinsicMixed g ginv x d i
                          - ∑ b, ∑ d, Γ x d b i * extrinsicMixed g ginv x b d   -- chart analogue of einsum
E8 minkowski_codazzi_witness (κ) (x) : non-vacuity: GaussianChart gMink gMink Set.univ ∧ hdiff ∧
    Einstein hypothesis of E5 with T = 0, Λ = 0 holds at x.
```

Scope notes (not strengthening): E-targets are proved only in a Gaussian normal chart (the
chart named by the source); κ, Λ are arbitrary reals (κ = 8πG/c⁴ > 0 not needed except κ ≠ 0 in
E6); no orthonormal-frame structure-constant identity, no coordinate invariance, no existence of
Gaussian charts, no multi-fluid converse (refuted in D3).
