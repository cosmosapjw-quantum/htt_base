"""Build the v6 (Fourth Revision) external-audit research report.

REV-R146 review-response fork of ``build_external_audit_report_v5.py``. The v6
report answers the external re-review of v5: B1 (W^2 convention unified to the
registered omega_ab omega^ab/(6H^2) + the parent identity displayed + SymPy
seal), B2 (P26-P32 proof bodies written), M1'-M6' (two-stage tau semantics with
P35 Imbens-Manski coverage, empty/unbounded/ceiling-unfit branches + A8, P36
joint-feasible-set G_F propagation, audit-grade section-10 provenance,
Omega_tilt/Omega_k closed forms, F>1 clip), and the minor items (Fourth
Revision title, [x_C]_+ notation, MIO/HTT wording, P13/P26 status demotion,
lambda_2 rename, ledger body-section column, external literature context).

Determinism: GENERATED_AT is a fixed constant (byte-stable sidecars) and
``--check`` regenerates every text artifact in memory and diffs against disk
(the PDF/zip are excluded from the check: pdflatex embeds timestamps).
Fail-closed: the review-cycle witness artifacts (seals + experiments + results
table) are REQUIRED inputs -- the builder exits rather than fabricating a row.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "external_audit_research_report_20260708_v6"
TEX_NAME = "external_audit_research_report_v6.tex"
PDF_NAME = "external_audit_research_report_v6.pdf"
ZIP_NAME = "external_audit_research_report_20260708_v6.zip"
GENERATED_AT = "2026-07-08T00:00:00"

# review-cycle witness artifacts (REQUIRED; the builder never fabricates them)
REQUIRED_ARTIFACTS = [
    "docs/generated/parent_identity_seal.json",
    "docs/generated/bianchi_v_constraint_seal.json",
    "docs/generated/egs3_experiments.json",
    "docs/generated/egs_results_table.json",
]


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
    # rev-r146 review-response cycle: identified-set/seal modules + artifacts
    "htt/obsstat/egs3_identified_set.py",
    "htt/obsstat/egs3_gf_interval.py",
    "htt/obsstat/egs3_evalue_merge.py",
    "htt/obsstat/egs3_prior_exposure.py",
    "htt/obsstat/egs3_parent_identity.py",
    "htt/obsstat/egs3_bianchi_v_constraint.py",
    "htt/obsstat/egs3_shear_memory_bias.py",
    "docs/generated/parent_identity_seal.json",
    "docs/generated/bianchi_v_constraint_seal.json",
    "docs/generated/egs3_experiments.json",
    "docs/generated/egs_results_table.json",
    # B1 code anchors: the registered W^2 convention already lives here
    "htt/bass/validation/comparator_policy.py",
    "htt/htt/htt/core/bounds.py",
    "htt/tsc/admissibility/three_bound_hierarchy.py",
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
    {"id": "P13", "title": "Shear memory of anisotropic stress", "owner": "BASS/HTT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/generated/formal_proof_appendix_current.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md", "htt/obsstat/egs3_shear_memory_bias.py"]},
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
    {"id": "P26", "title": "Partial-identification interval for x_C", "owner": "MIO/OBSSTAT/HTT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "docs/research_program/egs3/THEOREM_CANDIDATES.md", "htt/obsstat/egs3_identified_set.py"]},
    {"id": "P27", "title": "MES-rank route reconciliation", "owner": "BASS/OBSSTAT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["old_version/overleaf/chapters/ch03_bianchi_bounds.tex", "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "htt/obsstat/egs3_graded_comparator.py"]},
    {"id": "P28", "title": "Posterior prior-exposure under null directions", "owner": "HTT/MIO", "status": "DERIVED", "tier": "C2", "sources": ["htt/htt/htt/departure/posterior_pushforward.py", "htt/htt/htt/infer/posterior_exceedance.py"]},
    {"id": "P29", "title": "Finite-cover e-value combination", "owner": "OBSSTAT/HTT", "status": "DERIVED", "tier": "C2", "sources": ["htt/obsstat/egs3_calibration.py", "docs/research_program/egs3/THEOREM_CANDIDATES.md"]},
    {"id": "P30", "title": "Parameter duplication versus observation duplication", "owner": "OBSSTAT/HTT", "status": "DERIVED", "tier": "C2", "sources": ["htt/htt/htt/departure/paper_a_closure.py", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P31", "title": "Identified-set sharpness over PSD and ceiling cones", "owner": "MIO/OBSSTAT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md", "docs/research_program/pr04/PAPER_THEOREM_MAP.md"]},
    {"id": "P32", "title": "Optical ansatz branch identifiability", "owner": "HTT/OBSSTAT/BASS", "status": "DERIVED_CONDITIONAL", "tier": "C2-C3", "sources": ["htt/obsstat/lowell_likelihood_branches.py", "docs/ver3/06_OBSERVABLES_AND_STATISTICS_APPENDIX.md"]},
    {"id": "P33", "title": "Depth-gap delta-method propagation", "owner": "MIO/HTT", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "htt/obsstat/egs3_volterra_memory.py"]},
    {"id": "P34", "title": "Vector-g response covariance propagation", "owner": "OBSSTAT/HTT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md", "htt/mio/formalism/budget_spec.py"]},
    {"id": "P35", "title": "Two-stage identified-set coverage with Imbens-Manski endpoint correction", "owner": "OBSSTAT/MIO", "status": "DERIVED_CONDITIONAL", "tier": "C2", "sources": ["htt/obsstat/egs3_identified_set.py", "docs/generated/egs3_experiments.json"]},
    {"id": "P36", "title": "Joint-feasible-set depth-gap interval propagation", "owner": "MIO/OBSSTAT", "status": "DERIVED", "tier": "C2", "sources": ["htt/obsstat/egs3_gf_interval.py", "docs/ver2_upgrade/x_Q_Pi_F_G_model_independent_framework_upgrade.md"]},
]

# Body-section anchor for every ledger row (the P numbering is registry-stable,
# not body-monotone: P33-P36 live in sections 3.3-3.4).
BODY_SECTIONS = {
    "P1": "3.2", "P2": "3.2", "P3": "4", "P4": "4", "P5": "4",
    "P6": "5.1", "P7": "5.1", "P8": "5.2", "P9": "5.2", "P10": "5.2",
    "P11": "6", "P12": "6", "P13": "6", "P14": "6",
    "P15": "7", "P16": "7", "P17": "7", "P18": "7", "P19": "7", "P20": "7",
    "P21": "7", "P22": "7", "P23": "7.1", "P24": "7.1", "P25": "7.1",
    "P26": "3.4", "P27": "4", "P28": "8.2", "P29": "7", "P30": "5.2",
    "P31": "3.4", "P32": "8.4", "P33": "3.3", "P34": "3.3",
    "P35": "3.4", "P36": "3.3",
}

ALGORITHMS = [
    ("A1", "Domain-checked signed-comparator pushforward", "MIO/common"),
    ("A2", "Denominator policy and certified filling", "MIO/common"),
    ("A3", "Exceedance and finite-cover calibration", "OBSSTAT/HTT"),
    ("A4", "HTT-owned posterior pushforward", "HTT"),
    ("A5", "Response-class collapse from legacy labels", "HTT/OBSSTAT"),
    ("A6", "Local/global rank and overlap audit", "OBSSTAT/HTT"),
    ("A7", "Low-ell likelihood branch classifier", "OBSSTAT/HTT"),
    ("A8", "Identified-set reporting and status classification", "MIO/OBSSTAT/HTT"),
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
        body = BODY_SECTIONS.get(str(item["id"]), "--")
        row = (
            f"{tex_escape(item['id'])} & {tex_escape(item['title'])} & "
            f"{tex_escape(status)} & {owner} & \\S{tex_escape(body)}"
        )
        rows.append(row + r"\\")
    return "\n".join(rows)


def source_index(records: list[dict[str, object]]) -> str:
    lines = [
        "# External Audit Source Index, v6",
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
        "# 외부감사용 HTT 연구보고서 v6 내부 coverage ledger",
        "",
        "이 ledger는 공개 보고서 본문이 아니라, 각 정리와 방법론 항목이 v6 보고서 안에서 실제 서술되었는지 확인하기 위한 내부 추적표이다.",
        "외부 비-HTT PDF와 무관한 교차 분야 자료는 근거로 사용하지 않았다.",
        "v6은 v5 재심사(B1/B2 blocker + M1'-M6')에 대한 응답 개정판이며, P26-P32는 이제 전부 본문 증명을 가진다(ledger-only 등재 해소).",
        "",
        "## 본문 포함 정리",
        "",
        "| ID | 제목 | 상태 | 소유 영역 | 본문 위치 |",
        "|---|---|---|---|---|",
    ]
    for item in THEOREMS:
        body = BODY_SECTIONS.get(str(item["id"]), "--")
        lines.append(
            f"| `{item['id']}` | {item['title']} | `{item['status']}` | `{item['owner']}` | §{body} |"
        )
    lines.extend(
        [
            "",
            "## v6 재심사 지적 우선 반영",
            "",
            r"- B1: \(W^2=\omega_{ab}\omega^{ab}/(6H^2)\)로 통일하고 parent constraint identity를 본문에 명시; \(c=(1,-1,1,1)\)은 SymPy seal로 유도(코드는 이미 등록 규약이었음 — 문서 전용 수리).",
            "- B2: P26-P32 본문(진술+증명) 작성; ledger에 Body 열 추가.",
            "- M1': 2단 tau(사양검정 + 조건부 도달집합) + P35 coverage 정리 + Imbens-Manski 끝점 보정.",
            "- M2': empty(반증가능성)/unbounded(no-result) 분기 + 알고리즘 A8.",
            "- M3': P36 joint-feasible-set G_F 구간 전파; P33은 point-identified 정권으로 도메인 제한.",
            "- M4': 10절 검산표에 N/seed/SE/다중 임계값/artifact hash 명시; E1-E8 witness 표는 결정론적 저장소 아티팩트에서 렌더링(fail-closed).",
            "- M5': Omega_tilt/Omega_k 폐형식 등록; K1 lane에 Hartlap/Sellentin-Heavens 유한-시뮬레이션 보정 요건 등록.",
            "- M6': F>1 -> ceiling-unfit status clip(3.3절 + A2 + A8).",
            "- 사소: Fourth Revision 표기 일치; [x_C]_+ 표기 분리; posterior 문구 교정(HTT 소유; 본 보고서는 만들지 않음); P13/P26 상태 COND 강등; P15 응답계수 lambda_2로 개명; 외부 문헌 맥락 절(등록된 예외, 증거 아님).",
            "",
            "## 제외 원칙",
            "",
            "- legacy family ranking/evidence 숫자는 current reproduction 없이 본문 결과로 승격하지 않았다.",
            "- 내부 진행사, 방어적 검수 용어, 개발 이력 서사는 공개 보고서의 과학 근거에서 제외했다.",
            "- 보고서의 로컬 검산은 관측 결과가 아니라 방법론 검산으로만 표시했다.",
            "- Bianchi V seal은 constraint algebra 검산이며 dynamics 적분/가족 주장 아님.",
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
    # v6 (M4'): full reproducibility metadata -- N, seed, lambda, SE, and the
    # Markov comparison at MULTIPLE thresholds, not just t=10.
    seed = 20260707
    random.seed(seed)
    lam = 0.6
    n = 8000
    thresholds = (5.0, 10.0, 20.0)
    exceed = {t: 0 for t in thresholds}
    mean_e = 0.0
    sq_e = 0.0
    for _ in range(n):
        x = random.gauss(0.0, 1.0)
        e = pow(2.718281828459045, lam * x - 0.5 * lam * lam)
        mean_e += e
        sq_e += e * e
        for t in thresholds:
            if e >= t:
                exceed[t] += 1
    mean_e /= n
    var_e = max(sq_e / n - mean_e * mean_e, 0.0)
    se_e = (var_e / n) ** 0.5
    exceed_rates = {f"{t:g}": exceed[t] / n for t in thresholds}
    markov_bounds = {f"{t:g}": 1.0 / t for t in thresholds}

    # Identified interval example: reachable estimate fixes Sigma2=0.12, Omega_tilt=0.03;
    # unreached components satisfy 0<=W2<=0.04 and 0<=Omega_k_aniso<=0.02.
    sigma2 = 0.12
    omega_tilt = 0.03
    w2_max = 0.04
    ok_max = 0.02
    identified_interval = [sigma2 + omega_tilt - w2_max + 0.0, sigma2 + omega_tilt - 0.0 + ok_max]

    return {
        "dust_flrw_oracle_residual": dust_residual,
        "dust_flrw_oracle_kind": "closed-form (deterministic, no MC)",
        "current_response_rank": matrix_rank(current_rows),
        "enlarged_response_rank": matrix_rank(enlarged_rows),
        "response_rank_kind": "exact linear algebra (deterministic, no MC)",
        "e_value_mc_mean": mean_e,
        "e_value_mc_se": se_e,
        "e_value_mc_n": n,
        "e_value_mc_seed": seed,
        "e_value_mc_lambda": lam,
        "e_value_mc_exceedance_rates": exceed_rates,
        "e_value_markov_bounds": markov_bounds,
        "identified_interval_example": identified_interval,
        "identified_interval_kind": "closed-form (deterministic, no MC)",
        "notes": [
            "All checks are local synthetic/mathematical method checks, not observational results.",
            "The response-rank check encodes the P18/P22 route distinction in the registered g basis.",
            "The interval example demonstrates P26/P31 semantics without using external data.",
        ],
    }


def load_required_artifacts() -> dict[str, dict]:
    """Load the review-cycle witness artifacts, fail-closed (never fabricated)."""
    loaded: dict[str, dict] = {}
    missing = []
    for rel in REQUIRED_ARTIFACTS:
        p = ROOT / rel
        if not p.exists():
            missing.append(rel)
            continue
        loaded[rel] = json.loads(p.read_text(encoding="utf-8"))
    if missing:
        raise SystemExit(
            "missing required review-cycle artifacts (run `make egs3-seals`, "
            "`make egs3-experiments`, and `scripts/build_egs_results_table.py` "
            "first):\n  " + "\n  ".join(missing)
        )
    for rel in ("docs/generated/parent_identity_seal.json",
                "docs/generated/bianchi_v_constraint_seal.json"):
        if loaded[rel].get("status") != "PASS":
            raise SystemExit(f"seal artifact is not PASS: {rel}")
    return loaded


def review_cycle_witnesses(artifacts: dict[str, dict]) -> list[tuple[str, str, str]]:
    """(check, result-with-provenance, artifact-hash-prefix) rows for section 10."""
    def sha_prefix(rel: str) -> str:
        digest = sha256_file(ROOT / rel)
        return (digest or "")[:12]

    pis = artifacts["docs/generated/parent_identity_seal.json"]
    bvs = artifacts["docs/generated/bianchi_v_constraint_seal.json"]
    exp = artifacts["docs/generated/egs3_experiments.json"]["experiments"]
    e = exp.get("axis_e", {})
    f = exp.get("axis_f", {})
    e2 = e.get("E2_im_coverage", {})
    e3 = e.get("E3_refutability_power", {})
    e4 = e.get("E4_gf_joint_vs_naive", {})
    e7 = e.get("E7_evalue_merge", {})
    e8 = e.get("E8_prior_exposure", {})
    f3 = f.get("F3_shear_memory_bias", {})
    rows = [
        ("E1 parent-identity SymPy seal",
         f"status {pis['status']}; c derived {pis['parent_identity']['c_derived']}; "
         f"W2 mismatch factor {pis['w2_convention']['mismatch_factor']}; "
         f"(3/2) rule {pis['three_halves_rule']['derived_factor']} "
         f"(sympy {pis['sympy_version']}; deterministic)",
         sha_prefix("docs/generated/parent_identity_seal.json")),
        ("E2 Imbens-Manski coverage MC",
         f"projection {e2.get('coverage_projection', 0):.4f} >= IM "
         f"{e2.get('coverage_im', 0):.4f} (nominal 0.95) > naive endpoint "
         f"{e2.get('coverage_endpoint_naive', 0):.4f} "
         f"(N={e2.get('n_mc')}, seed {e2.get('seed')}, SE {e2.get('se_binomial', 0):.4f})",
         sha_prefix("docs/generated/egs3_experiments.json")),
        ("E3 refutability power MC",
         f"empty-set rate {e3.get('empty_rate', [0])[0]:.3f} at a=0 (size alpha1="
         f"{e3.get('alpha1')}) rising to {e3.get('empty_rate', [0, 0])[-1]:.2f} "
         f"(N={e3.get('n_mc')}, seed {e3.get('seed')}, binomial SE reported per point)",
         sha_prefix("docs/generated/egs3_experiments.json")),
        ("E4 joint-feasible-set G_F interval",
         f"joint width / naive width = {e4.get('width_ratio', 1):.3f}; joint within "
         f"naive {e4.get('joint_within_naive')} (deterministic grid)",
         sha_prefix("docs/generated/egs3_experiments.json")),
        ("E5 Bianchi V constraint seal",
         f"status {bvs['status']}; beta^2-scaling slope "
         f"{bvs['numeric_witness']['loglog_slope']:.4f}; Omega_K<=0 raises "
         f"{bvs['numeric_witness']['omega_k_breakdown_raises']} "
         f"(sympy {bvs['sympy_version']}; deterministic)",
         sha_prefix("docs/generated/bianchi_v_constraint_seal.json")),
        ("E6 shear-memory kernel bias",
         f"kappa bias zero-crossing at toy Weyl closure e0="
         f"{f3.get('zero_crossing_e0')}; bias range "
         f"[{min(f3.get('kappa_bias_ratio', [0])):.3f}, "
         f"{max(f3.get('kappa_bias_ratio', [0])):.3f}] (deterministic)",
         sha_prefix("docs/generated/egs3_experiments.json")),
        ("E7 dependent e-value merge MC",
         f"merged mean {e7.get('merged_mean', 0):.4f} +/- {e7.get('se', 0):.4f} <= 1 "
         f"under maximal dependence; Ville crossing rates within bounds "
         f"{e7.get('ville_holds')} (N={e7.get('n_sims')}, seed {e7.get('seed')})",
         sha_prefix("docs/generated/egs3_experiments.json")),
        ("E8 prior-exposure witness",
         f"null-direction posterior == prior with KL exactly 0: "
         f"{e8.get('kl_null_block_exact_zero')}; coupled-prior KL "
         f"{e8.get('coupled_prior_kl', 0):.4g} labelled prior-driven "
         f"(N={e8.get('n_samples')}, seed {e8.get('seed')})",
         sha_prefix("docs/generated/egs3_experiments.json")),
    ]
    return rows


def method_validation_rows(summary: dict[str, object]) -> str:
    ev_rates = summary["e_value_mc_exceedance_rates"]
    ev_bounds = summary["e_value_markov_bounds"]
    markov_txt = "; ".join(
        f"Pr(E>={t}) {ev_rates[t]:.4f} <= {ev_bounds[t]:.3f}" for t in ("5", "10", "20"))
    rows = [
        ("Dust-FLRW oracle", f"residual {summary['dust_flrw_oracle_residual']:.3g}",
         "closed form (no MC)"),
        ("Current scalar/radial response", f"rank {summary['current_response_rank']} in four-component g basis",
         "exact linear algebra"),
        ("Enlarged transverse/spin-2 response", f"rank {summary['enlarged_response_rank']} in the same toy basis",
         "exact linear algebra"),
        ("E-value Monte Carlo", f"mean {summary['e_value_mc_mean']:.4f} +/- {summary['e_value_mc_se']:.4f}; {markov_txt}",
         f"N={summary['e_value_mc_n']}, seed {summary['e_value_mc_seed']}, lambda={summary['e_value_mc_lambda']}"),
        ("Identified-set example", f"x_C in [{summary['identified_interval_example'][0]:.3f}, {summary['identified_interval_example'][1]:.3f}]",
         "closed form (no MC)"),
    ]
    return "\n".join(
        f"{tex_escape(name)} & {tex_escape(value)} & {tex_escape(meta)}\\\\"
        for name, value, meta in rows)


def witness_rows(rows: list[tuple[str, str, str]]) -> str:
    return "\n".join(
        f"{tex_escape(name)} & {tex_escape(value)} & \\code{{{sha}}}\\\\"
        for name, value, sha in rows)

def evidence_matrix(records: list[dict[str, object]]) -> dict[str, object]:
    return {
        "generated_at": GENERATED_AT,
        "package": OUT.name,
        "source_policy": "repo-local non-PDF source files only; external non-repository PDFs and non-HTT cross-domain drafts excluded",
        "new_downloads": False,
        "long_run_analysis_executed": False,
        "source_records": records,
        "excluded_source_classes": EXCLUDED_SOURCE_CLASSES,
        "theorems": [dict(item, body_section=BODY_SECTIONS.get(str(item["id"]), "--"))
                     for item in THEOREMS],
        "algorithms": [
            {"id": item[0], "title": item[1], "owner": item[2]} for item in ALGORITHMS
        ],
        "review_findings_addressed": [
            "B1: W^2 registered as omega_ab omega^ab/(6H^2) (= omega_a omega^a/(3H^2)); parent constraint identity displayed; comparator sign vector c=(1,-1,1,1) derived by SymPy seal; v5's omega_a omega^a/H^2 convention shown to be exactly 3x the registered value; document-only repair (code already registered).",
            "B2: P26-P32 proof bodies written into sections 3.4, 4, 5.2, 7, 8.2, 8.4 (ledger entries no longer body-less).",
            "M1': two-stage tau semantics (stage-1 specification test on the m-r residual directions; stage-2 conditional reachable ellipsoid) with the P35 coverage theorem and Imbens-Manski endpoint correction (external-context citations: Imbens & Manski 2004; Stoye 2009).",
            "M2': empty-set (refutability) and unbounded-set (no-result) reporting branches added to section 3.4 and algorithm A8.",
            "M3': P36 joint-feasible-set G_F interval propagation; P33 domain-restricted to the point-identified regime.",
            "M4': section-10 validation rows carry N, seed, SE, multi-threshold Markov checks, and artifact hash prefixes; the review-cycle witness table is rendered from the deterministic repo artifacts.",
            "M5': Omega_tilt and Omega_k_aniso closed forms registered; Hartlap/Sellentin-Heavens finite-simulation whitening-bias requirement added to the K1 lane.",
            "M6': F>1 -> ceiling-unfit status clip in section 3.3, A2, and A8.",
            "Minor: Fourth Revision title/abstract consistency; [x_C]_+ notation split from the sup endpoint; posterior/evidence wording corrected (HTT-owned; none made here); P13 and P26 statuses demoted to DERIVED_CONDITIONAL; P15 response coefficient renamed lambda_2 (kappa stays gravitational); ledger gains a body-section column; external literature context subsection added under the source-policy exception.",
        ],
    }


def build_tex(artifacts: dict[str, dict]) -> str:
    rows = theorem_ledger_rows()
    validation = method_validation_summary()
    validation_rows = method_validation_rows(validation)
    witness_table_rows = witness_rows(review_cycle_witnesses(artifacts))
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

\title{HTT External-Audit Research Report, Fourth Revision\\
\large Mathematical-Physics and Statistical Framework of the \code{htt_base} Repository}
\author{Generated from repo-local HTT sources only}
\date{2026-07-08}

\begin{document}
\maketitle

\begin{abstract}
This fourth revision reviews the current \code{htt_base} research programme as a scientific framework rather than as a code catalogue, and answers the external re-review of the third revision.  It deliberately removes all external non-repository PDF sources, rendered-PDF evidence paths, and cross-domain manuscript material.  The report follows the internal logic of the project: a signed FLRW-departure comparator is defined from a displayed parent constraint identity, its diagnostic functionals are separated from HTT-owned inference, response-rank theorems determine what current observables can and cannot identify, the identified-set semantics of the comparator are given a two-stage coverage construction with empty/unbounded/ceiling-unfit statuses, moment-cone and shear-memory results explain why scalar tilt is insufficient, low-\(\ell\) EGS statistics provide calibrated observable summaries, and the research plan states which future data products are needed before stronger observational claims are available.  The two blocking findings of the re-review are repaired here: the vorticity normalization is unified to the registered \(W^2=\omega_{ab}\omega^{ab}/(6H^2)\) with a symbolic seal (the previous \(\omega_a\omega^a/H^2\) statement was exactly three times the registered value; the code was already on the registered convention), and the seven ledger items P26--P32 now carry full statement-and-proof bodies.  No family assignment, detailed geometry claim, or native solver output is claimed, and no posterior or evidence statement is made (posterior and evidence objects are HTT-owned; this report makes none).
\end{abstract}

\tableofcontents

\section{Source Policy and Scope}
The report is based on repo-local source files: generated proof appendices and registries, theorem maps under \code{docs/research_program}, upgrade notes under \code{docs/ver2_upgrade} and \code{docs/ver3}, selected \code{old_version/overleaf} theorem sources, and current implementation files under \code{htt/mio}, \code{htt/htt/htt}, \code{htt/obsstat}, and \code{htt/bass}.  No PDF located outside the repository is used.  Repo-internal rendered PDFs are also not used as evidence when their source files are available.  Cross-domain manuscript drafts, or other non-HTT material, are excluded from the public theorem body.

The purpose is to expose what the current repository can defend: definitions, derived propositions, conditional statistical methodology, algorithmic contracts, and concrete future-analysis requirements.  The purpose is not to obtain rhetorical favour from a reviewer by foregrounding development history or internal gate architecture.

\subsection{Response map for this revision}
The fourth revision answers the external re-review of the third revision.  Each finding is repaired in the body, not in a rebuttal letter:

{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.10\linewidth} >{\raggedright\arraybackslash}p{0.44\linewidth} >{\raggedright\arraybackslash}p{0.12\linewidth} >{\raggedright\arraybackslash}p{0.24\linewidth}}
\toprule
Finding & Disposition & Body & Witness artifact\\
\midrule
B1 & \(W^2:=\omega_{ab}\omega^{ab}/(6H^2)\) registered; parent identity displayed; \(c\) derived, not postulated; the v5 \(\omega_a\omega^a/H^2\) statement was exactly \(3\times\) the registered value; document-only repair (code already registered) & \S3.1--3.2, \S4 & \code{parent_identity_seal.json} (SymPy); gates F1\\
B2 & P26--P32 statement-and-proof bodies written & \S3.4, \S4, \S5.2, \S7, \S8.2, \S8.4 & ledger body column\\
M1\('\) & two-stage \(\tau\) (specification test + conditional set) with the P35 coverage theorem and Imbens--Manski endpoint correction & \S3.4 & gates E1/E2; \code{egs3_experiments.json}\\
M2\('\) & empty-set (refutability) and unbounded-set (no-result) branches; algorithm A8 & \S3.4, \S9 & gates E1/E3\\
M3\('\) & P36 joint-feasible-set \(G_F\) interval; P33 domain-restricted & \S3.3 & gates E4\\
M4\('\) & section-10 rows carry \(N\), seed, SE, multi-threshold Markov checks, artifact hashes & \S10 & \code{method_validation_summary.json}\\
M5\('\) & \(\Omt\)/\(\Omk\) closed forms; Hartlap/Sellentin--Heavens whitening-bias requirement in the K1 lane & \S3.1, \S12 & --\\
M6\('\) & \(F>1\to\) ceiling-unfit clip & \S3.3, \S9 & gates E1\\
minor & Fourth-Revision consistency; \([x_C]_+\) notation; posterior wording; P13/P26 \(\to\) COND; \(\lambda_2\) rename; ledger body column; literature context & throughout & --\\
\bottomrule
\end{longtable}
}

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

\subsection{External literature context (source-policy note)}
The evidence base of this report is repo-local by policy.  This subsection is the single registered exception: external-context citations that position the methodology, used as CONTEXT only, never as evidence for any repo claim.  (i) The Bianchi \(\mathrm{VII}_h\) template tradition -- Bayesian fits assigning a detailed geometry and reporting vorticity/shear upper limits from WMAP and Planck temperature and polarization (Jaffe et al.; Saadeh et al.) -- is the methodological counterpoint to the identifiability-first route here: those analyses PRESUPPOSE a mode template (a geometry assignment), whereas the response-rank theorems of \S5.2 show the current channels cannot justify that assignment.  (ii) Planck and BBN Bianchi~I shear ceilings constrain \(\Sigma^2\) far below any low-\(\ell\) morphology scale, which is why the comparator treats \(\Sigma^2\) as a bounded, not measured, component until the native transfer lands.  (iii) The bipolar spherical harmonic (BipoSH) decomposition of \S7.1 originates with Hajian--Souradeep as the standard statistical-isotropy test basis.  (iv) The CF4 bulk-flow controversy -- large-depth amplitudes in tension with \(\Lambda\)CDM under some estimators and consistent under others, with estimator-covariance treatment the disputed ingredient -- is the live example motivating the registered bin/reference/covariance/null policy of the \(G_F\) lane.  (v) The e-value and anytime-valid inference literature (Ville's inequality; Gr\"unwald et al.; Vovk--Wang e-value merging; Ramdas et al.) supplies the calibration and merging facts formalized in P19/P29.  (vi) The partial-identification literature (Imbens--Manski 2004; Stoye 2009) supplies the endpoint-coverage semantics formalized in P35.  None of these citations is used to support a repo result; they mark where the formalism sits in the published landscape.

\section{Signed Comparator and Diagnostic Algebra}
\subsection{Registered component vector}
The public mathematical object is the registered four-component vector
\[
  \bm g=(g_\Sigma,g_W,g_t,g_k)
  =\left(\Sig,\Wsq,\Omt,\Omk\right).
\]
The registered conventions are
\[
  \Sig=\frac{\sigma_{ab}\sigma^{ab}}{6H^2},
  \qquad
  \Wsq=\frac{\omega_{ab}\omega^{ab}}{6H^2}=\frac{\omega_a\omega^a}{3H^2},
\]
where the second equality uses \(\omega_a=\frac12\epsilon_{abc}\omega^{bc}\), hence \(\omega_{ab}\omega^{ab}=2\omega_a\omega^a\) (verified symbolically in the parent-identity seal).  The vorticity normalization is thus EXACTLY parallel to the shear normalization: tensor norm over \(6H^2\).  The third revision stated \(\Wsq=\omega_a\omega^a/H^2\), which is exactly three times the registered value; that statement was a document defect, repaired here.  Three facts fix the repair uniquely: (i) the parent constraint identity below forces the \(1/(6H^2)\) tensor normalization for BOTH \(\Sig\) and \(\Wsq\); (ii) the P3 conversion rule \(X^2_{\max}=\frac32B^2\) is derived (not asserted) under this normalization; and (iii) the code was ALREADY on the registered convention (\code{comparator_policy.py} \code{Wstd_sq = omega_sq/(6 H^2)}; \code{bounds.py} and \code{three_bound_hierarchy.py} \code{W2_max = (3/2) B_omega^2}), so the repair is document-only and every bit-identical \(x_C\) anchor is untouched.  The three-convention table is sealed in \code{parent_identity_seal.json}:
\begin{center}
{\footnotesize
\begin{tabular}{lll}
\toprule
Convention & Value & Status\\
\midrule
\(\omega_{ab}\omega^{ab}/(6H^2)\) & \(=\omega_a\omega^a/(3H^2)\) & REGISTERED (constraint-natural; code)\\
\(\omega_a\omega^a/(3H^2)\) & identical to registered & equivalent vector form\\
\(\omega_a\omega^a/H^2\) & \(3\times\) registered & third-revision defect (retired)\\
\bottomrule
\end{tabular}
}
\end{center}

The tilt and curvature components now carry closed forms rather than verbal descriptions.  For a declared matter-frame tilt of rapidity \(\beta\) and equation of state \(w\) (registered form, \code{comparator_policy.py}, ch03 \code{eq:Otilt-def}),
\[
  \Omt=(1+w)\,\Omega_m\sinh^2\!\beta ,
\]
the energy-density excess of the tilted matter frame relative to the normal frame at \(O(\sinh^2\beta)\).  The curvature component is
\[
  \Omega_k=-\frac{{}^{3}\!R}{6H_\theta^2},
  \qquad
  \Omk=\Omega_k-\Omega_{k,{\rm ref}} ,
\]
with the reference \(\Omega_{k,{\rm ref}}\) fixed by the registered comparator policy (FLAT: \(0\); MATCHED: the declared isotropic FLRW curvature of the branch; NULL: withheld, forcing set-valued reporting).  All four entries are dimensionless, nonnegative component magnitudes before the signed comparator coefficients are applied.

The signed comparator is the linear functional
\[
  x_C=c^T\bm g,
  \qquad c=(1,-1,1,1)^T .
\]
The coefficient vector is not postulated: it is READ OFF the parent constraint identity of \S3.2, and the reading is sealed symbolically (tilted frame included) in \code{parent_identity_seal.json}.  This convention is deliberately stronger than a loose verbal definition: it fixes the sign of the vorticity channel, separates curvature from shear and tilt, and makes rank statements about current observables expressible as row-space statements about \(\bm g\).

\subsection{Parent constraint route}
The parent identity is now DISPLAYED, not merely named.  The generalized Friedmann (Gauss) constraint of the 1+3 covariant formalism is
\[
  \frac{\Theta^2}{3}
  =
  \kappa\mu+\Lambda-\frac{{}^{3}\!R}{2}+\sigma^2-\omega^2,
  \qquad
  \sigma^2\equiv\tfrac12\sigma_{ab}\sigma^{ab},
  \quad
  \omega^2\equiv\tfrac12\omega_{ab}\omega^{ab}.
\]
Dividing by \(3H^2\) (\(\Theta=3H\)) and evaluating the energy density in a declared tilted matter frame, \(\mu_u=\mu+(\mu+p)\sinh^2\beta\), gives the dimensionless budget
\begin{equation}
  1=\Omega_m+\Omega_\Lambda+\Omega_k+\Omt+\Sig-\Wsq ,
  \label{eq:parent}
\end{equation}
with \(\Omega_m=\kappa\mu/(3H^2)\), \(\Omega_\Lambda=\Lambda/(3H^2)\), and the component normalizations of \S3.1 FORCED by the division: \(\sigma^2/(3H^2)=\sigma_{ab}\sigma^{ab}/(6H^2)=\Sig\) and \(\omega^2/(3H^2)=\omega_{ab}\omega^{ab}/(6H^2)=\Wsq\).  The comparator sign vector \(c=(1,-1,1,1)\) is the gradient of the right-hand side of \eqref{eq:parent} with respect to \((\Sig,\Wsq,\Omt,\Omk)\); the derivation, including the tilted frame, is executed symbolically and fail-closed in \code{parent_identity_seal.json} (SymPy; gate class F1).

The comparator is obtained by comparing this registered non-FLRW budget identity with an FLRW reference after untracked scalar terms have either been declared absent for the branch or placed in an explicit residual.  Thus a result involving \(x_C\) has the logical form
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
  F=\frac{[x_C]_+}{U_C}\quad\hbox{only under an admissible ceiling policy},
\]
where \([x]_+=\max(0,x)\) denotes the positive part.  (The superscript notation \(x_C^+\) is reserved for the SUPREMUM endpoint of the identified set in \S3.3; the third revision overloaded one glyph for both meanings.)
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

The tolerance \(\tau\) is no longer a single conflated number.  The registered construction is TWO-STAGE (\S3.4, P35): the \(m-r\) residual directions orthogonal to the reachable column space carry a SPECIFICATION TEST at level \(\alpha_1\) with threshold \(\tau_1=\chi^2_{m-r,1-\alpha_1}\) -- if the residual statistic exceeds \(\tau_1\), the feasible set is empty and the correct report is a misfit/refutation status, not an interval -- while the \(r\) reachable directions carry a conditional \(\chi^2_{r,1-\alpha_2}\) ellipsoid.  Degrees of freedom are thus accounted separately on the reachable and residual subspaces, which is what makes the coverage statement of P35 possible.

The certified filling quantity is not a second name for \(x_C\).  With a declared positive ceiling \(U_C\),
\[
  F\in\left[[x_C^-]_+/U_C,\; [x_C^+]_+/U_C\right],
\]
and a scalar \(F\) is reported only when the interval and denominator policy permit it.  If \([x_C^+]_+/U_C>1\), the declared ceiling is inconsistent with the feasible set and the report is a CEILING-UNFIT status, never a silently clipped \(F\) (algorithm A2/A8).  A denominator-sensitivity analysis varies \(U_C\) across admissible MES or full-covariance ceilings and records whether conclusions are stable.

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
This is the multivariate delta method applied to the smooth map \((u,v)\mapsto\log u-\log v\).  The gradient at \((F_b,F_{b_0})\) is \((1/F_b,-1/F_{b_0})\), giving the displayed quadratic form.  The positivity condition is part of the domain; outside it the ratio/log route must be replaced by a different declared contrast.  DOMAIN RESTRICTION (fourth revision): the delta method presumes POINT-IDENTIFIED bin fillings with a regular covariance \(V_F\).  In the set-valued regime -- rank-deficient bins with ceiling-bounded null components -- the correct propagation is the joint-feasible-set interval of P36, not this formula.
\end{proof}

\paragraph{Proof item P34.}
\begin{proposition}[Vector-\(g\) response covariance propagation]
For a local estimator \(\widehat{\bm g}\) with covariance \(V_g\), any linear diagnostic \(z=a^T\bm g\) has variance \(a^TV_ga\).  In particular, the comparator variance is \(c^TV_gc\) when all four components are jointly estimated; if only a projection is estimated, the same formula applies only on the reachable block and the null block must be handled by an identified set or prior-exposure statement.
\end{proposition}
\begin{proof}
The variance of a linear transformation is \({\rm Var}(a^T\widehat{\bm g})=a^T{\rm Var}(\widehat{\bm g})a\).  When \(V_g\) is singular because only a row-space projection is observed, adding arbitrary finite covariance in null directions would be a modelling prior rather than data information.  Thus covariance propagation is valid on estimated coordinates, while unestimated coordinates require set-valued or HTT-prior-aware treatment.
\end{proof}

\paragraph{Proof item P36.}
\begin{proposition}[Joint-feasible-set depth-gap interval propagation]
Let two depth bins share unobserved null components \(s\) constrained to a common box \({\cal S}\) (one sky, hence ONE value of \(s\) for both bins), with bin fillings
\(N(s)=n_{\rm pt}+c_N\!\cdot\!s\) and \(D(s)=d_{\rm pt}+c_D\!\cdot\!s\), \(n_{\rm pt}\) and \(d_{\rm pt}\) ranging over their reachable intervals and \(D>0\) on the feasible set.  Then the identified interval of \(G_F=N/D\) is the joint envelope
\[
  \left[\inf_{s\in{\cal S}}\frac{n^-+c_N\!\cdot\!s}{d^++c_D\!\cdot\!s},\;
        \sup_{s\in{\cal S}}\frac{n^++c_N\!\cdot\!s}{d^-+c_D\!\cdot\!s}\right],
\]
and it is a SUBSET of the naive quotient of the two marginal intervals; the inclusion is strict whenever \(c_N,c_D\ne0\) and \({\cal S}\) is nondegenerate.
\end{proposition}
\begin{proof}
For fixed \(s\), the ratio is monotone in the numerator and antitone in the (positive) denominator, so the per-\(s\) extremes sit at the reachable-interval endpoints; the envelope over \({\cal S}\) follows.  The naive quotient optimizes the numerator's \(s\) and the denominator's \(s\) INDEPENDENTLY, i.e.\ over the product \({\cal S}\times{\cal S}\), whereas the joint object optimizes over the diagonal \(\{(s,s)\}\subset{\cal S}\times{\cal S}\).  Optimizing over a superset can only widen the extremes, giving the inclusion; on the registered toy the joint width is strictly smaller (gate class E4, width ratio \(\approx0.58\)).  Reporting the naive quotient as if it were the identified set therefore OVERSTATES the uncertainty; both objects are conservative, but only the joint interval is sharp.
\end{proof}

\subsection{Identified-set semantics and endpoint inference}
This subsection carries the operational resolution of the P1\(\times\)P18 tension flagged by the external review: the comparator needs all four components, the registered channels reach two, and the reportable object is therefore the identified interval with an explicit status algebra.  Four statuses exhaust the outcomes (algorithm A8; gate classes E1--E3): FEASIBLE (a finite sharp interval), EMPTY (the specification test rejects, or the stage-2 ellipsoid misses the physical cone -- this is REFUTABILITY, a feature: the model class is falsifiable), UNBOUNDED (a null direction with nonzero comparator coefficient carries no MES ceiling; the honest report is no-result, matching P24/P25), and CEILING-UNFIT (\([x_C^+]_+>U_C\); the declared ceiling is inconsistent with the feasible set).

\paragraph{Proof item P26.}
\begin{theorem}[Partial-identification interval for \(x_C\)]
Let \({\cal G}(y)\) be the feasible set of \S3.3 with the null space of \(R\) spanned by zero columns (the registered case), \({\cal C}_{\rm phys}\) the nonnegative cone, and \({\cal C}_{\rm MES}\) a ceiling box on the null components.  If \({\cal G}(y)\ne\emptyset\), then the image \(\{c^T\bm g:\bm g\in{\cal G}(y)\}\) is a closed interval \([x_C^-,x_C^+]\) with the exact decomposition
\[
  x_C^\pm
  =
  \left(\hbox{extremes of }c_R^T\bm g_R\hbox{ over the reachable ellipsoid}\cap\hbox{box}\right)
  +
  \sum_{j\in{\rm null}}
  \begin{cases}
    [0,\,c_jU_j] & c_j>0,\\
    [-|c_j|U_j,\,0] & c_j<0,
  \end{cases}
\]
where the null contributions add interval-wise.  In particular the vorticity ceiling enters the LOWER endpoint (\(c_W=-1\)) and the curvature ceiling the UPPER endpoint (\(c_k=+1\)).
\end{theorem}
\begin{proof}
\({\cal G}(y)\) is an intersection of convex sets (an ellipsoidal cylinder, an orthant, and a box), hence convex; the image of a convex set under a linear functional is an interval, and it is closed because \({\cal G}(y)\) is closed and the null box is compact in every direction with a finite ceiling.  Because null columns of \(R\) do not enter the data misfit, the feasible set factorizes as (reachable slice) \(\times\) (null box), so the extremes decompose as displayed.  The registered example (reachable point \(\Sig=0.12\), \(\Omt=0.03\); ceilings \(U_W=0.04\), \(U_k=0.02\)) gives \([0.11,\,0.17]\), reproduced bit-level by gate class E1.
\end{proof}

\paragraph{Proof item P31.}
\begin{lemma}[Identified-set sharpness]
Every point of \([x_C^-,x_C^+]\) in P26, including both endpoints, is attained by an admissible configuration: the interval is SHARP, not conservative.
\end{lemma}
\begin{proof}
The reachable extremes are attained because the ellipsoid-box intersection is compact and the functional continuous.  For the null components, any value \(g_j\in[0,U_j]\) must be realizable by a physical configuration: the PSD second-moment cone construction of P11 supplies it -- antipodal stream pairs realize ANY positive semidefinite second moment with vanishing first moment, so a null-sector magnitude anywhere in its ceiling box corresponds to an explicit admissible stream configuration.  Concatenating a reachable extremizer with a null-box extremizer attains each endpoint; intermediate values follow by convexity.  Thus no shorter interval is defensible, and no wider interval is honest.
\end{proof}

\paragraph{Proof item P35.}
\begin{theorem}[Two-stage coverage with Imbens--Manski endpoint correction]
Let \(\tau_1=\chi^2_{m-r,1-\alpha_1}\) and \(\tau_2=\chi^2_{r,1-\alpha_2}\) as in \S3.3, with Gaussian whitened noise.  Then:
(i) under a correctly specified response, \(\Prob(\hbox{EMPTY at stage 1})\le\alpha_1\), and the stage-1 statistic is ancillary to the reachable estimate, so the conditional stage-2 construction covers the reachable projection with probability \(\ge1-\alpha_2\) (jointly \(\ge1-\alpha_1-\alpha_2\) by Bonferroni);
(ii) the projection interval with per-endpoint \(z_{1-\alpha/2}\) covers the WHOLE identified set with asymptotic probability \(\ge1-\alpha\), hence is conservative for the scalar parameter \(x_C\);
(iii) a pointwise \(1-\alpha\) confidence interval for the PARAMETER \(x_C\in[x_C^-,x_C^+]\) is obtained with the critical value \(C_N\) solving
\[
  \Phi\!\left(C_N+\frac{\widehat\Delta}{\max(\widehat\sigma^-,\widehat\sigma^+)}\right)-\Phi(-C_N)=1-\alpha,
\]
where \(\widehat\Delta=\widehat x_C^+-\widehat x_C^-\); the naive per-endpoint one-sided \(z_{1-\alpha}\) construction undercovers, degrading to \(1-2\alpha\) as \(\Delta\to0\).
\end{theorem}
\begin{proof}
(i) The stage-1 statistic is the squared norm of the residual projection, distributed \(\chi^2_{m-r}\) under correct specification and independent of the reachable least-squares estimate (orthogonal projections of Gaussian noise); the stated levels follow from the quantile definitions.  (ii) Covering both endpoints simultaneously at \(z_{1-\alpha/2}\) covers every point between them.  (iii) In the registered construction both endpoint estimators share the SAME reachable noise (the null-box widths are deterministic), the exact regime of the Imbens--Manski equation: coverage of a boundary point equals \(\Phi(C+\Delta/\sigma)-\Phi(-C)\), and \(C_N\) restores level \(1-\alpha\) uniformly in \(\Delta\), interpolating between \(z_{1-\alpha}\) (\(\Delta\gg\sigma\)) and \(z_{1-\alpha/2}\) (\(\Delta=0\)) (Imbens--Manski 2004; Stoye 2009 -- external-context citations, \S2.3).  The Monte-Carlo witness (gate class E2; N=2000, seed 20260708) reproduces the ordering: projection \(\ge\) IM \(\approx0.95>\) naive endpoint.
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
The MES hypotheses bound the PSTF photon multipoles and the first covariant derivative terms that source the kinematical hierarchy.  Solving the linearized hierarchy for shear, vorticity, and acceleration gives different coefficient combinations because the dipole, quadrupole, and octupole enter the three equations with different projection coefficients.  The factor \(3/2\) is now DERIVED rather than asserted: with \(X^2:=x_{ab}x^{ab}/(6H^2)\), \(H=\Theta/3\), and the hierarchy bound \(\sqrt{x_{ab}x^{ab}}/\Theta\le B\), one gets \(X^2\le B^2\Theta^2/(6\Theta^2/9)=\frac32B^2\) (sealed in \code{parent_identity_seal.json}).  Note this conversion is consistent ONLY under the registered tensor-norm-over-\(6H^2\) convention of \S3.1 -- the third revision's \(\omega_a\omega^a/H^2\) vorticity statement contradicted exactly this rule, which is how the defect was caught.  Thus the result is a three-bound hierarchy, not a single scalar anisotropy number.
\end{proof}

\paragraph{Provenance of the \(\epsilon\)-coefficients.}  The rational coefficients \((\frac53,3,\frac37)\), \((\frac34,2,\frac27)\), \((\frac34,1,\frac3{14})\) are REGISTERED EXTERNAL values from the Maartens--Ellis--Stoeger 1995 linearized multipole hierarchy (external-context citation, \S2.3); they are carried as exact fractions in \code{three_bound_hierarchy.py} and \code{bounds.py} and are NOT rederived in this report.  Gate class F1 asserts bit-level agreement between the registered values recorded in the seal and the code-side constants, so any silent drift in either place fails the audit.  What IS derived here is the conversion rule between the \(\Theta\)-normalized bounds and the \(H\)-normalized squared ceilings.

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
The LRS Bianchi V momentum constraint couples the curvature-normalized shear response to the tilted matter flux: \(2A\Sigma_+=(1+w)\Omega_m\beta\) at leading order, with \(\Omega_K=A^2\).  At small tilt, the normal-frame flux is linear in \((1+w)\Omega_m\beta\).  Squaring the response and dividing by the curvature-magnitude term gives the displayed quadratic scaling.  The formula vanishes at \(\beta=0\), is undefined as a response formula when \(\Omega_K\le0\), and depends on the LRS/small-tilt assumptions.  The constraint algebra is now SEALED symbolically (\code{bianchi_v_constraint_seal.json}; gate class F2): the solved constraint reproduces the formula exactly; the exact-rapidity flux \((1+w)\Omega_m\sinh\beta\cosh\beta\) gives the first correction \(\Sigma^2_{\rm BV}\to\Sigma^2_{\rm BV}(1+\frac43\beta^2+O(\beta^4))\); a numeric witness confirms the \(\beta^2\) error scaling (log-log slope \(2.000\)); and the \(\Omega_K\le0\) domain violation raises rather than returning a number.  The seal is constraint algebra, NOT an integration of the tilted-LRS dynamical system (that expansion-normalized evolution check remains a registered stretch item in \S12).  It is therefore a conditional response proposition, not a current data assignment to Bianchi V geometry.
\end{proof}

\paragraph{Proof item P27.}
\begin{proposition}[MES-ceiling and response-rank routes are different morphisms]
The MES route of P3 maps all-observer near-isotropy hypotheses to MAGNITUDE CEILINGS on \((\Sig,\Wsq,A^2)\); the response-rank route of P18 maps a sky-template design to the set of UPDATABLE DIRECTIONS of \(\bm g\).  The two maps act on different inputs and constrain different aspects: a direction can carry zero Fisher information (a P18 null) while carrying a finite MES ceiling, with no contradiction.  Jointly they produce the identified set of P26: an ellipsoid slab on the reachable directions intersected with a ceiling box on the null directions.
\end{proposition}
\begin{proof}
The MES bound is a functional of the DERIVATIVE-AUGMENTED observable set: it uses the low multipoles AND their first covariant derivatives for all observers, which is information outside the row space of any single-observer sky-template design.  The response rank is a property of the registered design matrix alone.  Formally, the MES map factors through the dynamical hierarchy (P3), the rank map through the whitened template Gram matrix (P8/P18); neither factors through the other.  The vorticity sector is the canonical instance: \(\Wsq\) is a structural null of the radial design (P9), yet \(W^2_{\max}=\frac32B_\omega^2\) is finite -- which is precisely why the P26 interval is bounded below at \(-\frac32B_\omega^2\) rather than \(-\infty\).  The apparent v4-review contradiction dissolves once each statement carries its route tag.
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
If \(v\in\ker R\), then \(R(\theta+v)=R\theta\), so the observable mean is unchanged and the direction is not identifiable.  Conversely, nonzero row-space directions change the mean.  For \(R'=(R,R)\), one has \(R'(a,-a)=Ra-Ra=0\) for every compatible vector \(a\), while the row space has not gained a new independent block.  (This paragraph concerns COLUMN duplication -- duplicated parameters.  The distinct ROW-duplication case -- repeated observations -- is P30 below; the third revision's prose conflated the two.)
\end{proof}

\paragraph{Proof item P30.}
\begin{lemma}[Parameter duplication versus observation duplication]
Column duplication (P8) adds a kernel direction and NO information.  Row duplication -- repeating an observation channel -- adds Fisher information according to its noise correlation: for a duplicated row with noise correlation \(\rho\) between the two copies, the Fisher information in the duplicated direction scales as \(2/(1+\rho)\) times the single-copy value.  Independent noise (\(\rho=0\)) doubles the information; perfectly correlated noise (\(\rho=1\)) gains nothing.
\end{lemma}
\begin{proof}
For \(y_i=r^T\theta+\varepsilon_i\), \(i=1,2\), with \({\rm Var}(\varepsilon_i)=\sigma^2\) and \({\rm Corr}(\varepsilon_1,\varepsilon_2)=\rho\), the optimal combination is the mean, with variance \(\sigma^2(1+\rho)/2\); the Fisher information is its inverse, giving the stated factor.  At \(\rho=1\) the second copy is a deterministic function of the first, so the "two" observations are one.  Column duplication never enters this calculation: it changes the PARAMETER space, not the observation space.  Keeping the two operations distinct prevents the false inference that a re-labelled channel improves an estimator.
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

The quantitative consequence of an UNREGISTERED closure is now measured rather than asserted (gate class F3; \code{egs3_shear_memory_bias.py}): fitting the naive scalar closure \(\dot\sigma=-3H\sigma+\hat\kappa\Pi\) on trajectories generated by the exact linearized law with a toy Weyl closure \(E=e_0H\sigma\) recovers \(\hat\kappa\) without bias ONLY at the friction-matching value \(e_0=1\), with the bias growing monotonically away from it (\(+33\%\) at \(e_0=0\), \(-20\%\) at \(e_0=2\) on the registered driving history).  The qualitative memory conclusion survives every \(e_0\); the quantitative kernel does not survive an unregistered closure.  Accordingly the ledger status of this item is DERIVED\_CONDITIONAL (the third revision's DER tag overstated it, exactly as the review noted).
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
Assume \(a_2=\lambda_2\Sigma\), \(\lambda_2>0\), \(F_{\rm shear}=\Sigma^2/x_{\max}\), \(x_{\max}>0\), and \(D_2=c_D a_2^2\).  Then
\[
  F_{\rm shear}
  =
  \frac{a_2^2}{\lambda_2^2x_{\max}}
  =
  \frac{D_2}{c_D\lambda_2^2x_{\max}},
\]
so \(F_{\rm shear}\to0\) as the quadrupole amplitude tends to zero under the closure.
\end{theorem}
\begin{proof}
Substitute \(\Sigma=a_2/\lambda_2\) into \(F_{\rm shear}\).  The second equality follows from \(D_2=c_Da_2^2\).  The conclusion is closure-conditional; it does not assert that every observed quadrupole is a pure shear response.  (Notation: the quadrupole-to-shear response coefficient is now written \(\lambda_2\), retiring the third revision's overloaded \(\kappa\) -- in P13/P14 \(\kappa\) is the gravitational coupling, a physically unrelated constant.)
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

\paragraph{Proof item P29.}
\begin{lemma}[Finite-cover e-value combination under arbitrary dependence]
Let \(E_1,\dots,E_K\) be e-values for a common null (\(\E_0E_k\le1\)) computed on the cells of a finite cover, with ARBITRARY dependence between cells.  Then for any convex weights \(w_k\), the merged statistic \(E=\sum_kw_kE_k\) is again an e-value, and \(\Prob_0(E\ge t)\le1/t\) globally.  Moreover, for staged data arrival the product process \(M_t=\prod_{i\le t}E^{(i)}\) of sequential e-values with \(\E_0[E^{(i)}\mid{\cal F}_{i-1}]\le1\) is a nonnegative supermartingale, and Ville's inequality gives ANYTIME validity: \(\Prob_0(\sup_tM_t\ge1/\beta)\le\beta\) at every data-dependent stopping time.
\end{lemma}
\begin{proof}
\(\E_0E=\sum_kw_k\E_0E_k\le\sum_kw_k=1\) by LINEARITY of expectation, which holds regardless of the joint law of the \(E_k\) -- no independence, dependence model, or copula assumption enters.  Markov's inequality then applies to \(E\).  For the sequential part, \(\E_0[M_t\mid{\cal F}_{t-1}]=M_{t-1}\E_0[E^{(t)}\mid{\cal F}_{t-1}]\le M_{t-1}\), and Ville's inequality for nonnegative supermartingales bounds the crossing probability of the running supremum.  This is exactly the structure needed for the K1/K5 lanes, where data arrive in stages and the analysis time is not pre-specified: the type-I control survives optional stopping (external-context lineage: Ville; Vovk--Wang e-value merging; Ramdas et al.\ anytime-valid inference, \S2.3).  Both facts carry seeded Monte-Carlo witnesses under MAXIMAL dependence (a common factor across all cells): merged mean \(\le1\) within Monte-Carlo error and Ville crossing rates within their bounds (gate class E5).
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

\paragraph{Proof item P28.}
\begin{proposition}[Posterior prior-exposure on null response directions]
Suppose the likelihood depends on \(\bm g\) only through \(R\bm g\), and column \(j\) of \(R\) is identically zero.  If the prior factorizes across coordinate \(j\), \(\pi(\bm g)=\pi_j(g_j)\,\pi_{-j}(\bm g_{-j})\), then the posterior marginal of \(g_j\) EQUALS its prior marginal, and the Kullback--Leibler divergence between prior and posterior restricted to the \(g_j\) \(\sigma\)-field is exactly zero.  Consequently any pushforward statement \(\Ppost(Z>t)\) whose statistic \(Z\) loads on a null direction is, in that direction, a PRIOR statement and must be labelled prior-exposed.
\end{proposition}
\begin{proof}
The posterior density factorizes: \(p(\bm g\mid y)\propto L(y\mid R\bm g)\,\pi_j(g_j)\,\pi_{-j}(\bm g_{-j})\), and \(L\) does not depend on \(g_j\) because its column is zero.  Marginalizing over \(\bm g_{-j}\) leaves \(p(g_j\mid y)\propto\pi_j(g_j)\times\hbox{const}\), i.e.\ the prior.  The restricted KL is the KL between identical marginals, hence \(0\).  If instead the prior COUPLES \(g_j\) to reachable coordinates, the posterior marginal of \(g_j\) can move -- but only through the prior coupling, never through the likelihood, so the movement is prior-driven and must be reported as such.  The Gaussian-conjugate witness (gate class E6; closed-form KL \(=0.0\) exactly, coupled-prior KL \(>0\) labelled) is deterministic.  This proposition is the formal basis of the existing \code{prior_contaminated} classification in the departure-posterior pipeline: fail-closed reporting demands that prior-dominated directions never masquerade as data constraints.
\end{proof}

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

\paragraph{Proof item P32.}
\begin{proposition}[Optical-ansatz branch identifiability]
The mean-template and covariance branches are identifiable only under branch-specific conditions, and a scalar central \(\chi^2\) statistic closes neither.  (i) In the mean-template branch, \(\alpha\) is identifiable after orientation handling iff the orientation-processed template Gram matrix is nonsingular: either the orientation \(\varphi\) is fixed by registered metadata (then \(\rank T(\varphi)=\dim\alpha\) suffices), or \(\varphi\) is marginalized and the statistic must be NONCENTRAL, since uniform orientation averaging annihilates the linear mean response of any \(L>0\) template.  (ii) In the covariance branch, \(\alpha\) is identifiable iff the covariance directions \(\{C_a\}\) are linearly independent in the whitened space, i.e.\ the Fisher metric \(F_{ab}=\frac12\,{\rm tr}(C_0^{-1}C_aC_0^{-1}C_b)\) is nonsingular; this requires access to an anisotropic covariance object (off-diagonal BipoSH sectors, P23), which diagonal \(C_\ell\) compression destroys.  (iii) A scalar central \(\chi^2\) is a quadratic functional invariant under the orientation group and blind to the off-diagonal sectors, so it can detect neither the noncentrality of branch (i) nor the covariance directions of branch (ii): both branch responses lie in its null space.
\end{proposition}
\begin{proof}
(i) Uniform SO(3) marginalization of a spin-\(L>0\) template has zero mean by Schur orthogonality, so the surviving information sits at second order -- a noncentrality -- and least-squares identifiability reduces to the stated Gram condition at fixed \(\varphi\).  (ii) The covariance-branch score at \(\alpha=0\) is \(\frac12\,{\rm tr}[C_0^{-1}C_a(C_0^{-1}(YY^T-C_0))]\); its covariance is the stated Fisher metric, which is a Gram matrix in the whitened inner product and is nonsingular iff the \(C_a\) are independent there.  Diagonal compression projects each \(C_a\) onto its \(L=0,\ell=\ell'\) sector (P23), collapsing distinct anisotropic directions onto one axis and breaking independence.  (iii) A central \(\chi^2\) statistic has zero derivative with respect to a mean displacement at the null and depends on the covariance only through its rotation-invariant diagonal sector; both branch responses therefore vanish at first order.  Which branch applies, and with what orientation/covariance policy, is exactly the classification enforced by algorithm A7.
\end{proof}

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
    x_C_pos = max(0, x_C)          # the positive part [x_C]_+
    if x_C_pos > denominator:
        emit ceiling_unfit status  # F > 1: never silently clipped
    else:
        report F = x_C_pos / denominator
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

\subsection*{A8. Identified-set reporting and status classification}
\begin{verbatim}
inputs: y (whitened), R, c, cone lower bounds, MES ceiling box, alpha1, alpha2
tau1 = chi2_quantile(m - r, 1 - alpha1)   # specification test
tau2 = chi2_quantile(r, 1 - alpha2)       # conditional reachable set
s1 = squared residual of y off the reachable column space
if s1 > tau1:
    emit empty status                      # refutability: model class rejected
elif reachable ellipsoid does not meet the physical cone:
    emit empty status
elif any null direction with c_j != 0 lacks a finite ceiling:
    emit unbounded status                  # no-result (P24/P25 semantics)
else:
    [x_lo, x_hi] = reachable extremes (ellipsoid intersect box) + null-box terms
    if ceiling U_C declared and max(0, x_hi)/U_C > 1:
        emit ceiling_unfit status
    else:
        report the sharp interval [x_lo, x_hi]
        endpoint CI: Imbens-Manski critical value C_N (P35), never the
        naive one-sided z (undercovers as the width shrinks)
\end{verbatim}

\section{Local Method Validation Checks}
The package includes a small no-download validation file, \code{method_validation_summary.json}.  These checks exercise algebraic and statistical machinery only; they are not observational cosmology results and do not use external data.  Their role is to show that the report's strengthened definitions have executable counterparts.  Every row now carries its reproducibility metadata (M4\('\)): sample size, seed, and standard error where a Monte-Carlo enters, and an explicit "closed form / exact linear algebra" tag where none does.

{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.26\linewidth} >{\raggedright\arraybackslash}p{0.44\linewidth} >{\raggedright\arraybackslash}p{0.22\linewidth}}
\toprule
Check & Local result & N / seed / kind\\
\midrule
%VALIDATION_ROWS%
\bottomrule
\end{longtable}
}

The dust-FLRW row verifies the analytic oracle used for branch sanity checks.  The rank rows verify the P18/P22 distinction: current scalar/radial rows are rank two in the four-component \(\bm g\) basis, while additional transverse/spin-2-like rows can open the missing sectors in a toy design.  The e-value row checks Markov-compatible calibration in a synthetic null at THREE thresholds, with the Monte-Carlo standard error printed.  The interval row demonstrates that a missing \(\Wsq\) and \(\Omk\) sector produces an interval for \(x_C\), not a fabricated point estimate.

\subsection{Review-cycle experiment witnesses (E1--E8)}
The fourth revision adds a second, larger witness layer: the deterministic seal and experiment artifacts produced by the repository's gate programme (\code{make egs3-seals}, \code{make egs3-experiments}; gate classes E1--E7 and F1--F4).  The rows below are RENDERED FROM those artifacts -- the builder loads them fail-closed and refuses to run if any is missing or non-PASS -- and each row carries the SHA-256 prefix of its source artifact, so the printed numbers are content-addressed to the repository state.

{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.22\linewidth} >{\raggedright\arraybackslash}p{0.56\linewidth} >{\raggedright\arraybackslash}p{0.14\linewidth}}
\toprule
Witness & Result (with provenance) & Artifact sha256\\
\midrule
%WITNESS_ROWS%
\bottomrule
\end{longtable}
}

All witnesses are synthetic/symbolic methodology checks.  None is an observational result; none uses external data; the Bianchi V seal is constraint algebra under the stated LRS/small-tilt conditions, not a dynamical integration or a geometry claim.

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

REGISTERED REQUIREMENT (M5\('\)): when the K1 covariance is ESTIMATED from a finite simulation ensemble of size \(N_{\rm sim}\), its inverse is a biased precision estimate; before any \(\chi^2\), whitening, or e-value calibration claim, the lane must either apply the Hartlap correction factor \((N_{\rm sim}-m-2)/(N_{\rm sim}-1)\) for \(m\) data dimensions, or replace the Gaussian likelihood by the Sellentin--Heavens multivariate-\(t\) marginalization (external-context citations, \S2.3).  With the expected \(N_{\rm sim}\sim300\)--\(600\) E2E realizations and low-\(\ell\) data dimensions this is a percent-level but REGISTERED effect: omitting it silently inflates the apparent precision of the null calibration.

Registered stretch item: an expansion-normalized tilted-LRS Bianchi~V EVOLUTION check (integrating the Hewitt--Wainwright-type system and verifying that trajectories respect the P5 constraint en route) would upgrade the F2 constraint-algebra seal to a dynamics seal; it is registered here, not claimed.

\subsection{Native low-\(\ell\) handoff}
The solver-design documents are contract sources, not result sources.  A future native route must supply harmonic \(a_{\ell m}^{T,E,B}\), deterministic/stochastic/local-boost output separation, residual packs, transfer provenance, covariance metadata, and atlas/equivalence information before detailed geometry-side inference can be entertained.

\section{Theorem Coverage Ledger}
This table is a ledger, not the argument: every row now points to the body section carrying its statement and proof (the fourth revision closed the seven body-less rows P26--P32).  The P numbering is REGISTRY-STABLE, not body-monotone -- P33--P36 live in \S3.3--3.4 because that is where their mathematics belongs; the Body column is the index map.

{\footnotesize
\begin{longtable}{>{\raggedright\arraybackslash}p{0.08\linewidth} >{\raggedright\arraybackslash}p{0.46\linewidth} >{\raggedright\arraybackslash}p{0.12\linewidth} >{\raggedright\arraybackslash}p{0.14\linewidth} >{\raggedright\arraybackslash}p{0.08\linewidth}}
\toprule
ID & Item & Status & Owner & Body\\
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
Generating command & \code{python scripts/build_external_audit_report_v6.py} followed by local LaTeX build\\
\bottomrule
\end{longtable}

\end{document}
"""
    return (tex.replace("%THEOREM_ROWS%", rows)
               .replace("%VALIDATION_ROWS%", validation_rows)
               .replace("%WITNESS_ROWS%", witness_table_rows))


def audit_response_matrix_ko() -> str:
    return r"""# 외부 감사 반영 매트릭스 v6

이 파일은 공개 보고서 본문에 드러내기 위한 수사적 장치가 아니라, v5 재심사가 지적한 항목이 어떤 과학적 보강으로 반영되었는지 확인하기 위한 내부 추적표이다.

| 재심사 지적 | v6 반영 위치 | 처리 방식 |
|---|---|---|
| B1: W^2 규약 3배 내부 불일치(3.1절 vs P3 vs 제약) | 3.1-3.2절, P3, `parent_identity_seal.json` | \(W^2=\omega_{ab}\omega^{ab}/(6H^2)=\omega_a\omega^a/(3H^2)\)로 통일; parent identity를 본문에 표시; \(c=(1,-1,1,1)\)와 (3/2) 변환규칙을 SymPy로 유도; 3배 mismatch를 seal 안에서 재현+해소; 코드는 이미 등록 규약(문서 전용 수리, x_C 앵커 무손상) |
| B2: P26-P32 원장 등재, 본문 부재 | 3.4절(P26/P31/P35), 4절(P27), 5.2절(P30), 7절(P29), 8.2절(P28), 8.4절(P32) | 전 항목 진술+증명 본문 작성; ledger에 Body 열 추가 |
| M1': tau의 추론적 의미론 미선언 | 3.3-3.4절, P35 | 2단 구성(잔차 m-r 자유도 사양검정 alpha1 + 조건부 r-자유도 집합 alpha2); coverage 정리; Imbens-Manski 끝점 임계값(외부 맥락 인용: Imbens-Manski 2004, Stoye 2009); MC witness(gate E2) |
| M2': 공집합/무계 분기 부재 | 3.4절, A8 | empty = 반증가능성(사양검정, 크기 alpha1, 검정력 곡선 gate E3); unbounded = no-result(P24/P25와 동형) |
| M3': G_F 구간 전파 부재 | P36, P33 도메인 제한 | 공유 성분은 joint feasible set 위의 sup/inf(naive quotient는 진부분집합으로 과대); delta method는 point-identified 전용 |
| M4': 10절 표 provenance 부재 | 10절 | N/seed/SE/다중 임계값/hash 열 추가; E1-E8 witness 표를 결정론적 아티팩트에서 fail-closed 렌더링 |
| M5': 정의식/whitening 편향 잔존 | 3.1절, 12절 | \(\Omega_{tilt}=(1+w)\Omega_m\sinh^2\beta\), \(\Omega_k=-{}^3R/(6H_\theta^2)\), 참조정책(FLAT/MATCHED/NULL) 등록; K1 lane에 Hartlap/Sellentin-Heavens 요건 등록 |
| M6': F>1 무처리 | 3.3절, A2, A8 | ceiling-unfit status clip(조용한 클리핑 금지) |
| 사소 1: Third/second revision 불일치 | 제목/초록 | Fourth Revision으로 일치 |
| 사소 2: x_C^+ 기호 충돌 | P2, 3.3절, A2 | 양수부는 \([x_C]_+\), sup 끝점은 \(x_C^+\)로 분리 |
| 사소 3: MIO-owned posterior 문구 범주 오류 | 초록 | "no posterior or evidence statement is made (HTT-owned; this report makes none)"로 교정 |
| 사소 4: P8 행/열 복제 혼용 | P8 + P30 | 열 복제(P8)와 행 복제(P30, 독립 잡음 2배 / 완전상관 0 이득) 분리 |
| 사소 5: P 번호 비단조 | 13절 ledger | registry-stable 번호 정책 명시 + Body 열 = index map |
| 사소 6: P13 상태 DER 과대 | ledger | DERIVED_CONDITIONAL로 강등 + kappa 편향 곡선 witness(gate F3) |
| kappa 기호 삼중 충돌 | P15 | 응답계수를 lambda_2로 개명(P13/P14의 중력 결합 kappa와 분리) |
| 문헌 배치 부재 | 2.3절 | 외부 문헌 맥락 절(등록된 예외; 증거 아님): Bianchi VII_h 전통, Planck/BBN shear 한계, BipoSH(Hajian-Souradeep), CF4 논쟁, e-value 문헌, 부분식별 문헌 |
"""

def text_payloads() -> dict[str, str]:
    """Every text artifact of the package, regenerated in memory (for --check)."""
    artifacts = load_required_artifacts()
    records = [source_record(src) for src in SOURCE_FILES]
    return {
        TEX_NAME: build_tex(artifacts),
        "SOURCE_INDEX.md": source_index(records),
        "external_audit_content_ledger_ko.md": ledger_ko(),
        "external_audit_evidence_matrix.json": json.dumps(
            evidence_matrix(records), indent=2, ensure_ascii=False),
        "method_validation_summary.json": json.dumps(
            method_validation_summary(), indent=2, ensure_ascii=False),
        "external_audit_response_matrix_ko.md": audit_response_matrix_ko(),
        "MANIFEST.json": json.dumps({
            "package": OUT.name,
            "owner": "manuscript/common",
            "scope": "fourth-revision external audit report for htt_base research (v5 re-review response)",
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
                "Review-cycle witnesses are synthetic/symbolic methodology checks, not observational results.",
                "The Bianchi V seal is constraint algebra under stated conditions, not a dynamics integration or family claim.",
            ],
            "generating_command": "python scripts/build_external_audit_report_v6.py",
            "worktree_state": "git optional; this copied folder may not have git on PATH",
            "generated_at": GENERATED_AT,
        }, indent=2, ensure_ascii=False),
    }


def write_outputs() -> None:
    OUT.mkdir(exist_ok=True)
    for name, content in text_payloads().items():
        (OUT / name).write_text(content, encoding="utf-8")


def check_outputs() -> int:
    stale = []
    for name, content in text_payloads().items():
        path = OUT / name
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(str(path.relative_to(ROOT)))
    if stale:
        print("stale v6 report artifacts:\n  " + "\n  ".join(stale), file=sys.stderr)
        return 1
    print("v6 report text artifacts current (PDF/zip excluded from check)")
    return 0


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="regenerate text artifacts in memory and diff vs disk")
    args = parser.parse_args(argv)
    if args.check:
        return check_outputs()
    write_outputs()
    compile_pdf()
    package_zip()
    print(f"wrote {OUT}")
    print(f"wrote {ROOT / PDF_NAME}")
    print(f"wrote {ROOT / ZIP_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



















