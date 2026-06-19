#!/usr/bin/env python3
"""Build the PR-114 external audit disclosure package.

The package is a pre-solver audit bundle. It preserves claim tiers, transfer
provenance, manuscript blockers, and future-solver schema boundaries; it does
not certify publication readiness or native solver validation.
"""
import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from typing import Any, Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ZIP = Path("docs/generated/external_audit_package.zip")
DEFAULT_OUTPUT_MANIFEST = Path("docs/generated/external_audit_package_manifest.json")
SCHEMA_VERSION = "common.external_audit_package.v1"
ARTIFACT_ID = "external_audit_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
FIGURE_PAYLOAD_ROOTS = (
    Path("figures/current"),
    Path("figures/observed_current"),
    Path("figures/paper/ver2_generated"),
    Path("figures/conditioned_legacy"),
)
FIGURE_PAYLOAD_SUFFIXES = (".png", ".manifest.json")
FIGURE_MANIFEST_PROMOTION_TOKENS = (
    "production_candidate",
    "production_validated",
    "production-grade",
)


@dataclass(frozen=True)
class AuditPackageEntry:
    source_path: Path
    archive_path: str
    group: str
    description: str


def _entry(source: str, archive: str, group: str, description: str) -> AuditPackageEntry:
    return AuditPackageEntry(Path(source), archive, group, description)


DEFAULT_PACKAGE_ENTRIES: tuple[AuditPackageEntry, ...] = (
    # Prompts
    _entry("docs/audit_prompts/README.md", "prompts/README.md", "audit_prompts", "audit prompt index"),
    _entry(
        "docs/audit_prompts/claim_firewall_review.md",
        "prompts/claim_firewall_review.md",
        "audit_prompts",
        "claim firewall review prompt",
    ),
    _entry(
        "docs/audit_prompts/future_solver_interface_review.md",
        "prompts/future_solver_interface_review.md",
        "audit_prompts",
        "future solver interface review prompt",
    ),
    _entry(
        "docs/audit_prompts/local_global_review.md",
        "prompts/local_global_review.md",
        "audit_prompts",
        "local/global discrimination review prompt",
    ),
    _entry(
        "docs/audit_prompts/manuscript_figure_review.md",
        "prompts/manuscript_figure_review.md",
        "audit_prompts",
        "manuscript and figure provenance prompt",
    ),
    _entry(
        "docs/audit_prompts/transfer_provenance_review.md",
        "prompts/transfer_provenance_review.md",
        "audit_prompts",
        "transfer provenance review prompt",
    ),
    # Status, claims, and progress.
    _entry("docs/generated/claim_ledger.json", "status/claim_ledger.json", "pr_status", "generated claim ledger"),
    _entry("docs/generated/status_snapshot.json", "status/status_snapshot.json", "pr_status", "generated status snapshot"),
    _entry("docs/generated/status_matrix.md", "status/status_matrix.md", "pr_status", "generated status matrix"),
    _entry("docs/codex_handoff/pr_status.yaml", "status/pr_status.yaml", "pr_status", "DAG PR status"),
    _entry("docs/codex_handoff/pr_backlog.yaml", "status/pr_backlog.yaml", "pr_status", "DAG PR backlog"),
    _entry(
        "docs/generated/publication_claim_freeze.md",
        "status/publication_claim_freeze.md",
        "publication_claim_freeze",
        "publication claim freeze summary",
    ),
    _entry(
        "docs/generated/hostile_review_response_matrix.md",
        "status/hostile_review_response_matrix.md",
        "publication_claim_freeze",
        "hostile reviewer response matrix",
    ),
    _entry(
        "docs/generated/progress_checkpoints/progress_scoreboard.md",
        "status/progress_scoreboard.md",
        "pr_status",
        "generated progress scoreboard",
    ),
    _entry(
        "docs/generated/progress_checkpoints/checkpoint_060.md",
        "status/checkpoint_060.md",
        "pr_status",
        "five-PR checkpoint 060",
    ),
    # Result and provenance reports.
    _entry("docs/generated/result_pack_A.md", "reports/result_pack_A.md", "result_packs", "scalar-to-morphology report"),
    _entry("docs/generated/result_pack_B.md", "reports/result_pack_B.md", "result_packs", "local/global report"),
    _entry("docs/generated/result_pack_C.md", "reports/result_pack_C.md", "result_packs", "MIO certificate report"),
    _entry(
        "docs/generated/transfer_sensitivity_report.md",
        "reports/transfer_sensitivity_report.md",
        "transfer_provenance",
        "transfer provenance report",
    ),
    _entry(
        "docs/generated/manuscript_figure_inventory.md",
        "manuscript/manuscript_figure_inventory.md",
        "manuscript_audit",
        "manuscript figure inventory",
    ),
    _entry(
        "docs/generated/missing_figure_references.md",
        "manuscript/missing_figure_references.md",
        "manuscript_audit",
        "missing and quarantined figure references",
    ),
    _entry(
        "docs/generated/quarantined_figures.md",
        "manuscript/quarantined_figures.md",
        "manuscript_audit",
        "repository figure quarantine report",
    ),
    _entry(
        "docs/generated/pdf_claim_lint_report.md",
        "manuscript/pdf_claim_lint_report.md",
        "manuscript_audit",
        "compiled-PDF claim lint report",
    ),
    _entry(
        "docs/generated/current_manuscript_plot_list.md",
        "manuscript/current_manuscript_plot_list.md",
        "manuscript_audit",
        "current-code manuscript plot list",
    ),
    _entry(
        "docs/generated/expanded_manuscript_plot_list.md",
        "manuscript/expanded_manuscript_plot_list.md",
        "manuscript_audit",
        "expanded current plus conditioned-legacy manuscript plot list",
    ),
    _entry(
        "docs/generated/observed_current_plot_list.md",
        "manuscript/observed_current_plot_list.md",
        "manuscript_audit",
        "observed-data manuscript plot list",
    ),
    _entry(
        "docs/generated/manuscript_plot_list_index.md",
        "manuscript/manuscript_plot_list_index.md",
        "manuscript_audit",
        "combined manuscript plot-list index",
    ),
    _entry(
        "docs/generated/current_manuscript_figure_curation.json",
        "manuscript/current_manuscript_figure_curation.json",
        "manuscript_audit",
        "current-code manuscript figure curation data",
    ),
    _entry(
        "docs/generated/current_science_plot_payload.json",
        "manuscript/current_science_plot_payload.json",
        "manuscript_audit",
        "numeric payload for current conditioned physics diagnostic plots",
    ),
    _entry(
        "docs/generated/expanded_manuscript_figure_suite.json",
        "manuscript/expanded_manuscript_figure_suite.json",
        "manuscript_audit",
        "expanded manuscript figure-suite data",
    ),
    _entry(
        "docs/generated/observational_data_inventory.json",
        "reports/observational_data_inventory.json",
        "observed_data",
        "repo-local observational data inventory JSON",
    ),
    _entry(
        "docs/generated/observational_data_inventory.md",
        "reports/observational_data_inventory.md",
        "observed_data",
        "repo-local observational data inventory report",
    ),
    _entry(
        "docs/generated/observed_longrun_analysis.json",
        "reports/observed_longrun_analysis.json",
        "observed_data",
        "observed-data long-run diagnostic JSON",
    ),
    _entry(
        "docs/generated/observed_longrun_analysis.md",
        "reports/observed_longrun_analysis.md",
        "observed_data",
        "observed-data long-run diagnostic report",
    ),
    _entry(
        "docs/manuscript/generated/observed_figures_pipeline.tex",
        "manuscript/generated/observed_figures_pipeline.tex",
        "manuscript_audit",
        "observed-data pipeline LaTeX figure snippet",
    ),
    _entry(
        "docs/manuscript/generated/observed_figures_results.tex",
        "manuscript/generated/observed_figures_results.tex",
        "manuscript_audit",
        "observed-data results LaTeX figure snippet",
    ),
    _entry(
        "docs/generated/manuscript_pdf/htt_base_research_report.pdf",
        "manuscript/htt_base_research_report.pdf",
        "manuscript_pdf",
        "repo-local built research report PDF",
    ),
    _entry(
        "docs/generated/manuscript_pdf/htt_base_research_report.manifest.json",
        "manuscript/htt_base_research_report.manifest.json",
        "manuscript_pdf",
        "manifest and claim caveats for repo-local research report PDF",
    ),
    # Dependency PR deltas.
    _entry("docs/PR_DELTAS/pr-110.md", "pr_deltas/pr-110.md", "framework_reports", "Result Pack A PR delta"),
    _entry("docs/PR_DELTAS/pr-111.md", "pr_deltas/pr-111.md", "framework_reports", "Result Pack B PR delta"),
    _entry("docs/PR_DELTAS/pr-112.md", "pr_deltas/pr-112.md", "framework_reports", "Result Pack C PR delta"),
    _entry("docs/PR_DELTAS/pr-113.md", "pr_deltas/pr-113.md", "framework_reports", "manuscript audit PR delta"),
    _entry("docs/PR_DELTAS/pr-080.md", "pr_deltas/pr-080.md", "transfer_provenance", "transfer registry PR delta"),
    _entry("docs/PR_DELTAS/pr-082.md", "pr_deltas/pr-082.md", "transfer_provenance", "atlas transfer PR delta"),
    _entry("docs/PR_DELTAS/pr-083.md", "pr_deltas/pr-083.md", "transfer_provenance", "native schema PR delta"),
    _entry("docs/PR_DELTAS/pr-100.md", "pr_deltas/pr-100.md", "framework_reports", "directional MIO certificate PR delta"),
    _entry("docs/PR_DELTAS/pr-101.md", "pr_deltas/pr-101.md", "framework_reports", "redshift MIO certificate PR delta"),
    _entry("docs/PR_DELTAS/pr-102.md", "pr_deltas/pr-102.md", "framework_reports", "FLRW tension PR delta"),
    _entry("docs/PR_DELTAS/pr-103.md", "pr_deltas/pr-103.md", "framework_reports", "PR-103 trace-anatomy PR delta"),
    # Code snapshot files: scoped sources, not a whole-repo dump.
    _entry(
        "scripts/build_external_audit_package.py",
        "code_snapshot/scripts/build_external_audit_package.py",
        "code_snapshot",
        "audit package generator",
    ),
    _entry(
        "scripts/result_packs/generate_pack_A_scalar_to_morphology.py",
        "code_snapshot/scripts/result_packs/generate_pack_A_scalar_to_morphology.py",
        "code_snapshot",
        "Result Pack A generator",
    ),
    _entry(
        "scripts/result_packs/generate_pack_B_local_global.py",
        "code_snapshot/scripts/result_packs/generate_pack_B_local_global.py",
        "code_snapshot",
        "Result Pack B generator",
    ),
    _entry(
        "scripts/result_packs/generate_pack_C_mio_certificates.py",
        "code_snapshot/scripts/result_packs/generate_pack_C_mio_certificates.py",
        "code_snapshot",
        "Result Pack C generator",
    ),
    _entry(
        "scripts/generate_transfer_sensitivity_report.py",
        "code_snapshot/scripts/generate_transfer_sensitivity_report.py",
        "code_snapshot",
        "transfer sensitivity report generator",
    ),
    _entry(
        "scripts/audit_manuscript_figures.py",
        "code_snapshot/scripts/audit_manuscript_figures.py",
        "code_snapshot",
        "manuscript figure audit generator",
    ),
    _entry(
        "scripts/make_current_manuscript_figures.py",
        "code_snapshot/scripts/make_current_manuscript_figures.py",
        "code_snapshot",
        "current manifest-backed manuscript figure generator",
    ),
    _entry(
        "scripts/build_expanded_manuscript_figure_suite.py",
        "code_snapshot/scripts/build_expanded_manuscript_figure_suite.py",
        "code_snapshot",
        "expanded current and conditioned legacy figure-suite generator",
    ),
    _entry(
        "scripts/inventory_observational_data.py",
        "code_snapshot/scripts/inventory_observational_data.py",
        "code_snapshot",
        "observational data inventory generator",
    ),
    _entry(
        "scripts/make_observed_data_manuscript_figures.py",
        "code_snapshot/scripts/make_observed_data_manuscript_figures.py",
        "code_snapshot",
        "observed-data manuscript figure generator",
    ),
    _entry(
        "tests/contracts/test_observed_data_figures.py",
        "code_snapshot/tests/contracts/test_observed_data_figures.py",
        "code_snapshot",
        "observed-data figure contract tests",
    ),
    _entry("htt/src/common/artifact_manifest.py", "code_snapshot/htt/src/common/artifact_manifest.py", "code_snapshot", "manifest validation"),
    _entry("htt/src/common/transfer_registry.py", "code_snapshot/htt/src/common/transfer_registry.py", "code_snapshot", "transfer registry contract"),
    _entry("htt/src/common/status_snapshot.py", "code_snapshot/htt/src/common/status_snapshot.py", "code_snapshot", "status snapshot generator"),
    _entry("htt/bass/transfer/registry.py", "code_snapshot/htt/bass/transfer/registry.py", "code_snapshot", "external transfer registry"),
    _entry("htt/bass/transfer/aniclass_adapter.py", "code_snapshot/htt/bass/transfer/aniclass_adapter.py", "code_snapshot", "AniCLASS adapter"),
    _entry("htt/bass/transfer/native_schema.py", "code_snapshot/htt/bass/transfer/native_schema.py", "code_snapshot", "future native schema"),
    _entry("htt/bass/transfer/native_adapter.py", "code_snapshot/htt/bass/transfer/native_adapter.py", "code_snapshot", "future native adapter stub"),
    _entry("htt/bass/atlas/atlas_entry.py", "code_snapshot/htt/bass/atlas/atlas_entry.py", "code_snapshot", "AtlasEntryLite contract"),
    _entry("htt/mio/reports/departure_report.py", "code_snapshot/htt/mio/reports/departure_report.py", "code_snapshot", "MIO departure report"),
    _entry("htt/mio/formalism/budget_spec.py", "code_snapshot/htt/mio/formalism/budget_spec.py", "code_snapshot", "MIO denominator-policy budget contract"),
    _entry("htt/mio/coherence/directional.py", "code_snapshot/htt/mio/coherence/directional.py", "code_snapshot", "directional coherence certificate"),
    _entry("htt/mio/coherence/redshift_binned.py", "code_snapshot/htt/mio/coherence/redshift_binned.py", "code_snapshot", "redshift coherence certificate"),
    _entry("htt/mio/tension/flrw_tension.py", "code_snapshot/htt/mio/tension/flrw_tension.py", "code_snapshot", "FLRW tension gate"),
    _entry("htt/mio/decomposition/evidence_anatomy.py", "code_snapshot/htt/mio/decomposition/evidence_anatomy.py", "code_snapshot", "MIO trace anatomy narrative"),
    _entry("htt/htt/htt/departure/response_overlap.py", "code_snapshot/htt/htt/htt/departure/response_overlap.py", "code_snapshot", "HTT response overlap"),
    _entry("htt/htt/htt/departure/local_global_mixture.py", "code_snapshot/htt/htt/htt/departure/local_global_mixture.py", "code_snapshot", "HTT local/global mixture"),
    _entry("htt/htt/htt/departure/posterior_pushforward.py", "code_snapshot/htt/htt/htt/departure/posterior_pushforward.py", "code_snapshot", "HTT posterior pushforward"),
    _entry("htt/htt/htt/infer/loocv.py", "code_snapshot/htt/htt/htt/infer/loocv.py", "code_snapshot", "HTT LOOCV gate"),
    _entry("htt/htt/htt/infer/posterior_predictive.py", "code_snapshot/htt/htt/htt/infer/posterior_predictive.py", "code_snapshot", "HTT PPC gate"),
    _entry("htt/htt/htt/nulls/local_boost_depth_null.py", "code_snapshot/htt/htt/htt/nulls/local_boost_depth_null.py", "code_snapshot", "local boost null"),
    _entry("htt/htt/htt/nulls/selection_response_depth.py", "code_snapshot/htt/htt/htt/nulls/selection_response_depth.py", "code_snapshot", "survey/systematic null"),
    _entry("htt/obsstat/morphology.py", "code_snapshot/htt/obsstat/morphology.py", "code_snapshot", "OBSSTAT morphology"),
    _entry("htt/obsstat/scalar_lowell.py", "code_snapshot/htt/obsstat/scalar_lowell.py", "code_snapshot", "OBSSTAT scalar low-ell"),
    _entry("htt/obsstat/null_ensembles.py", "code_snapshot/htt/obsstat/null_ensembles.py", "code_snapshot", "OBSSTAT null ensembles"),
)


def _figure_payload_entries(repo_root: Path) -> tuple[AuditPackageEntry, ...]:
    entries: list[AuditPackageEntry] = []
    for root in FIGURE_PAYLOAD_ROOTS:
        absolute_root = repo_root / root
        if not absolute_root.exists():
            continue
        for path in sorted(absolute_root.iterdir()):
            if not path.is_file():
                continue
            name = path.name
            if not any(name.endswith(suffix) for suffix in FIGURE_PAYLOAD_SUFFIXES):
                continue
            relative = path.relative_to(repo_root)
            group = "figure_manifest" if name.endswith(".manifest.json") else "figure_payload"
            description = (
                "sidecar figure manifest"
                if group == "figure_manifest"
                else "auditable figure image payload"
            )
            entries.append(
                AuditPackageEntry(
                    source_path=relative,
                    archive_path=relative.as_posix(),
                    group=group,
                    description=description,
                )
            )
    return tuple(entries)


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_hash(payload: Any) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return _sha256_bytes(data)


def _git_commit(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _git_state(repo_root: Path) -> str:
    commit = _git_commit(repo_root)
    try:
        dirty = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return "unknown"
    return f"{commit}+dirty" if dirty else commit


def _tracked_paths(repo_root: Path) -> set[str] | None:
    inside_worktree = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if inside_worktree.returncode != 0:
        return None
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("git ls-files failed while building external audit package")
    return set(completed.stdout.splitlines())


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = list(sys.argv[1:] if argv is None else argv)
    args = [arg for arg in args if arg != "--check"]
    return " ".join(["python", "scripts/build_external_audit_package.py", *args]).strip()


def _normalise_output_path(path: Path) -> str:
    return path.as_posix()


def _entry_rows(
    repo_root: Path,
    entries: Iterable[AuditPackageEntry],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_archive_paths: set[str] = set()
    tracked_paths = _tracked_paths(repo_root)
    missing: list[str] = []
    untracked: list[str] = []
    for entry in sorted(entries, key=lambda item: item.archive_path):
        if entry.archive_path.startswith("/") or ".." in Path(entry.archive_path).parts:
            raise ValueError(f"unsafe archive path: {entry.archive_path}")
        if entry.archive_path in seen_archive_paths:
            raise ValueError(f"duplicate archive path: {entry.archive_path}")
        seen_archive_paths.add(entry.archive_path)
        source_text = entry.source_path.as_posix()
        if tracked_paths is not None and source_text not in tracked_paths:
            untracked.append(source_text)
            continue
        source = repo_root / entry.source_path
        if not source.is_file():
            missing.append(entry.source_path.as_posix())
            continue
        rows.append(
            {
                "source_path": entry.source_path.as_posix(),
                "archive_path": entry.archive_path,
                "group": entry.group,
                "description": entry.description,
                "sha256": _sha256_file(source),
                "size_bytes": source.stat().st_size,
            }
        )
    if missing:
        raise FileNotFoundError(
            "external audit package required inputs are missing: "
            + ", ".join(sorted(missing))
        )
    if untracked:
        raise RuntimeError(
            "external audit package required inputs are not tracked by git: "
            + ", ".join(sorted(untracked))
        )
    return rows


def _figure_pairs_complete(archive_paths: set[str], root: str) -> bool:
    png_stems = {
        path[: -len(".png")]
        for path in archive_paths
        if path.startswith(root) and path.endswith(".png")
    }
    manifest_stems = {
        path[: -len(".manifest.json")]
        for path in archive_paths
        if path.startswith(root) and path.endswith(".manifest.json")
    }
    return bool(png_stems) and png_stems == manifest_stems


def _required_assertions(rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
    archive_paths = {str(row["archive_path"]) for row in rows}
    groups = {str(row["group"]) for row in rows}
    figure_roots = (
        "figures/current/",
        "figures/observed_current/",
        "figures/paper/ver2_generated/",
        "figures/conditioned_legacy/",
    )
    return {
        "claim_ledger_included": "status/claim_ledger.json" in archive_paths,
        "transfer_provenance_included": "reports/transfer_sensitivity_report.md" in archive_paths,
        "figure_inventory_included": "manuscript/manuscript_figure_inventory.md" in archive_paths
        and "manuscript/missing_figure_references.md" in archive_paths,
        "figure_payloads_included": all(
            _figure_pairs_complete(archive_paths, root)
            for root in figure_roots
        ),
        "manuscript_pdf_included": (
            "manuscript/htt_base_research_report.pdf" in archive_paths
            and "manuscript/htt_base_research_report.manifest.json" in archive_paths
        ),
        "publication_claim_freeze_included": (
            "status/publication_claim_freeze.md" in archive_paths
            and "status/hostile_review_response_matrix.md" in archive_paths
        ),
        "plot_lists_included": (
            "manuscript/current_manuscript_plot_list.md" in archive_paths
            and "manuscript/expanded_manuscript_plot_list.md" in archive_paths
            and "manuscript/observed_current_plot_list.md" in archive_paths
            and "manuscript/manuscript_plot_list_index.md" in archive_paths
            and "manuscript/current_manuscript_figure_curation.json" in archive_paths
            and "manuscript/expanded_manuscript_figure_suite.json" in archive_paths
        ),
        "observed_data_deck_included": (
            "reports/observational_data_inventory.json" in archive_paths
            and "reports/observational_data_inventory.md" in archive_paths
            and "reports/observed_longrun_analysis.json" in archive_paths
            and "reports/observed_longrun_analysis.md" in archive_paths
            and "manuscript/generated/observed_figures_pipeline.tex" in archive_paths
            and "manuscript/generated/observed_figures_results.tex" in archive_paths
            and "code_snapshot/scripts/inventory_observational_data.py" in archive_paths
            and "code_snapshot/scripts/make_observed_data_manuscript_figures.py" in archive_paths
            and _figure_pairs_complete(archive_paths, "figures/observed_current/")
        ),
        "audit_prompts_included": "audit_prompts" in groups and "prompts/README.md" in archive_paths,
        "code_snapshot_included": "code_snapshot" in groups,
        "future_solver_interface_included": (
            "code_snapshot/htt/bass/transfer/native_schema.py" in archive_paths
            and "code_snapshot/htt/bass/transfer/native_adapter.py" in archive_paths
            and "prompts/future_solver_interface_review.md" in archive_paths
        ),
    }


def _figure_manifest_claim_lanes_safe(repo_root: Path, rows: Sequence[dict[str, Any]]) -> bool:
    for row in rows:
        if row["group"] != "figure_manifest":
            continue
        source_path = repo_root / str(row["source_path"])
        text = source_path.read_text(encoding="utf-8")
        if any(token in text for token in FIGURE_MANIFEST_PROMOTION_TOKENS):
            return False
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return False
        if payload.get("production_status") in {
            "production_candidate",
            "production_validated",
        }:
            return False
    return True


def _read_text_if_exists(repo_root: Path, relative: str) -> str:
    path = repo_root / relative
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _manuscript_blocker_summary(repo_root: Path) -> dict[str, int | str]:
    text = _read_text_if_exists(repo_root, "docs/generated/missing_figure_references.md")
    quarantine_text = _read_text_if_exists(repo_root, "docs/generated/quarantined_figures.md")
    summary: dict[str, int | str] = {
        "missing_refs": "unknown",
        "quarantined_refs": "unknown",
        "claim_risk_findings": "unknown",
        "manual_status_number_findings": "unknown",
        "repository_quarantined_figures": "unknown",
    }
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Missing refs:"):
            summary["missing_refs"] = int(stripped.rsplit(":", 1)[1].strip())
        elif stripped.startswith("- Quarantined refs:"):
            summary["quarantined_refs"] = int(stripped.rsplit(":", 1)[1].strip())
        elif stripped.startswith("- Claim-risk findings:"):
            summary["claim_risk_findings"] = int(stripped.rsplit(":", 1)[1].strip())
        elif stripped.startswith("- Manual/status-number findings:"):
            summary["manual_status_number_findings"] = int(stripped.rsplit(":", 1)[1].strip())
    for line in quarantine_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- Quarantined figures:"):
            summary["repository_quarantined_figures"] = int(stripped.rsplit(":", 1)[1].strip())
    return summary


def build_audit_package_payload(
    *,
    repo_root: Path | str = REPO_ROOT,
    output_zip: Path = DEFAULT_OUTPUT_ZIP,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    generating_command: str,
    package_entries: Sequence[AuditPackageEntry] = DEFAULT_PACKAGE_ENTRIES,
    git_commit: str | None = None,
    worktree_state: str | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    all_entries = tuple(package_entries) + _figure_payload_entries(root)
    rows = _entry_rows(root, all_entries)
    input_hashes = [f"{row['source_path']}:{row['sha256']}" for row in rows]
    input_artifacts = [
        {
            "path": row["source_path"],
            "sha256": row["sha256"],
            "included": True,
            "archive_path": row["archive_path"],
            "group": row["group"],
        }
        for row in rows
    ]
    assertions = _required_assertions(rows)
    assertions["figure_manifest_claim_lanes_safe"] = _figure_manifest_claim_lanes_safe(
        root,
        rows,
    )
    failed_gates = [
        name
        for name, passed in assertions.items()
        if not passed
    ]
    config = {
        "schema_version": SCHEMA_VERSION,
        "archive_paths": [row["archive_path"] for row in rows],
        "required_assertions": sorted(assertions),
    }
    config_hash = _stable_hash(config)
    commit = git_commit or _git_commit(root)
    state = worktree_state or _git_state(root)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": _normalise_output_path(output_zip),
        "manifest_path": _normalise_output_path(output_manifest),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts/build_external_audit_package.py",
        "git_commit": commit,
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "input_artifacts": input_artifacts,
        "code_version": state,
        "schema_version": SCHEMA_VERSION,
        "transfer_source": "mixed_none_observed_reference_external_transfer_conditioned_legacy",
        "sky_support_status": "pending_or_unknown_for_existing_directional_artifacts",
        "null_mock_status": "mixed_not_statistical_jackknife_bootstrap_diagnostic_and_legacy_conditioned",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": state,
        "archive_entries": rows,
        "archive_entry_count": len(rows),
        "required_assertions": assertions,
        "required_gates": sorted(assertions),
        "passed_gates": sorted(name for name, passed in assertions.items() if passed),
        "failed_gates": failed_gates,
        "report_generation_gates": {
            "archive_build": "pass" if not failed_gates else "fail",
            "manifest_json": "pass",
            "required_disclosure_inputs": "pass" if not failed_gates else "fail",
            "figure_payload_inclusion": "pass" if assertions.get("figure_payloads_included") else "fail",
            "figure_manifest_claim_lanes": "pass"
            if assertions.get("figure_manifest_claim_lanes_safe")
            else "fail",
            "known_quarantine_inventory_preserved": "warn",
        },
        "science_promotion_gates": {
            "native_low_ell_solver_validation": "fail",
            "native_morphology_atlas": "fail",
            "matched_null_mask_covariance_family_equivalence_stack": "fail",
            "transfer_sensitivity_numerical_propagation": "pending",
        },
        "publication_gates": {
            "publication_readiness": "fail",
            "claim_freeze_present": "pass" if assertions.get("publication_claim_freeze_included") else "fail",
            "pdf_claim_lint": "delegated_to_publication_claim_freeze",
        },
        "manuscript_blockers": _manuscript_blocker_summary(root),
        "caveats": [
            "External audit package only; not a publication-readiness or solver-validation artifact.",
            "Current transfer-dependent outputs remain transfer-conditional.",
            "MIO certificates are diagnostic reports and remain separate from HTT inference artifacts.",
            "Missing or quarantined manuscript figure references remain blockers.",
            "Manual/status-number manuscript findings and repository quarantine counts are preserved for external review.",
            "Future native solver interface material is schema-only unless native validated artifacts are separately manifested.",
        ],
    }
    return payload


def render_readme(payload: dict[str, Any]) -> str:
    blockers = payload["manuscript_blockers"]
    lines = [
        "# HTT External Audit Package",
        "",
        "This archive is a diagnostic external-audit disclosure package for the pre-solver HTT/MIO/BASS framework.",
        "It is not a publication freeze, not native solver validation, and not a geometry or family claim.",
        "",
        "## Required Assertions",
        "",
    ]
    lines.extend(
        f"- {key}: {value}"
        for key, value in sorted(payload["required_assertions"].items())
    )
    lines.extend(
        [
            "",
            "## Manuscript Blockers Preserved",
            "",
            f"- missing_refs: {blockers['missing_refs']}",
            f"- quarantined_refs: {blockers['quarantined_refs']}",
            f"- claim_risk_findings: {blockers['claim_risk_findings']}",
            f"- manual_status_number_findings: {blockers['manual_status_number_findings']}",
            f"- repository_quarantined_figures: {blockers['repository_quarantined_figures']}",
            "",
            "## Reviewer Entry Points",
            "",
            "- `prompts/`: adversarial review prompts.",
            "- `status/`: DAG, status, and claim ledger artifacts.",
            "- `reports/`: Result Packs A/B/C and transfer provenance report.",
            "- `manuscript/`: manuscript figure inventory, plot lists, PDF, PDF manifest, and blockers.",
            "- `code_snapshot/`: scoped source files for reproducing the audit surfaces.",
            "- Archived `pr_deltas/` and `status/` entries may preserve historical readiness vocabulary as provenance; current reports use diagnostic-only public readiness and legacy-not-current caveats.",
            "",
            "## Caveats",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["caveats"])
    lines.append("")
    return "\n".join(lines)


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def render_manifest_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def build_zip_bytes(repo_root: Path, payload: dict[str, Any]) -> bytes:
    from io import BytesIO

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        manifest_json = render_manifest_json(payload)
        archive.writestr(_zip_info("MANIFEST.json"), manifest_json.encode("utf-8"))
        archive.writestr(_zip_info("README.md"), render_readme(payload).encode("utf-8"))
        for row in sorted(payload["archive_entries"], key=lambda item: item["archive_path"]):
            data = (repo_root / row["source_path"]).read_bytes()
            archive.writestr(_zip_info(row["archive_path"]), data)
    return buffer.getvalue()


def _write_outputs(repo_root: Path, payload: dict[str, Any], output_zip: Path, output_manifest: Path) -> None:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = (
        output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    )
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    zip_bytes = build_zip_bytes(repo_root, payload)
    output_zip_path.write_bytes(zip_bytes)
    output_manifest_path.write_text(render_manifest_json(payload), encoding="utf-8")


def _check_outputs(repo_root: Path, payload: dict[str, Any], output_zip: Path, output_manifest: Path) -> int:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = (
        output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    )
    if not output_zip_path.exists() or not output_manifest_path.exists():
        print("missing audit package output")
        return 1
    expected_manifest = render_manifest_json(payload)
    actual_manifest = output_manifest_path.read_text(encoding="utf-8")
    if actual_manifest != expected_manifest:
        print("stale audit package manifest")
        return 1
    expected_zip = build_zip_bytes(repo_root, payload)
    if output_zip_path.read_bytes() != expected_zip:
        print("stale audit package zip")
        return 1
    print(f"up-to-date {output_zip_path}")
    return 0


def _existing_manifest_self_reference_fields(
    repo_root: Path,
    output_manifest: Path,
) -> tuple[str | None, str | None]:
    manifest_path = (
        output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    )
    if not manifest_path.exists():
        return None, None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, None
    commit = payload.get("git_commit")
    state = payload.get("git_commit_or_worktree_state")
    return (str(commit) if commit else None, str(state) if state else None)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-zip", type=Path, default=DEFAULT_OUTPUT_ZIP)
    parser.add_argument("--output-manifest", type=Path, default=DEFAULT_OUTPUT_MANIFEST)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--check", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    git_commit, worktree_state = (
        _existing_manifest_self_reference_fields(repo_root, args.output_manifest)
        if args.check
        else (None, None)
    )
    payload = build_audit_package_payload(
        repo_root=repo_root,
        output_zip=args.output_zip,
        output_manifest=args.output_manifest,
        generating_command=_command_from_args(argv),
        git_commit=git_commit,
        worktree_state=worktree_state,
    )
    if payload["failed_gates"]:
        print("audit package failed required gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print("DRY-RUN: not writing external audit package")
        print(f"archive_entry_count={payload['archive_entry_count']}")
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(repo_root, payload, args.output_zip, args.output_manifest)
    _write_outputs(repo_root, payload, args.output_zip, args.output_manifest)
    output_zip = args.output_zip if args.output_zip.is_absolute() else repo_root / args.output_zip
    output_manifest = (
        args.output_manifest if args.output_manifest.is_absolute() else repo_root / args.output_manifest
    )
    print(f"wrote {output_zip}")
    print(f"wrote {output_manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
