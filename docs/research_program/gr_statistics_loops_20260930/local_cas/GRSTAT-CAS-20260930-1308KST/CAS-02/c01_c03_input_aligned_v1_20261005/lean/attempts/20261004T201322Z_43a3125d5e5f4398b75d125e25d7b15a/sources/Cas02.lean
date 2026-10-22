import Mathlib

/-!
CAS-02, frozen C01--C03 input alignment. All component norms below are positive
Euclidean sums of squares in the fixed observer frame.
-/

namespace Cas02

abbrev V3 := Fin 3 → ℝ
abbrev M3 := Fin 3 → Fin 3 → ℝ
abbrev V4 := Fin 4 → ℝ
abbrev M4 := Fin 4 → Fin 4 → ℝ

def vSq (v : V3) : ℝ := ∑ i, v i ^ 2
def fSq3 (m : M3) : ℝ := ∑ i, ∑ j, m i j ^ 2
def fSq4 (m : M4) : ℝ := ∑ i, ∑ j, m i j ^ 2

noncomputable def optical (h0 : ℝ) (h1 : V3) (h2 : M3) : M4 :=
  Fin.cases (Fin.cases h0 (fun j => -h1 j / 2))
    (fun i => Fin.cases (-h1 i / 2) (fun j => h2 i j))

def metric : M4 := fun i j => if i = j then (if i = 0 then -1 else 1) else 0

@[simp] theorem optical_00 (a : ℝ) (b : V3) (c : M3) : optical a b c 0 0 = a := rfl
@[simp] theorem optical_0s (a : ℝ) (b : V3) (c : M3) (j : Fin 3) :
    optical a b c 0 j.succ = -b j / 2 := rfl
@[simp] theorem optical_s0 (a : ℝ) (b : V3) (c : M3) (i : Fin 3) :
    optical a b c i.succ 0 = -b i / 2 := rfl
@[simp] theorem optical_ss (a : ℝ) (b : V3) (c : M3) (i j : Fin 3) :
    optical a b c i.succ j.succ = c i j := rfl

theorem optical_fSq (h0 : ℝ) (h1 : V3) (h2 : M3)
    (_hsym : ∀ i j, h2 i j = h2 j i) :
    fSq4 (optical h0 h1 h2) = h0 ^ 2 + vSq h1 / 2 + fSq3 h2 := by
  simp [fSq4, fSq3, vSq, Fin.sum_univ_succ]
  simp only [show (1 : Fin 4) = Fin.succ (0 : Fin 3) by decide,
    show (2 : Fin 4) = Fin.succ (1 : Fin 3) by decide,
    show (3 : Fin 4) = Fin.succ (2 : Fin 3) by decide,
    optical_0s, optical_ss]
  ring

theorem optical_sub (a0 b0 : ℝ) (a1 b1 : V3) (a2 b2 : M3) :
    (fun i j => optical b0 b1 b2 i j - optical a0 a1 a2 i j) =
      optical (b0 - a0) (fun i => b1 i - a1 i) (fun i j => b2 i j - a2 i j) := by
  funext i j
  refine Fin.cases ?_ (fun i => ?_) i
  · refine Fin.cases ?_ (fun j => ?_) j
    · simp [optical]
    · simp [optical]; ring
  · refine Fin.cases ?_ (fun j => ?_) j
    · simp [optical]; ring
    · simp [optical]

theorem C01 (a0 b0 : ℝ) (a1 b1 : V3) (a2 b2 : M3)
    (ha : ∀ i j, a2 i j = a2 j i) (hb : ∀ i j, b2 i j = b2 j i) :
    fSq4 (fun i j => optical b0 b1 b2 i j - optical a0 a1 a2 i j) =
      (b0 - a0) ^ 2 + vSq (fun i => b1 i - a1 i) / 2 +
        fSq3 (fun i j => b2 i j - a2 i j) := by
  rw [optical_sub]
  exact optical_fSq _ _ _ (fun i j => by rw [ha i j, hb i j])

theorem metric_fSq : fSq4 metric = 4 := by
  simp [fSq4, metric]

theorem metric_frob_norm : Real.sqrt (fSq4 metric) = 2 := by
  rw [metric_fSq]
  norm_num

def quad (S : M4) (u : V4) : ℝ := ∑ i, ∑ j, u i * S i j * u j

theorem quad_sub_matrix (S T : M4) (u : V4) :
    quad (fun i j => T i j - S i j) u = quad T u - quad S u := by
  simp [quad, mul_sub, sub_mul, Finset.sum_sub_distrib]

theorem quad_sub_vector (S : M4) (u v : V4) :
    quad S v - quad S u =
      (∑ i, ∑ j, (v i - u i) * S i j * v j) +
        (∑ i, ∑ j, u i * S i j * (v j - u j)) := by
  calc
    quad S v - quad S u = ∑ i, ∑ j,
        (v i * S i j * v j - u i * S i j * u j) := by
          simp [quad, Finset.sum_sub_distrib]
    _ = (∑ i, ∑ j, (v i - u i) * S i j * v j) +
        (∑ i, ∑ j, u i * S i j * (v j - u j)) := by
          rw [← Finset.sum_add_distrib]
          apply Finset.sum_congr rfl
          intro i hi
          rw [← Finset.sum_add_distrib]
          apply Finset.sum_congr rfl
          intro j hj
          ring

theorem C02_anchor_second (S T : M4) (u v : V4) :
    quad T v - quad S u =
      quad (fun i j => T i j - S i j) v +
        (∑ i, ∑ j, (v i - u i) * S i j * v j) +
          (∑ i, ∑ j, u i * S i j * (v j - u j)) := by
  calc
    quad T v - quad S u = (quad T v - quad S v) + (quad S v - quad S u) := by ring
    _ = _ := by rw [← quad_sub_matrix, quad_sub_vector]; ring

theorem C02_anchor_first (S T : M4) (u v : V4) :
    quad T v - quad S u =
      quad (fun i j => T i j - S i j) u +
        (∑ i, ∑ j, (v i - u i) * T i j * v j) +
          (∑ i, ∑ j, u i * T i j * (v j - u j)) := by
  calc
    quad T v - quad S u = (quad T u - quad S u) + (quad T v - quad T u) := by ring
    _ = _ := by rw [← quad_sub_matrix, quad_sub_vector]; ring

section Chart

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

noncomputable def chart (d : E) : ℝ × E := (Real.sqrt (1 + ‖d‖ ^ 2), d)

noncomputable def chartJac (d : E) : E →L[ℝ] ℝ × E :=
  (((1 / (2 * Real.sqrt (1 + ‖d‖ ^ 2))) • (2 • innerSL ℝ d)).prod
    (ContinuousLinearMap.id ℝ E))

theorem C03_hasFDerivAt (d : E) : HasFDerivAt chart (chartJac d) d := by
  have hq := ((hasFDerivAt_id d).norm_sq.const_add 1)
  have hp : (1 + ‖d‖ ^ 2) ≠ 0 := by positivity
  have hs := hq.sqrt hp
  have hi : HasFDerivAt (fun x : E => x) (ContinuousLinearMap.id ℝ E) d :=
    hasFDerivAt_id d
  change HasFDerivAt (fun x : E => (Real.sqrt (1 + ‖x‖ ^ 2), x)) (chartJac d) d
  simpa [chartJac] using hs.prodMk hi

theorem chartJac_apply (d h : E) :
    (chartJac d h).1 = inner ℝ d h / Real.sqrt (1 + ‖d‖ ^ 2) ∧
      (chartJac d h).2 = h := by
  have hp : 0 < Real.sqrt (1 + ‖d‖ ^ 2) := Real.sqrt_pos.2 (by positivity)
  constructor
  · simp only [chartJac, ContinuousLinearMap.prod_apply, smul_apply,
      ContinuousLinearMap.id_apply, smul_eq_mul, innerSL_apply_apply]
    field_simp
    ring
  · simp [chartJac]

noncomputable def chartGram (d h k : E) : ℝ :=
  (chartJac d h).1 * (chartJac d k).1 + inner ℝ (chartJac d h).2 (chartJac d k).2

theorem C03_gram (d h k : E) :
    chartGram d h k = inner ℝ h k +
      inner ℝ d h * inner ℝ d k / (1 + ‖d‖ ^ 2) := by
  rcases chartJac_apply d h with ⟨hh, hh'⟩
  rcases chartJac_apply d k with ⟨hk, hk'⟩
  simp only [chartGram, hh, hk, hh', hk']
  have hp : 0 < 1 + ‖d‖ ^ 2 := by positivity
  have hs : Real.sqrt (1 + ‖d‖ ^ 2) ^ 2 = 1 + ‖d‖ ^ 2 :=
    Real.sq_sqrt (le_of_lt hp)
  have hn : Real.sqrt (1 + ‖d‖ ^ 2) ≠ 0 := ne_of_gt (Real.sqrt_pos.2 hp)
  calc
    inner ℝ d h / Real.sqrt (1 + ‖d‖ ^ 2) *
        (inner ℝ d k / Real.sqrt (1 + ‖d‖ ^ 2)) + inner ℝ h k =
      inner ℝ h k + inner ℝ d h * inner ℝ d k /
        Real.sqrt (1 + ‖d‖ ^ 2) ^ 2 := by field_simp; ring
    _ = _ := by rw [hs]

noncomputable def gramVec (d h : E) : E :=
  h + (inner ℝ d h / (1 + ‖d‖ ^ 2)) • d

theorem C03_gram_action (d h k : E) :
    inner ℝ (gramVec d h) k = chartGram d h k := by
  rw [C03_gram]
  simp [gramVec, inner_add_left, real_inner_smul_left]
  ring

theorem C03_transverse (d h : E) (ho : inner ℝ d h = 0) : gramVec d h = h := by
  simp [gramVec, ho]

theorem C03_transverse_iff (d h : E) (hd : d ≠ 0) :
    gramVec d h = h ↔ inner ℝ d h = 0 := by
  constructor
  · intro he
    have hs : (inner ℝ d h / (1 + ‖d‖ ^ 2)) • d = 0 := by
      simpa only [gramVec, add_eq_left] using he
    have hq : inner ℝ d h / (1 + ‖d‖ ^ 2) = 0 :=
      (smul_eq_zero.mp hs).resolve_right hd
    have hp : (1 + ‖d‖ ^ 2) ≠ 0 := by positivity
    exact (div_eq_zero_iff).mp hq |>.resolve_right hp
  · exact C03_transverse d h

theorem C03_longitudinal (d : E) :
    gramVec d d = (1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2)) • d := by
  simp [gramVec, add_smul]

theorem gramVec_smul (d h : E) (a : ℝ) :
    gramVec d (a • h) = a • gramVec d h := by
  simp [gramVec, inner_smul_right, smul_add, smul_smul]
  ring

theorem C03_longitudinal_span (d : E) (a : ℝ) :
    gramVec d (a • d) = (1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2)) • (a • d) := by
  rw [gramVec_smul, C03_longitudinal]
  simp [smul_smul, mul_comm]

theorem C03_zero_repeated (h : E) : gramVec (0 : E) h = h := by
  simp [gramVec]

theorem C03_eigenvalue_only (d h : E) (eig : ℝ) (hh : h ≠ 0)
    (he : gramVec d h = eig • h) :
    eig = 1 ∨ eig = 1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2) := by
  by_cases ho : inner ℝ d h = 0
  · left
    have he' : h = eig • h := (C03_transverse d h ho).symm.trans he
    have hz : (eig - 1) • h = 0 := by
      rw [sub_smul, one_smul]
      exact sub_eq_zero.mpr he'.symm
    have := (smul_eq_zero.mp hz).resolve_right hh
    linarith
  · right
    have hp : (1 + ‖d‖ ^ 2) ≠ 0 := by positivity
    have he' := congrArg (fun x : E => inner ℝ d x) he
    simp only [gramVec, inner_add_right, real_inner_smul_right,
      real_inner_self_eq_norm_sq] at he'
    have hc : (1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2)) * inner ℝ d h =
        eig * inner ℝ d h := by
      calc
        _ = inner ℝ d h + inner ℝ d h / (1 + ‖d‖ ^ 2) * ‖d‖ ^ 2 := by ring
        _ = eig * inner ℝ d h := by simpa only [smul_eq_mul] using he'
    exact (mul_right_cancel₀ ho hc).symm

theorem ratio_mono {a b : ℝ} (ha : 0 ≤ a) (hab : a ≤ b) :
    a / (1 + a) ≤ b / (1 + b) := by
  have h1 : 0 < 1 + a := by linarith
  have h2 : 0 < 1 + b := by linarith
  apply (div_le_div_iff₀ h1 h2).2
  nlinarith

theorem C03_rapidity_bound (d : E) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2) ≤ 1 + Real.tanh R ^ 2 := by
  have hsinh : 0 ≤ Real.sinh R := le_trans (norm_nonneg _) hd
  have hR : 0 ≤ R := Real.sinh_nonneg_iff.mp hsinh
  have hsq : ‖d‖ ^ 2 ≤ Real.sinh R ^ 2 :=
    sq_le_sq₀ (norm_nonneg _) hsinh |>.2 hd
  have hratio := ratio_mono (sq_nonneg ‖d‖) hsq
  have hc : 1 + Real.sinh R ^ 2 = Real.cosh R ^ 2 := by
    nlinarith [Real.cosh_sq_sub_sinh_sq R]
  have hcosh : Real.cosh R ≠ 0 := ne_of_gt (Real.cosh_pos R)
  have ht : Real.sinh R ^ 2 / (1 + Real.sinh R ^ 2) = Real.tanh R ^ 2 := by
    rw [hc, Real.tanh_eq_sinh_div_cosh]
    field_simp
  rw [← ht]
  linarith

end Chart

abbrev Euclidean3 := EuclideanSpace ℝ (Fin 3)

theorem C03_transverse_dimension (d : Euclidean3) (hd : d ≠ 0) :
    Module.finrank ℝ (ℝ ∙ d)ᗮ = 2 := by
  letI : Fact (Module.finrank ℝ Euclidean3 = 2 + 1) := ⟨by simp [Euclidean3]⟩
  exact Submodule.finrank_orthogonal_span_singleton (n := 2) hd

theorem C03_longitudinal_dimension (d : Euclidean3) (hd : d ≠ 0) :
    Module.finrank ℝ (ℝ ∙ d) = 1 := by
  exact finrank_span_singleton hd

theorem C03_zero_dimension : Module.finrank ℝ Euclidean3 = 3 := by
  simp [Euclidean3]

theorem C03_transverse_eigen_exists (d : Euclidean3) (hd : d ≠ 0) :
    ∃ h : Euclidean3, h ≠ 0 ∧ gramVec d h = h := by
  have hdim := C03_transverse_dimension d hd
  have hpos : 0 < Module.finrank ℝ (ℝ ∙ d)ᗮ := by omega
  obtain ⟨v, hv⟩ := Module.finrank_pos_iff_exists_ne_zero.mp hpos
  refine ⟨v, ?_, ?_⟩
  · intro hz
    apply hv
    exact Subtype.ext hz
  · exact C03_transverse d v (Submodule.mem_orthogonal_singleton_iff_inner_right.mp v.property)

end Cas02

#print axioms Cas02.C01
#print axioms Cas02.metric_frob_norm
#print axioms Cas02.C02_anchor_second
#print axioms Cas02.C02_anchor_first
#print axioms Cas02.C03_hasFDerivAt
#print axioms Cas02.chartJac_apply
#print axioms Cas02.C03_gram
#print axioms Cas02.C03_gram_action
#print axioms Cas02.C03_transverse_iff
#print axioms Cas02.C03_longitudinal_span
#print axioms Cas02.C03_eigenvalue_only
#print axioms Cas02.C03_zero_repeated
#print axioms Cas02.C03_rapidity_bound
#print axioms Cas02.C03_transverse_dimension
#print axioms Cas02.C03_longitudinal_dimension
#print axioms Cas02.C03_zero_dimension
#print axioms Cas02.C03_transverse_eigen_exists
