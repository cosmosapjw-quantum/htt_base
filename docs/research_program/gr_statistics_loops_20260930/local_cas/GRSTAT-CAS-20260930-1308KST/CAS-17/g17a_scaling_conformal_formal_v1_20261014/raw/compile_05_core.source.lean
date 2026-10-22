import Mathlib
import C01

/-!
# G17-A core: chart-level constant scale (CAS17-C02) and general conformal
# factor (CAS17-C03)

Scope (see `FROZEN_TARGETS.md`): one coordinate chart with length-valued
coordinates (`x⁰ = c t`), signature `(-,+,+,+)`.  A metric is a component field
`g : Pt n → Arr2 n`.  Christoffel symbols are *defined* by the Levi-Civita
formula from `fderiv` of `g`; covariant derivatives, the Riemann tensor, the
contravariant acceleration `A^a = U^b ∇_b U^a`, the covariant acceleration
`A_b = U^a ∇_a U_b` and `B_ab = ∇_(a U_b)` are *defined* from them.  No
transformation law is assumed; every scaling / conformal law below is proved.

Sources (SOURCE_RECOVERY.md): ADDED_BOOK_INTEGRATION.md:46-96,
COMMON_SPEC.md:4-23, OPTICAL_THEOREMS.md:9-50, NATIVE_INFERENCE_THEOREMS.md:9-35,
FINITE_DISTANCE_THEOREM.md:7-11, CAS-17.json:119-120.
`Z` means `1+z` (FINITE_DISTANCE_THEOREM.md:7, OPTICAL_THEOREMS.md:22).
Frame-level contractions reuse the reviewed CAS17-C01 module unchanged.
-/

noncomputable section

open Finset

namespace G17A

/-! ## Definitions -/

/-- Chart point: length-valued coordinate components (`x⁰ = c t`). -/
abbrev Pt (n : ℕ) := Fin n → ℝ

/-- A 2-index component array (kept as a plain Pi type so it carries a norm). -/
abbrev Arr2 (n : ℕ) := Fin n → Fin n → ℝ

/-- Length-valued chart coordinates from time and spatial components: `x⁰ = c t`. -/
def chartPoint (c t : ℝ) (xs : Fin 3 → ℝ) : Pt 4 := Fin.cons (c * t) xs

section Defs
variable {n : ℕ}

/-- Coordinate partial derivative `∂_b f (x)`. -/
def pd {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (f : Pt n → E) (x : Pt n) (b : Fin n) : E :=
  fderiv ℝ f x (Pi.single b 1)

/-- Contravariant inverse metric `g^{ab}`. -/
def ginv (g : Pt n → Arr2 n) (x : Pt n) : Matrix (Fin n) (Fin n) ℝ :=
  (Matrix.of (g x))⁻¹

/-- Levi-Civita Christoffel symbols `Γ^a_{bc}`. -/
def chris (g : Pt n → Arr2 n) (x : Pt n) (a b c : Fin n) : ℝ :=
  (1 / 2 : ℝ) * ∑ d, ginv g x a d * (pd g x b d c + pd g x c d b - pd g x d b c)

/-- `∇_b V^a` for a vector field with contravariant components. -/
def covVec (g : Pt n → Arr2 n) (V : Pt n → Pt n) (x : Pt n) (b a : Fin n) : ℝ :=
  pd V x b a + ∑ c, chris g x a b c * V x c

/-- `V^b ∇_b V^a`. -/
def selfCov (g : Pt n → Arr2 n) (V : Pt n → Pt n) (x : Pt n) (a : Fin n) : ℝ :=
  ∑ b, V x b * covVec g V x b a

/-- Lowered (covariant) components `V_b = g_{ba} V^a`. -/
def lower (g : Pt n → Arr2 n) (V : Pt n → Pt n) : Pt n → Pt n :=
  fun y b => ∑ a, g y b a * V y a

/-- `∇_a ω_b` for a covector field. -/
def covCov (g : Pt n → Arr2 n) (ω : Pt n → Pt n) (x : Pt n) (a b : Fin n) : ℝ :=
  pd ω x a b - ∑ c, chris g x c a b * ω x c

/-- Coordinate covariant rate tensor `B_ab = ∇_(a U_b)` (derivative first). -/
def Bcov (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) (a b : Fin n) : ℝ :=
  (covCov g (lower g U) x a b + covCov g (lower g U) x b a) / 2

/-- Covariant acceleration `A_b = U^a ∇_a U_b`. -/
def Acov (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) (b : Fin n) : ℝ :=
  ∑ a, U x a * covCov g (lower g U) x a b

/-- Riemann tensor, COMMON_SPEC.md:23 convention:
`R^a_bcd = ∂_c Γ^a_db - ∂_d Γ^a_cb + Γ^a_ce Γ^e_db - Γ^a_de Γ^e_cb`. -/
def riemann (g : Pt n → Arr2 n) (x : Pt n) (a b c d : Fin n) : ℝ :=
  pd (fun y => chris g y a d b) x c - pd (fun y => chris g y a c b) x d
    + ∑ e, (chris g x a c e * chris g x e d b - chris g x a d e * chris g x e c b)

/-- Metric contraction `g(V,W)`. -/
def contr (G : Arr2 n) (V W : Pt n) : ℝ := ∑ a, ∑ b, G a b * V a * W b

/-- Inverse-metric contraction of a covector `g^{ab} k_a k_b`. -/
def covNorm (Gi : Matrix (Fin n) (Fin n) ℝ) (k : Pt n) : ℝ := ∑ a, ∑ b, Gi a b * k a * k b

/-- Spatial projector `h^{ab} = g^{ab} + U^a U^b / c²`. -/
def hinv (g : Pt n → Arr2 n) (U : Pt n → Pt n) (c : ℝ) (x : Pt n) (a b : Fin n) : ℝ :=
  ginv g x a b + U x a * U x b / c ^ 2

/-- Conformal metric `e^{2φ} g`. -/
def conf (φ : Pt n → ℝ) (g : Pt n → Arr2 n) : Pt n → Arr2 n :=
  fun y => Real.exp (2 * φ y) • g y

/-- Physical velocity `U = c u`. -/
def physVel (c : ℝ) (u : Pt n → Pt n) : Pt n → Pt n := fun y => c • u y

/-- Contravariant coordinate components. -/
structure Contra (n : ℕ) where
  comp : Fin n → ℝ

/-- Covariant coordinate components. -/
structure Cov (n : ℕ) where
  comp : Fin n → ℝ

/-- Measured (orthonormal-tetrad) components. -/
structure Measured (n : ℕ) where
  comp : Fin n → ℝ

/-- Contravariant acceleration `A^a = U^b ∇_b U^a`. -/
def accelContra (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) : Contra n :=
  ⟨selfCov g U x⟩

/-- Covariant acceleration `A_b = U^a ∇_a U_b`. -/
def accelCov (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) : Cov n :=
  ⟨Acov g U x⟩

/-- Tetrad `E α` (coordinate components `e_α^a`) orthonormal for `G` with signs `η`. -/
def Orthonormal (G : Arr2 n) (E : Fin n → Pt n) (η : Fin n → ℝ) : Prop :=
  ∀ α β, contr G (E α) (E β) = if α = β then η α else 0

/-- Measured tetrad components of a covariant 2-tensor. -/
def tet2 (T : Arr2 n) (E : Fin n → Pt n) (α β : Fin n) : ℝ :=
  ∑ a, ∑ b, T a b * E α a * E β b

/-- Measured tetrad components of a vector, `V^α = η_α g(E_α, V)`. -/
def tetVec (G : Arr2 n) (E : Fin n → Pt n) (η : Fin n → ℝ) (V : Pt n) : Measured n :=
  ⟨fun α => η α * contr G (E α) V⟩

/-- Declared positive (Euclidean) norm of measured components. -/
def measNorm (m : Measured n) : ℝ := Real.sqrt (∑ α, m.comp α ^ 2)

/-- Measured frequency `ν = -k_a U^a / 2π` of eikonal covector `k` for physical velocity `U`. -/
def freq (k U : Pt n) : ℝ := -(∑ a, k a * U a) / (2 * Real.pi)

/-- Endpoint ratio `Z = 1+z = ν_emitted / ν_observed`. -/
def onePlusZ (ke Ue ko Uo : Pt n) : ℝ := freq ke Ue / freq ko Uo

end Defs

/-- `z = Z - 1`. -/
def zOf (Z : ℝ) : ℝ := Z - 1

/-! ### Frame-level contractions (reuse CAS17C01) -/

open CAS17C01 in
/-- `g_λ = λ² g` on the C01 orthonormal-frame vectors. -/
def scaledLorentz (lam : ℝ) (a b : Vec) : ℝ := lam ^ 2 * lorentz a b

open CAS17C01 in
/-- `K = -o + n`. -/
def Kvec (o n : Vec) : Vec := ⟨-o.t + n.t, -o.x + n.x, -o.y + n.y, -o.z + n.z⟩

open CAS17C01 in
/-- `γ = -B(u,o)` for a general bilinear form. -/
def gammaW (B : Vec → Vec → ℝ) (u o : Vec) : ℝ := -B u o

open CAS17C01 in
/-- `u - γ o`. -/
def relW (B : Vec → Vec → ℝ) (u o : Vec) : Vec :=
  ⟨u.t - gammaW B u o * o.t, u.x - gammaW B u o * o.x,
   u.y - gammaW B u o * o.y, u.z - gammaW B u o * o.z⟩

open CAS17C01 in
/-- `β² = B(u-γo,u-γo)/γ²`. -/
def betaSqW (B : Vec → Vec → ℝ) (u o : Vec) : ℝ :=
  B (relW B u o) (relW B u o) / (gammaW B u o) ^ 2

/-! ## Generic algebra -/

section Algebra
variable {n : ℕ}

theorem contr_smul (G : Arr2 n) (p q r : ℝ) (V W : Pt n) :
    contr (p • G) (q • V) (r • W) = p * q * r * contr G V W := by
  unfold contr
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun b _ => ?_
  simp only [Pi.smul_apply, smul_eq_mul]
  ring

theorem sum_one_mul (a : Fin n) (f : Fin n → ℝ) :
    ∑ c, (1 : Matrix (Fin n) (Fin n) ℝ) a c * f c = f a := by
  simp [Matrix.one_apply]

theorem inv_smul_real (M : Matrix (Fin n) (Fin n) ℝ) (k : ℝ) (hk : k ≠ 0)
    (h : IsUnit M.det) : (k • M)⁻¹ = k⁻¹ • M⁻¹ := by
  have := Matrix.inv_smul' M (Units.mk0 k hk) h
  simpa using this

theorem pd_const_smul {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (f : Pt n → E) (x : Pt n) (k : ℝ) (b : Fin n) :
    pd (fun y => k • f y) x b = k • pd f x b := by
  unfold pd
  rw [show (fun y => k • f y) = k • f from rfl, fderiv_const_smul_field]
  rfl

theorem ginv_const_smul (g : Pt n → Arr2 n) (x : Pt n) (k : ℝ) (hk : k ≠ 0)
    (hdet : IsUnit (Matrix.of (g x)).det) :
    ginv (fun y => k • g y) x = k⁻¹ • ginv g x := by
  unfold ginv
  rw [show Matrix.of (k • g x) = k • Matrix.of (g x) from (Matrix.smul_of _ _).symm,
    inv_smul_real _ _ hk hdet]

theorem inv_mul_entry (g : Pt n → Arr2 n) (x : Pt n) (hdet : IsUnit (Matrix.of (g x)).det)
    (a c : Fin n) : ∑ d, ginv g x a d * g x d c = (1 : Matrix (Fin n) (Fin n) ℝ) a c := by
  have := congrFun (congrFun (Matrix.nonsing_inv_mul _ hdet) a) c
  simpa [Matrix.mul_apply, ginv] using this

end Algebra

/-! ## C02 — constant scale -/

section C02Frame
open CAS17C01

theorem unit_preserved (lam : ℝ) (hlam : lam ≠ 0) (a b : Vec) :
    scaledLorentz lam (scale lam⁻¹ a) (scale lam⁻¹ b) = lorentz a b := by
  unfold scaledLorentz
  rw [lorentz_scale]
  field_simp

theorem lorentz_Kvec_self (o n : Vec) :
    lorentz (Kvec o n) (Kvec o n) = lorentz o o - 2 * lorentz o n + lorentz n n := by
  simp only [lorentz, Kvec]
  ring

theorem lorentz_o_Kvec (o n : Vec) : lorentz o (Kvec o n) = -lorentz o o + lorentz o n := by
  simp only [lorentz, Kvec]
  ring

theorem null_normalization_scale (lam μ : ℝ) (hlam : 0 < lam) (o n : Vec)
    (hoo : lorentz o o = -1) (hon : lorentz o n = 0) (hnn : lorentz n n = 1) :
    scaledLorentz lam (scale μ (Kvec o n)) (scale μ (Kvec o n)) = 0 ∧
      (scaledLorentz lam (scale lam⁻¹ o) (scale μ (Kvec o n)) = 1 ↔ μ = lam⁻¹) := by
  have hl : lam ≠ 0 := hlam.ne'
  refine ⟨?_, ?_⟩
  · unfold scaledLorentz
    rw [lorentz_scale, lorentz_Kvec_self, hoo, hon, hnn]
    ring
  · unfold scaledLorentz
    rw [lorentz_scale, lorentz_o_Kvec, hoo, hon]
    constructor
    · intro h
      field_simp at h
      field_simp
      linarith
    · intro h
      subst h
      field_simp

theorem intercept_invariant (lam : ℝ) (hlam : lam ≠ 0) (o n u : Vec) :
    scaledLorentz lam (scale lam⁻¹ (Kvec o n)) (scale lam⁻¹ u) = lorentz (Kvec o n) u :=
  unit_preserved lam hlam _ _

theorem intercept_formula (n u : Vec) (hn : n.t = 0) :
    lorentz (Kvec ⟨1, 0, 0, 0⟩ n) u = u.t + n.x * u.x + n.y * u.y + n.z * u.z := by
  simp only [lorentz, Kvec, hn]
  ring

theorem gamma_scale (lam : ℝ) (hlam : lam ≠ 0) (u o : Vec) :
    gammaW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o) = CAS17C01.gamma u o := by
  unfold gammaW CAS17C01.gamma
  rw [unit_preserved lam hlam]

theorem betaSqW_lorentz (u o : Vec) : betaSqW lorentz u o = CAS17C01.betaSq u o := rfl

theorem relW_scale (lam : ℝ) (hlam : lam ≠ 0) (u o : Vec) :
    relW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o) =
      scale lam⁻¹ (relativeSpatial u o) := by
  unfold relW
  rw [gamma_scale lam hlam]
  simp only [scale, relativeSpatial]
  congr 1 <;> ring

theorem betaSq_scale (lam : ℝ) (hlam : lam ≠ 0) (u o : Vec) :
    betaSqW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o) = CAS17C01.betaSq u o := by
  unfold betaSqW
  rw [relW_scale lam hlam, gamma_scale lam hlam, unit_preserved lam hlam]
  rfl

theorem beta_scale (lam : ℝ) (hlam : lam ≠ 0) (u o : Vec) :
    Real.sqrt (betaSqW (scaledLorentz lam) (scale lam⁻¹ u) (scale lam⁻¹ o)) =
      CAS17C01.beta u o := by
  rw [betaSq_scale lam hlam]
  rfl

end C02Frame

section C02Chart
variable {n : ℕ}

theorem chris_scale (g : Pt n → Arr2 n) (x : Pt n) (lam : ℝ) (hlam : lam ≠ 0)
    (hdet : IsUnit (Matrix.of (g x)).det) (a b c : Fin n) :
    chris (fun y => lam ^ 2 • g y) x a b c = chris g x a b c := by
  have hl2 : lam ^ 2 ≠ 0 := pow_ne_zero 2 hlam
  unfold chris
  rw [ginv_const_smul g x _ hl2 hdet]
  simp only [pd_const_smul, Matrix.smul_apply, Pi.smul_apply, smul_eq_mul]
  congr 1
  refine Finset.sum_congr rfl fun d _ => ?_
  field_simp

theorem physVel_scale (c lam : ℝ) (u : Pt n → Pt n) :
    physVel c (fun y => lam⁻¹ • u y) = fun y => lam⁻¹ • physVel c u y := by
  funext y
  simp only [physVel, smul_smul, mul_comm]

theorem velocity_norm_scale (G : Arr2 n) (U : Pt n) (lam : ℝ) (hlam : lam ≠ 0) :
    contr (lam ^ 2 • G) (lam⁻¹ • U) (lam⁻¹ • U) = contr G U U := by
  rw [contr_smul]
  field_simp

theorem accelContra_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) (lam : ℝ)
    (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det) (a : Fin n) :
    (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp a =
      (lam⁻¹) ^ 2 * (accelContra g U x).comp a := by
  simp only [accelContra, selfCov, covVec, chris_scale g x lam hlam hdet, pd_const_smul,
    Pi.smul_apply, smul_eq_mul]
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun b _ => ?_
  have : ∑ c, chris g x a b c * (lam⁻¹ * U x c) = lam⁻¹ * ∑ c, chris g x a b c * U x c := by
    rw [Finset.mul_sum]
    exact Finset.sum_congr rfl fun c _ => by ring
  rw [this]
  ring

theorem lower_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (lam : ℝ) (hlam : lam ≠ 0) :
    lower (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) = fun y => lam • lower g U y := by
  funext y b
  simp only [lower, Pi.smul_apply, smul_eq_mul]
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun a _ => ?_
  field_simp

theorem covCov_scale (g : Pt n → Arr2 n) (ω : Pt n → Pt n) (x : Pt n) (lam k : ℝ)
    (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det) (a b : Fin n) :
    covCov (fun y => lam ^ 2 • g y) (fun y => k • ω y) x a b = k * covCov g ω x a b := by
  simp only [covCov, chris_scale g x lam hlam hdet, pd_const_smul, Pi.smul_apply, smul_eq_mul]
  rw [mul_sub, Finset.mul_sum]
  congr 1
  exact Finset.sum_congr rfl fun c _ => by ring

theorem Bcov_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) (lam : ℝ)
    (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det) (a b : Fin n) :
    Bcov (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x a b = lam * Bcov g U x a b := by
  unfold Bcov
  rw [lower_scale g U lam hlam, covCov_scale g _ x lam lam hlam hdet,
    covCov_scale g _ x lam lam hlam hdet]
  ring

theorem accelCov_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) (lam : ℝ)
    (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det) (b : Fin n) :
    (accelCov (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp b =
      (accelCov g U x).comp b := by
  simp only [accelCov, Acov]
  rw [lower_scale g U lam hlam]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [covCov_scale g _ x lam lam hlam hdet]
  simp only [Pi.smul_apply, smul_eq_mul]
  field_simp

theorem orthonormal_scale (G : Arr2 n) (E : Fin n → Pt n) (η : Fin n → ℝ) (lam : ℝ)
    (hlam : lam ≠ 0) (h : Orthonormal G E η) :
    Orthonormal (lam ^ 2 • G) (fun α => lam⁻¹ • E α) η := by
  intro α β
  rw [velocity_norm_scale_gen G (E α) (E β) lam hlam]
  exact h α β
where
  velocity_norm_scale_gen (G : Arr2 n) (V W : Pt n) (lam : ℝ) (hlam : lam ≠ 0) :
      contr (lam ^ 2 • G) (lam⁻¹ • V) (lam⁻¹ • W) = contr G V W := by
    rw [contr_smul]
    field_simp

theorem B_measured_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n)
    (E : Fin n → Pt n) (lam : ℝ) (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det)
    (α β : Fin n) :
    tet2 (Bcov (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x) (fun γ => lam⁻¹ • E γ) α β =
      lam⁻¹ * tet2 (Bcov g U x) E α β := by
  unfold tet2
  simp only [Bcov_scale g U x lam hlam hdet, Pi.smul_apply, smul_eq_mul]
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun b _ => ?_
  field_simp

theorem accelContra_comp_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n) (lam : ℝ)
    (hlam : lam ≠ 0) (hdet : IsUnit (Matrix.of (g x)).det) :
    (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp =
      (lam⁻¹) ^ 2 • (accelContra g U x).comp := by
  funext a
  rw [accelContra_scale g U x lam hlam hdet a]
  rfl

theorem A_measured_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n)
    (E : Fin n → Pt n) (η : Fin n → ℝ) (lam : ℝ) (hlam : lam ≠ 0)
    (hdet : IsUnit (Matrix.of (g x)).det) (α : Fin n) :
    (tetVec (lam ^ 2 • g x) (fun γ => lam⁻¹ • E γ) η
        (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp).comp α =
      lam⁻¹ * (tetVec (g x) E η (accelContra g U x).comp).comp α := by
  simp only [tetVec]
  rw [accelContra_comp_scale g U x lam hlam hdet, contr_smul]
  field_simp

theorem A_measNorm_scale (g : Pt n → Arr2 n) (U : Pt n → Pt n) (x : Pt n)
    (E : Fin n → Pt n) (η : Fin n → ℝ) (lam : ℝ) (hlam : 0 < lam)
    (hdet : IsUnit (Matrix.of (g x)).det) :
    measNorm (tetVec (lam ^ 2 • g x) (fun γ => lam⁻¹ • E γ) η
        (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp) =
      lam⁻¹ * measNorm (tetVec (g x) E η (accelContra g U x).comp) := by
  unfold measNorm
  have h : ∀ α, (tetVec (lam ^ 2 • g x) (fun γ => lam⁻¹ • E γ) η
      (accelContra (fun y => lam ^ 2 • g y) (fun y => lam⁻¹ • U y) x).comp).comp α ^ 2 =
      (lam⁻¹) ^ 2 * (tetVec (g x) E η (accelContra g U x).comp).comp α ^ 2 := by
    intro α
    rw [A_measured_scale g U x E η lam hlam.ne' hdet α]
    ring
  simp only [h]
  rw [← Finset.mul_sum, Real.sqrt_mul (by positivity), Real.sqrt_sq (by positivity)]

theorem chris_scale_fun (g : Pt n → Arr2 n) (lam : ℝ) (hlam : lam ≠ 0)
    (hdet : ∀ y, IsUnit (Matrix.of (g y)).det) :
    chris (fun y => lam ^ 2 • g y) = chris g := by
  funext y a b c
  exact chris_scale g y lam hlam (hdet y) a b c

theorem riemann_scale (g : Pt n → Arr2 n) (x : Pt n) (lam : ℝ) (hlam : lam ≠ 0)
    (hdet : ∀ y, IsUnit (Matrix.of (g y)).det) (a b c d : Fin n) :
    riemann (fun y => lam ^ 2 • g y) x a b c d = riemann g x a b c d := by
  unfold riemann
  rw [chris_scale_fun g lam hlam hdet]

/-! ### Affine normalization, redshift and slope (constant scale) -/

theorem chart_null_normalization (G : Arr2 n) (o K : Pt n) (lam μ : ℝ) (hlam : 0 < lam)
    (hoK : contr G o K = 1) :
    contr (lam ^ 2 • G) (lam⁻¹ • o) (μ • K) = 1 ↔ μ = lam⁻¹ := by
  rw [contr_smul, hoK]
  have hl : lam ≠ 0 := hlam.ne'
  constructor
  · intro h
    field_simp at h
    field_simp
    linarith
  · intro h
    subst h
    field_simp

theorem affine_reparam (g : Pt n → Arr2 n) (γ : ℝ → Pt n) (lam s : ℝ) (hlam : lam ≠ 0)
    (hdet : IsUnit (Matrix.of (g (γ s))).det)
    (hgeo : ∀ a, deriv (deriv γ) s a +
      ∑ b, ∑ c, chris g (γ s) a b c * deriv γ s b * deriv γ s c = 0) :
    (fun t => γ (lam⁻¹ * t)) (lam * s) = γ s ∧
      deriv (fun t => γ (lam⁻¹ * t)) (lam * s) = lam⁻¹ • deriv γ s ∧
      ∀ a, deriv (deriv (fun t => γ (lam⁻¹ * t))) (lam * s) a +
        ∑ b, ∑ c, chris (fun y => lam ^ 2 • g y) (γ s) a b c *
          deriv (fun t => γ (lam⁻¹ * t)) (lam * s) b *
          deriv (fun t => γ (lam⁻¹ * t)) (lam * s) c = 0 := by
  have hs : lam⁻¹ * (lam * s) = s := by field_simp
  have hd1 : deriv (fun t => γ (lam⁻¹ * t)) = fun t => lam⁻¹ • deriv γ (lam⁻¹ * t) := by
    funext t
    exact deriv_comp_mul_left lam⁻¹ γ t
  have hd2 : ∀ t, deriv (deriv (fun t => γ (lam⁻¹ * t))) t =
      lam⁻¹ • lam⁻¹ • deriv (deriv γ) (lam⁻¹ * t) := by
    intro t
    rw [hd1, show (fun t => lam⁻¹ • deriv γ (lam⁻¹ * t)) =
      lam⁻¹ • (fun t => deriv γ (lam⁻¹ * t)) from rfl, deriv_const_smul_field,
      deriv_comp_mul_left]
  refine ⟨by simp only [hs], by rw [hd1]; simp only [hs], fun a => ?_⟩
  rw [hd2, hd1]
  simp only [hs, chris_scale g (γ s) lam hlam hdet, Pi.smul_apply, smul_eq_mul]
  have : ∑ b, ∑ c, chris g (γ s) a b c * (lam⁻¹ * deriv γ s b) * (lam⁻¹ * deriv γ s c) =
      (lam⁻¹) ^ 2 * ∑ b, ∑ c, chris g (γ s) a b c * deriv γ s b * deriv γ s c := by
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun b _ => ?_
    rw [Finset.mul_sum]
    exact Finset.sum_congr rfl fun c _ => by ring
  rw [this]
  have h := hgeo a
  linear_combination (lam⁻¹) ^ 2 * h

theorem freq_smul (k U : Pt n) (r : ℝ) : freq k (r • U) = r * freq k U := by
  unfold freq
  simp only [Pi.smul_apply, smul_eq_mul]
  rw [show ∑ a, k a * (r * U a) = r * ∑ a, k a * U a by
    rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun a _ => by ring]
  ring

theorem redshift_const_scale (ke Ue ko Uo : Pt n) (lam : ℝ) (hlam : lam ≠ 0) :
    onePlusZ ke (lam⁻¹ • Ue) ko (lam⁻¹ • Uo) = onePlusZ ke Ue ko Uo := by
  unfold onePlusZ
  rw [freq_smul, freq_smul]
  exact mul_div_mul_left _ _ (inv_ne_zero hlam)

end C02Chart

theorem slope_scale (zf zl : ℝ → ℝ) (lam H c : ℝ) (hlam : 0 < lam)
    (hrel : ∀ D, 0 ≤ D → zl (lam * D) = zf D)
    (hz : HasDerivWithinAt zf (H / c) (Set.Ici 0) 0) :
    HasDerivWithinAt zl (lam⁻¹ * H / c) (Set.Ici 0) 0 := by
  have hz' : HasDerivWithinAt zf (H / c) (Set.Ici 0) (lam⁻¹ * 0) := by simpa using hz
  have hlin : HasDerivWithinAt (fun D : ℝ => lam⁻¹ * D) lam⁻¹ (Set.Ici 0) 0 := by
    simpa using ((hasDerivAt_id (0 : ℝ)).const_mul lam⁻¹).hasDerivWithinAt
  have hmaps : Set.MapsTo (fun D : ℝ => lam⁻¹ * D) (Set.Ici 0) (Set.Ici 0) := by
    intro D hD
    exact mul_nonneg (inv_nonneg.mpr hlam.le) hD
  have hcomp := hz'.comp (0 : ℝ) hlin hmaps
  have heq : Set.EqOn zl (zf ∘ fun D : ℝ => lam⁻¹ * D) (Set.Ici 0) := by
    intro D hD
    simp only [Function.comp]
    rw [← hrel (lam⁻¹ * D) (mul_nonneg (inv_nonneg.mpr hlam.le) hD)]
    congr 1
    field_simp
  have h0 : zl 0 = (zf ∘ fun D : ℝ => lam⁻¹ * D) 0 := heq (Set.left_mem_Ici)
  have := hcomp.congr heq h0
  convert this using 1
  ring

/-! ## C03 — general conformal factor -/

section C03
variable {n : ℕ}

theorem pd_expsmul {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (φ : Pt n → ℝ) (V : Pt n → E) (x : Pt n) (m : ℝ) (hφ : DifferentiableAt ℝ φ x)
    (hV : DifferentiableAt ℝ V x) (b : Fin n) :
    pd (fun y => Real.exp (m * φ y) • V y) x b =
      Real.exp (m * φ x) • pd V x b + (m * Real.exp (m * φ x) * pd φ x b) • V x := by
  have h := ((hφ.hasFDerivAt.const_mul m).exp).smul hV.hasFDerivAt
  unfold pd
  rw [show (fun y => Real.exp (m * φ y) • V y) = (fun y => Real.exp (m * φ y)) • V from rfl,
    h.fderiv]
  simp only [ContinuousLinearMap.add_apply, ContinuousLinearMap.coe_smul',
    ContinuousLinearMap.smulRight_apply, Pi.smul_apply, smul_eq_mul]
  congr 1
  ring_nf

theorem pd_conf (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (x : Pt n)
    (hg : DifferentiableAt ℝ g x) (hφ : DifferentiableAt ℝ φ x) (b : Fin n) :
    pd (conf φ g) x b =
      Real.exp (2 * φ x) • pd g x b + (2 * Real.exp (2 * φ x) * pd φ x b) • g x :=
  pd_expsmul φ g x 2 hφ hg b

theorem ginv_conf (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (x : Pt n)
    (hdet : IsUnit (Matrix.of (g x)).det) :
    ginv (conf φ g) x = Real.exp (-(2 * φ x)) • ginv g x := by
  rw [show conf φ g x = Real.exp (2 * φ x) • g x from rfl]
  unfold ginv
  rw [show Matrix.of (Real.exp (2 * φ x) • g x) = Real.exp (2 * φ x) • Matrix.of (g x) from
    (Matrix.smul_of _ _).symm, inv_smul_real _ _ (Real.exp_pos _).ne' hdet, Real.exp_neg]

theorem conformal_christoffel (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (x : Pt n)
    (hg : DifferentiableAt ℝ g x) (hφ : DifferentiableAt ℝ φ x)
    (hdet : IsUnit (Matrix.of (g x)).det) (a b c : Fin n) :
    chris (conf φ g) x a b c = chris g x a b c
      + (1 : Matrix (Fin n) (Fin n) ℝ) a c * pd φ x b
      + (1 : Matrix (Fin n) (Fin n) ℝ) a b * pd φ x c
      - g x b c * ∑ d, ginv g x a d * pd φ x d := by
  have hE : Real.exp (2 * φ x) ≠ 0 := (Real.exp_pos _).ne'
  have step : chris (conf φ g) x a b c =
      ∑ d, ((1 / 2 : ℝ) * (ginv g x a d * (pd g x b d c + pd g x c d b - pd g x d b c))
        + (ginv g x a d * g x d c) * pd φ x b + (ginv g x a d * g x d b) * pd φ x c
        - g x b c * (ginv g x a d * pd φ x d)) := by
    unfold chris
    rw [ginv_conf g φ x hdet]
    simp only [pd_conf g φ x hg hφ, Matrix.smul_apply, Pi.add_apply, Pi.smul_apply,
      smul_eq_mul, Real.exp_neg]
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl fun d _ => ?_
    field_simp
    ring
  rw [step, Finset.sum_sub_distrib, Finset.sum_add_distrib, Finset.sum_add_distrib,
    ← Finset.mul_sum, ← Finset.sum_mul, ← Finset.sum_mul, ← Finset.mul_sum,
    inv_mul_entry g x hdet, inv_mul_entry g x hdet]
  unfold chris
  ring

/-- General weighted rescaling `V' = e^{mφ} V`. -/
theorem conformal_selfCov (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (V : Pt n → Pt n) (x : Pt n)
    (m : ℝ) (hg : DifferentiableAt ℝ g x) (hφ : DifferentiableAt ℝ φ x)
    (hV : DifferentiableAt ℝ V x) (hdet : IsUnit (Matrix.of (g x)).det) (a : Fin n) :
    selfCov (conf φ g) (fun y => Real.exp (m * φ y) • V y) x a =
      Real.exp (2 * m * φ x) * (selfCov g V x a
        + (m + 2) * (∑ b, V x b * pd φ x b) * V x a
        - contr (g x) (V x) (V x) * ∑ d, ginv g x a d * pd φ x d) := by
  set e := Real.exp (m * φ x) with he
  set W := ∑ d, ginv g x a d * pd φ x d with hW
  set S := ∑ b, V x b * pd φ x b with hS
  have he2 : Real.exp (2 * m * φ x) = e * e := by
    rw [he, ← Real.exp_add]; ring_nf
  have inner : ∀ b, ∑ c, chris (conf φ g) x a b c * (e * V x c) =
      e * (∑ c, chris g x a b c * V x c + pd φ x b * V x a
        + (1 : Matrix (Fin n) (Fin n) ℝ) a b * S - W * ∑ c, g x b c * V x c) := by
    intro b
    simp only [conformal_christoffel g φ x hg hφ hdet]
    have h1 : ∑ c, (1 : Matrix (Fin n) (Fin n) ℝ) a c * pd φ x b * V x c = pd φ x b * V x a := by
      rw [← sum_one_mul a (fun c => pd φ x b * V x c)]
      exact Finset.sum_congr rfl fun c _ => by ring
    have h2 : ∑ c, (1 : Matrix (Fin n) (Fin n) ℝ) a b * pd φ x c * V x c =
        (1 : Matrix (Fin n) (Fin n) ℝ) a b * S := by
      rw [hS, Finset.mul_sum]
      exact Finset.sum_congr rfl fun c _ => by ring
    have h3 : ∑ c, g x b c * W * V x c = W * ∑ c, g x b c * V x c := by
      rw [Finset.mul_sum]
      exact Finset.sum_congr rfl fun c _ => by ring
    rw [← hW]
    calc ∑ c, (chris g x a b c + (1 : Matrix (Fin n) (Fin n) ℝ) a c * pd φ x b
            + (1 : Matrix (Fin n) (Fin n) ℝ) a b * pd φ x c - g x b c * W) * (e * V x c)
        = e * (∑ c, chris g x a b c * V x c
            + ∑ c, (1 : Matrix (Fin n) (Fin n) ℝ) a c * pd φ x b * V x c
            + ∑ c, (1 : Matrix (Fin n) (Fin n) ℝ) a b * pd φ x c * V x c
            - ∑ c, g x b c * W * V x c) := by
          rw [← Finset.sum_add_distrib, ← Finset.sum_add_distrib, ← Finset.sum_sub_distrib,
            Finset.mul_sum]
          exact Finset.sum_congr rfl fun c _ => by ring
      _ = _ := by rw [h1, h2, h3]
  have hpd : ∀ b, pd (fun y => Real.exp (m * φ y) • V y) x b a =
      e * pd V x b a + m * e * pd φ x b * V x a := by
    intro b
    rw [pd_expsmul φ V x m hφ hV b]
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  unfold selfCov covVec
  simp only [hpd, Pi.smul_apply, smul_eq_mul, inner]
  have hcontr : contr (g x) (V x) (V x) = ∑ b, V x b * ∑ c, g x b c * V x c := by
    unfold contr
    refine Finset.sum_congr rfl fun b _ => ?_
    rw [Finset.mul_sum]
    exact Finset.sum_congr rfl fun c _ => by ring
  have hdelta : ∑ b, V x b * ((1 : Matrix (Fin n) (Fin n) ℝ) a b * S) = V x a * S := by
    rw [← sum_one_mul a (fun b => V x b * S)]
    exact Finset.sum_congr rfl fun b _ => by ring
  rw [he2, hcontr]
  calc ∑ b, e * V x b * (e * pd V x b a + m * e * pd φ x b * V x a
          + e * (∑ c, chris g x a b c * V x c + pd φ x b * V x a
            + (1 : Matrix (Fin n) (Fin n) ℝ) a b * S - W * ∑ c, g x b c * V x c))
      = e * e * (∑ b, V x b * (pd V x b a + ∑ c, chris g x a b c * V x c)
          + (m + 1) * (∑ b, V x b * pd φ x b) * V x a
          + ∑ b, V x b * ((1 : Matrix (Fin n) (Fin n) ℝ) a b * S)
          - W * ∑ b, V x b * ∑ c, g x b c * V x c) := by
        rw [Finset.mul_sum, Finset.mul_sum, Finset.mul_sum, Finset.mul_sum, Finset.sum_mul,
          Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib, ← Finset.sum_add_distrib,
          ← Finset.sum_sub_distrib, Finset.mul_sum]
        exact Finset.sum_congr rfl fun b _ => by ring
    _ = _ := by rw [hdelta, ← hS]; ring

theorem conformal_velocity_norm (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (U : Pt n → Pt n)
    (x : Pt n) :
    contr (conf φ g x) (Real.exp (-φ x) • U x) (Real.exp (-φ x) • U x) =
      contr (g x) (U x) (U x) := by
  rw [show conf φ g x = Real.exp (2 * φ x) • g x from rfl, contr_smul]
  have : Real.exp (2 * φ x) * Real.exp (-φ x) * Real.exp (-φ x) = 1 := by
    rw [← Real.exp_add, ← Real.exp_add]; ring_nf; exact Real.exp_zero
  rw [this, one_mul]

theorem conformal_accel (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (U : Pt n → Pt n) (x : Pt n)
    (c : ℝ) (hg : DifferentiableAt ℝ g x) (hφ : DifferentiableAt ℝ φ x)
    (hU : DifferentiableAt ℝ U x) (hdet : IsUnit (Matrix.of (g x)).det) (hc : c ≠ 0)
    (hnorm : contr (g x) (U x) (U x) = -c ^ 2) (a : Fin n) :
    (accelContra (conf φ g) (fun y => Real.exp (-φ y) • U y) x).comp a =
      Real.exp (-(2 * φ x)) *
        ((accelContra g U x).comp a + c ^ 2 * ∑ d, hinv g U c x a d * pd φ x d) := by
  have h := conformal_selfCov g φ U x (-1) hg hφ hU hdet a
  simp only [neg_one_mul] at h
  simp only [accelContra]
  rw [h, hnorm]
  have hsplit : c ^ 2 * ∑ d, hinv g U c x a d * pd φ x d =
      c ^ 2 * ∑ d, ginv g x a d * pd φ x d + U x a * ∑ b, U x b * pd φ x b := by
    unfold hinv
    simp only [add_mul, Finset.sum_add_distrib, mul_add]
    congr 1
    rw [Finset.mul_sum, Finset.mul_sum]
    refine Finset.sum_congr rfl fun d _ => ?_
    field_simp
  rw [hsplit]
  ring_nf

theorem conformal_null_affine (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (k : Pt n → Pt n)
    (x : Pt n) (hg : DifferentiableAt ℝ g x) (hφ : DifferentiableAt ℝ φ x)
    (hk : DifferentiableAt ℝ k x) (hdet : IsUnit (Matrix.of (g x)).det)
    (hnull : contr (g x) (k x) (k x) = 0) (a : Fin n) :
    selfCov (conf φ g) (fun y => Real.exp (-2 * φ y) • k y) x a =
      Real.exp (-4 * φ x) * selfCov g k x a := by
  rw [conformal_selfCov g φ k x (-2) hg hφ hk hdet a, hnull]
  ring_nf

theorem conformal_covector_null (g : Pt n → Arr2 n) (φ : Pt n → ℝ) (x : Pt n) (k : Pt n)
    (hdet : IsUnit (Matrix.of (g x)).det) :
    covNorm (ginv (conf φ g) x) k = Real.exp (-(2 * φ x)) * covNorm (ginv g x) k := by
  rw [ginv_conf g φ x hdet]
  unfold covNorm
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun a _ => ?_
  rw [Finset.mul_sum]
  refine Finset.sum_congr rfl fun b _ => ?_
  simp only [Matrix.smul_apply, smul_eq_mul]
  ring

theorem conformal_freq (k U : Pt n) (φ0 : ℝ) :
    freq k (Real.exp (-φ0) • U) = Real.exp (-φ0) * freq k U := freq_smul k U _

theorem conformal_redshift (ke Ue ko Uo : Pt n) (φe φo : ℝ) :
    onePlusZ ke (Real.exp (-φe) • Ue) ko (Real.exp (-φo) • Uo) =
      Real.exp (φo - φe) * onePlusZ ke Ue ko Uo := by
  unfold onePlusZ
  rw [freq_smul, freq_smul, mul_div_mul_comm, ← Real.exp_sub]
  ring_nf

theorem conformal_redshift_z (ke Ue ko Uo : Pt n) (φe φo : ℝ) :
    zOf (onePlusZ ke (Real.exp (-φe) • Ue) ko (Real.exp (-φo) • Uo)) + 1 =
      Real.exp (φo - φe) * (zOf (onePlusZ ke Ue ko Uo) + 1) := by
  unfold zOf
  rw [conformal_redshift]
  ring

theorem redshift_const_is_special_case (ke Ue ko Uo : Pt n) (lam : ℝ) (hlam : 0 < lam) :
    onePlusZ ke (lam⁻¹ • Ue) ko (lam⁻¹ • Uo) =
      Real.exp (Real.log lam - Real.log lam) * onePlusZ ke Ue ko Uo := by
  have h := conformal_redshift ke Ue ko Uo (Real.log lam) (Real.log lam)
  rwa [Real.exp_neg, Real.exp_log hlam] at h

end C03

/-! ## Negative controls and non-vacuity witnesses -/

/-- Minkowski components `diag(-1,1,1,1)`. -/
def eta4 : Arr2 4 := fun a b => if a = b then (if a = 0 then -1 else 1) else 0

/-- `e₀ = (1,0,0,0)`. -/
def e0 : Pt 4 := ![1, 0, 0, 0]

theorem eta4_diag : Matrix.of eta4 = Matrix.diagonal ![-1, 1, 1, 1] := by
  ext a b
  fin_cases a <;> fin_cases b <;> simp [eta4, Matrix.diagonal]

theorem eta4_det : (Matrix.of eta4).det = -1 := by
  rw [eta4_diag, Matrix.det_diagonal]
  simp [Fin.prod_univ_four]

theorem eta4_inv : (Matrix.of eta4)⁻¹ = Matrix.of eta4 := by
  apply Matrix.inv_eq_left_inv
  rw [eta4_diag, Matrix.diagonal_mul_diagonal]
  ext a b
  fin_cases a <;> fin_cases b <;> simp [Matrix.diagonal]

theorem minkowski_witness (c : ℝ) (hc : c ≠ 0) :
    IsUnit (Matrix.of eta4).det ∧ contr eta4 (c • e0) (c • e0) = -c ^ 2 := by
  refine ⟨by rw [eta4_det]; exact isUnit_one.neg, ?_⟩
  simp [contr, Fin.sum_univ_four, eta4, e0]
  ring

theorem pd_const {n : ℕ} {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] (v : E)
    (x : Pt n) (b : Fin n) : pd (fun _ : Pt n => v) x b = 0 := by
  simp [pd]

theorem pd_coord {n : ℕ} (i : Fin n) (x : Pt n) (b : Fin n) :
    pd (fun y : Pt n => y i) x b = (Pi.single b (1 : ℝ) : Pt n) i := by
  unfold pd
  rw [(hasFDerivAt_apply i x).fderiv]
  rfl

theorem conf_grad_counterexample (c : ℝ) (hc : c ≠ 0) :
    (fun x : Pt 4 => x 1) 0 = 0 ∧
      (accelContra (fun _ => eta4) (fun _ => c • e0) 0).comp 1 = 0 ∧
      (accelContra (conf (fun x : Pt 4 => x 1) (fun _ => eta4))
        (fun y => Real.exp (-(fun x : Pt 4 => x 1) y) • (fun _ => c • e0) y) 0).comp 1 = c ^ 2 := by
  have hchris : ∀ x a b d, chris (fun _ : Pt 4 => eta4) x a b d = 0 := by
    intro x a b d
    simp [chris, pd_const]
  refine ⟨rfl, ?_, ?_⟩
  · simp [accelContra, selfCov, covVec, hchris, pd_const]
  · obtain ⟨hdet, hnorm⟩ := minkowski_witness c hc
    have h := conformal_accel (fun _ => eta4) (fun x : Pt 4 => x 1) (fun _ => c • e0) 0 c
      (differentiableAt_const _) (differentiableAt_apply 1 0) (differentiableAt_const _)
      hdet hc hnorm 1
    rw [h]
    have hA : (accelContra (fun _ => eta4) (fun _ => c • e0) 0).comp 1 = 0 := by
      simp [accelContra, selfCov, covVec, hchris, pd_const]
    rw [hA]
    simp only [pd_coord, hinv, ginv, eta4_inv]
    simp [Fin.sum_univ_four, eta4, e0, Pi.single_apply]

theorem scale_inf_no_floor (N : ℝ) (hN : 0 < N) :
    ∀ ε > 0, ∃ lam > 0, 0 < lam⁻¹ * N ∧ lam⁻¹ * N < ε := by
  intro ε hε
  refine ⟨2 * N / ε, by positivity, by positivity, ?_⟩
  rw [inv_div]
  field_simp
  linarith

end G17A
