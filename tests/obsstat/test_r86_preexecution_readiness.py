"""R86 pre-execution checker must never dispatch / mutate original R78 DAG."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]
PKG=ROOT/"scripts/r86_audit_preexecution.py"
spec=importlib.util.spec_from_file_location("r86audit",PKG)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_exact_60_coding_ordinals_are_distinct_from_science_topological_order():
    z=mod.audit()
    assert [n["pre_execution"]["coding_ordinal_1_to_60"] for n in z["nodes"]]!=list(range(1,61))
    order={n["id"]:n["pre_execution"]["coding_ordinal_1_to_60"] for n in z["nodes"]}
    assert set(order)==set(z["topological_order"])
    assert len(order)==60 and len(z["edges"])==129
    assert order["SQ-CF4"]==1 and order["SQ-NATIVE"]==11
    assert order["S06"]==31 and order["H03"]==40
    assert order["B02"]==51 and order["K06"]==60


def test_original_science_42_states_and_60_graph_remain_untouched():
    z=mod.audit()
    dag=json.loads(mod.R78.read_text())
    orig=json.loads(mod.PUB.read_text())
    assert [node["state"] for node in z["nodes"]]==[node["state"] for node in dag["nodes"]]
    assert [node["id"] for node in z["nodes"]]==[node["id"] for node in dag["nodes"]]
    assert z["edges"]==dag["edges"]
    assert z["topological_order"]==dag["topological_order"]
    assert z["original_R78_60node_states_unchanged"]
    assert z["original_42_science_payload_sha256"]==dag["original_42_payload_sha256"]
    assert len(orig["nodes"])==42
    assert z["original_next_action_id"]=="SQ-CF4"


def test_all_sixty_have_real_preflight_group_and_auditable_code_source():
    z=mod.audit()
    nodes=z["nodes"]
    assert len({n["id"] for n in nodes})==60
    for n in nodes:
        e=n["pre_execution"]
        assert e["source_preflight_group"]
        assert e["associated_stage_code_or_test_exists"]
        assert e["code_module_references"]
        assert all((ROOT/path).exists() for path in e["code_module_references"])
        assert not e["full_node_physics_execution_qualified"]
        assert not e["preregistered_new_physical_null_proven"]


def test_six_of_six_scoped_coding_packages_sealed_after_R83_P0_A():
    z=mod.audit()
    groups=z["coding_stage_checkpoints"]
    assert len(groups)==6
    assert sum(g["C10_evidence_present"] for g in groups)==6
    assert z["R83_unsealed"]==[]
    r83=[g for g in groups if g["group"]=="R83_PRE_DAG_NODES31_40_20261120"]
    assert len(r83)==1 and r83[0]["C10_evidence_present"]
    assert z["agent_dispatch_policy"]["R83_P0_A_scoped_code_closure"].startswith("C9_C10_SEALED")
    assert all("Seal unverified coding preflight" not in x
               for x in z["agent_dispatch_policy"]["required_before_bounded_SQ_CF4_dispatch"])
    assert not z["full_60_code_science_execution_ready"]
    assert z["agent_dispatch_policy"]["status"]=="BLOCK_LOCAL_AGENT_START"


def test_live_source_byte_hashes_and_no_fake_physical_admission():
    z=mod.audit()
    assert len(z["real_source_hash_check"])==4
    assert all(x["present"] and x["actual_sha256"]==x["expected_sha256"]
               for x in z["real_source_hash_check"])
    assert z["scientific_42_state_counts"]=={
        "completed_scoped":18,"pending":23,"blocked_input":1}
    assert z["source_qualification_11_state_counts"]["ready_scoped"]==4
    assert z["seven_cross_phy_state_counts"]=={
        "theory_verified_physical_data_pending":7}


def test_all_agent_start_actions_denied_and_no_start_payload_exists():
    z=mod.audit()
    assert not z["full_60_code_science_execution_ready"]
    gate=z["agent_dispatch_policy"]
    assert gate["status"]=="BLOCK_LOCAL_AGENT_START"
    assert not gate["dispatch_performed"]
    assert not gate["start_packet_published"]
    assert not (mod.OUT/"START_LOCAL_AGENT.md").exists()
    assert not (mod.OUT/"START_LOCAL_AGENT.json").exists()


def test_proposed_legacy_entrypoints_are_explicitly_stale_not_faked():
    z=mod.audit()
    for name in ("htt/obsstat/htt_hubble_depth_window.py",
                 "scripts/run_htt_hubble_depth_tomography.py"):
        assert name in z["agent_dispatch_policy"]["stale_proposed_paths"]
        assert not (ROOT/name).exists()


def test_tampered_60_dag_next_action_fails_closed(tmp_path,monkeypatch):
    cloned=json.loads(mod.R78.read_text())
    cloned["next_action_id"]="B02"
    p=tmp_path/"fake_R78.json"
    p.write_text(json.dumps(cloned))
    monkeypatch.setattr(mod,"R78",p)
    with pytest.raises(AssertionError):
        mod.audit()
