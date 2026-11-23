"""R105 exact finite-mixture projection for one offset plus one 2MRS velocity mode."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.special import log_ndtr, logsumexp, ndtr, ndtri


def components(y, mu, sig, a, b, keep):
    """Return per-field, per-row log joint and log inclusion-pattern factors."""
    mu = np.asarray(mu, float)
    sig = np.asarray(sig, float)
    keep = np.asarray(keep)
    y = np.asarray(y, float)
    a = np.asarray(a, float)
    if (mu.ndim != 2 or mu.shape[1] != len(y) or keep.dtype != bool or
            keep.shape != y.shape or sig.shape != y.shape or a.shape != y.shape or
            not all(np.isfinite(x).all() for x in (mu,sig,a,b,y[keep])) or np.any(sig <= 0)):
        raise ValueError("invalid Gaussian/probit field data")
    t = (a + b*mu)/np.hypot(1.,b*sig)
    logpattern = log_ndtr(np.where(keep,t,-t))
    logjoint = logpattern.copy()
    logjoint[:,keep] = (log_ndtr(a[keep]+b*y[keep]) - np.log(sig[keep])
                        - .5*np.log(2.*np.pi) - .5*((y[keep]-mu[:,keep])/sig[keep])**2)
    return logjoint,logpattern


def predictive(joint, pattern, train, components_idx):
    """Uniform prior within subset; normalized log score conditional on all test indicators."""
    j = joint[components_idx]
    d = pattern[components_idx]
    logtrain = j[:,train].sum(1)
    logtest = j[:,~train].sum(1)
    loginc = d[:,~train].sum(1)
    w = logtrain-logsumexp(logtrain)
    w_pattern = w + loginc
    return dict(shared=float(logsumexp(w+logtest)-logsumexp(w_pattern)),
                fresh=float(logsumexp(logtest)-logsumexp(loginc)),
                train_logweights=w, prediction_logweights=w_pattern-logsumexp(w_pattern))


def conditional_pit(y, mu, sig, a, b, logweights, order=32):
    """Marginal PIT for selected test rows; integrate in normal-CDF coordinates."""
    t = ndtr((y-mu)/sig)
    q = ndtr((a+b*mu)/np.hypot(1.,b*sig))
    if not (np.all(q>0.) and np.isfinite(logweights).all()):
        raise ValueError("undefined selected PIT")
    nodes, wt = np.polynomial.legendre.leggauss(order)
    cumul = np.zeros_like(t)
    for node,w in zip(nodes,wt):
        # At t=0 the integral vanishes exactly. Avoid 0*(-inf) for b=0.
        u = np.maximum(.5*t*(node+1.),np.finfo(float).tiny)
        cumul += .5*w*ndtr(a + b*(mu + sig*ndtri(u)))
    return np.exp(logweights) @ (t*cumul/q)


def overlap(labels1, labels2):
    ng = np.bincount(5*labels1+labels2,minlength=25).reshape(5,5)
    i,j = linear_sum_assignment(-ng)
    return dict(cross_tab_pgc_rows_pgc1_columns=ng.tolist(),same_number_rows=int(ng.trace()),
                maximum_same_after_relabelling=int(ng[i,j].sum()),n_total=len(labels1))


def named_scores():
    alpha = np.repeat([0.,.5,1.,1.5,2.],5)
    u = np.tile([-300.,-100.,0.,100.,300.],5)
    return alpha,u,{"zero":(alpha==0)&(u==0), "offset_only":alpha==0, "fixed_2mrs":(alpha==1)&(u==0),
                    "fixed_2mrs_offset":alpha==1, "trained_scale_only":u==0,
                    "trained_scale_offset":np.ones(len(u),bool)}


def source_sample():
    from scripts.r104 import cf4_2mrs_field as r104
    from scripts.r103 import cf4_shared_field_holdout as old
    r100 = old.r100
    t2, s = r100.load_cf4_table2(), r100.load_sixdf_pv()
    ref = json.loads((r100.OUT_DIR/"CF4_UPSTREAM_KBAND_RESULTS.json").read_text())
    for name,p in (("cf4_table2",t2["path"]),("sixdf_pv_table1",r100.SIXDF_PATH)):
        if r100.sha256(p)!=ref["inputs"][name]["sha256"]:
            raise ValueError(f"R100 identity changed: {name}")
    m=old.sixdf_match_ambiguity_policies(t2,s,arcsec=15.,dv_kms=500.)
    inc=m["policies"]["unique_only_r101"]["included"]
    ng=r104.to_galactic(r104.hp.ang2vec(s["ra"],s["dec"],lonlat=True))
    sci,*_=r100.old._load_r30_and_bridge()
    z=s["cz_gal"]/r100.C
    r,g,*_=sci.background(z,64)
    g0 = sci.background(np.array([0.]),64)[1][0]
    v,ok=r104.interpolate(r104.load_field(),ng*(r*r104.H_LITTLE)[:,None])
    if not np.all(ok):
        raise ValueError("R104 all-parent 2MRS interpolation support changed")
    vlos=np.sum(v*ng,axis=1)*(g/g0)
    alpha,u,models=named_scores()
    mu=np.array([old.r99.finite_shift(sci,z,np.arctanh((a*vlos+s0)/r100.C),"bolometric")/(5.*r100.MAG)
                 for a,s0 in zip(alpha,u)])
    x=np.column_stack((np.ones(len(z)),s["cz_gal"]/1.e4-1.1,s["delta_d"],s["is_grouped"]))
    closest=m["closest_table2_indices"]
    links={k:old.build_group_clusters(s["groupid_raw"],secondary_keys=np.where(closest>=0,t2[k][np.maximum(closest,0)],-1))
           for k in ("pgc","pgc1")}
    return old,s,inc,x,mu,links,alpha,u,models,r104.FIELD_SHA


def run():
    old,s,inc,x,mu,links,alpha,u,models,field_sha=source_sample()
    doc=old.DOC/"R104_DATA_SOLVER_CONTINUATION_20261124"/"CF4_2MRS_FIELD.json"
    baseline=json.loads(doc.read_text())["sixdf_holdout"]["link_policies"]
    y=np.where(inc,s["delta_d"],np.nan)
    sig=s["epsilon_d"]
    definitions={"before":"offset_only","after":"fixed_2mrs_offset"}
    report,labels={},{}
    names=np.array(s["ids"])
    if len(names)!=len(set(names)):
        raise ValueError("6dFGSv source IDs not unique")
    for key,clusters in links.items():
        membership=np.full(len(y),-1)
        rows=[]
        pits=[]
        max_replay=0.
        max_quad=0.
        for f,(tr,te) in enumerate(old.group_kfold_indices(clusters,n_splits=5,seed=42)):
            if (membership[te]!=-1).any() or np.intersect1d(clusters[tr],clusters[te]).size:
                raise ValueError("invalid fold partition")
            membership[te]=f
            fit=old.fit_probit_with_hessian(x[tr],inc[tr])
            if not fit.converged:
                raise ValueError("selection fit failed")
            b=fit.beta_hat
            intercept=b[0]+b[1]*x[:,1]+b[3]*x[:,3]
            j,d=components(y,mu,sig,intercept,b[2],inc)
            mask=np.ones(len(y),bool); mask[te]=False
            stats={k:predictive(j,d,mask,v) for k,v in models.items()}
            score={k:round(v["shared"]-stats["zero"]["shared"],12) for k,v in stats.items()}
            prev=baseline[key]["folds"][f]
            for lab,k in definitions.items():
                for prior in ("fresh","shared"):
                    delta=stats[k][prior]-stats["zero"][prior]
                    max_replay=max(max_replay,abs(delta-prev[f"{lab}_{prior}_minus_zero"]))
            max_replay=max(max_replay,abs(score["fixed_2mrs"]-prev["field_only_fresh_minus_zero"]))
            q=te[inc[te]]
            wo=stats["trained_scale_offset"]
            vals=conditional_pit(y[q],mu[:,q],sig[q],intercept[q],b[2],wo["prediction_logweights"],32)
            subset=np.arange(0,len(q),17)
            trial=conditional_pit(y[q][subset],mu[:,q][:,subset],sig[q][subset],intercept[q][subset],b[2],
                                  wo["prediction_logweights"],64)
            max_quad=max(max_quad,float(np.max(abs(vals[subset]-trial))))
            pits.extend(vals.tolist())
            weights=np.exp(wo["train_logweights"])
            rows.append(dict(fold=f,n_test=int(len(te)),n_selected=len(q),
                             sorted_test_id_sha256=hashlib.sha256(("\n".join(sorted(names[te]))+"\n").encode()).hexdigest(),
                             scores_shared_minus_zero=score,mean_alpha_train=float(alpha@weights),
                             mean_offset_kms_train=float(u@weights),alpha_marginal_train=weights.reshape(5,5).sum(1).tolist()))
        if (membership<0).any() or max_replay>1e-7:
            raise ValueError(f"R104 replay or coverage mismatch for {key}: {max_replay}")
        if max_quad>1.e-4 or np.min(pits)<-1.e-4 or np.max(pits)>1.+1.e-4:
            raise ValueError(f"PIT quadrature accuracy {key}: {max_quad}")
        pp=np.asarray(pits)
        report[key]=dict(folds=rows,r104_max_absolute_score_replay_error=max_replay, n_parent=len(y),n_matched=int(inc.sum()),
                         scores_shared_minus_zero={k:sum(r["scores_shared_minus_zero"][k] for r in rows) for k in models},
                         pit_32_vs_64_subsample_max_error=max_quad,
                         marginal_predictive_coverage={str(level):float(np.mean((pp>=(1.-level)/2)&(pp<=(1.+level)/2)))
                                                       for level in (.50,.80,.95)},pit_mean=float(pp.mean()))
        labels[key]=membership
    return dict(schema="htt.r105.cf4_field_holdout/1", r104_artifact_sha256=hashlib.sha256(doc.read_bytes()).hexdigest(),
                field_sha256=field_sha, mean_transfer="R104 individual cz; outward bolometric velocity; g(z)/g(0)",
                priors=dict(alpha_values=sorted(set(alpha)),offset_kms=sorted(set(u)),weights="uniform on each declared model"),
                folds=report, linkage_fold_membership=overlap(labels["pgc"],labels["pgc1"]),
                scope="source-conditioned heldout selected-mark density; descriptive marginal coverage",
                calibrated_p=None, physical_Pi=None, physical_GF=None, source_qualification="BLOCKED_INPUT")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path)
    args=p.parse_args()
    payload=json.dumps(run(),indent=2,allow_nan=False)+"\n"
    if args.output:
        args.output.write_text(payload)
    else:
        print(payload,end="")
