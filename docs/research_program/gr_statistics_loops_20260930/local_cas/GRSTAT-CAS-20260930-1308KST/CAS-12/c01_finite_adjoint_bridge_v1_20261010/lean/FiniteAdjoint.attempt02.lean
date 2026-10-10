import Mathlib.Analysis.InnerProductSpace.Adjoint

/-!
CAS12-C01 only: a fixed linear operator on an arbitrary finite-dimensional real
positive inner-product space. No continuum operator, weighted integral,
integrability, limit exchange, or physical collision identification is defined.
The retained subspace is supplied; no retention property is inferred for L.
-/

set_option autoImplicit false

namespace CAS12C01

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
  [FiniteDimensional ℝ E]

/-- A finite moment, with the same supplied positive inner product on both sides. -/
def moment (K f : E) : ℝ := inner ℝ K f

/-- The source states agree on every moment in the supplied retained subspace. -/
def RetainedEquivalent (V : Submodule ℝ E) (f g : E) : Prop :=
  ∀ K ∈ V, moment K f = moment K g

/-- The actual mathlib finite adjoint is constructed, rather than postulated. -/
theorem fixed_adjoint_identity (L : E →ₗ[ℝ] E) (K f : E) :
    moment K (L f) = moment (L.adjoint K) f := by
  exact (LinearMap.adjoint_inner_left L f K).symm

omit [FiniteDimensional ℝ E] in
theorem retained_equivalent_iff (V : Submodule ℝ E) (f g : E) :
    RetainedEquivalent V f g ↔ f - g ∈ Vᗮ := by
  simp only [RetainedEquivalent, moment, Submodule.mem_orthogonal, inner_sub_right]
  exact forall_congr' fun K => forall_congr' fun _ => (sub_eq_zero.symm)

/-- A retained adjoint kernel annihilates every perturbation invisible to V. -/
theorem retained_adjoint_annihilation (L : E →ₗ[ℝ] E)
    (V : Submodule ℝ E) (K h : E)
    (hK : L.adjoint K ∈ V) (hh : h ∈ Vᗮ) :
    moment K (L h) = 0 := by
  rw [fixed_adjoint_identity]
  exact V.inner_right_of_mem_orthogonal hK hh

/-- In finite dimension, membership of L* K in V is also necessary for
annihilation of ALL V-invisible perturbations. -/
theorem retained_adjoint_iff_annihilation (L : E →ₗ[ℝ] E)
    (V : Submodule ℝ E) (K : E) :
    L.adjoint K ∈ V ↔ ∀ h ∈ Vᗮ, moment K (L h) = 0 := by
  constructor
  · intro hK h hh
    exact retained_adjoint_annihilation L V K h hK hh
  · intro hzero
    have hdouble : L.adjoint K ∈ Vᗮᗮ := by
      apply (Vᗮ.mem_orthogonal' (L.adjoint K)).mpr
      intro h hh
      exact (fixed_adjoint_identity L K h).symm.trans (hzero h hh)
    simpa only [V.orthogonal_orthogonal] using hdouble

/-- Identical retained source moments yield the same output K moment exactly
when the supplied adjoint kernel lies in the retained subspace. -/
theorem retained_equivalent_output (L : E →ₗ[ℝ] E)
    (V : Submodule ℝ E) (K f g : E)
    (hK : L.adjoint K ∈ V) (hfg : RetainedEquivalent V f g) :
    moment K (L f) = moment K (L g) := by
  have hz := retained_adjoint_annihilation L V K (f - g) hK
    ((retained_equivalent_iff V f g).mp hfg)
  simpa only [LinearMap.map_sub, moment, inner_sub_right, sub_eq_zero] using hz

/-- Exact characterization using pairs of states, not only a single residual. -/
theorem retained_adjoint_iff_output (L : E →ₗ[ℝ] E)
    (V : Submodule ℝ E) (K : E) :
    L.adjoint K ∈ V ↔
      ∀ f g, RetainedEquivalent V f g → moment K (L f) = moment K (L g) := by
  constructor
  · intro hK f g hfg
    exact retained_equivalent_output L V K f g hK hfg
  · intro hout
    apply (retained_adjoint_iff_annihilation L V K).mpr
    intro h hh
    have heq : RetainedEquivalent V h 0 := by
      apply (retained_equivalent_iff V h 0).mpr
      simpa only [sub_zero] using hh
    simpa only [map_zero, moment, inner_zero_right] using hout h 0 heq

/-- Retention of ALL adjoint kernels in V propagates retained equivalence.
The preservation premise is explicit, and is not a claim about an unknown L. -/
theorem retained_subspace_preserves_moments (L : E →ₗ[ℝ] E)
    (V : Submodule ℝ E) (f g : E)
    (hretained : ∀ K ∈ V, L.adjoint K ∈ V)
    (hfg : RetainedEquivalent V f g) : RetainedEquivalent V (L f) (L g) := by
  intro K hK
  exact retained_equivalent_output L V K f g (hretained K hK) hfg

/-- Empty retained information is insufficient for an identity operator:
a nonzero K has a nonzero self moment. This is a universal negative control. -/
omit [FiniteDimensional ℝ E] in
theorem identity_nonzero_control (K : E) (hK : K ≠ 0) :
    moment K ((LinearMap.id : E →ₗ[ℝ] E) K) ≠ 0 := by
  change inner ℝ K K ≠ 0
  intro hz
  exact hK ((inner_self_eq_zero (𝕜 := ℝ)).mp hz)

/-- Zero operators and zero-dimensional spaces need no exceptional division. -/
omit [FiniteDimensional ℝ E] in
theorem zero_operator_control (K f : E) :
    moment K ((0 : E →ₗ[ℝ] E) f) = 0 := by
  simp [moment]

end CAS12C01

#eval IO.println "BEGIN_THEOREM_STATEMENTS"
#check @CAS12C01.fixed_adjoint_identity
#check @CAS12C01.retained_equivalent_iff
#check @CAS12C01.retained_adjoint_annihilation
#check @CAS12C01.retained_adjoint_iff_annihilation
#check @CAS12C01.retained_equivalent_output
#check @CAS12C01.retained_adjoint_iff_output
#check @CAS12C01.retained_subspace_preserves_moments
#check @CAS12C01.identity_nonzero_control
#check @CAS12C01.zero_operator_control
#eval IO.println "END_THEOREM_STATEMENTS"
#eval IO.println "BEGIN_AXIOM_AUDIT"
#print axioms CAS12C01.fixed_adjoint_identity
#print axioms CAS12C01.retained_equivalent_iff
#print axioms CAS12C01.retained_adjoint_annihilation
#print axioms CAS12C01.retained_adjoint_iff_annihilation
#print axioms CAS12C01.retained_equivalent_output
#print axioms CAS12C01.retained_adjoint_iff_output
#print axioms CAS12C01.retained_subspace_preserves_moments
#print axioms CAS12C01.identity_nonzero_control
#print axioms CAS12C01.zero_operator_control
#eval IO.println "END_AXIOM_AUDIT"
