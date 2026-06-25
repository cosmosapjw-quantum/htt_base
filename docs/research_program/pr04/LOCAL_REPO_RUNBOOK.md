# Local repository runbook

## 0. Freeze the baseline

From the canonical repository root:

```bash
git status --short
git rev-parse HEAD
git switch -c research/pr04-multicomponent
python -m compileall -q htt
# Run the repository's existing fast and legacy regression commands here.
```

Record the commit, Python version, dependency lock hash, existing test result,
and any deliberate dirty files. Do not apply the overlay onto an unexplained
dirty working tree.

## 1. Preflight

```bash
python /path/to/prep06/tools/preflight_repo.py   --repo "$PWD"   --out artifacts/pr04/preflight.json
```

PASS requires a discoverable `htt` source umbrella, Python >=3.10, NumPy,
absence of non-identical overlay targets, and either a clean Git tree or an
explicit recorded waiver.

## 2. Review and merge in scientific dependency order

Apply one PR at a time:

```bash
python /path/to/prep06/tools/install_handoff.py --repo "$PWD" --apply-overlay --prs PR04-002
python /path/to/prep06/tools/verify_local_integration.py --repo "$PWD" --tests schema
# review and commit
```

Then repeat for `PR04-003`, `PR04-004`, `PR04-005`, `PR04-006`, and `PR04-007`.
The required review order is representation/conventions, GR first jet,
statistics, Bianchi-I constraints, theorem tests, then legacy pushforward.

The patch alternative is:

```bash
git apply --check /path/to/prep06/patches/0001-PR04-002-*.patch
git am /path/to/prep06/patches/0001-PR04-002-*.patch
```

## 3. Install repository scaffolding

```bash
python /path/to/prep06/tools/install_handoff.py   --repo "$PWD"   --install-scaffold
```

This installs external gate tests, the CI workflow, structured issue form,
research documentation, and the machine-readable ticket registry. Existing
non-identical files are never silently replaced.

## 4. Required merge gate

```bash
python /path/to/prep06/tools/verify_local_integration.py --repo "$PWD"
python -m compileall -q htt
# Run the canonical repository's full tests and legacy result-regression suite.
```

The external 23 tests are necessary but not sufficient. The local full suite is
the authority for compatibility with the canonical branch.

## 5. Open local execution tickets

Use `.github/ISSUE_TEMPLATE/research-execution.yml`, or generate Markdown:

```bash
python /path/to/prep06/tools/generate_issue_markdown.py   --registry /path/to/prep06/registries/local_tickets.json   --out-dir artifacts/pr04/issues
```

Create one parent research issue and attach the LR-06 tickets as sub-issues in
dependency order. A blocked ticket terminates with its registered blocker code;
it must not emit a substitute observational number.

## 6. Publication order

- PAPER-A and PAPER-B can proceed after LR-06A plus their proof-review gates.
- PAPER-C begins only after LR-06D–G produce calibrated artifacts and LR-06H
  passes joint rank, coverage, ablation and held-out gates.
- The Rust/native-transfer project remains separate under LR-06L.

## Deterministic numerical runtime

The verification command fixes OpenBLAS/OpenMP/MKL/NumExpr thread counts to one. This avoids oversubscription and import-plus-subprocess stalls and makes the theorem gate reproducible across CI jobs.
