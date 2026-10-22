import Mathlib
import CAS01C04Accepted

/-!
# G01-B: timelike neighbourhood, smooth normalization, 1-jet and local flow (chart level)

Source: `gr/OPTICAL_THEOREMS.md` §4 Theorem 3 (SHA-256 5ae2b6a6...c8b21), Eq. (17).
The accepted CAS-01 C01-C04 module is imported unchanged as `CAS01C04Accepted`
(namespace `GRSTATCAS01`); its affine candidate `fullSeed` is the seed `v` of Eq. (17).

Scope: chart level.  The metric is a `C^n` field of components on the chart `V = Fin 4 → ℝ`
with the normal-coordinate facts `g(0) = η`, `∂g(0) = 0` used by the source proof.  The
neighbourhood and the flow interval are existential and depend on all data (no uniform radius);
the flow is local (no completeness).  Manifold-level identifications are not claimed.
-/

namespace G01BTimelikeFlow

open Set Metric Filter Topology
open GRSTATCAS01 (eps eval cov fullSeed fullNormalized coordinateLine rest sourceS)

abbrev V := GRSTATCAS01.V
abbrev Form := GRSTATCAS01.Form

/-- Minkowski components `η = diag(-1,1,1,1)`. -/
def eta : Form := fun i j => if i = j then eps i else 0

/-- Chart-level hypotheses of the source proof: `C^n` symmetric metric components, equal to `η`
at the marked origin `p = 0`, with vanishing first derivative there (normal coordinates matched
to the observer tetrad). -/
structure NormalChartMetric (G : V → Form) (n : WithTop ℕ∞) : Prop where
  contDiff : ContDiff ℝ n G
  symm : ∀ x i j, G x i j = G x j i
  origin : G 0 = eta
  hasFDerivAt_origin : HasFDerivAt G (0 : V →L[ℝ] Form) 0

/-- `N(x) = -g_x(v(x), v(x))` for the affine seed `v = fullSeed u Q c`. -/
noncomputable def normSq (G : V → Form) (u : V) (Q : Form) (c : ℝ) (x : V) : ℝ :=
  -eval (G x) (fullSeed u Q c x) (fullSeed u Q c x)

/-- Positive-root normalized unit field `u(x) = v(x) / √(-g_x(v,v))` of Eq. (17). -/
noncomputable def unitField (G : V → Form) (u : V) (Q : Form) (c : ℝ) (x : V) : V :=
  fun b => fullSeed u Q c x b / Real.sqrt (normSq G u Q c x)

/-- Physical field `U = c u`. -/
noncomputable def physField (G : V → Form) (u : V) (Q : Form) (c : ℝ) (x : V) : V :=
  fun b => c * unitField G u Q c x b

/-- Points where the seed is timelike and future (w.r.t. the time-orientation field `T`). -/
def timelikeFutureSet (G : V → Form) (T : V → V) (u : V) (Q : Form) (c : ℝ) : Set V :=
  {x | eval (G x) (fullSeed u Q c x) (fullSeed u Q c x) < 0 ∧
       eval (G x) (fullSeed u Q c x) (T x) < 0}

/-- Coordinate partial derivative `∂_a f (x)`. -/
noncomputable def partialD (f : V → ℝ) (x : V) (a : Fin 4) : ℝ := fderiv ℝ f x (Pi.single a 1)

/-- Christoffel symbols of the first kind `Γ_{e,ab} = ½(∂_a g_eb + ∂_b g_ea − ∂_e g_ab)`. -/
noncomputable def christoffel1 (G : V → Form) (x : V) (e a b : Fin 4) : ℝ :=
  (partialD (fun y => G y e b) x a + partialD (fun y => G y e a) x b
    - partialD (fun y => G y a b) x e) / 2

/-- Lowered field `U_b = g_bc U^c`. -/
def lower (G : V → Form) (U : V → V) (x : V) (b : Fin 4) : ℝ := ∑ c, G x b c * U x c

/-- Chart covariant derivative `∇_a U_b = ∂_a U_b − Γ_{e,ab} U^e`. -/
noncomputable def covDerivLower (G : V → Form) (U : V → V) (x : V) (a b : Fin 4) : ℝ :=
  partialD (fun y => lower G U y b) x a - ∑ e, christoffel1 G x e a b * U x e

/-- Intercept observable of Eq. (4) evaluated on a field: `Z(n) = u(p)·K(p,n)`. -/
noncomputable def opticalZ (G : V → Form) (u : V → V) (x y z : ℝ) : ℝ :=
  eval (G 0) (u 0) (GRSTATCAS01.K x y z)

/-- Slope observable of Eq. (4) evaluated on a field: `H(n) = B_ab K^a K^b`, `B = ∇_(a U_b)`. -/
noncomputable def opticalH (G : V → Form) (U : V → V) (x y z : ℝ) : ℝ :=
  eval (GRSTATCAS01.symPart (fun a b => covDerivLower G U 0 a b))
    (GRSTATCAS01.K x y z) (GRSTATCAS01.K x y z)

/-! ## Elementary algebra -/

theorem eval_eta (v w : V) : eval eta v w = GRSTATCAS01.g v w := by
  simp [eval, eta, GRSTATCAS01.g, Fin.sum_univ_four]

theorem eval_add_form (S T : Form) (v w : V) :
    eval (fun i j => S i j + T i j) v w = eval S v w + eval T v w := by
  simp only [eval, add_mul, Finset.sum_add_distrib]

theorem eval_smul_form (e : ℝ) (T : Form) (v w : V) :
    eval (fun i j => e * T i j) v w = e * eval T v w := by
  simp only [eval, Finset.mul_sum]
  apply Finset.sum_congr rfl; intro i _
  apply Finset.sum_congr rfl; intro j _
  ring

theorem eval_div_left (M : Form) (s w : V) (r : ℝ) :
    eval M (fun b => s b / r) w = eval M s w / r := by
  simp only [eval, Finset.sum_div]
  apply Finset.sum_congr rfl; intro i _
  apply Finset.sum_congr rfl; intro j _
  ring

theorem eval_div_both (M : Form) (s : V) (r : ℝ) :
    eval M (fun b => s b / r) (fun b => s b / r) = eval M s s / r ^ 2 := by
  simp only [eval, Finset.sum_div]
  apply Finset.sum_congr rfl; intro i _
  apply Finset.sum_congr rfl; intro j _
  ring

theorem fullSeed_zero (u : V) (Q : Form) (c : ℝ) : fullSeed u Q c 0 = u := by
  funext b; simp [fullSeed]

theorem coordinateLine_zero (k : Fin 4) : coordinateLine k 0 = 0 := by
  funext a; simp [coordinateLine]

theorem normSq_origin {G : V → Form} (hG0 : G 0 = eta) (u : V) (Q : Form) (c : ℝ)
    (hu : GRSTATCAS01.g u u = -1) : normSq G u Q c 0 = 1 := by
  simp only [normSq, fullSeed_zero, hG0, eval_eta, hu]; norm_num

/-! ## Regularity -/

theorem contDiff_fullSeed (u : V) (Q : Form) (c : ℝ) {n : WithTop ℕ∞} :
    ContDiff ℝ n (fullSeed u Q c) := by
  refine contDiff_pi.2 fun b => ?_
  show ContDiff ℝ n fun x : V => u b + ∑ a, x a * (eps b * Q a b / c)
  exact contDiff_const.add (ContDiff.sum fun a _ => (contDiff_apply ℝ ℝ a).mul contDiff_const)

theorem contDiff_eval {n : WithTop ℕ∞} {G : V → Form} {s w : V → V} (hG : ContDiff ℝ n G)
    (hs : ContDiff ℝ n s) (hw : ContDiff ℝ n w) :
    ContDiff ℝ n (fun x => eval (G x) (s x) (w x)) := by
  show ContDiff ℝ n fun x => ∑ i, ∑ j, G x i j * s x i * w x j
  refine ContDiff.sum fun i _ => ContDiff.sum fun j _ => ?_
  exact (((contDiff_apply_apply ℝ ℝ i j).comp hG).mul ((contDiff_apply ℝ ℝ i).comp hs)).mul
    ((contDiff_apply ℝ ℝ j).comp hw)

theorem continuous_eval {G : V → Form} {s w : V → V} (hG : Continuous G) (hs : Continuous s)
    (hw : Continuous w) : Continuous (fun x => eval (G x) (s x) (w x)) := by
  show Continuous fun x => ∑ i, ∑ j, G x i j * s x i * w x j
  refine continuous_finsetSum _ fun i _ => continuous_finsetSum _ fun j _ => ?_
  exact (((continuous_apply j).comp ((continuous_apply i).comp hG)).mul
    ((continuous_apply i).comp hs)).mul ((continuous_apply j).comp hw)

/-! ## T1-T3: open timelike-future neighbourhood of positive radius -/

theorem timelikeFutureSet_isOpen {G : V → Form} {T : V → V} {u : V} {Q : Form} {c : ℝ}
    (hG : Continuous G) (hT : Continuous T) : IsOpen (timelikeFutureSet G T u Q c) := by
  have hs : Continuous (fullSeed u Q c) := (contDiff_fullSeed u Q c (n := 0)).continuous
  exact (isOpen_lt (continuous_eval hG hs hs) continuous_const).inter
    (isOpen_lt (continuous_eval hG hs hT) continuous_const)

theorem origin_mem_timelikeFutureSet {G : V → Form} {T : V → V} {u : V} {Q : Form} {c : ℝ}
    (hG0 : G 0 = eta) (hT0 : T 0 = rest) (hu : GRSTATCAS01.g u u = -1) (hfut : 0 < u 0) :
    (0 : V) ∈ timelikeFutureSet G T u Q c := by
  refine ⟨?_, ?_⟩
  · show eval (G 0) (fullSeed u Q c 0) (fullSeed u Q c 0) < 0
    rw [fullSeed_zero, hG0, eval_eta, hu]; norm_num
  · show eval (G 0) (fullSeed u Q c 0) (T 0) < 0
    rw [fullSeed_zero, hG0, hT0, eval_eta]
    simp [GRSTATCAS01.g, rest, Fin.sum_univ_four, eps]
    linarith

theorem exists_ball_subset_timelikeFutureSet {G : V → Form} {T : V → V} {u : V} {Q : Form}
    {c : ℝ} (hG : Continuous G) (hT : Continuous T) (hG0 : G 0 = eta) (hT0 : T 0 = rest)
    (hu : GRSTATCAS01.g u u = -1) (hfut : 0 < u 0) :
    ∃ ε > 0, Metric.ball (0 : V) ε ⊆ timelikeFutureSet G T u Q c :=
  Metric.isOpen_iff.1 (timelikeFutureSet_isOpen hG hT) 0
    (origin_mem_timelikeFutureSet hG0 hT0 hu hfut)

/-! ## T4-T7: smooth positive-root normalization, unit norm, future, value -/

theorem unitField_contDiffOn {n : WithTop ℕ∞} {G : V → Form} {T : V → V} {u : V} {Q : Form}
    {c : ℝ} (hG : ContDiff ℝ n G) :
    ContDiffOn ℝ n (unitField G u Q c) (timelikeFutureSet G T u Q c) := by
  intro x hx
  have hN : ContDiff ℝ n (normSq G u Q c) :=
    (contDiff_eval hG (contDiff_fullSeed u Q c) (contDiff_fullSeed u Q c)).neg
  have hpos : 0 < normSq G u Q c x := by unfold normSq; linarith [hx.1]
  refine ContDiffAt.contDiffWithinAt ?_
  refine contDiffAt_pi.2 fun b => ?_
  exact ((contDiff_apply ℝ ℝ b).comp (contDiff_fullSeed u Q c)).contDiffAt.div
    (hN.contDiffAt.sqrt hpos.ne') (Real.sqrt_pos.2 hpos).ne'

theorem physField_contDiffOn {n : WithTop ℕ∞} {G : V → Form} {T : V → V} {u : V} {Q : Form}
    {c : ℝ} (hG : ContDiff ℝ n G) :
    ContDiffOn ℝ n (physField G u Q c) (timelikeFutureSet G T u Q c) := by
  intro x hx
  have h' := contDiffWithinAt_pi.1 ((unitField_contDiffOn (T := T) (u := u) (Q := Q) (c := c) hG) x hx)
  exact contDiffWithinAt_pi.2 fun b => contDiffWithinAt_const.mul (h' b)

theorem unitField_unit {G : V → Form} {T : V → V} {u : V} {Q : Form} {c : ℝ} {x : V}
    (hx : x ∈ timelikeFutureSet G T u Q c) :
    eval (G x) (unitField G u Q c x) (unitField G u Q c x) = -1 := by
  have hE : eval (G x) (fullSeed u Q c x) (fullSeed u Q c x) < 0 := hx.1
  show eval (G x) (fun b => fullSeed u Q c x b / Real.sqrt (normSq G u Q c x))
    (fun b => fullSeed u Q c x b / Real.sqrt (normSq G u Q c x)) = -1
  rw [eval_div_both, Real.sq_sqrt (by unfold normSq; linarith)]
  unfold normSq
  rw [div_neg, div_self hE.ne]

theorem unitField_future {G : V → Form} {T : V → V} {u : V} {Q : Form} {c : ℝ} {x : V}
    (hx : x ∈ timelikeFutureSet G T u Q c) :
    eval (G x) (unitField G u Q c x) (T x) < 0 := by
  have hE : eval (G x) (fullSeed u Q c x) (fullSeed u Q c x) < 0 := hx.1
  show eval (G x) (fun b => fullSeed u Q c x b / Real.sqrt (normSq G u Q c x)) (T x) < 0
  rw [eval_div_left]
  have hpos : 0 < Real.sqrt (normSq G u Q c x) :=
    Real.sqrt_pos.2 (by unfold normSq; linarith)
  exact div_neg_of_neg_of_pos hx.2 hpos

theorem unitField_origin {G : V → Form} (hG0 : G 0 = eta) (u : V) (Q : Form) (c : ℝ)
    (hu : GRSTATCAS01.g u u = -1) : unitField G u Q c 0 = u := by
  funext b
  simp only [unitField, fullSeed_zero, normSq_origin hG0 u Q c hu, Real.sqrt_one, div_one]

/-! ## T8-T9: the 1-jet in a curved normal chart, and agreement with C04 -/

theorem hasDerivAt_coordinateLine (k : Fin 4) (t : ℝ) :
    HasDerivAt (coordinateLine k) (Pi.single k (1 : ℝ) : V) t := by
  rw [hasDerivAt_pi]
  intro a
  by_cases h : a = k
  · subst h; simpa [coordinateLine] using hasDerivAt_id' t
  · simpa [coordinateLine, h] using hasDerivAt_const t (0 : ℝ)

theorem seed_line_hasDerivAt (u : V) (Q : Form) (c : ℝ) (k i : Fin 4) (t : ℝ) :
    HasDerivAt (fun t => fullSeed u Q c (coordinateLine k t) i) (eps i * Q k i / c) t := by
  have h : (fun t => fullSeed u Q c (coordinateLine k t) i) =
      fun t => u i + t * (eps i * Q k i / c) := by
    funext t; rw [GRSTATCAS01.fullSeed_coordinateLine]; rfl
  rw [h]
  simpa using ((hasDerivAt_id' t).mul_const (eps i * Q k i / c)).const_add (u i)

theorem hasFDerivAt_G_comp {G : V → Form} (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0)
    (i j : Fin 4) : HasFDerivAt (fun x => G x i j) (0 : V →L[ℝ] ℝ) 0 := by
  have h1 := hasFDerivAt_pi'.1 hG' i
  have h2 := hasFDerivAt_pi'.1 h1 j
  simpa using h2

theorem G_line_hasDerivAt {G : V → Form} (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0)
    (k i j : Fin 4) : HasDerivAt (fun t => G (coordinateLine k t) i j) 0 0 := by
  have hG : HasFDerivAt (fun x => G x i j) (0 : V →L[ℝ] ℝ) (coordinateLine k 0) := by
    rw [coordinateLine_zero]; exact hasFDerivAt_G_comp hG' i j
  have h := hG.comp_hasDerivAt 0 (hasDerivAt_coordinateLine k 0)
  rw [ContinuousLinearMap.zero_apply] at h
  exact h

theorem normSq_line_hasDerivAt {G : V → Form} (hG0 : G 0 = eta)
    (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0) (u : V) (Q : Form) (c : ℝ)
    (hQ : ∀ k, cov Q u k = 0) (k : Fin 4) :
    HasDerivAt (fun t => normSq G u Q c (coordinateLine k t)) 0 0 := by
  have hterm : ∀ i j : Fin 4, HasDerivAt
      (fun t => G (coordinateLine k t) i j * fullSeed u Q c (coordinateLine k t) i *
        fullSeed u Q c (coordinateLine k t) j)
      ((0 * u i + eta i j * (eps i * Q k i / c)) * u j + eta i j * u i * (eps j * Q k j / c))
      0 := by
    intro i j
    have h := ((G_line_hasDerivAt hG' k i j).mul (seed_line_hasDerivAt u Q c k i 0)).mul
      (seed_line_hasDerivAt u Q c k j 0)
    simp only [coordinateLine_zero, fullSeed_zero, hG0, Pi.mul_apply] at h
    exact h
  have hsum := (HasDerivAt.fun_sum (u := Finset.univ) fun i _ =>
    HasDerivAt.fun_sum (u := Finset.univ) fun j _ => hterm i j).neg
  show HasDerivAt (fun t => -(∑ i, ∑ j, G (coordinateLine k t) i j *
      fullSeed u Q c (coordinateLine k t) i * fullSeed u Q c (coordinateLine k t) j)) 0 0
  refine hsum.congr_deriv ?_
  have key : (-(∑ i, ∑ j, ((0 * u i + eta i j * (eps i * Q k i / c)) * u j +
      eta i j * u i * (eps j * Q k j / c)))) = -(2 / c) * cov Q u k := by
    simp [eta, eps, Fin.sum_univ_four, cov] <;> ring
  rw [key, hQ k, mul_zero]

theorem unitField_coordinate_jet {G : V → Form} (hG0 : G 0 = eta)
    (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0) (u : V) (Q : Form) (c : ℝ)
    (hu : GRSTATCAS01.g u u = -1) (hQ : ∀ k, cov Q u k = 0) :
    ∀ k b, HasDerivAt (fun t => unitField G u Q c (coordinateLine k t) b)
      (eps b * Q k b / c) 0 := by
  intro k b
  have hN := normSq_line_hasDerivAt hG0 hG' u Q c hQ k
  have hN0 := normSq_origin hG0 u Q c hu
  have hsq := hN.sqrt (by simp only [coordinateLine_zero, hN0]; norm_num)
  have hdiv := (seed_line_hasDerivAt u Q c k b 0).div hsq
    (by simp only [coordinateLine_zero, hN0, Real.sqrt_one]; norm_num)
  refine hdiv.congr_deriv ?_
  simp [coordinateLine_zero, fullSeed_zero, hN0]

theorem jet_agrees_with_C04 {G : V → Form} (hG0 : G 0 = eta)
    (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0) (u : V) (Q : Form) (c : ℝ) (hc : 0 < c)
    (hu : GRSTATCAS01.g u u = -1) (hQ : ∀ k, cov Q u k = 0) :
    unitField G u Q c 0 = fullNormalized u Q c (fun _ => 0) ∧
      ∀ k b, ∃ d, HasDerivAt (fun t => unitField G u Q c (coordinateLine k t) b) d 0 ∧
        HasDerivAt (fun t => fullNormalized u Q c (coordinateLine k t) b) d 0 := by
  refine ⟨?_, fun k b => ⟨_, unitField_coordinate_jet hG0 hG' u Q c hu hQ k b,
    GRSTATCAS01.fullNormalized_coordinate_derivative u Q c k b hc hu (hQ k)⟩⟩
  rw [unitField_origin hG0 u Q c hu, GRSTATCAS01.fullNormalized_origin u Q c hu]

/-! ## T11-T13: local integral curves, local flow, local uniqueness -/

theorem physField_contDiffAt_one {n : WithTop ℕ∞} {G : V → Form} {T : V → V} {u : V}
    {Q : Form} {c : ℝ} (hG : ContDiff ℝ n G) (hn : 1 ≤ n) (hT : Continuous T) {x0 : V}
    (hx0 : x0 ∈ timelikeFutureSet G T u Q c) : ContDiffAt ℝ 1 (physField G u Q c) x0 :=
  ((physField_contDiffOn (T := T) hG).contDiffAt
    ((timelikeFutureSet_isOpen hG.continuous hT).mem_nhds hx0)).of_le hn

theorem physField_local_integral_curve {n : WithTop ℕ∞} {G : V → Form} {T : V → V} {u : V}
    {Q : Form} {c : ℝ} (hG : ContDiff ℝ n G) (hn : 1 ≤ n) (hT : Continuous T) :
    ∀ x0 ∈ timelikeFutureSet G T u Q c, ∃ α : ℝ → V, α 0 = x0 ∧ ∃ ε > 0,
      ∀ t ∈ Set.Ioo (-ε) ε, HasDerivAt α (physField G u Q c (α t)) t ∧
        α t ∈ timelikeFutureSet G T u Q c := by
  intro x0 hx0
  have hf := physField_contDiffAt_one hG hn hT hx0
  obtain ⟨α, hα0, ε, hε, hα⟩ :=
    hf.exists_forall_mem_closedBall_exists_eq_forall_mem_Ioo_hasDerivAt₀ 0
  have hcont : ContinuousAt α 0 :=
    (hα 0 ⟨by linarith, by linarith⟩).continuousAt
  have hmem : α ⁻¹' timelikeFutureSet G T u Q c ∈ 𝓝 (0 : ℝ) :=
    hcont.preimage_mem_nhds (by
      rw [hα0]; exact (timelikeFutureSet_isOpen hG.continuous hT).mem_nhds hx0)
  obtain ⟨δ, hδ, hball⟩ := Metric.mem_nhds_iff.1 hmem
  refine ⟨α, hα0, min ε δ, lt_min hε hδ, fun t ht => ⟨hα t ?_, hball ?_⟩⟩
  · have h1 := min_le_left ε δ
    exact ⟨by linarith [ht.1], by linarith [ht.2]⟩
  · have h2 := min_le_right ε δ
    rw [Metric.mem_ball, Real.dist_eq, sub_zero, abs_lt]
    exact ⟨by linarith [ht.1], by linarith [ht.2]⟩

theorem physField_local_flow {n : WithTop ℕ∞} {G : V → Form} {T : V → V} {u : V}
    {Q : Form} {c : ℝ} (hG : ContDiff ℝ n G) (hn : 1 ≤ n) (hT : Continuous T) :
    ∀ x0 ∈ timelikeFutureSet G T u Q c, ∃ α : V → ℝ → V,
      ∀ᶠ xt in 𝓝 x0 ×ˢ 𝓝 (0 : ℝ), α xt.1 0 = xt.1 ∧
        HasDerivAt (α xt.1) (physField G u Q c (α xt.1 xt.2)) xt.2 :=
  fun _ hx0 => (physField_contDiffAt_one hG hn hT hx0).exists_eventually_eq_hasDerivAt 0

theorem physField_integral_curve_unique {n : WithTop ℕ∞} {G : V → Form} {T : V → V} {u : V}
    {Q : Form} {c : ℝ} (hG : ContDiff ℝ n G) (hn : 1 ≤ n) (hT : Continuous T) :
    ∀ x0 ∈ timelikeFutureSet G T u Q c, ∀ γ₁ γ₂ : ℝ → V,
      (∀ᶠ t in 𝓝 0, HasDerivAt γ₁ (physField G u Q c (γ₁ t)) t) →
      (∀ᶠ t in 𝓝 0, HasDerivAt γ₂ (physField G u Q c (γ₂ t)) t) →
      γ₁ 0 = x0 → γ₂ 0 = x0 → γ₁ =ᶠ[𝓝 0] γ₂ := by
  intro x0 hx0 γ₁ γ₂ h₁ h₂ h₁0 h₂0
  obtain ⟨K, s, hs, hK⟩ := (physField_contDiffAt_one hG hn hT hx0).exists_lipschitzOnWith
  have hm₁ : ∀ᶠ t in 𝓝 (0 : ℝ), γ₁ t ∈ s :=
    h₁.self_of_nhds.continuousAt.preimage_mem_nhds (by rw [h₁0]; exact hs)
  have hm₂ : ∀ᶠ t in 𝓝 (0 : ℝ), γ₂ t ∈ s :=
    h₂.self_of_nhds.continuousAt.preimage_mem_nhds (by rw [h₂0]; exact hs)
  exact ODE_solution_unique_of_eventually (v := fun _ => physField G u Q c) (s := fun _ => s)
    (K := K) (Filter.Eventually.of_forall fun _ => hK) (h₁.and hm₁) (h₂.and hm₂)
    (h₁0.trans h₂0.symm)

/-! ## T10: covariant derivative of the physical field at the origin -/

theorem partialD_eq_of_hasDerivAt {f : V → ℝ} (hf : DifferentiableAt ℝ f 0) (a : Fin 4) {d : ℝ}
    (hd : HasDerivAt (fun t => f (coordinateLine a t)) d 0) : partialD f 0 a = d := by
  have hf' : HasFDerivAt f (fderiv ℝ f 0) (coordinateLine a 0) := by
    rw [coordinateLine_zero]; exact hf.hasFDerivAt
  exact (hf'.comp_hasDerivAt 0 (hasDerivAt_coordinateLine a 0)).unique hd

theorem christoffel1_origin {G : V → Form} (hG' : HasFDerivAt G (0 : V →L[ℝ] Form) 0)
    (e a b : Fin 4) : christoffel1 G 0 e a b = 0 := by
  simp only [christoffel1, partialD, (hasFDerivAt_G_comp hG' e b).fderiv,
    (hasFDerivAt_G_comp hG' e a).fderiv, (hasFDerivAt_G_comp hG' a b).fderiv]
  simp

theorem covDeriv_physField_origin {n : WithTop ℕ∞} {G : V → Form} (hG : NormalChartMetric G n)
    (hn : 1 ≤ n) {u : V} {Q : Form} {c : ℝ} (hc : 0 < c) (hu : GRSTATCAS01.g u u = -1)
    (hfut : 0 < u 0) (hQ : ∀ k, cov Q u k = 0) :
    ∀ a b, covDerivLower G (physField G u Q c) 0 a b = Q a b := by
  intro a b
  have hmem := origin_mem_timelikeFutureSet (T := fun _ => rest) (Q := Q) (c := c)
    hG.origin rfl hu hfut
  have hU : ContDiffAt ℝ 1 (physField G u Q c) 0 :=
    physField_contDiffAt_one hG.contDiff hn continuous_const hmem
  have hUd : DifferentiableAt ℝ (physField G u Q c) 0 := hU.differentiableAt one_ne_zero
  have hGd : DifferentiableAt ℝ G 0 := hG.hasFDerivAt_origin.differentiableAt
  have hLd : DifferentiableAt ℝ (fun y => lower G (physField G u Q c) y b) 0 := by
    show DifferentiableAt ℝ (fun y => ∑ c', G y b c' * physField G u Q c y c') 0
    exact DifferentiableAt.fun_sum fun c' _ =>
      (differentiableAt_pi.1 (differentiableAt_pi.1 hGd b) c').mul (differentiableAt_pi.1 hUd c')
  have hUl : ∀ c', HasDerivAt (fun t => physField G u Q c (coordinateLine a t) c')
      (c * (eps c' * Q a c' / c)) 0 := fun c' =>
    (unitField_coordinate_jet hG.origin hG.hasFDerivAt_origin u Q c hu hQ a c').const_mul c
  have hL : HasDerivAt (fun t => lower G (physField G u Q c) (coordinateLine a t) b)
      (∑ c', (0 * physField G u Q c (coordinateLine a 0) c' +
        G (coordinateLine a 0) b c' * (c * (eps c' * Q a c' / c)))) 0 :=
    HasDerivAt.fun_sum fun c' _ => (G_line_hasDerivAt hG.hasFDerivAt_origin a b c').mul (hUl c')
  have hpart := partialD_eq_of_hasDerivAt hLd a hL
  simp only [covDerivLower, hpart, christoffel1_origin hG.hasFDerivAt_origin, zero_mul,
    Finset.sum_const_zero, sub_zero, coordinateLine_zero, hG.origin, zero_add]
  have hc' : c ≠ 0 := hc.ne'
  fin_cases b <;> simp [eta, eps, Fin.sum_univ_four, hc'] <;> field_simp

/-! ## T14: bundled local realization (same constructed field and flow) -/

theorem eval_B_null (S : Form) (u : V) (x y z : ℝ) (hn : x * x + y * y + z * z = 1) :
    eval (GRSTATCAS01.B S u) (GRSTATCAS01.K x y z) (GRSTATCAS01.K x y z) =
      eval S (GRSTATCAS01.K x y z) (GRSTATCAS01.K x y z) := by
  have hsplit : GRSTATCAS01.B S u = fun i j => S i j + eval S u u * eta i j := rfl
  have hgK : GRSTATCAS01.g (GRSTATCAS01.K x y z) (GRSTATCAS01.K x y z) = 0 := by
    simp [GRSTATCAS01.g, GRSTATCAS01.K, Fin.sum_univ_four, eps]
    linarith
  rw [hsplit, eval_add_form, eval_smul_form, eval_eta, hgK, mul_zero, add_zero]

theorem sourceS_sym (h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz : ℝ) :
    GRSTATCAS01.sym (sourceS h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz) := by
  intro i j
  fin_cases i <;> fin_cases j <;> simp [sourceS]

theorem G01B_local_realization
    (ζ0 ζ1 ζ2 ζ3 h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz c : ℝ) (W : Form)
    (G : V → Form) (T : V → V) (n : WithTop ℕ∞)
    (hshell : ζ0 ^ 2 - (ζ1 ^ 2 + ζ2 ^ 2 + ζ3 ^ 2) = 1) (hζ0 : 1 ≤ ζ0)
    (hSTF : hxx + hyy + hzz = 0) (hc : 0 < c)
    (hW : GRSTATCAS01.skew W) (hWsp : GRSTATCAS01.spatial W ![ζ0, ζ1, ζ2, ζ3])
    (hG : NormalChartMetric G n) (hn : 1 ≤ n) (hT : Continuous T) (hT0 : T 0 = rest) :
    let u : V := ![ζ0, ζ1, ζ2, ζ3]
    let S := sourceS h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz
    let Qd := GRSTATCAS01.Q (GRSTATCAS01.B S u) W u
    let N := timelikeFutureSet G T u Qd c
    IsOpen N ∧ (0 : V) ∈ N ∧ (∃ ε > 0, Metric.ball (0 : V) ε ⊆ N) ∧
    ContDiffOn ℝ n (unitField G u Qd c) N ∧ ContDiffOn ℝ n (physField G u Qd c) N ∧
    (∀ x ∈ N, eval (G x) (unitField G u Qd c x) (unitField G u Qd c x) = -1 ∧
      eval (G x) (unitField G u Qd c x) (T x) < 0) ∧
    unitField G u Qd c 0 = u ∧
    (∀ k b, HasDerivAt (fun t => unitField G u Qd c (coordinateLine k t) b)
      (eps b * Qd k b / c) 0) ∧
    (∀ a b, covDerivLower G (physField G u Qd c) 0 a b = Qd a b) ∧
    (∀ x0 ∈ N, ∃ α : ℝ → V, α 0 = x0 ∧ ∃ ε > 0, ∀ t ∈ Set.Ioo (-ε) ε,
      HasDerivAt α (physField G u Qd c (α t)) t ∧ α t ∈ N) ∧
    (∀ x y z : ℝ, x * x + y * y + z * z = 1 →
      opticalZ G (unitField G u Qd c) x y z = ζ0 + ζ1 * x + ζ2 * y + ζ3 * z ∧
      opticalH G (physField G u Qd c) x y z =
        h0 + h1x * x + h1y * y + h1z * z +
        (hxx * x * x + hyy * y * y + hzz * z * z +
          2 * hxy * x * y + 2 * hxz * x * z + 2 * hyz * y * z)) := by
  intro u S Qd N
  have hu : GRSTATCAS01.g u u = -1 := by
    simp [u, GRSTATCAS01.g, Fin.sum_univ_four, eps]
    nlinarith [hshell]
  have hfut : 0 < u 0 := by
    show (0 : ℝ) < ![ζ0, ζ1, ζ2, ζ3] 0
    simp; linarith
  have hS : GRSTATCAS01.sym S := sourceS_sym _ _ _ _ _ _ _ _ _ _
  have hQ : ∀ k, cov Qd u k = 0 :=
    GRSTATCAS01.Q_right_null (GRSTATCAS01.B S u) W u hu (GRSTATCAS01.B_unit S u hu) hWsp
  have hGc : Continuous G := hG.contDiff.continuous
  have hcd : ∀ a b, covDerivLower G (physField G u Qd c) 0 a b = Qd a b :=
    covDeriv_physField_origin hG hn hc hu hfut hQ
  refine ⟨timelikeFutureSet_isOpen hGc hT,
    origin_mem_timelikeFutureSet hG.origin hT0 hu hfut,
    exists_ball_subset_timelikeFutureSet hGc hT hG.origin hT0 hu hfut,
    unitField_contDiffOn hG.contDiff, physField_contDiffOn hG.contDiff,
    fun x hx => ⟨unitField_unit hx, unitField_future hx⟩,
    unitField_origin hG.origin u Qd c hu,
    unitField_coordinate_jet hG.origin hG.hasFDerivAt_origin u Qd c hu hQ,
    hcd,
    physField_local_integral_curve hG.contDiff hn hT,
    fun x y z hn3 => ⟨?_, ?_⟩⟩
  · unfold opticalZ
    rw [hG.origin, unitField_origin hG.origin u Qd c hu, eval_eta]
    simp [u, GRSTATCAS01.g, GRSTATCAS01.K, Fin.sum_univ_four, eps]
  · have hfun : (fun a b => covDerivLower G (physField G u Qd c) 0 a b) = Qd := by
      funext a b; exact hcd a b
    have hsym : GRSTATCAS01.symPart Qd = GRSTATCAS01.B S u :=
      GRSTATCAS01.Q_symmetric_part (GRSTATCAS01.B S u) W u
        (GRSTATCAS01.B_symmetric S u hS) hW
    unfold opticalH
    rw [hfun, hsym, eval_B_null S u x y z hn3]
    exact GRSTATCAS01.general_sourceward_harmonics h0 h1x h1y h1z hxx hyy hzz hxy hxz hyz
      x y z hSTF

/-! ## Controls -/

/-- N1 non-vacuity: the Minkowski chart satisfies every chart hypothesis. -/
theorem minkowski_normalChartMetric (n : WithTop ℕ∞) : NormalChartMetric (fun _ => eta) n where
  contDiff := contDiff_const
  symm := by
    intro _ i j
    unfold eta
    by_cases h : i = j
    · subst h; rfl
    · simp [h, Ne.symm h]
  origin := rfl
  hasFDerivAt_origin := hasFDerivAt_const eta 0

/-- N2: in the flat chart the constructed field is literally the accepted C04 field. -/
theorem minkowski_unitField_eq_C04 (u : V) (Q : Form) (c : ℝ) :
    unitField (fun _ => eta) u Q c = fullNormalized u Q c := by
  funext x b
  simp only [unitField, normSq, eval_eta, fullNormalized]

/-- N3 negative control: within the admissible family of `G01B_local_realization`
(ζ = (1,0,0,0), STF data, W = 0, Minkowski chart) no radius works for every member. -/
theorem no_uniform_radius (c : ℝ) (hc : 0 < c) (T : V → V) :
    ∀ r > 0, ∃ lam > 0, ¬ (Metric.ball (0 : V) r ⊆ timelikeFutureSet (fun _ => eta) T rest
      (GRSTATCAS01.Q (GRSTATCAS01.B
        (sourceS (lam / 3) 0 0 0 (2 * lam / 3) (-lam / 3) (-lam / 3) 0 0 0) rest)
        (fun _ _ => 0) rest) c) := by
  intro r hr
  have hc0 : c ≠ 0 := hc.ne'
  have hr0 : r ≠ 0 := hr.ne'
  refine ⟨2 * c / r, by positivity, fun hsub => ?_⟩
  set lam := 2 * c / r with hlam
  set Qf := GRSTATCAS01.Q (GRSTATCAS01.B
      (sourceS (lam / 3) 0 0 0 (2 * lam / 3) (-lam / 3) (-lam / 3) 0 0 0) rest)
      (fun _ _ => 0) rest with hQf
  let xr : V := ![0, r / 2, 0, 0]
  have hxr : xr ∈ Metric.ball (0 : V) r := by
    rw [Metric.mem_ball, dist_zero_right, pi_norm_lt_iff hr]
    intro i
    fin_cases i <;> simp [xr, abs_of_pos hr, hr] <;> linarith
  have hmem := (hsub hxr).1
  have hQ1 : ∀ b : Fin 4, Qf 1 b = if b = 1 then lam else 0 := by
    intro b
    rw [hQf]
    fin_cases b <;>
      simp [GRSTATCAS01.Q, GRSTATCAS01.B, sourceS, cov, eval, GRSTATCAS01.flat, rest,
        Fin.sum_univ_four, eps] <;> ring
  have hseed : fullSeed rest Qf c xr = ![1, 1, 0, 0] := by
    funext b
    have e : fullSeed rest Qf c xr b = rest b + r / 2 * (eps b * Qf 1 b / c) := by
      simp [fullSeed, Fin.sum_univ_four, xr]
    rw [e, hQ1]
    fin_cases b <;> simp [rest, eps, hlam] <;> field_simp
  change eval eta _ _ < 0 at hmem
  rw [hseed, eval_eta] at hmem
  simp [GRSTATCAS01.g, Fin.sum_univ_four, eps] at hmem

end G01BTimelikeFlow
