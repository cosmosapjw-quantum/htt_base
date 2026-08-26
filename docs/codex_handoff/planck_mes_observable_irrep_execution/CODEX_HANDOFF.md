# Codex handoff — Planck MES observable-irrep formalism and carrier-preserving execution

## STATUS

```yaml
repository: cosmosapjw-quantum/htt_base
planning_branch: analysis/planck-mes-observable-irrep-execution-20260827
planning_predecessor_branch: analysis/planck-mes-extended-data-execution-20260826
planning_predecessor_sha: 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e
canonical_science_base_branch: changeset/pr324-mes-methodology-stack-20260826
canonical_science_base_sha: 3cdeaba39e164c911a26c5daa37f0e15b29614d3
canonical_science_base_tree: 47bdbb72aae62ca4280a96897f80028b1b910c20
package: docs/codex_handoff/planck_mes_observable_irrep_execution
mode: IMPLEMENT_AND_EXECUTE_ONE_WORK_UNIT_AT_A_TIME
claim_promotion: false
raw_data_mutation: forbidden
successor_planning_package: forbidden
```

This package supersedes the scalar-only runtime semantics of
`docs/codex_handoff/planck_mes_extended_data_execution`. Reuse its read-only
inventory safeguards, but do not execute its 999-map lane unless the same map
pass also emits the typed harmonic carrier required here.

Do **not** create another plan, audit package, governance schema, reviewer
contract, DAG node, or “pre-implementation” document. The next action is code
and then an objective map-free result.

## Scientific correction compiled into this handoff

For the registered `eps1=0` branch,

```text
W_max^2     = C2 / (30*pi*T0^2)
Sigma_max^2 = (27/98) * (7*eps2 + eps3)^2
```

and the mapping between `(C2,C3)` and `(Sigma_max^2,W_max^2)` is invertible on
the non-negative physical domain. The existing MES row is therefore
information-equivalent to the raw reduced row; differences in the historical
family ranks are reducer/family-coordinate effects, not independent physical
information.

The current numerical operator already produces retained `ell=2..5` harmonic
coefficients, but the V1 portable package discards them and serializes only
twelve scalar features. This execution sequence repairs that boundary before
large-data robustness work.

## Non-negotiable type separation

```text
JointAnisotropyState
    = physical pre-solver kinematics/velocity/geometry state

ObservableIrrepState
    = observed or simulated harmonic carrier with frame/operator provenance

MESAnchorSpec
    = one-way premise-dependent scalar ceiling

PhysicalResponseOperator
    = required explicit bridge before physical interpretation
```

Forbidden:

```text
ObservableIrrepState -> JointAnisotropyState without a response
MES/scalar/covariance -> direction/vector/STF
canonical axis sign -> handedness
Planck carrier -> physical shear/vorticity/tilt/Bianchi family
```

## Read exactly before implementation

```text
docs/codex_handoff/planck_mes_observable_irrep_execution/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/AUTHORITY_AND_SCOPE.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/FORMALISM_CONTRACT.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/MIGRATION_MAP.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_observable_irrep_execution/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/FRESH_CONTEXT_REVIEW_CONTRACT.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/PROCESS_COST_ASSESSMENT.yaml
docs/codex_handoff/planck_mes_observable_irrep_execution/IMPLEMENTATION_PLAN.md
scripts/validate_planck_mes_irrep_execution_plan.py
tests/contracts/test_planck_mes_irrep_execution_plan.py
```

Then inspect only the source/test surfaces listed by the current work unit.
Do not sweep unrelated project history.

## First commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git fetch origin --prune
git switch analysis/planck-mes-observable-irrep-execution-20260827
git pull --ff-only

test "$(git rev-parse origin/changeset/pr324-mes-methodology-stack-20260826)" = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"
test "$(git rev-parse 3cdeaba39e164c911a26c5daa37f0e15b29614d3^{tree})" = "47bdbb72aae62ca4280a96897f80028b1b910c20"
git merge-base --is-ancestor "2669a55ef230d1ca9e79c09d3344f7b15c50ac0e" HEAD

python scripts/validate_planck_mes_irrep_execution_plan.py
python -m pytest -q tests/contracts/test_planck_mes_irrep_execution_plan.py
git status --short
```

If either authority identity moved, stop with:

```text
STATUS = BLOCKED_BY_MOVED_AUTHORITY
```

Do not rebase, retarget, or infer a replacement authority.

## Runtime data root

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

Host-private manifests/logs belong under:

```text
$HTT_WORKDIR/analysis/planck_mes_observable_irrep/
```

Git may receive only source, tests, compact map-free carriers, tables, figures,
result/replay/terminal receipts, and small manifests.

## Work-unit execution rule

Execute exactly one ordered work unit from
`AUDIT_COMPILED_EXEC_PLAN.yaml`.

For each work unit:

1. create a fresh implementation branch from the accepted predecessor;
2. write the listed RED tests and preserve the failure;
3. implement the smallest change that satisfies the work-unit interfaces;
4. execute the required objective output, not only a scaffold;
5. run targeted, negative, and directly affected regression checks;
6. generate and inspect plots only where the work unit requires plot evidence;
7. commit/push and open one draft PR;
8. run one read-only fresh-context review;
9. apply at most one targeted repair unless a newly reproduced current-task
   P0/P1 appears;
10. record the work-unit terminal and immediately perform the declared PASS
    transition.

Do not run the full repository suite unless a distinct uncovered failure class
is stated first.

## PMI-WU-001 — start here

Objective: create the observable-irrep SSOT and enforce cross-layer
non-coercion.

Implementation branch:

```text
changeset/planck-mes-observable-irrep-core-20260827
```

Required source surfaces:

```text
htt/src/common/observable_irrep_state.py
htt/obsstat/observable_irrep_adapter.py
tests/common/test_observable_irrep_state.py
tests/obsstat/test_observable_irrep_adapter.py
docs/research_program/post_pr275/observable_irrep_formalism_v1.yaml
scripts/architecture/test_import_boundaries.py
```

The common type must be dependency-light and must not import healpy. It must
encode:

```text
row identity
spin/parity
ell
2*ell+1 real components
registered real-harmonic layout
frame
units
source identity
operator identity
mask identity
beam/pixel identity
typed missing blocks
canonical serialization identity
```

It must not be a subclass or payload substitute for `JointAnisotropyState`.

Required RED/green checks are listed under `PMI-WU-001`. Do not add observed
execution to this PR.

PASS transition:

```text
start PMI-WU-002 immediately
```

## PMI-WU-002 — mandatory first objective result

This work unit must happen before intake or a 999-map run. It preserves the
legacy scalar result and executes the mechanism audit on frozen map-free
inputs.

Implement the central finite-null engine and two reducers:

```text
LEGACY_ABS_LOO_MEDIAN
LOO_ECDF_MIDRANK
```

For the ECDF reducer:

```text
u_ij = (count(X_kj < X_ij, k!=i) + 0.5*count(X_kj = X_ij, k!=i)) / (N-1)
two-sided score = 2*abs(u_ij - 0.5)
upper score    = u_ij
lower score    = 1-u_ij
```

Execute the frozen factorial families:

```text
EPS_10
SQUARE_ONLY_10
CARRIER_ONLY_10
MES_10
```

and report their interaction rather than pretending an additive decomposition
when the discrete family-rank functional has an interaction.

Required outputs:

```text
docs/generated/planck_mes_coordinate_mechanism/result.json
docs/generated/planck_mes_coordinate_mechanism/replay.json
docs/generated/planck_mes_coordinate_mechanism/factorial_table.csv
docs/generated/planck_mes_coordinate_mechanism/tail_table.csv
docs/generated/planck_mes_coordinate_mechanism/tie_mass_table.csv
docs/generated/planck_mes_coordinate_mechanism/eps1_sensitivity.csv
docs/generated/planck_mes_coordinate_mechanism/effective_coordinate_count.json
docs/generated/planck_mes_coordinate_mechanism/figure_family_mechanism.pdf
docs/generated/planck_mes_coordinate_mechanism/figure_eps1_sensitivity.pdf
docs/generated/planck_mes_coordinate_mechanism/plot_audit.json
docs/generated/planck_mes_coordinate_mechanism/terminal.json
```

Historical exact locks must remain:

```text
GENERIC_12         = 133/301
RAW_REDUCED_10     = 110/301
EPS_REDUCED_10     = 109/301
MES_10             = 98/301
ANCHORS_ONLY_2     = 78/301
MORPHOLOGY_ONLY_8  = 88/301
minimum coordinate = multipole_l3_absdot_0 = 16/301
MES ceiling locals = 74/301, 74/301
```

A PASS here is the first real objective transition. After this point another
planning-only artifact is an automatic `PROCESS_STARVATION` failure.

## PMI-WU-003 — read-only data intake

Reuse, do not redesign, the predecessor's inventory semantics:

```text
SMICA CMB IDs 00000..00999 excluding 00970 = 999
SMICA noise IDs 00000..00299 = 300
Commander complete IDs 00000..00002
Commander .fits.partial IDs 00003..00006 quarantined
row 00818 judged by FITS semantics + digest, never size alone
NPIPE absent
raw metadata unchanged
```

PASS transition: recover the primary paired-300 harmonic carrier.

## PMI-WU-004 — primary 301-row carrier V2

Modify the existing map-processing/output boundary so the already computed
retained coefficients survive serialization.

Required V2 arrays:

```text
observed_real_alm: (32,)
null_real_alm:     (300,32)
scalar observed/null features retained beside them
ell blocks: 2,3,4,5 with dimensions 5,7,9,11
```

Required V1 invariants:

```text
all historical scalar feature bytes/ranks remain unchanged
the V2 scalar projection reproduces V1
carrier-derived scalar features reproduce stored features
```

Do not rename or overwrite V1. Emit a new V2 schema and replay.

## PMI-WU-005 — carrier-preserving SMICA 999 lane

Execute the official CMB-only inventory with one observation plus 999 nulls.
The same map pass must emit scalar features and typed 32-component carriers.
The 999 result is separate robustness, not the primary and not an
unconditional p-value.

After PASS, injection work must consume the map-free carrier rather than
rereading all null maps.

## PMI-WU-006 — morphology/template and injection execution

Implement observable-only morphology and harmonic template scores. Do not
reuse the physical `orbit_catalogue_v3.py` by coercing observed data into a
physical state.

Mandatory benchmark:

```text
ANALYTIC_AXISYMMETRIC_STF_L2_L3_V1
```

Definition is frozen in `FORMALISM_CONTRACT.yaml`: it is an observable-space
STF benchmark, not physical shear. Its `ell=2` and `ell=3` blocks each carry
half the total squared norm, `ell=4,5` vanish, and two independent
constructions must agree to `1e-12`.

Frozen orientation banks:

```text
score bank: HEALPIX_NSIDE2_ROLL8_V1 = 384 rotations
power bank: HEALPIX_NSIDE2_ROLL2_V1 = 96 rotations
amplitude grid a: 0,0.5,1,1.5,2,2.5,3,4,5,6
```

The amplitude `a` is the full-sky template RMS divided by the frozen null-only
median `ell=2,3` RMS.

Every rotated template must pass through the exact source transfer and joint
cut-sky operator before it is added to a carrier. Adding templates after
scalar feature extraction or bypassing orientation-dependent operator
response is P0.

The native candidate:

```text
NATIVE_BIANCHI_VIIH_CONTENT_BOUND_V1
```

runs only when exact bytes, solver commit/tree, conventions, transfer and
operator identities are admitted. Otherwise record:

```text
DEFERRED_MISSING_TEMPLATE_AUTHORITY
```

and continue the mandatory analytic lane.

Report power curves, Wilson intervals, `A50`/`A90` brackets and orientation
spread. These are method-sensitivity outputs, not Bianchi constraints.

## PMI-WU-007 — Commander and methods-paper reframe

Commander is same-operator descriptive comparison only:

```yaml
finite_rank_emitted: false
null_status: INSUFFICIENT_COMPLETE_NULLS
artifact_mode: EXPLORATORY_NONAUTHORITATIVE
```

The revised manuscript is methods-first:

```text
main result: coordinate sensitivity / reducer non-invariance
MES: case study and premise-normalized coordinate
harmonic carrier: preserved observable layer
injection: measured method sensitivity
physical shear/vorticity/family claims: absent without response
```

Consume only successful terminal+replay projections. Rebuild and inspect the
PDF after source changes.

## Required evidence bundle per work unit

```text
final_git_head
final_git_tree
git_status_porcelain
git_diff_stat
git_diff_check
executed_test_commands
invariant_results
objective_output_paths
plot_audit_paths_when_required
unresolved_blockers
candidate_dispositions_when_required
```

Byte mismatch classification:

```text
immutable input                         -> hard block
deterministic evidence under exact lock -> hard block
scientific numeric output               -> registered rank/invariant/tolerance
packaging/build metadata                -> reproducibility issue unless exact bytes required
```

## Fresh review

The first pass is read-only. Findings must contain:

```yaml
severity: P0|P1|P2|P3
current_task_blocking: true|false
file: path
line_or_symbol: location
violated_invariant: PMI-INV-* or exact statement
reproducer: command/evidence
explanation: defect
minimal_repair: bounded correction or BLOCKED disposition
```

PASS requires `P0=0`, `P1=0`. P2/P3 do not block the declared transition.

## Absolute stop states

```text
BLOCKED_BY_MOVED_AUTHORITY
BLOCKED_BY_P0
BLOCKED_BY_P1
BLOCKED_BY_UNRESOLVED_SPEC
BLOCKED_INVALID_FFP10_INVENTORY
BLOCKED_RAW_DATA_MUTATION
BLOCKED_CARRIER_CONVENTION
BLOCKED_V1_SCIENTIFIC_DIFFERENCE
BLOCKED_OPERATOR_RESPONSE_IDENTITY
```

A missing native Bianchi template is not a global blocker; it is a deferred
candidate disposition.

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

A plan, scaffold, test-only patch, unexecuted runner, or generated-but-unread
plot is not PASS.
