import Mathlib
import C01
import Proof
import G04AEigenline

/-!
# G03-A: timelike rest-space spectral structure and the local timelike eigenbranch (GR-CAS-03)

Imports, unchanged, the accepted CAS-03-C01 Lean (`C01`, namespace `CAS03C01`), the CAS-04 `Proof`
(namespace `GRSTATCAS04`) and the reviewed G04-A `G04AEigenline` (namespace `G04A`).

* A: the source premise "S^a_b has a timelike eigenvector" (OPTICAL Theorem 5 / CAS-03 assumption) is a
  supplied premise, equivalent to A(p)=0; it is NOT implied by Lorentz-self-adjointness (A3).
* B: the g-orthogonal rest space of any timelike `u` is a genuine Mathlib inner-product space.
* C: the restriction of a Lorentz-self-adjoint `S` with `S u = s u` is symmetric there; orthonormal
  eigenbasis; `dim ker(S - s) = 1 + #{i | p_i = s}`; bridge to the C01 rest kernel / fibre chart.
* D: CONDITIONAL smooth local branch (finite `C^n`) for any family `S(q)` on a Banach parameter space
  with an isolated (simple) timelike eigenvalue at `q0`; the optical source does not bind the family.
* E: controls. Rest-eigenvalue collision does not block the timelike branch but kills continuity of
  rest eigenvectors; losing timelike isolation can destroy the branch.
-/

namespace G03A
open GRSTATCAS04 G04A
open scoped Topology ContDiff RealInnerProductSpace

/-! ## Bridge between the CAS-03-C01 representation and Vec4/Mat4 -/

def ofV (v : CAS03C01.V) : Vec4 := Fin.cons v.1 v.2

def toMixed (s : CAS03C01.SymCov) : Mat4 := fun a b => eta a * CAS03C01.toMatrix s a b

def matVecL (t : Mat4) : Vec4 →ₗ[ℝ] Vec4 where
  toFun := matVec t
  map_add' := matVec_add t
  map_smul' := fun r v => matVec_smul t v r

def DactL (s : CAS03C01.SymCov) : CAS03C01.W →ₗ[ℝ] CAS03C01.W where
  toFun := CAS03C01.Dact s CAS03C01.e0
  map_add' := fun w w' => by
    funext i
    simp only [CAS03C01.Dact, Pi.add_apply, mul_add, Finset.sum_add_distrib]
  map_smul' := fun r w => by
    funext i
    simp only [CAS03C01.Dact, Pi.smul_apply, smul_eq_mul, RingHom.id_apply, Finset.mul_sum]
    apply Finset.sum_congr rfl; intro j _; ring

def kerDSub (s : CAS03C01.SymCov) : Submodule ℝ CAS03C01.W := LinearMap.ker (DactL s)

theorem ofV_zero (v : CAS03C01.V) : ofV v 0 = v.1 := rfl
theorem ofV_succ (v : CAS03C01.V) (i : Fin 3) : ofV v i.succ = v.2 i := rfl

theorem ofV_injective : Function.Injective ofV := by
  intro v v' h
  apply Prod.ext
  · exact congrFun h 0
  · funext i; exact congrFun h i.succ

theorem ofV_smulV (c : ℝ) (v : CAS03C01.V) : ofV (CAS03C01.smulV c v) = c • ofV v := by
  funext a
  cases a using Fin.cases with
  | zero => rfl
  | succ i => rfl

theorem toMatrix_symm (s : CAS03C01.SymCov) (a b : Fin 4) :
    CAS03C01.toMatrix s a b = CAS03C01.toMatrix s b a := by
  cases a using Fin.cases with
  | zero =>
    cases b using Fin.cases with
    | zero => rfl
    | succ j => rfl
  | succ i =>
    cases b using Fin.cases with
    | zero => rfl
    | succ j =>
      simp only [CAS03C01.toMatrix, Fin.cases_succ, Fin.cons_succ]
      exact (s.d_symm.apply i j).symm

theorem toMixed_selfAdjoint (s : CAS03C01.SymCov) : EtaSelfAdjoint (toMixed s) := by
  intro a b
  simp only [toMixed]
  rw [← mul_assoc, ← mul_assoc, eta_sq, eta_sq, toMatrix_symm]

theorem toMixed_matVec (s : CAS03C01.SymCov) (v : CAS03C01.V) :
    matVec (toMixed s) (ofV v) = ofV (CAS03C01.mixed s v) := by
  funext a
  cases a using Fin.cases with
  | zero =>
    simp [matVec, toMixed, ofV, Fin.sum_univ_succ, CAS03C01.mixed, CAS03C01.g, CAS03C01.act,
      CAS03C01.toMatrix, CAS03C01.dot, eta]
    ring
  | succ i =>
    simp [matVec, toMixed, ofV, Fin.sum_univ_succ, CAS03C01.mixed, CAS03C01.g, CAS03C01.act,
      CAS03C01.toMatrix, eta, Fin.succ_ne_zero]

theorem ofV_mass (v : CAS03C01.V) : lorentzDot (ofV v) (ofV v) = CAS03C01.mass v := by
  simp [lorentzDot, ofV, Fin.sum_univ_succ, CAS03C01.mass, CAS03C01.covPair, CAS03C01.g,
    CAS03C01.dot, eta, Fin.succ_ne_zero]
  ring

/-! ## A: the source premise -/

def TimelikeEigenPremise (s : CAS03C01.SymCov) : Prop :=
  ∃ (v : CAS03C01.V) (c : ℝ), CAS03C01.mass v < 0 ∧ CAS03C01.mixed s v = CAS03C01.smulV c v

/-- Timelike vectors have nonzero time component. -/
theorem timelike_time_ne (v : Vec4) (hv : lorentzDot v v < 0) : v 0 ≠ 0 := by
  intro h0
  rw [lorentzDot_expand, h0] at hv
  nlinarith [mul_self_nonneg (v 1), mul_self_nonneg (v 2), mul_self_nonneg (v 3)]

theorem A2_normalize (t : Mat4) (v : Vec4) (μ : ℝ) (hv : lorentzDot v v < 0)
    (he : matVec t v = μ • v) :
    ∃ (u : Vec4) (k : ℝ), k ≠ 0 ∧ u = k • v ∧ matVec t u = μ • u ∧
      lorentzDot u u = -1 ∧ 0 < u 0 := by
  have h0 := timelike_time_ne v hv
  set m := -lorentzDot v v with hm
  have hmpos : 0 < m := by linarith
  have hsq : Real.sqrt m ^ 2 = m := Real.sq_sqrt hmpos.le
  have hspos : 0 < Real.sqrt m := Real.sqrt_pos.2 hmpos
  have habs : 0 < |v 0| := abs_pos.2 h0
  set k := v 0 / (|v 0| * Real.sqrt m) with hk
  have hk2 : k ^ 2 * m = 1 := by
    rw [hk, div_pow, mul_pow, sq_abs, hsq]
    field_simp
  have hkne : k ≠ 0 := by
    intro hz; rw [hz] at hk2; norm_num at hk2
  refine ⟨k • v, k, hkne, rfl, ?_, ?_, ?_⟩
  · rw [matVec_smul, he, smul_comm]
  · rw [lorentzDot_smul_left, lorentzDot_smul_right]
    have : lorentzDot v v = -m := by rw [hm]; ring
    rw [this]; nlinarith
  · simp only [Pi.smul_apply, smul_eq_mul]
    have : k * v 0 = v 0 ^ 2 / (|v 0| * Real.sqrt m) := by rw [hk]; ring
    rw [this]
    apply div_pos _ (mul_pos habs hspos)
    exact lt_of_le_of_ne (sq_nonneg _) (Ne.symm (pow_ne_zero 2 h0))

theorem A1_premise_iff_mixed (s : CAS03C01.SymCov) :
    TimelikeEigenPremise s ↔
      ∃ (v : Vec4) (c : ℝ), lorentzDot v v < 0 ∧ matVec (toMixed s) v = c • v := by
  constructor
  · rintro ⟨v, c, hm, he⟩
    refine ⟨ofV v, c, by rw [ofV_mass]; exact hm, ?_⟩
    rw [toMixed_matVec, he, ofV_smulV]
  · rintro ⟨v, c, hm, he⟩
    set w : CAS03C01.V := (v 0, fun i => v i.succ) with hw
    have hvw : ofV w = v := by
      funext a
      cases a using Fin.cases with
      | zero => rfl
      | succ i => rfl
    refine ⟨w, c, by rw [← ofV_mass, hvw]; exact hm, ?_⟩
    apply ofV_injective
    rw [← toMixed_matVec, ofV_smulV, hvw, he]

theorem A1_premise_iff_geodesic (s : CAS03C01.SymCov) :
    TimelikeEigenPremise s ↔
      ∃ u : CAS03C01.V, CAS03C01.futureUnit u ∧ CAS03C01.bAct s u u = (0, CAS03C01.zeroW) := by
  constructor
  · intro hp
    obtain ⟨v, c, hm, he⟩ := (A1_premise_iff_mixed s).1 hp
    obtain ⟨u, k, _, _, hue, hun, huf⟩ := A2_normalize (toMixed s) v c hm he
    set w : CAS03C01.V := (u 0, fun i => u i.succ) with hw
    have huw : ofV w = u := by
      funext a
      cases a using Fin.cases with
      | zero => rfl
      | succ i => rfl
    have hmass : CAS03C01.mass w = -1 := by rw [← ofV_mass, huw]; exact hun
    have hmix : CAS03C01.mixed s w = CAS03C01.smulV c w := by
      apply ofV_injective
      rw [← toMixed_matVec, ofV_smulV, huw, hue]
    have hc := CAS03C01.metric_coefficient_unique s w c hmass hmix
    refine ⟨w, ⟨hmass, ?_⟩, ?_⟩
    · show 0 < w.1
      rw [← ofV_zero, huw]; exact huf
    · rw [CAS03C01.b_zero_iff_eigen, ← hc]; exact hmix
  · rintro ⟨u, hfu, hb⟩
    refine ⟨u, CAS03C01.st s u, ?_, (CAS03C01.b_zero_iff_eigen s u).1 hb⟩
    rw [hfu.1]; norm_num

def sRot : CAS03C01.SymCov where
  a := 0
  b := ![1, 0, 0]
  d := 0
  d_symm := Matrix.isSymm_zero

def sNull : CAS03C01.SymCov where
  a := 1
  b := ![1, 0, 0]
  d := Matrix.diagonal ![1, 0, 0]
  d_symm := Matrix.isSymm_diagonal _

theorem A3_rot_no_timelike : EtaSelfAdjoint (toMixed sRot) ∧ ¬ TimelikeEigenPremise sRot := by
  refine ⟨toMixed_selfAdjoint sRot, ?_⟩
  rintro ⟨v, c, hm, he⟩
  have h0 := congrArg Prod.fst he
  have h1 := congrFun (congrArg Prod.snd he) 0
  have h2 := congrFun (congrArg Prod.snd he) 1
  have h3 := congrFun (congrArg Prod.snd he) 2
  simp [CAS03C01.mixed, CAS03C01.g, CAS03C01.act, CAS03C01.smulV, sRot, CAS03C01.dot,
    Fin.sum_univ_three] at h0 h1 h2 h3
  simp [CAS03C01.mass, CAS03C01.covPair, CAS03C01.g, CAS03C01.dot, Fin.sum_univ_three] at hm
  -- h0 : -(v.2 0) = c * v.1 ; h1 : v.1 = c * v.2 0
  have hx : v.2 0 * (1 + c ^ 2) = 0 := by nlinarith
  have hx0 : v.2 0 = 0 := by
    rcases mul_eq_zero.1 hx with h | h
    · exact h
    · nlinarith [sq_nonneg c]
  have hv0 : v.1 = 0 := by rw [hx0] at h1; linarith
  rw [hx0, hv0] at hm
  nlinarith [mul_self_nonneg (v.2 1), mul_self_nonneg (v.2 2)]

theorem A3_null_no_timelike : EtaSelfAdjoint (toMixed sNull) ∧ ¬ TimelikeEigenPremise sNull := by
  refine ⟨toMixed_selfAdjoint sNull, ?_⟩
  rintro ⟨v, c, hm, he⟩
  have h0 := congrArg Prod.fst he
  have h1 := congrFun (congrArg Prod.snd he) 0
  simp [CAS03C01.mixed, CAS03C01.g, CAS03C01.act, CAS03C01.smulV, sNull, CAS03C01.dot,
    Fin.sum_univ_three, Matrix.diagonal] at h0 h1
  simp [CAS03C01.mass, CAS03C01.covPair, CAS03C01.g, CAS03C01.dot, Fin.sum_univ_three] at hm
  -- h0 : -(v.1 + v.2 0) = c * v.1 ; h1 : v.1 + v.2 0 = c * v.2 0
  have hs : c * (v.1 + v.2 0) = 0 := by linarith
  have hsum : v.1 + v.2 0 = 0 := by
    rcases mul_eq_zero.1 hs with hc | h
    · rw [hc] at h1; linarith
    · exact h
  have : v.2 0 = -v.1 := by linarith
  rw [this] at hm
  nlinarith [mul_self_nonneg (v.2 1), mul_self_nonneg (v.2 2)]

theorem A3_selfadjoint_insufficient :
    ∃ s : CAS03C01.SymCov, EtaSelfAdjoint (toMixed s) ∧ ¬ TimelikeEigenPremise s :=
  ⟨sRot, A3_rot_no_timelike⟩

/-! ## B: the rest space of a timelike vector is a genuine inner-product space -/

/-- Rest-space positive definiteness for an arbitrary (not necessarily unit) timelike `u`. -/
theorem B1_rest_posdef (u w : Vec4) (hu : lorentzDot u u < 0) (ho : lorentzDot u w = 0)
    (hw : w ≠ 0) : 0 < lorentzDot w w := by
  rw [lorentzDot_expand] at hu ho ⊢
  set A := u 1 * u 1 + u 2 * u 2 + u 3 * u 3 with hA
  set B := w 1 * w 1 + w 2 * w 2 + w 3 * w 3 with hB
  have hdot : u 0 * w 0 = u 1 * w 1 + u 2 * w 2 + u 3 * w 3 := by linarith
  have lag : (u 1 * w 1 + u 2 * w 2 + u 3 * w 3)^2 + ((u 1 * w 2 - u 2 * w 1)^2 +
      (u 1 * w 3 - u 3 * w 1)^2 + (u 2 * w 3 - u 3 * w 2)^2) = A * B := by
    simp only [hA, hB]; ring
  have hcs : (u 0 * w 0)^2 ≤ A * B := by
    rw [hdot, ← lag]
    nlinarith [sq_nonneg (u 1 * w 2 - u 2 * w 1), sq_nonneg (u 1 * w 3 - u 3 * w 1),
      sq_nonneg (u 2 * w 3 - u 3 * w 2)]
  have hA0 : 0 ≤ A := by
    have := mul_self_nonneg (u 1); have := mul_self_nonneg (u 2); have := mul_self_nonneg (u 3)
    simp only [hA]; linarith
  have hB0 : 0 ≤ B := by
    have := mul_self_nonneg (w 1); have := mul_self_nonneg (w 2); have := mul_self_nonneg (w 3)
    simp only [hB]; linarith
  have hgap : 0 < u 0 * u 0 - A := by linarith
  by_contra hneg
  have hle : B ≤ w 0 * w 0 := by linarith
  -- (u0^2 - A) w0^2 ≤ 0
  have h1 : (u 0 * u 0 - A) * (w 0 * w 0) ≤ 0 := by nlinarith
  have hw0 : w 0 * w 0 ≤ 0 := by
    by_contra h
    have := mul_pos hgap (lt_of_not_ge h)
    linarith
  have hw00 : w 0 = 0 := by nlinarith [mul_self_nonneg (w 0)]
  have hB00 : B = 0 := by rw [hw00] at hle; linarith
  have e1 : w 1 = 0 := by nlinarith [mul_self_nonneg (w 1), mul_self_nonneg (w 2), mul_self_nonneg (w 3)]
  have e2 : w 2 = 0 := by nlinarith [mul_self_nonneg (w 1), mul_self_nonneg (w 2), mul_self_nonneg (w 3)]
  have e3 : w 3 = 0 := by nlinarith [mul_self_nonneg (w 1), mul_self_nonneg (w 2), mul_self_nonneg (w 3)]
  apply hw
  funext i
  fin_cases i
  · exact hw00
  · exact e1
  · exact e2
  · exact e3

structure Timelike where
  vec : Vec4
  timelike : lorentzDot vec vec < 0

def lorentzFormL (u : Vec4) : Vec4 →ₗ[ℝ] ℝ where
  toFun := lorentzDot u
  map_add' := lorentzDot_add_right u
  map_smul' := fun r v => by simp [lorentzDot_smul_right]

def restSub (u : Vec4) : Submodule ℝ Vec4 := LinearMap.ker (lorentzFormL u)

theorem mem_restSub (u w : Vec4) : w ∈ restSub u ↔ lorentzDot u w = 0 := Iff.rfl

def RestSpace (τ : Timelike) : Type := ↥(restSub τ.vec)

instance (τ : Timelike) : AddCommGroup (RestSpace τ) :=
  inferInstanceAs (AddCommGroup ↥(restSub τ.vec))

instance (τ : Timelike) : Module ℝ (RestSpace τ) :=
  inferInstanceAs (Module ℝ ↥(restSub τ.vec))

instance (τ : Timelike) : FiniteDimensional ℝ (RestSpace τ) :=
  inferInstanceAs (FiniteDimensional ℝ ↥(restSub τ.vec))

def RestSpace.val {τ : Timelike} (x : RestSpace τ) : Vec4 :=
  Subtype.val (p := fun w => w ∈ restSub τ.vec) x

def RestSpace.mk {τ : Timelike} (w : Vec4) (h : lorentzDot τ.vec w = 0) : RestSpace τ :=
  (⟨w, h⟩ : ↥(restSub τ.vec))

theorem RestSpace.val_add {τ : Timelike} (x y : RestSpace τ) : (x + y).val = x.val + y.val := rfl
theorem RestSpace.val_smul {τ : Timelike} (r : ℝ) (x : RestSpace τ) : (r • x).val = r • x.val := rfl
theorem RestSpace.val_zero {τ : Timelike} : (0 : RestSpace τ).val = 0 := rfl
theorem RestSpace.mk_val {τ : Timelike} (w : Vec4) (h : lorentzDot τ.vec w = 0) :
    (RestSpace.mk (τ := τ) w h).val = w := rfl

theorem B2_val_injective (τ : Timelike) : Function.Injective (RestSpace.val (τ := τ)) :=
  fun _ _ h => Subtype.val_injective h

theorem B2_val_mem (τ : Timelike) (x : RestSpace τ) : lorentzDot τ.vec x.val = 0 :=
  (show ↥(restSub τ.vec) from x).2

theorem RestSpace.val_eq_zero {τ : Timelike} (x : RestSpace τ) : x.val = 0 ↔ x = 0 := by
  constructor
  · intro h; apply B2_val_injective τ; rw [h, RestSpace.val_zero]
  · intro h; rw [h, RestSpace.val_zero]

instance (τ : Timelike) : Inner ℝ (RestSpace τ) := ⟨fun x y => lorentzDot x.val y.val⟩

theorem inner_def' (τ : Timelike) (x y : RestSpace τ) : inner ℝ x y = lorentzDot x.val y.val := rfl

def restCore (τ : Timelike) : InnerProductSpace.Core ℝ (RestSpace τ) where
  toInner := inferInstance
  conj_inner_symm x y := by
    rw [conj_trivial, inner_def', inner_def', lorentzDot_comm]
  re_inner_nonneg x := by
    rw [RCLike.re_to_real, inner_def']
    by_cases h : x.val = 0
    · rw [h, lorentzDot_zero_right]
    · exact (B1_rest_posdef τ.vec x.val τ.timelike (B2_val_mem τ x) h).le
  add_left x y z := by
    rw [inner_def', inner_def', inner_def', RestSpace.val_add, lorentzDot_add_left]
  smul_left x y r := by
    rw [inner_def', inner_def', RestSpace.val_smul, lorentzDot_smul_left, conj_trivial]
  definite x hx := by
    rw [inner_def'] at hx
    by_contra h
    have h' : x.val ≠ 0 := fun h0 => h ((RestSpace.val_eq_zero x).1 h0)
    have := B1_rest_posdef τ.vec x.val τ.timelike (B2_val_mem τ x) h'
    linarith

noncomputable instance (τ : Timelike) : NormedAddCommGroup (RestSpace τ) :=
  @InnerProductSpace.Core.toNormedAddCommGroup ℝ (RestSpace τ) _ _ _ (restCore τ)

noncomputable instance (τ : Timelike) : InnerProductSpace ℝ (RestSpace τ) :=
  InnerProductSpace.ofCore _

theorem B2_inner_eq (τ : Timelike) (x y : RestSpace τ) : inner ℝ x y = lorentzDot x.val y.val :=
  rfl

theorem B2_posdef (τ : Timelike) (x : RestSpace τ) (hx : x ≠ 0) : 0 < inner ℝ x x := by
  rw [B2_inner_eq]
  have h' : x.val ≠ 0 := fun h0 => hx ((RestSpace.val_eq_zero x).1 h0)
  exact B1_rest_posdef τ.vec x.val τ.timelike (B2_val_mem τ x) h'

theorem B2_finrank (τ : Timelike) : Module.finrank ℝ (RestSpace τ) = 3 := by
  have h := LinearMap.finrank_range_add_finrank_ker (lorentzFormL τ.vec)
  have hr : LinearMap.range (lorentzFormL τ.vec) = ⊤ := by
    rw [LinearMap.range_eq_top]
    intro r
    refine ⟨(r / lorentzDot τ.vec τ.vec) • τ.vec, ?_⟩
    show lorentzDot τ.vec ((r / lorentzDot τ.vec τ.vec) • τ.vec) = r
    rw [lorentzDot_smul_right, div_mul_cancel₀ _ τ.timelike.ne]
  rw [hr, finrank_top, Module.finrank_self, Module.finrank_fin_fun] at h
  change Module.finrank ℝ ↥(restSub τ.vec) = 3
  unfold restSub
  omega

/-- A timelike vector is not Lorentz-orthogonal to another timelike vector. -/
theorem timelike_not_orth (v v' : Vec4) (hv : lorentzDot v v < 0) (hv' : lorentzDot v' v' < 0) :
    lorentzDot v v' ≠ 0 := by
  intro h0
  have hne : v' ≠ 0 := by
    intro hz; rw [hz, lorentzDot_zero_right] at hv'; exact lt_irrefl _ hv'
  have := B1_rest_posdef v v' hv h0 hne
  linarith

theorem A2_timelike_eigenvalue_unique (t : Mat4) (hsym : EtaSelfAdjoint t) (v v' : Vec4)
    (μ μ' : ℝ) (hv : lorentzDot v v < 0) (hv' : lorentzDot v' v' < 0)
    (he : matVec t v = μ • v) (he' : matVec t v' = μ' • v') : μ = μ' := by
  have hne := timelike_not_orth v v' hv hv'
  have h1 := selfAdj_dot hsym v v'
  rw [he, he', lorentzDot_smul_right, lorentzDot_smul_left] at h1
  have : (μ - μ') * lorentzDot v v' = 0 := by linarith
  rcases mul_eq_zero.1 this with h | h
  · linarith
  · exact absurd h hne

/-! ## C: restricted self-adjoint operator, orthonormal eigenbasis, kernel dimension -/

theorem restOp_mem (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (w : Vec4) (hw : lorentzDot τ.vec w = 0) :
    lorentzDot τ.vec (matVec t w) = 0 := by
  rw [selfAdj_dot hsym, he, lorentzDot_smul_left, hw, mul_zero]

def restOp (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : RestSpace τ →ₗ[ℝ] RestSpace τ where
  toFun x := RestSpace.mk (matVec t x.val) (restOp_mem τ t s hsym he x.val (B2_val_mem τ x))
  map_add' x y := by
    apply B2_val_injective τ
    simp only [RestSpace.mk_val, RestSpace.val_add, matVec_add]
  map_smul' r x := by
    apply B2_val_injective τ
    simp only [RestSpace.mk_val, RestSpace.val_smul, matVec_smul, RingHom.id_apply]

theorem C0_restOp_val (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (x : RestSpace τ) :
    (restOp τ t s hsym he x).val = matVec t x.val := rfl

theorem C1_restOp_symmetric (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : (restOp τ t s hsym he).IsSymmetric := by
  intro x y
  rw [B2_inner_eq, B2_inner_eq, C0_restOp_val, C0_restOp_val, selfAdj_dot hsym]

noncomputable def restEigenbasis (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : OrthonormalBasis (Fin 3) ℝ (RestSpace τ) :=
  (C1_restOp_symmetric τ t s hsym he).eigenvectorBasis (B2_finrank τ)

noncomputable def restEigenvalues (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : Fin 3 → ℝ :=
  (C1_restOp_symmetric τ t s hsym he).eigenvalues (B2_finrank τ)

theorem C1_rest_spectral (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    (∀ i, matVec t (restEigenbasis τ t s hsym he i).val =
      restEigenvalues τ t s hsym he i • (restEigenbasis τ t s hsym he i).val) ∧
    (∀ i j, lorentzDot (restEigenbasis τ t s hsym he i).val (restEigenbasis τ t s hsym he j).val =
      if i = j then 1 else 0) ∧
    (∀ i, lorentzDot τ.vec (restEigenbasis τ t s hsym he i).val = 0) := by
  refine ⟨fun i => ?_, fun i j => ?_, fun i => B2_val_mem τ _⟩
  · have h := (C1_restOp_symmetric τ t s hsym he).apply_eigenvectorBasis (B2_finrank τ) i
    have h' := congrArg RestSpace.val h
    rw [C0_restOp_val, RestSpace.val_smul] at h'
    simpa [restEigenbasis, restEigenvalues] using h'
  · have h := orthonormal_iff_ite.1 (restEigenbasis τ t s hsym he).orthonormal i j
    rw [B2_inner_eq] at h
    exact h

theorem C1_restEigenbasis_G04A (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    RestEigenbasis t τ.vec (fun i => (restEigenbasis τ t s hsym he i).val)
      (restEigenvalues τ t s hsym he) := by
  obtain ⟨h1, h2, h3⟩ := C1_rest_spectral τ t s hsym he
  exact ⟨h2, h3, h1⟩

theorem mem_restEig_iff (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (μ : ℝ) (w : RestSpace τ) :
    w ∈ Module.End.eigenspace (restOp τ t s hsym he) μ ↔ matVec t w.val = μ • w.val := by
  rw [Module.End.mem_eigenspace_iff]
  constructor
  · intro h
    have := congrArg RestSpace.val h
    rwa [C0_restOp_val, RestSpace.val_smul] at this
  · intro h
    apply B2_val_injective τ
    rw [C0_restOp_val, RestSpace.val_smul]; exact h

theorem mem_eig_iff (t : Mat4) (μ : ℝ) (v : Vec4) :
    v ∈ Module.End.eigenspace (matVecL t) μ ↔ matVec t v = μ • v := by
  rw [Module.End.mem_eigenspace_iff]; rfl

theorem C2_eigenspace_split (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) (v : Vec4) :
    v ∈ Module.End.eigenspace (matVecL t) s ↔
      ∃ (a : ℝ) (w : RestSpace τ), w ∈ Module.End.eigenspace (restOp τ t s hsym he) s ∧
        v = a • τ.vec + w.val := by
  rw [mem_eig_iff]
  have hne : lorentzDot τ.vec τ.vec ≠ 0 := τ.timelike.ne
  constructor
  · intro hv
    set a := lorentzDot τ.vec v / lorentzDot τ.vec τ.vec with ha
    have horth : lorentzDot τ.vec (v - a • τ.vec) = 0 := by
      rw [sub_eq_add_neg, lorentzDot_add_right, ← neg_smul, lorentzDot_smul_right, ha]
      field_simp; ring
    refine ⟨a, RestSpace.mk (v - a • τ.vec) horth, ?_, ?_⟩
    · rw [mem_restEig_iff, RestSpace.mk_val, sub_eq_add_neg, ← neg_smul, matVec_add, matVec_smul,
        hv, he, smul_add, smul_smul, smul_smul, mul_comm]
    · rw [RestSpace.mk_val]; abel
  · rintro ⟨a, w, hw, rfl⟩
    rw [mem_restEig_iff] at hw
    rw [matVec_add, matVec_smul, he, hw, smul_add, smul_smul, smul_smul, mul_comm]

/-- The linear splitting map `(a, w) ↦ a u + w` onto the timelike eigenspace. -/
noncomputable def splitMap (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    (ℝ × Module.End.eigenspace (restOp τ t s hsym he) s) →ₗ[ℝ]
      Module.End.eigenspace (matVecL t) s where
  toFun p := ⟨p.1 • τ.vec + (p.2 : RestSpace τ).val,
    (C2_eigenspace_split τ t s hsym he _).2 ⟨p.1, p.2, p.2.2, rfl⟩⟩
  map_add' p q := by
    apply Subtype.ext
    simp only [Prod.fst_add, Prod.snd_add, Submodule.coe_add, RestSpace.val_add, add_smul]
    abel
  map_smul' r p := by
    apply Subtype.ext
    simp only [Prod.smul_fst, Prod.smul_snd, Submodule.coe_smul, RestSpace.val_smul,
      RingHom.id_apply, smul_add, smul_smul, smul_eq_mul]

theorem splitMap_bijective (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) : Function.Bijective (splitMap τ t s hsym he) := by
  have hne : lorentzDot τ.vec τ.vec ≠ 0 := τ.timelike.ne
  constructor
  · rw [injective_iff_map_eq_zero]
    rintro ⟨a, w⟩ h
    have h' : a • τ.vec + (w : RestSpace τ).val = 0 := congrArg Subtype.val h
    have h1 := congrArg (lorentzDot τ.vec) h'
    rw [lorentzDot_add_right, lorentzDot_smul_right, B2_val_mem, lorentzDot_zero_right,
      add_zero] at h1
    have ha : a = 0 := by
      rcases mul_eq_zero.1 h1 with h | h
      · exact h
      · exact absurd h hne
    rw [ha, zero_smul, zero_add] at h'
    have hw : (w : RestSpace τ) = 0 := (RestSpace.val_eq_zero _).1 h'
    rw [ha]
    ext
    · rfl
    · simp [hw]
  · rintro ⟨v, hv⟩
    obtain ⟨a, w, hw, rfl⟩ := (C2_eigenspace_split τ t s hsym he v).1 hv
    exact ⟨(a, ⟨w, hw⟩), rfl⟩

theorem C2_finrank (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    Module.finrank ℝ (Module.End.eigenspace (matVecL t) s) =
      1 + Module.finrank ℝ (Module.End.eigenspace (restOp τ t s hsym he) s) ∧
    Module.finrank ℝ (Module.End.eigenspace (restOp τ t s hsym he) s) =
      (Finset.univ.filter fun i => restEigenvalues τ t s hsym he i = s).card := by
  constructor
  · rw [← LinearEquiv.finrank_eq (LinearEquiv.ofBijective _ (splitMap_bijective τ t s hsym he)),
      Module.finrank_prod, Module.finrank_self]
  · have h := (C1_restOp_symmetric τ t s hsym he).card_filter_eigenvalues_eq (B2_finrank τ) s
    rw [← h]
    simp [restEigenvalues]

theorem C3_isolation_iff (τ : Timelike) (t : Mat4) (s : ℝ) (hsym : EtaSelfAdjoint t)
    (he : matVec t τ.vec = s • τ.vec) :
    (RestGapInjective t τ.vec (-s) ↔ Module.End.eigenspace (restOp τ t s hsym he) s = ⊥) ∧
    (RestGapInjective t τ.vec (-s) ↔ ∀ i, restEigenvalues τ t s hsym he i ≠ s) ∧
    (RestGapInjective t τ.vec (-s) ↔
      Module.finrank ℝ (Module.End.eigenspace (matVecL t) s) = 1) := by
  have h1 : RestGapInjective t τ.vec (-s) ↔
      Module.End.eigenspace (restOp τ t s hsym he) s = ⊥ := by
    rw [Submodule.eq_bot_iff]
    constructor
    · intro hgap w hw
      rw [mem_restEig_iff] at hw
      have hz := hgap w.val (B2_val_mem τ w) (by
        rw [restProj_tangent _ _ (restOp_mem τ t s hsym he w.val (B2_val_mem τ w)), hw, neg_smul,
          add_neg_cancel])
      exact (RestSpace.val_eq_zero w).1 hz
    · intro hbot w ho heq
      rw [restProj_tangent _ _ (restOp_mem τ t s hsym he w ho), neg_smul,
        add_neg_eq_zero] at heq
      have := hbot (RestSpace.mk w ho) ((mem_restEig_iff τ t s hsym he s _).2 heq)
      have h' := congrArg RestSpace.val this
      rwa [RestSpace.mk_val, RestSpace.val_zero] at h'
  obtain ⟨hf1, hf2⟩ := C2_finrank τ t s hsym he
  have hK : Module.End.eigenspace (restOp τ t s hsym he) s = ⊥ ↔
      Module.finrank ℝ (Module.End.eigenspace (restOp τ t s hsym he) s) = 0 :=
    Submodule.finrank_eq_zero.symm
  refine ⟨h1, ?_, ?_⟩
  · rw [h1, hK, hf2, Finset.card_eq_zero, Finset.filter_eq_empty_iff]
    simp
  · rw [h1, hK, hf1]; omega

def e0T : Timelike := ⟨ofV CAS03C01.e0, sorry⟩

theorem C4_C01_rest_eigen (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    matVec (toMixed s) e0T.vec = CAS03C01.st s CAS03C01.e0 • e0T.vec := sorry

theorem C4_C01_kernel_bridge (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW)) :
    (∀ w : CAS03C01.W, CAS03C01.kerD s w ↔
      ∃ x ∈ Module.End.eigenspace (restOp e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
          (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest)) (CAS03C01.st s CAS03C01.e0),
        x.val = ofV (0, w)) ∧
    Module.finrank ℝ (kerDSub s) =
      (Finset.univ.filter fun i => restEigenvalues e0T (toMixed s) (CAS03C01.st s CAS03C01.e0)
          (toMixed_selfAdjoint s) (C4_C01_rest_eigen s hrest) i = CAS03C01.st s CAS03C01.e0).card ∧
    Module.finrank ℝ (Module.End.eigenspace (matVecL (toMixed s)) (CAS03C01.st s CAS03C01.e0)) =
      1 + Module.finrank ℝ (kerDSub s) := sorry

theorem C4_C01_fibre (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW))
    (hexp : CAS03C01.zeroExpansion s CAS03C01.e0) (v : CAS03C01.V) :
    CAS03C01.fibre s v ↔ ∃ w : CAS03C01.W, w ∈ kerDSub s ∧ v = CAS03C01.phi w := sorry

theorem C5_C01_isolation_iff_unique_velocity (s : CAS03C01.SymCov)
    (hrest : CAS03C01.bAct s CAS03C01.e0 CAS03C01.e0 = (0, CAS03C01.zeroW))
    (hexp : CAS03C01.zeroExpansion s CAS03C01.e0) :
    RestGapInjective (toMixed s) e0T.vec (-(CAS03C01.st s CAS03C01.e0)) ↔
      ∀ v, CAS03C01.fibre s v ↔ v = CAS03C01.e0 := sorry

theorem C6_C01_controls :
    RestGapInjective (toMixed (CAS03C01.diagonalExample CAS03C01.qPoint)) e0T.vec
      (-(CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qPoint) CAS03C01.e0)) ∧
    ¬ RestGapInjective (toMixed (CAS03C01.diagonalExample CAS03C01.qLine)) e0T.vec
      (-(CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qLine) CAS03C01.e0)) ∧
    Module.finrank ℝ (Module.End.eigenspace (matVecL (toMixed (CAS03C01.diagonalExample CAS03C01.qLine)))
      (CAS03C01.st (CAS03C01.diagonalExample CAS03C01.qLine) CAS03C01.e0)) = 2 := sorry

/-! ## D: conditional smooth local branch at an isolated (simple) timelike eigenvalue -/

structure TimelikeBranch {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E]
    (n : ℕ) (Sfam : E → Mat4) (V : Set E) (u : E → Vec4) (s : E → ℝ) : Prop where
  isOpen : IsOpen V
  smooth_u : ContDiffOn ℝ n u V
  smooth_s : ContDiffOn ℝ n s V
  eigen : ∀ q ∈ V, matVec (Sfam q) (u q) = s q • u q
  unit : ∀ q ∈ V, lorentzDot (u q) (u q) = -1
  future : ∀ q ∈ V, 0 < u q 0
  isolated : ∀ q ∈ V, RestGapInjective (Sfam q) (u q) (-(s q))
  unique : ∀ q ∈ V, ∀ (v : Vec4) (μ : ℝ), matVec (Sfam q) v = μ • v →
    lorentzDot v v = -1 → 0 < v 0 → v = u q ∧ μ = s q

theorem D1_branch {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (n : ℕ) (hn : 1 ≤ n) (D : Set E) (hD : IsOpen D) (Sfam : E → Mat4)
    (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : E) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hiso : RestGapInjective (Sfam q0) u0 (-s0)) :
    ∃ (V : Set E) (u : E → Vec4) (s : E → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := sorry

theorem D2_branch_vec4_via_G04A (n : ℕ) (hn : 1 ≤ n) (D : Set Vec4) (hD : IsOpen D)
    (Sfam : Vec4 → Mat4) (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : Vec4) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hiso : RestGapInjective (Sfam q0) u0 (-s0)) :
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (s : Vec4 → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := sorry

theorem D3_branch_simple {E : Type*} [NormedAddCommGroup E] [NormedSpace ℝ E] [CompleteSpace E]
    (n : ℕ) (hn : 1 ≤ n) (D : Set E) (hD : IsOpen D) (Sfam : E → Mat4)
    (hS : ContDiffOn ℝ n Sfam D) (hsym : ∀ q ∈ D, EtaSelfAdjoint (Sfam q))
    (q0 : E) (hq0 : q0 ∈ D) (u0 : Vec4) (s0 : ℝ)
    (he0 : matVec (Sfam q0) u0 = s0 • u0) (hn0 : lorentzDot u0 u0 = -1) (hf0 : 0 < u0 0)
    (hsimple : Module.finrank ℝ (Module.End.eigenspace (matVecL (Sfam q0)) s0) = 1) :
    ∃ (V : Set E) (u : E → Vec4) (s : E → ℝ),
      q0 ∈ V ∧ V ⊆ D ∧ u q0 = u0 ∧ s q0 = s0 ∧ TimelikeBranch n Sfam V u s := sorry

/-! ## E: controls separating rest-eigenvalue collision from loss of timelike isolation -/

def e0v : Vec4 := coordVec 0

def Rrot : Mat4 := ![![0, -1, 0, 0], ![1, 0, 0, 0], ![0, 0, 0, 0], ![0, 0, 0, 0]]

def Srot (q : Vec4) : Mat4 := q 1 • Rrot

def Pdiag : Mat4 := ![![0, 0, 0, 0], ![0, 1, 0, 0], ![0, 0, 1, 0], ![0, 0, 0, 1]]
def M1 : Mat4 := ![![0, 0, 0, 0], ![0, 1, 0, 0], ![0, 0, -1, 0], ![0, 0, 0, 0]]
def M2 : Mat4 := ![![0, 0, 0, 0], ![0, 0, 1, 0], ![0, 1, 0, 0], ![0, 0, 0, 0]]
def M3 : Mat4 := ![![0, 0, 0, 0], ![0, 0, 0, 0], ![0, 0, 0, 1], ![0, 0, 1, 0]]

def Scol (q : Vec4) : Mat4 := Pdiag + q 1 • M1 + q 2 • M2 + q 3 • M3

theorem E1_isolation_needed (n : ℕ) :
    ContDiff ℝ n Srot ∧ (∀ q, EtaSelfAdjoint (Srot q)) ∧
    matVec (Srot 0) e0v = (0 : ℝ) • e0v ∧ lorentzDot e0v e0v = -1 ∧ 0 < e0v 0 ∧
    ¬ RestGapInjective (Srot 0) e0v (-(0 : ℝ)) ∧
    ¬ ∃ V ∈ 𝓝 (0 : Vec4), ∀ q ∈ V, ∃ (v : Vec4) (μ : ℝ),
        lorentzDot v v < 0 ∧ matVec (Srot q) v = μ • v := sorry

theorem E2_collision_branch_exists (n : ℕ) (hn : 1 ≤ n) :
    ContDiff ℝ n Scol ∧ (∀ q, EtaSelfAdjoint (Scol q)) ∧
    (∀ w, lorentzDot e0v w = 0 → matVec (Scol 0) w = w) ∧
    RestGapInjective (Scol 0) e0v (-(0 : ℝ)) ∧
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (s : Vec4 → ℝ),
      (0 : Vec4) ∈ V ∧ u 0 = e0v ∧ s 0 = 0 ∧ TimelikeBranch n Scol V u s := sorry

theorem E3_no_continuous_rest_eigenvector :
    ¬ ∃ v : Vec4 → Vec4, ContinuousAt v 0 ∧ ∀ᶠ q in 𝓝 (0 : Vec4),
      lorentzDot e0v (v q) = 0 ∧ lorentzDot (v q) (v q) = 1 ∧
        ∃ μ : ℝ, matVec (Scol q) (v q) = μ • v q := sorry

end G03A
