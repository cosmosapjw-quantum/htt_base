# G05-B frozen targets (frozen before any proof compile of this package's modules)

Package task: G05-B (GR-CAS-05) "isolated eigenframe IFT and cubic germ realization".
Author lane: single Lean coding author (claude-opus-5-5). Status of this file: FROZEN.
Any later change to a statement below is recorded in `AMENDMENTS.md` with the reason; the final Lean
files must contain these statements verbatim (up to `:= by <proof>`).
Source recovery and modelling choices: `SOURCE_RECOVERY.md`.

Imported UNCHANGED (compiled into `raw/imports`): `CAS05C03.lean` (namespace `CAS05C03`),
`G05AConformalDEC.lean`, `G05BCubicDEC.lean` (namespaces `G05AConformalDEC`, `G05BCubicDEC`),
`Proof.lean` (CAS-04, namespace `GRSTATCAS04`, dependency of G04-A), `G04AEigenline.lean` (namespace `G04A`).
Notation from G05-A: `I = Fin 4`, `sum4`, `eta`, `bil`, `pd` (actual Fréchet partial), `dg`, `ginv`
(actual matrix inverse), `Gam`, `dGam`, `Ric`, `Rsc`, `Ein`, `stress` (`κT=G+Λg`), `gConf`, `gCub`,
`H`, `q`, `M`, `e0`, `diagT`, `Lorentzian`, `StrictDEC`.

## Module G05BJet (namespace `G05BJet`; `open G05AConformalDEC G05BCubicDEC`)

```lean
/-- `thirdJet g x y m n d = ∂_m ∂_n ∂_d g_xy (0)` (actual iterated partials). -/
noncomputable def thirdJet (g : (I → ℝ) → I → I → ℝ) (x y m n d : I) : ℝ :=
  pd (fun z => pd (fun w => dg g d x y w) n z) m 0

-- J1: first jet of the ACTUAL Einstein tensor at a critical point with g(0)=η
theorem Ein_first_jet (g : (I → ℝ) → I → I → ℝ)
    (hg : ∀ a c, ContDiff ℝ 3 (fun y => g y a c))
    (h0 : g 0 = eta) (hcrit : ∀ c a e, dg g c a e 0 = 0) (μ a c : I) :
    pd (fun y => Ein g y a c) μ 0 = CAS05C03.dEinstein (thirdJet g) μ a c := by <proof>

-- J2: the actual third jet of the cubic member is the C03 tensor J (baseline 3-jet vanishes)
theorem thirdJet_gCub (b : ℝ) (k : I → I → ℝ) (x y m n d : I) :
    thirdJet (gCub b k) x y m n d = CAS05C03.J b k x y m n d := by <proof>

-- J3: j²H = 0 (the 2-jet of g^(0) is preserved)
theorem two_jet_preserved (b : ℝ) (k : I → I → ℝ) :
    gCub b k 0 = gConf b 0 0 ∧
    (∀ c a e, dg (gCub b k) c a e 0 = dg (gConf b 0) c a e 0) ∧
    (∀ d c a e, pd (fun y => dg (gCub b k) c a e y) d 0 =
      pd (fun y => dg (gConf b 0) c a e y) d 0) := by <proof>

-- J4: all 40 first derivatives of the ACTUAL Einstein tensor / stress of the cubic member
theorem dEin_cub (b : ℝ) (k : I → I → ℝ) (μ a c : I) :
    pd (fun y => Ein (gCub b k) y a c) μ 0 = CAS05C03.closedDG b k μ a c := by <proof>

theorem dStress_cub (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (μ a c : I) :
    pd (fun y => stress (gCub b k) Λ κ y a c) μ 0 = CAS05C03.closedDG b k μ a c / κ := by <proof>

-- J5: prescribed derivative stress (right-inverse coefficients q, M in the actual metric)
theorem dStress_cub_0i (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (μ i : I) (hi : i ≠ 0) :
    pd (fun y => stress (gCub b k) Λ κ y 0 i) μ 0 =
      (if μ = 0 then q b k i else M b k i μ) / κ := by <proof>
```

## Module G05BIFT (namespace `G05BIFT`; `open G05AConformalDEC G05BCubicDEC`)

```lean
def mv (Mx : I → I → ℝ) (v : I → ℝ) : I → ℝ := fun a => sum4 (fun c => Mx a c * v c)

def FutureUnitEigenG (gx Tx : I → I → ℝ) (u : I → ℝ) (ε : ℝ) : Prop :=
  mv Tx u = (-ε) • u ∧ bil gx u u = -1 ∧ 0 < u 0

def restProjG (gx : I → I → ℝ) (u v : I → ℝ) : I → ℝ := v + bil gx u v • u

/-- Spectral isolation (source: `L = hT|_{u⊥} + εI` invertible), injective form. -/
def RestGapG (gx Tx : I → I → ℝ) (u : I → ℝ) (ε : ℝ) : Prop :=
  ∀ w : I → ℝ, bil gx u w = 0 → restProjG gx u (mv Tx w) + ε • w = 0 → w = 0

def SelfAdjG (gx Tx : I → I → ℝ) : Prop :=
  ∀ v w : I → ℝ, bil gx v (mv Tx w) = bil gx (mv Tx v) w

/-- Gauge-fixed (normalized) eigen-system `(x,(v,m)) ↦ (T(x)v − m v, g_x(v,v)+1)`. -/
def borderedG (g Tm : (I → ℝ) → I → I → ℝ) (p : (I → ℝ) × ((I → ℝ) × ℝ)) : (I → ℝ) × ℝ :=
  (mv (Tm p.1) p.2.1 - p.2.2 • p.2.1, bil (g p.1) p.2.1 p.2.1 + 1)

-- F1: derivative of the gauge-fixed map in the (v,m) direction
theorem borderedG_fderiv_inr {g Tm : (I → ℝ) → I → I → ℝ} {x : I → ℝ} {y : (I → ℝ) × ℝ}
    (hsym : ∀ a c, g x a c = g x c a)
    (hd : DifferentiableAt ℝ (borderedG g Tm) (x, y)) (w : I → ℝ) (m : ℝ) :
    (fderiv ℝ (borderedG g Tm) (x, y) ∘L ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)) (w, m) =
      (mv (Tm x) w - y.2 • w - m • y.1, 2 * bil (g x) y.1 w) := by <proof>

-- F2: spectral isolation ⇒ the IFT derivative is injective (hence invertible)
theorem borderedG_inj {gx Tx : I → I → ℝ} {u : I → ℝ} {ε : ℝ} (hsa : SelfAdjG gx Tx)
    (hu : FutureUnitEigenG gx Tx u ε) (hgap : RestGapG gx Tx u ε) (w : I → ℝ) (m : ℝ)
    (h : ((mv Tx w - (-ε) • w - m • u, 2 * bil gx u w) : (I → ℝ) × ℝ) = 0) :
    w = 0 ∧ m = 0 := by <proof>

-- F3: curved IFT: C^n normalized future energy eigenfield, gap persistence, local isolation
theorem curved_smooth_eigenline (n : ℕ) (hn : 1 ≤ n) (g Tm : (I → ℝ) → I → I → ℝ)
    (x0 : I → ℝ) (hg : ∀ a c, ContDiffAt ℝ n (fun y => g y a c) x0)
    (hT : ∀ a c, ContDiffAt ℝ n (fun y => Tm y a c) x0)
    (hgsym : ∀ x a c, g x a c = g x c a) (hsa0 : SelfAdjG (g x0) (Tm x0))
    (u0 : I → ℝ) (ε0 : ℝ) (h0 : FutureUnitEigenG (g x0) (Tm x0) u0 ε0)
    (hgap0 : RestGapG (g x0) (Tm x0) u0 ε0) :
    ∃ (V : Set (I → ℝ)) (u : (I → ℝ) → I → ℝ) (ε : (I → ℝ) → ℝ),
      IsOpen V ∧ x0 ∈ V ∧ u x0 = u0 ∧ ε x0 = ε0 ∧
      (∀ x ∈ V, ContDiffAt ℝ n u x ∧ ContDiffAt ℝ n ε x) ∧
      (∀ x ∈ V, FutureUnitEigenG (g x) (Tm x) (u x) (ε x) ∧ RestGapG (g x) (Tm x) (u x) (ε x)) ∧
      (∀ᶠ p in 𝓝 (x0, (u0, -ε0)), borderedG g Tm p = 0 → p.2 = (u p.1, -ε p.1)) := by <proof>

-- F4: pointwise uniqueness of the future unit timelike eigenvector (Lorentzian, self-adjoint, gap)
theorem unique_future_eigen (gx Tx : I → I → ℝ) (hgs : ∀ a c, gx a c = gx c a)
    (hL : Lorentzian gx) (hsa : SelfAdjG gx Tx) (u v : I → ℝ) (ε μ : ℝ)
    (hu : FutureUnitEigenG gx Tx u ε) (hgap : RestGapG gx Tx u ε)
    (hv : FutureUnitEigenG gx Tx v μ) : v = u ∧ μ = ε := by <proof>
```

## Module G05BSymm (namespace `G05BSymm`; `open G05AConformalDEC G05BCubicDEC G05BIFT`)

```lean
-- S1: the ACTUAL Ricci tensor of a symmetric C^2 metric field is symmetric wherever det g ≠ 0
theorem Ric_symm (g : (I → ℝ) → I → I → ℝ) (hg : ∀ a c, ContDiff ℝ 2 (fun y => g y a c))
    (hsym : ∀ y a c, g y a c = g y c a) (x : I → ℝ) (hdet : (toMat g x).det ≠ 0) (a c : I) :
    Ric g x a c = Ric g x c a := by <proof>

-- S2: the mixed Einstein-defined stress is g(x)-self-adjoint there
theorem selfAdj_mixed (g : (I → ℝ) → I → I → ℝ) (hg : ∀ a c, ContDiff ℝ 2 (fun y => g y a c))
    (hsym : ∀ y a c, g y a c = g y c a) (x : I → ℝ) (hdet : (toMat g x).det ≠ 0) (Λ κ : ℝ) :
    SelfAdjG (g x) (fun a c => sum4 (fun e => ginv g x a e * stress g Λ κ x e c)) := by <proof>
```

## Module G05BGerm (namespace `G05BGerm`; opens all of the above)

```lean
noncomputable def Tmix (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (x : I → ℝ) (a c : I) : ℝ :=
  sum4 (fun e => ginv (gCub b k) x a e * stress (gCub b k) Λ κ x e c)

/-- Levi-Civita covariant derivative `(∇_X u)^a = X(u^a) + Γ^a_{ce} X^c u^e` of the actual metric. -/
noncomputable def covD (g : (I → ℝ) → I → I → ℝ) (u : (I → ℝ) → I → ℝ) (x X : I → ℝ) (a : I) : ℝ :=
  fderiv ℝ u x X a + sum4 (fun c => sum4 (fun e => Gam g x a c e * X c * u x e))

def stdFrame (μ : I) : I → ℝ := Pi.single μ 1

/-- `g(∇_{E_μ} u, E_i)` at `x`. -/
noncomputable def rate (g : (I → ℝ) → I → I → ℝ) (u : (I → ℝ) → I → ℝ) (x : I → ℝ)
    (E : I → I → ℝ) (μ i : I) : ℝ :=
  bil (g x) (covD g u x (E μ)) (E i)

-- G1 (EF3 + IFT in ONE construction): every k admissible; member-dependent radius r
theorem EF3_local_germ (b Λ κ : ℝ) (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ)
    (k : I → I → ℝ) (n : ℕ) (hn : 1 ≤ n) :
    ∃ (r : ℝ) (u : (I → ℝ) → I → ℝ) (ε : (I → ℝ) → ℝ), 0 < r ∧
      gCub b k 0 = gConf b 0 0 ∧
      (∀ c a e, dg (gCub b k) c a e 0 = dg (gConf b 0) c a e 0) ∧
      (∀ d c a e, pd (fun y => dg (gCub b k) c a e y) d 0 =
        pd (fun y => dg (gConf b 0) c a e y) d 0) ∧
      (∀ x : I → ℝ, ‖x‖ < r →
        Lorentzian (gCub b k x) ∧ StrictDEC (gCub b k x) (stress (gCub b k) Λ κ x) ∧
        FutureUnitEigenG (gCub b k x) (Tmix b k Λ κ x) (u x) (ε x) ∧
        RestGapG (gCub b k x) (Tmix b k Λ κ x) (u x) (ε x) ∧
        ContDiffAt ℝ n u x ∧ ContDiffAt ℝ n ε x) ∧
      u 0 = e0 ∧ ε 0 = (6*b - Λ)/κ ∧
      stress (gCub b k) Λ κ 0 = diagT ((6*b - Λ)/κ) (Λ/κ) ∧
      stdFrame 0 = u 0 ∧
      (∀ μ ν, bil (gCub b k 0) (stdFrame μ) (stdFrame ν) = eta μ ν) ∧
      (∀ μ i, i ≠ 0 → pd (fun y => stress (gCub b k) Λ κ y 0 i) μ 0 =
        (if μ = 0 then q b k i else M b k i μ) / κ) ∧
      (∀ μ i, i ≠ 0 → rate (gCub b k) u 0 stdFrame μ i = k μ i) ∧
      (∀ᶠ p in 𝓝 ((0 : I → ℝ), (e0, -((6*b - Λ)/κ))),
        borderedG (gCub b k) (Tmix b k Λ κ) p = 0 → p.2 = (u p.1, -ε p.1)) := by <proof>

-- G2 (G1 + global isolation: the future unit timelike eigenvector is unique at every point of the ball)
theorem EF3_local_germ_unique (b Λ κ : ℝ) (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ)
    (k : I → I → ℝ) (n : ℕ) (hn : 1 ≤ n) :
    ∃ (r : ℝ) (u : (I → ℝ) → I → ℝ) (ε : (I → ℝ) → ℝ), 0 < r ∧
      (∀ x : I → ℝ, ‖x‖ < r →
        Lorentzian (gCub b k x) ∧ StrictDEC (gCub b k x) (stress (gCub b k) Λ κ x) ∧
        FutureUnitEigenG (gCub b k x) (Tmix b k Λ κ x) (u x) (ε x) ∧
        RestGapG (gCub b k x) (Tmix b k Λ κ x) (u x) (ε x) ∧
        ContDiffAt ℝ n u x ∧ ContDiffAt ℝ n ε x ∧
        ∀ (v : I → ℝ) (μ : ℝ), FutureUnitEigenG (gCub b k x) (Tmix b k Λ κ x) v μ →
          v = u x ∧ μ = ε x) ∧
      u 0 = e0 ∧ ε 0 = (6*b - Λ)/κ ∧
      (∀ μ i, i ≠ 0 → rate (gCub b k) u 0 stdFrame μ i = k μ i) := by <proof>

-- N1 (negative control): without spectral isolation (b = 0, so ε0 + p0 = 0) the gap fails at 0
theorem gap_fails_without_isolation (k : I → I → ℝ) (Λ κ : ℝ) (hκ : 0 < κ) :
    ¬ RestGapG (gCub 0 k 0) (Tmix 0 k Λ κ 0) e0 ((6*0 - Λ)/κ) := by <proof>

-- N2 (EF6 component, non-vacuity): same 2-jet and same u(0), different realized rate
theorem EF6_rates_not_determined_by_2jet (b Λ κ : ℝ) (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ)
    (n : ℕ) (hn : 1 ≤ n) :
    ∃ (k k' : I → I → ℝ) (u u' : (I → ℝ) → I → ℝ) (ε ε' : (I → ℝ) → ℝ) (r r' : ℝ),
      0 < r ∧ 0 < r' ∧
      (∀ x : I → ℝ, ‖x‖ < r → FutureUnitEigenG (gCub b k x) (Tmix b k Λ κ x) (u x) (ε x)) ∧
      (∀ x : I → ℝ, ‖x‖ < r' → FutureUnitEigenG (gCub b k' x) (Tmix b k' Λ κ x) (u' x) (ε' x)) ∧
      u 0 = u' 0 ∧ gCub b k 0 = gCub b k' 0 ∧
      (∀ c a e, dg (gCub b k) c a e 0 = dg (gCub b k') c a e 0) ∧
      (∀ d c a e, pd (fun y => dg (gCub b k) c a e y) d 0 =
        pd (fun y => dg (gCub b k') c a e y) d 0) ∧
      rate (gCub b k) u 0 stdFrame 0 1 ≠ rate (gCub b k') u' 0 stdFrame 0 1 := by <proof>
```

## Target map (card step → target)

* step 1 (gauge-fixed map, derivative): `borderedG`, F1 `borderedG_fderiv_inr`.
* step 2 (IFT invertibility from spectral isolation; smooth local eigenfield): F2, F3; isolation: F3 local
  branch uniqueness, F4 + S1/S2 + G2 global uniqueness; N1 shows the isolation hypothesis is not vacuous.
* step 3 (cubic coefficients in the ACTUAL metric; j²H=0; prescribed derivative stress): J1–J5, J3.
* step 4 (energy-field derivative ↔ rates; EF6 local germ): G1 (one construction: formal jet J, actual
  metric `gCub`, actual eigenfield `u` from F3), G2, N2.
* Admissibility: every real `k` (no restriction); prescribed rates are arbitrary through `k`
  (equivalently arbitrary `q,M` via the accepted C03 right inverse). Radius `r` is existential per
  member `(b,k,Λ,κ,n)`; no uniform radius.

## Forbidden
sorry/admit/sorryAx/native_decide/new axioms/maxHeartbeats hacks hiding failures; assuming the
eigenfield, its smoothness, the rate identity, the derivative stress, or Ric symmetry. Accepted axioms:
propext, Classical.choice, Quot.sound.
