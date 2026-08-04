# Codex Test Harness

`scripts/codex_harness/run_subset.py` provides deterministic local pytest
subsets for PR work. It runs from the repository root and prints the exact
child command before execution.

The runner does not hide child-process failures. It clears ambient pytest
controls, explicitly declares the repository source-layout roots in the child
environment, disables the pytest cache provider, and replaces the root
`addopts`. By default it uses `venv/bin/python` when the current checkout has
one and otherwise uses the interpreter running the harness.
Use `--python PATH` to override the child interpreter explicitly. Import
provenance is checked separately by the `active-import` PR-280 profile.
Authoritative receipt generation additionally requires a prefix-owned pytest
installation; a linked worktree may reuse the shared repository venv for that
receipt-only lane, and the resulting environment remains identity-bound.

## Subsets

| Subset | Command shape | Scope |
|---|---|---|
| `collect` | cache disabled, root `addopts` replaced, `--collect-only` | Import and collection reachability. |
| `smoke` | eight versioned explicit node IDs | Small process smoke; not scientific validation. |
| `fast` | six versioned explicit node IDs | Focused development feedback. |
| `package` | three explicit clean-wheel/resource node IDs | Packaging/import smoke. |

The source of these selections is
`docs/research_program/post_pr275/harness_profiles_v4.yaml`. Marker-only smoke
or fast selection is forbidden. The fuller PR-280 runner lists the exact,
current-active, scientific, data-preflight, formal-tool, publication, and
full-inventory profiles:

```bash
python scripts/codex_harness/run_pr280_harness.py list
```

The cache-free full-inventory authority is JUnit-based. Pytest's JUnit XML
does not distinguish an ordinary pass from XPASS, does not record deselected
items, and does not individually represent passing `unittest.subTest` rows.
The v4 receipt therefore reports `passed_or_xpassed_case_elements`, preserves
each non-pass subtest with an ordinal identity, and keeps the suite-declared
and extra-subtest counts separate. It never fabricates zero XPASS,
deselection, or hidden-subtest counts to reconcile older terminal summaries.

The fresh PR-280 run on execution source `315277077e27...` collected 10,799
testcase elements (10,815 suite-declared units) and ended with 458 failures,
71 skips, and 19 xfails. Exact rule classification covers all 548 non-pass
outcomes with `UNKNOWN_UNCLASSIFIED=0`. Three outcomes remain
`ACTIVE_CORE_REGRESSION`: the Python PSTF D2 progressive-closure guard, the
production CAMB-import policy, and the repo-scoped handoff installer's
transitive context closure. They are bound one-to-one to PR-296, PR-295, and
PR-297 respectively. This is a terminal negative harness candidate, not an
active-core pass or scientific readiness result; the two older 406-failure
records remain unchanged historical evidence.

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

The `package` subset is the three-node v4 profile above; it is not the whole
legacy `htt/test_packaging_imports.py` file.  The cache-free full inventory
still executes that file and records its environment-coupled historical
expectations in the exact failure map.

These subsets are L1 harness evidence only. They do not validate native solver
behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null
calibration, morphology compatibility, or family-identification evidence.
