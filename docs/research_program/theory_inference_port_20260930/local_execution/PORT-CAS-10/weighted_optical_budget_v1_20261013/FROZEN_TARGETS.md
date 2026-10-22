# P10-A frozen Lean targets (frozen before any proof attempt)

Package task: P10-A (PORT-CAS-10, "stress-gap body and weighted optical budget").
Lean file: `lean/P10AWeightedBudget.lean`, namespace `P10A`, `import Mathlib`.
Toolchain: Lean 4.31.0, mathlib fabf563a7c95a166b8d7b6efca11c8b4dc9d911f
(Lake project `/home/cosmosapjw/lean_oracles/viii_oracle`).

Faithfulness anchors are listed in `SOURCE_RECOVERY.md` (file:line). Signatures
below are the frozen statements; proofs may change, statements may not, except
for purely syntactic elaboration fixes (recorded in AUTHOR_RETURN.json if any).

Shared variables:

```lean
open MeasureTheory Set intervalIntegral
open scoped Interval
variable {V E : Type*} [NormedAddCommGroup V] [NormedSpace ℝ V]
  [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
```

## Definitions (source-faithful)

```lean
noncomputable def Bstar (c dstar deltastar : ℝ) : ℝ := c * dstar / deltastar

-- GR-04 velocity-jet encoding, re-declared verbatim (cited, not re-claimed):
abbrev Arr := Fin 4 → Fin 3 → ℝ     -- q μ i = rest component i of ∇_{E_μ} U, E_0 = u
def theta (q : Arr) : ℝ := ∑ i : Fin 3, q i.succ i
noncomputable def sigma (q : Arr) (i j : Fin 3) : ℝ :=
  (q i.succ j + q j.succ i) / 2 - (if i = j then theta q / 3 else 0)
noncomputable def skew (q : Arr) (i j : Fin 3) : ℝ := (q i.succ j - q j.succ i) / 2
noncomputable def omega (q : Arr) : Fin 3 → ℝ | 0 => skew q 1 2 | 1 => skew q 2 0 | 2 => skew q 0 1
def accel (c : ℝ) (q : Arr) (i : Fin 3) : ℝ := c * q 0 i

-- Frobenius-orthonormal STF five-vector (implementation docstring: "STF coefficients
-- use a Frobenius-orthonormal five-vector basis")
noncomputable def stf (q : Arr) : Fin 5 → ℝ :=
  ![(sigma q 0 0 - sigma q 1 1) * (√2 / 2), sigma q 2 2 * (√6 / 2),
    sigma q 0 1 * √2, sigma q 0 2 * √2, sigma q 1 2 * √2]

-- coordinate order (theta, sigma1..5, omega1..3, A1..3)
noncomputable def channel (c : ℝ) (q : Arr) : Fin 12 → ℝ :=
  ![theta q, stf q 0, stf q 1, stf q 2, stf q 3, stf q 4,
    omega q 0, omega q 1, omega q 2, accel c q 0, accel c q 1, accel c q 2]

noncomputable def baseWeight (c : ℝ) : Fin 12 → ℝ :=
  ![1/3, 1, 1, 1, 1, 1, 2, 2, 2, (c^2)⁻¹, (c^2)⁻¹, (c^2)⁻¹]
noncomputable def qWeight (c B : ℝ) : Fin 12 → ℝ := fun i => baseWeight c i / B ^ 2
noncomputable def Qmat (c B : ℝ) : Matrix (Fin 12) (Fin 12) ℝ := Matrix.diagonal (qWeight c B)

structure StressGapPremise where
  c : ℝ
  dstar : ℝ
  deltastar : ℝ
  hc : 0 < c
  hd : 0 < dstar
  hδ : 0 < deltastar
  D : Arr            -- D_μ^i = h(∇_{E_μ}T)u in the rest eigen-triad of L
  gap : Fin 3 → ℝ    -- ℓ_i = ε + λ_i, eigenvalues of L = S + εI
  jet : Arr          -- same-state velocity jet ∇_{E_μ}U^i
  eigenbranch : ∀ μ i, gap i * jet μ i = -c * D μ i
  gap_lower : ∀ i, deltastar ≤ |gap i|
  deriv_bound : Real.sqrt (∑ μ : Fin 4, ∑ i : Fin 3, (D μ i) ^ 2) ≤ dstar

noncomputable def Kw (a b : ℝ) (w : ℝ → ℝ) (A : ℝ → V →L[ℝ] E) (k : ℝ → V) : E :=
  ∫ t in a..b, w t • A t (k t)
```

## W1 — B* positivity

```lean
theorem W1_Bstar_pos {c dstar deltastar : ℝ} (hc : 0 < c) (hd : 0 < dstar)
    (hδ : 0 < deltastar) : 0 < Bstar c dstar deltastar
theorem W1_python_fixture : Bstar 2 2 4 = 1
```

## W2 — Q diagonal, positivity, quadratic-form identity, velocity-jet body

```lean
theorem W2a_Q_entries_pos {c B : ℝ} (hc : 0 < c) (hB : 0 < B) : ∀ i, 0 < qWeight c B i
theorem W2b_stf_frobenius (q : Arr) :
    ∑ k : Fin 5, (stf q k) ^ 2 = ∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j) ^ 2
theorem W2c_channel_rate (c : ℝ) (q : Arr) (hc : c ≠ 0) :
    ∑ i : Fin 12, baseWeight c i * (channel c q i) ^ 2 = ∑ μ : Fin 4, ∑ i : Fin 3, (q μ i) ^ 2
theorem W2d_Q_quadratic_form (c B : ℝ) (q : Arr) (hc : c ≠ 0) :
    channel c q ⬝ᵥ (Qmat c B *ᵥ channel c q) = (∑ μ : Fin 4, ∑ i : Fin 3, (q μ i) ^ 2) / B ^ 2
theorem W2e_stress_gap_body (P : StressGapPremise) :
    channel P.c P.jet ⬝ᵥ (Qmat P.c (Bstar P.c P.dstar P.deltastar) *ᵥ channel P.c P.jet) ≤ 1
```

## W3 — product differentiation and interval integration by parts

```lean
theorem W3a_product_derivative {w w' : ℝ → ℝ} {m m' : ℝ → E} {t : ℝ}
    (hw : HasDerivAt w (w' t) t) (hm : HasDerivAt m (m' t) t) :
    HasDerivAt (fun x => w x • m x) (w' t • m t + w t • m' t) t
theorem W3b_ibp {a b : ℝ} {w w' : ℝ → ℝ} {m m' : ℝ → E}
    (hw : ∀ t ∈ [[a, b]], HasDerivAt w (w' t) t) (hm : ∀ t ∈ [[a, b]], HasDerivAt m (m' t) t)
    (hw' : IntervalIntegrable w' volume a b) (hm' : IntervalIntegrable m' volume a b) :
    ∫ t in a..b, w t • m' t = (w b • m b - w a • m a) - ∫ t in a..b, w' t • m t
theorem W3c_ibp_absolutelyContinuous {a b : ℝ} {w m : ℝ → ℝ}
    (hw : AbsolutelyContinuousOnInterval w a b) (hm : AbsolutelyContinuousOnInterval m a b) :
    ∫ t in a..b, w t * deriv m t = (w b * m b - w a * m a) - ∫ t in a..b, deriv w t * m t
```

W3b is proved from W3a and FTC (`integral_eq_sub_of_hasDerivAt`), not by
calling Mathlib's IBP. W3c (scalar, absolutely continuous; the source's
`m ∈ AC`) uses Mathlib's `AbsolutelyContinuousOnInterval.integral_mul_deriv_eq_deriv_mul`.

## W4 — K_w identity (contract sign convention: K_w = I_ws + I_w'm − (w_b m_b − w_a m_a))

Source balance (ADJUDICATED_AMENDMENTS TF-W1): `m' + A k = s` a.e.

```lean
theorem W4a_Kw_identity {a b : ℝ} {w w' : ℝ → ℝ} {m m' s : ℝ → E}
    {A : ℝ → V →L[ℝ] E} {k : ℝ → V}
    (hw : ∀ t ∈ [[a, b]], HasDerivAt w (w' t) t) (hm : ∀ t ∈ [[a, b]], HasDerivAt m (m' t) t)
    (hw' : IntervalIntegrable w' volume a b) (hm' : IntervalIntegrable m' volume a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → m' t + A t (k t) = s t) :
    Kw a b w A k = (∫ t in a..b, w t • s t) + (∫ t in a..b, w' t • m t) - (w b • m b - w a • m a)
theorem W4b_Kw_identity_AC {a b : ℝ} {w m s : ℝ → ℝ} {A : ℝ → V →L[ℝ] ℝ} {k : ℝ → V}
    (hw : AbsolutelyContinuousOnInterval w a b) (hm : AbsolutelyContinuousOnInterval m a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → deriv m t + A t (k t) = s t) :
    Kw a b w A k = (∫ t in a..b, w t * s t) + (∫ t in a..b, deriv w t * m t) - (w b * m b - w a * m a)
```

## W5 — remainder budget with the finite kinematic bound k (M_k)

True coefficient `A = Ahat + dA` (Ahat supplied, dA uncertain). `L` = uniform
Lipschitz constant of k about t0, `Mk` = finite bound on ‖k‖.
V-integral = ∫|w|‖Ahat‖|t−t0| (implementation `variation_integral`),
P-integral = ∫|w|‖dA‖ (implementation `coefficient_error_integral`).

```lean
theorem W5a_remainder_budget {a b t0 L Mk : ℝ} (hab : a ≤ b) {w : ℝ → ℝ}
    {Ahat dA : ℝ → V →L[ℝ] E} {k : ℝ → V}
    (hk_lip : ∀ᵐ t, t ∈ Ioc a b → ‖k t - k t0‖ ≤ L * |t - t0|)
    (hk_bd : ∀ᵐ t, t ∈ Ioc a b → ‖k t‖ ≤ Mk)
    (hA_int : IntervalIntegrable (fun t => w t • Ahat t) volume a b)
    (hAk_int : IntervalIntegrable (fun t => w t • Ahat t (k t)) volume a b)
    (hdAk_int : IntervalIntegrable (fun t => w t • dA t (k t)) volume a b)
    (hV_int : IntervalIntegrable (fun t => |w t| * ‖Ahat t‖ * |t - t0|) volume a b)
    (hP_int : IntervalIntegrable (fun t => |w t| * ‖dA t‖) volume a b) :
    ‖(∫ t in a..b, w t • Ahat t) (k t0) - Kw a b w (fun t => Ahat t + dA t) k‖
      ≤ L * (∫ t in a..b, |w t| * ‖Ahat t‖ * |t - t0|) + Mk * (∫ t in a..b, |w t| * ‖dA t‖)

theorem W5b_weighted_optical_budget {a b t0 L Mk εnum : ℝ} (hab : a ≤ b)
    {w w' : ℝ → ℝ} {m m' s : ℝ → E} {Ahat dA : ℝ → V →L[ℝ] E} {k : ℝ → V}
    (hw : ∀ t ∈ [[a, b]], HasDerivAt w (w' t) t) (hm : ∀ t ∈ [[a, b]], HasDerivAt m (m' t) t)
    (hw' : IntervalIntegrable w' volume a b) (hm' : IntervalIntegrable m' volume a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → m' t + (Ahat t + dA t) (k t) = s t)
    (hk_lip : ∀ᵐ t, t ∈ Ioc a b → ‖k t - k t0‖ ≤ L * |t - t0|)
    (hk_bd : ∀ᵐ t, t ∈ Ioc a b → ‖k t‖ ≤ Mk)
    (hA_int : IntervalIntegrable (fun t => w t • Ahat t) volume a b)
    (hAk_int : IntervalIntegrable (fun t => w t • Ahat t (k t)) volume a b)
    (hdAk_int : IntervalIntegrable (fun t => w t • dA t (k t)) volume a b)
    (hV_int : IntervalIntegrable (fun t => |w t| * ‖Ahat t‖ * |t - t0|) volume a b)
    (hP_int : IntervalIntegrable (fun t => |w t| * ‖dA t‖) volume a b)
    (Iws Iwpm Ea Eb : E)
    (hnum : ‖(Iws + Iwpm - (Eb - Ea)) -
        ((∫ t in a..b, w t • s t) + (∫ t in a..b, w' t • m t) - (w b • m b - w a • m a))‖ ≤ εnum) :
    ‖(∫ t in a..b, w t • Ahat t) (k t0) - (Iws + Iwpm - (Eb - Ea))‖
      ≤ L * (∫ t in a..b, |w t| * ‖Ahat t‖ * |t - t0|)
        + Mk * (∫ t in a..b, |w t| * ‖dA t‖) + εnum

theorem W5c_weighted_optical_budget_AC {a b t0 L Mk εnum : ℝ} (hab : a ≤ b)
    {w m s : ℝ → ℝ} {Ahat dA : ℝ → V →L[ℝ] ℝ} {k : ℝ → V}
    (hw : AbsolutelyContinuousOnInterval w a b) (hm : AbsolutelyContinuousOnInterval m a b)
    (hs : IntervalIntegrable s volume a b)
    (hbal : ∀ᵐ t, t ∈ Ι a b → deriv m t + (Ahat t + dA t) (k t) = s t)
    (hk_lip : ∀ᵐ t, t ∈ Ioc a b → ‖k t - k t0‖ ≤ L * |t - t0|)
    (hk_bd : ∀ᵐ t, t ∈ Ioc a b → ‖k t‖ ≤ Mk)
    (hA_int : IntervalIntegrable (fun t => w t • Ahat t) volume a b)
    (hAk_int : IntervalIntegrable (fun t => w t • Ahat t (k t)) volume a b)
    (hdAk_int : IntervalIntegrable (fun t => w t • dA t (k t)) volume a b)
    (hV_int : IntervalIntegrable (fun t => |w t| * ‖Ahat t‖ * |t - t0|) volume a b)
    (hP_int : IntervalIntegrable (fun t => |w t| * ‖dA t‖) volume a b)
    (Iws Iwpm Ea Eb : ℝ)
    (hnum : |(Iws + Iwpm - (Eb - Ea)) -
        ((∫ t in a..b, w t * s t) + (∫ t in a..b, deriv w t * m t) - (w b * m b - w a * m a))| ≤ εnum) :
    |(∫ t in a..b, w t • Ahat t) (k t0) - (Iws + Iwpm - (Eb - Ea))|
      ≤ L * (∫ t in a..b, |w t| * ‖Ahat t‖ * |t - t0|)
        + Mk * (∫ t in a..b, |w t| * ‖dA t‖) + εnum
```

## W6 — negative controls

```lean
-- dropping the k bound: k-free radius parts are 0 (L=0 variation) and P = 1 is finite,
-- yet the actual error exceeds any prescribed finite C.
theorem W6a_no_finite_radius_without_k_bound (C : ℝ) : ∃ κ : ℝ,
    (∫ t in (0:ℝ)..1, |(1:ℝ)| * ‖(0 : ℝ →L[ℝ] ℝ)‖ * |t - 0|) = 0 ∧
    (∫ t in (0:ℝ)..1, |(1:ℝ)| * ‖ContinuousLinearMap.id ℝ ℝ‖) = 1 ∧
    C < ‖(∫ t in (0:ℝ)..1, (1:ℝ) • (0 : ℝ →L[ℝ] ℝ)) κ -
        Kw 0 1 (fun _ => (1:ℝ)) (fun _ => (0 : ℝ →L[ℝ] ℝ) + ContinuousLinearMap.id ℝ ℝ)
          (fun _ => κ)‖
-- the endpoint term cannot be dropped: w ≡ 1, m = id on [0,1]
theorem W6b_endpoint_term_needed :
    (∫ t in (0:ℝ)..1, (1:ℝ) • (1:ℝ)) ≠ -(∫ t in (0:ℝ)..1, (0:ℝ) • t)
-- endpoint sign: w ≡ 1, m = id, s ≡ 0, A k ≡ -1 satisfies the balance; contract
-- formula gives K_w = -1 exactly, sign-flipped endpoint gives +1 ≠ K_w.
theorem W6c_endpoint_sign :
    (∀ t : ℝ, (1:ℝ) + (-(ContinuousLinearMap.id ℝ ℝ)) (1:ℝ) = (0:ℝ)) ∧
    Kw 0 1 (fun _ => (1:ℝ)) (fun _ => -(ContinuousLinearMap.id ℝ ℝ)) (fun _ => (1:ℝ)) =
      (∫ t in (0:ℝ)..1, (1:ℝ) • (0:ℝ)) + (∫ t in (0:ℝ)..1, (0:ℝ) • t) - ((1:ℝ) • (1:ℝ) - (1:ℝ) • (0:ℝ)) ∧
    Kw 0 1 (fun _ => (1:ℝ)) (fun _ => -(ContinuousLinearMap.id ℝ ℝ)) (fun _ => (1:ℝ)) ≠
      (∫ t in (0:ℝ)..1, (1:ℝ) • (0:ℝ)) + (∫ t in (0:ℝ)..1, (0:ℝ) • t) + ((1:ℝ) • (1:ℝ) - (1:ℝ) • (0:ℝ))
```

## Explicit premises that remain premises (not proved here)

- Same-state stress eigenbranch is encoded by the differentiated, rest-projected
  eigen equation in the eigen-triad of L (`eigenbranch`); its derivation from an
  actual smooth stress is GR-04 `projected_eigen_derivative` (cited) and the general
  self-adjoint diagonalization bridge is not formalized here.
- d*, δ*, L, M_k, the integrability facts and the numerical error εnum are supplied
  premises; no physical provider is constructed.
- The C^1 window of the source is replaced by the more general hypotheses
  (HasDerivAt on [a,b] with integrable derivative, or AC in the scalar branch).
