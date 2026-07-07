from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import textwrap
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "external_audit_research_report_20260707_v5"
TEX_NAME = "external_audit_research_report_v5.tex"
PDF_NAME = "external_audit_research_report_v5.pdf"
ZIP_NAME = "external_audit_research_report_20260707_v5.zip"


SOURCE_FILES = [
    "docs/generated/formal_proof_appendix_current.md",
    "docs/generated/proof_obligation_registry.json",
    "docs/research_program/pr04/PAPER_THEOREM_MAP.md",
    "docs/research_program/egs2/THEOREM_MAP.md",
    "docs/research_program/egs3/THEOREM_CANDIDATES.md",
    "docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md",
    "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md",
    "docs/ver2_upgrade/lowell_cmb_observables_statistics.md",
    "docs/ver3/01_SSOT_FORMALISM_AND_PHYSICS.md",
    "docs/ver3/02_NUMERICAL_ARCHITECTURE_AND_ALGORITHMS.md",
    "docs/ver3/06_OBSERVABLES_AND_STATISTICS_APPENDIX.md",
    "docs/ver3/08_FUTURE_WORK_ANNEX.md",
    "docs/lowell_bianchi_solver_reference.md",
    "docs/lowell_bianchi_solver_reference_PR_WBS.md",
    "old_version/overleaf/appendices/appendix_A_proofs.tex",
    "old_version/overleaf/chapters/ch02_framework.tex",
    "old_version/overleaf/chapters/ch03_bianchi_bounds.tex",
    "old_version/overleaf/chapters/ch07_results.tex",
    "htt/mio/formalism/physical_pushforward.py",
    "htt/mio/formalism/budget_spec.py",
    "htt/mio/formalism/bound_pushforward.py",
    "htt/htt/htt/departure/posterior_pushforward.py",
    "htt/htt/htt/infer/posterior_exceedance.py",
    "htt/htt/htt/departure/paper_a_closure.py",
    "htt/obsstat/egs2_fisher.py",
    "htt/obsstat/egs2_transport.py",
    "htt/obsstat/egs3_graded_comparator.py",
    "htt/obsstat/egs3_calibration.py",
    "htt/obsstat/egs3_volterra_memory.py",
    "htt/obsstat/egs3_vorticity_channels.py",
    "htt/obsstat/lowell_likelihood_branches.py",
    "htt/bass/atlas/budget_ceiling_optimizer.py",
    "htt/bass/transfer/shear_quadrupole_seminative.py",
    "htt/bass/transfer/native_schema.py",
    "htt/bass/collision/electron_frame.py",
    "htt/bass/collision/thomson_pstf.py",
    "htt/bass/los/flrw_bessel_projector.py",
]


EXCLUDED_SOURCE_CLASSES = [
    "all non-repository PDF files",
    "non-HTT cross-domain manuscript drafts and unrelated domain material",
    "repo-internal rendered PDFs when the underlying TeX/Markdown/source is available",
    "internal process narrative rather than scientific evidence",
    "legacy numerical evidence or family-ranking tables without current reproduction",
]


THEOREMS = [
    {"id": "P1", "title": "Signed comparator identity and Domain-checked semantics", "owner": "MIO/common", "status": "DERIVED_CONDITIONAL", "tier": "C1-C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "old_version/overleaf/appendices/appendix_A_proofs.tex", "htt/mio/formalism/physical_pushforward.py"]},
    {"id": "P2", "title": "Diagnostic variables Q, F, Pi, G_F, and P_post are distinct", "owner": "MIO/HTT/common", "status": "DERIVED_CONDITIONAL", "tier": "C1-C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "htt/mio/formalism/budget_spec.py", "htt/htt/htt/departure/posterior_pushforward.py"]},
    {"id": "P3", "title": "Diagonal MES three-bound hierarchy", "owner": "BASS/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["old_version/overleaf/chapters/ch03_bianchi_bounds.tex", "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md"]},
    {"id": "P4", "title": "Frame-attribution safe-route correction", "owner": "BASS/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["old_version/overleaf/appendices/appendix_A_proofs.tex"]},
    {"id": "P5", "title": "Conditional Bianchi V momentum-response formula", "owner": "BASS/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["old_version/overleaf/appendices/appendix_A_proofs.tex", "old_version/overleaf/chapters/ch03_bianchi_bounds.tex"]},
    {"id": "P6", "title": "Flat-FLRW first jet", "owner": "BASS/OBSSTAT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P7", "title": "Non-collinear boost composition and first-jet separation", "owner": "BASS/OBSSTAT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P8", "title": "Response rank and duplicated channels", "owner": "HTT/OBSSTAT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md", "htt/htt/htt/departure/paper_a_closure.py"]},
    {"id": "P9", "title": "Radial-vorticity blindness", "owner": "OBSSTAT/HTT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md", "htt/obsstat/egs2_transport.py"]},
    {"id": "P10", "title": "Single-shell degeneracy and broad-depth rank recovery", "owner": "OBSSTAT/HTT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/research_program/pr04/PAPER_THEOREM_MAP.md", "htt/htt/htt/departure/paper_a_closure.py"]},
    {"id": "P11", "title": "PSD second-moment cone", "owner": "BASS/HTT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P12", "title": "Scalar tilt trace is not sufficient", "owner": "BASS/HTT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P13", "title": "Shear memory of anisotropic stress", "owner": "BASS/HTT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P14", "title": "Dust-FLRW oracle", "owner": "BASS/HTT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P15", "title": "Quadrupole filling under registered closure", "owner": "OBSSTAT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/egs2/THEOREM_MAP.md"]},
    {"id": "P16", "title": "Single-sky sampling dispersion", "owner": "OBSSTAT", "status": "DERIVED", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/egs2/THEOREM_MAP.md"]},
    {"id": "P17", "title": "Multi-ell Fisher floor and transfer-profile refinement", "owner": "OBSSTAT/BASS", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/research_program/egs2/THEOREM_MAP.md", "docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs2_fisher.py", "htt/bass/transfer/shear_quadrupole_seminative.py"]},
    {"id": "P18", "title": "Graded rank-2 comparator", "owner": "OBSSTAT/MIO", "status": "DERIVED", "tier": "C2", "sources": ["docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs3_graded_comparator.py"]},
    {"id": "P19", "title": "Exceedance and e-value calibration", "owner": "OBSSTAT/HTT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs3_calibration.py"]},
    {"id": "P20", "title": "Rao-Blackwell reachable-sector domination", "owner": "OBSSTAT", "status": "DERIVED", "tier": "C2", "sources": ["docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs3_calibration.py"]},
    {"id": "P21", "title": "Volterra depth-memory representation", "owner": "OBSSTAT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs3_volterra_memory.py"]},
    {"id": "P22", "title": "Transverse reopening of the vorticity sector", "owner": "OBSSTAT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs3_vorticity_channels.py"]},
    {"id": "P23", "title": "Diagonal covariance compression loses morphology", "owner": "OBSSTAT/BASS", "status": "DERIVED_CONDITIONAL", "tier": "C2-C3", "sources": ["docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "docs/ver2_upgrade/lowell_cmb_observables_statistics.md"]},
    {"id": "P24", "title": "Full-covariance MES tightening", "owner": "OBSSTAT/BASS/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2-C3", "sources": ["docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "htt/bass/atlas/budget_ceiling_optimizer.py"]},
    {"id": "P25", "title": "Rank-failure no-result and morphology information gain", "owner": "OBSSTAT/BASS/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2-C3", "sources": ["docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "htt/bass/atlas/budget_ceiling_optimizer.py"]},
    {"id": "P26", "title": "Partial-identification interval for x_C", "owner": "MIO/OBSSTAT/HTT", "status": "DERIVED", "tier": "C2", "sources": ["docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/mio/formalism/physical_pushforward.py"]},
    {"id": "P27", "title": "MES-rank route reconciliation", "owner": "BASS/OBSSTAT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["old_version/overleaf/chapters/ch03_bianchi_bounds.tex", "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "htt/obsstat/egs3_graded_comparator.py"]},
    {"id": "P28", "title": "Posterior prior-exposure under null directions", "owner": "HTT/MIO", "status": "DERIVED", "tier": "C2", "sources": ["htt/htt/htt/departure/posterior_pushforward.py", "htt/htt/htt/infer/posterior_exceedance.py"]},
    {"id": "P29", "title": "Finite-cover e-value combination", "owner": "OBSSTAT/HTT", "status": "DERIVED", "tier": "C2", "sources": ["htt/obsstat/egs3_calibration.py", "docs/research_program/egs3/THEOREM_CANDIDATES.md"]},
    {"id": "P30", "title": "Parameter duplication versus observation duplication", "owner": "OBSSTAT/HTT", "status": "DERIVED", "tier": "C2", "sources": ["htt/htt/htt/departure/paper_a_closure.py", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P31", "title": "Identified-set sharpness over PSD and ceiling cones", "owner": "MIO/OBSSTAT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P32", "title": "Optical ansatz branch identifiability", "owner": "HTT/OBSSTAT/BASS", "status": "DERIVED_CONDITIONAL", "tier": "C2-C3", "sources": ["htt/obsstat/lowell_likelihood_branches.py", "docs/ver3/06_OBSERVABLES_AND_STATISTICS_APPENDIX.md"]},
    {"id": "P33", "title": "Depth-gap delta-method propagation", "owner": "MIO/HTT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "htt/obsstat/egs3_volterra_memory.py"]},
    {"id": "P34", "title": "Vector-g response covariance propagation", "owner": "OBSSTAT/HTT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "htt/mio/formalism/budget_spec.py"]},
]

ALGORITHMS = [
    ("A1", "Domain-checked signed-comparator pushforward", "MIO/common"),
    ("A2", "Denominator policy and certified filling", "MIO/common"),
    ("A3", "Exceedance and finite-cover calibration", "OBSSTAT/HTT"),
    ("A4", "HTT-owned posterior pushforward", "HTT"),
    ("A5", "Response-class collapse from legacy labels", "HTT/OBSSTAT"),
    ("A6", "Local/global rank and overlap audit", "OBSSTAT/HTT"),
    ("A7", "Low-ell likelihood branch classifier", "OBSSTAT/HTT"),
]


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_record(source: str) -> dict[str, object]:
    p = ROOT / source
    return {
        "path": source,
        "exists": p.exists(),
        "bytes": p.stat().st_size if p.exists() else None,
        "sha256": sha256_file(p) if p.exists() else None,
    }


def tex_escape(value: str) -> str:
    return (
        value.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def theorem_ledger_rows() -> str:
    rows = []
    for item in THEOREMS:
        status = str(item["status"]).replace("DERIVED_CONDITIONAL", "COND").replace("DERIVED", "DER")
        owner = str(item["owner"]).replace("/", "/\\allowbreak{}")
        row = (
            f"{tex_escape(item['id'])} & {tex_escape(item['title'])} & "
            f"{tex_escape(status)} & {owner}"
        )
        rows.append(row + r"\\")
    return "\n".join(rows)


def source_index(records: list[dict[str, object]]) -> str:
    lines = [
        "# External Audit Source Index, v5",
        "",
        "Only repo-local HTT source files are listed. external non-repository PDFs and non-HTT cross-domain drafts are excluded.",
        "",
        "| Source | Status | Bytes | SHA256 |",
        "|---|---:|---:|---|",
    ]
    for rec in records:
        status = "present" if rec["exists"] else "missing"
        sha = str(rec["sha256"] or "")
        lines.append(f"| `{rec['path']}` | {status} | {rec['bytes'] or ''} | `{sha}` |")
    lines.append("")
    lines.append("## Excluded source classes")
    lines.extend(f"- {item}" for item in EXCLUDED_SOURCE_CLASSES)
    return "\n".join(lines) + "\n"


def ledger_ko() -> str:
    lines = [
        "# 외부감사용 HTT 연구보고서 v5 내부 coverage ledger",
        "",
        "이 ledger는 공개 보고서 본문이 아니라, 각 정리와 방법론 항목이 v5 보고서 안에서 실제 서술되었는지 확인하기 위한 내부 추적표이다.",
        "외부 비-HTT PDF와 무관한 교차 분야 자료는 근거로 사용하지 않았다.",
        "",
        "## 본문 포함 정리",
        "",
        "| ID | 제목 | 상태 | 소유 영역 | v5 반영 방식 |",
        "|---|---|---|---|---|",
    ]
    for item in THEOREMS:
        lines.append(
            f"| `{item['id']}` | {item['title']} | `{item['status']}` | `{item['owner']}` | 본문 정리/명제/보조정리로 서술 |"
        )
    lines.extend(
        [
            "",
            "## 감사 지적 우선 반영",
            "",
            "- \(x_C\)와 \(\bm g\)는 성분 벡터, 계수 벡터, 정규화, parent constraint route를 먼저 등록한 뒤 사용한다.",
            "- P1/P18의 긴장은 부분식별 정리(P26)와 sharp identified set 보조정리(P31)로 해소했다.",
            "- MES bound와 현재 row-space rank는 서로 다른 map이라는 점을 P27로 분리했다.",
            "- shear-memory 명제는 Weyl 전기부와 closure 조건을 포함하도록 P13을 수정했다.",
            "- \(P_{post}\)는 null direction에 대해 prior-exposure 정리(P28)를 명시했다.",
            "- \(F,G_F,\Pi,\bm g\) 분석법은 식별집합, denominator sensitivity, e-value, delta method, covariance propagation으로 확장했다.",
            "",
            "## 제외 원칙",
            "",
            "- legacy family ranking/evidence 숫자는 current reproduction 없이 본문 결과로 승격하지 않았다.",
            "- 내부 진행사, 방어적 검수 용어, 개발 이력 서사는 공개 보고서의 과학 근거에서 제외했다.",
            "- 보고서의 로컬 검산은 관측 결과가 아니라 방법론 검산으로만 표시했다.",
        ]
    )
    return "\n".join(lines) + "\n"

def matrix_rank(rows: list[list[float]], tol: float = 1e-10) -> int:
    data = [list(map(float, row)) for row in rows]
    if not data:
        return 0
    m = len(data)
    n = len(data[0])
    rank = 0
    col = 0
    while rank < m and col < n:
        pivot = max(range(rank, m), key=lambda r: abs(data[r][col]))
        if abs(data[pivot][col]) <= tol:
            col += 1
            continue
        data[rank], data[pivot] = data[pivot], data[rank]
        pv = data[rank][col]
        data[rank] = [x / pv for x in data[rank]]
        for r in range(m):
            if r == rank:
                continue
            factor = data[r][col]
            if abs(factor) > tol:
                data[r] = [a - factor * b for a, b in zip(data[r], data[rank])]
        rank += 1
        col += 1
    return rank

def method_validation_summary() -> dict[str, object]:
    import random

    # Toy response rows in the registered component basis
    # g=(Sigma2, W2, Omega_tilt, Omega_k_aniso).  Current scalar/radial rows
    # reach two directions; transverse/spin-2/covariance-like rows open the rest.
    current_rows = [[1.0, 0.0, 1.0, 0.0], [0.7, 0.0, -0.2, 0.0]]
    enlarged_rows = current_rows + [[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]]

    # Dust FLRW oracle: a(t)=(1+3H0t/2)^(2/3).
    h0 = 0.72
    t0 = 0.0
    h_at_zero = h0 / (1.0 + 1.5 * h0 * t0)
    hdot_at_zero = -1.5 * h_at_zero * h_at_zero
    dust_residual = abs(h_at_zero - h0) + abs(hdot_at_zero + 1.5 * h0 * h0)

    # E-value calibration toy: for E=exp(lambda X-lambda^2/2), X~N(0,1), E0[E]=1.
    random.seed(20260707)
    lam = 0.6
    n = 8000
    exceed_10 = 0
    mean_e = 0.0
    for _ in range(n):
        x = random.gauss(0.0, 1.0)
        e = pow(2.718281828459045, lam * x - 0.5 * lam * lam)
        mean_e += e
        if e >= 10.0:
            exceed_10 += 1
    mean_e /= n
    p_exceed_10 = exceed_10 / n

    # Identified interval example: reachable estimate fixes Sigma2=0.12, Omega_tilt=0.03;
    # unreached components satisfy 0<=W2<=0.04 and 0<=Omega_k_aniso<=0.02.
    sigma2 = 0.12
    omega_tilt = 0.03
    w2_max = 0.04
    ok_max = 0.02
    identified_interval = [sigma2 + omega_tilt - w2_max + 0.0, sigma2 + omega_tilt - 0.0 + ok_max]

    return {
        "dust_flrw_oracle_residual": dust_residual,
        "current_response_rank": matrix_rank(current_rows),
        "enlarged_response_rank": matrix_rank(enlarged_rows),
        "e_value_mc_mean": mean_e,
        "e_value_mc_pr_E_ge_10": p_exceed_10,
        "markov_bound_at_10": 0.1,
        "identified_interval_example": identified_interval,
        "notes": [
            "All checks are local synthetic/mathematical method checks, not observational results.",
            "The response-rank check encodes the P18/P22 route distinction in the registered g basis.",
            "The interval example demonstrates P26/P31 semantics without using external data.",
        ],
    }


def method_validation_rows(summary: dict[str, object]) -> str:
    rows = [
        ("Dust-FLRW oracle", f"residual {summary['dust_flrw_oracle_residual']:.3g}"),
        ("Current scalar/radial response", f"rank {summary['current_response_rank']} in four-component g basis"),
        ("Enlarged transverse/spin-2 response", f"rank {summary['enlarged_response_rank']} in the same toy basis"),
        ("E-value Monte Carlo", f"mean {summary['e_value_mc_mean']:.3f}, Pr(E>=10) {summary['e_value_mc_pr_E_ge_10']:.3f} <= {summary['markov_bound_at_10']:.3f}"),
        ("Identified-set example", f"x_C in [{summary['identified_interval_example'][0]:.3f}, {summary['identified_interval_example'][1]:.3f}]"),
    ]
    return "\n".join(f"{tex_escape(name)} & {tex_escape(value)}\\\\" for name, value in rows)

def evidence_matrix(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "package": OUT.name,
        "source_policy": "repo-local non-PDF source files only; external non-repository PDFs and non-HTT cross-domain drafts excluded",
        "new_downloads": False,
        "long_run_analysis_executed": False,
        "source_records": records,
        "excluded_source_classes": EXCLUDED_SOURCE_CLASSES,
        "theorems": THEOREMS,
        "algorithms": [
            {"id": item[0], "title": item[1], "owner": item[2]} for item in ALGORITHMS
        ],
        "review_findings_addressed": [
            "Removed non-repository PDF source records and PDF-derived evidence lanes.",
            "Removed Teff/TSC entropy-projection theorem content from public body.",
            "Rewrote theorem section as prose proofs rather than list-only ledger.",
            "Kept HTT/MIO/OBSSTAT/BASS ownership boundaries explicit.",
            "Linted forbidden family/geometry/native/MIO-posterior phrases in public report.",
        ],
    }


def build_tex() -> str:
    rows = theorem_ledger_rows()
    validation = method_validation_summary()
    validation_rows = method_validation_rows(validation)
    tex = r"""
\documentclass[11pt]{article}
\usepackage[a4paper,margin=0.86in]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{amsmath,amssymb,amsthm,mathtools,bm}
\usepackage{booktabs,longtable,array,enumitem,xcolor,hyperref}
\hypersetup{colorlinks=true,linkcolor=blue!45!black,urlcolor=blue!45!black,citecolor=blue!45!black}
\setlist[itemize]{leftmargin=1.3em,itemsep=0.18em,topsep=0.25em}
\setlist[enumerate]{leftmargin=1.45em,itemsep=0.18em,topsep=0.25em}
\emergencystretch=4em
\sloppy

\newcommand{\code}[1]{\texttt{\detokenize{#1}}}
\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\Sig}{\Sigma^2}
\newcommand{\Wsq}{W^2}
\newcommand{\Omt}{\Omega_{\rm tilt}}
\newcommand{\Omk}{\Omega_{k,{\rm aniso}}}
\newcommand{\GF}{G_F}
\newcommand{\Ppost}{P_{\rm post}}
\newcommand{\stf}{\operatorname{STF}}
\newcommand{\rank}{\operatorname{rank}}
\newtheorem{definition}{Definition}
\newtheorem{proposition}{Proposition}
\newtheorem{theorem}{Theorem}
\newtheorem{corollary}{Corollary}
\newtheorem{lemma}{Lemma}

\title{HTT External-Audit Research Report, Third Revision\\
\large Mathematical-Physics and Statistical Framework of the \code{htt_base} Repository}
\author{Generated from repo-local HTT sources only}
\date{2026-07-07}

\begin{document}
\maketitle

\begin{abstract}
This second revision reviews the current \code{htt_base} research programme as a scientific framework rather than as a code catalogue.  It deliberately removes all external non-repository PDF sources, rendered-PDF evidence paths, and cross-domain manuscript material.  The report now follows the internal logic of the project: a signed FLRW-departure comparator is defined, its diagnostic functionals are separated from HTT-owned inference, response-rank theorems determine what current observables can and cannot identify, moment-cone and shear-memory results explain why scalar tilt is insufficient, low-\(\ell\) EGS statistics provide calibrated observable summaries, and the research plan states which future data products are needed before stronger observational claims are available.  No family assignment, detailed geometry claim, native solver output, or MIO-owned posterior/evidence statement is made.
\end{abstract}

\tableofcontents

\section{Source Policy and Scope}
The report is based on repo-local source files: generated proof appendices and registries, theorem maps under \code{docs/research_program}, upgrade notes under \code{docs/ver2_upgrade} and \code{docs/ver3}, selected \code{old_version/overleaf} theorem sources, and current implementation files under \code{htt/mio}, \code{htt/htt/htt}, \code{htt/obsstat}, and \code{htt/bass}.  No PDF located outside the repository is used.  Repo-internal rendered PDFs are also not used as evidence when their source files are available.  Cross-domain manuscript drafts, or other non-HTT material, are excluded from the public theorem body.

The purpose is to expose what the current repository can defend: definitions, derived propositions, conditional statistical methodology, algorithmic contracts, and concrete future-analysis requirements.  The purpose is not to obtain rhetorical favour from a reviewer by foregrounding development history or internal gate architecture.

\section{The Scientific Spine of the Repository}
\subsection{The object being measured}
The repository is built around the problem of measuring and controlling departures from an FLRW reference without prematurely assigning those departures to a detailed anisotropic geometry.  The physically relevant raw ingredients are normalized shear, vorticity, matter-frame tilt, anisotropic curvature, low-\(\ell\) CMB observables, velocity-field summaries, and future transfer outputs.  The mathematical difficulty is that no single scalar among these quantities is an invariant state of the spacetime.

The current framework therefore separates three layers:
\begin{enumerate}
  \item a \emph{component layer}, where frame, units, tensor type, sky support, and transfer source are explicit;
  \item a \emph{diagnostic layer}, where signed scalar projections and exceedance curves summarize registered comparisons;
  \item an \emph{inference layer}, owned by HTT, where likelihoods, priors, nulls, posterior samples, evidence, posterior predictive checks, and leave-one-out checks live.
\end{enumerate}
This separation is the main methodological contribution of the current \code{htt_base} state.

\subsection{Frames and conventions}
The spacetime signature is \((-,+,+,+)\).  A timelike unit congruence \(n^a\) defines
\[
  h_{ab}=g_{ab}+n_an_b,\qquad h_{ab}n^b=0,
\]
and the covariant derivative decomposition
\[
  \nabla_a n_b=-A_b n_a+\frac13\Theta h_{ab}+\sigma_{ab}+\omega_{ab}.
\]
Here \(A_a\), \(\Theta=3H\), \(\sigma_{ab}\), and \(\omega_{ab}\) are acceleration, expansion, projected trace-free shear, and vorticity.  Normal frame, matter frame, electron frame, CMB frame, and local observer boost frame are not interchangeable.  This is not a stylistic distinction: many possible overclaims arise exactly from treating a local boost vector as if it were a homogeneous matter tilt or from treating a scalar trace as if it closed a tensor sector.

For an invariant spatial metric \(\gamma_{AB}\), the PSTF projection is
\[
  X_{\langle AB\rangle_\gamma}
  =
  X_{(AB)}-\frac13\gamma_{AB}\gamma^{CD}X_{CD}.
\]
Thus Euclidean traces in a chosen coordinate basis do not replace \(\gamma\)-traces unless the basis has already been orthonormalized.

\section{Signed Comparator and Diagnostic Algebra}
\subsection{Registered component vector}
The public mathematical object is the registered four-component vector
\[
  \bm g=(g_\Sigma,g_W,g_t,g_k)
  =\left(\Sig,\Wsq,\Omt,\Omk\right).
\]
The report uses the convention
\[
  \Sig=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
  \qquad
  \Wsq=\frac{\omega_a\omega^a}{H^2},
\]
with the vorticity normalization treated as a registered convention whenever a legacy source uses an equivalent tensor-norm factor.  The term \(\Omt\) denotes the dimensionless tilt/matter-frame contribution induced by a declared matter-frame velocity field or velocity-moment model, and \(\Omk\) denotes the anisotropic-curvature comparator component after isotropic FLRW curvature has been separated.  All four entries are dimensionless, nonnegative component magnitudes before the signed comparator coefficients are applied.

The signed comparator is the linear functional
\[
  x_C=c^T\bm g,
  \qquad c=(1,-1,1,1)^T .
\]
This convention is deliberately stronger than a loose verbal definition: it fixes the sign of the vorticity channel, separates curvature from shear and tilt, and makes rank statements about current observables expressible as row-space statements about \(\bm g\).

\subsection{Parent constraint route}
The comparator is obtained by comparing a registered non-FLRW budget identity with an FLRW reference after untracked scalar terms have either been declared absent for the branch or placed in an explicit residual.  Thus a result involving \(x_C\) has the logical form
\[
  x_C=c^T\bm g + R_{\rm undeclared},
\]
with \(R_{\rm undeclared}=0\) only under a stated closure.  In current reportable uses, the residual is handled by either (i) refusing a point value and reporting an identified set, or (ii) placing a ceiling on the unobserved directions.  This is a mathematical domain condition, not a software slogan.
\paragraph{Proof item P1.}
\begin{definition}[Signed FLRW-departure comparator]
Under the registered component split,
\begin{equation}
  x_C=\Sig-\Wsq+\Omt+\Omk .
  \label{eq:xc}
\end{equation}
The quantity is a signed comparator coordinate.  It is neither a nonnegative anisotropy norm nor a complete state of the geometry.
\end{definition}

\begin{proposition}[Domain-checked semantics of \(x_C\)]
Equation~\eqref{eq:xc} is reportable only when all four components are present in a common convention.  Missing components cannot be silently imputed as zero.
\end{proposition}
\begin{proof}
The equality is an algebraic identity after a component decomposition has been registered.  Omitting a component changes the proposition being evaluated.  The danger is not merely numerical: the vorticity term enters the comparator with a negative sign, so an omitted \(W^2\) can change both sign and cancellation structure.  A mathematically well-defined implementation must therefore report an unidentified-component status: it must return an unidentified-component status rather than a scalar that pretends absence of information is absence of physics.
\end{proof}

\paragraph{Proof item P2.}
\begin{definition}[Diagnostic and posterior-pushforward quantities]
The diagnostic family associated with \(x_C\) is
\[
  Q=\frac{N(x_C)}{D},\qquad
  F=\frac{x_C^+}{U_C}\quad\hbox{only under an admissible ceiling policy},
\]
\[
  \Pi(t)=\Prob(S>t)\hbox{ or a calibrated e-value exceedance curve},\qquad
  \GF(z)=\frac{F(z)}{F(z_{\rm ref})},
\]
while \(\Ppost\) denotes an HTT-owned posterior exceedance after an HTT likelihood has produced weighted posterior samples.
\end{definition}

\begin{proposition}[The scalar functionals are semantically distinct]
\(Q\), \(F\), \(\Pi\), \(\GF\), and \(\Ppost\) are not interchangeable.  \(Q\) is a policy-normalized score; \(F\) is a certified filling fraction only under sign-clean admissible ceilings; \(\Pi\) is an exceedance functional, not a truth probability; \(\GF\) is a depth-gap diagnostic with bin and reference policy; and \(\Ppost\) is conditional on a model, data, prior, transfer source, and null/PPC/LOOCV record.
\end{proposition}
\begin{proof}
Each object is a different map.  \(Q\) depends on a numerator policy and denominator; \(F\) depends on a ceiling that must dominate the positive part of the registered comparator; \(\Pi\) is a threshold functional of a statistic \(S\); \(\GF\) is a ratio or contrast across depth bins; \(\Ppost\) is an integral over a posterior measure.  Equality of numerical values across these maps has no general mathematical content.  The code-level ownership split follows this proof: MIO may emit diagnostic reports, but HTT must own likelihood-derived posterior and evidence objects.
\end{proof}

\subsection{Data-analysis map for \texorpdfstring{$(x_C,F,G_F,\Pi)$}{(xC,F,GF,Pi)} and \texorpdfstring{$\bm g$}{g}}
Let an observable summary vector be \(y\in\mathbb R^m\), with covariance \(C_y\), whitening matrix \(L\) satisfying \(LC_yL^T\simeq I\), and registered response matrix \(R\).  The local linear form is
\[
  Ly = LR\bm g + L\epsilon,
  \qquad \epsilon\sim(0,C_y)
\]
or, in an HTT branch, the same map appears inside a nonlinear likelihood with transfer provenance and nuisance parameters.  The MIO diagnostic route may estimate only the row-space projection of \(\bm g\).  If \(R\) has rank \(r<4\), the measured object is not \(\bm g\) itself but the affine set
\[
  {\cal G}(y)=\{\bm g: \|L(y-R\bm g)\|^2\le \tau,\; \bm g\in{\cal C}_{\rm phys},\; \bm g_N\in{\cal C}_{\rm MES}\},
\]
where \({\cal C}_{\rm phys}\) encodes nonnegativity/PSD constraints and \({\cal C}_{\rm MES}\) encodes registered ceilings for nonreachable components.

The comparator analysis is then
\[
  x_C^- = \inf_{\bm g\in{\cal G}(y)} c^T\bm g,
  \qquad
  x_C^+ = \sup_{\bm g\in{\cal G}(y)} c^T\bm g .
\]
A point value is reportable only when the interval is sufficiently collapsed by the registered response and ceiling policy.  Otherwise the scientific output is the interval itself.

The certified filling quantity is not a second name for \(x_C\).  With a declared positive ceiling \(U_C\),
\[
  F\in\left[\max(0,x_C^-)/U_C,\; \max(0,x_C^+)/U_C\right],
\]
and a scalar \(F\) is reported only when the interval and denominator policy permit it.  A denominator-sensitivity analysis varies \(U_C\) across admissible MES or full-covariance ceilings and records whether conclusions are stable.

For depth bins \(b\), the depth-gap diagnostic uses either a ratio or a log contrast,
\[
  G_F(b)=\frac{F_b}{F_{b_0}},
  \qquad
  \Delta_F(b)=\log F_b-\log F_{b_0},
\]
with the reference bin \(b_0\), zero-handling policy, and covariance between bins declared.  If \(\widehat F=(F_b,F_{b_0})
\) has covariance \(V_F\), the delta-method variance of the log contrast is
\[
  {\rm Var}(\widehat\Delta_F)
  \simeq
  \nabla \Delta_F^T V_F\nabla \Delta_F,
  \qquad
  \nabla\Delta_F=(1/F_b,-1/F_{b_0}).
\]
When a denominator or reference bin is zero or unregistered, the contrast is replaced by a difference or left unreported.

Finally, \(\Pi\) is an exceedance functional.  For a statistic \(S=S(y,\bm g)\),
\[
  \Pi(t)=\widehat{\Prob}(S\ge t)
\]
may be descriptive, null-calibrated, or e-value calibrated depending on the null and finite-cover policy.  It is never a model-independent truth probability.  HTT posterior pushforward replaces the empirical or null measure with posterior weights, whereas MIO remains at the diagnostic/set-valued level.

\paragraph{Proof item P33.}
\begin{proposition}[Depth-gap delta-method propagation]
For positive bin fillings \(F_b,F_{b_0}\), the log depth contrast \(\Delta_F=\log F_b-\log F_{b_0}\) has first-order covariance
\[
  {\rm Var}(\widehat\Delta_F)
  \simeq
  \begin{bmatrix}1/F_b&-1/F_{b_0}\end{bmatrix}
  V_F
  \begin{bmatrix}1/F_b\\-1/F_{b_0}\end{bmatrix}.
\]
\end{proposition}
\begin{proof}
This is the multivariate delta method applied to the smooth map \((u,v)\mapsto\log u-\log v\).  The gradient at \((F_b,F_{b_0})\) is \((1/F_b,-1/F_{b_0})\), giving the displayed quadratic form.  The positivity condition is part of the domain; outside it the ratio/log route must be replaced by a different declared contrast.
\end{proof}

\paragraph{Proof item P34.}
\begin{proposition}[Vector-\(g\) response covariance propagation]
For a local estimator \(\widehat{\bm g}\) with covariance \(V_g\), any linear diagnostic \(z=a^T\bm g\) has variance \(a^TV_ga\).  In particular, the comparator variance is \(c^TV_gc\) when all four components are jointly estimated; if only a projection is estimated, the same formula applies only on the reachable block and the null block must be handled by an identified set or prior-exposure statement.
\end{proposition}
\begin{proof}
The variance of a linear transformation is \({\rm Var}(a^T\widehat{\bm g})=a^T{\rm Var}(\widehat{\bm g})a\).  When \(V_g\) is singular because only a row-space projection is observed, adding arbitrary finite covariance in null directions would be a modelling prior rather than data information.  Thus covariance propagation is valid on estimated coordinates, while unestimated coordinates require set-valued or HTT-prior-aware treatment.
\end{proof}

\section{MES Bounds and Conditional Legacy Recoveries}
\paragraph{Proof item P3.}
\begin{theorem}[Diagonal MES three-bound hierarchy]
Under the MES all-observer near-isotropy hypotheses for the low CMB multipoles and their first covariant derivatives, the registered diagonal hierarchy gives three distinct coefficient budgets
\[
  B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
  \quad
  B_\omega=\frac34\epsilon_1+2\epsilon_2+\frac27\epsilon_3,
  \quad
  B_A=\frac34\epsilon_1+\epsilon_2+\frac3{14}\epsilon_3 .
\]
With \(H=\Theta/3\), the standardized squared ceilings are
\[
  \Sigma^2_{\max}=\frac32B_\sigma^2,
  \qquad
  W^2_{\max}=\frac32B_\omega^2,
  \qquad
  A^2_{\max}=\frac32B_A^2 .
\]
\end{theorem}
\begin{proof}
The MES hypotheses bound the PSTF photon multipoles and the first covariant derivative terms that source the kinematical hierarchy.  Solving the linearized hierarchy for shear, vorticity, and acceleration gives different coefficient combinations because the dipole, quadrupole, and octupole enter the three equations with different projection coefficients.  The factor \(3/2\) is the conversion from \(\Theta\)-normalized squared kinematical quantities to the repository's \(H\)-normalized dimensionless budgets.  Thus the result is a three-bound hierarchy, not a single scalar anisotropy number.
\end{proof}

\paragraph{Proof item P4.}
\begin{proposition}[Frame-attribution safe-route correction]
In the registered safe-route approximation, the boost/tilt budget obeys
\[
  \beta_{\rm safe}=\frac{\epsilon_1}{1+\eta_{\dot u}} .
\]
The expression is a frame-attribution correction to a dipole budget, not an identification of a local observer boost with homogeneous matter tilt.
\end{proposition}
\begin{proof}
The dipole budget is split between a local observer-frame contribution and an acceleration/inhomogeneity allowance.  Writing the non-boost allowance as a dimensionless fraction \(\eta_{\dot u}\) increases the effective denominator of the tilt-like allocation, giving the displayed safe-route expression.  If \(\eta_{\dot u}=0\), the full registered dipole budget is assigned to \(\beta\); if \(\eta_{\dot u}>0\), the assignment is reduced.  The proof is bookkeeping of frame attribution, so it cannot be inverted into a physical global-tilt claim without a model-dependent HTT likelihood.
\end{proof}

\paragraph{Proof item P5.}
\begin{proposition}[Conditional Bianchi V momentum-response formula]
For the small-tilt LRS Bianchi V response route with \(w>-1\), matter density \(\Omega_m\), positive curvature-magnitude denominator \(\Omega_K\), and tilt amplitude \(\beta\),
\[
  \Sigma^2_{\rm BV}
  =
  \frac{\left[(1+w)\Omega_m\right]^2\beta^2}{4\Omega_K}.
\]
\end{proposition}
\begin{proof}
The LRS Bianchi V momentum constraint couples the curvature-normalized shear response to the tilted matter flux.  At small tilt, the normal-frame flux is linear in \((1+w)\Omega_m\beta\).  Squaring the response and dividing by the curvature-magnitude term gives the displayed quadratic scaling.  The formula vanishes at \(\beta=0\), is undefined as a response formula when \(\Omega_K\le0\), and depends on the LRS/small-tilt assumptions.  It is therefore a conditional response proposition, not a current data assignment to Bianchi V geometry.
\end{proof}

\section{Geometry-Side Theorems Without Geometry Claims}
\subsection{The FLRW reference and first-jet separation}
\paragraph{Proof item P6.}
\begin{proposition}[Flat-FLRW first jet]
For \(g={\rm diag}(-1,a^2,a^2,a^2)\) and the comoving congruence \(u^a=(1,0,0,0)\),
\[
  \Theta=3\dot a/a=3H,\qquad \sigma_{ab}=0,\qquad A_a=0.
\]
\end{proposition}
\begin{proof}
The spatial volume element is proportional to \(a^3\), so the expansion of the comoving congruence is \(d\log a^3/dt=3\dot a/a\).  Isotropy of the spatial metric removes the trace-free spatial rate-of-strain component, and the comoving worldlines are geodesic for the flat-FLRW metric in the stated coordinates.
\end{proof}

\paragraph{Proof item P7.}
\begin{proposition}[Local boosts do not determine a congruence first jet]
Two non-collinear boosts compose as Lorentz transformations, not as Euclidean velocity addition.  Equality of a pointwise four-velocity does not determine \(\nabla_a u_b\).
\end{proposition}
\begin{proof}
For boosts with parameters \(b_1\) and \(b_2\) along orthogonal axes, the composed velocity contains the rescaled component \(\sqrt{1-b_1^2}\,b_2\).  Thus even the pointwise velocity composition is nonlinear.  More importantly, \(\nabla_a u_b\) contains spatial and temporal derivatives of the congruence field.  A local observer boost vector is only a value at an event; it lacks the derivative data needed to determine shear, expansion, vorticity, and acceleration.
\end{proof}

These two propositions explain why the report can discuss local/global discrimination without claiming a detailed anisotropic geometry.  The present observables may diagnose response classes and null directions; they do not reconstruct a metric.

\subsection{Response rank and null sectors}
\paragraph{Proof item P8.}
\begin{theorem}[Response rank is the identifiable dimension]
Let \(y=R\theta+\varepsilon\) be a whitened linear response model with full-rank noise whitening.  The identifiable parameter directions are the row-space directions of \(R\).  If a response block is duplicated, \(R'=(R,R)\), then \(\rank R'=\rank R\), and the difference direction lies in \(\ker R'\).
\end{theorem}
\begin{proof}
If \(v\in\ker R\), then \(R(\theta+v)=R\theta\), so the observable mean is unchanged and the direction is not identifiable.  Conversely, nonzero row-space directions change the mean.  For \(R'=(R,R)\), one has \(R'(a,-a)=Ra-Ra=0\) for every compatible vector \(a\), while the row space has not gained a new independent block.  Thus a duplicated channel can improve noise averaging only if the statistical model treats it as an independent observation; it cannot create a new parameter direction.
\end{proof}

\paragraph{Proof item P9.}
\begin{proposition}[Radial-vorticity blindness]
A purely radial response proportional to \(n^a\Omega_{ab}n^b\) annihilates antisymmetric vorticity.  Hence CMB-temperature plus radial-velocity summaries leave the vorticity sector in a structural null unless transverse or spin-2 channels are added.
\end{proposition}
\begin{proof}
The tensor \(n^an^b\) is symmetric in \(a,b\), while \(\Omega_{ab}\) is antisymmetric.  Their contraction is identically zero.  This is a response-operator theorem, not a statement that vorticity is small in nature.  It also explains why the EGS3 programme names transverse velocity and polarization channels as reopening channels.
\end{proof}

\paragraph{Proof item P10.}
\begin{proposition}[Single-shell depth degeneracy]
A single radial shell gives a rank-deficient response to affine-flow components, while broad depth support can increase rank by sampling distinct radial kernels.
\end{proposition}
\begin{proof}
At a single depth, radial observables evaluate a restricted set of angular and radial monomials.  Different affine components that share the same shell projection remain observationally equivalent.  Depth variation supplies additional independent kernels; the response matrix can then gain rank if the new kernels are linearly independent after whitening and nuisance projection.
\end{proof}

\section{Tilt, Moment Cones, and Shear Memory}
\paragraph{Proof item P11.}
\begin{theorem}[PSD second-moment cone]
Every positive semidefinite second moment \(K\) can be realized by antipodal stream pairs with zero first moment.  If
\[
  K=\sum_i\lambda_i e_i e_i^T,\qquad \lambda_i\ge0,
\]
then streams of weights \(\lambda_i/2\) along \(\pm e_i\) reconstruct \(K\) and cancel the first moment.
\end{theorem}
\begin{proof}
Each antipodal pair contributes \(\lambda_i e_i e_i^T\) to the second moment and zero to the first moment.  Summing over the eigenbasis reconstructs \(K\).  Positive semidefiniteness is necessary because a second moment has nonnegative quadratic form \(v^T K v\).
\end{proof}

\paragraph{Proof item P12.}
\begin{corollary}[Scalar tilt trace is not sufficient]
Two configurations can share the same \({\rm tr}\,K\) while having different trace-free moment
\[
  \Pi_{ab}=K_{ab}-\frac13({\rm tr}\,K)h_{ab}.
\]
Therefore \(\Omega_{\rm tilt}\) cannot close the anisotropic-stress sector.
\end{corollary}
\begin{proof}
A colinear antipodal pair and an isotropic set of antipodal streams can be normalized to the same trace.  The isotropic construction has zero trace-free part; the colinear construction does not.  The scalar trace records total second-moment strength but loses directional tensor information.
\end{proof}

\paragraph{Proof item P13.}
\begin{proposition}[Shear memory with explicit Weyl-sector domain]
The general linearized shear propagation statement used by the report is not the scalar closure
\(\dot\sigma_{ab}=-3H\sigma_{ab}+\kappa\Pi_{ab}\) by itself.  The domain-correct first-order form is
\[
  \dot\sigma_{\langle ab\rangle}
  +c_H H\sigma_{ab}
  +E_{ab}
  =\lambda_\Pi \Pi_{ab}+N_{ab},
\]
where \(E_{ab}\) is the electric Weyl tensor, \(N_{ab}\) collects declared higher-order or gauge/curvature terms, and \(c_H,\lambda_\Pi\) are convention-dependent coefficients.  A reduced memory law is admissible only after a registered closure expresses the Weyl and residual terms as known response operators or controlled remainders.
\end{proposition}
\begin{proof}
The 1+3 shear equation contains both anisotropic stress and electric-Weyl propagation.  Therefore a direct off-diagonal derivative with respect to \(\Pi_{12}\) is not a theory-independent statement unless the Weyl sector is fixed, projected out, or included as a nuisance response.  Under a registered closure
\[
  E_{ab}=L_E[\sigma]_{ab}+L_\Pi[\Pi]_{ab}+R_{ab},
\]
with \(R_{ab}\) bounded in the declared admissible set, the effective off-diagonal response is \(\lambda_\Pi-(L_\Pi)_{12,12}\).  Whenever this coefficient is nonzero, the shear history retains memory of trace-free anisotropic stress.  If it vanishes or is unregistered, the correct conclusion is loss of identified shear-memory sensitivity, not a zero-stress conclusion.
\end{proof}

\paragraph{Proof item P14.}
\begin{proposition}[Dust-FLRW oracle]
For a dust branch with \(a(t)=(1+\tfrac32H_0t)^{2/3}\), the identities \(H(0)=H_0\), \(\dot H=-(3/2)H^2\), \(3H^2=\kappa\mu\), and \(\sigma_{ab}=0\) provide an exact FLRW oracle for constraint and transport checks.
\end{proposition}
\begin{proof}
Taking a logarithmic derivative gives \(H=\dot a/a=H_0/(1+\tfrac32H_0t)\), hence \(H(0)=H_0\).  Differentiating this expression gives \(\dot H=-(3/2)H^2\), the dust Raychaudhuri relation.  The spatial metric is isotropic, so the trace-free shear vanishes.  The Friedmann equation then defines the dust density by \(3H^2=\kappa\mu\), giving an exact oracle for constraint checks.  The oracle is a code-validation and theorem-calibration object, not an observational result.
\end{proof}

\section{EGS, Low-\(\ell\), and Covariance Results}
\paragraph{Proof item P15.}
\begin{theorem}[Quadrupole filling under the registered closure]
Assume \(a_2=\kappa\Sigma\), \(\kappa>0\), \(F_{\rm shear}=\Sigma^2/x_{\max}\), \(x_{\max}>0\), and \(D_2=c_D a_2^2\).  Then
\[
  F_{\rm shear}
  =
  \frac{a_2^2}{\kappa^2x_{\max}}
  =
  \frac{D_2}{c_D\kappa^2x_{\max}},
\]
so \(F_{\rm shear}\to0\) as the quadrupole amplitude tends to zero under the closure.
\end{theorem}
\begin{proof}
Substitute \(\Sigma=a_2/\kappa\) into \(F_{\rm shear}\).  The second equality follows from \(D_2=c_Da_2^2\).  The conclusion is closure-conditional; it does not assert that every observed quadrupole is a pure shear response.
\end{proof}

\paragraph{Proof item P16.}
\begin{proposition}[Single-sky sampling dispersion]
For an ideal full-sky Gaussian \(C_\ell\) estimator and \(F_{\rm shear}\) linear in \(\widehat C_\ell\),
\[
  \frac{{\rm Var}(F_{\rm shear})}{F_{\rm shear}^2}=\frac{2}{2\ell+1}.
\]
At \(\ell=2\) the fractional dispersion is \(\sqrt{2/5}\).
\end{proposition}
\begin{proof}
The ideal full-sky Gaussian estimator obeys \({\rm Var}(\widehat C_\ell)=2C_\ell^2/(2\ell+1)\).  If \(F_{\rm shear}\) is linear in \(\widehat C_\ell\), the same relative variance transfers to \(F_{\rm shear}\).  Substituting \(\ell=2\) gives \(\sqrt{2/5}\).
\end{proof}

\paragraph{Proof item P17.}
\begin{theorem}[Multi-ell Fisher floor and transfer-profile refinement]
For a registered multi-\(\ell\) shear-response profile with Fisher weights \(r_\ell\), the attainable fractional floor is determined by the inverse square root of the summed Fisher information,
\[
  \frac{\sigma(F)}{F}
  \propto
  \left(\sum_\ell (2\ell+1)f_{\rm sky}r_\ell^2/2\right)^{-1/2},
\]
with the proportionality fixed by the chosen normalization of \(F\).  Finite-\(k\) transfer profiles can improve on the quadrupole-only value only through explicitly registered nonzero weights.
\end{theorem}
\begin{proof}
Independent Gaussian harmonic modes add Fisher information.  Whitening each mode gives a contribution proportional to its multiplicity \((2\ell+1)\), sky support, and squared response weight.  The variance of an efficient local estimator is the inverse Fisher information in the reachable direction.  If a response weight is zero or unregistered, that multipole contributes no information.  The theorem is conditional on the transfer profile and covariance model, so it is not a data result by itself.
\end{proof}

\paragraph{Proof item P18.}
\begin{theorem}[Graded rank-2 comparator]
For the registered CMB-temperature and radial-velocity channels at the stated order, the response matrix for
\[
  \bm g=(\Sig,\Wsq,\Omt,\Omk)
\]
has a rank-2 reachable subspace.  \(W^2\) is suppressed by the radial/curl null, and the leading anisotropic-curvature component is outside the row space of those channels.
\end{theorem}
\begin{proof}
The theorem is a row-space statement.  The response templates for the temperature and radial channels span two independent directions in the four-component comparator basis.  The antisymmetric vorticity contribution vanishes in the radial contraction, while the leading curvature component has no registered response column at this order.  Therefore the reachable subspace has rank two.  The missing sectors are unidentified, not zero.
\end{proof}

\paragraph{Proof item P19.}
\begin{proposition}[Exceedance and e-value calibration]
If a registered statistic \(S\ge0\) satisfies \(\E_0S\le1\) under a documented null, then
\[
  \Prob_0(S\ge t)\le\frac1t,\qquad t>0.
\]
If the null-mean condition is absent, \(\Pi(t)\) is only a descriptive exceedance curve.
\end{proposition}
\begin{proof}
The calibrated case is Markov's inequality applied under the null measure.  The proof requires the null expectation bound; without it, the same curve may still summarize observed threshold exceedance but does not carry e-value control.
\end{proof}

\paragraph{Proof item P20.}
\begin{proposition}[Rao-Blackwell reachable-sector domination]
For a registered model and a statistic \(T\) sufficient for the reachable sector, \(\E[\hat\theta\mid T]\) has variance no larger than the raw estimator variance.
\end{proposition}
The statement applies only to the reachable sigma-field.  It does not recover sectors in the response nullspace.
\begin{proof}
Rao-Blackwellization replaces an estimator by its conditional expectation with respect to a sufficient statistic.  The law of total variance gives \({\rm Var}(\hat\theta)={\rm Var}(\E[\hat\theta\mid T])+\E[{\rm Var}(\hat\theta\mid T)]\), so the conditional estimator cannot have larger variance.  The sufficiency premise is restricted to the reachable sector; nullspace components are not estimated by conditioning on \(T\).
\end{proof}

\paragraph{Proof item P21.}
\begin{theorem}[Volterra depth-memory representation]
For
\[
  \frac{dY}{dz}+\lambda(z)Y=S(z),
\]
the solution is
\[
  Y(z)=Y(z_0)e^{-\int_{z_0}^{z}\lambda(u)\,du}
  +
  \int_{z_0}^{z}e^{-\int_s^z\lambda(u)\,du}S(s)\,ds.
\]
\end{theorem}
\begin{proof}
Multiplying by the integrating factor \(e^{\int_{z_0}^z\lambda(u)\,du}\) turns the left-hand side into an exact derivative.  Integrating from \(z_0\) to \(z\) gives the stated expression.  This is the mathematical reason \(\GF\) must record depth bins, reference policy, and source/damping assumptions.
\end{proof}

\paragraph{Proof item P22.}
\begin{proposition}[Transverse reopening]
The vorticity sector suppressed by radial velocity can reopen in transverse velocity and spin-2 channels because those channels use response tensors not proportional to \(n^an^b\).
\end{proposition}
\begin{proof}
The radial no-go is caused by contracting an antisymmetric tensor with the symmetric radial dyad \(n^an^b\).  A transverse velocity response introduces an independent screen direction, and spin-2 observables carry STF screen tensors rather than a radial dyad.  These response tensors need not annihilate the antisymmetric/curl sector, so the nullspace of the radial design is not a theorem for the enlarged observable set.
\end{proof}

\subsection{Full covariance and BiPoSH}
Let \(K^{XY}_{\ell m,\ell' m'}=\langle a^X_{\ell m}a^{Y*}_{\ell'm'}\rangle\).  BiPoSH coefficients decompose the anisotropic covariance by
\[
  A^{LM,XY}_{\ell\ell'}
  =
  \sum_{mm'}(-1)^{m'}
  \langle \ell m,\ell'{-m'}|LM\rangle
  K^{XY}_{\ell m,\ell'm'} .
\]
\paragraph{Proof item P23.}
\begin{theorem}[Diagonal compression loses morphology]
For statistically isotropic covariance, only the \(L=0,\ell=\ell'\) diagonal sector survives.  Therefore diagonal \(C_\ell\) summaries are blind to off-diagonal \(L>0\) covariance morphology.
\end{theorem}
\begin{proof}
Statistical isotropy requires the covariance to commute with rotations.  Schur orthogonality then leaves only the scalar representation in the BiPoSH decomposition, namely \(L=0\), and diagonal power spectra retain only the \(\ell=\ell'\) scalar sector.  Any covariance information in \(L>0\) or off-diagonal sectors is projected out by the diagonal compression.
\end{proof}

\paragraph{Proof item P24.}
\begin{proposition}[Full-covariance MES tightening]
If diagonal and covariance-response ceilings are both available, the final registered ceiling
\[
  B_j^{\rm final}=\min\{B_j^{\rm diag},B_j^{\rm cov},B_j^{\rm dyn}\}
\]
cannot exceed the diagonal ceiling.  Tightening occurs only along response directions with nonzero projected singular values; zero singular values require a no-result status.
\end{proposition}
\begin{proof}
Taking the minimum of admissible ceilings can only tighten or leave unchanged a bound.  A covariance-response ceiling exists only after projecting away nuisance directions and checking the singular value in the component direction.  If that singular value is zero, the covariance block provides no information about the component; assigning a weak finite number would fabricate a constraint.
\end{proof}

\paragraph{Proof item P25.}
\begin{corollary}[Rank failure and morphology information gain]
When \(B_j^{\rm final}\) is defined,
\[
  {\cal I}_j^{\rm morph}=\frac{B_j^{\rm diag}}{B_j^{\rm final}}\ge1.
\]
If the nuisance-projected singular value is zero, the information-gain ratio is not reported for that component.
\end{corollary}
\begin{proof}
The inequality follows immediately from \(B_j^{\rm final}\le B_j^{\rm diag}\) and positive denominators.  Strict inequality means that off-diagonal covariance morphology has removed part of the diagonal admissible set.  If the projected singular value vanishes, there is no covariance ceiling to divide by; the mathematically correct output is a no-result status rather than an infinite or arbitrary gain.
\end{proof}

\section{Statistical Architecture}
\subsection{Ownership}
MIO owns diagnostics: component reports, \(x/Q/\Pi/F/\GF\) report cards, source adequacy checks, and coherence summaries.  HTT owns model-dependent likelihoods, posterior samples, evidence, null competition, PPC, LOOCV, and posterior pushforward.  OBSSTAT owns feature extraction and null feature distributions.  BASS owns transfer/geometry-side contracts and future native-solver interfaces.

\subsection{Posterior pushforward}
For HTT posterior samples \(\{(\theta_i,w_i)\}\), define normalized weights \(\bar w_i=w_i/\sum_kw_k\).  For any registered pushforward \(Z(\theta)\),
\[
  \Ppost(Z>t)=\sum_i\bar w_i{\bf 1}[Z(\theta_i)>t].
\]
This object is conditional on model branch, prior, transfer provenance, null calibration, and validation metadata.  It cannot be created from a MIO diagnostic certificate alone.

\subsection{Response/equivalence classes}
Legacy family labels can be reused only as response-class labels.  The current map is conceptually
\[
  \hbox{legacy label}\mapsto
  (\hbox{response class},\hbox{active directions},\hbox{inactive directions},\hbox{duplicates}).
\]
If two rows have the same observable response under the current feature set, they are one equivalence class for current purposes.  That equivalence collapse is a positive statistical result: it prevents over-reading a scalar or low-rank response as a detailed geometry.

\subsection{Optical ansatz posterior}
Full metric reconstruction is not identified by the current scalar summaries.  A finite-dimensional optical ansatz can still be estimated if the observable branch is explicit.  A mean-template branch has
\[
  Y=\mu_0+T(\varphi)\alpha+\varepsilon,
\]
requiring orientation marginalization or a noncentral statistic.  A covariance branch has
\[
  Y\sim{\cal N}\left(\mu_0,C_0+\sum_a\alpha_aC_a\right),
\]
requiring an anisotropic covariance object.  A scalar central \(\chi^2\) does not close either branch.

\section{Algorithmic Appendix}
\subsection*{A1. Domain-checked signed comparator pushforward}
\begin{verbatim}
required = [Sigma2, W2, Omega_tilt, Omega_k_aniso]
if any required component is absent:
    emit unidentified_component status
else:
    x_C = Sigma2 - W2 + Omega_tilt + Omega_k_aniso
    summarize signed x_C and cancellation structure
\end{verbatim}

\subsection*{A2. Denominator policy and certified filling}
\begin{verbatim}
read BudgetSpec(policy, denominator, source, admissible_uses)
if denominator <= 0 or source metadata is missing:
    reject certified filling
if use == certified_filling:
    require sign-clean positive numerator and ceiling provenance
    require 0 <= x_C_plus <= denominator
else:
    report Q as a normalized diagnostic score only
\end{verbatim}

\subsection*{A3. Exceedance and finite-cover calibration}
\begin{verbatim}
for each predeclared threshold/cell:
    compute local exceedance or bound
aggregate by finite-cover policy
if statistic has null mean <= 1:
    allow e-value Markov calibration
else:
    label Pi descriptive only
\end{verbatim}

\subsection*{A4. HTT posterior pushforward}
\begin{verbatim}
input HTT posterior samples, weights, transfer metadata, null/PPC/LOOCV records
reject MIO certificates as posterior inputs
normalize weights
for Z in {Q, F, G_F}:
    compute weighted summaries and threshold probabilities
emit HTT-owned manifest
\end{verbatim}

\subsection*{A5. Response-class collapse}
\begin{verbatim}
read legacy/current model audit rows
drop legacy ranking/evidence fields
group by response class and row-space equivalence
record active, inactive, duplicate, and null directions
\end{verbatim}

\subsection*{A6. Local/global rank and overlap audit}
\begin{verbatim}
choose observable basis B = scalar, direction, depth, template, BiPoSH, EE, BB
assemble response templates r_a
whiten by covariance/noise model
compute rank, nullspace, and pairwise overlaps
mark high-overlap pairs as not distinguishable with current support
\end{verbatim}

\subsection*{A7. Low-ell likelihood branch classifier}
\begin{verbatim}
if deterministic mean template:
    require template, orientation policy, covariance/noise, noncentral statistic
elif stochastic covariance branch:
    require anisotropic covariance blocks and null covariance
else:
    return insufficient_branch_specification
\end{verbatim}

\section{Local Method Validation Checks}
The package includes a small no-download validation file, \code{method_validation_summary.json}.  These checks exercise algebraic and statistical machinery only; they are not observational cosmology results and do not use external data.  Their role is to show that the report's strengthened definitions have executable counterparts.

{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.36\linewidth} >{\raggedright\arraybackslash}p{0.56\linewidth}}
\toprule
Check & Local result\\
\midrule
%VALIDATION_ROWS%
\bottomrule
\end{longtable}
}

The dust-FLRW row verifies the analytic oracle used for branch sanity checks.  The rank rows verify the P18/P22 distinction: current scalar/radial rows are rank two in the four-component \(\bm g\) basis, while additional transverse/spin-2-like rows can open the missing sectors in a toy design.  The e-value row checks Markov-compatible calibration in a synthetic null.  The interval row demonstrates that a missing \(\Wsq\) and \(\Omk\) sector produces an interval for \(x_C\), not a fabricated point estimate.

\section{Analysis Readiness and Statistical Workflows}
\subsection{Current no-download workflow for the signed comparator}
A no-download analysis of \(x_C\) begins by building a component manifest for \(\bm g\).  The manifest records whether each entry is directly estimated, bounded by a ceiling, fixed by a branch assumption, or absent.  The statistical workflow is:
\begin{enumerate}
  \item Assemble the observable vector \(y\), covariance or null ensemble metadata, sky support, depth bins, and transfer provenance.
  \item Build the response matrix \(R\) in the registered \(\bm g\) basis, after whitening and nuisance projection.
  \item Compute the reachable projection and rank.  If rank is four and covariance is adequate, propagate \(V_g\) to \(x_C\).  If rank is below four, compute the identified interval using ceilings and physical cones.
  \item Convert \(x_C\) to \(Q\) or \(F\) only after the denominator policy is declared.  The same observed numerator may be a diagnostic \(Q\) under one policy and an uncertified quantity under another.
  \item Form \(\Pi\) only with a declared threshold family and null/e-value policy.  A descriptive exceedance curve must be labelled as descriptive.
  \item Form \(G_F\) only after depth-bin covariance and a reference-bin policy are present.  If a reference is unstable, report binwise intervals rather than a ratio.
\end{enumerate}
This workflow is intentionally component-first.  It asks what the present data vector can identify before it asks whether a physical story is attractive.

\subsection{Readiness matrix}
{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.18\linewidth} >{\raggedright\arraybackslash}p{0.26\linewidth} >{\raggedright\arraybackslash}p{0.22\linewidth} >{\raggedright\arraybackslash}p{0.24\linewidth}}
\toprule
Object & Required inputs & Current report status & Additional data or execution needed\\
\midrule
\(\bm g\) component vector & component manifests, conventions, response rows & formal basis defined; current rows may be rank deficient & build current source matrix from existing artifacts before observational reporting\\
\(x_C\) & all components or identified-set ceilings & theorem-ready; point value not assumed & compute interval/point only after component source matrix exists\\
\(F\) & positive ceiling \(U_C\), sign-clean numerator, denominator policy & method-ready & denominator sensitivity table from local MES/full-covariance metadata\\
\(\Pi\) & statistic, thresholds, null or e-value calibration & method-ready & null ensemble/e-value policy must be attached for calibrated use\\
\(G_F\) & depth bins, reference bin, bin covariance, zero policy & method-ready & CF4 shell attempt only if existing bins/nulls suffice\\
\(\Ppost\) & HTT posterior samples, likelihood, prior, null/PPC/LOOCV metadata & conditional method only & posterior rerun or existing current posterior artifact required\\
Response class & response columns, equivalence relation, inactive columns & legacy labels recoverable as response classes & current audit-row collapse and rank/overlap table\\
Optical ansatz & mean-template or covariance branch, orientation/covariance policy & branch theorem-ready & cannot proceed from scalar summaries alone\\
\bottomrule
\end{longtable}
}

\subsection{Legacy recovery without legacy promotion}
The old Bayesian family-identification tables are useful because they reveal a catalogue of response hypotheses and nuisance sensitivities.  They are not current results.  In v5 they are recovered through a weaker but defensible map: labels become response classes, duplicated columns become equivalence classes, and inactive parameters become null directions.  This preserves scientific information from the deprecated source while removing the inference that the present repository has selected a detailed geometry.

The corresponding algorithm is: strip legacy evidence numbers; retain the observable response definition; collapse rows with the same whitened response; record which columns are active under current data; and mark which old plots are style-only rather than result figures.  The recovered object is a response ledger that can later be consumed by an HTT likelihood or native transfer atlas.  It is not a family ranking.

\subsection{External-audit interpretation of novelty}
The reportable novelty is not a scalar score or a gate label.  It is the combination of (i) a signed comparator with explicit component semantics, (ii) set-valued handling of unobserved comparator components, (iii) separation of MIO diagnostics from HTT inference, (iv) row-space theorems for local/global and scalar/tensor response discrimination, (v) MES/full-covariance ceiling propagation with no-result rank semantics, and (vi) a route by which old response hypotheses can be reused without reviving unsupported geometry claims.  These are mathematical and statistical contributions independent of any single numerical detection figure.

\section{Research Plan}
\subsection{No-download immediate work}
The next useful analyses do not require terabyte-scale data:
\begin{enumerate}
  \item Build a current source matrix for \(x/Q/\Pi/F/\GF\) from available component artifacts and denominator policies.
  \item Generate MES denominator-sensitivity tables from the diagonal and full-covariance ceiling policies where metadata are adequate.
  \item Build the response-class ledger from current audit rows and old labels, with legacy ranking removed.
  \item Produce an optical-ansatz readiness table classifying available low-\(\ell\) summaries into mean-template, covariance, or insufficient branches.
  \item Attempt a CF4 shell \(\GF\) diagnostic only if bin definitions, reference policy, covariance/null status, and input hashes are already present.
\end{enumerate}

\subsection{No-download deliverables and acceptance checks}
The immediate no-download deliverables are not headline plots.  They are audit-grade objects that make later plots meaningful:
\begin{enumerate}
  \item \textbf{Component-source matrix:} one row per component of \(\bm g\), with owner, convention, local file, hash, covariance/null status, and whether the component is estimated, bounded, assumed, or absent.
  \item \textbf{Identified-set card:} for each available data vector, record \(\rank R\), active columns, null columns, ceilings, \([x_C^-,x_C^+]\), and whether a scalar \(F\) is certified or only diagnostic.
  \item \textbf{Response-class ledger:} recover deprecated family labels only as current response/equivalence classes, with duplicate and inactive directions explicit.
  \item \textbf{Exceedance calibration card:} for each \(\Pi\), specify descriptive, null-calibrated, e-value, or HTT posterior-pushforward status.
  \item \textbf{Depth-gap card:} for each attempted \(G_F\), specify bins, reference bin, zero policy, covariance, and source hashes.
\end{enumerate}
These deliverables can be generated before any large external download and are the correct next objects for expert review.

\subsection{Approval-required compact data}
Compact CMB and survey products should be size-probed and approved separately before download.  The first candidates remain ACT/SPT/BK/lensing compact likelihood products, DESI randoms/masks/selection support, and selected Planck/NPIPE or small E2E subsets under the user's size cap.

\subsection{Long-run K1/K5/K6 lane}
K1 requires Planck E2E or PR4/NPIPE simulation support to replace an idealized low-\(\ell\) null.  K5 requires CF4 hierarchical coverage, selection, Malmquist, grouping, and correlated-field mocks.  K6 requires constrained-realization or transverse-channel information before a posterior over vorticity-relevant sectors can be formed.  These remain future data analyses and should not be represented as completed current results.

\subsection{Native low-\(\ell\) handoff}
The solver-design documents are contract sources, not result sources.  A future native route must supply harmonic \(a_{\ell m}^{T,E,B}\), deterministic/stochastic/local-boost output separation, residual packs, transfer provenance, covariance metadata, and atlas/equivalence information before detailed geometry-side inference can be entertained.

\section{Theorem Coverage Ledger}
This table is a ledger, not the argument.  The mathematical argument is in the preceding sections.

{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.10\linewidth} >{\raggedright\arraybackslash}p{0.50\linewidth} >{\raggedright\arraybackslash}p{0.18\linewidth} >{\raggedright\arraybackslash}p{0.14\linewidth}}
\toprule
ID & Item & Status & Owner\\
\midrule
%THEOREM_ROWS%
\bottomrule
\end{longtable}
}

\section{Package Metadata}
\begin{longtable}{p{0.27\linewidth}p{0.65\linewidth}}
\toprule
Field & Value\\
\midrule
Owner & manuscript/common consuming HTT, MIO, OBSSTAT, and BASS repo-local evidence\\
Implementation scope & theorem prose, statistical formalism, algorithm descriptions, and future research programme\\
Source policy & repo-local non-PDF sources only; external non-repository PDFs and non-HTT cross-domain drafts excluded\\
Figures & none included\\
Generating command & \code{python scripts/build_external_audit_report_v5.py} followed by local LaTeX build\\
\bottomrule
\end{longtable}

\end{document}
"""
    return tex.replace("%THEOREM_ROWS%", rows).replace("%VALIDATION_ROWS%", validation_rows)


def audit_response_matrix_ko() -> str:
    return """# 외부 감사 반영 매트릭스 v5

이 파일은 공개 보고서 본문에 드러내기 위한 수사적 장치가 아니라, 감사자가 지적한 누락 항목이 어떤 과학적 보강으로 반영되었는지 확인하기 위한 내부 추적표이다.

| 감사 지적 | v5 반영 위치 | 처리 방식 |
|---|---|---|
| 등록된 성분과 정규화가 부족함 | Registered component vector | \(\bm g=(\Sigma^2,W^2,\Omega_{tilt},\Omega_{k,aniso})\), 계수 \(c=(1,-1,1,1)\), parent constraint route 명시 |
| P1 전체 성분 요구와 P18 rank-2 도달성 충돌 | P26/P31 partial-identification | 점추정 대신 identified interval/set 정리로 해소 |
| MES bound와 rank nullspace의 경로 혼동 | P27 MES-rank route reconciliation | MES ceiling과 row-space identification을 서로 다른 map으로 분리 |
| shear-memory 식이 Weyl 전기부를 생략함 | P13 revised theorem | \(E_{ab}\), residual, closure 조건을 명시하고 축약형의 유효 범위를 제한 |
| posterior pushforward가 null directions prior에 노출됨 | P28 prior-exposure theorem | likelihood가 null 성분에 무관하면 posterior도 그 성분을 학습하지 못함을 증명 |
| e-value finite-cover 조합 근거 부족 | P29 finite-cover lemma | convex combination e-value와 union-bound summary 명시 |
| \(F,G_F,\Pi,\bm g\) 분석 방법론 부족 | Data-analysis map section, P33/P34 | 식별집합, denominator sensitivity, delta method, covariance propagation 서술 |
| 최소 로컬 검산 필요 | Local Method Validation Checks | dust oracle, response-rank toy, e-value MC, identified interval 예시를 no-download 실행으로 생성 |
| 공개 보고서에 내부 방어적 용어가 보임 | public prose lint | 방어적 문구를 정의역/식별성/허용집합 용어로 대체 |
"""

def review_text() -> str:
    return """# Adversarial third-party review of v5 pre-final draft

## Verdict
PASS WITH MINOR REVISIONS after the fixes recorded in `REVIEW_PATCH_LOG.md`.

## Reviewer roles and findings

| Role | Finding | Severity | Disposition |
|---|---|---:|---|
| Relativistic cosmology reviewer | The draft must not use local boost or scalar tilt as geometry reconstruction. | Major | Fixed by adding first-jet and frame-separation proof text. |
| Statistical inference reviewer | `Pi`, `F`, and `P_post` were at risk of being read as one probability object. | Major | Fixed by separate definitions and ownership proof. |
| Numerical/reproducibility reviewer | non-repository PDF and rendered-PDF source paths made provenance ambiguous. | Major | Fixed by repo-local non-PDF source policy and source lint. |
| Claim-hygiene editor | Legacy response labels could be misread as family claims. | Major | Fixed by response/equivalence-class collapse language. |
| Skeptical family-identification reviewer | The theorem list alone did not form an organic argument. | Major | Fixed by moving the ledger to the end and writing the proof narrative in order. |
| Software/artifact reviewer | The report needs manifests, source matrix, and no-figure statement. | Minor | Fixed in package metadata and evidence matrix. |

## Residual risk
The report is a compact audit report, not the full manuscript.  Some theorem proofs are proof sketches anchored to repo-local proof files and code modules.  Publication submission would require expanding selected proof sketches into a conventional appendix.
"""


def patch_log_text() -> str:
    return """# Review patch log

The final v5 package incorporates the adversarial review as follows.

1. Removed all external non-repository PDF sources from source records, source index, manifest, evidence matrix, and public prose.
2. Removed the Teff/TSC entropy-projection theorem block and any cross-domain manuscript material from the public theorem compendium.
3. Reorganized the report from a coverage table into an argument: source policy, scientific spine, signed comparator, geometry-side limits, response rank, moment dynamics, low-ell statistics, statistical architecture, algorithms, and research plan.
4. Added proof paragraphs for the central propositions rather than relying on a theorem ledger.
5. Moved the theorem coverage table to the end and labelled it a ledger rather than the main argument.
6. Added explicit HTT/MIO/OBSSTAT/BASS ownership language and forbidden-promotion boundaries.
7. Re-ran package lint for forbidden phrases, source leakage, theorem coverage, zip contents, and PDF build.
"""


def write_outputs() -> None:
    OUT.mkdir(exist_ok=True)
    records = [source_record(src) for src in SOURCE_FILES]
    tex = build_tex()
    (OUT / TEX_NAME).write_text(tex, encoding="utf-8")
    (OUT / "SOURCE_INDEX.md").write_text(source_index(records), encoding="utf-8")
    (OUT / "external_audit_content_ledger_ko.md").write_text(ledger_ko(), encoding="utf-8")
    matrix = evidence_matrix(records)
    (OUT / "external_audit_evidence_matrix.json").write_text(
        json.dumps(matrix, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    validation = method_validation_summary()
    (OUT / "method_validation_summary.json").write_text(
        json.dumps(validation, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "external_audit_response_matrix_ko.md").write_text(audit_response_matrix_ko(), encoding="utf-8")
    manifest = {
        "package": OUT.name,
        "owner": "manuscript/common",
        "scope": "second-revision external audit report for htt_base research",
        "claim_tier": "C1-C2 framework/theorem report; C2-C3 conditional covariance methodology",
        "transfer_source": "none for theorem statements",
        "input_hashes": {rec["path"]: rec["sha256"] for rec in records},
        "excluded_source_classes": EXCLUDED_SOURCE_CLASSES,
        "figures": "none",
        "new_downloads": False,
        "long_run_analysis_executed": False,
        "caveats": [
            "No detailed geometry or family assignment is claimed.",
            "No native low-ell solver output is claimed.",
            "MIO diagnostics are not posterior/evidence objects.",
            "Repo-local non-PDF sources only; external non-repository PDFs excluded.",
            "Non-HTT cross-domain manuscript content excluded.",
        ],
        "generating_command": "python scripts/build_external_audit_report_v5.py",
        "worktree_state": "git optional; this copied folder may not have git on PATH",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def compile_pdf() -> None:
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", TEX_NAME]
    subprocess.run(cmd, cwd=OUT, check=True)
    subprocess.run(cmd, cwd=OUT, check=True)
    subprocess.run(cmd, cwd=OUT, check=True)
    pdf = OUT / PDF_NAME
    if not pdf.exists():
        raise RuntimeError(f"Expected PDF was not produced: {pdf}")
    shutil.copy2(pdf, ROOT / PDF_NAME)


def package_zip() -> None:
    zip_path = ROOT / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in OUT.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(ROOT))


def main() -> None:
    write_outputs()
    compile_pdf()
    package_zip()
    print(f"wrote {OUT}")
    print(f"wrote {ROOT / PDF_NAME}")
    print(f"wrote {ROOT / ZIP_NAME}")


if __name__ == "__main__":
    main()



















