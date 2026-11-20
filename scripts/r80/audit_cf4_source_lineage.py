"""R80: bounded real CF4 selected-group source binding and mask morphology.

Requires restored original local CF4 table3/table4 and frozen selected 35,970
source carrier. Does not infer real physical shear or change R78 states.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy import units as u

from htt.obsstat.catalogs.cf4_grouped_observations import (
    load_grouped_observations, METHODS)
from htt.obsstat.pre_dag_fast import (
    hemisphere_moments, last_backend_receipt)

ROOT=Path("docs/research_program/observational_publication_20261015")
RAW=Path("/mnt/extdrive/workdir/raw/cf4_full")
SELECT=Path("docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz")
OP=ROOT/"OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/audit_backup/derived/A_RAW_36x35970.npz"
R36=ROOT/"OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/RESULT.json"
OUTPUT=ROOT/"R80_SQ_CF4_SOURCE_BINDING_20261120/RESULT.json"
C=299792.458

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()

def to_builtin(x):
    if isinstance(x,np.generic):return x.item()
    raise TypeError(f"cannot serialize {type(x)}")

def masked_diagnostics(n,axis,s=0.03):
    fast=hemisphere_moments(n,axis)
    receipt=last_backend_receipt()
    slow=hemisphere_moments(n,axis,native_lib=None)
    for key in ("weights","means","second","counts"):
        np.testing.assert_allclose(fast[key],slow[key],atol=1e-12,rtol=2e-12)
    delta=fast["second"][1]-fast["second"][0]
    assert abs(np.trace(delta))<2e-12
    evals,U=np.linalg.eigh(delta)
    kernel=U@np.diag([-s,0.,s])@U.T
    assert abs(np.trace(kernel))<1e-13 and np.linalg.norm(kernel@U[:,1])<1e-13
    shear_leak=float(np.einsum("ij,ij",kernel,delta))
    max_leak=float(s*(evals[2]-evals[0]))
    assert abs(shear_leak-max_leak)<3e-13
    return {"n":int(len(n)),
       "hemisphere_minus_plus_counts":fast["counts"].astype(int).tolist(),
       "weighted_direction_mean_difference":(fast["means"][1]-fast["means"][0]).tolist(),
       "selection_second_moment_eigenvalues":evals.tolist(),
       "typeV_jtotal0_chi0_synthetic_eigen_amplitude":float(s),
       "sharp_even_shear_to_hemispherical_mean_bound":max_leak,
       "explicit_matched_bound_saturation":shear_leak,
       "backend_actual":{"used":receipt.get("used"),"certified":receipt.get("source_certified"),"n_rows":receipt.get("n_rows")},
       "interpretation":"exact unweighted source-sky response; synthetic Type V template not measured shear or velocity"}

def main():
    pins=json.loads(R36.read_text())
    sources=[RAW/"table3.dat",RAW/"table4.dat",RAW/"ReadMe",SELECT,OP]
    for x in sources:
        if not x.is_file():raise FileNotFoundError(f"pinned original unavailable: {x}")
    source_hashes={str(p):sha(p) for p in sources}
    assert source_hashes[str(RAW/"table4.dat")]=="b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94"
    assert source_hashes[str(SELECT)]==pins["source_sha256"]
    assert source_hashes[str(OP)]==pins["artifact_sha256"]
    raw=load_grouped_observations(RAW/"table3.dat",RAW/"table4.dat",RAW/"ReadMe")
    assert len(raw.group_id)==38053
    with np.load(SELECT,allow_pickle=False) as select, np.load(OP,allow_pickle=False) as op:
        ids=select["group_id"]
        assert len(ids)==35970 and np.all(np.diff(ids)>0)
        assert np.array_equal(ids,op["group_id"])
        ix=np.searchsorted(raw.group_id,ids)
        if np.any(ix>=len(raw.group_id)) or not np.array_equal(raw.group_id[ix],ids):
            raise AssertionError("R54/R58 selected groups are not a subset of original CF4")
        dm_err=float(np.max(abs(select["dmzp"]-raw.modulus[ix])))
        e_err=float(np.max(abs(select["e_dmzp"]-raw.modulus_error[ix])))
        if max(dm_err,e_err)!=0:raise AssertionError("CF4 modulus or uncertainty mismatched")
        n=select["n_J2000"]
        dots=np.einsum("ni,ni->n",n,raw.direction[ix])
        angles=2*np.arcsin(np.clip(np.linalg.norm(n-raw.direction[ix],axis=1)/2,0,1))*180/np.pi*3600
        assert np.max(angles)<.02
        labels=select["method_family"]
        selected_z=select["z_CMB"]
        selected_methods=list(map(str,np.unique(labels)))
        assert set(selected_methods)=={"FP","TF","SN","OTHER"}
        operator_checksum=hashlib.sha256(np.ascontiguousarray(op["A_raw"]).tobytes()).hexdigest()
        assert op["A_raw"].shape==(36,35970)
    # Table4 published V3k is an integer. Avoid mixing heliocentric Vh and CMB V3k.
    table4_lines={int(s[:7]):s for s in (RAW/"table4.dat").read_text().splitlines() if s.strip()}
    assert len(table4_lines)==38053
    v3k=np.asarray([float(table4_lines[int(g)][39:44]) for g in ids])
    redshift_err=float(np.max(abs(v3k/C-selected_z)))
    assert redshift_err<1e-12, redshift_err
    selected_radius=np.asarray([float(table4_lines[int(g)][21:26]) for g in ids])
    all_radii=np.asarray([float(table4_lines[int(g)][21:26]) for g in raw.group_id])
    assert np.all(selected_radius>0) and np.all(all_radii>0)
    # Method information table3 is a presence indicator; selected method
    # is a categorical assignment from historical source estimand, not
    # automatically identical to one table3 presence flag.
    selected_presence=raw.method_presence[ix]
    presence_total=selected_presence.sum(axis=1)
    zero_counts={k:int(np.sum((labels==k)&(presence_total==0))) for k in selected_methods}
    positive_counts={k:int(np.sum((labels==k)&(presence_total>1))) for k in selected_methods}
    method_counts={k:int(np.sum(labels==k)) for k in selected_methods}
    assert sum(method_counts.values())==35970
    assert sum(zero_counts.values())==int(np.sum(presence_total==0))
    # CMB dipole axis is in Galactic coordinates, all source vectors in J2000.
    icrs=SkyCoord(l=264.021*u.deg,b=48.253*u.deg,frame="galactic").icrs
    axis=np.asarray([np.cos(icrs.dec.rad)*np.cos(icrs.ra.rad),
                     np.cos(icrs.dec.rad)*np.sin(icrs.ra.rad),
                     np.sin(icrs.dec.rad)])
    assert abs(np.linalg.norm(axis)-1)<1e-14
    selected_40_400=(selected_radius>=40)&(selected_radius<400)
    raw_40_400=(all_radii>=40)&(all_radii<400)
    diag={
        "full_table4_40_400":masked_diagnostics(raw.direction[raw_40_400],axis),
        "selected_35970_all_radii":masked_diagnostics(n,axis),
        "selected_40_400":masked_diagnostics(n[selected_40_400],axis)}
    for k in selected_methods:
        mk=(labels==k)&selected_40_400
        if int(np.sum(mk))>=100:
            diag["selected_"+k+"_40_400"]=masked_diagnostics(n[mk],axis)
    # Explicit reproducible heldout five partitions of selected source IDs;
    # compare geometry only, not independent cosmic likelihood coverage.
    heldout={}
    for fold in range(5):
        mk=selected_40_400&(ids%5==fold)
        if np.sum(mk)>100:
            heldout[f"id_mod5_{fold}"]=masked_diagnostics(n[mk],axis)
    aligned_selected=np.isin(raw.group_id,ids,assume_unique=True)
    assert np.sum(aligned_selected)==35970
    missing_ids=raw.group_id[~aligned_selected]
    out={
       "schema":"htt.r80.sq_cf4_source_lineage_mask/1",
       "state":"SOURCE_GROUP_ID_AND_GEOMETRY_QUALIFIED; PV_CALIBRATION_SELECTION_COVARIANCE_UNRESOLVED",
       "source_sha256":source_hashes,
       "source_frames":{"group":"CDS CF4 table3 and table4 J2000 1PGC group identity",
                        "selected":"R54/R58 selected J2000 source vectors and redshift CMB V3k/c",
                        "cmb_axis":"(l,b)=(264.021,48.253) Galactic converted by astropy to ICRS J2000"},
       "original_all_group_count":len(raw.group_id),"exact_selected_group_count":len(ids),
       "excluded_group_count":len(missing_ids),
       "excluded_group_ids_sha256":hashlib.sha256(np.ascontiguousarray(missing_ids,dtype="<i8").tobytes()).hexdigest(),
       "selected_group_ids_sha256":hashlib.sha256(np.ascontiguousarray(ids,dtype="<i8").tobytes()).hexdigest(),
       "original_R36_A_RAW_36x35970_bytes_sha256":source_hashes[str(OP)],
       "operator_raw_matrix_sha256":operator_checksum,
       "exact_selected_modulus_max_abs_error":dm_err,
       "exact_selected_modulus_uncertainty_max_abs_error":e_err,
       "selected_v3k_c_to_z_CMB_max_abs_error":redshift_err,
       "selected_J2000_direction_p95_arcsec":float(np.quantile(angles,.95)),
       "selected_J2000_direction_max_arcsec":float(np.max(angles)),
       "selected_method_family_count":method_counts,
       "table3_method_presence_metadata_names":list(METHODS),
       "table3_method_presence_selected_counts":dict(zip(METHODS,map(int,selected_presence.sum(axis=0)))),
       "selected_methods_with_zero_table3_method_presence":zero_counts,
       "selected_methods_with_multi_table3_method_presence":positive_counts,
       "selected_group_zero_method_presence_count":int(np.sum(presence_total==0)),
       "selected_group_multi_method_presence_count":int(np.sum(presence_total>1)),
       "angular_mask_diagnostics":diag,
       "heldout_by_group_id_modulo_five_GEOMETRY_ONLY":heldout,
       "scientific_nonclaims":[
           "R77 full-raw-table4 40-400 mask is not the R61 35970-group same-source likelihood",
           "The source-selected method_family is not a one-to-one translation of raw table3 positive method flags",
           "The actual R54/R58 36x35970 and R61 32D covariance is not a measured full source-level PV/selection covariance",
           "The synthetic Type V STF shear amplitude and hemisphere leakage bound are geometric responses, not cosmological shear or acceleration detection",
           "SQ-CF4 full source qualification remains unresolved: cross-method zero-point and correlated PV/selection response must be physically modelled"] }
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(out,ensure_ascii=False,indent=2,default=to_builtin)+"\n")
    print(json.dumps({"selected":len(ids),"excluded":len(missing_ids),
        "max_arcsec":out["selected_J2000_direction_max_arcsec"],
        "selected_40_400":int(np.sum(selected_40_400)),
        "mask_leakage_selected":diag["selected_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"],
        "mask_leakage_full":diag["full_table4_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"],
        "zero_presence":out["selected_group_zero_method_presence_count"],
        "used_backend":diag["selected_40_400"]["backend_actual"]},ensure_ascii=False))

if __name__=="__main__":
    main()
