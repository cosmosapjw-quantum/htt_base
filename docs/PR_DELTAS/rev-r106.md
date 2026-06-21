# REV-R106 - Code-Capability External-Audit Package (broad raw-source disclosure)

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: code_and_pipeline_source_only_no_raw_data
sky_support_status: not_applicable_code_audit
null_mock_status: not_applicable_code_audit
generating_command: `Codex REV-R106 build a code-capability external-audit zip that shows every runnable capability with broad raw code, guides, and data-access list`
git_commit_or_worktree_state: pending_rev_r106_commit

## Request

Make a zip an external auditor can use to see everything runnable in the
codebase: a list of the data the code can actually access, a detailed
explanation of the large code surface, and the essential real code files in raw
form. Include code currently marked old/legacy/deprecated so its separate
executability can be probed. Exclude incidental noise -- raw datasets, tests,
and claim-gate/blocker code. Be broad, not overly compact or conservative.

## Approach

New builder `scripts/build_code_capability_audit_package.py` produces a
deterministic disclosure zip aimed at an execution-feasibility audit, distinct
from the result/claim packages (which carry prose and results, not code).

Selection is rule-based off `git ls-files` (tracked, deterministic):

INCLUDED (broad, on purpose) -- 764 entries / ~292k LOC:
- full non-test library tree: `htt/bass` (210), `htt/htt` (125), `htt/mio`
  (41), `htt/obsstat` (15), `htt/workspace` (16), `htt/src` COMMON (22);
- Rust `bass_rs` solver crate `src/` (165 .rs) + `Cargo.toml`/`Cargo.lock`;
- runnable science drivers `scripts/` (55, gate/lint CLIs removed);
- data-download pipeline `dl_pipeline/` (19) incl. the `sources.json` manifest;
- recombination + reionization execution stacks (18);
- LEGACY `htt/tsc` + `htt/tsc_legacy` (50) -- shipped so their separate
  executability can be probed;
- configs, package manifests, code READMEs, and the data/repo inventories.

EXCLUDED (incidental noise):
- tests / `conftest` / `pytest.ini`;
- raw datasets + binaries (`.npz/.fits/.csv/.png/.pdf/...`);
- claim-gate / lint / validate / audit-package / status enforcement CLIs
  (`GATE_SCRIPTS` allow-list-of-exclusions);
- `target/`, `venv/`, figures, gitignored `project/`.

Four navigation guides are generated, not hand-waved:
- `02_CODE_MAP.md` (auto): per-package file counts, LOC, and purpose.
- `03_ENTRY_POINTS.md` (auto): 93 detected runnables (Python `__main__`/argparse,
  shell, Rust `fn main`) with one-line descriptions.
- `04_DATA_ACCESS.md` (auto): the external-download manifest (Planck/ACT/SPT/
  BICEP-Keck/DESI/CF4/CAMB) + a static scan listing 212 data paths/URLs the
  shipped code references + the inventory pointer.
- `01_ARCHITECTURE_GUIDE.md` (authored): the BASS/HTT/MIO/OBSSTAT ownership
  stack, the dual MB-95/PSTF solver track, execution stacks, and the legacy
  layer.

Plus `00_README.md` and a dedicated capability/feasibility `AUDIT_PROMPT.md`.

## Role Split

- Code-cartographer steelman: source the file list from `git ls-files`; bucket
  by real top-level package; auto-generate the map/entry-points/data-access from
  the actual files, not a hand list.
- Claim-gate reviewer steelman: this is a code-disclosure, not a results bundle;
  the manifest keeps `claim_tier=diagnostic_only`, `family_identification:false`,
  `native_solver_result:false`, and a scope note that code inclusion is not a
  validated result.
- Harness/reproducibility steelman: byte-deterministic zip (fixed date, sorted
  entries) with `--check`/`--dry-run` and required assertions
  (no_test_files / no_raw_datasets / no_gate_blocker_clis + presence of
  library/rust/science/legacy/pipeline/stack groups).

## Changes

- `scripts/build_code_capability_audit_package.py`: the builder + guide
  generators + authored guide/README/prompt.
- `docs/code_capability_audit/htt_base_code_capability_audit_package.{zip,_manifest.json}`
  + `htt_base_code_capability_audit_prompt.md`.
- `tests/contracts/test_code_capability_audit_package.py`: gates pass; broad
  inclusion (>500 entries, library>300, rust>100, science>20, legacy/pipeline/
  stack present); tests/raw-data/gate-CLIs excluded; guides present; manifest
  keeps family-ID/native-solver blocked; deterministic; on-disk up-to-date.

## Artifact Metadata

- owner: COMMON
- implementation_scope: common
- claim_tier: diagnostic_only
- config_hash:
  - `scripts/build_code_capability_audit_package.py:sha256:b98089c9c64a723efb0b371d066b38fefd4d0e56c09a05ff30048971d881e2b1`
  - `tests/contracts/test_code_capability_audit_package.py:sha256:34f255152dfd9e46d66c1260ed9becad1813b993ee6e3f943b103c52bf669ba0`
  - `docs/code_capability_audit/htt_base_code_capability_audit_package.zip:sha256:90c2d9cc4af7829ff89b5fba87ebadd12b09657f0472d4b3bd6b25435a2742f1`
- caveats:
  - broad raw-source disclosure for code/capability audit; not a results or claims bundle;
  - tests, raw datasets, and claim-gate/lint enforcement CLIs excluded as noise;
  - legacy tsc included for separate-executability probing; not an active science owner;
  - no raw observational data shipped; the data-access guide + inventory list what the code can reach.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `venv/bin/python scripts/build_code_capability_audit_package.py` | PASS | 764 entries; ~292k LOC across 758 source files; all assertions true. |
| `venv/bin/python scripts/build_code_capability_audit_package.py --check` | PASS | Byte-deterministic; up-to-date. |
| `venv/bin/python scripts/build_code_capability_audit_package.py --dry-run` | PASS | group_counts: library 441, rust 165, science 55, legacy 50, pipeline 19, stacks 18. |
| `pytest -q tests/contracts/test_code_capability_audit_package.py` | PASS | `7 passed`. |
