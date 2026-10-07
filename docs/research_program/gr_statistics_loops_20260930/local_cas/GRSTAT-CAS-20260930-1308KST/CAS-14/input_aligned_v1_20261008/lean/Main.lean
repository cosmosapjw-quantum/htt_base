import Mathlib

open Matrix BigOperators

namespace CAS14

abbrev V := Fin 3 → ℝ

def W (ω x : V) : V :=
  ![ω 2 * x 1 - ω 1 * x 2,
    ω 0 * x 2 - ω 2 * x 0,
    ω 1 * x 0 - ω 0 * x 1]

def P (x v : V) : V := v - (x ⬝ᵥ v) • x

theorem W_sign (ω x : V) : W ω x = -(ω ⨯₃ x) := by
  simp [W, cross_apply, Matrix.vec3_eq]

theorem C01_cross_projection (x ω : V) (hx : x ⬝ᵥ x = 1) :
    x ⨯₃ (ω ⨯₃ x) = P x ω := by
  rw [cross_cross_eq_smul_sub_smul', hx, one_smul, dotProduct_comm]
  rfl

theorem C01_cross_data (x ω : V) (hx : x ⬝ᵥ x = 1) :
    x ⨯₃ (-W ω x) = P x ω := by
  rw [W_sign, neg_neg]
  exact C01_cross_projection x ω hx

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

def G (w : ι → ℝ) (x : ι → V) (v : V) : V :=
  ∑ i, (w i) • P (x i) v

noncomputable def Astack (w : ι → ℝ) (x : ι → V) (v : V) (i : ι) : V :=
  Real.sqrt (w i) • (x i ⨯₃ v)

def b (w : ι → ℝ) (x y : ι → V) : V :=
  ∑ i, (w i) • (x i ⨯₃ y i)

theorem C01_b_eq_G (w : ι → ℝ) (x : ι → V) (ω : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) :
    b w x (fun i => -W ω (x i)) = G w x ω := by
  simp only [b, G]
  apply Finset.sum_congr rfl
  intro i _
  rw [C01_cross_data (x i) ω (hx i)]

theorem dot_P_eq_cross_sq (x v : V) (hx : x ⬝ᵥ x = 1) :
    v ⬝ᵥ P x v = (v ⨯₃ x) ⬝ᵥ (v ⨯₃ x) := by
  rw [P, dotProduct_sub, dotProduct_smul, cross_dot_cross, hx]
  ring

theorem C02_gram (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) :
    v ⬝ᵥ G w x v = ∑ i, w i * ((v ⨯₃ x i) ⬝ᵥ (v ⨯₃ x i)) := by
  rw [G, dotProduct_sum]
  apply Finset.sum_congr rfl
  intro i _
  rw [dotProduct_smul, dot_P_eq_cross_sq (x i) v (hx i)]
  rfl

theorem C02_stack_normal (w : ι → ℝ) (x : ι → V) (v u : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 ≤ w i) :
    (∑ i, Astack w x v i ⬝ᵥ Astack w x u i) = v ⬝ᵥ G w x u := by
  rw [G, dotProduct_sum]
  apply Finset.sum_congr rfl
  intro i _
  simp only [Astack, dotProduct_smul, smul_dotProduct, P, dotProduct_sub]
  rw [cross_dot_cross, hx i]
  simp only [smul_eq_mul, one_mul]
  rw [← mul_assoc, ← pow_two]
  rw [Real.sq_sqrt (hw i)]

theorem cross_zero_iff_span_unit (x v : V) (hx : x ⬝ᵥ x = 1) :
    v ⨯₃ x = 0 ↔ v ∈ Submodule.span ℝ {x} := by
  constructor
  · intro h
    have h' : v = (x ⬝ᵥ v) • x := by
      have htrip := C01_cross_projection x v hx
      rw [h] at htrip
      simp [P] at htrip
      exact sub_eq_zero.mp htrip.symm
    rw [h']
    exact Submodule.smul_mem _ _ (Submodule.subset_span (Set.mem_singleton x))
  · intro h
    obtain ⟨a, rfl⟩ := Submodule.mem_span_singleton.mp h
    simp [cross_apply, smul_eq_mul, mul_assoc, mul_comm, mul_left_comm]

theorem cross_sq_nonneg (v x : V) :
    0 ≤ (v ⨯₃ x) ⬝ᵥ (v ⨯₃ x) := by
  unfold dotProduct
  exact Finset.sum_nonneg (fun i _ => mul_self_nonneg _)

theorem C02_gram_nonneg (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i) :
    0 ≤ v ⬝ᵥ G w x v := by
  rw [C02_gram w x v hx]
  exact Finset.sum_nonneg (fun i _ => mul_nonneg (le_of_lt (hw i)) (cross_sq_nonneg v (x i)))

theorem C02_kernel_cross (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i) :
    G w x v = 0 ↔ ∀ i, v ⨯₃ x i = 0 := by
  constructor
  · intro h i
    have hsum : ∑ j, w j * ((v ⨯₃ x j) ⬝ᵥ (v ⨯₃ x j)) = 0 := by
      rw [← C02_gram w x v hx, h, dotProduct_zero]
    have hi := (Finset.sum_eq_zero_iff_of_nonneg
      (s := Finset.univ) (f := fun j => w j * ((v ⨯₃ x j) ⬝ᵥ (v ⨯₃ x j)))
      (fun j _ => mul_nonneg (le_of_lt (hw j)) (cross_sq_nonneg v (x j)))).mp hsum i (Finset.mem_univ i)
    have hsq : (v ⨯₃ x i) ⬝ᵥ (v ⨯₃ x i) = 0 := (mul_eq_zero.mp hi).resolve_left (ne_of_gt (hw i))
    exact dotProduct_self_eq_zero.mp hsq
  · intro h
    -- The Gram vector itself vanishes termwise when each cross product vanishes.
    rw [G]
    apply Finset.sum_eq_zero
    intro i _
    have hP : P (x i) v = 0 := by
      have htrip := C01_cross_projection (x i) v (hx i)
      rw [h i] at htrip
      simpa using htrip.symm
    simp [hP]

theorem C02_kernel_intersection (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i) :
    G w x v = 0 ↔ ∀ i, v ∈ Submodule.span ℝ {x i} := by
  rw [C02_kernel_cross w x v hx hw]
  exact forall_congr' (fun i => cross_zero_iff_span_unit (x i) v (hx i))

theorem C02_all_parallel_control (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i₀ : ι) (hparallel : ∀ i, Submodule.span ℝ {x i} = Submodule.span ℝ {x i₀}) :
    G w x v = 0 ↔ v ∈ Submodule.span ℝ {x i₀} := by
  rw [C02_kernel_intersection w x v hx hw]
  constructor
  · intro h
    exact h i₀
  · intro h i
    rw [hparallel i]
    exact h

theorem C02_two_nonparallel_kernel_zero (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i j : ι) (hij : x i ⨯₃ x j ≠ 0)
    (hG : G w x v = 0) : v = 0 := by
  have hcross := (C02_kernel_cross w x v hx hw).mp hG
  have hP : v = (x i ⬝ᵥ v) • x i := by
    have ht := C01_cross_projection (x i) v (hx i)
    rw [hcross i] at ht
    simp [P] at ht
    exact sub_eq_zero.mp ht.symm
  have hs : (x i ⬝ᵥ v) = 0 := by
    have h : (x i ⬝ᵥ v) • (x i ⨯₃ x j) = 0 := by
      calc
        (x i ⬝ᵥ v) • (x i ⨯₃ x j) = ((x i ⬝ᵥ v) • x i) ⨯₃ x j := by simp
        _ = v ⨯₃ x j := by rw [← hP]
        _ = 0 := hcross j
    exact (smul_eq_zero.mp h).resolve_right hij
  simpa [hs] using hP

theorem C02_two_nonparallel_pos (w : ι → ℝ) (x : ι → V) (v : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i j : ι) (hij : x i ⨯₃ x j ≠ 0) (hv : v ≠ 0) :
    0 < v ⬝ᵥ G w x v := by
  have hnn := C02_gram_nonneg w x v hx hw
  rcases eq_or_lt_of_le hnn with hzero | hpos
  · have hsum : ∑ k, w k * ((v ⨯₃ x k) ⬝ᵥ (v ⨯₃ x k)) = 0 := by
      rw [← C02_gram w x v hx, ← hzero]
    have hcross : ∀ k, v ⨯₃ x k = 0 := by
      intro k
      have hk := (Finset.sum_eq_zero_iff_of_nonneg
        (s := Finset.univ) (f := fun l => w l * ((v ⨯₃ x l) ⬝ᵥ (v ⨯₃ x l)))
        (fun l _ => mul_nonneg (le_of_lt (hw l)) (cross_sq_nonneg v (x l)))).mp hsum k (Finset.mem_univ k)
      exact dotProduct_self_eq_zero.mp ((mul_eq_zero.mp hk).resolve_left (ne_of_gt (hw k)))
    have hG : G w x v = 0 := (C02_kernel_cross w x v hx hw).mpr hcross
    exact False.elim (hv (C02_two_nonparallel_kernel_zero w x v hx hw i j hij hG))
  · exact hpos

def Glin (w : ι → ℝ) (x : ι → V) : V →ₗ[ℝ] V where
  toFun := G w x
  map_add' v u := by
    simp only [G, P, dotProduct_add, smul_add]
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    module
  map_smul' a v := by
    simp only [G, P, dotProduct_smul, smul_sub, smul_smul, RingHom.id_apply]
    rw [Finset.smul_sum]
    apply Finset.sum_congr rfl
    intro i _
    module

theorem C02_two_nonparallel_injective (w : ι → ℝ) (x : ι → V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i j : ι) (hij : x i ⨯₃ x j ≠ 0) :
    Function.Injective (Glin w x) := by
  rw [← LinearMap.ker_eq_bot, LinearMap.ker_eq_bot']
  intro v hv
  exact C02_two_nonparallel_kernel_zero w x v hx hw i j hij
    (show G w x v = 0 from hv)

noncomputable def G_equiv (w : ι → ℝ) (x : ι → V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i j : ι) (hij : x i ⨯₃ x j ≠ 0) : V ≃ₗ[ℝ] V :=
  LinearEquiv.ofBijective (Glin w x)
    ⟨C02_two_nonparallel_injective w x hx hw i j hij,
      LinearMap.injective_iff_surjective.mp
        (C02_two_nonparallel_injective w x hx hw i j hij)⟩

theorem C02_inverse_formula (w : ι → ℝ) (x : ι → V) (ω : V)
    (hx : ∀ i, x i ⬝ᵥ x i = 1) (hw : ∀ i, 0 < w i)
    (i j : ι) (hij : x i ⨯₃ x j ≠ 0) :
    (G_equiv w x hx hw i j hij).symm
      (b w x (fun k => -W ω (x k))) = ω := by
  rw [C01_b_eq_G w x ω hx]
  exact (G_equiv w x hx hw i j hij).symm_apply_apply ω

section Pseudoinverse

variable {F : Type*} [NormedAddCommGroup F] [InnerProductSpace ℝ F]
  [FiniteDimensional ℝ F]

abbrev E := EuclideanSpace ℝ (Fin 3)

noncomputable def mpInv (A : E →L[ℝ] F) (hA : Function.Injective A) : F → E :=
  fun y => (LinearEquiv.ofInjective A.toLinearMap hA).symm
    ((LinearMap.range A.toLinearMap).orthogonalProjectionOnto y)

theorem mpInv_left (A : E →L[ℝ] F) (hA : Function.Injective A) (v : E) :
    mpInv A hA (A v) = v := by
  let R := LinearMap.range A.toLinearMap
  let e := LinearEquiv.ofInjective A.toLinearMap hA
  have hp : R.orthogonalProjectionOnto (A v) = e v := by
    apply Subtype.ext
    change R.starProjection (A v) = A v
    exact R.starProjection_eq_self_iff.mpr (LinearMap.mem_range_self A.toLinearMap v)
  change e.symm (R.orthogonalProjectionOnto (A v)) = v
  rw [hp]
  exact e.symm_apply_apply v

theorem mpInv_projection (A : E →L[ℝ] F) (hA : Function.Injective A) (y : F) :
    A (mpInv A hA y) = (LinearMap.range A.toLinearMap).starProjection y := by
  let R := LinearMap.range A.toLinearMap
  let e := LinearEquiv.ofInjective A.toLinearMap hA
  have he := e.apply_symm_apply (R.orthogonalProjectionOnto y)
  exact congrArg Subtype.val he

theorem mpInv_bound (A : E →L[ℝ] F) (hA : Function.Injective A)
    (σ : ℝ) (hσ : 0 < σ)
    (hlower : ∀ v : E, σ * ‖v‖ ≤ ‖A v‖) (y : F) :
    ‖mpInv A hA y‖ ≤ ‖y‖ / σ := by
  have h := hlower (mpInv A hA y)
  rw [mpInv_projection A hA y] at h
  have hp := (LinearMap.range A.toLinearMap).norm_starProjection_apply_le y
  exact (le_div_iff₀ hσ).mpr (by simpa [mul_comm] using h.trans hp)

theorem mpInv_add (A : E →L[ℝ] F) (hA : Function.Injective A) (y z : F) :
    mpInv A hA (y + z) = mpInv A hA y + mpInv A hA z := by
  simp [mpInv, map_add]

theorem C03_exact_bound (A : E →L[ℝ] F) (hA : Function.Injective A)
    (σ ε : ℝ) (hσ : 0 < σ) (hε : 0 ≤ ε)
    (hlower : ∀ v : E, σ * ‖v‖ ≤ ‖A v‖)
    (ω : E) (e : F) (he : ‖e‖ ≤ ε) :
    ‖mpInv A hA (A ω + e) - ω‖ ≤ ε / σ := by
  rw [mpInv_add, mpInv_left, add_sub_cancel_left]
  exact (mpInv_bound A hA σ hσ hlower e).trans (div_le_div_of_nonneg_right he hσ.le)

theorem C03_perturbed_bound (A Ahat : E →L[ℝ] F)
    (hAhat : Function.Injective Ahat)
    (σhat εy εA Ω : ℝ)
    (hσ : 0 < σhat) (hεy : 0 ≤ εy) (hεA : 0 ≤ εA) (hΩ : 0 ≤ Ω)
    (hlower : ∀ v : E, σhat * ‖v‖ ≤ ‖Ahat v‖)
    (hop : ‖Ahat - A‖ ≤ εA)
    (ω : E) (hω : ‖ω‖ ≤ Ω)
    (e : F) (he : ‖e‖ ≤ εy) :
    ‖mpInv Ahat hAhat (A ω + e) - ω‖ ≤ (εy + εA * Ω) / σhat := by
  have hrewrite : A ω + e = Ahat ω + ((A - Ahat) ω + e) := by
    simp only [ContinuousLinearMap.sub_apply]
    abel
  rw [hrewrite, mpInv_add, mpInv_left, add_sub_cancel_left]
  have hop' : ‖A - Ahat‖ ≤ εA := by simpa [norm_sub_rev] using hop
  have hpert : ‖(A - Ahat) ω‖ ≤ εA * Ω := by
    calc
      ‖(A - Ahat) ω‖ ≤ ‖A - Ahat‖ * ‖ω‖ := ContinuousLinearMap.le_opNorm _ _
      _ ≤ εA * Ω := mul_le_mul hop' hω (norm_nonneg _) hεA
  have hnoise : ‖(A - Ahat) ω + e‖ ≤ εy + εA * Ω := by
    calc
      ‖(A - Ahat) ω + e‖ ≤ ‖(A - Ahat) ω‖ + ‖e‖ := norm_add_le _ _
      _ ≤ εy + εA * Ω := by linarith
  exact (mpInv_bound Ahat hAhat σhat hσ hlower _).trans
    (div_le_div_of_nonneg_right hnoise hσ.le)

theorem C03_zero_data_error (A : E →L[ℝ] F) (hA : Function.Injective A) (ω : E) :
    mpInv A hA (A ω) - ω = 0 := by
  rw [mpInv_left, sub_self]

theorem C03_zero_operator_error (A : E →L[ℝ] F) (hA : Function.Injective A)
    (σ ε : ℝ) (hσ : 0 < σ) (hε : 0 ≤ ε)
    (hlower : ∀ v : E, σ * ‖v‖ ≤ ‖A v‖)
    (ω : E) (e : F) (he : ‖e‖ ≤ ε) :
    ‖mpInv A hA (A ω + e) - ω‖ ≤ ε / σ :=
  C03_exact_bound A hA σ ε hσ hε hlower ω e he

end Pseudoinverse

def Wmat (ω : V) : Matrix (Fin 3) (Fin 3) ℝ :=
  !![0, ω 2, -ω 1; -ω 2, 0, ω 0; ω 1, -ω 0, 0]

def frobSq (ω : V) : ℝ := ∑ i : Fin 3, ∑ j : Fin 3, (Wmat ω i j) ^ 2

theorem C03_frobenius_sq (δω : V) : frobSq δω = 2 * (δω ⬝ᵥ δω) := by
  simp [frobSq, Wmat, Fin.sum_univ_succ, vec3_dotProduct]
  ring

theorem C03_frobenius (δω : V) :
    Real.sqrt (frobSq δω) = Real.sqrt 2 * Real.sqrt (δω ⬝ᵥ δω) := by
  rw [C03_frobenius_sq, Real.sqrt_mul (by norm_num : (0 : ℝ) ≤ 2)]

theorem Wmat_mulVec (ω x : V) : (Wmat ω).mulVec x = W ω x := by
  ext k
  fin_cases k <;>
    simp [Wmat, W, Matrix.mulVec, dotProduct, Fin.sum_univ_succ] <;> ring

def e₁ : V := ![1, 0, 0]
def e₂ : V := ![0, 1, 0]

theorem C02_e1_e2_control (w₁ w₂ : ℝ) (v : V) :
    G ![w₁, w₂] ![e₁, e₂] v =
      ![w₂ * v 0, w₁ * v 1, (w₁ + w₂) * v 2] := by
  ext k
  fin_cases k <;>
    simp [G, P, e₁, e₂, Fin.sum_univ_succ, vec3_dotProduct] <;> ring

theorem C03_no_amplitude_control (C : ℝ) :
    ∃ ω : ℝ, |(ω / 2) - ω| > C := by
  refine ⟨2 * (|C| + 1), ?_⟩
  have h : 0 < |C| + 1 := by positivity
  have hC : C ≤ |C| := le_abs_self C
  have heq : (2 * (|C| + 1)) / 2 - 2 * (|C| + 1) = -(|C| + 1) := by ring
  rw [heq, abs_neg, abs_of_pos h]
  linarith

#print axioms CAS14.W_sign
#print axioms CAS14.C01_cross_data
#print axioms CAS14.C01_b_eq_G
#print axioms CAS14.C02_stack_normal
#print axioms CAS14.C02_kernel_intersection
#print axioms CAS14.C02_all_parallel_control
#print axioms CAS14.C02_two_nonparallel_pos
#print axioms CAS14.C02_inverse_formula
#print axioms CAS14.C02_e1_e2_control
#print axioms CAS14.C03_exact_bound
#print axioms CAS14.C03_perturbed_bound
#print axioms CAS14.C03_zero_data_error
#print axioms CAS14.C03_zero_operator_error
#print axioms CAS14.C03_frobenius
#print axioms CAS14.C03_no_amplitude_control

end CAS14
