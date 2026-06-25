#!/usr/bin/env python3
"""Build a self-contained external-audit package for the FINAL RESULTS report.

This is a separate, smaller package from the full research-only audit bundle.
It wraps only the credible-claim distillation in `docs/final_report/`: the
self-contained LaTeX report and its compiled PDF, the six manifest-backed
figures it embeds, the machine-checked generated records that back its
numbers, and the publication claim-freeze context.  It ships its own
adversarial audit prompt.

The compiled PDF *is* included here (the report is short), so an external
reviewer can read it directly; the LaTeX source is included so claims can be
traced to source.  Deterministic: a fixed zip date and sorted entries make the
archive byte-reproducible, so `--check` can detect drift.

    python scripts/build_final_report_audit_package.py            # write
    python scripts/build_final_report_audit_package.py --check    # verify
    python scripts/build_final_report_audit_package.py --dry-run  # list only
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
REPORT_DIR = Path("docs/final_report")
DEFAULT_OUTPUT_ZIP = REPORT_DIR / "htt_base_final_results_audit_package.zip"
DEFAULT_OUTPUT_MANIFEST = REPORT_DIR / "htt_base_final_results_audit_package_manifest.json"
DEFAULT_OUTPUT_PROMPT = REPORT_DIR / "htt_base_final_results_audit_prompt.md"
SCHEMA_VERSION = "common.final_report_audit_package.v1"
ARTIFACT_ID = "final_report_audit_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ARCHIVE_ROOT = "final_report_audit"

# Report source (required).
REPORT_FILES = (
    "docs/final_report/main.tex",
    "docs/final_report/main.pdf",
)

# The manifest-backed figures the report embeds, with sidecars.
FIGURE_STEMS = (
    "figures/current/fig_theorem_nt_a1_quadrupole_filling",
    "figures/current/fig_theorem_nt_a3_cosmic_variance_floor",
    "figures/current/fig_theorem_nt_b3_gf_transport",
    "figures/current/fig_pr04_a1_rank_ladder",
    "figures/current/fig_pr04_a2_wigner",
    "figures/current/fig_pr04_b1_nonsufficiency",
    "figures/current/fig_pr04_b2_dust_shear",
    "figures/observed_current/fig_observed_lowell_null_significance",
    "figures/observed_current/fig_observed_lowell_morphology_axis",
    "figures/observed_current/fig_observed_cf4_bulkflow_apex_depth",
    "figures/observed_current/fig_observed_cf4_bulkflow_likelihood",
    "figures/observed_current/fig_observed_cf4_affine_flow",
)

# Generated records that back the report's numbers (provenance, not prose).
EVIDENCE_FILES = (
    "docs/generated/egs_lowell_theorem_proofs.json",
    "docs/generated/egs_lowell_theorem_proofs.md",
    "docs/generated/lowell_morphology_real_map_report.json",
    "docs/generated/lowell_morphology_real_map_report.md",
    "docs/generated/cf4_bulkflow_apex_depth_report.json",
    "docs/generated/cf4_bulkflow_apex_depth_report.md",
    "docs/generated/pr04_paper_theorem_proofs.json",
    "docs/generated/pr04_paper_theorem_proofs.md",
    "docs/generated/cf4_bulkflow_likelihood_report.json",
    "docs/generated/cf4_bulkflow_likelihood_report.md",
    "docs/generated/cf4_affine_flow_report.json",
    "docs/generated/cf4_affine_flow_report.md",
    "docs/generated/transfer_sensitivity_report.md",
    "docs/generated/new_results_real_data_summary.md",
    "docs/generated/publication_claim_freeze.md",
    # PR07 audit-repair evidence backing the new report sections.
    "docs/generated/pr07_wolfram_proofs.json",
    "docs/generated/pr07_cove_report.json",
    "docs/generated/pr07_paper_a.json",
    "docs/generated/pr07_paper_b.json",
    "docs/generated/pr07_k1_global_synthetic.json",
    "docs/generated/pr07_k5_hierarchical_synthetic.json",
    "docs/generated/pr07_k6_affine_ensemble_synthetic.json",
)


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


def _git_state(repo_root: Path) -> str:
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True, capture_output=True, check=False
    )
    head = commit.stdout.strip() if commit.returncode == 0 else "unknown"
    dirty = subprocess.run(
        ["git", "status", "--short"], cwd=repo_root, text=True, capture_output=True, check=False
    )
    return f"{head}+dirty" if dirty.stdout.strip() else head


def _file_entry(rel: str, group: str) -> Entry:
    return Entry(archive_path=f"{ARCHIVE_ROOT}/{rel}", group=group, source_path=Path(rel))


def _virtual_entry(archive: str, group: str, text: str) -> Entry:
    return Entry(archive_path=archive, group=group, content=text.encode("utf-8"))


def _collect_entries(repo_root: Path) -> list[Entry]:
    entries: list[Entry] = [
        _virtual_entry("README.md", "package_readme", render_readme()),
        _virtual_entry("AUDIT_PROMPT.md", "audit_prompt", render_prompt()),
    ]
    for rel in REPORT_FILES:
        if not (repo_root / rel).is_file():
            raise FileNotFoundError(f"required report file missing (build the PDF first): {rel}")
        entries.append(_file_entry(rel, "report_source" if rel.endswith(".tex") else "report_pdf"))
    for stem in FIGURE_STEMS:
        png = f"{stem}.png"
        manifest = f"{stem}.manifest.json"
        if not (repo_root / png).is_file():
            raise FileNotFoundError(f"required figure missing: {png}")
        if not (repo_root / manifest).is_file():
            raise FileNotFoundError(f"required figure manifest missing: {manifest}")
        entries.append(_file_entry(png, "figure_payload"))
        entries.append(_file_entry(manifest, "figure_manifest"))
        source_json = f"{stem}.source.json"
        if (repo_root / source_json).is_file():
            entries.append(_file_entry(source_json, "figure_source_json"))
    for rel in EVIDENCE_FILES:
        if not (repo_root / rel).is_file():
            raise FileNotFoundError(f"required evidence record missing: {rel}")
        entries.append(_file_entry(rel, "evidence_record"))
    return entries


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
    figure_png = {p[:-4] for p in paths if p.endswith(".png")}
    figure_manifest = {p[: -len(".manifest.json")] for p in paths if p.endswith(".manifest.json")}
    return {
        "report_tex_included": f"{ARCHIVE_ROOT}/docs/final_report/main.tex" in paths,
        "report_pdf_included": f"{ARCHIVE_ROOT}/docs/final_report/main.pdf" in paths,
        "audit_prompt_included": "AUDIT_PROMPT.md" in paths,
        "readme_included": "README.md" in paths,
        "all_figures_have_manifest": bool(figure_png) and figure_png == figure_manifest,
        "six_figures_present": len(figure_png) == len(FIGURE_STEMS),
        "theorem_proof_record_included": f"{ARCHIVE_ROOT}/docs/generated/egs_lowell_theorem_proofs.json" in paths,
        "k1_report_included": f"{ARCHIVE_ROOT}/docs/generated/lowell_morphology_real_map_report.json" in paths,
        "k4_report_included": f"{ARCHIVE_ROOT}/docs/generated/cf4_bulkflow_apex_depth_report.json" in paths,
        "transfer_inventory_included": f"{ARCHIVE_ROOT}/docs/generated/transfer_sensitivity_report.md" in paths,
        "claim_freeze_included": f"{ARCHIVE_ROOT}/docs/generated/publication_claim_freeze.md" in paths,
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
    entries = _collect_entries(root)
    rows = _entry_rows(root, entries)
    assertions = _assertions(rows)
    failed = [name for name, ok in assertions.items() if not ok]
    state = worktree_state or _git_state(root)
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
        "transfer_source": "mixed_none_observed_and_external_transfer_conditional",
        "sky_support_status": "mixed_full_sky_map_and_cf4_reconstruction_grid",
        "null_mock_status": "mixed_null_calibrated_bootstrap_and_synthetic_theorem",
        "family_identification": False,
        "native_solver_result": False,
        "schema_version": SCHEMA_VERSION,
        "created_by": "scripts/build_final_report_audit_package.py",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": state,
        "code_version": state,
        "config_hash": _stable_hash(config),
        "input_hashes": [f"{r['source_path']}:{r['sha256']}" for r in rows],
        "archive_entries": rows,
        "archive_entry_count": len(rows),
        "required_assertions": assertions,
        "passed_gates": sorted(n for n, ok in assertions.items() if ok),
        "failed_gates": failed,
        "science_promotion_gates": {
            "native_low_ell_solver_validation": "fail_not_available",
            "native_morphology_atlas": "fail_not_available",
            "family_identification_or_geometry_detection": "blocked",
            "model_ranking_or_posterior_odds": "forbidden",
        },
        "caveats": [
            "Self-contained credible-claim distillation; not the full development manuscript.",
            "All results are diagnostic-only or explicitly transfer-conditional.",
            "No Bianchi family-ID, no geometry detection, no native low-ell solver validation.",
            "MIO certificates are diagnostic-only and separate from HTT inference.",
            "K1 p-values are local, look-elsewhere-tracked, single-sky, not full-covariance.",
        ],
    }
    return payload, tuple(entries)


def render_readme() -> str:
    return """# Final Results Report -- External Audit Package

This package is a self-contained, credible-claim distillation of the
tetrad-based departure-decomposition program. It deliberately excludes
development history and any result that does not survive the project's
claim-firewall.

Contents:
- `AUDIT_PROMPT.md` -- adversarial physics/math/statistics audit prompt.
- `final_report_audit/docs/final_report/main.pdf` -- the compiled report (read this).
- `final_report_audit/docs/final_report/main.tex` -- LaTeX source (trace claims).
- `final_report_audit/figures/...` -- the six embedded figures with sidecar manifests.
- `final_report_audit/docs/generated/...` -- the machine-checked records that back the numbers.

What this report claims:
- a diagnostic-only departure-comparator framework (x_C and its variables);
- three Wolfram-verified conditional EGS-type theorems (NT-A1, NT-A3, NT-B3);
- two null-calibrated model-independent real-data measurements (Planck low-ell, CF4 bulk flow);
- explicitly transfer-conditional diagnostics (provenance only).

What this report does NOT claim (blocked):
- no identified Bianchi family, no detected anisotropic geometry;
- no native low-ell solver output or morphology atlas;
- no posterior odds, Bayes-factor headline, or model ranking;
- no native-validation label on any external/proxy transfer output.
"""


def render_prompt() -> str:
    return """# Adversarial Audit Prompt: Final Results Report (Credible-Claim Distillation)

You are an external adversarial reviewer. Audit only the research content:
physics, mathematics, statistics, inference design, claim tiers, figure and
table interpretation, and internal logic. Do not review software, packaging,
or code style.

## Inputs

Use this archive only. Read in this order:
1. `final_report_audit/docs/final_report/main.pdf` (or `main.tex`).
2. `final_report_audit/docs/generated/egs_lowell_theorem_proofs.{json,md}` (theorem proof record).
3. `final_report_audit/docs/generated/lowell_morphology_real_map_report.{json,md}` (K1).
4. `final_report_audit/docs/generated/cf4_bulkflow_apex_depth_report.{json,md}` (K4).
5. `final_report_audit/docs/generated/transfer_sensitivity_report.md` (transfer-conditional rows).
6. `final_report_audit/docs/generated/publication_claim_freeze.md` (claim boundaries).
7. figure sidecar manifests for any figure you cite.

## Hard boundaries (reject if used as a current result)

- an identified Bianchi family or a detected anisotropic geometry;
- native-solver validation for any external/proxy transfer output;
- a scalar diagnostic (x_C, Q, Pi, F, G_F), axis, or low-ell feature promoted to geometry/family evidence;
- a MIO certificate used as posterior odds, model weight, or HTT evidence;
- a globally significant low-ell anomaly detection (the K1 p-values are local, look-elsewhere-tracked, single-sky, not full-covariance/mask-coupled).

## Required output

Use exactly these sections:
1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Minimal Defensible Claim`: one conservative paragraph.
3. `Fatal Blockers`: only blockers that invalidate a stated result.
4. `Theorem Audit`: per theorem (NT-A1, NT-A3, NT-B3) -- are the hypotheses
   complete, the closure coefficient correctly attributed, the cosmic-variance
   floor branch-correct, the EGS limits valid? Table: `Item | Status | Issue | Required Fix`.
5. `Statistics Audit`: K1 null calibration, look-elsewhere handling, mask/covariance
   caveats; K4 bootstrap-as-lower-bound, edge-effect flag, volume-coordinate caveat.
   Table: `Item | Status | Issue | Required Fix`.
6. `Transfer-Provenance Audit`: is every transfer-conditional row clearly non-native
   and premise-conditioned? Any leakage into a headline?
7. `Claim-Tier Corrections`: exact wording to downgrade or remove.
8. `Claims That Are Safe`: bullet list allowed under current evidence.

## Token discipline

Return findings only. Cite `path:line` or a figure manifest path. If a section
is acceptable, say so in one sentence.
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
        print("missing final-report audit package output")
        return 1
    if man_path.read_text(encoding="utf-8") != _render_manifest(payload):
        print("stale final-report audit manifest")
        return 1
    if prompt_path.read_text(encoding="utf-8") != render_prompt():
        print("stale final-report audit prompt")
        return 1
    if zip_path.read_bytes() != _build_zip_bytes(repo_root, payload, entries):
        print("stale final-report audit zip")
        return 1
    print(f"up-to-date {zip_path}")
    return 0


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = [a for a in (sys.argv[1:] if argv is None else list(argv)) if a not in ("--check", "--dry-run")]
    return " ".join(["python", "scripts/build_final_report_audit_package.py", *args]).strip()


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
        print("final-report audit package failed gates: " + ", ".join(payload["failed_gates"]))
        return 1
    if args.dry_run:
        print(f"DRY-RUN archive_entry_count={payload['archive_entry_count']}")
        for key, value in sorted(payload["required_assertions"].items()):
            print(f"{key}={value}")
        return 0
    if args.check:
        return _check_outputs(repo_root, payload, entries, args.output_zip, args.output_manifest, args.output_prompt)
    _write_outputs(repo_root, payload, entries, args.output_zip, args.output_manifest, args.output_prompt)
    print(f"wrote {_resolve(repo_root, args.output_zip)}")
    print(f"wrote {_resolve(repo_root, args.output_manifest)}")
    print(f"wrote {_resolve(repo_root, args.output_prompt)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
