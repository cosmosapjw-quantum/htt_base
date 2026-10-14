import Mathlib
import G05BJet
import G05BIFT
import G05BSymm

/-!
# G05-B, module 4: one construction — formal jet, actual metric, actual eigenfield

For `b > 0`, `Λ < 3b`, `κ > 0`, every real `k` (the 4×3 block `k μ i`, `i ≠ 0`) and every finite
`n ≥ 1`:
* the actual metric is the cubic member `gCub b k = e^{2φ_0}η + H` (EF3 eq. (6)), with the
  accepted C03 right-inverse coefficients `q = −6b k_0·`, `M = −6b k_··ᵀ`;
* its 2-jet at 0 is that of `g^(0)` (`j²H = 0`), and its actual stress has
  `∂_0 T_0i(0) = q_i/κ`, `∂_j T_0i(0) = M_ij/κ` (G05BJet);
* the actual energy eigenfield `u` is the curved IFT branch (G05BIFT) of the mixed actual stress;
* on a member-dependent ball: Lorentzian, strict DEC (G05-A), future unit eigenvector, gap, `C^n`;
* the covariant rates of the actual eigenfield at 0 are `g(∇_{E_μ}u, E_i)(0) = k μ i`.
`EF3_local_germ_unique` adds global uniqueness of the future unit timelike eigenvector at every point
of the ball (Ricci symmetry from G05BSymm + Lorentzian rest-space positivity).
-/

namespace G05BGerm

open G05AConformalDEC G05BCubicDEC G05BJet G05BIFT G05BSymm
open scoped Topology

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

/-! ## Regularity of the actual mixed stress of the cubic member -/

theorem ginv_cub_cd (b : ℝ) (k : I → I → ℝ) (m : ℕ) (a c : I) :
    ContDiffAt ℝ m (fun y => ginv (gCub b k) y a c) 0 := by
  unfold ginv
  exact contDiffAt_inv_entry (toMat (gCub b k)) (fun i j => gCub_contDiff b k i j) 0
    (det_cub b k) a c

theorem Gam_cub_cd (b : ℝ) (k : I → I → ℝ) (n : ℕ) (a i j : I) :
    ContDiffAt ℝ (n + 1) (fun y => Gam (gCub b k) y a i j) 0 := by
  have h1 : ∀ a c, ContDiffAt ℝ (n + 1) (fun y => ginv (gCub b k) y a c) 0 := by
    intro a c
    have := ginv_cub_cd b k (n + 1) a c
    exact_mod_cast this
  have h2 : ∀ c a e, ContDiffAt ℝ (n + 1) (fun y => dg (gCub b k) c a e y) 0 :=
    fun c a e => (pd_contDiff_succ (m := n + 1) (gCub_contDiff b k a e) c).contDiffAt.of_le
      (by exact_mod_cast le_rfl)
  unfold Gam sum4
  fun_prop

theorem stress_cub_cd (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (n : ℕ) (a c : I) :
    ContDiffAt ℝ n (fun y => stress (gCub b k) Λ κ y a c) 0 := by
  have h1 : ∀ a c, ContDiffAt ℝ n (fun y => ginv (gCub b k) y a c) 0 :=
    fun a c => ginv_cub_cd b k n a c
  have h2 : ∀ a i j, ContDiffAt ℝ n (fun y => Gam (gCub b k) y a i j) 0 :=
    fun a i j => (Gam_cub_cd b k n a i j).of_le (by exact_mod_cast Nat.le_succ n)
  have h3 : ∀ d a i j, ContDiffAt ℝ n (fun y => dGam (gCub b k) d a i j y) 0 :=
    fun d a i j => pd_contDiffAt_succ (Gam_cub_cd b k n a i j) d
  have h4 : ∀ a c, ContDiffAt ℝ n (fun y => gCub b k y a c) 0 :=
    fun a c => (gCub_contDiff b k a c).contDiffAt
  unfold stress Ein Rsc Ric sum4
  fun_prop

theorem Tmix_cd (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (n : ℕ) (a c : I) :
    ContDiffAt ℝ n (fun y => Tmix b k Λ κ y a c) 0 := by
  have h1 := ginv_cub_cd b k n
  have h2 := stress_cub_cd b k Λ κ n
  unfold Tmix sum4
  fun_prop

/-! ## Base point -/

theorem ginv_cub0 (b : ℝ) (k : I → I → ℝ) (a c : I) : ginv (gCub b k) 0 a c = eta a c :=
  ginv0 (gCub b k) (gCub_origin_eta b k) a c

theorem Tmix_origin (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (a c : I) :
    Tmix b k Λ κ 0 a c = if a = c then (if a = 0 then -((6*b - Λ)/κ) else Λ/κ) else 0 := by
  simp only [Tmix, ginv_cub0, stress_cub_origin]
  fin_cases a <;> fin_cases c <;> simp [sum4, eta, delta, sig, diagT]

theorem e0_eq_stdFrame : stdFrame 0 = e0 := by
  funext a; fin_cases a <;> simp [stdFrame, e0]

theorem eigen_origin (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) :
    FutureUnitEigenG (gCub b k 0) (Tmix b k Λ κ 0) e0 ((6*b - Λ)/κ) := by
  refine ⟨?_, ?_, ?_⟩
  · funext a
    simp only [mv, Tmix_origin]
    fin_cases a <;> simp [sum4, e0]
  · rw [gCub_origin_eta]; simp [bil, sum4, eta, delta, sig, e0]
  · simp [e0]

theorem gap_origin (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (hb : 0 < b) (hκ : 0 < κ) :
    RestGapG (gCub b k 0) (Tmix b k Λ κ 0) e0 ((6*b - Λ)/κ) := by
  rw [gCub_origin_eta]
  intro w ho hL
  have hw0 : w 0 = 0 := by
    simp [bil, sum4, eta, delta, sig, e0] at ho; linarith
  have hgapv : (6*b - Λ)/κ + Λ/κ ≠ 0 := by
    have : (6*b - Λ)/κ + Λ/κ = 6*b/κ := by ring
    rw [this]; positivity
  have hc : ∀ i : I, i ≠ 0 → ((6*b - Λ)/κ + Λ/κ) * w i = 0 := by
    intro i hi
    have := congrFun hL i
    simp only [restProjG, mv, Tmix_origin, Pi.add_apply, Pi.smul_apply, smul_eq_mul,
      Pi.zero_apply] at this
    fin_cases i
    · exact absurd rfl hi
    all_goals simp [sum4, e0, bil, eta, delta, sig, hw0] at this ⊢; linarith
  funext a
  by_cases ha : a = 0
  · subst ha; simpa using hw0
  · have := hc a ha
    rcases mul_eq_zero.mp this with h | h
    · exact absurd h hgapv
    · simpa using h

/-! ## Derivative of the actual eigenfield at the origin -/

theorem pd_component {u : (I → ℝ) → I → ℝ} {x : I → ℝ} (hu : DifferentiableAt ℝ u x)
    (i μ : I) : pd (fun y => u y i) μ x = fderiv ℝ u x (Pi.single μ 1) i := by
  have h := hasFDerivAt_pi'.1 hu.hasFDerivAt i
  unfold pd
  rw [h.fderiv]
  rfl

theorem dTmix_origin (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (μ i : I) :
    pd (fun y => Tmix b k Λ κ y i 0) μ 0 = CAS05C03.closedDG b k μ i 0 / κ := by
  have hgi : ∀ a c, DifferentiableAt ℝ (fun y => ginv (gCub b k) y a c) 0 :=
    fun a c => (ginv_cub_cd b k 1 a c).differentiableAt (by norm_num)
  have hst : ∀ a c, DifferentiableAt ℝ (fun y => stress (gCub b k) Λ κ y a c) 0 :=
    fun a c => (stress_cub_cd b k Λ κ 1 a c).differentiableAt (by norm_num)
  have hdg := dginv0 (gCub b k) (gCub_smooth3 b k) (gCub_origin_eta b k) (cub_crit b k)
  unfold Tmix
  rw [pd_sum4 (F := fun e y => ginv (gCub b k) y i e * stress (gCub b k) Λ κ y e 0)
    (fun e => by have := hgi i e; have := hst e 0; fun_prop)]
  simp only [sum4]
  rw [pd_mul μ (hgi i 0) (hst 0 0), pd_mul μ (hgi i 1) (hst 1 0), pd_mul μ (hgi i 2) (hst 2 0),
    pd_mul μ (hgi i 3) (hst 3 0)]
  simp only [hdg, ginv_cub0, dStress_cub, mul_zero, add_zero]
  fin_cases i <;> simp [eta, delta, sig]

theorem rate_origin (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) (hb : 0 < b) (hκ : 0 < κ)
    (u : (I → ℝ) → I → ℝ) (ε : (I → ℝ) → ℝ) (V : Set (I → ℝ)) (hV : V ∈ 𝓝 (0 : I → ℝ))
    (hu : DifferentiableAt ℝ u 0) (hε : DifferentiableAt ℝ ε 0)
    (heig : ∀ x ∈ V, FutureUnitEigenG (gCub b k x) (Tmix b k Λ κ x) (u x) (ε x))
    (hu0 : u 0 = e0) (hε0 : ε 0 = (6*b - Λ)/κ) (μ i : I) (hi : i ≠ 0) :
    rate (gCub b k) u 0 stdFrame μ i = k μ i := by
  have huc : ∀ c, DifferentiableAt ℝ (fun y => u y c) 0 := differentiableAt_pi.1 hu
  have hT : ∀ a c, DifferentiableAt ℝ (fun y => Tmix b k Λ κ y a c) 0 :=
    fun a c => (Tmix_cd b k Λ κ 1 a c).differentiableAt (by norm_num)
  -- differentiate the eigen-equation, component i
  have hev : ∀ᶠ y in 𝓝 (0 : I → ℝ),
      sum4 (fun c => Tmix b k Λ κ y i c * u y c) + ε y * u y i = 0 := by
    filter_upwards [hV] with y hy
    have := congrFun (heig y hy).1 i
    simp only [mv, Pi.smul_apply, smul_eq_mul] at this
    rw [this]; ring
  have hd := pd_congr_nhds hev μ
  rw [pd_const, pd_add μ (by have := hT i; have := huc; unfold sum4; fun_prop)
      (by have := huc i; fun_prop),
    pd_sum4 (F := fun c y => Tmix b k Λ κ y i c * u y c)
      (fun c => by have := hT i c; have := huc c; fun_prop),
    pd_mul μ hε (huc i)] at hd
  simp only [sum4] at hd
  rw [pd_mul μ (hT i 0) (huc 0), pd_mul μ (hT i 1) (huc 1), pd_mul μ (hT i 2) (huc 2),
    pd_mul μ (hT i 3) (huc 3)] at hd
  simp only [Tmix_origin, hu0, hε0, e0] at hd
  have hdT := dTmix_origin b k Λ κ μ i
  -- the rate is the coordinate derivative of the component (Γ(0) = 0, g(0) = η)
  have hGam0 : ∀ a c e, Gam (gCub b k) 0 a c e = 0 := Gam_crit (gCub b k) (cub_crit b k)
  have hrate : rate (gCub b k) u 0 stdFrame μ i = pd (fun y => u y i) μ 0 := by
    rw [pd_component hu i μ]
    simp only [rate, covD, hGam0, zero_mul, sum4, add_zero, gCub_origin_eta, stdFrame]
    fin_cases i
    · exact absurd rfl hi
    all_goals simp [bil, sum4, eta, delta, sig]
  rw [hrate]
  have hgap : (6*b - Λ)/κ + Λ/κ = 6*b/κ := by ring
  have hκ0 : κ ≠ 0 := hκ.ne'
  have hb0 : b ≠ 0 := hb.ne'
  fin_cases i
  · exact absurd rfl hi
  all_goals
    simp at hd hdT
    rw [hdT] at hd
    fin_cases μ <;>
      simp [CAS05C03.closedDG, CAS05C03.q, CAS05C03.M] at hd ⊢ <;>
      field_simp at hd ⊢ <;> linarith

/-! ## Lorentzian points are nondegenerate -/

theorem det_ne_of_lorentzian (gx : I → I → ℝ) (hL : Lorentzian gx) :
    (Matrix.of gx).det ≠ 0 := by
  intro h
  obtain ⟨w, hw0, hw⟩ := Matrix.exists_mulVec_eq_zero_iff.2 h
  have hbil : ∀ v, bil gx v w = 0 := by
    intro v
    have : ∀ a, sum4 (fun c => gx a c * w c) = 0 := by
      intro a
      have := congrFun hw a
      simp only [Matrix.mulVec, dotProduct, Fin.sum_univ_four, Matrix.of_apply,
        Pi.zero_apply] at this
      simp only [sum4]; linarith
    have e : bil gx v w = sum4 (fun a => v a * sum4 (fun c => gx a c * w c)) := by
      simp only [bil, sum4]; ring
    rw [e]; simp [this, sum4]
  have := hL.2 w hw0 (hbil e0)
  rw [hbil w] at this
  exact lt_irrefl _ this

/-! ## G1, G2, N1, N2 -/

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
        borderedG (gCub b k) (Tmix b k Λ κ) p = 0 → p.2 = (u p.1, -ε p.1)) := by
  have hsa0 : SelfAdjG (gCub b k 0) (Tmix b k Λ κ 0) :=
    selfAdj_mixed (gCub b k) (fun a c => gCub_contDiff b k a c) (fun y a c => gCub_symmetric b k y a c)
      0 (det_cub b k) Λ κ
  obtain ⟨V, u, ε, hVo, h0V, hu0, hε0, hreg, heig, hloc⟩ :=
    curved_smooth_eigenline n hn (gCub b k) (Tmix b k Λ κ) 0
      (fun a c => (gCub_contDiff b k a c).contDiffAt) (fun a c => Tmix_cd b k Λ κ n a c)
      (fun x a c => gCub_symmetric b k x a c) hsa0 e0 ((6*b - Λ)/κ)
      (eigen_origin b k Λ κ) (gap_origin b k Λ κ hb hκ)
  obtain ⟨r1, hr1, hB2⟩ := strict_dec_neighborhood_cubic b k Λ κ hb hΛ hκ
  obtain ⟨r2, hr2, hball⟩ := Metric.isOpen_iff.1 hVo 0 h0V
  have hn0 : (n : WithTop ℕ∞) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  have hud : DifferentiableAt ℝ u 0 := (hreg 0 h0V).1.differentiableAt hn0
  have hεd : DifferentiableAt ℝ ε 0 := (hreg 0 h0V).2.differentiableAt hn0
  refine ⟨min r1 r2, u, ε, lt_min hr1 hr2, gCub_origin b k,
    fun c a e => by rw [cub_crit, conf_crit], cub_jet b k, ?_, hu0, hε0,
    stress_cub_origin b k Λ κ, by rw [hu0, e0_eq_stdFrame], ?_,
    fun μ i hi => dStress_cub_0i b k Λ κ μ i hi,
    fun μ i hi => rate_origin b k Λ κ hb hκ u ε V (hVo.mem_nhds h0V) hud hεd
      (fun x hx => (heig x hx).1) hu0 hε0 μ i hi, hloc⟩
  · intro x hx
    have hxV : x ∈ V := hball (by
      rw [Metric.mem_ball, dist_zero_right]; exact lt_of_lt_of_le hx (min_le_right _ _))
    have hB := hB2 x (lt_of_lt_of_le hx (min_le_left _ _))
    exact ⟨hB.1, hB.2, (heig x hxV).1, (heig x hxV).2, (hreg x hxV).1, (hreg x hxV).2⟩
  · intro μ ν
    rw [gCub_origin_eta]
    fin_cases μ <;> fin_cases ν <;> simp [bil, sum4, eta, delta, sig, stdFrame, Pi.single_apply]

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
      (∀ μ i, i ≠ 0 → rate (gCub b k) u 0 stdFrame μ i = k μ i) := by
  obtain ⟨r, u, ε, hr, -, -, -, hball, hu0, hε0, -, -, -, -, hrate, -⟩ :=
    EF3_local_germ b Λ κ hb hΛ hκ k n hn
  refine ⟨r, u, ε, hr, ?_, hu0, hε0, hrate⟩
  intro x hx
  obtain ⟨hL, hD, hE, hG, hcu, hce⟩ := hball x hx
  refine ⟨hL, hD, hE, hG, hcu, hce, ?_⟩
  intro v μ hv
  have hdet : (toMat (gCub b k) x).det ≠ 0 := det_ne_of_lorentzian _ hL
  have hsa : SelfAdjG (gCub b k x) (Tmix b k Λ κ x) :=
    selfAdj_mixed (gCub b k) (fun a c => gCub_contDiff b k a c)
      (fun y a c => gCub_symmetric b k y a c) x hdet Λ κ
  exact unique_future_eigen (gCub b k x) (Tmix b k Λ κ x) (gCub_symmetric b k x) hL hsa
    (u x) v (ε x) μ hE hG hv

theorem gap_fails_without_isolation (k : I → I → ℝ) (Λ κ : ℝ) (hκ : 0 < κ) :
    ¬ RestGapG (gCub 0 k 0) (Tmix 0 k Λ κ 0) e0 ((6*0 - Λ)/κ) := by
  intro h
  rw [gCub_origin_eta] at h
  have hw := h (Pi.single 1 1) (by simp [bil, sum4, eta, delta, sig, e0, Pi.single_apply]) (by
    funext a
    simp only [restProjG, mv, Tmix_origin, Pi.add_apply, Pi.smul_apply, smul_eq_mul,
      Pi.zero_apply]
    fin_cases a <;> simp [sum4, bil, eta, delta, sig, e0, Pi.single_apply] <;> ring)
  have := congrFun hw 1
  simp at this

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
      rate (gCub b k) u 0 stdFrame 0 1 ≠ rate (gCub b k') u' 0 stdFrame 0 1 := by
  set k : I → I → ℝ := fun _ _ => 0
  set k' : I → I → ℝ := fun μ i => if μ = 0 ∧ i = 1 then 1 else 0 with hk'
  obtain ⟨r, u, ε, hr, -, -, -, hb1, hu0, -, -, -, -, -, hrate, -⟩ :=
    EF3_local_germ b Λ κ hb hΛ hκ k n hn
  obtain ⟨r', u', ε', hr', -, -, -, hb1', hu0', -, -, -, -, -, hrate', -⟩ :=
    EF3_local_germ b Λ κ hb hΛ hκ k' n hn
  refine ⟨k, k', u, u', ε, ε', r, r', hr, hr', fun x hx => (hb1 x hx).2.2.1,
    fun x hx => (hb1' x hx).2.2.1, by rw [hu0, hu0'], by rw [gCub_origin, gCub_origin],
    fun c a e => by rw [cub_crit, cub_crit], fun d c a e => by rw [cub_jet, cub_jet], ?_⟩
  rw [hrate 0 1 (by decide), hrate' 0 1 (by decide)]
  simp [k, hk']

end G05BGerm
