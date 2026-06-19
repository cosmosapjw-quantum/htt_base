#!/usr/bin/env python3
"""Build an external audit bundle focused on x_C/Q/Pi/F/G_F formalism.

This package is narrower than the research-only manuscript bundle.  It is for
physics/statistics reviewers who need to audit the departure formalism,
denominator policies, exceedance/occupancy/depth-gap semantics, and the figures
that expose those quantities.  It intentionally excludes the compiled PDF and
keeps code samples to the files required to understand the formalism.
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
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402


DEFAULT_OUTPUT_ZIP = Path("docs/generated/statistical_formalism_audit_package.zip")
DEFAULT_OUTPUT_MANIFEST = Path("docs/generated/statistical_formalism_audit_package_manifest.json")
DEFAULT_OUTPUT_PROMPT = Path("docs/generated/statistical_formalism_audit_prompt.md")
DEFAULT_OUTPUT_READINESS = Path("docs/generated/statistical_formalism_reaudit_readiness.md")
SCHEMA_VERSION = "common.statistical_formalism_audit_package.v1"
ARTIFACT_ID = "statistical_formalism_audit_package"
ARCHIVE_ROOT = "statistical_formalism_audit"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)

LATEX_SOURCE_FILES = (
    "docs/manuscript/main.tex",
    "docs/manuscript/references.bib",
    "docs/manuscript/ch01_introduction.tex",
    "docs/manuscript/ch02_dipole_anomaly.tex",
    "docs/manuscript/ch03_framework.tex",
    "docs/manuscript/ch04_bianchi_bounds.tex",
    "docs/manuscript/ch05_teff_corrections.tex",
    "docs/manuscript/ch06_pipeline.tex",
    "docs/manuscript/ch07_results.tex",
    "docs/manuscript/ch08_robustness.tex",
    "docs/manuscript/ch09_discussion.tex",
    "docs/manuscript/ch10_future.tex",
    "docs/manuscript/ch11_error_hierarchy.tex",
    "docs/manuscript/appendices.tex",
    "docs/manuscript/generated/current_figures_pipeline.tex",
    "docs/manuscript/generated/current_figures_results.tex",
    "docs/manuscript/generated/current_figures_ver2_exports.tex",
    "docs/manuscript/generated/ver2_result_pack_summary.tex",
    "docs/manuscript/generated/ver2_artifact_export_policy.tex",
    "docs/manuscript/generated/ver2_figure_manifest_status.tex",
    "docs/manuscript/generated/formalism_methods_claim_ladder.tex",
)

FORMALISM_METADATA_FILES = (
    "docs/generated/current_manuscript_plot_list.md",
    "docs/generated/expanded_manuscript_plot_list.md",
    "docs/generated/current_science_plot_payload.json",
    "docs/generated/gf_matched_null_forecast_report.json",
    "docs/generated/gf_matched_null_forecast_report.md",
    "docs/generated/result_pack_A.md",
    "docs/generated/result_pack_B.md",
    "docs/generated/result_pack_C.md",
    "docs/generated/transfer_sensitivity_report.md",
    "docs/generated/publication_claim_freeze.md",
    "docs/generated/pdf_claim_lint_report.md",
    "docs/generated/revision_claim_lanes.md",
    "docs/generated/formalism_audit_originality_response_matrix.md",
    "docs/generated/hostile_review_response_matrix.md",
    "docs/generated/semantic_firewall_fuzz_report.json",
    "docs/generated/semantic_firewall_fuzz_report.md",
    "docs/ver2_upgrade/generated/claim_ledger.json",
    "docs/ver2_upgrade/generated/status_snapshot.json",
    "docs/ver2_upgrade/generated/result_pack_C_departure_cards.json",
    "docs/ver2_upgrade/generated/result_pack_C_departure_cards.md",
    "docs/ver2_upgrade/generated/result_pack_D_mio_certificates.json",
    "docs/ver2_upgrade/generated/result_pack_D_mio_certificates.md",
    "docs/ver2_upgrade/generated/artifacts/common_ver2_export_departure_report.json",
    "docs/ver2_upgrade/generated/artifacts/mio_predictive_residuals_certificate.json",
    "docs/ver2_upgrade/generated/artifacts/htt_ver2_export_discrimination_matrix.json",
)

FORMALISM_CODE_FILES = (
    "htt/src/common/departure_contracts.py",
    "htt/src/common/semantic_guards/no_overclaim.py",
    "htt/src/common/transfer_registry.py",
    "htt/workspace/contracts/htt_posterior.py",
    "htt/bass/atlas/atlas_entry.py",
    "htt/bass/transfer/registry.py",
    "htt/mio/formalism/__init__.py",
    "htt/mio/formalism/budget_spec.py",
    "htt/mio/formalism/component_breakdown.py",
    "htt/mio/formalism/departure_bundle.py",
    "htt/mio/formalism/exceedance.py",
    "htt/mio/formalism/filling_fraction.py",
    "htt/mio/formalism/isotropy_gap.py",
    "htt/mio/formalism/normalized_score.py",
    "htt/mio/reports/departure_report.py",
    "htt/htt/htt/departure/posterior_pushforward.py",
    "htt/htt/htt/departure/response_overlap.py",
    "htt/htt/htt/infer/matched_complexity.py",
    "htt/htt/htt/infer/null_competition.py",
    "htt/htt/htt/nulls/local_boost_depth_null.py",
    "htt/htt/htt/nulls/selection_response_depth.py",
    "scripts/generate_semantic_firewall_fuzz_report.py",
    "scripts/verify_formalism_figure_labels.py",
)

FORMALISM_TEST_FILES = (
    "tests/mio/test_budget_spec.py",
    "tests/mio/test_departure_bundle.py",
    "tests/mio/test_departure_report.py",
    "tests/mio/test_exceedance.py",
    "tests/mio/test_filling_fraction.py",
    "tests/mio/test_isotropy_gap.py",
    "tests/mio/test_normalized_score.py",
    "tests/contracts/test_formalism_figure_labels.py",
    "tests/contracts/test_semantic_firewall_fuzz.py",
    "tests/htt/test_matched_nulls.py",
    "tests/htt/test_posterior_pushforward.py",
)

FORMALISM_FIGURE_BASES = (
    "figures/current/fig_current_qfpi_gf_semantic_split",
    "figures/current/fig_current_transfer_sensitivity_tornado",
    "figures/current/fig_current_mio_depth_residual_vectors",
    "figures/current/fig_current_mio_certificate_status",
    "figures/current/fig_current_local_global_rank_fpr",
    "figures/paper/ver2_generated/fig_ver2c_departure_card_summary",
    "figures/paper/ver2_generated/fig_ver2d_mio_predictive_residuals",
    "figures/conditioned_legacy/root__fig_departure_summary",
    "figures/conditioned_legacy/root__fig_filling_fraction_posterior",
    "figures/conditioned_legacy/root__fig_filling_z_evolution",
    "figures/conditioned_legacy/root__fig_q_decomposition",
    "figures/conditioned_legacy/root__fig_isotropy_pvalue_per_combination",
    "figures/conditioned_legacy/parallel-track__fig_05_filling_fraction_scenarios",
)

REQUIRED_CURRENT_ASSERTIONS = (
    ("full_external_package_check", "venv/bin/python scripts/build_external_audit_package.py --check", "pass"),
    ("research_only_package_check", "venv/bin/python scripts/build_research_only_audit_package.py --check", "pass"),
    ("ver2_export_check", "venv/bin/python scripts/ver2_artifact_export.py --check", "pass"),
    ("publication_claim_freeze_check", "venv/bin/python scripts/check_publication_claim_freeze.py --check", "pass"),
    ("manuscript_figure_audit", "venv/bin/python scripts/audit_manuscript_figures.py --dry-run", "0 missing, 0 quarantined, 0 claim-risk"),
    ("focused_package_tests", "venv/bin/python -m pytest tests/contracts/test_audit_package_generator.py tests/contracts/test_research_only_audit_package.py scripts/test_ver2_artifact_export.py -q", "pass"),
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
        return self.source_path.as_posix() if self.source_path else f"virtual:{self.archive_path}"


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
    return " ".join(["python", "scripts/build_statistical_formalism_audit_package.py", *args]).strip()


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


def _file_entries(
    repo_root: Path,
    paths: Sequence[str],
    *,
    group: str,
    description: str,
) -> list[PackageEntry]:
    entries: list[PackageEntry] = []
    for rel in paths:
        if not (repo_root / rel).is_file():
            raise FileNotFoundError(f"required statistical-formalism audit input missing: {rel}")
        entries.append(_entry(rel, rel, group, description))
    return entries


def _figure_entries(repo_root: Path) -> list[PackageEntry]:
    entries: list[PackageEntry] = []
    for base in FORMALISM_FIGURE_BASES:
        png = Path(base + ".png")
        manifest = Path(base + ".manifest.json")
        if not (repo_root / png).is_file():
            raise FileNotFoundError(f"required statistical-formalism figure missing: {png}")
        if not (repo_root / manifest).is_file():
            raise FileNotFoundError(f"required statistical-formalism figure manifest missing: {manifest}")
        entries.append(_entry(png.as_posix(), png.as_posix(), "formalism_figure", "x_C/Q/Pi/F/G_F or related diagnostic figure payload"))
        entries.append(_entry(manifest.as_posix(), manifest.as_posix(), "formalism_figure_manifest", "sidecar manifest for included formalism figure"))
        caption = Path(base + ".caption.txt")
        if (repo_root / caption).is_file():
            entries.append(_entry(caption.as_posix(), caption.as_posix(), "formalism_figure_caption", "caption sidecar for VER2 formalism figure"))
    return entries


def _entry_rows(repo_root: Path, entries: Sequence[PackageEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in sorted(entries, key=lambda item: item.archive_path):
        parts = Path(entry.archive_path).parts
        if entry.archive_path.startswith("/") or ".." in parts:
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


def _figure_manifest_lanes_safe(repo_root: Path, rows: Sequence[dict[str, Any]]) -> bool:
    for row in rows:
        if row["group"] != "formalism_figure_manifest":
            continue
        source = row["source_path"]
        if not isinstance(source, str) or source.startswith("virtual:"):
            return False
        payload = json.loads((repo_root / source).read_text(encoding="utf-8"))
        claim_tier = payload.get("claim_tier")
        if claim_tier == "exploratory":
            if "conditioned_legacy" not in source:
                return False
            caveats = " ".join(str(item) for item in payload.get("caveats", ())).lower()
            if "legacy" not in caveats or "condition" not in caveats:
                return False
        elif claim_tier != "diagnostic_only":
            return False
        if payload.get("production_status") != "diagnostic_only":
            return False
        text = json.dumps(payload, sort_keys=True)
        if "production_candidate" in text or "production_validated" in text:
            return False
    return True


def _required_assertions(repo_root: Path, rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
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
        "latex_source_included": f"{ARCHIVE_ROOT}/docs/manuscript/main.tex" in archive_paths,
        "statistical_prompt_included": "AUDIT_PROMPT_STATISTICAL_FORMALISM.md" in archive_paths,
        "readiness_checklist_included": "READINESS_CHECKLIST.md" in archive_paths,
        "figure_label_linter_report_included": "FIGURE_LABEL_LINTER_REPORT.md" in archive_paths,
        "formalism_code_included": all(f"{ARCHIVE_ROOT}/{rel}" in archive_paths for rel in FORMALISM_CODE_FILES),
        "formalism_tests_included": all(f"{ARCHIVE_ROOT}/{rel}" in archive_paths for rel in FORMALISM_TEST_FILES),
        "formalism_metadata_included": all(f"{ARCHIVE_ROOT}/{rel}" in archive_paths for rel in FORMALISM_METADATA_FILES),
        "formalism_figures_have_payload_and_manifest": bool(figure_png) and figure_png == figure_manifest,
        "figure_manifest_lanes_safe": _figure_manifest_lanes_safe(repo_root, rows),
        "minimal_formalism_scope_only": {"formalism_code", "formalism_test"}.issubset(groups)
        and not any(path.startswith(f"{ARCHIVE_ROOT}/docs/generated/manuscript_pdf/") for path in archive_paths),
    }


def render_readiness_checklist() -> str:
    lines = [
        "# Statistical Formalism Re-Audit Readiness Checklist",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_none_external_and_conditioned_legacy",
        "sky_support_status: not_directional_for_formalism_package",
        "null_mock_status: mixed_formalism_tests_and_diagnostic_null_context",
        "",
        "## Commit Policy Check",
        "",
        "- No explicit user or repo instruction forbids commits in the current `htt_base` contract.",
        "- `AGENTS.md` requires commit after tests and self-review for DAG PR work.",
        "- This checklist is not a request to make scientific claims stronger.",
        "",
        "## Prior Audit Findings And Fix Status",
        "",
        "| Finding | Status | Evidence | Residual risk |",
        "| --- | --- | --- | --- |",
        "| Full external audit package missed PDF/figure payload context | addressed | `scripts/build_external_audit_package.py --check` passes; package contains PDF and figure payloads | package remains diagnostic-only |",
        "| Research-only package was stale | addressed | `scripts/build_research_only_audit_package.py --check` passes | intentionally excludes PDF |",
        "| VER2 sidecars carried production promotion labels | addressed | included VER2 manuscript figure sidecars are diagnostic-only | legacy result-pack text may mention readiness labels as historical context |",
        "| Manifest self-reference caused post-commit stale loops | addressed | VER2 and package check-mode preserve/normalise self-referential git fields | generated manifests still record worktree state as provenance |",
        "| LaTeX byproducts polluted worktree/package risk | addressed | byproducts ignored and package tests exclude logs/aux files | local scratch files may exist after future latexmk runs |",
        "| Native solver/family-ID overclaim risk | guarded | claim-lint, figure audit, package manifests keep native/family gates failed | stronger claims still require native morphology atlas and matched null/mask/covariance gates |",
        "| Manuscript result framing did not foreground method-level contribution | addressed | `docs/manuscript/generated/formalism_methods_claim_ladder.tex` and chapter sources are included for audit | still not an observed-data discovery claim |",
        "| Formalism-audit response matrix absent from narrow re-audit bundle | addressed | `docs/generated/formalism_audit_originality_response_matrix.md` is packaged | matrix is a response target, not proof of correctness |",
        "| Figure-label linter output absent from narrow re-audit bundle | addressed | `FIGURE_LABEL_LINTER_REPORT.md` is generated and required to pass | linter checks labels, not physical validity |",
        "",
        "## Validation Commands To Re-Run",
        "",
    ]
    lines.extend(f"- `{command}` -> {status}" for _name, command, status in REQUIRED_CURRENT_ASSERTIONS)
    lines.extend(
        [
            "",
            "## x_C/Q/Pi/F/G_F Audit Focus",
            "",
            "- `x_C`: signed comparator coordinate, not invariant anisotropy magnitude.",
            "- `Q`: policy-normalized score with explicit numerator and denominator policy.",
            "- `Pi`: exceedance curve only, not truth probability.",
            "- `F`: certified filling fraction only under sign-clean samples and admissible ceiling.",
            "- `G_F`: depth-gap diagnostic requiring bin metadata and null/calibration status.",
            "- MIO formalism remains diagnostic; HTT evidence/posterior surfaces are separate.",
            "- Scalar formalism values cannot imply geometry detection or Bianchi family-ID.",
            "",
        ]
    )
    return "\n".join(lines)


def render_figure_label_linter_report(repo_root: Path) -> tuple[str, bool]:
    payload = repo_root / "docs/generated/current_science_plot_payload.json"
    script = repo_root / "scripts/verify_formalism_figure_labels.py"
    completed = subprocess.run(
        [sys.executable, script.as_posix(), payload.as_posix()],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    status = "pass" if completed.returncode == 0 else "fail"
    lines = [
        "# Formalism Figure Label Linter Report",
        "",
        "owner: COMMON",
        "implementation_scope: formalism_figure_label_lint",
        "claim_tier: diagnostic_only",
        "transfer_source: mixed_none_external_and_conditioned_legacy",
        "sky_support_status: not_directional_for_label_lint",
        "null_mock_status: not_statistical",
        "input_hashes:",
        f"- docs/generated/current_science_plot_payload.json:{_sha256_file(payload)}",
        f"- scripts/verify_formalism_figure_labels.py:{_sha256_file(script)}",
        "caveats:",
        "- This report checks current generated formalism figure labels only.",
        "- Passing this linter does not validate native transfer, observed-data evidence, or family-ID.",
        "generating_command: venv/bin/python scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json",
        "",
        "## Summary",
        "",
        f"- Exit code: `{completed.returncode}`",
        f"- Status: `{status}`",
        "",
        "## Stdout",
        "",
        "```text",
        completed.stdout.strip() or "<empty>",
        "```",
        "",
        "## Stderr",
        "",
        "```text",
        completed.stderr.strip() or "<empty>",
        "```",
        "",
    ]
    return "\n".join(lines), completed.returncode == 0


def render_prompt() -> str:
    return """# Adversarial Audit Prompt: x_C/Q/Pi/F/G_F Statistical Formalism

You are an external hostile reviewer. Audit only the statistical and physical formalization of `x_C`, `Q`, `Pi`, `F`, and `G_F`, plus the manuscript/result figures that use them. Do not review software style, packaging aesthetics, CI design, or general code quality.

## Inputs

Read in this order:
1. `READINESS_CHECKLIST.md`
2. `statistical_formalism_audit/docs/manuscript/main.tex`
3. manuscript chapters `ch01_introduction.tex`, `ch03_framework.tex`, `ch07_results.tex`, and `ch09_discussion.tex`
4. generated LaTeX snippets under `statistical_formalism_audit/docs/manuscript/generated/`, especially `formalism_methods_claim_ladder.tex`
5. `statistical_formalism_audit/docs/generated/formalism_audit_originality_response_matrix.md`
6. `FIGURE_LABEL_LINTER_REPORT.md`
7. `statistical_formalism_audit/docs/generated/current_science_plot_payload.json`
8. `statistical_formalism_audit/docs/generated/result_pack_A.md`
9. `statistical_formalism_audit/docs/generated/result_pack_B.md`
10. `statistical_formalism_audit/docs/generated/result_pack_C.md`
11. VER2 departure/MIO generated reports under `statistical_formalism_audit/docs/ver2_upgrade/generated/`
12. figure manifests under `statistical_formalism_audit/figures/`
13. formalism code/tests only when prose or manifests are insufficient.

## Hard Boundaries

- No native low-ell Bianchi solver result is present.
- External/legacy transfer-dependent results are transfer-conditional.
- MIO diagnostics are not posterior odds, evidence, or truth certificates.
- HTT owns model-dependent likelihood, evidence, PPC, LOOCV, and posterior pushforward.
- `x_C`, `Q`, `Pi`, `F`, `G_F`, direction coherence, residual vectors, or low-ell summaries cannot identify Bianchi family or geometry.

## Required Verdict

Return exactly these sections:

1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Minimal Defensible Claim`: one conservative paragraph.
3. `Fatal Blockers`: only blockers that invalidate the formalism or current manuscript use.
4. `Formalism Findings`: table `Severity | Location | Problem | Required Fix`.
5. `Equation/Definition Audit`: table `Quantity | Status | Issue | Required Fix`.
6. `Statistical Semantics Audit`: table `Item | Status | Issue | Required Fix`.
7. `Figure Interpretation Audit`: only figures whose interpretation overreaches.
8. `Claim-Tier Corrections`: exact wording to replace.
9. `Additional Analyses Required`: analyses needed before stronger claims.
10. `Safe Claims`: bullet list.

## Attack Checklist

### Novelty and substance
- Decide whether the manuscript states a genuine methods contribution or merely renames existing diagnostics.
- Check whether the semantic-firewall machinery has operational consequences: forbidden label tests, figure-label linter gates, manifest lanes, and MIO/HTT ownership separation.
- Reject originality claims that are not backed by explicit package evidence, equations, tests, or generated manifests.

### x_C
- Verify sign convention in `x_C = Sigma^2 - W^2 + Omega_tilt + Omega_k_aniso`.
- Check whether `x_C` is ever described as invariant magnitude or geometry evidence.
- Check FLRW, no-tilt, local-boost-only, global-tilt-only, and negative-coordinate limits.
- Require signed sector components and absolute-magnitude summaries wherever cancellation can hide large terms.

### Cancellation and magnitude reporting
- Check all figures and prose that aggregate `x_C`, `Q`, `F`, or `G_F` for cancellation artifacts.
- Require explicit signed sector components, total magnitude, cancellation ratio, or a stated reason why the quantity is not cancellation-sensitive.
- Reject claims that a small signed aggregate is physically small without a companion magnitude diagnostic.

### Q
- Verify numerator and denominator policy are explicit.
- Check denominator positivity, finite status, and policy compatibility.
- Reject uses where `Q` becomes occupancy, filling fraction, posterior probability, or family evidence.

### Pi
- Verify `Pi` is threshold exceedance only.
- Reject truth-probability, detection-probability, or posterior-odds language unless it is explicitly HTT-owned posterior pushforward with matching caveats.
- Check threshold registration and look-elsewhere metadata.

### F
- Verify `F` is certified occupancy only under sign-clean samples and admissible ceiling.
- Check no clipping hides super-ceiling or negative samples.
- Reject claims that external-transfer denominators certify native filling.

### G_F
- Verify depth-bin metadata, reference/comparison bins, floor-applied-by-bin reporting, raw/effective `F`, denominator split, null status, and calibration caveats.
- Treat matched-null `G_F` reports as forecast-only unless observed matched nulls, PPC, LOOCV, prior sweeps, covariance, and native morphology-atlas gates are all explicitly bound.
- Reject `G_F` as global-tilt evidence unless local/systematic null competition and matched calibration are present.

### MIO/HTT separation
- Check MIO report cards do not create evidence, posterior odds, model ranking, or truth certificates.
- Check HTT posterior pushforward does not merge MIO certificates as evidence.
- Check result packs keep diagnostic status distinct from production readiness labels.
- Check whether semantic-firewall machinery blocks leakage across these lanes in generated outputs, not just in prose.

### Legacy lnB leakage
- Identify any `lnB`, Bayes-factor, evidence-like, or production-readiness language inherited from legacy or VER2 files.
- Accept legacy tokens only when they are explicitly archival, not used as current scientific evidence, and do not enter MIO diagnostic claims.
- Reject any hidden promotion of diagnostic reports into observed-data evidence via legacy readiness language.

### Figures
- For each included figure, inspect its manifest before judging the caption.
- Treat conditioned legacy figures as prior-context diagnostics only.
- Reject any visual inference that is not supported by manifest claim tier, null status, covariance status, and transfer provenance.

## Rejection Triggers

Reject if any current claim says or implies:
- a detected Bianchi geometry.
- an identified Bianchi family.
- external-transfer output is described as native-validated.
- diagnostic-only MIO material is promoted into model-probability, evidence-like, or truth-status language.
- scalar formalism values alone imply geometry, family, or native-solver validation.
"""


def render_readme() -> str:
    return """# Statistical Formalism External Audit Package

This archive is a narrow re-audit bundle for `x_C/Q/Pi/F/G_F` formalism.

Use `AUDIT_PROMPT_STATISTICAL_FORMALISM.md` first.  The compiled PDF is
excluded; selected LaTeX source, generated reports, figure payloads/manifests,
formalism code, and formalism tests are included only where needed to interpret
the statistical definitions and manuscript figures.

This package is diagnostic-only.  It is not native solver validation, not a
geometry detection claim, and not a Bianchi family-ID claim.
Historical status ledgers may preserve archived readiness vocabulary as
provenance; current result packs use diagnostic-only public readiness and
legacy-not-current caveats.
"""


def build_payload(
    *,
    repo_root: Path | str = REPO_ROOT,
    output_zip: Path = DEFAULT_OUTPUT_ZIP,
    output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
    output_prompt: Path = DEFAULT_OUTPUT_PROMPT,
    output_readiness: Path = DEFAULT_OUTPUT_READINESS,
    generating_command: str,
    git_commit: str | None = None,
    worktree_state: str | None = None,
) -> tuple[dict[str, Any], Sequence[PackageEntry]]:
    root = Path(repo_root).resolve()
    linter_report, linter_passed = render_figure_label_linter_report(root)
    entries: list[PackageEntry] = [
        _virtual_entry("README.md", "package_readme", "statistical formalism audit package guide", render_readme()),
        _virtual_entry("AUDIT_PROMPT_STATISTICAL_FORMALISM.md", "statistical_prompt", "adversarial statistical formalism audit prompt", render_prompt()),
        _virtual_entry("READINESS_CHECKLIST.md", "readiness_checklist", "pre re-audit finding/fix checklist", render_readiness_checklist()),
        _virtual_entry("FIGURE_LABEL_LINTER_REPORT.md", "figure_label_linter_report", "generated formalism figure-label linter report", linter_report),
        *_file_entries(root, LATEX_SOURCE_FILES, group="latex_source", description="LaTeX source and generated snippets needed to locate formalism claims"),
        *_file_entries(root, FORMALISM_METADATA_FILES, group="formalism_metadata", description="generated result packs, ledgers, and payloads for formalism audit"),
        *_file_entries(root, FORMALISM_CODE_FILES, group="formalism_code", description="minimal formalism code required to audit definitions"),
        *_file_entries(root, FORMALISM_TEST_FILES, group="formalism_test", description="formalism tests documenting constraints and forbidden semantics"),
        *_figure_entries(root),
    ]
    rows = _entry_rows(root, entries)
    assertions = _required_assertions(root, rows)
    assertions["figure_label_linter_passed"] = linter_passed
    failed_gates = [name for name, ok in assertions.items() if not ok]
    archive_paths = [row["archive_path"] for row in rows]
    config = {
        "schema_version": SCHEMA_VERSION,
        "archive_paths": archive_paths,
        "assertions": sorted(assertions),
        "package_focus": "x_C_Q_Pi_F_G_F_statistical_formalism",
        "pdf_excluded": True,
    }
    commit = git_commit or _git_commit(root)
    state = worktree_state or _git_state(root)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": output_zip.as_posix(),
        "manifest_path": output_manifest.as_posix(),
        "prompt_path": output_prompt.as_posix(),
        "readiness_path": output_readiness.as_posix(),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts/build_statistical_formalism_audit_package.py",
        "git_commit": commit,
        "config_hash": _stable_hash(config),
        "input_hashes": [f"{row['source_path']}:{row['sha256']}" for row in rows],
        "code_version": state,
        "schema_version": SCHEMA_VERSION,
        "transfer_source": "mixed_none_external_transfer_and_conditioned_legacy",
        "sky_support_status": "not_directional",
        "null_mock_status": "mixed_formalism_tests_diagnostic_nulls_and_conditioned_legacy",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": state,
        "archive_entries": rows,
        "archive_entry_count": len(rows),
        "required_assertions": assertions,
        "required_gates": sorted(assertions),
        "passed_gates": sorted(name for name, ok in assertions.items() if ok),
        "failed_gates": failed_gates,
        "report_generation_gates": {
            "archive_build": "pass" if not failed_gates else "fail",
            "figure_payload_manifest_pairing": "pass" if assertions.get("formalism_figures_have_payload_and_manifest") else "fail",
            "figure_manifest_claim_lanes": "pass" if assertions.get("figure_manifest_lanes_safe") else "fail",
            "compiled_pdf_excluded": "pass" if assertions.get("compiled_pdf_excluded") else "fail",
        },
        "science_promotion_gates": {
            "native_low_ell_solver_validation": "fail_not_available",
            "native_morphology_atlas": "fail_not_available",
            "family_identification": "blocked",
            "xqpi_fg_geometry_claim": "blocked",
        },
        "publication_gates": {
            "external_statistical_formalism_audit_ready": "pass" if not failed_gates else "fail",
            "publication_ready": "fail_diagnostic_only",
        },
        "formalism_focus": {
            "x_C": "signed comparator coordinate",
            "Q": "policy-normalized diagnostic score",
            "Pi": "threshold exceedance curve",
            "F": "certified filling fraction under sign-clean/admissible-ceiling conditions",
            "G_F": "depth-gap diagnostic with bin/null metadata requirements",
        },
        "caveats": [
            "The package is for external physics/statistics/formalism audit only.",
            "The compiled PDF is excluded to reduce size; selected LaTeX source is included.",
            "Formalism code/tests are included only to clarify definitions and gates.",
            "Scalar formalism quantities do not support Bianchi geometry detection or family-ID.",
            "Current transfer-dependent and conditioned legacy material remains transfer-conditional.",
        ],
    }
    issues = validate_manifest_payload(
        payload,
        manifest_path=output_manifest,
        expected_artifact_path=output_zip.as_posix(),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid statistical formalism audit manifest: {rendered}")
    return payload, tuple(entries)


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


def _write_outputs(
    repo_root: Path,
    payload: dict[str, Any],
    entries: Sequence[PackageEntry],
    output_zip: Path,
    output_manifest: Path,
    output_prompt: Path,
    output_readiness: Path,
) -> None:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    output_prompt_path = output_prompt if output_prompt.is_absolute() else repo_root / output_prompt
    output_readiness_path = output_readiness if output_readiness.is_absolute() else repo_root / output_readiness
    output_zip_path.parent.mkdir(parents=True, exist_ok=True)
    output_zip_path.write_bytes(_build_zip_bytes(repo_root, payload, entries))
    output_manifest_path.write_text(_render_manifest(payload), encoding="utf-8")
    output_prompt_path.write_text(render_prompt(), encoding="utf-8")
    output_readiness_path.write_text(render_readiness_checklist(), encoding="utf-8")


def _check_outputs(
    repo_root: Path,
    payload: dict[str, Any],
    entries: Sequence[PackageEntry],
    output_zip: Path,
    output_manifest: Path,
    output_prompt: Path,
    output_readiness: Path,
) -> int:
    output_zip_path = output_zip if output_zip.is_absolute() else repo_root / output_zip
    output_manifest_path = output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
    output_prompt_path = output_prompt if output_prompt.is_absolute() else repo_root / output_prompt
    output_readiness_path = output_readiness if output_readiness.is_absolute() else repo_root / output_readiness
    if not output_zip_path.exists() or not output_manifest_path.exists():
        print("missing statistical formalism audit package output")
        return 1
    if not output_prompt_path.exists() or not output_readiness_path.exists():
        print("missing statistical formalism audit prompt/readiness output")
        return 1
    if output_manifest_path.read_text(encoding="utf-8") != _render_manifest(payload):
        print("stale statistical formalism audit manifest")
        return 1
    if output_prompt_path.read_text(encoding="utf-8") != render_prompt():
        print("stale statistical formalism audit prompt")
        return 1
    if output_readiness_path.read_text(encoding="utf-8") != render_readiness_checklist():
        print("stale statistical formalism audit readiness checklist")
        return 1
    if output_zip_path.read_bytes() != _build_zip_bytes(repo_root, payload, entries):
        print("stale statistical formalism audit zip")
        return 1
    print(f"up-to-date {output_zip_path}")
    return 0


def _existing_manifest_self_reference_fields(
    repo_root: Path,
    output_manifest: Path,
) -> tuple[str | None, str | None]:
    manifest_path = output_manifest if output_manifest.is_absolute() else repo_root / output_manifest
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
    parser.add_argument("--output-prompt", type=Path, default=DEFAULT_OUTPUT_PROMPT)
    parser.add_argument("--output-readiness", type=Path, default=DEFAULT_OUTPUT_READINESS)
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
    payload, entries = build_payload(
        repo_root=repo_root,
        output_zip=args.output_zip,
        output_manifest=args.output_manifest,
        output_prompt=args.output_prompt,
        output_readiness=args.output_readiness,
        generating_command=_command_from_args(argv),
        git_commit=git_commit,
        worktree_state=worktree_state,
    )
    if payload["failed_gates"]:
        print("statistical formalism audit package failed required gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print("DRY-RUN: not writing statistical formalism audit package")
        print(f"archive_entry_count={payload['archive_entry_count']}")
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(
            repo_root,
            payload,
            entries,
            args.output_zip,
            args.output_manifest,
            args.output_prompt,
            args.output_readiness,
        )
    _write_outputs(
        repo_root,
        payload,
        entries,
        args.output_zip,
        args.output_manifest,
        args.output_prompt,
        args.output_readiness,
    )
    output_zip = args.output_zip if args.output_zip.is_absolute() else repo_root / args.output_zip
    output_manifest = args.output_manifest if args.output_manifest.is_absolute() else repo_root / args.output_manifest
    output_prompt = args.output_prompt if args.output_prompt.is_absolute() else repo_root / args.output_prompt
    output_readiness = args.output_readiness if args.output_readiness.is_absolute() else repo_root / args.output_readiness
    print(f"wrote {output_zip}")
    print(f"wrote {output_manifest}")
    print(f"wrote {output_prompt}")
    print(f"wrote {output_readiness}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
