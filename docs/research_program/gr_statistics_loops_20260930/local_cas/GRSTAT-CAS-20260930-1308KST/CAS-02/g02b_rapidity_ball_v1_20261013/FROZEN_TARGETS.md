# G02-B frozen targets

Provenance of this file: the interrupted earlier author attempt (API credit exhaustion) left only
`SOURCE_RECOVERY.md`, `lean/` (empty), `raw/imports/` (empty) and `raw/probes/` (empty) in T. No
`FROZEN_TARGETS.md` and no raw compile receipt existed. This file was therefore written fresh by the
continuing author (in-session subagent fallback), BEFORE any proof compile. `SOURCE_RECOVERY.md` from the
interrupted attempt was re-verified (all quoted sha256 values and file:line citations re-checked against
the working tree at HEAD `b976a27c`) and is kept unchanged.

Module: `T/lean/G02BRapidityBall.lean`, namespace `G02B`, importing unchanged
`Cas02` (C01-C03, sha256 `283f6437...b520`) and `InverseBound` (C04, namespace `CAS02C04`,
sha256 `bfdf0a77...085c6b`). `open scoped Matrix.Norms.Frobenius` exactly as in C04, so `‖·‖` on
`CAS02C04.Mat4` is the Frobenius norm. All vector norms are positive Euclidean observer component
norms (`InnerProductSpace ℝ E`, `EuclideanSpace ℝ (Fin n)`); no Lorentz/indefinite form appears in any
inequality (card pitfall 1).

Card quantifiers preserved: `d`, `h` universal over a general real inner-product space `E` (Gram
section) or over `Vec3`; `R : ℝ` is NOT assumed nonnegative anywhere — `0 ≤ R` is derived from
`‖d‖ ≤ sinh R`; `R = 0` and `d = 0` are never excluded (acceptance 1). The ball radius used by the
projection is exactly `sinh R`. `[Nontrivial E]` is required only for attainment/existence statements
(a maximum over an empty set of nonzero vectors does not exist); `Vec3` is nontrivial.

Definitions introduced (not postulated formulas; each is either the source definition or a named
constant whose value is then proved):

```lean
noncomputable def lamMax (d : E) : ℝ := 1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2)
noncomputable def emb : (ℝ × CAS02C04.Vec3) →L[ℝ] CAS02C04.Vec4   -- (t, x) ↦ (t, x0, x1, x2), Euclidean target
noncomputable def ballProj (r : ℝ) (x : E) : E := if ‖x‖ ≤ r then x else (r / ‖x‖) • x
noncomputable def fstJac (d : E) : E →L[ℝ] ℝ := (ContinuousLinearMap.fst ℝ ℝ E).comp (Cas02.chartJac d)
noncomputable def lipConst (R : ℝ) : ℝ := Real.sqrt (1 + Real.tanh R ^ 2)
```

## T1 — actual Du Gram: maximum eigenvalue and operator norm (card lean_step 1), d = 0 included

```lean
theorem gram_quad_eq (d h : E) :
    Cas02.chartGram d h h = ‖h‖ ^ 2 + (inner ℝ d h) ^ 2 / (1 + ‖d‖ ^ 2)
theorem gram_quad_le (d h : E) : Cas02.chartGram d h h ≤ lamMax d * ‖h‖ ^ 2
theorem gram_eig_le (d h : E) (eig : ℝ) (hh : h ≠ 0)
    (he : Cas02.gramVec d h = eig • h) : eig ≤ lamMax d
theorem gram_lamMax_eigen [Nontrivial E] (d : E) :
    ∃ h : E, h ≠ 0 ∧ Cas02.gramVec d h = lamMax d • h
theorem gram_max_eigenvalue [Nontrivial E] (d : E) :
    IsGreatest {eig : ℝ | ∃ h : E, h ≠ 0 ∧ Cas02.gramVec d h = eig • h} (lamMax d)
theorem gram_rayleigh_max [Nontrivial E] (d : E) :
    IsGreatest {q : ℝ | ∃ h : E, h ≠ 0 ∧ q = Cas02.chartGram d h h / ‖h‖ ^ 2} (lamMax d)
theorem lamMax_zero : lamMax (0 : E) = 1
-- Euclidean-target derivative of the C04 map `future` (= emb ∘ chart), and its operator norm
theorem future_eq_emb_chart (d : CAS02C04.Vec3) : CAS02C04.future d = emb (Cas02.chart d)
theorem emb_norm_sq (p : ℝ × CAS02C04.Vec3) : ‖emb p‖ ^ 2 = p.1 ^ 2 + ‖p.2‖ ^ 2
theorem future_hasFDerivAt (d : CAS02C04.Vec3) :
    HasFDerivAt CAS02C04.future (emb.comp (Cas02.chartJac d)) d
theorem futureJac_norm_sq (d h : CAS02C04.Vec3) :
    ‖(emb.comp (Cas02.chartJac d)) h‖ ^ 2 = Cas02.chartGram d h h
theorem futureJac_opNorm (d : CAS02C04.Vec3) :
    ‖emb.comp (Cas02.chartJac d)‖ = Real.sqrt (lamMax d)
```

## T2 — rapidity bound and monotonicity (card lean_step 2)

```lean
theorem lamMax_le_rapidity (d : E) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    0 ≤ R ∧ lamMax d ≤ 1 + Real.tanh R ^ 2
theorem lamMax_at_rapidity (d : E) (χ : ℝ) (hd : ‖d‖ = Real.sinh χ) :
    lamMax d = 1 + Real.tanh χ ^ 2                       -- sharpness on the rapidity sphere
theorem lamMax_mono {d₁ d₂ : E} (h : ‖d₁‖ ≤ ‖d₂‖) : lamMax d₁ ≤ lamMax d₂
theorem rapidity_cap_monotone :
    MonotoneOn (fun R : ℝ => 1 + Real.tanh R ^ 2) (Set.Ici 0)
theorem rapidity_mem_ball (d : E) (χ R : ℝ) (hd : ‖d‖ = Real.sinh χ) (hχR : χ ≤ R) :
    ‖d‖ ≤ Real.sinh R
theorem rapidity_R_zero (d : E) (hd : ‖d‖ ≤ Real.sinh 0) :
    d = 0 ∧ lamMax d = 1 ∧ 1 + Real.tanh 0 ^ 2 = 1
theorem futureJac_opNorm_le_rapidity (d : CAS02C04.Vec3) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    ‖emb.comp (Cas02.chartJac d)‖ ≤ lipConst R
```

## T3 — closed Euclidean ball projection (card lean_step 3); hr : 0 ≤ r is the nonempty-ball condition

```lean
theorem ballProj_norm_le {r : ℝ} (hr : 0 ≤ r) (x : E) : ‖ballProj r x‖ ≤ r
theorem ballProj_eq_self_iff {r : ℝ} (hr : 0 ≤ r) (x : E) : ballProj r x = x ↔ ‖x‖ ≤ r
theorem ballProj_variational {r : ℝ} (hr : 0 ≤ r) (x z : E) (hz : ‖z‖ ≤ r) :
    inner ℝ (x - ballProj r x) (z - ballProj r x) ≤ 0
theorem ballProj_nearest {r : ℝ} (hr : 0 ≤ r) (x z : E) (hz : ‖z‖ ≤ r) :
    ‖x - ballProj r x‖ ≤ ‖x - z‖
theorem ballProj_nonexpansive {r : ℝ} (hr : 0 ≤ r) (x y : E) :
    ‖ballProj r x - ballProj r y‖ ≤ ‖x - y‖           -- projection constant 1
theorem ballProj_error {r : ℝ} (hr : 0 ≤ r) (ζ ζhat : E) (hζ : ‖ζ‖ ≤ r) (η : ℝ)
    (h : ‖ζhat - ζ‖ ≤ η) : ‖ballProj r ζhat - ζ‖ ≤ η
theorem ballProj_zero_radius (x : E) : ballProj 0 x = 0
theorem ballProj_moves {r : ℝ} (hr : 0 ≤ r) (x : E) (hx : r < ‖x‖) : ballProj r x ≠ x   -- negative control
```

## T4 — mean-value Lipschitz bounds on the convex ball (card lean_step 4, first half)

```lean
theorem fstJac_norm_le (d : E) : ‖fstJac d‖ ≤ ‖d‖ / Real.sqrt (1 + ‖d‖ ^ 2)
theorem rapidity_ratio_le (d : E) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    ‖d‖ / Real.sqrt (1 + ‖d‖ ^ 2) ≤ Real.tanh R
theorem chart_fst_lipschitz_on_ball (R : ℝ) (a b : E)
    (ha : ‖a‖ ≤ Real.sinh R) (hb : ‖b‖ ≤ Real.sinh R) :
    |Real.sqrt (1 + ‖a‖ ^ 2) - Real.sqrt (1 + ‖b‖ ^ 2)| ≤ Real.tanh R * ‖a - b‖
theorem future_lipschitz_on_ball (R : ℝ) (a b : CAS02C04.Vec3)
    (ha : ‖a‖ ≤ Real.sinh R) (hb : ‖b‖ ≤ Real.sinh R) :
    ‖CAS02C04.future a - CAS02C04.future b‖ ≤ lipConst R * ‖a - b‖   -- regularity constant
theorem clipped_future_error (R ηd : ℝ) (ζ ζhat : CAS02C04.Vec3)
    (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd) :
    ‖CAS02C04.future (ballProj (Real.sinh R) ζhat) - CAS02C04.future ζ‖ ≤ lipConst R * ηd   -- source eq (22)
theorem clipped_monopole_check (R ηd η0 ζ0hat : ℝ) (ζ ζhat : E)
    (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd)
    (h0 : |ζ0hat - Real.sqrt (1 + ‖ζ‖ ^ 2)| ≤ η0) :
    |ζ0hat - Real.sqrt (1 + ‖ballProj (Real.sinh R) ζhat‖ ^ 2)| ≤ η0 + Real.tanh R * ηd   -- source eq (23)
```

## T5 — connection to the C04 positive-anchor finite inverse bound (card lean_step 4, second half)

```lean
theorem G02B_offshell_inverse_bound (S Sstar : CAS02C04.Mat4) (ζ ζhat : CAS02C04.Vec3) (R ηd : ℝ)
    (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd) :
    ‖CAS02C04.inverse Sstar (CAS02C04.future (ballProj (Real.sinh R) ζhat)) -
        CAS02C04.inverse S (CAS02C04.future ζ)‖ ≤
      (1 + 2 * CAS02C04.rapidityCap R ^ 2) * ‖Sstar - S‖ +
      4 * CAS02C04.rapidityCap R * min (CAS02C04.spectral S) (CAS02C04.spectral Sstar) *
        (lipConst R * ηd)
theorem G02B_offshell_inverse_bound_explicit (S Sstar : CAS02C04.Mat4) (ζ ζhat : CAS02C04.Vec3)
    (R ηd εH : ℝ) (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd) (hH : ‖Sstar - S‖ ≤ εH) :
    ‖CAS02C04.inverse Sstar (CAS02C04.future (ballProj (Real.sinh R) ζhat)) -
        CAS02C04.inverse S (CAS02C04.future ζ)‖ ≤
      (1 + 2 * CAS02C04.rapidityCap R ^ 2) * εH +
      4 * CAS02C04.rapidityCap R * CAS02C04.spectral Sstar * (lipConst R * ηd)
```
Explicit constants carried: `M = rapidityCap R = √cosh(2R)` (C04), regularity constant
`lipConst R = √(1+tanh²R)` (proved here from the actual derivative), projection constant `1`
(nonexpansive), amplitude factor `min(‖S‖op, ‖S*‖op)` (C04 `spectral`). `S*` is arbitrary (supplied slope
representative); `ζ` is the true dipole with rapidity ≤ R; `ζhat` the supplied dipole. No statement asserts
that `ζhat` (or the supplied sky) is admissible (card pitfall 2, contract STAB-OFFSHELL).

## Boundary / non-vacuity / negative controls

```lean
theorem G02B_R_zero_constants (ζhat : E) :
    ballProj (Real.sinh 0) ζhat = 0 ∧ lipConst 0 = 1 ∧ CAS02C04.rapidityCap 0 = 1
theorem G02B_nonvacuous_offshell :
    ∃ ζ ζhat : CAS02C04.Vec3, ∃ R ηd : ℝ, ‖ζ‖ ≤ Real.sinh R ∧ ‖ζhat - ζ‖ ≤ ηd ∧
      R = 0 ∧ ζ = 0 ∧ ballProj (Real.sinh R) ζhat ≠ ζhat     -- R=0, d=0, genuinely off-ball input
theorem scalar_bound_needs_ball :
    ¬ ∀ a b : CAS02C04.Vec3,
      |Real.sqrt (1 + ‖a‖ ^ 2) - Real.sqrt (1 + ‖b‖ ^ 2)| ≤ Real.tanh 0 * ‖a - b‖   -- ball hypothesis is necessary
```

## Explicitly not targeted
- Physical admissibility / exact-image membership of the supplied sky or of the clipped output.
- Sharpness of the C04 constant; statistical calibration; any scientific admission (stays HOLD).
- Wolfram/xAct, SymPy and Sage/Singular axes of the card (`tool_tasks`): not executed in this author run.
