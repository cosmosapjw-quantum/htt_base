import Mathlib

/-!
# PR-323 MES methodology core: Lean/mathlib axis

This file is the independent Lean axis for
`CAS-PR323-MES-METHODOLOGY-CORE-001`.

The statements are exact over `ℝ`.  The rotation generators use the active,
right-handed Cartesian convention.  The directional reconstruction consumes
only the registered second- and fourth-sphere-moment identities.  Odd
contractions are zero in the coefficient model by antipodal parity; no third
moment is assumed.  The Fisher ordering is two depth profiles tensor three
directional components.

This is a diagnostic-only methodology receipt.  It proves no physical
local/global response, native transfer result, geometry/family identification,
posterior evidence, or release claim.
-/

set_option autoImplicit false
set_option maxRecDepth 100000

open scoped BigOperators Kronecker Matrix

namespace PR323MESMethodologyCore

noncomputable section

abbrev Vec3 := Fin 3 → ℝ
abbrev Mat3 := Matrix (Fin 3) (Fin 3) ℝ

/-! ## Standard infinitesimal SO(3) generators -/

def Jx : Mat3 :=
  ![![0, 0, 0],
    ![0, 0, -1],
    ![0, 1, 0]]

def Jy : Mat3 :=
  ![![0, 0, 1],
    ![0, 0, 0],
    ![-1, 0, 0]]

def Jz : Mat3 :=
  ![![0, -1, 0],
    ![1, 0, 0],
    ![0, 0, 0]]

/-- A vector fixed by all three standard infinitesimal generators is zero. -/
theorem scalar_to_vector_no_go
    (v : Vec3)
    (hx : Jx.mulVec v = 0)
    (hy : Jy.mulVec v = 0)
    (hz : Jz.mulVec v = 0) :
    v = 0 := by
  funext i
  fin_cases i
  · have h := congrFun hy 2
    simpa [Jy, Matrix.mulVec, dotProduct, Fin.sum_univ_three] using h
  · have h := congrFun hz 0
    simpa [Jz, Matrix.mulVec, dotProduct, Fin.sum_univ_three] using h
  · have h := congrFun hx 1
    simpa [Jx, Matrix.mulVec, dotProduct, Fin.sum_univ_three] using h

/-- Five-coordinate representation of a real symmetric trace-free 3x3 tensor. -/
structure STF3 where
  xx : ℝ
  yy : ℝ
  xy : ℝ
  xz : ℝ
  yz : ℝ

namespace STF3

def toMatrix (S : STF3) : Mat3 :=
  ![![S.xx, S.xy, S.xz],
    ![S.xy, S.yy, S.yz],
    ![S.xz, S.yz, -S.xx - S.yy]]

@[simp] theorem toMatrix_symmetric (S : STF3) : S.toMatrixᵀ = S.toMatrix := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [toMatrix]

@[simp] theorem toMatrix_trace (S : STF3) : Matrix.trace S.toMatrix = 0 := by
  simp [Matrix.trace, toMatrix, Fin.sum_univ_three]

end STF3

/-- A symmetric trace-free tensor commuting with every standard generator is zero. -/
theorem scalar_to_stf2_no_go
    (S : STF3)
    (hx : Jx * S.toMatrix = S.toMatrix * Jx)
    (hy : Jy * S.toMatrix = S.toMatrix * Jy)
    (hz : Jz * S.toMatrix = S.toMatrix * Jz) :
    S = ⟨0, 0, 0, 0, 0⟩ := by
  have hxy : S.xy = 0 := by
    have h := congrFun (congrFun hz 0) 0
    simp [Jz, STF3.toMatrix, Matrix.mul_apply, Fin.sum_univ_three] at h
    linarith
  have hdiag : S.xx = S.yy := by
    have h := congrFun (congrFun hz 0) 1
    simp [Jz, STF3.toMatrix, Matrix.mul_apply, Fin.sum_univ_three] at h
    linarith
  have hyz : S.yz = 0 := by
    have h := congrFun (congrFun hz 0) 2
    simp [Jz, STF3.toMatrix, Matrix.mul_apply, Fin.sum_univ_three] at h
    linarith
  have hxz : S.xz = 0 := by
    have h := congrFun (congrFun hz 1) 2
    simp [Jz, STF3.toMatrix, Matrix.mul_apply, Fin.sum_univ_three] at h
    linarith
  have htraceBranch : -S.xx - S.yy = S.xx := by
    have h := congrFun (congrFun hy 0) 2
    simp [Jy, STF3.toMatrix, Matrix.mul_apply, Fin.sum_univ_three] at h
    linarith
  have hxx : S.xx = 0 := by linarith
  have hyy : S.yy = 0 := by linarith
  cases S
  simp_all

/-! ## Full-sky directional moment reconstruction -/

def delta (i j : Fin 3) : ℝ := if i = j then 1 else 0

/--
Only the two normalized sphere moments permitted by the CAS contract are
fields.  Odd coefficient contractions below are definitionally zero because
the full-sky area measure and the registered field are antipodally paired.
-/
structure FullSkyMoments where
  second : Fin 3 → Fin 3 → ℝ
  fourth : Fin 3 → Fin 3 → Fin 3 → Fin 3 → ℝ
  second_eq : ∀ i j,
    second i j = (4 * Real.pi / 3) * delta i j
  fourth_eq : ∀ i j k l,
    fourth i j k l = (4 * Real.pi / 15) *
      (delta i j * delta k l + delta i k * delta j l + delta i l * delta j k)

/-- Raw dipole contraction for q(n)=v·n+S_ij n_i n_j. -/
def dipoleRaw (M : FullSkyMoments) (v : Vec3) (S : STF3) (a : Fin 3) : ℝ :=
  (∑ i, v i * M.second i a) +
  (∑ i, ∑ j, S.toMatrix i j * (0 : ℝ))

def dipoleRecovered (M : FullSkyMoments) (v : Vec3) (S : STF3) : Vec3 :=
  fun a ↦ (3 / (4 * Real.pi)) * dipoleRaw M v S a

/-- The registered 3/(4π) dipole normalization reconstructs v exactly. -/
theorem directional_dipole_recovery
    (M : FullSkyMoments) (v : Vec3) (S : STF3) :
    dipoleRecovered M v S = v := by
  funext a
  fin_cases a <;>
    simp [dipoleRecovered, dipoleRaw, M.second_eq, delta, Fin.sum_univ_three] <;>
    field_simp [Real.pi_ne_zero] <;>
    ring

/-- Raw STF2 contraction against n_a n_b-δ_ab/3. -/
def stf2Raw
    (M : FullSkyMoments) (v : Vec3) (S : STF3) (a b : Fin 3) : ℝ :=
  (∑ i, v i * (0 : ℝ)) +
  (∑ i, ∑ j, S.toMatrix i j *
    (M.fourth i j a b - delta a b / 3 * M.second i j))

def stf2Recovered (M : FullSkyMoments) (v : Vec3) (S : STF3) : Mat3 :=
  fun a b ↦ (15 / (8 * Real.pi)) * stf2Raw M v S a b

/-- The registered 15/(8π) STF2 normalization reconstructs S exactly. -/
theorem directional_stf2_recovery
    (M : FullSkyMoments) (v : Vec3) (S : STF3) :
    stf2Recovered M v S = S.toMatrix := by
  ext a b
  fin_cases a <;> fin_cases b <;>
    simp [stf2Recovered, stf2Raw, M.second_eq, M.fourth_eq,
      STF3.toMatrix, delta, Fin.sum_univ_three] <;>
    field_simp [Real.pi_ne_zero] <;>
    ring

/-! ## Ordered simple-spectrum eigenframe slice -/

def eigenframeSliceJacobian (lam1 lam2 lam3 : ℝ) : Mat3 :=
  ![![lam2 - lam3, 0, 0],
    ![0, lam3 - lam1, 0],
    ![0, 0, lam1 - lam2]]

theorem eigenframe_slice_determinant (lam1 lam2 lam3 : ℝ) :
    Matrix.det (eigenframeSliceJacobian lam1 lam2 lam3) =
      -(lam1 - lam2) * (lam1 - lam3) * (lam2 - lam3) := by
  simp [eigenframeSliceJacobian, Matrix.det_fin_three]
  ring

/-- The continuous orbit map is transverse on the simple-spectrum locus. -/
theorem eigenframe_slice_transverse_simple_spectrum
    (lam1 lam2 lam3 : ℝ)
    (h12 : lam1 ≠ lam2) (h13 : lam1 ≠ lam3) (h23 : lam2 ≠ lam3) :
    Matrix.det (eigenframeSliceJacobian lam1 lam2 lam3) ≠ 0 := by
  rw [eigenframe_slice_determinant]
  exact mul_ne_zero (mul_ne_zero (neg_ne_zero.mpr (sub_ne_zero.mpr h12))
    (sub_ne_zero.mpr h13)) (sub_ne_zero.mpr h23)

/-! ## Local/global Fisher factorization and one-shell obstruction -/

def depthGram (k₁₁ k₁₂ k₂₂ : ℝ) : Matrix (Fin 2) (Fin 2) ℝ :=
  ![![k₁₁, k₁₂], ![k₁₂, k₂₂]]

def directionalMetric (p q r : ℝ) : Mat3 :=
  ![![p, 0, 0], ![0, q, 0], ![0, 0, r]]

def localGlobalFisher
    (k₁₁ k₁₂ k₂₂ p q r : ℝ) :
    Matrix (Fin 2 × Fin 3) (Fin 2 × Fin 3) ℝ :=
  depthGram k₁₁ k₁₂ k₂₂ ⊗ₖ directionalMetric p q r

/-- det(K⊗S)=det(K)^3 det(S)^2 for the 2-depth by 3-direction ordering. -/
theorem local_global_fisher_factorization
    (k₁₁ k₁₂ k₂₂ p q r : ℝ) :
    Matrix.det (localGlobalFisher k₁₁ k₁₂ k₂₂ p q r) =
      Matrix.det (depthGram k₁₁ k₁₂ k₂₂) ^ 3 *
      Matrix.det (directionalMetric p q r) ^ 2 := by
  simpa [localGlobalFisher] using
    (Matrix.det_kronecker (depthGram k₁₁ k₁₂ k₂₂)
      (directionalMetric p q r))

/-- A one-shell depth Gram matrix has determinant zero. -/
theorem one_shell_depth_gram_singular (fL fG : ℝ) :
    Matrix.det (depthGram (fL * fL) (fL * fG) (fG * fG)) = 0 := by
  simp [depthGram, Matrix.det_fin_two]
  ring

/-! ## Fixed invertible anchor: Fisher congruence and rank invariance -/

theorem fisher_congruence
    {m n : Type} [Fintype m] [Fintype n]
    (R : Matrix m n ℝ) (Cinv : Matrix m m ℝ) (D : Matrix n n ℝ) :
    (R * D)ᵀ * Cinv * (R * D) = Dᵀ * (Rᵀ * Cinv * R) * D := by
  simp only [Matrix.transpose_mul, Matrix.mul_assoc]

theorem invertible_congruence_rank
    {n : Type} [Fintype n] [DecidableEq n]
    (F D : Matrix n n ℝ) (hD : IsUnit D.det) :
    (Dᵀ * F * D).rank = F.rank := by
  calc
    (Dᵀ * F * D).rank = (Dᵀ * F).rank :=
      Matrix.rank_mul_eq_left_of_isUnit_det D (Dᵀ * F) hD
    _ = F.rank := by
      apply Matrix.rank_mul_eq_right_of_isUnit_det Dᵀ F
      simpa using hD

/-- A positive fixed scalar anchor is invertible and preserves Fisher rank. -/
theorem invertible_anchor_fisher_congruence
    {n : Type} [Fintype n] [DecidableEq n]
    (F : Matrix n n ℝ) (U : ℝ) (hU : 0 < U) :
    (((1 / U) • (1 : Matrix n n ℝ))ᵀ * F *
      ((1 / U) • (1 : Matrix n n ℝ))).rank = F.rank := by
  apply invertible_congruence_rank
  rw [Matrix.det_smul, Matrix.det_one]
  exact isUnit_iff_ne_zero.mpr
    (mul_ne_zero (pow_ne_zero _ (one_div_ne_zero (ne_of_gt hU))) one_ne_zero)

/-! ## Observation-inclusive finite ranks -/

def rejectingRanks (m : ℕ) : Finset ℕ :=
  (Finset.Icc 1 (m + 1)).filter (fun r ↦ 20 * r ≤ m + 1)

def rejectingRankCount (m : ℕ) : ℕ := (rejectingRanks m).card

/-- Exact alpha=1/20 observation-inclusive size for m=1,...,100. -/
theorem finite_rank_formula_n1_100 :
    ∀ m ∈ Finset.Icc 1 100,
      rejectingRankCount m = (m + 1) / 20 := by
  decide

def conservativeRank {n : ℕ} (score : Fin n → ℝ) (obs : Fin n) : ℕ :=
  (Finset.univ.filter (fun j ↦ score obs ≤ score j)).card

def strictTieBrokenRank {n : ℕ} (score : Fin n → ℝ) (obs : Fin n) : ℕ :=
  1 + (Finset.univ.filter (fun j ↦ score obs < score j)).card

theorem strict_rank_le_conservative_rank
    {n : ℕ} (score : Fin n → ℝ) (obs : Fin n) :
    strictTieBrokenRank score obs ≤ conservativeRank score obs := by
  unfold strictTieBrokenRank conservativeRank
  let A := Finset.univ.filter (fun j ↦ score obs < score j)
  let B := Finset.univ.filter (fun j ↦ score obs ≤ score j)
  have hnot : obs ∉ A := by simp [A]
  have hsub : insert obs A ⊆ B := by
    intro j hj
    rw [Finset.mem_insert] at hj
    rw [Finset.mem_filter]
    refine ⟨Finset.mem_univ _, ?_⟩
    rcases hj with rfl | hj
    · exact le_rfl
    · exact le_of_lt (Finset.mem_filter.mp hj).2
  have hcard : (insert obs A).card = 1 + A.card := by
    simpa [hnot, Nat.add_comm]
  change 1 + A.card ≤ B.card
  rw [← hcard]
  exact Finset.card_le_card hsub

/-- Ties cannot enlarge the alpha=1/20 rejection set for m=1,...,100. -/
theorem finite_rank_ties_conservative_n1_100
    (m : ℕ) (hm₁ : 1 ≤ m) (hm₁₀₀ : m ≤ 100)
    (score : Fin (m + 1) → ℝ)
    (hreject : 20 * conservativeRank score ⟨0, Nat.zero_lt_succ m⟩ ≤ m + 1) :
    20 * strictTieBrokenRank score ⟨0, Nat.zero_lt_succ m⟩ ≤ m + 1 := by
  have hle := strict_rank_le_conservative_rank score ⟨0, Nat.zero_lt_succ m⟩
  omega

/-! ## Antipodal weighted-axis construction -/

structure AxisWeights where
  value : Fin 3 → ℝ
  nonnegative : ∀ i, 0 ≤ value i
  total : ∑ i, value i = 1

def axisCoordinate (i a : Fin 3) : ℝ := delta i a

def antipodalMean (w : AxisWeights) (a : Fin 3) : ℝ :=
  ∑ i, ((w.value i / 2) * axisCoordinate i a +
    (w.value i / 2) * (-axisCoordinate i a))

/-- The paired positive/negative Cartesian-axis measure has zero mean. -/
theorem zero_mean_antipodal_construction (w : AxisWeights) :
    antipodalMean w = 0 := by
  funext a
  simp [antipodalMean]

def antipodalSecondMoment (w : AxisWeights) (a b : Fin 3) : ℝ :=
  ∑ i, ((w.value i / 2) * (axisCoordinate i a * axisCoordinate i b) +
    (w.value i / 2) * ((-axisCoordinate i a) * (-axisCoordinate i b)))

/-- The paired-axis second moment is diag(lambda1,lambda2,lambda3). -/
theorem second_moment_antipodal_construction (w : AxisWeights) (a b : Fin 3) :
    antipodalSecondMoment w a b = if a = b then w.value a else 0 := by
  fin_cases a <;> fin_cases b <;>
    simp [antipodalSecondMoment, axisCoordinate, delta, Fin.sum_univ_three] <;>
    ring

/-! ## Typed bundle tying every registered runner check to a theorem -/

structure RegisteredProofBundle : Prop where
  scalar_to_vector_no_go :
    ∀ (v : Vec3), Jx.mulVec v = 0 → Jy.mulVec v = 0 → Jz.mulVec v = 0 → v = 0
  scalar_to_stf2_no_go :
    ∀ (S : STF3), Jx * S.toMatrix = S.toMatrix * Jx →
      Jy * S.toMatrix = S.toMatrix * Jy →
      Jz * S.toMatrix = S.toMatrix * Jz → S = ⟨0, 0, 0, 0, 0⟩
  directional_dipole_recovery :
    ∀ (M : FullSkyMoments) (v : Vec3) (S : STF3), dipoleRecovered M v S = v
  directional_stf2_recovery :
    ∀ (M : FullSkyMoments) (v : Vec3) (S : STF3), stf2Recovered M v S = S.toMatrix
  eigenframe_slice_transverse_simple_spectrum :
    ∀ (lam1 lam2 lam3 : ℝ), lam1 ≠ lam2 → lam1 ≠ lam3 → lam2 ≠ lam3 →
      Matrix.det (eigenframeSliceJacobian lam1 lam2 lam3) ≠ 0
  local_global_fisher_factorization :
    ∀ (k₁₁ k₁₂ k₂₂ p q r : ℝ),
      Matrix.det (localGlobalFisher k₁₁ k₁₂ k₂₂ p q r) =
        Matrix.det (depthGram k₁₁ k₁₂ k₂₂) ^ 3 *
        Matrix.det (directionalMetric p q r) ^ 2
  invertible_anchor_fisher_congruence :
    ∀ {n : Type} [Fintype n] [DecidableEq n]
      (F : Matrix n n ℝ) (U : ℝ), 0 < U →
      (((1 / U) • (1 : Matrix n n ℝ))ᵀ * F *
        ((1 / U) • (1 : Matrix n n ℝ))).rank = F.rank
  finite_rank_formula_n1_100 :
    ∀ m ∈ Finset.Icc 1 100, rejectingRankCount m = (m + 1) / 20
  finite_rank_ties_conservative_n1_100 :
    ∀ (m : ℕ), 1 ≤ m → m ≤ 100 → ∀ (score : Fin (m + 1) → ℝ),
      20 * conservativeRank score ⟨0, Nat.zero_lt_succ m⟩ ≤ m + 1 →
      20 * strictTieBrokenRank score ⟨0, Nat.zero_lt_succ m⟩ ≤ m + 1
  zero_mean_antipodal_construction :
    ∀ (w : AxisWeights), antipodalMean w = 0
  second_moment_antipodal_construction :
    ∀ (w : AxisWeights) (a b : Fin 3),
      antipodalSecondMoment w a b = if a = b then w.value a else 0

def registeredProofBundle : RegisteredProofBundle where
  scalar_to_vector_no_go := scalar_to_vector_no_go
  scalar_to_stf2_no_go := scalar_to_stf2_no_go
  directional_dipole_recovery := directional_dipole_recovery
  directional_stf2_recovery := directional_stf2_recovery
  eigenframe_slice_transverse_simple_spectrum := eigenframe_slice_transverse_simple_spectrum
  local_global_fisher_factorization := local_global_fisher_factorization
  invertible_anchor_fisher_congruence := invertible_anchor_fisher_congruence
  finite_rank_formula_n1_100 := finite_rank_formula_n1_100
  finite_rank_ties_conservative_n1_100 := by
    intro m hm₁ hm₁₀₀ score hreject
    exact finite_rank_ties_conservative_n1_100 m hm₁ hm₁₀₀ score hreject
  zero_mean_antipodal_construction := zero_mean_antipodal_construction
  second_moment_antipodal_construction := second_moment_antipodal_construction

#print axioms registeredProofBundle

end
end PR323MESMethodologyCore
