import Mathlib

set_option maxHeartbeats 4000000

/-!
# G05-A Part A: conformal family, Einstein-defined stress, strict DEC neighborhood

Coordinates `x : Fin 4 → ℝ` (index 0 = x0 = c t), signature (-,+,+,+),
`eta = diag(-1,1,1,1)`.  The metric field is `gConf b lam x = exp(2 phi x) • eta`
with the CAS-05 contract polynomial
`phi = -b x0^2 - b |x|^2/2 + lam x0^2 x1 / 2`.

The Einstein tensor is NOT postulated.  It is defined for an arbitrary metric
field from actual Fréchet partial derivatives (`pd`), the actual matrix inverse,
Christoffel symbols, the CAS-05 Ricci convention
`R_ab = ∂_c Γ^c_ba - ∂_b Γ^c_ca + Γ^c_ce Γ^e_ba - Γ^c_be Γ^e_ca`,
the scalar `R = g^{ab} R_ab` and `G = Ric - g R / 2`.  For the conformal field we
prove that this equals the displayed formula
`G_ab = -2 φ_ab + 2 φ_a φ_b + 2 η_ab □φ + η_ab (dφ)^2`, with φ_a, φ_ab the actual
partial derivatives of the polynomial φ.  The algebraic core follows the accepted
CAS-05 C01 finite derivation (CAS05Finite.lean, `christoffel_from_metric`,
`ricci_from_connection`, `einstein_from_metric`); here it is re-proved and bound to
actual derivatives.

Strict DEC (pairing form, the lead-frozen convention):
`∀ V W ≠ 0, g(V,V) ≤ 0, V0 > 0, g(W,W) ≤ 0, W0 > 0 → T(V,W) > 0`.
Norm on `Fin 4 → ℝ` is Mathlib's sup norm.
-/

namespace G05AConformalDEC

abbrev I := Fin 4

def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3
def sig (a : I) : ℝ := if a = 0 then -1 else 1
def delta (a c : I) : ℝ := if a = c then 1 else 0
def eta (a c : I) : ℝ := delta a c * sig a

/-- Bilinear pairing `M(V,W) = Σ_{a,c} M_ac V^a W^c`. -/
def bil (M : I → I → ℝ) (V W : I → ℝ) : ℝ :=
  sum4 (fun a => sum4 (fun c => M a c * V a * W c))

/-- Future-directed causal vector for the metric components `g`
(time orientation by the coordinate component `V 0 > 0`). -/
def FutureCausal (g : I → I → ℝ) (V : I → ℝ) : Prop :=
  bil g V V ≤ 0 ∧ 0 < V 0

/-- Strict dominant energy condition, pairing form. -/
def StrictDEC (g T : I → I → ℝ) : Prop :=
  ∀ V W : I → ℝ, V ≠ 0 → W ≠ 0 → FutureCausal g V → FutureCausal g W →
    0 < bil T V W

/-! ## Actual coordinate partial derivatives -/

/-- `pd f c x = ∂_c f (x)`, the Fréchet derivative applied to the basis vector `e_c`. -/
noncomputable def pd (f : (I → ℝ) → ℝ) (c : I) (x : I → ℝ) : ℝ :=
  fderiv ℝ f x (Pi.single c 1)

theorem pd_add {f g : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) :
    pd (fun y => f y + g y) c x = pd f c x + pd g c x := by
  simp [pd, fderiv_fun_add hf hg]

theorem pd_sub {f g : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) :
    pd (fun y => f y - g y) c x = pd f c x - pd g c x := by
  simp [pd, fderiv_fun_sub hf hg]

theorem pd_mul {f g : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) :
    pd (fun y => f y * g y) c x = f x * pd g c x + g x * pd f c x := by
  simp [pd, fderiv_fun_mul hf hg]

theorem pd_neg {f : (I → ℝ) → ℝ} {x : I → ℝ} (c : I) :
    pd (fun y => -f y) c x = -pd f c x := by
  simp [pd]

theorem pd_const (k : ℝ) (c : I) (x : I → ℝ) : pd (fun _ => k) c x = 0 := by
  simp [pd]

theorem pd_coord (a c : I) (x : I → ℝ) :
    pd (fun y => y a) c x = if a = c then 1 else 0 := by
  unfold pd
  rw [(hasFDerivAt_apply a x).fderiv]
  simp [Pi.single_apply]

theorem pd_exp {f : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) :
    pd (fun y => Real.exp (f y)) c x = Real.exp (f x) * pd f c x := by
  simp [pd, fderiv_exp hf]

theorem pd_pow {f : (I → ℝ) → ℝ} {x : I → ℝ} (c : I) (n : ℕ)
    (hf : DifferentiableAt ℝ f x) :
    pd (fun y => f y ^ n) c x = n * f x ^ (n - 1) * pd f c x := by
  simp only [pd, fderiv_fun_pow n hf]
  simp [nsmul_eq_mul]

/-! ## Einstein tensor of a metric field, from actual derivatives -/

def toMat (g : (I → ℝ) → I → I → ℝ) (x : I → ℝ) : Matrix I I ℝ := Matrix.of (g x)

noncomputable def ginv (g : (I → ℝ) → I → I → ℝ) (x : I → ℝ) (a c : I) : ℝ :=
  (toMat g x)⁻¹ a c

/-- `dg g c a e x = ∂_c g_ae (x)`. -/
noncomputable def dg (g : (I → ℝ) → I → I → ℝ) (c a e : I) (x : I → ℝ) : ℝ :=
  pd (fun y => g y a e) c x

/-- `Γ^a_ij = (1/2) g^{ad} (∂_i g_jd + ∂_j g_id - ∂_d g_ij)`. -/
noncomputable def Gam (g : (I → ℝ) → I → I → ℝ) (x : I → ℝ) (a i j : I) : ℝ :=
  (1 / 2 : ℝ) * sum4 (fun d =>
    ginv g x a d * (dg g i j d x + dg g j i d x - dg g d i j x))

/-- `dGam g d a i j x = ∂_d Γ^a_ij (x)` (actual derivative). -/
noncomputable def dGam (g : (I → ℝ) → I → I → ℝ) (d a i j : I) (x : I → ℝ) : ℝ :=
  pd (fun y => Gam g y a i j) d x

noncomputable def Ric (g : (I → ℝ) → I → I → ℝ) (x : I → ℝ) (a i : I) : ℝ :=
  sum4 (fun c =>
    dGam g c c i a x - dGam g i c c a x +
    sum4 (fun e =>
      Gam g x c c e * Gam g x e i a - Gam g x c i e * Gam g x e c a))

noncomputable def Rsc (g : (I → ℝ) → I → I → ℝ) (x : I → ℝ) : ℝ :=
  sum4 (fun a => sum4 (fun c => ginv g x a c * Ric g x a c))

noncomputable def Ein (g : (I → ℝ) → I → I → ℝ) (x : I → ℝ) (a c : I) : ℝ :=
  Ric g x a c - g x a c * Rsc g x / 2

/-- Einstein-defined stress `κ T = G + Λ g`. -/
noncomputable def stress (g : (I → ℝ) → I → I → ℝ) (Λ κ : ℝ) (x : I → ℝ)
    (a c : I) : ℝ :=
  (Ein g x a c + Λ * g x a c) / κ

/-! ## The conformal family -/

noncomputable def phi (b lam : ℝ) (X : I → ℝ) : ℝ :=
  -b * X 0 ^ 2 - b / 2 * (X 1 ^ 2 + X 2 ^ 2 + X 3 ^ 2) +
    lam / 2 * X 0 ^ 2 * X 1

noncomputable def pPhi (b lam : ℝ) (X : I → ℝ) (a : I) : ℝ :=
  (-2*b*X 0 + lam*X 0*X 1)*delta a 0 +
  (-b*X 1 + lam/2*X 0^2)*delta a 1 -
  b*X 2*delta a 2 - b*X 3*delta a 3

def hPhi (b lam : ℝ) (X : I → ℝ) (a c : I) : ℝ :=
  (-2*b+lam*X 1)*delta a 0*delta c 0 -
  b*(delta a 1*delta c 1 + delta a 2*delta c 2 + delta a 3*delta c 3) +
  lam*X 0*(delta a 0*delta c 1 + delta a 1*delta c 0)

theorem hPhi_sym (b lam : ℝ) (X : I → ℝ) (a c : I) :
    hPhi b lam X a c = hPhi b lam X c a := by
  unfold hPhi
  ring

noncomputable def gConf (b lam : ℝ) (x : I → ℝ) (a c : I) : ℝ :=
  Real.exp (2 * phi b lam x) * eta a c

@[fun_prop] theorem phi_differentiable (b lam : ℝ) : Differentiable ℝ (phi b lam) := by
  unfold phi; fun_prop

@[fun_prop] theorem phi_continuous (b lam : ℝ) : Continuous (phi b lam) := by
  unfold phi; fun_prop

@[fun_prop] theorem pPhi_differentiable (b lam : ℝ) (c : I) :
    Differentiable ℝ (fun y => pPhi b lam y c) := by
  unfold pPhi; fun_prop

@[fun_prop] theorem pPhi_continuous (b lam : ℝ) (c : I) :
    Continuous (fun y => pPhi b lam y c) := by
  unfold pPhi; fun_prop

@[fun_prop] theorem hPhi_continuous (b lam : ℝ) (a c : I) :
    Continuous (fun y => hPhi b lam y a c) := by
  unfold hPhi; fun_prop

/-- φ_c is the actual partial derivative of φ. -/
theorem pd_phi (b lam : ℝ) (c : I) (y : I → ℝ) :
    pd (phi b lam) c y = pPhi b lam y c := by
  have e : phi b lam = fun y => -b * y 0 ^ 2 - b / 2 * (y 1 ^ 2 + y 2 ^ 2 + y 3 ^ 2) +
      lam / 2 * y 0 ^ 2 * y 1 := rfl
  rw [e]
  simp (disch := fun_prop) only [pd_add, pd_sub, pd_mul, pd_pow, pd_const, pd_coord]
  fin_cases c <;> simp [pPhi, delta] <;> ring

/-- φ_dc is the actual partial derivative of φ_c. -/
theorem pd_pPhi (b lam : ℝ) (c d : I) (y : I → ℝ) :
    pd (fun y => pPhi b lam y c) d y = hPhi b lam y d c := by
  fin_cases c <;>
  · simp only [pPhi, delta]
    simp (disch := fun_prop) only [pd_add, pd_sub, pd_mul, pd_pow, pd_const, pd_coord,
      pd_neg]
    fin_cases d <;> simp [hPhi, delta] <;> ring

/-- First derivative of the actual conformal metric. -/
theorem dg_conf (b lam : ℝ) (c a e : I) (y : I → ℝ) :
    dg (gConf b lam) c a e y = 2 * Real.exp (2 * phi b lam y) * pPhi b lam y c * eta a e := by
  unfold dg gConf
  simp (disch := fun_prop) only [pd_mul, pd_exp, pd_const, pd_phi]
  ring

theorem toMat_conf_mul (b lam : ℝ) (x : I → ℝ) :
    toMat (gConf b lam) x *
      Matrix.of (fun a c => (Real.exp (2 * phi b lam x))⁻¹ * eta a c) = 1 := by
  have hE : Real.exp (2 * phi b lam x) ≠ 0 := Real.exp_ne_zero _
  ext i j
  simp only [Matrix.mul_apply, Fin.sum_univ_four, toMat, gConf, Matrix.of_apply,
    Matrix.one_apply]
  fin_cases i <;> fin_cases j <;> simp [eta, delta, sig, hE]

theorem conf_mul_toMat (b lam : ℝ) (x : I → ℝ) :
    Matrix.of (fun a c => (Real.exp (2 * phi b lam x))⁻¹ * eta a c) *
      toMat (gConf b lam) x = 1 := by
  have hE : Real.exp (2 * phi b lam x) ≠ 0 := Real.exp_ne_zero _
  ext i j
  simp only [Matrix.mul_apply, Fin.sum_univ_four, toMat, gConf, Matrix.of_apply,
    Matrix.one_apply]
  fin_cases i <;> fin_cases j <;> simp [eta, delta, sig, hE]

/-- The actual inverse metric of the conformal field. -/
theorem ginv_conf (b lam : ℝ) (x : I → ℝ) (a c : I) :
    ginv (gConf b lam) x a c = (Real.exp (2 * phi b lam x))⁻¹ * eta a c := by
  unfold ginv
  rw [Matrix.inv_eq_right_inv (toMat_conf_mul b lam x)]
  rfl

/-! ### Algebraic core (accepted CAS-05 C01 pattern, re-proved) -/

def conformalChristoffel (p : I → ℝ) (a i j : I) : ℝ :=
  delta a i * p j + delta a j * p i - eta i j * sig a * p a

def conformalDChristoffel (h : I → I → ℝ) (d a i j : I) : ℝ :=
  delta a i * h d j + delta a j * h d i - eta i j * sig a * h d a

theorem christoffel_alg (E : ℝ) (p : I → ℝ) (hE : E ≠ 0) (a i j : I) :
    (1 / 2 : ℝ) * sum4 (fun d =>
      E⁻¹ * eta a d * (2 * E * p i * eta j d + 2 * E * p j * eta i d -
        2 * E * p d * eta i j)) = conformalChristoffel p a i j := by
  fin_cases a <;> fin_cases i <;> fin_cases j <;>
    simp [conformalChristoffel, sum4, eta, delta, sig] <;> field_simp <;> ring

theorem Gam_conf (b lam : ℝ) (x : I → ℝ) (a i j : I) :
    Gam (gConf b lam) x a i j = conformalChristoffel (pPhi b lam x) a i j := by
  have hE : Real.exp (2 * phi b lam x) ≠ 0 := Real.exp_ne_zero _
  simp only [Gam, ginv_conf, dg_conf]
  exact christoffel_alg _ _ hE a i j

theorem dGam_conf (b lam : ℝ) (x : I → ℝ) (d a i j : I) :
    dGam (gConf b lam) d a i j x = conformalDChristoffel (hPhi b lam x) d a i j := by
  unfold dGam
  have e : (fun y => Gam (gConf b lam) y a i j) =
      fun y => delta a i * pPhi b lam y j + delta a j * pPhi b lam y i -
        eta i j * sig a * pPhi b lam y a := by
    funext y
    rw [Gam_conf]
    rfl
  rw [e]
  simp (disch := fun_prop) only [pd_add, pd_sub, pd_mul, pd_const, pd_pPhi]
  simp only [conformalDChristoffel]
  ring

def ricciFromConnection (p : I → ℝ) (h : I → I → ℝ) (a i : I) : ℝ :=
  sum4 (fun c =>
    conformalDChristoffel h c c i a - conformalDChristoffel h i c c a +
    sum4 (fun e =>
      conformalChristoffel p c c e * conformalChristoffel p e i a -
      conformalChristoffel p c i e * conformalChristoffel p e c a))

def boxH (h : I → I → ℝ) : ℝ := sum4 (fun c => sig c * h c c)
def normP (p : I → ℝ) : ℝ := sum4 (fun c => sig c * p c * p c)

def conformalRicci (p : I → ℝ) (h : I → I → ℝ) (a i : I) : ℝ :=
  -2 * h a i + 2 * p a * p i - eta a i * (boxH h + 2 * normP p)

theorem ricci_from_connection (p : I → ℝ) (h : I → I → ℝ)
    (hsym : ∀ a i, h a i = h i a) (a i : I) :
    ricciFromConnection p h a i = conformalRicci p h a i := by
  have hs : h i a = h a i := hsym i a
  fin_cases a <;> fin_cases i <;>
    simp [ricciFromConnection, conformalRicci, conformalChristoffel,
      conformalDChristoffel, boxH, normP, sum4, eta, delta, sig] <;>
    simp at hs <;> nlinarith [hs]

def conformalEinstein (p : I → ℝ) (h : I → I → ℝ) (a i : I) : ℝ :=
  -2 * h a i + 2 * p a * p i + 2 * eta a i * boxH h + eta a i * normP p

theorem Ric_conf (b lam : ℝ) (x : I → ℝ) (a i : I) :
    Ric (gConf b lam) x a i = conformalRicci (pPhi b lam x) (hPhi b lam x) a i := by
  have e : Ric (gConf b lam) x a i = ricciFromConnection (pPhi b lam x) (hPhi b lam x) a i := by
    simp only [Ric, ricciFromConnection, dGam_conf, Gam_conf]
  rw [e]
  exact ricci_from_connection _ _ (hPhi_sym b lam x) a i

/-- A2 core: the Einstein tensor computed from the actual conformal metric equals
the displayed conformal formula. -/
theorem Ein_conf (b lam : ℝ) (x : I → ℝ) (a i : I) :
    Ein (gConf b lam) x a i = conformalEinstein (pPhi b lam x) (hPhi b lam x) a i := by
  have hE : Real.exp (2 * phi b lam x) ≠ 0 := Real.exp_ne_zero _
  simp only [Ein, Rsc, ginv_conf, Ric_conf, gConf]
  generalize Real.exp (2 * phi b lam x) = E at hE ⊢
  generalize pPhi b lam x = p
  generalize hPhi b lam x = h
  fin_cases a <;> fin_cases i <;>
    simp [conformalRicci, conformalEinstein, boxH, normP, sum4, eta, delta, sig] <;>
    field_simp <;> ring

/-- **A2 einstein_stress_def.** The Einstein-defined stress of `g = exp(2φ) η`
(curvature computed from actual derivatives, `κ T = G + Λ g`) equals
`(-2 φ_ac + 2 φ_a φ_c + 2 η_ac □φ + η_ac (dφ)^2 + Λ e^{2φ} η_ac)/κ`
where `φ_a = ∂_a φ`, `φ_ac = ∂_c ∂_a φ` are actual partial derivatives,
`□φ = η^{ee} φ_ee`, `(dφ)^2 = η^{ee} φ_e φ_e`. -/
theorem einstein_stress_def (b lam Λ κ : ℝ) (x : I → ℝ) (a c : I) :
    stress (gConf b lam) Λ κ x a c =
      (-2 * pd (fun y => pd (phi b lam) a y) c x +
        2 * pd (phi b lam) a x * pd (phi b lam) c x +
        2 * eta a c * sum4 (fun e => sig e * pd (fun y => pd (phi b lam) e y) e x) +
        eta a c * sum4 (fun e => sig e * pd (phi b lam) e x * pd (phi b lam) e x) +
        Λ * (Real.exp (2 * phi b lam x) * eta a c)) / κ := by
  simp only [stress, Ein_conf, pd_phi, pd_pPhi, conformalEinstein, boxH, normP, gConf]
  rw [hPhi_sym b lam x c a]

theorem phi_origin (b lam : ℝ) : phi b lam 0 = 0 := by simp [phi]

theorem gConf_origin (b lam : ℝ) : gConf b lam 0 = eta := by
  funext a c
  simp [gConf, phi_origin]

theorem stress_conf_origin (b lam Λ κ : ℝ) (a c : I) :
    stress (gConf b lam) Λ κ 0 a c =
      if a = c then (if a = 0 then (6*b - Λ)/κ else Λ/κ) else 0 := by
  rw [stress, Ein_conf]
  fin_cases a <;> fin_cases c <;>
    simp [conformalEinstein, pPhi, hPhi, boxH, normP, sum4, eta, delta, sig, gConf,
      phi_origin] <;> ring

theorem stress_conf_origin_00 (b lam Λ κ : ℝ) :
    stress (gConf b lam) Λ κ 0 0 0 = (6*b - Λ)/κ := by
  rw [stress_conf_origin]; simp

theorem stress_conf_origin_ii (b lam Λ κ : ℝ) (i : I) (hi : i ≠ 0) :
    stress (gConf b lam) Λ κ 0 i i = Λ/κ := by
  rw [stress_conf_origin]; simp [hi]

theorem stress_conf_origin_offdiag (b lam Λ κ : ℝ) (a c : I) (hac : a ≠ c) :
    stress (gConf b lam) Λ κ 0 a c = 0 := by
  rw [stress_conf_origin]; simp [hac]

/-! ## A1: Lorentz signature/causal structure everywhere -/

theorem bil_conf (b lam : ℝ) (x V W : I → ℝ) :
    bil (gConf b lam x) V W = Real.exp (2 * phi b lam x) * bil eta V W := by
  simp only [bil, sum4, gConf]
  ring

/-- **A1 conformal_lorentz_everywhere.** For every `x`, `g(x) = e^{2φ(x)} η` has the
two-sided inverse `e^{-2φ(x)} η` (nondegenerate, `det ≠ 0`) and exactly the causal and
timelike vectors of `η`. -/
theorem conformal_lorentz_everywhere (b lam : ℝ) (x : I → ℝ) :
    toMat (gConf b lam) x *
        Matrix.of (fun a c => (Real.exp (2 * phi b lam x))⁻¹ * eta a c) = 1 ∧
      Matrix.of (fun a c => (Real.exp (2 * phi b lam x))⁻¹ * eta a c) *
        toMat (gConf b lam) x = 1 ∧
      (toMat (gConf b lam) x).det ≠ 0 ∧
      (∀ V : I → ℝ, bil (gConf b lam x) V V ≤ 0 ↔ bil eta V V ≤ 0) ∧
      (∀ V : I → ℝ, bil (gConf b lam x) V V < 0 ↔ bil eta V V < 0) := by
  have hE : 0 < Real.exp (2 * phi b lam x) := Real.exp_pos _
  refine ⟨toMat_conf_mul b lam x, conf_mul_toMat b lam x,
    Matrix.det_ne_zero_of_right_inverse (toMat_conf_mul b lam x), ?_, ?_⟩
  · intro V
    rw [bil_conf]
    constructor
    · intro h
      by_contra h'
      push Not at h'
      have := mul_pos hE h'
      linarith
    · intro h
      exact mul_nonpos_of_nonneg_of_nonpos hE.le h
  · intro V
    rw [bil_conf]
    constructor
    · intro h
      by_contra h'
      push Not at h'
      have := mul_nonneg hE.le h'
      linarith
    · intro h
      exact mul_neg_of_pos_of_neg hE h

/-! ## General strict-DEC persistence lemma -/

theorem bil_eta (V W : I → ℝ) :
    bil eta V W = -(V 0 * W 0) + V 1 * W 1 + V 2 * W 2 + V 3 * W 3 := by
  simp [bil, sum4, eta, delta, sig]

def diagT (e p : ℝ) (a c : I) : ℝ := if a = c then (if a = 0 then e else p) else 0

theorem bil_diagT (e p : ℝ) (V W : I → ℝ) :
    bil (diagT e p) V W = e * V 0 * W 0 + p * (V 1 * W 1 + V 2 * W 2 + V 3 * W 3) := by
  simp [bil, sum4, diagT]
  ring

theorem bil_split (M N : I → I → ℝ) (V W : I → ℝ) :
    bil M V W = bil N V W + bil (fun a c => M a c - N a c) V W := by
  simp only [bil, sum4]
  ring

theorem term_lower_sq (d u v δ : ℝ) (hd : |d| ≤ δ) :
    -(δ * ((u ^ 2 + v ^ 2) / 2)) ≤ d * u * v := by
  have h1 : |u * v| ≤ (u ^ 2 + v ^ 2) / 2 := by
    rw [abs_le]; constructor <;> nlinarith [sq_nonneg (u + v), sq_nonneg (u - v)]
  have h2 : |d * u * v| ≤ δ * ((u ^ 2 + v ^ 2) / 2) := by
    rw [mul_assoc, abs_mul]
    exact mul_le_mul hd h1 (abs_nonneg _) ((abs_nonneg d).trans hd)
  exact (neg_le_neg h2).trans (neg_abs_le _)

theorem term_lower_K (d u w δ K : ℝ) (hd : |d| ≤ δ) (huw : |u * w| ≤ K) :
    -(δ * K) ≤ d * u * w := by
  have h2 : |d * u * w| ≤ δ * K := by
    rw [mul_assoc, abs_mul]
    exact mul_le_mul hd huw (abs_nonneg _) ((abs_nonneg d).trans hd)
  exact (neg_le_neg h2).trans (neg_abs_le _)

theorem quad_lower (D : I → I → ℝ) (δ : ℝ) (hD : ∀ a c, |D a c| ≤ δ) (V : I → ℝ) :
    -(4 * δ * (V 0 ^ 2 + V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2)) ≤ bil D V V := by
  have h := fun a c => term_lower_sq (D a c) (V a) (V c) δ (hD a c)
  simp only [bil, sum4]
  linarith [h 0 0, h 0 1, h 0 2, h 0 3, h 1 0, h 1 1, h 1 2, h 1 3,
    h 2 0, h 2 1, h 2 2, h 2 3, h 3 0, h 3 1, h 3 2, h 3 3]

theorem bil_lower_K (D : I → I → ℝ) (δ K : ℝ) (hD : ∀ a c, |D a c| ≤ δ)
    (V W : I → ℝ) (hVW : ∀ a c, |V a * W c| ≤ K) :
    -(16 * δ * K) ≤ bil D V W := by
  have h := fun a c => term_lower_K (D a c) (V a) (W c) δ K (hD a c) (hVW a c)
  simp only [bil, sum4]
  linarith [h 0 0, h 0 1, h 0 2, h 0 3, h 1 0, h 1 1, h 1 2, h 1 3,
    h 2 0, h 2 1, h 2 2, h 2 3, h 3 0, h 3 1, h 3 2, h 3 3]

/-- Causal vectors of a metric entrywise `δ`-close to `η` lie in the cone
`|v|^2 ≤ s V0^2`. -/
theorem causal_cone_bound (g : I → I → ℝ) (s δ : ℝ) (hs : 1 ≤ s) (hδ0 : 0 ≤ δ)
    (hδ : 8 * δ * (s + 1) ≤ s - 1) (hg : ∀ a c, |g a c - eta a c| ≤ δ)
    (V : I → ℝ) (hV : bil g V V ≤ 0) :
    V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2 ≤ s * V 0 ^ 2 := by
  have hsplit := bil_split g eta V V
  have hq := quad_lower (fun a c => g a c - eta a c) δ hg V
  rw [bil_eta] at hsplit
  set A := V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2 with hA
  set B := V 0 ^ 2 with hB
  have hA0 : 0 ≤ A := by positivity
  have hB0 : 0 ≤ B := by positivity
  have key : A * (1 - 4 * δ) ≤ B * (1 + 4 * δ) := by nlinarith
  have hpos : 0 < 1 - 4 * δ := by nlinarith
  have hk2 : B * (1 + 4 * δ) ≤ s * B * (1 - 4 * δ) := by nlinarith
  have : (A - s * B) * (1 - 4 * δ) ≤ 0 := by nlinarith
  nlinarith

theorem sq_le_of_cone (V : I → ℝ) (s : ℝ) (hs : 1 ≤ s)
    (hV : V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2 ≤ s * V 0 ^ 2) (a : I) :
    V a ^ 2 ≤ s * V 0 ^ 2 := by
  have h0 : 0 ≤ V 0 ^ 2 := sq_nonneg _
  have h1 := sq_nonneg (V 1)
  have h2 := sq_nonneg (V 2)
  have h3 := sq_nonneg (V 3)
  fin_cases a <;> simp <;> nlinarith

theorem prod_bound (V W : I → ℝ) (s : ℝ) (hs : 1 ≤ s) (hV0 : 0 < V 0) (hW0 : 0 < W 0)
    (hV : V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2 ≤ s * V 0 ^ 2)
    (hW : W 1 ^ 2 + W 2 ^ 2 + W 3 ^ 2 ≤ s * W 0 ^ 2) (a c : I) :
    |V a * W c| ≤ s * V 0 * W 0 := by
  apply abs_le_of_sq_le_sq _ (by positivity)
  have ha := sq_le_of_cone V s hs hV a
  have hc := sq_le_of_cone W s hs hW c
  have : (V a * W c) ^ 2 = V a ^ 2 * W c ^ 2 := by ring
  rw [this]
  have : (s * V 0 * W 0) ^ 2 = (s * V 0 ^ 2) * (s * W 0 ^ 2) := by ring
  rw [this]
  exact mul_le_mul ha hc (sq_nonneg _) (by positivity)

theorem dot_bound (V W : I → ℝ) (s : ℝ) (hs : 1 ≤ s) (hV0 : 0 < V 0) (hW0 : 0 < W 0)
    (hV : V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2 ≤ s * V 0 ^ 2)
    (hW : W 1 ^ 2 + W 2 ^ 2 + W 3 ^ 2 ≤ s * W 0 ^ 2) :
    |V 1 * W 1 + V 2 * W 2 + V 3 * W 3| ≤ s * V 0 * W 0 := by
  apply abs_le_of_sq_le_sq _ (by positivity)
  have cs : (V 1 * W 1 + V 2 * W 2 + V 3 * W 3) ^ 2 ≤
      (V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2) * (W 1 ^ 2 + W 2 ^ 2 + W 3 ^ 2) := by
    nlinarith [sq_nonneg (V 1 * W 2 - V 2 * W 1), sq_nonneg (V 1 * W 3 - V 3 * W 1),
      sq_nonneg (V 2 * W 3 - V 3 * W 2)]
  have : (s * V 0 * W 0) ^ 2 = (s * V 0 ^ 2) * (s * W 0 ^ 2) := by ring
  rw [this]
  exact cs.trans (mul_le_mul hV hW (by positivity) (by positivity))

/-- Lower bound for the diagonal stress on the cone `|v|^2 ≤ s V0^2`. -/
theorem diag_lower (e p s : ℝ) (V W : I → ℝ) (hs : 1 ≤ s) (hV0 : 0 < V 0) (hW0 : 0 < W 0)
    (hV : V 1 ^ 2 + V 2 ^ 2 + V 3 ^ 2 ≤ s * V 0 ^ 2)
    (hW : W 1 ^ 2 + W 2 ^ 2 + W 3 ^ 2 ≤ s * W 0 ^ 2) :
    (e - |p| * s) * (V 0 * W 0) ≤ bil (diagT e p) V W := by
  rw [bil_diagT]
  have hd := dot_bound V W s hs hV0 hW0 hV hW
  set x := V 1 * W 1 + V 2 * W 2 + V 3 * W 3
  have h1 : -(|p| * (s * V 0 * W 0)) ≤ p * x := by
    have : |p * x| ≤ |p| * (s * V 0 * W 0) := by
      rw [abs_mul]; exact mul_le_mul_of_nonneg_left hd (abs_nonneg p)
    exact (neg_le_neg this).trans (neg_abs_le _)
  nlinarith

/-- General persistence lemma: a metric field continuous at 0 with `g(0) = η` and a
stress field continuous at 0 with `T(0) = diag(e,p,p,p)`, `|p| < e`, give strict DEC
(with respect to the cone of `g(x)`) on a ball around 0.  The radius is produced by
continuity and depends on the given fields. -/
theorem strictDEC_nhds (gF TF : (I → ℝ) → I → I → ℝ) (e p : ℝ)
    (hg : ContinuousAt gF 0) (hT : ContinuousAt TF 0)
    (hg0 : gF 0 = eta) (hT0 : TF 0 = diagT e p) (hep : |p| < e) :
    ∃ r > 0, ∀ x : I → ℝ, ‖x‖ < r → StrictDEC (gF x) (TF x) := by
  set d := e - |p| with hd
  have hdpos : 0 < d := by linarith
  have hp0 : 0 ≤ |p| := abs_nonneg p
  set t := d / (2 * (|p| + 1)) with ht
  have htpos : 0 < t := by positivity
  set s := 1 + t with hsdef
  have hs1 : 1 ≤ s := by linarith
  have hspos : 0 < s := by linarith
  have hps : |p| * s ≤ |p| + d / 2 := by
    have h1 : |p| * t = d / 2 * (|p| / (|p| + 1)) := by
      rw [ht]; field_simp
    have h2 : |p| / (|p| + 1) ≤ 1 := by
      rw [div_le_one (by positivity)]; linarith
    have h3 : |p| * t ≤ d / 2 := by
      rw [h1]; nlinarith
    rw [hsdef]; nlinarith
  set m := d / 2 with hm
  have hmpos : 0 < m := by positivity
  have hem : m ≤ e - |p| * s := by linarith
  set δg := t / (8 * (s + 1)) with hδg
  have hδgpos : 0 < δg := by positivity
  have hδgle : 8 * δg * (s + 1) ≤ s - 1 := by
    rw [hδg]; field_simp; linarith
  set δT := m / (32 * s) with hδT
  have hδTpos : 0 < δT := by positivity
  obtain ⟨r1, hr1, H1⟩ := Metric.continuousAt_iff.mp hg δg hδgpos
  obtain ⟨r2, hr2, H2⟩ := Metric.continuousAt_iff.mp hT δT hδTpos
  refine ⟨min r1 r2, lt_min hr1 hr2, ?_⟩
  intro x hx
  have hx1 : dist x 0 < r1 := by
    rw [dist_zero_right]; exact lt_of_lt_of_le hx (min_le_left _ _)
  have hx2 : dist x 0 < r2 := by
    rw [dist_zero_right]; exact lt_of_lt_of_le hx (min_le_right _ _)
  have Hg := H1 hx1
  have HT := H2 hx2
  have hgent : ∀ a c, |gF x a c - eta a c| ≤ δg := by
    intro a c
    have h1 : dist (gF x a c) (gF 0 a c) ≤ dist (gF x) (gF 0) :=
      (dist_le_pi_dist (gF x a) (gF 0 a) c).trans (dist_le_pi_dist (gF x) (gF 0) a)
    have e1 : gF 0 a c = eta a c := by rw [hg0]
    rw [Real.dist_eq, e1] at h1
    linarith
  have hTent : ∀ a c, |TF x a c - diagT e p a c| ≤ δT := by
    intro a c
    have h1 : dist (TF x a c) (TF 0 a c) ≤ dist (TF x) (TF 0) :=
      (dist_le_pi_dist (TF x a) (TF 0 a) c).trans (dist_le_pi_dist (TF x) (TF 0) a)
    have e1 : TF 0 a c = diagT e p a c := by rw [hT0]
    rw [Real.dist_eq, e1] at h1
    linarith
  intro V W _ _ hV hW
  have hVc := causal_cone_bound (gF x) s δg hs1 hδgpos.le hδgle hgent V hV.1
  have hWc := causal_cone_bound (gF x) s δg hs1 hδgpos.le hδgle hgent W hW.1
  have hVW := prod_bound V W s hs1 hV.2 hW.2 hVc hWc
  have hlow0 := diag_lower e p s V W hs1 hV.2 hW.2 hVc hWc
  have hpert := bil_lower_K (fun a c => TF x a c - diagT e p a c) δT (s * V 0 * W 0)
    hTent V W hVW
  have hsplit := bil_split (TF x) (diagT e p) V W
  have hVW0 : 0 < V 0 * W 0 := mul_pos hV.2 hW.2
  have h16 : 16 * δT * (s * V 0 * W 0) = m / 2 * (V 0 * W 0) := by
    rw [hδT]; field_simp; ring
  rw [hsplit]
  have hlow1 : m * (V 0 * W 0) ≤ (e - |p| * s) * (V 0 * W 0) :=
    mul_le_mul_of_nonneg_right hem hVW0.le
  nlinarith

/-! ## A3 strict DEC at the origin, and boundary negative control -/

theorem stress_conf_origin_diag (b lam Λ κ : ℝ) :
    stress (gConf b lam) Λ κ 0 = diagT ((6*b - Λ)/κ) (Λ/κ) := by
  funext a c
  rw [stress_conf_origin]
  rfl

theorem origin_margin (b Λ κ : ℝ) (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ) :
    |Λ/κ| < (6*b - Λ)/κ := by
  rw [abs_lt]
  constructor
  · have : (6*b - Λ)/κ + Λ/κ = 6*b/κ := by ring
    have : 0 < 6*b/κ := by positivity
    linarith
  · have hdiff : 0 < (6*b - 2*Λ)/κ := div_pos (by linarith) hκ
    have : (6*b - Λ)/κ - Λ/κ = (6*b - 2*Λ)/κ := by ring
    linarith

/-- **A3 strict_dec_origin.** -/
theorem strict_dec_origin (b lam Λ κ : ℝ) (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ) :
    StrictDEC eta (stress (gConf b lam) Λ κ 0) := by
  rw [stress_conf_origin_diag]
  intro V W _ _ hV hW
  have hc : ∀ U : I → ℝ, bil eta U U ≤ 0 → U 1 ^ 2 + U 2 ^ 2 + U 3 ^ 2 ≤ 1 * U 0 ^ 2 := by
    intro U hU
    rw [bil_eta] at hU
    nlinarith
  have h := diag_lower ((6*b - Λ)/κ) (Λ/κ) 1 V W le_rfl hV.2 hW.2 (hc V hV.1) (hc W hW.1)
  have hm := origin_margin b Λ κ hb hΛ hκ
  have hVW0 : 0 < V 0 * W 0 := mul_pos hV.2 hW.2
  have : 0 < ((6*b - Λ)/κ - |Λ/κ| * 1) * (V 0 * W 0) := by
    apply mul_pos _ hVW0; linarith
  linarith

/-- Negative control: at the boundary `Λ = 3b` strict DEC fails at the origin. -/
theorem strict_dec_origin_fails_at_boundary (b lam κ : ℝ) :
    ¬ StrictDEC eta (stress (gConf b lam) (3*b) κ 0) := by
  intro h
  rw [stress_conf_origin_diag] at h
  let V : I → ℝ := fun a => if a = 0 then 1 else if a = 1 then 1 else 0
  let W : I → ℝ := fun a => if a = 0 then 1 else if a = 1 then -1 else 0
  have hV0 : V ≠ 0 := by
    intro hv; have := congrFun hv 0; simp [V] at this
  have hW0 : W ≠ 0 := by
    intro hw; have := congrFun hw 0; simp [W] at this
  have hVc : FutureCausal eta V := by
    refine ⟨?_, ?_⟩
    · rw [bil_eta]; simp [V]
    · simp [V]
  have hWc : FutureCausal eta W := by
    refine ⟨?_, ?_⟩
    · rw [bil_eta]; simp [W]
    · simp [W]
  have := h V W hV0 hW0 hVc hWc
  rw [bil_diagT] at this
  simp [V, W] at this
  have e : (6 * b - 3 * b) / κ - 3 * b / κ = 0 := by ring
  linarith

/-! ## A4 strict DEC on a parameter-dependent neighborhood -/

theorem gConf_continuous (b lam : ℝ) : Continuous (gConf b lam) := by
  apply continuous_pi; intro a; apply continuous_pi; intro c
  unfold gConf; fun_prop

theorem stress_conf_continuous (b lam Λ κ : ℝ) : Continuous (stress (gConf b lam) Λ κ) := by
  apply continuous_pi; intro a; apply continuous_pi; intro c
  have e : (fun x => stress (gConf b lam) Λ κ x a c) = fun x =>
      (conformalEinstein (pPhi b lam x) (hPhi b lam x) a c + Λ * gConf b lam x a c) / κ := by
    funext x; rw [stress, Ein_conf]
  rw [e]
  unfold conformalEinstein boxH normP sum4 gConf
  fun_prop

/-- **A4 strict_dec_neighborhood.** For fixed `b, lam, Λ, κ` there is a radius `r > 0`
(depending on these parameters; no uniformity in `lam` is claimed) such that strict DEC
holds at every `x` with `‖x‖ < r`, with respect to the causal cone of `g(x)`, which by
A1 is the cone of `η`. -/
theorem strict_dec_neighborhood (b lam Λ κ : ℝ) (hb : 0 < b) (hΛ : Λ < 3*b) (hκ : 0 < κ) :
    ∃ r > 0, ∀ x : I → ℝ, ‖x‖ < r →
      StrictDEC (gConf b lam x) (stress (gConf b lam) Λ κ x) ∧
      StrictDEC eta (stress (gConf b lam) Λ κ x) := by
  obtain ⟨r, hr, H⟩ := strictDEC_nhds (gConf b lam) (stress (gConf b lam) Λ κ)
    ((6*b - Λ)/κ) (Λ/κ) (gConf_continuous b lam).continuousAt
    (stress_conf_continuous b lam Λ κ).continuousAt (gConf_origin b lam)
    (stress_conf_origin_diag b lam Λ κ) (origin_margin b Λ κ hb hΛ hκ)
  refine ⟨r, hr, fun x hx => ⟨H x hx, ?_⟩⟩
  intro V W hV hW hVc hWc
  have hcone := (conformal_lorentz_everywhere b lam x).2.2.2.1
  exact H x hx V W hV hW ⟨(hcone V).2 hVc.1, hVc.2⟩ ⟨(hcone W).2 hWc.1, hWc.2⟩

end G05AConformalDEC
