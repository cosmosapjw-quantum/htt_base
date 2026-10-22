# R195-A frozen targets (written before any proof compile)

Card: `HTT_ALL_OBLIGATIONS_20261011/tasks/R195-A.json` (parent PR-195, reuse PR-222 mechanics,
consumed exports PR-187 frame conventions + PR-222 multi-window law). Scope (verbatim, KO):
"B_W=v0+finite-k residual를 window·spectrum·gauge/frame 및 remainder와 함께 증명한다."
Source definitions and citations: `SOURCE_RECOVERY.md`.

Module: `lean/R195AWindowedBulk.lean`, namespace `R195A`. Toolchain Lean 4.31.0,
Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.

## Common objects (definitions, not hypotheses)

```lean
inductive Frame | n | u | obs              -- PR-187 tags; no default frame
inductive RemKind | window | selection | calibration

-- windowed bulk flow, Bochner window integral over a general window measure ν
-- (ν = Lebesgue for a continuous window, ν = finite sum of Diracs for a discrete tracer window)
def bulk (ν : Measure E) (W : E → ℝ) (v : Ω → E → V) (ω : Ω) : V := ∫ x, W x • v ω x ∂ν

-- window transfer function  Ŵ(k) = ∫ e^{-i⟨k,x⟩} W(x) dν(x)
def ft (ν : Measure E) (W : E → ℝ) (k : E) : ℂ := ∫ x, cexp (-((⟪k, x⟫_ℝ : ℂ) * I)) * (W x : ℂ) ∂ν

def wobs (ν) (W) (L : V →L[ℝ] ℝ) (v) (ω) : ℝ := L (bulk ν W v ω)   -- one window, one projection

structure Rem (fr : Frame) (κ : RemKind) (V : Type*) where val : V
structure ObsModel (fr : Frame) (V : Type*) where
  v0 : V; resid : V; win : Rem fr .window V; sel : Rem fr .selection V; cal : Rem fr .calibration V
def ObsModel.obs (M) : V := M.v0 + M.resid + M.win.val + M.sel.val + M.cal.val
```

Random-field hypotheses are explicit theorem arguments (never axioms): second moments /
measurability / integrability enter as `Integrable` of the joint integrand on `P.prod (ν.prod ν')`
(this is the exact Fubini hypothesis; T8 tries to derive it from finite second moments);
stationarity + power spectrum enter as the spectral representation
`E[a(x) b(y)] = ∫ e^{i⟨k,x-y⟩} p_ab(k) dμ(k)` with `p_ab ∈ L¹(μ)` (finite-variance spectral density;
μ general, e.g. Lebesgue/(2π)^3). Window integrability `W ∈ L¹(ν)`.

## Targets

T1 `bulk_decomposition` (exact Bochner decomposition, general normalization branch)
```lean
theorem bulk_decomposition [CompleteSpace V] {ν : Measure E} {W : E → ℝ} {v u : Ω → E → V}
    {v0 : V} {ω : Ω} (hW : Integrable W ν) (hu : Integrable (fun x => W x • u ω x) ν)
    (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x) :
    bulk ν W v ω = (∫ x, W x ∂ν) • v0 + bulk ν W u ω
```
T1n `bulk_decomposition_normalized`: same hypotheses plus `hnorm : ∫ x, W x ∂ν = 1`, conclusion
`bulk ν W v ω = v0 + bulk ν W u ω`.
T1g `ft_zero`: `ft ν W 0 = ((∫ x, W x ∂ν : ℝ) : ℂ)` (homogeneous-mode gain = Ŵ(0)).

T2 `cross_window_config` (full cross-window law in configuration space; no stationarity)
```lean
theorem cross_window_config {P : Measure Ω} [SFinite P] {ν ν' : Measure E} [SFinite ν] [SFinite ν']
    {W W' : E → ℝ} {a b : Ω → E → ℝ}
    (hjoint : Integrable (fun q : Ω × (E × E) => (W q.2.1 * a q.1 q.2.1) * (W' q.2.2 * b q.1 q.2.2))
      (P.prod (ν.prod ν'))) :
    ∫ ω, bulk ν W a ω * bulk ν' W' b ω ∂P
      = ∫ z, W z.1 * W' z.2 * (∫ ω, a ω z.1 * b ω z.2 ∂P) ∂(ν.prod ν')
```

T3 `cross_window_spectral` (covariance/cross-covariance from the power spectrum; E finite-dim inner product space)
```lean
theorem cross_window_spectral {P : Measure Ω} [SFinite P] {ν ν' μ : Measure E}
    [SFinite ν] [SFinite ν'] [SFinite μ] {W W' : E → ℝ} {a b : Ω → E → ℝ} {p : E → ℂ}
    (hW : Integrable W ν) (hW' : Integrable W' ν') (hp : Integrable p μ)
    (hjoint : <as T2>)
    (hK : ∀ x y, ((∫ ω, a ω x * b ω y ∂P : ℝ) : ℂ) = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * p k ∂μ) :
    ((∫ ω, bulk ν W a ω * bulk ν' W' b ω ∂P : ℝ) : ℂ)
      = ∫ k, conj (ft ν W k) * ft ν' W' k * p k ∂μ
```
T3m `residual_mean_zero`
```lean
theorem residual_mean_zero {P : Measure Ω} [SFinite P] {ν : Measure E} [SFinite ν] {W : E → ℝ}
    {a : Ω → E → ℝ} (hint : Integrable (fun q : Ω × E => W q.2 * a q.1 q.2) (P.prod ν))
    (hmean : ∀ x, ∫ ω, a ω x ∂P = 0) : ∫ ω, bulk ν W a ω ∂P = 0
```

T4 `multiwindow_forward_law` (PR-222 multi-window stochastic forward operator, generalized:
rows = windows m with projection L m; cross terms for every pair (m,n), m ≠ n included)
```lean
theorem multiwindow_forward_law {ι : Type*} [CompleteSpace V] {P : Measure Ω} [IsProbabilityMeasure P]
    {μ : Measure E} [SFinite μ] (ν : ι → Measure E) [∀ m, SFinite (ν m)] (W : ι → E → ℝ)
    (L : ι → V →L[ℝ] ℝ) (v u : Ω → E → V) (v0 : V) (pc : ι → ι → E → ℂ)
    (hW : ∀ m, Integrable (W m) (ν m)) (hnorm : ∀ m, ∫ x, W m x ∂(ν m) = 1)
    (hv : ∀ ω m, ∀ᵐ x ∂(ν m), v ω x = v0 + u ω x)
    (hu : ∀ ω m, Integrable (fun x => W m x • u ω x) (ν m))
    (hint1 : ∀ m, Integrable (fun q : Ω × E => W m q.2 * L m (u q.1 q.2)) (P.prod (ν m)))
    (hmean : ∀ m x, ∫ ω, L m (u ω x) ∂P = 0)
    (hjoint : ∀ m n, Integrable (fun q : Ω × (E × E) =>
        (W m q.2.1 * L m (u q.1 q.2.1)) * (W n q.2.2 * L n (u q.1 q.2.2))) (P.prod ((ν m).prod (ν n))))
    (hpc : ∀ m n, Integrable (pc m n) μ)
    (hK : ∀ m n x y, ((∫ ω, L m (u ω x) * L n (u ω y) ∂P : ℝ) : ℂ)
        = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * pc m n k ∂μ) :
    (∀ m ω, wobs (ν m) (W m) (L m) v ω = L m v0 + bulk (ν m) (W m) (fun ω x => L m (u ω x)) ω) ∧
    (∀ m, ∫ ω, wobs (ν m) (W m) (L m) v ω ∂P = L m v0) ∧
    (∀ m n, ((∫ ω, (wobs (ν m) (W m) (L m) v ω - L m v0) * (wobs (ν n) (W n) (L n) v ω - L n v0) ∂P : ℝ) : ℂ)
        = ∫ k, conj (ft (ν m) (W m) k) * ft (ν n) (W n) k * pc m n k ∂μ)
```

T5 typed additive remainders
```lean
theorem ObsModel.obs_sub_v0 [AddCommGroup V] (M : ObsModel fr V) :
    M.obs - M.v0 = M.resid + (M.win.val + M.sel.val + M.cal.val)
theorem ObsModel.remainder_bound [NormedAddCommGroup V] (M : ObsModel fr V) :
    ‖M.obs - M.v0 - M.resid‖ ≤ ‖M.win.val‖ + ‖M.sel.val‖ + ‖M.cal.val‖
theorem finite_window_remainder [CompleteSpace V] {ν} {W We : E → ℝ} {v u} {v0 : V} {ω}
    (hW : Integrable W ν) (hWe : Integrable We ν) (hu : Integrable (fun x => W x • u ω x) ν)
    (hue : Integrable (fun x => We x • u ω x) ν) (hv : ∀ᵐ x ∂ν, v ω x = v0 + u ω x) :
    bulk ν We v ω - bulk ν W v ω = (∫ x, We x - W x ∂ν) • v0 + bulk ν (fun x => We x - W x) u ω
theorem finite_window_remainder_normalized : <same + hn : ∫ W = 1, hne : ∫ We = 1> →
    bulk ν We v ω - bulk ν W v ω = bulk ν (fun x => We x - W x) u ω
def ObsModel.ofBulk (fr) (ν W We v v0 u ω) (s : Rem fr .selection V) (c : Rem fr .calibration V) : ObsModel fr V
  -- v0, resid := bulk ν W u ω, win := ⟨bulk ν We v ω - bulk ν W v ω⟩, sel := s, cal := c
theorem ObsModel.ofBulk_obs : <T1n hypotheses for W> →
    (ObsModel.ofBulk fr ν W We v v0 u ω s c).obs = bulk ν We v ω + s.val + c.val
```

T6 `spectral_excludes_k0` (finite-k carrier; constant mode carried by v0 only when μ has no atom at 0)
```lean
theorem spectral_excludes_k0 [NoAtoms μ] (F : E → ℂ) : ∫ k, F k ∂μ = ∫ k in ({0}ᶜ : Set E), F k ∂μ
```

T7 non-vacuity witnesses and negative controls (Ω = Fin 4 uniform, E = ℝ,
a(j,x) = cos(x + jπ/2) written as cos x, -sin x, -cos x, sin x; spectral measure δ₁ + δ₋₁, p = 1/4)
- `witness_mean_zero : ∀ x, ∫ ω, aw ω x ∂Pw = 0`
- `witness_cov : ∀ x y, ∫ ω, aw ω x * aw ω y ∂Pw = Real.cos (x - y) / 2`
- `witness_spectral : ∀ x y, ((∫ ω, aw ω x * aw ω y ∂Pw : ℝ) : ℂ) = ∫ k, cexp ((⟪k, x - y⟫_ℝ : ℂ) * I) * (1/4 : ℂ) ∂(dirac 1 + dirac (-1))` (hK satisfiable, μ ≠ 0, no atom at k = 0)
- `witness_residual_nonzero (v0 : ℝ) : bulk (dirac 0) (fun _ => 1) (fun ω x => v0 + aw ω x) 0 ≠ v0` (negative control: "B/c = homogeneous β" substitution fails)
- `witness_residual_variance : ∫ ω, (bulk (dirac 0) (fun _ => 1) aw ω) ^ 2 ∂Pw = 1 / 2`
- `witness_cross_window : ∫ ω, bulk (dirac 0) (fun _ => 1) aw ω * bulk (dirac 1) (fun _ => 1) aw ω ∂Pw = Real.cos 1 / 2 ∧ 0 < Real.cos 1 / 2` (negative control: zeroing the cross-window term is false)
- `witness_nonidentification : bulk (dirac 0) 1 (fun ω x => (0:ℝ) + aw ω x) 0 = bulk (dirac 0) 1 (fun ω x => (1:ℝ) + aw ω x) 1` (negative control: an observed bulk value cannot distinguish v0 = 0 from v0 = 1, so a bridge failure is not evidence of v0 = 0 / Ω_tilt = 0)

T8 (optional, attempted) `hjoint_of_second_moments`: derive the T2/T3 joint integrability from
joint a.e.-strong measurability, uniform finite second moments `∫ a(ω,x)^2 dP ≤ Ca`, `∫ b(ω,y)^2 dP ≤ Cb`
(for all x, y) and `W ∈ L¹(ν)`, `W' ∈ L¹(ν')`. If not closed, the explicit `hjoint` hypothesis stays.

## Explicitly not claimed
scientific admission; v0 → Ω_tilt / β mapping (R194-A/B); β = B/c substitution (refuted as a
substitution by T7); isotropic radial reduction cov = δ_ij (aHf)^2/(6π²)∫P e^{-k²R²} dk; the linear-theory
kernel P_v,ij = (aHf)² P(k) k_i k_j / k⁴ (it is a permitted instance of p, not derived); Bochner's theorem
(existence of the spectral density is a hypothesis); magnitudes/models of selection and calibration
remainders (only their typed additive placement); PR-222 GLS rank-3 numerics; real-data fitting.
