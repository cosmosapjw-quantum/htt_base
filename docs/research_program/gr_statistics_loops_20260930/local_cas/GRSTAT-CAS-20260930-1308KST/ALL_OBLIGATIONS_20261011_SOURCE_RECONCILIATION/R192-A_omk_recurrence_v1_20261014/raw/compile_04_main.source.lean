/-
R192-A: OMK all-order invariant-graph recurrence, resonance set and compatibility.

Registered reduced system (docs/research_program/long_horizon_rescue/pr131_spec.yaml 81-84;
htt/src/common/omk_near_flrw_expansion.py 72-82):
  q         = (1+3w)(1-K)/2 + (3/2)(1-w) Sigma^2
  dSigma/dN = -K - (Sigma/2)[(1+3w)K + 3(1-w)(1-Sigma^2)]
  dK/dN     = 2K(q + Sigma)
Invariant graph Sigma = h(K) = sum_{n>=1} c_n K^n, residual h' F_K(h,K) - F_Sigma(h,K)
(omk_near_flrw_expansion.py line 113). Formal power series only: no convergence claim.
-/
import Mathlib

open PowerSeries
open Finset (antidiagonal mem_antidiagonal sum_congr)

namespace R192A

noncomputable section

variable {F : Type*} [Field F]

open scoped Classical

section VectorField
variable {A : Type*} [CommRing A] [Algebra F A]

/-- deceleration parameter `q` of the registered OMK system -/
def qOMK (w : F) (S K : A) : A :=
  algebraMap F A ((1 + 3 * w) / 2) * (1 - K) + algebraMap F A (3 / 2 * (1 - w)) * S ^ 2

/-- `dSigma/dN` -/
def fSigma (w : F) (S K : A) : A :=
  -K - algebraMap F A (1 / 2) * S *
    (algebraMap F A (1 + 3 * w) * K + algebraMap F A (3 * (1 - w)) * (1 - S ^ 2))

/-- `dK/dN` -/
def fK (w : F) (S K : A) : A := 2 * K * (qOMK w S K + S)

end VectorField

/-- invariance residual of the graph `Sigma = h(K)` -/
def invRes (w : F) (h : F⟦X⟧) : F⟦X⟧ :=
  d⁄dX F h * fK w h X - fSigma w h X

/-- `lambda_K` -/
def gOMK (w : F) : F := 1 + 3 * w
/-- `-lambda_Sigma` -/
def aOMK (w : F) : F := 3 / 2 * (1 - w)
/-- recurrence denominator `n lambda_K - lambda_Sigma` -/
def denom (w : F) (n : ℕ) : F := (n : F) * gOMK w + aOMK w

def quadE (c : ℕ → F) (n : ℕ) : F := ∑ p ∈ antidiagonal n, (p.1 : F) * c p.1 * c p.2
def cubE (c : ℕ → F) (n : ℕ) : F :=
  ∑ p ∈ antidiagonal n, (p.1 : F) * c p.1 * ∑ q ∈ antidiagonal p.2, c q.1 * c q.2
def cub (c : ℕ → F) (n : ℕ) : F :=
  ∑ p ∈ antidiagonal n, c p.1 * ∑ q ∈ antidiagonal p.2, c q.1 * c q.2

def rhsR (w : F) (c : ℕ → F) (n : ℕ) : F :=
  (if n = 1 then -1 else 0) + (((n - 1 : ℕ) : F) * gOMK w - gOMK w / 2) * c (n - 1)
    - 2 * quadE c n - 2 * aOMK w * cubE c n + aOMK w * cub c n

/-- the general solution sequence: free value `t n` at resonant orders -/
def seqWith (w : F) (t : ℕ → F) : ℕ → F
  | 0 => 0
  | n + 1 => if denom w (n + 1) = 0 then t (n + 1) else
      rhsR w (fun k => if k < n + 1 then seqWith w t k else 0) (n + 1) / denom w (n + 1)

/-! ### coefficient comparison -/

lemma coeff_X_mul_derivative (h : F⟦X⟧) (n : ℕ) :
    coeff n (X * d⁄dX F h) = (n : F) * coeff n h := by
  cases n with
  | zero => simp
  | succ n => rw [coeff_succ_X_mul, coeff_derivative]; push_cast; ring

lemma coeff_hh (c : ℕ → F) (n : ℕ) :
    coeff n (PowerSeries.mk c * PowerSeries.mk c) = ∑ q ∈ antidiagonal n, c q.1 * c q.2 := by
  simp [coeff_mul]

lemma coeff_XD_h (c : ℕ → F) (n : ℕ) :
    coeff n ((X * d⁄dX F (PowerSeries.mk c)) * PowerSeries.mk c) = quadE c n := by
  rw [coeff_mul]; unfold quadE
  refine sum_congr rfl fun p _ => ?_
  rw [coeff_X_mul_derivative, coeff_mk, coeff_mk]

lemma coeff_XD_hh (c : ℕ → F) (n : ℕ) :
    coeff n ((X * d⁄dX F (PowerSeries.mk c)) * (PowerSeries.mk c * PowerSeries.mk c)) = cubE c n := by
  rw [coeff_mul]; unfold cubE
  refine sum_congr rfl fun p _ => ?_
  rw [coeff_X_mul_derivative, coeff_mk, coeff_hh]

lemma coeff_hhh (c : ℕ → F) (n : ℕ) :
    coeff n (PowerSeries.mk c * (PowerSeries.mk c * PowerSeries.mk c)) = cub c n := by
  rw [coeff_mul]; unfold cub
  refine sum_congr rfl fun p _ => ?_
  rw [coeff_mk, coeff_hh]

/-- literal expansion of the residual (pure commutative-ring identity, any field) -/
lemma invRes_eq (w : F) (h : F⟦X⟧) :
    invRes w h =
      C 2 * (C ((1 + 3 * w) / 2) * (X * d⁄dX F h))
      - C 2 * (C ((1 + 3 * w) / 2) * (X * (X * d⁄dX F h)))
      + C 2 * (C (3 / 2 * (1 - w)) * ((X * d⁄dX F h) * (h * h)))
      + C 2 * ((X * d⁄dX F h) * h) + X
      + C (1 / 2) * (C (1 + 3 * w) * (X * h))
      + C (1 / 2) * (C (3 * (1 - w)) * h)
      - C (1 / 2) * (C (3 * (1 - w)) * (h * (h * h))) := by
  unfold invRes fK qOMK fSigma
  simp only [algebraMap_eq]
  rw [show (2 : F⟦X⟧) = C 2 from (map_ofNat C 2).symm]
  ring

/-- characteristic-free coefficient formula -/
lemma coeff_invRes_succ_raw (w : F) (c : ℕ → F) (n : ℕ) :
    coeff (n + 1) (invRes w (PowerSeries.mk c)) =
      2 * ((1 + 3 * w) / 2 * (((n + 1 : ℕ) : F) * c (n + 1)))
      - 2 * ((1 + 3 * w) / 2 * ((n : F) * c n))
      + 2 * (3 / 2 * (1 - w) * cubE c (n + 1))
      + 2 * quadE c (n + 1) + (if n + 1 = 1 then 1 else 0)
      + 1 / 2 * ((1 + 3 * w) * c n)
      + 1 / 2 * (3 * (1 - w) * c (n + 1))
      - 1 / 2 * (3 * (1 - w) * cub c (n + 1)) := by
  rw [invRes_eq]
  simp only [LinearMap.map_add, LinearMap.map_sub, coeff_C_mul, coeff_XD_h, coeff_XD_hh,
    coeff_hhh, coeff_X, coeff_succ_X_mul, coeff_X_mul_derivative, coeff_derivative, coeff_mk]
  push_cast
  ring

/-- T1 -/
theorem coeff_invRes_zero (w : F) (c : ℕ → F) (hc0 : c 0 = 0) :
    coeff 0 (invRes w (PowerSeries.mk c)) = 0 := by
  rw [invRes_eq]
  simp only [LinearMap.map_add, LinearMap.map_sub, coeff_C_mul, coeff_XD_h, coeff_XD_hh,
    coeff_hhh, coeff_X, coeff_zero_X_mul, coeff_mk]
  simp [quadE, cubE, cub, hc0]

/-- T2: coefficient comparison at every order `n + 1` -/
theorem coeff_invRes_succ [CharZero F] (w : F) (c : ℕ → F) (n : ℕ) :
    coeff (n + 1) (invRes w (PowerSeries.mk c)) = denom w (n + 1) * c (n + 1) - rhsR w c (n + 1) := by
  rw [coeff_invRes_succ_raw]
  unfold denom rhsR gOMK aOMK
  rw [Nat.add_sub_cancel]
  split_ifs <;> push_cast <;> ring

/-- T3 -/
theorem invariant_iff_recurrence [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0) :
    invRes w (PowerSeries.mk c) = 0 ↔ ∀ n, 1 ≤ n → denom w n * c n = rhsR w c n := by
  constructor
  · intro h n hn
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    have := congrArg (coeff (m + 1)) h
    rw [coeff_invRes_succ, map_zero] at this
    exact sub_eq_zero.mp this
  · intro h
    ext n
    rw [map_zero]
    cases n with
    | zero => exact coeff_invRes_zero w c hc0
    | succ m => rw [coeff_invRes_succ, h (m + 1) (by omega), sub_self]

/-! ### triangularity -/

lemma agree_two {c c' : ℕ → F} {n : ℕ} (hc0 : c 0 = 0) (hc0' : c' 0 = 0)
    (hag : ∀ k, k < n → c k = c' k) {i j : ℕ} (hij : i + j = n) :
    c i * c j = c' i * c' j := by
  rcases Nat.eq_zero_or_pos i with rfl | hi
  · simp [hc0, hc0']
  rcases Nat.eq_zero_or_pos j with rfl | hj
  · simp [hc0, hc0']
  rw [hag i (by omega), hag j (by omega)]

lemma agree_three {c c' : ℕ → F} {n : ℕ} (hc0 : c 0 = 0) (hc0' : c' 0 = 0)
    (hag : ∀ k, k < n → c k = c' k) {i j : ℕ} (hij : i + j = n) :
    c i * ∑ q ∈ antidiagonal j, c q.1 * c q.2 =
      c' i * ∑ q ∈ antidiagonal j, c' q.1 * c' q.2 := by
  rcases Nat.eq_zero_or_pos i with rfl | hi
  · simp [hc0, hc0']
  rcases Nat.eq_zero_or_pos j with rfl | hj
  · simp [hc0, hc0']
  rw [hag i (by omega)]
  congr 1
  refine sum_congr rfl fun q hq => ?_
  have := mem_antidiagonal.mp hq
  rw [hag q.1 (by omega), hag q.2 (by omega)]

/-- T4: `rhsR w c n` depends only on `c 0, ..., c (n-1)` -/
theorem rhsR_lower_order (w : F) (c c' : ℕ → F) (n : ℕ) (hn : 1 ≤ n) (hc0 : c 0 = 0)
    (hagree : ∀ k, k < n → c k = c' k) : rhsR w c n = rhsR w c' n := by
  have hc0' : c' 0 = 0 := by rw [← hagree 0 (by omega), hc0]
  have hq : quadE c n = quadE c' n := by
    unfold quadE
    refine sum_congr rfl fun p hp => ?_
    rw [mul_assoc, mul_assoc, agree_two hc0 hc0' hagree (mem_antidiagonal.mp hp)]
  have hce : cubE c n = cubE c' n := by
    unfold cubE
    refine sum_congr rfl fun p hp => ?_
    rw [mul_assoc, mul_assoc, agree_three hc0 hc0' hagree (mem_antidiagonal.mp hp)]
  have hcu : cub c n = cub c' n := by
    unfold cub
    exact sum_congr rfl fun p hp => agree_three hc0 hc0' hagree (mem_antidiagonal.mp hp)
  unfold rhsR
  rw [hq, hce, hcu, hagree (n - 1) (by omega)]

/-! ### the general solution sequence -/

lemma seqWith_zero (w : F) (t : ℕ → F) : seqWith w t 0 = 0 := by
  rw [seqWith]

lemma seqWith_succ (w : F) (t : ℕ → F) (n : ℕ) :
    seqWith w t (n + 1) = if denom w (n + 1) = 0 then t (n + 1) else
      rhsR w (fun k => if k < n + 1 then seqWith w t k else 0) (n + 1) / denom w (n + 1) := by
  rw [seqWith]

lemma rhsR_trunc (w : F) (t : ℕ → F) (n : ℕ) :
    rhsR w (fun k => if k < n + 1 then seqWith w t k else 0) (n + 1) =
      rhsR w (seqWith w t) (n + 1) :=
  (rhsR_lower_order w (seqWith w t) _ (n + 1) (by omega) (seqWith_zero w t)
    (fun k hk => by simp [hk])).symm

/-- T6b: at a resonant order the coefficient is free -/
theorem seqWith_resonant (w : F) (t : ℕ → F) (n : ℕ) (hn : 1 ≤ n) (hres : denom w n = 0) :
    seqWith w t n = t n := by
  obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
  rw [seqWith_succ, if_pos hres]

lemma seqWith_rec (w : F) (t : ℕ → F) (n : ℕ) (hn : 1 ≤ n) (hd : denom w n ≠ 0) :
    denom w n * seqWith w t n = rhsR w (seqWith w t) n := by
  obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
  rw [seqWith_succ, if_neg hd, rhsR_trunc, mul_div_cancel₀ _ hd]

/-- T6: compatibility conditions are necessary and sufficient -/
theorem seqWith_invariant_iff [CharZero F] (w : F) (t : ℕ → F) :
    invRes w (PowerSeries.mk (seqWith w t)) = 0 ↔
      ∀ n, 1 ≤ n → denom w n = 0 → rhsR w (seqWith w t) n = 0 := by
  rw [invariant_iff_recurrence w _ (seqWith_zero w t)]
  constructor
  · intro h n hn hd
    rw [← h n hn, hd, zero_mul]
  · intro h n hn
    by_cases hd : denom w n = 0
    · rw [h n hn hd, hd, zero_mul]
    · exact seqWith_rec w t n hn hd

/-- T5: characterization of every zero-constant formal invariant graph -/
theorem solution_iff [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0) :
    invRes w (PowerSeries.mk c) = 0 ↔
      (c = seqWith w c ∧ ∀ n, 1 ≤ n → denom w n = 0 → rhsR w c n = 0) := by
  constructor
  · intro h
    have hrec := (invariant_iff_recurrence w c hc0).mp h
    refine ⟨?_, fun n hn hd => by rw [← hrec n hn, hd, zero_mul]⟩
    funext n
    induction n using Nat.strong_induction_on with
    | _ n ih =>
      cases n with
      | zero => rw [hc0, seqWith_zero]
      | succ m =>
        rw [seqWith_succ]
        split_ifs with hd
        · rfl
        · rw [eq_div_iff hd]
          have hl : rhsR w (fun k => if k < m + 1 then seqWith w c k else 0) (m + 1) =
              rhsR w c (m + 1) :=
            (rhsR_lower_order w c _ (m + 1) (by omega) hc0
              (fun k hk => by simp [hk, ih k hk])).symm
          rw [hl, ← hrec (m + 1) (by omega), mul_comm]
  · rintro ⟨hfix, hcompat⟩
    rw [hfix]
    refine (seqWith_invariant_iff w c).mpr fun n hn hd => ?_
    rw [← hfix]
    exact hcompat n hn hd

lemma eq_of_recurrence [CharZero F] (w : F) (hnr : ∀ n, 1 ≤ n → denom w n ≠ 0)
    (c c' : ℕ → F) (hc0 : c 0 = 0) (hc0' : c' 0 = 0)
    (rc : ∀ n, 1 ≤ n → denom w n * c n = rhsR w c n)
    (rc' : ∀ n, 1 ≤ n → denom w n * c' n = rhsR w c' n) : c = c' := by
  funext n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    cases n with
    | zero => rw [hc0, hc0']
    | succ m =>
      apply mul_left_cancel₀ (hnr (m + 1) (by omega))
      rw [rc (m + 1) (by omega), rc' (m + 1) (by omega)]
      exact rhsR_lower_order w c c' (m + 1) (by omega) hc0 ih

/-- T7: unique formal invariant graph when no order is resonant -/
theorem exists_unique_of_nonresonant [CharZero F] (w : F)
    (hnr : ∀ n, 1 ≤ n → denom w n ≠ 0) :
    ∃! c : ℕ → F, c 0 = 0 ∧ invRes w (PowerSeries.mk c) = 0 := by
  have hs : invRes w (PowerSeries.mk (seqWith w 0)) = 0 :=
    (seqWith_invariant_iff w 0).mpr fun n hn hd => absurd hd (hnr n hn)
  refine ⟨seqWith w 0, ⟨seqWith_zero w 0, hs⟩, ?_⟩
  rintro c ⟨hc0, hinv⟩
  exact eq_of_recurrence w hnr c _ hc0 (seqWith_zero w 0)
    ((invariant_iff_recurrence w c hc0).mp hinv)
    ((invariant_iff_recurrence w _ (seqWith_zero w 0)).mp hs)

/-! ### resonance set -/

/-- T8 -/
theorem two_mul_denom [CharZero F] (w : F) (n : ℕ) :
    2 * denom w n = (6 * (n : F) - 3) * w + (2 * (n : F) + 3) := by
  unfold denom gOMK aOMK; ring

/-- T8b: the zero set of every denominator -/
theorem denom_eq_zero_iff [CharZero F] (w : F) (n : ℕ) (hn : 1 ≤ n) :
    denom w n = 0 ↔ w = -(2 * (n : F) + 3) / (6 * (n : F) - 3) := by
  have h63 : (6 * (n : F) - 3) ≠ 0 := by
    intro h
    have h' : ((6 * n : ℕ) : F) = ((3 : ℕ) : F) := by push_cast; linear_combination h
    have := Nat.cast_injective h'
    omega
  have h2 := two_mul_denom w n
  rw [eq_div_iff h63]
  constructor
  · intro hd
    rw [hd] at h2
    linear_combination -h2
  · intro hw
    linear_combination (1 / 2 : F) * h2 + (1 / 2 : F) * hw

/-- T8c -/
theorem denom_one [CharZero F] (w : F) : denom w 1 = (3 * w + 5) / 2 := by
  unfold denom gOMK aOMK; push_cast; ring
theorem denom_two [CharZero F] (w : F) : denom w 2 = (9 * w + 7) / 2 := by
  unfold denom gOMK aOMK; push_cast; ring
theorem denom_three [CharZero F] (w : F) : denom w 3 = 3 * (5 * w + 3) / 2 := by
  unfold denom gOMK aOMK; push_cast; ring

/-- T8d: the marginal entries are not denominator zeros -/
theorem denom_ne_zero_marginal [CharZero F] (n : ℕ) (hn : 1 ≤ n) :
    denom (-1 / 3 : F) n ≠ 0 ∧ denom (1 : F) n ≠ 0 := by
  have hn0 : (n : F) ≠ 0 := Nat.cast_ne_zero.mpr (by omega)
  constructor
  · unfold denom gOMK aOMK; norm_num
  · unfold denom gOMK aOMK; norm_num; omega

/-- T9 -/
theorem denom_pos_on_domain (w : ℝ) (hlo : -1 / 3 < w) (hhi : w < 1) (n : ℕ) (hn : 1 ≤ n) :
    0 < denom w n := by
  have : (1 : ℝ) ≤ n := by exact_mod_cast hn
  unfold denom gOMK aOMK
  nlinarith

/-- T9b: every resonance lies in `[-5/3, -1/3)` -/
theorem resonance_mem_Ico (n : ℕ) (hn : 1 ≤ n) :
    -5 / 3 ≤ -(2 * (n : ℝ) + 3) / (6 * n - 3) ∧ -(2 * (n : ℝ) + 3) / (6 * n - 3) < -1 / 3 := by
  have h1 : (1 : ℝ) ≤ n := by exact_mod_cast hn
  have hpos : (0 : ℝ) < 6 * n - 3 := by linarith
  constructor
  · rw [le_div_iff₀ hpos]; linarith
  · rw [div_lt_iff₀ hpos]; linarith

/-- T9c -/
theorem exists_unique_on_domain (w : ℝ) (hlo : -1 / 3 < w) (hhi : w < 1) :
    ∃! c : ℕ → ℝ, c 0 = 0 ∧ invRes w (PowerSeries.mk c) = 0 :=
  exists_unique_of_nonresonant w fun n hn => (denom_pos_on_domain w hlo hhi n hn).ne'

/-! ### existing finite coefficients as instances -/

/-- T10a -/
theorem rhsR_one [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0) : rhsR w c 1 = -1 := by
  simp [rhsR, quadE, cubE, cub, Finset.Nat.sum_antidiagonal_eq_sum_range_succ_mk,
    Finset.sum_range_succ, hc0]

theorem rhsR_two [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0) :
    rhsR w c 2 = c 1 * (gOMK w / 2 - 2 * c 1) := by
  simp [rhsR, quadE, cubE, cub, Finset.Nat.sum_antidiagonal_eq_sum_range_succ_mk,
    Finset.sum_range_succ, hc0]
  ring

theorem rhsR_three [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0) :
    rhsR w c 3 = 3 * gOMK w / 2 * c 2 - 6 * c 1 * c 2 - aOMK w * c 1 ^ 3 := by
  simp [rhsR, quadE, cubE, cub, Finset.Nat.sum_antidiagonal_eq_sum_range_succ_mk,
    Finset.sum_range_succ, hc0]
  ring

/-- T10b -/
theorem coeff_one_of_invariant [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0)
    (hinv : invRes w (PowerSeries.mk c) = 0) (h1 : 3 * w + 5 ≠ 0) : c 1 = -2 / (3 * w + 5) := by
  have r := (invariant_iff_recurrence w c hc0).mp hinv 1 le_rfl
  rw [rhsR_one w c hc0, denom_one] at r
  rw [eq_div_iff h1]
  linear_combination 2 * r

/-- T10d (pr131 spec form, `s = -a`) -/
theorem coeff_two_spec_form [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0)
    (hinv : invRes w (PowerSeries.mk c) = 0) (h1 : 3 * w + 5 ≠ 0) (h2 : 9 * w + 7 ≠ 0) :
    c 2 = c 1 * (gOMK w / 2 - 2 * c 1) / (2 * gOMK w + aOMK w) := by
  have r := (invariant_iff_recurrence w c hc0).mp hinv 2 (by norm_num)
  rw [rhsR_two w c hc0] at r
  have hd : 2 * gOMK w + aOMK w = denom w 2 := by unfold denom; push_cast; ring
  have hne : denom w 2 ≠ 0 := by
    rw [denom_two]; intro h; apply h2; linear_combination 2 * h
  rw [hd, eq_div_iff hne, mul_comm]
  exact r

/-- T10c -/
theorem coeff_two_of_invariant [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0)
    (hinv : invRes w (PowerSeries.mk c) = 0) (h1 : 3 * w + 5 ≠ 0) (h2 : 9 * w + 7 ≠ 0) :
    c 2 = -2 * (9 * w ^ 2 + 18 * w + 13) / ((3 * w + 5) ^ 2 * (9 * w + 7)) := by
  rw [coeff_two_spec_form w c hc0 hinv h1 h2, coeff_one_of_invariant w c hc0 hinv h1]
  unfold gOMK aOMK
  have h3 : (2 * (1 + 3 * w) + 3 / 2 * (1 - w)) ≠ 0 := by
    intro h; apply h2; linear_combination 2 * h
  field_simp
  ring

/-- T10e -/
theorem coeff_three_of_invariant [CharZero F] (w : F) (c : ℕ → F) (hc0 : c 0 = 0)
    (hinv : invRes w (PowerSeries.mk c) = 0) (h1 : 3 * w + 5 ≠ 0) (h2 : 9 * w + 7 ≠ 0)
    (h3 : 5 * w + 3 ≠ 0) :
    c 3 = -2 * (81 * w ^ 4 + 324 * w ^ 3 + 594 * w ^ 2 + 460 * w + 141) /
      ((3 * w + 5) ^ 3 * (5 * w + 3) * (9 * w + 7)) := by
  have r := (invariant_iff_recurrence w c hc0).mp hinv 3 (by norm_num)
  rw [rhsR_three w c hc0, denom_three] at r
  have hne : 3 * (5 * w + 3) / 2 ≠ 0 := by
    intro h; apply h3; linear_combination (2 / 3 : F) * h
  have e1 := coeff_one_of_invariant w c hc0 hinv h1
  have e2 := coeff_two_of_invariant w c hc0 hinv h1 h2
  rw [eq_div_iff h1] at e1
  rw [eq_div_iff (mul_ne_zero (pow_ne_zero 2 h1) h2)] at e2
  rw [eq_div_iff (mul_ne_zero (mul_ne_zero (pow_ne_zero 3 h1) h3) h2)]
  unfold gOMK aOMK at r
  linear_combination (2 / 3 * (3 * w + 5) ^ 3 * (9 * w + 7)) * r
    + ((1 + 3 * w) * (3 * w + 5) - 4 * (3 * w + 5) * c 1) * e2
    + (8 * (9 * w ^ 2 + 18 * w + 13) - 2 / 3 * (3 / 2 * (1 - w)) * (9 * w + 7) *
        ((c 1 * (3 * w + 5)) ^ 2 - 2 * (c 1 * (3 * w + 5)) + 4)) * e1

/-- T10f (dust) -/
theorem dust_values [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0) (hinv : invRes (0 : F) (PowerSeries.mk c) = 0) :
    c 1 = -2 / 5 ∧ c 2 = -26 / 175 ∧ c 3 = -94 / 875 := by
  have h1 : (3 * (0 : F) + 5) ≠ 0 := by norm_num
  have h2 : (9 * (0 : F) + 7) ≠ 0 := by norm_num
  have h3 : (5 * (0 : F) + 3) ≠ 0 := by norm_num
  refine ⟨?_, ?_, ?_⟩
  · rw [coeff_one_of_invariant 0 c hc0 hinv h1]; norm_num
  · rw [coeff_two_of_invariant 0 c hc0 hinv h1 h2]; norm_num
  · rw [coeff_three_of_invariant 0 c hc0 hinv h1 h2 h3]; norm_num

/-- T10f (radiation) -/
theorem radiation_values [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0)
    (hinv : invRes (1 / 3 : F) (PowerSeries.mk c) = 0) :
    c 1 = -1 / 3 ∧ c 2 = -1 / 9 ∧ c 3 = -2 / 27 := by
  have h1 : (3 * (1 / 3 : F) + 5) ≠ 0 := by norm_num
  have h2 : (9 * (1 / 3 : F) + 7) ≠ 0 := by norm_num
  have h3 : (5 * (1 / 3 : F) + 3) ≠ 0 := by norm_num
  refine ⟨?_, ?_, ?_⟩
  · rw [coeff_one_of_invariant _ c hc0 hinv h1]; norm_num
  · rw [coeff_two_of_invariant _ c hc0 hinv h1 h2]; norm_num
  · rw [coeff_three_of_invariant _ c hc0 hinv h1 h2 h3]; norm_num

/-! ### the exact linear graph `Sigma = kappa K` is not invariant when `c2 ≠ 0` -/

/-- T11 -/
theorem linear_graph_not_invariant [CharZero F] (w : F) (h1 : 3 * w + 5 ≠ 0)
    (h2 : 9 * w + 7 ≠ 0) (hq : 9 * w ^ 2 + 18 * w + 13 ≠ 0) (κ : F) :
    invRes w (C κ * X) ≠ 0 := by
  intro hinv
  set c : ℕ → F := fun n => coeff n (C κ * X) with hcdef
  have hmk : PowerSeries.mk c = C κ * X := by ext n; simp [c]
  have hc0 : c 0 = 0 := by simp [c]
  have hc2 : c 2 = 0 := by simp [c, coeff_X]
  rw [← hmk] at hinv
  have e1 := coeff_one_of_invariant w c hc0 hinv h1
  have r2 := (invariant_iff_recurrence w c hc0).mp hinv 2 (by norm_num)
  rw [rhsR_two w c hc0, hc2, mul_zero, e1] at r2
  have key : -2 / (3 * w + 5) * (gOMK w / 2 - 2 * (-2 / (3 * w + 5))) =
      -(9 * w ^ 2 + 18 * w + 13) / (3 * w + 5) ^ 2 := by
    unfold gOMK; field_simp; ring
  rw [key, eq_comm, div_eq_zero_iff, neg_eq_zero] at r2
  rcases r2 with h | h
  · exact hq h
  · exact h1 (pow_eq_zero_iff (by norm_num) |>.mp h)

/-- T11b -/
theorem linear_graph_not_invariant_on_domain (w : ℝ) (hlo : -1 / 3 < w) (hhi : w < 1) (κ : ℝ) :
    invRes w (C κ * X) ≠ 0 :=
  linear_graph_not_invariant w (by linarith) (by linarith)
    (by nlinarith [sq_nonneg (w + 1)]) κ

/-- T12: real-point tangency defect of the line `Sigma = kappa K` -/
theorem linear_line_defect [CharZero F] (w K : F) (h1 : 3 * w + 5 ≠ 0) :
    fSigma w (-2 / (3 * w + 5) * K) K - (-2 / (3 * w + 5)) * fK w (-2 / (3 * w + 5) * K) K =
      (-2 / (3 * w + 5)) * ((1 + 3 * w) / 2 - 2 * (-2 / (3 * w + 5))) * K ^ 2
        - 3 / 2 * (1 - w) * (-2 / (3 * w + 5)) ^ 3 * K ^ 3 := by
  unfold fSigma fK qOMK
  simp only [Algebra.algebraMap_self, RingHom.id_apply]
  field_simp
  ring

/-- T12b: recorded counterexample at dust, `K = 1/10` -/
theorem dust_line_counterexample :
    fSigma (A := ℚ) (0 : ℚ) (-2 / 5 * (1 / 10)) (1 / 10)
      - (-2 / 5) * fK (A := ℚ) (0 : ℚ) (-2 / 5 * (1 / 10)) (1 / 10)
      = -319 / 62500 := by
  unfold fSigma fK qOMK
  simp only [Algebra.algebraMap_self, RingHom.id_apply]
  norm_num

/-! ### negative controls and non-vacuity -/

/-- N1 -/
theorem no_solution_order_one_resonance [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0) :
    invRes (-5 / 3 : F) (PowerSeries.mk c) ≠ 0 := by
  intro hinv
  have r := (invariant_iff_recurrence _ c hc0).mp hinv 1 le_rfl
  rw [rhsR_one _ c hc0, denom_one] at r
  norm_num at r

/-- N2 -/
theorem no_solution_order_two_resonance [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0) :
    invRes (-7 / 9 : F) (PowerSeries.mk c) ≠ 0 := by
  intro hinv
  have e1 := coeff_one_of_invariant _ c hc0 hinv (by norm_num)
  have r := (invariant_iff_recurrence _ c hc0).mp hinv 2 (by norm_num)
  rw [rhsR_two _ c hc0, denom_two, e1] at r
  unfold gOMK at r
  norm_num at r

/-- N3 -/
theorem no_solution_order_three_resonance [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0) :
    invRes (-3 / 5 : F) (PowerSeries.mk c) ≠ 0 := by
  intro hinv
  have e1 := coeff_one_of_invariant _ c hc0 hinv (by norm_num)
  have e2 := coeff_two_of_invariant _ c hc0 hinv (by norm_num) (by norm_num)
  have r := (invariant_iff_recurrence _ c hc0).mp hinv 3 (by norm_num)
  rw [rhsR_three _ c hc0, denom_three, e1, e2] at r
  unfold gOMK aOMK at r
  norm_num at r

/-- compatibility values recorded in FROZEN_TARGETS N2/N3 -/
theorem rhsR_two_at_order_two_resonance [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0)
    (hinv1 : c 1 = -2 / (3 * (-7 / 9 : F) + 5)) : rhsR (-7 / 9 : F) c 2 = -5 / 8 := by
  rw [rhsR_two _ c hc0, hinv1]; unfold gOMK; norm_num

theorem rhsR_three_at_order_three_resonance [CharZero F] (c : ℕ → F) (hc0 : c 0 = 0)
    (hc1 : c 1 = -2 / (3 * (-3 / 5 : F) + 5))
    (hc2 : c 2 = -2 * (9 * (-3 / 5 : F) ^ 2 + 18 * (-3 / 5) + 13) /
      ((3 * (-3 / 5 : F) + 5) ^ 2 * (9 * (-3 / 5) + 7))) :
    rhsR (-3 / 5 : F) c 3 = -567 / 512 := by
  rw [rhsR_three _ c hc0, hc1, hc2]; unfold gOMK aOMK; norm_num

/-- V1: non-vacuity -/
theorem dust_solution_exists :
    ∃ c : ℕ → ℝ, c 0 = 0 ∧ invRes 0 (PowerSeries.mk c) = 0 ∧ c 2 = -26 / 175 := by
  obtain ⟨c, ⟨hc0, hinv⟩, -⟩ := exists_unique_on_domain 0 (by norm_num) (by norm_num)
  exact ⟨c, hc0, hinv, (dust_values c hc0 hinv).2.1⟩

/-- N0 (amendment witness): the frozen T2 without a characteristic hypothesis is false
in characteristic 2. -/
theorem frozen_T2_fails_char_two :
    ¬ ∀ (w : ZMod 2) (c : ℕ → ZMod 2) (n : ℕ),
      coeff (n + 1) (invRes w (PowerSeries.mk c)) = denom w (n + 1) * c (n + 1) - rhsR w c (n + 1) := by
  intro h
  have := h 0 (fun n => if n = 1 then 1 else 0) 0
  rw [coeff_invRes_succ_raw] at this
  simp [rhsR, denom, gOMK, aOMK, quadE, cubE, cub,
    Finset.Nat.sum_antidiagonal_eq_sum_range_succ_mk, Finset.sum_range_succ] at this
  have h2 : (2 : ZMod 2) = 0 := rfl
  simp only [div_eq_mul_inv, h2, inv_zero, mul_zero, zero_mul, add_zero, zero_add] at this
  exact absurd this (by decide)

end

end R192A
