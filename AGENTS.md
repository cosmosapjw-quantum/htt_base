# Repository Guidelines

## Project Structure & Module Organization
The root crate in `src/` is the Rust core: physics, solver, recombination, source assembly, and PyO3 bindings exposed through `src/lib.rs`. Active Python work lives in `htt/`, which contains the current `bass`, `htt`, `mio`, `tsc`, `workspace`, and shared `src/common` packages plus their tests. `legacy/` preserves the older integrated Python layout and Makefile workflows; touch it only for compatibility work. Research notes and governance live in `docs/`, figure outputs in `figures/`, helper scripts in `scripts/`, and stable regression inputs in `tests/fixtures/`.

## Build, Test, and Development Commands
Use the Rust gates for core changes:

- `cargo build --lib --release` compiles the main library and is a standard PR check.
- `cargo test --lib --release --no-run` is the fast compile/test sanity gate.
- `cargo test --lib --release <module_or_test_name>` runs targeted Rust tests for the area you changed.

Use the active Python package for HTT/BASS/TSC work:

- `python -m pip install -e ./htt[dev]` installs the editable Python workspace.
- `venv/bin/python -m pytest htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` runs the current touched-surface regression.
- `python scripts/make_paper_figures.py` regenerates paper figures when analysis or reporting logic changes.
- `make -C legacy test` runs the preserved legacy suite when compatibility matters.

## Coding Style & Naming Conventions
Rust follows standard conventions: `snake_case` for modules/functions, `CamelCase` for types, small focused modules, and shared constants routed through SSOT helpers rather than duplicated locally. Python uses 4-space indentation, `snake_case` modules and tests, explicit type hints, frozen dataclasses where contracts are shared, and short module docstrings. Prefer `python -m pytest` over bare `pytest` to avoid import-path drift.

## Testing Guidelines
Name Python tests `test_*.py`; keep fixtures near the owning package or in `tests/fixtures/` for shared baselines. New changes should add identity, limit, regression, and provenance/caveat checks, matching the expectations in `docs/PR_CONSTITUTION.md`. When a change affects physics definitions or exported semantics, verify the relevant SSOT path in `docs/SSOT_POLICY.md`.

## Commit & Pull Request Guidelines
Match the existing commit style: a scoped track or audit prefix, then a concise subject, for example `FB-3.2: ...` or `W23D3: AUDIT(...) ...`. Keep each commit to one logical object or rule change. PRs should summarize affected modules, list exact verification commands, note any baseline or figure deltas, and add or update the corresponding design note in `docs/PR_DELTAS/` when the change is architectural.
