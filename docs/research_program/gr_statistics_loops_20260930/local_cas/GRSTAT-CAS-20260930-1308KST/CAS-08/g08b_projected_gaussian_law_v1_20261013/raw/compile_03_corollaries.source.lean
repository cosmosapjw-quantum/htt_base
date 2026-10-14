import G08AWhitening

/-!
Named corollaries for the CAS-08 C01/C02 card items "annihilation" and
"rank formula", stated for the residual projector P = 1 - A X of a
Moore–Penrose pair and for the whitened response A = W F.
Added after independent review of `G08AWhitening.lean` (note N1); that
source is unchanged.
-/

namespace G08AWhitening

open Matrix

variable {n k : ℕ}

/-- Annihilation: the residual projector kills the response columns. -/
theorem residual_annihilates (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) : (1 - A * X) * A = 0 := by
  rw [Matrix.sub_mul, Matrix.one_mul, hX.1, sub_self]

/-- Rank formula: `rank (1 - A X) = n - rank A`. -/
theorem residual_rank (A : Matrix (Fin n) (Fin k) ℝ) (X : Matrix (Fin k) (Fin n) ℝ)
    (hX : IsMoorePenrose A X) : (1 - A * X).rank = n - A.rank := by
  obtain ⟨U, hU, -, hP⟩ := projector_spectrum A X hX
  rw [hP, rank_conj_diag U hU]
  have : (Finset.univ.filter fun i : Fin n => (if (i:ℕ) < n - A.rank then (1:ℝ) else 0) ≠ 0)
      = Finset.univ.filter fun i : Fin n => (i:ℕ) < n - A.rank := by
    apply Finset.filter_congr; intro i _; split_ifs <;> simp_all
  rw [this, Fin.card_filter_val_lt]
  omega

/-- Whitening does not change the response rank, so `ν = n - rank F`. -/
theorem nu_eq (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (hW : IsUnit W ∧ W * C * Wᵀ = 1) : (W * F).rank = F.rank :=
  rank_mul_eq_right_of_isUnit_det W F ((Matrix.isUnit_iff_isUnit_det W).mp hW.1)

/-- The whitened residual projector has rank `n - rank F`. -/
theorem whitened_residual_rank (C W : Matrix (Fin n) (Fin n) ℝ) (F : Matrix (Fin n) (Fin k) ℝ)
    (X : Matrix (Fin k) (Fin n) ℝ) (hW : IsUnit W ∧ W * C * Wᵀ = 1)
    (hX : IsMoorePenrose (W * F) X) : (1 - W * F * X).rank = n - F.rank := by
  rw [residual_rank (W * F) X hX, nu_eq C W F hW]

end G08AWhitening
