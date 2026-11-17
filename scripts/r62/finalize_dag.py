"""Apply the authorized R62 scoped DAG insertion exactly once, after review."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def run(review_status):
    base = Path("docs/research_program/observational_publication_20261015")
    folder = base / "R62_ANISOTROPY_CLASSIFICATION_20261117"
    pr, parent = "PR-R62-ANISOTROPY-CLASSIFICATION", "PR-R61-KINEMATIC-MEASUREMENT"
    record = json.loads((folder / "RESEARCH_RECORD.json").read_text())
    if any(s["status"] != "complete" for s in record["stages"][:9]):
        raise ValueError("R1-R9/C1-C9 must be complete before the stage10 insertion")
    if not (folder / "REVIEW/final_review.json").exists():
        raise ValueError("fresh review artifact missing")
    final_review = json.loads((folder / "REVIEW/final_review.json").read_text())
    if final_review["verdict"] != "PASS" or any(f["status"] != "CLOSED" for f in final_review["findings"]):
        raise ValueError("independent review is not closed")
    if final_review["journal_submission"] != "NOT_READY_TO_SUBMIT":
        raise ValueError("unexpected manuscript decision")
    backlog, status = Path("docs/codex_handoff/pr_backlog.yaml"), Path("docs/codex_handoff/pr_status.yaml")
    old_text = backlog.read_text()
    old = yaml.safe_load(old_text)
    if any(c["id"] == pr for c in old["prs"]):
        raise ValueError("R62 card already exists; finalizer is one-shot")
    if len(old["prs"]) != 285:
        raise ValueError("canonical backlog changed from reviewed baseline")
    files = [str(folder), "scripts/r62", "tests/r62", "htt/htt/htt/infer/r62_tensor_classes.py",
             "htt/bass/background/tilted_bianchi_state.py", "htt/bass/background/convention_bridge.py",
             "htt/bass/diagnostics/bianchi_similarity.py", str(backlog), str(status), str(base / "PUBLICATION_DAG.json")]
    card = dict(id=pr, wave=0,
        title="Classify source-aware CF4 tensor confidence sets and actual Bianchi tilt constraints",
        owner="HTT", depends=[parent], files=files,
        tests=["OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider -q tests/r62 tests/r49/test_gbi01_convention_bridge.py tests/r49/test_gbi02_tilted_state_and_constraints.py htt/bass/diagnostics/test_bianchi_similarity.py",
               ".venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml",
               ".venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check",
               ".venv/bin/python -B scripts/htt_publication_dag.py --validate"],
        dod=["Complete exactly one owner-selected ten-stage classification study using existing theory, PR/branch history and owned observed inputs.",
             "Retain actual source operators, signed STF basis, full cross-window covariance and fixed-law conditions in 21/26-parameter source responses.",
             "Execute all declared class queries with exact-class feasible witnesses or sound necessary exclusions, without nonlinear Wilks/model-probability claims.",
             "Correct actual-state Bianchi momentum admissibility and velocity Jacobian; preserve source/frame and initial-slice/evolution boundaries.",
             "Complete one fresh independent review, finite paper plan and additive P5 companion linkage; preserve original42 gates and NOT_READY_TO_SUBMIT."],
        notes=str(folder / "RESEARCH_DAG.json"),
        kill="No Bianchi family/tilt/physical shear detection from phenomenological tensors; no canonical-IX universal no-tilt claim; no independent multiplication of correlated nuisance experiments; no automatic successor or local-agent prompt.",
        level="L0", scope="science", risk="R2", claim_tier_ceiling="C0", user_authorized=True,
        authorization="2026-11-17 owner explicitly selected anisotropy classification including Bianchi/tilt and all ten theory/coding stages; earlier non-force GitHub push authorization persists.")
    needle = "  - " + parent + "\n"
    if old_text.count(needle) != 2:
        raise ValueError("expected topological and strict-extension predecessor entries")
    updated = old_text.replace(needle, needle + "  - " + pr + "\n")
    updated = updated.rstrip() + "\n" + yaml.safe_dump([card], sort_keys=False, allow_unicode=True, width=105)
    parsed = yaml.safe_load(updated)
    if len(parsed["prs"]) != 286 or parsed["prs"][:-1] != old["prs"]:
        raise ValueError("existing PR cards were not preserved")
    status_text = status.read_text()
    status_before = yaml.safe_load(status_text)
    if pr in status_text or "\ncompleted:\n" not in status_text:
        raise ValueError("unexpected status input")
    status_new = status_text.replace("\ncompleted:\n", "\ncompleted:\n- " + pr + "\n", 1)
    status_new += "\n# " + pr + ": complete_scoped C0. Source-aware CF4 class compatibility, common-offset quotient, actual-operator injection and state-dependent Bianchi/tilt repair. Original42 science gates and P5 acceptance preserved. No family discovery, automatic successor or local-agent prompt.\n"
    if len(yaml.safe_load(status_new)["completed"]) != len(status_before["completed"]) + 1:
        raise ValueError("unexpected completed-card count")

    publication = base / "PUBLICATION_DAG.json"
    pub = json.loads(publication.read_text())
    core_hash = digest(pub["nodes"])
    if core_hash != "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d":
        raise ValueError("original science node payload changed")
    original_papers = copy.deepcopy(pub["papers"])
    previous = pub["current_scientific_route"]
    if previous["canonical_pr"] != parent:
        raise ValueError("unexpected current scientific route")
    pub.setdefault("previous_scientific_routes", []).append(previous)
    pub["current_scientific_route"] = dict(
        date="2026-11-17", source_base_sha="c118982e56ee50d68dd0446aa10f16ffe65bd02b",
        canonical_pr=pr, selected_paper="P5",
        scope="Only anisotropy classification including conditional Bianchi/tilt; one integrated ten-stage study",
        report=str(folder / "REPORT_KO.md"), plan=str(folder / "RESEARCH_PLAN_KO.md"), research_dag=str(folder / "RESEARCH_DAG.json"),
        status="COMPLETE_SCOPED_C0", review=review_status,
        active_result=str(folder / "RESULTS/INTERPRETATION_SUMMARY.json"),
        original_six_tracks_and_42_gates_preserved=True, automatic_successor=False,
        local_agent_prompt_created=False, submission_status="NOT_READY_TO_SUBMIT",
        authorization="Current explicit owner ten-stage branch request; inherited non-force GitHub publication authority.")
    for paper in pub["papers"]:
        if paper["id"] == "P5":
            if "current_scoped_classification" in paper:
                raise ValueError("existing P5 companion pointer must not be overwritten")
            paper["current_scoped_classification"] = dict(pr=pr, report=str(folder / "REPORT_KO.md"),
                plan=str(folder / "RESEARCH_PLAN_KO.md"), research_dag=str(folder / "RESEARCH_DAG.json"),
                original_acceptance_status_preserved=True)
    restored_papers = copy.deepcopy(pub["papers"])
    for paper in restored_papers:
        if paper["id"] == "P5":
            paper.pop("current_scoped_classification")
    if restored_papers != original_papers or digest(pub["nodes"]) != core_hash:
        raise ValueError("original publication contracts changed")
    pub["next_action"] = "Use R62's finite P5 companion plan: qualify physical source/normal-frame response and calibration before Bianchi attribution; reuse observed class constraints and action equivalences. No automatic successor loop."

    titles = [
        ("Fix the single classification question and live baseline", ["RESEARCH_RECORD.json", "REVIEW/history_map.md"]),
        ("Reuse internal PR/branch research and verify primary sources", ["REVIEW/history_sources.json", "REVIEW/literature_map.md"]),
        ("Define tensor classes, source response and actual constraint fibres", ["DESIGN.md", "THEORY.md"]),
        ("Select finite class/calibration and actual-source experiments", ["DESIGN.md"]),
        ("Derive and implement class witnesses and Bianchi repairs", ["THEORY.md", "REVIEW/WOLFRAM_CHECK.json"]),
        ("Validate affected scientific implementations", ["RESULTS/AFFECTED_TEST_RECEIPT.json"]),
        ("Execute actual CF4 and conditional Bianchi constructions", ["RESULTS/SOURCE_EXECUTION.json", "RESULTS/CLASSIFICATION_EXECUTION.json", "RESULTS/BIANCHI_EXAMPLES.json"]),
        ("Interpret source-order sensitivity and observable limits", ["RESULTS/INTERPRETATION_SUMMARY.json", "REPORT_KO.md"]),
        ("Complete one fresh independent final review and bounded repair", ["REVIEW/final_review.md", "REVIEW/final_review.json", "REVIEW/R62_F1_CLOSURE.json", "RESULTS/INHERITED_SN_REUSE.json"]),
        ("Finalize the finite paper plan, DAG and authorized release", ["RESEARCH_PLAN_KO.md", "VALIDATION.md", "DAG_VALIDATION.json"])]
    tasks = [dict(id=f"R62-{j:02d}", theory_stage=f"R{j}", coding_stage=f"C{j}", title=title,
                  depends_on=[] if j == 1 else [f"R62-{j-1:02d}"], status="complete_scoped", evidence=evidence)
             for j, (title, evidence) in enumerate(titles, 1)]
    future = [
        dict(id="P5-R62-RESPONSE", depends_on=["R62-10"], status="unresolved_input", needed="Source/congruence-qualified distance response linking signed observed tensors to normal shear; preserve identifiable quotients and truncation error."),
        dict(id="P5-R62-OPTICS", depends_on=["P5-R62-RESPONSE"], status="pending_conditional", needed="If low-z truncation is insufficient, close it with candidate-limited null-geodesic/Jacobi transport using admissible backgrounds, without imposing a Boltzmann hierarchy."),
        dict(id="P5-R62-CALIBRATION", depends_on=["R62-10"], status="unresolved_input", needed="Independent angular/depth calibration and matched-source covariance/selection information; propagate arbitrary calibration through the actual estimator bias map."),
        dict(id="P5-R62-REPLICATION", depends_on=["P5-R62-RESPONSE", "P5-R62-CALIBRATION"], status="pending", completed_in_R62="Four inherited qualified SN STF carriers reused; all contain zero", needed="Extend existing public-SN assets to a source-matched distance likelihood with physical frame, source/host/calibration overlap and shared-PV covariance handled."),
        dict(id="P5-R62-GEOMETRY", depends_on=["P5-R62-REPLICATION"], status="unresolved_input", needed="Constrain actual Bianchi momentum/curvature fibres using normal stress, frame transport and connection/curvature-derivative or explicit evolution closure; report action-equivalence candidate sets."),
        dict(id="P5-R62-PAPER", depends_on=["P5-R62-REPLICATION"], status="pending", needed="One manuscript decision at the achieved observable or physical-geometry claim level; consolidate into existing paper if standalone scientific contribution remains insufficient.")]
    scoped = dict(schema="htt.r62.research_dag/1", baseline_commit="c118982e56ee50d68dd0446aa10f16ffe65bd02b",
        canonical_pr=pr, parent_pr=parent, selected_paper="P5", claim_tier="C0", scope="Single ten-stage anisotropy-classification study",
        status="COMPLETE_SCOPED_C0", tasks=tasks, future_science=future,
        original_42_node_payload_sha256=core_hash, original_42_node_states_changed=False,
        key_results=dict(n_sources=35970, n_carriers=42, class_queries=210, structured_class_intersections=168,
                         J2_varying_zero_p=[.6204076028460508, .888056401799735], J3_varying_zero_p=[.6256041282048106, .9398175605562865],
                         inherited_SN_carriers=4, inherited_SN_zero_intersections=4,
                         Bianchi_family_detected=False, source_operator_frame_preservation="Counterexample executed",
                         independent_review_finding="R62-FR-01 CLOSED; scale-relative physical constraints"),
        conditions="Fixed Gaussian working law and finite observed-z source response; no unconditional shear, full LRS or family attribution.",
        automatic_successor=False, local_agent_prompt_created=False, submission_status="NOT_READY_TO_SUBMIT")
    readme = base / "README.md"
    text = readme.read_text()
    header = "# HTT 관측논문 6트랙 출판 중심 DAG\n\n"
    if header not in text or "## Current kinematic measurement study — R61, 2026-11-17" not in text:
        raise ValueError("programme README has changed")
    text = text.replace("## Current kinematic measurement study — R61, 2026-11-17", "## Previous kinematic measurement study — R61, 2026-11-17", 1)
    text = text.replace("현재 선택된 P6 가지의 진입점이다", "이전 P6 연구의 진입점이다", 1)
    entry = "## Current anisotropy classification study — R62, 2026-11-17\n\n[R62 관측 분류·물리 심사](R62_ANISOTROPY_CLASSIFICATION_20261117/REPORT_KO.md), [단일 논문 계획](R62_ANISOTROPY_CLASSIFICATION_20261117/RESEARCH_PLAN_KO.md), [연구 DAG](R62_ANISOTROPY_CLASSIFICATION_20261117/RESEARCH_DAG.json)이 현재 선택된 P5 companion 경로다. 실제 CF4 source response와 공분산으로 42개 carrier·210개 class 질문을 계산했다. 네 형태 클래스는 모두 공동 신뢰영역에 남으며 Bianchi family 검출을 주장하지 않는다. 관측 연산자의 apparent-frame 반례와 실제 상태의 Bianchi/tilt 제약 교정을 포함한다. 원래 P5 acceptance 및 42개 과학 gate는 유지하며 submission 상태는 NOT_READY_TO_SUBMIT이다.\n\n"
    text = text.replace(header, header + entry, 1)
    # All validations precede canonical mutation.
    backlog.write_text(updated)
    status.write_text(status_new)
    publication.write_text(json.dumps(pub, indent=2, ensure_ascii=False) + "\n")
    readme.write_text(text)
    (folder / "RESEARCH_DAG.json").write_text(json.dumps(scoped, indent=2, ensure_ascii=False) + "\n")
    receipt = dict(canonical_card_added=pr, old_backlog_entries=285, new_backlog_entries=286,
                   old_completed_count=len(status_before["completed"]), new_completed_count=len(status_before["completed"])+1,
                   previous_cards_semantically_unchanged=True, original_node_payload_sha256=core_hash,
                   original_nodes_unchanged=True, original_paper_contracts_preserved=True, selected_scope="P5 companion only", review=review_status)
    (folder / "DAG_UPDATE_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-status", required=True)
    run(parser.parse_args().review_status)
