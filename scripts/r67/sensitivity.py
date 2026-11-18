"""Exploratory radial-nuisance and outlier sensitivity on the same CF4 matched groups."""
from pathlib import Path
import argparse,json
import numpy as np
from scripts.r67.fusion import read_cf4_groups,stf_features,score_model


def run(root:Path,out:Path,reps=2048,seed=20261118):
    D=read_cf4_groups(root)
    dist=D['distance_mpc']
    m1,m2=D['mu']['FP'],D['mu']['TF']
    e1,e2=D['err']['FP'],D['err']['TF']
    sel=np.isfinite(m1)&np.isfinite(m2)&np.isfinite(e1)&np.isfinite(e2)&(e1>0)&(e2>0)&(dist>0)
    d,ns,ids=dist[sel],D['n'][sel],D['id'][sel]
    y=m1[sel]-m2[sel]
    e=np.hypot(e1[sel],e2[sel])
    lr=np.log(d);u=(lr-lr.mean())/lr.std()
    ang=np.column_stack([ns,stf_features(ns)])
    result=[]
    for order in [0,1,2,3]:
        X0=np.column_stack([u**i for i in range(order+1)])
        r=score_model(y/e,X0/e[:,None],ang/e[:,None],ids,reps,seed+order)
        result.append({'radial_polynomial_degree':order,'group_count':int(len(y)),
                'wild_group_p':r['wild_group_p_exploratory'],
                'naive_chisq_p':r['naive_chisq_reference_p'],
                'delta_working':r['delta_chisq_working'],
                'rank_all':r['rank_all']})
    # No censoring in primary. Refit as a diagnostic after removing large
    # radial-only residuals, checking whether primary depends on obvious outliers.
    X0=np.column_stack([np.ones(len(u)),u,u*u])
    beta=np.linalg.lstsq(X0/e[:,None],y/e,rcond=None)[0]
    resid=np.abs((y-X0@beta)/e)
    kept=resid<=3.
    r=score_model(y[kept]/e[kept],X0[kept]/e[kept,None],
        ang[kept]/e[kept,None],ids[kept],reps,seed+8)
    obj={'data_source':D['source_sha256'],'primary_method':'FP-TF',
         'radial_polynomial_variations':result,
         'exploratory_large_standardized_residual_filter':{'rule':'|radial-only residual/error|<=3','retained':int(kept.sum()),'excluded':int((~kept).sum()),'wild_group_p':r['wild_group_p_exploratory'],'warning':'Posthoc sensitivity, never replace primary results'},
         'bootstrap':'Group-rademacher, upstream correlation and selection uncalibrated',
         'status':'exploratory robustness only'}
    out.mkdir(parents=True,exist_ok=True)
    (out/'RADIAL_ROBUSTNESS.json').write_text(json.dumps(obj,indent=2)+'\n')
    print(json.dumps(obj,indent=2))
    return obj
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument('--cf4',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    ap.add_argument('--out',type=Path,default=Path('docs/research_program/observational_publication_20261015/R67_SEVEN_AXIS_FUSION_20261118/RESULTS'))
    a=ap.parse_args()
    run(a.cf4,a.out)
