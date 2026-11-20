"""R88 P0-C: source-authority, DAG and no-start regression tests."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/r88/run_p0c.py"
spec = importlib.util.spec_from_file_location("r88_p0c", SCRIPT)
p0c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p0c)


@pytest.fixture(scope="module")
def packet():
    # The actual four source files are rehashed, not replaced by mocks.
    return p0c.build_packet("SQ-CF4")


def test_exact_source_and_60_node_129_hard_edge_authority(packet):
    dag, readiness, source, returned = p0c.read_authority()
    assert len(dag["nodes"]) == len(set(n["id"] for n in dag["nodes"])) == 60
    assert len(dag["edges"]) == 129 and all(e["hard"] for e in dag["edges"])
    assert dag["next_action_id"] == packet["science_graph"]["next_science_node"] == "SQ-CF4"
    assert packet["science_graph"]["original_42_sha256"] == p0c.SHA_42
    assert readiness["agent_dispatch_policy"]["status"] == "BLOCK_LOCAL_AGENT_START"
    assert returned["P0_B_true_physical_covariance_status"] == "BLOCKED_INPUT"
    assert source["original_released_group_count"] == 38053


def test_selected_source_prerequisites_and_stop_conditions(packet):
    assert [(x["node_id"], x["state"]) for x in packet["prerequisites"]] == [
        ("E1", "completed_scoped"), ("X01", "completed_scoped"), ("H01", "completed_scoped")]
    assert "method" in packet["node_contract"]["acceptance"].lower()
    assert packet["node_contract"]["stop_condition"]
    assert packet["science_graph"]["hard_edges"] == 129


def test_four_original_data_hashes_match_real_bytes(packet):
    checks = packet["input_contract"]["source_provenance"]
    assert len(checks) == 4
    assert all(c["status"] == "VERIFIED_BYTES" and
               c["actual_sha256"] == c["expected_sha256"] for c in checks)
    assert packet["input_contract"]["selected_groups"] == 35970
    assert packet["input_contract"]["original_method_indicators"] == 7
    assert packet["input_contract"]["error_bearing_multi_method_groups"] == 922
    assert packet["input_contract"]["already_globally_intercalibrated"]


def test_missing_physics_is_blocked_not_invented(packet):
    assert packet["status"] == "BLOCKED_INPUT"
    physics = packet["physics_status"]
    assert physics["source_gate"] == "BLOCKED_INPUT"
    assert len(physics["missing_inputs"]) == 4
    for name in ("S_PV", "J_cal_Sigma_cal_J_cal_T", "C_selection",
                 "independent_null", "physical_Pi"):
        assert physics[name] is None
    assert not packet["physical_posterior_admitted"]
    assert not packet["science_execution_authorized"]


@pytest.mark.parametrize("node", ["B02", "S02", "SQ-GAIA", "E0", "BAD-NODE"])
def test_any_other_node_fails_closed(node):
    with pytest.raises(p0c.PolicyDenied):
        p0c.build_packet(node)


@pytest.mark.parametrize("frame", ["NORMAL_CONGRUENCE", "LOCAL_OBSERVER", "ICRS", "GALACTIC", ""])
def test_observer_frame_drift_fails_closed(frame):
    with pytest.raises(p0c.PolicyDenied):
        p0c.build_packet("SQ-CF4", frame)


def test_original_dag_byte_tamper_fails_closed(tmp_path, monkeypatch):
    cloned = json.loads(p0c.R78.read_text(encoding="utf-8"))
    cloned["next_action_id"] = "B02"
    bad = tmp_path / "bad_r78.json"
    bad.write_text(json.dumps(cloned), encoding="utf-8")
    monkeypatch.setattr(p0c, "R78", bad)
    with pytest.raises(p0c.ContractError, match="SHA256 mismatch"):
        p0c.read_authority()


def test_readiness_overlay_byte_tamper_fails_closed(tmp_path, monkeypatch):
    cloned = json.loads(p0c.R86.read_text(encoding="utf-8"))
    cloned["agent_dispatch_policy"]["dispatch_performed"] = True
    bad = tmp_path / "bad_r86.json"
    bad.write_text(json.dumps(cloned), encoding="utf-8")
    monkeypatch.setattr(p0c, "R86", bad)
    with pytest.raises(p0c.ContractError, match="SHA256 mismatch"):
        p0c.read_authority()


def test_original_data_byte_tamper_fails_closed(tmp_path, monkeypatch):
    _, readiness, source, _ = p0c.read_authority()
    original_source_path = p0c.source_path
    damaged = tmp_path / "table3.dat"
    damaged.write_bytes(b"one tampered byte")
    monkeypatch.setattr(p0c, "source_path",
                        lambda name: damaged if name.endswith("table3.dat") else original_source_path(name))
    with pytest.raises(p0c.ContractError, match="source byte mismatch"):
        p0c.verify_sources(source, readiness)


def test_missing_source_does_not_forge_verification(tmp_path, monkeypatch):
    _, readiness, source, _ = p0c.read_authority()
    original_source_path = p0c.source_path
    missing = tmp_path / "missing.dat"
    monkeypatch.setattr(p0c, "source_path",
                        lambda name: missing if name.endswith("table3.dat") else original_source_path(name))
    checks = p0c.verify_sources(source, readiness)
    assert checks[0]["status"] == "MISSING_BLOCKED_INPUT"
    assert checks[0]["actual_sha256"] is None


def test_r83_seal_sha_tamper_rejected():
    _, readiness, _, _ = p0c.read_authority()
    altered = copy.deepcopy(readiness)
    for item in altered["coding_stage_checkpoints"]:
        if item["group"].startswith("R83_"):
            item["C10_SHA256"] = "0" * 64
    with pytest.raises(p0c.ContractError, match="C10 SHA mismatch"):
        p0c.verify_seals(altered)


def test_graph_edge_tamper_rejected():
    dag, readiness, _, _ = p0c.read_authority()
    bad = copy.deepcopy(dag)
    bad["edges"][0]["hard"] = False
    with pytest.raises(p0c.ContractError):
        p0c.verify_graph(bad, readiness)


def test_cli_never_writes_or_dispatches(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    before = {p.name for p in tmp_path.iterdir()}
    assert p0c.main(["--node", "SQ-CF4", "--dry-run"]) == 0
    generated = json.loads(capsys.readouterr().out)
    after = {p.name for p in tmp_path.iterdir()}
    assert before == after == set()
    assert generated["operation"] == "READ_ONLY_DRY_RUN"
    assert generated["status"] == "BLOCKED_INPUT"
    assert generated["file_writes"] is False
    assert generated["agent_dispatched"] is False
    assert generated["start_local_agent_published"] is False
    assert generated["output_ownership"]["new_science_output_path"] is None


def test_cli_requires_explicit_dry_run(capsys):
    with pytest.raises(SystemExit) as exc:
        p0c.main(["--node", "SQ-CF4"])
    assert exc.value.code == 2
    assert "--dry-run required" in capsys.readouterr().err


def test_cli_denied_node_exits_nonzero(capsys):
    assert p0c.main(["--dry-run", "--node", "B02"]) == 2
    rejected = json.loads(capsys.readouterr().err)
    assert rejected["status"] == "REJECTED_FAIL_CLOSED"
    assert rejected["agent_dispatched"] is False
