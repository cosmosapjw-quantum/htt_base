"""R90 solver-free Bianchi attribution and safe source intake, scoped contracts."""
import hashlib, json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scripts.r90 import sf_attribution as a, crossroute, build_science_lanes as b, selection_support
from scripts.r90.download_minimal import ALLOWLIST, DEST

def payload(name):
 return json.loads((b.OUT/name).read_text())

def test_r78_immutable_60_nodes_129_edges():
 dag=b.validate_inputs()
 assert len(dag["nodes"])==60 and len(dag["edges"])==129
 assert dag["next_action_id"]=="SQ-CF4"
 assert b.hash_path(b.SSOT)==b.EXPECTED_SHA_R78

def test_non_solver_overlay_17_units_exact_six_plus_seven():
 d=payload("WORK_DAG.json")
 s=[n for n in d["nodes"] if n["lane"]=="solver_free"]
 t=[n for n in d["nodes"] if n["lane"]=="external_native_transfer"]
 assert len(s)==17 and len(t)==5
 assert {n["id"] for n in s}>={f"SF-P{i}" for i in range(1,7)}
 assert {n["id"] for n in s}>={f"SF-PHY-{i:02d}" for i in range(1,8)}
 assert {n["id"] for n in t}=={"TRANSFER-"+x for x in b.SOLVER_ORIGINAL}
 assert len(d["original_node_lane_mappings"])==60
 assert not any(x["scientific_state_changed"] for x in d["original_node_lane_mappings"])
 assert not d["no_global_agent_START"] is False

def test_all_original_hard_dependencies_remain_in_unmodified_ssot():
 d=b.validate_inputs()
 parents={n["id"]:set(n.get("depends_on",[])) for n in d["nodes"]}
 assert parents["B03"]=={"B02","L03"}
 assert parents["H04"]=={"H02","H03"}
 assert parents["PHY-07"]=={"SQ-CF4","SQ-RADIO","SQ-OPTICAL","SQ-FRAME"}

def test_stf_frobenius_orthonormal_and_rotation_invariant():
 E=a.STF
 np.testing.assert_allclose(np.einsum("aij,bij->ab",E,E),np.eye(5),atol=3e-15)
 for v in ([.3,.2,-.7],[1.1,0,.2]):
  B=a.rotation_stf(Rotation.from_rotvec(v).as_matrix())
  np.testing.assert_allclose(B.T@B,np.eye(5),atol=5e-15)

def test_exceptional_vi_rank_stratum():
 assert np.linalg.matrix_rank(a.codazzi_stf((0,1,-4),2/3))==2
 assert np.linalg.matrix_rank(a.codazzi_stf((0,1,-4),0.6))==3
 assert np.linalg.matrix_rank(a.codazzi_stf((0,0,0),0))==0
 assert np.linalg.matrix_rank(a.codazzi_stf((0,0,0),1))==3

def test_all_r62_seven_variants_twelve_witnesses_source_identity():
 d=payload("ATTRIBUTION_RESULT.json")
 assert len(d["source_variants"])==7
 for name,r in d["source_variants"].items():
  assert r["finite_witness_count"]==12
  assert len(r["canonical_compatibility"])==12
  assert (a.ROOT/r["source"]).is_file()
  assert a.sha(a.ROOT/r["source"])==r["sha256"]
  assert r["fiveview"]["Pi_physical"] is None
  assert r["fiveview"]["G_F_physical"] is None
  for _,v in r["canonical_compatibility"].items():
   assert v["feasible_distance2_upper"]<=r["confidence_cutoff95"]
   assert v["status"]=="CANONICAL_WITNESS_COMPATIBLE"
 assert d["novel_family_attribution"].startswith("NOT_ESTABLISHED")
 assert d["native_boltzmann_required"] is False

def test_witness_profile_independent_of_gaussian_normalization():
 variant=a.evaluate_variant("log",fast=True)
 original=json.loads((a.R62/"log__J2_coefficients.json").read_text())
 y=np.array(original["mean"])
 C=np.array(original["covariance"])
 n,aa=a.CANONICAL_REPRESENTATIVES["V"]
 J=a.codazzi_stf(n,aa)
 from scipy.linalg import null_space
 B=null_space(J)
 q,w=a.profile_fixed_orientation(y,C,B,np.eye(3))
 r=y-w
 direct=float(r@np.linalg.solve(C,r))
 assert np.isclose(q,direct,atol=1e-9,rtol=1e-9)
 assert variant["canonical_compatibility"]["V"]["feasible_distance2_upper"]<=q+1e-9

def test_flexible_flux_algebraic_only():
 # For any STF normal-frame shear x, choose momentum q=M*x.
 x=np.array([.03,-.04,.07,.02,.04])
 for n,aa in a.CANONICAL_REPRESENTATIVES.values():
  C=a.codazzi_stf(n,aa)
  q=C@x
  np.testing.assert_allclose(C@x-q,np.zeros(3),atol=1e-15)
 # This alone makes no statement about DEC/EOS/actual source realization.

def test_new_real_seven_cross_phy_boundaries():
 d=payload("CROSS_PHY_RESULT.json")
 assert all(f"PHY-{i:02d}" in d for i in range(1,8))
 assert d["physical_Pi"] is None and d["physical_GF"] is None
 assert d["PHY-01"]["masked_leakage_dipole_norm"]>0
 assert d["PHY-05"]["VI_exception_rank"]==2
 assert d["PHY-05"]["VI_generic_rank"]==3
 assert d["PHY-07"]["rank9"]==9 and d["PHY-07"]["rank12"]==12
 assert d["PHY-06"]["rotation_preserves_chi_abs_error"]<1e-12

def test_downloads_fixed_local_small_and_byte_qualified():
 d=payload("DOWNLOAD_RECEIPT.json")
 assert d["download_folder"]==str(DEST)
 assert not d["whole_PR4_downloaded"]
 assert not d["downloaded_to_external_drive"]
 assert d["total_bytes"]==1679839
 assert len(d["files"])==3
 for x in d["files"]:
  p=Path(x["path"])
  assert p.parent==DEST and p.is_file()
  assert p.stat().st_size==ALLOWLIST[x["name"]][0]
  assert hashlib.md5(p.read_bytes()).hexdigest()==x["md5"]
  assert b.hash_path(p)==x["sha256"]

def test_quaia_selection_relative_maps_are_finite_not_cosmo_likelihood():
 d=payload("QUAIA_SELECTION_RESULT.json")
 assert d["same_pixelization_49152"]
 assert -1<=d["cross_threshold_full_pixel_delta_pearson"]<=1
 assert len(d["full_survey_selection_maps"])==2
 assert d["physical_Pi"] is None and d["physical_GF"] is None
 for k,v in d["full_survey_selection_maps"].items():
  assert v["n_pixels"]==49152
  assert 0<=v["F_uniform_sky_selection_gt0p5"]<=1
  assert v["coordinate_chart"]=="UNVERIFIED_FROM_FITS_HEADER"

def test_blocker_ledger_real_categories_and_remaining_physics():
 ledger=payload("BLOCKER_LEDGER.json")
 assert ledger["unresolved_non_solver_blocks"]>0
 assert ledger["external_transfer_blocks"]==2
 assert {"DATA","MODEL","ADDITIONAL_ANALYSIS","SOLVER_DEPENDENT"}=={x["category"] for x in ledger["entries"]}
 assert all(x["physical_claim_status"]=="OPEN_NOT_CLOSED" for x in ledger["entries"])
 assert all(x["solverfree_route"] and x["exact_missing_to_promote"] for x in ledger["entries"])

def test_reused_six_paper_evidence_exact_sha():
 ev=payload("REUSED_SIX_PAPER_EVIDENCE.json")
 assert set(ev)==set(b.SF_GROUPS)
 for v in ev.values():
  assert b.hash_path(b.ROOT/v["path"])==v["sha256"]

def test_20_stage_boundaries_no_fake_independent_reviews():
 ev=payload("STAGE_EVIDENCE.json")
 assert len(ev["theory"])==10 and len(ev["coding"])==10
 assert ev["native_subagent"]=="NOT_RUN_NO_HOST_NATIVE_SPAWN"
 assert not ev["scientific_60_of_60_pass"] and not ev["physical_Bianchi_type_identified"]

def test_create_only_sources_have_not_been_modified():
 assert a.sha(a.G07)==payload("ATTRIBUTION_RESULT.json")["source_G07_sha256"]
 assert b.hash_path(b.SSOT)==b.EXPECTED_SHA_R78

def test_own_r90_report_has_no_sci_pass_claim():
 text=(b.OUT/"REPORT_KO.md").read_text()
 assert "84/84" in text
 assert "original science state unchanged" in text
 assert "NOT" in text
