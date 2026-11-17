#!/usr/bin/env python3
"""Transport the actual published CF4 redshift chart in the fixed R63 mean.

This is a deterministic, first-order mean correction with the SAME catalogue,
window operator and covariance. It does not replace the catalogue redshifts,
invent an observer likelihood, reconstruct distance photometry, or certify a
nonlinear boost. The existing R63 separation information is unchanged because
the known additive offset is common to both competing mean families.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy import linalg, stats

PROGRAM="docs/research_program/observational_publication_20261015"
FOLDER=PROGRAM+"/R63_LOCAL_BOOST_GLOBAL_TILT_20261117"
C=299792.458


def run(root,output):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output.exists():
        raise ValueError("refusing to overwrite chart transport")
    sys.path[:0]=[str(root/"scripts/r58"),str(root/"scripts/r63"),str(root/"htt"),str(root/"htt/src")]
    import run_r58_owned_tensor as old
    import r63_cf4_q_check as qcheck
    from htt.htt.infer import r63_frame_history as fh
    de,_,cf,mt=old.import_modules(root,None)
    diagnostic=qcheck.main(root)
    data=cf.load();cat=data["cat"]
    n,z=cat["n_J2000"],cat["z_CMB"]
    raw=gzip.decompress((root/"workdir/raw/cf4_full/table4.dat.gz").read_bytes())
    if hashlib.sha256(raw).hexdigest()!="b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94":
        raise ValueError("published Table4 identity changed")
    records={int(s[:7]):s for s in raw.splitlines() if s.strip()}
    selected=[records[int(i)] for i in cat["group_id"]]
    vh=np.array([float(s[27:32]) for s in selected])
    v3k=np.array([float(s[39:44]) for s in selected])
    qactual=C*np.log1p((v3k-vh)/(C+vh))
    reference=np.asarray(diagnostic["additive_fit"]["vector"]["xyz_icrs_km_s"])
    qideal=n@reference
    deltaq=qactual-qideal
    # An explicit enclosing error body under nearest-integer tabulation;
    # this is a deterministic sensitivity, not a probability law.
    eps_q=.5*C*(1/(C+v3k-.5)+1/(C+vh-.5))
    lr=de.log_distance_ratio(cat["dmzp"],z,cf.OMEGA_M)
    g=lr["g_per_km_s"]
    tau2=de.log_noise_variance(cat["e_dmzp"],g,cf.SIGMA_STAR)
    with np.load(cf.OUT_DIR/"R54_L04_SURVEY_LABELS.npz",allow_pickle=False) as lab:
        if not np.array_equal(lab["group_id"],cat["group_id"]):raise ValueError("survey order")
        survey=dict(labels=lab["survey"].copy(),raw_labels=lab["survey_unpooled"].copy(),min_side=100)
    ops,_=cf.build_operators(cat,data["a_raw"],tau2,survey=survey)
    bg=fh.background_factors(z,cf.OMEGA_M,1e-4)
    coeffs={"free_history":g+2/C,"rad_constant":bg["g_per_km_s"]+2/C,"rad_tied":bg["g_per_km_s"]+2/C}
    carrier=root/FOLDER/"RESULTS/OBSERVED/FRAME_HISTORY_CARRIERS.npz"
    if hashlib.sha256(carrier.read_bytes()).hexdigest()!="c79a877c82621caa2af5ce14bb7f9e2d30a582735a557d9601ebbb25d25095fc":
        raise ValueError("R63 first observed carrier changed")
    saved=np.load(carrier,allow_pickle=False)
    rows=saved["row_indices32"]
    models={}
    for name in old.VARIANTS:
        op=ops[name][rows];cov=saved[name+"__cov32"]
        chol=linalg.cholesky(cov,lower=True)
        y=saved[name+"__y32"]
        for degree in (2,3):
            for kind in coeffs:
                key=name+f"__J{degree}__"+kind
                x=saved[key+"__response"]
                oldh=saved[key+"__estimate"]
                var=saved[key+"__covariance"]
                offset=op@(coeffs[kind]*deltaq)
                offsetw=linalg.solve_triangular(chol,offset,lower=True)
                xw=saved[key+"__likelihood_factor"]
                # Reconstruct the linear estimator from its scaled SVD, avoiding
                # catastrophic cancellation in covariance @ Xw.T for weak W.
                scale=saved[key+"__parameter_scale"]
                left,sv,right=linalg.svd(xw*scale,full_matrices=False)
                gain=((scale[:,None]*right.T)/sv)@left.T
                newh=oldh-gain@offsetw
                yw=saved[key+"__likelihood_offset"]-offsetw
                resid=yw-xw@newh
                target=slice(3,6) if kind=="free_history" else slice(0,3)
                h,v=newh[target],var[target,target]
                wald=float(h@linalg.solve(v,h,assume_a="pos"))
                # Independent fit on exactly the same shifted finite experiment.
                yy=y if kind=="free_history" else y-saved[name+"__rad_background_offset32"]
                direct=mt.fit_linear(yy-offset,cov,x,saved[key+"__parameter_scale"])
                err=float(np.max(abs(newh-direct["estimate"])/saved[key+"__parameter_scale"]))
                if err>2e-7:raise ValueError("affine correction failed direct GLS parity")
                # Only the declared target support under bounded q-rounding.
                score_op=linalg.solve_triangular(chol,op,lower=True)
                raw_gain=gain[target]@score_op
                raw_gain*=coeffs[kind][None,:]
                support=np.sum(abs(raw_gain)*eps_q[None,:],axis=1)
                corner=eps_q*np.sign(raw_gain[0])
                if abs(raw_gain[0]@corner-support[0])>1e-10*max(support[0],1.):
                    raise ValueError("rounding box support witness failed")
                models[key]={"kind":kind,"degree":degree,"operator":name,
                    "target":"W_km_s" if kind=="free_history" else "U_or_bulk_km_s",
                    "old_target":oldh[target].tolist(),"corrected_target":h.tolist(),
                    "target_shift":(h-oldh[target]).tolist(),"target_covariance":v.tolist(),
                    "zero_wald":wald,"zero_nominal_p":float(stats.chi2.sf(wald,3)),
                    "residual_chi2":float(resid@resid),"dof":len(y)-x.shape[1],
                    "affine_GLS_scaled_parity_error":err,
                    "rounding_box_target_support_km_s":support.tolist(),
                    "source_offset_whitened_norm":float(linalg.norm(offsetw)),
                    "geometry_unchanged":True}
    output.parent.mkdir(parents=True,exist_ok=True)
    result={"schema":"htt.r63.catalogue_chart_transport/1",
        "script_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_carrier_sha256":hashlib.sha256(carrier.read_bytes()).hexdigest(),
        "q_diagnostic":diagnostic,
        "response_offset":"O_m[(A+1)*(q_published-n.a)/c]; subtract from y for the declared fixed logarithmic-reference mean",
        "reference":"a is a deterministic least-squares representation of published additive correction; not an independent physical observer estimate",
        "physical_status":"conditional first-order optical/source mean; complete distance p, finite boost and method aggregation still unresolved",
        "same_experiment":"all source rows, quoted-z operators, covariance and design fixed; known offset is propagated, not a new redshift catalogue",
        "rounding_body":"Under +/-0.5 km/s independent coordinate intervals for continuous Vh and V3k, q error bounded by derivative supremum; fixed reference a, no stochastic rounding law; coordinate support only, not simultaneous attainment",
        "separation_power_bound":"unchanged: common additive source correction cancels from difference of mean families",
        "models":models}
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"models":len(models),"max_GLS_parity_error":max(r["affine_GLS_scaled_parity_error"] for r in models.values()),
        "max_U_shift_km_s":max(np.linalg.norm(r["target_shift"]) for r in models.values() if r["kind"]=="rad_tied"),
        "W_zero_J2_max_p":max(r["zero_nominal_p"] for r in models.values() if r["kind"]=="free_history" and r["degree"]==2)}))


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",default=".")
    parser.add_argument("--output",required=True)
    args=parser.parse_args();run(args.root,args.output)
