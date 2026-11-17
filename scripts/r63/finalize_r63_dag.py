"""Insert the authorized R63 scoped DAG once, only after completed research and review.

This file is a prepared mutation utility. Reading/importing it does not mutate files.
Run explicitly from the existing checkout (or pass --root) after R1-R9/C1-C9
and the fresh independent review have closed. It neither runs a successor loop nor
changes original paper acceptances, original42 nodes, or other PR cards.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml

BASELINE = "f29bbab420a33aecb1c398ddd961fd45097f536b"
CORE_HASH = "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
PR = "PR-R63-LOCAL-BOOST-GLOBAL-TILT"
PARENT = "PR-R62-ANISOTROPY-CLASSIFICATION"
BASE = Path("docs/research_program/observational_publication_20261015")
FOLDER = BASE / "R63_LOCAL_BOOST_GLOBAL_TILT_20261117"


def digest(value):
    # Preserve the original programme's exact canonical JSON hash convention.
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load_json(path):
    return json.loads(path.read_text())


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def run(root, review_status):
    root = Path(root).resolve()
    if not review_status.strip():
        raise ValueError("an explicit review summary is required")
    folder = root / FOLDER
    record = load_json(folder / "RESEARCH_RECORD.json")
    if record.get("baseline_commit") != BASELINE or record.get("selected_paper") != "P4":
        raise ValueError("research record is not the selected R63 baseline/P4 study")
    stages = record.get("stages", [])
    if len(stages) != 10 or any(
        s.get("number") != j or s.get("status") != "complete"
        for j, s in enumerate(stages[:9], 1)
    ):
        raise ValueError("exactly ten stages and completed R1-R9/C1-C9 are required")
    if record.get("submission_status") != "NOT_READY_TO_SUBMIT":
        raise ValueError("research record changed the submission decision")
    review_path = folder / "REVIEW/final_review.json"
    if not review_path.is_file():
        raise ValueError("fresh independent final-review artifact missing")
    review = load_json(review_path)
    if review.get("verdict") != "PASS" or "findings" not in review:
        raise ValueError("fresh final review has not returned PASS with explicit findings")
    if any(f.get("status") != "CLOSED" for f in review["findings"]):
        raise ValueError("fresh independent-review findings remain open")
    submission = review.get("journal_submission", review.get("submission_status"))
    if submission != "NOT_READY_TO_SUBMIT":
        raise ValueError("review must preserve NOT_READY_TO_SUBMIT")
    if any(review.get(k) not in (None, "NOT_READY_TO_SUBMIT")
           for k in ("journal_submission", "submission_status")):
        raise ValueError("conflicting final-review submission decisions")

    summary_path = folder / "RESULTS/INTERPRETATION_SUMMARY.json"
    summary = load_json(summary_path)
    if summary.get("publication_status") != "NOT_READY_TO_SUBMIT":
        raise ValueError("interpretation summary changed the submission decision")
    if summary.get("free_history_fits") != 14 or summary.get("n_operators") != 7:
        raise ValueError("unexpected actual-data experiment dimensions")
    for field in ("W_p_J2_corrected", "W_p_J3_corrected", "max_U_chart_shift_norm_km_s",
                  "max_power_body", "body", "sources"):
        if field not in summary:
            raise ValueError("corrected interpretation field missing: " + field)

    titles = [
        ("Fix one P4 question and the actual existing-checkout baseline",
         ["RESEARCH_RECORD.json", "DESIGN.md"]),
        ("Reuse PR/branch history, actual carrier identities and primary sources",
         ["REVIEW/r63_history.md", "REVIEW/r63_history_sources.json",
          "REVIEW/r63_literature.md", "REVIEW/r63_sources.json"]),
        ("Bind frames, physical history, source units and catalogue corrections",
         ["DESIGN.md", "THEORY.md", "REVIEW/r63_cf4_contract.md",
          "REVIEW/r63_frame_r3_contract.md"]),
        ("Select the finite actual-CF4 response and physical-power experiment",
         ["DESIGN.md"]),
        ("Construct processed endpoint/history responses and implement the finite experiment",
         ["THEORY.md", "REVIEW/WOLFRAM_CHECK.json"]),
        ("Verify affected response, physical-body, projector and Gaussian code",
         ["RESULTS/AFFECTED_TEST_RECEIPT.json"]),
        ("Execute owned CF4 source responses and finite physical-history comparisons",
         ["RESULTS/OBSERVED_EXECUTION_01.json", "RESULTS/OBSERVED/FRAME_HISTORY_RESULT.json"]),
        ("Transport the actual catalogue chart and decide physical-scale discrimination and publication route",
         ["RESULTS/CF4_PUBLISHED_Q_DIAGNOSTIC.json", "RESULTS/CHART_TRANSPORT_EXECUTION.json",
          "RESULTS/CATALOGUE_CHART_TRANSPORT.json", "RESULTS/INTERPRETATION_SUMMARY.json", "REPORT_KO.md", "RESEARCH_PLAN_KO.md",
          "REVIEW/r63_remote_dipole_map.md"]),
        ("Close one fresh independent review and its bounded correction episode",
         ["REVIEW/final_review.md", "REVIEW/final_review.json", "VALIDATION.md"]),
        ("Preserve the finite P4 plan, canonical DAG and authorized scoped release",
         ["RESEARCH_PLAN_KO.md", "VALIDATION.md", "DAG_VALIDATION.json"]),
    ]
    # Stages 1-9 must cite files which exist before canonical mutation.
    missing = sorted({str(FOLDER / p) for _, ev in titles[:9] for p in ev
                      if not (folder / p).is_file()})
    if missing:
        raise ValueError("completed-stage evidence files missing: " + ", ".join(missing))

    backlog_rel = Path("docs/codex_handoff/pr_backlog.yaml")
    status_rel = Path("docs/codex_handoff/pr_status.yaml")
    backlog, status = root / backlog_rel, root / status_rel
    old_text, status_text = backlog.read_text(), status.read_text()
    old, status_before = yaml.safe_load(old_text), yaml.safe_load(status_text)
    if len(old["prs"]) != 286 or len(status_before["completed"]) != 221:
        raise ValueError("canonical backlog/completed counts changed from 286/221")
    if any(c["id"] == PR for c in old["prs"]) or PR in status_before["completed"]:
        raise ValueError("R63 already exists; this finalizer is one-shot")
    if not any(c["id"] == PARENT for c in old["prs"]) or PARENT not in status_before["completed"]:
        raise ValueError("R62 predecessor is not preserved and completed")

    files = [
        str(FOLDER), "scripts/r63", "tests/r63", "htt/htt/htt/infer/r63_frame_history.py",
        str(backlog_rel), str(status_rel), str(BASE / "PUBLICATION_DAG.json"),
        str(BASE / "README.md"),
    ]
    card = dict(
        id=PR, wave=0,
        title="Distinguish processed local endpoints and compensated histories on actual CF4 data",
        owner="HTT", depends=[PARENT], files=files,
        tests=[
            "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider -q tests/r63 tests/r58/test_mixed_tensor_likelihood.py tests/r58/test_five_views.py",
            ".venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml",
            ".venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check",
            ".venv/bin/python -B scripts/htt_publication_dag.py --validate",
        ],
        dod=[
            "Complete exactly one integrated ten-stage owner-selected P4 study using existing primary sources, history and actual owned CF4 operators/covariance.",
            "Derive explicit observer/source/catalogue-frame fibres and transport the restricted compensated physical history into the actual eta chart.",
            "Execute full-vector/STF rank and physical-size discrimination calculations with shared nuisance, full cross covariance and unphysical tangent estimates labelled.",
            "Preserve the actual published additive-redshift correction through same-law affine transport and retain unresolved heterogeneous distance/flux response.",
            "Close one fresh independent final review; preserve original42 gates, old paper contracts and NOT_READY_TO_SUBMIT with a finite source/independent-channel plan.",
        ],
        notes=str(FOLDER / "RESEARCH_DAG.json"),
        kill="No physical superluminal W measurement, unrestricted global-tilt exclusion, invented aberration covariance or adopted unresolved kSZ amplitude limit; no automatic successor or local-agent prompt.",
        level="L0", scope="science", risk="R2", claim_tier_ceiling="C0",
        user_authorized=True,
        authorization="2026-11-17 owner explicitly selected local observer boost versus global tilt in one full ten-stage branch; inherited non-force GitHub publication authority persists.",
    )
    needle = "  - " + PARENT + "\n"
    if old_text.count(needle) != 2:
        raise ValueError("expected two predecessor entries in topological/strict-extension orders")
    updated = old_text.replace(needle, needle + "  - " + PR + "\n")
    updated = updated.rstrip() + "\n" + yaml.safe_dump(
        [card], sort_keys=False, allow_unicode=True, width=105)
    parsed = yaml.safe_load(updated)
    if len(parsed["prs"]) != 287 or parsed["prs"][:-1] != old["prs"]:
        raise ValueError("existing PR cards were not preserved")
    # Only predecessor-adjacent list insertions are allowed outside prs.
    def remove_new_pr(value):
        if isinstance(value, dict):
            return {k: remove_new_pr(v) for k, v in value.items()}
        if isinstance(value, list):
            return [remove_new_pr(v) for v in value if v != PR]
        return value
    if remove_new_pr({k: v for k, v in parsed.items() if k != "prs"}) != {
        k: v for k, v in old.items() if k != "prs"
    }:
        raise ValueError("existing backlog metadata changed")

    if PR in status_text or "\ncompleted:\n" not in status_text:
        raise ValueError("unexpected status source")
    status_new = status_text.replace("\ncompleted:\n", "\ncompleted:\n- " + PR + "\n", 1)
    status_new += (
        "\n# " + PR + ": complete_scoped C0. Actual CF4 endpoint/history response, "
        "same-law catalogue correction and physical-size power bound; original42/P4 "
        "acceptance preserved. No detection, automatic successor or local-agent prompt.\n"
    )
    status_after = yaml.safe_load(status_new)
    expected_status = copy.deepcopy(status_before)
    expected_status["completed"] = [PR] + expected_status["completed"]
    if status_after != expected_status or len(status_after["completed"]) != 222:
        raise ValueError("status mutation exceeds the single authorized completion")

    publication = root / BASE / "PUBLICATION_DAG.json"
    pub = load_json(publication)
    if len(pub["nodes"]) != 42 or digest(pub["nodes"]) != CORE_HASH:
        raise ValueError("original42 science-node payload changed")
    original_papers = copy.deepcopy(pub["papers"])
    previous = copy.deepcopy(pub["current_scientific_route"])
    if previous["canonical_pr"] != PARENT:
        raise ValueError("unexpected current scientific route")
    p4 = [p for p in pub["papers"] if p["id"] == "P4"]
    if len(p4) != 1 or "current_scoped_frame_discrimination" in p4[0]:
        raise ValueError("P4 companion pointer missing/duplicated or already added")
    pub.setdefault("previous_scientific_routes", []).append(previous)
    pub["current_scientific_route"] = dict(
        date="2026-11-17", source_base_sha=BASELINE, canonical_pr=PR, selected_paper="P4",
        scope="Only local observer boost, coherent bulk and source-constrained compensated global-history discrimination; one integrated ten-stage study",
        report=str(FOLDER / "REPORT_KO.md"), plan=str(FOLDER / "RESEARCH_PLAN_KO.md"),
        research_dag=str(FOLDER / "RESEARCH_DAG.json"), status="COMPLETE_SCOPED_C0",
        review=review_status, active_result=str(FOLDER / "RESULTS/INTERPRETATION_SUMMARY.json"),
        original_six_tracks_and_42_gates_preserved=True, automatic_successor=False,
        local_agent_prompt_created=False, submission_status="NOT_READY_TO_SUBMIT",
        authorization="Current explicit owner ten-stage branch request; inherited non-force GitHub publication authority.",
    )
    p4[0]["current_scoped_frame_discrimination"] = dict(
        pr=PR, report=str(FOLDER / "REPORT_KO.md"), plan=str(FOLDER / "RESEARCH_PLAN_KO.md"),
        research_dag=str(FOLDER / "RESEARCH_DAG.json"),
        original_acceptance_status_preserved=True,
    )
    restored_papers = copy.deepcopy(pub["papers"])
    next(p for p in restored_papers if p["id"] == "P4").pop("current_scoped_frame_discrimination")
    if restored_papers != original_papers or digest(pub["nodes"]) != CORE_HASH:
        raise ValueError("original paper contracts or original42 states changed")
    pub["next_action"] = (
        "Preserve R63's conditional P4 result; recover remote-dipole amplitude normalization, "
        "window/bias and electron/photon source contract, qualify finite physical/catalogue "
        "errors, then decide a source-matched independent-channel comparison. Qualified "
        "aberration joint law is the bounded fallback. No automatic successor or further "
        "unchanged CF4 fitting loop."
    )

    tasks = [
        dict(id=f"R63-{j:02d}", theory_stage=f"R{j}", coding_stage=f"C{j}", title=title,
             depends_on=[] if j == 1 else [f"R63-{j-1:02d}"],
             status="complete_scoped", evidence=evidence)
        for j, (title, evidence) in enumerate(titles, 1)
    ]
    future = [
        dict(id="P4-R63-REMOTE-NORMALIZATION", depends_on=["R63-10"], status="unresolved_input",
             needed="Resolve the published remote-dipole D_h versus D_C amplitude and likelihood normalization from an exact public source; neither conditional 26 km/s conversion is an adopted physical U limit.",
             stop="If exact normalization remains unavailable, preserve both labelled arithmetic maps and stop this source path."),
        dict(id="P4-R63-REMOTE-SOURCE", depends_on=["P4-R63-REMOTE-NORMALIZATION"], status="unresolved_input",
             needed="Bind normalized reconstruction window/moments, optical-depth bias law and joint uncertainty, electron-to-dust and photon-to-compensating-radiation matching, endpoint-map response and actual inherited likelihood/prior.",
             acceptance="Transport w_eff=[1+z/(1+R)] n.U with window/bias uncertainty; no invented Cartesian Gaussian or double bias correction."),
        dict(id="P4-R63-PHYSICAL-ERROR", depends_on=["R63-10"], status="unresolved_input",
             needed="Bound the finite-interval observer/Doppler and quadratic stress/metric/optical remainder for the selected source model; retain physical-body versus necessary-superset distinction.",
             acceptance="The qualified projected error must be smaller than the proposed channel's discriminating signal."),
        dict(id="P4-R63-CATALOGUE-CALIBRATION", depends_on=["R63-10"], status="unresolved_input",
             completed="Actual published redshift-chart affine transport completed; tied U max shift and corrected W tests recorded.",
             needed="Qualify heterogeneous CF4 distance/flux deboost, method/group response, selection and calibration covariance; preserve existing estimator and conditional coefficient results."),
        dict(id="P4-R63-ABERRATION-JOINT", depends_on=["R63-10"], status="conditional_fallback",
             trigger="Remote-source normalization/likelihood path cannot be qualified.",
             needed="Obtain actual joint aberration/Doppler vector likelihood or posterior with dipole-distortion, lensing, mask/noise/foreground and shared-CMB covariance; scalar amplitude/direction bars are not a substitute."),
        dict(id="P4-R63-CHANNEL-DECISION",
             depends_on=["P4-R63-PHYSICAL-ERROR", "P4-R63-CATALOGUE-CALIBRATION"],
             alternative_input_paths=[["P4-R63-REMOTE-SOURCE"], ["P4-R63-ABERRATION-JOINT"]],
             status="pending_conditional",
             needed="Use one qualified independent channel to cut the endpoint/history fibre, with shared-state covariance/coverage and physical source conditions.",
             screening="At alpha=.1 and target power=.8, oracle mean distance delta>=Phi^-1(.8)-Phi^-1(.1) about2.12 is necessary, not sufficient; no unchanged CF4 expansion when its bound remains about2.4e-6."),
        dict(id="P4-R63-PAPER", depends_on=["P4-R63-CHANNEL-DECISION"], status="pending_conditional",
             needed="Decide one methods/application or source-qualified physical manuscript at achieved claim level; consolidate R63 into existing companion/appendix if standalone novelty remains thin.",
             stop="No accepted independent channel/remainder means preserve P4 HOLD/NOT_READY rather than launch a new unchanged loop."),
    ]
    result_fields = (
        "n_sources", "n_operators", "n_source_orders", "free_history_fits",
        "base_and_physical_fits", "J2_depth_calibration_fits", "chart_transported_fits",
        "W_p_J2_corrected", "W_p_J3_corrected", "W_sd_all_components_km_s",
        "unphysical_tangent_estimate_count", "full_history_target_ranks",
        "dipole_only_history_target_ranks", "power_alpha", "max_power_body",
        "max_power_300", "max_distance_body", "body", "max_U_chart_shift_norm_km_s",
        "max_affine_parity_error", "max_free_W_physical_ball_likelihood_delta_bound",
    )
    scoped = dict(
        schema="htt.r63.research_dag/1", baseline_commit=BASELINE, canonical_pr=PR,
        parent_pr=PARENT, selected_paper="P4", claim_tier="C0",
        scope="Single ten-stage local-observer/source-history discrimination study",
        status="COMPLETE_SCOPED_C0", tasks=tasks, future_science=future,
        original_42_node_payload_sha256=CORE_HASH, original_42_node_states_changed=False,
        key_results={k: summary[k] for k in result_fields},
        interpretation_sources=summary["sources"],
        conditions="Fixed inherited Gaussian covariance and finite source model; unphysical unconstrained tangent W is not a measured velocity; no general globality or independent-channel admission.",
        automatic_successor=False, local_agent_prompt_created=False,
        submission_status="NOT_READY_TO_SUBMIT",
    )

    readme = root / BASE / "README.md"
    programme_text = readme.read_text()
    header = "# HTT 관측논문 6트랙 출판 중심 DAG\n\n"
    old_header = "## Current anisotropy classification study — R62, 2026-11-17"
    if programme_text.count(header) != 1 or programme_text.count(old_header) != 1:
        raise ValueError("programme README differs from the observed R62 baseline")
    programme_text = programme_text.replace(
        old_header, "## Previous anisotropy classification study — R62, 2026-11-17", 1)
    programme_text = programme_text.replace(
        "현재 선택된 P5 companion 경로다", "이전 P5 companion 경로다", 1)
    entry = (
        "## Current local-boost/global-history discrimination study — R63, 2026-11-17\n\n"
        "[R63 실제 자료·프레임 결과](R63_LOCAL_BOOST_GLOBAL_TILT_20261117/REPORT_KO.md), "
        "[유한 P4 논문 계획](R63_LOCAL_BOOST_GLOBAL_TILT_20261117/RESEARCH_PLAN_KO.md), "
        "[연구 DAG](R63_LOCAL_BOOST_GLOBAL_TILT_20261117/RESEARCH_DAG.json)이 현재 선택된 P4 "
        "companion 경로다. 원본 CF4의 35,970개 group과 전체 covariance를 재사용해 endpoint "
        "fibre, 물리적으로 제한한 history의 약한 rank3 및 actual-q affine transport를 계산했다. "
        "dipole12만으로는 같은 nuisance 아래 history rank0이며, full32에서 rank3가 남아도 "
        "선택한 물리 body의 oracle power 상한은 alpha=.1에서 .100000419 이하다. 이는 고정 "
        "Gaussian 실험의 조건부 결과이며 global tilt 검출이나 보편적 불가능성 정리가 아니다. "
        "기존 P4 companion keys·paper acceptance와 원래42개 과학 gate를 보존한다. "
        "submission은 NOT_READY_TO_SUBMIT이며 자동 다음 루프·로컬 agent prompt는 없다.\n\n"
    )
    programme_text = programme_text.replace(header, header + entry, 1)

    receipt = dict(
        canonical_card_added=PR, old_backlog_entries=286, new_backlog_entries=287,
        old_completed_count=221, new_completed_count=222,
        previous_cards_semantically_unchanged=True, original_node_payload_sha256=CORE_HASH,
        original_nodes_unchanged=True, original_paper_contracts_preserved=True,
        old_P4_companion_keys_preserved=True, selected_scope="P4 companion only",
        review=review_status, interpretation_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        automatic_successor=False, local_agent_prompt_created=False,
    )
    # Validate serialization and all input gates before the first mutation.
    payloads = {
        backlog: updated, status: status_new, publication: encoded(pub),
        readme: programme_text, folder / "RESEARCH_DAG.json": encoded(scoped),
        folder / "DAG_UPDATE_RECEIPT.json": encoded(receipt),
    }
    if any(p.exists() for p in (folder / "RESEARCH_DAG.json", folder / "DAG_UPDATE_RECEIPT.json")):
        raise ValueError("scoped DAG or receipt already exists; refuse a repeated insertion")
    for path, contents in payloads.items():
        path.write_text(contents)
    print(encoded(receipt), end="")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--review-status", required=True)
    args = parser.parse_args()
    run(args.root, args.review_status)
