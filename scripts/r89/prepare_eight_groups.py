"""R89: derive eight bounded analysis handoff packages from immutable R78/R86/R87.

Read-only by default. --write creates ONLY the R89 handoff files.
There is no science-run, worker, agent, PR, or task-dispatch operation.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
DEST = BASE / "R89_EIGHT_ANALYSIS_HANDOFF_20261121"
R88_SCRIPT = ROOT / "scripts/r88/run_p0c.py"
SCHEMA = "htt.r89.eight_science_analysis_handoff_only/1"
PIN_BRANCH = "research/r69-observable-physics-bridges-20261118"
PARENT_HEAD = "13820f70a0a5f4b1624faddd871a42805c4f46c8"

# R78 node IDs are frozen. Do not alter the graph, scientific states or
# original dependencies to make these groups runnable.
SPECS = (
    {
        "id": "G01_COMMON", "name": "공통 증거·source authority",
        "nodes": ["E0", "E1", "E2", "E3", "X01", "X02", "X03"],
        "minutes": [15, 45],
        "goal": "Reconcile already scoped-complete foundations and exact source/claims without replaying an entire old science campaign.",
        "source_need": "R78/R86/R87 immutable authority, historical original 42-node science hash, prior evidence locations",
        "stop": "Any citation, source identity or original-state conflict; no post-hoc science promotion",
        "tests": ["tests/obsstat/test_r86_preexecution_readiness.py",
                  "tests/obsstat/test_r88_p0c.py"],
    },
    {
        "id": "G02_CF4", "name": "CF4 거리·PV·방향별 Hubble",
        "nodes": ["SQ-CF4", "H01", "H02", "H03", "H04", "H05", "H06"],
        "minutes": [30, 90],
        "goal": "Reuse R87 35,970-group exact method contrasts/heldout and H03/K02 source-conditioned windows; identify precisely which physical claims remain blocked.",
        "source_need": "CF4 original table3/table4/ReadMe, 35,970 selected NPZ; independent pre-intercalibration calibration response, physical PV and selection law still absent",
        "stop": "Missing independent true S_PV, J_cal Sigma_cal J_cal^T, C_selection or upstream heldout means no physical H(z,n) / posterior / H04 promotion",
        "tests": ["tests/obsstat/test_r87_cf4_p0b.py", "tests/obsstat/test_r83_p2p3_fast.py",
                  "tests/obsstat/test_r88_p0c.py"],
    },
    {
        "id": "G03_GAIA", "name": "Gaia 비방사형 source·VSH",
        "nodes": ["SQ-GAIA", "K01", "K02", "K03", "K04", "K05", "K06"],
        "minutes": [30, 120],
        "goal": "Reuse Gaia CRF/VSH actual source moments, K01/K02 identification and bounded redshift/AGN/scan-alias source diagnostics.",
        "source_need": "Gaia selected catalog/normal-equation artifacts; independent AGN/scan/redshift null and common normal-frame optical response not established",
        "stop": "Do not infer physical normal-frame shear/omega/beta or combined K04/K05 posterior without independent source response and covariance",
        "tests": ["tests/obsstat/test_pre_dag_fast.py", "tests/obsstat/test_r85_p5p6_fast.py"],
    },
    {
        "id": "G04_RADIO_FRAME", "name": "NVSS radio·observer/matter frame",
        "nodes": ["SQ-RADIO", "SQ-FRAME", "V01", "V02", "V03", "V04", "V05", "V06"],
        "minutes": [20, 90],
        "goal": "Reuse actual NVSS 33k pixel/185 ring/3 flux bin source response and local-boost geometry, separating global matter tilt from endpoint copying.",
        "source_need": "R65/R74 NVSS conditional carriers, Planck processed local boost; independent radio selection/LSS null and physical global tilt transfer not established",
        "stop": "No identified global tilt, cross-probe Bayes factor or cosmic detection from a conditional ring score/source-unmatched response",
        "tests": ["tests/obsstat/test_r84_p4_bianchi_fast.py", "tests/obsstat/test_pre_dag_fast.py"],
    },
    {
        "id": "G05_PLANCK", "name": "Planck 저다중극·FFP null",
        "nodes": ["SQ-CMB-NULL", "L01", "L02", "L03", "L04", "L05", "L06"],
        "minutes": [30, 180],
        "goal": "Reuse L01/L02 signed-parity/processed-variant response and existing eight paired FFP pilot ID tests; classify what real release-matched null is missing.",
        "source_need": "Existing same-sky processing/pilot FFP products; full release-matched Commander T/E/B exchangeable signal+noise+foreground null unavailable",
        "stop": "Do not count nine processing variants as independent skies or eight pilot FFP pairs as a calibrated release-matched null; no rarity/p-value promotion",
        "tests": ["tests/obsstat/test_r83_p2p3_fast.py", "tests/obsstat/test_pre_dag_fast.py"],
    },
    {
        "id": "G06_P1", "name": "P1 5-view 통계·identified-set",
        "nodes": ["SQ-P1-ANCHOR", "S01", "S02", "S03", "S04", "S05", "S06"],
        "minutes": [10, 60],
        "goal": "Rerun source-conditioned 2,048 coupled P1 functional draws and exact unknown-mass/anchor-floor checks; preserve conditional interpretation.",
        "source_need": "R82 source-conditioned finite-law arrays; true selected 274-row physical normal-frame anchor and matched observational law unavailable",
        "stop": "Never turn apparent q_app, synthetic floors or unknown physical sectors into physical Pi, G_F or normalized likelihood",
        "tests": ["tests/obsstat/test_r82_p1_fast.py"],
    },
    {
        "id": "G07_BIANCHI", "name": "Bianchi Lie/atlas 입력 적격성",
        "nodes": ["SQ-NATIVE", "SQ-LIE-FLUX", "B01", "B02", "B03", "B04", "B05"],
        "minutes": [15, 60],
        "goal": "Reuse arbitrary Bianchi Lie/Jacobi/Codazzi algebra and B02 external-payload validators without pretending to implement an all-m physical solver.",
        "source_need": "Actual external native polarized all-m transfer histories, IC/mode/Planck response and normal-frame rho,j,pi are unavailable",
        "stop": "No solver substitution, fake native atlas, high-ell transfer evidence, family identification or B03/B04 promotion",
        "tests": ["tests/obsstat/test_r85_p5p6_fast.py", "tests/obsstat/test_r81_phy_fast.py"],
    },
    {
        "id": "G08_OPTICAL_PHY", "name": "Optical 전달·cross-cov·PHY-01..07",
        "nodes": ["SQ-PHOTON-FLUX", "SQ-OPTICAL", "SQ-CROSS-COV",
                  "PHY-01", "PHY-02", "PHY-03", "PHY-04", "PHY-05", "PHY-06", "PHY-07"],
        "minutes": [30, 120],
        "goal": "Reuse R77 PHY theorem/geometry kernels and source-typed optical/cross-probe constraints; only advance independently supported partial cases.",
        "source_need": "Finite-z Sachs/Jacobi/common-congruence transfer, photon higher moments, independent normal-frame sources and joint cross-source covariance/null unavailable",
        "stop": "No spontaneous construction of physical transfer, cosmic Pi/G_F, joint independent null, or physical cross-paper confirmation",
        "tests": ["tests/obsstat/test_r81_phy_fast.py", "tests/obsstat/test_r85_p5p6_fast.py"],
    },
)

class PackageError(ValueError):
    pass


def load_r88():
    spec = importlib.util.spec_from_file_location("r89_source_r88", R88_SCRIPT)
    if spec is None or spec.loader is None:
        raise PackageError("R88 source adapter unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def catalog():
    r88 = load_r88()
    dag, overlay, method, returned = r88.read_authority()
    mapping = {n["id"]: n for n in dag["nodes"]}
    layer = {n["id"]: n for n in overlay["nodes"]}
    positions = {node_id: pos for pos, node_id in enumerate(dag["topological_order"])}
    groups = {}
    flat = []
    for spec in SPECS:
        if spec["id"] in groups:
            raise PackageError("duplicate group ID")
        ids = spec["nodes"]
        if len(ids) != len(set(ids)) or any(i not in mapping for i in ids):
            raise PackageError(f"duplicate/unknown science ID in {spec['id']}")
        flat.extend(ids)
        groups[spec["id"]] = spec
        if spec["minutes"][0] <= 0 or spec["minutes"][1] < spec["minutes"][0]:
            raise PackageError("invalid planning range")
        for path in spec["tests"]:
            if not (ROOT / path).is_file():
                raise PackageError(f"missing existing regression test {path}")
    if len(groups) != 8 or len(flat) != len(set(flat)) != 60 or set(flat) != set(mapping):
        raise PackageError("eight-group partition does not cover exact 60-node SSOT")
    if (sum(n["state"] == "completed_scoped" for n in mapping.values()) != 18
        or sum(n["state"] == "ready_scoped" for n in mapping.values()) != 4
        or dag["next_action_id"] != "SQ-CF4"
        or overlay["agent_dispatch_policy"]["status"] != "BLOCK_LOCAL_AGENT_START"):
        raise PackageError("source-scoped scientific eligibility drift")
    source_status = r88.verify_sources(method, overlay)
    if any(x["status"] == "VERIFIED_BYTES" and x["actual_sha256"] != x["expected_sha256"]
           for x in source_status):
        raise PackageError("source SHA mismatch")
    for item in overlay["coding_stage_checkpoints"]:
        if not item["C10_evidence_present"]:
            raise PackageError("nonsealed code preparation")
    if method["claim_gate"]["actual_full_C_qualified"] or returned["P0_B_true_physical_covariance_status"] != "BLOCKED_INPUT":
        raise PackageError("P0-B physics status may not be upgraded")
    return dag, overlay, mapping, layer, positions, source_status


def _eligibility(node):
    state = node["state"]
    if state == "completed_scoped":
        return "REUSE_SCOPED_PRIOR_EVIDENCE"
    if state == "ready_scoped":
        return "BOUNDED_SOURCE_DIAGNOSTIC_ONLY"
    if state == "theory_verified_physical_data_pending":
        return "THEORY_ONLY_EXTERNAL_DATA_PENDING"
    return "NO_FULL_SCIENCE_EXECUTION"


def build_manifest():
    dag, overlay, nodes, layer, positions, source_status = catalog()
    owner = {nid: spec["id"] for spec in SPECS for nid in spec["nodes"]}
    packages = []
    for spec in SPECS:
        ids = sorted(spec["nodes"], key=positions.__getitem__)
        dependencies = []
        for edge in dag["edges"]:
            if edge["to"] in ids:
                dependencies.append({
                    "from": edge["from"], "to": edge["to"], "kind": edge["kind"],
                    "hard": edge["hard"], "from_group": owner[edge["from"]],
                    "cross_group": owner[edge["from"]] != spec["id"],
                    "source_state": nodes[edge["from"]]["state"],
                })
        upstream = sorted({e["from_group"] for e in dependencies if e["cross_group"]})
        node_records = []
        for id_ in ids:
            original = nodes[id_]
            pre = layer[id_]["pre_execution"]
            node_records.append({
                "id": id_, "paper": original["paper"],
                "node_class": original.get("node_class", "original_science"),
                "r78_state": original["state"], "eligibility": _eligibility(original),
                "depends_on_original": original.get("depends_on", []),
                "goal": original["objective"],
                "acceptance": original["acceptance"],
                "stop": original.get("stop_condition", original.get("next_action", "")),
                "numerical_preflight_sealed": pre["code_preparation_checkpoint_complete"],
                "full_physics_qualified": pre["full_node_physics_execution_qualified"],
                "physical_null_proven": pre["preregistered_new_physical_null_proven"],
                "source_remainder": pre["unresolved_execution_requirement"],
                "actual_code_references": pre["code_module_references"],
            })
        packages.append({
            "group_id": spec["id"], "name": spec["name"], "node_ids": ids,
            "node_count": len(ids),
            "estimate_minutes": {"min": spec["minutes"][0], "max": spec["minutes"][1],
                                 "kind": "PLANNING_HEURISTIC_NOT_END_TO_END_MEASURED"},
            "objective": spec["goal"],
            "required_sources_and_limitations": spec["source_need"],
            "science_stop": spec["stop"], "external_source_cannot_be_assumed": True,
            "upstream_groups": upstream,
            "dependencies_including_overlay": dependencies,
            "nodes": node_records,
            "existing_test_files": spec["tests"],
            "existing_module_paths": sorted({f for n in node_records for f in n["actual_code_references"]}),
            "source_ready_node_ids": [n["id"] for n in node_records if n["r78_state"] == "ready_scoped"],
            "historically_scoped_complete": [n["id"] for n in node_records if n["r78_state"] == "completed_scoped"],
            "unqualified_node_ids": [n["id"] for n in node_records
                                     if n["eligibility"] in ("NO_FULL_SCIENCE_EXECUTION",
                                                              "THEORY_ONLY_EXTERNAL_DATA_PENDING")],
            "write_scope": f"docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/{spec['id']}/",
            "allow_full_science_DAG_dispatch": False, "allow_agent_launch_from_this_packet": False,
            "packet_is_not_execution_authority": True,
        })
    totals = {"min": sum(s["minutes"][0] for s in SPECS),
              "max": sum(s["minutes"][1] for s in SPECS)}
    return {
        "schema": SCHEMA, "date": "2026-11-21 KST",
        "purpose": "eight mutually exclusive bounded analysis work packets, not 60-node science executor",
        "source_branch": PIN_BRANCH, "parent_HEAD_at_preparation": PARENT_HEAD,
        "science_SSOT": str(load_r88().R78.relative_to(ROOT)),
        "science_R78_sha256": load_r88().SHA_R78,
        "R86_overlay_sha256": load_r88().SHA_R86,
        "historical_42_node_sha256": load_r88().SHA_42,
        "R87_result_sha256": load_r88().SHA_R87,
        "nodes": 60, "hard_edges": 129, "stage_seals": 6,
        "historical_scoped_completed": 18, "source_ready_scoped": 4,
        "PHY_theory_only": 7, "original_science_NEXT_ID": "SQ-CF4",
        "whole_program_eligibility": "BLOCK_LOCAL_AGENT_START",
        "source_qualification_may_run_bounded_diagnostics": True,
        "independent_physical_PV_calibration_selection_heldout": "BLOCKED_INPUT",
        "external_native_Bianchi_solver": "UNAVAILABLE_NOT_REPLACED",
        "source_checks_at_package_time": source_status,
        "planning_total_minutes_sequential": totals,
        "planning_limit": "3-12.75 h only for source-bounded review/replay with explicit blocked results; not 60 science completions or external-source acquisition",
        "agent_exec_performed": False, "worker_started": False, "science_states_edited": False,
        "packages": packages,
    }


def render_package(pkg):
    lines = [
        f"# {pkg['group_id']} | {pkg['name']}",
        "",
        "**이 파일은 연구 작업 패킷이며 실행권한이나 START_LOCAL_AGENT 문서가 아니다.**",
        f"해당 {pkg['node_count']}개 노드의 경계 안에서 source 재검증/기존 계산 재현/구체적 결과만 작성한다.",
        f"예측 소요시간: {pkg['estimate_minutes']['min']}–{pkg['estimate_minutes']['max']}분. 이는 전체 물리 완료 시간이 아닌 계획 가정이다.",
        "",
        "## 목표", pkg["objective"], "",
        "## Source, blocking contracts", pkg["required_sources_and_limitations"],
        "STOP: " + pkg["science_stop"], "",
        "## 원본 R78 노드 및 판정",
    ]
    for n in pkg["nodes"]:
        lines.append(f"- {n['id']} | R78={n['r78_state']} | action={n['eligibility']} | preflight={n['numerical_preflight_sealed']}")
    lines += [
        "", "## 그룹 간 선행 패키지",
        ", ".join(pkg["upstream_groups"]) if pkg["upstream_groups"] else "없음. 단, 원본 node dependencies와 scientific acceptance는 불변.",
        "그룹 간 edge는 기존 R78의 hard edge 및 qualification overlay를 그대로 인용한다. "
        "그룹의 numerical preflight가 완료되었다고 선행 과학 노드가 완료된 것은 아니다.",
        "",
        "## 기존 코드 및 테스트",
    ]
    for path in pkg["existing_module_paths"]:
        lines.append(f"- code: {path}")
    lines += ["", "최소 회귀 검증 명령 (기존 checkout):",
              "PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 "
              "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B -m pytest "
              "-p no:cacheprovider -q " + " ".join(pkg["existing_test_files"]), "",
              "## 새 결과 작성 경계",
              f"- 허용된 분석군별 결과 공간: {pkg['write_scope']}",
              "- 원래 R78/R86/R87/R88 원본 DAG, raw source, published result, main, "
              "기존 미추적 사용자 파일은 변경 금지.",
              "- 실제 계산이 필요하면 해당 원본 runner의 argv/입력/생성물 소유권을 먼저 확인하고 "
              "명시된 한정 범위에서만 실행. 코드 확장은 작은 실제 버그 수정 외에는 수행하지 않는다.",
              "- 기존 완료된 증거는 정확한 source ID로 재사용하고 반복 전체 계산은 생략.",
              "- 출력: node별 {NOT_ATTEMPTED, REUSED_SCOPED, DIAGNOSTIC_COMPLETED_SCOPED, "
              "BLOCKED_INPUT, BLOCKED_DEPENDENCY, FAILED} 구분, 변경 파일, 테스트 명령·결과, "
              "source SHA, 남은 물리 결측, 다음 실제 조치.",
              "- 절대 full 60-node science complete, true physical Pi, Bianchi family identified, "
              "release-matched null PASS, local agent START를 주장하지 않는다.",
              "",
        ]
    return "\n".join(lines).rstrip("\n") + "\n"


def render_master(manifest):
    ids = [p["group_id"] for p in manifest["packages"]]
    return f"""# Local coding agent handoff | R89 eight analysis work packages

작업 위치: /home/cosmosapjw/Dropbox/bianchi/htt_base
기준 브랜치: {PIN_BRANCH}
기준 Git 부모 커밋: {PARENT_HEAD} (이 R89 패키지 게시 커밋은 후속 HEAD일 수 있다)
정본: docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json
작업 묶음: docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/MANIFEST.json

목표: 원래 60노드를 정확히 여덟 개의 source/분석군으로 분배하여, 기존 코드를 최대한 재사용하는 실질적인 한정 분석을 순차적으로 수행하라. 이 프롬프트는 60개 과학 노드의 무조건적 production START나 허위 완료를 승인하지 않는다.

실행 전:
1. AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md, R78 INTEGRATED_DAG, R86 EXECUTION_READINESS_DAG, R87 P0-B 과학 반환, R88 P0-C 보고 및 이 R89 MANIFEST를 읽어라. 현재 git HEAD, branch, 추적/미추적 dirty, 원본 source SHA를 확인하라.
2. PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/r89/prepare_eight_groups.py --check 와 R78 validate_unified.py --strict-authority 를 실행하라. 60 unique IDs/129 hard edges/8 그룹/원래 42 science hash/C10 6/6/원래 NEXT_ID SQ-CF4를 검증하고 기존 R78/R86의 scientific state를 절대로 변경하지 마라.
3. 작업 그룹 순서는 {' → '.join(ids)}. 동일한 자료와 수치 계산은 이전 패키지의 정확한 결과를 재사용하라. 그룹 간 hard dependency는 R78/R86 그대로 적용하고, block된 노드는 수치 코드가 있어도 물리학적 성공으로 승격하지 마라.

각 그룹:
- 해당 PACKET_*.md 및 MANIFEST.json의 구체적 node, 입력, stop, 코드/테스트, write ownership만 수행하라. 한 분석군의 허용 결과 영역은 R89/runs/<group_id>/이며 서로 겹치지 않는다.
- 이미 completed_scoped인 노드는 증거만 확인하고 전체 재계산은 하지 않는다. ready_scoped 네 노드(SQ-CF4, SQ-GAIA, SQ-RADIO, SQ-FRAME)는 실제 source-dependent bounded 진단만 할 수 있다. 나머지는 원래 상태를 유지한 채 기존 커널 회귀·증거 확인·입력 blocker 분류까지만 수행한다.
- CF4 original group table은 이미 global MCMC intercalibration을 거쳤고 true S_PV, J_cal Sigma_cal J_cal^T, C_selection, independent upstream heldout는 결측이다. Planck 9 processes를 독립 sky로 세지 말고 8 pilot FFP를 full null이라 주장하지 않는다. 물리적 광자/Bianchi native solver나 공통 congruence transfer는 만들어내지 않는다.
- 기존 runner가 실제 실행 가능한 것으로 확인되면 source hash와 create-only output 경계에서만 계산하라. 미확보 외부 입력을 합성자료로 메우지 마라. 증거를 보존할 의미가 있을 때에만 코드/수치·출력 등을 새로 작성하고, 대형 구현 대신 기존 code paths를 우선하라.
- 로컬 자원은 매 패키지 시작 시 실제 측정하라. 기존 C8의 millisecond 숫자는 커널 전용이지 전체 pipeline 시간이 아니다. 35,970x35,970 dense float64 covariance는 행렬 한 장만 약 9.64 GiB이므로 불필요한 dense 복제·nested BLAS/OpenMP 과할당을 피하라. GPU 가용성은 검증 전 가정하지 마라.
- 그룹별 최소 검증(기존 테스트), 실제 artifact, 물리/수치/구현/환경 오류 구분, 한 번의 합당한 독립 검토 후 같은 active research branch에 그 그룹만 선택적으로 commit/push하라. 실질적 새 결과가 없는 봉쇄 사례는 빈 커밋을 만들지 말고 기존 근거와 정확한 BLOCKED 결과를 반환하라. 원격 identity를 확인하되 main merge, force push, unrelated dirty staging, 자동 PR/status 변경은 하지 마라. 검증이 실패하면 실제 blocker를 기록하고 거기서 더 이상 승격하지 마라.
- Return/report: 그룹ID, 원래 IDs, source/provenance, 실행한 실제 명령과 exit, 새 수치 결과 또는 정확한 재사용 근거, test outcome, 서브노드별 REUSED_SCOPED / DIAGNOSTIC_COMPLETED_SCOPED / BLOCKED_INPUT / BLOCKED_DEPENDENCY / NOT_ATTEMPTED / FAILED, 기존 논문 claim 판정 변경 없음, commit/remote result 또는 미게시 이유, 다음 실행 가능한 물리 작업. 끝에서 60개 원본 ID의 커버리지와 유일성을 합산하되 60/60 SCIENCE PASS로 표현하지 마라.

중단 조건: R78/R86/R87 authority mismatch, source hash drift, 현재 브랜치 충돌, 실제 미확보 physical covariance/null, 소유권 충돌, native solver 부재로 인한 수학적 결론 부족 등. 차단된 분석군은 BLOCKED_INPUT을 남기고 독립된 다른 그룹의 안전한 source 진단을 계속할 수 있으나, 전체 60노드 자동 연속 science execution이나 local-agent START 파일 발행은 금지다.

이번 위임은 8개 bounded analysis packages의 실행이다. 별도 요청이 없는 한 전체 논문 자동 제출·merge나 외부 raw 데이터 교체를 하지 마라.
"""


def all_artifacts(manifest):
    arts = {"MANIFEST.json": json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            "HANDOFF_PROMPT_KO.md": render_master(manifest)}
    for pkg in manifest["packages"]:
        arts[f"PACKET_{pkg['group_id']}.md"] = render_package(pkg)
    return arts


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Validate existing generated files; read-only")
    mode.add_argument("--write", action="store_true", help="Create/update R89 handoff files only")
    mode.add_argument("--group", metavar="GROUP_ID", help="Print one bounded packet to stdout; no execution")
    args = cli.parse_args(argv)
    try:
        manifest = build_manifest()
        artifacts = all_artifacts(manifest)
        if args.group:
            pkg = next((p for p in manifest["packages"] if p["group_id"] == args.group), None)
            if pkg is None:
                raise PackageError(f"unknown group ID: {args.group}")
            print(json.dumps(pkg, indent=2, ensure_ascii=False))
            return 0
        if args.write:
            DEST.mkdir(parents=True, exist_ok=True)
            for name, content in artifacts.items():
                (DEST / name).write_text(content, encoding="utf-8")
        elif args.check:
            for name, content in artifacts.items():
                if not (DEST / name).is_file() or (DEST / name).read_bytes() != content.encode("utf-8"):
                    raise PackageError(f"missing or stale handoff artifact: {name}")
        print(json.dumps({"state": "HANDOFF_PREPARED_ONLY", "action": "WRITE" if args.write else "CHECK",
                          "groups": len(manifest["packages"]), "node_ids_unique": manifest["nodes"],
                          "edges": manifest["hard_edges"], "source_ready_scoped": 4,
                          "source_physics_block": "BLOCKED_INPUT", "agent_dispatched": False,
                          "artifacts": len(artifacts),
                          "planned_min_minutes": manifest["planning_total_minutes_sequential"]["min"],
                          "planned_max_minutes": manifest["planning_total_minutes_sequential"]["max"]},
                         ensure_ascii=False))
        return 0
    except (PackageError, ValueError, KeyError, TypeError, OSError) as exc:
        print(f"R89 FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
