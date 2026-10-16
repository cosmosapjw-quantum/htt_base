"""Independent empirical method-sky inventory for previous CF4 35,970 selected-source NPZ.

This original-source-derived NPZ was already sha-verified in publication PR #545.
It is a selected catalogue. Source sky anisotropy is NOT cosmological anisotropy.
"""
from __future__ import annotations
import argparse,hashlib,io,json,zipfile
from pathlib import Path
import numpy as np
from selection_identifiability import fit_profile_nullspace
NAME='source/h03/htt_six_paper_h03/inputs/selected_source_observables.npz'
SHA='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'

def audit_npz_bytes(data:bytes):
    if hashlib.sha256(data).hexdigest()!=SHA:
        raise ValueError('selected original-source NPZ SHA mismatch')
    z=np.load(io.BytesIO(data),allow_pickle=False)
    try:
        ids=z['group_id'];n=z['n_J2000'];families=z['method_family']
        if len(ids)!=35970 or len(n)!=35970 or n.shape!=(35970,3) or len(families)!=35970:
            raise ValueError('source support mismatch')
        if len(np.unique(ids))!=len(ids):raise ValueError('not unique CF4 group IDs')
        if not np.allclose(np.sum(n*n,axis=1),1,rtol=0,atol=4e-12):raise ValueError('not unit sky')
        lab=sorted(np.unique(families).tolist())
        if len(lab)<2:raise ValueError('unexpected one-method source')
        Z=np.stack([(families==v).astype(float) for v in lab],axis=1)
        nx,ny,nz=n.T
        X=np.stack([nx,ny,nz,nx**2-nz**2,ny**2-nz**2,2*nx*ny,2*nx*nz,2*ny*nz],axis=1)
        res=fit_profile_nullspace(Z,X)
        by={}
        for k in lab:
            mask=families==k;v=n[mask]
            by[k]={'n_groups':int(mask.sum()),'sky_mean_n_J2000':np.mean(v,axis=0).tolist(),
                   'mean_dipole_norm':float(np.linalg.norm(v.mean(axis=0))),
                   'mean_STF2_shape':X[mask,3:].mean(axis=0).tolist(),
                   'fraction_of_selected_source':float(mask.mean())}
        res.update({'selected_source_count':len(ids),'source_npz_sha256':SHA,
          'schema':'htt.CF4_35970_source_method_sky_v2/1','group_1PGC_unique':True,
          'source_membership':'ONE_SELECTED_COHORT_NOT_PARENT_INCLUSION_PROBABILITY',
          'methods':by,'global_sky_dipole_mean':np.mean(n,axis=0).tolist(),
          'source_conditioned_anisotropy_observation':'ACTUAL_CF4_SELECTED_SKY_METHOD_COUNTS_NOT_GEOMETRIC_KINEMATICS',
          'claim_admission':'SAMPLE_SUPPORT_AUDIT_ONLY; H02 SELECTION HOLD'})
        return res
    finally:z.close()


def main():
    p=argparse.ArgumentParser()
    grp=p.add_mutually_exclusive_group(required=True)
    grp.add_argument('--archive',type=Path)
    grp.add_argument('--npz',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.archive:
        with zipfile.ZipFile(a.archive) as z:data=z.read(NAME)
    else:data=a.npz.read_bytes()
    out=audit_npz_bytes(data)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'source_count':out['selected_source_count'],'rank':out['rank_angular_after_calibration'],'method_counts':{k:v['n_groups'] for k,v in out['methods'].items()},'status':out['claim_admission']},ensure_ascii=False))
if __name__=='__main__':main()
