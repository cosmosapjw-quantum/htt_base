# P11-A frozen targets (PORT-CAS-11, dense Gaussian GLS and deterministic remainder)

Frozen 2026-10-13T10:49Z, BEFORE any proof was written. Statement-only elaboration
check: `raw/compile_01_stmt.*` (exit 0, every body `sorry`; source sha256
`be485f2994d93361d8f6b953b65334adb4ce3494ed5b0ad73bf5f6b92ffdad8a`). The proof file
`lean/P11ADenseGLS.lean` (namespace `P11ADenseGLS`) must reproduce these statements
verbatim (namespace aside). Any deviation must be recorded in AUTHOR_RETURN.json.

## Source being formalized (verbatim)

* CAS_CONTRACT.json `CAS-11`: identity `M=(X^T C^-1 X)^-1 X^T C^-1; Cov=M C M^T; |M r|<=|M| b`;
  assumptions `known SPD C; rank13 X; fixed independent distances/selection; |r|<=b`.
* Card P11-A lean_steps: (1) SPD C → inverse/sqrt whitening and XᵀC⁻¹X positive definite;
  (2) build M, prove MX=I; (3) Gaussian pushforward mean/covariance MCMᵀ as an actual
  probability law; (4) deterministic ‖r‖≤b ⇒ ‖Mr‖≤‖M‖b and confidence/remainder separation.
  Acceptance: dense C cross-covariance included; known C and fixed selection kept in the theorem type.
  Pitfalls: no silent estimated-C substitution; no ridge hiding rank deficiency.
* PORT_MAP.json: has NO entry with id `PORT-CAS-11` (ports list F*/TBO-*/BIC-* only); the
  nearest owning implementation is `htt.infer.endpoint_cosmography.fit_endpoint_cosmography`
  (port TBO-02), whose remainder bound is `bias_bound = np.abs(influence) @ bounds`, i.e.
  componentwise `|(M r)_i| ≤ Σ_j |M_ij| b_j` with `|r_j| ≤ b_j`.

## Norm convention decision

The source `|M r| ≤ |M| b` is read, per the owning code, as the **componentwise** bound with
`|M|` the entrywise absolute matrix and `b` a per-row bound vector (R3a, primary). Two operator
norm corollaries are also frozen: ℓ∞ (Mathlib `Matrix.linftyOpNormedAddCommGroup`, max row
absolute sum; vectors with sup norm) R3b, and Euclidean ℓ2 operator norm
(`Matrix.Norms.L2Operator`) R3c.

## Scope encoded in the types

* `C : Matrix (Fin n) (Fin n) ℝ` is a fixed, known parameter with hypothesis `C.PosDef`
  (dense: no diagonal/block assumption; all cross-covariances allowed). No estimated C anywhere.
* `X : Matrix (Fin n) (Fin k) ℝ` fixed (fixed distances/selection = deterministic design rows),
  hypothesis `X.rank = k` (generic k; contract rank 13 is the instance R6). No ridge/jitter:
  rank deficiency is a negative control (R4), not regularized.
* Remainder `r` deterministic, entering the Gaussian mean only (not extra noise).

## Definitions

```lean
def gram (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) :
    Matrix (Fin k) (Fin k) ℝ := Xᵀ * C⁻¹ * X
def glsM (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) :
    Matrix (Fin k) (Fin n) ℝ := (gram C X)⁻¹ * Xᵀ * C⁻¹
def wrss (C : Matrix (Fin n) (Fin n) ℝ) (X : Matrix (Fin n) (Fin k) ℝ) (y : Fin n → ℝ)
    (θ : Fin k → ℝ) : ℝ := (y - X *ᵥ θ) ⬝ᵥ (C⁻¹ *ᵥ (y - X *ᵥ θ))
def linCLM (M : Matrix (Fin k) (Fin n) ℝ) :
    EuclideanSpace ℝ (Fin n) →L[ℝ] EuclideanSpace ℝ (Fin k) :=
  LinearMap.toContinuousLinearMap (Matrix.toEuclideanLin M)
def Xbad : Matrix (Fin 2) (Fin 2) ℝ := !![1, 1; 1, 1]
```

## Targets (exact statements; `C X` binders as above unless shown)

* R0 `mulVec_injective_of_rank_eq (X) (hX : X.rank = k) : Function.Injective X.mulVec`
* R1a `gram_posDef (C X) (hC : C.PosDef) (hX : X.rank = k) : (gram C X).PosDef`
* R1b `gram_isUnit_det (C X) (hC) (hX) : IsUnit (gram C X).det`
* R1c `gls_unbiased (C X) (hC) (hX) : glsM C X * X = 1`
* R1d `gls_normal_eq (C X) (hC) (hX) (y) : Xᵀ *ᵥ (C⁻¹ *ᵥ (y - X *ᵥ (glsM C X *ᵥ y))) = 0`
* R1e `gls_minimizes (C X) (hC) (hX) (y) (θ) : wrss C X y (glsM C X *ᵥ y) ≤ wrss C X y θ`
* R1f `gls_minimizer_unique (C X) (hC) (hX) (y) (θ) (h : wrss C X y θ = wrss C X y (glsM C X *ᵥ y)) : θ = glsM C X *ᵥ y`
* R1g `gls_moorePenrose_link (C X) (hC) (hX) (W) (hW : IsUnit W ∧ W * C * Wᵀ = 1) :
   G08AWhitening.IsMoorePenrose (W * X) (glsM C X * W⁻¹) ∧ ∀ y, (glsM C X * W⁻¹) *ᵥ (W *ᵥ y) = glsM C X *ᵥ y`
  (links to reviewed G08-A: `whitening_exists` supplies W; `gls_minimum` then applies)
* R2 `gls_covariance (C X) (hC) (hX) : glsM C X * C * (glsM C X)ᵀ = (gram C X)⁻¹`
* R3a `remainder_componentwise (M : Matrix (Fin k) (Fin n) ℝ) (r b) (hr : ∀ j, |r j| ≤ b j) (i) : |(M *ᵥ r) i| ≤ ∑ j, |M i j| * b j`
* R3b (local instance `Matrix.linftyOpNormedAddCommGroup`)
  `remainder_linfty (M) (r) (β) (hβ : 0 ≤ β) (hr : ∀ j, |r j| ≤ β) : ‖M *ᵥ r‖ ≤ ‖M‖ * β`
* R3c (`open scoped Matrix.Norms.L2Operator`)
  `remainder_l2 (M) (r : EuclideanSpace ℝ (Fin n)) (β) (hr : ‖r‖ ≤ β) : ‖(EuclideanSpace.equiv (Fin k) ℝ).symm (M *ᵥ r)‖ ≤ ‖M‖ * β`
* R3d `gls_decomposition (C X) (hC) (hX) (θ) (r e) : glsM C X *ᵥ (X *ᵥ θ + r + e) = θ + glsM C X *ᵥ r + glsM C X *ᵥ e`
* R3e `gls_bias_bound (C X) (hC) (hX) (θ) (r b) (hr : ∀ j, |r j| ≤ b j) (i) : |(glsM C X *ᵥ (X *ᵥ θ + r)) i - θ i| ≤ ∑ j, |glsM C X i j| * b j`
* R4a `gram_det_zero_of_rank_lt (C X) (h : X.rank < k) : (gram C X).det = 0` (any C)
* R4b `no_left_inverse_of_rank_lt (X) (h : X.rank < k) : ¬ ∃ M : Matrix (Fin k) (Fin n) ℝ, M * X = 1`
* R4c `negative_control : Xbad.rank < 2 ∧ (gram (1 : Matrix (Fin 2) (Fin 2) ℝ) Xbad).det = 0 ∧ ¬ ∃ M : Matrix (Fin 2) (Fin 2) ℝ, M * Xbad = 1`
* R5a `gaussian_linear_pushforward (C) (hC : C.PosSemidef) (m : EuclideanSpace ℝ (Fin n)) (M : Matrix (Fin k) (Fin n) ℝ) :
   (multivariateGaussian m C).map (linCLM M) = multivariateGaussian (linCLM M m) (M * C * Mᵀ)`
* R5b `gls_estimator_law (C X) (hC) (hX) (θ) (r) :
   (multivariateGaussian (WithLp.toLp 2 (X *ᵥ θ + r)) C).map (linCLM (glsM C X)) =
     multivariateGaussian (WithLp.toLp 2 (θ + glsM C X *ᵥ r)) (gram C X)⁻¹`
* R6 `rank13_instance (C) (X : Matrix (Fin n) (Fin 13) ℝ) (hC) (hX : X.rank = 13) (θ) (r b) (hr) :`
  conjunction of R1a, R1c, R1e (∀ y θ'), R2, R3e (∀ i), R5b at k = 13 (exact text in StatementCheck.lean).

Mathlib API used for R5: `ProbabilityTheory.multivariateGaussian` (Mathlib/Probability/Distributions/Gaussian/Multivariate.lean at the pin), `IsGaussian.ext`, `covarianceBilin_map`.

Not targeted: estimated covariance, coverage/confidence-interval probability statements beyond the
exact law R5b, rank 13 of the actual physical design (G09-B), any scientific admission.
