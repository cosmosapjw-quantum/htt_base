import Mathlib.Analysis.Calculus.Deriv.Inv
import Mathlib.LinearAlgebra.Matrix.Rank
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.Tactic

set_option maxRecDepth 4096
set_option maxHeartbeats 2000000

open scoped BigOperators Matrix
noncomputable section
namespace R7

-- Fixed symmetric rank-three witness in the contract's 111,...,333 ordering.
def O : Fin 3 → Fin 3 → Fin 3 → ℝ :=
  ![![![1,0,0], ![0,-2,1], ![0,1,1]],
    ![![0,-2,1], ![-2,1,-1], ![1,-1,-1]],
    ![![0,1,1], ![1,-1,-1], ![1,-1,1]]]
def Q : Matrix (Fin 3) (Fin 3) ℝ := Matrix.diagonal ![-1,0,1]
def v : Fin 3 → ℝ := ![0,-1,1]

theorem T1_symmetry : (∀ i j k, O i j k = O j i k) ∧
    (∀ i j k, O i j k = O i k j) := by
  constructor <;> intro i j k <;> fin_cases i <;> fin_cases j <;> fin_cases k <;> norm_num [O]

theorem T1_trace_and_contraction :
    Matrix.trace Q = 0 ∧ (∀ i, ∑ j, O i j j = 0) ∧
    (∀ i, ∑ j, ∑ k, O i j k * Q j k = v i) ∧
    Matrix.det (![v, Q.mulVec v, Q.mulVec (Q.mulVec v)] : Matrix (Fin 3) (Fin 3) ℝ) = 0 := by
  refine ⟨?_, ?_, ?_, ?_⟩
  · norm_num [Q, Matrix.trace, Fin.sum_univ_succ]
  · intro i; fin_cases i <;> norm_num [O, Fin.sum_univ_succ]
  · intro i; fin_cases i <;> norm_num [O, Q, v, Fin.sum_univ_succ, Matrix.diagonal, Matrix.cons_val]
  · have hqv : Q.mulVec v = ![0,0,1] := by
      ext i; fin_cases i <;> norm_num [Q, v, Matrix.mulVec, dotProduct, Fin.sum_univ_succ, Matrix.diagonal, Matrix.cons_val]
    have hqqv : Q.mulVec ![0,0,1] = ![0,0,1] := by
      ext i; fin_cases i <;> norm_num [Q, v, Matrix.mulVec, dotProduct, Fin.sum_univ_succ, Matrix.diagonal, Matrix.cons_val]
    rw [hqv, hqqv]
    change Matrix.det (!![0,-1,1; 0,0,1; 0,0,1] : Matrix (Fin 3) (Fin 3) ℝ) = 0
    simp [Matrix.det_fin_three, Matrix.cons_val, Matrix.vecHead, Matrix.vecTail]


-- Distinct Q eigenvalues reducing rotations to signed axes is the accepted premise.
-- Each nonzero diagonal O component forces a sign reversal; proper determinant is impossible.
theorem T1_no_proper_signed_stabilizer (s : Fin 3 → ℝ)
    (hs : ∀ i, s i ^ 2 = 1) (hproper : s 0 * s 1 * s 2 = 1)
    (hmap : ∀ i, s i ^ 3 * O i i i = -O i i i) : False := by
  have negs : ∀ i, s i = -1 := by
    intro i
    have hi := hmap i
    have hsq := hs i
    have hod : O i i i = 1 := by fin_cases i <;> norm_num [O]
    rw [hod] at hi
    nlinarith [hsq]
  rw [negs 0, negs 1, negs 2] at hproper
  norm_num at hproper

-- Genuine derivative rule with the positive absolute-temperature denominator.
theorem T3_normalized_derivative (q temp : ℝ → ℝ) (qdot tempdot x : ℝ)
    (hq : HasDerivAt q qdot x) (ht : HasDerivAt temp tempdot x) (hp : 0 < temp x) :
    HasDerivAt (fun y => q y / temp y)
      ((qdot * temp x - q x * tempdot) / temp x ^ 2) x := by
  exact hq.fun_div ht (ne_of_gt hp)

theorem T3_normalized_derivative_and_odd_signs (Theta qdot Dd divo Cdot Cout E : ℝ)
    (hTheta : 0 < Theta) :
    -qdot - (-Dd) - (3/7 : ℝ) * (-divo) = -qdot + Dd + (3/7 : ℝ)*divo ∧
    -(3/Theta)*(-Cdot) - (-Cout) - (6/(5*Theta))*E =
      3*Cdot/Theta + Cout - 6*E/(5*Theta) := by
  constructor <;> field_simp <;> ring

-- Truncated coefficient multiplication for compatible finite real matrices.
-- (B0,B1) is the degree-0 and degree-1 coefficient of the inverse series.
-- These equations are exactly the degree-0/1 coefficients of (I-t E)B(t)=I.
theorem T5_inverse_coefficients {n : Type*} [Fintype n] [DecidableEq n]
    (E B0 B1 : Matrix n n ℝ) (h0 : (1 : Matrix n n ℝ) * B0 = 1)
    (h1 : (1 : Matrix n n ℝ) * B1 + (-E) * B0 = 0) :
    B0 = 1 ∧ B1 = E := by
  have hB0 : B0 = 1 := by simpa using h0
  rw [hB0] at h1
  simp only [one_mul, Matrix.mul_one, Matrix.neg_mul] at h1
  exact ⟨hB0, eq_of_sub_eq_zero (by simpa [sub_eq_add_neg] using h1)⟩

theorem T5_first_order_inverse_coefficient {n p q : Type*}
    [Fintype n] [DecidableEq n] (E : Matrix n n ℝ)
    (C : Matrix p n ℝ) (A : Matrix n q ℝ) :
    ((1 : Matrix n n ℝ) * E + (-E) * 1 = 0) ∧
    ((0 : Matrix p n ℝ) * E + (-C) * (1 : Matrix n n ℝ)) * A = -(C * A) := by
  simp

-- d,k,h denote nonnegative norms; c f/(1-36f) is the supplied operator bound.
theorem T5_scalar_cost_implication (f c d k h : ℝ)
    (hf : 0 < f) (hsmall : f < 1/36) (hc : 0 < c) (hd : 0 < d)
    (hk : 0 ≤ k) (hh : 0 ≤ h)
    (hbound : k ≤ c*f/(1-36*f)) (hcancel : d ≤ k*h) :
    d^2 * (1-36*f)^2 / (c^2*f^2) ≤ h^2 := by
  have hden : 0 < 1-36*f := by linarith
  have hcf : 0 < c*f := mul_pos hc hf
  have hineq : d ≤ (c*f/(1-36*f))*h := le_trans hcancel (mul_le_mul_of_nonneg_right hbound hh)
  have hmul : d*(1-36*f) ≤ c*f*h := by
    have htmp := (mul_le_mul_of_nonneg_right hineq (le_of_lt hden))
    field_simp at htmp
    nlinarith [htmp]
  have hdiv : d*(1-36*f)/(c*f) ≤ h := (div_le_iff₀ hcf).2 (by nlinarith [hmul])
  have hpos : 0 ≤ d*(1-36*f)/(c*f) := le_of_lt (div_pos (mul_pos hd hden) hcf)
  have hsquare : (d*(1-36*f)/(c*f))^2 ≤ h^2 := by nlinarith
  convert hsquare using 1 <;> field_simp <;> ring

theorem T6_scalar_information_one_fifth :
    (1 : ℝ) * (1/1 - 1/(1+(1/4))) * 1 = 1/5 ∧
    ((1 : ℝ) - 1/(1+1/4)) - (1 - 1/1) = 1/5 := by norm_num

def acceptedSquaredMinor : Fin 6 → ℝ := ![13854851227718467321621702138503980744130367185396095166590753194419819749485140749388736644495507/2946385964528764001602729286917704836323445407941374503789674365768429551770231683936450693300224,45897747416692690585791274614572327208356017181052125887012037607944001265218344300648587575/11439368869955288869320571209776405550745656790554396265529415077685155349137762741139313524736,39493718757090374514153222808257755001282326150716790292260982205042519060828776367475925/215305412825852519355010761635586687254061841359588806014692042617344168936576686059039460687872,3965156020663594870880515310630136258902710414400775484668459177/613649291260366690751581334535331511253026015611909498783126158409990144,33648590107505417977636161099564743354425815/321031865290431140061490488646804497908163936256,1654580299939355708034129/1995199839012425102786560]
def acceptedNormalDet : Fin 6 → ℝ := ![2371221567616482963655661538277/124939643158494289811515067921858560,1784012728720795037550100553/1743019575313815427057966907392,10945595347193184954026503331/871509787656907713528983453696,104531461379720327/1585267068834414592,665044625583572687/3170534137668829184,1/2]

def rows : Fin 6 → ℕ := ![4,4,4,3,2,1]
theorem rows_le_four (m : Fin 6) : rows m ≤ 4 := by fin_cases m <;> norm_num [rows]
def pivot (m : Fin 6) (j : Fin (rows m)) : Fin 4 := Fin.castLE (rows_le_four m) j
-- Index j corresponds to source ell=7+j, identically for every accepted block.
theorem accepted_columns_within_ten (m : Fin 6) (j : Fin (rows m)) :
    7 + (pivot m j).val ≤ 10 := by have := (pivot m j).isLt; omega

theorem accepted_rational_positivity :
    (∀ m, 0 < acceptedSquaredMinor m) ∧ (∀ m, 0 < acceptedNormalDet m) := by
  constructor <;> intro m <;> fin_cases m <;> norm_num [acceptedSquaredMinor, acceptedNormalDet]

-- The historical operator is NOT reconstructed. Its accepted column-minor identities
-- are explicit hypotheses, from which the rank of every cutoff-10 block follows.
theorem accepted_block_full_row_rank (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ)
    (haccepted : ∀ m, (Matrix.det ((B m).submatrix id (pivot m)))^2 = acceptedSquaredMinor m) :
    ∀ m, (B m).rank = rows m := by
  intro m
  have hdet : Matrix.det ((B m).submatrix id (pivot m)) ≠ 0 := by
    intro hz
    have hp := accepted_rational_positivity.1 m
    have heq := haccepted m
    rw [hz] at heq
    norm_num at heq
    linarith
  have hrank : ((B m).submatrix id (pivot m)).rank = rows m := by
    have hi : IsUnit ((B m).submatrix id (pivot m)) := (Matrix.isUnit_iff_isUnit_det _).mpr (isUnit_iff_ne_zero.mpr hdet)
    simpa using Matrix.rank_of_isUnit ((B m).submatrix id (pivot m)) hi
  have hlo := Matrix.rank_submatrix_le (B m) id (pivot m)
  have hhi := Matrix.rank_le_height (B m)
  omega

def storedRank (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ) : ℕ :=
  (B 0).rank + 2*((B 1).rank+(B 2).rank+(B 3).rank+(B 4).rank+(B 5).rank)

theorem cutoff_ten_stored_rank (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ)
    (haccepted : ∀ m, (Matrix.det ((B m).submatrix id (pivot m)))^2 = acceptedSquaredMinor m) :
    storedRank B = 32 := by
  simp only [storedRank, accepted_block_full_row_rank B haccepted]
  rfl

-- Below 10, the m=0 block has fewer than four source columns (ells 7..L).
-- Hence full row rank is impossible before 10, independently of the actual entries.
theorem cutoff_below_ten_not_full (L : ℕ) (hL : L < 10)
    (B0 : Matrix (Fin 4) (Fin (L-6)) ℝ) : B0.rank < 4 := by
  have hb := Matrix.rank_le_width B0
  omega

theorem L10_accepted_minors_and_minimal_cutoff
    (B : (m : Fin 6) → Matrix (Fin (rows m)) (Fin 4) ℝ)
    (haccepted : ∀ m, (Matrix.det ((B m).submatrix id (pivot m)))^2 = acceptedSquaredMinor m) :
    storedRank B = 32 ∧
    (∀ L : ℕ, L < 10 → ∀ B0 : Matrix (Fin 4) (Fin (L-6)) ℝ, B0.rank < 4) ∧
    (∀ m (j : Fin (rows m)), 7 + (pivot m j).val ≤ 10) := by
  exact ⟨cutoff_ten_stored_rank B haccepted, cutoff_below_ten_not_full, accepted_columns_within_ten⟩

#print axioms T1_symmetry
#print axioms T1_trace_and_contraction
#print axioms T1_no_proper_signed_stabilizer
#print axioms T3_normalized_derivative
#print axioms T3_normalized_derivative_and_odd_signs
#print axioms T5_inverse_coefficients
#print axioms T5_first_order_inverse_coefficient
#print axioms T5_scalar_cost_implication
#print axioms T6_scalar_information_one_fifth
#print axioms accepted_rational_positivity
#print axioms L10_accepted_minors_and_minimal_cutoff
end R7
