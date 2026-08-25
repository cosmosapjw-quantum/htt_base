# PR-321 HSC S19A/Y3 Fourier-SACC readiness — adversarial re-audit

## Authority

```yaml
repository: cosmosapjw-quantum/htt_base
pull_request: 412
base_sha: a968e11461ed28c8d5cc1244f0122edc704579c4
audited_head: 43e27e8c93eb18195ceca41a22c90b7e6dd014bf
audited_tree: c4379c1c24aee5dec22af930a39242eb52f35c9d
deployment_profile: private_single_researcher_local_v1
```

## Verdict

```yaml
P0: 0
P1: 6
P2: 3
current_result:
  byte_snapshot_bound: true
  full_release_vector_shape: [170]
  full_release_covariance_shape: [170, 170]
  science_reference_ready: false
  observed_science_result: false
terminal:
  BLOCKED_PR321_REAUDIT_REPAIR_AND_LOCAL_RERUN
```

The exact release snapshot, decoded-vector hash, covariance hash, four-tracer
ordering, ten EE pairs, seventeen stored bandpowers per pair, stored windows,
and full covariance are useful durable readiness evidence.  They must be
preserved.

The current terminal `READY_FOR_WINDOW_CONVOLVED_REFERENCE` is too strong.
The official release description states that the file also contains each
tomographic tracer's \(N(z)\), that the fiducial science analysis uses
\(300<\ell<1800\), and that the covariance must receive the same scale cuts.
Those required theory/reference inputs are not bound in the current result.

## Scientific findings

### P1-001 — the official fiducial science selection is absent

The release contains 17 bandpowers per pair over approximately
\(100\le\ell\le15800\), but the published fiducial analysis keeps six bins per
pair with centers

```text
350, 500, 700, 900, 1200, 1600
```

corresponding to \(300<\ell<1800\).  Thus the fiducial vector has length

\[
10\times6=60.
\]

The large-scale cut is motivated by detected B-mode systematics; the
small-scale cut is motivated by intrinsic-alignment and baryonic-feedback
model reliability.  A future theory/reference comparison must use the exact
60-element index set and the matching \(60\times60\) covariance slice unless a
different scale selection is separately preregistered.

### P1-002 — the four tracer \(N(z)\) distributions are not bound

A window-convolved weak-lensing reference cannot be defined from EE bandpowers
and bandpower windows alone.  The four source-redshift distributions are
required inputs to the theory prediction.  PR-321 validates only tracer names
and quantities; it neither validates nor content-binds the tracer `z` and `nz`
arrays.

Required evidence per tracer:

```yaml
name:
z_sha256_float64_le:
nz_sha256_float64_le:
sample_count:
z_min:
z_max:
strictly_increasing_z:
nz_nonnegative:
integral_positive:
normalized_mean_z:
```

### P1-003 — legacy stored ordering is assumed, not independently replayed

The exact file lacks the newer `sacc_ordering` column.  The loader warning is
currently promoted to `legacy_stored_order=true`.  Binding the exact file and
loader version makes the assumption reproducible, but the semantic row order
must also be cross-checked:

1. `payload.mean` equals the ordered list of `row.value`;
2. the ten pair blocks are contiguous and have the registered order;
3. each block has the registered ell sequence;
4. the SACC pair-selection API returns the same indices and values;
5. covariance subblocks follow the same indices.

### P1-004 — the result has no explicit role in the recovered MES method

The released `cl_ee` bandpowers are rotationally averaged scalar two-point
statistics.  Directional phase information needed to construct the project's
polar vectors, axial vectors, or STF moments is not present in this product.

The result must carry:

```yaml
mes_methodology_role: SCALAR_TOMOGRAPHIC_CONTROL_ONLY
directional_information_status: PROJECTED_OUT_IN_TOMOGRAPHIC_CL_EE
mes_vector_tensor_status: NOT_APPLICABLE_NO_DIRECTION_INDEXED_FIELD
local_global_status: NOT_APPLICABLE_NO_DIRECTIONAL_RESPONSE
```

This does not reduce the value of the SACC product.  It makes it a scalar
tomographic/reference control and prevents another generic scalar lane from
replacing the MES vector/tensor scientific spine.

### P1-005 — status provenance is misbound

The current status patch writes PR #412's URL into the historical PR-289 row
while the actual PR-321 row retains `pr_url: null`.

Required repair:

```yaml
historical_stacked_pr_execution.PR-289.pr_url:
  https://github.com/cosmosapjw-quantum/htt_base/pull/386

stacked_pr_execution.prs.PR-321.pr_url:
  https://github.com/cosmosapjw-quantum/htt_base/pull/412
```

After the scientific repair, PR-321's review/readiness fields must remain
pending until the exact local SACC rerun passes.

### P1-006 — the anti-drift size statement is false as written

The registered anti-drift row says “seven scientific files and net additions
at most 700”, while the actual PR contains 19 paths and a net increase greater
than 700 after generated/mirror bookkeeping.  A scientific work unit should be
bounded by one coherent invariant family, not by a metric that the committed
change already violates.

Replace it with:

```yaml
semantic_boundary:
  - one HSC-only release-vector readiness cell
  - no likelihood, null inference, KiDS result, or MES directional result
substantive_paths:
  exact_allowlist: [...]
generated_and_mirror_paths:
  derived_only: true
```

## P2 findings

1. Covariance rank is serialized as 170 after Cholesky success rather than
   explicitly recording numerical rank and minimum eigenvalue.
2. The reproduction command contains one operator-specific absolute local path;
   use an environment variable or placeholder.
3. “Fast analysis” overstates a readiness-only operation; use “fast readiness”
   or “released-vector inspection”.

## Corrected terminal ladder

```yaml
current_committed_result:
  BLOCKED_PR321_REAUDIT_REPAIR_AND_LOCAL_RERUN

after_code_repair_before_real_rerun:
  BLOCKED_EXACT_HSC_SACC_RERUN_REQUIRED

after_exact_rerun:
  READY_FOR_FIDUCIAL_WINDOW_CONVOLVED_REFERENCE_SPECIFICATION

still_blocked:
  - actual theory/reference vector
  - likelihood or finite-null calibration
  - E/B closure
  - HSC-KiDS joint inference
  - MES vector/tensor analysis
  - local-boost/global-tilt discrimination
```

## Relation to the MES recovery programme

PR-321 is a nonblocking input/control for the later low-redshift programme.
It is not the direction-indexed scalar field required by the MES moment bridge.

A future HSC MES-directional lane needs map/object-level shear, masks, PSF and
selection information sufficient to construct direction-dependent scalar or
spin-2 fields.  The present SACC remains useful for:

- tomography and \(N(z)\);
- scale-selection authority;
- bandpower-window and covariance checks;
- scalar consistency/reference controls.

The live-DAG allocation work unit in the MES recovery plan must reread PR-321,
preserve it after PR-320, and classify it as `SCALAR_TOMOGRAPHIC_CONTROL_ONLY`.
