# P03-A frozen targets (written before the first proof compile)

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/P03-A.json` (sha256 of extracted card
`7c943fce68fff0ebcfaf28b45ecb42239b9a66b5dc934a5d710793a0cf400679`).
Source obligation: `CAS_CONTRACT.json` CAS-03 (sha256 `904d95fe…3c389fad`):
identity `theta=c tr(h D); sigma=c sym(hDh)-theta*h/3; omega=c antisym(hDh); A=c^2 u.D`,
assumptions `D_ab=nabla_a u_b; D*u=0; u.u=-1`, signature `-+++`, `u=U/c`.

Namespace: `PORTCAS03VelocityJetDecomposition`, module `VelocityJetDecomposition`.
Imports (unchanged, reviewed): `VelocityJetRest` (P03 rest bridge) and `PortCas01`.

## Fixed index convention (from source, see SOURCE_RECOVERY.md)

* `u : Fin 4 → ℝ` contravariant `u^a`, dimensionless; `g` covariant `g_ab`; `ginv` = `g^ab`.
* `D a b = D_ab = ∇_a u_b` (derivative index first, both covariant), as in CAS-03 and
  `relativistic_kinematics.py:338`.
* `D *ᵥ u = 0` means `D_ab u^b = 0`; `u ᵥ* D` is `u^a D_ab` (contraction on the derivative index).
* Projectors: `projDown = δ_a^c + u_a u^c`, `projUp = δ^a_c + u^a u_c`,
  `hDown = g + u_a u_b`, `hUp = ginv + u^a u^b`, `spatialJet g u D = projDown * D * projDownᵀ`
  (exactly `projector@d@projector.T` in the implementation).
* `expansion c ginv g u D := c * contract ginv (spatialJet g u D)` (implementation form
  `c*trace(METRIC@spatial)`); the card form `c tr(hD)` is a theorem (T3/T5).
* `shear := c • symPart S - (θ/3) • hDown`, `vorticity := c • skewPart S`,
  `acceleration c u D := c^2 • (u ᵥ* D)`.
* Pointwise hypotheses: `hg : gᵀ = g`, `hinv : g * ginv = 1`, `hu : u ⬝ᵥ (g *ᵥ u) = -1`.
  These are *weaker* than signature `(-,+,+,+)` (any symmetric nondegenerate metric);
  signature `-+++` is used concretely in T7 through PORT-CAS-01 `eta`.

## Field-level definitions (T1)

* `pd f x a := fderiv ℝ f x (Pi.single a 1)` (actual Fréchet partial derivative).
* `lowerField g u y b := ∑ c, g y b c * u y c`.
* `nablaUp Γ u x a c := pd (fun y => u y c) x a + ∑ d, Γ x c a d * u x d`  (Γ x c a d = Γ^c_{ad}).
* `velJet Γ g u x a b := pd (fun y => lowerField g u y b) x a - ∑ c, Γ x c a b * lowerField g u x c`
  (`∇_a u_b`).
* `MetricCompatibleAt Γ g x := ∀ a b c, pd (fun y => g y b c) x a = ∑ d, (Γ x d a b * g x d c + Γ x d a c * g x b d)`
  (`∇g = 0`; torsion not restricted).
* `FieldDiffAt g u x` := all component functions of `g` and `u` differentiable at `x`.

## Frozen theorem signatures

T1 (D·u = 0 derived from the differentiated normalization, not assumed):
```
theorem velJet_eq_lower (hd : FieldDiffAt g u x) (hc : MetricCompatibleAt Γ g x) (a b : Fin 4) :
    velJet Γ g u x a b = ∑ c, g x b c * nablaUp Γ u x a c
theorem velJet_mulVec_u (hd : FieldDiffAt g u x) (hc : MetricCompatibleAt Γ g x) (hsym : (g x)ᵀ = g x)
    (hnorm : ∀ᶠ y in 𝓝 x, u y ⬝ᵥ (g y *ᵥ u y) = -1) :
    velJetMatrix Γ g u x *ᵥ u x = 0
```
T2 (projector, trace 3):
```
theorem projUp_idem (hu) : projUp g u * projUp g u = projUp g u
theorem projDown_idem (hu) : projDown g u * projDown g u = projDown g u
theorem trace_projUp (hu) : trace (projUp g u) = 3
theorem trace_projDown (hu) : trace (projDown g u) = 3
theorem projUp_mulVec_u (hu) : projUp g u *ᵥ u = 0
theorem u_vecMul_projDown (hu) : u ᵥ* projDown g u = 0
theorem hDown_eq_g_mul_projUp : hDown g u = g * projUp g u
theorem hDown_symm (hg) : (hDown g u)ᵀ = hDown g u
theorem hDown_mulVec_u (hu) : hDown g u *ᵥ u = 0
theorem hDown_proj (hg hinv hu) : hDown g u * ginv * hDown g u = hDown g u
theorem trace_ginv_hDown (hinv hu) : trace (ginv * hDown g u) = 3
theorem ginv_hDown_ginv (hg hinv) : ginv * hDown g u * ginv = hUp ginv u
theorem projUp_ginv_projDown (hg hinv hu) : projUp g u * ginv * projDown g u = hUp ginv u
```
T3 (trace forms):
```
theorem contract_ginv_spatialJet (hg hinv hu) (D) : contract ginv (spatialJet g u D) = contract (hUp ginv u) D
theorem contract_hUp_of_rest (D) (hD : D *ᵥ u = 0) : contract (hUp ginv u) D = contract ginv D
```
T4 (trace/STF/skew decomposition of hDh, for every D; c arbitrary real):
```
theorem decomposition (c D) : c • spatialJet g u D = shear c ginv g u D + (expansion c ginv g u D / 3) • hDown g u + vorticity c g u D
theorem shear_symm (hg) : (shear c ginv g u D)ᵀ = shear c ginv g u D
theorem vorticity_skew : (vorticity c g u D)ᵀ = -vorticity c g u D
theorem shear_traceless (hg hinv hu) : contract ginv (shear c ginv g u D) = 0
theorem vorticity_traceless (hg hinv) : contract ginv (vorticity c g u D) = 0
theorem spatialJet_mulVec_u (hu) / u_vecMul_spatialJet (hu)
theorem shear_mulVec_u (hu) / u_vecMul_shear (hg hu) / vorticity_mulVec_u (hu) / u_vecMul_vorticity (hu)
theorem shear_vorticity_orthogonal (hg hinv) : metricInner ginv σ ω = 0
theorem shear_h_orthogonal (hg hinv hu) : metricInner ginv σ (hDown g u) = 0
theorem vorticity_h_orthogonal (hg hinv) : metricInner ginv ω (hDown g u) = 0
```
T5 (composition with c, Q = c D, acceleration, reconstruction):
```
theorem acceleration_eq_rest : acceleration c u D = PORTCAS03VelocityJetRest.physicalAcceleration u D c
theorem acceleration_orthogonal (hD : D *ᵥ u = 0) : u ⬝ᵥ acceleration c u D = 0
theorem expansion_eq_trace_hD (hg hinv hu) : expansion c ginv g u D = c * contract (hUp ginv u) D
theorem expansion_eq_div_of_rest (hg hinv hu hD) : expansion c ginv g u D = c * contract ginv D
theorem spatialJet_of_rest (hD) : spatialJet g u D = D + vecMulVec (g *ᵥ u) (u ᵥ* D)
theorem reconstruction (hD) : c ^ 2 • D = c • (σ + (θ/3) • hDown g u + ω) - vecMulVec (g *ᵥ u) (acceleration c u D)
theorem kinematics_in_Q (hg hinv hu) : θ = contract ginv (spatialJet g u (c • D)) ∧ θ = contract (hUp ginv u) (c • D) ∧
    σ = symPart (spatialJet g u (c • D)) - (θ/3) • hDown g u ∧ ω = skewPart (spatialJet g u (c • D)) ∧
    acceleration c u D = (c • u) ᵥ* (c • D)
theorem D_eq_inv_smul_Q (hc : 0 < c) : D = c⁻¹ • (c • D)
theorem pointwise_kinematics (hg hinv hu) (hc : 0 < c) (D) (hD : D *ᵥ u = 0) : <conjunction of T3–T5>
theorem velJetMatrix_smul (hd) (c) : velJetMatrix Γ g (fun y => c • u y) x = c • velJetMatrix Γ g u x
```
T6 (field master theorem, actual ∇u, explicit `0 < c`):
```
theorem velocity_jet_kinematics (hd hcomp hsym) (hinv : g x * ginv = 1)
    (hnorm : ∀ᶠ y in 𝓝 x, u y ⬝ᵥ (g y *ᵥ u y) = -1) (hc : 0 < c) : D·u = 0 ∧ Q = c • D ∧ D = c⁻¹ • Q ∧
    θ = c tr(hD) ∧ decomposition ∧ σ symmetric ∧ σ traceless ∧ σ u = 0 ∧ ω skew ∧ ω u = 0 ∧ u·A = 0 ∧
    A = (c • u) ᵥ* Q ∧ reconstruction      (D := velJetMatrix Γ g u x, Q := velJetMatrix Γ g (c•u) x)
```
T7 (instances, PORT-CAS-01 reuse, non-vacuity, negative controls):
```
theorem boost_admissible (x y z) (hs : PortCas01.s x y z < 1) : fourVelocity ⬝ᵥ (eta *ᵥ fourVelocity) = -1
theorem boost_kinematics (hs) (hc : 0 < c) (D) (hD : D *ᵥ fourVelocity = 0) : trace 3 ∧ trace 3 ∧ σ traceless ∧ u·A = 0 ∧ reconstruction
theorem beta_zero_hDown : hDown eta (fourVelocity 0 0 0) = diagonal ![0,1,1,1]
theorem uEx_rest (x : Pt) : velJetMatrix Γ0 gMink uEx x *ᵥ uEx x = 0       -- u = (cosh φ, sinh φ, 0, 0), φ = 2y⁰+3y¹+5y²
theorem uEx_jet_zero : velJetMatrix Γ0 gMink uEx 0 = Dex                   -- concrete Jacobian
theorem uEx_kinematics_zero : θ = 6 ∧ σ = … ∧ ω = … ∧ A = ![0,8,0,0]      -- c = 2
theorem same_velocity_different_jet : uRest 0 = uEx 0 ∧ both normalized ∧ θ(uRest) = 0 ∧ θ(uEx) = 6   (negative control: pitfall 1)
theorem pointwise_normalization_insufficient : g(u,u)(0) = -1 ∧ FieldDiffAt ∧ MetricCompatibleAt ∧ (D *ᵥ u) 0 = -1  (negative control: T1 hypothesis is necessary)
```

## Explicit scope limits

* T1 is a chart-level statement with an arbitrary (possibly torsionful) metric-compatible
  connection given by coefficients `Γ`; it is not a smooth-manifold/`Mathlib` connection API theorem.
* Units are not typed in Lean; the `D` vs `Q` relation is the theorem `Q = c • D`.
* No claim that finite velocity determines `D` (T7 negative control proves the opposite).

## Amendment log (appended after compiles; frozen statements above not weakened)

* compile_03/04 (exit 1): tactic/elaboration fixes only (noncomputable markers on `symPart`,
  `skewPart`, `shear`, `vorticity`; disambiguated `Matrix.*_apply`; `HasFDerivAt.fun_sum`). No
  frozen statement changed.
* After compile_05: `boost_kinematics` gained the extra conjunct `D = c⁻¹ • (c • D)` (uses the
  explicit `0 < c`); this strengthens the conclusion, hypotheses unchanged.
* Before compile_08: added cross-check `acceleration_eq_two_sym (hD : D *ᵥ u = 0) :
  acceleration c u D = (2 * c ^ 2) • (symPart D *ᵥ u)` (COMMON_SPEC.md:12). Additive.
* Auxiliary lemmas not listed above (helpers, all audited): `ul_dot_u`, `ginv_mul_g`, `ginv_symm`,
  `g_mulVec_eq_vecMul`, `ginv_mulVec_ul`, `ul_vecMul_ginv`, `projDown_transpose`, `contract_eq_trace`,
  `trace_ginv_transpose`, `u_vecMul_hDown`, `metricInner_sym_skew`, `metricInner_skew_sym`,
  `spatialJet_smul`, `contract_smul_right`, `hasFDerivAt_sum_mul`, `pd_sum_mul`,
  `lowerField_differentiableAt`, `eta_symm`, `eta_mul_eta`, `mink_compatible`, `hasFDerivAt_phiEx`,
  `uEx_comp0..3`, `uEx_diff`, `uEx_norm`, `uEx_zero`, `pd_uEx0..3`, `spatialJet_Dex`, `hDown_e0`,
  `uRest_jet_zero`.
