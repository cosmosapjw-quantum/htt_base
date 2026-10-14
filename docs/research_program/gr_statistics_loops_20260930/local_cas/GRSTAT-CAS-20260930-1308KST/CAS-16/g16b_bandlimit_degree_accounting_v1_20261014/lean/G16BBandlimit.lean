import FullBridge

/-!
# G16-B: scalar bandlimit and `D* = max(L+4, LC+2, LT+2)` degree accounting

Source: `supplements/DOSSIER_POSITIVE_BRIDGE.md` (B3), (B5), (C3) paragraph; contract
`cas/contracts/CAS-16.json` CAS-16-C02/C03.  The accepted CAS16-C03 modules are imported
unchanged; `CAS16C03.fullMonomialTheorem` is used only through linearity.

* `shBand L`  : real span of the real spherical harmonics `ℓ ≤ L` (associated-Legendre form,
  Rodrigues `P_ℓ`), in the chart `(μ, φ)`.
* `cartSpan D`: real span of restricted Cartesian monomials `x^a y^b z^c`, `a+b+c ≤ D`.
* Actual integrands of (B3)/(B5): brightness moment, weak residual, collision, transport.

Spin-weighted (polarized) quadrature is excluded.
-/

namespace G16B

open scoped Interval

/-- Chart functions on `S²`: `(μ, φ) ↦ value`, `μ = cos θ`. -/
abbrev ChartFn := ℝ → ℝ → ℝ

/-! ## Restricted Cartesian polynomial span -/

/-- Restricted Cartesian monomials of total degree at most `D`. -/
def cartMonomials (D : ℕ) : Set ChartFn :=
  {f | ∃ a b c : ℕ, a + b + c ≤ D ∧ f = CAS16C03.monomial a b c}

/-- Restricted Cartesian polynomial span of degree at most `D`. -/
noncomputable def cartSpan (D : ℕ) : Submodule ℝ ChartFn :=
  Submodule.span ℝ (cartMonomials D)

/-! ## Scalar spherical-harmonic bandlimit -/

/-- Legendre polynomial by Rodrigues' formula. -/
noncomputable def legendreP (l : ℕ) : Polynomial ℝ :=
  Polynomial.C (1 / ((2 : ℝ) ^ l * (Nat.factorial l : ℝ))) *
    Polynomial.derivative^[l] ((Polynomial.X ^ 2 - 1) ^ l)

/-- Polynomial factor `(d/dμ)^m P_ℓ` of the associated Legendre function `P_ℓ^m`. -/
noncomputable def assocLegendrePoly (l m : ℕ) : Polynomial ℝ :=
  Polynomial.derivative^[m] (legendreP l)

/-- Real spherical harmonic, cosine type (normalization and Condon–Shortley sign omitted). -/
noncomputable def shCos (l m : ℕ) : ChartFn := fun μ φ =>
  Real.sqrt (1 - μ ^ 2) ^ m * (assocLegendrePoly l m).eval μ * Real.cos ((m : ℝ) * φ)

/-- Real spherical harmonic, sine type (normalization and Condon–Shortley sign omitted). -/
noncomputable def shSin (l m : ℕ) : ChartFn := fun μ φ =>
  Real.sqrt (1 - μ ^ 2) ^ m * (assocLegendrePoly l m).eval μ * Real.sin ((m : ℝ) * φ)

/-- Real spherical harmonics with `m ≤ ℓ ≤ L`. -/
def shGenerators (L : ℕ) : Set ChartFn :=
  {f | ∃ l m : ℕ, m ≤ l ∧ l ≤ L ∧ (f = shCos l m ∨ f = shSin l m)}

/-- Scalar bandlimit `L`: real span of real spherical harmonics with `ℓ ≤ L`. -/
noncomputable def shBand (L : ℕ) : Submodule ℝ ChartFn :=
  Submodule.span ℝ (shGenerators L)

/-! ## Actual angular integrands of (B3), (B5) -/

/-- Unit propagation direction `e(μ, φ)`. -/
noncomputable def eVec (μ φ : ℝ) : Fin 3 → ℝ :=
  ![CAS16C03.sphereX μ φ, CAS16C03.sphereY μ φ, CAS16C03.sphereZ μ]

/-- (B5) weak-residual angular kernel, component `(i,j)`:
`[4H - σ:ee] e_i e_j + a_i e_j + e_i a_j + (σe)_i e_j + e_i (σe)_j`. -/
noncomputable def weakKernel (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ)
    (i j : Fin 3) : ChartFn := fun μ φ =>
  (4 * H - ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) * (eVec μ φ i * eVec μ φ j)
    + (a i * eVec μ φ j + eVec μ φ i * a j)
    + ((∑ k, σ i k * eVec μ φ k) * eVec μ φ j + eVec μ φ i * (∑ k, σ j k * eVec μ φ k))

/-- (B3) brightness moment integrand `I e_i e_j`. -/
noncomputable def momentIntegrand (I : ChartFn) (i j : Fin 3) : ChartFn :=
  fun μ φ => I μ φ * (eVec μ φ i * eVec μ φ j)

/-- (B5) brightness (weak-residual) integrand `I K_ij`. -/
noncomputable def weakResidualIntegrand (I : ChartFn) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) : ChartFn :=
  fun μ φ => I μ φ * weakKernel H a σ i j μ φ

/-- Collision integrand `C e_i e_j` of `C_2`. -/
noncomputable def collisionIntegrand (C : ChartFn) (i j : Fin 3) : ChartFn :=
  fun μ φ => C μ φ * (eVec μ φ i * eVec μ φ j)

/-- Transport integrand `(𝒟I) e_i e_j` of `T_2`. -/
noncomputable def transportIntegrand (T : ChartFn) (i j : Fin 3) : ChartFn :=
  fun μ φ => T μ φ * (eVec μ φ i * eVec μ φ j)

/-- Full (B5) residual integrand `R_ij`. -/
noncomputable def residualIntegrand (I C T : ChartFn) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) : ChartFn :=
  fun μ φ => collisionIntegrand C i j μ φ - transportIntegrand T i j μ φ
    - weakResidualIntegrand I H a σ i j μ φ

/-- `D* = max(L+4, LC+2, LT+2)`. -/
def Dstar (L LC LT : ℕ) : ℕ := max (L + 4) (max (LC + 2) (LT + 2))

/-- The GL5 × Nφ9 product rule of C03, on an arbitrary chart function. -/
noncomputable def quadRule (f : ChartFn) : ℝ :=
  (1 / 2 : ℝ) * ∑ r : Fin 5, CAS16C03.gl5Weight r *
    ((1 / 9 : ℝ) * ∑ j : Fin 9, f (CAS16C03.gl5Node r) (CAS16C03.azimuth 9 j))

/-- The normalized sphere mean of C03, on an arbitrary chart function. -/
noncomputable def sphereMeanFn (f : ChartFn) : ℝ :=
  (1 / (4 * Real.pi) : ℝ) * ∫ μ in (-1 : ℝ)..1, ∫ φ in (0 : ℝ)..(2 * Real.pi), f μ φ

/-! ## T2: product-degree lemma and monotonicity -/

theorem monomial_mem_cartSpan {D a b c : ℕ} (h : a + b + c ≤ D) :
    CAS16C03.monomial a b c ∈ cartSpan D :=
  Submodule.subset_span ⟨a, b, c, h, rfl⟩

theorem cartSpan_mono {A B : ℕ} (h : A ≤ B) : cartSpan A ≤ cartSpan B := by
  apply Submodule.span_mono
  rintro f ⟨a, b, c, hd, rfl⟩
  exact ⟨a, b, c, le_trans hd h, rfl⟩

theorem monomial_mul (a b c a' b' c' : ℕ) :
    CAS16C03.monomial a b c * CAS16C03.monomial a' b' c' =
      CAS16C03.monomial (a + a') (b + b') (c + c') := by
  funext μ φ
  simp only [Pi.mul_apply, CAS16C03.monomial, pow_add]
  ring

theorem mul_mem_cartSpan {A B : ℕ} {f g : ChartFn}
    (hf : f ∈ cartSpan A) (hg : g ∈ cartSpan B) : f * g ∈ cartSpan (A + B) := by
  induction hf using Submodule.span_induction with
  | mem x hx =>
      induction hg using Submodule.span_induction with
      | mem y hy =>
          obtain ⟨a, b, c, hd, rfl⟩ := hx
          obtain ⟨a', b', c', hd', rfl⟩ := hy
          rw [monomial_mul]
          exact monomial_mem_cartSpan (by omega)
      | zero => simp
      | add y z _ _ hy hz =>
          rw [mul_add]
          exact Submodule.add_mem _ hy hz
      | smul r y _ hy =>
          rw [mul_smul_comm]
          exact Submodule.smul_mem _ r hy
  | zero => simp
  | add x y _ _ hx hy =>
      rw [add_mul]
      exact Submodule.add_mem _ hx hy
  | smul r x _ hx =>
      rw [smul_mul_assoc]
      exact Submodule.smul_mem _ r hx

/-! ## T1: spherical-harmonic bandlimit ⊆ restricted Cartesian span -/

/-- `(1-μ²)^{m/2} cos(mφ)`. -/
noncomputable def cosHarm (m : ℕ) : ChartFn := fun μ φ =>
  Real.sqrt (1 - μ ^ 2) ^ m * Real.cos ((m : ℝ) * φ)

/-- `(1-μ²)^{m/2} sin(mφ)`. -/
noncomputable def sinHarm (m : ℕ) : ChartFn := fun μ φ =>
  Real.sqrt (1 - μ ^ 2) ^ m * Real.sin ((m : ℝ) * φ)

theorem cosHarm_succ (m : ℕ) :
    cosHarm (m + 1) = cosHarm m * CAS16C03.monomial 1 0 0 -
      sinHarm m * CAS16C03.monomial 0 1 0 := by
  funext μ φ
  have hφ : ((m + 1 : ℕ) : ℝ) * φ = (m : ℝ) * φ + φ := by push_cast; ring
  simp only [cosHarm, sinHarm, Pi.sub_apply, Pi.mul_apply, CAS16C03.monomial,
    CAS16C03.sphereX, CAS16C03.sphereY, CAS16C03.sphereZ, hφ, Real.cos_add]
  ring

theorem sinHarm_succ (m : ℕ) :
    sinHarm (m + 1) = sinHarm m * CAS16C03.monomial 1 0 0 +
      cosHarm m * CAS16C03.monomial 0 1 0 := by
  funext μ φ
  have hφ : ((m + 1 : ℕ) : ℝ) * φ = (m : ℝ) * φ + φ := by push_cast; ring
  simp only [cosHarm, sinHarm, Pi.add_apply, Pi.mul_apply, CAS16C03.monomial,
    CAS16C03.sphereX, CAS16C03.sphereY, CAS16C03.sphereZ, hφ, Real.sin_add]
  ring

theorem harm_mem (m : ℕ) : cosHarm m ∈ cartSpan m ∧ sinHarm m ∈ cartSpan m := by
  induction m with
  | zero =>
      constructor
      · have h : cosHarm 0 = CAS16C03.monomial 0 0 0 := by
          funext μ φ
          simp [cosHarm, CAS16C03.monomial]
        rw [h]
        exact monomial_mem_cartSpan (by norm_num)
      · have h : sinHarm 0 = 0 := by
          funext μ φ
          simp [sinHarm]
        rw [h]
        exact Submodule.zero_mem _
  | succ m ih =>
      have hX : CAS16C03.monomial 1 0 0 ∈ cartSpan 1 := monomial_mem_cartSpan (by norm_num)
      have hY : CAS16C03.monomial 0 1 0 ∈ cartSpan 1 := monomial_mem_cartSpan (by norm_num)
      constructor
      · rw [cosHarm_succ]
        exact Submodule.sub_mem _ (mul_mem_cartSpan ih.1 hX) (mul_mem_cartSpan ih.2 hY)
      · rw [sinHarm_succ]
        exact Submodule.add_mem _ (mul_mem_cartSpan ih.2 hX) (mul_mem_cartSpan ih.1 hY)

/-- A polynomial in `μ = z` lies in the Cartesian span of its degree. -/
theorem polyEval_mem (p : Polynomial ℝ) :
    (fun μ (_ : ℝ) => p.eval μ) ∈ cartSpan p.natDegree := by
  have h : (fun μ (_ : ℝ) => p.eval μ) =
      ∑ i ∈ Finset.range (p.natDegree + 1), p.coeff i • CAS16C03.monomial 0 0 i := by
    funext μ φ
    rw [Polynomial.eval_eq_sum_range]
    simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul, CAS16C03.monomial,
      CAS16C03.sphereZ, pow_zero, one_mul]
  rw [h]
  apply Submodule.sum_mem
  intro i hi
  apply Submodule.smul_mem
  exact monomial_mem_cartSpan (by simp at hi; omega)

theorem legendreP_natDegree_le (l : ℕ) : (legendreP l).natDegree ≤ l := by
  unfold legendreP
  refine (Polynomial.natDegree_C_mul_le _ _).trans ?_
  refine (Polynomial.natDegree_iterate_derivative _ _).trans ?_
  have h1 : (Polynomial.X ^ 2 - 1 : Polynomial ℝ).natDegree ≤ 2 := by compute_degree
  have h2 : ((Polynomial.X ^ 2 - 1 : Polynomial ℝ) ^ l).natDegree ≤ l * 2 :=
    Polynomial.natDegree_pow_le_of_le l h1
  omega

theorem assocLegendrePoly_natDegree_le (l m : ℕ) :
    (assocLegendrePoly l m).natDegree ≤ l - m := by
  unfold assocLegendrePoly
  refine (Polynomial.natDegree_iterate_derivative _ _).trans ?_
  have := legendreP_natDegree_le l
  omega

theorem shCos_eq (l m : ℕ) :
    shCos l m = cosHarm m * (fun μ (_ : ℝ) => (assocLegendrePoly l m).eval μ) := by
  funext μ φ
  simp only [shCos, cosHarm, Pi.mul_apply]
  ring

theorem shSin_eq (l m : ℕ) :
    shSin l m = sinHarm m * (fun μ (_ : ℝ) => (assocLegendrePoly l m).eval μ) := by
  funext μ φ
  simp only [shSin, sinHarm, Pi.mul_apply]
  ring

theorem shCos_mem {l m : ℕ} (hml : m ≤ l) : shCos l m ∈ cartSpan l := by
  rw [shCos_eq]
  have hp := polyEval_mem (assocLegendrePoly l m)
  have hd := assocLegendrePoly_natDegree_le l m
  exact cartSpan_mono (by omega) (mul_mem_cartSpan (harm_mem m).1 hp)

theorem shSin_mem {l m : ℕ} (hml : m ≤ l) : shSin l m ∈ cartSpan l := by
  rw [shSin_eq]
  have hp := polyEval_mem (assocLegendrePoly l m)
  have hd := assocLegendrePoly_natDegree_le l m
  exact cartSpan_mono (by omega) (mul_mem_cartSpan (harm_mem m).2 hp)

/-- T1: a scalar spherical-harmonic bandlimit `L` field is the restriction of a Cartesian
polynomial of degree at most `L`. -/
theorem shBand_le_cartSpan (L : ℕ) : shBand L ≤ cartSpan L := by
  apply Submodule.span_le.mpr
  rintro f ⟨l, m, hml, hlL, hf | hf⟩
  · rw [hf]; exact cartSpan_mono hlL (shCos_mem hml)
  · rw [hf]; exact cartSpan_mono hlL (shSin_mem hml)

/-! ## T3: actual angular factors -/

theorem eCoord_mem (i : Fin 3) : (fun μ φ => eVec μ φ i) ∈ cartSpan 1 := by
  fin_cases i
  · have h : (fun μ φ => eVec μ φ 0) = CAS16C03.monomial 1 0 0 := by
      funext μ φ; simp [eVec, CAS16C03.monomial]
    simpa [h] using (monomial_mem_cartSpan (D := 1) (a := 1) (b := 0) (c := 0) (by norm_num))
  · have h : (fun μ φ => eVec μ φ 1) = CAS16C03.monomial 0 1 0 := by
      funext μ φ; simp [eVec, CAS16C03.monomial]
    simpa [h] using (monomial_mem_cartSpan (D := 1) (a := 0) (b := 1) (c := 0) (by norm_num))
  · have h : (fun μ φ => eVec μ φ 2) = CAS16C03.monomial 0 0 1 := by
      funext μ φ; simp [eVec, CAS16C03.monomial]
    simpa [h] using (monomial_mem_cartSpan (D := 1) (a := 0) (b := 0) (c := 1) (by norm_num))

theorem const_mem (D : ℕ) (r : ℝ) : (fun (_ _ : ℝ) => r) ∈ cartSpan D := by
  have h : (fun (_ _ : ℝ) => r) = r • CAS16C03.monomial 0 0 0 := by
    funext μ φ; simp [CAS16C03.monomial]
  rw [h]
  exact Submodule.smul_mem _ r (monomial_mem_cartSpan (by norm_num))

theorem eiej_mem (i j : Fin 3) : (fun μ φ => eVec μ φ i * eVec μ φ j) ∈ cartSpan 2 := by
  have h : (fun μ φ => eVec μ φ i * eVec μ φ j) =
      (fun μ φ => eVec μ φ i) * (fun μ φ => eVec μ φ j) := by
    funext μ φ; simp only [Pi.mul_apply]
  rw [h]
  exact mul_mem_cartSpan (A := 1) (B := 1) (eCoord_mem i) (eCoord_mem j)

theorem weakKernel_mem (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    weakKernel H a σ i j ∈ cartSpan 4 := by
  -- σ:ee ∈ cartSpan 2
  have hsee : (fun μ φ => ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) ∈ cartSpan 2 := by
    have h : (fun μ φ => ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) =
        ∑ k, ∑ l, σ k l • (fun μ φ => eVec μ φ k * eVec μ φ l) := by
      funext μ φ
      simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul, mul_assoc]
    rw [h]
    exact Submodule.sum_mem _ fun k _ => Submodule.sum_mem _ fun l _ =>
      Submodule.smul_mem _ _ (eiej_mem k l)
  -- (σe)_i ∈ cartSpan 1
  have hse (i : Fin 3) : (fun μ φ => ∑ k, σ i k * eVec μ φ k) ∈ cartSpan 1 := by
    have h : (fun μ φ => ∑ k, σ i k * eVec μ φ k) =
        ∑ k, σ i k • (fun μ φ => eVec μ φ k) := by
      funext μ φ
      simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul]
    rw [h]
    exact Submodule.sum_mem _ fun k _ => Submodule.smul_mem _ _ (eCoord_mem k)
  have h4H : (fun μ φ => 4 * H - ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) ∈ cartSpan 2 := by
    have h : (fun μ φ => 4 * H - ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) =
        (fun (_ _ : ℝ) => 4 * H) - (fun μ φ => ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) := by
      funext μ φ; simp
    rw [h]
    exact Submodule.sub_mem _ (const_mem 2 (4 * H)) hsee
  have hT1 : (fun μ φ => (4 * H - ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) *
      (eVec μ φ i * eVec μ φ j)) ∈ cartSpan 4 :=
    mul_mem_cartSpan (A := 2) (B := 2) h4H (eiej_mem i j)
  have hT2 : (fun μ φ => a i * eVec μ φ j + eVec μ φ i * a j) ∈ cartSpan 4 := by
    have h : (fun μ φ => a i * eVec μ φ j + eVec μ φ i * a j) =
        a i • (fun μ φ => eVec μ φ j) + a j • (fun μ φ => eVec μ φ i) := by
      funext μ φ; simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]; ring
    rw [h]
    exact cartSpan_mono (by norm_num) (Submodule.add_mem _
      (Submodule.smul_mem _ _ (eCoord_mem j)) (Submodule.smul_mem _ _ (eCoord_mem i)))
  have hT3 : (fun μ φ => (∑ k, σ i k * eVec μ φ k) * eVec μ φ j +
      eVec μ φ i * (∑ k, σ j k * eVec μ φ k)) ∈ cartSpan 4 := by
    have h : (fun μ φ => (∑ k, σ i k * eVec μ φ k) * eVec μ φ j +
        eVec μ φ i * (∑ k, σ j k * eVec μ φ k)) =
        (fun μ φ => ∑ k, σ i k * eVec μ φ k) * (fun μ φ => eVec μ φ j) +
        (fun μ φ => eVec μ φ i) * (fun μ φ => ∑ k, σ j k * eVec μ φ k) := by
      funext μ φ; simp only [Pi.add_apply, Pi.mul_apply]
    rw [h]
    exact cartSpan_mono (by norm_num) (Submodule.add_mem _
      (mul_mem_cartSpan (hse i) (eCoord_mem j)) (mul_mem_cartSpan (eCoord_mem i) (hse j)))
  have h : weakKernel H a σ i j =
      (fun μ φ => (4 * H - ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) *
        (eVec μ φ i * eVec μ φ j)) +
      (fun μ φ => a i * eVec μ φ j + eVec μ φ i * a j) +
      (fun μ φ => (∑ k, σ i k * eVec μ φ k) * eVec μ φ j +
        eVec μ φ i * (∑ k, σ j k * eVec μ φ k)) := by
    funext μ φ; simp only [weakKernel, Pi.add_apply]
  rw [h]
  exact Submodule.add_mem _ (Submodule.add_mem _ hT1 hT2) hT3

/-! ## T4: increments +4, +2, +2 as membership of the actual integrands -/

theorem weakResidual_mem {L : ℕ} {I : ChartFn} (hI : I ∈ shBand L) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    weakResidualIntegrand I H a σ i j ∈ cartSpan (L + 4) := by
  have h : weakResidualIntegrand I H a σ i j = I * weakKernel H a σ i j := rfl
  rw [h]
  exact mul_mem_cartSpan (shBand_le_cartSpan L hI) (weakKernel_mem H a σ i j)

theorem moment_mem {L : ℕ} {I : ChartFn} (hI : I ∈ shBand L) (i j : Fin 3) :
    momentIntegrand I i j ∈ cartSpan (L + 2) := by
  have h : momentIntegrand I i j = I * (fun μ φ => eVec μ φ i * eVec μ φ j) := rfl
  rw [h]
  exact mul_mem_cartSpan (shBand_le_cartSpan L hI) (eiej_mem i j)

theorem collision_mem {LC : ℕ} {C : ChartFn} (hC : C ∈ shBand LC) (i j : Fin 3) :
    collisionIntegrand C i j ∈ cartSpan (LC + 2) := by
  have h : collisionIntegrand C i j = C * (fun μ φ => eVec μ φ i * eVec μ φ j) := rfl
  rw [h]
  exact mul_mem_cartSpan (shBand_le_cartSpan LC hC) (eiej_mem i j)

theorem transport_mem {LT : ℕ} {T : ChartFn} (hT : T ∈ shBand LT) (i j : Fin 3) :
    transportIntegrand T i j ∈ cartSpan (LT + 2) := by
  have h : transportIntegrand T i j = T * (fun μ φ => eVec μ φ i * eVec μ φ j) := rfl
  rw [h]
  exact mul_mem_cartSpan (shBand_le_cartSpan LT hT) (eiej_mem i j)

/-! ## T5: `D*` with actual membership -/

theorem dstar_membership {L LC LT : ℕ} {I C T : ChartFn}
    (hI : I ∈ shBand L) (hC : C ∈ shBand LC) (hT : T ∈ shBand LT)
    (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    momentIntegrand I i j ∈ cartSpan (Dstar L LC LT) ∧
    weakResidualIntegrand I H a σ i j ∈ cartSpan (Dstar L LC LT) ∧
    collisionIntegrand C i j ∈ cartSpan (Dstar L LC LT) ∧
    transportIntegrand T i j ∈ cartSpan (Dstar L LC LT) ∧
    residualIntegrand I C T H a σ i j ∈ cartSpan (Dstar L LC LT) := by
  have h1 : L + 2 ≤ Dstar L LC LT := by unfold Dstar; omega
  have h2 : L + 4 ≤ Dstar L LC LT := by unfold Dstar; omega
  have h3 : LC + 2 ≤ Dstar L LC LT := by unfold Dstar; omega
  have h4 : LT + 2 ≤ Dstar L LC LT := by unfold Dstar; omega
  have hm := cartSpan_mono h1 (moment_mem hI i j)
  have hw := cartSpan_mono h2 (weakResidual_mem hI H a σ i j)
  have hc := cartSpan_mono h3 (collision_mem hC i j)
  have ht := cartSpan_mono h4 (transport_mem hT i j)
  refine ⟨hm, hw, hc, ht, ?_⟩
  have h : residualIntegrand I C T H a σ i j =
      collisionIntegrand C i j - transportIntegrand T i j - weakResidualIntegrand I H a σ i j := rfl
  rw [h]
  exact Submodule.sub_mem _ (Submodule.sub_mem _ hc ht) hw

/-! ## T6: linearity wrapper of the accepted C03 theorem -/

theorem quadRule_monomial (a b c : ℕ) :
    quadRule (CAS16C03.monomial a b c) = CAS16C03.productRule a b c := rfl

theorem sphereMeanFn_monomial (a b c : ℕ) :
    sphereMeanFn (CAS16C03.monomial a b c) = CAS16C03.sphereMean a b c := rfl

theorem continuous_of_mem_cartSpan {D : ℕ} {f : ChartFn} (hf : f ∈ cartSpan D) :
    Continuous (Function.uncurry f) := by
  induction hf using Submodule.span_induction with
  | mem x hx =>
      obtain ⟨a, b, c, _, rfl⟩ := hx
      unfold Function.uncurry CAS16C03.monomial CAS16C03.sphereX CAS16C03.sphereY
        CAS16C03.sphereZ
      fun_prop
  | zero => exact continuous_const
  | add x y _ _ hx hy => exact hx.add hy
  | smul r x _ hx => exact continuous_const.mul hx

theorem quadRule_add (f g : ChartFn) : quadRule (f + g) = quadRule f + quadRule g := by
  simp only [quadRule, Pi.add_apply, Finset.sum_add_distrib, mul_add]

theorem quadRule_smul (r : ℝ) (f : ChartFn) : quadRule (r • f) = r * quadRule f := by
  have h : ∀ w s : ℝ, w * (1 / 9 * (r * s)) = r * (w * (1 / 9 * s)) := fun w s => by ring
  unfold quadRule
  simp only [Pi.smul_apply, smul_eq_mul, ← Finset.mul_sum, h]
  ring

theorem quadRule_zero : quadRule 0 = 0 := by simp [quadRule]

theorem sphereMeanFn_zero : sphereMeanFn 0 = 0 := by simp [sphereMeanFn]

theorem sphereMeanFn_add {f g : ChartFn} (hf : Continuous (Function.uncurry f))
    (hg : Continuous (Function.uncurry g)) :
    sphereMeanFn (f + g) = sphereMeanFn f + sphereMeanFn g := by
  have hfi (μ : ℝ) : IntervalIntegrable (f μ) MeasureTheory.volume 0 (2 * Real.pi) :=
    (hf.comp (Continuous.prodMk continuous_const continuous_id)).intervalIntegrable _ _
  have hgi (μ : ℝ) : IntervalIntegrable (g μ) MeasureTheory.volume 0 (2 * Real.pi) :=
    (hg.comp (Continuous.prodMk continuous_const continuous_id)).intervalIntegrable _ _
  have hF : Continuous fun μ => ∫ φ in (0 : ℝ)..(2 * Real.pi), f μ φ :=
    intervalIntegral.continuous_parametric_intervalIntegral_of_continuous' hf _ _
  have hG : Continuous fun μ => ∫ φ in (0 : ℝ)..(2 * Real.pi), g μ φ :=
    intervalIntegral.continuous_parametric_intervalIntegral_of_continuous' hg _ _
  unfold sphereMeanFn
  simp only [Pi.add_apply]
  simp_rw [intervalIntegral.integral_add (hfi _) (hgi _)]
  rw [intervalIntegral.integral_add (hF.intervalIntegrable _ _) (hG.intervalIntegrable _ _)]
  ring

theorem sphereMeanFn_smul (r : ℝ) (f : ChartFn) :
    sphereMeanFn (r • f) = r * sphereMeanFn f := by
  unfold sphereMeanFn
  simp only [Pi.smul_apply, smul_eq_mul, intervalIntegral.integral_const_mul]
  ring

/-- T6: the GL5 × Nφ9 rule is exact on the whole restricted Cartesian span of degree 8. -/
theorem quadRule_exact_cartSpan8 {f : ChartFn} (hf : f ∈ cartSpan 8) :
    quadRule f = sphereMeanFn f := by
  induction hf using Submodule.span_induction with
  | mem x hx =>
      obtain ⟨a, b, c, hd, rfl⟩ := hx
      rw [quadRule_monomial, sphereMeanFn_monomial]
      exact CAS16C03.fullMonomialTheorem a b c hd
  | zero => rw [quadRule_zero, sphereMeanFn_zero]
  | add x y hx hy ihx ihy =>
      rw [quadRule_add, sphereMeanFn_add (continuous_of_mem_cartSpan hx)
        (continuous_of_mem_cartSpan hy), ihx, ihy]
  | smul r x _ ihx =>
      rw [quadRule_smul, sphereMeanFn_smul, ihx]

/-! ## T7: the instance `(L, LC, LT) = (4, 6, 4)` -/

theorem dstar_464 : Dstar 4 6 4 = 8 := by decide

theorem c3_arith_464 :
    (Dstar 4 6 4 + 1 + 1) / 2 ≤ 5 ∧ Dstar 4 6 4 + 1 ≤ 9 ∧ Dstar 4 6 4 ≤ 2 * 5 - 1 := by
  decide

theorem actual_integrands_exact_464 {I C T : ChartFn}
    (hI : I ∈ shBand 4) (hC : C ∈ shBand 6) (hT : T ∈ shBand 4)
    (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    quadRule (momentIntegrand I i j) = sphereMeanFn (momentIntegrand I i j) ∧
    quadRule (weakResidualIntegrand I H a σ i j) =
      sphereMeanFn (weakResidualIntegrand I H a σ i j) ∧
    quadRule (collisionIntegrand C i j) = sphereMeanFn (collisionIntegrand C i j) ∧
    quadRule (transportIntegrand T i j) = sphereMeanFn (transportIntegrand T i j) ∧
    quadRule (residualIntegrand I C T H a σ i j) =
      sphereMeanFn (residualIntegrand I C T H a σ i j) := by
  obtain ⟨hm, hw, hc, ht, hr⟩ := dstar_membership hI hC hT H a σ i j
  rw [dstar_464] at hm hw hc ht hr
  exact ⟨quadRule_exact_cartSpan8 hm, quadRule_exact_cartSpan8 hw,
    quadRule_exact_cartSpan8 hc, quadRule_exact_cartSpan8 ht, quadRule_exact_cartSpan8 hr⟩

/-! ## T8: general C3 ceiling arithmetic -/

theorem c3_ceil_iff (D N : ℕ) : (D + 1 + 1) / 2 ≤ N ↔ D + 1 ≤ 2 * N := by
  omega

/-! ## Non-vacuity witnesses -/

theorem one_mem_shBand (L : ℕ) : (fun _ _ => (1 : ℝ)) ∈ shBand L := by
  have h : shCos 0 0 = (fun _ _ => (1 : ℝ)) := by
    funext μ φ
    simp [shCos, assocLegendrePoly, legendreP]
  rw [← h]
  exact Submodule.subset_span ⟨0, 0, le_rfl, Nat.zero_le L, Or.inl rfl⟩

theorem weakKernel_witness_ne :
    weakKernel 0 0 !![1, 0, 0; 0, 0, 0; 0, 0, 0] 0 0 0 0 ≠ 0 := by
  simp [weakKernel, eVec, CAS16C03.sphereX, CAS16C03.sphereY, CAS16C03.sphereZ,
    Fin.sum_univ_three]

theorem shCos_witness_mem : shCos 4 4 ∈ shBand 4 :=
  Submodule.subset_span ⟨4, 4, le_rfl, le_rfl, Or.inl rfl⟩

end G16B
