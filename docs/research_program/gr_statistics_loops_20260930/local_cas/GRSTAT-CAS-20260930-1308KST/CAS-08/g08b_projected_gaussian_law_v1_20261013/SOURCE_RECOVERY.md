# G08-B source recovery

Task card: `HTT_ALL_OBLIGATIONS_20261011/tasks/G08-B.json`, read with `unzip -p`.
- Card bytes sha256: `37d0b82aa803b003c035c29086cd214f93d09517637b2d2682beaa9db4ab1ae5`.
- Package zip sha256: `2d0b6da9308ab43e070a620f49241640b5aa7c80c277e1f0857edea22bc4af6f`.
- Card `source_snapshot`: `a30d84c7918b54238a48fa62e2ef482f7e6d36fa`.
- Repository HEAD when this unit started: `d53c9ddde60d0646667ebb0cddd342aeb22b6253`. The checkout was dirty and was not modified outside this directory.

Directory state at start: this directory `T` did not exist. The earlier author process created no files, so there were no partial receipts and no `FROZEN_TARGETS.md` to inherit. Everything here was written by this author run.

## Card source paths

| path | sha256 | used for |
|---|---|---|
| `docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-08.json` | `3a89149e4e025298b35e5db550142c5b25351dc5aef5ee1071f29977030f8d3e` | see below |
| `.../CAS-08/c01_c02_projection_bridge_v1_20261011/RETURN.json` | `e36fc25e207bf067a4eebee255615a90ad61badc498abf3bc3602c7da73825e1` | the bridge `not_proved` list includes "Probabilistic covariance transformation or Gaussian/chi-square/coverage law". That is the gap closed here. |

What `CAS-08.json` supplies:
- `semantics.assumptions`: "Known positive-definite C; fixed nuisance F", "Gaussian native law for N1; true complete theta in frozen domain".
- `semantics.singular_loci`: "CONF-RANK0 coverage1" and "CONF-ESTIMATEDC no exactchi2".
- `full_theorem_boundary.additional_analytic_obligations[0]`: "Gaussian invariance and chi-square quantile".
- `uncontracted_research_targets[2]`: "At truth projected residual is sum_nu independent normal squares; quantile gives1-alpha fornu>0".
- `exclusions`: "No Wilks law".

The contract does **not** state the quantile convention: which side of the inequality, what happens at the endpoints, or the rank-0 rule. Its `research_provenance_hashes` entry names the theory note that does:

| path | sha256 (matches contract) |
|---|---|
| `docs/research_program/gr_statistics_loops_20260930/statistics/NATIVE_INFERENCE_THEOREMS.md` | `e215836882047c50a1a5ae6da605d62aa2c553d0de055e279eee3ce35ec8e322` |

Disclosure: the contract marks that file "orchestrator_identity_only" and lists `statistics/**` as a forbidden sibling path for *blind four-axis CAS execution*. This package task is not a blind CAS axis run. The dispatch explicitly asks that the "<= vs <", the alpha endpoints and the rank-0 case match the source, and this note is the only place they are stated. It was therefore read for §4, lines 39–92 of the current file. That read is a correlation, recorded here, and no four-axis CAS status is claimed.

### Recovered statements (NATIVE_INFERENCE_THEOREMS.md)

- **Line 41, model (4):** `y = m(θ*) + F β* + ε, ε ~ N_m(0,C)`.
- **Line 73:** `W=C^(-1/2), any fixed whitening matrix with WCW^T=I. Let P be the Euclidean orthogonal projector onto col(WF)^⊥.`
- **Line 75:** `ν = m-rank(F)`. Here m is the data dimension (Lean `n`).
- **Line 77:** `For 0<α<1 and ν>0, let qν,α be the (1-α) quantile of χ²_ν.` The endpoints α=0 and α=1 are excluded by the source.
- **Lines 79–80, (7):** `Q_y(θ) = || P W [y-m(θ)] ||²`, `Cα(y) = {θ∈Ω : Q_y(θ)≤qν,α}`. This is a **non-strict** `≤`.
- **Lines 82–86, (8):** `Pr_{θ*,β*}{θ*∈Cα(y)} = 1-α, uniformly in β*`. This is **equality**.
- **Line 90:** `If ν=0 set q=0; Cα=Ω and coverage is one.`
- **Line 92, proof sketch:**
  - PWF=0.
  - Wε has m independent standard normal coordinates.
  - Orthogonally diagonalize P into ν ones and m−ν zeros.
  - Q at θ* is a sum of ν independent squared standard normals.
- **Line 94:** the χ² law holds at the true complete θ. It is not a law for `min_θ Q`.
- **Lines 45 and 67:** these cover estimated C, selection, data-dependent remainder bounds and union bounds. They are excluded from this card, and the card pitfall "estimated C/selected F 법칙은 별도 theorem 없이 포함하지 않는다" excludes them too.

### Deterministic remainder (card lean_steps[3])
In the source, the remainder enters as part of the complete parameter `θ ∈ Ω`, the enlarged domain of §3 (lines 55–67). `m(θ*)` already includes it, so (8) needs no separate containment bound. Here this is encoded as a universal quantifier over the model map `m : Θ → ℝⁿ`, the domain `Ω`, and `θ* ∈ Ω`. The union bound `1-α-δ` on line 67, for remainder bounds estimated by a separate procedure, is **not** formalized.

## Reused, reviewed Lean sources (imported unchanged)

| source | sha256 | review |
|---|---|---|
| `.../CAS-08/c01_c02_projection_bridge_v1_20261011/ProjectionBridge.lean` | `440e3820a53a1bc12465975eaed331db2e9b4f7fbdc4e97d9d5c58a4c1cc2219` | PASS_SCOPED (RETURN.json) |
| `.../CAS-08/g08a_whitening_gls_v1_20261013/lean/G08AWhitening.lean` | `e62280213d23063cf4309aa8bdc814b2925f44f50cb81859f6b91bcb976bf045` | PASS_WITH_NOTES (REVIEW.md) |
| `.../CAS-08/g08a_whitening_gls_v1_20261013/lean/G08ACorollaries.lean` | `225e46da37dd6a8841c1dfae9e32488712c1dfdc548213a01d5d91653704b34e` | PASS_WITH_NOTES (REVIEW.md) |

Definitions used from them:
- `G08AWhitening.IsMoorePenrose` (G08AWhitening.lean:145).
- `projected_covariance` (:334).
- `residualProjector_eq` (:258), connecting the matrix `1 - A X` to the bridge's `starProjection` onto `(range A)ᗮ`.
- `residual_transpose` and `residual_idempotent` (:247, :251).
- `nu_eq` (G08ACorollaries.lean:34), giving `rank(WF) = rank F`.
- Bridge `P`, `K`, `responseRange` and `P_eq_subtype_projection` (ProjectionBridge.lean:32–43).

P12-A was consulted for the multivariateGaussian API pattern. It is at `theory_inference_port_20260930/.../PORT-CAS-12/gaussian_law_equality_v1_20261013/lean/P12GaussianLaw.lean`, sha256 `5a6ce15d…`, PASS_WITH_NOTES. Its theorems are **not imported**: the Mathlib lemmas it wraps are used directly. P11-A (dense GLS remainder) is not needed.

## Mathlib at the pin (fabf563a)

The following are present at the pin:
- `ProbabilityTheory.stdGaussian`, `multivariateGaussian`, `IsGaussian.ext`, `covarianceBilin_map`, `covarianceBilin_stdGaussian`, `map_pi_eq_stdGaussian`.
  - Source: Mathlib/Probability/Distributions/Gaussian/{Multivariate,CharFun}.lean.
  - Source: Mathlib/Probability/Moments/CovarianceBilin.lean:110.
- `iIndepFun_pi` and `iIndepFun_iff_map_fun_eq_pi_map` (Mathlib/Probability/Independence/Basic.lean:861, :892).
- `ProbabilityTheory.cdf`, `measure_cdf`, `StieltjesFunction.measure_singleton` (Mathlib/Probability/CDF.lean, MeasureTheory/Measure/Stieltjes.lean:545).
- `gammaMeasure a r` (Mathlib/Probability/Distributions/Gamma.lean:128).
- `OrthonormalBasis.starProjection_eq_sum_rankOne` (Mathlib/Analysis/InnerProductSpace/PiL2.lean:573).

Absent at the pin:
- **No chi-square distribution.** A search for `chiSq|chiSquared|chi_squared` in Mathlib found no hits.
- **No theorem identifying a sum of squared standard normals with `gammaMeasure (ν/2) (1/2)`.**

`chiSq ν` is therefore *defined* as the law of `∑_{i<ν} Z_i²` with `Z` distributed as the product of ν standard normals. That is the source's own wording: "sum of squares of precisely ν independent standard normals". The identification with the Gamma/χ² density, and with SciPy's numerical `chi2.ppf`, is an exact recorded gap. It is not claimed.

## Resume addendum (2026-10-14 author resume)

The first author run was cut off by a credit/rate limit after writing this file, `FROZEN_TARGETS.md` (v1, sha256 `7a7fbce302f1ac9af0d46a5ce8af37d05626f14e82b414253c08e3a8b78f7238`, snapshot `raw/FROZEN_TARGETS_v1.snapshot.md`, freeze time `2026-10-13T11:56:26Z`) and the three import receipts `compile_01..03` (all exit 0). The resumed author re-read the card, the frozen statements and the recovered source lines above, and kept the frozen statements unchanged because they match the source quantifiers, measure, `0<α<1`, `ν>0` / `ν=0` branches and the non-strict `≤`. All earlier receipts are kept.

Syntax-only deviations from the frozen text (no change to any statement's meaning):
- The probability-space binder `ℙ` collides with Mathlib's scoped notation `ℙ` (`Mathlib/Probability/Notation.lean:73`, activated by `open ProbabilityTheory`), so it is written as the escaped identifier `«ℙ»`. The binder name is still `ℙ` (the `#check` output prints `(ℙ : MeasureTheory.Measure Ω)`).
- The module header additionally opens `Filter Topology` for proof-internal notation (`𝓝[>]`, `Tendsto`). No frozen statement uses these namespaces.
- Non-frozen helper lemmas (`quad_aux`, `adjoint_toEuclideanCLM`, `measurable_Qstat`, `measurable_sumSq`, `frame_norm_sq`, `PW_annihilates`, `PW_covariance`, `map_PW`, `sum_castLE`, `stdGaussian_map_projector`, `coords_projector`, `coords_law_projector`, `law_norm_sq`, `projector_zero`, `Qstat_rank_zero`) are proved in the same module, and none of them is a hypothesis of a frozen theorem.

Extra Mathlib names used, all checked at the pin:
- `Measure.ext_of_charFun`, `charFun_stdGaussian`, `map_pi_eq_stdGaussian`.
- `measurePreserving_piFinSuccAbove` (MeasureTheory/Constructions/Pi.lean:801), `Measure.prod_apply_symm`.
- `noAtoms_gaussianReal` (Probability/Distributions/Gaussian/Real.lean:233), `Set.Finite.measure_zero`.
- `Monotone.tendsto_leftLim` (Topology/Order/LeftRightLim.lean:342), `StieltjesFunction.right_continuous`, `StieltjesFunction.measure_singleton`, `measure_cdf`, `ofReal_cdf`.
- `Measure.pi_map_eval` (MeasureTheory/Constructions/Pi.lean:378), `iIndepFun_iff_map_fun_eq_pi_map`.
