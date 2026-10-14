/-
G15-B re-execution closeout, additive target U (review note N2).

Uniform rank ≤ 4 statement for the (B5) angular weight: ONE polynomial p of total degree ≤ 4,
chosen before the measure μ and the brightness I, represents the (B5) weight integral for every
finite rotation-invariant μ and every continuous I, and expands it into brightness moments of
rank ≤ 4.  Derived from the reviewed `G15B.wB5_degree_le_four` plus linearity of the integral.

Imports the reviewed module `G15BSphere` unchanged.  See FROZEN_TARGETS.md (Part B).
-/
import Mathlib
import G15BSphere

open MeasureTheory MvPolynomial
open G15B

namespace G15BU

/-- U, with the measure class not restricted to rotation-invariant measures. -/
theorem B5_rank_le_four_uniform_finite (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      (∀ m ∈ p.support, (m.sum fun _ n => n) ≤ 4) ∧
      ∀ (μ : Measure S2) [IsFiniteMeasure μ], ∀ I : E3 → ℝ, Continuous I →
        (∫ e : S2, I e * wB5 H a σ e i j ∂μ =
            ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ) ∧
        ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
          ∑ m ∈ p.support, MvPolynomial.coeff m p * ∫ e : S2, I e * ∏ k, (e : E3) k ^ m k ∂μ := by
  obtain ⟨p, hdeg, hev⟩ := wB5_degree_le_four H a σ i j
  refine ⟨p, hdeg, fun m hm => (le_totalDegree hm).trans hdeg, ?_⟩
  intro μ _ I hI
  have h1 : ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
      ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ :=
    integral_congr_ae (ae_of_all _ fun e => by simp only [hev])
  refine ⟨h1, ?_⟩
  have hpt : ∀ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p =
      ∑ m ∈ p.support, MvPolynomial.coeff m p * (I e * ∏ k, (e : E3) k ^ m k) := by
    intro e
    rw [MvPolynomial.eval_eq', Finset.mul_sum]
    exact Finset.sum_congr rfl fun m _ => by ring
  have hint : ∀ m : Fin 3 →₀ ℕ, Integrable (fun e : S2 => I e * ∏ k, (e : E3) k ^ m k) μ :=
    fun m => integrable_cont μ (g := fun x => I x * ∏ k, x k ^ m k)
      (hI.mul (continuous_finsetProd _ fun k _ => (continuous_coord k).pow _))
  rw [h1, integral_congr_ae (ae_of_all _ hpt),
    integral_finsetSum _ fun m _ => (hint m).const_mul _]
  exact Finset.sum_congr rfl fun m _ => integral_const_mul _ _

/-- Target U: uniform rank ≤ 4 (p independent of μ and I). -/
theorem B5_rank_le_four_uniform (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      (∀ m ∈ p.support, (m.sum fun _ n => n) ≤ 4) ∧
      ∀ (μ : Measure S2) [IsFiniteMeasure μ], RotInv μ → ∀ I : E3 → ℝ, Continuous I →
        (∫ e : S2, I e * wB5 H a σ e i j ∂μ =
            ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ) ∧
        ∫ e : S2, I e * wB5 H a σ e i j ∂μ =
          ∑ m ∈ p.support, MvPolynomial.coeff m p * ∫ e : S2, I e * ∏ k, (e : E3) k ^ m k ∂μ := by
  obtain ⟨p, hdeg, hsupp, hall⟩ := B5_rank_le_four_uniform_finite H a σ i j
  refine ⟨p, hdeg, hsupp, ?_⟩
  intro μ _ _ I hI
  exact hall μ I hI

/-- Non-vacuity: the hypothesis class of U is inhabited by the dΩ instance `σS`. -/
theorem B5_rank_le_four_uniform_σS (H : ℝ) (a : E3) (σ : E3 →L[ℝ] E3) (i j : Fin 3) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 4 ∧
      ∀ I : E3 → ℝ, Continuous I →
        ∫ e : S2, I e * wB5 H a σ e i j ∂σS =
          ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂σS := by
  obtain ⟨p, hdeg, _, hall⟩ := B5_rank_le_four_uniform H a σ i j
  exact ⟨p, hdeg, fun I hI => (hall σS σS_rotInv I hI).1⟩

/-- Negative control (review note N2): with the I-wise quantifier order, a degree-0 polynomial
reproduces any prescribed value whenever ∫ I dμ ≠ 0. -/
theorem iwise_form_degenerate (μ : Measure S2) {I : E3 → ℝ}
    (hI0 : ∫ e : S2, I e ∂μ ≠ 0) (v : ℝ) :
    ∃ p : MvPolynomial (Fin 3) ℝ, p.totalDegree ≤ 0 ∧
      ∫ e : S2, I e * MvPolynomial.eval (fun k => (e : E3) k) p ∂μ = v := by
  refine ⟨C (v / ∫ e : S2, I e ∂μ), (totalDegree_C _).le, ?_⟩
  simp only [eval_C]
  rw [integral_mul_const]
  field_simp

end G15BU
