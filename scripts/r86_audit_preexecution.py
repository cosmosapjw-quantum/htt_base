"""R86: read-only check of pre-execution software/science readiness for all 60 R78 nodes.

The R79-R85 *coding-preparation ordinal* is NOT R78's topological or native
node order. This program does NOT execute a science task or create an agent
start packet. It writes a derived readiness overlay only with --write.
"""
from __future__ import annotations

import argparse,collections,hashlib,json,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"docs/research_program/observational_publication_20261015"
R78=BASE/"R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
PUB=BASE/"PUBLICATION_DAG.json"
OUT=BASE/"R86_PRE_EXEC_READINESS_20261120"
PREFIXES=[
 ("R79_PRE_DAG_CODING_20261119",
  ["SQ-CF4","SQ-GAIA","SQ-RADIO","SQ-FRAME","SQ-P1-ANCHOR","SQ-CMB-NULL",
   "SQ-PHOTON-FLUX","SQ-LIE-FLUX","SQ-OPTICAL","SQ-CROSS-COV"]),
 ("R81_PRE_DAG_NODES11_20_20261120",
  ["SQ-NATIVE",*[f"PHY-{i:02d}" for i in range(1,8)],"E0","E1"]),
 ("R82_PRE_DAG_NODES21_30_20261120",
  ["E2","E3","X01","X02","X03","S01","S02","S03","S04","S05"]),
 ("R83_PRE_DAG_NODES31_40_20261120",
  ["S06",*[f"L{i:02d}" for i in range(1,7)],"H01","H02","H03"]),
 ("R84_PRE_DAG_NODES41_50_20261120",
  ["H04","H05","H06",*[f"V{i:02d}" for i in range(1,7)],"B01"]),
 ("R85_PRE_DAG_NODES51_60_20261120",
  [*[f"B{i:02d}" for i in range(2,6)],*[f"K{i:02d}" for i in range(1,7)]])
]
STAGE_MODULE={
 "R79_PRE_DAG_CODING_20261119":["htt/obsstat/pre_dag_fast.py","htt/obsstat/analysis_lane.json"],
 "R81_PRE_DAG_NODES11_20_20261120":["htt/obsstat/phy_fast.py"],
 "R82_PRE_DAG_NODES21_30_20261120":["htt/obsstat/p1_fast.py","htt/obsstat/publication_functionals.py"],
 "R83_PRE_DAG_NODES31_40_20261120":["htt/obsstat/p2p3_fast.py"],
 "R84_PRE_DAG_NODES41_50_20261120":["htt/obsstat/p4_bianchi_fast.py"],
 "R85_PRE_DAG_NODES51_60_20261120":["htt/obsstat/p5p6_fast.py"]
}
STAGE_TEST={
 "R79_PRE_DAG_CODING_20261119":"tests/obsstat/test_pre_dag_fast.py",
 "R81_PRE_DAG_NODES11_20_20261120":"tests/obsstat/test_r81_phy_fast.py",
 "R82_PRE_DAG_NODES21_30_20261120":"tests/obsstat/test_r82_p1_fast.py",
 "R83_PRE_DAG_NODES31_40_20261120":"tests/obsstat/test_r83_p2p3_fast.py",
 "R84_PRE_DAG_NODES41_50_20261120":"tests/obsstat/test_r84_p4_bianchi_fast.py",
 "R85_PRE_DAG_NODES51_60_20261120":"tests/obsstat/test_r85_p5p6_fast.py"
}
SOURCE_REMAINDER={
 "SQ-CF4":"R80 exact 35970 selected source lineage plus R87 real seven-method table3 group overlap and four sky heldout product-residual diagnostics now available. Published method moduli were globally MCMC-intercalibrated, so true upstream zero-point posterior/J_cal, calibrated correlated S_PV, survey completeness C_selection and independently calibrated heldout remain unavailable.",
 "SQ-GAIA":"Actual source moments and VSH numerical kernels exist; independent redshift/AGN/scan alias/selection covariance and qualified nonradial source null pending.",
 "SQ-RADIO":"Actual NVSS conditional 33k×185-ring 3-bin score exists; LSS, kappa, flux migration and matched selection/null pending.",
 "SQ-FRAME":"Finite local Lorentz kinematics exists; physical observed emitter/matter/normal common frame history and source transfer missing.",
 "SQ-P1-ANCHOR":"Source 274-row selected x needs real physical optical-to-normal scale/denominator and matched null; undefined mass cannot be filled by working-law MC.",
 "SQ-CMB-NULL":"Planck same-sky nine processes and eight FFP pilot pairs are not full matched exchangeable Commander T/E/B Monte Carlo.",
 "SQ-PHOTON-FLUX":"Full energy-dependent photon angular distribution, physical higher moments, common frame/Thomson closure and flux source missing.",
 "SQ-LIE-FLUX":"Independent measured normal rho/j/pi and external matter covariance for arbitrary Class A/B missing.",
 "SQ-OPTICAL":"No source-qualified finite-z Sachs/Jacobi/position-drift forward observable across actual sample with matching IC/BC and instrument selection.",
 "SQ-CROSS-COV":"No empirically calibrated shared C across CF4/Gaia/Planck/radio or independent heldout joint null.",
 "SQ-NATIVE":"No qualified external true physical polarized all-m Bianchi T/E/B history/mode/IC transfer; the NPZ schema checker is not a solver.",
 "S02":"Original optical-to-kinematic source anchor missing; 2048 coupled P1 working draws not a physical posterior.",
 "H02":"Real method-family source overlap, zero-point, correlated peculiar velocity and selection covariance not implemented/source-qualified.",
 "L03":"Actual same-release CMB T/E/B null ensemble and source exchangeability missing.",
 "B02":"External full polarized all-m physical Bianchi family/mode transfer absent.",
 "K03":"Original Gaia 755850 cross moments exist, but independent sky/AGN/scan and normal-frame nonradial transfer not source-qualified."
}
NODE_MODULE={
 "H01":["docs/research_program/observational_publication_20261015/H03_20261016/src/h03_tomography.py"],
 "H03":["docs/research_program/observational_publication_20261015/H03_20261016/src/h03_tomography.py",
        "htt/obsstat/p2p3_fast.py"],
 "K01":["htt/obsstat/publication_frame_kinematics.py"],
 "K02":["htt/obsstat/p5p6_fast.py"],
 "V01":["htt/obsstat/publication_frame_kinematics.py"],
 "V04":["htt/obsstat/p4_bianchi_fast.py"],
 "S02":["htt/obsstat/p1_fast.py"],
 "L03":["htt/obsstat/p2p3_fast.py"],
 "B02":["htt/obsstat/p5p6_fast.py"],
 "SQ-CF4":["scripts/r80/audit_cf4_source_lineage.py",
            "htt/obsstat/cf4_p0b.py","scripts/r87/run_p0b.py"]
}
TRUE_SOURCE=[
 ("CF4 35970 selected NPZ","docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz",
  "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"),
 ("CF4 original group table4","/mnt/extdrive/workdir/raw/cf4_full/table4.dat",
  "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94"),
 ("CF4 original method table3","/mnt/extdrive/workdir/raw/cf4_full/table3.dat",
  "c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d"),
 ("K03 external Gaia cross moments","/mnt/extdrive/workdir/htt_open_data/k03_pm_20261023/cross_moments.npz",
  "70fc2fee88803a7211c1c157ff87b4adb05b0807a00c03dc38d51f31b3842662")
]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for part in iter(lambda:stream.read(1<<20),b""):h.update(part)
    return h.hexdigest()


def audit():
    parent=json.loads(R78.read_text())
    historical=json.loads(PUB.read_text())
    byid={n["id"]:n for n in parent["nodes"]}
    order=[node for folder,ids in PREFIXES for node in ids]
    assert len(order)==len(set(order))==60 and set(order)==set(byid)
    assert len(parent["edges"])==129 and parent["next_action_id"]=="SQ-CF4"
    origsha=hashlib.sha256(json.dumps(historical["nodes"],sort_keys=True).encode()).hexdigest()
    assert origsha==parent["original_42_payload_sha256"]=="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
    program=[]
    unsealed=[]
    for folder,names in PREFIXES:
        dest=BASE/folder
        matrix=dest/"C10_NODE_MATRIX.json"
        has_C10=matrix.is_file()
        if has_C10:
            original=json.loads(matrix.read_text())
            claimed=[x.get("node_id",x.get("science_node_id")) for x in original.get("nodes",[])]
            assert claimed==names,(folder,"C10 matrix differs from coding ordinal")
        else:
            unsealed.append({"group":folder,"node_ids":names,
                 "missing":[v for v in ("C9_REVIEW.json","C10_NODE_MATRIX.json",
                     "PROVENANCE.json","REPORT_KO.md","HANDOFF_KO.md") if not (dest/v).is_file()]})
        for item in STAGE_MODULE[folder]+[STAGE_TEST[folder]]:
            assert (ROOT/item).is_file(),(folder,"missing installed code/test",item)
        program.append({"group":folder,"coding_node_ids":names,
           "code_modules":STAGE_MODULE[folder],"test_file":STAGE_TEST[folder],
           "C10_evidence_present":has_C10,
           "C10_SHA256":sha(matrix) if has_C10 else None})
    sources=[{"name":label,"path":file,"expected_sha256":checksum,
        "present":Path(file).is_file(),
        "actual_sha256":sha(file) if Path(file).is_file() else None}
             for label,file,checksum in TRUE_SOURCE]
    assert all(x["actual_sha256"]==x["expected_sha256"] for x in sources),"real-source byte drift"
    historical_type=collections.Counter(n["state"] for n in historical["nodes"])
    assert historical_type=={"completed_scoped":18,"pending":23,"blocked_input":1}
    extra=collections.Counter(n["state"] for n in parent["nodes"] if n.get("node_class")=="source_qualification")
    assert extra["ready_scoped"]==4
    phy=collections.Counter(n["state"] for n in parent["nodes"] if n.get("node_class")=="physical_cross_route")
    assert phy["theory_verified_physical_data_pending"]==7
    edges=parent["edges"]
    incoming=collections.defaultdict(list)
    for e in edges:incoming[e["to"]].append({"from":e["from"],"kind":e["kind"],"hard":e["hard"]})
    nodes=[]
    ordinal={id:i for i,id in enumerate(order,1)}
    folders={id:folder for folder,names in PREFIXES for id in names}
    for n in parent["nodes"]:
        key=n["id"]
        stage=folders[key]
        sealed=(BASE/stage/"C10_NODE_MATRIX.json").is_file()
        if n.get("node_class")=="physical_cross_route":
            software="CONDITIONAL_THEOREM_OR_GEOMETRY_KERNEL_ONLY"
        elif n["state"]=="completed_scoped":
            software="EXISTING_SCOPED_SOURCE_RESULT_OR_VALIDATED_OPERATOR"
        elif n["state"]=="ready_scoped":
            software="BOUNDED_SOURCE_DIAGNOSTIC_AVAILABLE_ONLY"
        elif key.startswith(("S","L","H","V","B","K")) and key not in ("SQ-CF4",):
            software="PARTIAL_NUMERICAL_KERNEL_OR_INPUT_VALIDATOR_NOT_FULL_SCIENCE_TASK"
        else:
            software="INPUT_VALIDATOR_OR_CONDITIONAL_OPERATOR_NOT_PRODUCTION_PHYSICS"
        if stage in [v["group"] for v in unsealed]:
            software=software+"; STAGE_C9_C10_NOT_SEALED"
        actual=[x for x in STAGE_MODULE[stage]+NODE_MODULE.get(key,[]) if (ROOT/x).is_file()]
        source_remainder=SOURCE_REMAINDER.get(key)
        if source_remainder is None:
            a=n.get("external_missing",[])
            source_remainder="; ".join(a) if a else (
             "Requires source-verified physics acceptance or actual dependency outputs; "
             "a numerical preflight does not upgrade scientific readiness")
        nodes.append(dict(n,
            pre_execution={
                "coding_ordinal_1_to_60":ordinal[key],
                "source_preflight_group":stage,
                "code_preparation_checkpoint_complete":sealed,
                "code_module_references":sorted(set(actual)),
                "associated_stage_code_or_test_exists":bool(actual),
                "software_evidence_scope":software,
                "science_state_from_R78_unchanged":n["state"],
                "full_node_physics_execution_qualified":False,
                "unresolved_execution_requirement":source_remainder,
                "preregistered_new_physical_null_proven":False,
                "stage_source_matrix":f"docs/research_program/observational_publication_20261015/{stage}/C10_NODE_MATRIX.json" if sealed else None,
                "incoming_dependencies":incoming[key]
            }))
    legacy_missing=[
      "htt/obsstat/htt_hubble_depth_window.py",
      "scripts/run_htt_hubble_depth_tomography.py"]
    assert all(not (ROOT/f).exists() for f in legacy_missing)
    # A sealed numerical package is NOT a source-qualified scientific task.
    # Recompute this operational status from current R83 C10 evidence, instead
    # of replaying the historical R86 pre-P0-A five-of-six checkpoint.
    has_unsealed_stage=bool(unsealed)
    reasons=[
        "Original science graph has 18 scoped-completed historical nodes, 23 pending and 1 blocked; 7 physical-cross routes are theory-only.",
        "The 60-node R78 graph has no 60-node production execution controller; the original 42-node CLI reports 0 ready.",
    ]
    if has_unsealed_stage:
        reasons.append("At least one numerical preflight package lacks an actual C10 verified evidence/seal.")
    reasons += [
        "R87 P0-B now verifies actual selected 35970 CF4 source, 926 multi-method presence groups, 922 usable contrast groups and post-intercalibration four-block residual prediction; however true correlated PV, upstream cross-method zero-point posterior, survey selection covariance and independent calibration heldout remain unqualified.",
        "B02 external full physical all-m polarization, full Planck matched CMB null and K03 common-congruence cross-source covariance are not qualified.",
        "Original 42-node planned_code still has two proposed paths that do not exist; actual replacement functions live elsewhere."
    ]
    required=[]
    if has_unsealed_stage:
        required.append("Seal unverified coding preflight C9/C10 and source receipts without staging unrelated edits.")
    required.extend([
        "Provide a tested exact 60-node read-only task packet adapter for SQ-CF4; blocked/unknown node fail-closed and no automatic worker.",
        "Implement source-matched 35970-ID method zero-point/PV/selection covariance and a preregistered real heldout coverage test, or an honest physically blocked result.",
        "Verify source-bound R86 overlay and immutable R78 scientific states during dry run."
    ])
    blocked={
       "status":"BLOCK_LOCAL_AGENT_START",
       "reasons":reasons,
       "R83_P0_A_scoped_code_closure":("C9_C10_SEALED; SCIENCE_DEPENDENCIES_REMAIN" if not has_unsealed_stage
                                      else "NOT_YET_SEALED"),
       "missing_R83_checkpoint":unsealed,
       "stale_proposed_paths":legacy_missing,
       "required_before_bounded_SQ_CF4_dispatch":required,
       "external_sources_required_for_full_60":[
           "Planck release-matched T/E/B MC/null with exchangeable processing, original full photon moments/normal-frame flux",
           "independent Bianchi all-m polarized T/E/B histories/initial conditions/beam/source response",
           "Gaia/radio/CMB/CF4 common normal-frame transport and matched cross-source covariance/null",
           "P1 physical scale/denominator and selected source response"
       ],
       "dispatch_performed":False,
       "start_packet_published":False,
       "allowed_output":"BLOCKED_READINESS_REPORT_ONLY"
    }
    r87_path=BASE/"R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/RESULT.json"
    r87_return=BASE/"R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/P0B_SCIENCE_RETURN.json"
    r87_closure=BASE/"R87_SQ_CF4_P0B_METHOD_COV_HELDOUT_20261120/P0B_CLOSURE_RECEIPT.json"
    if not all(x.is_file() for x in (r87_path,r87_return,r87_closure)):
        raise AssertionError("R87 source diagnostic or physical-blocked closure receipt missing")
    r87=json.loads(r87_path.read_text())
    r87_status=json.loads(r87_return.read_text())
    r87_done=json.loads(r87_closure.read_text())
    if (r87["selected_original_group_count"]!=35970 or
        r87["usable_six_methods_with_released_positive_error_multigroup_count"]!=922 or
        r87_status["P0_B_true_physical_covariance_status"]!="BLOCKED_INPUT" or
        r87_status["local_agent_START"] is not False or
        r87_done["full_physical_C_status"]!="BLOCKED_INPUT" or
        r87_done["R87_source_RESULT_sha256"]!=sha(r87_path) or
        r87_done["R87_science_RETURN_sha256"]!=sha(r87_return)):
        raise AssertionError("R87 P0-B source or blocked science contract drift")
    derived={
      "schema":"htt.r86.r78_60node_preexecution_readiness_overlay/1",
      "date":"2026-11-20 KST",
      "derived_from_R78_DAG":str(R78.relative_to(ROOT)),
      "original_R78_byte_sha256":sha(R78),
      "original_42_science_payload_sha256":origsha,
      "original_R78_60node_states_unchanged":True,
      "original_edges_unchanged":True,
      "original_topological_order_unchanged":True,
      "original_next_action_id":"SQ-CF4",
      "R87_SQ_CF4_real_source_diagnostic":{
        "P0_B_source_result":"SOURCE_CONTRAST_SKY_DIAGNOSTIC_COMPLETED_SCOPED",
        "P0_B_physical_C_and_independent_heldout":"BLOCKED_INPUT",
        "selected_group_count":35970,"usable_sixmethod_multigroup_count":922,
        "source_RESULT_SHA256":sha(r87_path),
        "science_RETURN_SHA256":sha(r87_return),
        "P0_B_closure_receipt_SHA256":sha(r87_closure),
        "P0_B_new_source_test_count":r87_status["validated_new_tests"],
        "P0_B_related_scoped_test_count":r87_status["validated_related_scoped_tests"],
        "path":str(r87_path.relative_to(ROOT)),
        "physical_Pi":None},
      "original_software_PR_backlog_authority":"docs/codex_handoff/pr_backlog.yaml",
      "coding_ordinal_is_NOT_original_R78_array_or_toposort":True,
      "coding_stage_checkpoints":program,
      "R83_unsealed":unsealed,
      "real_source_hash_check":sources,
      "scientific_42_state_counts":dict(historical_type),
      "source_qualification_11_state_counts":dict(extra),
      "seven_cross_phy_state_counts":dict(phy),
      "full_60_code_science_execution_ready":False,
      "bounded_source_slices_exist":True,
      "agent_dispatch_policy":blocked,
      "nodes":nodes,
      "edges":edges,
      "topological_order":parent["topological_order"]
    }
    assert len(derived["nodes"])==60 and len(derived["edges"])==129
    assert [n["id"] for n in derived["nodes"]]==[n["id"] for n in parent["nodes"]]
    return derived


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--write",action="store_true",help="Write only derived R86 file; never execute science")
    args=parser.parse_args()
    data=audit()
    if args.write:
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/"EXECUTION_READINESS_DAG.json").write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"pass":True,"nodes":len(data["nodes"]),"edges":len(data["edges"]),
        "code_preparation_checkpoint_sealed":sum(x["C10_evidence_present"] for x in data["coding_stage_checkpoints"]),
        "coding_stage_count":len(data["coding_stage_checkpoints"]),
        "R83_missing_outputs":data["R83_unsealed"][0]["missing"] if data["R83_unsealed"] else [],
        "actual_next_sci":data["original_next_action_id"],
        "all_science_code_ready":data["full_60_code_science_execution_ready"],
        "agent_start":"BLOCKED_NOT_DISPATCHED","write":args.write},ensure_ascii=False))
if __name__=="__main__":main()
