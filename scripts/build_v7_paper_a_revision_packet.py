#!/usr/bin/env python3
"""Generate the v7 Paper A text-revision packet.

This is a manuscript-facing instruction artifact, not a compiled paper claim. It
keeps audit/process language out of Paper A and records the exact claim-safe text
changes needed for P31/P35/P36/MES and the report-figure lane.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402


SCRIPT_PATH = "scripts/build_v7_paper_a_revision_packet.py"
OUT_JSON = REPO_ROOT / "docs/generated/v7_paper_a_revision_packet.json"
OUT_MD = REPO_ROOT / "docs/generated/v7_paper_a_revision_packet.md"
OUT_TEX = REPO_ROOT / "docs/generated/v7_paper_a_skeleton.tex"
SOURCE_FILES = (
    REPO_ROOT / "htt/obsstat/egs3_identified_set.py",
    REPO_ROOT / "htt/obsstat/egs3_gf_interval.py",
    REPO_ROOT / "docs/generated/v7_fortification_witnesses.json",
    REPO_ROOT / "docs/generated/k5_cf4_identified_interval_card.json",
)


REPLACEMENT_RULES = (
    {
        "target": "P31",
        "old_risk": "sharpness stated as physical realization",
        "replacement": "sharpness is for the registered convex component-box model; full physical realization is deferred",
        "claim_tier": "conditional",
        "required_caveat": "does not certify nonlinear GR realizability",
    },
    {
        "target": "P35",
        "old_risk": "known-covariance and simulation-estimated covariance thresholds mixed",
        "replacement": "split threshold policy into known_chi2 and estimated_covariance_f with n_sim metadata",
        "claim_tier": "diagnostic_only",
        "required_caveat": "finite-simulation covariance requires Hotelling/F threshold",
    },
    {
        "target": "P36",
        "old_risk": "strictness described as universal",
        "replacement": "joint interval is a subset of naive; strictness requires a shared-extrema conflict",
        "claim_tier": "conditional",
        "required_caveat": "aligned shared boxes collapse to equality",
    },
    {
        "target": "MES",
        "old_risk": "registered external coefficients over-read as rederived here",
        "replacement": "MES epsilon coefficients remain registered_external until a dedicated derivation seal exists",
        "claim_tier": "diagnostic_only",
        "required_caveat": "parent identity seal records rederived_here=false for MES coefficients",
    },
    {
        "target": "figures",
        "old_risk": "data figures read as inference claims",
        "replacement": "current report figures are appendix diagnostics unless matched null/covariance gates pass",
        "claim_tier": "diagnostic_only",
        "required_caveat": "no posterior odds, p-value, native solver output, or morphology-family promotion",
    },
)


PAPER_A_SECTIONS = (
    {
        "section": "Abstract",
        "instruction": "Frame the paper as an identifiability and diagnostic-methods paper, not as a detection paper.",
    },
    {
        "section": "Component-box theorem",
        "instruction": "State signed lower/upper component boxes and report open/all curvature branches.",
    },
    {
        "section": "Two-stage thresholds",
        "instruction": "Give separate known-covariance and estimated-covariance threshold policies.",
    },
    {
        "section": "Depth-gap interval propagation",
        "instruction": "State joint subset relation and the strict/equality criterion.",
    },
    {
        "section": "Data diagnostic appendix",
        "instruction": "Put K5/CF4 closure and current data figures in diagnostic appendix lanes until blockers clear.",
    },
)


FORBIDDEN_PROMOTIONS = (
    "native low-ell solver output from current transfer-conditional artifacts",
    "posterior odds from OBSSTAT/MIO diagnostic cards",
    "morphology-family promotion from scalar or interval diagnostics",
    "observed x_C result while any component remains PLUGIN/BLOCKED",
)


def _repo_relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _input_hashes(paths: tuple[Path, ...]) -> list[str]:
    return [f"{_repo_relative(path)}:{_sha256_file(path)}" for path in paths if path.is_file()]


def _config_hash(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, sort_keys=True, default=float)
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(*, generating_command: str) -> dict[str, Any]:
    hashes = _input_hashes(SOURCE_FILES)
    payload: dict[str, Any] = {
        "artifact_id": "manuscript.v7_paper_a_revision_packet",
        "artifact_path": _repo_relative(OUT_JSON),
        "schema": "htt.v7_paper_a_revision_packet.v1",
        "schema_version": "htt.v7_paper_a_revision_packet.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "external_audit_conditioned",
        "allowed_use": "external_audit",
        "created_by": SCRIPT_PATH,
        "git_commit": "content-addressed",
        "code_version": "content-addressed",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "config_hash": _config_hash(
            {
                "input_hashes": hashes,
                "replacement_rules": REPLACEMENT_RULES,
                "paper_a_sections": PAPER_A_SECTIONS,
                "forbidden_promotions": FORBIDDEN_PROMOTIONS,
                "version": "v7-paper-a-revision-packet",
            }
        ),
        "input_hashes": hashes,
        "caveats": [
            "Manuscript-facing revision packet only; not a compiled manuscript.",
            "No Paper A claim may outrun the generated v7 witness/card artifacts.",
            "Report data figures remain appendix diagnostics until promotion gates pass.",
        ],
        "required_gates": [
            "P31_component_box_scope",
            "P35_threshold_policy_split",
            "P36_strictness_iff",
            "MES_registered_external_caveat",
            "figure_lane_appendix_diagnostic",
        ],
        "passed_gates": [
            "P31_component_box_scope",
            "P35_threshold_policy_split",
            "P36_strictness_iff",
            "MES_registered_external_caveat",
            "figure_lane_appendix_diagnostic",
        ],
        "failed_gates": [
            "compiled_manuscript_not_claimed",
            "native_solver_absent",
            "measured_R_card_absent",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": "content-addressed",
        "replacement_rules": list(REPLACEMENT_RULES),
        "paper_a_sections": list(PAPER_A_SECTIONS),
        "forbidden_promotions": list(FORBIDDEN_PROMOTIONS),
        "tex_skeleton_path": _repo_relative(OUT_TEX),
        "statistics_definitions": {
            "purpose": "claim-safe Paper A wording and section skeleton",
            "source_witnesses": [
                "docs/generated/v7_fortification_witnesses.json",
                "docs/generated/k5_cf4_identified_interval_card.json",
            ],
        },
    }
    issues = validate_manifest_payload(
        payload,
        manifest_path=OUT_JSON.relative_to(REPO_ROOT),
        expected_artifact_path=_repo_relative(OUT_JSON),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid Paper A revision packet manifest: {rendered}")
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# v7 Paper A Revision Packet",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"config_hash: `{payload['config_hash']}`",
        f"generating_command: `{payload['generating_command']}`",
        "",
        "## Replacement Rules",
        "",
        "| Target | Replacement | Caveat |",
        "| --- | --- | --- |",
    ]
    for row in payload["replacement_rules"]:
        lines.append(
            f"| {row['target']} | {row['replacement']} | {row['required_caveat']} |"
        )
    lines.extend([
        "",
        "## Paper A Skeleton",
        "",
        "| Section | Instruction |",
        "| --- | --- |",
    ])
    for row in payload["paper_a_sections"]:
        lines.append(f"| {row['section']} | {row['instruction']} |")
    lines.extend([
        "",
        "## Forbidden Promotions",
        "",
    ])
    lines.extend(f"- {row}" for row in payload["forbidden_promotions"])
    return "\n".join(lines) + "\n"


def render_tex(payload: dict[str, Any]) -> str:
    del payload
    return r"""\documentclass[11pt]{article}
\usepackage{amsmath}
\usepackage{booktabs}
\title{Paper A Skeleton: Identified Component-Box Diagnostics for Low-Ell Anisotropy}
\author{HTT Collaboration Draft}
\date{Generated diagnostic skeleton; not a compiled-submission claim}
\begin{document}
\maketitle

\begin{abstract}
We present a claim-tiered identifiability and diagnostic framework. The current
artifacts are diagnostic and transfer-conditional; they do not use native low-ell
solver output and do not promote morphology-family conclusions.
\end{abstract}

\section{Component-Box Identified Sets}
The component vector is bounded by signed lower and upper boxes. The curvature
component is reported with both open and all-branch intervals.

\section{Two-Stage Thresholds}
Known-covariance chi-square thresholds and simulation-estimated covariance
Hotelling/F thresholds are separate policies with explicit metadata.

\section{Depth-Gap Interval Propagation}
The joint interval is a subset of the naive quotient interval. Strictness requires
a shared-extrema conflict; aligned shared boxes can collapse to equality.

\section{Diagnostic Data Appendix}
The K5/CF4 card is a pipeline-closure diagnostic while Sigma2, W2, and Omega-k
components remain blocked placeholders. Report figures are appendix diagnostics
unless matched-null and covariance gates pass.

\end{document}
"""


def _command_from_args(argv: list[str] | None) -> str:
    args = sys.argv[1:] if argv is None else argv
    return "venv/bin/python " + SCRIPT_PATH + (
        "" if not args else " " + " ".join(shlex.quote(arg) for arg in args)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if outputs are stale")
    args = parser.parse_args(argv)
    command = _command_from_args(argv)
    if args.check:
        command = "venv/bin/python " + SCRIPT_PATH
    payload = build_payload(generating_command=command)
    json_text = json.dumps(payload, indent=2, sort_keys=True, default=float) + "\n"
    md_text = render_markdown(payload)
    tex_text = render_tex(payload)
    if args.check:
        stale = []
        expected = ((OUT_JSON, json_text), (OUT_MD, md_text), (OUT_TEX, tex_text))
        for path, text in expected:
            if not path.is_file() or path.read_text(encoding="utf-8") != text:
                stale.append(_repo_relative(path))
        if stale:
            print("stale outputs: " + ", ".join(stale))
            return 1
        print("v7_paper_a_revision_packet outputs up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    OUT_TEX.write_text(tex_text, encoding="utf-8")
    print(f"wrote {_repo_relative(OUT_JSON)}")
    print(f"wrote {_repo_relative(OUT_MD)}")
    print(f"wrote {_repo_relative(OUT_TEX)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
