#!/usr/bin/env python3
"""Build a CODE-CAPABILITY external-audit package.

Unlike the research-only / final-results packages (which carry results and
prose), this package shows an external auditor *what the codebase can actually
run*: the science/solver source tree in raw form, the data the code can reach,
auto-generated navigation guides, and an authored architecture guide.

Included (broad, on purpose):
- the full non-test library tree (BASS / HTT / MIO / OBSSTAT / workspace /
  common), the Rust ``bass_rs`` solver crate, the runnable science scripts, the
  data-download pipeline, the recombination/reionization execution stacks, the
  config files, and the legacy ``tsc`` Teff-chart layer (kept so the auditor can
  probe its separate executability);
- four auto-generated guides (code map, entry points, data access) plus an
  authored architecture guide, README, and audit prompt;
- the observational-data inventory and repo inventory.

Excluded (incidental noise, per the audit request):
- tests and conftest files;
- raw datasets and binary artifacts (``.npz/.fits/.csv/.png/.pdf/...``);
- claim-gate / lint / validate / audit-package / status *enforcement* CLIs
  (the blocker scaffolding), listed in ``GATE_SCRIPTS``;
- build trees (``target/``, ``venv/``), figures, and the gitignored ``project/``.

The archive is byte-deterministic (fixed zip date, sorted entries) so ``--check``
detects drift.

    python scripts/build_code_capability_audit_package.py            # write
    python scripts/build_code_capability_audit_package.py --check    # verify
    python scripts/build_code_capability_audit_package.py --dry-run  # summary
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = Path("docs/code_capability_audit")
DEFAULT_OUTPUT_ZIP = REPORT_DIR / "htt_base_code_capability_audit_package.zip"
DEFAULT_OUTPUT_MANIFEST = REPORT_DIR / "htt_base_code_capability_audit_package_manifest.json"
DEFAULT_OUTPUT_PROMPT = REPORT_DIR / "htt_base_code_capability_audit_prompt.md"
SCHEMA_VERSION = "common.code_capability_audit_package.v1"
ARTIFACT_ID = "code_capability_audit_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ARCHIVE_ROOT = "code_capability_audit"

THIS_SCRIPT = "scripts/build_code_capability_audit_package.py"

# --- inclusion rules ---------------------------------------------------------

# Roots whose source tree we walk and include (minus tests/data, see below).
CODE_ROOTS = (
    "htt/",
    "src/",
    "scripts/",
    "dl_pipeline/",
    "recombination_execution_stack/",
    "reionization_execution_stack/",
    "configs/",
)
CODE_EXTS = {".py", ".rs", ".pyx", ".pyi", ".sh"}
CONFIG_EXTS = {".toml", ".yaml", ".yml", ".cfg", ".ini"}
# .json/.txt only inside these (config), never generic generated reports.
CONFIG_JSON_PREFIXES = ("dl_pipeline/config/", "dl_pipeline/assets/obs_meta/", "configs/")
README_MAX_DEPTH_ROOTS = CODE_ROOTS  # README.md inside code roots explains code.

# Individually pinned files (build manifests, top-level guides, inventories).
PINNED_FILES = (
    "Cargo.toml",
    "Cargo.lock",
    "README.md",
    "CLAUDE.md",
    "htt/pyproject.toml",
    "dl_pipeline/requirements.txt",
    "dl_pipeline/run_all.sh",
    "docs/generated/observational_data_inventory.md",
    "docs/generated/observational_data_inventory.json",
    "docs/generated/optional_dependency_status.md",
    "docs/generated/repo_inventory.json",
    "docs/SSOT_POLICY.md",
)

# --- exclusion rules ---------------------------------------------------------

EXCLUDE_PATH_SUBSTRINGS = (
    "/tests/",
    "/test/",
    "/__pycache__/",
    "/target/",
    "/venv/",
    "/node_modules/",
    "/.git/",
)
EXCLUDE_BASENAME_RE = re.compile(r"^(test_.*\.py|.*_test\.py|conftest\.py|pytest\.ini|\.coveragerc)$")
RAW_DATA_EXTS = {
    ".npz", ".npy", ".fits", ".fit", ".csv", ".tsv", ".h5", ".hdf5", ".parquet",
    ".png", ".jpg", ".jpeg", ".pdf", ".zip", ".gz", ".xz", ".sha256", ".log",
    ".bbl", ".blg", ".aux", ".xlsx", ".pkl", ".pickle", ".npy",
}

# Claim-gate / lint / validate / audit-package / status enforcement CLIs.
GATE_SCRIPTS = frozenset(
    {
        "audit_manuscript_figures.py",
        "check_artifact_manifests.py",
        "check_claim_language.py",
        "check_publication_claim_freeze.py",
        "pdf_claim_lint.py",
        "build_external_audit_package.py",
        "build_research_only_audit_package.py",
        "build_statistical_formalism_audit_package.py",
        "build_final_report_audit_package.py",
        "build_code_capability_audit_package.py",
        "generate_semantic_firewall_fuzz_report.py",
        "verify_formalism_figure_labels.py",
        "verify_skill_layout.py",
        "validate_codex_config_shape.py",
        "validate_pr_dag.py",
        "init_status.py",
        "progress_report.py",
        "new_pr_delta.py",
        "skill_index.py",
        "generate_manuscript_status_snippets.py",
        "generate_theorem_to_test_map.py",
        "inventory_revision_program_packages.py",
        "inventory_external_research_inputs.py",
        "generate_revision_experiment_assets.py",
        "generate_revision_research_program.py",
    }
)

# Per-top-level-package one-line purpose for the auto-generated code map.
PACKAGE_PURPOSE = {
    "htt/bass": "BASS physics core: PSTF/tetrad hierarchy, recombination, kinetic theory, transfer, atlas, geometry, closure.",
    "htt/htt": "HTT inference layer: departure models, evidence, nulls, posterior pushforward, statistics, observational bounds.",
    "htt/mio": "MIO observatory: diagnostic certificates, coherence, tension, evidence anatomy, formalism (budgets/bounds).",
    "htt/obsstat": "OBSSTAT observer-side estimators: low-ell scalars, morphology, null ensembles, map/feature extraction.",
    "htt/workspace": "Workspace contracts and orchestration glue between BASS/HTT/MIO/OBSSTAT.",
    "htt/src": "Shared COMMON layer: contracts, artifact manifests, status snapshot, transfer registry.",
    "htt/tsc": "LEGACY Teff-chart service layer and admissibility overlays (import-compatible, not an active science owner).",
    "htt/tsc_legacy": "LEGACY frozen TSC reproduction shims.",
    "htt/scripts": "In-package helper drivers.",
    "src": "Rust bass_rs crate: MB-95 production solver (CAMB-convention sync gauge, Rodas5P/diffsol), PyO3 bindings.",
    "scripts": "Runnable science drivers: CAMB/PSTF comparisons, FLRW spectrum export, real-data measurements, runtime diagnostics, figure makers.",
    "dl_pipeline": "Observational-data download/extraction pipeline (Planck/ACT/SPT/BICEP-Keck/DESI/CF4/CAMB) with a single sources.json manifest.",
    "recombination_execution_stack": "Anisotropic radiative-transfer recombination execution bundle.",
    "reionization_execution_stack": "Anisotropic radiative-transfer reionization execution bundle.",
    "configs": "Runnable configuration files.",
    "htt (top-level)": "Top-level htt package files: __init__, packaging, precision dashboard, README.",
    "(root manifests & guides)": "Repo-root build manifests and guides (Cargo.toml/lock, README, CLAUDE.md).",
    "(inventories & policy docs)": "Observational-data and repo inventories, optional-dependency status, SSoT policy.",
}


# --- helpers -----------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    archive_path: str
    group: str
    source_path: Path | None = None
    content: bytes | None = None

    def bytes(self, repo_root: Path) -> bytes:
        if self.content is not None:
            return self.content
        assert self.source_path is not None
        return (repo_root / self.source_path).read_bytes()

    def source_text(self) -> str:
        return self.source_path.as_posix() if self.source_path is not None else f"virtual:{self.archive_path}"


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _stable_hash(payload: Any) -> str:
    return _sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())


def _git_files(repo_root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=repo_root, text=True, capture_output=True, check=True
    )
    return sorted(line for line in out.stdout.splitlines() if line.strip())


def _git_state(repo_root: Path) -> str:
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True, capture_output=True, check=False
    )
    commit = head.stdout.strip() if head.returncode == 0 else "unknown"
    dirty = subprocess.run(
        ["git", "status", "--short"], cwd=repo_root, text=True, capture_output=True, check=False
    )
    return f"{commit}+dirty" if dirty.stdout.strip() else commit


def _is_excluded(rel: str) -> bool:
    if any(sub in f"/{rel}" for sub in EXCLUDE_PATH_SUBSTRINGS):
        return True
    base = rel.rsplit("/", 1)[-1]
    if EXCLUDE_BASENAME_RE.match(base):
        return True
    if Path(rel).suffix.lower() in RAW_DATA_EXTS:
        return True
    if rel.startswith("scripts/") and base in GATE_SCRIPTS:
        return True
    return False


def _is_included(rel: str) -> bool:
    if _is_excluded(rel):
        return False
    suffix = Path(rel).suffix.lower()
    base = rel.rsplit("/", 1)[-1]
    in_code_root = any(rel.startswith(root) for root in CODE_ROOTS)
    if in_code_root:
        if suffix in CODE_EXTS or suffix in CONFIG_EXTS:
            return True
        if base == "README.md":
            return True
        if suffix == ".json" and any(rel.startswith(p) for p in CONFIG_JSON_PREFIXES):
            return True
        if suffix == ".txt" and rel.startswith("dl_pipeline/"):
            return True
        if suffix == ".md" and rel.startswith(
            ("dl_pipeline/", "recombination_execution_stack/", "reionization_execution_stack/")
        ):
            return True
        return False
    return False


def _group_for(rel: str) -> str:
    suffix = Path(rel).suffix.lower()
    if rel.startswith("src/") or suffix == ".rs":
        return "rust_solver_source"
    if rel.startswith("scripts/"):
        return "science_driver"
    if rel.startswith("dl_pipeline/"):
        return "data_pipeline"
    if rel.startswith(("recombination_execution_stack/", "reionization_execution_stack/")):
        return "execution_stack"
    if rel.startswith("htt/tsc"):
        return "legacy_tsc"
    if rel.startswith("htt/"):
        return "library_source"
    if rel.startswith("configs/"):
        return "config"
    return "support"


def _collect_source_entries(repo_root: Path) -> list[Entry]:
    files = _git_files(repo_root)
    chosen: list[str] = []
    for rel in files:
        if _is_included(rel):
            chosen.append(rel)
    for rel in PINNED_FILES:
        if rel not in chosen and (repo_root / rel).is_file() and not _is_excluded(rel):
            chosen.append(rel)
    entries: list[Entry] = []
    for rel in sorted(set(chosen)):
        if not (repo_root / rel).is_file():
            continue
        entries.append(Entry(archive_path=f"{ARCHIVE_ROOT}/{rel}", group=_group_for(rel), source_path=Path(rel)))
    return entries


# --- guide generation --------------------------------------------------------


def _loc(data: bytes) -> int:
    return data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)


def _module_docstring_first_line(text: str) -> str:
    m = re.search(r'^\s*(?:[rbuRBU]{0,2})("""|\'\'\')(.*?)\1', text, re.DOTALL | re.MULTILINE)
    if not m:
        return ""
    body = m.group(2).strip().splitlines()
    return body[0].strip() if body else ""


def _top_package(rel: str) -> str:
    parts = rel.split("/")
    if "/" not in rel:
        return "(root manifests & guides)"
    if rel.startswith("docs/"):
        return "(inventories & policy docs)"
    if rel.startswith("htt/") and len(parts) >= 2:
        # htt/<file> (a dotted top-level file) buckets together; htt/<pkg>/... keeps the package.
        return "htt (top-level)" if "." in parts[1] else "/".join(parts[:2])
    return parts[0]


def _gen_code_map(repo_root: Path, source_entries: Sequence[Entry]) -> str:
    buckets: dict[str, dict[str, int]] = {}
    for entry in source_entries:
        rel = entry.source_path.as_posix()  # type: ignore[union-attr]
        pkg = _top_package(rel)
        data = (repo_root / rel).read_bytes()
        b = buckets.setdefault(pkg, {"files": 0, "loc": 0})
        b["files"] += 1
        b["loc"] += _loc(data)
    lines = [
        "# Code Map (auto-generated)",
        "",
        "Per top-level package: included source-file count and total lines of code",
        "(tests, raw data, and gate/lint CLIs are excluded by the package rules).",
        "",
        "| Package | Files | LOC | Purpose |",
        "| --- | ---: | ---: | --- |",
    ]
    for pkg in sorted(buckets):
        b = buckets[pkg]
        purpose = PACKAGE_PURPOSE.get(pkg, "")
        lines.append(f"| `{pkg}` | {b['files']} | {b['loc']} | {purpose} |")
    total_files = sum(b["files"] for b in buckets.values())
    total_loc = sum(b["loc"] for b in buckets.values())
    lines += ["| | | | |", f"| **total** | **{total_files}** | **{total_loc}** | |", ""]
    return "\n".join(lines) + "\n"


def _gen_entry_points(repo_root: Path, source_entries: Sequence[Entry]) -> str:
    rows: list[tuple[str, str, str]] = []
    for entry in source_entries:
        rel = entry.source_path.as_posix()  # type: ignore[union-attr]
        suffix = Path(rel).suffix.lower()
        if suffix == ".py":
            text = (repo_root / rel).read_text(encoding="utf-8", errors="replace")
            runnable = '__main__' in text and 'if __name__' in text
            argparse = "ArgumentParser" in text or "argparse" in text
            if not (runnable or argparse):
                continue
            kind = "CLI (argparse)" if argparse else "module main"
            doc = _module_docstring_first_line(text)
            rows.append((rel, kind, doc))
        elif suffix == ".sh":
            text = (repo_root / rel).read_text(encoding="utf-8", errors="replace")
            first = next((ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#!")), "")
            doc = first[1:].strip() if first.startswith("#") else ""
            rows.append((rel, "shell script", doc))
        elif suffix == ".rs":
            text = (repo_root / rel).read_text(encoding="utf-8", errors="replace")
            if re.search(r"\bfn\s+main\s*\(", text):
                rows.append((rel, "rust binary (fn main)", ""))
    rows.sort()
    lines = [
        "# Entry Points (auto-generated)",
        "",
        f"{len(rows)} runnable entry points were detected (Python `__main__`/argparse,",
        "shell scripts, and Rust `fn main`). The Rust crate is primarily a PyO3",
        "`cdylib` imported as `bass_rs`; most execution is driven from the Python",
        "science drivers under `scripts/`.",
        "",
        "| Path | Kind | One-line description |",
        "| --- | --- | --- |",
    ]
    for rel, kind, doc in rows:
        doc = doc.replace("|", "\\|")[:140]
        lines.append(f"| `{rel}` | {kind} | {doc} |")
    return "\n".join(lines) + "\n"


def _gen_data_access(repo_root: Path, source_entries: Sequence[Entry]) -> str:
    lines = [
        "# Data Access (auto-generated)",
        "",
        "What real data the code can reach, where it comes from, and how it is",
        "fetched/extracted. Raw datasets themselves are NOT shipped in this package;",
        "this guide plus the bundled `observational_data_inventory` lists them.",
        "",
        "## External download manifest (`dl_pipeline/config/sources.json`)",
        "",
    ]
    sources_path = repo_root / "dl_pipeline/config/sources.json"
    if sources_path.is_file():
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
        order = sources.get("_schema", {}).get("stage_order", [])
        keys = order or [k for k in sources if not k.startswith("_")]
        lines += [
            "| Stage | Doc | Base URL(s) / method | Size est. |",
            "| --- | --- | --- | --- |",
        ]
        for key in keys:
            stage = sources.get(key)
            if not isinstance(stage, dict):
                continue
            doc = str(stage.get("_doc", "")).replace("|", "\\|")[:120]
            method = stage.get("method", "")
            bases = [v for k, v in stage.items() if k.startswith("base") and isinstance(v, str)]
            url = (method + " " if method else "") + ("; ".join(bases) if bases else "")
            url = url.replace("|", "\\|")[:120] or "—"
            size = stage.get("size_estimate_GB")
            size_s = f"{size} GB" if size is not None else ""
            lines.append(f"| `{key}` | {doc} | {url} | {size_s} |")
        lines.append("")
    else:
        lines += ["(sources.json not found)", ""]

    # Static scan of included code for data references.
    ref_re = re.compile(
        r"(workdir/obs_bundle[\w./\-]*|data/[\w./\-]+|[\w./\-]+\.(?:npz|fits|fit|csv|h5|hdf5|npy)|https?://[\w./\-:%?=&]+)"
    )
    refs: set[str] = set()
    for entry in source_entries:
        rel = entry.source_path.as_posix()  # type: ignore[union-attr]
        if Path(rel).suffix.lower() not in {".py", ".rs", ".sh", ".json", ".yaml", ".yml", ".toml"}:
            continue
        text = (repo_root / rel).read_text(encoding="utf-8", errors="replace")
        for m in ref_re.finditer(text):
            ref = m.group(1).strip("\"'`,()[]{}")
            if len(ref) > 4 and not ref.endswith("/"):
                refs.add(ref)
    capped = sorted(refs)[:250]
    lines += [
        "## Data references found in the included code (static scan)",
        "",
        f"{len(refs)} distinct data paths/URLs were referenced in the shipped code "
        f"(showing {len(capped)}). These are the concrete inputs/outputs the code reads or writes.",
        "",
        "```",
        *capped,
        "```",
        "",
        "## Inventory",
        "",
        "See `code_capability_audit/docs/generated/observational_data_inventory.md` for the",
        "full inventory (Planck PR3 spectra/maps/masks/lensing, ACT, SPT-3G, BICEP/Keck,",
        "DESI Y1 tracers, CF4 peculiar-velocity grid, CAMB references) with per-file hashes",
        "and presence status under `workdir/obs_bundle/`.",
        "",
    ]
    return "\n".join(lines) + "\n"


def _virtual(archive: str, group: str, text: str) -> Entry:
    return Entry(archive_path=archive, group=group, content=text.encode("utf-8"))


def _all_entries(repo_root: Path) -> list[Entry]:
    source_entries = _collect_source_entries(repo_root)
    guides = [
        _virtual("00_README.md", "package_readme", render_readme()),
        _virtual("AUDIT_PROMPT.md", "audit_prompt", render_prompt()),
        _virtual("01_ARCHITECTURE_GUIDE.md", "guide", render_architecture_guide()),
        _virtual("02_CODE_MAP.md", "guide", _gen_code_map(repo_root, source_entries)),
        _virtual("03_ENTRY_POINTS.md", "guide", _gen_entry_points(repo_root, source_entries)),
        _virtual("04_DATA_ACCESS.md", "guide", _gen_data_access(repo_root, source_entries)),
    ]
    return [*guides, *source_entries]


# --- payload + zip -----------------------------------------------------------


def _entry_rows(repo_root: Path, entries: Sequence[Entry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in sorted(entries, key=lambda e: e.archive_path):
        parts = Path(entry.archive_path).parts
        if entry.archive_path.startswith("/") or ".." in parts:
            raise ValueError(f"unsafe archive path: {entry.archive_path}")
        if entry.archive_path in seen:
            raise ValueError(f"duplicate archive path: {entry.archive_path}")
        seen.add(entry.archive_path)
        data = entry.bytes(repo_root)
        rows.append(
            {
                "source_path": entry.source_text(),
                "archive_path": entry.archive_path,
                "group": entry.group,
                "sha256": _sha256(data),
                "size_bytes": len(data),
            }
        )
    return rows


def _assertions(rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
    paths = {r["archive_path"] for r in rows}
    groups = {r["group"] for r in rows}
    no_tests = not any("/tests/" in p or "/test_" in p or p.endswith("_test.py") for p in paths)
    no_raw = not any(Path(p).suffix.lower() in RAW_DATA_EXTS for p in paths)
    no_gate = not any(p.rsplit("/", 1)[-1] in GATE_SCRIPTS for p in paths)
    return {
        "readme_included": "00_README.md" in paths,
        "audit_prompt_included": "AUDIT_PROMPT.md" in paths,
        "architecture_guide_included": "01_ARCHITECTURE_GUIDE.md" in paths,
        "code_map_included": "02_CODE_MAP.md" in paths,
        "entry_points_included": "03_ENTRY_POINTS.md" in paths,
        "data_access_included": "04_DATA_ACCESS.md" in paths,
        "library_source_present": "library_source" in groups,
        "rust_solver_source_present": "rust_solver_source" in groups,
        "science_drivers_present": "science_driver" in groups,
        "data_pipeline_present": "data_pipeline" in groups,
        "execution_stacks_present": "execution_stack" in groups,
        "legacy_tsc_present": "legacy_tsc" in groups,
        "observational_inventory_included": f"{ARCHIVE_ROOT}/docs/generated/observational_data_inventory.md" in paths,
        "no_test_files": no_tests,
        "no_raw_datasets": no_raw,
        "no_gate_blocker_clis": no_gate,
    }


def build_payload(
    *,
    repo_root: Path = REPO_ROOT,
    output_zip: Path = DEFAULT_OUTPUT_ZIP,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_prompt: Path = DEFAULT_OUTPUT_PROMPT,
    generating_command: str,
    worktree_state: str | None = None,
) -> tuple[dict[str, Any], Sequence[Entry]]:
    root = Path(repo_root).resolve()
    entries = _all_entries(root)
    rows = _entry_rows(root, entries)
    assertions = _assertions(rows)
    failed = [name for name, ok in assertions.items() if not ok]
    state = worktree_state or _git_state(root)
    group_counts: dict[str, int] = {}
    for r in rows:
        group_counts[r["group"]] = group_counts.get(r["group"], 0) + 1
    config = {
        "schema_version": SCHEMA_VERSION,
        "archive_paths": [r["archive_path"] for r in rows],
        "assertions": sorted(assertions),
    }
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": output_zip.as_posix(),
        "manifest_path": output_manifest.as_posix(),
        "prompt_path": output_prompt.as_posix(),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "transfer_source": "code_and_pipeline_source_only_no_raw_data",
        "sky_support_status": "not_applicable_code_audit",
        "null_mock_status": "not_applicable_code_audit",
        "family_identification": False,
        "native_solver_result": False,
        "schema_version": SCHEMA_VERSION,
        "created_by": THIS_SCRIPT,
        "generating_command": generating_command,
        "git_commit_or_worktree_state": state,
        "code_version": state,
        "config_hash": _stable_hash(config),
        "input_hashes": [f"{r['source_path']}:{r['sha256']}" for r in rows],
        "archive_entries": rows,
        "archive_entry_count": len(rows),
        "group_counts": group_counts,
        "required_assertions": assertions,
        "passed_gates": sorted(n for n, ok in assertions.items() if ok),
        "failed_gates": failed,
        "scope_note": "Raw code-capability disclosure: broad source tree for execution-feasibility audit; not a results bundle.",
        "caveats": [
            "Broad raw-source disclosure for code/capability audit; not a results or claims bundle.",
            "Tests, raw datasets, and claim-gate/lint/validate enforcement CLIs are excluded as noise.",
            "Legacy tsc layer is included so its separate executability can be probed; it is not an active science owner.",
            "No raw observational data is shipped; the data-access guide and inventory list what the code can reach.",
            "Inclusion of code does not imply a validated science result; see the result/claim packages for claim tiers.",
        ],
    }
    return payload, tuple(entries)


def render_readme() -> str:
    return f"""# HTT/BASS Code-Capability External Audit Package

This package is a broad, raw-source disclosure for an **execution-feasibility /
capability audit**. It answers: *what can this codebase actually run, and what
data can it reach?* It is intentionally NOT compact.

## Read in this order

1. `01_ARCHITECTURE_GUIDE.md` — authored map of the BASS/HTT/MIO/OBSSTAT stack,
   the dual solver tracks, the execution stacks, and the legacy layer.
2. `02_CODE_MAP.md` — per-package file counts, LOC, and purpose (auto-generated).
3. `03_ENTRY_POINTS.md` — every detected runnable (Python CLI/`__main__`, shell,
   Rust `fn main`) with a one-line description (auto-generated).
4. `04_DATA_ACCESS.md` — the external-download manifest, a static scan of data
   paths/URLs in the shipped code, and the observational-data inventory pointer.
5. The raw source under `{ARCHIVE_ROOT}/` — read whatever the guides point you to.

## What is included (broad, on purpose)

- The full non-test library tree: `htt/bass`, `htt/htt`, `htt/mio`,
  `htt/obsstat`, `htt/workspace`, `htt/src` (COMMON), and the **legacy**
  `htt/tsc` Teff-chart layer.
- The Rust `bass_rs` solver crate (`src/`, `Cargo.toml`, `Cargo.lock`).
- The runnable science drivers (`scripts/`, minus gate/lint CLIs).
- The data-download pipeline (`dl_pipeline/`) and its `sources.json` manifest.
- The recombination/reionization execution stacks.
- Config files, package manifests, code READMEs, and the data/repo inventories.

## What is excluded (incidental noise)

- Tests and `conftest` files.
- Raw datasets and binary artifacts (`.npz/.fits/.csv/.png/.pdf/...`).
- Claim-gate / lint / validate / audit-package / status **enforcement** CLIs.
- Build trees (`target/`, `venv/`), figures, and the gitignored `project/`.

## Caveat

Inclusion of code does not imply a validated science result. Family-ID,
geometry detection, native low-ell solver validation, and posterior/odds claims
remain blocked; see the separate results/claim packages for the claim tiers.
"""


def render_prompt() -> str:
    return """# Code-Capability / Execution-Feasibility Audit Prompt

You are an external engineering+scientific auditor. Your job is to assess
**what this codebase can actually run and compute**, and whether its claimed
capabilities are supported by the source. Review the code as code; do not grade
the project's claim tiers here (a separate package covers results/claims).

## Inputs

This archive only. Start from the four guides at the archive root
(`01_ARCHITECTURE_GUIDE.md`, `02_CODE_MAP.md`, `03_ENTRY_POINTS.md`,
`04_DATA_ACCESS.md`), then read the raw source under `code_capability_audit/`.

## Questions to answer

1. **Runnability.** For each major entry point in `03_ENTRY_POINTS.md`, is the
   code path actually executable as described? Identify missing dependencies,
   dead imports, or stubs masquerading as implementations.
2. **Capability inventory.** Enumerate what the codebase can genuinely compute:
   the Rust MB-95 solver path, the PSTF/tetrad hierarchy, recombination/kinetic
   theory, the HTT inference layer, the MIO diagnostics, the OBSSTAT estimators,
   the execution stacks. Flag any capability that is asserted in docstrings but
   not implemented.
3. **Data reach.** Using `04_DATA_ACCESS.md`, confirm what real data the code
   can load and what must be downloaded first. Are the loaders consistent with
   the download manifest? Any path that cannot be satisfied?
4. **Legacy / deprecated executability.** The `htt/tsc` legacy layer is shipped.
   Determine whether it still runs independently, what it computes, and whether
   any of it is worth re-activating or is safe to retire.
5. **Architecture integrity.** Are the BASS/HTT/MIO/OBSSTAT ownership boundaries
   real in the code (imports, interfaces), or only documented?
6. **Risk.** Where would a new contributor be misled about what runs?

## Output

1. `Capability Map`: table `Subsystem | Runnable? | What it computes | Evidence (path) | Gaps`.
2. `Entry-Point Findings`: per-entry status (runs / needs-deps / broken / stub).
3. `Data-Reach Findings`: which inputs are satisfiable, which need downloads.
4. `Legacy Verdict`: tsc (and any other legacy) — runs / partial / dead; reactivate or retire.
5. `Architecture Findings`: where ownership boundaries hold or leak.
6. `Top Risks`: ranked list of places where capability is over- or under-stated.

Cite `path:line`. Prefer concise tables. Do not review code style or formatting.
"""


def render_architecture_guide() -> str:
    return """# Architecture Guide (authored)

This codebase computes CMB and large-scale-structure observables for FLRW and
Bianchi-anisotropic cosmologies, and runs an observer-side statistical
observatory on real data. It is organised as a four-owner stack plus a dual
solver track.

## Ownership stack

- **BASS** (`htt/bass`, Rust `src/`) — physics. Owns the solver(s): the
  PSTF/tetrad 1+3-covariant multipole hierarchy (the target formulation for
  Bianchi+tilt), recombination and kinetic theory, transfer, the atlas, the
  geometry/closure dispatch, and the line-of-sight + spectrum assembly.
- **HTT** (`htt/htt`) — inference / observation bridge. Owns model-dependent
  likelihoods, evidence, predictive checks (PPC/LOOCV), null competition,
  posterior pushforward, response-overlap rank audits, and the observational
  bounds layer. HTT owns all evidence terms.
- **MIO** (`htt/mio`) — reporting / diagnostics observatory. Owns
  *diagnostic-only* certificates (directional coherence, redshift-binned depth,
  FLRW tension, predictive residuals, evidence anatomy) and the formalism layer
  (dynamic budgets, bound pushforward). MIO reports are not posteriors, truth
  certificates, or model-ranking objects, and are read-only to HTT evidence.
- **OBSSTAT** (`htt/obsstat`) — observer-side estimators. Owns feature
  extraction only: low-ell scalars (S_1/2, parity, planarity), morphology axes
  (power-inertia tensor), null ensembles, and map/feature utilities.
- **COMMON** (`htt/src/common`) — shared contracts, artifact manifests, status
  snapshot, and the transfer registry that all owners depend on.

## Dual solver track

- **MB-95 production path** — the Rust `bass_rs` crate (`src/`). A
  CAMB-convention synchronous-gauge Boltzmann solver using Rodas5P / diffsol
  ODE integrators, exposed to Python via PyO3. This is the currently-anchored
  spectrum path (FLRW limit regression anchor D_2 = 1002.086744 uK^2).
- **PSTF primary path** — the Python `htt/bass` tetrad-native hierarchy. The
  target formulation for Bianchi+tilt; its FLRW limit is being driven to be
  bit-identical with the MB-95 anchor. Runtime diagnostics for this track are
  the `scripts/v5_*` drivers.

The honest scope: registry + shear-source are validated for all 11 Bianchi
types; full end-to-end low-ell line-of-sight coverage is closed for FLRW, I, V,
and IX, with the remaining families restricted to axis-aligned mode subsets.
Off-axis modes raise `OutOfScopeError`. Globally-tilted backgrounds use a
policy-fixed velocity closure by default.

## Real-data observatory

`scripts/make_lowell_morphology_real_map.py` and
`scripts/make_cf4_bulkflow_apex_depth.py` run the OBSSTAT estimators on the
Planck PR3 map and the CF4 reconstruction grid, calibrated against
isotropic-LCDM nulls / bootstrap. `scripts/reproduce_cf4pp_lnb.py` and the
`scripts/compare_flrw_lowell_pstf_to_camb.py` / `export_flrw_lowell_pstf_spectrum.py`
drivers exercise the transfer and spectrum paths. Symbolic theorem proofs run
through `scripts/prove_egs_lowell_theorems.py` (Wolfram).

## Data pipeline

`dl_pipeline/` is a self-contained downloader/extractor with a single
source-of-truth manifest (`dl_pipeline/config/sources.json`) covering Planck
PR3, ACT, SPT-3G, BICEP/Keck, DESI Y1, CF4, and CAMB references. The extracted
products land under `workdir/obs_bundle/*.npz`; the bundled
`observational_data_inventory.md` lists every file with hashes and presence
status. Raw datasets are NOT shipped in this package.

## Execution stacks

`recombination_execution_stack/` and `reionization_execution_stack/` are
anisotropic radiative-transfer coding bundles — separate execution surfaces for
the recombination and reionization physics.

## Legacy layer

`htt/tsc` is the legacy Teff-chart service layer. It remains import-compatible
for old chart/admissibility overlays and reproducibility checks, but is not an
active science owner, runtime gate, evidence/posterior owner, MIO certificate
owner, native solver, or family-identification path. It is shipped here so its
separate executability can be probed.
"""


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def _render_manifest(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _build_zip_bytes(repo_root: Path, payload: dict[str, Any], entries: Sequence[Entry]) -> bytes:
    from io import BytesIO

    by_path = {e.archive_path: e for e in entries}
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(_zip_info("MANIFEST.json"), _render_manifest(payload).encode("utf-8"))
        for row in sorted(payload["archive_entries"], key=lambda r: r["archive_path"]):
            archive.writestr(_zip_info(row["archive_path"]), by_path[row["archive_path"]].bytes(repo_root))
    return buffer.getvalue()


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _write_outputs(repo_root, payload, entries, output_zip, output_manifest, output_prompt) -> None:
    zip_path = _resolve(repo_root, output_zip)
    man_path = _resolve(repo_root, output_manifest)
    prompt_path = _resolve(repo_root, output_prompt)
    for p in (zip_path, man_path, prompt_path):
        p.parent.mkdir(parents=True, exist_ok=True)
    zip_path.write_bytes(_build_zip_bytes(repo_root, payload, entries))
    man_path.write_text(_render_manifest(payload), encoding="utf-8")
    prompt_path.write_text(render_prompt(), encoding="utf-8")


def _check_outputs(repo_root, payload, entries, output_zip, output_manifest, output_prompt) -> int:
    zip_path = _resolve(repo_root, output_zip)
    man_path = _resolve(repo_root, output_manifest)
    prompt_path = _resolve(repo_root, output_prompt)
    if not (zip_path.exists() and man_path.exists() and prompt_path.exists()):
        print("missing code-capability audit package output")
        return 1
    if man_path.read_text(encoding="utf-8") != _render_manifest(payload):
        print("stale code-capability audit manifest")
        return 1
    if prompt_path.read_text(encoding="utf-8") != render_prompt():
        print("stale code-capability audit prompt")
        return 1
    if zip_path.read_bytes() != _build_zip_bytes(repo_root, payload, entries):
        print("stale code-capability audit zip")
        return 1
    print(f"up-to-date {zip_path}")
    return 0


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = [a for a in (sys.argv[1:] if argv is None else list(argv)) if a not in ("--check", "--dry-run")]
    return " ".join(["python", THIS_SCRIPT, *args]).strip()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-zip", type=Path, default=DEFAULT_OUTPUT_ZIP)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    parser.add_argument("--output-prompt", type=Path, default=DEFAULT_OUTPUT_PROMPT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    worktree_state: str | None = None
    man_path = _resolve(repo_root, args.output_manifest)
    if args.check and man_path.exists():
        existing = json.loads(man_path.read_text(encoding="utf-8"))
        worktree_state = existing.get("git_commit_or_worktree_state") or existing.get("code_version")
    payload, entries = build_payload(
        repo_root=repo_root,
        output_zip=args.output_zip,
        output_manifest=args.output_manifest,
        output_prompt=args.output_prompt,
        generating_command=_command_from_args(argv),
        worktree_state=worktree_state,
    )
    if payload["failed_gates"]:
        print("code-capability package failed gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print(f"DRY-RUN archive_entry_count={payload['archive_entry_count']}")
        print("group_counts=" + json.dumps(payload["group_counts"], sort_keys=True))
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(repo_root, payload, entries, args.output_zip, args.output_manifest, args.output_prompt)
    _write_outputs(repo_root, payload, entries, args.output_zip, args.output_manifest, args.output_prompt)
    print(f"wrote {_resolve(repo_root, args.output_zip)} ({payload['archive_entry_count']} entries)")
    print(f"wrote {_resolve(repo_root, args.output_manifest)}")
    print(f"wrote {_resolve(repo_root, args.output_prompt)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
