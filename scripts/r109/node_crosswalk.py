"""Bind R109 native evidence to the canonical R78 DAG, preserving all scientific states."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

BASE = Path(__file__).resolve().parents[2] / "docs/research_program/observational_publication_20261015"
OUT = BASE/"R109_NATIVE_RUST_BIANCHI_20261124"
REGISTRIES = {
    "R78": ("R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json", "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"),
    "R105": ("R105_RESEARCH_20261124/NODE60_EXECUTION.json", "9b2f78f4c1935f3c72e4deffbd4c394b47672172b1ea813b68c610c4997529ab"),
    "R108": ("R108_LOS_ATLAS_DATA_20261124/R108_RESULTS.json", "128c0c38f7ed1d6c81e5fb680068798b84fbb4a8ca2f61cdfae1952873277f52"),
}
# Each route is narrower than its original R78 acceptance.
DIRECT = {
    "B01": ("atlas", "Twelve finite Lie-family initial-state templates, including exceptional VI_-1/9; scoped inventory only."),
    "B02": ("atlas,material", "All signed m of polarized finite homogeneous skies; separately integrated early REC and late REI material. High-ell and physical initial-mode transfer remain open."),
    "B03": ("atlas,commander", "The measured R108 Commander response acts on the signed R109 recoil modes across archived orientations. No observed temperature/polarization score, matched-release null or blinded recovery."),
    "SQ-NATIVE": ("atlas,material,commander", "Three original Rust repositories now supply executable deterministic templates and source-bound finite material. Family-confusion, real Planck injection and held-out null remain open."),
    "SQ-PHOTON-FLUX": ("atlas", "Observer/propagation frames, numerical photon flux and separate dust/recoil terms in a common synthetic normal frame. Independent source photon moments and covariance remain open."),
    "SQ-LIE-FLUX": ("atlas,codazzi,rotations", "Hamiltonian, Codazzi, Jacobi and radiation/dust flux diagnostics on evolved Lie data. Independent observed rho, j, pi and shear covariance remain open."),
    "SQ-FRAME": ("atlas,material", "Exact FLRW boost control, source electron velocity and observer velocity are distinct. Signed REI donor redshift/clock tested in its finite observer frame. Survey frame calibration remains open."),
    "PHY-02": ("atlas", "Normal photon flux and multifluid constraints are checked in numerical initial-value trajectories. The observational frame-matched moment law and held-out test remain open."),
    "PHY-05": ("atlas,codazzi,rotations", "Common-time Codazzi/Jacobi and split radiation/dust flux on exceptional VI_-1/9, with temporal and angular refinements. Independent noisy residual covariance and rank test remain open."),
}
RELATED = {
    "H02":"Manticore supplied 1,120 LOS draws on 14 clusters. The project still lacks a three-dimensional posterior grid on the registered CF4 support.",
    "SQ-CF4":"The new Manticore source has 14 cluster locations. It does not supply the selected CF4 catalogue covariance or held-out independence.",
    "SQ-CMB-NULL":"Commander response now acts on deterministic native skies, but supplies no additional independent null realizations or calibration." ,
    "B04":"Family simulations supply candidates; no R109 confusion matrix or observational evidence ratio.",
    "L03":"Simulated intrinsic sky modes can enter a matched release pipeline; the Planck null depth is inherited.",
    "SQ-OPTICAL":"The REI photon-redshift optical-depth check uses LRS-I material; a finite-z Jacobi/position-drift transfer fit is still separate.",
    "SQ-CROSS-COV":"A finite weighted law on model skies cannot determine actual cross-survey covariance or a held-out null.",
    "PHY-03":"Doppler FLRW control uses one observer velocity; radio flux response and survey count law require real source populations.",
    "PHY-06":"Numerical higher multipoles and evolving stress supply controlled test cases. This round does not identify the proposed dot-stress commutator on measured photons.",
}
PAPER_NAMES = {"P1":"Five-variable tensor inference","P2":"Large-angle CMB morphology",
               "P3":"Directional Hubble field","P4":"Radio dipole and observer motion",
               "P5":"Bianchi classification","P6":"Beyond-FLRW kinematics"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def generate(bass_repo, directory=OUT):
    docs = {}
    for name, (relative, expected) in REGISTRIES.items():
        data = (BASE/relative).read_bytes()
        if digest(data) != expected:
            raise ValueError(f"altered {name} registry")
        docs[name] = json.loads(data)
    old, last = docs["R78"], docs["R105"]
    nodes = {r["id"]:r for r in old["nodes"]}
    if (len(nodes) != 60 or len(old["edges"]) != 129 or last["edges"] != old["edges"]
            or set(nodes) != {r["id"] for r in last["nodes"]}):
        raise ValueError("inconsistent science DAG")
    commander_path=directory/"COMMANDER_NATIVE_PROJECTION.json"
    commander_raw=commander_path.read_bytes()
    commander=json.loads(commander_raw)
    coefficient_file=directory/"COMMANDER_NATIVE_COEFFICIENTS.npz"
    coefficient_sha=digest(coefficient_file.read_bytes())
    codazzi_file=directory/"CODAZZI_FIX_KO.md"
    codazzi_bytes=codazzi_file.read_bytes()
    manticore_file=directory/"MANTICORE_ROUTE_KO.md"
    manticore_bytes=manticore_file.read_bytes()
    if not (commander.get("shape")==[12,384,3,5] and commander["channels"]==["T","E","B"]
            and coefficient_sha==commander["output_sha256"]):
        raise ValueError("invalid Commander response receipt")
    new_raw = (directory/"NATIVE_MATERIAL_SKY.json").read_bytes()
    new = json.loads(new_raw)
    rev = new["binaries"]["bass"]["commit"]
    atlas_path = "research/r109_native_sky/ATLAS.json"
    atlas_raw = subprocess.check_output(["git", "-C", str(bass_repo), "show", f"{rev}:{atlas_path}"])
    atlas = json.loads(atlas_raw)
    rotation_path = "research/r109_native_sky/LIE_ROTATIONS.json"
    rotation_raw = subprocess.check_output(["git", "-C", str(bass_repo), "show", f"{rev}:{rotation_path}"])
    json.loads(rotation_raw)
    if not (atlas["archive_sha256"] == commander["atlas_sha256"] and all("recoil_"+k in atlas["cases"] for k in ("I","II","III","IV","V","VI0","VIh","VIstar","VII0","VIIh","VIII","IX"))
            and "boost_max_component_error" in atlas["controls"] and len(new["cases"]) == 6):
        raise ValueError("required native receipts do not contain the declared cases")
    rows = []
    for inherited in last["nodes"]:
        node_id=inherited["id"]
        n=nodes[node_id]
        if n["state"] != inherited["canonical_state"] or n["acceptance"] != inherited["canonical_acceptance"]:
            raise ValueError(f"canonical state or acceptance changed at {node_id}")
        row={"id":node_id,"paper":n["paper"],"canonical_state":n["state"],"depends_on":n["depends_on"]}
        if node_id in DIRECT:
            ids, text = DIRECT[node_id]
            row.update(r109="direct_scoped_numerical",evidence=ids.split(","),comment=text)
        elif node_id in RELATED:
            row.update(r109="upstream_relevance_only",comment=RELATED[node_id])
            if node_id in ("H02","SQ-CF4"):
                row["evidence"]=["manticore"]
            if node_id=="SQ-CMB-NULL":
                row["evidence"]=["commander"]
        else:
            row["r109"]="inherited"
        rows.append(row)
    return {"schema":"htt.r109.canonical_crosswalk/1","authority":{k:{"path":p,"sha256":s} for k,(p,s) in REGISTRIES.items()},
            "original_42_sha256":old["original_42_payload_sha256"],"next_id":old["next_action_id"],
            "counts":{"nodes":len(rows),"edges":len(old["edges"]),"R109_coverage":dict(Counter(x["r109"] for x in rows)),
                      "canonical_states":dict(Counter(x["canonical_state"] for x in rows)),"scientific_promotions":0},
            "evidence":{"rotations":{"repo":"cosmosapjw-quantum/bass","commit":rev,"path":rotation_path,
                                     "sha256":digest(rotation_raw),"scope":"native rotated generic Lie data"},
                        "codazzi":{"repo":"cosmosapjw-quantum/htt_base","path":str(codazzi_file.relative_to(BASE)),
                                   "sha256":digest(codazzi_bytes),"scope":"initial-data versus public residual sign"},
                        "manticore":{"repo":"cosmosapjw-quantum/htt_base","path":str(manticore_file.relative_to(BASE)),
                                     "sha256":digest(manticore_bytes),"measured_cluster_los_draws":1120,
                                     "unique_clusters":14,"target_3d_Manticore_grids":0},
                        "commander":{"repo":"cosmosapjw-quantum/htt_base","path":str(commander_path.relative_to(BASE)),
                                     "sha256":digest(commander_raw),"operator_output_shape":commander["shape"],
                                     "coefficient_file":coefficient_file.name,"coefficient_sha256":coefficient_sha},
                        "atlas":{"repo":"cosmosapjw-quantum/bass","commit":rev,"path":atlas_path,
                                 "sha256":digest(atlas_raw),"cases":len(atlas["cases"]),"mode_archive_sha256":atlas["archive_sha256"]},
                        "material":{"repo":"cosmosapjw-quantum/htt_base","path":str((directory/"NATIVE_MATERIAL_SKY.json").relative_to(BASE)),
                                    "sha256":digest(new_raw),"cases":len(new["cases"]),
                                    "native_skies":sum(len(x.get("transfer_runs",[])) for x in new["cases"].values())}},
            "six_papers":{k:{"topic":PAPER_NAMES[k],"nodes":[x["id"] for x in rows if x["paper"]==k]}
                          for k in old["papers"]},
            "seven_cross_routes":[{**x,"objective":nodes[x["id"]]["objective"]} for x in old["seven_R77_PHY_combinations"]],
            "R108_route_groups":list(docs["R108"]["nodes"]),"nodes":rows,
            "physical_Pi":None,"physical_GF":None,"calibrated_p":None,"family_attribution":None}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bass-repo",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=OUT/"NODE_CROSSWALK.json")
    args=parser.parse_args()
    args.output.write_text(json.dumps(generate(args.bass_repo),indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    main()
