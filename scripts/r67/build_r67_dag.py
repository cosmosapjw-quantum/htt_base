"""Create additive seven-axis fusion DAG and conditional data nodes; protect 42 science gates.

No download, no automatic successor, no invented acceptance/independent review.
"""
from pathlib import Path
import json, hashlib, subprocess, copy

BASE=Path("docs/research_program/observational_publication_20261015")
FOLDER=BASE/"R67_SEVEN_AXIS_FUSION_20261118"
BASELINE="1d833bbe0e6c70a42f2d0af002c2e6a7cfcd0593"
CARD="PR-R67-SEVEN-AXIS-FUSION"


def write(p,data):
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+"\n")


def sha(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda:f.read(8*1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def run():
    root=Path(".")
    c=json.loads((FOLDER/"RESULTS/CF4_METHOD_CONTRAST.json").read_text())
    a=json.loads((FOLDER/"RESULTS/GAIA_EB_FRAME.json").read_text())
    assert c["original_group_count"]==38053
    assert c["bootstrap_count"]==32768
    assert c["network"]["rank_all"]==22 and c["network"]["n_groups"]==998
    assert a["results"]["quality"]["n_sources"]==1580645
    pub=BASE/"PUBLICATION_DAG.json"
    p=json.loads(pub.read_text())
    assert len(p["papers"])==6 and len(p["nodes"])==42
    # Compare to the pinned *original* baseline, not just an in-memory
    # snapshot from a possibly already-mutated working tree.
    base = json.loads(subprocess.check_output(
        ["git", "show", f"{BASELINE}:{pub.as_posix()}"], text=True))
    original_nodes=copy.deepcopy(p["nodes"])
    original_papers=copy.deepcopy(p["papers"])
    if original_nodes != base["nodes"] or original_papers != base["papers"]:
        raise AssertionError("Original 42 scientific nodes or P1–P6 paper acceptance differs from baseline")
    old_route=copy.deepcopy(p.get("current_scientific_route"))
    assert old_route["canonical_pr"]=="PR-R66-LOWELL-PHYSICAL-OBSERVABLES"
    origin=original_nodes
    original_hash=hashlib.sha256(json.dumps(origin,sort_keys=True).encode()).hexdigest()
    assert original_hash=="e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
    seven=[
      {"id":"A1","name":"Tensorized five-variable inference","paper":"P1","prior":["R39","R58","R60"],"role":"typed likelihood, nonlinear identified set"},
      {"id":"A2","name":"Low-ell morphology to radiation observables","paper":"P2","prior":["R66"],"role":"signed photon-stress and DQ quotient"},
      {"id":"A3","name":"Radio/source-count dipole anomaly","paper":"P4","prior":["R65"],"role":"population/flux-selection observer template"},
      {"id":"A4","name":"Beyond-FLRW kinematical measurement","paper":"P6","prior":["R61"],"role":"congruence-compatible sigma,omega,A,beta"},
      {"id":"A5","name":"Anisotropy and Bianchi classification","paper":"P5","prior":["R62"],"role":"source-matched class/equivalence"},
      {"id":"A6","name":"Redshift/directional Hubble factor","paper":"P3","prior":["R64"],"role":"H_D(z,n), calibration & depth"},
      {"id":"A7","name":"Local observer boost versus global tilt","paper":"P4","prior":["R63"],"role":"frame/history and independent probe"}
    ]
    paths={
      "cf4_full":"raw/cf4_full/{table3.dat,table4.dat}",
      "gaia_crf3":"raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits",
      "planck":"raw/planck_data/ and htt_open_data/r36_pr4_actual",
      "radio":"raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0, raw/new_acquisitions/radio_hi",
      "sn":"raw/pantheonplus_release_c447f0f_20261110",
      "hsc":"raw/hsc_y3_fourier_space_data_vector.sacc, raw/hsc_y3_mock_1404"
    }
    new_data=[
      {"id":"D-PR4-COMMANDER-T-MC","kind":"scalar-temperature MC ensemble 0200..0299","already_local":"one verified completed 0200, the old 005a I fields are zero","trigger":"P2 candidate stress/doppler result requires real source-qualified Commander T covariance/exchangeability, and exact 0200 product unit+response contract has been verified","download_condition":"number of additional realizations prescribed by predeclared desired tail resolution and covariance rank; no broad campaign","status":"DORMANT_CONDITIONAL"},
      {"id":"D-DESI-DR1-PV","kind":"98,292-object DR1 Fundamental Plane PV value-added release and matched random/selection","already_local":"Fuji limited FP tables, DESI BGS clustering mocks and SDSS PV, not the full DR1 PV source file","trigger":"CF4 method-matched source comparison cannot discriminate calibration vs real bulk and official DR1 PV product is publicly and source-qualified available","download_condition":"confirmed official DESI DR1 VAC and overlapping source IDs/covariance protocol","status":"DORMANT_CONDITIONAL"},
      {"id":"D-RACS-RMS-MISSING","kind":"RACS missing RMS/footprint tiles","already_local":"267 candidate FITS plus control/partial metadata and radio catalogues","trigger":"actual sky completeness of those 267 FITS tiles insufficient for a frozen RACS dipole selection model","download_condition":"download only missing coverage tiles with official release receipts","status":"DORMANT_CONDITIONAL"},
      {"id":"D-GAIA-QSO-Z","kind":"source-qualified quasar redshifts and AGN structure-motion covariates","already_local":"Gaia-CRF3 1,614,173 proper motions, scanning-law and ICRF3, VLBA 713","trigger":"physical redshift dependence of VSH l>=2 has a fixed source/observer frame transfer and current crossmatches cannot support bins","download_condition":"source IDs, predictive-z bias/validation, Gaia frame error budget predeclared; do not count raw Gaia PMs as cosmological matter shear","status":"DORMANT_CONDITIONAL"},
      {"id":"D-REMOTE-DIPOLE","kind":"kSZ remote CMB dipole reconstruction window and bias response","already_local":"published theory and some high-l maps; exact W_v,b_v and full cross-covariance unqualified","trigger":"P4 physical compensated-history source model passes frame/normalization injection and cannot be constrained by existing independent channels","download_condition":"official window/bias/covariance maps or coefficients with comparable velocity units; not convert quoted amplitude directly","status":"DORMANT_CONDITIONAL"},
      {"id":"D-HSC-Y3-ADDITIONAL-MOCK","kind":"more independent weak lensing ray-tracing realizations","already_local":"6 survey fields×108 mock catalogs, 108 underlying parent realizations among 1404 placements","trigger":"actual source-optical transfer exists and current parent-realization covariance/coverage is insufficient for predeclared inference accuracy","download_condition":"explicit independent underlying parent IDs rather than counting placements as independent skies","status":"DORMANT_CONDITIONAL"},
      {"id":"D-BIANCHI-TRANSFER","kind":"polarized source/metric physical Bianchi transfer calibration","already_local":"R62 normal-frame constraint and R66 signed radiation stress; no source-qualified full polarised high-l transfer","trigger":"one chosen type/mode/tilt family and observer/surface epoch passed constraint/optical injection but missing polarized/finite-k response","download_condition":"first use verified external result/benchmark, not build an unvalidated native solver as an implicit data intake","status":"CONDITIONAL_PHYSICS_NOT_PURE_DOWNLOAD"}
    ]
    write(FOLDER/"CONDITIONAL_DATA_REGISTRY.json",{"schema":"htt.r67.conditional_data/1","date":"2026-11-18","root":"/mnt/extdrive/workdir","data_census":"2026-11-18 partial enumerated 219893 files; 79 directories unvisited after 240s, no whole-filesystem identity claim","on_demand_only":True,"automatic_downloads":False,"items":new_data})
    stages_theory=[{"id":f"R{i}","status":"COMPLETE_SCOPED","evidence":"THEORY_10_STAGES.md"} for i in range(1,11)]
    stages_code=[{"id":f"C{i}","status":"COMPLETE_SCOPED","evidence":"CODING_10_STAGES.md"} for i in range(1,9)]
    stages_code.extend([{"id":"C9","status":"INDEPENDENT_CLI_REVIEW_AND_TARGETED_REPAIR_DONE_NATIVE_NOT_RUN","evidence":"REVIEW/review_closure.json"},{"id":"C10","status":"SCOPED_CONTENT_VALIDATED_REMOTE_DELIVERY_TO_VERIFY","evidence":"VALIDATION.md"}])
    fusion_routes=[
      {"id":"FUSE-A","axes":["A1","A4","A6"],"target":"relative method angular calibration and H_D/shear nuisance",
       "state":"ACTUAL_CF4_EXECUTED_CONDITIONAL","evidence":"RESULTS/CF4_METHOD_CONTRAST.json","current_rank":22,
       "next":"R64 source-level H_D cofit with real method shared covariance and heldout coverage","accept":"demonstrate conditional interval/coverage gain or publish calibration limitation, no cosmological p without source selection",
       "physical_referent":"same-group relative distance calibration"},
      {"id":"FUSE-B","axes":["A3","A4","A7"],"target":"observer-frame acceleration/rotation, relative flow and global matter tilt",
       "state":"GAIA_EB_OBSERVED_OTHER_PHYSICAL_JOINT_UNQUALIFIED","evidence":"RESULTS/GAIA_EB_FRAME.json",
       "next":"validated independent VLBA redshift/frame or radio selection matched source transfer","accept":"show source-qualified physical J_eff rank and calibrated cross-covariance; no joining acceleration and velocity by name",
       "physical_referent":"observer-frame angular drift, distinct from bulk flow"},
      {"id":"FUSE-C","axes":["A1","A2","A4","A5"],"target":"radiation stress to integrated geometric shear/Bianchi compatibility",
       "state":"REUSED_SIGNED_OBSERVABLES_PHYSICAL_TRANSFER_UNRESOLVED","evidence":"R62/R66 reports referenced in THEORY_10_STAGES.md",
       "next":"restricted physical transfer and paired T/E/B null","accept":"one type/mode recovery under verified source/polarisation transfer, not morphology-axis-only identification",
       "physical_referent":"photon radiation stress versus spacetime integrated shear"},
      {"id":"FUSE-D","axes":["A1","A4","A5","A6"],"target":"lensing spin2 and spacetime optical/kinematical consistency",
       "state":"DORMANT_OPTICAL_TRANSFER_DEPENDENT","evidence":"disk audit plus R61/R62 prior",
       "next":"typed Jacobi/Sachs transfer and source-overlap covariance before a joint fit","accept":"at least one common physical functional with source-qualified Jacobian and coverage",
       "physical_referent":"lensing distortion, not directly fluid sigma"}
    ]
    dag={
      "schema":"htt.r67.seven_axis_fusion/1",
      "baseline_commit":BASELINE,"date":"2026-11-18","canonical_card":CARD,
      "paper_tracks":6,"research_axes_count":7,"research_axes":seven,
      "original_paper_node_count":42,"original_science_node_sha256":original_hash,
      "original_paper_acceptance_unchanged":True,"existing_scoped_route_preserved":"PR-R66-LOWELL-PHYSICAL-OBSERVABLES",
      "source_locations":paths,
      "stage_theory":stages_theory,"stage_coding":stages_code,
      "fusion_routes":fusion_routes,
      "data_dependency_registry":"CONDITIONAL_DATA_REGISTRY.json",
      "research_plan":"RESEARCH_PLAN_KO.md",
      "validation":"VALIDATION.md",
      "review_closeout":"REVIEW/review_closure.json",
      "actual_results":["RESULTS/CF4_METHOD_CONTRAST.json","RESULTS/GAIA_EB_FRAME.json","RESULTS/RADIAL_ROBUSTNESS.json"],
      "statistical_status":"EXPLORATORY_CONDITIONAL_NOT_COSMOLOGICAL_DETECTION",
      "submission_status":"NOT_READY_TO_SUBMIT","native_subagent":"NOT_RUN_NO_HOST_TOOL",
      "automatic_successor":False,"automatic_download":False,
      "copying_raw_observation_data_to_repo":False
    }
    write(FOLDER/"FUSION_DAG.json",dag)
    p["cross_paper_seven_axis_fusion"]={
      "date":"2026-11-18","canonical_card":CARD,"research_axes_count":7,
      "six_papers_preserved":True,"original_science_node_sha256":original_hash,
      "status":"SCOPED_EXPLORATORY_RESEARCH","submission_status":"NOT_READY_TO_SUBMIT",
      "report":str(FOLDER/"REPORT_KO.md"),"theory":str(FOLDER/"THEORY_10_STAGES.md"),
      "coding":str(FOLDER/"CODING_10_STAGES.md"),
      "research_plan":str(FOLDER/"RESEARCH_PLAN_KO.md"),
      "review_closeout":str(FOLDER/"REVIEW/review_closure.json"),
      "fusion_dag":str(FOLDER/"FUSION_DAG.json"),
      "conditional_data_registry":str(FOLDER/"CONDITIONAL_DATA_REGISTRY.json"),
      "no_automatic_new_science_gates":True
    }
    assert p["nodes"]==base["nodes"] and p["papers"]==base["papers"]
    assert p.get("current_scientific_route")==old_route
    write(pub,p)
    files=[*sorted(Path("scripts/r67").glob("*.py")),*sorted(Path("tests").glob("test_r67_*.py")),
      FOLDER/"RESULTS/CF4_METHOD_CONTRAST.json",FOLDER/"RESULTS/GAIA_EB_FRAME.json",
      FOLDER/"RESULTS/RADIAL_ROBUSTNESS.json",
      FOLDER/"THEORY_10_STAGES.md",FOLDER/"CODING_10_STAGES.md",FOLDER/"REPORT_KO.md",
      FOLDER/"RESEARCH_PLAN_KO.md",FOLDER/"VALIDATION.md",
      FOLDER/"REVIEW/independent_read_only_review.md",FOLDER/"REVIEW/review_closure.json"]
    inputsha={"CF4_table3":c["source_sha256"]["table3.dat"],
              "CF4_table4":c["source_sha256"]["table4.dat"]}
    gaia=Path(a["input"])
    if gaia.exists():inputsha["Gaia_CRf3_FITS"]=sha(gaia)
    write(FOLDER/"PROVENANCE.json",{
      "baseline_commit":BASELINE,"branch":subprocess.check_output(["git","branch","--show-current"],text=True).strip(),
      "schema":"htt.r67.provenance/1",
      "source_sha256":inputsha,
      "science_file_sha256":{str(f):sha(f) for f in files},
      "science_and_numerical_identity_not_equal_to_physical_calibration":True,
      "native_subagent":"NOT_RUN", "five_var_claim":"not independent evidence",
      "original42_preserved":True,"submission_status":"NOT_READY_TO_SUBMIT"
    })
    print(json.dumps({"seven_axes":len(seven),"six_papers":len(p["papers"]),"42_nodes":len(p["nodes"]),
        "routes":len(fusion_routes),"conditional_data_nodes":len(new_data),"sourcehashes":inputsha},indent=2))
if __name__=="__main__":run()
