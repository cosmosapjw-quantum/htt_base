#!/usr/bin/env python3
"""Build a self-contained, context-independent RESEARCH-EVALUATION package at repo root.

Unlike the final-report audit package (report + provenance only) and the code-capability
package (raw source only), this bundle is built for an external reviewer with **no prior
knowledge of the repository** to give a **critical and constructive** evaluation of the
*research content*: the report, the essential research code that produces every headline,
the machine-checked result records, and the runnable gate tests. It ships its own
context-independent review prompt (explains the project from scratch).

Deterministic (fixed zip date, sorted entries, content-addressed provenance) so `--check`
detects drift. Outputs at REPO ROOT:

    htt_base_research_evaluation_package.zip
    htt_base_research_evaluation_package_manifest.json
    htt_base_research_evaluation_prompt.md

    python scripts/build_research_evaluation_package.py            # write
    python scripts/build_research_evaluation_package.py --check    # verify
    python scripts/build_research_evaluation_package.py --dry-run  # list only
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys
import zipfile
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ZIP = Path("htt_base_research_evaluation_package.zip")
DEFAULT_OUTPUT_MANIFEST = Path("htt_base_research_evaluation_package_manifest.json")
DEFAULT_OUTPUT_PROMPT = Path("htt_base_research_evaluation_prompt.md")
SCHEMA_VERSION = "common.research_evaluation_package.v1"
ARTIFACT_ID = "research_evaluation_package"
FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)
ARCHIVE_ROOT = "research_evaluation"
# content-addressed provenance: pinned by config_hash + input_hashes, not volatile HEAD
PROVENANCE = "content-addressed"

REPORT_FILES = ("docs/final_report/main.tex", "docs/final_report/main.pdf")

# The research content code: the modules + drivers that PRODUCE every headline.
RESEARCH_CODE = (
    # five-variable framework + graded/PSD comparator
    "htt/htt/htt/core/departure_posteriors.py",
    "htt/obsstat/egs3_graded_comparator.py",
    "htt/obsstat/egs3_psd_cone.py",
    "htt/obsstat/egs3_calibration.py",
    "htt/obsstat/egs3_volterra_memory.py",
    "htt/obsstat/egs3_vorticity_channels.py",
    # EGS2 theorem modules
    "htt/obsstat/egs2_fisher.py",
    "htt/obsstat/egs2_shear_bracket.py",
    "htt/obsstat/egs2_transport.py",
    "htt/obsstat/constrained_realizations.py",
    # GR/Boltzmann transfer
    "htt/bass/transfer/shear_quadrupole_seminative.py",
    # real-data estimators
    "htt/obsstat/lowell_global_calibration.py",
    "htt/obsstat/lowell_map_features.py",
    "htt/obsstat/morphology.py",
    "htt/obsstat/scalar_lowell.py",
    "htt/obsstat/biposh_features.py",
    "htt/obsstat/affine_flow.py",
    "htt/obsstat/bulkflow_mle.py",
    "htt/obsstat/lowell_precision.py",
    # discharge + aggregation drivers
    "scripts/k1_global_maxscan.py",
    "scripts/k5_cf4_release_coverage.py",
    "scripts/k6_cf4_curl_posterior.py",
    "scripts/pr08_006_joint_artifact.py",
    "scripts/build_egs_results_table.py",
    "scripts/make_blocker_discharge_figures.py",
    # symbolic cores
    "wolfram/egs3_bracket_constants.wls",
    "wolfram/egs3_psd_cone.wls",
)

# Runnable gate tests (so the reviewer can re-run the claims).
TEST_FILES = (
    "research_gates/egs3/tests/test_egs3_axis_a.py",
    "research_gates/egs3/tests/test_egs3_axis_b.py",
    "research_gates/egs3/tests/test_egs3_axis_psd.py",
    "research_gates/egs2/tests/test_egs2_fisher_bracket.py",
    "research_gates/egs2/tests/test_egs2_transport.py",
    "research_gates/egs2/tests/test_egs2_blocker_discharges.py",
    "research_gates/external_audit_2026_06_29/reviewer_verification.py",
    "tests/obsstat/test_k1_global_maxscan.py",
    "tests/obsstat/test_k1_noise_mode.py",
    "tests/obsstat/test_lowell_precision.py",
    "tests/obsstat/test_k5_cf4_release_coverage.py",
    "tests/obsstat/test_k6_cf4_curl_posterior.py",
    "tests/contracts/test_pr08_006_joint_artifact.py",
    "tests/contracts/test_psd_cone_redesign.py",
)

# Reproducibility references: the commands/records cited in the report's
# Reproducibility section. Bundled so the package is genuinely self-contained --
# every script + proof record the report cites is present under the
# `research_evaluation/` subtree (a report-reference existence check passes there)
# (external-audit pr08_reassessment finding: report referenced commands not shipped).
REPRODUCIBILITY_REFS = (
    "scripts/prove_egs_lowell_theorems.py",
    "scripts/make_egs_lowell_theorem_figures.py",
    "scripts/make_pr04_paper_figures.py",
    "scripts/make_lowell_morphology_real_map.py",
    "scripts/make_cf4_bulkflow_apex_depth.py",
    "scripts/make_cf4_bulkflow_likelihood.py",
    "scripts/make_cf4_affine_flow.py",
    "scripts/generate_transfer_sensitivity_report.py",
    "scripts/run_pr07_experiments.py",
    "scripts/cove_verify_pr07.py",
    "scripts/claim_lint_research_surfaces.py",
    "docs/generated/egs_lowell_theorem_proofs.json",
    "docs/generated/pr04_paper_theorem_proofs.json",
    "research_gates/pr04/tests/test_pr04_bianchi.py",
    "research_gates/pr04/tests/test_pr04_congruence.py",
    "research_gates/pr04/tests/test_pr04_integration.py",
    "research_gates/pr04/tests/test_pr04_pushforward.py",
    "research_gates/pr04/tests/test_pr04_response.py",
    "research_gates/pr04/tests/test_pr04_schema.py",
)

# Machine-checked result records that back every number.
RESULT_RECORDS = (
    "docs/generated/egs_results_table.json",
    "docs/generated/egs_results_table.md",
    "docs/generated/egs3_experiments.json",
    "docs/generated/egs3_psd_cone_proof.json",
    "docs/generated/egs3_bracket_constants_proof.json",
    "docs/generated/egs2_experiments.json",
    "docs/generated/k1_global_maxscan.json",
    "docs/generated/k5_cf4_release_coverage.json",
    "docs/generated/k6_cf4_curl_posterior.json",
    "docs/generated/pr08_006_joint_artifact.json",
    "docs/research_program/BLOCKERS.md",
    "docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md",
)

FIGURE_STEMS = (
    "figures/current/fig_egs3_a1_graded_rank",
    "figures/current/fig_egs3_psd_cone",
    "figures/current/fig_egs2_nt2a1_fisher_floor",
    "figures/current/fig_egs3_b1_floor_profile",
    "figures/current/fig_egs3_b2_volterra",
    "figures/current/fig_egs3_b3_vorticity",
    "figures/current/fig_blocker_discharges",
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


def _file_entry(rel: str, group: str) -> Entry:
    return Entry(archive_path=f"{ARCHIVE_ROOT}/{rel}", group=group, source_path=Path(rel))


def _virtual_entry(archive: str, group: str, text: str) -> Entry:
    return Entry(archive_path=archive, group=group, content=text.encode("utf-8"))


def _collect_entries(repo_root: Path) -> list[Entry]:
    entries: list[Entry] = [
        _virtual_entry("README.md", "package_readme", render_readme()),
        _virtual_entry("REVIEW_PROMPT.md", "review_prompt", render_prompt()),
    ]
    groups = (
        (REPORT_FILES, "report"),
        (RESEARCH_CODE, "research_code"),
        (TEST_FILES, "gate_test"),
        (RESULT_RECORDS, "result_record"),
        (REPRODUCIBILITY_REFS, "reproducibility_ref"),
    )
    for files, group in groups:
        for rel in files:
            if not (repo_root / rel).is_file():
                raise FileNotFoundError(f"required {group} missing: {rel}")
            entries.append(_file_entry(rel, group))
    for stem in FIGURE_STEMS:
        for suffix, grp in ((".png", "figure_payload"), (".manifest.json", "figure_manifest")):
            rel = f"{stem}{suffix}"
            if not (repo_root / rel).is_file():
                raise FileNotFoundError(f"required figure file missing: {rel}")
            entries.append(_file_entry(rel, grp))
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
        rows.append({"source_path": entry.source_text(), "archive_path": entry.archive_path,
                     "group": entry.group, "sha256": _sha256(data), "size_bytes": len(data)})
    return rows


def _assertions(rows: Sequence[dict[str, Any]]) -> dict[str, bool]:
    paths = {r["archive_path"] for r in rows}
    groups = [r["group"] for r in rows]
    return {
        "report_pdf_included": f"{ARCHIVE_ROOT}/docs/final_report/main.pdf" in paths,
        "report_tex_included": f"{ARCHIVE_ROOT}/docs/final_report/main.tex" in paths,
        "review_prompt_included": "REVIEW_PROMPT.md" in paths,
        "readme_included": "README.md" in paths,
        "research_code_present": groups.count("research_code") >= 20,
        "gate_tests_present": groups.count("gate_test") >= 8,
        "result_records_present": groups.count("result_record") >= 10,
        "reproducibility_refs_present": groups.count("reproducibility_ref") >= 13,
        "joint_artifact_included": f"{ARCHIVE_ROOT}/docs/generated/pr08_006_joint_artifact.json" in paths,
        "results_table_included": f"{ARCHIVE_ROOT}/docs/generated/egs_results_table.json" in paths,
        "blockers_included": f"{ARCHIVE_ROOT}/docs/research_program/BLOCKERS.md" in paths,
    }


def build_payload(*, repo_root: Path = REPO_ROOT, output_zip: Path = DEFAULT_OUTPUT_ZIP,
                  output_manifest: Path = DEFAULT_OUTPUT_MANIFEST,
                  output_prompt: Path = DEFAULT_OUTPUT_PROMPT,
                  generating_command: str) -> tuple[dict[str, Any], Sequence[Entry]]:
    root = Path(repo_root).resolve()
    entries = _collect_entries(root)
    rows = _entry_rows(root, entries)
    assertions = _assertions(rows)
    failed = [name for name, ok in assertions.items() if not ok]
    config = {"schema_version": SCHEMA_VERSION, "archive_paths": [r["archive_path"] for r in rows],
              "assertions": sorted(assertions)}
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
        "null_mock_status": "mixed_null_calibrated_release_matched_and_synthetic_theorem",
        "family_identification": False,
        "native_solver_result": False,
        "schema_version": SCHEMA_VERSION,
        "created_by": "scripts/build_research_evaluation_package.py",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": PROVENANCE,
        "code_version": PROVENANCE,
        "config_hash": _stable_hash(config),
        "input_hashes": [f"{r['source_path']}:{r['sha256']}" for r in rows],
        "archive_entries": rows,
        "archive_entry_count": len(rows),
        "required_assertions": assertions,
        "passed_gates": sorted(n for n, ok in assertions.items() if ok),
        "failed_gates": failed,
        "science_promotion_gates": {
            "native_low_ell_solver_validation": "fail_not_available",
            "family_identification_or_geometry_detection": "blocked",
            "model_ranking_or_posterior_odds": "forbidden",
        },
        "caveats": [
            "Self-contained, context-independent research-evaluation bundle.",
            "All results are diagnostic-only / model-independent / transfer-conditional.",
            "No Bianchi family-ID, no geometry detection, no native low-ell solver validation.",
            "K6 is a structural no-go; K1 is a partial (look-elsewhere) discharge under a LambdaCDM null.",
            "External-data E2E runs (K1 full E2E) remain pending; see BLOCKERS.md + K1_E2E_DOWNLOAD_GUIDE.md.",
        ],
    }
    return payload, tuple(entries)


def render_readme() -> str:
    return """# BASS / HTT research-evaluation package (self-contained, context-independent)

This bundle lets a reviewer with **no prior knowledge of the repository** read the
research report, inspect the essential code that produces every headline, re-run the
gate tests, and read the machine-checked result records -- then give a **critical and
constructive** evaluation of the *research content*.

Read `REVIEW_PROMPT.md` first: it explains the project from scratch and states exactly
what to evaluate and what the claim boundaries are.

## Contents

- `REVIEW_PROMPT.md` -- context-independent critical+constructive review prompt.
- `research_evaluation/docs/final_report/main.pdf` (+ `main.tex`) -- the research report.
- `research_evaluation/htt/...`, `.../scripts/...`, `.../wolfram/...` -- the research code
  (five-variable + graded/PSD comparator, EGS2/EGS3 theorem modules, GR/Boltzmann
  transfer, the real-data estimators, the K1/K5/K6 + PR08-006 discharge drivers, symbolic cores).
- `research_evaluation/.../tests/...` -- runnable gate tests for the claims.
- `research_evaluation/docs/generated/...` -- result records (consolidated table, the
  K1/K5/K6 discharges, the PR08-006 joint comparator, theorem proofs).
- `research_evaluation/docs/research_program/{BLOCKERS.md,K1_E2E_DOWNLOAD_GUIDE.md}` --
  what is blocked and how to unblock it.

The repository subtree root inside this archive is `research_evaluation/`: every path
the report cites (e.g. `scripts/...`, `docs/generated/...`) is present under that
directory, so commands run from `research_evaluation/` resolve.

## How to run the gate tests (optional, if you have python+numpy)

```bash
cd research_evaluation
PYTHONPATH=.:htt:htt/htt python -m pytest tests research_gates -q
```

## Claim envelope (do not exceed)

Diagnostic-only / model-independent descriptors + conditional theorems + (where inputs
are owned) calibrated measurements. No Bianchi-family identification, no geometry
detection, no native low-ell solver output, no MIO-as-odds, no scalar->family promotion.
K5: the CF4 bulk flow is measured, but its cosmic-variance coverage is conditional on a
fixed LambdaCDM prior. K6 is a WF mean-field structural no-go (true CR posterior still
blocked). K1 is a partial (look-elsewhere) discharge under a LambdaCDM null, not E2E.
"""


def render_prompt() -> str:
    return """# Critical & constructive research review -- BASS / HTT departure-decomposition program

You are an expert cosmology + statistics reviewer. You have **no prior knowledge** of this
project; everything you need is in this archive. Give a review that is both **critical**
(find every flaw, overclaim, hidden assumption, and gap) **and constructive** (say
concretely what would make each result correct, stronger, and publishable). Review the
*research content only* -- physics, mathematics, statistics, inference design, claim
calibration -- not software style or packaging.

## What this project is (from scratch)

The program tests whether the cosmic microwave background (CMB) and low-redshift peculiar
velocities depart from the standard isotropic FLRW cosmology toward an anisotropic
(Bianchi + tilt) one. It deliberately works **without** a native low-ell anisotropic
Boltzmann solver (which does not exist here), so it cannot identify a Bianchi family or
detect a geometry. Instead it builds a *diagnostic comparator* over four physical sectors
-- shear `Sigma^2`, vorticity `W^2`, tilt `Omega_tilt`, anisotropic curvature `Omega_k` --
and asks which sectors current data can even constrain, with what calibration, and which
are provably blind. The intended contribution is a rank-aware, provenance-bound
identifiability + calibration result, plus conditional EGS-type (Ehlers-Geren-Sachs)
theorems applying GR + the covariant Boltzmann hierarchy directly to these variables.

## What to read (in order)

1. `research_evaluation/docs/final_report/main.pdf` -- the report (start here).
2. `docs/generated/egs_results_table.md` -- the consolidated results table (14 proven +
   3 data rows).
3. The K1/K5/K6 discharge records `docs/generated/k{1,5,6}_*.json` and the joint
   comparator `docs/generated/pr08_006_joint_artifact.json`.
4. The code under `htt/` and `scripts/` for any result you want to verify; the gate tests
   under `tests/`, `research_gates/`.
5. `docs/research_program/BLOCKERS.md` for what is blocked and why.

## Key claims to evaluate (be adversarial, then constructive)

- **Identifiability / rank:** within the registered leading-channel response map the
  comparator is rank-2 -- `Sigma^2` (CMB quadrupole) and `Omega_tilt` (dipole/bulk flow)
  are reachable. The two null sectors are NOT the same kind: `W^2` is a genuine,
  order-independent structural null (radial `n.Omega.n=0` + CMB curl/Weyl-blindness; its
  response column is a genuine zero, not `Sigma^2`-collinear), while `Omega_k` is a
  leading-EGS-order no-channel that re-opens beyond leading order. Is the response-map /
  null-space argument correct and complete? Is the genuine-zero-vs-degeneracy distinction sound?
- **PSD-cone redesign:** the comparator as a PSD matrix `M>=0` with `x_C = tr(C M)`
  bit-identical to the scalar; admissible set = convex cone; blind sector = structural
  null; bracket = convex cone-shell. Is this representation faithful and useful, or
  cosmetic?
- **EGS-type theorems (A/B axes):** Fisher-CR floor and its k-profile; Volterra
  depth-memory; vorticity radial-blindness with transverse re-opening; the two-sided
  shear bracket; the visibility-kernel contraction. Are the hypotheses complete, limits
  valid, constants correctly attributed (e.g. the ETM coefficient kappa=4/21)?
- **Real-data discharges:**
  - K5 -- CF4 bulk flow |B|~341+/-102 km/s (a measurement; consistent with the LambdaCDM
    ~150-250 km/s expectation at this depth), error cosmic-variance-dominated. The
    cosmic-variance-inclusive coverage 0.67 (vs 0.19 measurement-only) is from
    geometry-and-error matched Gaussian bulk-flow mocks and is CONDITIONAL on a fixed
    LambdaCDM sigma_cv=150 km/s/comp prior; full selection/Malmquist/grouping/correlated
    mocks remain a gate. Is the conditional-coverage framing honest? Frame/selection caveats?
  - K6 -- a WF mean-field structural *no-go*: the CF4 Wiener-filter velocity field is
    curl-suppressed (vorticity <= 0.6% of shear), estimator validated by an injected
    solid-body curl mode. A true Hoffman-Ribak CR vorticity posterior remains blocked.
    Is "WF-prior no-go, not detection" the honest reading?
  - K1 -- global look-elsewhere p = 0.097 (SMICA) / 0.121 (Commander, ~25% method
    dependence -- reported side by side, not averaged) under an *isotropic LambdaCDM null*;
    the full FFP10/NPIPE E2E-systematics null is not yet bound (a noise-augmented null is
    built and ready to run). Is the partial-discharge framing honest? Is the look-elsewhere
    max-scan valid?
  - PR08-006 -- the joint comparator: rank-2 = ONE measured sector (Omega_tilt) + ONE
    partial sector (Sigma^2), with `W^2,Omega_k` fail-closed (never zeroed), no collapsed
    scalar. Is the fail-closed assembly correct, and the one-full-plus-one-partial honest?

## Hard boundaries (flag any violation as a fatal overclaim)

- an identified Bianchi family or detected anisotropic geometry from any scalar/axis/feature;
- native-solver validation for any external/proxy transfer output;
- a globally significant low-ell anomaly *detection* (K1 is local/look-elsewhere, LambdaCDM-null, not E2E);
- a physical-vorticity claim from K6 (it is a structural no-go on a curl-suppressed field);
- a MIO diagnostic used as posterior odds / model weight / evidence; any scalar->family promotion.

## Required output

1. **Verdict:** PASS | MINOR REVISIONS | MAJOR REVISIONS | REJECT / NOT READY.
2. **Minimal defensible claim:** one conservative paragraph -- what can honestly be stated today.
3. **Novelty assessment:** is the rank-aware comparator + two-sector no-go + conditional
   EGS-type theorems a genuine, publishable contribution without the native solver? What is
   the strongest honest framing?
4. **Fatal blockers:** only those that invalidate a stated result.
5. **Theorem audit** (table `Item | Status | Issue | Required fix`): hypotheses, limits, constants.
6. **Statistics audit** (table): K1 null/look-elsewhere; K5 coverage/cosmic-variance/selection;
   K6 no-go logic; PR08-006 rank + fail-closed; identifiability rank argument.
7. **Constructive roadmap:** the smallest set of additional analyses/tests that would make
   each result publishable (e.g. what the FFP10/NPIPE E2E run must show; CF4 mock realism;
   theorem generalizations).
8. **Claim-tier corrections:** exact wording to downgrade/remove; and **claims that are safe** as stated.

Cite `path` (and line/figure) for every finding. If a part is acceptable, say so in one sentence.
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
        print("missing research-evaluation package output")
        return 1
    if man_path.read_text(encoding="utf-8") != _render_manifest(payload):
        print("stale research-evaluation manifest")
        return 1
    if prompt_path.read_text(encoding="utf-8") != render_prompt():
        print("stale research-evaluation prompt")
        return 1
    if zip_path.read_bytes() != _build_zip_bytes(repo_root, payload, entries):
        print("stale research-evaluation zip")
        return 1
    print(f"up-to-date {zip_path}")
    return 0


def _command_from_args(argv: Sequence[str] | None) -> str:
    args = [a for a in (sys.argv[1:] if argv is None else list(argv)) if a not in ("--check", "--dry-run")]
    return " ".join(["python", "scripts/build_research_evaluation_package.py", *args]).strip()


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
    payload, entries = build_payload(
        repo_root=repo_root, output_zip=args.output_zip, output_manifest=args.output_manifest,
        output_prompt=args.output_prompt, generating_command=_command_from_args(argv),
    )
    if payload["failed_gates"]:
        print("research-evaluation package failed gates: " + ", ".join(payload["failed_gates"]))
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
