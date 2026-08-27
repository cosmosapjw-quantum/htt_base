# Codex Handoff — Planck MES Observable-Irrep / Global-Formalism Execution

## STATUS

```yaml
repository: cosmosapjw-quantum/htt_base
active_package: docs/codex_handoff/planck_mes_irrep_global_formalism_execution
planning_branch: analysis/planck-mes-extended-data-execution-20260826
planning_predecessor_sha: 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e
canonical_science_base: changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3
draft_pr: 417
mode: IMPLEMENT_AND_EXECUTE_ONE_WORK_UNIT_AT_A_TIME
claim_promotion: false
raw_data_mutation: forbidden
first_work_unit: PMG-WU-001
first_mandatory_objective_execution: PMG-WU-003
```

This package replaces the old `PED-WU-001..004` execution order. Preserve the
old package as historical inventory/route evidence, but do not execute those
IDs directly.

Do not create another plan, audit package, reviewer contract, DAG node, or
governance schema.

## Read Exactly

```text
docs/codex_handoff/ACTIVE_PLANCK_MES_EXECUTION_PACKAGE.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/AUTHORITY_AND_SCOPE.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/PRIOR_PLAN_SUPERSESSION.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/FORMALISM_CONTRACT.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/FORMALISM_MIGRATION_MATRIX.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/DATA_ROUTE_MATRIX.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/FRESH_CONTEXT_REVIEW_CONTRACT.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/FINAL_DIFFERENTIAL_AUDIT_CONTRACT.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/PROCESS_COST_ASSESSMENT.yaml
scripts/validate_planck_mes_irrep_global_formalism_plan.py
```

Then inspect only the source/test files listed by the current work unit.

## First Commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

git fetch origin --prune
git switch analysis/planck-mes-extended-data-execution-20260826
git pull --ff-only

test "$(git rev-parse origin/changeset/pr324-mes-methodology-stack-20260826)" = "3cdeaba39e164c911a26c5daa37f0e15b29614d3"
git merge-base --is-ancestor "2669a55ef230d1ca9e79c09d3344f7b15c50ac0e" HEAD
test "$(git rev-parse 3cdeaba39e164c911a26c5daa37f0e15b29614d3^{tree})" = "47bdbb72aae62ca4280a96897f80028b1b910c20"

python scripts/validate_planck_mes_irrep_global_formalism_plan.py
python -m pytest -q tests/contracts/test_planck_mes_irrep_global_formalism_plan.py
git status --short
```

If any authority check fails:

```text
STATUS = BLOCKED_BY_MOVED_AUTHORITY
```

Do not rebase, guess a new base, or rewrite the package.

## Governing Semantic Boundary

```text
ObservableIrrepState
    observer/data harmonic and STF content

JointAnisotropyState
    physical pre-solver kinematics/velocity/geometry

MesPremiseNormalizer
    one-way channel-typed premise normalization

ResponseBoundObservableState
    observable state plus certified forward response
```

Never substitute one for another.

The exact registered `epsilon_1=0` identities are:

```text
W2_max = C2/(30*pi*T0^2)
Sigma2_max = (27/98)*(7*epsilon2+epsilon3)^2
sigma(Sigma2_max,W2_max,M) = sigma(C2,C3,M)
independent_information_gain = false
```

## Work-Unit Execution Policy

Execute exactly one work unit from `AUDIT_COMPILED_EXEC_PLAN.yaml`.

For each work unit:

1. create a fresh implementation branch from the accepted predecessor SHA;
2. write the listed RED tests first and preserve the failure output;
3. implement the smallest bounded change;
4. execute the real objective output when required;
5. run targeted, negative, and directly affected regression checks;
6. inspect generated plots where required;
7. commit and push one coherent work unit;
8. open or update one draft stacked PR targeting the accepted predecessor;
9. perform one read-only fresh-context review;
10. apply at most one targeted repair unless a new reproduced current-task P0/P1 appears;
11. execute the explicit pass transition.

A plan, scaffold, test-only patch, or source file without required real output
is not PASS.

## Start With PMG-WU-001

Goal: create `ObservableIrrepState` and freeze the scalar baseline without
touching map runners or scientific outputs.

Do not start the local-data intake or 999-map pass first. The next expensive
map pass must preserve the 32-dimensional retained carrier.

After `PMG-WU-002`, immediately execute `PMG-WU-003`. Two enabling units are
the maximum allowed process-only prelude.

If two substantial cycles produce only contracts, reviews, manifests, or other
process outputs, classify `PROCESS_STARVATION`, freeze optional governance,
and execute `PMG-WU-003` or the shortest admissible objective work unit.

## Local Data Root

Beginning with `PMG-WU-004`:

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
$HTT_WORKDIR/analysis/planck_mes_irrep_global_formalism/
```

Only small portable no-pickle carriers, summaries, tables, figures, and
receipts enter Git.

## Stop Conditions

```text
BLOCKED_BY_MOVED_AUTHORITY
BLOCKED_BY_UNRESOLVED_SPEC
BLOCKED_BY_P0
BLOCKED_BY_P1
BLOCKED_RAW_DATA_MUTATION
BLOCKED_OPERATOR_IDENTITY_MISMATCH
BLOCKED_CARRIER_SCALAR_CLOSURE
BLOCKED_OBSERVABLE_PHYSICAL_TYPE_CONFLATION
BLOCKED_POSTHOC_REGISTRY
```

A non-anomalous result, a scalar/irrep disagreement, or an unavailable
physical template is not automatically a software failure.

## Completion Reporting

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

Every report must state the concrete DAG transition just achieved.
