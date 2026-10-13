# R2-05 selected shared-latent density candidate

Candidate IMPLEMENTED / CONDITIONAL, pending fresh independent review. Owner HTT, claim tier C0, transfer source none. Actual CF4/CMB/DESI joint physical fit remains HOLD. Requested author gpt-6.1-sol/medium; observed model and effort UNKNOWN. Upstream proofs assumed valid by owner; no proof campaign was rerun. R2-06 native solver is absent and skipped by owner direction.

## Implementation and assumptions

`r7_joint_experiment.py` extends the existing `compose_joint_law`/`JointObservationLaw` path with `SelectedConditionalBlock`, `ProperSharedLatentRule`, and `SelectedJointDensityProvider`. The existing `JointGaussianProvider` API remains available. A block binds the original law specification and scope, source, ordered measurement IDs, ordered object IDs, selection identity, normalization definition and fixed observed count. The callback contract is a normalized selected conditional density with respect to the original full-dimensional Lebesgue measure dY. Its normalization, selection calibration and conditional independence are supplied scientific obligations, not inferred from strings or tests.

The provider either sums conditionally independent selected block log densities using an explicit source-bound independence assertion, or calls an explicitly normalized full joint conditional density on canonical unique Y. It then performs **one** logsumexp integration over the shared latent measure. Product-specific integration of a shared nuisance is not used. The supplied positive latent probabilities must already sum to one within 64 machine eps; missing or improper weights are refused. No fabricated count factor is added. Externally conditioning or profiling an already integrated shared latent is refused. Profile/objective kinds are refused in both block and joint callback declarations.

`DISCRETE_EXACT` denotes the exact finite-mixture model under the specified proper discrete prior. `CONTINUOUS_QUADRATURE` denotes a finite-mixture approximation to a continuous prior. It is explicitly labelled `SUPPLIED_CONTINUOUS_PRIOR_QUADRATURE_APPROXIMATION_NOT_CERTIFIED_EVIDENCE`; no continuous-law evidence admission or global integration-error certificate follows from the fixture reference agreement. A continuous physical application needs a source-bound controlled integrator/error contract or an explicitly accepted discrete model. This implementation does not reinterpret prior quadrature as measured physical support.

Exact duplicate bound laws are removed before density evaluation. Duplicate identity must preserve observations/order, live predictions, latent/conditioning and transfer scope. Incompatible partial overlaps are refused, including equal numbers with different object/source/scope identities. The block list is supplied in **deduplicated-law order**; provider canonical measurement order must match that order. Partial overlapping marginal densities are never multiplied or silently reduced. A source-bound explicit joint callback handles dependence between distinct canonical coordinates. There is no automatic arbitrary-overlap marginalizer.

The marginal mean is deliberately unavailable unless a future adapter supplies it. `JointObservationLaw.loglik` provides the normalized density; calling the joint `.mean` raises rather than manufacturing a zero prediction or confusing conditional means with a marginal mean. Constant-Gaussian identification/acceptance tools continue to refuse nonGaussian laws.

`r9_depth_law.selected_depth_law` is a separate typed adapter for this normalized density measure. It accepts fixed `DepthRepresentation`, original Y or bijective `(Y0,HY)`, and includes `-log|det T|` in the transformed density. The current anchored depth T has determinant one. Contrasts alone, fitted transport and unspecified/singular reference measures are refused. This is the same Y, never additional independent evidence; continuous quadrature approximation labels remain unchanged.

## Validation

Existing `/usr/bin/python` was used explicitly. First run: 22 PASS. Final affected run: **79 PASS in 7.24 s**. Raw logs and exact commands are retained in `raw/` and `COMMANDS.md`; neither run failed. Tests include independently evaluated finite shared-latent Laplace reference, direct continuous selected-Gaussian quadrature at a fixed fixture point, independent conditional and joint selection normalization, shared versus separate nuisance integrals, analytical dense Gaussian rank-one covariance and existing Gaussian-provider parity, repeated-data evidence invariance, source/object/value/scope/conditioning/prediction conflicts, profile/improper prior rejection, explicit dependent joint conditional callback, fixed-count metadata, manufactured shared-latent injection covariance and mean, and depth restoration/density-ratio invariance. Tolerances are fixed in the tests; normalization/injection checks do not establish actual-product coverage.

The first run and final affected run include existing joint, depth, Gaussian, catalogue-law and evidence-binding contracts. No unrelated historical test campaign was rerun.

## Source and claim audit

Read the R2 ZIP priority cards `NEXT_TASK.json`, `ANALYSIS_DAG.json`, `RESULTS.json`, `review/REVIEW_RESULT.json`, the R2-05 card and `research/REPO_REUSE.md`/`JOINT_COMPRESSION_AND_ERROR.md`, current runtime/AGENTS guidance, and R2-01/02/03 RETURNs. Exact local source and candidate hashes are in `RETURN.json`. The implementation uses the existing scientific package interfaces and library operations; no new external API assumption was needed.

The controller supplied a separate read-only official DESI DR1 BGS product-identity check: H5 SHA256 `7d398e75ad7ba5f939ae12fd5c694ae97ec5eb64fd3521eb1894a1106aba179f`, equal to the OBS-05 local summary, supported by the [official checksum list](https://data.desi.lbl.gov/public/dr1/vac/dr1/full-shape-bao-clustering/v1.0/data_v1.2/likelihood/dr1_vac_dr1_full-shape-bao-clustering_v1.0_data_v12_likelihood.sha256sum). This worker did not refetch it. It identifies a product; it does not supply a joint CF4/CMB/DESI law or alter historical OBS-05 evidence.

| Claim | Owner | Status | Evidence and ceiling |
|---|---|---|---|
| Source-bound finite-mixture density composition | HTT | IMPLEMENTED / CONDITIONAL | Numerical fixture tests; supplied normalization/selection/independence obligations |
| Gaussian limit and duplicate/depth preservation | HTT | CONDITIONAL | Independent references and existing-path tests, stated model and measure |
| Continuous physical-prior evidence | HTT | HOLD | Supplied quadrature is not a controlled global error contract |
| Actual cross-product physical fit | HTT | HOLD | Joint shared-sky/object/calibration/velocity law absent |

Missing inputs remain the actual full joint measurement/selection law and source-bound shared priors: CF4 all-method source/selection and joint modulus/redshift/grouping/flow calibration; CMB physical dipole/angular mean, omission treatment, released-product processor and shared-sky cross-product law; DESI window/mock/selection and cross-product overlap/calibration law; and any controlled continuous-prior integration needed for physical evidence. Component product identity and C0 diagnostics do not supply these inputs. Same-sky CMB products are not independent measurements. No native family identification, MIO posterior, fabricated zero physics, or native transfer claim is made.

No commit, push, PR, status-ledger change or scientific admission was performed by this writer. Candidate is frozen for the separate reviewer; scoped review remains pending.
