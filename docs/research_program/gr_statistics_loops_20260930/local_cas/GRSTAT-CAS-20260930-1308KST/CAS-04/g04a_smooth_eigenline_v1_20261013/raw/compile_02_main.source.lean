import Mathlib
import Proof

/-!
# G04-A: rest-basis budget at a smooth selected energy eigenline (GR-CAS-04)

Imports the accepted scoped CAS-04 Lean `Proof.lean` (namespace `GRSTATCAS04`) unchanged and
connects its finite statements C01–C04 to an actual smooth energy eigenfield:

* E0 `E0_gap_iff_eigenvalues`: "L = S_T + εI invertible on the rest space" ⇔ all `ε + p_i ≠ 0`.
* E1 `E1_smooth_eigenline`: implicit function theorem on the bordered system
  `(v, μ) ↦ (T v − μ v, η(v,v) + 1)` gives a C^n normalized future eigenfield near a simple point;
  `E1u_unique`: the future unit timelike eigenvector is unique wherever L is invertible.
* E2 `E2_directional_C01`, `E2_path_C01`: the field's derivative obeys Proof.lean's C01.
* E3 `E3_restbasis_exists`, `E3_hproj`, `E3_weighted_rate`: pointwise rest orthonormal eigenbasis;
  Proof.lean's C02 premise `hproj` is derived (not assumed) for the actual rate fields.
* E4 `E4_gap_budget`, `E4_euler_actual`: C03 (gap `|ε + p_i|`, equality support) and C04 (Euler)
  at the actual fields. `G04A_composite` chains E1 → E3 → E4 from base-point hypotheses only.

Scope: flat Minkowski η in inertial coordinates (covariant derivative = coordinate derivative),
finite regularity C^n (1 ≤ n), local neighbourhood only (no global continuation), simple
(non-degenerate) energy eigenvalue only.
-/

namespace G04A
open GRSTATCAS04 Finset
open scoped Topology ContDiff

def EtaSelfAdjoint (t : Mat4) : Prop := ∀ a b : Fin 4, eta a * t a b = eta b * t b a

def RestGapInjective (t : Mat4) (u : Vec4) (ε : ℝ) : Prop :=
  ∀ w : Vec4, lorentzDot u w = 0 → restProj u (matVec t w) + ε • w = 0 → w = 0

def FutureUnitEigen (t : Mat4) (u : Vec4) (ε : ℝ) : Prop :=
  matVec t u = (-ε) • u ∧ lorentzDot u u = -1 ∧ 0 < u 0

def RestEigenbasis (t : Mat4) (u : Vec4) (e : Fin 3 → Vec4) (p : Fin 3 → ℝ) : Prop :=
  (∀ i j, lorentzDot (e i) (e j) = if i = j then 1 else 0) ∧
  (∀ i, lorentzDot u (e i) = 0) ∧ (∀ i, matVec t (e i) = p i • e i)

/-! ### Algebraic helper lemmas -/

theorem eta_zero : eta 0 = -1 := by simp [eta]
theorem eta_one : eta 1 = 1 := by simp [eta]
theorem eta_two : eta 2 = 1 := by
  have : (2 : Fin 4) ≠ 0 := by decide
  simp [eta, this]
theorem eta_three : eta 3 = 1 := by
  have : (3 : Fin 4) ≠ 0 := by decide
  simp [eta, this]

theorem lorentzDot_expand (v w : Vec4) :
    lorentzDot v w = -(v 0 * w 0) + v 1 * w 1 + v 2 * w 2 + v 3 * w 3 := by
  rw [lorentzDot, Fin.sum_univ_four, eta_zero, eta_one, eta_two, eta_three]; ring

theorem lorentzDot_comm (v w : Vec4) : lorentzDot v w = lorentzDot w v := by
  simp only [lorentzDot]; apply Finset.sum_congr rfl; intro i _; ring

theorem lorentzDot_add_left (u v w : Vec4) :
    lorentzDot (u + v) w = lorentzDot u w + lorentzDot v w := by
  rw [lorentzDot_comm, lorentzDot_add_right, lorentzDot_comm w, lorentzDot_comm w]

theorem lorentzDot_smul_left (u v : Vec4) (r : ℝ) :
    lorentzDot (r • u) v = r * lorentzDot u v := by
  rw [lorentzDot_comm, lorentzDot_smul_right, lorentzDot_comm]

theorem lorentzDot_zero_right (u : Vec4) : lorentzDot u 0 = 0 := by
  simp [lorentzDot]

theorem lorentzDot_sum_right (u : Vec4) {ι : Type*} (s : Finset ι) (v : ι → Vec4) :
    lorentzDot u (∑ k ∈ s, v k) = ∑ k ∈ s, lorentzDot u (v k) := by
  classical
  induction s using Finset.induction_on with
  | empty => simp [lorentzDot]
  | insert k s hk ih => rw [Finset.sum_insert hk, Finset.sum_insert hk, lorentzDot_add_right, ih]

theorem lorentzDot_sum_left (u : Vec4) {ι : Type*} (s : Finset ι) (v : ι → Vec4) :
    lorentzDot (∑ k ∈ s, v k) u = ∑ k ∈ s, lorentzDot (v k) u := by
  rw [lorentzDot_comm, lorentzDot_sum_right]
  exact Finset.sum_congr rfl (fun k _ => lorentzDot_comm _ _)

theorem matVec_sum (t : Mat4) {ι : Type*} (s : Finset ι) (v : ι → Vec4) :
    matVec t (∑ k ∈ s, v k) = ∑ k ∈ s, matVec t (v k) := by
  classical
  induction s using Finset.induction_on with
  | empty => funext a; simp [matVec]
  | insert k s hk ih => rw [Finset.sum_insert hk, Finset.sum_insert hk, matVec_add, ih]

theorem restProj_inner (u v w : Vec4) (h : lorentzDot w u = 0) :
    lorentzDot w (restProj u v) = lorentzDot w v := by
  have : restProj u v = v + lorentzDot u v • u := by funext a; simp [restProj]
  rw [this, lorentzDot_add_right, lorentzDot_smul_right, h, mul_zero, add_zero]

theorem selfAdj_dot {t : Mat4} (h : EtaSelfAdjoint t) (v w : Vec4) :
    lorentzDot v (matVec t w) = lorentzDot (matVec t v) w := by
  simp only [lorentzDot, matVec, Finset.mul_sum, Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl; intro b _
  apply Finset.sum_congr rfl; intro a _
  linear_combination (v a * w b) * h a b

/-- For a future/past-agnostic unit timelike `u`, the rest space is positive semidefinite. -/
theorem rest_nonneg (u w : Vec4) (hn : lorentzDot u u = -1) (ho : lorentzDot u w = 0) :
    0 ≤ lorentzDot w w := by
  rw [lorentzDot_expand] at hn ho ⊢
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
  have hu0 : u 0 * u 0 = 1 + A := by linarith
  have hB0 : 0 ≤ B := by
    have := mul_self_nonneg (w 1); have := mul_self_nonneg (w 2); have := mul_self_nonneg (w 3)
    simp only [hB]; linarith
  have hA0 : 0 ≤ A := by
    have := mul_self_nonneg (u 1); have := mul_self_nonneg (u 2); have := mul_self_nonneg (u 3)
    simp only [hA]; linarith
  have key : (u 0 * u 0) * (B - w 0 * w 0) ≥ B := by
    have : (u 0 * w 0)^2 = (u 0 * u 0) * (w 0 * w 0) := by ring
    nlinarith
  have hpos : 0 < u 0 * u 0 := by linarith
  have : 0 ≤ B - w 0 * w 0 := by
    by_contra hneg
    replace hneg := not_le.mp hneg
    have := mul_neg_of_pos_of_neg hpos hneg
    linarith
  simp only [hB] at this
  linarith

/-! ### Completeness of an η-orthonormal frame -/

theorem frame_complete (F : Fin 4 → Vec4)
    (hF : ∀ μ ν, lorentzDot (F μ) (F ν) = if μ = ν then eta μ else 0) (w : Vec4) :
    w = ∑ μ : Fin 4, (eta μ * lorentzDot (F μ) w) • F μ := by
  let M : Matrix (Fin 4) (Fin 4) ℝ := Matrix.of fun a μ => F μ a
  let G : Matrix (Fin 4) (Fin 4) ℝ := Matrix.diagonal eta
  have hG : G * G = 1 := by
    simp only [G, Matrix.diagonal_mul_diagonal]
    rw [← Matrix.diagonal_one]; congr 1; funext i; fin_cases i <;> simp [eta]
  have hO : M.transpose * G * M = G := by
    ext μ ν
    have := hF μ ν
    simp only [lorentzDot] at this
    simp only [M, G, Matrix.mul_apply, Matrix.transpose_apply, Matrix.of_apply,
      Matrix.diagonal_apply, mul_ite, mul_zero, Finset.sum_ite_eq', Finset.mem_univ, if_true]
    rw [← this]
    apply Finset.sum_congr rfl; intro i _; ring
  have h1 : (G * M.transpose * G) * M = 1 := by
    calc (G * M.transpose * G) * M = G * (M.transpose * G * M) := by
          simp only [Matrix.mul_assoc]
      _ = 1 := by rw [hO, hG]
  have h2 : M * (G * M.transpose * G) = 1 := mul_eq_one_comm.mp h1
  funext a
  have hab : ∀ b, (∑ μ : Fin 4, F μ a * eta μ * F μ b * eta b) = if a = b then 1 else 0 := by
    intro b
    have := congrFun (congrFun h2 a) b
    simp only [M, G, Matrix.mul_apply, Matrix.transpose_apply, Matrix.of_apply,
      Matrix.diagonal_apply, mul_ite, mul_zero, Finset.sum_ite_eq', Finset.mem_univ, if_true,
      Matrix.one_apply, ite_mul, zero_mul, Finset.sum_ite_eq] at this
    rw [← this]
    apply Finset.sum_congr rfl; intro μ _
    simp [mul_comm, mul_left_comm]
  simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul, lorentzDot]
  calc w a = ∑ b : Fin 4, (if a = b then 1 else 0) * w b := by simp
    _ = ∑ b : Fin 4, (∑ μ : Fin 4, F μ a * eta μ * F μ b * eta b) * w b := by
        apply Finset.sum_congr rfl; intro b _; rw [hab b]
    _ = _ := by
        simp only [Finset.sum_mul, Finset.mul_sum]
        rw [Finset.sum_comm]
        apply Finset.sum_congr rfl; intro μ _
        apply Finset.sum_congr rfl; intro b _
        ring

/-- Expansion of a rest vector in an orthonormal rest triad. -/
theorem rest_expand (u : Vec4) (e : Fin 3 → Vec4) (hn : lorentzDot u u = -1)
    (he : ∀ i j, lorentzDot (e i) (e j) = if i = j then 1 else 0)
    (hue : ∀ i, lorentzDot u (e i) = 0) (w : Vec4) :
    w = (-(lorentzDot u w)) • u + ∑ i : Fin 3, (lorentzDot (e i) w) • e i := by
  have hF : ∀ μ ν, lorentzDot ((Fin.cons u e : Fin 4 → Vec4) μ) ((Fin.cons u e : Fin 4 → Vec4) ν)
      = if μ = ν then eta μ else 0 := by
    intro μ ν
    refine Fin.cases ?_ (fun i => ?_) μ <;> refine Fin.cases ?_ (fun j => ?_) ν
    · simp [hn, eta]
    · simp [hue j, Fin.succ_ne_zero, eq_comm (a := (0 : Fin 4))]
    · simp [lorentzDot_comm (e i) u, hue i, Fin.succ_ne_zero]
    · simp [he i j, eta, Fin.succ_ne_zero, Fin.succ_inj]
  have := frame_complete _ hF w
  rw [Fin.sum_univ_succ] at this
  simpa [eta] using this

/-! ### Boost frame: an explicit η-orthonormal rest triad for a future unit timelike `u` -/

noncomputable def boost (u : Vec4) (i : Fin 3) : Vec4 :=
  fun a => if a = 0 then u i.succ else (if a = i.succ then 1 else 0) + u a * u i.succ * (1 / (1 + u 0))

theorem boost_props (u : Vec4) (hn : lorentzDot u u = -1) (hf : 0 < u 0) :
    (∀ i j, lorentzDot (boost u i) (boost u j) = if i = j then 1 else 0) ∧
    (∀ i, lorentzDot u (boost u i) = 0) := by
  have hk : (1 / (1 + u 0)) * (1 + u 0) = 1 := by field_simp
  set k := 1 / (1 + u 0) with hkdef
  rw [lorentzDot_expand] at hn
  constructor
  · intro i j
    fin_cases i <;> fin_cases j <;> simp [boost, lorentzDot_expand]
    · linear_combination (u 1 * u 1 * (1 + (u 0 - 1) * k)) * hk + (u 1 * u 1 * k ^ 2) * hn
    · linear_combination (u 1 * u 2 * (1 + (u 0 - 1) * k)) * hk + (u 1 * u 2 * k ^ 2) * hn
    · linear_combination (u 1 * u 3 * (1 + (u 0 - 1) * k)) * hk + (u 1 * u 3 * k ^ 2) * hn
    · linear_combination (u 2 * u 1 * (1 + (u 0 - 1) * k)) * hk + (u 2 * u 1 * k ^ 2) * hn
    · linear_combination (u 2 * u 2 * (1 + (u 0 - 1) * k)) * hk + (u 2 * u 2 * k ^ 2) * hn
    · linear_combination (u 2 * u 3 * (1 + (u 0 - 1) * k)) * hk + (u 2 * u 3 * k ^ 2) * hn
    · linear_combination (u 3 * u 1 * (1 + (u 0 - 1) * k)) * hk + (u 3 * u 1 * k ^ 2) * hn
    · linear_combination (u 3 * u 2 * (1 + (u 0 - 1) * k)) * hk + (u 3 * u 2 * k ^ 2) * hn
    · linear_combination (u 3 * u 3 * (1 + (u 0 - 1) * k)) * hk + (u 3 * u 3 * k ^ 2) * hn
  · intro i
    fin_cases i <;> simp [boost, lorentzDot_expand]
    · linear_combination (u 1 * (u 0 - 1)) * hk + (u 1 * k) * hn
    · linear_combination (u 2 * (u 0 - 1)) * hk + (u 2 * k) * hn
    · linear_combination (u 3 * (u 0 - 1)) * hk + (u 3 * k) * hn

theorem lorentzDot_orthoSum (e : Fin 3 → Vec4)
    (he : ∀ i j, lorentzDot (e i) (e j) = if i = j then 1 else 0) (a : Fin 3 → ℝ) (i : Fin 3) :
    lorentzDot (e i) (∑ j : Fin 3, a j • e j) = a i := by
  rw [lorentzDot_sum_right]
  simp only [lorentzDot_smul_right, he, mul_ite, mul_one, mul_zero]
  simp

/-- Pointwise rest inner product / orthonormal rest eigenbasis (E3, pointwise construction). -/
theorem E3_restbasis_exists (t : Mat4) (u : Vec4) (ε : ℝ) (hsym : EtaSelfAdjoint t)
    (hu : FutureUnitEigen t u ε) : ∃ (e : Fin 3 → Vec4) (p : Fin 3 → ℝ), RestEigenbasis t u e p := by
  obtain ⟨hEig, hn, hf⟩ := hu
  obtain ⟨hff, huf⟩ := boost_props u hn hf
  set f := boost u with hfdef
  let A : Matrix (Fin 3) (Fin 3) ℝ := Matrix.of fun i j => lorentzDot (f i) (matVec t (f j))
  have hA : A.IsHermitian := by
    apply Matrix.IsHermitian.ext; intro i j
    simp only [A, Matrix.of_apply, star_trivial]
    rw [selfAdj_dot hsym, lorentzDot_comm]
  let O := hA.eigenvectorBasis
  let e : Fin 3 → Vec4 := fun j => ∑ k : Fin 3, (O j k) • f k
  -- T maps each boost vector into the rest space, expanded in the boost triad
  have hTf : ∀ k, matVec t (f k) = ∑ l : Fin 3, A l k • f l := by
    intro k
    have hx := rest_expand u f hn hff huf (matVec t (f k))
    have h0 : lorentzDot u (matVec t (f k)) = 0 := by
      rw [selfAdj_dot hsym, hEig, lorentzDot_smul_left, huf k, mul_zero]
    rw [h0, neg_zero, zero_smul, zero_add] at hx
    exact hx
  refine ⟨e, hA.eigenvalues, ?_, ?_, ?_⟩
  · intro i j
    have hO := (orthonormal_iff_ite.1 O.orthonormal) i j
    rw [EuclideanSpace.inner_eq_star_dotProduct] at hO
    have : lorentzDot (e i) (e j) = ∑ k : Fin 3, O i k * O j k := by
      simp only [e]
      rw [lorentzDot_sum_left]
      apply Finset.sum_congr rfl; intro k _
      rw [lorentzDot_smul_left, lorentzDot_orthoSum f hff]
    rw [this, ← hO]
    simp [dotProduct, mul_comm]
  · intro i
    simp only [e]
    rw [lorentzDot_sum_right]
    simp [lorentzDot_smul_right, huf]
  · intro j
    have hev := congrFun (hA.mulVec_eigenvectorBasis j)
    simp only [e]
    rw [matVec_sum]
    simp only [matVec_smul, hTf, Finset.smul_sum, smul_smul]
    rw [Finset.sum_comm]
    apply Finset.sum_congr rfl; intro l _
    rw [← Finset.sum_smul]
    congr 1
    have := hev l
    simp only [Matrix.mulVec, dotProduct, Pi.smul_apply, smul_eq_mul, A, Matrix.of_apply] at this
    rw [← this]
    apply Finset.sum_congr rfl; intro k _
    simp only [A, Matrix.of_apply, O]; ring

/-- E0: the source's two forms of the spectral separation agree. -/
theorem E0_gap_iff_eigenvalues (t : Mat4) (u : Vec4) (ε : ℝ) (e : Fin 3 → Vec4)
    (p : Fin 3 → ℝ) (hn : lorentzDot u u = -1) (hB : RestEigenbasis t u e p) :
    RestGapInjective t u ε ↔ ∀ i, ε + p i ≠ 0 := by
  obtain ⟨he, hue, hTe⟩ := hB
  constructor
  · intro hgap i hzero
    have h1 : restProj u (matVec t (e i)) + ε • e i = 0 := by
      rw [hTe i, restProj_smul, restProj_tangent u (e i) (hue i), ← add_smul]
      have : p i + ε = 0 := by linarith
      simp [this]
    have h2 := hgap (e i) (hue i) h1
    have h3 := he i i
    rw [h2, lorentzDot_zero_right] at h3
    simp at h3
  · intro hne w ho heq
    have hw := rest_expand u e hn he hue w
    rw [ho, neg_zero, zero_smul, zero_add] at hw
    have hTw : matVec t w = ∑ i : Fin 3, (lorentzDot (e i) w * p i) • e i := by
      conv_lhs => rw [hw]
      rw [matVec_sum]
      apply Finset.sum_congr rfl; intro i _
      rw [matVec_smul, hTe i, smul_smul]
    have hci : ∀ i, lorentzDot (e i) w = 0 := by
      intro i
      have h := congrArg (lorentzDot (e i)) heq
      rw [lorentzDot_add_right, restProj_inner u _ _ (by rw [lorentzDot_comm]; exact hue i),
        lorentzDot_smul_right, lorentzDot_zero_right, hTw, lorentzDot_orthoSum e he] at h
      have h' : (p i + ε) * lorentzDot (e i) w = 0 := by linarith
      rcases mul_eq_zero.mp h' with h0 | h0
      · exact absurd (by linarith : ε + p i = 0) (hne i)
      · exact h0
    rw [hw]
    simp [hci]

/-- E1u: wherever L is invertible, the future unit timelike eigenvector is unique. -/
theorem E1u_unique (t : Mat4) (u v : Vec4) (ε μ : ℝ) (hsym : EtaSelfAdjoint t)
    (hu : FutureUnitEigen t u ε) (hgap : RestGapInjective t u ε)
    (hv : FutureUnitEigen t v μ) : v = u ∧ μ = ε := by
  obtain ⟨hTu, hnu, hfu⟩ := hu
  obtain ⟨hTv, hnv, hfv⟩ := hv
  have huv : lorentzDot u v ≠ 0 := by
    intro h0
    have := rest_nonneg u v hnu h0
    linarith
  have hme : μ = ε := by
    have h1 := selfAdj_dot hsym u v
    rw [hTu, hTv, lorentzDot_smul_right, lorentzDot_smul_left] at h1
    have : (ε - μ) * lorentzDot u v = 0 := by linarith
    rcases mul_eq_zero.mp this with h | h
    · linarith
    · exact absurd h huv
  subst hme
  set w := v + lorentzDot u v • u with hw
  have how : lorentzDot u w = 0 := by
    rw [hw, lorentzDot_add_right, lorentzDot_smul_right, hnu]; ring
  have hTw : matVec t w = (-μ) • w := by
    rw [hw, matVec_add, matVec_smul, hTu, hTv, smul_add, smul_smul, smul_smul, mul_comm]
  have hw0 : w = 0 := hgap w how (by
    rw [hTw, restProj_smul, restProj_tangent u w how, ← add_smul]; simp)
  have hvu : v = (-(lorentzDot u v)) • u := by
    have : v + lorentzDot u v • u = 0 := hw0
    rw [neg_smul, eq_neg_iff_add_eq_zero]; exact this
  have hsq : lorentzDot u v * lorentzDot u v = 1 := by
    have := hnv
    rw [hvu, lorentzDot_smul_left, lorentzDot_smul_right, hnu] at this
    linarith
  have hneg : lorentzDot u v < 0 := by
    have h0 := congrFun hvu 0
    simp only [Pi.smul_apply, smul_eq_mul] at h0
    by_contra hc
    replace hc := not_lt.mp hc
    have : -(lorentzDot u v) * u 0 ≤ 0 := by
      have := mul_nonneg hc hfu.le; linarith
    linarith
  have hm1 : lorentzDot u v = -1 := by nlinarith
  refine ⟨?_, rfl⟩
  rw [hvu, hm1]; simp

/-! ### E1: implicit function theorem on the bordered eigen-system -/

structure SmoothEnergyFrame (n : ℕ) (T : Vec4 → Mat4) (V : Set Vec4)
    (u : Vec4 → Vec4) (ε : Vec4 → ℝ) : Prop where
  isOpen : IsOpen V
  smooth_T : ContDiffOn ℝ n T V
  smooth_u : ContDiffOn ℝ n u V
  smooth_ε : ContDiffOn ℝ n ε V
  selfAdj : ∀ x ∈ V, EtaSelfAdjoint (T x)
  eigen : ∀ x ∈ V, FutureUnitEigen (T x) (u x) (ε x)
  gap : ∀ x ∈ V, RestGapInjective (T x) (u x) (ε x)

/-- The bordered eigen-system `(x, (v, μ)) ↦ (T(x) v − μ v, η(v,v) + 1)` (source line 91). -/
def bordered (T : Vec4 → Mat4) (q : Vec4 × (Vec4 × ℝ)) : Vec4 × ℝ :=
  (matVec (T q.1) q.2.1 - q.2.2 • q.2.1, lorentzDot q.2.1 q.2.1 + 1)

theorem bordered_contDiffAt {n : ℕ} {T : Vec4 → Mat4} {x : Vec4} (hT : ContDiffAt ℝ n T x)
    (y : Vec4 × ℝ) : ContDiffAt ℝ n (bordered T) (x, y) := by
  have hTab : ∀ a b, ContDiffAt ℝ n (fun q : Vec4 × (Vec4 × ℝ) => T q.1 a b) (x, y) := by
    intro a b
    have h1 : ContDiffAt ℝ n (fun z => T z a b) x := contDiffAt_pi.1 (contDiffAt_pi.1 hT a) b
    exact h1.comp (x, y) contDiffAt_fst
  have hv : ∀ b, ContDiffAt ℝ n (fun q : Vec4 × (Vec4 × ℝ) => q.2.1 b) (x, y) := by
    intro b
    exact ((contDiff_apply ℝ ℝ b).contDiffAt).comp (x, y) (contDiffAt_fst.comp (x, y) contDiffAt_snd)
  have hm : ContDiffAt ℝ n (fun q : Vec4 × (Vec4 × ℝ) => q.2.2) (x, y) :=
    contDiffAt_snd.comp (x, y) contDiffAt_snd
  refine ContDiffAt.prodMk ?_ ?_
  · refine contDiffAt_pi.2 (fun a => ?_)
    have : (fun q : Vec4 × (Vec4 × ℝ) => (matVec (T q.1) q.2.1 - q.2.2 • q.2.1) a) =
        fun q => (∑ b : Fin 4, T q.1 a b * q.2.1 b) - q.2.2 * q.2.1 a := by
      funext q; simp [matVec]
    rw [this]
    exact (ContDiffAt.sum fun b _ => (hTab a b).mul (hv b)).sub (hm.mul (hv a))
  · have : (fun q : Vec4 × (Vec4 × ℝ) => lorentzDot q.2.1 q.2.1 + 1) =
        fun q => (∑ i : Fin 4, eta i * q.2.1 i * q.2.1 i) + 1 := by
      funext q; simp [lorentzDot]
    rw [this]
    exact (ContDiffAt.sum fun i _ => (contDiffAt_const.mul (hv i)).mul (hv i)).add contDiffAt_const

theorem quad_hasDerivAt (α β γ : ℝ) :
    HasDerivAt (fun s : ℝ => α + β * s + γ * s ^ 2) β 0 := by
  have h1 : HasDerivAt (fun s : ℝ => s) 1 0 := hasDerivAt_id' 0
  have h : HasDerivAt (fun s : ℝ => α + β * s + γ * s ^ 2) (β * 1 + γ * (↑2 * 0 ^ (2 - 1) * 1)) 0 :=
    ((h1.const_mul β).const_add α).add ((h1.pow 2).const_mul γ)
  exact h.congr_deriv (by norm_num)

/-- The `(v, μ)`-block of the derivative of the bordered system (its "bordered Jacobian"). -/
theorem bordered_fderiv_inr {T : Vec4 → Mat4} {x : Vec4} {y : Vec4 × ℝ}
    (hd : DifferentiableAt ℝ (bordered T) (x, y)) (w : Vec4) (m : ℝ) :
    (fderiv ℝ (bordered T) (x, y) ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)) (w, m) =
      (matVec (T x) w - y.2 • w - m • y.1, 2 * lorentzDot y.1 w) := by
  rw [ContinuousLinearMap.comp_apply, ContinuousLinearMap.inr_apply]
  set d : Vec4 × (Vec4 × ℝ) := (0, (w, m))
  have hline : HasDerivAt (fun s : ℝ => ((x, y) : Vec4 × (Vec4 × ℝ)) + s • d) d 0 := by
    simpa using ((hasDerivAt_id (0 : ℝ)).smul_const d).const_add ((x, y) : Vec4 × (Vec4 × ℝ))
  have h1 := hd.hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) hline (by simp)
  have h2 : HasDerivAt (bordered T ∘ fun s : ℝ => ((x, y) : Vec4 × (Vec4 × ℝ)) + s • d)
      (matVec (T x) w - y.2 • w - m • y.1, 2 * lorentzDot y.1 w) 0 := by
    have hfun : (bordered T ∘ fun s : ℝ => ((x, y) : Vec4 × (Vec4 × ℝ)) + s • d) =
        fun s => (matVec (T x) (y.1 + s • w) - (y.2 + s * m) • (y.1 + s • w),
          lorentzDot (y.1 + s • w) (y.1 + s • w) + 1) := by
      funext s; simp [bordered, d]
    rw [hfun]
    refine HasDerivAt.prodMk ?_ ?_
    · refine hasDerivAt_pi.2 (fun a => ?_)
      have hc : (fun s : ℝ => (matVec (T x) (y.1 + s • w) - (y.2 + s * m) • (y.1 + s • w)) a) =
          fun s => ((∑ b : Fin 4, T x a b * y.1 b) - y.2 * y.1 a) +
            ((∑ b : Fin 4, T x a b * w b) - y.2 * w a - m * y.1 a) * s + (-(m * w a)) * s ^ 2 := by
        funext s; simp [matVec, Fin.sum_univ_four]; ring
      rw [hc]
      have := quad_hasDerivAt ((∑ b : Fin 4, T x a b * y.1 b) - y.2 * y.1 a)
        ((∑ b : Fin 4, T x a b * w b) - y.2 * w a - m * y.1 a) (-(m * w a))
      exact this.congr_deriv (by simp [matVec])
    · have hc : (fun s : ℝ => lorentzDot (y.1 + s • w) (y.1 + s • w) + 1) =
          fun s => (lorentzDot y.1 y.1 + 1) + (2 * lorentzDot y.1 w) * s + (lorentzDot w w) * s ^ 2 := by
        funext s; simp only [lorentzDot_expand, Pi.add_apply, Pi.smul_apply, smul_eq_mul]; ring
      rw [hc]
      exact quad_hasDerivAt _ _ _
  exact h1.unique h2

theorem bordered_inj {t : Mat4} {u : Vec4} {ε : ℝ} (hsym : EtaSelfAdjoint t)
    (hu : matVec t u = (-ε) • u) (hn : lorentzDot u u = -1) (hgap : RestGapInjective t u ε)
    (w : Vec4) (m : ℝ)
    (h : ((matVec t w - (-ε) • w - m • u, 2 * lorentzDot u w) : Vec4 × ℝ) = 0) :
    w = 0 ∧ m = 0 := by
  have h1 : matVec t w - (-ε) • w - m • u = 0 := congrArg Prod.fst h
  have h2 : 2 * lorentzDot u w = 0 := congrArg Prod.snd h
  have ho : lorentzDot u w = 0 := by linarith
  have hTw : lorentzDot u (matVec t w) = 0 := by
    rw [selfAdj_dot hsym, hu, lorentzDot_smul_left, ho, mul_zero]
  have hm : m = 0 := by
    have := congrArg (lorentzDot u) h1
    have e1 : matVec t w - (-ε) • w - m • u = matVec t w + (ε • w + (-m) • u) := by
      funext a; simp; ring
    rw [e1, lorentzDot_add_right, lorentzDot_add_right, lorentzDot_smul_right,
      lorentzDot_smul_right, hTw, ho, hn, lorentzDot_zero_right] at this
    linarith
  subst hm
  refine ⟨hgap w ho ?_, rfl⟩
  have e2 : matVec t w - (-ε) • w - (0 : ℝ) • u = matVec t w + ε • w := by
    funext a; simp
  rw [e2] at h1
  have hr : restProj u (matVec t w) = matVec t w := restProj_tangent u _ hTw
  rw [hr]; exact h1

theorem isInvertible_of_injective {L : (Vec4 × ℝ) →L[ℝ] (Vec4 × ℝ)}
    (h : Function.Injective L) : L.IsInvertible :=
  ⟨(LinearEquiv.ofInjectiveEndo L.toLinearMap h).toContinuousLinearEquiv, by ext v <;> rfl⟩

/-- E1: smooth (C^n) normalized future energy eigenfield near a simple point (IFT). -/
theorem E1_smooth_eigenline (n : ℕ) (hn : 1 ≤ n) (S : Set Vec4) (hS : IsOpen S)
    (T : Vec4 → Mat4) (hT : ContDiffOn ℝ n T S) (hsym : ∀ x ∈ S, EtaSelfAdjoint (T x))
    (x0 : Vec4) (hx0 : x0 ∈ S) (u0 : Vec4) (ε0 : ℝ)
    (h0 : FutureUnitEigen (T x0) u0 ε0) (hgap0 : RestGapInjective (T x0) u0 ε0) :
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (ε : Vec4 → ℝ),
      x0 ∈ V ∧ V ⊆ S ∧ u x0 = u0 ∧ ε x0 = ε0 ∧ SmoothEnergyFrame n T V u ε := by
  obtain ⟨hE0, hN0, hF0⟩ := h0
  have hn0 : ((n : ℕ∞ω)) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  have hninf : ((n : ℕ∞ω)) ≠ ∞ := by simp
  have hn1 : (1 : ℕ∞ω) ≤ n := by exact_mod_cast hn
  have hTat : ∀ x ∈ S, ContDiffAt ℝ n T x := fun x hx => hT.contDiffAt (hS.mem_nhds hx)
  set p0 : Vec4 × (Vec4 × ℝ) := (x0, (u0, -ε0)) with hp0
  have hcd : ContDiffAt ℝ n (bordered T) p0 := bordered_contDiffAt (hTat x0 hx0) _
  have hdiff : ∀ x ∈ S, ∀ y, DifferentiableAt ℝ (bordered T) (x, y) :=
    fun x hx y => (bordered_contDiffAt (hTat x hx) y).differentiableAt (by exact_mod_cast hn0)
  have hinv : (fderiv ℝ (bordered T) p0 ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)).IsInvertible := by
    apply isInvertible_of_injective
    rw [injective_iff_map_eq_zero]
    rintro ⟨w, m⟩ hwm
    rw [bordered_fderiv_inr (hdiff x0 hx0 _)] at hwm
    obtain ⟨hw, hm⟩ := bordered_inj (hsym x0 hx0) hE0 hN0 hgap0 w m hwm
    simp [hw, hm]
  set ψ := hcd.implicitFunction hn0 hinv with hψdef
  have hψ0 : ψ x0 = (u0, -ε0) := hcd.implicitFunction_apply_self hn0 hinv
  have hψcd : ContDiffAt ℝ n ψ x0 := hcd.contDiffAt_implicitFunction hn0 hinv
  have ev1 : ∀ᶠ x in 𝓝 x0, bordered T (x, ψ x) = bordered T p0 :=
    hcd.eventually_apply_implicitFunction hn0 hinv
  have ev2 : ∀ᶠ x in 𝓝 x0, ContDiffAt ℝ n ψ x := hψcd.eventually hninf
  have ev3 : ∀ᶠ x in 𝓝 x0, 0 < (ψ x).1 0 := by
    have hc : ContinuousAt (fun x => (ψ x).1 0) x0 :=
      (continuous_apply 0).continuousAt.comp (continuousAt_fst.comp hψcd.continuousAt)
    have ht := hc.tendsto
    simp only [hψ0] at ht
    exact ht.eventually_const_lt hF0
  have ev4 : ∀ᶠ x in 𝓝 x0, x ∈ S := hS.mem_nhds hx0
  have ev5 : ∀ᶠ x in 𝓝 x0,
      (fderiv ℝ (bordered T) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)).IsInvertible := by
    have hc : ContinuousAt (fun x =>
        fderiv ℝ (bordered T) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)) x0 := by
      have hpair : ContinuousAt (fun x => (x, ψ x)) x0 :=
        continuousAt_id.prodMk hψcd.continuousAt
      have hfd : ContinuousAt (fderiv ℝ (bordered T)) (x0, ψ x0) := by
        rw [hψ0]; exact hcd.continuousAt_fderiv hn0
      exact (ContinuousAt.comp (f := fun x => (x, ψ x)) hfd hpair).clm_comp continuousAt_const
    have hmem : Set.range ((↑) : ((Vec4 × ℝ) ≃L[ℝ] (Vec4 × ℝ)) → (Vec4 × ℝ) →L[ℝ] (Vec4 × ℝ)) ∈
        𝓝 (fderiv ℝ (bordered T) (x0, ψ x0) ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)) := by
      apply ContinuousLinearEquiv.isOpen.mem_nhds
      rw [hψ0]; exact hinv
    exact hc.preimage_mem_nhds hmem
  obtain ⟨V, hVprop, hVopen, hx0V⟩ :=
    eventually_nhds_iff.1 (ev1.and (ev2.and (ev3.and (ev4.and ev5))))
  have hVS : V ⊆ S := fun x hx => (hVprop x hx).2.2.2.1
  have hbp0 : bordered T p0 = 0 := by
    simp only [bordered, hp0, hE0]
    ext a <;> simp [hN0]
  refine ⟨V, fun x => (ψ x).1, fun x => -(ψ x).2, hx0V, hVS, by simp [hψ0], by simp [hψ0], ?_⟩
  refine ⟨hVopen, hT.mono hVS, ?_, ?_, fun x hx => hsym x (hVS hx), ?_, ?_⟩
  · intro x hx
    exact (contDiffAt_fst.comp x (hVprop x hx).2.1).contDiffWithinAt
  · intro x hx
    exact (contDiffAt_snd.comp x (hVprop x hx).2.1).neg.contDiffWithinAt
  · intro x hx
    have hb := (hVprop x hx).1
    rw [hbp0] at hb
    have hb1 : matVec (T x) (ψ x).1 - (ψ x).2 • (ψ x).1 = 0 := congrArg Prod.fst hb
    have hb2 : lorentzDot (ψ x).1 (ψ x).1 + 1 = 0 := congrArg Prod.snd hb
    refine ⟨?_, by linarith, (hVprop x hx).2.2.1⟩
    rw [neg_neg]; exact sub_eq_zero.mp hb1
  · intro x hx w ho hL
    have hxS := hVS hx
    have hb := (hVprop x hx).1
    rw [hbp0] at hb
    have hb1 : matVec (T x) (ψ x).1 = (ψ x).2 • (ψ x).1 := sub_eq_zero.mp (congrArg Prod.fst hb)
    have hTw : lorentzDot (ψ x).1 (matVec (T x) w) = 0 := by
      rw [selfAdj_dot (hsym x hxS), hb1, lorentzDot_smul_left, ho, mul_zero]
    rw [restProj_tangent _ _ hTw] at hL
    have hinj := ((hVprop x hx).2.2.2.2).injective
    have hz : (fderiv ℝ (bordered T) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)) (w, 0) =
        (fderiv ℝ (bordered T) (x, ψ x) ∘L ContinuousLinearMap.inr ℝ Vec4 (Vec4 × ℝ)) 0 := by
      rw [map_zero, bordered_fderiv_inr (hdiff x hxS _)]
      have e1 : matVec (T x) w - (ψ x).2 • w - (0 : ℝ) • (ψ x).1 = matVec (T x) w + (-(ψ x).2) • w := by
        funext a; simp; ring
      rw [e1, hL, ho]; simp
    have := hinj hz
    exact congrArg Prod.fst this

/-! ### E2: derivative of the actual eigenfield obeys Proof.lean's C01 -/

theorem bounded_path (V : Set Vec4) (hV : IsOpen V) (x : Vec4) (hx : x ∈ V)
    (X : Fin 4 → Vec4) : ∃ r : ℝ, 0 < r ∧ ∀ a s, x + (r * Real.sin s) • X a ∈ V := by
  obtain ⟨δ, hδ, hball⟩ := Metric.isOpen_iff.1 hV x hx
  set N := ∑ a : Fin 4, ‖X a‖ with hN
  have hN0 : 0 ≤ N := Finset.sum_nonneg (fun a _ => norm_nonneg (X a))
  set r := δ / (2 * (N + 1)) with hr
  have hrpos : 0 < r := by positivity
  have hrN : r * (N + 1) = δ / 2 := by rw [hr]; field_simp
  refine ⟨r, hrpos, fun a s => hball ?_⟩
  rw [Metric.mem_ball, dist_eq_norm, add_sub_cancel_left, norm_smul]
  have h1 : ‖r * Real.sin s‖ ≤ r := by
    rw [Real.norm_eq_abs, abs_mul, abs_of_pos hrpos]
    exact mul_le_of_le_one_right hrpos.le (Real.abs_sin_le_one s)
  have h2 : ‖X a‖ ≤ N := Finset.single_le_sum (f := fun a => ‖X a‖)
    (fun a _ => norm_nonneg (X a)) (Finset.mem_univ a)
  calc ‖r * Real.sin s‖ * ‖X a‖ ≤ r * N :=
        mul_le_mul h1 h2 (norm_nonneg _) hrpos.le
    _ ≤ r * (N + 1) := by nlinarith
    _ = δ / 2 := hrN
    _ < δ := by linarith

theorem sin_path_hasDerivAt (x X : Vec4) (r : ℝ) :
    HasDerivAt (fun s : ℝ => x + (r * Real.sin s) • X) (r • X) 0 := by
  have h := (((Real.hasDerivAt_sin 0).const_mul r).smul_const X).const_add x
  exact h.congr_deriv (by simp)

theorem matVec_smul_left (t : Mat4) (v : Vec4) (r : ℝ) :
    matVec (r • t) v = r • matVec t v := by
  funext a; simp [matVec, Finset.mul_sum, mul_assoc]

theorem E2_directional_C01 {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) (X : Vec4) :
    restProj (u x) (matVec (T x) (c • fderiv ℝ u x X)) + ε x • (c • fderiv ℝ u x X) =
      (-c) • restProj (u x) (matVec (fderiv ℝ T x X) (u x)) := by
  have hn0 : ((n : ℕ∞ω)) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  have hVx : V ∈ 𝓝 x := hF.isOpen.mem_nhds hx
  have hTd := ((hF.smooth_T.differentiableOn hn0).differentiableAt hVx).hasFDerivAt
  have hud := ((hF.smooth_u.differentiableOn hn0).differentiableAt hVx).hasFDerivAt
  have hεd := ((hF.smooth_ε.differentiableOn hn0).differentiableAt hVx).hasFDerivAt
  obtain ⟨r, hr, hpath⟩ := bounded_path V hF.isOpen x hx (fun _ => X)
  set γ : ℝ → Vec4 := fun s => x + (r * Real.sin s) • X with hγ
  have hγV : ∀ s, γ s ∈ V := fun s => hpath 0 s
  have hγ0 : x = γ 0 := by simp [hγ]
  have hγd : HasDerivAt γ (r • X) 0 := sin_path_hasDerivAt x X r
  have hT1 := hTd.comp_hasDerivAt_of_eq (0 : ℝ) hγd hγ0
  have hu1 := hud.comp_hasDerivAt_of_eq (0 : ℝ) hγd hγ0
  have hε1 := hεd.comp_hasDerivAt_of_eq (0 : ℝ) hγd hγ0
  have ht : ∀ a b, HasDerivAt (fun s => T (γ s) a b) (fderiv ℝ T x (r • X) a b) 0 :=
    fun a b => hasDerivAt_pi.1 (hasDerivAt_pi.1 hT1 a) b
  have hu : ∀ a, HasDerivAt (fun s => u (γ s) a) (fderiv ℝ u x (r • X) a) 0 :=
    fun a => hasDerivAt_pi.1 hu1 a
  have key := projected_eigen_derivative (fun s => T (γ s)) (fun s => u (γ s)) (fun s => ε (γ s))
    0 (c / r) (fderiv ℝ T x (r • X)) (fderiv ℝ u x (r • X)) (fderiv ℝ ε x (r • X))
    (div_pos hc hr) ht hu hε1 (fun s => (hF.eigen (γ s) (hγV s)).2.1)
    (fun s => (hF.eigen (γ s) (hγV s)).1)
  simp only [← hγ0] at key
  rw [map_smul, map_smul] at key
  have h1 : (c / r) • (r • fderiv ℝ u x X) = c • fderiv ℝ u x X := by
    rw [smul_smul, div_mul_cancel₀ c hr.ne']
  have h2 : (-(c / r)) • restProj (u x) (matVec (r • fderiv ℝ T x X) (u x)) =
      (-c) • restProj (u x) (matVec (fderiv ℝ T x X) (u x)) := by
    rw [matVec_smul_left, restProj_smul, smul_smul, neg_mul, div_mul_cancel₀ c hr.ne']
  rw [h1, h2] at key
  exact key

theorem E2_path_C01 {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (γ : ℝ → Vec4) (s0 : ℝ) (X : Vec4) (hγ : HasDerivAt γ X s0)
    (hγV : γ s0 ∈ V) (du : Vec4) (dt : Mat4)
    (hdu : HasDerivAt (fun s => u (γ s)) du s0) (hdt : HasDerivAt (fun s => T (γ s)) dt s0) :
    restProj (u (γ s0)) (matVec (T (γ s0)) (c • du)) + ε (γ s0) • (c • du) =
      (-c) • restProj (u (γ s0)) (matVec dt (u (γ s0))) := by
  have hn0 : ((n : ℕ∞ω)) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  have hVx : V ∈ 𝓝 (γ s0) := hF.isOpen.mem_nhds hγV
  have hTd := ((hF.smooth_T.differentiableOn hn0).differentiableAt hVx).hasFDerivAt
  have hud := ((hF.smooth_u.differentiableOn hn0).differentiableAt hVx).hasFDerivAt
  have e1 : du = fderiv ℝ u (γ s0) X := hdu.unique (hud.comp_hasDerivAt s0 hγ)
  have e2 : dt = fderiv ℝ T (γ s0) X := hdt.unique (hTd.comp_hasDerivAt s0 hγ)
  rw [e1, e2]
  exact E2_directional_C01 hn hF c hc (γ s0) hγV X

/-! ### E3: actual rest basis and the derived C02 premise `hproj` -/

def frameVec (u : Vec4) (e : Fin 3 → Vec4) : Fin 4 → Vec4 := Fin.cons u e

noncomputable def rateArr (c : ℝ) (u : Vec4 → Vec4) (x : Vec4) (e : Fin 3 → Vec4) : Arr :=
  fun μ i => lorentzDot (e i) (c • fderiv ℝ u x (frameVec (u x) e μ))

noncomputable def sourceArr (T : Vec4 → Mat4) (u : Vec4 → Vec4) (x : Vec4)
    (e : Fin 3 → Vec4) : Arr :=
  fun μ i => lorentzDot (e i) (restProj (u x) (matVec (fderiv ℝ T x (frameVec (u x) e μ)) (u x)))

noncomputable def rateBudget (c : ℝ) (q : Arr) : ℝ :=
  (theta q)^2 / 3 + (∑ i : Fin 3, ∑ j : Fin 3, (sigma q i j)^2) +
    2 * (∑ i : Fin 3, (omega q i)^2) + (∑ i : Fin 3, (accel c q i)^2) / c^2

theorem E3_hproj {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) (e : Fin 3 → Vec4) (p : Fin 3 → ℝ)
    (hB : RestEigenbasis (T x) (u x) e p) :
    (∀ i, ε x + p i ≠ 0) ∧
    ∀ μ i, (fun j => ε x + p j) i * rateArr c u x e μ i = -c * sourceArr T u x e μ i := by
  have hgap := (E0_gap_iff_eigenvalues (T x) (u x) (ε x) e p (hF.eigen x hx).2.1 hB).1 (hF.gap x hx)
  refine ⟨hgap, fun μ i => ?_⟩
  obtain ⟨he, hue, hTe⟩ := hB
  have h2 := congrArg (lorentzDot (e i))
    (E2_directional_C01 hn hF c hc x hx (frameVec (u x) e μ))
  have heu : lorentzDot (e i) (u x) = 0 := by rw [lorentzDot_comm]; exact hue i
  rw [lorentzDot_add_right, restProj_inner _ _ _ heu, selfAdj_dot (hF.selfAdj x hx), hTe i,
    lorentzDot_smul_left, lorentzDot_smul_right, lorentzDot_smul_right] at h2
  simp only [rateArr, sourceArr]
  simp only [lorentzDot_smul_right] at h2 ⊢
  linear_combination h2

theorem E3_weighted_rate {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) :
    ∃ (e : Fin 3 → Vec4) (p : Fin 3 → ℝ), RestEigenbasis (T x) (u x) e p ∧
      (∀ i, ε x + p i ≠ 0) ∧
      (∀ μ i, (ε x + p i) * rateArr c u x e μ i = -c * sourceArr T u x e μ i) ∧
      rateBudget c (rateArr c u x e) =
        c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (ε x + p i)^2) := by
  obtain ⟨e, p, hB⟩ := E3_restbasis_exists (T x) (u x) (ε x) (hF.selfAdj x hx) (hF.eigen x hx)
  obtain ⟨hgap, hproj⟩ := E3_hproj hn hF c hc x hx e p hB
  refine ⟨e, p, hB, hgap, hproj, ?_⟩
  exact weighted_rate_from_eigenbasis c (rateArr c u x e) (sourceArr T u x e)
    (fun i => ε x + p i) hc hgap hproj

/-! ### E4: C03 and C04 at the actual fields -/

noncomputable def minGap (ε : ℝ) (p : Fin 3 → ℝ) : ℝ :=
  Finset.univ.inf' Finset.univ_nonempty (fun i => |ε + p i|)

theorem E4_gap_budget {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (c : ℝ) (hc : 0 < c) (x : Vec4) (hx : x ∈ V) (e : Fin 3 → Vec4) (p : Fin 3 → ℝ)
    (hB : RestEigenbasis (T x) (u x) e p) :
    0 < minGap (ε x) p ∧
    rateBudget c (rateArr c u x e) =
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (ε x + p i)^2) ∧
    rateBudget c (rateArr c u x e) ≤
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (minGap (ε x) p)^2) ∧
    (rateBudget c (rateArr c u x e) =
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (minGap (ε x) p)^2) ↔
      ∀ μ i, sourceArr T u x e μ i = 0 ∨ |ε x + p i| = minGap (ε x) p) := by
  obtain ⟨hgap, hproj⟩ := E3_hproj hn hF c hc x hx e p hB
  have hW : rateBudget c (rateArr c u x e) =
      c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (ε x + p i)^2) :=
    weighted_rate_from_eigenbasis c (rateArr c u x e) (sourceArr T u x e)
      (fun i => ε x + p i) hc hgap hproj
  have hδ : 0 < minGap (ε x) p :=
    (Finset.lt_inf'_iff _).2 (fun i _ => abs_pos.2 (hgap i))
  have hg : ∀ i, minGap (ε x) p ≤ |ε x + p i| :=
    fun i => Finset.inf'_le (fun i => |ε x + p i|) (Finset.mem_univ i)
  have hmin : ∃ i, |ε x + p i| = minGap (ε x) p := by
    obtain ⟨i, _, hi⟩ := Finset.exists_mem_eq_inf' Finset.univ_nonempty (fun i => |ε x + p i|)
    exact ⟨i, hi.symm⟩
  have hC := physical_gap_bound_and_equality c (minGap (ε x) p) (sourceArr T u x e)
    (fun i => ε x + p i) hc hδ hg hmin
  refine ⟨hδ, hW, ?_, ?_⟩
  · rw [hW]; exact hC.1
  · rw [hW]; exact hC.2

def fluidMixed (e p : ℝ) (w : Vec4) : Mat4 :=
  fun a b => (e + p) * w a * (eta b * w b) + (if a = b then p else 0)

def coordVec (a : Fin 4) : Vec4 := Pi.single a 1

theorem eta_sq (b : Fin 4) : eta b * eta b = 1 := by
  fin_cases b <;> simp [eta_zero, eta_one, eta_two, eta_three]

theorem fluid_eigen (e p : ℝ) (w : Vec4) (hn : lorentzDot w w = -1) :
    matVec (fluidMixed e p w) w = (-e) • w := by
  funext a
  have h : (∑ b : Fin 4, ((e + p) * w a * (eta b * w b) + (if a = b then p else 0)) * w b) =
      (e + p) * w a * lorentzDot w w + p * w a := by
    simp only [lorentzDot, Fin.sum_univ_four]
    fin_cases a <;> simp <;> ring
  simp only [matVec, fluidMixed, Pi.smul_apply, smul_eq_mul]
  rw [h, hn]; ring

theorem fluid_rest (e p : ℝ) (w v : Vec4) (ho : lorentzDot w v = 0) :
    matVec (fluidMixed e p w) v = p • v := by
  funext a
  have h : (∑ b : Fin 4, ((e + p) * w a * (eta b * w b) + (if a = b then p else 0)) * v b) =
      (e + p) * w a * lorentzDot w v + p * v a := by
    simp only [lorentzDot, Fin.sum_univ_four]
    fin_cases a <;> simp <;> ring
  simp only [matVec, fluidMixed, Pi.smul_apply, smul_eq_mul]
  rw [h, ho]; ring

theorem fluidMixed_raise (e p : ℝ) (w : Vec4) (a b : Fin 4) :
    fluidMixed e p w a b * eta b = fluidStress e p w a b := by
  have := eta_sq b
  simp only [fluidMixed, fluidStress]
  split_ifs <;> linear_combination ((e + p) * w a * w b) * this

theorem accJet_smul (u : Vec4) (D : Fin 4 → Vec4) (r : ℝ) :
    accJet u (fun a => r • D a) = r • accJet u D := by
  funext b; simp [accJet, Finset.mul_sum]; apply Finset.sum_congr rfl; intro a _; ring

theorem raiseGrad_smul (g : Vec4) (r : ℝ) :
    raiseGrad (fun a => r * g a) = r • raiseGrad g := by
  funext b; simp [raiseGrad]; ring

theorem E4_euler_actual {n : ℕ} (hn : 1 ≤ n) {T : Vec4 → Mat4} {V : Set Vec4}
    {u : Vec4 → Vec4} {ε : Vec4 → ℝ} (hF : SmoothEnergyFrame n T V u ε)
    (eF pF : Vec4 → ℝ) (w : Vec4 → Vec4)
    (hfluid : ∀ y ∈ V, T y = fluidMixed (eF y) (pF y) (w y))
    (hw : ∀ y ∈ V, lorentzDot (w y) (w y) = -1 ∧ 0 < w y 0)
    (x : Vec4) (hx : x ∈ V) (hpd : DifferentiableAt ℝ pF x)
    (hcons : ∀ b, ∑ a : Fin 4, fderiv ℝ (fun y => T y a b * eta b) x (coordVec a) = 0)
    (c : ℝ) (hc : 0 < c) :
    (∀ y ∈ V, w y = u y ∧ eF y = ε y) ∧ ε x + pF x ≠ 0 ∧
    c^2 • accJet (u x) (fun a => fderiv ℝ u x (coordVec a)) =
      (-c^2 / (ε x + pF x)) • restProj (u x) (raiseGrad (fun a => fderiv ℝ pF x (coordVec a))) := by
  have hn0 : ((n : ℕ∞ω)) ≠ 0 := by exact_mod_cast (show n ≠ 0 by omega)
  -- Step 1: the fluid velocity is the selected energy eigenfield (E1u)
  have hwu : ∀ y ∈ V, w y = u y ∧ eF y = ε y := by
    intro y hy
    have hfe : FutureUnitEigen (T y) (w y) (eF y) := by
      refine ⟨?_, (hw y hy).1, (hw y hy).2⟩
      rw [hfluid y hy]; exact fluid_eigen _ _ _ (hw y hy).1
    exact E1u_unique (T y) (u y) (w y) (ε y) (eF y) (hF.selfAdj y hy) (hF.eigen y hy)
      (hF.gap y hy) hfe
  -- Step 2: the enthalpy gap ε + p is nonzero (from the simple-eigenvalue condition)
  have hgapx : ε x + pF x ≠ 0 := by
    intro hz
    obtain ⟨e, p, he, hue, -⟩ :=
      E3_restbasis_exists (T x) (u x) (ε x) (hF.selfAdj x hx) (hF.eigen x hx)
    have hT0 : matVec (T x) (e 0) = pF x • e 0 := by
      rw [hfluid x hx]
      exact fluid_rest _ _ _ _ (by rw [(hwu x hx).1]; exact hue 0)
    have h0 := hF.gap x hx (e 0) (hue 0) (by
      rw [hT0, restProj_smul, restProj_tangent _ _ (hue 0), ← add_smul,
        show pF x + ε x = 0 by linarith, zero_smul])
    have h1 := he 0 0
    rw [h0, lorentzDot_zero_right] at h1
    simp at h1
  refine ⟨hwu, hgapx, ?_⟩
  -- Step 3: bounded coordinate paths and Proof.lean's C04
  have hVx : V ∈ 𝓝 x := hF.isOpen.mem_nhds hx
  have hud := ((hF.smooth_u.differentiableOn hn0).differentiableAt hVx)
  have hεd := ((hF.smooth_ε.differentiableOn hn0).differentiableAt hVx)
  obtain ⟨r, hr, hpath⟩ := bounded_path V hF.isOpen x hx coordVec
  set γ : Fin 4 → ℝ → Vec4 := fun a s => x + (r * Real.sin s) • coordVec a with hγ
  have hγ0 : ∀ a, x = γ a 0 := fun a => by simp [hγ]
  have hγd : ∀ a, HasDerivAt (γ a) (r • coordVec a) 0 := fun a => sin_path_hasDerivAt x _ r
  have he : ∀ a, HasDerivAt (fun s => ε (γ a s)) (fderiv ℝ ε x (r • coordVec a)) 0 :=
    fun a => hεd.hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) (hγd a) (hγ0 a)
  have hp : ∀ a, HasDerivAt (fun s => pF (γ a s)) (fderiv ℝ pF x (r • coordVec a)) 0 :=
    fun a => hpd.hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) (hγd a) (hγ0 a)
  have hu : ∀ a b, HasDerivAt (fun s => u (γ a s) b) (fderiv ℝ u x (r • coordVec a) b) 0 :=
    fun a b => hasDerivAt_pi.1 (hud.hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) (hγd a) (hγ0 a)) b
  -- conservation along the paths
  have hG : ∀ a b, DifferentiableAt ℝ (fun y => fluidStress (ε y) (pF y) (u y) a b) x := by
    intro a b
    simp only [fluidStress]
    have hua : DifferentiableAt ℝ (fun y => u y a) x := differentiableAt_pi.1 hud a
    have hub : DifferentiableAt ℝ (fun y => u y b) x := differentiableAt_pi.1 hud b
    exact (((hεd.add hpd).mul hua).mul hub).add (hpd.const_mul _)
  have hEq : ∀ a b, (fun y => T y a b * eta b) =ᶠ[𝓝 x]
      (fun y => fluidStress (ε y) (pF y) (u y) a b) := by
    intro a b
    filter_upwards [hVx] with y hy
    rw [hfluid y hy, fluidMixed_raise, (hwu y hy).1, (hwu y hy).2]
  have hcons' : ∀ b, (∑ a : Fin 4,
      deriv (fun s => fluidStress (ε (γ a s)) (pF (γ a s)) (u (γ a s)) a b) 0) = 0 := by
    intro b
    have hd : ∀ a, deriv (fun s => fluidStress (ε (γ a s)) (pF (γ a s)) (u (γ a s)) a b) 0 =
        r * fderiv ℝ (fun y => T y a b * eta b) x (coordVec a) := by
      intro a
      have h1 := (hG a b).hasFDerivAt.comp_hasDerivAt_of_eq (0 : ℝ) (hγd a) (hγ0 a)
      rw [show (fun s => fluidStress (ε (γ a s)) (pF (γ a s)) (u (γ a s)) a b) =
        ((fun y => fluidStress (ε y) (pF y) (u y) a b) ∘ γ a) from rfl, h1.deriv,
        (hEq a b).fderiv_eq, map_smul, smul_eq_mul]
    simp only [hd, ← Finset.mul_sum, hcons b, mul_zero]
  have key := euler_from_actual_conservation (fun a s => ε (γ a s)) (fun a s => pF (γ a s))
    (fun a s => u (γ a s)) (ε x) (pF x) c (u x)
    (fun a => fderiv ℝ ε x (r • coordVec a)) (fun a => fderiv ℝ pF x (r • coordVec a))
    (fun a => fderiv ℝ u x (r • coordVec a)) hc hgapx
    (fun a => by simp [← hγ0 a]) (fun a => by simp [← hγ0 a]) (fun a => by simp [← hγ0 a])
    he hp hu (fun a s => (hF.eigen (γ a s) (hpath a s)).2.1) hcons'
  have hdu : (fun a => fderiv ℝ u x (r • coordVec a)) = fun a => r • fderiv ℝ u x (coordVec a) := by
    funext a; rw [map_smul]
  have hdp : (fun a => fderiv ℝ pF x (r • coordVec a)) = fun a => r * fderiv ℝ pF x (coordVec a) := by
    funext a; rw [map_smul, smul_eq_mul]
  rw [hdu, hdp, accJet_smul, raiseGrad_smul, restProj_smul, smul_comm (c^2) r,
    smul_comm (-c^2 / (ε x + pF x)) r] at key
  exact smul_right_injective Vec4 hr.ne' key

/-- Composite: from base-point hypotheses only, E1 → E3 → E4 at every point of the neighbourhood. -/
theorem G04A_composite (n : ℕ) (hn : 1 ≤ n) (S : Set Vec4) (hS : IsOpen S)
    (T : Vec4 → Mat4) (hT : ContDiffOn ℝ n T S) (hsym : ∀ x ∈ S, EtaSelfAdjoint (T x))
    (x0 : Vec4) (hx0 : x0 ∈ S) (u0 : Vec4) (ε0 : ℝ)
    (h0 : FutureUnitEigen (T x0) u0 ε0) (hgap0 : RestGapInjective (T x0) u0 ε0)
    (c : ℝ) (hc : 0 < c) :
    ∃ (V : Set Vec4) (u : Vec4 → Vec4) (ε : Vec4 → ℝ),
      x0 ∈ V ∧ V ⊆ S ∧ u x0 = u0 ∧ ε x0 = ε0 ∧ SmoothEnergyFrame n T V u ε ∧
      ∀ x ∈ V, ∃ (e : Fin 3 → Vec4) (p : Fin 3 → ℝ), RestEigenbasis (T x) (u x) e p ∧
        (∀ i, ε x + p i ≠ 0) ∧
        (∀ μ i, (ε x + p i) * rateArr c u x e μ i = -c * sourceArr T u x e μ i) ∧
        0 < minGap (ε x) p ∧
        rateBudget c (rateArr c u x e) =
          c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (ε x + p i)^2) ∧
        rateBudget c (rateArr c u x e) ≤
          c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (minGap (ε x) p)^2) ∧
        (rateBudget c (rateArr c u x e) =
          c^2 * (∑ μ : Fin 4, ∑ i : Fin 3, (sourceArr T u x e μ i)^2 / (minGap (ε x) p)^2) ↔
          ∀ μ i, sourceArr T u x e μ i = 0 ∨ |ε x + p i| = minGap (ε x) p) := by
  obtain ⟨V, u, ε, hx0V, hVS, hu0, hε0, hF⟩ :=
    E1_smooth_eigenline n hn S hS T hT hsym x0 hx0 u0 ε0 h0 hgap0
  refine ⟨V, u, ε, hx0V, hVS, hu0, hε0, hF, fun x hx => ?_⟩
  obtain ⟨e, p, hB⟩ := E3_restbasis_exists (T x) (u x) (ε x) (hF.selfAdj x hx) (hF.eigen x hx)
  obtain ⟨hgap, hproj⟩ := E3_hproj hn hF c hc x hx e p hB
  exact ⟨e, p, hB, hgap, hproj, E4_gap_budget hn hF c hc x hx e p hB⟩

end G04A
