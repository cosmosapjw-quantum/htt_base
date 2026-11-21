"""R94: bounded implementation/solver-source readiness tests, not science DAG PASS."""
from pathlib import Path
import hashlib
import json
import math
import numpy as np
import pytest
from sympy.physics.wigner import wigner_3j

from scripts.r94 import gaunt_fast as fast
from scripts.r94 import stream_fullres as stream
from scripts.r94 import prepare_handoff as handoff
from scripts.r93.smica_ffp999_biposh import iso_theory_cl, gaunt_terms, project_biposh, loo_diag_q

D=handoff.D
def read(name):
 return json.loads((D/name).read_text())

def test_r78_original_60_129_immutable():
 from scripts.r94.prepare_handoff import sha
 assert sha(handoff.R78)==handoff.EXPECTED_SHA
 d=json.loads(handoff.R78.read_text())
 assert len(d["nodes"])==60 and len(d["edges"])==129
 assert d["next_action_id"]=="SQ-CF4"

def test_gaunt_closedform_exact_wigner_samples():
 for l in (2,3,4,5,10,40,46):
  for m in (-l,-1,0,1,l):
   if abs(m)>l:continue
   for M in (0,1,2):
    ref=(-1)**m*math.sqrt(5*(2*l+1)*(2*l+5)/(4*math.pi))*float(wigner_3j(l,2,l+2,0,0,0))*float(wigner_3j(l,2,l+2,-m,M,m-M))
    value=fast.gaunt_l2_stepup(l,m,M)
    assert value==pytest.approx(ref,rel=6e-14,abs=3e-15)

def test_gaunt_invalid_arguments_fail_explicitly():
 for l,m,M in [(-1,0,0),(4,5,0),(4,0,3)]:
  with pytest.raises(ValueError):
   fast.gaunt_l2_stepup(l,m,M)
 with pytest.raises(ValueError):
  fast.build_terms(np.ones(10),8,bands=((2,8),))

def test_gaunt_cpp_kernel_matches_reference_on_real_map():
 c=iso_theory_cl()
 terms=fast.build_terms(c,48)
 old=gaunt_terms(c)
 path=Path.home()/"Downloads/htt_r93_ffp999_alm_biposh/SMICA_999_NSIDE64_MASKED_ALM_L48.npz"
 with np.load(path,allow_pickle=False) as j:
  alm=j["paired_masked_alm_lmax48"][:20].astype(np.complex128)
 reference=project_biposh(alm,old)
 new=fast.project(alm,terms,"native")
 np.testing.assert_allclose(reference,new,rtol=1e-12,atol=2e-12)

def test_numpy_gaunt_match_compiled_cpp():
 c=iso_theory_cl()
 terms=fast.build_terms(c,48)
 rng=np.random.default_rng(409)
 alm=rng.normal(size=(16,1225))+1j*rng.normal(size=(16,1225))
 for l in range(49):alm[:,l]=alm[:,l].real
 numpy_res=fast.project(alm,terms,"numpy")
 native_res=fast.project(alm,terms,"native")
 np.testing.assert_allclose(numpy_res,native_res,rtol=2e-12,atol=1e-11)

def test_loo_fast_matches_np_delete_999():
 rng=np.random.default_rng(94)
 x=rng.normal(loc=1.0,scale=.5,size=(999,20))
 z=rng.normal(size=20)
 old=loo_diag_q(x,z)
 new=fast.loo_diagonal_fast(x,z)
 assert old["null_tail_count"]==new["null_tail_count"]
 assert new["rank_p"]==pytest.approx(old["rank_p"])
 assert new["observed_score"]==pytest.approx(old["observed_score"],rel=5e-13,abs=3e-13)

def test_loo_stable_under_large_shared_offsets():
 rng=np.random.default_rng(93)
 x=rng.normal(size=(120,5))+1e6
 z=rng.normal(size=5)+1e6
 ref=loo_diag_q(x,z)
 new=fast.loo_diagonal_fast(x,z)
 assert new["rank_p"]==pytest.approx(ref["rank_p"],abs=0)
 assert new["observed_score"]==pytest.approx(ref["observed_score"],rel=1e-9)

def test_gaunt_benchmark_uses_real_full999_with_same_statistic():
 j=read("GAUNT_CXX_SOURCE_BENCHMARK.json")
 assert j["fixed_params"]["n_cmb"]==999
 assert j["fixed_params"]["n_unique_noise"]==300
 assert j["n_exact_sympy_gaunt_reference_cases"]==54
 assert j["max_gaunt_abs_error"]<3e-14
 assert j["projector_max_abs_error_vs_R93_native"]<3e-12
 assert j["mc_rank_no_change"]=={"300":97/301,"999":.249,"300_tail":96,"999_tail":248}
 assert j["end_to_end_speedup_not_claimed"]

def test_gaunt_benchmark_source_sha_and_binary_source_identical():
 j=read("GAUNT_CXX_SOURCE_BENCHMARK.json")
 assert fast.sha(Path(j["source_identity"]["native_binary_path"]))==j["source_identity"]["native_binary_sha256"]
 assert fast.sha(Path(fast.__file__))==j["source_identity"]["R94_code_source_sha256"]
 assert fast.sha(fast.CPP)==j["source_identity"]["R94_CPP_source_sha256"]

def test_actual_ffp_fullres_stream_pilot_3_ids_and_source_sha():
 j=read("FFP10_FULLRES_STREAM_PILOT.json")
 assert j["selected_cmb_ids"]==[0,818,999]
 assert j["source_case_count"]==3 and j["raw_file_sha_actual"]
 assert not j["full_resolution_entire_999_done"]
 assert not j["full_EB_null_calibrated"]
 assert stream.sha(Path(j["private_harmonic_path"]))==j["private_harmonic_sha256"]
 with np.load(j["private_harmonic_path"],allow_pickle=False) as d:
  assert d["TEB_alm"].shape==(3,3,1225)
  np.testing.assert_array_equal(d["cmb_ids"],[0,818,999])
  np.testing.assert_array_equal(d["noise_ids"],[0,218,99])

def test_bad_padding_00818_is_documented_not_hidden():
 p=read("FFP10_FULLRES_STREAM_PILOT.json")
 case=next(x for x in p["cases"] if x["id"]==818)
 assert case["actual_hashed"]
 assert any("truncated" in w for w in case["observed_reader_warnings"])
 assert all(not x["observed_reader_warnings"] for x in p["cases"] if x["id"]!=818)

def test_reused_solver_12_families_einstein_euler_and_screen():
 d=read("REUSED_SOLVER_CONDITIONAL_TRANSFER.json")
 assert d["counts"]=={"exact_geodesic_family_count":12,"linearized_executed":6,
   "linearized_rejected_correctly":6,"cutoff_case_count":12,
   "dynamic_Einstein_Euler_families":12}
 assert len(d["dynamic_12_family_Einstein_Euler_and_geodesic"])==12
 assert max(x["max_hamiltonian"] for x in d["dynamic_12_family_Einstein_Euler_and_geodesic"].values())<1e-8
 assert max(x["max_codazzi"] for x in d["dynamic_12_family_Einstein_Euler_and_geodesic"].values())<1e-8
 assert max(x["max_null_err"] for x in d["dynamic_12_family_Einstein_Euler_and_geodesic"].values())<1e-8
 assert all(x["claim_tier"].startswith("EXACT_SYNTHETIC") for x in d["full_12_bianchi_families_geodesic"].values())

def test_reused_exact_Thomson_REC_REI_source_not_fake_physical():
 d=read("REUSED_SOLVER_CONDITIONAL_TRANSFER.json")
 assert 0<d["source"][0]["fractional_energy_error"]<1e-12
 assert d["source"][0]["screen_leak"]<1e-12
 assert 0<d["optical_history_BianchiI_constructed"]["tau_with_fixed_xe"]<1
 assert d["optical_history_BianchiI_constructed"]["REI_electron_history_qualified"] is False
 assert d["REI_pair_bound_construction"]["source_Ne_difference_envelope"]<1e-6
 assert not d["physics_claim_ceiling"]["native_all_m_CMB_EB_likelihood"]
 assert d["physics_claim_ceiling"]["source_congruence_and_transfer_calibration"] is None

def test_reused_solver_original_source_shas_current():
 from scripts.r94.prepare_handoff import sha
 d=read("REUSED_SOLVER_CONDITIONAL_TRANSFER.json")
 s=d["sources_sha256"]
 assert sha(Path("/home/cosmosapjw/bass/bianchi/q/polarization.py"))==s["BASS_polarization"]
 assert sha(Path("htt/bass/transport/general_bianchi_transfer.py"))==s["HTT_R49_transfer"]
 assert sha(Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi/src/full_bianchi_hyrec/background/axisymmetric_bianchi_i.py"))==s["REC_background"]

def test_three_root_deep_scan_actual_and_private_index():
 j=read("SOURCE_REUSE_INDEX.json")
 assert len(j["local_roots"])==3
 assert j["all_physical_files"]==15712
 assert j["all_zip_member_records"]==4320
 assert len(j["curated_source_sha256"])==19
 assert j["source_python_symbol_candidates"]>=1000
 assert Path(j["private_local_index"]).is_file()
 assert j["source_modification"] is False

def test_pdf_dossier_source_text_qualified():
 j=read("SOURCE_REUSE_INDEX.json")
 pdf=[x for x in j["curated_source_sha256"] if x["rel"].endswith(".pdf")]
 assert len(pdf)==8
 assert all(x["pages"]>5 for x in pdf)
 assert all(x["pdftotext_exit"]==0 and x["text_chars"]>1000 for x in pdf)

def test_every_original_60_node_receives_no_fake_pass():
 j=read("R94_PROGRAM_EXECUTION_MAP.json")
 assert j["r78_nodes"]==60 and j["r78_hard_edges"]==129
 assert j["scientific_next_id"]=="SQ-CF4"
 assert set(j["six_paper_routes"])=={"P1","P2","P3","P4","P5","P6"}
 assert len(j["rows"])==60
 assert len(j["seven_PHY_nodes"])==7
 assert set(j["external_native_boltzmann_required_ids"])=={"SQ-NATIVE","B02","B03","B04","B05"}
 assert all(not x["original_science_status_changed"] for x in j["rows"])
 assert all(not x["actual_r94_physical_science_acceptance"] for x in j["rows"])

def test_old_R89_blocker_counts_preserved():
 j=read("R94_PROGRAM_EXECUTION_MAP.json")
 assert j["r89_verdict_totals"]=={
  "REUSED_SCOPED":18,"DIAGNOSTIC_COMPLETED_SCOPED":4,
  "BLOCKED_INPUT":9,"BLOCKED_DEPENDENCY":29}

def test_no_unauthorised_nonrepo_artifact_links():
 j=read("SOURCE_REUSE_INDEX.json")
 assert j["private_all_filename_index"].startswith(str(Path.home()/"Downloads"))
 assert not j["file_extract_or_copy_to_repo"]

def test_handoff_written_and_data_safe():
 j=read("R94_PROGRAM_EXECUTION_MAP.json")
 assert "next_science_question" in j["rows"][0]
 p=D/"LOCAL_CODING_AGENT_HANDOFF_KO.md"
 assert p.exists()
 assert "SQ-CF4" in p.read_text()
 assert "Boltzmann" in p.read_text()
 assert "Downloads" in p.read_text()
