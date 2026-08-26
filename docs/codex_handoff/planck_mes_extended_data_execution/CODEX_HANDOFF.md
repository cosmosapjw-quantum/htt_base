# Codex handoff — execute Planck MES extended-data robustness without process drift

## STATUS

```yaml
repository: cosmosapjw-quantum/htt_base
planning_branch: analysis/planck-mes-extended-data-execution-20260826
canonical_base_branch: changeset/pr324-mes-methodology-stack-20260826
canonical_base_sha: 3cdeaba39e164c911a26c5daa37f0e15b29614d3
canonical_base_tree: 47bdbb72aae62ca4280a96897f80028b1b910c20
package: docs/codex_handoff/planck_mes_extended_data_execution
mode: IMPLEMENT_AND_EXECUTE_ONE_WORK_UNIT_AT_A_TIME
claim_promotion: false
raw_data_mutation: forbidden
```

This is the implementation handoff. Do **not** create another plan, audit package, reviewer contract, governance schema, or DAG node.

The required transition is:

```text
user-reported local inventory
→ verified read-only intake
→ real SMICA 999-CMB-only execution
→ real Commander observation comparison
→ clean provenance + bounded paper supplement
```

## Read exactly

```text
docs/codex_handoff/planck_mes_extended_data_execution/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_extended_data_execution/AUTHORITY_AND_SCOPE.yaml
docs/codex_handoff/planck_mes_extended_data_execution/DATA_AVAILABILITY_SNAPSHOT.yaml
docs/codex_handoff/planck_mes_extended_data_execution/DATA_ROUTE_MATRIX.yaml
docs/codex_handoff/planck_mes_extended_data_execution/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_extended_data_execution/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/planck_mes_extended_data_execution/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/planck_mes_extended_data_execution/FRESH_CONTEXT_REVIEW_CONTRACT.yaml
docs/codex_handoff/planck_mes_extended_data_execution/FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml
docs/codex_handoff/planck_mes_extended_data_execution/PROCESS_COST_ASSESSMENT.yaml
scripts/validate_planck_mes_extended_data_plan.py
```

Then inspect only the existing implementation surfaces needed by the current work unit:

```text
scripts/observed_runs/prepare_planck_pr3_admission.py
scripts/observed_runs/run_planck_pr3.py
scripts/observed_runs/run_planck_mes_morphology.py
htt/obsstat/planck_pr3_operator.py
htt/obsstat/mes_row_anchor.py
tests/integration/test_planck_pr3_admission_preparation.py
tests/integration/test_planck_pr3_current_stack.py
tests/integration/test_planck_mes_morphology.py
tests/paper/test_planck_mes_first_paper.py
```

## First commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git fetch origin --prune
git switch analysis/planck-mes-extended-data-execution-20260826
git pull --ff-only

test "$(git merge-base 3cdeaba39e164c911a26c5daa37f0e15b29614d3 HEAD)" = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"
test "$(git rev-parse origin/changeset/pr324-mes-methodology-stack-20260826)" = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"

python scripts/validate_planck_mes_extended_data_plan.py
git status --short
```

If the base branch no longer resolves to `3cdeaba39e164c911a26c5daa37f0e15b29614d3`, stop:

```text
STATUS = BLOCKED_BY_MOVED_AUTHORITY
```

Do not rebase or guess a new base.

## Local data root

```bash
export HTT_WORKDIR=/mnt/sn850x2t/htt_base_e2e/workdir
test -d "$HTT_WORKDIR/raw"
```

Never write beneath:

```text
$HTT_WORKDIR/raw
$HTT_WORKDIR/downloads
$HTT_WORKDIR/cobaya_packages/data
```

Full host manifests and runtime logs belong under:

```text
$HTT_WORKDIR/analysis/planck_mes_extended_data/
```

Only portable summaries, small map-free arrays, tables, figures, and receipts may enter Git.

## Work-unit execution policy

Execute exactly one ordered work unit from `AUDIT_COMPILED_EXEC_PLAN.yaml`.

For each work unit:

1. create a fresh implementation branch from the accepted predecessor;
2. write the listed RED tests first;
3. run the RED test and preserve the failure;
4. implement the smallest bounded change;
5. execute the real objective output when the work unit requires it;
6. run targeted, negative, and directly affected regression tests;
7. inspect generated plots as evidence;
8. commit/push and open one draft PR;
9. run one read-only fresh-context review;
10. apply at most one targeted repair unless a newly reproduced current-task P0/P1 appears.

Do not run the full repository suite unless a distinct cross-surface failure justifies it.

## PED-WU-001 — start here

Objective: convert the reported 12,239-file, 976,978,065,267-byte raw tree into a verified typed intake without mutation.

Implementation branch suggestion:

```text
changeset/planck-mes-extended-data-intake-20260826
```

The inspector must verify at least:

- SMICA CMB IDs `00000..00999`, excluding official missing `00970`, count `999`;
- SMICA noise IDs `00000..00299`, count `300`;
- Commander complete IDs `00000..00002`;
- Commander `.fits.partial` IDs `00003..00006` are quarantined;
- NPIPE/PR4 file count is zero and status is unavailable;
- no HSC/SACC payload exists in `hsc_kids`; KiDS payloads are classified separately;
- realization `00818` gets a semantic FITS/checksum receipt. A 1,218-byte size difference alone is neither PASS nor FAIL;
- pre/post raw-tree metadata are unchanged.

Preflight uses metadata and existing checksum sidecars. Do not hash unrelated 910-GiB data before execution. Stream-hash each selected Planck file during its first scientific read.

Required objective outputs:

```text
docs/generated/planck_mes_extended_data/intake_summary.json
docs/generated/planck_mes_extended_data/route_receipt.json
$HTT_WORKDIR/analysis/planck_mes_extended_data/intake_manifest.json
```

Pass transition: immediately begin `PED-WU-002`.

## PED-WU-002 — execute, do not only scaffold

Create a separate explicit 999-null SMICA CMB-only lane. Reuse the registered joint cut-sky operator and active MES row-anchor factory. Do not refactor or alter the existing paired-300 attended path.

Exact inventory:

```text
null rows = 999 official SMICA CMB maps
IDs       = 00000..00999 excluding 00970 only
pool N    = 1000 including the observed SMICA row
noise     = absent by design
tails     = two-sided
families  = GENERIC_12, RAW_REDUCED_10, EPS_REDUCED_10,
            MES_10, ANCHORS_ONLY_2, MORPHOLOGY_ONLY_8
```

The output is an empirical CMB-only robustness rank, **not** an unconditional or exchangeability-calibrated p-value and not a replacement for the paired CMB+noise primary result.

Required objective outputs:

```text
docs/generated/planck_mes_smica_cmbonly_999/result.json
docs/generated/planck_mes_smica_cmbonly_999/replay.json
docs/generated/planck_mes_smica_cmbonly_999/features.npz
docs/generated/planck_mes_smica_cmbonly_999/features.json
docs/generated/planck_mes_smica_cmbonly_999/terminal.json
docs/generated/planck_mes_smica_cmbonly_999/figure_family_rank_comparison.pdf
docs/generated/planck_mes_smica_cmbonly_999/figure_row_score_distribution.pdf
docs/generated/planck_mes_smica_cmbonly_999/figure_00818_influence.pdf
docs/generated/planck_mes_smica_cmbonly_999/plot_audit.json
```

The preregistered 00818 influence plot may remove row 00818 only for a diagnostic comparison. The primary CMB-only result must still include it after semantic admission.

Before completion, re-run the focused primary tests and require the existing exact values:

```text
GENERIC_12 = 133/301
RAW_REDUCED_10 = 110/301
EPS_REDUCED_10 = 109/301
MES_10 = 98/301
ANCHORS_ONLY_2 = 78/301
MORPHOLOGY_ONLY_8 = 88/301
MES ceiling ranks = 74/301 each
minimum = multipole_l3_absdot_0 = 16/301
```

Pass transition: begin `PED-WU-003` regardless of whether the robustness rank is numerically close to the primary rank.

## PED-WU-003 — Commander is descriptive only

Process the observed Commander map with the exact same registered operator projection used for SMICA. Use complete Commander CMB `00000..00002` only as implementation sanity rows. Never emit a finite rank or p-value.

Required fields include:

```yaml
format: PLANCK_MES_COMMANDER_OBSERVATION_COMPARISON_V1
finite_rank_emitted: false
commander_null_status: INSUFFICIENT_COMPLETE_NULLS
artifact_mode: EXPLORATORY_NONAUTHORITATIVE
```

The four `.fits.partial` files must never be opened as FITS inputs.

Required objective outputs:

```text
docs/generated/planck_mes_commander_observation/result.json
docs/generated/planck_mes_commander_observation/replay.json
docs/generated/planck_mes_commander_observation/terminal.json
docs/generated/planck_mes_commander_observation/feature_delta_table.csv
docs/generated/planck_mes_commander_observation/figure_coordinate_comparison.pdf
```

Pass transition: begin `PED-WU-004`.

## PED-WU-004 — submission provenance and paper supplement

Consume only `SUCCEEDED` terminals with portable replay `MATCH`. Extend the paper builder with an optional typed robustness summary. When the robustness input is absent, preserve the current primary manuscript semantics.

The primary Paper A result remains the paired 300 CMB+noise analysis. Add only a bounded robustness appendix/table:

- CMB-only 999 empirical ranks are labeled separately;
- Commander is coordinate-only;
- neither is described as physical shear/vorticity, direction, local/global identification, or Bianchi-family evidence;
- do not strengthen the abstract automatically.

Perform one clean-head map-free replay and bind:

```text
candidate commit/tree
generator source hash
selected input identities
PED-WU-002 terminal/replay projections
PED-WU-003 terminal/replay projections
```

Run focused paper/MES tests, `latexmk`, and PDF inspection. One read-only fresh review is enough. After at most one targeted repair, transition to external scientific review or journal-submission preparation.

## Absolute stop conditions

Stop without guessing when any of these occurs:

```text
BLOCKED_BY_MOVED_AUTHORITY
BLOCKED_MISSING_WORKDIR
BLOCKED_INVALID_FFP10_INVENTORY
BLOCKED_INVALID_FFP10_00818
BLOCKED_RAW_DATA_MUTATION
BLOCKED_OPERATOR_IDENTITY_MISMATCH
BLOCKED_PRIMARY_SCIENTIFIC_DIFFERENCE
BLOCKED_COMMANDER_ADMISSION
```

A packaging-only PDF difference is not a scientific failure.

## Deferred routes

Do not implement these in the current four-work-unit sequence:

- ACT DR6 lensing: separate C2 control, not an MES temperature ceiling;
- CF4: preferred Paper B directional low-z candidate after a physical response operator exists;
- DESI: mock-calibrated density/scalar control; compressed fullshape products do not supply direction;
- KiDS: spin-2 candidate; HSC is absent;
- JWST/2MRS: future local-velocity/local-boost control;
- SPT/ACT DR4/BICEP–Keck: later cross-CMB controls;
- PR171 theory archives: source authority only, not observed evidence.

## Completion reporting

Use only:

```text
PASS
PASS_WITH_NONBLOCKING_FINDINGS
BLOCKED_BY_UNRESOLVED_SPEC
BLOCKED_BY_P0
BLOCKED_BY_P1
PARTIAL
FAILED
```

A plan, scaffold, or test-only patch is not PASS when the work unit requires a real host execution.
