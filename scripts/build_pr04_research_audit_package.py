#!/usr/bin/env python3
"""Build the PR04 / LR-06 research external-audit package.

A self-contained bundle for an external research auditor of the
multicomponent / congruence / restricted-Bianchi-I program executed on the
`research/pr04-multicomponent` branch. Unlike the final-report package (the
polished report only) and the code-capability package (raw source only), this
carries the *reviewable research surface*: the credible-claim report, the
Wolfram proof records + theorem-to-test map, the theorem implementations and the
new observer-side estimators, the property gate tests, the new real-data
measurement reports, the honest LR-06 ticket ledger + claim/stop gates, the
figures, and this session's PR deltas. It ships its own adversarial research
audit prompt.

Deterministic (fixed zip date, sorted entries) so `--check` detects drift.

    python scripts/build_pr04_research_audit_package.py            # write
    python scripts/build_pr04_research_audit_package.py --check    # verify
    python scripts/build_pr04_research_audit_package.py --dry-run  # summary
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
OUT_DIR = Path("docs/research_program/pr04")
DEFAULT_OUTPUT_ZIP = OUT_DIR / "htt_pr04_research_audit_package.zip"
DEFAULT_OUTPUT_MANIFEST = OUT_DIR / "htt_pr04_research_audit_package_manifest.json"
DEFAULT_OUTPUT_PROMPT = OUT_DIR / "htt_pr04_research_audit_prompt.md"
SCHEMA_VERSION = "common.pr04_research_audit_package.v1"
ARTIFACT_ID = "pr04_research_audit_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ARCHIVE_ROOT = "pr04_research_audit"
THIS_SCRIPT = "scripts/build_pr04_research_audit_package.py"

REPORT_FILES = ("docs/final_report/main.tex", "docs/final_report/main.pdf")

THEOREM_RECORDS = (
    "docs/generated/egs_lowell_theorem_proofs.json",
    "docs/generated/egs_lowell_theorem_proofs.md",
    "docs/generated/pr04_paper_theorem_proofs.json",
    "docs/generated/pr04_paper_theorem_proofs.md",
    "docs/research_program/pr04/PAPER_THEOREM_MAP.md",
    # PR07 audit-repair symbolic + chain-of-verification records.
    "docs/generated/pr07_wolfram_proofs.json",
    "docs/generated/pr07_cove_report.json",
    "docs/generated/pr07_capability_probe.json",
)

MEASUREMENT_REPORTS = (
    "docs/generated/lowell_morphology_real_map_report.json",
    "docs/generated/lowell_morphology_real_map_report.md",
    "docs/generated/cf4_bulkflow_apex_depth_report.json",
    "docs/generated/cf4_bulkflow_apex_depth_report.md",
    "docs/generated/cf4_bulkflow_likelihood_report.json",
    "docs/generated/cf4_bulkflow_likelihood_report.md",
    "docs/generated/cf4_affine_flow_report.json",
    "docs/generated/cf4_affine_flow_report.md",
    # PR07 synthetic estimator-mechanics + theorem-fixture evidence.
    "docs/generated/pr07_paper_a.json",
    "docs/generated/pr07_paper_b.json",
    "docs/generated/pr07_k1_global_synthetic.json",
    "docs/generated/pr07_k5_hierarchical_synthetic.json",
    "docs/generated/pr07_k6_affine_ensemble_synthetic.json",
    # EGS2 extension experiment evidence (NT2-* + blocker discharges).
    "docs/generated/egs2_experiments.json",
    # EGS3 extension experiment evidence + B4 + PSD-cone symbolic records.
    "docs/generated/egs3_experiments.json",
    "docs/generated/egs3_bracket_constants_proof.json",
    "docs/generated/egs3_psd_cone_proof.json",
    # Consolidated cross-programme results table (data-analysis aggregate).
    "docs/generated/egs_results_table.json",
    "docs/generated/egs_results_table.md",
    # Real-data blocker discharges (rev-r127): K1 global max-scan, K5 coverage, K6 curl no-go.
    "docs/generated/k1_global_maxscan.json",
    "docs/generated/k5_cf4_release_coverage.json",
    "docs/generated/k6_cf4_curl_posterior.json",
    # PR08-006 joint artifact over the discharged sectors (rev-r129).
    "docs/generated/pr08_006_joint_artifact.json",
)

# Theorem implementations (PR04 overlay) + OBSSTAT estimators + PR07 modules.
SOURCE_FILES = (
    "htt/htt/htt/common/stf_canonical.py",
    "htt/htt/htt/common/multicomponent_blocks.py",
    "htt/bass/observer/congruence_ssot.py",
    "htt/htt/htt/departure/multicomponent_response.py",
    "htt/htt/htt/departure/paper_a_closure.py",
    "htt/bass/background/bi_continuation/__init__.py",
    "htt/bass/background/bi_continuation/moments.py",
    "htt/bass/background/bi_continuation/dynamics.py",
    "htt/bass/background/bi_continuation/verification.py",
    "htt/mio/formalism/physical_pushforward.py",
    "htt/htt/htt/integration/pr04_canonical_bridge.py",
    "htt/obsstat/affine_flow.py",
    "htt/obsstat/bulkflow_mle.py",
    "htt/obsstat/lowell_global_calibration.py",
    # EGS2 extension theorem modules + blocker-discharge mechanics.
    "htt/obsstat/egs2_fisher.py",
    "htt/obsstat/egs2_shear_bracket.py",
    "htt/obsstat/egs2_transport.py",
    "htt/obsstat/constrained_realizations.py",
    # EGS3 extension theorem modules (graded comparator + GR/Boltzmann).
    "htt/obsstat/egs3_graded_comparator.py",
    "htt/obsstat/egs3_calibration.py",
    "htt/obsstat/egs3_volterra_memory.py",
    "htt/obsstat/egs3_vorticity_channels.py",
    "htt/obsstat/egs3_psd_cone.py",
    "htt/bass/transfer/shear_quadrupole_seminative.py",
)

DRIVER_SCRIPTS = (
    "scripts/prove_egs_lowell_theorems.py",
    "scripts/prove_pr04_paper_theorems.py",
    "scripts/make_pr04_paper_figures.py",
    "scripts/make_cf4_bulkflow_likelihood.py",
    "scripts/make_cf4_affine_flow.py",
    "dl_pipeline/scripts/extract_cf4_full.py",
    "Makefile",
    "dl_pipeline/config/sources.json",
    # PR07 audit-repair harness.
    "scripts/run_pr07_wolfram_proofs.py",
    "scripts/run_pr07_experiments.py",
    "scripts/cove_verify_pr07.py",
    "scripts/capability_probe.py",
    "wolfram/pr07_symbolic_core.wls",
    "wolfram/pr07_xact_abstract.wls",
    "wolfram/pr07_bianchi_i_coordinates.wls",
    # EGS2 extension driver.
    "scripts/run_egs2_experiments.py",
    # EGS3 extension driver + B4 symbolic core.
    "scripts/run_egs3_experiments.py",
    "scripts/make_egs2_egs3_theorem_figures.py",
    "scripts/build_egs_results_table.py",
    "scripts/k1_global_maxscan.py",
    "scripts/k5_cf4_release_coverage.py",
    "scripts/k6_cf4_curl_posterior.py",
    "scripts/pr08_006_joint_artifact.py",
    "scripts/make_blocker_discharge_figures.py",
    "wolfram/egs3_bracket_constants.wls",
    "wolfram/egs3_psd_cone.wls",
)

GOVERNANCE_FILES = (
    "docs/research_program/pr04/LR06_TICKET_LEDGER.md",
    "docs/research_program/pr04/DATA_ACQUISITION_STATUS.md",
    "docs/research_program/pr04/RUST_NEW_PROJECT_DESIGN.md",
    "docs/research_program/pr04/CLAIM_AND_STOP_GATES.md",
    "docs/research_program/pr04/PAPER_EXIT_CRITERIA.md",
    "docs/research_program/pr04/LOCAL_REPO_EXECUTION_SCHEDULE.md",
    # PR07 audit-repair programme surface.
    "docs/research_program/pr07/README.md",
    "docs/research_program/pr07/PR_LIST.md",
    "docs/research_program/pr07/AGENT_SKILL_MAP.md",
    "docs/research_program/pr07/BLOCKER_RESOLUTION_MATRIX.md",
    "docs/research_program/pr07/CLAIM_GATES.md",
    "docs/research_program/pr07/DEPENDENCY_SCHEDULE.md",
    "docs/research_program/pr07/PAPER_FREEZE_PR07_007_008.md",
    "docs/research_program/pr07/PR08-005_2MRS_CROSS_RECONSTRUCTION_CONTRACT.md",
    "docs/research_program/pr07/WEB_CRAG_LEDGER.md",
    "docs/research_program/pr07/pr_registry.yaml",
    "docs/research_program/pr07/tickets/PR08-001.yaml",
    "docs/research_program/pr07/tickets/PR08-003.yaml",
    "docs/research_program/pr07/tickets/PR08-004.yaml",
    "docs/research_program/pr07/tickets/PR08-006.yaml",
    "docs/research_program/pr07/tickets/PR10-solver.yaml",
    # EGS2 extension programme surface.
    "docs/research_program/egs2/README.md",
    "docs/research_program/egs2/THEOREM_MAP.md",
    "docs/research_program/egs2/BLOCKER_DISCHARGES.md",
    "docs/research_program/egs2/PRIOR_ART.md",
    "docs/research_program/egs2/CLAIM_LEDGER.yaml",
    "docs/research_program/egs2/NEXT_DAG.yaml",
    "docs/research_program/egs2/tickets/K5_release_matched_mocks.yaml",
    "docs/research_program/egs2/tickets/semi_native_shear_to_quadrupole.yaml",
    # EGS3 programme surface (framework upgrade + theorem candidates + tickets).
    "docs/research_program/BLOCKERS.md",
    "docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md",
    "docs/research_program/egs3/README.md",
    "docs/research_program/egs3/FRAMEWORK_CRITIQUE_AND_REDESIGN.md",
    "docs/research_program/egs3/THEOREM_CANDIDATES.md",
    "docs/research_program/egs3/DIVERGENCE.md",
    "docs/research_program/egs3/BLOCKER_SOLUTIONS.md",
    "docs/research_program/egs3/CLAIM_LEDGER.yaml",
    "docs/research_program/egs3/tickets/k1_ffp10_npipe.yaml",
    "docs/research_program/egs3/tickets/cf4_wfcr.yaml",
    "docs/research_program/egs3/tickets/psd_cone_redesign.yaml",
)

FIGURE_STEMS = (
    "figures/current/fig_theorem_nt_a1_quadrupole_filling",
    "figures/current/fig_theorem_nt_a3_cosmic_variance_floor",
    "figures/current/fig_theorem_nt_b3_gf_transport",
    "figures/current/fig_pr04_a1_rank_ladder",
    "figures/current/fig_pr04_a2_wigner",
    "figures/current/fig_pr04_b1_nonsufficiency",
    "figures/current/fig_pr04_b2_dust_shear",
    "figures/current/fig_egs3_a1_graded_rank",
    "figures/current/fig_egs3_a3_evalue_calibration",
    "figures/current/fig_egs2_nt2a1_fisher_floor",
    "figures/current/fig_egs3_b1_floor_profile",
    "figures/current/fig_egs3_b2_volterra",
    "figures/current/fig_egs3_b3_vorticity",
    "figures/current/fig_egs2_nt2b1_bracket",
    "figures/current/fig_egs3_psd_cone",
    "figures/current/fig_blocker_discharges",
    "figures/observed_current/fig_observed_lowell_null_significance",
    "figures/observed_current/fig_observed_lowell_morphology_axis",
    "figures/observed_current/fig_observed_cf4_bulkflow_apex_depth",
    "figures/observed_current/fig_observed_cf4_bulkflow_likelihood",
    "figures/observed_current/fig_observed_cf4_affine_flow",
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
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=repo_root, text=True, capture_output=True, check=False)
    commit = head.stdout.strip() if head.returncode == 0 else "unknown"
    dirty = subprocess.run(["git", "status", "--short"], cwd=repo_root, text=True, capture_output=True, check=False)
    return f"{commit}+dirty" if dirty.stdout.strip() else commit


def _file_entry(rel: str, group: str) -> Entry:
    return Entry(archive_path=f"{ARCHIVE_ROOT}/{rel}", group=group, source_path=Path(rel))


def _virtual(archive: str, group: str, text: str) -> Entry:
    return Entry(archive_path=archive, group=group, content=text.encode("utf-8"))


def _pr_deltas(repo_root: Path) -> list[str]:
    return sorted(
        p.relative_to(repo_root).as_posix()
        for n in range(108, 130)
        for p in [repo_root / f"docs/PR_DELTAS/rev-r{n}.md"]
        if p.is_file()
    )


def _gate_tests(repo_root: Path) -> list[str]:
    out: list[str] = []
    for rel, pat in (("research_gates/pr04/tests", "test_pr0*_*.py"),
                     ("research_gates/pr07/tests", "test_pr0*_*.py"),
                     ("research_gates/egs2/tests", "test_egs2_*.py"),
                     ("research_gates/egs3/tests", "test_egs3_*.py")):
        d = repo_root / rel
        if d.is_dir():
            out += [p.relative_to(repo_root).as_posix() for p in d.glob(pat)]
    return sorted(out)


def _collect(repo_root: Path) -> list[Entry]:
    entries: list[Entry] = [
        _virtual("00_README.md", "package_readme", render_readme()),
        _virtual("AUDIT_PROMPT.md", "audit_prompt", render_prompt()),
    ]
    def add(rels: Sequence[str], group: str) -> None:
        for rel in rels:
            if not (repo_root / rel).is_file():
                raise FileNotFoundError(f"required {group} file missing: {rel}")
            entries.append(_file_entry(rel, group))
    add(REPORT_FILES, "report")
    add(THEOREM_RECORDS, "theorem_record")
    add(MEASUREMENT_REPORTS, "measurement_report")
    add(SOURCE_FILES, "theorem_implementation")
    add(DRIVER_SCRIPTS, "driver_script")
    add(GOVERNANCE_FILES, "governance")
    add(_gate_tests(repo_root), "gate_test")
    add(_pr_deltas(repo_root), "pr_delta")
    for stem in FIGURE_STEMS:
        png, man = f"{stem}.png", f"{stem}.manifest.json"
        if not (repo_root / png).is_file() or not (repo_root / man).is_file():
            raise FileNotFoundError(f"figure or manifest missing: {stem}")
        entries.append(_file_entry(png, "figure_payload"))
        entries.append(_file_entry(man, "figure_manifest"))
        src = f"{stem}.source.json"
        if (repo_root / src).is_file():
            entries.append(_file_entry(src, "figure_source_json"))
    return entries


def _entry_rows(repo_root: Path, entries: Sequence[Entry]) -> list[dict[str, Any]]:
    rows, seen = [], set()
    for entry in sorted(entries, key=lambda e: e.archive_path):
        if entry.archive_path.startswith("/") or ".." in Path(entry.archive_path).parts:
            raise ValueError(f"unsafe archive path: {entry.archive_path}")
        if entry.archive_path in seen:
            raise ValueError(f"duplicate archive path: {entry.archive_path}")
        seen.add(entry.archive_path)
        data = entry.bytes(repo_root)
        rows.append({"source_path": entry.source_text(), "archive_path": entry.archive_path,
                     "group": entry.group, "sha256": _sha256(data), "size_bytes": len(data)})
    return rows


def _assertions(rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
    paths = {r["archive_path"] for r in rows}
    groups: dict[str, int] = {}
    for r in rows:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
    figure_png = {p[:-4] for p in paths if p.endswith(".png")}
    figure_man = {p[: -len(".manifest.json")] for p in paths if p.endswith(".manifest.json")}
    return {
        "readme_included": "00_README.md" in paths,
        "audit_prompt_included": "AUDIT_PROMPT.md" in paths,
        "report_tex_and_pdf_included": f"{ARCHIVE_ROOT}/docs/final_report/main.tex" in paths
        and f"{ARCHIVE_ROOT}/docs/final_report/main.pdf" in paths,
        "pr04_proof_record_included": f"{ARCHIVE_ROOT}/docs/generated/pr04_paper_theorem_proofs.json" in paths,
        "theorem_implementations_present": groups.get("theorem_implementation", 0) >= 9,
        "obsstat_estimators_present": f"{ARCHIVE_ROOT}/htt/obsstat/affine_flow.py" in paths
        and f"{ARCHIVE_ROOT}/htt/obsstat/bulkflow_mle.py" in paths,
        "gate_tests_present": groups.get("gate_test", 0) >= 6,
        "measurement_reports_present": groups.get("measurement_report", 0) >= 8,
        "ledger_and_stop_gates_included": f"{ARCHIVE_ROOT}/docs/research_program/pr04/LR06_TICKET_LEDGER.md" in paths
        and f"{ARCHIVE_ROOT}/docs/research_program/pr04/CLAIM_AND_STOP_GATES.md" in paths,
        "pr_deltas_present": groups.get("pr_delta", 0) >= 7,
        "all_figures_have_manifest": bool(figure_png) and figure_png == figure_man,
        "twelve_figures": len(figure_png) == len(FIGURE_STEMS),
    }


def build_payload(*, repo_root: Path = REPO_ROOT, output_zip: Path = DEFAULT_OUTPUT_ZIP,
                  output_manifest: Path = DEFAULT_OUTPUT_MANIFEST, output_prompt: Path = DEFAULT_OUTPUT_PROMPT,
                  generating_command: str, worktree_state: str | None = None) -> tuple[dict[str, Any], Sequence[Entry]]:
    root = Path(repo_root).resolve()
    entries = _collect(root)
    rows = _entry_rows(root, entries)
    assertions = _assertions(rows)
    failed = [n for n, ok in assertions.items() if not ok]
    state = worktree_state or _git_state(root)
    groups: dict[str, int] = {}
    for r in rows:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
    config = {"schema_version": SCHEMA_VERSION, "archive_paths": [r["archive_path"] for r in rows],
              "assertions": sorted(assertions)}
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID, "artifact_path": output_zip.as_posix(),
        "manifest_path": output_manifest.as_posix(), "prompt_path": output_prompt.as_posix(),
        "owner": "COMMON", "implementation_scope": "common", "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "transfer_source": "mixed_none_observed_and_external_transfer_conditional",
        "family_identification": False, "native_solver_result": False,
        "schema_version": SCHEMA_VERSION, "created_by": THIS_SCRIPT,
        "generating_command": generating_command, "git_commit_or_worktree_state": state, "code_version": state,
        "config_hash": _stable_hash(config),
        "input_hashes": [f"{r['source_path']}:{r['sha256']}" for r in rows],
        "archive_entries": rows, "archive_entry_count": len(rows), "group_counts": groups,
        "required_assertions": assertions, "passed_gates": sorted(n for n, ok in assertions.items() if ok),
        "failed_gates": failed,
        "science_promotion_gates": {
            "native_low_ell_solver_validation": "fail_not_available",
            "family_identification_or_geometry_detection": "blocked",
            "global_tilt_from_cf4_distances": "blocked",
            "model_ranking_or_posterior_odds": "forbidden",
        },
        "caveats": [
            "Research-audit bundle for the PR04/LR-06/PR07 program; diagnostic-only / conditional-theorem.",
            "Includes the PR07 adversarial-audit repairs: theorem restatements, an independent dynamics verifier, a Wolfram/xAct symbolic gate, a CoVe report, and synthetic estimator-mechanics.",
            "Theorems are conditional structural identities, not detections.",
            "CF4 measurements are kinematic descriptors; vorticity reconstruction-conditioned; no global-tilt claim.",
            "No native low-ell solver output, family-ID, geometry detection, or posterior odds.",
            "Raw datasets are not shipped; reports carry release hashes + provenance.",
        ],
    }
    return payload, tuple(entries)


def render_readme() -> str:
    return """# HTT/BASS PR04 + LR-06 + PR07 Research External-Audit Package

Self-contained bundle for external review of the multicomponent / congruence /
restricted-Bianchi-I research program, including the PR07 adversarial-audit
repairs (branch `research/pr04-multicomponent`).

## Read in this order

1. `AUDIT_PROMPT.md` -- the adversarial research audit prompt.
2. `pr04_research_audit/docs/final_report/main.pdf` -- the credible-claim report.
3. `pr04_research_audit/docs/generated/pr04_paper_theorem_proofs.md` and
   `egs_lowell_theorem_proofs.md` -- the Wolfram-verified theorem cores; map in
   `docs/research_program/pr04/PAPER_THEOREM_MAP.md`.
4. `pr04_research_audit/docs/generated/pr07_wolfram_proofs.json` and
   `pr07_cove_report.json` -- the PR07 symbolic/xAct gate and the concise
   chain-of-verification (13 checks); the synthetic mechanics evidence is in
   `pr07_{paper_a,paper_b,k1,k5,k6}*.json`.
5. The measurement reports under `docs/generated/` (Planck low-ell K1; CF4 apex
   K4; CF4 full-release bulk flow K5; CF4 affine flow K6).
6. The theorem implementations (PR04 overlay + OBSSTAT estimators + the PR07
   `paper_a_closure`/`verification`/`lowell_global_calibration` modules), the gate
   tests under `research_gates/{pr04,pr07}/tests/`, and the `Makefile` targets
   (`pr04-gates`, `pr07-gates`, `pr07-wolfram`).
7. The honest status: `docs/research_program/pr04/LR06_TICKET_LEDGER.md`,
   `CLAIM_AND_STOP_GATES.md`, and the PR07 programme surface under
   `docs/research_program/pr07/` (PR list, agent/skill map, blocker matrix,
   claim gates, registry + blocked tickets); per-PR deltas under `docs/PR_DELTAS/`.

## What this bundle is / is not

- It is the reviewable research surface: report + proofs + implementations +
  gates + measurements + honest blocker ledger.
- It is NOT a results-freeze: every result is diagnostic-only, a conditional
  theorem, or explicitly synthetic estimator-mechanics. Family-ID, geometry
  detection, native low-ell solver validation, global-tilt-from-CF4, and
  posterior/odds claims remain blocked.
- Raw datasets are not shipped; reports carry release hashes and provenance.
"""


def render_prompt() -> str:
    return """# Adversarial Research Audit Prompt: PR04 + LR-06 + PR07 Program

You are an external adversarial reviewer. Audit only the research content:
physics, mathematics, statistics, theorem hypotheses, estimator design, claim
tiers, and figure/measurement interpretation. Do not grade code style.

## Inputs

This archive only. Start from `docs/final_report/main.pdf`, then the proof
records, the theorem implementations, the gate tests, and the measurement
reports.

## Required output sections

1. `Verdict`: PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. `Theorem Audit`: per core (A-rank with full-column-rank qualifier, A-flrw,
   A-boost vs A-first-jet split, A-radial-novortex, A-shell-degeneracy,
   A-temporal-rank; B-nonsuff, B-psd, B-dust, B-shear; NT-A1 closure-conditional
   identity, NT-A3 estimator sampling variance, NT-B3 additive contrast) -- are
   the hypotheses complete and the symbolic claim correct (cross-check against
   `pr07_wolfram_proofs.json`)? Is the registered Bianchi-I branch stated? Was
   any forbidden token (EGS identity, cosmic-variance floor, CRLB, Wigner-angle,
   minimum-variance estimator) reintroduced? Table `Item | Status | Issue |
   Required Fix`.
3. `Estimator/Statistics Audit`: K1 null calibration + max-scan look-elsewhere;
   K4/K5/K6 bulk-flow + affine decomposition -- weighted-GLS (not minimum-variance)
   with conditional inverse-Fisher covariance, sigma_star nuisance, hierarchical
   random-effect coverage (`pr07_k5_*`), forward-mock coverage, K6 curl-suppression
   structural non-identifiability (`pr07_k6_*`), selection/Malmquist caveats. Are
   the synthetic mechanics correctly separated from observational claims?
4. `Independent-Verification Audit`: does the chain-rule dynamics verifier
   (`pr07_paper_b.json`) re-derive conservation/transport independently of the
   production RHS, and does the CoVe report (`pr07_cove_report.json`) terminate
   blocked lanes in registered blocker codes rather than substitute numbers?
5. `Claim-Tier Corrections`: exact wording to downgrade or remove.
6. `Blocked-Item Check`: confirm no scalar->family, no global-tilt-from-CF4, no
   MIO-as-odds, no native-solver inheritance, no radial-vorticity claim leaked.
7. `Claims That Are Safe`: bullet list allowed under current evidence.

## Hard boundaries (reject if used as a current result)

- an identified Bianchi family or detected anisotropic geometry;
- a global-tilt claim from CF4 distance data alone;
- native-solver validation for any external/proxy transfer output;
- a MIO certificate used as posterior odds or HTT evidence;
- a vorticity detection from a curl-suppressed reconstruction;
- a globally significant low-ell anomaly (K1 p-values are local, single-sky,
  look-elsewhere-tracked, not full-covariance/mask-coupled).

Cite `path:line` or a figure manifest path. Prefer concise tables.
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
    buf = BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as ar:
        ar.writestr(_zip_info("MANIFEST.json"), _render_manifest(payload).encode("utf-8"))
        for row in sorted(payload["archive_entries"], key=lambda r: r["archive_path"]):
            ar.writestr(_zip_info(row["archive_path"]), by_path[row["archive_path"]].bytes(repo_root))
    return buf.getvalue()


def _resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _write_outputs(repo_root, payload, entries, output_zip, output_manifest, output_prompt) -> None:
    zp, mp, pp = (_resolve(repo_root, p) for p in (output_zip, output_manifest, output_prompt))
    for p in (zp, mp, pp):
        p.parent.mkdir(parents=True, exist_ok=True)
    zp.write_bytes(_build_zip_bytes(repo_root, payload, entries))
    mp.write_text(_render_manifest(payload), encoding="utf-8")
    pp.write_text(render_prompt(), encoding="utf-8")


def _check_outputs(repo_root, payload, entries, output_zip, output_manifest, output_prompt) -> int:
    zp, mp, pp = (_resolve(repo_root, p) for p in (output_zip, output_manifest, output_prompt))
    if not (zp.exists() and mp.exists() and pp.exists()):
        print("missing pr04 research audit package output"); return 1
    if mp.read_text(encoding="utf-8") != _render_manifest(payload):
        print("stale pr04 research audit manifest"); return 1
    if pp.read_text(encoding="utf-8") != render_prompt():
        print("stale pr04 research audit prompt"); return 1
    if zp.read_bytes() != _build_zip_bytes(repo_root, payload, entries):
        print("stale pr04 research audit zip"); return 1
    print(f"up-to-date {zp}"); return 0


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
    worktree_state = None
    mp = _resolve(repo_root, args.output_manifest)
    if args.check and mp.exists():
        worktree_state = json.loads(mp.read_text(encoding="utf-8")).get("git_commit_or_worktree_state")
    payload, entries = build_payload(repo_root=repo_root, output_zip=args.output_zip,
                                     output_manifest=args.output_manifest, output_prompt=args.output_prompt,
                                     generating_command=_command_from_args(argv), worktree_state=worktree_state)
    if payload["failed_gates"]:
        print("pr04 research audit package failed gates: " + ", ".join(payload["failed_gates"])); return 1
    if args.dry_run:
        print(f"DRY-RUN archive_entry_count={payload['archive_entry_count']}")
        print("group_counts=" + json.dumps(payload["group_counts"], sort_keys=True))
        for k, v in sorted(payload["required_assertions"].items()):
            print(f"{k}={v}")
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
