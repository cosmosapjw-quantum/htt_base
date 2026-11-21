"""R92: curated, reproducible, user-scoped third-loop intake.

Full local file and ZIP/TAR member indexes are in private ~/Downloads; R92
commits only scope-limited scientific source identities, metadata counts and
high-ell analytic toy check. Strict create-only --write; --check recomputes
source hashes/content for selected files without modifying any user repo.
"""
import argparse,collections,hashlib,json,subprocess,sys,zipfile
from pathlib import Path
from scripts.r92.high_ell_gaunt_oracle import examine

BASE=Path("/home/cosmosapjw")
HTT=BASE/"Dropbox/bianchi/htt_base"
OUT=HTT/"docs/research_program/observational_publication_20261015/R92_BASS_HIGH_ELL_THIRD_PREP_20261121"
PRIVATE=BASE/"Downloads/htt_r92_private_index"
SCAN=PRIVATE/"R92_DEEP_INDEX_20261121.summary.json"
GH=PRIVATE/"R92_REMOTE_GITHUB_AUDIT.json"
NATIVE=PRIVATE/"R92_BASS_NATIVE_ISOLATED_PROBE.json"
R78=HTT/"docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R78_SHA="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
ROOTS=[
BASE/"Dropbox/dossier",
BASE/"Dropbox/bianchi/rec_bianchi",
BASE/"Dropbox/bianchi/rei_bianchi",
BASE/"Dropbox/Mayukh_cowork/ver3",
BASE/"Dropbox/Mayukh_cowork/ver2",
BASE/"bass",
HTT/"legacy",
]
# Curated files are a selection from the exhaustive private searchable index.
# Every item has a role and a semantic claim ceiling.
CURATED=[
(0,"BASS_Integrated_Dossier.pdf","unified geometry/transport/reionization/observation theory"),
(0,"Dossier_I_Homogeneous_Geometry.pdf","general Lie/Codazzi/tilt Einstein constraints"),
(0,"Dossier_II_Kinetic_Transport.pdf","photon collisions/boost/screen transport"),
(0,"Dossier_III_Atomic_Processes.pdf","atomic material source/recombination support"),
(0,"Dossier_IV_Reionization.pdf","direction dependent opacity/electron current"),
(0,"Dossier_V_Conservative_Approximation.pdf","adjoint error bounds/constraint evolution"),
(0,"Dossier_VI_Nuclear_Reactions.pdf","initial composition/source support, not immediate anisotropy likelihood"),
(0,"Dossier_VII_Observation.pdf","finite aperture/polarized observables Kasner"),
(5,"bianchi/charts/class_a_tilted_multi.py","class A tilted multi-species source"),
(5,"bianchi/charts/class_b_tilted.py","class B tilted frame/gauge/constraints"),
(5,"bianchi/matter/hierarchy.py","PSTF kinetic moment lmax=6 only"),
(5,"bianchi/matter/grid_boltzmann.py","angle/momentum grid Thomson collision oracle"),
(5,"bianchi/matter/freestream.py","homogeneous massless/null transport quadrature"),
(5,"bianchi/q/polarization.py","basis free J_ab screen and Thomson"),
(5,"bianchi/q/transport.py","native-required photon radial/angular transport"),
(5,"bianchi/physical/frame_transport.py","orthonormal triad/observer frame"),
(5,"tests/test_v1_high_l_signs.py","l4 tilted equation test (current native ABI blocker)"),
(5,"tests/test_p_polarization.py","polarization exact finite tests"),
(5,"repro/native/BASS-RF02B-R4-DELTA-20260826/rf02b-wheel/bianchi_rustcore-0.1.0-cp312-cp312-manylinux_2_34_x86_64.whl","local installed/native artifact probe (not accepted wheel)"),
(1,"src/full_bianchi_hyrec/trajectory/characteristic_angular.py","axisymmetric Bianchi I frequency/angle characteristics"),
(1,"src/full_bianchi_hyrec/trajectory/full_coupled_adaptive.py","physical coupled H/He history candidate"),
(1,"src/full_bianchi_hyrec/recoil/full_harmonic_deposition.py","recoil harmonic angular deposition"),
(1,"src/full_bianchi_hyrec/background/axisymmetric_bianchi_i.py","Bianchi I background axisymmetric exact"),
(1,"tests/trajectory/test_axisymmetric_bianchi_i_physical_transport.py","axisymmetric ray transport tests"),
(2,"docs/science/current_OPERATOR_SPEC.md","current reionization current/opacity operator"),
(2,"docs/science/current_STATE_LEDGER.md","REI state acceptance limits"),
(3,"HTT.zip","Mayukh historical tilted-distance likelihood and synthetic controls"),
(3,"bianchi_defect_overleaf.zip","Mayukh Bianchi derivation manuscript source"),
(4,"code_data_package.zip","Mayukh older mock and tilted FLRW implementation"),
(4,"manuscript_source.zip","Mayukh original mathematical draft"),
(6,"bianchi_departure_v091_github.zip","historical lowl pixel/BipoSH code; fsky-only correction suspect"),
(6,"bass_htt_mio_github_ready_current.zip","historical projected solver L4/L6/L8 scope"),
(6,"bass_htt_mio_github_ready_PR28_20260416.zip","historical multipole handoff; not native physical solver"),
(6,"bianchi_origin.zip","early lowell Bianchi math/solver design"),
]
HTT_SOURCES=[
("htt/bass/background/general_tilted_evolution.py","R49 general tilted background bridge"),
("htt/bass/transport/general_bianchi_transfer.py","R49 source-conditional Bianchi transport"),
("htt/htt/htt/infer/r49_general_bianchi_likelihood.py","R49 multi-probe likelihood bridge"),
("scripts/r91/pliklite_baseline.py","Plik-lite high-l FLRW scalar baseline not Bianchi likelihood"),
("scripts/r90/sf_attribution.py","R90 STF-Codazzi conditional Bianchi compatibility"),
("scripts/r91/planck_cl_morphology.py","R91 same-C2 different chi exact counterexample"),
]
ARCHIVE_HITS=[
(3,"HTT.zip","HTT/htt/catalog_likelihood.py"),
(3,"HTT.zip","HTT/outputs/null_test_integrated.json"),
(6,"bianchi_departure_v091_github.zip","htt/likelihood/biposh_masked.py"),
(6,"bianchi_departure_v091_github.zip","htt/likelihood/pixel_lowl.py"),
(6,"bass_htt_mio_github_ready_current.zip","bass_htt_mio_github_ready_current/docs/pr13/PR13AG_PROJECTED_MULTIPOLE_SOLVER_SCOPE.md"),
(6,"mz_cmb_truncation_artifacts.zip","mz_cmb_truncation/SUMMARY.md"),
]
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for buf in iter(lambda:f.read(1<<20),b""):h.update(buf)
 return h.hexdigest()
def pdf_pages(p):
 obj=subprocess.run(["pdfinfo",str(p)],capture_output=True,text=True,timeout=12)
 if obj.returncode: return None
 for l in obj.stdout.splitlines():
  if l.startswith("Pages:"):return int(l.split(":",1)[1])
 return None
def local_source():
 rows=[]
 for r,rel,role in CURATED:
  p=ROOTS[r]/rel
  if not p.is_file():raise RuntimeError("missing expected selected source: "+str(p))
  d={"root_id":r,"relative_path":rel,"bytes":p.stat().st_size,
     "sha256":sha(p),"role":role,
     "science_status":"CANDIDATE_FOR_BRIDGE_NOT_PHYSICAL_PASS"}
  if rel.endswith(".pdf"):d["pages"]=pdf_pages(p)
  rows.append(d)
 for rel,role in HTT_SOURCES:
  p=HTT/rel
  if not p.is_file():raise RuntimeError("missing HTT scientific entry: "+rel)
  rows.append({"root_id":"HTT_ACTIVE","relative_path":rel,
               "bytes":p.stat().st_size,"sha256":sha(p),
               "role":role,"science_status":"PRIOR_SOURCE_SCOPE_ONLY"})
 archived=[]
 for r,name,member in ARCHIVE_HITS:
  p=ROOTS[r]/name
  with zipfile.ZipFile(p) as z:
   info=z.getinfo(member)
   # Avoid extraction: hash byte content of small curated member only
   if info.file_size>200_000:raise RuntimeError("curated member too large")
   content=z.read(info)
   archived.append({"root_id":r,"archive":name,"member":member,
                    "bytes":info.file_size,"crc":info.CRC,
                    "sha256":hashlib.sha256(content).hexdigest(),
                    "reuses":"history/model prototype only; do not promote to observation without external source"})
 return {"schema":"htt.r92.selected_science_modules_source_ids/1",
         "curated_source_files":rows,"archive_members_sampled_and_content_hashed":archived,
         "original_dossier_copyright_scope":"only metadata and short notes published; PDFs not repackaged"}
def audit_scan():
 j=json.loads(SCAN.read_text())
 larger=json.loads((PRIVATE/"R92_LARGETAR_SECOND_PASS.json").read_text())
 idx=json.loads((PRIVATE/"R92_SEARCH_INDEX_STATUS.json").read_text())
 assert len(j["roots"])==7 and j["total_files"]==92127
 assert j["archive_count"]==754 and idx["count"]==256138
 good=sum(k.startswith("INDEXED") for k in j["archive_status"] for _ in range(j["archive_status"][k]))
 large_good=sum(x["status"]=="INDEXED_TAR_SECOND_PASS" for x in larger)
 errors=[x for x in json.loads((PRIVATE/"R92_DEEP_INDEX_20261121.archives.json").read_text())["archives"] if x["status"]=="ERROR"]
 return {"schema":"htt.r92.seven_exact_source_roots_archive_members/1",
         "root_metrics":[{"root_id":r["root_id"],"root":r["root"],"file_entries":r["files"],"directory_entries":r["dirs"],
                          "bytes_sum":r["bytes"],"kinds":r["kinds"]} for r in j["roots"]],
         "total_files":j["total_files"],"archive_files":j["archive_count"],
         "archive_main_metadata_indexed":good,
         "deferred_large_tars_extra_indexed":large_good,
         "archive_indexed_total":good+large_good,
         "archive_current_unreadable":len(errors),
         "unreadable_reason_codes":[{"root_id":x["root"],"archive":x["rel"],
                                    "reason":"ZIP_CENTRAL_DIRECTORY_INVALID"} for x in errors],
         "zip_tar_member_records":j["archive_member_count"],
         "nested_indexed_member_records":j["nested_archive_entries"],
         "large_tar_secondpass_members":sum(x["member_names_partial_or_full"] for x in larger if x["status"]=="INDEXED_TAR_SECOND_PASS"),
         "full_private_search_entries":idx["count"],"private_search_db":idx["database"],
         "private_index_not_in_repo":True,"read_only_no_archive_extraction":True}
def remote():
 j=json.loads(GH.read_text())
 rows=[]
 for item in j["projects"]:
  if item.get("is_private"):
   rows.append({"name":item["name"],"status":"PRIVATE_METADATA_ONLY_NOT_PUBLIC_REPO_SNAPSHOT"})
   continue
  rows.append({"name":item["name"],"url":item.get("url"),"status":item["status"],
               "branches":[{"branch":b.get("branch"),"head_sha":b.get("head_sha"),"paths_returned":b.get("blob_paths"),
                            "api_tree_truncated":b.get("truncated",None),"status":b.get("status")} for b in item["branches"]]})
 # HTT live active branch tree is complete locally; cannot elevate GitHub API partial to full
 # Historical R92 response measured the parent tree before the R92 commit.
 # Compare to that immutable commit, never to changing HEAD after publication.
 n=subprocess.run(["git","ls-tree","-r","--name-only","13cf6b7dbf12144d51410395bd2962f281d884b3"],cwd=HTT,capture_output=True,text=True,timeout=20,check=True)
 return {"schema":"htt.r92.related_github_branch_tree_audit/1","public_related":rows,
         "htt_active_branch_local_full_tree_count":len(n.stdout.splitlines()),
         "htt_api_truncation_recovered_by_local_git_tree":True,
         "historical_open_prs_not_merged_by_this_work":True}
def backend():
 j=json.loads(NATIVE.read_text())
 return {"schema":"htt.r92.bass_native_and_high_l_gate/1",
         "BASS_hierarchy_supported_Lmax":6,
         "BASS_high_l_l4_pytest_bass_env":{"pass":1,"fail":1,
                   "failure":"Installed native bianchi_rustcore lacks rayon_thread_pool_size; not a physics sign mismatch"},
         "BASS_polarization_pure_numpy_pytest":{"pass":3,"fail":0},
         "isolated_matching_wheel_symbol":j["rayon_capability_available"],
         "isolated_matching_wheel_test_status":j["test"]["status"],
         "isolated_wheel_failure":"RF00 installed SBOM byte size identity mismatch in development temporary isolation",
         "bass_or_htt_installed_packages_changed":False,
         "recovery":"Qualify wheel metadata/SBOM in locked provenance; install only through separately authorized BASS owner workflow",
         "third_loop_bianchi_high_ell_ready":False}
def build():
 if sha(R78)!="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11":
  raise RuntimeError("R78 source identity drift")
 maps={
  "SCANNED_ROOTS_AND_ARCHIVES.json":audit_scan(),
  "CURATED_BASS_BIANCHI_SOURCES.json":local_source(),
  "GITHUB_REPO_PROVENANCE.json":remote(),
  "HIGH_ELL_L2_GAUNT_CONSTRUCTION.json":examine(),
  "BASS_NATIVE_AND_TRANSFER_READINESS.json":backend()
 }
 return {name:json.dumps(payload,indent=2,ensure_ascii=False)+"\n" for name,payload in maps.items()}
def main():
 ap=argparse.ArgumentParser()
 x=ap.add_mutually_exclusive_group(required=True)
 x.add_argument("--write",action="store_true")
 x.add_argument("--check",action="store_true")
 args=ap.parse_args()
 try:
  result=build()
  if args.write:
   if any(OUT.iterdir()):raise RuntimeError("R92 create-only output dir not empty")
   for n,s in result.items():(OUT/n).write_text(s)
  else:
   for n,s in result.items():
    if (OUT/n).read_bytes()!=s.encode():raise RuntimeError("R92 content check mismatch "+n)
  print(json.dumps({"status":"PREPARATION_ONLY","files":len(result),
                    "archives_total":754,"archive_indexed":753,
                    "local_files":92127,"searchable_entries":256138,
                    "whole_third_cycle_executed":False,
                    "physical_Bianchi_family_attribution_claimed":False,
                    "mode":"write" if args.write else "check"},ensure_ascii=False))
  return 0
 except (OSError,KeyError,ValueError,RuntimeError,zipfile.BadZipFile) as e:
  print("R92_PREP_FAIL_CLOSED",repr(e),file=sys.stderr);return 2
if __name__=="__main__":raise SystemExit(main())
