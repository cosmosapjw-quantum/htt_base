# Codex execution prompt — PMG-WU-002

Repository: `cosmosapjw-quantum/htt_base`

Use the transition package at:

`docs/codex_handoff/planck_mes_pmg_wu002_execution_transition`

The implemented PMG-WU-001 source is:

```yaml
branch: changeset/planck-mes-observable-irrep-state-20260827
commit: 47ef087b158e0dbf8ac4b7b5205f39c1a050d9c0
tree: 8abbe9040cb72357387ec3c29f0e1e74921af0ea
pull_request: 419
```

Do not use `analysis/planck-mes-pmg-wu002-transition-20260827`; that ref does not exist.

Before coding, read `CODEX_HANDOFF.md` and validate the package:

```bash
python scripts/validate_planck_mes_pmg_wu002_transition.py --check-git
python -m pytest -q tests/contracts/test_planck_mes_pmg_wu002_transition.py
```

PR #419 is an open draft. If it has not been accepted and no explicit user instruction authorizes stacked execution, stop with `BLOCKED_BY_UNRESOLVED_SPEC` and state the one required decision: merge/accept first versus stacked PMG-WU-002.

After the base is authorized, implement **exactly PMG-WU-002** on a fresh branch. Use TDD. Add `MesPremiseNormalizer`, `ResponseBoundObservableState`, exact-type adapters/refusals, migration coverage, and a content-bound `wu002_terminal.json`. Preserve every frozen scalar result and all observer/physical/response boundaries.

Do not read Planck maps, implement a physical response model, run the full suite, change scientific expected outputs, or create another planning package.

On PASS, start PMG-WU-003 immediately. Never report PASS for a scaffold, documentation-only patch, or unexecuted work.
