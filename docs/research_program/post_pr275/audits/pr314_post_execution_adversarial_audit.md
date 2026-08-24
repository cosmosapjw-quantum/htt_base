# PR-314 post-execution adversarial science audit

## Audit identity

```yaml
schema: htt.post_execution_adversarial_audit.v2
audited_pull_request: 403
audited_branch: changeset/pr314-planck-pr3-attended-analysis-20260824
audited_head: 883a7cf41116e6740b1bac9b76a5e9c6b3fd188e
audited_tree: de7b83aac8a5357e9cfee518924ab6c0a0972fb3
audited_result:
  path: docs/generated/pr314_planck_pr3_smica_existing_result.json
  sha256: 898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97
audited_replay:
  path: docs/generated/pr314_planck_pr3_smica_existing_replay.json
  state: REPLAY_MATCH
science_execution_commit: b6411109a54d4f2ac05bc60cac270d936c1b9417
science_execution_tree: ab2d595e2d6246f5f3a5fa91e49694499d05276c
operating_profile: private_single_researcher_local_v1
security_or_antitamper_review: out_of_scope
fast_path_instruction: USER_APPROVED_AND_INTENTIONAL
```

## Executive verdict

```yaml
fast_path:
  SMICA_only: accepted_scope
  exact_300_CMB_plus_noise_pairs: accepted_scope
  no_Commander: accepted_scope
  no_999_CMB_only_pooling: correct
  focused_validation_instead_of_full_repo_suite: accepted_instruction

current_result:
  status: ACCEPTED_AS_EXECUTED_DELIVERED_PRODUCT_CONDITIONAL_NEGATIVE_DIAGNOSTIC
  preserve_as_evidence: true
  merge_as_executed_evidence: true
  merge_as_mask_conditioned_or_component_robust_result: false
  publication_ready_planck_result: false

scientific_findings:
  P0:
    - CUT_SKY_MONOPOLE_DIPOLE_NUISANCE_NOT_JOINTLY_PROFILED
  P1:
    - COMMON_MASK_DOES_NOT_CURRENTLY_DEFINE_THE_PRIMARY_ESTIMAND
    - FEATURE_TAIL_ESTIMAND_NOT_PHYSICALLY_DIRECTED
    - RAW_OBSERVATION_AND_PAIR_MANIFEST_NOT_ACCEPTANCE_BOUND
    - FFP10_RANK_IS_SIMULATION_CONDITIONAL
    - PR314_LOAD_BEARING_TESTS_NOT_EXPLICIT_CLEAN_CI_CELLS
    - FEATURE_LEVEL_PORTABLE_REPLAY_MISSING
  P2:
    - DIRECT_SMICA_RUNNER_PARTIALLY_DUPLICATES_ATTENDED_EXECUTION_PATH
    - PIXWIN_RUNTIME_AUXILIARY_NOT_FROZEN
    - CONDITIONAL_RANK_FIELD_NAMING_TOO_PVALUE_LIKE
```

The intentional fast path is not a defect. The exact scientific object produced by
PR-314 is a finite-rank diagnostic of the delivered full-sky/inpainted Planck
PR3 SMICA product under one frozen 12-feature, two-sided operator and exactly
300 released CMB-plus-noise rows. It is a legitimate negative conditional
result. It is not yet a common-mask-conditioned result, a Commander-robust
Planck result, an unconditional probability statement, or an HTT/Bianchi
inference.

The follow-up must not retroactively choose a different primary estimator
because it produces a more interesting observed rank. PR-314 remains frozen as
the delivered-product branch. PR-315 adds a mathematically cleaner
mask-conditioned branch, compares it with the frozen result, and reports both.

## Scientific result

The observation-inclusive family rank is

\[
p_{\rm family}^{\rm finite}
 = \frac{133}{301}
 = \frac{19}{43}
 \simeq 0.4418604651.
\]

The exact current 300-row SMICA CMB-plus-noise ensemble therefore does not place
the observation in a small global tail for the frozen 12-feature two-sided
family.

The smallest local finite ranks are

```yaml
cl_l5: 16/301              # approximately 0.05316
multipole_l3_absdot_0: 20/301  # approximately 0.06645
power_tensor_gap_l3: 19/43
cl_l4: 32/43
family: 133/301
```

No local entry survives the empirical family scan as a small global tail. This
does **not** prove statistical isotropy in general. It says only that this
preselected SMICA-only feature family did not find a global outlier under the
current conditional simulation ensemble.

The covariance matrix is full rank, `12/12`. Its diagonal-standardized
condition number is approximately `1279.99`; its raw condition number is
approximately `1.14e10`. The covariance is validated and replay-checked, but it
is not used to whiten the finite-rank scan. It therefore establishes numerical
feature support, not a covariance-weighted likelihood or stronger significance.

## Why the 300-pair fast path is defensible

Planck 2018 provides 300 noise-plus-systematics simulations and 999 CMB-only
simulations. The component-separation pipelines use fixed weights for the
simulations, making the CMB and noise contributions linearly combinable. The
intentional pairing of the first 300 released CMB rows with the 300 SMICA
noise/systematics rows is therefore a defensible, complete noise-bearing fast
slice.

Primary reference:

- Planck Collaboration IV (2020), Sections 3.5 and 4.4:
  https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html
- ESA PR3 component-separated CMB maps:
  https://esdcdoi.esac.esa.int/doi/html/data/astronomy/planck/CMB_Maps.html

The same reference also reports few-percent simulation biases and stresses that
a statistic must be checked for sensitivity to data/simulation mismatch. The
rank is therefore conditional on this simulation model. The 999 CMB-only rows
are a separate sensitivity tier and must never be pooled with the 300 primary
rows or described as additional independent CMB-plus-noise realizations.

## Stack-wide methodology and realized-capability audit

| Work unit | Repository capability added or repaired | Used by PR-314? | Actual effect on the executed result |
|---|---|---:|---|
| PR-281 | orbit/anisotropy-type acceptance | no | no orbit-type or family classification enters the run |
| PR-282 | exact parity readiness and dependent e-value merge | feature only, not method | one parity-ratio feature is measured; the exact P-equivariance test and e-value merger are not executed |
| PR-283 | covariance-whitened weak-identification abstention and response-geometry contracts | no numerical use | only the general claim firewall survives; no response or identified set is computed |
| PR-284 | finite depth-path calibration | no | no depth-path statistic enters Planck SMICA |
| PR-285/286 | Pillar-T/Pillar-S adjudication | no | no theorem/adjudication result enters this run |
| PR-287 | blind-replay containment | partial concept only | PR-314 performs a compact replay, but not through the full PR-287 challenge/truth execution route |
| PR-288 | analytic/Dynesty/Sobol evidence, PPC and fold-refit LOO semantics | no | no likelihood, posterior, evidence, PPC or LOO result |
| PR-300/302 | one-command readiness and PR-151 producer quarantine | boundary only | PR-151 historical producers remain excluded; no old DESI result enters the run |
| PR-289/303 | exact six-lane data identity and admission replay | no full-lane use | PR-314 uses a custom SMICA slice plan instead of the canonical 13-component PLANCK admission |
| PR-304 | cryptographic human authorization contract | no, intentionally dormant | correctly excluded under `private_single_researcher_local_v1` |
| PR-305 | minimal attended executor, confirmation, lock, start/terminal records | partial | the direct SMICA path reimplements the main ideas instead of entering through the shared dispatcher |
| PR-306 | Planck beam/pixel commonization, real-linear mask inverse, Majorana vectors, features, FFP10 finite rank and profiling | yes | this is the main scientific implementation used by PR-314 |
| PR-307/312/313 | CF4 operator attempt, failure evidence and closeout | no | no CF4 catalogue, affine flow or identified set enters the result |
| PR-308 | ACT DR6 operator | no | no ACT data or simulation result |
| PR-309 | JWST-SN row/covariance operator | no | no JWST-SN rows or competitor geometry |
| PR-310 | HSC/KiDS spin-2 operator | no | no shear/tomographic result |
| PR-311 | DESI successor-formalism operator | no | no DESI catalogue or mocks |
| PR-314 | SMICA-only observed fast path | yes | the only observed-data result in this execution |
| Majorana multipole-vector method | implemented in PR-306 | yes | genuine projective roots are used; power-tensor poles are not substituted |
| full matched SMICA/Commander covariance | implemented synthetically | no | unavailable in the SMICA-only run |
| observation-inclusive finite rank | implemented | yes | exact 301-unit conservative rank |
| response-rank/local-global discrimination | implemented synthetically | no | `NOT_COMPUTED_SMICA_ONLY`; global response remains missing |
| MIO/HTT ownership separation | implemented | firewall only | prevents diagnostic ranks from being called evidence or posterior |
| native Bianchi atlas/transfer | absent | no | family identification remains blocked |

## Methodological implementation verdict

### Implemented and actually active

- Planck PR3 SMICA map and exact 300-row CMB-plus-noise processing;
- K_CMB to microK_CMB conversion;
- frozen `ell=2..5` feature family;
- non-amplifying beam/pixel transfer;
- real-linear low-ell mask coupling inverse;
- genuine Majorana multipole vectors;
- exact feature order;
- full 12-by-12 empirical covariance validation;
- observation-inclusive local and family finite ranks;
- exact compact-map replay of the committed result;
- explicit SMICA-only, diagnostic-only and pre-native-atlas claim ceiling.

### Implemented in the repository but not used by this result

- Commander and matched same-sky joint covariance;
- local response rank and local/global partial identification;
- Bayesian evidence, PPC and LOO;
- full PR-289 PLANCK admission;
- parity e-value merger;
- CF4, ACT, JWST-SN, HSC/KiDS and DESI operators;
- cross-probe synthesis;
- native transfer, geometry detection and Bianchi-family classification.

### Claimed in prose more strongly than implemented

- “common-mask” can be read as if zero-weight pixels cannot affect the result;
  the current primary statistic is instead conditional on the delivered
  full-sky/inpainted map before the later low-resolution mask inverse;
- “deconvolved `ell=2..5` coefficients” do not yet have a known-alm oracle that
  profiles monopole/dipole jointly with the retained band on the cut sky;
- “reproducible replay” currently means replay on retained off-repo compact
  products, not a portable feature-level package contained in the repository.

## P0-001 — monopole/dipole nuisance is not jointly profiled with the retained band

### Current sequence

The raw full-sky map is first projected to `ell<=5` and synthesized at
`Nside=16`. `_process_map` then:

1. fits monopole and dipole on mask support;
2. subtracts those full-sky `ell<=1` templates;
3. computes a full-sky harmonic transform;
4. applies the common mask;
5. inverts a coupling matrix containing only `ell=2..5`.

On a cut sky, the nuisance basis \(X_{0,1}\) and retained basis \(Y_{2:5}\) are
not orthogonal under \(W\). Sequentially estimating

\[
\widehat\beta=(X^T W X)^{-1}X^TWT
\]

and then applying an inverse built only for \(Y\) does not in general recover
the same retained coefficients as the joint model. The residual nuisance
component can leak through the mask into the retained pseudo-coefficients.

The correct primary cut-sky estimator must solve the joint system

\[
D = [X_{0,1}\;Y_{2:5}],\qquad
\widehat\theta=(D^T W D)^{-1}D^TW T,
\]

and retain the \(Y_{2:5}\) block. An exactly equivalent
Frisch-Waugh-Lovell implementation is allowed only if both the data and the
retained design are residualized with respect to \(X_{0,1}\).

### Required RED/GREEN oracles

- a known pure `ell=2..5` sky plus arbitrary monopole/dipole must recover the
  same retained coefficients on the registered mask;
- changing monopole/dipole amplitudes over a broad range must not change the
  retained coefficients;
- the joint-fit implementation and an independently constructed dense fixture
  must agree;
- a singular or over-conditioned joint normal matrix must abstain.

This P0 concerns the semantic identity of the reported retained coefficients.
The empirical PR-314 rank remains preserved as an executed statistic of the
legacy operator.

## P1-001 — the common mask enters after full-sky band limitation

`reduce_temperature_map()` first evaluates `map2alm(..., lmax=5)` on the
delivered full-sky product and only then synthesizes the compact map. The common
mask enters later. Contamination confined to zero-weight mask pixels can thus
contribute to the delivered full-sky low multipoles before the mask inverse.

This does not fabricate the current rank: it defines a delivered-product
conditional statistic. It does mean the result cannot be described as
mask-conditioned or insensitive to excluded regions.

PR-315 must add a separately named high-resolution mask-conditioned branch and
the following metamorphic oracle:

```text
add contamination only where common_mask == 0
amplitudes: 1, 1e2, 1e4, 1e8
expected: joint mask-conditioned l=2..5 coefficients and all 12 features unchanged
```

The legacy full-sky branch remains frozen. Neither branch may be selected as
primary after inspecting its observed rank.

## P1-002 — the feature-tail estimand is a generic two-sided omnibus

`calibrate_complete_synthetic_pool()` uses `two-sided` for every feature. This
is a valid generic outlier family. It is not the same estimand as literature
claims such as low quadrupole power or unusually high alignment.

Preserve the exact PR-314 family as

```text
SMICA_LOWELL_12_FEATURE_TWO_SIDED_OMNIBUS_V1
```

Any directed-tail family must be separately named, justified by prior
literature or a pre-existing claim, and frozen before its new observed ranks
are evaluated. Failure to justify such a registry is not a blocker for the
two-sided rerun; it is a typed blocker for the directed sensitivity analysis.

## P1-003 — raw observation and pair lineage is not acceptance-bound

The plan binds the observed filename and size. The raw observed SHA-256 is
computed after execution begins. The compact null bundle is hashed, but the
ordered 300 raw CMB hashes, 300 raw noise hashes and exact pair mapping are not
part of the attended acceptance.

This is scientific provenance, not an anti-tamper issue. PR-315 must create one
ordered raw-input manifest during preparation and bind its digest before the
rerun.

## P1-004 — the rank is conditional on simulation adequacy

The 300-pair rank is appropriate for the intentional fast path. It remains
conditional on:

- the fiducial CMB ensemble;
- fixed component-separation weights;
- FFP10 noise/systematics fidelity;
- residual foreground and inpainting mismatch;
- the selected map-processing branch.

Planck Collaboration IV reports that the simulations are the appropriate
end-to-end noise/systematics resource but also documents residual biases and
the need for statistic-specific validation. The result must therefore be
labelled a conditional finite-rank fraction, not an unconditional p-value.

Separate sensitivity tiers may include 999 CMB-only rows, alternate legal
CMB/noise pairings, or map/mask branches. They must remain separately labelled
and must not delay the user-approved primary 300-pair path.

## P1-005 — load-bearing PR-314 tests are not explicit clean-CI cells

The PR merge-ref workflow is green, but its Repository-integrity job explicitly
runs PR-309, PR-310 and PR-311 cells, not the three PR-314 test files or a
committed-result replay. Local focused testing was user-approved; a direct
clean-CI consumer is still needed before treating the result path as durable.

Add one step to the existing workflow. Do not create another workflow.

## P1-006 — replay is raw-free but not portable at feature level

The replay matches when the off-repo plan, compact null maps, mask, beam, window
and covariance are available. An independent checkout cannot recompute the
committed ranks from repository artifacts alone.

Export a compact package containing:

```yaml
observed_feature_vector: [12]
null_feature_matrix: [300, 12]
row_ids: [300]
feature_order: [12]
feature_units: [12]
covariance: [12, 12]
tail_registry:
operator_hashes:
raw_input_manifest_hash:
```

This is small, sufficient and directly testable.

## P2 notes

### Execution-path reuse

PR-314 directly implements acceptance/start/terminal logic rather than using
the shared PR-305 dispatcher. Under the single-researcher model this is not a
security defect. Avoid another framework. PR-315 should either extract one
small shared helper or add an architecture test proving there is still only one
scientific operator and one finite-rank implementation.

### `healpy.pixwin` auxiliary data

The first run downloaded a small official healpy pixel-window table. Freeze the
local file hash or vendor only that official auxiliary table if license permits.
Do not add a general download manager.

### Result naming

Prefer:

```yaml
conditional_family_rank_fraction: 133/301
conditional_family_rank_reduced: 19/43
null_count: 300
simulation_condition: SMICA_FFP10_CMB_PLUS_NOISE_FAST_SLICE
```

Keep `p` only as an explicitly conditional empirical-rank alias.

## Accumulated code-quality finding

The stack has successfully moved from process-only preparation to real
observational execution. It has also accumulated several dormant or
lane-specific frameworks. Do **not** start a cleanup, security, Rust or generic
architecture PR before PR-315. The next change must be the named Planck
scientific robustness capability. Cleanup is justified only after the new
primary and legacy branches have a frozen numerical comparison.

## Development decision

```yaml
decision: ACCEPT_PR314_AS_CONDITIONAL_EXECUTED_EVIDENCE_AND_ADD_PR315_ROBUSTNESS_RERUN
preserve_PR314_result: true
PR314_result_role: DELIVERED_FULLSKY_SMICA_300PAIR_CONDITIONAL_NEGATIVE_DIAGNOSTIC
PR314_merge_disposition: ALLOW_AS_EXECUTED_EVIDENCE_AFTER_AUDIT_LINK
next_work_unit: PR-315
next_capability: PLANCK_SMICA_JOINT_CUTSKY_LOWELL_ROBUSTNESS_AND_PORTABLE_FEATURE_REPLAY
DAG_rule:
  - append PR-315 after PR-314
  - do not reorder or rewrite an existing dependency
  - if PR-314 closes without merge, bind the exact terminal receipt
security_infrastructure: forbidden
Rust: forbidden_without_profiled_numeric_leaf
```

PR-315 begins with failing scientific regression tests. It does not expand the
fast path to Commander or require the 999-row sensitivity tier before the
primary 300-pair comparison is complete.
