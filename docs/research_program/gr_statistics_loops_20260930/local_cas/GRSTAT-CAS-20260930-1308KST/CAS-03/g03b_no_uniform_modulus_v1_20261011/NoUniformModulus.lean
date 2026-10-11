import BoundedFamily

/-! A punctured positive-error obstruction for slope-only velocity bounds. -/

namespace G03BNoUniformModulus

open G03BBoostedKernelMembership G03BFutureUnitUniqueness
  G03BPositiveSequence G03BBoundedFamily Filter

noncomputable section

def observerDistance (u v : FourVector) : Real := observerNorm (u - v)

def VanishingSlopeModulus (omega : Real → Real) : Prop :=
  Filter.Tendsto omega (nhdsWithin (0 : Real) (Set.Ioi (0 : Real))) (nhds (0 : Real))

def BoundedSourcePair (R L b2 b3 epsilon chi : Real) : Prop :=
  0 < epsilon ∧ 0 < chi ∧ chi ≤ R ∧ 0 < b2 ∧ 0 < b3 ∧
  observerNorm (uChi chi) ≤ Real.sqrt (Real.cosh (2 * R)) ∧
  observerNorm (uChi 0) ≤ Real.sqrt (Real.cosh (2 * R)) ∧
  rateAmplitude (boostedB epsilon chi b2 b3) ≤ L ∧
  rateAmplitude (boostedB epsilon 0 b2 b3) ≤ L

def UniformSlopeVelocityBound (R L b2 b3 : Real) (omega : Real → Real) : Prop :=
  ∀ epsilon chi : Real, BoundedSourcePair R L b2 b3 epsilon chi →
    observerDistance (uChi chi) (uChi 0) ≤ omega (coefficientError epsilon chi b2 b3)

theorem observerDistance_uChi_pos (chi : Real) (hchi : 0 < chi) :
    0 < observerDistance (uChi chi) (uChi 0) := by
  have hs : 0 < Real.sinh chi := Real.sinh_pos_iff.mpr hchi
  unfold observerDistance observerNorm observerNormSq
  apply Real.sqrt_pos.2
  simp [uChi, Fin.sum_univ_succ, Pi.sub_apply]
  nlinarith [sq_pos_of_pos hs, sq_nonneg (Real.cosh chi - 1)]

theorem coefficientError_pos (epsilon chi b2 b3 : Real)
    (he : 0 < epsilon) (hchi : 0 < chi) :
    0 < coefficientError epsilon chi b2 b3 := by
  have hs : 0 < Real.sinh chi := Real.sinh_pos_iff.mpr hchi
  have hc : 0 < Real.cosh chi := Real.cosh_pos chi
  unfold coefficientError
  rw [G03BSquaredCoefficientError.slopeRepresentative_difference_frobeniusSq]
  apply Real.sqrt_pos.2
  positivity

theorem no_uniform_slope_only_velocity_modulus
    (epsilon0 chi R b2 b3 : Real) (he0 : 0 < epsilon0)
    (hchi : 0 < chi) (hchiR : chi ≤ R) (h2 : 0 < b2) (h3 : 0 < b3) :
    ¬ ∃ omega : Real → Real, VanishingSlopeModulus omega ∧
      UniformSlopeVelocityBound R (rateCap epsilon0 R b2 b3) b2 b3 omega := by
  rintro ⟨omega, hvanish, hbound⟩
  let err : Nat → Real := fun n => coefficientError (epsilonSeq epsilon0 n) chi b2 b3
  have herr0 : Tendsto err atTop (nhds (0 : Real)) :=
    coefficientError_tendsto_zero epsilon0 chi b2 b3
  have herrpos (n : Nat) : 0 < err n :=
    coefficientError_pos (epsilonSeq epsilon0 n) chi b2 b3
      (epsilonSeq_pos epsilon0 he0 n) hchi
  have herrWithin : Tendsto err atTop
      (nhdsWithin (0 : Real) (Set.Ioi (0 : Real))) :=
    tendsto_nhdsWithin_of_tendsto_nhds_of_eventually_within err herr0
      (Eventually.of_forall fun n => herrpos n)
  have homega : Tendsto (fun n : Nat => omega (err n)) atTop (nhds (0 : Real)) :=
    hvanish.comp herrWithin
  have hpair (n : Nat) :
      BoundedSourcePair R (rateCap epsilon0 R b2 b3) b2 b3
        (epsilonSeq epsilon0 n) chi := by
    obtain ⟨hu, hz⟩ := observerNorm_pair_le chi R hchi.le hchiR
    obtain ⟨hr, hr0⟩ :=
      rateAmplitude_sequence_pair_le epsilon0 chi R b2 b3 he0 hchi.le hchiR n
    exact ⟨epsilonSeq_pos epsilon0 he0 n, hchi, hchiR, h2, h3,
      hu, hz, hr, hr0⟩
  have hsep : 0 < observerDistance (uChi chi) (uChi 0) :=
    observerDistance_uChi_pos chi hchi
  have hlim : observerDistance (uChi chi) (uChi 0) ≤ 0 :=
    le_of_tendsto_of_tendsto' tendsto_const_nhds homega
      (fun n => hbound (epsilonSeq epsilon0 n) chi (hpair n))
  exact (not_le_of_gt hsep) hlim

end
end G03BNoUniformModulus

#print axioms G03BNoUniformModulus.observerDistance_uChi_pos
#print axioms G03BNoUniformModulus.coefficientError_pos
#print axioms G03BNoUniformModulus.no_uniform_slope_only_velocity_modulus
