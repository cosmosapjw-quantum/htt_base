import Mathlib.Analysis.Real.Sqrt
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.LinearAlgebra.Matrix.Rank
import Mathlib.Tactic.FinCases
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.NormNum.RealSqrt

/-!
# PR-254 final Lean axis

Faithful conditional-scope formalization of the eight obligations in
`CAS-PR254-ANCHOR-GEOMETRY-001`, including the final registered ordered
polytope normals and bounds.  No converse, uniqueness, evidence, physical
proximity, or family-identification statement is introduced.
-/

noncomputable section

open scoped BigOperators

namespace PR254R3LeanAxis

/-! ## A maximum over a nonempty finite type -/

section FiniteMaximum

variable {ι : Type*} [Fintype ι] [Nonempty ι]

def finiteMax (f : ι → ℝ) : ℝ :=
  Finset.univ.sup' Finset.univ_nonempty f

theorem finiteMax_le_iff (f : ι → ℝ) (c : ℝ) :
    finiteMax f ≤ c ↔ ∀ i, f i ≤ c := by
  simp [finiteMax, Finset.sup'_le_iff]

theorem le_finiteMax (f : ι → ℝ) (i : ι) :
    f i ≤ finiteMax f := by
  unfold finiteMax
  exact Finset.le_sup' (f := f) (Finset.mem_univ i)

end FiniteMaximum

/-! ## Product of typed Euclidean block balls -/

structure ProductBlockAnchor (n k : ℕ) where
  blocks : Fin k → Finset (Fin n)
  radii : Fin k → ℝ
  radii_pos : ∀ j, 0 < radii j
  covers_once : ∀ i : Fin n, ∃! j : Fin k, i ∈ blocks j

def blockEuclideanNorm {n k : ℕ} (A : ProductBlockAnchor n k)
    (u : Fin n → ℝ) (j : Fin k) : ℝ :=
  Real.sqrt (∑ i ∈ A.blocks j, (u i) ^ 2)

def productGauge {n k : ℕ} [NeZero k] (A : ProductBlockAnchor n k)
    (u : Fin n → ℝ) : ℝ :=
  finiteMax (fun j => blockEuclideanNorm A u j / A.radii j)

theorem product_ball_max_ratio {n k : ℕ} [NeZero k]
    (A : ProductBlockAnchor n k) (u : Fin n → ℝ) :
    productGauge A u =
      finiteMax (fun j => blockEuclideanNorm A u j / A.radii j) := rfl

theorem productGauge_le_one_iff {n k : ℕ} [NeZero k]
    (A : ProductBlockAnchor n k) (u : Fin n → ℝ) :
    productGauge A u ≤ 1 ↔
      ∀ j, blockEuclideanNorm A u j ≤ A.radii j := by
  rw [productGauge, finiteMax_le_iff]
  constructor
  · intro h j
    simpa using (div_le_iff₀ (A.radii_pos j)).mp (h j)
  · intro h j
    apply (div_le_iff₀ (A.radii_pos j)).mpr
    simpa using h j

def productFixtureGauge : ℝ :=
  max (Real.sqrt ((3 : ℝ) ^ 2 + 4 ^ 2) / 2)
      (Real.sqrt ((8 : ℝ) ^ 2) / 4)

theorem product_fixture_exact : productFixtureGauge = (5 : ℝ) / 2 := by
  have h25 : Real.sqrt (25 : ℝ) = 5 := by norm_num
  have h64 : Real.sqrt (64 : ℝ) = 8 := by norm_num
  norm_num [productFixtureGauge, h25, h64]

/-! ## Positive-definite ellipsoid -/

def quadraticForm {n : ℕ} (Q : Matrix (Fin n) (Fin n) ℝ)
    (u : Fin n → ℝ) : ℝ :=
  ∑ i, ∑ j, u i * Q i j * u j

structure EllipsoidAnchor (n : ℕ) where
  Q : Matrix (Fin n) (Fin n) ℝ
  symmetric : Q.transpose = Q
  positive_definite : ∀ u : Fin n → ℝ, u ≠ 0 → 0 < quadraticForm Q u

def ellipsoidGauge {n : ℕ} (A : EllipsoidAnchor n)
    (u : Fin n → ℝ) : ℝ :=
  Real.sqrt (quadraticForm A.Q u)

theorem ellipsoid_unit_sublevel {n : ℕ} (A : EllipsoidAnchor n)
    (u : Fin n → ℝ) :
    ellipsoidGauge A u ≤ 1 ↔ quadraticForm A.Q u ≤ 1 := by
  simp [ellipsoidGauge]

def ellipsoidFixtureQ : Matrix (Fin 2) (Fin 2) ℝ :=
  !![(1 : ℝ) / 4, 0; 0, (1 : ℝ) / 9]

def ellipsoidFixtureU : Fin 2 → ℝ := ![(2 : ℝ), 0]

theorem ellipsoid_fixture_form (u : Fin 2 → ℝ) :
    quadraticForm ellipsoidFixtureQ u =
      (u 0) ^ 2 / 4 + (u 1) ^ 2 / 9 := by
  simp [quadraticForm, ellipsoidFixtureQ, Fin.sum_univ_two]
  ring

theorem ellipsoid_fixture_positive_definite :
    ∀ u : Fin 2 → ℝ, u ≠ 0 → 0 < quadraticForm ellipsoidFixtureQ u := by
  intro u hu
  have hcomponent : u 0 ≠ 0 ∨ u 1 ≠ 0 := by
    by_cases h0 : u 0 = 0
    · right
      intro h1
      apply hu
      funext i
      fin_cases i
      · exact h0
      · exact h1
    · exact Or.inl h0
  rw [ellipsoid_fixture_form]
  rcases hcomponent with h0 | h1
  · have hs0 : 0 < (u 0) ^ 2 := sq_pos_of_ne_zero h0
    have hs1 : 0 ≤ (u 1) ^ 2 := sq_nonneg (u 1)
    nlinarith
  · have hs0 : 0 ≤ (u 0) ^ 2 := sq_nonneg (u 0)
    have hs1 : 0 < (u 1) ^ 2 := sq_pos_of_ne_zero h1
    nlinarith

def ellipsoidFixture : EllipsoidAnchor 2 where
  Q := ellipsoidFixtureQ
  symmetric := by
    ext i j
    fin_cases i <;> fin_cases j <;>
      norm_num [ellipsoidFixtureQ, Matrix.transpose_apply]
  positive_definite := ellipsoid_fixture_positive_definite

theorem ellipsoid_fixture_exact :
    quadraticForm ellipsoidFixtureQ ellipsoidFixtureU = 1 := by
  rw [ellipsoid_fixture_form]
  norm_num [ellipsoidFixtureU]

/-! ## Certified centrally symmetric spanning H-polytope -/

def normalsSpan {n : ℕ} {ι : Type*} (normal : ι → Fin n → ℝ) : Prop :=
  ∀ u : Fin n → ℝ,
    (∀ i, dotProduct (normal i) u = 0) → u = 0

structure HPolytopeAnchor (n : ℕ) (ι : Type*) [Fintype ι] where
  normal : ι → Fin n → ℝ
  bound : ι → ℝ
  bound_pos : ∀ i, 0 < bound i
  normals_span : normalsSpan normal
  antipodal : ∀ i, ∃ j, normal j = -normal i ∧ bound j = bound i

def rawPolytopeGauge {n : ℕ} {ι : Type*}
    [Fintype ι] [Nonempty ι]
    (A : HPolytopeAnchor n ι) (u : Fin n → ℝ) : ℝ :=
  finiteMax (fun i => dotProduct (A.normal i) u / A.bound i)

def polytopeGauge {n : ℕ} {ι : Type*}
    [Fintype ι] [Nonempty ι]
    (A : HPolytopeAnchor n ι) (u : Fin n → ℝ) : ℝ :=
  max (rawPolytopeGauge A u) 0

theorem polytope_unit_sublevel {n : ℕ} {ι : Type*}
    [Fintype ι] [Nonempty ι]
    (A : HPolytopeAnchor n ι) (u : Fin n → ℝ) :
    polytopeGauge A u ≤ 1 ↔
      ∀ i, dotProduct (A.normal i) u ≤ A.bound i := by
  constructor
  · intro h i
    have hraw : rawPolytopeGauge A u ≤ 1 := (max_le_iff.mp h).1
    have hratio : dotProduct (A.normal i) u / A.bound i ≤ 1 :=
      (finiteMax_le_iff
        (fun j => dotProduct (A.normal j) u / A.bound j) 1).mp hraw i
    simpa using (div_le_iff₀ (A.bound_pos i)).mp hratio
  · intro h
    apply max_le
    · apply (finiteMax_le_iff
        (fun i => dotProduct (A.normal i) u / A.bound i) 1).mpr
      intro i
      apply (div_le_iff₀ (A.bound_pos i)).mpr
      simpa using h i
    · norm_num

def polytopeFixtureU : Fin 2 → ℝ := ![(1 : ℝ), 2]

def polytopeFixtureBounds : Fin 4 → ℝ :=
  ![(2 : ℝ), 2, 4, 4]

def polytopeFixtureNormals : Fin 4 → Fin 2 → ℝ :=
  ![![(1 : ℝ), 0], ![-1, 0], ![0, 1], ![0, -1]]

theorem polytope_fixture_normals_span :
    normalsSpan polytopeFixtureNormals := by
  unfold normalsSpan
  intro u h
  funext j
  fin_cases j
  · have h0 := h 0
    simpa [polytopeFixtureNormals, dotProduct, Fin.sum_univ_two] using h0
  · have h2 := h 2
    simpa [polytopeFixtureNormals, dotProduct, Fin.sum_univ_two] using h2

def polytopeFixture : HPolytopeAnchor 2 (Fin 4) where
  normal := polytopeFixtureNormals
  bound := polytopeFixtureBounds
  bound_pos := by
    intro i
    fin_cases i <;> norm_num [polytopeFixtureBounds]
  normals_span := polytope_fixture_normals_span
  antipodal := by
    intro i
    fin_cases i
    · refine ⟨1, ?_, ?_⟩
      · ext j
        fin_cases j <;> simp [polytopeFixtureNormals]
      · simp [polytopeFixtureBounds]
    · refine ⟨0, ?_, ?_⟩
      · ext j
        fin_cases j <;> simp [polytopeFixtureNormals]
      · simp [polytopeFixtureBounds]
    · refine ⟨3, ?_, ?_⟩
      · ext j
        fin_cases j <;> simp [polytopeFixtureNormals]
      · simp [polytopeFixtureBounds]
    · refine ⟨2, ?_, ?_⟩
      · ext j
        fin_cases j <;> simp [polytopeFixtureNormals]
      · simp [polytopeFixtureBounds]

theorem polytope_fixture_exact :
    polytopeGauge polytopeFixture polytopeFixtureU = (1 : ℝ) / 2 := by
  apply le_antisymm
  · apply max_le
    · apply (finiteMax_le_iff
        (fun i =>
          dotProduct (polytopeFixture.normal i) polytopeFixtureU /
            polytopeFixture.bound i) ((1 : ℝ) / 2)).mpr
      intro i
      fin_cases i <;>
        norm_num [polytopeFixture, polytopeFixtureNormals,
          polytopeFixtureBounds, polytopeFixtureU, dotProduct,
          Fin.sum_univ_two]
    · norm_num
  · have hterm :
        dotProduct (polytopeFixture.normal 0) polytopeFixtureU /
            polytopeFixture.bound 0 ≤
          finiteMax (fun i =>
            dotProduct (polytopeFixture.normal i) polytopeFixtureU /
              polytopeFixture.bound i) :=
      le_finiteMax
        (fun i =>
          dotProduct (polytopeFixture.normal i) polytopeFixtureU /
            polytopeFixture.bound i) 0
    have hraw : (1 : ℝ) / 2 ≤ rawPolytopeGauge
        polytopeFixture polytopeFixtureU := by
      simpa [rawPolytopeGauge, polytopeFixture, polytopeFixtureNormals,
        polytopeFixtureBounds, polytopeFixtureU, dotProduct,
        Fin.sum_univ_two] using hterm
    exact hraw.trans (le_max_left _ _)

/-! ## One-way outer-envelope implication -/

def unitSublevel {V : Type*} (rho : V → ℝ) : Set V :=
  {u | rho u ≤ 1}

def outerEnvelopeViolation {V : Type*} (H : Set V)
    (rho : V → ℝ) : Set V :=
  {u | u ∈ H ∧ ¬rho u ≤ 1}

theorem one_way_outer_envelope {V : Type*} (H : Set V) (rho : V → ℝ)
    (hcontain : H ⊆ unitSublevel rho) :
    ∀ u, u ∈ H → rho u ≤ 1 := by
  intro u hu
  exact hcontain hu

theorem one_way_violation_empty {V : Type*} (H : Set V) (rho : V → ℝ)
    (hcontain : H ⊆ unitSublevel rho) :
    outerEnvelopeViolation H rho = ∅ := by
  ext u
  constructor
  · intro hu
    exact False.elim (hu.2 (one_way_outer_envelope H rho hcontain u hu.1))
  · simp

noncomputable def finiteViolationCount {V : Type*}
    (H : Finset V) (rho : V → ℝ) : ℕ := by
  classical
  exact (H.filter fun u => ¬rho u ≤ 1).card

theorem finite_violation_count_zero {V : Type*}
    (H : Finset V) (rho : V → ℝ)
    (h : ∀ u ∈ H, rho u ≤ 1) :
    finiteViolationCount H rho = 0 := by
  classical
  simpa [finiteViolationCount] using h

/-! ## Invertible response scaling -/

theorem invertible_scaling_rank {m n : Type*}
    [Fintype m] [Fintype n] [DecidableEq n]
    (R : Matrix m n ℝ) (D : Matrix n n ℝ) (hD : IsUnit D.det) :
    (R * D).rank = R.rank :=
  Matrix.rank_mul_eq_left_of_isUnit_det D R hD

theorem transformed_response_identity {m n : Type*}
    [Fintype m] [Fintype n] [DecidableEq n]
    (R : Matrix m n ℝ) (D : Matrix n n ℝ) (u : n → ℝ)
    (hD : IsUnit D.det) :
    R.mulVec u = (R * D).mulVec ((D⁻¹).mulVec u) := by
  symm
  calc
    (R * D).mulVec ((D⁻¹).mulVec u) =
        ((R * D) * D⁻¹).mulVec u := by
      rw [Matrix.mulVec_mulVec]
    _ = R.mulVec u := by
      rw [Matrix.mul_assoc, Matrix.mul_nonsing_inv D hD, Matrix.mul_one]

def rankFixtureR : Matrix (Fin 3) (Fin 2) ℝ :=
  !![(1 : ℝ), 2; 0, 1; 1, 0]

def rankFixtureD : Matrix (Fin 2) (Fin 2) ℝ :=
  !![(2 : ℝ), 1; 0, (1 : ℝ) / 2]

def rankFixtureS : Matrix (Fin 2) (Fin 2) ℝ :=
  !![(1 : ℝ), 2; 0, 1]

def firstTwoRows (i : Fin 2) : Fin 3 :=
  Fin.castLE (by decide) i

theorem rank_fixture_submatrix :
    rankFixtureR.submatrix firstTwoRows id = rankFixtureS := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [rankFixtureR, rankFixtureS, firstTwoRows]

theorem rank_fixture_S_det : rankFixtureS.det = 1 := by
  norm_num [rankFixtureS, Matrix.det_fin_two]

theorem rank_fixture_S_isUnit : IsUnit rankFixtureS.det := by
  rw [rank_fixture_S_det]
  exact isUnit_one

theorem rank_fixture_S_isUnit_matrix : IsUnit rankFixtureS :=
  rankFixtureS.isUnit_iff_isUnit_det.mpr rank_fixture_S_isUnit

theorem rank_fixture_S_exact : rankFixtureS.rank = 2 := by
  simpa using Matrix.rank_of_isUnit rankFixtureS rank_fixture_S_isUnit_matrix

theorem rank_fixture_R_exact : rankFixtureR.rank = 2 := by
  have hlower : 2 ≤ rankFixtureR.rank := by
    have hsub := Matrix.rank_submatrix_le rankFixtureR firstTwoRows id
    rw [rank_fixture_submatrix, rank_fixture_S_exact] at hsub
    exact hsub
  have hupper : rankFixtureR.rank ≤ 2 := by
    simpa using Matrix.rank_le_card_width rankFixtureR
  exact le_antisymm hupper hlower

theorem rank_fixture_D_det : rankFixtureD.det = 1 := by
  norm_num [rankFixtureD, Matrix.det_fin_two]

theorem rank_fixture_D_isUnit : IsUnit rankFixtureD.det := by
  rw [rank_fixture_D_det]
  exact isUnit_one

theorem rank_fixture_RD_exact :
    (rankFixtureR * rankFixtureD).rank = 2 := by
  rw [invertible_scaling_rank rankFixtureR rankFixtureD
      rank_fixture_D_isUnit,
    rank_fixture_R_exact]

/-! ## J1 exact outer-envelope counterexample -/

def symmetricInterval (r : ℝ) : Set ℝ := {x | |x| ≤ r}
def radiusGauge (r x : ℝ) : ℝ := |x| / r

def j1Physical : Set ℝ := symmetricInterval ((1 : ℝ) / 2)
def j1AnchorA : Set ℝ := symmetricInterval 1
def j1AnchorB : Set ℝ := symmetricInterval 2

theorem j1_outer_containments :
    j1Physical ⊆ j1AnchorA ∧ j1Physical ⊆ j1AnchorB := by
  constructor <;> intro x hx
  · change |x| ≤ (1 : ℝ) / 2 at hx
    change |x| ≤ (1 : ℝ)
    linarith
  · change |x| ≤ (1 : ℝ) / 2 at hx
    change |x| ≤ (2 : ℝ)
    linarith

theorem j1_anchor_a_not_physical : j1AnchorA ≠ j1Physical := by
  intro h
  have hx : (3 / 4 : ℝ) ∈ j1AnchorA := by
    norm_num [j1AnchorA, symmetricInterval]
  rw [h] at hx
  norm_num [j1Physical, symmetricInterval] at hx

theorem j1_anchor_b_not_physical : j1AnchorB ≠ j1Physical := by
  intro h
  have hx : (3 / 2 : ℝ) ∈ j1AnchorB := by
    norm_num [j1AnchorB, symmetricInterval]
  rw [h] at hx
  norm_num [j1Physical, symmetricInterval] at hx

theorem j1_rho_a_exact : radiusGauge 1 ((1 : ℝ) / 2) = 1 / 2 := by
  norm_num [radiusGauge]

theorem j1_rho_b_exact : radiusGauge 2 ((1 : ℝ) / 2) = 1 / 4 := by
  norm_num [radiusGauge]

theorem j1_counterexample :
    j1Physical ⊆ j1AnchorA ∧
    j1Physical ⊆ j1AnchorB ∧
    j1AnchorA ≠ j1Physical ∧
    j1AnchorB ≠ j1Physical ∧
    radiusGauge 1 ((1 : ℝ) / 2) ≠
      radiusGauge 2 ((1 : ℝ) / 2) := by
  refine ⟨j1_outer_containments.1, j1_outer_containments.2,
    j1_anchor_a_not_physical, j1_anchor_b_not_physical, ?_⟩
  rw [j1_rho_a_exact, j1_rho_b_exact]
  norm_num

/-! ## J2 exact dependence counterexample -/

def comonotoneNumerator : Bool → Rat
  | false => 1
  | true => 2

def comonotoneAnchor : Bool → Rat
  | false => 1
  | true => 2

def countermonotoneNumerator : Bool → Rat
  | false => 1
  | true => 2

def countermonotoneAnchor : Bool → Rat
  | false => 2
  | true => 1

def atomProbability (X : Bool → Rat) (value : Rat) : Rat :=
  ((if X false = value then 1 else 0) +
   (if X true = value then 1 else 0)) / 2

def exceedanceProbability (N B : Bool → Rat) : Rat :=
  ((if N false / B false > 1 then 1 else 0) +
   (if N true / B true > 1 then 1 else 0)) / 2

theorem j2_positive_atoms :
    (∀ b, 0 < comonotoneNumerator b ∧ 0 < comonotoneAnchor b) ∧
    (∀ b, 0 < countermonotoneNumerator b ∧
      0 < countermonotoneAnchor b) := by
  constructor <;> intro b <;> cases b <;> native_decide

theorem j2_same_marginals :
    atomProbability comonotoneNumerator 1 = 1 / 2 ∧
    atomProbability comonotoneNumerator 2 = 1 / 2 ∧
    atomProbability countermonotoneNumerator 1 = 1 / 2 ∧
    atomProbability countermonotoneNumerator 2 = 1 / 2 ∧
    atomProbability comonotoneAnchor 1 = 1 / 2 ∧
    atomProbability comonotoneAnchor 2 = 1 / 2 ∧
    atomProbability countermonotoneAnchor 1 = 1 / 2 ∧
    atomProbability countermonotoneAnchor 2 = 1 / 2 := by
  native_decide

theorem j2_comonotone_exceedance_exact :
    exceedanceProbability comonotoneNumerator comonotoneAnchor = 0 := by
  native_decide

theorem j2_countermonotone_exceedance_exact :
    exceedanceProbability countermonotoneNumerator
      countermonotoneAnchor = (1 : Rat) / 2 := by
  native_decide

theorem j2_dependence_counterexample :
    exceedanceProbability comonotoneNumerator comonotoneAnchor ≠
      exceedanceProbability countermonotoneNumerator
        countermonotoneAnchor := by
  rw [j2_comonotone_exceedance_exact,
    j2_countermonotone_exceedance_exact]
  norm_num

/-! ## Exact runner payload -/

def payload : String :=
  "{" ++
  "\"checks\":{" ++
    "\"product_ball_max_ratio\":true," ++
    "\"ellipsoid_unit_sublevel\":true," ++
    "\"polytope_unit_sublevel\":true," ++
    "\"one_way_outer_envelope\":true," ++
    "\"invertible_scaling_rank\":true," ++
    "\"transformed_response_identity\":true," ++
    "\"j1_counterexample\":true," ++
    "\"j2_dependence_counterexample\":true" ++
  "}," ++
  "\"domain_assumption_diff\":[]," ++
  "\"computed\":{" ++
    "\"product_gauge\":\"5/2\"," ++
    "\"ellipsoid_gauge_sq\":\"1\"," ++
    "\"polytope_gauge\":\"1/2\"," ++
    "\"rank_R\":\"2\"," ++
    "\"rank_RD\":\"2\"," ++
    "\"det_D\":\"1\"," ++
    "\"j1_rho_a\":\"1/2\"," ++
    "\"j1_rho_b\":\"1/4\"," ++
    "\"j2_comonotone_exceedance\":\"0\"," ++
    "\"j2_countermonotone_exceedance\":\"1/2\"," ++
    "\"one_way_violation_count\":\"0\"" ++
  "}," ++
  "\"counterexample\":null," ++
  "\"correlation_disclosure\":" ++
    "\"This axis was authored by the same GPT-5.6 model family available to " ++
    "other run roles; Lean kernel checking is engine evidence, not independent " ++
    "derivation authorship\"" ++
  "}"

def axisMain : IO Unit :=
  IO.println payload

end PR254R3LeanAxis

def main : IO Unit :=
  PR254R3LeanAxis.axisMain
