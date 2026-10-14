import Mathlib
import G05BCubicDEC
import G04AEigenline

/-!
# G05-B, module 2: curved isolated-eigenframe implicit function theorem

Curved adaptation of the reviewed flat G04-A bordered IFT (G04-A is imported unchanged; only its
generic helpers `G04A.quad_hasDerivAt` and `G04A.isInvertible_of_injective` are used).

* `borderedG`: the gauge-fixed (normalized) eigen-system
  `(x,(v,m)) ↦ (T(x) v − m v, g_x(v,v) + 1)` with the ACTUAL metric `g(x)`.
* F1 `borderedG_fderiv_inr`: its `(v,m)`-derivative.
* F2 `borderedG_inj`: spectral isolation (`L = hT|_{u⊥} + εI` injective) at a self-adjoint point
  makes that derivative injective.
* F3 `curved_smooth_eigenline`: C^n normalized future energy eigenfield, persistence of the gap,
  local isolation of the branch.
* F4 `unique_future_eigen`: at a Lorentzian point with a self-adjoint `T` and a gap, the future unit
  timelike eigenvector is unique.
-/

namespace G05BIFT

open G05AConformalDEC G05BCubicDEC
open scoped Topology ContDiff

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

/-! ## Bilinear-form algebra -/

theorem bil_add_right (Mx : I → I → ℝ) (V W W' : I → ℝ) :
    bil Mx V (W + W') = bil Mx V W + bil Mx V W' := by
  simp only [bil, sum4, Pi.add_apply]; ring

theorem bil_sub_right (Mx : I → I → ℝ) (V W W' : I → ℝ) :
    bil Mx V (W - W') = bil Mx V W - bil Mx V W' := by
  simp only [bil, sum4, Pi.sub_apply]; ring

theorem bil_smul_right (Mx : I → I → ℝ) (V W : I → ℝ) (r : ℝ) :
    bil Mx V (r • W) = r * bil Mx V W := by
  simp only [bil, sum4, Pi.smul_apply, smul_eq_mul]; ring

theorem bil_add_left (Mx : I → I → ℝ) (V V' W : I → ℝ) :
    bil Mx (V + V') W = bil Mx V W + bil Mx V' W := by
  simp only [bil, sum4, Pi.add_apply]; ring

theorem bil_sub_left (Mx : I → I → ℝ) (V V' W : I → ℝ) :
    bil Mx (V - V') W = bil Mx V W - bil Mx V' W := by
  simp only [bil, sum4, Pi.sub_apply]; ring

theorem bil_smul_left (Mx : I → I → ℝ) (V W : I → ℝ) (r : ℝ) :
    bil Mx (r • V) W = r * bil Mx V W := by
  simp only [bil, sum4, Pi.smul_apply, smul_eq_mul]; ring

theorem bil_zero_right (Mx : I → I → ℝ) (V : I → ℝ) : bil Mx V 0 = 0 := by
  simp [bil, sum4]

theorem bil_comm (Mx : I → I → ℝ) (hs : ∀ a c, Mx a c = Mx c a) (V W : I → ℝ) :
    bil Mx V W = bil Mx W V := by
  simp only [bil, sum4]
  rw [hs 1 0, hs 2 0, hs 2 1, hs 3 0, hs 3 1, hs 3 2]
  ring

theorem mv_add (Mx : I → I → ℝ) (v w : I → ℝ) : mv Mx (v + w) = mv Mx v + mv Mx w := by
  funext a; simp only [mv, sum4, Pi.add_apply]; ring

theorem mv_smul (Mx : I → I → ℝ) (v : I → ℝ) (r : ℝ) : mv Mx (r • v) = r • mv Mx v := by
  funext a; simp only [mv, sum4, Pi.smul_apply, smul_eq_mul]; ring

/-! ## F1: derivative of the gauge-fixed map -/

theorem borderedG_fderiv_inr {g Tm : (I → ℝ) → I → I → ℝ} {x : I → ℝ} {y : (I → ℝ) × ℝ}
    (hsym : ∀ a c, g x a c = g x c a)
    (hd : DifferentiableAt ℝ (borderedG g Tm) (x, y)) (w : I → ℝ) (m : ℝ) :
    (fderiv ℝ (borderedG g Tm) (x, y) ∘L ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)) (w, m) =
      (mv (Tm x) w - y.2 • w - m • y.1, 2 * bil (g x) y.1 w) := by
  rw [ContinuousLinearMap.comp_apply, ContinuousLinearMap.inr_apply]
  set d : (I → ℝ) × ((I → ℝ) × ℝ) := (0, (w, m))
  have hline : HasDerivAt (fun s : ℝ => ((x, y) : (I → ℝ) × ((I → ℝ) × ℝ)) + s • d) d 0 := by
    simpa using ((hasDerivAt_id (0 : ℝ)).smul_const d).const_add
      ((x, y) : (I → ℝ) × ((I → ℝ) × ℝ))
  have h1 := hd.hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) hline (by simp)
  have h2 : HasDerivAt (borderedG g Tm ∘ fun s : ℝ => ((x, y) : (I → ℝ) × ((I → ℝ) × ℝ)) + s • d)
      (mv (Tm x) w - y.2 • w - m • y.1, 2 * bil (g x) y.1 w) 0 := by
    have hfun : (borderedG g Tm ∘ fun s : ℝ => ((x, y) : (I → ℝ) × ((I → ℝ) × ℝ)) + s • d) =
        fun s => (mv (Tm x) (y.1 + s • w) - (y.2 + s * m) • (y.1 + s • w),
          bil (g x) (y.1 + s • w) (y.1 + s • w) + 1) := by
      funext s; simp [borderedG, d]
    rw [hfun]
    refine HasDerivAt.prodMk ?_ ?_
    · refine hasDerivAt_pi.2 (fun a => ?_)
      have hc : (fun s : ℝ => (mv (Tm x) (y.1 + s • w) - (y.2 + s * m) • (y.1 + s • w)) a) =
          fun s => (mv (Tm x) y.1 a - y.2 * y.1 a) +
            (mv (Tm x) w a - y.2 * w a - m * y.1 a) * s + (-(m * w a)) * s ^ 2 := by
        funext s; simp only [mv, sum4, Pi.sub_apply, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
        ring
      rw [hc]
      exact (G04A.quad_hasDerivAt _ _ _).congr_deriv (by simp [mv])
    · have hc : (fun s : ℝ => bil (g x) (y.1 + s • w) (y.1 + s • w) + 1) =
          fun s => (bil (g x) y.1 y.1 + 1) + (2 * bil (g x) y.1 w) * s +
            (bil (g x) w w) * s ^ 2 := by
        funext s
        rw [bil_add_left, bil_add_right, bil_add_right, bil_smul_left, bil_smul_left,
          bil_smul_right, bil_smul_right, bil_comm (g x) hsym w y.1]
        ring
      rw [hc]
      exact G04A.quad_hasDerivAt _ _ _
  exact h1.unique h2

/-! ## F2: spectral isolation gives an injective IFT derivative -/

theorem borderedG_inj {gx Tx : I → I → ℝ} {u : I → ℝ} {ε : ℝ} (hsa : SelfAdjG gx Tx)
    (hu : FutureUnitEigenG gx Tx u ε) (hgap : RestGapG gx Tx u ε) (w : I → ℝ) (m : ℝ)
    (h : ((mv Tx w - (-ε) • w - m • u, 2 * bil gx u w) : (I → ℝ) × ℝ) = 0) :
    w = 0 ∧ m = 0 := by
  obtain ⟨hTu, hn, _⟩ := hu
  have h1 : mv Tx w - (-ε) • w - m • u = 0 := congrArg Prod.fst h
  have h2 : 2 * bil gx u w = 0 := congrArg Prod.snd h
  have ho : bil gx u w = 0 := by linarith
  have hTw : bil gx u (mv Tx w) = 0 := by
    rw [hsa u w, hTu, bil_smul_left, ho, mul_zero]
  have hm : m = 0 := by
    have := congrArg (bil gx u) h1
    rw [bil_sub_right, bil_sub_right, bil_smul_right, bil_smul_right, hTw, ho, hn,
      bil_zero_right] at this
    linarith
  subst hm
  refine ⟨hgap w ho ?_, rfl⟩
  have e1 : restProjG gx u (mv Tx w) + ε • w = mv Tx w - (-ε) • w - (0 : ℝ) • u := by
    simp only [restProjG, hTw, zero_smul, add_zero, neg_smul, sub_neg_eq_add, sub_zero]
  rw [e1]; exact h1

/-! ## F3: curved implicit function theorem -/

theorem borderedG_contDiffAt {n : ℕ} {g Tm : (I → ℝ) → I → I → ℝ} {x : I → ℝ}
    (hg : ∀ a c, ContDiffAt ℝ n (fun y => g y a c) x)
    (hT : ∀ a c, ContDiffAt ℝ n (fun y => Tm y a c) x) (y : (I → ℝ) × ℝ) :
    ContDiffAt ℝ n (borderedG g Tm) (x, y) := by
  have hTab : ∀ a c, ContDiffAt ℝ n
      (fun p : (I → ℝ) × ((I → ℝ) × ℝ) => Tm p.1 a c) (x, y) :=
    fun a c => (hT a c).comp (x, y) contDiffAt_fst
  have hgab : ∀ a c, ContDiffAt ℝ n
      (fun p : (I → ℝ) × ((I → ℝ) × ℝ) => g p.1 a c) (x, y) :=
    fun a c => (hg a c).comp (x, y) contDiffAt_fst
  have hv : ∀ b, ContDiffAt ℝ n (fun p : (I → ℝ) × ((I → ℝ) × ℝ) => p.2.1 b) (x, y) := by
    intro b
    exact ((contDiff_apply ℝ ℝ b).contDiffAt).comp (x, y)
      (contDiffAt_fst.comp (x, y) contDiffAt_snd)
  have hm : ContDiffAt ℝ n (fun p : (I → ℝ) × ((I → ℝ) × ℝ) => p.2.2) (x, y) :=
    contDiffAt_snd.comp (x, y) contDiffAt_snd
  refine ContDiffAt.prodMk ?_ ?_
  · refine contDiffAt_pi.2 (fun a => ?_)
    have e : (fun p : (I → ℝ) × ((I → ℝ) × ℝ) => (mv (Tm p.1) p.2.1 - p.2.2 • p.2.1) a) =
        fun p => sum4 (fun c => Tm p.1 a c * p.2.1 c) - p.2.2 * p.2.1 a := by
      funext p; simp [mv]
    rw [e]
    have := hTab a; have := hv
    unfold sum4; fun_prop
  · have e : (fun p : (I → ℝ) × ((I → ℝ) × ℝ) => bil (g p.1) p.2.1 p.2.1 + 1) =
        fun p => sum4 (fun a => sum4 (fun c => g p.1 a c * p.2.1 a * p.2.1 c)) + 1 := rfl
    rw [e]
    have := hgab; have := hv
    unfold sum4; fun_prop

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
      (∀ᶠ p in 𝓝 (x0, (u0, -ε0)), borderedG g Tm p = 0 → p.2 = (u p.1, -ε p.1)) := by
  obtain ⟨hE0, hN0, hF0⟩ := h0
  have hn0 : ((n : WithTop ℕ∞)) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  have hninf : ((n : WithTop ℕ∞)) ≠ ∞ := by simp
  set p0 : (I → ℝ) × ((I → ℝ) × ℝ) := (x0, (u0, -ε0)) with hp0
  have hcd : ContDiffAt ℝ n (borderedG g Tm) p0 := borderedG_contDiffAt hg hT _
  -- regularity of the data near x0
  have evReg : ∀ᶠ x in 𝓝 x0, (∀ a c, ContDiffAt ℝ n (fun y => g y a c) x) ∧
      (∀ a c, ContDiffAt ℝ n (fun y => Tm y a c) x) := by
    refine Filter.Eventually.and ?_ ?_
    · exact Filter.eventually_all.2 (fun a => Filter.eventually_all.2
        (fun c => (hg a c).eventually hninf))
    · exact Filter.eventually_all.2 (fun a => Filter.eventually_all.2
        (fun c => (hT a c).eventually hninf))
  have hinv : (fderiv ℝ (borderedG g Tm) p0 ∘L
      ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)).IsInvertible := by
    apply G04A.isInvertible_of_injective
    rw [injective_iff_map_eq_zero]
    rintro ⟨w, m⟩ hwm
    rw [borderedG_fderiv_inr (hgsym x0) (hcd.differentiableAt (by exact_mod_cast hn0))] at hwm
    obtain ⟨hw, hm⟩ := borderedG_inj hsa0 ⟨hE0, hN0, hF0⟩ hgap0 w m hwm
    simp [hw, hm]
  set ψ := hcd.implicitFunction hn0 hinv with hψdef
  have hψ0 : ψ x0 = (u0, -ε0) := hcd.implicitFunction_apply_self hn0 hinv
  have hψcd : ContDiffAt ℝ n ψ x0 := hcd.contDiffAt_implicitFunction hn0 hinv
  have ev1 : ∀ᶠ x in 𝓝 x0, borderedG g Tm (x, ψ x) = borderedG g Tm p0 :=
    hcd.eventually_apply_implicitFunction hn0 hinv
  have ev2 : ∀ᶠ x in 𝓝 x0, ContDiffAt ℝ n ψ x := hψcd.eventually hninf
  have ev3 : ∀ᶠ x in 𝓝 x0, 0 < (ψ x).1 0 := by
    have hc : ContinuousAt (fun x => (ψ x).1 0) x0 :=
      (continuous_apply 0).continuousAt.comp (continuousAt_fst.comp hψcd.continuousAt)
    have ht := hc.tendsto
    simp only [hψ0] at ht
    exact ht.eventually_const_lt hF0
  have ev5 : ∀ᶠ x in 𝓝 x0, (fderiv ℝ (borderedG g Tm) (x, ψ x) ∘L
      ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)).IsInvertible := by
    have hc : ContinuousAt (fun x => fderiv ℝ (borderedG g Tm) (x, ψ x) ∘L
        ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)) x0 := by
      have hpair : ContinuousAt (fun x => (x, ψ x)) x0 :=
        continuousAt_id.prodMk hψcd.continuousAt
      have hfd : ContinuousAt (fderiv ℝ (borderedG g Tm)) (x0, ψ x0) := by
        rw [hψ0]; exact hcd.continuousAt_fderiv hn0
      exact (ContinuousAt.comp (f := fun x => (x, ψ x)) hfd hpair).clm_comp continuousAt_const
    have hmem : Set.range ((↑) : (((I → ℝ) × ℝ) ≃L[ℝ] ((I → ℝ) × ℝ)) →
        ((I → ℝ) × ℝ) →L[ℝ] ((I → ℝ) × ℝ)) ∈
        𝓝 (fderiv ℝ (borderedG g Tm) (x0, ψ x0) ∘L
          ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)) := by
      apply ContinuousLinearEquiv.isOpen.mem_nhds
      rw [hψ0]; exact hinv
    exact hc.preimage_mem_nhds hmem
  obtain ⟨V, hVprop, hVopen, hx0V⟩ :=
    eventually_nhds_iff.1 (ev1.and (ev2.and (ev3.and (evReg.and ev5))))
  have hbp0 : borderedG g Tm p0 = 0 := by
    simp only [borderedG, hp0, hE0]
    ext a <;> simp [hN0]
  have hloc := hcd.eventually_apply_eq_iff_implicitFunction hn0 hinv
  refine ⟨V, fun x => (ψ x).1, fun x => -(ψ x).2, hVopen, hx0V, by simp [hψ0], by simp [hψ0],
    ?_, ?_, ?_⟩
  · intro x hx
    exact ⟨contDiffAt_fst.comp x (hVprop x hx).2.1,
      (contDiffAt_snd.comp x (hVprop x hx).2.1).neg⟩
  · intro x hx
    have hb := (hVprop x hx).1
    rw [hbp0] at hb
    have hb1 : mv (Tm x) (ψ x).1 - (ψ x).2 • (ψ x).1 = 0 := congrArg Prod.fst hb
    have hb2 : bil (g x) (ψ x).1 (ψ x).1 + 1 = 0 := congrArg Prod.snd hb
    refine ⟨⟨?_, by linarith, (hVprop x hx).2.2.1⟩, ?_⟩
    · rw [neg_neg]; exact sub_eq_zero.mp hb1
    · intro w ho hL
      have hreg := (hVprop x hx).2.2.2.1
      have hdiff : DifferentiableAt ℝ (borderedG g Tm) (x, ψ x) :=
        (borderedG_contDiffAt hreg.1 hreg.2 (ψ x)).differentiableAt (by exact_mod_cast hn0)
      have hinj := ((hVprop x hx).2.2.2.2).injective
      set mm : ℝ := -bil (g x) (ψ x).1 (mv (Tm x) w) with hmm
      have hz : (fderiv ℝ (borderedG g Tm) (x, ψ x) ∘L
          ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)) (w, mm) =
          (fderiv ℝ (borderedG g Tm) (x, ψ x) ∘L
            ContinuousLinearMap.inr ℝ (I → ℝ) ((I → ℝ) × ℝ)) 0 := by
        rw [map_zero, borderedG_fderiv_inr (hgsym x) hdiff]
        have e1 : mv (Tm x) w - (ψ x).2 • w - mm • (ψ x).1 =
            restProjG (g x) (ψ x).1 (mv (Tm x) w) + (-(ψ x).2) • w := by
          simp only [restProjG, hmm, neg_smul, sub_neg_eq_add]
          abel
        rw [e1, hL, ho]
        simp
      have := hinj hz
      exact congrArg Prod.fst this
  · filter_upwards [hloc] with p hp hB
    rw [hbp0] at hp
    have := hp.1 hB
    rw [← this, neg_neg]

/-! ## F4: pointwise uniqueness of the future unit timelike eigenvector -/

/-- Rest-space positivity at a Lorentzian point: `g(u,u) < 0`, `g(u,w) = 0`, `w ≠ 0` ⇒ `g(w,w) > 0`. -/
theorem rest_pos (gx : I → I → ℝ) (hgs : ∀ a c, gx a c = gx c a) (hL : Lorentzian gx)
    (u w : I → ℝ) (hu : bil gx u u < 0) (ho : bil gx u w = 0) (hw : w ≠ 0) :
    0 < bil gx w w := by
  by_contra hneg0
  have hneg : bil gx w w ≤ 0 := not_lt.mp hneg0
  set α := bil gx e0 w with hα
  set β := bil gx e0 u with hβ
  by_cases hb : β = 0
  · have hu0 : u ≠ 0 := by
      intro h; rw [h, bil_zero_right] at hu; exact lt_irrefl _ hu
    have := hL.2 u hu0 hb
    linarith
  · set z : I → ℝ := α • u - β • w with hz
    have hz0 : bil gx e0 z = 0 := by
      rw [hz, bil_sub_right, bil_smul_right, bil_smul_right]; ring
    have hzne : z ≠ 0 := by
      intro hz'
      have h1 := congrArg (bil gx u) hz'
      rw [hz, bil_sub_right, bil_smul_right, bil_smul_right, ho, bil_zero_right] at h1
      have hαz : α = 0 := by
        have : α * bil gx u u = 0 := by linarith
        rcases mul_eq_zero.mp this with h | h
        · exact h
        · linarith
      apply hw
      have h2 : β • w = 0 := by
        have := hz'; rw [hz, hαz, zero_smul, zero_sub, neg_eq_zero] at this; exact this
      rcases smul_eq_zero.mp h2 with h | h
      · exact absurd h hb
      · exact h
    have hpos := hL.2 z hzne hz0
    have hexp : bil gx z z = α ^ 2 * bil gx u u + β ^ 2 * bil gx w w := by
      rw [hz]
      simp only [bil_sub_left, bil_sub_right, bil_smul_left, bil_smul_right]
      rw [bil_comm gx hgs w u, ho]
      ring
    have h1 : α ^ 2 * bil gx u u ≤ 0 := mul_nonpos_of_nonneg_of_nonpos (sq_nonneg _) hu.le
    have h2 : β ^ 2 * bil gx w w ≤ 0 := mul_nonpos_of_nonneg_of_nonpos (sq_nonneg _) hneg
    linarith

theorem unique_future_eigen (gx Tx : I → I → ℝ) (hgs : ∀ a c, gx a c = gx c a)
    (hL : Lorentzian gx) (hsa : SelfAdjG gx Tx) (u v : I → ℝ) (ε μ : ℝ)
    (hu : FutureUnitEigenG gx Tx u ε) (hgap : RestGapG gx Tx u ε)
    (hv : FutureUnitEigenG gx Tx v μ) : v = u ∧ μ = ε := by
  obtain ⟨hTu, hnu, hfu⟩ := hu
  obtain ⟨hTv, hnv, hfv⟩ := hv
  have hv0 : v ≠ 0 := by
    intro h; rw [h] at hfv; simp at hfv
  have huv : bil gx u v ≠ 0 := by
    intro h0
    have := rest_pos gx hgs hL u v (by linarith) h0 hv0
    linarith
  have hme : μ = ε := by
    have h1 := hsa u v
    rw [hTu, hTv, bil_smul_right, bil_smul_left] at h1
    have : (ε - μ) * bil gx u v = 0 := by linarith
    rcases mul_eq_zero.mp this with h | h
    · linarith
    · exact absurd h huv
  subst hme
  set w := v + bil gx u v • u with hw
  have how : bil gx u w = 0 := by
    rw [hw, bil_add_right, bil_smul_right, hnu]; ring
  have hTw : mv Tx w = (-μ) • w := by
    rw [hw, mv_add, mv_smul, hTu, hTv, smul_add, smul_smul, smul_smul, mul_comm]
  have hw0 : w = 0 := hgap w how (by
    rw [hTw]
    simp only [restProjG, bil_smul_right, how, mul_zero, zero_smul, add_zero]
    rw [← add_smul]; simp)
  have hvu : v = (-(bil gx u v)) • u := by
    have : v + bil gx u v • u = 0 := hw0
    rw [neg_smul, eq_neg_iff_add_eq_zero]; exact this
  have hsq : bil gx u v * bil gx u v = 1 := by
    have := hnv
    rw [hvu, bil_smul_left, bil_smul_right, hnu] at this
    linarith
  have hneg : bil gx u v < 0 := by
    have h0 := congrFun hvu 0
    simp only [Pi.smul_apply, smul_eq_mul] at h0
    by_contra hc
    replace hc := not_lt.mp hc
    have : -(bil gx u v) * u 0 ≤ 0 := by
      have := mul_nonneg hc hfu.le; linarith
    linarith
  have hm1 : bil gx u v = -1 := by nlinarith
  refine ⟨?_, rfl⟩
  rw [hvu, hm1]; simp

end G05BIFT
