# Codex handoff — PMG-WU-002 global-formalism boundary migration

## Authority

```yaml
repository: cosmosapjw-quantum/htt_base
package_compilation_host: changeset/planck-mes-observable-irrep-state-20260827
accepted_via: PR #419 merged
accepted_merge_commit: c1068f12e63b473c145ca895a2335aceba2c04ec
accepted_merge_tree: 19305cc126ff3eab905765d39093b9488896c01a
implementation_branch: changeset/planck-mes-global-formalism-adapters-20260827
wu001_implementation_source: 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0
wu001_implementation_tree: 8abbe9040cb72357387ec3c29f0e1e74921af0ea
pull_request: 419
canonical_science_base: changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3
planning_base: analysis/planck-mes-extended-data-execution-20260826@80781295cb161436eac164fc40bd7f57adfe10d1
selected_work_unit: PMG-WU-002
```

The nonexistent ref `analysis/planck-mes-pmg-wu002-transition-20260827` is
forbidden. The transition package was compiled on the PR #419 head branch and
is now present in the accepted merge ancestry and the implementation branch.

## Execution permission

PR #419 was an open draft when the package was compiled, so
`PR419_ACCEPTANCE_BINDING.yaml` intentionally preserves that historical
`OPEN_DRAFT/PENDING` snapshot. Current inspectable Git authority supersedes
that compilation-time state:

- PR #419 is merged at `c1068f12e63b473c145ca895a2335aceba2c04ec`;
- the accepted tree is `19305cc126ff3eab905765d39093b9488896c01a`;
- `changeset/planck-mes-global-formalism-adapters-20260827` is descended from
  that merge and is the authorized PMG-WU-002 implementation branch;
- no additional stacked-execution decision is required.

A moved remote ref, missing package after an exact fetch, failed package
validator, or dirty worktree remains blocking. The former PR-acceptance choice
is resolved and must not produce `BLOCKED_BY_UNRESOLVED_SPEC` again.

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
git switch changeset/planck-mes-global-formalism-adapters-20260827
git pull --ff-only origin changeset/planck-mes-global-formalism-adapters-20260827

test "$(git rev-parse 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0^{tree})" = \
  "8abbe9040cb72357387ec3c29f0e1e74921af0ea"
git merge-base --is-ancestor \
  47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0 HEAD
git merge-base --is-ancestor \
  c1068f12e63b473c145ca895a2335aceba2c04ec HEAD

for path in \
  docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/CODEX_HANDOFF.md \
  scripts/validate_planck_mes_pmg_wu002_transition.py \
  tests/contracts/test_planck_mes_pmg_wu002_transition.py; do
  test -f "$path"
done

python scripts/validate_planck_mes_pmg_wu002_transition.py --check-git
python -m pytest -q tests/contracts/test_planck_mes_pmg_wu002_transition.py
python -m pytest -q tests/contracts/test_observable_irrep_state.py

export PMG_WU002_BASE_SHA="$(git rev-parse HEAD)"
test -z "$(git status --porcelain)"
```

The base variable is deliberately captured from the exact fetched branch head
immediately before edits. This prevents transition-seal documentation commits
from contaminating the later PMG-WU-002 changed-path check.

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

1. Add RED tests for premise information fabrication, response mismatch,
   rank-deficient point identification, physical-orbit refusal, legacy payload
   mutation, and migration coverage.
2. Implement `mes_premise_normalization.py` and
   `response_bound_observable_state.py`.
3. Add the smallest adapters/refusals in the four declared legacy surfaces.
4. Update `migration_status.json`.
5. Emit `wu002_terminal.json` with final commit/tree, test commands, hashes,
   replay, and next action PMG-WU-003.
6. Run the transition diff validator against `$PMG_WU002_BASE_SHA`.
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

A scaffold, tests-only patch, documentation-only patch, or unexecuted terminal
is not PASS.
