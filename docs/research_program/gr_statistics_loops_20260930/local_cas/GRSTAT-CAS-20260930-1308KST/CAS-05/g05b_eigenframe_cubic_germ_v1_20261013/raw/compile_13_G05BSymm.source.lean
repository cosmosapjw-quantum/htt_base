import Mathlib
import G05BJet
import G05BIFT

/-!
# G05-B, module 3: symmetry of the ACTUAL Ricci tensor and self-adjointness of the mixed stress

The G05-A Ricci tensor `R_ai = ∂_c Γ^c_{ia} − ∂_i Γ^c_{ca} + ΓΓ − ΓΓ` is defined from actual
derivatives; its symmetry is not built in.  It is proved here for a symmetric `C^2` metric field at
every point where `det g ≠ 0`:
* `Γ^c_{ia} = Γ^c_{ai}` (from symmetry of `g`);
* the `ΓΓ` part is symmetric by re-indexing;
* `Σ_c Γ^c_{ca} = ½ g^{kd} ∂_a g_{kd}`; its derivative is symmetric by the symmetric second
  derivative of `g` (Mathlib `ContDiffAt.isSymmSndFDerivAt`) and by the derivative of the inverse
  `∂g^{-1} = −g^{-1}(∂g)g^{-1}` (derived from `g^{-1}g = 1` near the point).
-/

namespace G05BSymm

open G05AConformalDEC G05BCubicDEC G05BJet G05BIFT
open scoped Topology

theorem pd_pd_comm {f : (I → ℝ) → ℝ} {x : I → ℝ} (hf : ContDiffAt ℝ 2 f x) (a i : I) :
    pd (fun z => pd f a z) i x = pd (fun z => pd f i z) a x := by
  have hs := hf.isSymmSndFDerivAt (by simp)
  have hd : DifferentiableAt ℝ (fderiv ℝ f) x :=
    (hf.fderiv_right (m := 1) (by norm_num)).differentiableAt (by norm_num)
  unfold pd
  rw [fderiv_clm_apply hd (differentiableAt_const _), fderiv_clm_apply hd (differentiableAt_const _)]
  simp only [fderiv_const, Pi.zero_apply, ContinuousLinearMap.comp_zero, add_zero,
    ContinuousLinearMap.flip_apply]
  exact hs _ _

/-- Exchange of a doubly indexed sum. -/
theorem sum4_comm (F : I → I → ℝ) :
    sum4 (fun c => sum4 (fun e => F c e)) = sum4 (fun e => sum4 (fun c => F c e)) := by
  simp only [sum4]; ring

theorem GG_symm (G : I → I → I → ℝ) (hG : ∀ c i e, G c i e = G c e i) (a i : I) :
    sum4 (fun c => sum4 (fun e => G c c e * G e i a - G c i e * G e c a)) =
    sum4 (fun c => sum4 (fun e => G c c e * G e a i - G c a e * G e c i)) := by
  have h1 : sum4 (fun c => sum4 (fun e => G c a e * G e c i)) =
      sum4 (fun c => sum4 (fun e => G c i e * G e c a)) := by
    rw [sum4_comm]
    congr 1; funext e; congr 1; funext c
    rw [hG c a e, hG e c i]; ring
  have h2 : ∀ c e, G e i a = G e a i := fun c e => hG e i a
  have e1 : ∀ (P Q : I → I → ℝ), sum4 (fun c => sum4 (fun e => P c e - Q c e)) =
      sum4 (fun c => sum4 (fun e => P c e)) - sum4 (fun c => sum4 (fun e => Q c e)) := by
    intro P Q; simp only [sum4]; ring
  rw [e1, e1, h1]
  simp only [h2 0 0]
  congr 2; funext c; congr 1; funext e; rw [hG e i a]

section Sym

variable (g : (I → ℝ) → I → I → ℝ) (hg : ∀ a c, ContDiff ℝ 2 (fun y => g y a c))
  (hsym : ∀ y a c, g y a c = g y c a)

include hsym in
theorem dg_symm (c a e : I) (y : I → ℝ) : dg g c a e y = dg g c e a y := by
  unfold dg
  have : (fun z => g z a e) = fun z => g z e a := funext fun z => hsym z a e
  rw [this]

include hsym in
theorem ginv_symm (y : I → ℝ) (a c : I) : ginv g y a c = ginv g y c a := by
  unfold ginv
  have ht : (toMat g y)ᵀ = toMat g y := by
    ext i j; simp only [Matrix.transpose_apply, toMat, Matrix.of_apply]; exact hsym y j i
  have := congrFun (congrFun (Matrix.transpose_nonsing_inv (toMat g y)) c) a
  rw [ht, Matrix.transpose_apply] at this
  exact this

include hsym in
theorem Gam_symm (y : I → ℝ) (a i j : I) : Gam g y a i j = Gam g y a j i := by
  unfold Gam
  simp only [sum4]
  rw [dg_symm g hsym 0 i j y, dg_symm g hsym 1 i j y, dg_symm g hsym 2 i j y,
    dg_symm g hsym 3 i j y]
  ring

include hsym in
theorem dGam_symm (d a i j : I) (y : I → ℝ) : dGam g d a i j y = dGam g d a j i y := by
  unfold dGam
  have : (fun z => Gam g z a i j) = fun z => Gam g z a j i := funext fun z => Gam_symm g hsym z a i j
  rw [this]

include hsym in
/-- Contracted Christoffel symbol: `Σ_k Γ^k_{ka} = ½ Σ_{k,d} g^{kd} ∂_a g_{kd}`. -/
theorem trGam (z : I → ℝ) (a : I) :
    sum4 (fun k => Gam g z k k a) =
      (1 / 2 : ℝ) * sum4 (fun k => sum4 (fun d => ginv g z k d * dg g a k d z)) := by
  have hcancel : sum4 (fun k => sum4 (fun d => ginv g z k d * dg g k a d z)) =
      sum4 (fun k => sum4 (fun d => ginv g z k d * dg g d k a z)) := by
    rw [sum4_comm]
    congr 1; funext d; congr 1; funext k
    rw [ginv_symm g hsym z k d, dg_symm g hsym d k a z]
  have e1 : sum4 (fun k => Gam g z k k a) = (1 / 2 : ℝ) * (
      sum4 (fun k => sum4 (fun d => ginv g z k d * dg g k a d z)) +
      sum4 (fun k => sum4 (fun d => ginv g z k d * dg g a k d z)) -
      sum4 (fun k => sum4 (fun d => ginv g z k d * dg g d k a z))) := by
    simp only [Gam, sum4]; ring
  rw [e1, hcancel]; ring

include hg in
theorem dg_contDiff1 (c a e : I) : ContDiff ℝ 1 (fun y => dg g c a e y) :=
  pd_contDiff_succ (m := 1) (hg a e) c

section AtX

variable (x : I → ℝ) (hdet : (toMat g x).det ≠ 0)

include hg hdet in
theorem ginv_cdx (a c : I) : ContDiffAt ℝ 2 (fun y => ginv g y a c) x := by
  unfold ginv
  exact contDiffAt_inv_entry (toMat g) (fun i j => hg i j) x hdet a c

include hg hdet in
theorem ginv_mul_ev (a c : I) :
    ∀ᶠ y in 𝓝 x, sum4 (fun e => ginv g y a e * g y e c) = if a = c then 1 else 0 := by
  have hcont : ContinuousAt (fun y => (toMat g y).det) x :=
    (contDiff_det (toMat g) (fun i j => hg i j)).continuous.continuousAt
  filter_upwards [hcont.eventually_ne hdet] with y hy
  have hm := Matrix.nonsing_inv_mul (toMat g y) (Ne.isUnit hy)
  have := congrFun (congrFun hm a) c
  simp only [Matrix.mul_apply, Fin.sum_univ_four, Matrix.one_apply] at this
  simp only [sum4, ginv]
  rw [← this]
  rfl

include hdet in
theorem g_mul_ginv (e d : I) :
    sum4 (fun d' => g x e d' * ginv g x d' d) = if e = d then 1 else 0 := by
  have hm := Matrix.mul_nonsing_inv (toMat g x) (Ne.isUnit hdet)
  have := congrFun (congrFun hm e) d
  simp only [Matrix.mul_apply, Fin.sum_univ_four, Matrix.one_apply] at this
  simp only [sum4, ginv]
  rw [← this]
  rfl

include hg hdet in
/-- Derivative of the actual inverse metric: `∂_i g^{cd} = −g^{cp} ∂_i g_{pq} g^{qd}`. -/
theorem pd_ginv (i c d : I) :
    pd (fun y => ginv g y c d) i x =
      -sum4 (fun p => sum4 (fun q => ginv g x c p * dg g i p q x * ginv g x q d)) := by
  have hgi : ∀ a c, DifferentiableAt ℝ (fun y => ginv g y a c) x :=
    fun a c => (ginv_cdx g hg x hdet a c).differentiableAt (by norm_num)
  have hgg : ∀ a c, DifferentiableAt ℝ (fun y => g y a c) x :=
    fun a c => (hg a c).differentiable (by norm_num) x
  set D : I → I → ℝ := fun c e => pd (fun y => ginv g y c e) i x with hD
  have key : ∀ c d', sum4 (fun e => g x e d' * D c e) =
      -sum4 (fun e => ginv g x c e * dg g i e d' x) := by
    intro c d'
    have h1 := pd_congr_nhds (ginv_mul_ev g hg x hdet c d') i
    rw [pd_const, pd_sum4 (F := fun e y => ginv g y c e * g y e d')
      (fun e => by have := hgi c e; have := hgg e d'; fun_prop)] at h1
    simp only [sum4] at h1 ⊢
    rw [pd_mul i (hgi c 0) (hgg 0 d'), pd_mul i (hgi c 1) (hgg 1 d'),
      pd_mul i (hgi c 2) (hgg 2 d'), pd_mul i (hgi c 3) (hgg 3 d')] at h1
    simp only [dg, hD]
    linarith
  have gg := g_mul_ginv g x hdet
  calc pd (fun y => ginv g y c d) i x = sum4 (fun e => D c e * (if e = d then 1 else 0)) := by
        simp only [hD]; fin_cases d <;> simp [sum4]
    _ = sum4 (fun e => D c e * sum4 (fun d' => g x e d' * ginv g x d' d)) := by
        simp only [gg]
    _ = sum4 (fun d' => ginv g x d' d * sum4 (fun e => g x e d' * D c e)) := by
        simp only [sum4]; ring
    _ = sum4 (fun d' => ginv g x d' d * -sum4 (fun e => ginv g x c e * dg g i e d' x)) := by
        simp only [key]
    _ = _ := by simp only [sum4]; ring

include hg hsym hdet in
theorem trace_dGam (a c : I) :
    sum4 (fun k => dGam g c k k a x) = sum4 (fun k => dGam g a k k c x) := by
  have hgi : ∀ a c, DifferentiableAt ℝ (fun y => ginv g y a c) x :=
    fun a c => (ginv_cdx g hg x hdet a c).differentiableAt (by norm_num)
  have hdg : ∀ c a e, Differentiable ℝ (fun y => dg g c a e y) :=
    fun c a e => (dg_contDiff1 g hg c a e).differentiable (by norm_num)
  have hGam : ∀ a i j, DifferentiableAt ℝ (fun y => Gam g y a i j) x := by
    intro a i j
    have := hgi; have := fun c a e => (hdg c a e) x
    unfold Gam sum4; fun_prop
  have hF : ∀ a, (fun y => sum4 (fun k => Gam g y k k a)) =
      fun y => (1 / 2 : ℝ) * sum4 (fun k => sum4 (fun d => ginv g y k d * dg g a k d y)) :=
    fun a => funext fun y => trGam g hsym y a
  have hpdF : ∀ a c, sum4 (fun k => dGam g c k k a x) =
      (1 / 2 : ℝ) * sum4 (fun k => sum4 (fun d => ginv g x k d * pd (fun y => dg g a k d y) c x +
        dg g a k d x * pd (fun y => ginv g y k d) c x)) := by
    intro a c
    have e1 : sum4 (fun k => dGam g c k k a x) = pd (fun y => sum4 (fun k => Gam g y k k a)) c x := by
      rw [pd_sum4 (F := fun k y => Gam g y k k a) (fun k => hGam k k a)]
      rfl
    rw [e1, hF a, pd_mul c (differentiableAt_const _)
      (by have := hgi; have := fun c a e => (hdg c a e) x; unfold sum4; fun_prop), pd_const,
      pd_sum4 (F := fun k y => sum4 (fun d => ginv g y k d * dg g a k d y))
        (fun k => by have := hgi; have := fun c a e => (hdg c a e) x; unfold sum4; fun_prop)]
    simp only [zero_mul, add_zero]
    congr 1; congr 1; funext k
    rw [pd_sum4 (F := fun d y => ginv g y k d * dg g a k d y)
      (fun d => by have := hgi k d; have := (hdg a k d) x; fun_prop)]
    congr 1; funext d
    rw [pd_mul c (hgi k d) ((hdg a k d) x)]
  rw [hpdF a c, hpdF c a]
  -- second-derivative symmetry
  have hss : ∀ k d, pd (fun y => dg g a k d y) c x = pd (fun y => dg g c k d y) a x := by
    intro k d
    exact pd_pd_comm ((hg k d).contDiffAt) a c
  simp only [hss, pd_ginv g hg x hdet]
  -- remaining finite identity: symmetric metric and inverse
  have s1 := ginv_symm g hsym x 1 0; have s2 := ginv_symm g hsym x 2 0
  have s3 := ginv_symm g hsym x 2 1; have s4 := ginv_symm g hsym x 3 0
  have s5 := ginv_symm g hsym x 3 1; have s6 := ginv_symm g hsym x 3 2
  have a1 := dg_symm g hsym a 1 0 x; have a2 := dg_symm g hsym a 2 0 x
  have a3 := dg_symm g hsym a 2 1 x; have a4 := dg_symm g hsym a 3 0 x
  have a5 := dg_symm g hsym a 3 1 x; have a6 := dg_symm g hsym a 3 2 x
  have c1 := dg_symm g hsym c 1 0 x; have c2 := dg_symm g hsym c 2 0 x
  have c3 := dg_symm g hsym c 2 1 x; have c4 := dg_symm g hsym c 3 0 x
  have c5 := dg_symm g hsym c 3 1 x; have c6 := dg_symm g hsym c 3 2 x
  have b1 := (dg_symm g hsym a 1 0 x); have hc := hsym
  simp only [sum4]
  simp only [s1, s2, s3, s4, s5, s6, a1, a2, a3, a4, a5, a6, c1, c2, c3, c4, c5, c6]
  ring

include hg hsym hdet in
/-- **S1.** The actual Ricci tensor is symmetric wherever `det g ≠ 0`. -/
theorem Ric_symm (a c : I) : Ric g x a c = Ric g x c a := by
  have hGG := GG_symm (fun c i e => Gam g x c i e) (fun c i e => Gam_symm g hsym x c i e) a c
  have htr := trace_dGam g hg hsym x hdet a c
  have e1 : ∀ a c, Ric g x a c = sum4 (fun k => dGam g k k c a x) - sum4 (fun k => dGam g c k k a x) +
      sum4 (fun k => sum4 (fun e => Gam g x k k e * Gam g x e c a - Gam g x k c e * Gam g x e k a)) := by
    intro a c; simp only [Ric, sum4]; ring
  rw [e1 a c, e1 c a, htr]
  simp only [dGam_symm g hsym _ _ c a x] at *
  rw [hGG]
  congr 2
  simp only [sum4]
  rw [dGam_symm g hsym 0 0 c a x, dGam_symm g hsym 1 1 c a x, dGam_symm g hsym 2 2 c a x,
    dGam_symm g hsym 3 3 c a x]

include hg hsym hdet in
theorem stress_symm (Λ κ : ℝ) (a c : I) : stress g Λ κ x a c = stress g Λ κ x c a := by
  unfold stress Ein
  rw [Ric_symm g hg hsym x hdet a c, hsym x a c]

include hg hsym hdet in
/-- **S2.** The mixed Einstein-defined stress is `g(x)`-self-adjoint. -/
theorem selfAdj_mixed (Λ κ : ℝ) :
    SelfAdjG (g x) (fun a c => sum4 (fun e => ginv g x a e * stress g Λ κ x e c)) := by
  set T := stress g Λ κ x with hT
  have gg := g_mul_ginv g x hdet
  have hrow : ∀ (a : I) (w : I → ℝ), sum4 (fun b => g x a b *
      mv (fun a c => sum4 (fun e => ginv g x a e * T e c)) w b) = sum4 (fun c => T a c * w c) := by
    intro a w
    calc sum4 (fun b => g x a b * mv (fun a c => sum4 (fun e => ginv g x a e * T e c)) w b)
        = sum4 (fun e => sum4 (fun b => g x a b * ginv g x b e) * sum4 (fun c => T e c * w c)) := by
          simp only [mv, sum4]; ring
      _ = sum4 (fun c => T a c * w c) := by
          simp only [gg]; fin_cases a <;> simp [sum4]
  intro v w
  have lhs : bil (g x) v (mv (fun a c => sum4 (fun e => ginv g x a e * T e c)) w) =
      sum4 (fun a => v a * sum4 (fun b => g x a b *
        mv (fun a c => sum4 (fun e => ginv g x a e * T e c)) w b)) := by
    simp only [bil, sum4]; ring
  have rhs : bil (g x) (mv (fun a c => sum4 (fun e => ginv g x a e * T e c)) v) w =
      sum4 (fun b => w b * sum4 (fun a => g x b a *
        mv (fun a c => sum4 (fun e => ginv g x a e * T e c)) v a)) := by
    simp only [bil, sum4]
    rw [hsym x 0 1, hsym x 0 2, hsym x 0 3, hsym x 1 0, hsym x 1 2, hsym x 1 3, hsym x 2 0,
      hsym x 2 1, hsym x 2 3, hsym x 3 0, hsym x 3 1, hsym x 3 2]
    ring
  rw [lhs, rhs]
  simp only [hrow]
  have hTs : ∀ a c, T a c = T c a := fun a c => stress_symm g hg hsym x hdet Λ κ a c
  simp only [sum4]
  rw [hTs 1 0, hTs 2 0, hTs 2 1, hTs 3 0, hTs 3 1, hTs 3 2]
  ring

end AtX

end Sym

end G05BSymm
