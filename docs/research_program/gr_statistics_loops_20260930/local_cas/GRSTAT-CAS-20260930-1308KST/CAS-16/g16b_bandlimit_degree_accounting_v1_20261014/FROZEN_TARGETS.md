# G16-B frozen targets (written before any proof compile)

Module: `lean/G16BBandlimit.lean`, namespace `G16B`, `import FullBridge` (C03, unchanged).
Toolchain: Lean 4.31.0, mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, Lake project
`/home/cosmosapjw/lean_oracles/viii_oracle`.

## Definitions (frozen; see SOURCE_RECOVERY.md for provenance)

```lean
abbrev ChartFn := ℝ → ℝ → ℝ                       -- (μ, φ) ↦ value, chart of S²

def cartMonomials (D : ℕ) : Set ChartFn :=
  {f | ∃ a b c : ℕ, a + b + c ≤ D ∧ f = CAS16C03.monomial a b c}
noncomputable def cartSpan (D : ℕ) : Submodule ℝ ChartFn := Submodule.span ℝ (cartMonomials D)

noncomputable def legendreP (l : ℕ) : Polynomial ℝ :=            -- Rodrigues
  Polynomial.C (1 / ((2 : ℝ) ^ l * (Nat.factorial l : ℝ))) *
    Polynomial.derivative^[l] ((Polynomial.X ^ 2 - 1) ^ l)
noncomputable def assocLegendrePoly (l m : ℕ) : Polynomial ℝ := Polynomial.derivative^[m] (legendreP l)
noncomputable def shCos (l m : ℕ) : ChartFn := fun μ φ =>
  Real.sqrt (1 - μ ^ 2) ^ m * (assocLegendrePoly l m).eval μ * Real.cos ((m : ℝ) * φ)
noncomputable def shSin (l m : ℕ) : ChartFn := fun μ φ =>
  Real.sqrt (1 - μ ^ 2) ^ m * (assocLegendrePoly l m).eval μ * Real.sin ((m : ℝ) * φ)
def shGenerators (L : ℕ) : Set ChartFn :=
  {f | ∃ l m : ℕ, m ≤ l ∧ l ≤ L ∧ (f = shCos l m ∨ f = shSin l m)}
noncomputable def shBand (L : ℕ) : Submodule ℝ ChartFn := Submodule.span ℝ (shGenerators L)

noncomputable def eVec (μ φ : ℝ) : Fin 3 → ℝ :=
  ![CAS16C03.sphereX μ φ, CAS16C03.sphereY μ φ, CAS16C03.sphereZ μ]

-- (B5) weak-residual angular kernel, component (i,j):
-- [4H - σ:ee] e_i e_j + a_i e_j + e_i a_j + (σe)_i e_j + e_i (σe)_j
noncomputable def weakKernel (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ)
    (i j : Fin 3) : ChartFn := fun μ φ =>
  (4 * H - ∑ k, ∑ l, σ k l * eVec μ φ k * eVec μ φ l) * (eVec μ φ i * eVec μ φ j)
    + (a i * eVec μ φ j + eVec μ φ i * a j)
    + ((∑ k, σ i k * eVec μ φ k) * eVec μ φ j + eVec μ φ i * (∑ k, σ j k * eVec μ φ k))

noncomputable def momentIntegrand (I : ChartFn) (i j : Fin 3) : ChartFn :=          -- (B3) M
  fun μ φ => I μ φ * (eVec μ φ i * eVec μ φ j)
noncomputable def weakResidualIntegrand (I : ChartFn) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) : ChartFn :=                      -- (B5) brightness part
  fun μ φ => I μ φ * weakKernel H a σ i j μ φ
noncomputable def collisionIntegrand (C : ChartFn) (i j : Fin 3) : ChartFn :=       -- C_2
  fun μ φ => C μ φ * (eVec μ φ i * eVec μ φ j)
noncomputable def transportIntegrand (T : ChartFn) (i j : Fin 3) : ChartFn :=       -- T_2, T = 𝒟I
  fun μ φ => T μ φ * (eVec μ φ i * eVec μ φ j)
noncomputable def residualIntegrand (I C T : ChartFn) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) : ChartFn :=                      -- full (B5) R_ij integrand
  fun μ φ => collisionIntegrand C i j μ φ - transportIntegrand T i j μ φ
    - weakResidualIntegrand I H a σ i j μ φ

def Dstar (L LC LT : ℕ) : ℕ := max (L + 4) (max (LC + 2) (LT + 2))

noncomputable def quadRule (f : ChartFn) : ℝ :=
  (1 / 2 : ℝ) * ∑ r : Fin 5, CAS16C03.gl5Weight r *
    ((1 / 9 : ℝ) * ∑ j : Fin 9, f (CAS16C03.gl5Node r) (CAS16C03.azimuth 9 j))
noncomputable def sphereMeanFn (f : ChartFn) : ℝ :=
  (1 / (4 * Real.pi) : ℝ) * ∫ μ in (-1 : ℝ)..1, ∫ φ in (0 : ℝ)..(2 * Real.pi), f μ φ
```

## Targets

T1 (scalar SH bandlimit ⊆ restricted Cartesian polynomial span, the direction needed):
```lean
theorem shBand_le_cartSpan (L : ℕ) : shBand L ≤ cartSpan L
```
T2 (product-degree lemma, membership level):
```lean
theorem mul_mem_cartSpan {A B : ℕ} {f g : ChartFn}
    (hf : f ∈ cartSpan A) (hg : g ∈ cartSpan B) : f * g ∈ cartSpan (A + B)
theorem cartSpan_mono {A B : ℕ} (h : A ≤ B) : cartSpan A ≤ cartSpan B
```
T3 (actual angular factors):
```lean
theorem eiej_mem (i j : Fin 3) : (fun μ φ => eVec μ φ i * eVec μ φ j) ∈ cartSpan 2
theorem weakKernel_mem (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    weakKernel H a σ i j ∈ cartSpan 4
```
T4 (increments +4, +2, +2 as span membership of the actual integrands, all L, LC, LT, H, a, σ, i, j):
```lean
theorem weakResidual_mem {L : ℕ} {I : ChartFn} (hI : I ∈ shBand L) (H : ℝ) (a : Fin 3 → ℝ)
    (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    weakResidualIntegrand I H a σ i j ∈ cartSpan (L + 4)
theorem moment_mem {L : ℕ} {I : ChartFn} (hI : I ∈ shBand L) (i j : Fin 3) :
    momentIntegrand I i j ∈ cartSpan (L + 2)
theorem collision_mem {LC : ℕ} {C : ChartFn} (hC : C ∈ shBand LC) (i j : Fin 3) :
    collisionIntegrand C i j ∈ cartSpan (LC + 2)
theorem transport_mem {LT : ℕ} {T : ChartFn} (hT : T ∈ shBand LT) (i j : Fin 3) :
    transportIntegrand T i j ∈ cartSpan (LT + 2)
```
T5 (D* accounting with actual membership):
```lean
theorem dstar_membership {L LC LT : ℕ} {I C T : ChartFn}
    (hI : I ∈ shBand L) (hC : C ∈ shBand LC) (hT : T ∈ shBand LT)
    (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    momentIntegrand I i j ∈ cartSpan (Dstar L LC LT) ∧
    weakResidualIntegrand I H a σ i j ∈ cartSpan (Dstar L LC LT) ∧
    collisionIntegrand C i j ∈ cartSpan (Dstar L LC LT) ∧
    transportIntegrand T i j ∈ cartSpan (Dstar L LC LT) ∧
    residualIntegrand I C T H a σ i j ∈ cartSpan (Dstar L LC LT)
```
T6 (linearity wrapper of the accepted C03 theorem):
```lean
theorem quadRule_monomial (a b c : ℕ) : quadRule (CAS16C03.monomial a b c) = CAS16C03.productRule a b c
theorem sphereMeanFn_monomial (a b c : ℕ) : sphereMeanFn (CAS16C03.monomial a b c) = CAS16C03.sphereMean a b c
theorem quadRule_exact_cartSpan8 {f : ChartFn} (hf : f ∈ cartSpan 8) : quadRule f = sphereMeanFn f
```
T7 (instance (L,LC,LT) = (4,6,4), actual integrands; plus C3 arithmetic at this instance):
```lean
theorem dstar_464 : Dstar 4 6 4 = 8
theorem c3_arith_464 : (Dstar 4 6 4 + 1 + 1) / 2 ≤ 5 ∧ Dstar 4 6 4 + 1 ≤ 9 ∧ Dstar 4 6 4 ≤ 2 * 5 - 1
theorem actual_integrands_exact_464 {I C T : ChartFn}
    (hI : I ∈ shBand 4) (hC : C ∈ shBand 6) (hT : T ∈ shBand 4)
    (H : ℝ) (a : Fin 3 → ℝ) (σ : Matrix (Fin 3) (Fin 3) ℝ) (i j : Fin 3) :
    quadRule (momentIntegrand I i j) = sphereMeanFn (momentIntegrand I i j) ∧
    quadRule (weakResidualIntegrand I H a σ i j) = sphereMeanFn (weakResidualIntegrand I H a σ i j) ∧
    quadRule (collisionIntegrand C i j) = sphereMeanFn (collisionIntegrand C i j) ∧
    quadRule (transportIntegrand T i j) = sphereMeanFn (transportIntegrand T i j) ∧
    quadRule (residualIntegrand I C T H a σ i j) = sphereMeanFn (residualIntegrand I C T H a σ i j)
```
T8 (general arithmetic only: the ceiling form of C3 is equivalent to `2 N_μ - 1 ≥ D`):
```lean
theorem c3_ceil_iff (D N : ℕ) : (D + 1 + 1) / 2 ≤ N ↔ D + 1 ≤ 2 * N
```

## Non-vacuity witnesses / controls

```lean
theorem one_mem_shBand (L : ℕ) : (fun _ _ => (1 : ℝ)) ∈ shBand L       -- hypotheses satisfiable
theorem weakKernel_witness_ne :                                        -- kernel not identically 0
    weakKernel 0 0 !![1, 0, 0; 0, 0, 0; 0, 0, 0] 0 0 0 0 ≠ 0
theorem shCos_witness_mem : shCos 4 4 ∈ shBand 4                       -- a genuine ℓ = m = 4 harmonic
```
Negative controls already proved and only cited (not re-executed as targets): C03
`CAS16C03.radialFailure` (GL4, μ⁸) and `CAS16C03.azimuthFailure` (Nφ = 8, cos⁸φ).

## Boundary / quantifier notes

* Quantifiers: T1–T5 are universal in `L, LC, LT` and in `H, a, σ` (σ any real 3×3 matrix; the
  physical symmetric trace-free shear is a special case), `i, j`. No finite instance is labelled general.
* T6/T7 are the fixed finite rule GL5 × Nφ=9 only; they do not assert C3 sufficiency for other orders.
* Domain/measure: chart `[-1,1] × [0,2π]`, `dμ dφ / 4π` (C03). Spin quadrature excluded.
* Increments are upper bounds (membership); sharpness (that +4,+2,+2 cannot be lowered) is not claimed.
