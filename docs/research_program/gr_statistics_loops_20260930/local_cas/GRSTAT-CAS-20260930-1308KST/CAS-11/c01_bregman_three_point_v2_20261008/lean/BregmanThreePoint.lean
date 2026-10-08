import Mathlib

/-!
CAS-11-C01: exact finite Bregman three-point identity and moment cancellation.
The real vectors are functions on arbitrary `Fin n`; `n = 0` and `k = 0`
are included. No convexity, positivity, or continuum assumption is used.
-/

namespace CAS11C01

open Finset

def dot {n : ℕ} (x y : Fin n → ℝ) : ℝ :=
  ∑ i, x i * y i

def bregman {n : ℕ} (H : (Fin n → ℝ) → ℝ)
    (gradH : (Fin n → ℝ) → Fin n → ℝ)
    (x y : Fin n → ℝ) : ℝ :=
  H x - H y - dot (gradH y) (fun i => x i - y i)

theorem three_point {n : ℕ} (H : (Fin n → ℝ) → ℝ)
    (gradH : (Fin n → ℝ) → Fin n → ℝ)
    (f g h : Fin n → ℝ) :
    bregman H gradH f g - bregman H gradH f h -
        bregman H gradH h g =
      dot (fun i => gradH h i - gradH g i)
        (fun i => f i - h i) := by
  simp only [bregman, dot, mul_sub, sub_mul, Finset.sum_sub_distrib]
  ring

def matVec {n k : ℕ} (V : Fin n → Fin k → ℝ)
    (lam : Fin k → ℝ) : Fin n → ℝ :=
  fun i => ∑ j, V i j * lam j

def transposeVec {n k : ℕ} (V : Fin n → Fin k → ℝ)
    (w : Fin n → ℝ) : Fin k → ℝ :=
  fun j => ∑ i, V i j * w i

theorem dot_matVec {n k : ℕ} (V : Fin n → Fin k → ℝ)
    (lam : Fin k → ℝ) (w : Fin n → ℝ) :
    dot (matVec V lam) w = ∑ j, lam j * transposeVec V w j := by
  simp only [dot, matVec, transposeVec]
  calc
    ∑ i, (∑ j, V i j * lam j) * w i =
        ∑ i, ∑ j, V i j * lam j * w i := by simp_rw [Finset.sum_mul]
    _ = ∑ j, ∑ i, V i j * lam j * w i := Finset.sum_comm
    _ = ∑ j, lam j * ∑ i, V i j * w i := by
      apply Finset.sum_congr rfl
      intro j _
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro i _
      ring

theorem exact_moment_cancellation {n k : ℕ}
    (V : Fin n → Fin k → ℝ) (lam : Fin k → ℝ)
    (f h : Fin n → ℝ)
    (hgrad ggrad : Fin n → ℝ)
    (hmatch : (fun i => hgrad i - ggrad i) = matVec V lam)
    (moment : transposeVec V (fun i => f i - h i) = 0) :
    dot (fun i => hgrad i - ggrad i)
      (fun i => f i - h i) = 0 := by
  rw [hmatch, dot_matVec]
  simp [moment]

theorem three_point_cancel {n k : ℕ}
    (H : (Fin n → ℝ) → ℝ)
    (gradH : (Fin n → ℝ) → Fin n → ℝ)
    (V : Fin n → Fin k → ℝ) (lam : Fin k → ℝ)
    (f g h : Fin n → ℝ)
    (hmatch : (fun i => gradH h i - gradH g i) = matVec V lam)
    (moment : transposeVec V (fun i => f i - h i) = 0) :
    bregman H gradH f g - bregman H gradH f h -
      bregman H gradH h g = 0 := by
  rw [three_point]
  exact exact_moment_cancellation V lam f h (gradH h) (gradH g) hmatch moment

noncomputable def cubicBregman (x y : ℝ) : ℝ :=
  x ^ 3 / 3 - y ^ 3 / 3 - y ^ 2 * (x - y)

theorem cubic_forward : cubicBregman 2 1 = 4 / 3 := by
  norm_num [cubicBregman]

theorem cubic_reverse : cubicBregman 1 2 = 5 / 3 := by
  norm_num [cubicBregman]

theorem cubic_orientation_nonzero :
    cubicBregman 2 1 ≠ cubicBregman 1 2 := by
  rw [cubic_forward, cubic_reverse]
  norm_num

theorem approximate_moment_nonzero :
    (1 : ℝ) * 1 * (1 / 10) = 1 / 10 ∧
      (1 : ℝ) * 1 * (1 / 10) ≠ 0 := by
  norm_num

#print axioms three_point
#print axioms dot_matVec
#print axioms exact_moment_cancellation
#print axioms three_point_cancel
#print axioms cubic_orientation_nonzero
#print axioms approximate_moment_nonzero

end CAS11C01
