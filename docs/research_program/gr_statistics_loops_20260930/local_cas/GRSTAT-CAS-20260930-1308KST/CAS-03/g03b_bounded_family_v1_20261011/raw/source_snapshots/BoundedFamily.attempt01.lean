import PositiveSequence

/-! Fixed-observer Euclidean component caps for the displayed source family. -/

namespace G03BBoundedFamily

open scoped BigOperators Matrix
open G03BBoostedKernelMembership G03BSquaredCoefficientError G03BPositiveSequence

noncomputable section

def observerNormSq (v : FourVector) : Real := ∑ i : Fin 4, (v i)^2

def observerNorm (v : FourVector) : Real := Real.sqrt (observerNormSq v)

def rateAmplitude (B : FourMatrix) : Real := Real.sqrt (frobeniusSq B)

def rateCap (epsilon0 R b2 b3 : Real) : Real :=
  Real.sqrt (epsilon0^2 * Real.cosh (2 * R)^2 + b2^2 + b3^2)

theorem epsilonSeq_le_initial (epsilon0 : Real) (he0 : 0 ≤ epsilon0) (n : Nat) :
    epsilonSeq epsilon0 n ≤ epsilon0 := by
  have hn : 0 ≤ (n : Real) := Nat.cast_nonneg n
  have hd : 0 < (n : Real) + 1 := by linarith
  unfold epsilonSeq
  apply (div_le_iff₀ hd).2
  nlinarith

theorem observerNormSq_uChi (chi : Real) :
    observerNormSq (uChi chi) = Real.cosh (2 * chi) := by
  simp [observerNormSq, uChi, Fin.sum_univ_succ, Real.cosh_two_mul]

theorem frobeniusSq_boostedB (epsilon chi b2 b3 : Real) :
    frobeniusSq (boostedB epsilon chi b2 b3) =
      epsilon^2 * Real.cosh (2 * chi)^2 + b2^2 + b3^2 := by
  simp [frobeniusSq, boostedB, covOuter, rflat, e2flat, e3flat,
    Fin.sum_univ_succ, Real.cosh_two_mul]
  ring

theorem observerNorm_pair_le (chi R : Real) (hchi : 0 ≤ chi) (hchiR : chi ≤ R) :
    observerNorm (uChi chi) ≤ Real.sqrt (Real.cosh (2 * R)) ∧
      observerNorm (uChi 0) ≤ Real.sqrt (Real.cosh (2 * R)) := by
  have hR : 0 ≤ R := le_trans hchi hchiR
  have hc : Real.cosh (2 * chi) ≤ Real.cosh (2 * R) := by
    apply Real.cosh_le_cosh.mpr
    rw [abs_of_nonneg (by nlinarith : 0 ≤ 2 * chi),
      abs_of_nonneg (by nlinarith : 0 ≤ 2 * R)]
    linarith
  constructor
  · simpa [observerNorm, observerNormSq_uChi] using Real.sqrt_le_sqrt hc
  · have hzero : Real.cosh (2 * (0 : Real)) ≤ Real.cosh (2 * R) := by
      simpa using (le_trans (le_refl (1 : Real)) (Real.one_le_cosh (2 * R)))
    simpa [observerNorm, observerNormSq_uChi] using Real.sqrt_le_sqrt hzero

theorem rateAmplitude_sequence_pair_le (epsilon0 chi R b2 b3 : Real)
    (he0 : 0 < epsilon0) (hchi : 0 ≤ chi) (hchiR : chi ≤ R) (n : Nat) :
    rateAmplitude (boostedB (epsilonSeq epsilon0 n) chi b2 b3) ≤
      rateCap epsilon0 R b2 b3 ∧
    rateAmplitude (boostedB (epsilonSeq epsilon0 n) 0 b2 b3) ≤
      rateCap epsilon0 R b2 b3 := by
  have hepos : 0 ≤ epsilonSeq epsilon0 n :=
    (epsilonSeq_pos epsilon0 he0 n).le
  have hele : epsilonSeq epsilon0 n ≤ epsilon0 :=
    epsilonSeq_le_initial epsilon0 he0.le n
  have he2 : (epsilonSeq epsilon0 n)^2 ≤ epsilon0^2 := by nlinarith
  have hbound (xi : Real) (hxi : 0 ≤ xi) (hxiR : xi ≤ R) :
      rateAmplitude (boostedB (epsilonSeq epsilon0 n) xi b2 b3) ≤
        rateCap epsilon0 R b2 b3 := by
    have hR : 0 ≤ R := le_trans hxi hxiR
    have hc : Real.cosh (2 * xi) ≤ Real.cosh (2 * R) := by
      apply Real.cosh_le_cosh.mpr
      rw [abs_of_nonneg (by nlinarith : 0 ≤ 2 * xi),
        abs_of_nonneg (by nlinarith : 0 ≤ 2 * R)]
      linarith
    have hc2 : Real.cosh (2 * xi)^2 ≤ Real.cosh (2 * R)^2 := by
      nlinarith [Real.cosh_pos (2 * xi), Real.cosh_pos (2 * R)]
    have hmul : (epsilonSeq epsilon0 n)^2 * Real.cosh (2 * xi)^2 ≤
        epsilon0^2 * Real.cosh (2 * R)^2 :=
      mul_le_mul he2 hc2 (sq_nonneg _) (sq_nonneg _)
    unfold rateAmplitude rateCap
    rw [frobeniusSq_boostedB]
    exact Real.sqrt_le_sqrt (by linarith)
  exact ⟨hbound chi hchi hchiR, hbound 0 (le_refl 0) hchi⟩

end
end G03BBoundedFamily

#print axioms G03BBoundedFamily.epsilonSeq_le_initial
#print axioms G03BBoundedFamily.observerNormSq_uChi
#print axioms G03BBoundedFamily.frobeniusSq_boostedB
#print axioms G03BBoundedFamily.observerNorm_pair_le
#print axioms G03BBoundedFamily.rateAmplitude_sequence_pair_le
