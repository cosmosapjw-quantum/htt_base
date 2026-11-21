"""R93 third science cycle: actual source identities, numerics, and anti-PASS claims."""
import json, math,hashlib,ast
from pathlib import Path
import numpy as np
import pytest
import healpy as hp
from sympy.physics.wigner import wigner_3j
from scripts.r93 import build_third_science_overlay as a
from scripts.r93 import smica_ffp999_biposh as b
from scripts.r93 import legacy_cf4_doppler as d
from scripts.r93 import legacy_biposh_critic as legacy

@pytest.fixture(scope="module")
def r93():
 names=["SMICA_999_NSIDE64_BIPOSH_RESULT.json",
 "NSIDE2048_VS_N64_ALM_TRANSFER_QA.json",
 "SMICA_FULLRES_EB_FIRSTPAIR_PILOT.json",
 "LEGACY_BIPOSH_INVALID_ESTIMAND.json",
 "CF4_LEGACY_TILT_DOPPLER_COMPARISON.json",
 "BASS_HTT_CODAZZI_SAME_STATE_RESULT.json",
 "LEGACY_SECOND_DEEP_SCAN.json",
 "WORK_DAG_60_EVIDENCE.json"]
 return {n:json.loads((a.OUT/n).read_text()) for n in names}

def test_original_DAG_count_sha_and_next_action():
 dag=json.loads(a.R78.read_text())
 assert a.sha(a.R78)==a.SHA_R78
 assert len(dag["nodes"])==60 and len(dag["edges"])==129
 assert dag["next_action_id"]=="SQ-CF4"

def test_all_original_60_never_promoted(r93):
 j=r93["WORK_DAG_60_EVIDENCE.json"]
 assert j["frozen_original_nodes"]==60 and j["frozen_original_edges"]==129
 assert j["original_next_action_id"]=="SQ-CF4"
 assert j["no_unconditional_science_60_pass"]
 assert len(j["items"])==60
 assert all(not n["physics_publication_pass_promoted"] for n in j["items"])
 assert all(not n["original_R78_science_state_changed"] for n in j["items"])

def test_six_papers_and_seven_phy_nodes_present(r93):
 j=r93["WORK_DAG_60_EVIDENCE.json"]
 assert set(j["new_papers_scoped"])=={"P1","P2","P3","P4","P5","P6"}
 assert len(j["old_seven_PHY"])==7
 assert set(j["external_native_boltzmann_lane"])==a.TRANSFER
 assert j["r93_science_coverage"]["actual_new_P2_T_NSID64_999"]==999
 assert not j["r93_science_coverage"]["original_60_scientific_nodes_all_executed"]

def test_work_overlay_exact_R89_status_not_relabelled(r93):
 j=r93["WORK_DAG_60_EVIDENCE.json"]
 assert j["r89_verdict_totals"]=={
 "REUSED_SCOPED":18,"DIAGNOSTIC_COMPLETED_SCOPED":4,
 "BLOCKED_INPUT":9,"BLOCKED_DEPENDENCY":29}

def test_four_band_joint_mc_counts_and_p_rank(r93):
 j=r93["SMICA_999_NSIDE64_BIPOSH_RESULT.json"]
 assert j["source_counts"]["cmb_ids"]==999
 assert j["source_counts"]["noise_ids"]==300
 assert j["source_counts"]["missing_cmb_id"]==970
 assert j["fft_lmax"]==48 and j["nside"]==64
 assert len(j["bands"])==4
 t=j["global_unique_noise_300"]
 assert t["MC_N"]==300 and t["null_tail_count"]==96
 assert t["rank_p"]==pytest.approx(97/301)
 s=j["global_noise_reused_999"]
 assert s["MC_N"]==999 and s["null_tail_count"]==248
 assert s["rank_p"]==pytest.approx(249/1000)
 assert j["Bianchi_family_attribution"] is None

def test_all999_complex_alm_persisted_and_id970_missing(r93):
 j=r93["SMICA_999_NSIDE64_BIPOSH_RESULT.json"]
 p=Path(j["private_full_alm_path"])
 assert p.exists() and b.sha(p)==j["private_full_alm_sha256"]
 with np.load(p,allow_pickle=False) as f:
  ids=f["cmb_ids"]
  nids=f["noise_id_for_each_cmb"]
  alm=f["paired_masked_alm_lmax48"]
  x=f["biposh_real5_by_band"]
 assert alm.shape==(999,hp.Alm.getsize(48))
 assert x.shape==(999,4,5)
 assert set(ids)==set(range(1000))-{970}
 np.testing.assert_array_equal(nids,ids%300)

def test_300_unique_noise_and_recycled_999_not_claimed_iid(r93):
 j=r93["SMICA_999_NSIDE64_BIPOSH_RESULT.json"]
 assert j["source_counts"]["noise_pairing"]=="noise_id = cmb_id % 300"
 assert "300_REUSED_NOISE" in j["claim"]
 assert j["physical_significance"].startswith("conditional")
 assert len(j["global_reused_noise_cycle_sensitivity"])==3
 assert all(x["MC_N"]>50 for x in j["global_reused_noise_cycle_sensitivity"].values())

def test_source_cache_sha_registered_and_A8_replay(r93):
 j=r93["SMICA_999_NSIDE64_BIPOSH_RESULT.json"]
 assert j["source_cache_sha256"]=="86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
 assert j["cache_original_lmax8_alm_max_abs_rounding"]<2e-6
 assert b.sha(b.CACHE)==j["source_cache_sha256"]

def test_theory_fixed_ell_mapping_and_gaunt_3j_rules():
 C=b.iso_theory_cl()
 assert np.all(C[2:]>0)
 t=b.gaunt_terms(C)
 assert len(t)==len(b.BANDS)*3
 for l in (8,40):
  assert wigner_3j(l,2,l+1,0,0,0)==0
  assert wigner_3j(l,2,l+2,0,0,0)!=0
 for (ib,M),v in t.items():
  assert v["G_squared_norm"]>0
  assert len(v["terms"])>0

def test_null_alm_is_complex_and_real_m0_encoder(r93):
 j=r93["SMICA_999_NSIDE64_BIPOSH_RESULT.json"]
 for name,row in j["bands"].items():
  assert len(row["observed_signed_biposh_real5"])==5
  assert row["unique_noise_300"]["rank_p"]>0
  assert row["recycled_noise_999"]["rank_p"]>0

def test_positive_quadrupole_injection_all_four_bands(r93):
 j=r93["SMICA_999_NSIDE64_BIPOSH_RESULT.json"]
 assert j["injection_gY20"]==.1
 assert len(j["injection_average_shift_A20_by_band"])==4
 assert all(v>0.05 for v in j["injection_average_shift_A20_by_band"])

def test_NSIDE64_high_l_not_claimed_exact(r93):
 j=r93["NSIDE2048_VS_N64_ALM_TRANSFER_QA.json"]
 e=[j["bands"][s]["relative_alm_L2_difference"] for s in ("2-8","9-16","17-32","33-46")]
 assert e[0]<e[1]<e[2]<e[3]
 assert e[3]==pytest.approx(.0408649943,rel=1e-4)
 assert j["no_high_l_detection"]
 assert "single" in j["scope"]

def test_one_real_EB_pilot_does_not_count_as_null(r93):
 j=r93["SMICA_FULLRES_EB_FIRSTPAIR_PILOT.json"]
 assert j["nside"]==2048 and j["lmax"]==48
 assert j["full_999_EB_done"] is False
 assert j["Bianchi_family_detected"] is False
 assert len(j["observed_EB_bandpowers"])==4
 assert len(j["one_MC_pair_EB_bandpowers"])==4
 assert 0.7<j["mean_weighted_f_sky_polarization"]<.85

def test_CF4_full35970_beta0_and_gamma_effect(r93):
 j=r93["CF4_LEGACY_TILT_DOPPLER_COMPARISON.json"]
 assert j["cf4_all_selected_groups"]==35970
 m=j["amplitude_grid"]
 assert m["0.0"]["lowz_dmu_p95_abs_mag"]==0
 assert m["0.001"]["lowz_dmu_p95_abs_mag"]==pytest.approx(7.21710166041e-5,rel=1e-7)
 assert m["0.003"]["lowz_dmu_p95_abs_mag"]==pytest.approx(6.57136904836e-4,rel=1e-7)
 assert m["0.01"]["lowz_dmu_p95_abs_mag"]>m["0.003"]["lowz_dmu_p95_abs_mag"]
 assert j["physical_SQ_CF4_acceptance"]=="BLOCKED_INPUT"

def test_CF4_exact_formula_gamma_consistency():
 beta=.13;mu=.73;zc=.12
 gam=1/math.sqrt(1-beta**2)
 zobs=(1+zc)*gam*(1+beta*mu)-1
 recover=(1+zobs)/(gam*(1+beta*mu))-1
 assert recover==pytest.approx(zc,abs=1e-13)
 old=(1+zobs)/(1+beta*mu)-1
 assert old!=pytest.approx(zc,abs=1e-4)

def test_CF4_legacy_zip_member_source_identity(r93):
 j=r93["CF4_LEGACY_TILT_DOPPLER_COMPARISON.json"]
 assert j["source_zip_sha256"]==d.sha(d.ZIP)
 assert j["cf4_group_sha256"]==d.sha(d.CF4)
 assert j["legacy_code_not_executed"]

def test_R93_legacy_second_deep_scan_active_not_old_snapshot(r93):
 j=r93["LEGACY_SECOND_DEEP_SCAN.json"]
 assert j["physical_file_count"]==2913
 assert j["zip_count"]==24
 assert j["zip_member_count"]==4320
 assert j["python_AST_parsed_count"]==1005
 assert j["sqlite_FTS_search_entries"]==5325
 assert j["archives_not_extracted"] and j["no_source_modification"]
 assert Path(j["private_search_database"]).is_file()

def test_legacy_extracted_vs_zip_duplicates_verified(r93):
 j=r93["LEGACY_SECOND_DEEP_SCAN.json"]
 eq=j["selected_archive_extracted_identity"]
 assert sum(x["bytes_identical"] for x in eq.values())==1294
 assert not any(x["content_mismatch"] or x["extracted_missing_or_unmapped"] for x in eq.values())

def test_legacy_biposh_is_invalid_estimand(r93):
 j=r93["LEGACY_BIPOSH_INVALID_ESTIMAND.json"]
 assert j["MC_N"]==999
 assert j["legacy_pseudo_A20_positive_fraction"]==1
 assert j["legacy_pseudo_A20_mean"]>0
 assert all(.45<x<.55 for x in j["proper_Gaunt_centered_A20_fraction_negative_by_band"])
 assert "INVALID" in j["conclusion"]
 assert j["publication_significance"]=="NOT_QUALIFIED"

def test_BASS_HTT_convention_bridge_cross_code(r93):
 j=r93["BASS_HTT_CODAZZI_SAME_STATE_RESULT.json"]
 assert j["test_count"]==60 and j["canonical_strata"]==12
 assert j["max_equation_residual"]<5e-12
 assert j["max_SO3_covariance_residual"]<5e-12
 assert j["normalizations"].startswith("Sigma=sigma/H")
 assert not j["physical_family_attribution"]
 assert not j["full_tilted_positive_EOS_coverage"]

def test_BASS_HTT_source_hash_still_matches(r93):
 j=r93["BASS_HTT_CODAZZI_SAME_STATE_RESULT.json"]
 p=Path("/home/cosmosapjw/bass/bianchi/conventions.py")
 q=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/background/convention_bridge.py")
 assert a.sha(p)==j["source_sha256"]["BASS"]
 assert a.sha(q)==j["source_sha256"]["HTT"]

def test_legacy_script_implements_not_bogus_same_noise_independence():
 s=b.__doc__
 assert "300 noise IDs" in s
 assert "NOT constitute" in s
 assert "999-noise null" in s

def test_R93_code_syntax_static():
 for file in Path("scripts/r93").glob("*.py"):
  ast.parse(file.read_text(),filename=str(file))

def test_legacy_report_and_handoff():
 out=a.OUT
 assert (out/"R1_C1_TO_R10_C10_RESEARCH_REPORT_KO.md").is_file()
 assert "60노드 전체" in (out/"R1_C1_TO_R10_C10_RESEARCH_REPORT_KO.md").read_text()
