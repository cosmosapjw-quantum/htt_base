"""Targeted R67 numerical/semantic tests, no novel physical prior implied."""
from pathlib import Path

import numpy as np
import pytest

from scripts.r67.fusion import (read_cf4_groups, stf_features, features,
                                pair_experiment, grouped_network, score_model)


def toy_groups(N=400, seed=21):
    rng = np.random.default_rng(seed)
    n = rng.normal(size=(N,3))
    n /= np.linalg.norm(n, axis=1)[:,None]
    D = np.exp(rng.uniform(np.log(20),np.log(300),size=N))
    mu_common = rng.normal(33,1,N)
    vals = {x:mu_common.copy() for x in ("FP","TF","SN")}
    errs = {x:np.full(N,.3) for x in ("FP","TF","SN")}
    return {"id":np.arange(N),"distance_mpc":D,"n":n,
            "mu":vals,"err":errs}


def test_stf_evenness_and_orthogonality():
    rng = np.random.default_rng(79)
    n = rng.normal(size=(50000,3))
    n/=np.linalg.norm(n,axis=1)[:,None]
    q = stf_features(n)
    np.testing.assert_allclose(q,stf_features(-n),atol=1e-14)
    assert np.max(np.abs(np.mean(q,axis=0))) < .006
    np.testing.assert_allclose(q.T@q/len(q), np.eye(5)*2/15, atol=.004)


def test_same_group_common_distance_cancels():
    a=toy_groups()
    f=features(a["distance_mpc"],a["n"],np.log(a["distance_mpc"]).mean(),
               np.log(a["distance_mpc"]).std())
    beta=np.array([.03,.02,.015,.04,-.06,.05,.03,.005,-.04,.01,.03])
    a["mu"]["TF"]=a["mu"]["FP"]+f@beta
    p=pair_experiment(a,"TF","FP",64,8)
    assert p["overlap_groups"]==400 and p["rank_all"]==11
    np.testing.assert_allclose(p["beta_full"],beta,atol=1e-10)
    shift=np.cos(np.arange(400)*.1) + 33
    for k in a["mu"]:
        a["mu"][k]+=shift
    p2=pair_experiment(a,"TF","FP",64,8)
    np.testing.assert_allclose(p2["beta_full"],beta,atol=1e-10)
    np.testing.assert_allclose(p["beta_full"],p2["beta_full"],atol=1e-10)


def test_joint_network_profiles_group_intercepts_and_gauge():
    a=toy_groups(seed=37)
    ell=np.log(a["distance_mpc"])
    f=features(a["distance_mpc"],a["n"],ell.mean(),ell.std())
    btf=np.array([.06,-.01,.03,.02,-.01,.04,.005,.02,-.003,.012,.022])
    bsn=np.array([-.12,.01,.02,-.02,.04,.03,-.01,.017,.01,.004,-.027])
    a["mu"]["TF"]+=f@btf
    a["mu"]["SN"]+=f@bsn
    res=grouped_network(a,reps=64,seed=17)
    assert res["rank_all"]==22
    assert res["n_groups"]==400 and res["n_contrasts"]==800
    assert res["triple_method_groups"]==400
    np.testing.assert_allclose(res["beta_full"][:3],btf[:3],atol=1e-10)
    np.testing.assert_allclose(res["beta_full"][3:6],bsn[:3],atol=1e-10)
    np.testing.assert_allclose(res["beta_full"][6:14],btf[3:],atol=1e-10)
    np.testing.assert_allclose(res["beta_full"][14:22],bsn[3:],atol=1e-10)
    for k in a["mu"]:
        a["mu"][k]+=a["distance_mpc"]*.013
    res2=grouped_network(a,reps=64,seed=17)
    np.testing.assert_allclose(res["beta_full"],res2["beta_full"],atol=1e-10)


def test_incomplete_network_rank_scoped():
    a=toy_groups(200)
    for j in range(200):
        a["mu"]["SN"][j]=np.nan
        a["err"]["SN"][j]=np.nan
    with pytest.raises(ValueError,match="(rank deficient|nonidentification)"):
        grouped_network(a,reps=16)


def test_wild_null_reproducibility():
    a=toy_groups(250,seed=42)
    a["mu"]["TF"]+=np.random.default_rng(9).normal(0,.3,250)
    x=pair_experiment(a,"FP","TF",100,7)
    y=pair_experiment(a,"FP","TF",100,7)
    assert x["wild_group_p_exploratory"]==y["wild_group_p_exploratory"]
    assert x["rank_all"]==11


def test_real_cf4_source_optional():
    d=Path("/mnt/extdrive/workdir/raw/cf4_full")
    if not (d/"table3.dat").exists():
        pytest.skip("Only portable synthetic numerical tests available")
    a=read_cf4_groups(d)
    assert len(a["id"])==38053
    overlap=np.isfinite(a["mu"]["FP"]) & np.isfinite(a["mu"]["TF"])
    assert int(overlap.sum())==694
    assert np.unique(a["id"]).size==38053

def test_rank_deficient_nuisance_fails_closed():
    # Fresh-review counterexample: blindly completing X0 QR can steal
    # angular signal, even though the true added-variable gain is 4.
    z=np.array([1.,-1.,1.,-1.])
    X0=np.ones((4,2))  # two duplicate nuisance columns, rank 1
    Xa=z[:,None]
    with pytest.raises(ValueError,match="Radial nuisance rank deficient"):
        score_model(z,X0,Xa,np.arange(4),16,22)
    b0=np.linalg.lstsq(X0,z,rcond=None)[0]
    full=np.column_stack([X0,Xa])
    b=np.linalg.lstsq(full,z,rcond=None)[0]
    np.testing.assert_allclose(np.linalg.norm(z-X0@b0)**2-
                               np.linalg.norm(z-full@b)**2,4.,atol=1e-12)


def test_equivalent_lnH_rms_has_nonnegative_sign():
    a=toy_groups(250,seed=72)
    f=features(a["distance_mpc"],a["n"],
               np.log(a["distance_mpc"]).mean(),
               np.log(a["distance_mpc"]).std())
    a["mu"]["TF"]+=f[:,3] * .03
    result=pair_experiment(a,"FP","TF",32,9)
    assert result["equivalent_lnH_angular_rms_if_fixed_redshift"]>=0
    np.testing.assert_allclose(result["equivalent_lnH_angular_rms_if_fixed_redshift"],
                               np.log(10)/5*result["full_sky_model_angular_rms_mag"])
