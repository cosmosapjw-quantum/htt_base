"""R88 P0-C: read-only, fail-closed R78/R86 SQ-CF4 pre-execution packet.

No worker, production science execution, filesystem mutation, or scientific
state transition is implemented. A successful dry-run reports BLOCKED_INPUT.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs/research_program/observational_publication_20261015"
R78 = BASE / "R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R86 = BASE / "R86_PRE_EXEC_READINESS_20261120/EXECUTION_READINESS_DAG.json"
R87DIR = BASE / "R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120"
R87 = R87DIR / "RESULT.json"
RETURN = R87DIR / "P0B_SCIENCE_RETURN.json"
CLOSURE = R87DIR / "P0B_CLOSURE_RECEIPT.json"
PUBLICATION = BASE / "PUBLICATION_DAG.json"
# Pinned to actual parent HEAD 73906628...; do not trust editable self-reported hashes.
SHA_R78 = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
SHA_R86 = "2f6cb20f541100d5db8d53a1745ad627e5729e83afff48e4585745a56b30a467"
SHA_R87 = "c357670dadaada250f75f3a41959d712add11b3d4c45f00bfbc46f4dc3fdc199"
SHA_42 = "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
FRAME = "ICRS_J2000_DIRECTIONS_AND_CMB_REDSHIFT"
NODE = "SQ-CF4"
SOURCES = (
    "/mnt/extdrive/workdir/raw/cf4_full/table3.dat",
    "/mnt/extdrive/workdir/raw/cf4_full/table4.dat",
    "/mnt/extdrive/workdir/raw/cf4_full/ReadMe",
    "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz",
)
MISSING_PHYSICS = (
    "independently calibrated 35970-group S_PV or velocity-field realizations",
    "upstream intercalibration posterior and J_cal Sigma_cal J_cal^T",
    "survey selection/completeness model and C_selection",
    "independent upstream calibration and selection-matched heldout/null coverage",
)


class ContractError(ValueError):
    """SHA, DAG or scientific admission contract is not met."""


class PolicyDenied(ValueError):
    """The requested node, frame or operation is not permitted."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_pinned(path: Path, digest: str) -> dict:
    if not path.is_file() or sha256(path) != digest:
        raise ContractError(f"missing or SHA256 mismatch: {path}")
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ContractError(f"expected JSON object: {path}")
    return obj


def verify_graph(original: dict, overlay: dict) -> dict:
    nodes, edges, order = original["nodes"], original["edges"], original["topological_order"]
    byid = {n["id"]: n for n in nodes}
    if (len(nodes), len(byid), len(edges), len(order), len(set(order))) != (60, 60, 129, 60, 60):
        raise ContractError("R78 graph cardinality not 60 nodes / 129 edges")
    if set(byid) != set(order) or original["next_action_id"] != NODE:
        raise ContractError("R78 next science node/ID set changed")
    if (sum(n.get("node_class") == "source_qualification" for n in nodes),
        sum(n.get("node_class") == "physical_cross_route" for n in nodes)) != (11, 7):
        raise ContractError("42+11+7 node taxonomy drift")
    if Counter(n["state"] for n in nodes if "node_class" not in n) != {
        "completed_scoped": 18, "pending": 23, "blocked_input": 1
    }:
        raise ContractError("original 42 science states drift")
    stripped_overlay = [{k: v for k, v in n.items() if k != "pre_execution"}
                        for n in overlay["nodes"]]
    if stripped_overlay != nodes or overlay["edges"] != edges or overlay["topological_order"] != order:
        raise ContractError("R86 overlay diverged from R78 science SSOT")
    ranks = {n: i for i, n in enumerate(order)}
    seen, incoming = set(), defaultdict(set)
    for e in edges:
        a, b = e["from"], e["to"]
        if (a not in byid or b not in byid or not e.get("hard")
            or ranks[a] >= ranks[b] or (a, b) in seen):
            raise ContractError("duplicate, dangling, soft, cyclic or unordered hard edge")
        seen.add((a, b))
        incoming[b].add(a)
    for n in nodes:
        if not set(n.get("depends_on", [])) <= incoming[n["id"]]:
            raise ContractError(f"missing explicit hard dependencies: {n['id']}")
    if incoming[NODE] != {"E1", "X01", "H01"}:
        raise ContractError("SQ-CF4 hard dependency list drift")
    return byid


def verify_seals(overlay: dict) -> None:
    stages = overlay["coding_stage_checkpoints"]
    if len(stages) != 6 or overlay["R83_unsealed"]:
        raise ContractError("missing stage C10 seal")
    r83 = []
    for item in stages:
        path = BASE / item["group"] / "C10_NODE_MATRIX.json"
        if not item["C10_evidence_present"] or not path.is_file() or sha256(path) != item["C10_SHA256"]:
            raise ContractError(f"C10 SHA mismatch or absent: {path}")
        if item["group"].startswith("R83_"):
            r83.append(item)
    if len(r83) != 1 or len(r83[0]["coding_node_ids"]) != 10:
        raise ContractError("R83 ten-node preflight/closure drift")
    if overlay["agent_dispatch_policy"]["R83_P0_A_scoped_code_closure"] != (
        "C9_C10_SEALED; SCIENCE_DEPENDENCIES_REMAIN"
    ):
        raise ContractError("R83 C9/C10 software closure not verified")


def read_authority() -> tuple[dict, dict, dict, dict]:
    dag = read_pinned(R78, SHA_R78)
    pre = read_pinned(R86, SHA_R86)
    method = read_pinned(R87, SHA_R87)
    verify_graph(dag, pre)
    if (pre["original_R78_byte_sha256"] != SHA_R78 or
        pre["original_42_science_payload_sha256"] != SHA_42 or
        dag["original_42_payload_sha256"] != SHA_42 or
        pre["original_next_action_id"] != NODE or
        not all(pre[k] for k in (
            "original_R78_60node_states_unchanged",
            "original_edges_unchanged",
            "original_topological_order_unchanged"))):
        raise ContractError("R78/R86 identity or source authority changed")
    original_42 = json.loads(PUBLICATION.read_text(encoding="utf-8"))["nodes"]
    if hashlib.sha256(json.dumps(original_42, sort_keys=True).encode()).hexdigest() != SHA_42:
        raise ContractError("original 42 scientific payload SHA drift")
    verify_seals(pre)
    policy = pre["agent_dispatch_policy"]
    if (policy["status"] != "BLOCK_LOCAL_AGENT_START"
        or policy["dispatch_performed"] or policy["start_packet_published"]
        or pre["full_60_code_science_execution_ready"]):
        raise ContractError("no-start invariant changed")
    p0b = pre["R87_SQ_CF4_real_source_diagnostic"]
    if p0b["source_RESULT_SHA256"] != SHA_R87:
        raise ContractError("R87 source receipt drift")
    returned = read_pinned(RETURN, p0b["science_RETURN_SHA256"])
    closure = read_pinned(CLOSURE, p0b["P0_B_closure_receipt_SHA256"])
    if closure["R87_source_RESULT_sha256"] != SHA_R87 or (
        closure["R87_science_RETURN_sha256"] != sha256(RETURN)
    ):
        raise ContractError("P0-B closure source binding drift")
    if (returned["P0_B_true_physical_covariance_status"] != "BLOCKED_INPUT"
        or returned["local_agent_START"] is not False
        or returned["R78_parent_science_states_changed"]
        or closure["full_physical_C_status"] != "BLOCKED_INPUT"
        or any(returned[k] is not None for k in (
            "selection_completeness_C", "physically_calibrated_source_PV_C",
            "method_calibration_J_Sigma_JT", "independent_upstream_heldout_coverage"))):
        raise ContractError("P0-B was incorrectly promoted to full physical science")
    if (method["selected_original_group_count"] != 35970
        or method["original_released_group_count"] != 38053
        or method["original_multi_method_presence_group_count"] != 926
        or method["usable_six_methods_with_released_positive_error_multigroup_count"] != 922
        or len(method["seven_original_method_presence_counts"]) != 7
        or method["method_modulus_input_semantics"] !=
        "ALREADY_INTERCALIBRATED_GROUPED_DISTANCE_ESTIMATES_NOT_RAW_ZERO_POINTS"
        or method["claim_gate"]["actual_full_C_qualified"]
        or method["claim_gate"]["actual_spatial_calibration_heldout_qualified"]
        or method["claim_gate"]["physical_p_value"] is not None
        or method["identification_obstruction"]["true_physics_Pi"] is not None):
        raise ContractError("P0-B source group or science gate drift")
    return dag, pre, method, returned


def source_path(name: str) -> Path:
    return Path(name) if name.startswith("/") else ROOT / name


def verify_sources(method: dict, pre: dict) -> list[dict]:
    if set(method["source_sha256"]) != set(SOURCES):
        raise ContractError("unregistered original CF4 source paths")
    check_from_r86 = {x["path"]: x["expected_sha256"] for x in pre["real_source_hash_check"]}
    for name in SOURCES:
        if name in check_from_r86 and method["source_sha256"][name] != check_from_r86[name]:
            raise ContractError("R86/R87 source SHA conflict")
    result = []
    for name in SOURCES:
        path = source_path(name)
        digest = sha256(path) if path.is_file() else None
        expected = method["source_sha256"][name]
        if digest is not None and digest != expected:
            raise ContractError(f"source byte mismatch: {name}")
        result.append({"path": name, "expected_sha256": expected,
                       "actual_sha256": digest,
                       "status": "VERIFIED_BYTES" if digest else "MISSING_BLOCKED_INPUT",
                       "source_owner": "original CF4 CDS" if name.startswith("/") else "R54/R58 selected groups"})
    return result


def build_packet(node: str, frame: str = FRAME) -> dict:
    if frame != FRAME:
        raise PolicyDenied("observer frame mismatch; no unapproved physical frame transport")
    dag, pre, method, returned = read_authority()
    nodes = verify_graph(dag, pre)
    if node not in nodes:
        raise PolicyDenied(f"unknown science node: {node}")
    if node != NODE:
        raise PolicyDenied(f"out of P0-C scope: {node}; only SQ-CF4 dry-run allowed")
    target = nodes[NODE]
    observed = next(n["pre_execution"] for n in pre["nodes"] if n["id"] == NODE)
    if (target["state"] != "ready_scoped"
        or observed["science_state_from_R78_unchanged"] != "ready_scoped"
        or not observed["code_preparation_checkpoint_complete"]
        or observed["full_node_physics_execution_qualified"]
        or observed["preregistered_new_physical_null_proven"]):
        raise ContractError("SQ-CF4 readiness cannot be promoted")
    dependencies = [{"node_id": k, "state": nodes[k]["state"],
                     "authority": "scoped prior evidence, not full observational inference"}
                    for k in ("E1", "X01", "H01")]
    if any(d["state"] != "completed_scoped" for d in dependencies):
        raise ContractError("hard predecessor source evidence is incomplete")
    inputs = verify_sources(method, pre)
    return {
        "schema": "htt.r88.p0c.r78_sqcf4_readonly_packet/1",
        "operation": "READ_ONLY_DRY_RUN", "phase": "P0-C", "node_id": NODE,
        "status": "BLOCKED_INPUT", "source_diagnostic_available": True,
        "science_execution_authorized": False, "agent_dispatched": False,
        "start_local_agent_published": False, "file_writes": False,
        "physical_posterior_admitted": False,
        "science_graph": {"path": str(R78.relative_to(ROOT)), "sha256": SHA_R78,
                          "original_42_sha256": SHA_42, "nodes": 60, "hard_edges": 129,
                          "next_science_node": dag["next_action_id"]},
        "readiness": {"overlay_sha256": SHA_R86, "C10_stage_seals": 6,
                      "local_agent_status": pre["agent_dispatch_policy"]["status"]},
        "prerequisites": dependencies,
        "node_contract": {"state": target["state"], "objective": target["objective"],
                          "physics_goal": target["physics_goal"], "source_identity": target["source_identity"],
                          "acceptance": target["acceptance"], "stop_condition": target["stop_condition"],
                          "scientific_claim_tier": target["scientific_claim_tier"]},
        "input_contract": {"observer_frame": frame, "selected_groups": 35970,
                           "original_released_groups": 38053,
                           "selected_group_id_sha256": method["selected_group_ID_sha256"],
                           "original_method_indicators": 7,
                           "error_bearing_multi_method_groups": 922,
                           "method_network_rank": 5, "already_globally_intercalibrated": True,
                           "heldout": "4 group-ID-disjoint RA quadrants, but globally calibrated upstream",
                           "source_provenance": inputs},
        "physics_status": {"C_expression": "N_stat+S_PV+J_cal Sigma_cal J_cal^T+C_selection",
                           "N_stat": "diagonal working source quoted errors only",
                           "S_PV": None, "J_cal_Sigma_cal_J_cal_T": None, "C_selection": None,
                           "independent_null": None, "physical_Pi": None,
                           "missing_inputs": list(MISSING_PHYSICS),
                           "source_gate": returned["P0_B_true_physical_covariance_status"]},
        "output_ownership": {"existing_source_diagnostic": str(R87.relative_to(ROOT)),
                             "existing_diagnostic_producer": "scripts/r87/run_p0b.py",
                             "future_physical_input_owner": "external original calibration/velocity/selection providers",
                             "new_science_output_path": None,
                             "no_worker_command": True, "no_output_written": True},
        "stop": "no physical H(z,n), Pi, GF, or source-null claim without independently qualified covariance/coverage",
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--node", required=True)
    cli.add_argument("--dry-run", action="store_true")
    cli.add_argument("--observer-frame", default=FRAME)
    args = cli.parse_args(argv)
    if not args.dry_run:
        cli.error("--dry-run required; no science dispatcher implemented")
    try:
        packet = build_packet(args.node, args.observer_frame)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"status": "REJECTED_FAIL_CLOSED", "reason": str(exc),
                          "node_id": args.node, "agent_dispatched": False},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
