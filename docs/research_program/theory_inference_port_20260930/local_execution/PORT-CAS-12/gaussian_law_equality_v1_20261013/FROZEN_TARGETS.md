# P12-A frozen targets (PORT-CAS-12, CAS-12)

Frozen before any proof attempt. Source contract identity: `N(mu1,C1)=N(mu2,C2) iff mu1=mu2 and C1=C2`;
assumptions: same finite measurement space; same conditioning; states separately admissible.

Toolchain: Lean 4.31.0, Mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`, cwd `/home/cosmosapjw/lean_oracles/viii_oracle`, `lean -R`.

Lean namespace `P12GaussianLaw`; `open MeasureTheory ProbabilityTheory Matrix`; `variable {n : ℕ}`.
The Gaussian law is Mathlib's `ProbabilityTheory.multivariateGaussian μ S`
(= `(stdGaussian (EuclideanSpace ℝ ι)).map (fun x ↦ μ + toEuclideanCLM (CFC.sqrt S) x)`,
Mathlib/Probability/Distributions/Gaussian/Multivariate.lean).

## Encoding of the contract premises

- "same finite measurement space": both laws are measures on the single type
  `EuclideanSpace ℝ (Fin n)` (same `n`, same coordinate order). Different spaces cannot even be
  compared by `=` in Lean; nothing is claimed about them.
- "same conditioning": encoded only by using one fixed measurable space/coordinate frame; no
  conditioning operation is formalized (caller declaration in the owning Python code).
- "states separately admissible": two independent hypotheses `S1.PosSemidef`, `S2.PosSemidef`
  (singular, rank-deficient and zero covariance allowed). G5 shows the premise is load-bearing.

## G1 law equality iff parameter equality

```lean
theorem law_eq_iff {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef) :
    multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2
```
Forward: first moments (`∫ x, x`) and coordinate covariances (`cov[x i, x j]`), whose integrability
is supplied by `IsGaussian` (Fernique). Converse: both sides are the same affine pushforward of
the common standard Gaussian.

Corollary (rank strata):
```lean
theorem rank_eq_of_law_eq {μ1 μ2 : EuclideanSpace ℝ (Fin n)} {S1 S2 : Matrix (Fin n) (Fin n) ℝ}
    (h1 : S1.PosSemidef) (h2 : S2.PosSemidef)
    (h : multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2) : S1.rank = S2.rank
```

## G2 moments of the law (PSD `S`, including `S = 0`)

```lean
theorem mean_of_law (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ) :
    ∫ x, x ∂(multivariateGaussian μ S) = μ
theorem mean_coord_of_law (μ : EuclideanSpace ℝ (Fin n)) (S : Matrix (Fin n) (Fin n) ℝ)
    (i : Fin n) : ∫ x, x i ∂(multivariateGaussian μ S) = μ i
theorem covariance_of_law (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (i j : Fin n) :
    cov[fun x ↦ x i, fun x ↦ x j; multivariateGaussian μ S] = S i j
theorem covarianceBilin_of_law (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : S.PosSemidef) (x y : EuclideanSpace ℝ (Fin n)) :
    covarianceBilin (multivariateGaussian μ S) x y = x ⬝ᵥ S *ᵥ y
theorem centered_second_moment_of_law (μ : EuclideanSpace ℝ (Fin n))
    {S : Matrix (Fin n) (Fin n) ℝ} (hS : S.PosSemidef) (i j : Fin n) :
    ∫ x, (x i - μ i) * (x j - μ j) ∂(multivariateGaussian μ S) = S i j
```
(The mean statements need no PSD premise.)

## G3 zero covariance

```lean
theorem zero_covariance (μ : EuclideanSpace ℝ (Fin n)) :
    multivariateGaussian μ (0 : Matrix (Fin n) (Fin n) ℝ) = Measure.dirac μ
```

## G4 singular examples (dimension 2, rank-1 PSD)

```lean
noncomputable def Sa : Matrix (Fin 2) (Fin 2) ℝ := Matrix.diagonal ![1, 0]
noncomputable def Sb : Matrix (Fin 2) (Fin 2) ℝ := Matrix.diagonal ![0, 1]
noncomputable def e1 : EuclideanSpace ℝ (Fin 2) := EuclideanSpace.single 1 1
theorem Sa_posSemidef : Sa.PosSemidef
theorem Sb_posSemidef : Sb.PosSemidef
theorem Sa_rank : Sa.rank = 1
theorem Sb_rank : Sb.rank = 1
theorem singular_example :
    multivariateGaussian 0 Sa ≠ multivariateGaussian e1 Sa ∧
    multivariateGaussian 0 Sa ≠ multivariateGaussian 0 Sb ∧
    multivariateGaussian (0 : EuclideanSpace ℝ (Fin 2)) Sa ≠ multivariateGaussian 0 0
theorem mean_only_comparison_insufficient :
    ∃ (μ : EuclideanSpace ℝ (Fin 2)) (S1 S2 : Matrix (Fin 2) (Fin 2) ℝ),
      S1.PosSemidef ∧ S2.PosSemidef ∧ S1.rank = 1 ∧ S2.rank = 1 ∧
      multivariateGaussian μ S1 ≠ multivariateGaussian μ S2
theorem covariance_only_comparison_insufficient :
    ∃ (μ1 μ2 : EuclideanSpace ℝ (Fin 2)) (S : Matrix (Fin 2) (Fin 2) ℝ),
      S.PosSemidef ∧ S.rank = 1 ∧ multivariateGaussian μ1 S ≠ multivariateGaussian μ2 S
```
Note: `e1` is a mean shift along the null direction of `Sa` (the law is supported on a line
through the mean in direction `e0`); the shift is still detected.

## G5 non-PSD caveat

```lean
theorem non_psd_eq_dirac (μ : EuclideanSpace ℝ (Fin n)) {S : Matrix (Fin n) (Fin n) ℝ}
    (hS : ¬ S.PosSemidef) : multivariateGaussian μ S = Measure.dirac μ
noncomputable def N1 : Matrix (Fin 1) (Fin 1) ℝ := Matrix.diagonal (fun _ ↦ -1)
theorem non_psd_caveat :
    ¬ N1.PosSemidef ∧ N1 ≠ 0 ∧
      multivariateGaussian (0 : EuclideanSpace ℝ (Fin 1)) N1 = multivariateGaussian 0 0
theorem law_eq_iff_needs_psd :
    ¬ ∀ (μ1 μ2 : EuclideanSpace ℝ (Fin 1)) (S1 S2 : Matrix (Fin 1) (Fin 1) ℝ),
      (multivariateGaussian μ1 S1 = multivariateGaussian μ2 S2 ↔ μ1 = μ2 ∧ S1 = S2)
```

## Adjustments relative to the dispatch wording

- G2 "covariance matrix is S" is delivered both as coordinate covariances `cov[x i, x j] = S i j`,
  as the Mathlib covariance bilinear form `x ⬝ᵥ S *ᵥ y`, and as an explicit centered second
  moment integral. G2 mean is stated without a PSD premise (it holds for all `S`).
- G4 adds the zero-vs-rank-1 pair and existential "insufficiency" forms; G5 adds the formal
  statement that the unconditional iff is false (N1 collapses to the zero-covariance Dirac law).
- Rank-strata corollary added under G1.

## Not claimed

Global physical injectivity; different conditioning or measurement spaces; non-Gaussian laws;
full PORT-CAS-12; scientific admission.
