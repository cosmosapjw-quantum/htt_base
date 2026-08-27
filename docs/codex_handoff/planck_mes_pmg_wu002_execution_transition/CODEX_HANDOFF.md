# Codex handoff — PMG-WU-002 global-formalism boundary migration

## Authority

```yaml
repository: cosmosapjw-quantum/htt_base
package_host_branch: changeset/planck-mes-observable-irrep-state-20260827
wu001_implementation_source: 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0
wu001_implementation_tree: 8abbe9040cb72357387ec3c29f0e1e74921af0ea
pull_request: 419
canonical_science_base: changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3
planning_base: analysis/planck-mes-extended-data-execution-20260826@80781295cb161436eac164fc40bd7f57adfe10d1
selected_work_unit: PMG-WU-002
```

The nonexistent ref `analysis/planck-mes-pmg-wu002-transition-20260827` is forbidden.  
This package lives on the real PR #419 head branch.

## Execution permission

PR #419 is still an open draft at package compilation. Therefore:

- preferred: merge/accept PR #419, then create a fresh PMG-WU-002 branch from the accepted descendant containing this package;
- stacked exception: execute from the exact package-host head only after an explicit user decision;
- do not implement PMG-WU-002 on the PR #419 branch itself merely because this package is stored there.

## Read before editing

```text
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/PACKAGE_INDEX.yaml
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/AUTHORITY_AND_SCOPE.yaml
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/PR419_ACCEPTANCE_BINDING.yaml
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/VALIDATOR_TRANSITION_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/PMG_WU002_EXECUTION_CONTRACT.yaml
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/GUIDE_BINDING.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/FORMALISM_CONTRACT.yaml
docs/codex_handoff/planck_mes_irrep_global_formalism_execution/FORMALISM_MIGRATION_MATRIX.yaml
docs/generated/planck_mes_irrep_formalism/wu001_terminal.json
scripts/validate_planck_mes_pmg_wu002_transition.py
```

## First commands

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch origin --prune

test "$(git rev-parse 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0^{tree})" = "8abbe9040cb72357387ec3c29f0e1e74921af0ea"
git merge-base --is-ancestor "47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0" HEAD

python scripts/validate_planck_mes_pmg_wu002_transition.py --check-git
python -m pytest -q tests/contracts/test_planck_mes_pmg_wu002_transition.py
python -m pytest -q tests/contracts/test_observable_irrep_state.py
```

If PR #419 has not been accepted and the user did not explicitly authorize stacked execution, stop:

```text
BLOCKED_BY_UNRESOLVED_SPEC:
  question: whether to merge PR #419 first or execute PMG-WU-002 as a stacked branch
```

Do not guess.

## Required implementation branch

After authority is resolved:

```bash
git switch --detach <accepted-base-sha>
git switch -c changeset/planck-mes-global-formalism-adapters-$(date +%Y%m%d)
```

## Objective

Implement exactly PMG-WU-002:

```text
canonical ObservableIrrepState
        !=
physical JointAnisotropyState

MesPremiseNormalizer
  = one-way, same-channel premise normalization
  creates_direction = false
  creates_STF_shape = false
  creates_information = false

ResponseBoundObservableState
  requires exact response/channel/frame/basis/units compatibility
  reports identified sets when response rank is deficient

orbit_catalogue_v3
  accepts physical JointAnisotropyState only
  refuses ObservableIrrepState exactly
```

## Test-first order

1. Add RED tests for premise information fabrication, response mismatch, rank-deficient point identification, physical-orbit refusal, legacy payload mutation, and migration coverage.
2. Implement `mes_premise_normalization.py` and `response_bound_observable_state.py`.
3. Add the smallest adapters/refusals in the four declared legacy surfaces.
4. Update `migration_status.json`.
5. Emit `wu002_terminal.json` with final commit/tree, test commands, hashes, replay, and next action PMG-WU-003.
6. Run the transition diff validator.
7. Run one read-only fresh review; apply at most one targeted repair.

## Forbidden

- no Planck map read;
- no new statistical result;
- no physical forward-response model;
- no scalar-to-direction/STF construction;
- no ObservableIrrepState input to physical orbit code;
- no change to frozen scalar ranks, expected outputs, or tolerances;
- no successor planning package;
- no full suite by default.

## PASS transition

```text
PMG-WU-002 SUCCEEDED
→ immediately start PMG-WU-003
→ execute the map-free coordinate/reducer mechanism audit
```

A scaffold, tests-only patch, documentation-only patch, or unexecuted terminal is not PASS.
