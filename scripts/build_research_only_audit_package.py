#!/usr/bin/env python3
"""Build a research-only external audit package for the manuscript.

This package excludes the compiled PDF and excludes broad code snapshots.  It is
for physics, mathematics, statistics, claim-formulation, and result-surface
review only.  Code samples are included only where they are needed to interpret
manuscript figures beyond the prose and sidecar manifests.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
for root in (REPO_ROOT, COMMON_ROOT, REPO_ROOT / "scripts"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from audit_manuscript_figures import build_manuscript_figure_audit  # noqa: E402
from common.artifact_manifest import validate_manifest_payload  # noqa: E402


DEFAULT_OUTPUT_ZIP = Path("docs/generated/research_only_external_audit_package.zip")
DEFAULT_OUTPUT_MANIFEST = Path("docs/generated/research_only_external_audit_package_manifest.json")
DEFAULT_OUTPUT_PROMPT = Path("docs/generated/research_only_external_audit_prompt.md")
SCHEMA_VERSION = "common.research_only_external_audit_package.v1"
ARTIFACT_ID = "research_only_external_audit_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ARCHIVE_ROOT = "research_audit_source"

METADATA_FILES = (
    "docs/generated/manuscript_plot_list_index.md",
    "docs/generated/current_manuscript_plot_list.md",
    "docs/generated/observed_current_plot_list.md",
    "docs/generated/expanded_manuscript_plot_list.md",
    "docs/generated/manuscript_figure_inventory.md",
    "docs/generated/missing_figure_references.md",
    "docs/generated/quarantined_figures.md",
    "docs/generated/pdf_claim_lint_report.md",
    "docs/generated/publication_claim_freeze.md",
    "docs/generated/claim_ledger.json",
    "docs/generated/result_pack_A.md",
    "docs/generated/result_pack_B.md",
    "docs/generated/result_pack_C.md",
    "docs/generated/transfer_sensitivity_report.md",
    "docs/generated/current_manuscript_figure_curation.json",
    "docs/generated/current_science_plot_payload.json",
    "docs/generated/expanded_manuscript_figure_suite.json",
    "docs/generated/observational_data_inventory.json",
    "docs/generated/observational_data_inventory.md",
    "docs/generated/observed_longrun_analysis.json",
    "docs/generated/observed_longrun_analysis.md",
)

REVISION_PROGRAM_FILES = (
    "docs/audits/revision_program_2026-06-18/package_inventory.json",
    "docs/audits/revision_program_2026-06-18/package_inventory.md",
    "docs/generated/revision_plan_crosswalk.md",
    "docs/generated/revision_novelty_ledger.md",
    "docs/generated/revision_claim_lanes.md",
    "docs/generated/revision_literature_crag.md",
    "docs/generated/revision_defense_dossier.md",
    "docs/codex_handoff/pr_dag_revision.yaml",
)

CODE_SAMPLE_FILES = (
    "scripts/make_current_manuscript_figures.py",
    "scripts/make_observed_data_manuscript_figures.py",
    "scripts/build_expanded_manuscript_figure_suite.py",
    "scripts/curate_current_manuscript_figures.py",
)


@dataclass(frozen=True)
class PackageEntry:
    archive_path: str
    group: str
    description: str
    source_path: Path | None = None
    content: bytes | None = None

    def bytes(self, repo_root: Path) -> bytes:
        if self.content is not None:
            return self.content
        if self.source_path is None:
            raise ValueError(f"entry {self.archive_path} has no source or content")
        return (repo_root / self.source_path).read_bytes()

    def source_text(self) -> str:
        return self.source_path.as_posix() if self.source_path is not None else f"virtual:{self.archive_path}"


def _repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return _sha256_bytes(encoded)


def _git_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def _git_state(repo_root: Path) -> str:
    commit = _git_commit(repo_root)
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "unknown"
    return f"{commit}+dirty" if completed.stdout.strip() else commit


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = [arg for arg in (sys.argv[1:] if argv is None else list(argv)) if arg != "--check"]
    return " ".join(["python", "scripts/build_research_only_audit_package.py", *args]).strip()


def _entry(source: str, archive: str, group: str, description: str) -> PackageEntry:
    return PackageEntry(
        source_path=Path(source),
        archive_path=f"{ARCHIVE_ROOT}/{archive}",
        group=group,
        description=description,
    )


def _virtual_entry(archive: str, group: str, description: str, text: str) -> PackageEntry:
    return PackageEntry(
        archive_path=archive,
        group=group,
        description=description,
        content=text.encode("utf-8"),
    )


def _latex_source_entries(repo_root: Path) -> list[PackageEntry]:
    entries: list[PackageEntry] = []
    manuscript_root = repo_root / "docs/manuscript"
    for path in sorted(manuscript_root.rglob("*")):
        if not path.is_file():
            continue
        rel = _repo_relative(path, repo_root)
        parts = Path(rel).parts
        if "build_audit_fix" in parts:
            continue
        if path.suffix not in {".tex", ".bib"}:
            continue
        entries.append(
            _entry(
                rel,
                rel,
                "latex_source",
                "LaTeX source required to inspect the research report without the heavy PDF",
            )
        )
    return entries


def _figure_entries(repo_root: Path) -> list[PackageEntry]:
    audit = build_manuscript_figure_audit(
        repo_root,
        manuscript_root=repo_root / "docs/manuscript",
    )
    entries: list[PackageEntry] = []
    seen: set[str] = set()
    missing: list[str] = []
    for record in audit.figure_records:
        if record.status != "resolved" or record.resolved_path is None or record.manifest_path is None:
            missing.append(f"{record.tex_path}:{record.line}:{record.include_path}:{record.status}")
            continue
        for rel in (record.resolved_path, record.manifest_path):
            if rel in seen:
                continue
            seen.add(rel)
            entries.append(
                _entry(
                    rel,
                    rel,
                    "manuscript_figure_payload" if rel.endswith(".png") else "manuscript_figure_manifest",
                    "manuscript figure payload or sidecar manifest referenced by LaTeX",
                )
            )
    if missing:
        raise RuntimeError("research audit package requires all manuscript figures to be resolved with manifests: " + "; ".join(missing[:8]))
    return entries


def _metadata_entries(repo_root: Path) -> list[PackageEntry]:
    entries: list[PackageEntry] = []
    for rel in METADATA_FILES:
        path = repo_root / rel
        if not path.is_file():
            raise FileNotFoundError(f"required research metadata missing: {rel}")
        entries.append(
            _entry(
                rel,
                rel,
                "research_metadata",
                "generated research/result/claim metadata needed for physics-statistics audit",
            )
        )
    return entries


def _revision_program_entries(repo_root: Path) -> list[PackageEntry]:
    entries: list[PackageEntry] = []
    for rel in REVISION_PROGRAM_FILES:
        path = repo_root / rel
        if not path.is_file():
            raise FileNotFoundError(f"required revision program input missing: {rel}")
        entries.append(
            _entry(
                rel,
                rel,
                "revision_program",
                "revision program inventory, crosswalk, claim lanes, CRAG, defense, or DAG input required by this research-only audit slice",
            )
        )
    return entries


def _code_sample_entries(repo_root: Path) -> list[PackageEntry]:
    entries = [
        _virtual_entry(
            f"{ARCHIVE_ROOT}/code_samples/README.md",
            "minimal_code_sample",
            "instructions for ignoring code style and using code only as figure-method context",
            CODE_SAMPLE_README,
        )
    ]
    for rel in CODE_SAMPLE_FILES:
        path = repo_root / rel
        if not path.is_file():
            raise FileNotFoundError(f"required minimal code sample missing: {rel}")
        entries.append(
            _entry(
                rel,
                f"code_samples/{Path(rel).name}",
                "minimal_code_sample",
                "minimal plot-generation code sample; not included for software audit",
            )
        )
    return entries


def _entry_rows(repo_root: Path, entries: Sequence[PackageEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in sorted(entries, key=lambda item: item.archive_path):
        path_parts = Path(entry.archive_path).parts
        if entry.archive_path.startswith("/") or ".." in path_parts:
            raise ValueError(f"unsafe archive path: {entry.archive_path}")
        if entry.archive_path in seen:
            raise ValueError(f"duplicate archive path: {entry.archive_path}")
        if entry.archive_path.lower().endswith(".pdf"):
            raise ValueError(f"PDF files are intentionally excluded: {entry.archive_path}")
        seen.add(entry.archive_path)
        data = entry.bytes(repo_root)
        rows.append(
            {
                "source_path": entry.source_text(),
                "archive_path": entry.archive_path,
                "group": entry.group,
                "description": entry.description,
                "sha256": _sha256_bytes(data),
                "size_bytes": len(data),
            }
        )
    return rows


def _required_assertions(rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
    archive_paths = {row["archive_path"] for row in rows}
    groups = {row["group"] for row in rows}
    figure_png = {
        path[:-4]
        for path in archive_paths
        if path.startswith(f"{ARCHIVE_ROOT}/figures/") and path.endswith(".png")
    }
    figure_manifest = {
        path[: -len(".manifest.json")]
        for path in archive_paths
        if path.startswith(f"{ARCHIVE_ROOT}/figures/") and path.endswith(".manifest.json")
    }
    return {
        "compiled_pdf_excluded": not any(path.lower().endswith(".pdf") for path in archive_paths),
        "latex_source_included": f"{ARCHIVE_ROOT}/docs/manuscript/main.tex" in archive_paths
        and f"{ARCHIVE_ROOT}/docs/manuscript/references.bib" in archive_paths,
        "generated_tex_snippets_included": any(path.startswith(f"{ARCHIVE_ROOT}/docs/manuscript/generated/") and path.endswith(".tex") for path in archive_paths),
        "all_manuscript_figures_have_payload_and_manifest": bool(figure_png) and figure_png == figure_manifest,
        "plot_lists_included": f"{ARCHIVE_ROOT}/docs/generated/manuscript_plot_list_index.md" in archive_paths
        and f"{ARCHIVE_ROOT}/docs/generated/observed_current_plot_list.md" in archive_paths
        and f"{ARCHIVE_ROOT}/docs/generated/current_manuscript_plot_list.md" in archive_paths
        and f"{ARCHIVE_ROOT}/docs/generated/expanded_manuscript_plot_list.md" in archive_paths,
        "result_packs_included": all(
            f"{ARCHIVE_ROOT}/docs/generated/result_pack_{letter}.md" in archive_paths
            for letter in ("A", "B", "C")
        ),
        "claim_and_transfer_metadata_included": f"{ARCHIVE_ROOT}/docs/generated/claim_ledger.json" in archive_paths
        and f"{ARCHIVE_ROOT}/docs/generated/transfer_sensitivity_report.md" in archive_paths,
        "minimal_code_samples_only": "minimal_code_sample" in groups
        and not any(path.startswith(f"{ARCHIVE_ROOT}/htt/") for path in archive_paths)
        and not any(path.startswith(f"{ARCHIVE_ROOT}/code_snapshot/") for path in archive_paths),
        "research_prompt_included": "AUDIT_PROMPT_RESEARCH_ONLY.md" in archive_paths,
        "revision_program_files_included": all(
            f"{ARCHIVE_ROOT}/{rel}" in archive_paths for rel in REVISION_PROGRAM_FILES
        ),
    }


def build_payload(
    *,
    repo_root: Path | str = REPO_ROOT,
    output_zip: Path = DEFAULT_OUTPUT_ZIP,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_prompt: Path = DEFAULT_OUTPUT_PROMPT,
    generating_command: str,
    worktree_state: str | None = None,
    git_commit: str | None = None,
) -> tuple[dict[str, Any], Sequence[PackageEntry]]:
    root = Path(repo_root).resolve()
    prompt_text = render_prompt()
    entries: list[PackageEntry] = [
        _virtual_entry("README.md", "package_readme", "research-only audit package guide", render_readme()),
        _virtual_entry("AUDIT_PROMPT_RESEARCH_ONLY.md", "research_prompt", "adversarial physics/math/statistics audit prompt", prompt_text),
        *_latex_source_entries(root),
        *_figure_entries(root),
        *_metadata_entries(root),
        *_revision_program_entries(root),
        *_code_sample_entries(root),
    ]
    rows = _entry_rows(root, entries)
    assertions = _required_assertions(rows)
    failed_gates = [name for name, ok in assertions.items() if not ok]
    archive_paths = [row["archive_path"] for row in rows]
    config = {
        "schema_version": SCHEMA_VERSION,
        "archive_paths": archive_paths,
        "assertions": sorted(assertions),
        "pdf_excluded": True,
        "code_policy": "minimal_plot_context_only",
    }
    commit = git_commit or _git_commit(root)
    state = worktree_state or _git_state(root)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": output_zip.as_posix(),
        "manifest_path": output_manifest.as_posix(),
        "prompt_path": output_prompt.as_posix(),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts/build_research_only_audit_package.py",
        "git_commit": commit,
        "config_hash": _stable_hash(config),
        "input_hashes": [f"{row['source_path']}:{row['sha256']}" for row in rows],
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
        "passed_gates": sorted(name for name, ok in assertions.items() if ok),
        "failed_gates": failed_gates,
        "report_generation_gates": {
            "latex_source_packaging": "pass" if assertions.get("latex_source_included") else "fail",
            "figure_payload_manifest_pairing": "pass" if assertions.get("all_manuscript_figures_have_payload_and_manifest") else "fail",
            "compiled_pdf_excluded": "pass" if assertions.get("compiled_pdf_excluded") else "fail",
            "minimal_code_policy": "pass" if assertions.get("minimal_code_samples_only") else "fail",
        },
        "science_promotion_gates": {
            "native_low_ell_solver_validation": "fail_not_available",
            "native_morphology_atlas": "fail_not_available",
            "matched_mask_covariance_family_equivalence_stack": "not_uniformly_bound_across_legacy_material",
            "research_only_external_review": "pending",
            "revision_program_external_audit_context": "pass"
            if assertions.get("revision_program_files_included")
            else "fail_missing_required_revision_files",
        },
        "publication_gates": {
            "external_research_audit_ready": "pass" if not failed_gates else "fail",
            "publication_ready": "fail_diagnostic_only",
        },
        "caveats": [
            "This package is for external research-formulation and result audit only; it is not a code review bundle.",
            "The compiled PDF is intentionally excluded to reduce package size; LaTeX source and figure payloads are included.",
            "Code samples are included only to clarify plot construction where prose and manifests may be insufficient.",
            "Current transfer-dependent and conditioned legacy material remains transfer-conditional.",
            "The native low-ell morphology atlas is absent; Bianchi family-ID and geometry-detection claims remain blocked.",
        ],
    }
    issues = validate_manifest_payload(
        payload,
        manifest_path=output_manifest,
        expected_artifact_path=output_zip.as_posix(),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid research-only audit manifest: {rendered}")
    return payload, tuple(entries)


def render_readme() -> str:
    return """# Research-Only External Audit Package

Purpose: external adversarial review of the research formalization and results in the HTT/Bianchi manuscript.

Scope:
- Review physics, mathematics, statistics, inference design, claim tiers, and figure/result interpretation.
- Do not review software engineering, packaging, test style, code quality, or repo architecture.
- The compiled PDF is excluded. Use `research_audit_source/docs/manuscript/main.tex`.
- All manuscript `\\includegraphics` payloads and sidecar manifests are included under `research_audit_source/figures/`.
- Code samples under `research_audit_source/code_samples/` are included only to clarify plot construction.

Recommended reading order:
1. `AUDIT_PROMPT_RESEARCH_ONLY.md`
2. `research_audit_source/docs/manuscript/main.tex`
3. `research_audit_source/docs/generated/manuscript_plot_list_index.md`
4. `research_audit_source/docs/generated/result_pack_A.md`, `result_pack_B.md`, `result_pack_C.md`
5. Figure sidecar manifests for any figure criticized.

Known boundaries:
- No current native low-ell Bianchi solver output is present.
- Current transfer-dependent rows are transfer-conditional.
- MIO certificates are diagnostic-only and are not HTT evidence terms.
- Scalar x/Q/Pi/F/G, direction coherence, or low-ell features do not identify a Bianchi family.
- Historical status ledgers may preserve archived readiness vocabulary as provenance; current result packs use diagnostic-only public readiness and legacy-not-current caveats.
"""


CODE_SAMPLE_README = """# Minimal Code Samples

These files are included only to clarify how manuscript plots were assembled.
Do not perform a software/code-quality review.

Use them only when the LaTeX caption, plot-list row, figure sidecar manifest,
or generated result pack is insufficient to answer a physics/statistics question
about a figure.  Prefer manifests and generated numeric payloads first.
"""


def render_prompt() -> str:
    return """# Adversarial Research Audit Prompt: HTT/Bianchi Manuscript

You are an external adversarial reviewer. Audit only the research formalization and results: physics, mathematics, statistics, inference design, claim tiers, figure interpretation, and manuscript logic. Do not review programming style, code architecture, packaging, tests as software, or implementation aesthetics.

## Inputs

Use this archive only. The compiled PDF is intentionally absent.

Read in this order:
1. `research_audit_source/docs/manuscript/main.tex`
2. chapter files included by `main.tex`
3. `research_audit_source/docs/generated/manuscript_plot_list_index.md`
4. `research_audit_source/docs/generated/result_pack_A.md`
5. `research_audit_source/docs/generated/result_pack_B.md`
6. `research_audit_source/docs/generated/result_pack_C.md`
7. `research_audit_source/docs/generated/transfer_sensitivity_report.md`
8. figure manifests for figures you cite
9. code samples only if manifests/prose are insufficient to understand a figure

## Hard Boundaries

- No native low-ell Bianchi Boltzmann solver output is available in this manuscript.
- External/AniCLASS/legacy transfer outputs are transfer-conditional, not native.
- MIO diagnostics/certificates are not posterior odds, truth certificates, or HTT evidence terms.
- HTT owns model-dependent likelihoods, evidence, PPC, LOOCV, null competition, and posterior pushforward.
- OBSSTAT owns observable feature extraction only.
- Scalar `x`, `Q`, `Pi`, `F`, `G_F`, direction coherence, low-ell residuals, or morphology axes do not identify a Bianchi family.
- Bianchi family-ID and geometry-detection claims are blocked unless a native low-ell morphology atlas, matched nulls, masks, covariance, and family-equivalence gates are present.

## Token Discipline

Return findings only. Do not summarize chapters. Do not quote long passages. Cite `path:line` or figure manifest path. If a section is acceptable, write one short sentence. Prefer tables with concise issue text.

## Required Output

Use exactly these sections:

1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Minimal Defensible Claim`: one paragraph, conservative.
3. `Fatal Blockers`: only blockers that invalidate the current main claim.
4. `Major Findings`: table with columns `Severity | Location | Problem | Why It Matters | Required Fix`.
5. `Physics/Math Audit`: table with `Item | Status | Issue | Required Fix`.
6. `Statistics/Inference Audit`: table with `Item | Status | Issue | Required Fix`.
7. `Figure/Result Audit`: list only figures/tables whose interpretation is wrong, under-supported, or overclaimed.
8. `Claim-Tier Corrections`: exact wording to downgrade or remove.
9. `Additional Analyses Required`: analyses needed before stronger claims are allowed.
10. `Claims That Are Safe`: bullet list of claims allowed under current evidence.

## Adversarial Checks

### A. Physics and mathematical formalization
- Are frame conventions explicit and consistent: normal frame, matter frame, CMB frame, local boost frame, geometry frame?
- Are units, signs, and dimensions correct for shear, vorticity, tilt rapidity, curvature, `x_C`, `Q`, `Pi`, `F`, and `G_F`?
- Do FLRW, no-tilt, local-boost-only, global-tilt-only, zero-denominator, and rank-deficient limits behave correctly?
- Is `x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso` treated as a signed comparator coordinate rather than an invariant anisotropy magnitude?
- Is MES use derived under stated assumptions, or merely asserted?
- Are deterministic template effects separated from anisotropic covariance effects?

### B. Transfer and solver provenance
- Wherever a value depends on external/AniCLASS/legacy transfer, is the transfer dependence explicit?
- Does any caption/table imply native BASS/native solver validation?
- Are family labels used only as provenance/equivalence-class labels, not as identified geometry?
- Are future-native adapter/schema discussions clearly non-result surfaces?

### C. Statistical inference and evidence
- Are likelihood factors, priors, channel independence/correlation assumptions, and Occam penalties justified?
- Are Bayes factors robust to channel ablation, prior changes, covariance assumptions, and look-elsewhere effects?
- Are PPC, LOOCV, null competition, and matched-mask/covariance gates present where evidence claims require them?
- Are local boost, global tilt, and survey/systematic alternatives separated?
- Are DESI, CF4, Planck, high-l, and lensing figures descriptive unless calibrated nulls/covariance are bound?
- Are bootstrap/jackknife intervals presented only as diagnostics, not p-values or posteriors?

### D. Observational-data plot interpretation
- Planck low-l residuals: do not accept sigma-bar residuals as full-covariance, cosmic-variance, mask-coupled p-values.
- Planck spectra/lensing: check theory/reference transfer labeling.
- DESI footprint/weights: check sky support and selection-systematics caveats.
- CF4 velocity/density/depth: check volume-coordinate caveats and avoid angular sky-fraction overclaim.
- Long-run jackknife/bootstrap: verify no evidence, p-value, or posterior language is inferred.

### E. Legacy and conditioned figures
- Treat conditioned legacy appendix figures as hypothesis-conditioned diagnostics only.
- Do not allow legacy evidence bars, posterior triangles, pairwise matrices, direction plots, or sensitivity plots to become current production evidence unless current null/PPC/LOOCV/mask/covariance gates are present.
- Check whether legacy material conflicts with current claim boundaries in main chapters.

### F. Manuscript structure and rhetoric
- Identify places where strong rhetoric outruns evidence.
- Flag any manual/status-number claims that should be generated-source claims.
- Flag any result that is visually persuasive but not mathematically/statistically supported.
- Distinguish: proved, derived, implemented, generated, smoke-tested, validated, transfer-conditional, diagnostic-only, proposed, speculative.

## Rejection Triggers

Reject or mark not ready if any of these are used as current results:
- an identified Bianchi family.
- a detected Bianchi geometry.
- native validation claimed for external-transfer output.
- MIO diagnostics promoted into posterior, evidence, or truth-certificate status.
- Scalar diagnostics alone used as geometry/family evidence.
- Evidence claim lacking required null/covariance/prior/PPC/LOOCV support.
"""


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    return info


def _render_manifest(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _build_zip_bytes(repo_root: Path, payload: dict[str, Any], entries: Sequence[PackageEntry]) -> bytes:
    from io import BytesIO

    entry_by_archive = {entry.archive_path: entry for entry in entries}
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(_zip_info("MANIFEST.json"), _render_manifest(payload).encode("utf-8"))
        for row in sorted(payload["archive_entries"], key=lambda item: item["archive_path"]):
            entry = entry_by_archive[row["archive_path"]]
            archive.writestr(_zip_info(row["archive_path"]), entry.bytes(repo_root))
    return buffer.getvalue()


def _write_outputs(repo_root: Path, payload: dict[str, Any], entries: Sequence[PackageEntry], output_zip: Path, output_manifest: Path, output_prompt: Path) -> None:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    output_prompt_path = output_prompt if output_prompt.is_absolute() else repo_root / output_prompt
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    output_prompt_path.parent.mkdir(parents=True, exist_ok=True)
    output_zip_path.write_bytes(_build_zip_bytes(repo_root, payload, entries))
    output_manifest_path.write_text(_render_manifest(payload), encoding="utf-8")
    output_prompt_path.write_text(render_prompt(), encoding="utf-8")


def _check_outputs(repo_root: Path, payload: dict[str, Any], entries: Sequence[PackageEntry], output_zip: Path, output_manifest: Path, output_prompt: Path) -> int:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    output_prompt_path = output_prompt if output_prompt.is_absolute() else repo_root / output_prompt
    if not output_zip_path.exists() or not output_manifest_path.exists() or not output_prompt_path.exists():
        print("missing research-only audit package output")
        return 1
    if output_manifest_path.read_text(encoding="utf-8") != _render_manifest(payload):
        print("stale research-only audit package manifest")
        return 1
    if output_prompt_path.read_text(encoding="utf-8") != render_prompt():
        print("stale research-only audit prompt")
        return 1
    expected_zip = _build_zip_bytes(repo_root, payload, entries)
    if output_zip_path.read_bytes() != expected_zip:
        print("stale research-only audit package zip")
        return 1
    print(f"up-to-date {output_zip_path}")
    return 0


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
    check_manifest_path = args.output_manifest if args.output_manifest.is_absolute() else repo_root / args.output_manifest
    check_metadata: dict[str, Any] = {}
    if args.check and check_manifest_path.exists():
        existing_manifest = json.loads(check_manifest_path.read_text(encoding="utf-8"))
        check_metadata = {
            "git_commit": existing_manifest.get("git_commit"),
            "worktree_state": existing_manifest.get("git_commit_or_worktree_state")
            or existing_manifest.get("code_version"),
        }
    payload, entries = build_payload(
        repo_root=repo_root,
        output_zip=args.output_zip,
        output_manifest=args.output_manifest,
        output_prompt=args.output_prompt,
        generating_command=_command_from_args(argv),
        worktree_state=check_metadata.get("worktree_state"),
        git_commit=check_metadata.get("git_commit"),
    )
    if payload["failed_gates"]:
        print("research-only package failed required gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print("DRY-RUN: not writing research-only audit package")
        print(f"archive_entry_count={payload['archive_entry_count']}")
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(repo_root, payload, entries, args.output_zip, args.output_manifest, args.output_prompt)
    _write_outputs(repo_root, payload, entries, args.output_zip, args.output_manifest, args.output_prompt)
    print(f"wrote {repo_root / args.output_zip if not args.output_zip.is_absolute() else args.output_zip}")
    print(f"wrote {repo_root / args.output_manifest if not args.output_manifest.is_absolute() else args.output_manifest}")
    print(f"wrote {repo_root / args.output_prompt if not args.output_prompt.is_absolute() else args.output_prompt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
