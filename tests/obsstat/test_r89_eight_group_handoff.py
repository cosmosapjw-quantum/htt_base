"""R89 eight-group handoff contract: coverage, authority, no-dispatch."""
from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/r89/prepare_eight_groups.py"
spec = importlib.util.spec_from_file_location("r89_handoff", SCRIPT)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


@pytest.fixture(scope="module")
def manifest():
    return h.build_manifest()


def test_partition_exact_60_unique_and_129_original_hard_edges(manifest):
    assert manifest["nodes"] == 60
    assert manifest["hard_edges"] == 129
    assert len(manifest["packages"]) == 8
    flat = [nid for p in manifest["packages"] for nid in p["node_ids"]]
    assert len(flat) == len(set(flat)) == 60
    assert [p["node_count"] for p in manifest["packages"]] == [7, 7, 7, 8, 7, 7, 7, 10]
    r88 = h.load_r88()
    original, _, _, _ = r88.read_authority()
    assert set(flat) == {n["id"] for n in original["nodes"]}


def test_every_node_state_and_science_eligibility_is_original(manifest):
    r88 = h.load_r88()
    original, overlay, _, _ = r88.read_authority()
    states = {n["id"]: n["state"] for n in original["nodes"]}
    pre = {n["id"]: n["pre_execution"] for n in overlay["nodes"]}
    for pkg in manifest["packages"]:
        for node in pkg["nodes"]:
            assert node["r78_state"] == states[node["id"]]
            assert node["full_physics_qualified"] is False
            assert node["physical_null_proven"] is False
            assert node["numerical_preflight_sealed"]
            assert node["eligibility"] == h._eligibility({"state": states[node["id"]]})
            assert node["source_remainder"] == pre[node["id"]]["unresolved_execution_requirement"]
    assert manifest["historical_scoped_completed"] == 18
    assert manifest["source_ready_scoped"] == 4
    assert manifest["PHY_theory_only"] == 7


def test_exact_four_bounded_source_qualifiers(manifest):
    available = {node for p in manifest["packages"] for node in p["source_ready_node_ids"]}
    assert available == {"SQ-CF4", "SQ-GAIA", "SQ-RADIO", "SQ-FRAME"}
    assert manifest["original_science_NEXT_ID"] == "SQ-CF4"
    assert manifest["whole_program_eligibility"] == "BLOCK_LOCAL_AGENT_START"
    assert manifest["independent_physical_PV_calibration_selection_heldout"] == "BLOCKED_INPUT"
    assert manifest["external_native_Bianchi_solver"] == "UNAVAILABLE_NOT_REPLACED"


def test_all_129_edges_accounted_for_once_with_correct_group_ownership(manifest):
    packages = manifest["packages"]
    owner = {node: p["group_id"] for p in packages for node in p["node_ids"]}
    edges = [e for p in packages for e in p["dependencies_including_overlay"]]
    assert len(edges) == 129
    assert len({(e["from"], e["to"], e["kind"]) for e in edges}) == 129
    for edge in edges:
        assert edge["hard"]
        assert edge["from_group"] == owner[edge["from"]]
        assert edge["cross_group"] == (owner[edge["from"]] != owner[edge["to"]])
    assert any(e["cross_group"] for e in edges)


def test_plan_not_executable_or_science_complete(manifest):
    assert manifest["agent_exec_performed"] is False
    assert manifest["worker_started"] is False
    assert manifest["science_states_edited"] is False
    for pkg in manifest["packages"]:
        assert not pkg["allow_full_science_DAG_dispatch"]
        assert not pkg["allow_agent_launch_from_this_packet"]
        assert pkg["packet_is_not_execution_authority"]
        assert pkg["write_scope"].endswith(pkg["group_id"] + "/")
        assert pkg["external_source_cannot_be_assumed"]


def test_time_budget_is_planning_only_not_physical_runtime(manifest):
    totals = manifest["planning_total_minutes_sequential"]
    assert totals == {"min": 180, "max": 765}
    assert all(p["estimate_minutes"]["kind"] == "PLANNING_HEURISTIC_NOT_END_TO_END_MEASURED"
               for p in manifest["packages"])
    assert "not 60 science completions" in manifest["planning_limit"]


def test_sanity_of_original_CF4_source_ownership_and_block(manifest):
    files = manifest["source_checks_at_package_time"]
    assert len(files) == 4
    assert all(f["status"] in ("VERIFIED_BYTES", "MISSING_BLOCKED_INPUT") for f in files)
    assert all((f["status"] != "VERIFIED_BYTES" or f["actual_sha256"] == f["expected_sha256"])
               for f in files)
    cf4 = next(p for p in manifest["packages"] if p["group_id"] == "G02_CF4")
    assert "SQ-CF4" in cf4["source_ready_node_ids"]
    assert "S_PV" in cf4["science_stop"]
    assert "C_selection" in cf4["science_stop"]


def test_generated_packet_text_includes_source_and_safety(manifest):
    for pkg in manifest["packages"]:
        text = h.render_package(pkg)
        assert pkg["name"] in text
        assert pkg["science_stop"] in text
        assert "원래 R78" in text
        assert "START_LOCAL_AGENT" in text
        assert "physical Pi" in text
        assert all(n in text for n in pkg["node_ids"])
    master = h.render_master(manifest)
    assert "60개 과학 노드" in master
    assert all(p["group_id"] in master for p in manifest["packages"])
    assert "60/60 SCIENCE PASS" in master


def test_generator_artifacts_present_and_byte_consistent(manifest):
    generated = h.all_artifacts(manifest)
    assert len(generated) == 10
    assert sum(k.startswith("PACKET_") for k in generated) == 8
    for name, contents in generated.items():
        path = h.DEST / name
        assert path.is_file()
        assert path.read_bytes() == contents.encode("utf-8")


def test_no_start_artifacts_present_in_output_directory():
    assert not list(h.DEST.glob("START_LOCAL_AGENT*"))
    assert not list(h.DEST.glob("*DISPATCH*"))
    assert not (h.DEST / "runs").exists()


def test_missing_group_fails_closed(capsys):
    assert h.main(["--group", "G09_NOT_FOUND"]) == 2
    assert "FAIL_CLOSED" in capsys.readouterr().err


def test_single_group_cli_prints_data_does_not_write(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert h.main(["--group", "G03_GAIA"]) == 0
    pkg = json.loads(capsys.readouterr().out)
    assert pkg["group_id"] == "G03_GAIA"
    assert pkg["allow_agent_launch_from_this_packet"] is False
    assert not list(tmp_path.iterdir())


def test_missing_manifest_in_check_mode_fails_closed(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(h, "DEST", tmp_path / "unpublished")
    assert h.main(["--check"]) == 2
    assert "missing or stale" in capsys.readouterr().err


def test_write_mode_only_writes_ten_handoff_files(tmp_path, monkeypatch, capsys):
    empty = tmp_path / "new_packets"
    monkeypatch.setattr(h, "DEST", empty)
    assert h.main(["--write"]) == 0
    files = sorted(p.name for p in empty.iterdir())
    assert len(files) == 10
    assert "MANIFEST.json" in files
    assert "HANDOFF_PROMPT_KO.md" in files
    assert not any(name.startswith("START_LOCAL_AGENT") for name in files)
    assert h.main(["--check"]) == 0


def test_partition_missing_node_cannot_be_accepted(monkeypatch):
    specs = deepcopy(h.SPECS)
    specs[0]["nodes"].pop()
    monkeypatch.setattr(h, "SPECS", tuple(specs))
    with pytest.raises(h.PackageError, match="eight-group partition"):
        h.build_manifest()


def test_partition_duplicate_cannot_be_accepted(monkeypatch):
    specs = deepcopy(h.SPECS)
    specs[0]["nodes"][-1] = specs[0]["nodes"][0]
    monkeypatch.setattr(h, "SPECS", tuple(specs))
    with pytest.raises(h.PackageError, match="duplicate/unknown"):
        h.build_manifest()
