import Mathlib

/-!
CAS08 C01/C02 finite-dimensional real inner-product projection bridge.

`P L` is the actual orthogonal projection onto `(range L)ᗮ` as an ambient
continuous linear endomorphism. Mathlib's current subtype-valued API is
`orthogonalProjectionOnto` (the old `orthogonalProjection` is its deprecated
alias); `starProjection` is exactly its composition with the subtype inclusion.
No projector properties or least-squares premises are supplied as hypotheses.
No probability law, pseudoinverse formula, C03 decision, or science admission
is asserted here. The norm is the given real inner-product norm.
-/

noncomputable section

namespace CAS08ProjectionBridge

open scoped InnerProductSpace

variable {V E : Type*}
  [NormedAddCommGroup V] [InnerProductSpace ℝ V]
  [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [finV : FiniteDimensional ℝ V] [FiniteDimensional ℝ E]

include finV

-- Keep the packet's finite-V domain explicit although projection needs only finite E.
set_option linter.unusedSectionVars false

/-- The fitted-response subspace, with no full-rank assumption. -/
def responseRange (L : V →L[ℝ] E) : Submodule ℝ E :=
  LinearMap.range L.toLinearMap

/-- The residual subspace. -/
def K (L : V →L[ℝ] E) : Submodule ℝ E := (responseRange L)ᗮ

/-- The actual Mathlib orthogonal residual projector. -/
def P (L : V →L[ℝ] E) : E →L[ℝ] E := (K L).starProjection

/-- Explicit bridge to the subtype-valued orthogonal projection API. -/
theorem P_eq_subtype_projection (L : V →L[ℝ] E) :
    P L = (K L).subtypeL ∘L (K L).orthogonalProjectionOnto := rfl

theorem P_mem_K (L : V →L[ℝ] E) (x : E) : P L x ∈ K L :=
  (K L).starProjection_apply_mem x

/-- C01: nontrivial ambient-space projector idempotence. -/
theorem projector_idempotent (L : V →L[ℝ] E) (x : E) :
    P L (P L x) = P L x :=
  (K L).starProjection_eq_self_iff.mpr (P_mem_K L x)

theorem projector_comp_self (L : V →L[ℝ] E) : P L ∘L P L = P L := by
  ext x
  exact projector_idempotent L x

/-- C01: symmetry under the real inner product. -/
theorem projector_symmetric (L : V →L[ℝ] E) (x y : E) :
    ⟪P L x, y⟫_ℝ = ⟪x, P L y⟫_ℝ :=
  (K L).inner_starProjection_left_eq_right x y

theorem projector_selfAdjoint (L : V →L[ℝ] E) : IsSelfAdjoint (P L) :=
  isSelfAdjoint_starProjection (K L)

/-- C01: every fitted response is annihilated. -/
theorem projector_annihilates (L : V →L[ℝ] E) (v : V) : P L (L v) = 0 := by
  exact Submodule.starProjection_orthogonal_apply_eq_zero
    (K := responseRange L) ⟨v, rfl⟩

theorem projector_comp_response (L : V →L[ℝ] E) : P L ∘L L = 0 := by
  ext v
  exact projector_annihilates L v

/-- The residual is exactly the orthogonal complement projection. -/
theorem residual_identity (L : V →L[ℝ] E) (x : E) :
    P L x = x - (responseRange L).starProjection x := by
  simp only [P, K, Submodule.starProjection_orthogonal,
    sub_apply, ContinuousLinearMap.id_apply]

/-- C02: exact point-to-range distance, using Mathlib's metric `infDist`. -/
theorem least_squares_distance (L : V →L[ℝ] E) (x : E) :
    Metric.infDist x (responseRange L : Set E) = ‖P L x‖ := by
  rw [Metric.infDist_eq_iInf, residual_identity]
  simp_rw [dist_eq_norm]
  change (⨅ y : responseRange L, ‖x - (y : E)‖) =
    ‖x - (responseRange L).starProjection x‖
  exact ((responseRange L).starProjection_minimal x).symm

/-- A residual lower bound for every coefficient vector. -/
theorem least_squares_lower_bound (L : V →L[ℝ] E) (x : E) (v : V) :
    ‖P L x‖ ≤ ‖x - L v‖ := by
  rw [← least_squares_distance L x]
  simpa only [dist_eq_norm] using
    (Metric.infDist_le_dist_of_mem (s := (responseRange L : Set E)) ⟨v, rfl⟩
      : Metric.infDist x (responseRange L : Set E) ≤ dist x (L v))

/-- The minimum is attained even for rank-deficient or zero response maps. -/
theorem least_squares_attained (L : V →L[ℝ] E) (x : E) :
    ∃ v : V, x - L v = P L x ∧ ∀ w : V, ‖x - L v‖ ≤ ‖x - L w‖ := by
  obtain ⟨v, hv⟩ := (responseRange L).starProjection_apply_mem x
  change L v = (responseRange L).starProjection x at hv
  refine ⟨v, ?_, ?_⟩
  · rw [hv, ← residual_identity]
  · intro w
    rw [hv, ← residual_identity]
    exact least_squares_lower_bound L x w

/-- C02 complementary rank, stated as dimension of the actual projector range. -/
theorem complementary_rank (L : V →L[ℝ] E) :
    Module.finrank ℝ (LinearMap.range (P L).toLinearMap) +
      Module.finrank ℝ (responseRange L) = Module.finrank ℝ E := by
  rw [P, Submodule.range_starProjection]
  change Module.finrank ℝ ((responseRange L)ᗮ) + Module.finrank ℝ (responseRange L) =
    Module.finrank ℝ E
  rw [Nat.add_comm]
  exact (responseRange L).finrank_add_finrank_orthogonal

theorem complementary_rank_sub (L : V →L[ℝ] E) :
    Module.finrank ℝ (LinearMap.range (P L).toLinearMap) =
      Module.finrank ℝ E - Module.finrank ℝ (responseRange L) := by
  have h := complementary_rank L
  omega

/-- C02 covariance algebra component only: no Gaussian distribution is claimed. -/
theorem covariance_projector_algebra (L : V →L[ℝ] E) (x : E) :
    P L (P L x) = P L x := projector_idempotent L x

/-- The real transpose/adjoint covariance algebra identity. -/
theorem covariance_adjoint_algebra (L : V →L[ℝ] E) :
    P L ∘L (P L).adjoint = P L := by
  rw [ContinuousLinearMap.isSelfAdjoint_iff'.mp (projector_selfAdjoint L)]
  exact projector_comp_self L

/-- Zero-range boundary: every ambient vector is its own residual. -/
theorem zero_range_projector (L : V →L[ℝ] E) (h : responseRange L = ⊥) :
    P L = ContinuousLinearMap.id ℝ E := by
  ext x
  rw [residual_identity, h, Submodule.starProjection_bot]
  simp

/-- Full-range boundary: the residual vanishes. -/
theorem full_range_projector (L : V →L[ℝ] E) (h : responseRange L = ⊤) :
    P L = 0 := by
  simp only [P, K, h, Submodule.top_orthogonal_eq_bot, Submodule.starProjection_bot]

end CAS08ProjectionBridge

#check CAS08ProjectionBridge.P_eq_subtype_projection
#check CAS08ProjectionBridge.projector_idempotent
#check CAS08ProjectionBridge.projector_comp_self
#check CAS08ProjectionBridge.projector_symmetric
#check CAS08ProjectionBridge.projector_selfAdjoint
#check CAS08ProjectionBridge.projector_annihilates
#check CAS08ProjectionBridge.projector_comp_response
#check CAS08ProjectionBridge.residual_identity
#check CAS08ProjectionBridge.least_squares_distance
#check CAS08ProjectionBridge.least_squares_lower_bound
#check CAS08ProjectionBridge.least_squares_attained
#check CAS08ProjectionBridge.complementary_rank
#check CAS08ProjectionBridge.complementary_rank_sub
#check CAS08ProjectionBridge.covariance_projector_algebra
#check CAS08ProjectionBridge.covariance_adjoint_algebra
#check CAS08ProjectionBridge.zero_range_projector
#check CAS08ProjectionBridge.full_range_projector

#print axioms CAS08ProjectionBridge.P_eq_subtype_projection
#print axioms CAS08ProjectionBridge.projector_idempotent
#print axioms CAS08ProjectionBridge.projector_comp_self
#print axioms CAS08ProjectionBridge.projector_symmetric
#print axioms CAS08ProjectionBridge.projector_selfAdjoint
#print axioms CAS08ProjectionBridge.projector_annihilates
#print axioms CAS08ProjectionBridge.projector_comp_response
#print axioms CAS08ProjectionBridge.residual_identity
#print axioms CAS08ProjectionBridge.least_squares_distance
#print axioms CAS08ProjectionBridge.least_squares_lower_bound
#print axioms CAS08ProjectionBridge.least_squares_attained
#print axioms CAS08ProjectionBridge.complementary_rank
#print axioms CAS08ProjectionBridge.complementary_rank_sub
#print axioms CAS08ProjectionBridge.covariance_projector_algebra
#print axioms CAS08ProjectionBridge.covariance_adjoint_algebra
#print axioms CAS08ProjectionBridge.zero_range_projector
#print axioms CAS08ProjectionBridge.full_range_projector
