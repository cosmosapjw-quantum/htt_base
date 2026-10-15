"""Six-paper progress utility tests, distinct scientific manuscript status."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts"))
from htt_publication_dag import load
from htt_publication_progress import report


def test_research_scoped_progress_partitions_all_42_nodes():
    result=report(load())
    assert result["all_task_nodes"]==42
    assert result["completed_scoped_nodes"]==9
    assert result["ready_nodes"]==6
    assert result["blocked_external_nodes"]==7
    assert result["waiting_dependency_nodes"]==20
    assert result["completed_scoped_fraction"]==9/42
    assert result["completed_scoped_percent"]==100*9/42
    assert result["manuscript_submission_gates_passed"]==0
    assert result["manuscript_submission_gates_total"]==6
    assert result["pending_scientific_claims_are_not_node_completion"]


def test_no_paper_submission_claim_in_six_track_snapshot():
    x=report(load())
    by=x["scoped_progress_by_track"]
    assert set(by)=={"COMMON","P1","P2","P3","P4","P5","P6"}
    assert by["COMMON"]["completed_scoped"]==5
    assert by["P1"]["completed_scoped"]==1
    assert by["P2"]["completed_scoped"]==0
    assert by["P3"]["completed_scoped"]==2
    assert by["P4"]["completed_scoped"]==1
    assert all(by[p]["completed_scoped"]==0 for p in ("P5","P6"))
    assert x["manuscript_status"]=="0/6: NOT_READY_TO_SUBMIT"
    old=ROOT/"docs/research_program/observational_publication_20261015/DAG_PROGRESS_20261015_phase_null.json"
    prior=json.loads(old.read_text())
    assert prior["completed_scoped_nodes"]==8  # immutable prior scientific checkpoint
    assert prior["ready_nodes"]==7
    saved=ROOT/"docs/research_program/observational_publication_20261015/DAG_PROGRESS_20261015_finite_boost.json"
    assert json.loads(saved.read_text())==x  # current bounded one-event boost checkpoint


def test_selection_ledger_completed_only_retrospective_registration():
    d=load()
    by={t["id"]:t for t in d["nodes"]}
    assert by["X03"]["state"]=="completed_scoped"
    assert by["L02"]["state"]=="pending"
    assert by["L03"]["external_missing"]
    assert by["X03"]["claim_tier"].startswith("SCOPED")
    assert all((ROOT/p).exists() for p in by["X03"]["existing_evidence"])
    source=ROOT/"docs/research_program/observational_publication_20261015/CLAIM_SELECTION_LEDGER.json"
    ledger=json.loads(source.read_text())
    assert ledger["prospective_confirmatory_registration_created"] is False
    assert all(record["confirmatory"] is False for record in ledger["papers"])
