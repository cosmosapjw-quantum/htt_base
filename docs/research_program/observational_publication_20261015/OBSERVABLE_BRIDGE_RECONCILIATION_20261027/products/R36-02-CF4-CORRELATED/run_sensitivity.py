"""Refit fixed-weight H03 operators on declared subsets for PV sensitivity."""
from __future__ import annotations

import json
from pathlib import Path
import time

import numpy as np
from scipy.linalg import qr, solve_triangular

import run_correlated as r

def fit_operator(mask,source,sigma):
    n=source['n_J2000'];z=source['z_CMB']
    d=10**((source['dmzp']-25)/5)
    basis=np.array([[[1,0,0],[0,-1,0],[0,0,0]],
                    [[1,0,0],[0,1,0],[0,0,-2]],
                    [[0,1,0],[1,0,0],[0,0,0]],
                    [[0,0,1],[0,0,0],[1,0,0]],
                    [[0,0,0],[0,0,1],[0,1,0]]],float)
    basis/=np.array([np.sqrt(2),np.sqrt(6),np.sqrt(2),np.sqrt(2),np.sqrt(2)])[:,None,None]
    X=d[:,None]*np.column_stack((np.ones(len(z)),n,
        np.einsum('ni,aij,nj->na',n,basis,n)))
    blocks=[];identity=[]
    for centre in (.025,.04,.06,.08):
        w=np.exp(-.5*((z[mask]-centre)/.012)**2)/sigma[mask]**2
        sw=np.sqrt(w);q,R=qr(sw[:,None]*X[mask],mode='economic',check_finite=False)
        a=solve_triangular(R,q.T,check_finite=False)*sw
        full=np.zeros((9,len(z)));full[:,mask]=a
        blocks.append(full);identity.append(float(np.max(abs(full@X-np.eye(9)))))
    return np.concatenate(blocks),max(identity)

def main():
    t=time.monotonic()
    with np.load(r.SOURCE,allow_pickle=False) as z:
        source={k:z[k] for k in ['z_CMB','dmzp','e_dmzp','n_J2000','method_family','group_id']}
    with np.load(r.OPERATOR,allow_pickle=False) as z:
        sigma=z['sigma'];ref=z['A_raw']
    chi,g,*_=r.old.background(source['z_CMB'],64)
    x=chi[:,None]*source['n_J2000'];n=source['n_J2000']
    amp,_=r.old.power_amplitude()
    target,maps=r.quadrature_inventory([('C',53,32)])
    with np.load(r.EXTERNAL/'STAGE_C.npz') as z:
        baseline=z['total'][:36,:36]
    masks={
        'north_ICRS_nz_nonnegative':n[:,2]>=0,
        'south_ICRS_nz_negative':n[:,2]<0,
        'exclude_FP':source['method_family']!='FP',
        'exclude_TF':source['method_family']!='TF',
    }
    results={};matrices={};radii=[5,10,20]
    for name,mask in masks.items():
        A,identity=fit_operator(mask,source,sigma)
        r.require(identity<1e-9,name+' operator identity')
        # Full source vector keeps exact source positions and row ordering;
        # zero columns correspond only to the declared subset exclusion.
        modes,_=r.finufft_modes(target,x,n,g,A,1e-12)
        cov,_=r.cov_from_modes(maps['C'],modes,amp)
        C=cov[0]+cov[1]
        matrices[name]=C
        summary=[]
        for ir,R in enumerate(radii):
            block=C[36*ir:36*(ir+1),36*ir:36*(ir+1)]
            base=baseline
            summary.append({'R_hinv_Mpc':R,'trace':float(np.trace(block)),
                'trace_ratio_to_full_sample':float(np.trace(block)/np.trace(base)),
                'frobenius_relative_to_full_sample':float(np.linalg.norm(block-base)/np.linalg.norm(base)),
                'rank_1e_10':r.diagnostics(block)['rank_1e_10']})
        results[name]={'selected_rows':int(np.sum(mask)),'selection_rule':name,
            'A_X_max_abs':identity,'bands_sum_blocks':summary,
            'same_EH98_field_and_source_epochs':True}
    np.savez_compressed(r.EXTERNAL/'SENSITIVITY_MATRICES.npz',**matrices)
    out={'schema':'htt.r36.cf4_operator_sensitivity/1','time_seconds':time.monotonic()-t,
         'same_nominal_source':'R36-01 exact 35,970 selected groups',
         'new_operator_mean_fits':'fixed H03 design and weights refitted on each stated subset',
         'independent_catalogue_confirmation':False,'results':results}
    r.write_json(r.HERE/'SENSITIVITY.json',out)
    print(json.dumps({'time_seconds':out['time_seconds'],'cases':list(results)}))

if __name__=='__main__':main()
