import G05AConformalDEC

set_option maxHeartbeats 4000000
set_option maxRecDepth 4096

/-!
# G05-A Part B: cubic family `g = e^{2 φ_0} η + H` (ENERGYFRAME_THEOREMS.md EF3, eq. (6))

Source recovery (see SOURCE_RECOVERY.md): EF3 fixes the 2-jet of
`g^(0) = e^{2φ_0} η`, `φ_0 = -b x0^2 - b|x|^2/2` (= `phi b 0`), and sets
`g = g^(0) + H` with the symmetric cubic perturbation
`H_00 = 0`, `H_ij = -δ_ij x0 S_kl x^k x^l / 2`,
`H_0i = -x0 r^2 q_i / 2 - r^2 W_ij x^j / 5`,
`q_i = -6b k_0i`, `M_ij = -6b k_ji`, `S = sym M`, `W = skew M`.
The stress is Einstein-defined, `κ T = G[g] + Λ g`; EF3 asserts that `g` is Lorentzian
near 0 and that strict DEC persists "as in EF2".  The polynomial `H` and its third-jet
tensor `J` are copied verbatim from the accepted CAS-05 C03 Lean file
(CAS05C03.lean, `H`, `J`, `H_from_third_jet`).

The Einstein tensor is the general one from G05AConformalDEC (actual derivatives,
actual matrix inverse).  Proven here:
* B1: on a member-dependent ball, `g(x)` is Lorentzian
  (`g(e0,e0) < 0` and `g` positive definite on the `g`-orthogonal complement of `e0`).
* B2: on a member-dependent ball, the Einstein-defined stress satisfies strict DEC
  (pairing form) with respect to the causal cone of `g(x)`.
-/

namespace G05BCubicDEC

open G05AConformalDEC

def sdelta (a c : I) : ℝ := if a = 0 then 0 else delta a c

def q (b : ℝ) (k : I → I → ℝ) (i : I) : ℝ :=
  if i = 0 then 0 else -6*b*k 0 i
def M (b : ℝ) (k : I → I → ℝ) (i j : I) : ℝ :=
  if i = 0 ∨ j = 0 then 0 else -6*b*k j i
noncomputable def S (b : ℝ) (k : I → I → ℝ) (i j : I) : ℝ :=
  (M b k i j + M b k j i)/2
noncomputable def W (b : ℝ) (k : I → I → ℝ) (i j : I) : ℝ :=
  (M b k i j - M b k j i)/2

def r2 (X : I → ℝ) : ℝ := X 1^2 + X 2^2 + X 3^2
noncomputable def Sxx (b : ℝ) (k : I → I → ℝ) (X : I → ℝ) : ℝ :=
  sum4 (fun i => sum4 (fun j => S b k i j * X i * X j))
noncomputable def WX (b : ℝ) (k : I → I → ℝ) (X : I → ℝ) (i : I) : ℝ :=
  sum4 (fun j => W b k i j * X j)

/-- EF3 eq. (6) cubic perturbation (verbatim from accepted CAS05C03). -/
noncomputable def H (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : ℝ :=
  if a = 0 then
    if c = 0 then 0 else -X 0*r2 X*q b k c/2 - r2 X*WX b k X c/5
  else if c = 0 then
    -X 0*r2 X*q b k a/2 - r2 X*WX b k X a/5
  else -delta a c*X 0*Sxx b k X/2

theorem H_symmetric (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : H b k a c X = H b k c a X := by
  fin_cases a <;> fin_cases c <;>
    simp [H, delta]

noncomputable def J0i (b : ℝ) (k : I → I → ℝ)
    (i d e f : I) : ℝ :=
  -q b k i*(delta d 0*sdelta e f + delta e 0*sdelta d f +
            delta f 0*sdelta d e) -
  (2/5 : ℝ)*(sdelta d e*W b k i f + sdelta d f*W b k i e +
             sdelta e f*W b k i d)

noncomputable def Jii (b : ℝ) (k : I → I → ℝ)
    (d e f : I) : ℝ :=
  -(delta d 0*S b k e f + delta e 0*S b k d f + delta f 0*S b k d e)

noncomputable def J (b : ℝ) (k : I → I → ℝ)
    (a c d e f : I) : ℝ :=
  if a = 0 then if c = 0 then 0 else J0i b k c d e f
  else if c = 0 then J0i b k a d e f
  else delta a c * Jii b k d e f

noncomputable def cubicFromJ (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : ℝ :=
  (1/6 : ℝ)*sum4 (fun d => sum4 (fun e =>
    sum4 (fun f => J b k a c d e f * X d * X e * X f)))

theorem H_from_third_jet (b : ℝ) (k : I → I → ℝ)
    (a c : I) (X : I → ℝ) : H b k a c X = cubicFromJ b k a c X := by
  fin_cases a <;> fin_cases c <;>
    simp [H, cubicFromJ, J, J0i, Jii, Sxx, WX, r2,
      sum4, sdelta, delta, S, W] <;> ring

theorem H_origin (b : ℝ) (k : I → I → ℝ) (a c : I) : H b k a c 0 = 0 := by
  simp [H, r2, Sxx, WX, sum4]

/-- The cubic-family metric `g = e^{2 φ_0} η + H`, `φ_0 = phi b 0`. -/
noncomputable def gCub (b : ℝ) (k : I → I → ℝ) (x : I → ℝ) (a c : I) : ℝ :=
  Real.exp (2 * phi b 0 x) * eta a c + H b k a c x

theorem gCub_symmetric (b : ℝ) (k : I → I → ℝ) (x : I → ℝ) (a c : I) :
    gCub b k x a c = gCub b k x c a := by
  unfold gCub
  rw [H_symmetric b k a c x]
  congr 2
  fin_cases a <;> fin_cases c <;> simp [eta, delta, sig]

/-! ## Polynomial derivatives of the cubic perturbation -/

theorem pd_cubic3 (T : I → I → I → ℝ) (c : I) (x : I → ℝ) :
    pd (fun y => sum4 (fun d => sum4 (fun e => sum4 (fun f => T d e f * y d * y e * y f))))
        c x =
      sum4 (fun e => sum4 (fun f => (T c e f + T e c f + T e f c) * x e * x f)) := by
  simp only [sum4]
  simp (disch := fun_prop) only [pd_add, pd_mul, pd_coord, pd_const]
  fin_cases c <;> simp <;> ring

theorem pd_quad_origin (Q : I → I → ℝ) (d : I) :
    pd (fun y => sum4 (fun e => sum4 (fun f => Q e f * y e * y f))) d 0 = 0 := by
  simp only [sum4]
  simp (disch := fun_prop) only [pd_add, pd_mul, pd_coord, pd_const]
  simp

theorem H_cubic_form (b : ℝ) (k : I → I → ℝ) (a c : I) :
    (fun y => H b k a c y) = fun y => sum4 (fun d => sum4 (fun e =>
      sum4 (fun f => J b k a c d e f / 6 * y d * y e * y f))) := by
  funext y
  rw [H_from_third_jet]
  simp only [cubicFromJ, sum4]
  ring

theorem H_contDiff (b : ℝ) (k : I → I → ℝ) (a c : I) {n : WithTop ℕ∞} :
    ContDiff ℝ n (fun y => H b k a c y) := by
  rw [H_cubic_form]
  simp only [sum4]
  fun_prop

theorem pd_H (b : ℝ) (k : I → I → ℝ) (a c e : I) (y : I → ℝ) :
    pd (fun z => H b k a c z) e y =
      sum4 (fun e' => sum4 (fun f =>
        (J b k a c e e' f / 6 + J b k a c e' e f / 6 + J b k a c e' f e / 6) *
          y e' * y f)) := by
  rw [H_cubic_form]
  exact pd_cubic3 (fun d e f => J b k a c d e f / 6) e y

theorem pd_H_origin (b : ℝ) (k : I → I → ℝ) (a c e : I) :
    pd (fun z => H b k a c z) e 0 = 0 := by
  rw [pd_H]
  simp [sum4]

theorem pd_pd_H_origin (b : ℝ) (k : I → I → ℝ) (a c e d : I) :
    pd (fun y => pd (fun z => H b k a c z) e y) d 0 = 0 := by
  have h : (fun y => pd (fun z => H b k a c z) e y) = fun y =>
      sum4 (fun e' => sum4 (fun f =>
        (J b k a c e e' f / 6 + J b k a c e' e f / 6 + J b k a c e' f e / 6) *
          y e' * y f)) := funext (pd_H b k a c e)
  rw [h]
  exact pd_quad_origin _ d

/-! ## General regularity of the Einstein-defined stress at a point -/

theorem pd_contDiff (f : (I → ℝ) → ℝ) (hf : ContDiff ℝ 2 f) (c : I) :
    ContDiff ℝ 1 (fun y => pd f c y) := by
  unfold pd
  exact (hf.fderiv_right (m := 1) (by norm_num)).clm_apply contDiff_const

theorem contDiff_det {n : WithTop ℕ∞} (Mf : (I → ℝ) → Matrix I I ℝ)
    (h : ∀ i j, ContDiff ℝ n fun y => Mf y i j) : ContDiff ℝ n fun y => (Mf y).det := by
  simp only [Matrix.det_apply']
  apply ContDiff.sum
  intro σ _
  exact contDiff_const.mul (contDiff_prod fun i _ => h (σ i) i)

theorem contDiff_adj {n : WithTop ℕ∞} (Mf : (I → ℝ) → Matrix I I ℝ)
    (h : ∀ i j, ContDiff ℝ n fun y => Mf y i j) (i j : I) :
    ContDiff ℝ n fun y => (Mf y).adjugate i j := by
  simp only [Matrix.adjugate_apply]
  apply contDiff_det
  intro k l
  simp only [Matrix.updateRow_apply]
  split_ifs
  · exact contDiff_const
  · exact h k l

theorem contDiffAt_inv_entry {n : WithTop ℕ∞} (Mf : (I → ℝ) → Matrix I I ℝ)
    (h : ∀ i j, ContDiff ℝ n fun y => Mf y i j) (x : I → ℝ) (hx : (Mf x).det ≠ 0)
    (a c : I) : ContDiffAt ℝ n (fun y => (Mf y)⁻¹ a c) x := by
  have e : (fun y => (Mf y)⁻¹ a c) = fun y => ((Mf y).det)⁻¹ * (Mf y).adjugate a c := by
    funext y
    rw [Matrix.inv_def]
    simp [Ring.inverse_eq_inv']
  rw [e]
  exact ((contDiff_det Mf h).contDiffAt.inv hx).mul (contDiff_adj Mf h a c).contDiffAt

section General

variable (g : (I → ℝ) → I → I → ℝ) (hg : ∀ a c, ContDiff ℝ 2 (fun y => g y a c))
  (hdet : (toMat g 0).det ≠ 0)

include hg in
theorem dg_contDiff (c a e : I) : ContDiff ℝ 1 (fun y => dg g c a e y) :=
  pd_contDiff _ (hg a e) c

include hg hdet in
theorem ginv_contDiffAt (a c : I) : ContDiffAt ℝ 1 (fun y => ginv g y a c) 0 := by
  unfold ginv
  exact contDiffAt_inv_entry (toMat g) (fun i j => (hg i j).of_le (by norm_num)) 0 hdet a c

include hg hdet in
theorem Gam_contDiffAt (a i j : I) : ContDiffAt ℝ 1 (fun y => Gam g y a i j) 0 := by
  have h1 := ginv_contDiffAt g hg hdet
  have h2 : ∀ c a e, ContDiffAt ℝ 1 (fun y => dg g c a e y) 0 :=
    fun c a e => (dg_contDiff g hg c a e).contDiffAt
  unfold Gam sum4
  fun_prop

include hg hdet in
theorem dGam_continuousAt (d a i j : I) : ContinuousAt (fun y => dGam g d a i j y) 0 := by
  unfold dGam pd
  have h := (Gam_contDiffAt g hg hdet a i j).fderiv_right (m := 0) (by norm_num)
  exact h.continuousAt.clm_apply continuousAt_const

include hg hdet in
/-- The Einstein-defined stress of a `C^2` metric field nondegenerate at 0 is continuous
at 0. -/
theorem stress_continuousAt (Λ κ : ℝ) : ContinuousAt (stress g Λ κ) 0 := by
  have h1 : ∀ a c, ContinuousAt (fun y => ginv g y a c) 0 :=
    fun a c => (ginv_contDiffAt g hg hdet a c).continuousAt
  have h2 : ∀ a i j, ContinuousAt (fun y => Gam g y a i j) 0 :=
    fun a i j => (Gam_contDiffAt g hg hdet a i j).continuousAt
  have h3 : ∀ d a i j, ContinuousAt (fun y => dGam g d a i j y) 0 :=
    dGam_continuousAt g hg hdet
  have h4 : ∀ a c, ContinuousAt (fun y => g y a c) 0 :=
    fun a c => (hg a c).continuous.continuousAt
  apply continuousAt_pi.2; intro a
  apply continuousAt_pi.2; intro c
  unfold stress Ein Rsc Ric sum4
  fun_prop

theorem Gam_crit (hcrit : ∀ c a e, dg g c a e 0 = 0) (a i j : I) : Gam g 0 a i j = 0 := by
  simp [Gam, hcrit]

include hg hdet in
/-- At a point where `∂g = 0`, `∂Γ` is `g^{-1}` times the second metric derivatives. -/
theorem dGam_crit (hcrit : ∀ c a e, dg g c a e 0 = 0) (d a i j : I) :
    dGam g d a i j 0 = (1 / 2 : ℝ) * sum4 (fun e => ginv g 0 a e *
      (pd (fun y => dg g i j e y) d 0 + pd (fun y => dg g j i e y) d 0 -
        pd (fun y => dg g e i j y) d 0)) := by
  have h1 : ∀ a c, DifferentiableAt ℝ (fun y => ginv g y a c) 0 :=
    fun a c => (ginv_contDiffAt g hg hdet a c).differentiableAt (by norm_num)
  have h2 : ∀ c a e, Differentiable ℝ (fun y => dg g c a e y) :=
    fun c a e => (dg_contDiff g hg c a e).differentiable (by norm_num)
  unfold dGam Gam
  simp only [sum4]
  simp (disch := fun_prop) only [pd_mul, pd_add, pd_sub, pd_const]
  simp [hcrit]
  ring

end General

/-- Two `C^2` metric fields, nondegenerate and critical (`∂g = 0`) at 0, with equal
value and equal second derivatives at 0, have equal Einstein tensor at 0. -/
theorem Ein_eq_of_jet (g1 g2 : (I → ℝ) → I → I → ℝ)
    (hg1 : ∀ a c, ContDiff ℝ 2 (fun y => g1 y a c))
    (hg2 : ∀ a c, ContDiff ℝ 2 (fun y => g2 y a c))
    (hdet1 : (toMat g1 0).det ≠ 0) (hdet2 : (toMat g2 0).det ≠ 0)
    (hcrit1 : ∀ c a e, dg g1 c a e 0 = 0) (hcrit2 : ∀ c a e, dg g2 c a e 0 = 0)
    (h0 : g1 0 = g2 0)
    (hjet : ∀ d c a e, pd (fun y => dg g1 c a e y) d 0 = pd (fun y => dg g2 c a e y) d 0)
    (a c : I) : Ein g1 0 a c = Ein g2 0 a c := by
  have hginv : ∀ a c, ginv g1 0 a c = ginv g2 0 a c := by
    intro a c; simp only [ginv, toMat, h0]
  simp only [Ein, Rsc, Ric, dGam_crit g1 hg1 hdet1 hcrit1, dGam_crit g2 hg2 hdet2 hcrit2,
    Gam_crit g1 hcrit1, Gam_crit g2 hcrit2, hginv, hjet, h0]

/-! ## Cubic family: 2-jet at the origin -/

theorem gConf_contDiff (b lam : ℝ) (a c : I) {n : WithTop ℕ∞} :
    ContDiff ℝ n (fun y => gConf b lam y a c) := by
  unfold gConf phi
  fun_prop

theorem gCub_contDiff (b : ℝ) (k : I → I → ℝ) (a c : I) {n : WithTop ℕ∞} :
    ContDiff ℝ n (fun y => gCub b k y a c) :=
  (gConf_contDiff b 0 a c).add (H_contDiff b k a c)

theorem gCub_origin (b : ℝ) (k : I → I → ℝ) : gCub b k 0 = gConf b 0 0 := by
  funext a c
  simp [gCub, gConf, H_origin]

theorem gCub_origin_eta (b : ℝ) (k : I → I → ℝ) : gCub b k 0 = eta := by
  rw [gCub_origin, gConf_origin]

theorem dg_cub_split (b : ℝ) (k : I → I → ℝ) (c a e : I) (y : I → ℝ) :
    dg (gCub b k) c a e y = dg (gConf b 0) c a e y + pd (fun z => H b k a e z) c y := by
  unfold dg
  show pd (fun y => gConf b 0 y a e + H b k a e y) c y = _
  exact pd_add c ((gConf_contDiff b 0 a e (n := 1)).differentiable (by norm_num) y)
    ((H_contDiff b k a e (n := 1)).differentiable (by norm_num) y)

theorem pPhi_origin (b lam : ℝ) (c : I) : pPhi b lam 0 c = 0 := by
  simp [pPhi]

theorem conf_crit (b : ℝ) (c a e : I) : dg (gConf b 0) c a e 0 = 0 := by
  rw [dg_conf, pPhi_origin]; ring

theorem cub_crit (b : ℝ) (k : I → I → ℝ) (c a e : I) : dg (gCub b k) c a e 0 = 0 := by
  rw [dg_cub_split, conf_crit, pd_H_origin]; ring

theorem cub_jet (b : ℝ) (k : I → I → ℝ) (d c a e : I) :
    pd (fun y => dg (gCub b k) c a e y) d 0 = pd (fun y => dg (gConf b 0) c a e y) d 0 := by
  have h : (fun y => dg (gCub b k) c a e y) =
      fun y => dg (gConf b 0) c a e y + pd (fun z => H b k a e z) c y :=
    funext (dg_cub_split b k c a e)
  rw [h, pd_add d ((dg_contDiff (gConf b 0) (fun a c => gConf_contDiff b 0 a c) c a e).differentiable
      (by norm_num) 0)
    ((pd_contDiff _ (H_contDiff b k a e) c).differentiable (by norm_num) 0),
    pd_pd_H_origin, add_zero]

theorem det_conf (b lam : ℝ) (x : I → ℝ) : (toMat (gConf b lam) x).det ≠ 0 :=
  Matrix.det_ne_zero_of_right_inverse (toMat_conf_mul b lam x)

theorem det_cub (b : ℝ) (k : I → I → ℝ) : (toMat (gCub b k) 0).det ≠ 0 := by
  have e : toMat (gCub b k) 0 = toMat (gConf b 0) 0 := by
    unfold toMat; rw [gCub_origin]
  rw [e]
  exact det_conf b 0 0

/-- The Einstein-defined stress of the cubic member at the origin equals that of the
conformal baseline: `T(0) = diag((6b-Λ)/κ, Λ/κ, Λ/κ, Λ/κ)`. -/
theorem stress_cub_origin (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ) :
    stress (gCub b k) Λ κ 0 = diagT ((6*b - Λ)/κ) (Λ/κ) := by
  funext a c
  have hE := Ein_eq_of_jet (gCub b k) (gConf b 0) (fun a c => gCub_contDiff b k a c)
    (fun a c => gConf_contDiff b 0 a c) (det_cub b k) (det_conf b 0 0) (cub_crit b k)
    (conf_crit b) (gCub_origin b k) (cub_jet b k) a c
  have e : stress (gCub b k) Λ κ 0 a c = stress (gConf b 0) Λ κ 0 a c := by
    unfold stress; rw [hE, gCub_origin]
  rw [e, stress_conf_origin_diag]

theorem gCub_continuousAt (b : ℝ) (k : I → I → ℝ) : ContinuousAt (gCub b k) 0 := by
  apply continuousAt_pi.2; intro a
  apply continuousAt_pi.2; intro c
  exact (gCub_contDiff b k a c (n := 0)).continuous.continuousAt

/-! ## B1: Lorentzian neighborhood -/

def e0 : I → ℝ := fun a => if a = 0 then 1 else 0

/-- Lorentzian signature, recorded choice: `g(e0,e0) < 0` and `g` is positive definite on
the `g`-orthogonal complement of `e0` (for symmetric `g` this is inertia `(1,3)`). -/
def Lorentzian (g : I → I → ℝ) : Prop :=
  bil g e0 e0 < 0 ∧ ∀ w : I → ℝ, w ≠ 0 → bil g e0 w = 0 → 0 < bil g w w

theorem lorentzian_of_close (g : I → I → ℝ) (hg : ∀ a c, |g a c - eta a c| ≤ 1/10) :
    Lorentzian g := by
  have hb := fun a c => abs_le.mp (hg a c)
  have h00 := hb 0 0
  have h01 := hb 0 1
  have h02 := hb 0 2
  have h03 := hb 0 3
  simp [eta, delta, sig] at h00 h01 h02 h03
  have he0 : bil g e0 e0 = g 0 0 := by simp [bil, sum4, e0]
  have he0w : ∀ w : I → ℝ, bil g e0 w = g 0 0 * w 0 + g 0 1 * w 1 + g 0 2 * w 2 + g 0 3 * w 3 := by
    intro w; simp [bil, sum4, e0]
  refine ⟨by rw [he0]; linarith, ?_⟩
  intro w hw horth
  rw [he0w] at horth
  have hD := quad_lower (fun a c => g a c - eta a c) (1/10) hg w
  have hsplit := bil_split g eta w w
  rw [bil_eta] at hsplit
  set A := w 1 ^ 2 + w 2 ^ 2 + w 3 ^ 2 with hA
  have hA0 : 0 ≤ A := by positivity
  have hX : (g 0 1 * w 1 + g 0 2 * w 2 + g 0 3 * w 3) ^ 2 ≤
      (g 0 1 ^ 2 + g 0 2 ^ 2 + g 0 3 ^ 2) * A := by
    rw [hA]
    nlinarith [sq_nonneg (g 0 1 * w 2 - g 0 2 * w 1), sq_nonneg (g 0 1 * w 3 - g 0 3 * w 1),
      sq_nonneg (g 0 2 * w 3 - g 0 3 * w 2)]
  have hgs : g 0 1 ^ 2 + g 0 2 ^ 2 + g 0 3 ^ 2 ≤ 3/100 := by nlinarith
  have hg00 : 81/100 ≤ g 0 0 ^ 2 := by nlinarith
  have hw0eq : g 0 0 * w 0 = -(g 0 1 * w 1 + g 0 2 * w 2 + g 0 3 * w 3) := by linarith
  have hw0 : 81/100 * w 0 ^ 2 ≤ 3/100 * A := by
    calc 81/100 * w 0 ^ 2 ≤ g 0 0 ^ 2 * w 0 ^ 2 := mul_le_mul_of_nonneg_right hg00 (sq_nonneg _)
      _ = (g 0 0 * w 0) ^ 2 := by ring
      _ = (g 0 1 * w 1 + g 0 2 * w 2 + g 0 3 * w 3) ^ 2 := by rw [hw0eq]; ring
      _ ≤ (g 0 1 ^ 2 + g 0 2 ^ 2 + g 0 3 ^ 2) * A := hX
      _ ≤ 3/100 * A := mul_le_mul_of_nonneg_right hgs hA0
  by_cases hAz : A = 0
  · exfalso
    apply hw
    have h1 : w 1 = 0 := by nlinarith [sq_nonneg (w 1), sq_nonneg (w 2), sq_nonneg (w 3)]
    have h2 : w 2 = 0 := by nlinarith [sq_nonneg (w 1), sq_nonneg (w 2), sq_nonneg (w 3)]
    have h3 : w 3 = 0 := by nlinarith [sq_nonneg (w 1), sq_nonneg (w 2), sq_nonneg (w 3)]
    have h0 : w 0 = 0 := by nlinarith [sq_nonneg (w 0)]
    funext a
    fin_cases a <;> simp [h0, h1, h2, h3]
  · have hApos : 0 < A := lt_of_le_of_ne hA0 (Ne.symm hAz)
    rw [hsplit]
    nlinarith

theorem lorentzian_nhds (gF : (I → ℝ) → I → I → ℝ) (hg : ContinuousAt gF 0)
    (hg0 : gF 0 = eta) : ∃ r > 0, ∀ x : I → ℝ, ‖x‖ < r → Lorentzian (gF x) := by
  obtain ⟨r, hr, H⟩ := Metric.continuousAt_iff.mp hg (1/10) (by norm_num)
  refine ⟨r, hr, fun x hx => lorentzian_of_close _ ?_⟩
  intro a c
  have hx' : dist x 0 < r := by rwa [dist_zero_right]
  have h1 := (dist_le_pi_dist (gF x a) (gF 0 a) c).trans (dist_le_pi_dist (gF x) (gF 0) a)
  have e1 : gF 0 a c = eta a c := by rw [hg0]
  rw [Real.dist_eq, e1] at h1
  linarith [H hx']

/-- **B1 lorentz_neighborhood.** For each member `(b, k)` there is a radius `r > 0`
(member-dependent) such that for `‖x‖ < r` the cubic-family metric is symmetric and
Lorentzian. -/
theorem lorentz_neighborhood (b : ℝ) (k : I → I → ℝ) :
    ∃ r > 0, ∀ x : I → ℝ, ‖x‖ < r →
      Lorentzian (gCub b k x) ∧ ∀ a c, gCub b k x a c = gCub b k x c a := by
  obtain ⟨r, hr, H⟩ := lorentzian_nhds (gCub b k) (gCub_continuousAt b k) (gCub_origin_eta b k)
  exact ⟨r, hr, fun x hx => ⟨H x hx, gCub_symmetric b k x⟩⟩

/-! ## B2: strict DEC on a member-dependent neighborhood -/

/-- **B2 strict_dec_neighborhood_cubic.** For `b > 0`, `Λ < 3b`, `κ > 0` and every
`k`, there is a member-dependent radius `r > 0` such that for `‖x‖ < r` the cubic metric
is Lorentzian and its Einstein-defined stress obeys strict DEC with respect to the causal
cone of `g(x)`. -/
theorem strict_dec_neighborhood_cubic (b : ℝ) (k : I → I → ℝ) (Λ κ : ℝ)
    (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ) :
    ∃ r > 0, ∀ x : I → ℝ, ‖x‖ < r →
      Lorentzian (gCub b k x) ∧ StrictDEC (gCub b k x) (stress (gCub b k) Λ κ x) := by
  obtain ⟨r1, hr1, H1⟩ := lorentz_neighborhood b k
  obtain ⟨r2, hr2, H2⟩ := strictDEC_nhds (gCub b k) (stress (gCub b k) Λ κ)
    ((6*b - Λ)/κ) (Λ/κ) (gCub_continuousAt b k)
    (stress_continuousAt (gCub b k) (fun a c => gCub_contDiff b k a c) (det_cub b k) Λ κ)
    (gCub_origin_eta b k) (stress_cub_origin b k Λ κ) (origin_margin b Λ κ hb hΛ hκ)
  refine ⟨min r1 r2, lt_min hr1 hr2, fun x hx => ⟨(H1 x ?_).1, H2 x ?_⟩⟩
  · exact lt_of_lt_of_le hx (min_le_left _ _)
  · exact lt_of_lt_of_le hx (min_le_right _ _)

end G05BCubicDEC
