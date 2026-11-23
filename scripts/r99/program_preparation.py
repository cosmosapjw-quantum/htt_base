"""Read-only scientific authority and executable preparation overlay for the R78 DAG."""
from __future__ import annotations

import argparse
from collections import Counter
from graphlib import TopologicalSorter
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from scripts.r98.program_preparation import DAG, OUT as PREVIOUS, PIN, ROOT

BASE = DAG.parent.parent
OUT = BASE / "R99_FIFTH_BLOCKER_RESOLUTION_20261123"
FILE = "NODE60_EXECUTION_PREPARATION.json"
ACTIONS = "BLOCKER_ACTIONS.md"
R98_PIN = "ab3ab214385770a06b733cfcb9c211ba8c7b2c913eb1c962be9eb11159cee964"
GATES_PIN = "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
PY = ".venv/bin/python"
# kind/producer, additional files consumed or reused, producer command args
LANES = {
    "CF4_SOURCE_LAW": ("cf4_source_law", ["CF4_RESULTS.json"], []),
    "OPTICAL_TRANSFER": ("optical", ["OPTICAL_RESULTS.json"], []),
    "GAIA_SHARED_FIELD": ("gaia_shared_field", ["GAIA_SHARED_FIELD_RESULTS.json","GAIA_SHARED_FIELD_COVARIANCES.npz"], []),
    "SOURCE_ACQUISITION": ("acquisition", ["ACQUISITION_RESULTS.json","ACQUISITION_PLAN.json",
                          "inputs/lotss_outer_exposure_nside16.npz"], ["footprint"]),
}
# Each delta names its remaining obligation and executable work under it. M08 binds R98-EXT.
UPDATES = {
    "D01": (["CF4_SOURCE_LAW","SOURCE_ACQUISITION"], "SDSS PV v1.1 and 6dFGSv table 1 selected in the exact 20,927,710-byte two-product plan; prefix and release metadata captured.",
            "Pre-registration joint method/anchor law and calibrator/holdout membership remain absent.",
            "Acquire bounded full payloads, match galaxy/host and group IDs, then reconstruct calibration/holdout roles and shared anchor covariance."),
    "D02": (["CF4_SOURCE_LAW","SOURCE_ACQUISITION"], "Normalized selected-mark joint field example, sharp supported-mark bounds and the bounded FP acquisition plan are available.",
            "Target/rejection denominators, zero-support strata and true method-specific inclusion are unresolved.",
            "Join upstream eligible parents to the selected survey samples; recover native cuts, rejections, and group inclusion denominators."),
    "M01": (["CF4_SOURCE_LAW"], "Three finite-z source responses, nonlinear marginal moments and first-chaos low-k projections on 35,970 groups; corrected magnitude-tilt covariance and paired score.",
            "Source-specific observable assignment, calibrated full-k joint velocity/selection law and external holdout remain open.",
            "Recover native estimator conventions and calibrate full-band coherent and small-scale terms using identified source data."),
    "M02": (["OPTICAL_TRANSFER"], "Finite-z positional Jacobi transport and separate observer/emitter boosts were implemented on declared backgrounds.",
            "Source-distance priors, position drift/proper motion, matched T_C and T_G kernels and coverage remain open.",
            "Construct position drift on matched worldlines and source-frame transfer kernels; validate against independent source and coverage tests."),
    "D04": (["GAIA_SHARED_FIELD"], "Shared angular-field covariance and cross-fit terms propagated through the full-source sufficient statistics for ten fits (six base fits and four Quaia redshift bins), 48 patches and 160 joint coefficients.",
            "A release-qualified Gaia AGIS spatial error law and independent AGN centroid/source controls remain missing.",
            "Attach audited calibration and independent source labels with exact IDs and test the held-out angular residuals."),
    "M05": (["GAIA_SHARED_FIELD","OPTICAL_TRANSFER"], "Ten fits share a six-component source/scan nuisance field across 48 patches. The 160-coefficient analysis includes cross-fit covariance and supported-subspace checks.",
            "Physical joint scan/AGN field, transfer and normal-frame identification remain uncalibrated.",
            "Condition shared covariance on independent AGIS/AGN controls and a positional-drift response with frame-spin degeneracies."),
    "D05": (["SOURCE_ACQUISITION"], "Outer polygons for 1,580 LoTSS mosaics were unioned and rasterized; the fitted intensity can use this geometric solid-angle offset.",
            "Interior weight holes, RMS, source association, flux/size completeness and the SED response remain unmeasured.",
            "Acquire per-mosaic weights/RMS with explicit byte limits, recover internal coverage and validate with source injections and SED matches."),
    "D03": (["SOURCE_ACQUISITION"], "PR3 Commander simulation job is specified by the acquisition manifest and product identities; full data remain external.",
            "Component-matched noise and the joint split/foreground/systematics null remain unqualified.",
            "Retrieve the selected Commander product under an explicit budget and verify release, simulation, beam, mask and split genealogy."),
    "M08": (["BIANCHI"], "R98-EXT already evaluated a first radiation-feedback iteration on the prescribed histories.",
            "Iterated self-consistent Einstein–Boltzmann backreaction and the primordial initial-condition atlas remain open.",
            "Propagate successive coupled radiation/background iterates and test convergence, constraints and matched external solutions."),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def verify_contract(dag, previous, original):
    base_ids = {n["id"] for n in original}
    retained = [n for n in dag["nodes"] if n["id"] in base_ids]
    original_sha = hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()
    if len(original) != 42 or retained != original or original_sha != GATES_PIN:
        raise ValueError("original 42 scientific contracts changed")
    if dag["edges"] != previous["canonical_edges"] or len(dag["edges"]) != 129:
        raise ValueError("canonical edge drift")
    nodes = {n["id"]:n for n in dag["nodes"]}
    legacy = {n["id"]:n for n in previous["nodes"]}
    if len(nodes) != 60 or nodes.keys() != legacy.keys() or dag["next_action_id"] != "SQ-CF4":
        raise ValueError("canonical node set or next-node drift")
    parents = {k:set(n["depends_on"]) for k,n in nodes.items()}
    for e in dag["edges"]:
        if e.get("hard",True):
            parents[e["to"]].add(e["from"])
    sources = previous["blockers"]
    if Counter(b["category"] for b in sources.values()) != {"DATA":6,"MODEL":9,"ADDITIONAL_ANALYSIS":6}:
        raise ValueError("obligation inventory changed")
    propagated = {}
    for key in TopologicalSorter(parents).static_order():
        n, old = nodes[key], legacy[key]
        for source, target in [("state","original_state"),("objective","original_objective"),
                               ("acceptance","original_acceptance"),("depends_on","original_dependencies")]:
            if n[source] != old[target]:
                raise ValueError(f"{key}: {source} contract changed")
        if sorted(parents[key]) != old["effective_hard_dependencies"]:
            raise ValueError(f"{key}: hard dependency mismatch")
        blockers = set(old["direct_blockers"]).union(*(propagated[k] for k in parents[key]))
        if not blockers <= sources.keys() or sorted(blockers) != old["all_blockers_including_dependencies"]:
            raise ValueError(f"{key}: inherited blocker mismatch")
        propagated[key] = blockers
    return propagated


def packages(previous):
    pkgs = {}
    for key, original in previous["packages"].items():
        for name in original["outputs"]:
            if digest(PREVIOUS/name) != original["output_sha256"][name]:
                raise ValueError(f"{key}: frozen predecessor result {name} changed")
        pkgs[key] = {**original, "evidence_directory":str(PREVIOUS.relative_to(ROOT)), "stage":"R98 frozen reuse"}
    for key,(mod,items,args) in LANES.items():
        script = ROOT / "scripts/r99" / f"{mod}.py"
        record = read(OUT/items[0])
        producer = digest(script)
        if key == "CF4_SOURCE_LAW":
            claimed = record["inputs_sha256"]["R99_code"]
        elif key == "OPTICAL_TRANSFER":
            claimed = record["inputs_sha256"]["scripts/r99/optical.py"]
            for f,h in record["inputs_sha256"].items():
                if digest(ROOT/f) != h:
                    raise ValueError(f"optical input identity drift: {f}")
        elif key == "GAIA_SHARED_FIELD":
            claimed = record["code_sha256"]
            if digest(OUT/items[1]) != record["covariance_artifact"]["sha256"]:
                raise ValueError("Gaia covariance identity drift")
        else:
            plan = read(OUT/items[1])
            claimed = record["producer_sha256"]
            if plan["producer_sha256"] != producer or digest(OUT/items[2]) != record["output_npz_sha256"]:
                raise ValueError("acquisition plan or exposure identity drift")
        if claimed != producer:
            raise ValueError(f"{key}: result and producer identity differ")
        pkgs[key] = dict(command=[PY,"-B","-m",f"scripts.r99.{mod}",*args], outputs=items,
                         output_sha256={f:digest(OUT/f) for f in items}, producer_sha256=producer,
                         evidence_directory=str(OUT.relative_to(ROOT)), stage="R99 conditional preparation")
    return pkgs


def build():
    if digest(DAG) != PIN or digest(PREVIOUS/FILE) != R98_PIN:
        raise ValueError("science authority or inherited overlay identity drift")
    dag, previous = read(DAG), read(PREVIOUS/FILE)
    original = read(BASE/"PUBLICATION_DAG.json")["nodes"]
    propagated = verify_contract(dag,previous,original)
    pkgs = packages(previous)
    obligations = {}
    for key, old in previous["blockers"].items():
        affected = [n["id"] for n in previous["nodes"] if key in propagated[n["id"]]]
        if affected != old["affected_nodes"]:
            raise ValueError(f"{key}: affected node list drift")
        direct = [n["id"] for n in previous["nodes"] if key in n["direct_blockers"]]
        lanes, delta, residual, action = UPDATES.get(key, ([], "Inherited R98 obligation and preparation.",
                                                          old["current_defect"], old["prepared_action"]))
        obligations[key] = dict(old, current_defect=residual, prepared_action=action, direct_nodes=direct,
                                cycle_delta=delta, evidence_packages=lanes, affected_nodes=affected)
    # Section 11 is the post-checkpoint source-law/solver continuation in the R98 report.
    feedback_sources = (
        ("REPORT_KO.md", "§11, P5 Bianchi row", "aa34c4ffb7e8e00a87dbe2fc6d585676cbafb41504d8e82d48a3b77bc362a293"),
        ("BIANCHI_HISTORY_RESULTS.json", "families.*.radiation_feedback_1loop", pkgs["BIANCHI"]["output_sha256"]["BIANCHI_HISTORY_RESULTS.json"]),
    )
    evidence = []
    for name, locator, pin in feedback_sources:
        path = PREVIOUS / name
        if digest(path) != pin:
            raise ValueError(f"R98 feedback evidence changed: {name}")
        evidence.append(dict(path=str(path.relative_to(ROOT)), locator=locator, sha256=pin))
    family = read(PREVIOUS/"BIANCHI_HISTORY_RESULTS.json")["families"]
    obligations["M08"]["extension_evidence"] = evidence
    obligations["M08"]["max_one_loop_delta_sigma_over_H_VII_h"] = family["VII_h"]["radiation_feedback_1loop"]["max_1loop_delta_sigma_over_H"]
    gaia = read(OUT/"GAIA_SHARED_FIELD_RESULTS.json")
    fit_names = list(gaia["actual_rhs_refit_max_error_by_fit"])
    dimensions = (len(fit_names), sum(n in {"quaia_z0","quaia_z1","quaia_z2","quaia_z3"} for n in fit_names),
                  gaia["patches"]["count"], gaia["rank47_supported_and_unsupported_components"]["dimension"],
                  len(gaia["component_order"]))
    if dimensions != (10,4,48,160,6):
        raise ValueError(f"Gaia fit/field description differs from its reported dimensions: {dimensions}")
    rows=[]
    for old in previous["nodes"]:
        bs = old["all_blockers_including_dependencies"]
        pk = list(dict.fromkeys(old["preparation_packages"] + [p for k in bs for p in obligations[k]["evidence_packages"]]))
        actions = [obligations[k]["prepared_action"] for k in old["direct_blockers"]] or old["next_action"]
        rows.append(dict(old, preparation_packages=pk, next_action=actions,
                    available_results=[str(Path(pkgs[p]["evidence_directory"])/f) for p in pk for f in pkgs[p]["outputs"]],
                    changed_obligations=[k for k in bs if k in UPDATES]))
    return dict(schema="htt.r99.exact60_preparation/1", theory_checkpoint="575ff4811b6a5ae12d7c14bf7cd8ecadef7e58aa",
                science_authority=previous["science_authority"], inherited_overlay_sha256=R98_PIN,
                original_42_payload_sha256=GATES_PIN, canonical_edges=dag["edges"],
                source_qualification_overlay=dag["source_qualification_overlay"], counts=previous["counts"],
                node_count_by_paper=previous["node_count_by_paper"], next_id=dag["next_action_id"],
                interpretation="Conditional calculation and acquisition preparation; all original scientific acceptance states preserved.",
                packages=pkgs, blockers=obligations, nodes=rows)

def render_actions(data):
    lines=["# R99: execution preparation and outstanding obligations", "",
           "The canonical program retains 60 nodes and 129 edges. Eighteen nodes carry their original scoped completions; this cycle adds zero scientific promotions. SQ-CF4 is the next source qualifier.",
           "", "Preparation reuses seven R98 products and four R99 lanes. Source identity, chosen assumptions and executable commands are recorded per package in NODE60_EXECUTION_PREPARATION.json.",
           "", "## Node-level applicability", "",
           "| Node | State | Direct obligations | Inherited and direct obligations | Evidence updated this cycle |",
           "|---|---|---|---|---|"]
    for r in data["nodes"]:
        cells=[r["id"],r["original_state"],", ".join(r["direct_blockers"]) or "—",
               ", ".join(r["all_blockers_including_dependencies"]) or "—",", ".join(r["changed_obligations"]) or "—"]
        lines.append("| "+" | ".join(cells)+" |")
    for k,b in data["blockers"].items():
        lines.extend(["",f"## {k} · {b['label']} ({b['category']})","",b["cycle_delta"],"",
                      b["current_defect"],"",b["prepared_action"],"",
                      f"Direct nodes: {', '.join(b['direct_nodes']) or '—'}.  ",
                      f"All affected nodes: {', '.join(b['affected_nodes']) or '—'}.  ",
                      f"Evidence: {', '.join(b['evidence_packages']) or b['R98_evidence']}."])
        for source in b.get("extension_evidence", []):
            lines.append(f"Extension evidence: {source['path']} ({source['locator']}); SHA-256 {source['sha256']}.")
    return "\n".join(lines)+"\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare","science"), default="prepare", nargs="?")
    parser.add_argument("--node", default="SQ-CF4")
    parser.add_argument("--check", action="store_true", help="compare the saved overlay and actions against live source identities")
    parser.add_argument("--run-package", choices=sorted(LANES), help="rerun one explicitly named current-cycle preparation lane")
    args=parser.parse_args(argv)
    if args.run_package and (args.mode != "prepare" or args.check):
        parser.error("--run-package applies only to prepare without --check")
    if args.node not in {n["id"] for n in read(DAG)["nodes"]}:
        parser.error("unknown canonical node")
    if args.run_package:
        mod,_,extra=LANES[args.run_package]
        env={**os.environ,"OPENBLAS_NUM_THREADS":"1","MKL_NUM_THREADS":"1","OMP_NUM_THREADS":"1","PYTHONDONTWRITEBYTECODE":"1"}
        subprocess.run([PY,"-B","-m",f"scripts.r99.{mod}",*extra],cwd=ROOT,env=env,check=True)
    data=build()
    actions=render_actions(data)
    if args.check or args.mode=="science":
        if data != read(OUT/FILE) or actions != (OUT/ACTIONS).read_text():
            raise ValueError("saved execution preparation differs from verified inputs")
    else:
        (OUT/FILE).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
        (OUT/ACTIONS).write_text(actions)
    row=next(n for n in data["nodes"] if n["id"]==args.node)
    print(json.dumps(dict(mode=args.mode,node=args.node,science_status=row["science_status"],next_id=data["next_id"],
        counts=data["counts"],packages=row["preparation_packages"],blockers=row["all_blockers_including_dependencies"],
        science_command_executed=False,promoted=False)))
    return 3 if args.mode=="science" and row["science_status"]=="SCIENCE_BLOCKED" else 0


if __name__=="__main__":
    sys.exit(main())
