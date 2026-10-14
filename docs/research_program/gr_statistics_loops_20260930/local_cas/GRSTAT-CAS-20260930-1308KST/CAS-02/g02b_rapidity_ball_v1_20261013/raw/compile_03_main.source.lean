import Cas02
import InverseBound

/-!
G02-B: rapidity-ball operator bound, closed Euclidean ball projection and
mean-value Lipschitz composition into the C04 finite inverse bound.

Imports the reviewed C01-C03 source `Cas02` and the C04 source `InverseBound`
unchanged. All vector norms are positive Euclidean observer component norms;
matrix norms on `CAS02C04.Mat4` are Frobenius (same scope as C04). No Lorentz or
indefinite form is used in any inequality. Nothing here asserts physical
admissibility of a supplied (off-shell) dipole or of the clipped output.
-/

open scoped Matrix.Norms.Frobenius

namespace G02B

section General

variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]

/-- Largest eigenvalue of the actual chart-derivative Gram operator. -/
noncomputable def lamMax (d : E) : ℝ := 1 + ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2)

theorem one_le_lamMax (d : E) : 1 ≤ lamMax d := by
  unfold lamMax
  have : 0 ≤ ‖d‖ ^ 2 / (1 + ‖d‖ ^ 2) := by positivity
  linarith

theorem lamMax_zero : lamMax (0 : E) = 1 := by simp [lamMax]

/-! ### T1: Gram quadratic form, maximum eigenvalue -/

theorem gram_quad_eq (d h : E) :
    Cas02.chartGram d h h = ‖h‖ ^ 2 + (inner ℝ d h) ^ 2 / (1 + ‖d‖ ^ 2) := by
  rw [Cas02.C03_gram, real_inner_self_eq_norm_sq]
  ring

theorem gram_quad_le (d h : E) : Cas02.chartGram d h h ≤ lamMax d * ‖h‖ ^ 2 := by
  rw [gram_quad_eq]
  have hp : 0 < 1 + ‖d‖ ^ 2 := by positivity
  have hcs : (inner ℝ d h) ^ 2 ≤ ‖d‖ ^ 2 * ‖h‖ ^ 2 := by
    have h1 := abs_real_inner_le_norm d h
    calc (inner ℝ d h) ^ 2 = |inner ℝ d h| ^ 2 := (sq_abs _).symm
      _ ≤ (‖d‖ * ‖h‖) ^ 2 := pow_le_pow_left₀ (abs_nonneg _) h1 2
      _ = ‖d‖ ^ 2 * ‖h‖ ^ 2 := by ring
  have h2 : (inner ℝ d h) ^ 2 / (1 + ‖d‖ ^ 2) ≤ ‖d‖ ^ 2 * ‖h‖ ^ 2 / (1 + ‖d‖ ^ 2) :=
    div_le_div_of_nonneg_right hcs hp.le
  have e : lamMax d * ‖h‖ ^ 2 = ‖h‖ ^ 2 + ‖d‖ ^ 2 * ‖h‖ ^ 2 / (1 + ‖d‖ ^ 2) := by
    rw [lamMax, add_mul, one_mul, div_mul_eq_mul_div]
  rw [e]
  linarith

theorem gram_eig_le (d h : E) (eig : ℝ) (hh : h ≠ 0)
    (he : Cas02.gramVec d h = eig • h) : eig ≤ lamMax d := by
  rcases Cas02.C03_eigenvalue_only d h eig hh he with h1 | h2
  · rw [h1]; exact one_le_lamMax d
  · rw [h2]; exact le_of_eq rfl

theorem gram_lamMax_eigen [Nontrivial E] (d : E) :
    ∃ h : E, h ≠ 0 ∧ Cas02.gramVec d h = lamMax d • h := by
  by_cases hd : d = 0
  · obtain ⟨h, hh⟩ := exists_ne (0 : E)
    refine ⟨h, hh, ?_⟩
    subst hd
    rw [Cas02.C03_zero_repeated, lamMax_zero, one_smul]
  · exact ⟨d, hd, Cas02.C03_longitudinal d⟩

theorem gram_max_eigenvalue [Nontrivial E] (d : E) :
    IsGreatest {eig : ℝ | ∃ h : E, h ≠ 0 ∧ Cas02.gramVec d h = eig • h} (lamMax d) :=
  ⟨gram_lamMax_eigen d, fun _ ⟨h, hh, he⟩ => gram_eig_le d h _ hh he⟩

theorem gram_quad_attained [Nontrivial E] (d : E) :
    ∃ h : E, h ≠ 0 ∧ Cas02.chartGram d h h = lamMax d * ‖h‖ ^ 2 := by
  obtain ⟨h, hh, he⟩ := gram_lamMax_eigen d
  refine ⟨h, hh, ?_⟩
  rw [← Cas02.C03_gram_action, he, real_inner_smul_left, real_inner_self_eq_norm_sq]

theorem gram_rayleigh_max [Nontrivial E] (d : E) :
    IsGreatest {q : ℝ | ∃ h : E, h ≠ 0 ∧ q = Cas02.chartGram d h h / ‖h‖ ^ 2} (lamMax d) := by
  constructor
  · obtain ⟨h, hh, he⟩ := gram_quad_attained d
    have hn : (0 : ℝ) < ‖h‖ ^ 2 := by have := norm_pos_iff.mpr hh; positivity
    exact ⟨h, hh, by rw [he, mul_div_assoc, div_self hn.ne', mul_one]⟩
  · rintro q ⟨h, hh, rfl⟩
    have hn : (0 : ℝ) < ‖h‖ ^ 2 := by have := norm_pos_iff.mpr hh; positivity
    rw [div_le_iff₀ hn]
    exact gram_quad_le d h

/-! ### T2: rapidity bound and monotonicity -/

theorem tanh_sq_eq_ratio (R : ℝ) :
    Real.tanh R ^ 2 = Real.sinh R ^ 2 / (1 + Real.sinh R ^ 2) := by
  have hc : 1 + Real.sinh R ^ 2 = Real.cosh R ^ 2 := by
    nlinarith [Real.cosh_sq_sub_sinh_sq R]
  have hcosh : Real.cosh R ≠ 0 := ne_of_gt (Real.cosh_pos R)
  rw [hc, Real.tanh_eq_sinh_div_cosh, div_pow]

theorem lamMax_le_rapidity (d : E) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    0 ≤ R ∧ lamMax d ≤ 1 + Real.tanh R ^ 2 :=
  ⟨Real.sinh_nonneg_iff.mp ((norm_nonneg d).trans hd), Cas02.C03_rapidity_bound d R hd⟩

theorem lamMax_at_rapidity (d : E) (χ : ℝ) (hd : ‖d‖ = Real.sinh χ) :
    lamMax d = 1 + Real.tanh χ ^ 2 := by
  rw [lamMax, hd, tanh_sq_eq_ratio]

theorem lamMax_mono {d₁ d₂ : E} (h : ‖d₁‖ ≤ ‖d₂‖) : lamMax d₁ ≤ lamMax d₂ := by
  unfold lamMax
  have := Cas02.ratio_mono (sq_nonneg ‖d₁‖) (pow_le_pow_left₀ (norm_nonneg _) h 2)
  linarith

theorem rapidity_cap_monotone :
    MonotoneOn (fun R : ℝ => 1 + Real.tanh R ^ 2) (Set.Ici 0) := by
  intro a ha b _ hab
  show 1 + Real.tanh a ^ 2 ≤ 1 + Real.tanh b ^ 2
  rw [tanh_sq_eq_ratio, tanh_sq_eq_ratio]
  have hsa : 0 ≤ Real.sinh a := Real.sinh_nonneg_iff.mpr ha
  have hs : Real.sinh a ^ 2 ≤ Real.sinh b ^ 2 :=
    pow_le_pow_left₀ hsa (Real.sinh_le_sinh.mpr hab) 2
  have := Cas02.ratio_mono (sq_nonneg _) hs
  linarith

theorem rapidity_mem_ball (d : E) (χ R : ℝ) (hd : ‖d‖ = Real.sinh χ) (hχR : χ ≤ R) :
    ‖d‖ ≤ Real.sinh R := by
  rw [hd]; exact Real.sinh_le_sinh.mpr hχR

theorem rapidity_R_zero (d : E) (hd : ‖d‖ ≤ Real.sinh 0) :
    d = 0 ∧ lamMax d = 1 ∧ 1 + Real.tanh 0 ^ 2 = 1 := by
  have h0 : d = 0 := by
    rw [Real.sinh_zero] at hd
    exact norm_le_zero_iff.mp hd
  subst h0
  exact ⟨rfl, lamMax_zero, by simp⟩

theorem tanh_nonneg_of_nonneg (R : ℝ) (hR : 0 ≤ R) : 0 ≤ Real.tanh R := by
  rw [Real.tanh_eq_sinh_div_cosh]
  exact div_nonneg (Real.sinh_nonneg_iff.mpr hR) (Real.cosh_pos R).le

/-! ### T3: closed Euclidean ball projection -/

/-- Radial (metric) projection onto the closed Euclidean ball of radius `r` about `0`. -/
noncomputable def ballProj (r : ℝ) (x : E) : E := if ‖x‖ ≤ r then x else (r / ‖x‖) • x

theorem ballProj_of_le {r : ℝ} {x : E} (h : ‖x‖ ≤ r) : ballProj r x = x := if_pos h

theorem ballProj_of_lt {r : ℝ} {x : E} (h : r < ‖x‖) : ballProj r x = (r / ‖x‖) • x :=
  if_neg (not_le.mpr h)

theorem ballProj_norm_le {r : ℝ} (hr : 0 ≤ r) (x : E) : ‖ballProj r x‖ ≤ r := by
  by_cases h : ‖x‖ ≤ r
  · rw [ballProj_of_le h]; exact h
  · push_neg at h
    have hx : 0 < ‖x‖ := hr.trans_lt h
    calc ‖ballProj r x‖ = r := by
          rw [ballProj_of_lt h, norm_smul, Real.norm_eq_abs,
            abs_of_nonneg (div_nonneg hr hx.le), div_mul_cancel₀ r hx.ne']
      _ ≤ r := le_rfl

theorem ballProj_eq_self_iff {r : ℝ} (hr : 0 ≤ r) (x : E) : ballProj r x = x ↔ ‖x‖ ≤ r := by
  constructor
  · intro h
    have := ballProj_norm_le hr x
    rwa [h] at this
  · exact ballProj_of_le

theorem ballProj_variational {r : ℝ} (hr : 0 ≤ r) (x z : E) (hz : ‖z‖ ≤ r) :
    inner ℝ (x - ballProj r x) (z - ballProj r x) ≤ 0 := by
  by_cases h : ‖x‖ ≤ r
  · rw [ballProj_of_le h, sub_self, inner_zero_left]
  · push_neg at h
    have hx : 0 < ‖x‖ := hr.trans_lt h
    rw [ballProj_of_lt h]
    have e1 : x - (r / ‖x‖) • x = (1 - r / ‖x‖) • x := by rw [sub_smul, one_smul]
    rw [e1, real_inner_smul_left, inner_sub_right, real_inner_smul_right,
      real_inner_self_eq_norm_sq]
    have hc : 0 ≤ 1 - r / ‖x‖ := by
      rw [sub_nonneg, div_le_one hx]; exact h.le
    have hxz : inner ℝ x z ≤ ‖x‖ * ‖z‖ := real_inner_le_norm x z
    have e : r / ‖x‖ * ‖x‖ ^ 2 = r * ‖x‖ := by
      rw [pow_two, ← mul_assoc, div_mul_cancel₀ r hx.ne']
    have hneg : inner ℝ x z - r / ‖x‖ * ‖x‖ ^ 2 ≤ 0 := by
      rw [e]; nlinarith [mul_le_mul_of_nonneg_left hz hx.le]
    nlinarith [mul_nonneg hc (neg_nonneg.mpr hneg)]

theorem ballProj_nearest {r : ℝ} (hr : 0 ≤ r) (x z : E) (hz : ‖z‖ ≤ r) :
    ‖x - ballProj r x‖ ≤ ‖x - z‖ := by
  have hv := ballProj_variational hr x z hz
  have e : x - z = (x - ballProj r x) - (z - ballProj r x) := by abel
  have hsq : ‖x - z‖ ^ 2 = ‖x - ballProj r x‖ ^ 2 -
      2 * inner ℝ (x - ballProj r x) (z - ballProj r x) + ‖z - ballProj r x‖ ^ 2 := by
    rw [e, norm_sub_sq_real]
  have h2 : ‖x - ballProj r x‖ ^ 2 ≤ ‖x - z‖ ^ 2 := by
    nlinarith [sq_nonneg ‖z - ballProj r x‖]
  exact (sq_le_sq₀ (norm_nonneg _) (norm_nonneg _)).1 h2

theorem nonexp_of_variational (x y p q : E) (h1 : inner ℝ (x - p) (q - p) ≤ 0)
    (h2 : inner ℝ (y - q) (p - q) ≤ 0) : ‖p - q‖ ≤ ‖x - y‖ := by
  have key : ‖p - q‖ ^ 2 ≤ inner ℝ (x - y) (p - q) := by
    have e1 : x - y = ((x - p) - (y - q)) + (p - q) := by abel
    have e3 : inner ℝ (x - p) (p - q) = - inner ℝ (x - p) (q - p) := by
      rw [← inner_neg_right, neg_sub]
    rw [e1, inner_add_left, inner_sub_left, real_inner_self_eq_norm_sq, e3]
    linarith
  have hcs := real_inner_le_norm (x - y) (p - q)
  nlinarith [norm_nonneg (p - q), norm_nonneg (x - y)]

theorem ballProj_nonexpansive {r : ℝ} (hr : 0 ≤ r) (x y : E) :
    ‖ballProj r x - ballProj r y‖ ≤ ‖x - y‖ :=
  nonexp_of_variational x y (ballProj r x) (ballProj r y)
    (ballProj_variational hr x _ (ballProj_norm_le hr y))
    (ballProj_variational hr y _ (ballProj_norm_le hr x))

theorem ballProj_error {r : ℝ} (hr : 0 ≤ r) (ζ ζhat : E) (hζ : ‖ζ‖ ≤ r) (η : ℝ)
    (h : ‖ζhat - ζ‖ ≤ η) : ‖ballProj r ζhat - ζ‖ ≤ η := by
  have := ballProj_nonexpansive hr ζhat ζ
  rw [ballProj_of_le hζ] at this
  exact this.trans h

theorem ballProj_zero_radius (x : E) : ballProj 0 x = 0 := by
  by_cases h : ‖x‖ ≤ 0
  · rw [ballProj_of_le h]; exact norm_le_zero_iff.mp h
  · push_neg at h
    rw [ballProj_of_lt h, zero_div, zero_smul]

theorem ballProj_moves {r : ℝ} (hr : 0 ≤ r) (x : E) (hx : r < ‖x‖) : ballProj r x ≠ x := by
  intro h
  have := (ballProj_eq_self_iff hr x).1 h
  linarith

/-! ### T4: derivative bound on the ball and mean-value Lipschitz bounds -/

/-- First (time) component of the actual chart derivative `C03_hasFDerivAt`. -/
noncomputable def fstJac (d : E) : E →L[ℝ] ℝ :=
  (ContinuousLinearMap.fst ℝ ℝ E).comp (Cas02.chartJac d)

theorem chart_fst_hasFDerivAt (d : E) :
    HasFDerivAt (fun x : E => (Cas02.chart x).1) (fstJac d) d :=
  (Cas02.C03_hasFDerivAt d).fst

theorem fstJac_norm_le (d : E) : ‖fstJac d‖ ≤ ‖d‖ / Real.sqrt (1 + ‖d‖ ^ 2) := by
  have hs : 0 < Real.sqrt (1 + ‖d‖ ^ 2) := Real.sqrt_pos.2 (by positivity)
  apply ContinuousLinearMap.opNorm_le_bound _ (div_nonneg (norm_nonneg _) hs.le)
  intro h
  have e : fstJac d h = (Cas02.chartJac d h).1 := rfl
  rw [e, (Cas02.chartJac_apply d h).1, Real.norm_eq_abs, abs_div, abs_of_pos hs,
    div_mul_eq_mul_div]
  exact div_le_div_of_nonneg_right (abs_real_inner_le_norm d h) hs.le

theorem rapidity_ratio_le (d : E) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    ‖d‖ / Real.sqrt (1 + ‖d‖ ^ 2) ≤ Real.tanh R := by
  have hR := (lamMax_le_rapidity d R hd).1
  have hp : 0 ≤ 1 + ‖d‖ ^ 2 := by positivity
  have h0 : 0 ≤ ‖d‖ / Real.sqrt (1 + ‖d‖ ^ 2) := div_nonneg (norm_nonneg _) (Real.sqrt_nonneg _)
  have h1 : 0 ≤ Real.tanh R := tanh_nonneg_of_nonneg R hR
  have hsq : (‖d‖ / Real.sqrt (1 + ‖d‖ ^ 2)) ^ 2 ≤ Real.tanh R ^ 2 := by
    rw [div_pow, Real.sq_sqrt hp]
    have := Cas02.C03_rapidity_bound d R hd
    linarith
  exact (sq_le_sq₀ h0 h1).1 hsq

theorem chart_fst_lipschitz_on_ball (R : ℝ) (a b : E)
    (ha : ‖a‖ ≤ Real.sinh R) (hb : ‖b‖ ≤ Real.sinh R) :
    |Real.sqrt (1 + ‖a‖ ^ 2) - Real.sqrt (1 + ‖b‖ ^ 2)| ≤ Real.tanh R * ‖a - b‖ := by
  have hs : Convex ℝ (Metric.closedBall (0 : E) (Real.sinh R)) := convex_closedBall _ _
  have := hs.norm_image_sub_le_of_norm_hasFDerivWithin_le
    (f := fun x : E => (Cas02.chart x).1) (f' := fstJac)
    (fun x _ => (chart_fst_hasFDerivAt x).hasFDerivWithinAt)
    (fun x hx => (fstJac_norm_le x).trans
      (rapidity_ratio_le x R (mem_closedBall_zero_iff.mp hx)))
    (mem_closedBall_zero_iff.mpr hb) (mem_closedBall_zero_iff.mpr ha)
  simpa [Cas02.chart, Real.norm_eq_abs] using this

/-- Regularity (Lipschitz) constant of `future` on the rapidity ball. -/
noncomputable def lipConst (R : ℝ) : ℝ := Real.sqrt (1 + Real.tanh R ^ 2)

theorem lipConst_nonneg (R : ℝ) : 0 ≤ lipConst R := Real.sqrt_nonneg _

theorem chart_fst_error (R ηd : ℝ) (ζ ζhat : E) (hζ : ‖ζ‖ ≤ Real.sinh R)
    (hd : ‖ζhat - ζ‖ ≤ ηd) :
    |Real.sqrt (1 + ‖ζ‖ ^ 2) - Real.sqrt (1 + ‖ballProj (Real.sinh R) ζhat‖ ^ 2)| ≤
      Real.tanh R * ηd := by
  have hr : 0 ≤ Real.sinh R := (norm_nonneg ζ).trans hζ
  have hR := (lamMax_le_rapidity ζ R hζ).1
  have hstar := ballProj_norm_le hr ζhat
  have herr := ballProj_error hr ζ ζhat hζ ηd hd
  have hl := chart_fst_lipschitz_on_ball R ζ (ballProj (Real.sinh R) ζhat) hζ hstar
  rw [norm_sub_rev] at hl
  exact hl.trans (mul_le_mul_of_nonneg_left herr (tanh_nonneg_of_nonneg R hR))

theorem clipped_monopole_check (R ηd η0 ζ0hat : ℝ) (ζ ζhat : E)
    (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd)
    (h0 : |ζ0hat - Real.sqrt (1 + ‖ζ‖ ^ 2)| ≤ η0) :
    |ζ0hat - Real.sqrt (1 + ‖ballProj (Real.sinh R) ζhat‖ ^ 2)| ≤
      η0 + Real.tanh R * ηd := by
  have h1 := chart_fst_error R ηd ζ ζhat hζ hd
  calc |ζ0hat - Real.sqrt (1 + ‖ballProj (Real.sinh R) ζhat‖ ^ 2)|
      = |(ζ0hat - Real.sqrt (1 + ‖ζ‖ ^ 2)) +
          (Real.sqrt (1 + ‖ζ‖ ^ 2) - Real.sqrt (1 + ‖ballProj (Real.sinh R) ζhat‖ ^ 2))| := by
        ring_nf
    _ ≤ |ζ0hat - Real.sqrt (1 + ‖ζ‖ ^ 2)| +
          |Real.sqrt (1 + ‖ζ‖ ^ 2) - Real.sqrt (1 + ‖ballProj (Real.sinh R) ζhat‖ ^ 2)| :=
        abs_add_le _ _
    _ ≤ η0 + Real.tanh R * ηd := add_le_add h0 h1

theorem G02B_R_zero_proj (ζhat : E) : ballProj (Real.sinh 0) ζhat = 0 := by
  rw [Real.sinh_zero]; exact ballProj_zero_radius ζhat

end General

/-! ### Euclidean-target derivative of the C04 map `future` -/

/-- `(t, x) ↦ (t, x₀, x₁, x₂)` into the Euclidean observer component space. -/
noncomputable def embLin : (ℝ × CAS02C04.Vec3) →ₗ[ℝ] CAS02C04.Vec4 where
  toFun p := (EuclideanSpace.equiv (Fin 4) ℝ).symm ![p.1, p.2 0, p.2 1, p.2 2]
  map_add' p q := by
    ext i; fin_cases i <;> simp
  map_smul' c p := by
    ext i; fin_cases i <;> simp

noncomputable def emb : (ℝ × CAS02C04.Vec3) →L[ℝ] CAS02C04.Vec4 :=
  LinearMap.toContinuousLinearMap embLin

theorem emb_apply (p : ℝ × CAS02C04.Vec3) :
    emb p = (EuclideanSpace.equiv (Fin 4) ℝ).symm ![p.1, p.2 0, p.2 1, p.2 2] := rfl

theorem emb_norm_sq (p : ℝ × CAS02C04.Vec3) : ‖emb p‖ ^ 2 = p.1 ^ 2 + ‖p.2‖ ^ 2 := by
  rw [EuclideanSpace.real_norm_sq_eq, EuclideanSpace.real_norm_sq_eq, emb_apply]
  simp [Fin.sum_univ_four, Fin.sum_univ_three]
  ring

theorem future_eq_emb_chart (d : CAS02C04.Vec3) : CAS02C04.future d = emb (Cas02.chart d) := rfl

theorem future_hasFDerivAt (d : CAS02C04.Vec3) :
    HasFDerivAt CAS02C04.future (emb.comp (Cas02.chartJac d)) d := by
  have h := emb.hasFDerivAt.comp d (Cas02.C03_hasFDerivAt d)
  have hf : CAS02C04.future = fun x => emb (Cas02.chart x) := funext future_eq_emb_chart
  rw [hf]
  exact h

theorem futureJac_norm_sq (d h : CAS02C04.Vec3) :
    ‖(emb.comp (Cas02.chartJac d)) h‖ ^ 2 = Cas02.chartGram d h h := by
  rw [ContinuousLinearMap.comp_apply, emb_norm_sq, Cas02.chartGram,
    real_inner_self_eq_norm_sq]
  ring

theorem futureJac_bound (d h : CAS02C04.Vec3) :
    ‖(emb.comp (Cas02.chartJac d)) h‖ ≤ Real.sqrt (lamMax d) * ‖h‖ := by
  have h1 := gram_quad_le d h
  rw [← futureJac_norm_sq] at h1
  have h2 := Real.abs_le_sqrt h1
  rw [abs_of_nonneg (norm_nonneg _),
    Real.sqrt_mul (by linarith [one_le_lamMax d]), Real.sqrt_sq (norm_nonneg _)] at h2
  exact h2

theorem futureJac_opNorm (d : CAS02C04.Vec3) :
    ‖emb.comp (Cas02.chartJac d)‖ = Real.sqrt (lamMax d) := by
  apply le_antisymm
  · exact ContinuousLinearMap.opNorm_le_bound _ (Real.sqrt_nonneg _) (futureJac_bound d)
  · obtain ⟨h, hh, he⟩ := gram_quad_attained d
    have hn : 0 < ‖h‖ := norm_pos_iff.mpr hh
    have h1 := (emb.comp (Cas02.chartJac d)).le_opNorm h
    have h2 : ‖(emb.comp (Cas02.chartJac d)) h‖ = Real.sqrt (lamMax d) * ‖h‖ := by
      rw [← Real.sqrt_sq (norm_nonneg ((emb.comp (Cas02.chartJac d)) h)), futureJac_norm_sq,
        he, Real.sqrt_mul (by linarith [one_le_lamMax d]), Real.sqrt_sq hn.le]
    rw [h2] at h1
    exact le_of_mul_le_mul_right h1 hn

theorem futureJac_opNorm_le_rapidity (d : CAS02C04.Vec3) (R : ℝ) (hd : ‖d‖ ≤ Real.sinh R) :
    ‖emb.comp (Cas02.chartJac d)‖ ≤ lipConst R := by
  rw [futureJac_opNorm]
  exact Real.sqrt_le_sqrt (Cas02.C03_rapidity_bound d R hd)

theorem future_lipschitz_on_ball (R : ℝ) (a b : CAS02C04.Vec3)
    (ha : ‖a‖ ≤ Real.sinh R) (hb : ‖b‖ ≤ Real.sinh R) :
    ‖CAS02C04.future a - CAS02C04.future b‖ ≤ lipConst R * ‖a - b‖ :=
  (convex_closedBall (0 : CAS02C04.Vec3) (Real.sinh R)).norm_image_sub_le_of_norm_hasFDerivWithin_le
    (f := CAS02C04.future) (f' := fun x => emb.comp (Cas02.chartJac x))
    (fun x _ => (future_hasFDerivAt x).hasFDerivWithinAt)
    (fun x hx => futureJac_opNorm_le_rapidity x R (mem_closedBall_zero_iff.mp hx))
    (mem_closedBall_zero_iff.mpr hb) (mem_closedBall_zero_iff.mpr ha)

theorem clipped_future_error (R ηd : ℝ) (ζ ζhat : CAS02C04.Vec3)
    (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd) :
    ‖CAS02C04.future (ballProj (Real.sinh R) ζhat) - CAS02C04.future ζ‖ ≤ lipConst R * ηd := by
  have hr : 0 ≤ Real.sinh R := (norm_nonneg ζ).trans hζ
  have hstar := ballProj_norm_le hr ζhat
  have hl := future_lipschitz_on_ball R (ballProj (Real.sinh R) ζhat) ζ hstar hζ
  exact hl.trans (mul_le_mul_of_nonneg_left (ballProj_error hr ζ ζhat hζ ηd hd)
    (lipConst_nonneg R))

/-! ### T5: connection to the C04 finite inverse bound -/

theorem G02B_offshell_inverse_bound (S Sstar : CAS02C04.Mat4) (ζ ζhat : CAS02C04.Vec3)
    (R ηd : ℝ) (hζ : ‖ζ‖ ≤ Real.sinh R) (hd : ‖ζhat - ζ‖ ≤ ηd) :
    ‖CAS02C04.inverse Sstar (CAS02C04.future (ballProj (Real.sinh R) ζhat)) -
        CAS02C04.inverse S (CAS02C04.future ζ)‖ ≤
      (1 + 2 * CAS02C04.rapidityCap R ^ 2) * ‖Sstar - S‖ +
      4 * CAS02C04.rapidityCap R * min (CAS02C04.spectral S) (CAS02C04.spectral Sstar) *
        (lipConst R * ηd) := by
  have hr : 0 ≤ Real.sinh R := (norm_nonneg ζ).trans hζ
  have hstar := ballProj_norm_le hr ζhat
  have h := CAS02C04.CAS_02_C04 S Sstar ζ (ballProj (Real.sinh R) ζhat) R hζ hstar
  have hu := clipped_future_error R ηd ζ ζhat hζ hd
  have hM : 0 ≤ CAS02C04.rapidityCap R := Real.sqrt_nonneg _
  have hmin : 0 ≤ min (CAS02C04.spectral S) (CAS02C04.spectral Sstar) :=
    le_min (CAS02C04.spectral_nonneg S) (CAS02C04.spectral_nonneg Sstar)
  have hk : 0 ≤ 4 * CAS02C04.rapidityCap R *
      min (CAS02C04.spectral S) (CAS02C04.spectral Sstar) := by positivity
  exact h.trans (add_le_add_left (mul_le_mul_of_nonneg_left hu hk) _)

theorem G02B_offshell_inverse_bound_explicit (S Sstar : CAS02C04.Mat4)
    (ζ ζhat : CAS02C04.Vec3) (R ηd εH : ℝ) (hζ : ‖ζ‖ ≤ Real.sinh R)
    (hd : ‖ζhat - ζ‖ ≤ ηd) (hH : ‖Sstar - S‖ ≤ εH) :
    ‖CAS02C04.inverse Sstar (CAS02C04.future (ballProj (Real.sinh R) ζhat)) -
        CAS02C04.inverse S (CAS02C04.future ζ)‖ ≤
      (1 + 2 * CAS02C04.rapidityCap R ^ 2) * εH +
      4 * CAS02C04.rapidityCap R * CAS02C04.spectral Sstar * (lipConst R * ηd) := by
  have h := G02B_offshell_inverse_bound S Sstar ζ ζhat R ηd hζ hd
  have hηd : 0 ≤ ηd := (norm_nonneg _).trans hd
  have hM : 0 ≤ CAS02C04.rapidityCap R := Real.sqrt_nonneg _
  have hc : 0 ≤ 1 + 2 * CAS02C04.rapidityCap R ^ 2 := by positivity
  have hL : 0 ≤ lipConst R * ηd := mul_nonneg (lipConst_nonneg R) hηd
  have h1 : (1 + 2 * CAS02C04.rapidityCap R ^ 2) * ‖Sstar - S‖ ≤
      (1 + 2 * CAS02C04.rapidityCap R ^ 2) * εH := mul_le_mul_of_nonneg_left hH hc
  have h2 : 4 * CAS02C04.rapidityCap R * min (CAS02C04.spectral S) (CAS02C04.spectral Sstar) *
        (lipConst R * ηd) ≤
      4 * CAS02C04.rapidityCap R * CAS02C04.spectral Sstar * (lipConst R * ηd) := by
    have hm := min_le_right (CAS02C04.spectral S) (CAS02C04.spectral Sstar)
    have h4 : 0 ≤ 4 * CAS02C04.rapidityCap R := by positivity
    exact mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left hm h4) hL
  linarith

/-! ### Boundary, non-vacuity and negative controls -/

theorem G02B_R_zero_constants {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (ζhat : E) :
    ballProj (Real.sinh 0) ζhat = 0 ∧ lipConst 0 = 1 ∧ CAS02C04.rapidityCap 0 = 1 := by
  refine ⟨G02B_R_zero_proj ζhat, ?_, ?_⟩
  · simp [lipConst]
  · simp [CAS02C04.rapidityCap]

theorem single_norm : ‖EuclideanSpace.single (0 : Fin 3) (1 : ℝ)‖ = 1 := by
  rw [EuclideanSpace.norm_single]; simp

theorem G02B_nonvacuous_offshell :
    ∃ ζ ζhat : CAS02C04.Vec3, ∃ R ηd : ℝ, ‖ζ‖ ≤ Real.sinh R ∧ ‖ζhat - ζ‖ ≤ ηd ∧
      R = 0 ∧ ζ = 0 ∧ ballProj (Real.sinh R) ζhat ≠ ζhat := by
  refine ⟨0, EuclideanSpace.single (0 : Fin 3) (1 : ℝ), 0, 1, ?_, ?_, rfl, rfl, ?_⟩
  · simp
  · rw [sub_zero, single_norm]
  · rw [Real.sinh_zero]
    exact ballProj_moves le_rfl _ (by rw [single_norm]; norm_num)

theorem scalar_bound_needs_ball :
    ¬ ∀ a b : CAS02C04.Vec3,
      |Real.sqrt (1 + ‖a‖ ^ 2) - Real.sqrt (1 + ‖b‖ ^ 2)| ≤ Real.tanh 0 * ‖a - b‖ := by
  intro hall
  have h := hall (EuclideanSpace.single (0 : Fin 3) (1 : ℝ)) 0
  rw [single_norm, Real.tanh_zero, zero_mul, norm_zero] at h
  have h2 : Real.sqrt (1 + 1 ^ 2) = Real.sqrt (1 + 0 ^ 2) := by
    have := abs_nonpos_iff.mp h
    linarith
  norm_num at h2

end G02B
