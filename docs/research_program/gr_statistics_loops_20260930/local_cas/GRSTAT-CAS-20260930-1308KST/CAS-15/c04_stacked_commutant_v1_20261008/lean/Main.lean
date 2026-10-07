import Mathlib

/-!
Exact finite-dimensional CAS-15 C04 certificate.  The vector `w` parametrizes all
real skew 3 by 3 matrices through the cross-product action.  The displayed
orientation is immaterial to the commutant, but is fixed throughout this file.
-/

open Matrix BigOperators Module

namespace CAS15C04

abbrev V := Fin 3 → ℝ
abbrev M := Matrix (Fin 3) (Fin 3) ℝ

def skew (w : V) : M := !![0, -w 2, w 1; w 2, 0, -w 0; -w 1, w 0, 0]
def axis (α β : ℝ) (n : V) : M := fun i j => (if i = j then α else 0) + β * n i * n j
def comm (A B : M) : M := A * B - B * A
def unit (n : V) : Prop := n ⬝ᵥ n = 1

theorem axis_symmetric (α β : ℝ) (n : V) : (axis α β n)ᵀ = axis α β n := by
  ext i j
  simp [axis, Matrix.transpose_apply, eq_comm]
  ring

theorem skew_is_skew (w : V) : (skew w)ᵀ = -skew w := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [skew]

theorem skew_represents_all (W : M) (hW : Wᵀ = -W) :
    W = skew ![W 2 1, W 0 2, W 1 0] := by
  have hp (i j : Fin 3) : W j i = -W i j := by
    have h := congrArg (fun X : M => X i j) hW
    simpa using h
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [skew] <;> linarith [hp 0 0, hp 0 1, hp 0 2,
      hp 1 0, hp 1 1, hp 1 2, hp 2 0, hp 2 1, hp 2 2]

theorem skew_mulVec (w n : V) : (skew w).mulVec n = w ⨯₃ n := by
  ext i
  fin_cases i <;>
    simp [skew, Matrix.mulVec, dotProduct, Fin.sum_univ_three, cross_apply,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two] <;> ring

theorem axis_comm_apply (α β : ℝ) (n w : V) (i j : Fin 3) :
    comm (axis α β n) (skew w) i j =
      -β * (n i * (w ⨯₃ n) j + (w ⨯₃ n) i * n j) := by
  fin_cases i <;> fin_cases j <;>
    simp [axis, comm, Matrix.mul_apply, Matrix.vecMul, Fin.sum_univ_three, skew, cross_apply,
      vecHead, vecTail,
      Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_two] <;> ring

theorem axis_comm_zero_iff_cross_zero (α β : ℝ) (n w : V)
    (hn : unit n) (hβ : β ≠ 0) :
    comm (axis α β n) (skew w) = 0 ↔ w ⨯₃ n = 0 := by
  let v : V := w ⨯₃ n
  constructor
  · intro hc
    have hp (i j : Fin 3) : n i * v j + v i * n j = 0 := by
      have h := congrArg (fun X : M => X i j) hc
      rw [axis_comm_apply] at h
      simp only [Matrix.zero_apply] at h
      exact (mul_eq_zero.mp h).resolve_left (neg_ne_zero.mpr hβ)
    have hunit : n 0 * n 0 + n 1 * n 1 + n 2 * n 2 = 1 := by
      simpa [unit, vec3_dotProduct, pow_two] using hn
    have horth : n 0 * v 0 + n 1 * v 1 + n 2 * v 2 = 0 := by
      simpa [v, vec3_dotProduct] using (dot_cross_self w n)
    have hv (i : Fin 3) : v i = 0 := by
      have h0 := congrArg (fun x : ℝ => x * n 0) (hp i 0)
      have h1 := congrArg (fun x : ℝ => x * n 1) (hp i 1)
      have h2 := congrArg (fun x : ℝ => x * n 2) (hp i 2)
      have hu := congrArg (fun x : ℝ => x * v i) hunit
      have ho := congrArg (fun x : ℝ => x * n i) horth
      nlinarith
    exact funext hv
  · intro hv
    ext i j
    rw [axis_comm_apply, hv]
    simp

theorem two_cross_zero (w n₁ n₂ : V) (hn₁ : unit n₁)
    (hind : LinearIndependent ℝ ![n₁, n₂])
    (h₁ : w ⨯₃ n₁ = 0) (h₂ : w ⨯₃ n₂ = 0) : w = 0 := by
  have ht : w ⨯₃ (n₁ ⨯₃ n₂) = 0 := by
    rw [leibniz_cross, h₁, h₂]
    simp
  rw [cross_cross_eq_smul_sub_smul'] at ht
  have hcoeff : (w ⬝ᵥ n₂) • n₁ + (-(n₁ ⬝ᵥ w)) • n₂ = 0 := by
    simpa [sub_eq_add_neg, neg_smul] using ht
  have hdot : n₁ ⬝ᵥ w = 0 := by
    exact neg_eq_zero.mp ((LinearIndependent.pair_iff.mp hind) _ _ hcoeff).2
  have htr := cross_cross_eq_smul_sub_smul' n₁ w n₁
  rw [h₁] at htr
  have hdot' : w ⬝ᵥ n₁ = 0 := by simpa [dotProduct_comm] using hdot
  rw [show n₁ ⬝ᵥ n₁ = 1 from hn₁, one_smul, hdot', zero_smul, sub_zero] at htr
  simpa using htr.symm

theorem cross_zero_iff_span (w n : V) (hn : unit n) :
    w ⨯₃ n = 0 ↔ w ∈ ℝ ∙ n := by
  constructor
  · intro h
    have ht := cross_cross_eq_smul_sub_smul' n w n
    rw [h] at ht
    have hh : w = (w ⬝ᵥ n) • n := by
      rw [show n ⬝ᵥ n = 1 from hn, one_smul] at ht
      exact sub_eq_zero.mp (by simpa using ht.symm)
    exact Submodule.mem_span_singleton.mpr ⟨w ⬝ᵥ n, hh.symm⟩
  · intro h
    obtain ⟨r, rfl⟩ := Submodule.mem_span_singleton.mp h
    simp

theorem two_axis_common_commutant_zero
    (α₁ β₁ α₂ β₂ : ℝ) (n₁ n₂ w : V)
    (hu₁ : unit n₁) (hu₂ : unit n₂)
    (hb₁ : β₁ ≠ 0) (hb₂ : β₂ ≠ 0)
    (hind : LinearIndependent ℝ ![n₁, n₂])
    (h₁ : comm (axis α₁ β₁ n₁) (skew w) = 0)
    (h₂ : comm (axis α₂ β₂ n₂) (skew w) = 0) : w = 0 := by
  exact two_cross_zero w n₁ n₂ hu₁ hind
    ((axis_comm_zero_iff_cross_zero α₁ β₁ n₁ w hu₁ hb₁).mp h₁)
    ((axis_comm_zero_iff_cross_zero α₂ β₂ n₂ w hu₂ hb₂).mp h₂)

def e₀ : V := ![1, 0, 0]
def e₁ : V := ![0, 1, 0]
def e₂ : V := ![0, 0, 1]

theorem skew_decomp (w : V) :
    skew w = w 0 • skew e₀ + w 1 • skew e₁ + w 2 • skew e₂ := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [skew, e₀, e₁, e₂, Matrix.add_apply]

theorem comm_add (A B C : M) : comm A (B + C) = comm A B + comm A C := by
  simp [comm, Matrix.mul_add, Matrix.add_mul, sub_add_sub_comm]

theorem comm_smul (A B : M) (r : ℝ) : comm A (r • B) = r • comm A B := by
  simp [comm, smul_sub]

theorem comm_decomp (A : M) (w : V) :
    comm A (skew w) =
      w 0 • comm A (skew e₀) +
      w 1 • comm A (skew e₁) +
      w 2 • comm A (skew e₂) := by
  rw [skew_decomp, comm_add, comm_add, comm_smul, comm_smul, comm_smul]

noncomputable def s : ℝ := (Real.sqrt 2)⁻¹
noncomputable def E₀ : M := s • skew e₀
noncomputable def E₁ : M := s • skew e₁
noncomputable def E₂ : M := s • skew e₂

theorem s_ne_zero : s ≠ 0 := by
  unfold s
  positivity

theorem s_sq : s * s = 1 / 2 := by
  unfold s
  have hs : (Real.sqrt 2) ^ 2 = 2 := Real.sq_sqrt (by norm_num)
  have hn : Real.sqrt 2 ≠ 0 := by positivity
  field_simp
  nlinarith [hs]

def frobenius (A B : M) : ℝ := ∑ p : Fin 3, ∑ q : Fin 3, A p q * B p q

theorem orthonormal_skew_basis (i j : Fin 3) :
    frobenius (![E₀, E₁, E₂] i) (![E₀, E₁, E₂] j) = if i = j then 1 else 0 := by
  fin_cases i <;> fin_cases j <;>
    simp [frobenius, E₀, E₁, E₂, skew, e₀, e₁, e₂,
      Fin.sum_univ_three, s_sq] <;>
    nlinarith [s_sq]

theorem comm_orth_decomp (A : M) (w : V) :
    comm A (s • skew w) =
      w 0 • comm A E₀ + w 1 • comm A E₁ + w 2 • comm A E₂ := by
  rw [comm_smul, comm_decomp]
  simp [E₀, E₁, E₂, comm_smul, smul_add, smul_smul, mul_comm]

abbrev Observation (k : ℕ) := Fin k × Fin 3 × Fin 3

noncomputable def response {k : ℕ} (Ms : Fin k → M) : Matrix (Observation k) (Fin 3) ℝ :=
  fun ⟨a, p, q⟩ i =>
    ![comm (Ms a) E₀ p q,
      comm (Ms a) E₁ p q,
      comm (Ms a) E₂ p q] i

noncomputable def gram {k : ℕ} (Ms : Fin k → M) : M := (response Ms)ᵀ * response Ms

theorem response_mulVec {k : ℕ} (Ms : Fin k → M) (w : V)
    (a : Fin k) (p q : Fin 3) :
    (response Ms).mulVec w (a, p, q) = comm (Ms a) (s • skew w) p q := by
  have h := congrArg (fun X : M => X p q) (comm_orth_decomp (Ms a) w)
  simpa [response, Matrix.mulVec, dotProduct, Fin.sum_univ_three,
    Matrix.add_apply, Matrix.smul_apply, mul_comm] using h.symm

theorem gram_apply {k : ℕ} (Ms : Fin k → M) (i j : Fin 3) :
    gram Ms i j = ∑ a : Fin k, ∑ p : Fin 3, ∑ q : Fin 3,
      comm (Ms a) (![E₀, E₁, E₂] i) p q *
      comm (Ms a) (![E₀, E₁, E₂] j) p q := by
  classical
  fin_cases i <;> fin_cases j <;>
    simp [gram, response, Matrix.mul_apply, Fintype.sum_prod_type]

theorem gram_frobenius {k : ℕ} (Ms : Fin k → M) (i j : Fin 3) :
    gram Ms i j = ∑ a : Fin k,
      frobenius (comm (Ms a) (![E₀, E₁, E₂] i))
        (comm (Ms a) (![E₀, E₁, E₂] j)) := by
  simpa [frobenius] using gram_apply Ms i j

theorem gram_kernel_iff {k : ℕ} (Ms : Fin k → M) (w : V) :
    (gram Ms).mulVec w = 0 ↔
      ∀ a : Fin k, comm (Ms a) (skew w) = 0 := by
  have hk := Matrix.ker_mulVecLin_transpose_mul_self (response Ms)
  constructor
  · intro h a
    have hr : (response Ms).mulVec w = 0 := by
      have hm : w ∈ LinearMap.ker (gram Ms).mulVecLin := by
        change (gram Ms).mulVec w = 0
        exact h
      rw [gram, hk] at hm
      change (response Ms).mulVec w = 0 at hm
      exact hm
    ext p q
    have hv := congrArg (fun v : Observation k → ℝ => v (a, p, q)) hr
    rw [response_mulVec, comm_smul] at hv
    simpa using (mul_eq_zero.mp (by simpa using hv)).resolve_left s_ne_zero
  · intro h
    have hr : (response Ms).mulVec w = 0 := by
      funext x
      rcases x with ⟨a,p,q⟩
      rw [response_mulVec, comm_smul, h a]
      simp
    have hm : w ∈ LinearMap.ker (response Ms).mulVecLin := by
      change (response Ms).mulVec w = 0
      exact hr
    have : w ∈ LinearMap.ker (gram Ms).mulVecLin := by
      rw [gram, hk]
      exact hm
    change (gram Ms).mulVec w = 0 at this
    exact this

theorem gram_kernel_all_skew {k : ℕ} (Ms : Fin k → M) (W : M)
    (hW : Wᵀ = -W) :
    (gram Ms).mulVec (![W 2 1, W 0 2, W 1 0]) = 0 ↔
      ∀ a : Fin k, comm (Ms a) W = 0 := by
  rw [gram_kernel_iff]
  simp only [← skew_represents_all W hW]

def pairAxes (α₁ β₁ α₂ β₂ : ℝ) (n₁ n₂ : V) : Fin 2 → M :=
  ![axis α₁ β₁ n₁, axis α₂ β₂ n₂]

theorem pair_response_injective
    (α₁ β₁ α₂ β₂ : ℝ) (n₁ n₂ : V)
    (hu₁ : unit n₁) (hu₂ : unit n₂)
    (hb₁ : β₁ ≠ 0) (hb₂ : β₂ ≠ 0)
    (hind : LinearIndependent ℝ ![n₁, n₂]) :
    Function.Injective (response (pairAxes α₁ β₁ α₂ β₂ n₁ n₂)).mulVec := by
  let Ms := pairAxes α₁ β₁ α₂ β₂ n₁ n₂
  have hz (w : V) (h : (response Ms).mulVec w = 0) : w = 0 := by
    have hg : (gram Ms).mulVec w = 0 := by
      rw [gram, ← mulVec_mulVec, h, mulVec_zero]
    have hall := (gram_kernel_iff Ms w).mp hg
    exact two_axis_common_commutant_zero α₁ β₁ α₂ β₂ n₁ n₂ w hu₁ hu₂ hb₁ hb₂ hind
      (by simpa [Ms, pairAxes] using hall 0)
      (by simpa [Ms, pairAxes] using hall 1)
  intro x y hxy
  apply sub_eq_zero.mp
  apply hz
  rw [mulVec_sub, hxy, sub_self]

theorem pair_gram_posDef_rank_three
    (α₁ β₁ α₂ β₂ : ℝ) (n₁ n₂ : V)
    (hu₁ : unit n₁) (hu₂ : unit n₂)
    (hb₁ : β₁ ≠ 0) (hb₂ : β₂ ≠ 0)
    (hind : LinearIndependent ℝ ![n₁, n₂]) :
    (gram (pairAxes α₁ β₁ α₂ β₂ n₁ n₂)).PosDef ∧
      (gram (pairAxes α₁ β₁ α₂ β₂ n₁ n₂)).rank = 3 := by
  have hi := pair_response_injective α₁ β₁ α₂ β₂ n₁ n₂ hu₁ hu₂ hb₁ hb₂ hind
  have hp : (gram (pairAxes α₁ β₁ α₂ β₂ n₁ n₂)).PosDef := by
    simpa [gram] using Matrix.PosDef.conjTranspose_mul_self
      (response (pairAxes α₁ β₁ α₂ β₂ n₁ n₂)) hi
  refine ⟨hp, ?_⟩
  simpa using Matrix.rank_of_isUnit _ hp.isUnit

def oneAxis (α β : ℝ) (n : V) : Fin 1 → M := fun _ => axis α β n

theorem one_axis_kernel_span (α β : ℝ) (n : V)
    (hn : unit n) (hβ : β ≠ 0) :
    LinearMap.ker (gram (oneAxis α β n)).mulVecLin = ℝ ∙ n := by
  ext w
  change (gram (oneAxis α β n)).mulVec w = 0 ↔ w ∈ ℝ ∙ n
  rw [gram_kernel_iff]
  constructor
  · intro h
    exact (cross_zero_iff_span w n hn).mp
      ((axis_comm_zero_iff_cross_zero α β n w hn hβ).mp
        (by simpa [oneAxis] using h 0))
  · intro h a
    fin_cases a
    exact (axis_comm_zero_iff_cross_zero α β n w hn hβ).mpr
      ((cross_zero_iff_span w n hn).mpr h)

theorem one_axis_rank_two (α β : ℝ) (n : V)
    (hn : unit n) (hβ : β ≠ 0) :
    (gram (oneAxis α β n)).rank = 2 := by
  have hn0 : n ≠ 0 := by
    intro h
    have : n ⬝ᵥ n = 1 := hn
    simp [h] at this
  have hker : finrank ℝ (LinearMap.ker (gram (oneAxis α β n)).mulVecLin) = 1 := by
    rw [one_axis_kernel_span α β n hn hβ, finrank_span_singleton hn0]
  have hr := LinearMap.finrank_range_add_finrank_ker
    (gram (oneAxis α β n)).mulVecLin
  rw [hker] at hr
  have hdim : finrank ℝ V = 3 := by simp [V]
  rw [hdim] at hr
  change (gram (oneAxis α β n)).rank + 1 = 3 at hr
  omega

theorem isotropic_response_zero (α : ℝ) (n w : V) :
    comm (axis α 0 n) (skew w) = 0 := by
  ext i j
  rw [axis_comm_apply]
  simp

theorem parallel_pair_kernel_span (α₁ β₁ α₂ β₂ : ℝ) (n : V)
    (hn : unit n) (hβ₁ : β₁ ≠ 0) (hβ₂ : β₂ ≠ 0) :
    LinearMap.ker (gram (pairAxes α₁ β₁ α₂ β₂ n n)).mulVecLin = ℝ ∙ n := by
  ext w
  change (gram (pairAxes α₁ β₁ α₂ β₂ n n)).mulVec w = 0 ↔ w ∈ ℝ ∙ n
  rw [gram_kernel_iff]
  constructor
  · intro h
    exact (cross_zero_iff_span w n hn).mp
      ((axis_comm_zero_iff_cross_zero α₁ β₁ n w hn hβ₁).mp
        (by simpa [pairAxes] using h 0))
  · intro h a
    fin_cases a
    · exact (axis_comm_zero_iff_cross_zero α₁ β₁ n w hn hβ₁).mpr
        ((cross_zero_iff_span w n hn).mpr h)
    · exact (axis_comm_zero_iff_cross_zero α₂ β₂ n w hn hβ₂).mpr
        ((cross_zero_iff_span w n hn).mpr h)

theorem parallel_pair_kernel_dimension_one (α₁ β₁ α₂ β₂ : ℝ) (n : V)
    (hn : unit n) (hβ₁ : β₁ ≠ 0) (hβ₂ : β₂ ≠ 0) :
    finrank ℝ (LinearMap.ker (gram (pairAxes α₁ β₁ α₂ β₂ n n)).mulVecLin) = 1 := by
  have hn0 : n ≠ 0 := by
    intro h
    have hu : n ⬝ᵥ n = 1 := hn
    simp [h] at hu
  rw [parallel_pair_kernel_span α₁ β₁ α₂ β₂ n hn hβ₁ hβ₂,
    finrank_span_singleton hn0]

end CAS15C04

#print axioms CAS15C04.skew_represents_all
#print axioms CAS15C04.orthonormal_skew_basis
#print axioms CAS15C04.gram_frobenius
#print axioms CAS15C04.gram_kernel_iff
#print axioms CAS15C04.gram_kernel_all_skew
#print axioms CAS15C04.one_axis_rank_two
#print axioms CAS15C04.pair_gram_posDef_rank_three
#print axioms CAS15C04.parallel_pair_kernel_dimension_one
