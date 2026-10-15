"""Focused six-paper research DAG semantics; no astrophysical PASS implied."""
import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "scripts/htt_publication_dag.py"
spec=importlib.util.spec_from_file_location("htt_publication_dag",MODULE)
dag=importlib.util.module_from_spec(spec)
spec.loader.exec_module(dag)


def test_actual_six_paper_program_unique_and_acyclic():
    x=dag.load()
    info=dag.validate(x)
    assert info["paper_count"]==6
    assert info["node_count"]==42
    assert info["submission_gates"]==6
    assert info["reused_evidence_anchors"]==12  # original 4, H01/H03/S01, X03/V01, K01/K02 and S02 scoped
    assert {p["id"] for p in x["papers"]}=={"P1","P2","P3","P4","P5","P6"}
    assert all(p["publication_status"]=="NOT_READY_TO_SUBMIT" for p in x["papers"])


def test_ready_is_actual_dependency_scoped_not_priority_confusion():
    x=dag.load()
    selected={n["id"] for n in dag.ready(x)}
    assert selected=={"X01","X02","L01","B01"}
    assert not {"L03","H02","V03","B02","K03"}&selected
    assert all(v["id"] not in selected for v in dag.blocked(x))


def test_blocked_input_does_not_block_independent_study():
    x=dag.load()
    blocked={v["id"] for v in dag.blocked(x)}
    assert {"L03","H02","S04","V03","B02","K03","K04"} <= blocked
    assert "H03" not in blocked
    assert "S02" not in {v["id"] for v in dag.ready(x)}
    assert "S03" not in {v["id"] for v in dag.ready(x)}


def test_no_invented_ready_paper_after_technical_prereq_completed():
    x=dag.load()
    byid={v["id"]:v for v in x["nodes"]}
    for paper in ("P1","P2","P3","P4","P5","P6"):
        term=next(v for v in x["nodes"] if v["paper"]==paper and v["submission_terminal"])
        assert dag.resolved_status(term,byid)!="ready"
        assert term["state"]=="pending"


def test_task_packet_exact_task_and_provenance_limits():
    x=dag.load()
    pkt=dag.task_packet(x,"S02")
    assert pkt["status"]=="completed_scoped"
    assert pkt["task"]["paper"]=="P1"
    assert "S01" in pkt["task"]["depends_on"]
    assert pkt["scientific_limits"]["same_sky_independence"]=="NOT_ASSUMED"
    assert pkt["paper"]["publication_status"]=="NOT_READY_TO_SUBMIT"


def test_dag_export_derived_is_hash_stable_and_non_scheduling():
    x=dag.load()
    a=dag.derived_queue(x)
    b=dag.derived_queue(dag.load())
    assert a==b
    assert len(a["ready"])==4
    assert not a["background_scheduler"]
    assert a["scientific_claim"]=="NOT_READY_TO_SUBMIT"


def test_dependency_cycle_refused():
    x=copy.deepcopy(dag.load())
    anchor=next(i for i in x["nodes"] if i["id"]=="E0")
    anchor["depends_on"]=["K06"]
    with pytest.raises(dag.PublicationDAGError,match="cycle"):
        dag.validate(x)


def test_unknown_dependency_refused():
    x=copy.deepcopy(dag.load())
    x["nodes"][-1]["depends_on"].append("ABSENT-R99")
    with pytest.raises(dag.PublicationDAGError,match="dependency"):
        dag.validate(x)


def test_false_paper_promotion_rejected():
    x=copy.deepcopy(dag.load())
    x["papers"][0]["publication_status"]="READY_TO_SUBMIT"
    with pytest.raises(dag.PublicationDAGError,match="submission readiness"):
        dag.validate(x)


def test_completed_without_receipt_rejected():
    x=copy.deepcopy(dag.load())
    x["nodes"][0]["existing_evidence"]=[]
    with pytest.raises(dag.PublicationDAGError,match="unverified completion"):
        dag.validate(x)


def test_no_sixth_terminal_guard_rejected():
    x=copy.deepcopy(dag.load())
    next(z for z in x["nodes"] if z["id"]=="K06")["submission_terminal"]=False
    with pytest.raises(dag.PublicationDAGError,match="publication gate"):
        dag.validate(x)


def test_base_source_snapshot_keeps_byte_and_semantic_ownership_distinct():
    import json
    src=ROOT/"docs/research_program/observational_publication_20261015/SOURCE_CROSSWALK_AT_DESIGN.json"
    doc=json.loads(src.read_text())
    assert doc["owner_dirty_status"]=="PRESERVE_NOT_MUTATED"
    assert doc["same_sky_products"]=="NOT_INDEPENDENT"
    records=doc["records"]
    assert len(records)==9 and len({s["id"] for s in records})==9
    for item in records:
        assert len(item["sha256_checked_20261015"])==64
        assert item["size_bytes"]>0
        assert not item["new_measurement"]
    assert sum(s["authority"]=="LOCAL_ONLY_UNTRACKED_AT_REDESIGN" for s in records)==3
    assert sum(s["authority"]=="TRACKED_BASE_COMMIT_CONTENT" for s in records)==6


def test_six_distinct_paper_definitions_and_claim_selection_present():
    x=dag.load()
    paper={p["id"]:p for p in x["papers"]}
    assert "Pi" in paper["P1"]["estimands"]
    assert "O(3)" in paper["P2"]["estimands"]
    assert "Theta/3" in paper["P3"]["estimands"]
    assert "beta_RM" in paper["P4"]["estimands"]
    assert "Bianchi" in paper["P5"]["title"]
    assert "sigma_ab" in paper["P6"]["estimands"]
    assert x["policy"]["posthoc"]=="HISTORICAL RETROSPECTIVE RESULTS NOT CONFIRMATORY"
    assert all(not p["planned_pr_is_open"] for p in x["papers"])


def test_actual_progress_keeps_partial_physics_gate_pending_and_source_receipts():
    x=dag.load()
    byid={n["id"]:n for n in x["nodes"]}
    for id_ in ("S01","H01","H03"):
        z=byid[id_]
        assert z["state"]=="completed_scoped"
        assert z["existing_evidence"]
        for ref in z["existing_evidence"]:
            assert (ROOT/ref).is_file(), (id_,ref)
    assert byid["L01"]["state"]=="pending" and byid["L01"]["existing_evidence"]
    assert byid["K01"]["state"]=="completed_scoped"
    assert byid["K02"]["state"]=="completed_scoped"
    assert byid["K02"]["existing_evidence"]
    for ref in byid["K01"]["existing_evidence"]:
        assert (ROOT/ref).is_file(), ("K01",ref)
    assert byid["H02"]["external_missing"]
    assert not [z for z in x["papers"] if z["publication_status"]!="NOT_READY_TO_SUBMIT"]
