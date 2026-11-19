"""R79 C7: source-typed numerical preparation checked against original physics.

Original R61/R65/R66/R74/R75/R69 sources read-only. This is not a new joint
cosmological likelihood or native Bianchi Einstein--Boltzmann transfer.
"""
import hashlib
import json
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u
from scipy.integrate import solve_ivp

from scripts.r68.fiveview_geometry import E, stf_coordinates, stf_matrix
from htt.obsstat.pre_dag_fast import (
    OnlineCovariance, codazzi_map, confidence_support,
    photon_feasibility, ring_softmax_occupancy, rotate_stf,
    sachs_rhs, schur_covariance, analysis_lane_policy)

ROOT=Path("docs/research_program/observational_publication_20261015")
HERE=ROOT/"R79_PRE_DAG_CODING_20261119"
R61=ROOT/"R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/IMAGES/KINEMATIC_IMAGES.json"
NVSS=ROOT/"R65_DIPOLE_ANOMALY_20261117/RESULTS"
R66=ROOT/"R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"
R74=ROOT/"R74_P4_SOURCE_SCORE_FIVEVIEW_20261119/RESULTS.json"
R75=ROOT/"R75_P5_LIE_TILT_FIVEVIEW_20261119/RESULTS.json"
GAIA=HERE/"C7_GAIA_FULL_REPLAY.json"


def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()


def radio():
    original=json.loads((NVSS/"NVSS_OBSERVED_RESULT.json").read_text())
    summary=json.loads((NVSS/"INTERPRETATION_SUMMARY.json").read_text())
    previous=json.loads(R74.read_text())
    carrier=NVSS/"NVSS_CONDITIONAL_CARRIERS.npz"
    assert sha(carrier)==previous["source_hashes"]["R65_original_pixel_carrier"]
    with np.load(carrier,allow_pickle=False) as z:
        n=np.asarray(z["base64_pixel_vectors"],float)
        groups=np.asarray(z["base64_groups"],int)
        counts=np.asarray(z["base64_counts"],float)
    assert n.shape==(33000,3) and counts.shape==(3,33000)
    _,inverse=np.unique(groups,return_inverse=True)
    assert len(np.unique(inverse))==185
    cmb=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
    axis=np.array([np.cos(cmb.ra.rad)*np.cos(cmb.dec.rad),
                   np.sin(cmb.ra.rad)*np.cos(cmb.dec.rad),
                   np.sin(cmb.dec.rad)])
    event=n@axis>0
    k=summary["nvss_tables"][0]["peak_response_diagnostics"]["0.75"]["response"]
    fitted=original["models"]["base64_dipole"]["independent_fits"]
    out={}
    for j in range(3):
        logw=n[:,:2]@np.asarray(fitted[j]["estimate"][:2])
        totals=np.bincount(inverse,weights=counts[j],minlength=185)
        got=ring_softmax_occupancy(logw,inverse,event,totals,directions=n,k=k[j])
        old=previous["actual_R65_masked_F_response"]["source_geometry_and_exact_ring_z_null"][f"bin_{j+1}"]
        f_diff=abs(got["F"]-old["F_ring_predicted_at_beta0"])
        grad_diff=np.max(np.abs(got["dF_dbeta"]-old["F_ring_kinematic_score_gradient"]))
        assert f_diff<2e-13 and grad_diff<3e-12,(j,f_diff,grad_diff)
        assert abs(got["dF_dbeta"][2])<2e-13
        out[f"bin_{j+1}"]={
            "selected_count":int(counts[j].sum()),
            "source_F":got["F"],
            "conditional_dF_dbeta":got["dF_dbeta"].tolist(),
            "old_R74_F_absolute_error":float(f_diff),
            "old_R74_gradient_max_error":float(grad_diff),
            "observed_physical_beta_or_GF":False}
    return out


def photon_and_lie():
    r66=json.loads(R66.read_text())
    original={}
    for release in ("PR3","PR4"):
        x=r66["nonlinear"][release]["radiation_moment_bundle"]["pi5_over_rho"]
        p=photon_feasibility(stf_matrix(x),f=None)
        assert p["admissible"] is None and p["pressure_PSD"]
        original[release]={"P_min_eigen":float(p["pressure_eig"][0]),
                           "photon_flux_source_missing":True}
    S=np.array([[-2.,0.,0.],[0.,0.,1.],[0.,1.,2.]])
    x=stf_coordinates(S)
    N=np.diag([0.,3.,-3.])
    a=np.array([1.,0.,0.])
    M=codazzi_map(a,N)
    assert np.linalg.matrix_rank(M)==2
    np.testing.assert_allclose(M@x,0.,atol=1e-13)
    Q=np.array([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]])
    xnew=rotate_stf(x,Q)
    newmap=codazzi_map(Q@a,Q@N@Q.T)
    np.testing.assert_allclose(newmap@xnew,Q@(M@x),atol=2e-13)
    original["exceptional_VI_minus_one_ninth"]={
        "Codazzi_map_rank":2,
        "rotation_equivariance":"PASS",
        "total_flux_from_independent_physical_source":"UNAVAILABLE"}
    return original


def cf4_support():
    x=json.loads(R61.read_text())
    model=x["variants"]["log"]["1.0"]
    mu=np.asarray(model["estimate11"],float)
    C=np.asarray(model["covariance11"],float)
    assert mu.shape==(11,) and C.shape==(11,11)
    n=np.eye(3)
    w=np.column_stack([np.zeros((3,3)),n,
                       np.einsum("ni,aij,nj->na",n,E,n)])
    cutoff=x["contract"]["cutoffs"]["simultaneous11"]
    lo,hi=confidence_support(mu,C,w,cutoff=cutoff)
    exp=w@mu-np.sqrt(cutoff*np.einsum("ni,ij,nj->n",w,C,w))
    np.testing.assert_allclose(lo,exp,atol=1e-13,rtol=0)
    conditional=schur_covariance(C,3)
    assert np.linalg.eigvalsh(conditional)[0]>0
    return {"R61_source_rows":x["source"]["n_groups"],
            "simultaneous11_cutoff":float(cutoff),
            "three_source_angular_lower":lo.tolist(),
            "three_source_angular_upper":hi.tolist(),
            "conditional_Schur_eigen_min":float(np.linalg.eigvalsh(conditional)[0]),
            "physical_H_and_vorticity_unidentified":True}


def optics():
    initial=np.r_[np.zeros(4),np.eye(2).ravel()]
    tests={}
    for k in (0.,.1):
        T=np.eye(2)*k
        sol=solve_ivp(lambda t,y:sachs_rhs(y,T),(0.,1.),initial,
                      rtol=3e-12,atol=3e-14)
        assert sol.success
        J=sol.y[:4,-1].reshape(2,2)
        analytic=1. if k==0 else np.sin(np.sqrt(k))/np.sqrt(k)
        error=np.linalg.norm(J-analytic*np.eye(2))
        assert error<3e-11
        tests[str(k)]={"fixed_affine_J_analytic":float(analytic),
                       "Frobenius_error":float(error)}
    return tests


def gaia_full():
    data=json.loads(GAIA.read_text())
    assert data["source_total_rows"]==1614173
    fits=data["original_saved_fit_comparison"]
    assert fits["quality"]["n"]==1580645
    max_err=max(max(case["errors"].values()) for case in fits.values())
    assert max_err<2e-9
    patch=data["original_saved_patch_covariance_comparison"]
    assert patch["relative_covariance"]<2e-8
    return {"full_Gaia_total":data["source_total_rows"],
            "quality":fits["quality"]["n"],
            "R69_source_parity_max_error":float(max_err),
            "R69_192_patch_cov_relative_error":patch["relative_covariance"],
            "original_data_sha":data["original_source_sha256"],
            "physical_kinematic_transfer":"NOT_ESTABLISHED"}


def online():
    rng=np.random.default_rng(20261119)
    x=rng.normal(size=(135,5))
    acc=OnlineCovariance(5)
    for z in (x[:9],x[9:21],x[21:]):acc.update(z)
    truth=np.cov(x,rowvar=False)
    delta=np.linalg.norm(acc.covariance()-truth)/np.linalg.norm(truth)
    assert delta<1e-13
    return {"synthetic_draws":135,"relative_sample_cov_error":float(delta),
            "actual_CMB_matched_MC_null":"BLOCKED_SOURCE"}


def main():
    src=(R61,NVSS/"NVSS_CONDITIONAL_CARRIERS.npz",R66,R74,R75,GAIA)
    return {"schema":"htt.r79.pre_dag_ten_node_code_physics/1",
            "lane_default":analysis_lane_policy()["mode"],
            "read_only_source_sha256":{str(p):sha(p) for p in src},
            "SQ-RADIO":radio(),
            "SQ-PHOTON_FLUX_AND_LIE_FLUX":photon_and_lie(),
            "SQ-CF4_AND_P1_ANCHOR":cf4_support(),
            "SQ-OPTICAL":optics(),
            "SQ-GAIA":gaia_full(),
            "SQ-CMB_NULL":online(),
            "SQ-FRAME":"proper SO(3) STF and Lie rank tested; physical beta/normal reference not measured",
            "SQ-CROSS_COV":"Schur SPD arithmetic tested; actual cross-probe source C missing",
            "science_claim":"NUMERIC_PREPARATION_CHECKED; no SQ5-10 science gate promoted"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False))
