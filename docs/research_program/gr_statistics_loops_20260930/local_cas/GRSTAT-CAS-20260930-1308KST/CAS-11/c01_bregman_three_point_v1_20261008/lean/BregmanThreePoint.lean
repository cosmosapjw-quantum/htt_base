import Mathlib

/-! CAS-11-C01: finite real Euclidean Bregman identity and exact moment cancellation.
    H and its gradient are arbitrary values/functions at the named points. No
    convexity, positivity, continuum, or integrability premise is used. -/

namespace CAS11C01

open scoped BigOperators

def dot {n : ℕ} (x y : Fin n → ℝ) : ℝ := ∑ i, x i * y i

def bregman {n : ℕ} (H : (Fin n → ℝ) → ℝ)
    (gradH : (Fin n → ℝ) → Fin n → ℝ) (x y : Fin n → ℝ) : ℝ :=
  H x - H y - dot (gradH y) (fun i => x i - y i)

theorem three_point {n : ℕ} (H : (Fin n → ℝ) → ℝ)
    (gradH : (Fin n → ℝ) → Fin n → ℝ) (f g h : Fin n → ℝ) :
    bregman H gradH f g - bregman H gradH f h - bregman H gradH h g =
      dot (fun i => gradH h i - gradH g i) (fun i => f i - h i) := by
  simp only [bregman, dot, Finset.sum_sub_distrib, mul_sub, sub_mul]
  ring

def mv {n k : ℕ} (V : Fin n → Fin k → ℝ) (lam : Fin k → ℝ) : Fin n → ℝ :=
  fun i => ∑ j, V i j * lam j

def tmv {n k : ℕ} (V : Fin n → Fin k → ℝ) (x : Fin n → ℝ) : Fin k → ℝ :=
  fun j => ∑ i, V i j * x i

theorem transpose_pairing {n k : ℕ} (V : Fin n → Fin k → ℝ)
    (lam : Fin k → ℝ) (x : Fin n → ℝ) :
    dot (mv V lam) x = dot lam (tmv V x) := by
  simp only [dot, mv, tmv]
  simp_rw [Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro j _
  apply Finset.sum_congr rfl
  intro i _
  ring

theorem exact_moment_cancellation {n k : ℕ}
    (H : (Fin n → ℝ) → ℝ) (gradH : (Fin n → ℝ) → Fin n → ℝ)
    (f g h : Fin n → ℝ) (V : Fin n → Fin k → ℝ) (lam : Fin k → ℝ)
    (hgrad : (fun i => gradH h i - gradH g i) = mv V lam)
    (hmoment : tmv V (fun i => f i - h i) = 0) :
    bregman H gradH f g - bregman H gradH f h - bregman H gradH h g = 0 := by
  rw [three_point, hgrad, transpose_pairing, hmoment]
  simp [dot]

noncomputable def cubic (x : Fin 1 → ℝ) : ℝ := x 0 ^ 3 / 3
def cubicGrad (x : Fin 1 → ℝ) : Fin 1 → ℝ := fun _ => x 0 ^ 2

theorem orientation_control_forward :
    bregman cubic cubicGrad (fun _ => 2) (fun _ => 1) = 4 / 3 := by
  norm_num [bregman, cubic, cubicGrad, dot, Fin.sum_univ_one]

theorem orientation_control_reverse :
    bregman cubic cubicGrad (fun _ => 1) (fun _ => 2) = 5 / 3 := by
  norm_num [bregman, cubic, cubicGrad, dot, Fin.sum_univ_one]

theorem approximate_moment_control :
    dot (mv (fun (_ : Fin 1) (_ : Fin 1) => (1 : ℝ)) (fun _ => 1))
      (fun _ => (1 / 10 : ℝ)) = 1 / 10 := by
  norm_num [dot, mv, Fin.sum_univ_one]

theorem approximate_moment_nonzero :
    dot (mv (fun (_ : Fin 1) (_ : Fin 1) => (1 : ℝ)) (fun _ => 1))
      (fun _ => (1 / 10 : ℝ)) ≠ 0 := by
  rw [approximate_moment_control]
  norm_num

end CAS11C01

#print axioms CAS11C01.three_point
#print axioms CAS11C01.transpose_pairing
#print axioms CAS11C01.exact_moment_cancellation
#print axioms CAS11C01.orientation_control_forward
#print axioms CAS11C01.orientation_control_reverse
#print axioms CAS11C01.approximate_moment_control
#print axioms CAS11C01.approximate_moment_nonzero
