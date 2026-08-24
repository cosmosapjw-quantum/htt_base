# PR-314 post-execution adversarial science audit

## Audit identity

```yaml
schema: htt.post_execution_adversarial_audit.v1
audited_pull_request: 403
audited_head: 883a7cf41116e6740b1bac9b76a5e9c6b3fd188e
audited_tree: de7b83eab93a2fa49d7f1f052f37b2e43c11ecb6
audited_result:
  path: docs/generated/pr314_planck_pr3_smica_existing_result.json
  sha256: 898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97
execution_commit: b6411109a54d4f2ac05bc60cac270d936c1b9417
execution_tree: ab2d595e2d6246f5f3a5fa91e49694499d05276c
operating_profile: private_single_researcher_local_v1
security_or_antitamper_review: out_of_scope
```

## Final hostile verdict

```yaml
current_result_status: PROVISIONAL_SMICA_CONDITIONAL_DIAGNOSTIC
merge_as_final_scientific_result: false
preserve_as_executed_evidence: true
P0:
  - MASK_ORDER_PREBANDLIMIT_LEAKAGE_NOT_RULED_OUT
P1:
  - FEATURE_TAIL_ESTIMAND_NOT_SCIENCE_DIRECTION_REGISTERED
  - RAW_INPUT_AND_PAIR_LINEAGE_NOT_ACCEPTANCE_BOUND
  - FFP10_EXCHANGEABILITY_AND_SYSTEMATICS_CONDITIONALITY_UNQUANTIFIED
  - PR314_LOAD_BEARING_TESTS_NOT_IN_CLEAN_CI
  - COMPACT_REPLAY_NOT_FEATURE_LEVEL_PORTABLE
  - ACCUMULATED_EXECUTION_METHOD_PARTIALLY_BYPASSED
P2:
  - PIXWIN_RUNTIME_DOWNLOAD_NOT_FROZEN
  - CONDITIONAL_RANK_FIELD_NAMING_TOO_PVALUE_LIKE
  - HISTORICAL_PR_TERMINAL_DOCS_CONTAIN_PROVISIONAL_WORDING
```

The executed result is real and reproducible on the retained local inputs. It is not fabricated and it should not be deleted. It is not yet a stable Planck low-ell result because the primary reduction order has not passed the masked-region contamination oracle described below.

## What the executed result actually says

The observed SMICA feature-family rank is

\[
  \frac{19}{43}=\frac{133}{301}\simeq0.44186.
\]

Under the exact current operator and the exact 300 paired `SMICA CMB_i + SMICA noise_i` rows, the observation is not in a small global finite-rank tail. The smallest local ranks are:

```yaml
cl_l5: 16/301
multipole_l3_absdot_0: 20/301
cl_l4: 32/301
power_tensor_gap_l3: 19/43
family: 19/43
```

This is a negative conditional diagnostic, not evidence for an anomaly, source, geometry, Bianchi family, or global anisotropy. The result does not include Commander robustness, a joint component-separation covariance, a global response, Bayesian evidence, or cross-probe inference.

## Accumulated-methodology use audit

| Layer | Present in repository | Used by PR-314 | Hostile finding |
|---|---|---:|---|
| PR-288 Bayesian evidence/PPC/LOO | yes | no | no likelihood, posterior, evidence, PPC, or LOO result was produced |
| PR-289 exact full PLANCK admission | yes | no | PR-314 uses a custom SMICA slice plan rather than the 13-component lane |
| PR-304 cryptographic authorization | dormant | no | correctly omitted under the single-researcher policy |
| PR-305 attended executor semantics | yes | partial | confirmation/start/terminal ideas were reimplemented in a direct SMICA path instead of using one executor |
| PR-306 Planck operator | yes | yes | mask inverse, Majorana multipole vectors, feature order, FFP10 rank logic, and profiling are active |
| PR-307/312/313 CF4 methodology | yes | no | no CF4 data or affine-flow inference entered this result |
| PR-308 ACT methodology | yes | no | no ACT release or simulation result entered this result |
| PR-309 JWST-SN methodology | yes | no | no JWST row/covariance result entered this result |
| PR-310 HSC/KiDS methodology | yes | no | no spin-2 or cross-covariance result entered this result |
| PR-311 DESI methodology | yes | no | no DESI catalogue or mock result entered this result |
| Majorana multipole vectors | yes | yes | genuine projective roots are used rather than power-tensor poles |
| real-linear mask inverse | yes | yes, after pre-bandlimit | the ordering of mask application versus low-ell projection is the P0 |
| same observation/null operator | intended | partly | feature extraction after compact reduction is identical; high-resolution reduction is not mask-conditioned |
| full covariance | yes | validation only | covariance is validated but the finite family rank is empirical and covariance-free |
| observation-inclusive finite rank | yes | yes | exact 301-unit conservative rank is used |
| local/global partial identification | yes | no | no response or identified-set result is produced |
| theory VT/CAS propositions | yes | no | no theorem result enters this observational diagnostic |
| MIO/HTT separation | yes | firewall only | the absence of inference claims follows the firewall; no MIO/HTT quantity is computed |

## P0-001 — common-mask information enters too late

### Current operator order

The current preparation first takes a full-sky harmonic projection truncated at `lmax=5` and synthesizes an `Nside=16` map. The common temperature mask is applied only later, when the already band-limited map is passed through the mask-coupling inverse.

Schematically, the current path is

\[
T_{\rm full}\;\xrightarrow{B_{\ell\le5}}\;T_{\rm low}
\;\xrightarrow{W,\,M_W^{-1}}\;\widehat a_{2\ldots5}.
\]

If a foreground residual, processing artefact, or inpainted realization lives in a region later downweighted by `W`, its full-sky low-ell projection `B_{l<=5} c` has already spread over the whole sphere. A later cut-sky inverse cannot prove that contribution absent. The FFP10 `CMB+noise` rows do not contain the same unknown residual foreground realization, so observation/null exchangeability is not established for that leakage.

Planck 2018 explicitly provides a common confidence mask because significant residuals remain near the Galactic plane and point sources, and its component-separation paper notes both 300 noise-plus-systematics simulations and 999 CMB-only simulations with fixed pipeline weights. It also states that the best simulations retain few-percent relative biases to the data. References:

- [Planck 2018 IV, Sections 3.5 and 4.2](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html)
- [ESA Planck CMB map description](https://esdcdoi.esac.esa.int/doi/html/data/astronomy/planck/CMB_Maps.html)

### Required primary replacement

Estimate the retained low-ell coefficients directly from the high-resolution map on the admitted mask support:

\[
\widehat a
=
(Y^T W Y)^{-1}Y^T W\bigl(T-X_{0,1}\widehat\beta\bigr),
\]

where `Y` is the real harmonic design for `2 <= ell <= 5`, `X_{0,1}` is the monopole/dipole design, and all normal matrices and right-hand sides are accumulated in bounded pixel chunks. Apply the registered source-to-target beam/pixel transfer after this weighted fit. Use byte-identical code and mask for the observation and every null row.

The delivered full-sky/inpainted-map route may remain as a named robustness branch. The current `full-sky bandlimit then mask inverse` route may remain only as a legacy comparison branch.

### Mandatory RED/GREEN oracle

Inject arbitrarily large contamination exclusively into pixels whose common-mask weight is zero. For the new primary operator, the retained `ell=2..5` coefficients and all twelve features must remain unchanged within a registered tolerance. The current operator is expected to fail this oracle before the repair.

## P1 findings

### P1-001 — the estimand is a two-sided omnibus, not a literature-directed anomaly test

`calibrate_complete_synthetic_pool` uses `two-sided` for all twelve features. This is a valid generic outlier family, but low power, high alignment, and parity hypotheses do not all have the same natural tail. Preserve the current two-sided family as the frozen primary result. Before any directional reanalysis, register a feature-tail map from pre-existing physical/literature hypotheses without inspecting new ranks. Report the directed family only as a separately named sensitivity analysis.

### P1-002 — raw lineage is result-bound, not acceptance-bound

The attended acceptance binds the observed filename and byte size, while its raw SHA-256 is computed after the run starts. The final result records the actual hash, so this is not an anti-tamper issue. It is a scientific provenance gap. The repaired plan must bind the observed raw SHA-256 and an ordered manifest of every raw CMB/noise pair before execution.

### P1-003 — the finite rank is conditional on an imperfect simulation model

The 300 paired rows are the correct complete noise-bearing primary slice available for SMICA. They support an empirical conditional rank. They do not incorporate uncertainty in residual foregrounds, component-separation weights, or all data/simulation mismatch. Keep the 300-pair result primary, but add separately labelled sensitivity tiers:

1. 999 CMB-only rows for cosmic-variance-only sensitivity, never pooled with the primary rows;
2. a dependence-aware reuse/permutation analysis of the 300 noise rows if additional CMB sampling is desired;
3. mask/inpainting and component-separation robustness.

No secondary tier may be described as 999 independent CMB-plus-noise realizations.

### P1-004 — PR-314 tests are absent from clean pull-request CI

The exact pull-request workflow runs generic repository contracts and PR-309/310/311 cells, but it does not explicitly execute the three PR-314 test files or a committed-result replay. Add one existing-workflow step for:

```text
tests/integration/test_planck_pr3_admission_preparation.py
tests/integration/test_planck_pr3_current_stack.py
tests/integration/test_planck_pr3_operator.py
```

and a feature-level result/replay verification command.

### P1-005 — replay is raw-free but not portable

The committed replay JSON records a match, but an independent checkout cannot recompute it without the off-repo plan, compact null maps, covariance, mask, beam, and window files. Export a compact feature-level reproduction package containing:

```yaml
observed_feature_vector: [12 floats]
null_feature_matrix: [300, 12]
row_ids: [300 strings]
feature_order: [12 strings]
covariance: [12, 12]
tail_registry:
operator_and_input_hashes:
```

This package is small and sufficient to recompute every committed finite rank without raw Planck products.

### P1-006 — accumulated execution methodology is only partially reused

PR-314 correctly reuses the PR-306 scientific operator, but it introduces a direct SMICA acceptance/start/terminal path instead of the PR-305 dispatcher and bypasses the PR-289 full-lane identity. Do not create a new framework to fix this. Extract only the minimal shared attended-run helper required by the next real lane, or keep the direct path but add an explicit architecture test proving that no second science operator or rank implementation exists.

## P2 items

- Freeze the `healpy.pixwin` auxiliary data or record its exact downloaded file hash and version so a first run never depends on an unrecorded network fetch.
- Rename or annotate `finite_feature_family_p` as a conditional finite-rank fraction; it is not an unconditional calibrated probability.
- Do not spend a separate cleanup PR rewriting provisional wording in old PR deltas. Produce one capability/use matrix in the post-execution report and let future scientific PRs consume it.

## Development decision

```yaml
decision: REPAIR_AND_RERUN_BEFORE_SCIENTIFIC_ACCEPTANCE
preserve_PR314_result: true
PR314_result_role: legacy_operator_provisional_diagnostic
next_work_unit: PR-315
next_capability: PLANCK_SMICA_MASK_CONDITIONED_LOWELL_RERUN_AND_PORTABLE_FEATURE_REPLAY
DAG_rule:
  - append PR-315 after PR-314
  - do not reorder or rewrite any existing PR dependency
  - PR-315 requires PR-314 evidence whether PR-314 merges or closes with receipt
security_infrastructure: forbidden
Rust: forbidden_without_profiled_numeric_leaf
```

The next work unit must begin with failing scientific regression tests, not with a prose-only patch or another process framework.