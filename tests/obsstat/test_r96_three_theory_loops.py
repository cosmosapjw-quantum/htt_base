"""R96 three theory loops - scoped numerical/physics/source audit.

Tests are intentionally not a publication-science PASS; exactly verify
the new legacy repair, CF4 two non-equivalent covariance models,
masked fullcov BiPoSH conditional MC and the selected-m spin2 transport.
"""
from pathlib import Path
from hashlib import sha256
import json
import math
import numpy as np
import healpy as hp
import pytest

from scripts.r96 import cf4_covariance_bridge as cf
from scripts.r96 import cmb_crossfit_null as cmb
from scripts.r96 import legacy_biposh_recovered as legacy
from scripts.r96 import spin2_mblock_extension as spin
from scripts.r96 import reindex_source_reuse as index

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122"
def data(p):return json.loads((OUT/p).read_text())

def test_original_R78_authority_untouched():
 p=ROOT/"docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
 assert sha256(p.read_bytes()).hexdigest()=="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
 d=json.loads(p.read_text())
 assert len(d["nodes"])==60 and len(d["edges"])==129 and d["next_action_id"]=="SQ-CF4"

def test_CF4_real_35970_and_non_psd_difference():
 q=data("CF4_COVARIANCE_RECONCILIATION.json")
 assert q["N_group"]==35970 and q["H03_nwindows"]==4
 assert q["J_cal_36x7_rank"]==7 and q["J_bulk_36x3_rank"]==3
 assert q["cross_model_difference"]["difference_eigen_min"]<0
 assert q["cross_model_difference"]["difference_eigen_max"]>0
 assert not q["cross_model_difference"]["difference_is_psd"]
 assert q["theta_R36_max_abs_diff"]<1e-10
 assert q["max_H0_R95_parity"]<2e-7
 assert not q["publication_ready"] and q["full_S_PV_and_calibration"] is None

def test_CF4_R36_residue_positive_and_H0_not_overpromoted():
 q=data("CF4_COVARIANCE_RECONCILIATION.json")
 r=q["model_B_inherited_R36"]
 assert r["positive_remainder_min_eigen"]>0
 assert r["H0"]==pytest.approx(72.23817782005885,rel=1e-10)
 assert q["model_A_R95_lowrank_grid"]["R5"]["0.05"]["H0"]==pytest.approx(72.00983492814537,rel=1e-10)
 assert q["model_A_R95_lowrank_grid"]["R5"]["0.00"]["H0"]!=pytest.approx(r["H0"],abs=.1)

def test_CF4_woodbury_dense_random_spd_compatible():
 rng=np.random.default_rng(96)
 n,p,m=36,9,7
 X=rng.normal(size=(n,n));C0=X@X.T+2*np.eye(n)
 U=rng.normal(size=(n,m))*.2
 D=rng.normal(size=(n,p));y=rng.normal(size=n)
 beta,cov,chi=cf.woodbury_gls(C0,U,D,y)
 from scipy.linalg import cho_factor,cho_solve
 C=C0+U@U.T
 cc=cho_factor(C,lower=True)
 V=cho_solve(cc,D)
 cf2=np.linalg.inv(D.T@V)
 th=cf2@(D.T@cho_solve(cc,y))
 np.testing.assert_allclose(beta,th,atol=2e-12)
 np.testing.assert_allclose(cov,cf2,atol=2e-12)
 assert chi>0

def test_biposh_legacy_source_sha_and_fail_closed():
 p=legacy.ORIGINAL
 assert p.exists()
 assert "biposh[2] += np.real(a_lm * np.conj(a_lm))" in p.read_text()
 assert legacy.provenance()["original_retained_untouched"]
 nside=8;cl=np.zeros(13);cl[2:]=1/np.arange(2,13)**2
 m=np.zeros(hp.nside2npix(nside));mask=np.ones_like(m)
 with pytest.raises(ValueError,match="source-matched"):
  legacy.estimate_biposh_L2(m,mask,cl,lmax=12,nside=nside)
 with pytest.raises(ValueError,match="matched"):
  legacy.biposh_variance(cl,1.0)

def test_biposh_real_matched_MC_works_and_full_cov():
 rng=np.random.default_rng(960)
 nside=8;npix=hp.nside2npix(nside);lmax=12
 mask=np.ones(npix)
 # Use deterministic moderately anisotropic mask, same for obs+all MC.
 theta,phi=hp.pix2ang(nside,np.arange(npix))
 mask[(theta>1.15)&(theta<2.0)]=0
 cl=np.zeros(lmax+1);ell=np.arange(2,lmax+1);cl[2:]=.1/(ell*(ell+1))
 mc=[]
 for _ in range(32):
  a=np.zeros(hp.Alm.getsize(lmax),complex)
  for l in range(2,lmax+1):
   a[hp.Alm.getidx(lmax,l,0)]=rng.normal(scale=np.sqrt(cl[l]))
   for m in range(1,l+1):
    a[hp.Alm.getidx(lmax,l,m)]=(rng.normal()+1j*rng.normal())*np.sqrt(cl[l]/2)
  mc.append(hp.alm2map(a,nside=nside,lmax=lmax))
 q,c=legacy.estimate_biposh_L2(mc[0],mask,cl,lmax,nside,
     mc_sky_maps=mc[1:],backend="numpy")
 assert q.shape==(5,) and c.shape==(5,5)
 np.testing.assert_allclose(c,c.T,atol=2e-15)
 assert np.linalg.eigvalsh(c).min()>0
 l=legacy.BiPoSHLikelihood(q,c,mask)
 assert l.log_likelihood(q)==pytest.approx(0.,abs=1e-14)
 assert np.isfinite(l.log_likelihood(np.zeros(5)))

def test_CMB_N300_full_cov_and_holdout_not_false_detection():
 j=data("CMB_MASK_BIPO_CROSSVALIDATED_NULL.json")
 assert j["N_MC_unique_noise"]==300 and j["N_signal_MC_full"]==999
 assert j["nside_source"]==2048
 assert j["shrinkage_grid_predeclared"]["0.2"]["N"]==300
 assert j["shrinkage_grid_predeclared"]["0.2"]["d"]==60
 assert j["shrinkage_grid_predeclared"]["0.2"]["shrunken_corr_min_eigen"]>0
 assert j["disjoint_150train_150test"]["N_train"]==150
 assert j["disjoint_150train_150test"]["N_test"]==150
 assert j["R95_original_diagonal_60D_rank"]==pytest.approx(78/301)
 assert j["Bianchi_family_attribution"] is None and j["physical_GF"] is None

def test_CMB_LOO_fullcov_matches_brute_small_sample():
 rng=np.random.default_rng(9601)
 X=rng.normal(size=(30,5))
 y=rng.normal(size=5)
 d=cmb.metric(X,y,shrinkage=.2)
 n=len(X)
 from scipy.linalg import cho_factor,cho_solve
 vals=[]
 for i in range(n):
  rest=np.delete(X,i,axis=0)
  mu=rest.mean(0)
  C=np.cov(rest,rowvar=False,ddof=1)
  sd=np.sqrt(C.diagonal())
  corr=.8*C/sd[:,None]/sd[None,:]+.2*np.eye(5)
  v=(X[i]-mu)/sd
  ch=cho_factor(corr,lower=True)
  vals.append(float(v@cho_solve(ch,v)))
 mu=X.mean(0);C=np.cov(X,rowvar=False,ddof=1);sd=np.sqrt(np.diag(C))
 corr=.8*C/sd[:,None]/sd[None,:]+.2*np.eye(5)
 v=(y-mu)/sd;qq=float(v@cho_solve(cho_factor(corr,lower=True),v))
 assert d["obs_score"]==pytest.approx(qq,rel=2e-13)
 assert d["tail_count"]==sum(x>=qq for x in vals)

def test_spin2_exact_recurrence_and_3j_coeffs():
 j=data("SPIN2_MBLOCK_HIERARCHY.json")
 assert max(j["recurrence_oracle"].values())<2e-12
 assert spin.c_spin(4,2,2)==pytest.approx(1/math.sqrt(7),rel=2e-14)
 assert set(map(int,j["stf_source_normalized_by_m"]))==set(range(-2,3))
 assert j["m_modes_executed"]==[-2,-1,0,1,2]
 assert j["ell_max_executed"]==[8,16,32,60]

def test_spin2_streaming_skew_hermitian_and_B_parity():
 import numpy as np
 for L in (8,16):
  for m in (-2,-1,0,1,2):
   A,K=spin.mblock_matrices(L,m,k=.012)
   assert np.max(abs((A+A.getH()).toarray()))<1e-13
   ev=np.sort(np.linalg.eigvals(K.toarray()[[2,L+1],:][:,[2,L+1]]).real)
   np.testing.assert_allclose(ev,[-1.,-.3],atol=1e-13)
  A,K=spin.mblock_matrices(L,0,k=.012)
  assert np.max(abs(A.toarray()[L+1:,L+1:][-1:]))>=0 # shapes exercise
 j=data("SPIN2_MBLOCK_HIERARCHY.json")
 assert j["m0_B60_abs"]==0.
 assert all(v["B2_abs"]==0. for v in j["zero_k_null_B"])

def test_spin2_source_STF_harmonics_reality():
 S=np.array([[.3,.12,0],[.12,-.2,.09],[0,.09,-.1]])
 am=spin.stf_source_harmonics(S)
 for m in (1,2):
  assert am[-m]==pytest.approx(((-1)**m)*np.conj(am[m]),abs=1e-13)

def test_spin2_allm_claim_limited():
 j=data("SPIN2_MBLOCK_HIERARCHY.json")
 assert not j["full_all_m_curved_tilted_bianchi_coupling_produced"]
 assert j["physical_CMB_power_spectra_or_Bianchi_posterior"] is None
 assert not j["legacy_pr13ag_synthetic_source_promoted"]

def test_source_reindex_three_parent_root_and_remote():
 j=data("SOURCE_REUSE_AUDIT.json")
 assert len(j["roots"])==7 and j["file_count"]>90000
 assert j["archive_member_count"]>150000
 assert j["source_corpus_modified"] is False
 assert j["provenance_source_locks"]["LEGACY_BIPOSH"]["exists"]
 assert Path(j["private_index"]).exists()
 assert j["errors"] and any("zip" in x for x in j["errors"])
 assert data("GITHUB_SOURCE_AUDIT.json")["read_only"] is True
