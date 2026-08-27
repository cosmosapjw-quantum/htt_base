# Codex execution prompt — PMG-WU-002

Repository: `cosmosapjw-quantum/htt_base`

Use the transition package at:

`docs/codex_handoff/planck_mes_pmg_wu002_execution_transition`

## Accepted execution authority

```yaml
accepted_via: PR #419 merged
accepted_merge_commit: c1068f12e63b473c145ca895a2335aceba2c04ec
accepted_merge_tree: 19305cc126ff3eab905765d39093b9488896c01a
implementation_branch: changeset/planck-mes-global-formalism-adapters-20260827
wu001_implementation_commit: 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0
wu001_implementation_tree: 8abbe9040cb72357387ec3c29f0e1e74921af0ea
pull_request: 419
```

The historical `PR419_ACCEPTANCE_BINDING.yaml` records the compilation-time
`OPEN_DRAFT/PENDING` state. It is provenance, not the current live authority.
PR #419 is now merged, so PMG-WU-002 execution permission is granted from the
accepted descendant above.

Do not use `analysis/planck-mes-pmg-wu002-transition-20260827`; that ref does
not exist. Do not resume from the stale `47ef087...` branch tip.

Before coding:

```bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch origin --prune
git switch changeset/planck-mes-global-formalism-adapters-20260827
git pull --ff-only origin changeset/planck-mes-global-formalism-adapters-20260827

git merge-base --is-ancestor \
  c1068f12e63b473c145ca895a2335aceba2c04ec HEAD

test -f docs/codex_handoff/planck_mes_pmg_wu002_execution_transition/CODEX_HANDOFF.md
test -f scripts/validate_planck_mes_pmg_wu002_transition.py
test -f tests/contracts/test_planck_mes_pmg_wu002_transition.py

python scripts/validate_planck_mes_pmg_wu002_transition.py --check-git
python -m pytest -q tests/contracts/test_planck_mes_pmg_wu002_transition.py
python -m pytest -q tests/contracts/test_observable_irrep_state.py

export PMG_WU002_BASE_SHA="$(git rev-parse HEAD)"
test -z "$(git status --porcelain)"
```

Do **not** return `BLOCKED_BY_UNRESOLVED_SPEC` for PR #419 acceptance or a
missing transition package after the commands above pass. A moved remote ref,
missing file after the exact fetch, failed validator, or dirty worktree remains
a legitimate blocker.

Implement **exactly PMG-WU-002** on this branch using TDD. Add
`MesPremiseNormalizer`, `ResponseBoundObservableState`, exact-type
adapters/refusals, complete migration coverage, and a content-bound
`wu002_terminal.json`. Preserve every frozen scalar result and all
observer/physical/response boundaries.

Do not read Planck maps, implement a physical response model, run the full
suite by default, change scientific expected outputs, or create another
planning package.

Before reporting PASS:

```bash
git diff --name-only "$PMG_WU002_BASE_SHA"..HEAD | \
  python scripts/validate_planck_mes_pmg_wu002_transition.py --changed-paths -
git diff --check "$PMG_WU002_BASE_SHA"..HEAD
```

On PASS, start PMG-WU-003 immediately. Never report PASS for a scaffold,
documentation-only patch, tests-only patch, or unexecuted work.
