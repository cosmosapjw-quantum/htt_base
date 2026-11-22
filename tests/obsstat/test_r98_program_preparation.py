"""Meaningful authority/dependency and science non-promotion regression."""
import json
from pathlib import Path
import pytest
from scripts.r98 import program_preparation as p

@pytest.fixture
def manifest(tmp_path,monkeypatch):
    monkeypatch.setattr(p,"OUT",tmp_path)
    return p.build()

def test_all_exact_ids_and_qualification_edges(manifest):
    canonical=json.loads(p.DAG.read_text())
    assert {n["id"] for n in manifest["nodes"]}=={n["id"] for n in canonical["nodes"]}
    assert manifest["counts"]["nodes"]==60
    assert manifest["counts"]["edges"]==129
    assert manifest["counts"]["node_payload_dependencies"]==118
    assert manifest["canonical_edges"]==canonical["edges"]
    rows={n["id"]:n for n in manifest["nodes"]}
    for target,sources in canonical["source_qualification_overlay"].items():
        assert set(sources)<=set(rows[target]["effective_hard_dependencies"])
    assert "SQ-RADIO" in rows["V04"]["effective_hard_dependencies"]
    assert {"D05","M06"}<=set(rows["V04"]["all_blockers_including_dependencies"])

def test_no_science_promotion_or_unknown_package(manifest):
    assert manifest["counts"]["new_science_nodes_promoted"]==0
    assert manifest["counts"]["original_scoped_completed"]==18
    assert manifest["counts"]["distinct_open_obligations"]=={"DATA":6,"MODEL":9,"ADDITIONAL_ANALYSIS":6}
    for row in manifest["nodes"]:
        assert not row["new_acceptance_claimed"]
        assert row["preparation_packages"]
        assert set(row["preparation_packages"])<=set(manifest["packages"])
        if row["science_status"]=="SCIENCE_BLOCKED":
            assert row["all_blockers_including_dependencies"]

def test_science_entry_fails_closed(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(p,"OUT",tmp_path)
    def forbidden(*a,**k):raise AssertionError("blocked science must not launch calculation")
    monkeypatch.setattr(p.subprocess,"run",forbidden)
    assert p.main(["--node","SQ-CF4","--mode","science","--execute"])==3
    data=json.loads(capsys.readouterr().out)
    assert data["science_command_executed"] is False
    assert {"D01","D02","M01"}<=set(data["blockers"])

def test_inherited_scoped_status_does_not_execute_science(tmp_path,monkeypatch,capsys):
    monkeypatch.setattr(p,"OUT",tmp_path)
    monkeypatch.setattr(p.subprocess,"run",lambda *a,**k:pytest.fail("unexpected execution"))
    assert p.main(["--node","E0","--mode","science","--execute"])==0
    assert json.loads(capsys.readouterr().out)["science_command_executed"] is False

def test_authority_drift_is_rejected(tmp_path,monkeypatch):
    changed=tmp_path/"dag.json";changed.write_bytes(p.DAG.read_bytes()+b"\n")
    monkeypatch.setattr(p,"DAG",changed)
    with pytest.raises(RuntimeError,match="authority changed"):p.build()
