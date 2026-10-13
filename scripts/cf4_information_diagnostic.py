#!/usr/bin/env python3
"""Generate OBS-02 sensitivity spectra; does not fit observed velocities."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'htt'),str(ROOT/'htt/htt'),str(ROOT/'htt/src')]
import numpy as np
from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations, METHODS
from htt.infer.cf4_information import NoiseScenario,profiled_rows,information,contrast_uncertainty,NAMES,T_CART_TO_FROB

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'workdir/raw/cf4_full')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/observational_methods_20261013/OBS-02')
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    cat=load_grouped_observations(args.source/'table3.dat.gz',args.source/'table4.dat.gz',args.source/'ReadMe')
    scenarios=[NoiseScenario('fixed_cal_sigma30_motion150',30,150),NoiseScenario('fixed_cal_sigma100_motion300',100,300),
        NoiseScenario('free_common_sigma100_motion300',100,300,True),
        NoiseScenario('free_common_and_method_sigma100_motion300',100,300,True,True)]
    results=[]
    for scenario in scenarios:
        x,n,r,z=profiled_rows(cat,scenario)
        low,high=np.quantile(r,[.49,.51])
        masks={'full':np.ones(len(r),bool),'central_49_51_percent_dA_fiducial':(r>=low)&(r<=high),
            'delete_nearest_quartile':r>np.quantile(r,.25),'delete_farthest_quartile':r<np.quantile(r,.75)}
        masks.update({'delete_presence_'+name:~cat.method_presence[:,j] for j,name in enumerate(METHODS)})
        for name,mask in masks.items():
            if not mask.any():continue
            info=information(x,n,mask)
            contrasts={}
            for j,p in enumerate(NAMES):
                g=np.eye(13)[j];contrasts[p]=contrast_uncertainty(info,g)
            # Ratios of directional expansion to H are invariant under free scale.
            for j,p in enumerate(NAMES[5:],5):
                g=np.eye(13)[j]/70.
                contrasts[p+'_over_H_at_zero_anisotropy']=contrast_uncertainty(info,g)
            results.append({'scenario':scenario.__dict__,'sample':name,'selected_group_sha256':hashlib.sha256(np.asarray(cat.group_id[mask],dtype='<i8').tobytes()).hexdigest(),
                'r_fiducial_Mpc_min_max':[float(r[mask].min()),float(r[mask].max())],
                **{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in info.items()},'contrasts':contrasts})
    report={'task':'OBS-02','owner':'HTT inference; obsstat catalogue parsing','scope':'catalogue-conditioned local sensitivity under declared independent diagonal noise and free calibration scenarios',
        'claim_tier':'diagnostic_only','transfer_source':'none','config_identity':'inline fixed scenarios, scales and fiducial in scripts/cf4_information_diagnostic.py','physical_rank_admission':'HOLD','selection_status':'SELECTION_LAW_NOT_BOUND',
        'source':cat.provenance,'row_count':len(cat.group_id),'method_presence_counts':dict(zip(METHODS,cat.method_presence.sum(axis=0).tolist())),'negative_or_zero_vh_count':int(np.sum(cat.vh_km_s<=0)),
        'distance_error':{'median_modulus_sigma_mag':float(np.median(cat.modulus_error)),
            'fraction_sigma_ln_distance_above_0_2':float(np.mean(cat.modulus_error/(5/np.log(10))>.2))},
        'fiducial':{'H_km_s_Mpc':70.,'b0_B_A_STF':'zero','z_true':'Vh/c','dA':'exp((DMzp-25)/a)/(1+z_true)^2; fixed linearization, not fitted distance'},
        'noise_contract':'e_DMzp as published marginal sigma; independent per-group mu/redshift/source-motion scenario penalties; not measured full covariance',
        'source_motion_row':'pseudo residual c*z-h; model noise penalty, not extra observation',
        'scale_null_contract':'isotropic fiducial specialization: delta H=H*epsilon, delta ln dA=-epsilon, delta kappa=a*epsilon; generally all nine expansion coefficients scale together; zero fiducial anisotropy makes their absolute tangent zero',
        'nuisance_contract':'one free common mu zero point; optional independent unconstrained offsets for boolean method PRESENCE, not fractional method weights',
        'deletion_contract':'remove groups possessing method; retained DMzp never recomputed; depth masks fixed at baseline fiducial',
        'basis':{'order':list(NAMES),'cartesian_q':'(a,b,d,e,f); matrix [[a,d,e],[d,b,f],[e,f,-a-b]]',
            'cartesian_to_frobenius':T_CART_TO_FROB.tolist(),'covariance_transform':'V_F=T V_C T.T; inverse T for reverse transform'},
        'reused_geometry':{'source':'package evidence/cf4_geometry.json','uniform_dL_proxy_full_rank':[12,13],
            'full_condition':[11.199086342043145,14.477312895579985],'narrow_condition':[304.7664339803345,396.9632003755181],
            'comparison':'legacy per-sample normalized uniform dL spectra are distinct from current fixed physical column scaling'},
        'caveats':['no selection normalization','no actual shared calibration covariance supplied','no physical response fit or significance',
            'first-order latent profiling only; broad distance errors limit approximation','numerical rank is tolerance and scale dependent',
            'method deletion is a footprint diagnostic, not independent distance reanalysis','no global tilt/vorticity or native Bianchi family identification'],
        'runtime':{'requested_model':'gpt-6.1-sol','requested_effort':'medium','observed_runtime':'UNKNOWN',
            'python':sys.executable,'python_version':platform.python_version(),'numpy':np.__version__,
            'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()},'results':results}
    (args.output/'information.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.5))
    for item in results:
        s=np.array(item['singular_values']);s=np.where(s>item['rank_tolerance'],s,np.nan)
        if item['sample']=='full':axes[0].semilogy(np.arange(1,len(s)+1),s,'o-',label=item['scenario']['name'])
        if item['scenario']['name']=='free_common_and_method_sigma100_motion300':axes[1].semilogy(np.arange(1,len(s)+1),s,'o-',label=item['sample'])
    for ax in axes:
        ax.set_xlabel('descending singular mode');ax.set_ylabel('profiled response / scenario noise (fixed coefficient scales)');ax.legend(fontsize=6);ax.grid(alpha=.25)
    axes[0].set_title('Full grouped sample: scenario comparison');axes[1].set_title('Common + method nuisance: footprint deletion')
    fig.suptitle('CF4 local sensitivity; numerical null modes omitted; physical admission HOLD')
    fig.tight_layout();fig.savefig(args.output/'singular_values.png',dpi=170);fig.savefig(args.output/'singular_values.pdf');plt.close(fig)
    print(json.dumps({'rows':len(cat.group_id),'comparisons':len(results),'output':str(args.output),'full_ranks':[(i['scenario']['name'],i['rank']) for i in results if i['sample']=='full']}))
if __name__=='__main__':main()
