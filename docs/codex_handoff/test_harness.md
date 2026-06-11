# Codex Test Harness

`scripts/codex_harness/run_subset.py` provides deterministic local pytest
subsets for PR work. It runs from the repository root and prints the exact
child command before execution.

The runner does not set `PYTHONPATH` or hide child-process failures. By default
it uses `venv/bin/python` when the repository virtual environment exists; if it
does not, it uses the interpreter running the harness. Use `--python PATH` to
override the child interpreter explicitly.

## Subsets

| Subset | Command shape | Scope |
|---|---|---|
| `collect` | `python -m pytest --collect-only -q` | Import and collection reachability. |
| `smoke` | `python -m pytest -m smoke -q` | Small smoke tests; not scientific validation. |
| `fast` | `python -m pytest -m "fast and not slow" -q` | Fast marked local subset. |
| `package` | `python -m pytest htt/test_packaging_imports.py -q` | Packaging/import smoke. |

List available subsets:

```bash
python scripts/codex_harness/run_subset.py --list
```

Print a command without running it:

```bash
python scripts/codex_harness/run_subset.py smoke --dry-run
```

Run a subset:

```bash
python scripts/codex_harness/run_subset.py package
```

These subsets are L1 harness evidence only. They do not validate native solver
behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null
calibration, morphology compatibility, or family-identification evidence.
