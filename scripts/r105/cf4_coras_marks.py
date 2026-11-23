"""Evaluate compiled CORAS mean and residual fields on R104 6dFGSv group-heldout marks."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.special import logsumexp
from scripts.r105 import cf4_field_holdout as mark
from scripts.r105 import coras_reduce
from scripts.r105 import coras_flow


def site_geometry():
    from scripts.r103 import cf4_shared_field_holdout as old
    from scripts.r104 import cf4_2mrs_field as field
    s=old.r100.load_sixdf_pv()
    sci,*_=old.r100.old._load_r30_and_bridge()
    z=s["cz_gal"]/old.r100.C
    r,g,*_=sci.background(z,64)
    g0=sci.H0*(-1.5*sci.OM+1/sci.growth_integral(np.array([1.]),64)[0])
    names_sha=hashlib.sha256(("\n".join(s["ids"])+"\n").encode()).hexdigest()
    sites=dict(ids=np.arange(1,len(r)+1),ng=field.to_galactic(field.hp.ang2vec(s["ra"],s["dec"],lonlat=True)),
               radius=r*field.H_LITTLE,catalogue=dict(name="6dFGSv Table 1",id_encoding="one-based source row",
                    ordered_names_sha256=names_sha,table1_sha256=old.r100.sha256(old.r100.SIXDF_PATH)))
    return sites,g/g0,sci,z


def fold_score(summaries, which):
    """Summaries columns = log J_train,f, log J_test,f, log D_test,f; equal priors."""
    factors=np.asarray(summaries)[which]
    logw=factors[:,0]-logsumexp(factors[:,0])
    return dict(logscore=float(logsumexp(logw+factors[:,1])-logsumexp(logw+factors[:,2])),
                effective_training_components=float(np.exp(-logsumexp(2*logw))),
                max_training_weight=float(np.exp(logw.max())))


def score(directory, reference):
    old,s,inc,x,nn_mu,links,_,_,models,nn_sha=mark.source_sample()
    geom,growth,sci,z=site_geometry()
    rec,_,_,first,last=coras_reduce.metadata(directory,geom)
    if rec.get("catalogue")!=geom["catalogue"] or rec.get("nodes")!=["SQ-CF4"]:
        raise ValueError("6dFGSv catalogue binding mismatch")
    seeds=list(range(first,last+1))
    residuals=[f"residual_{i}.tsv" for i in seeds]
    if set(rec["output_sha256"])!=set(residuals)|{"mean.tsv"} or {f.name for f in directory.glob("residual_*.tsv")}!=set(residuals):
        raise ValueError("partial or stale CORAS field draw set")
    ids=geom["ids"]

    def read(name):
        p=directory/name
        if coras_reduce._sha(p)!=rec["output_sha256"][name]:
            raise ValueError(f"field hash mismatch: {name}")
        return coras_reduce.read_radial(p,ids)

    mean=read("mean.tsv")
    mark_y=np.where(inc,s["delta_d"],np.nan)
    sig=s["epsilon_d"]
    offsets=np.array([-300.,-100.,0.,100.,300.])
    ref=json.loads(reference.read_text())
    names=np.asarray(s["ids"])
    folds=[]
    for key,clusters in links.items():
        for fi,(tr,te) in enumerate(old.group_kfold_indices(clusters,n_splits=5,seed=42)):
            fid=hashlib.sha256(("\n".join(sorted(names[te]))+"\n").encode()).hexdigest()
            oldfold=ref["folds"][key]["folds"][fi]
            if fid!=oldfold["sorted_test_id_sha256"] or np.intersect1d(clusters[tr],clusters[te]).size:
                raise ValueError("R105 fold identity mismatch")
            fit=old.fit_probit_with_hessian(x[tr],inc[tr])
            if not fit.converged:
                raise ValueError("selection fit failed")
            b=fit.beta_hat
            folds.append(dict(key=key,f=fi,tr=tr,te=te,a=b[0]+b[1]*x[:,1]+b[3]*x[:,3],
                              b=b[2],existing=oldfold["scores_shared_minus_zero"]["fixed_2mrs"],s=[]))

    def accumulate(mus):
        for f in folds:
            j,d=mark.components(mark_y,mus,sig,f["a"],f["b"],inc)
            tr,te=f["tr"],f["te"]
            f["s"].extend(np.column_stack((j[:,tr].sum(1),j[:,te].sum(1),d[:,te].sum(1))).tolist())

    # First two components are no flow and the reference 2MRS NeuralNet mean.
    accumulate(np.vstack((np.zeros(len(z)),nn_mu[models["fixed_2mrs"]][0])))
    tags=[("zero",0.),("nn",0.)]
    # Keep only per-field/per-fold sufficient statistics between blocks.
    for name in ["mean.tsv",*residuals]:
        v=mean.copy()
        if name!="mean.tsv":
            v+=read(name)
        mus=np.stack([old.r99.finite_shift(sci,z,np.arctanh((u+growth*v)/old.r100.C),"bolometric")/(5*old.r100.MAG)
                      for u in offsets])
        accumulate(mus)
        tags.extend((name,u) for u in offsets)
    name,u=np.array([t[0] for t in tags]),np.array([t[1] for t in tags])
    draw=np.isin(name,residuals)
    choices=dict(zero=name=="zero",nn=name=="nn",coras_mean=(name=="mean.tsv")&(u==0),
                 coras_mean_offset=name=="mean.tsv",coras_draws=draw&(u==0),coras_draws_offset=draw)
    if len(seeds)>=4:
        for half, subset in enumerate(np.array_split(residuals,2)):
            choices[f"coras_half{half+1}_offset"]=np.isin(name,subset)
    result={}
    for f in folds:
        scores={k:fold_score(f["s"],mask) for k,mask in choices.items()}
        row={k:v["logscore"]-scores["zero"]["logscore"] for k,v in scores.items()}
        if abs(row["nn"]-f["existing"])>1e-7:
            raise ValueError("inconsistent R105 matched 2MRS score")
        result.setdefault(f["key"],[]).append(dict(fold=f["f"],shared_minus_zero=row,
                     effective_training_components={k:v["effective_training_components"] for k,v in scores.items()}))
    return dict(schema="htt.r105.6df_coras_field_marks/1",coras_run_sha256=coras_reduce._sha(directory/"run.json"),
                r105_reference_sha256=coras_reduce._sha(reference),nn_sha256=nn_sha,mean_sha256=rec["output_sha256"]["mean.tsv"],
                n_parent=len(z),n_selected=int(inc.sum()),runs_config=rec["config"],catalogue=rec["catalogue"],seed_ids=seeds,
                sum_heldout_shared_minus_zero={k:{m:sum(r["shared_minus_zero"][m] for r in rows) for m in choices}
                                               for k,rows in result.items()}, folds=result,
                scope="Finite equal-weight 2MRS-constrained CORAS residual draws at fixed CF3-calibrated growth and bulk; "
                      "fitted selection per fold. Conditional predictive score, no calibrated p or joint survey error covariance.",
                source_qualification="BLOCKED_INPUT",physical_Pi=None,calibrated_p=None)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    cmds=p.add_subparsers(dest="action",required=True)
    gen=cmds.add_parser("generate")
    for n in ("donor","binary","output"):
        gen.add_argument("--"+n,type=Path,required=True)
    for n,d in (("first",1),("last",8),("radial",24),("ell",4),("fft",16),("threads",1)):
        gen.add_argument("--"+n,type=int,default=d)
    gen.add_argument("--smoothing",type=float,default=15.)
    red=cmds.add_parser("score")
    red.add_argument("--run",type=Path,required=True)
    red.add_argument("--reference",type=Path,required=True)
    red.add_argument("--output",type=Path,required=True)
    args=p.parse_args(argv)
    if args.action=="generate":
        coras_flow.run(args,site_factory=lambda:site_geometry()[0],nodes=("SQ-CF4",))
    else:
        from scripts.r103.manticore_cf4_pv import staged
        value=score(args.run,args.reference)
        with staged(args.output) as f:
            f.write((json.dumps(value,indent=2,allow_nan=False)+"\n").encode())


if __name__=="__main__":
    main()
