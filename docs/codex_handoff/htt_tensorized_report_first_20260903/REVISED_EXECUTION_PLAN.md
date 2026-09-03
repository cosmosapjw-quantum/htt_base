# HTT tensorized report-first execution plan

## Purpose

Reorder the active `htt_base` research programme so that the current tensorized methodology and the WU-010/WU-011 response results are first compiled into a stable research report, then the observation-bearing analysis is rerun locally under corrected tensor semantics, and only afterward the remaining WU-011 numerical-identifiability closeout resumes.

This plan supersedes any continuation that treats scalar-only MES ranks or WU-006--008 tensor/injection outputs as current scientific results.

## Fixed authority

### Tensorized-method authority

```yaml
pr: 440
branch: changeset/mes-tensor-research-integration-20260830
head: 687234128d7c12d04e68aad0f303c21d2d470393
base: codex_emergency@e7dc5fd99c6574eee1e93b6a2ec05beb394de034
role: CURRENT_TENSORIZED_MES_SEMANTIC_AUTHORITY
```

### Historical carrier input authority

```yaml
source_commit: ccba350d7b725b227c64436e32af96abfe786449
source_tree: e91b8a4f57777c71c2bf1fc0f8c21395753481ba
paired_carrier_sha256: 0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93
frozen_scalar_npz_sha256: b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b
role: IMMUTABLE_INPUT_ONLY
```

### Local-observer response authority

```yaml
wu010_pr: 442
wu010_head: 29427a1f7f2c5d46e43ffe03053c4ac13e969228
wu010_state: PASS_FRESH_READ_ONLY_REVIEW_WITH_TYPED_LIMITATIONS
wu011_pr: 444
wu011_current_head: de73549c16ac6ceb63f924c86611e0a5ceb4711d
wu011_last_scientific_terminal: PASS_TASK7C_MATCHED_CONTROL_RANK_UNRESOLVED
role: SEPARATE_ADDITIVE_RESPONSE_LINEAGE
```

The tensorized-method and WU009--011 lineages are Git-diverged. Do not represent the report as a linear source ancestry. Integrate scientific results by explicit authority references only.

## Global claim firewall

Forbidden until their dedicated gates close:

- scalar-only MES historical ranks as current results;
- WU-006--008 old Q/O/tensor/foreground/injection interpretations;
- statistic or tail chosen after viewing corrected observed rank;
- calibrated CMB-only-999 significance against a noisy observation;
- empirical beta fit or boost subtraction;
- local boost = global tilt identification;
- physical shear/vorticity or Bianchi-family attribution;
- finite-HEALPix all-direction high-ell containment theorem before A4 numerical-error closure;
- BASS/native-solver substitution or solver claims.

## Phase R0 — report authority freeze

### Output

`docs/research_reports/HTT_TENSORIZED_MES_RESPONSE_SYNTHESIS_20260903.md`

### Required content

- scalar/WU006--008 supersession ledger;
- correct stored-real harmonic/STF conventions;
- original-PSTF MES normalization and conditional role;
- tensor/Krylov representation and SO(3)/O(3) boundary;
- finite-null validity and exchangeability boundary;
- WU-010 exact full-sky local-observer response;
- WU-011 processed response, continuum L12 result and A4 error-envelope status;
- explicit statement that corrected observational rank has not yet been produced;
- revised research DAG.

### Terminal

```text
REPORT_SYNTHESIS_FROZEN_PRE_RERUN
```

No observed-data numerical result is generated in R0.

## Phase R1 — actual-checkout tensor representation repair

### Goal

Generate corrected Q/O tensors and MES conditional functions from immutable stored-real carrier inputs without reopening FITS maps or generating anomaly ranks.

### First verification

Run on the actual isolated checkout:

```bash
PYTHONPATH=htt/src python -m pytest -q -p no:cacheprovider \
  tests/common/test_mes_krylov_completion.py \
  tests/integration/test_mes_tensor_mapfree_repair.py

python -m py_compile \
  htt/src/common/mes_krylov_completion.py \
  scripts/observed_runs/rebuild_mes_tensor_carriers.py

git diff --check
```

### Execution

Use a new, nonexisting output directory:

```bash
python scripts/observed_runs/rebuild_mes_tensor_carriers.py \
  --repo . \
  --output-dir docs/generated/mes_tensor_representation_repair_run01 \
  --t0-uk 2725500 \
  --residual-epsilon1 0 \
  --execute
```

`epsilon1=0` is a declared conditional attribution scenario, not an observed intrinsic-dipole measurement.

### Mandatory invariants

- source head/tree exactly match pinned historical authority;
- paired artifact hashes match;
- no unsafe pickle/dtype or row-order drift;
- stored carrier uses Euclidean orthonormal-real metric;
- independent spherical integration produces Q/O;
- `Q:Q = 75/(8*pi) C2` rowwise;
- `O:O = 245/(8*pi) C3` rowwise;
- proper-rotation covariance checks;
- Krylov chart unavailable rows preserve tensors and row membership;
- 301 paired rows;
- 1000 observation+CMB-only rows with only ID 00970 absent and 00818 present;
- same observed carrier in both arms;
- no rank, p-value or physical-source claim emitted.

### Terminal

Only:

```text
EXECUTED_PENDING_INDEPENDENT_REVIEW
```

Do not self-promote to scientific success.

## Phase R2 — independent representation review

### Review binding

Review must bind:

- candidate git head and tree;
- source-object identities;
- input manifest;
- exact output manifest/hashes;
- Q/O radial identities;
- rotation/mirror tests;
- unavailable-chart behavior;
- absence of reused old Q/O/rank arrays.

### Possible terminals

```text
PASS_REPRESENTATION_REPAIR_REVIEWED
FAIL_REPRESENTATION_REPAIR
BLOCKED_BY_SOURCE_OR_RUNTIME_IDENTITY
```

If code changes after review, create a new candidate and repeat review. An evidence-only closeout may follow a clean review without source changes.

## Phase R3 — statistic registry before corrected observation evaluation

Do not immediately ask “what is the new Planck rank?” after R2. First freeze the experiment.

### R3A historical-sensitivity registry

Historical questions may be rerun only as a correction/sensitivity study. Preserve their definitions where scientifically meaningful, but do not call them the current primary statistic.

Required labels:

```text
HISTORICAL_SENSITIVITY_ONLY
NOT_CURRENT_CONFIRMATORY_STATISTIC
```

### R3B new tensor/orbit statistic registry

Freeze one bounded family before observed evaluation. Candidate inputs may include:

- full Q/O amplitudes plus explicitly normalized shape coordinates;
- conditioned Krylov16 orbit packet;
- chirality-sensitive SO(3) coordinate where admissible;
- response-orthogonal or nuisance-projected quantities only under a declared response model.

For every coordinate/statistic freeze:

- units and normalization;
- action group and chart domain;
- missing/unavailable handling;
- tail direction;
- joint score/reducer;
- calibration pool;
- dependence handling;
- nuisance model;
- multiplicity/family rule;
- power/kill tests;
- observation-blind registration hash.

### Prohibition

Do not reuse the withdrawn WU-008 injection registry without the corrected basis/intervention definition.

## Phase R4 — corrected local observational rerun

### Primary lane

Use the admitted local Planck/FFP10 observation-plus-CMB+noise paired surface for the primary finite-null result.

Requirements:

- exact data/source admission readback before execution;
- no raw mutation;
- same operator for observation and every null row;
- corrected tensor representation;
- frozen R3 statistic registry;
- row-equivariant handling of chart failure/missingness;
- observation-inclusive finite calibration;
- complete portable output/replay receipt.

### CMB-only lane

Keep as descriptive sensitivity unless a faithful joint observation/noise null is supplied.

Do not call the CMB-only lane an independent replication when rows share underlying CMB realizations or the observation has unmatched noise/systematics.

### Output namespace

Use a new output namespace. Never overwrite or silently relabel old WU006--008 result directories.

### Scientific terminal

The terminal must state exactly which null/statistic/representation was used and must permit `NO_ADMISSIBLE_NEW_RESULT`.

## Phase R5 — report Results update

Only after R4:

1. replace the current “no corrected result yet” section with the admitted R4 outputs;
2. keep superseded scalar/WU006--008 numbers out of headline tables;
3. include historical comparisons only in a clearly quarantined correction/sensitivity subsection if useful;
4. regenerate figures from current artifacts;
5. run two-width hostile figure audit and residual pass;
6. perform a fresh blind statistical/methodological review.

No narrative may be written to imply that a more extreme tensor statistic was selected because it produced a smaller observed rank.

## Phase R6 — resume WU-011 A4 engineering

After the corrected observation pipeline is stable, resume the original processed-response closeout.

### Immediate A4 tasks

1. seal branch-specific validation fixtures so tests fail for the intended validator branch;
2. run byte-exact source in a supported Python/NumPy environment;
3. bind family partition, basis, radius, calibration and holdout registries by content hash;
4. add resolution, map2alm-iteration and processing-lmax numerical controls;
5. preserve continuum discrepancy as independent heldout evidence where appropriate;
6. recompute six-direction error-whitened generalized singular values;
7. adjudicate robust full-row rank only under a complete declared error class;
8. if partial rank is used, open a separate Wedin/spectral-gap lane rather than promoting thresholded singular vectors.

### Allowed terminals

```text
PASS_TASK7C_ROBUST_CONTINUUM_AND_DISCRETE_SURJECTIVITY_NO_GO
PASS_TASK7C_NUMERICAL_ENVELOPE_UNRESOLVED
BLOCKED_BY_ERROR_ENVELOPE_INCOMPLETE
BLOCKED_BY_LINEAGE_OR_RUNTIME_DISAGREEMENT
```

An unresolved discrete terminal does not erase the continuum L12 result.

## Phase R7 — publication split decision

After R4/R5 and enough of R6 is stable, decide between:

### One integrated report

Tensorized Planck finite-null morphology + response-limited identifiability in one long methods/results paper.

### Two-report split

1. **Tensorized low-ell Planck inference** -- corrected representation, statistics, local rerun, robustness;
2. **Local-observer response and low-ell identifiability** -- WU010/WU011 exact/processed response, continuum high-ell result, numerical-error theory.

Do not split merely to preserve PR/work-unit history.

## Readiness after plan reorder

```yaml
report_pre_rerun_theory_methods: ~95_percent
corrected_tensor_representation_admitted: 0_percent_until_R1_R2
corrected_observational_result: 0_percent_until_R4
wu010_scoped_response: closed_with_typed_limits
wu011_engineering: ~90_percent
wu011_finite_operator_scientific_closeout: unresolved
```

## Correct next action

Execute **R1 only** in a local isolated checkout. Do not resume A4 engineering or create a new observed statistic before the corrected tensor representation has an independently reviewed artifact.
