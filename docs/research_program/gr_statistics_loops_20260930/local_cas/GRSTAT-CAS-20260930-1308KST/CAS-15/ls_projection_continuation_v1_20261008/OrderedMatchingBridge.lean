import CAS15Spectral

noncomputable section
namespace CAS15OrderedMatching
open scoped InnerProductSpace
open Module
abbrev V3 := EuclideanSpace ℝ (Fin 3)
theorem dim3 : Module.finrank ℝ V3 = 3 := by simp [V3]

def basisSpan (b : OrthonormalBasis (Fin 3) ℝ V3) (s : Set (Fin 3)) :
    Submodule ℝ V3 := Submodule.span ℝ (b '' s)

theorem basisSpan_finrank (b : OrthonormalBasis (Fin 3) ℝ V3)
    (s : Set (Fin 3)) [Fintype s] : Module.finrank ℝ (basisSpan b s) = Fintype.card s := by
  classical
  have hr : Set.range (fun j : s => b j) = b '' s := by aesop
  rw [basisSpan, ← hr]
  exact finrank_span_eq_card (b.toBasis.linearIndependent.comp _ Subtype.val_injective)

theorem coeff_zero (b : OrthonormalBasis (Fin 3) ℝ V3)
    (s : Set (Fin 3)) (v : V3) (hv : v ∈ basisSpan b s)
    (j : Fin 3) (hj : j ∉ s) : b.repr v j = 0 := by
  classical
  induction hv using Submodule.span_induction with
  | mem x hx =>
      rcases hx with ⟨k, hk, rfl⟩
      have hkj : j ≠ k := by aesop
      simp [b.repr_self, hkj]
  | zero => simp
  | add x y hx hy ihx ihy => simpa using congrArg₂ (· + ·) ihx ihy
  | smul a x hx ih => simpa using congrArg (a * ·) ih

theorem rayleigh_sum (T : V3 →ₗ[ℝ] V3) (hT : T.IsSymmetric) (v : V3) :
    ⟪T v, v⟫_ℝ = ∑ j : Fin 3,
      hT.eigenvalues dim3 j * ((hT.eigenvectorBasis dim3).repr v j)^2 := by
  rw [← (hT.eigenvectorBasis dim3).repr.inner_map_map]
  simp only [PiLp.inner_apply, hT.eigenvectorBasis_apply_self_apply dim3]
  apply Finset.sum_congr rfl
  intro j hj
  simp
  ring

theorem norm_sq_sum (b : OrthonormalBasis (Fin 3) ℝ V3) (v : V3) :
    ‖v‖^2 = ∑ j : Fin 3, (b.repr v j)^2 := by
  calc
    ‖v‖^2 = ⟪v,v⟫_ℝ := (real_inner_self_eq_norm_sq v).symm
    _ = ⟪b.repr v,b.repr v⟫_ℝ := (b.repr.inner_map_map v v).symm
    _ = ∑ j : Fin 3, (b.repr v j)^2 := by
      simp only [PiLp.inner_apply, Real.inner_apply]
      apply Finset.sum_congr rfl
      intro j hj
      ring

theorem rayleigh_lower (T : V3 →ₗ[ℝ] V3) (hT : T.IsSymmetric)
    (s : Set (Fin 3)) (c : ℝ) (v : V3)
    (hv : v ∈ basisSpan (hT.eigenvectorBasis dim3) s)
    (hc : ∀ j ∈ s, c ≤ hT.eigenvalues dim3 j) :
    c * ‖v‖^2 ≤ ⟪T v, v⟫_ℝ := by
  rw [rayleigh_sum T hT, norm_sq_sum (hT.eigenvectorBasis dim3), Finset.mul_sum]
  apply Finset.sum_le_sum
  intro j hj
  by_cases hs : j ∈ s
  · exact mul_le_mul_of_nonneg_right (hc j hs) (sq_nonneg _)
  · rw [coeff_zero _ s v hv j hs]
    simp

theorem rayleigh_upper (T : V3 →ₗ[ℝ] V3) (hT : T.IsSymmetric)
    (s : Set (Fin 3)) (c : ℝ) (v : V3)
    (hv : v ∈ basisSpan (hT.eigenvectorBasis dim3) s)
    (hc : ∀ j ∈ s, hT.eigenvalues dim3 j ≤ c) :
    ⟪T v, v⟫_ℝ ≤ c * ‖v‖^2 := by
  rw [rayleigh_sum T hT, norm_sq_sum (hT.eigenvectorBasis dim3), Finset.mul_sum]
  apply Finset.sum_le_sum
  intro j hj
  by_cases hs : j ∈ s
  · exact mul_le_mul_of_nonneg_right (hc j hs) (sq_nonneg _)
  · rw [coeff_zero _ s v hv j hs]
    simp

/-- The high B and low A spectral subspaces overlap by their dimensions.
The dimensions are i+1 and 3-i, independently of eigenvalue multiplicities. -/
theorem spectral_intersection (a b : OrthonormalBasis (Fin 3) ℝ V3) (i : Fin 3) :
    ∃ v : V3, v ≠ 0 ∧ v ∈ basisSpan b {j | j ≤ i} ∧
      v ∈ basisSpan a {j | i ≤ j} := by
  classical
  let S := basisSpan b {j | j ≤ i}
  let U := basisSpan a {j | i ≤ j}
  have hdim : Module.finrank ℝ S + Module.finrank ℝ U = 4 := by
    dsimp [S, U]
    rw [basisSpan_finrank, basisSpan_finrank]
    fin_cases i <;> decide
  have hne : S ⊓ U ≠ ⊥ := by
    intro h
    have heq := Submodule.finrank_sup_add_finrank_inf_eq S U
    rw [h] at heq
    simp only [finrank_bot, add_zero] at heq
    rw [hdim] at heq
    have hle := Submodule.finrank_le (S ⊔ U)
    have hthree : Module.finrank ℝ V3 = 3 := by simp [V3]
    omega
  have hex : ∃ v ∈ S ⊓ U, v ≠ (0 : V3) := by
    by_contra h
    push Not at h
    apply hne
    exact (Submodule.eq_bot_iff _).mpr h
  obtain ⟨v, hv, hn⟩ := hex
  exact ⟨v, hn, hv.1, hv.2⟩

/-- One-sided ordered Weyl comparison, proved via spectral-subspace intersection. -/
theorem ordered_eigenvalue_le (A B : V3 →L[ℝ] V3)
    (hA : A.toLinearMap.IsSymmetric) (hB : B.toLinearMap.IsSymmetric)
    (i : Fin 3) : hB.eigenvalues dim3 i ≤ hA.eigenvalues dim3 i + ‖B - A‖ := by
  obtain ⟨v, hv, hBv, hAv⟩ :=
    spectral_intersection (hA.eigenvectorBasis dim3) (hB.eigenvectorBasis dim3) i
  have hb := rayleigh_lower B.toLinearMap hB {j | j ≤ i} (hB.eigenvalues dim3 i) v hBv
    (fun j hj => hB.eigenvalues_antitone dim3 hj)
  have ha := rayleigh_upper A.toLinearMap hA {j | i ≤ j} (hA.eigenvalues dim3 i) v hAv
    (fun j hj => hA.eigenvalues_antitone dim3 hj)
  change hB.eigenvalues dim3 i * ‖v‖^2 ≤ ⟪B v, v⟫_ℝ at hb
  change ⟪A v, v⟫_ℝ ≤ hA.eigenvalues dim3 i * ‖v‖^2 at ha
  have he : |⟪(B - A) v, v⟫_ℝ| ≤ ‖B - A‖ * ‖v‖^2 := by
    calc
      |⟪(B - A) v, v⟫_ℝ| ≤ ‖(B - A) v‖ * ‖v‖ := abs_real_inner_le_norm _ _
      _ ≤ (‖B - A‖ * ‖v‖) * ‖v‖ :=
        mul_le_mul_of_nonneg_right ((B - A).le_opNorm v) (norm_nonneg _)
      _ = ‖B - A‖ * ‖v‖^2 := by ring
  have hp : 0 < ‖v‖^2 := sq_pos_of_pos (norm_pos_iff.mpr hv)
  have hu := (abs_le.mp he).2
  simp only [sub_apply, inner_sub_left] at hu
  have hm : hB.eigenvalues dim3 i * ‖v‖^2 ≤
      (hA.eigenvalues dim3 i + ‖B - A‖) * ‖v‖^2 := by nlinarith
  exact (mul_le_mul_iff_of_pos_right hp).mp hm

/-- Same-index descending eigenvalues are 1-Lipschitz in the induced Euclidean norm.
No simplicity, chosen matching, or permutation premise is required. -/
theorem ordered_matching (A B : V3 →L[ℝ] V3)
    (hA : A.toLinearMap.IsSymmetric) (hB : B.toLinearMap.IsSymmetric)
    (epsM : ℝ) (hpert : ‖B - A‖ ≤ epsM) :
    ∀ i : Fin 3, |hB.eigenvalues dim3 i - hA.eigenvalues dim3 i| ≤ epsM := by
  intro i
  have hu := ordered_eigenvalue_le A B hA hB i
  have hl := ordered_eigenvalue_le B A hB hA i
  rw [norm_sub_rev] at hl
  exact abs_le.mpr ⟨by linarith, by linarith⟩

theorem ordered_gap_bound (A B : V3 →L[ℝ] V3)
    (hA : A.toLinearMap.IsSymmetric) (hB : B.toLinearMap.IsSymmetric)
    (epsM : ℝ) (hpert : ‖B - A‖ ≤ epsM) :
    CAS15Spectral.orderedGap (hA.eigenvalues dim3) - 2 * epsM ≤
      CAS15Spectral.orderedGap (hB.eigenvalues dim3) :=
  CAS15Spectral.ordered_gap_from_pointwise_matches _ _ _
    (ordered_matching A B hA hB epsM hpert)

#print axioms ordered_matching
#print axioms ordered_gap_bound

abbrev M3 := Matrix (Fin 3) (Fin 3) ℝ
def matrixOperator (M : M3) : V3 →L[ℝ] V3 :=
  Matrix.toEuclideanCLM (n := Fin 3) (𝕜 := ℝ) M

theorem matrixOperator_symmetric (M : M3) (hM : M.IsSymm) :
    (matrixOperator M).toLinearMap.IsSymmetric := by
  apply Matrix.isSymmetric_toEuclideanLin_iff.mpr
  exact Matrix.isHermitian_iff_isSymm.mpr hM

/-- Native decreasing spectrum, with multiplicity, of a real symmetric 3x3 matrix. -/
def orderedSpectrum (M : M3) (hM : M.IsSymm) : Fin 3 → ℝ :=
  (matrixOperator_symmetric M hM).eigenvalues dim3

theorem orderedSpectrum_antitone (M : M3) (hM : M.IsSymm) :
    Antitone (orderedSpectrum M hM) :=
  (matrixOperator_symmetric M hM).eigenvalues_antitone dim3

/-- Arbitrary real symmetric matrices: all three same-index eigenvalue matches
follow from the induced Euclidean operator norm of the matrix perturbation. -/
theorem matrix_ordered_matching (M Mhat : M3) (hM : M.IsSymm) (hMhat : Mhat.IsSymm)
    (epsM : ℝ) (hpert : ‖matrixOperator (Mhat - M)‖ ≤ epsM) :
    ∀ i : Fin 3, |orderedSpectrum Mhat hMhat i - orderedSpectrum M hM i| ≤ epsM := by
  apply ordered_matching (matrixOperator M) (matrixOperator Mhat)
    (matrixOperator_symmetric M hM) (matrixOperator_symmetric Mhat hMhat) epsM
  simpa only [matrixOperator, map_sub] using hpert

theorem matrix_ordered_gap_bound (M Mhat : M3) (hM : M.IsSymm) (hMhat : Mhat.IsSymm)
    (epsM : ℝ) (hpert : ‖matrixOperator (Mhat - M)‖ ≤ epsM) :
    CAS15Spectral.orderedGap (orderedSpectrum M hM) - 2 * epsM ≤
      CAS15Spectral.orderedGap (orderedSpectrum Mhat hMhat) :=
  CAS15Spectral.ordered_gap_from_pointwise_matches _ _ _
    (matrix_ordered_matching M Mhat hM hMhat epsM hpert)

#print axioms matrix_ordered_matching
#print axioms matrix_ordered_gap_bound
end CAS15OrderedMatching
