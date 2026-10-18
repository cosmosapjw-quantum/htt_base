"""Create-only P3/H03 source-conditioned, 9D CF4 redshift angular tomography.

Use released frozen CF4 groups ONLY, not a physical Hubble/distance/selection law.
Python -m pytest tests first; then --source /absolute/path and --output /new/directory.
"""
from __future__ import annotations
import argparse, json, platform, sys
from pathlib import Path
import numpy as np
from scipy.linalg import lstsq
import h03_tomography as H

HERE=Path(__file__).resolve().parent

def discover_source() -> Path:
    bundled=HERE.parent/'inputs'/'selected_source_observables.npz'
    if bundled.is_file():return bundled
    for root in HERE.parents:
        if root.name=='htt_base':
            path=root/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
            if path.is_file():return path
    raise FileNotFoundError('Source unavailable: provide the exact frozen CF4 selected_source_observables.npz; no substitution allowed')


def theta_summary(theta:np.ndarray,fit_info:dict,signal_cov:np.ndarray|None=None)->dict:
    coeff=np.asarray(theta,float)
    dd=coeff[1:4];Q=H.quadrupole_matrix(coeff[4:])
    norm=float(np.linalg.norm(dd));frob=float(np.linalg.norm(coeff[4:]))
    direction=None
    if norm>0:
        dip=dd/norm;direction={'ICRS_RA_deg':float(np.degrees(np.mod(np.arctan2(dip[1],dip[0]),2*np.pi))),
                             'ICRS_Dec_deg':float(np.degrees(np.arcsin(np.clip(dip[2],-1,1))))}
    return {'H0_working_km_s_Mpc':float(coeff[0]), 'dipole_cartesian_km_s_Mpc':dd.tolist(),
            'dipole_norm_km_s_Mpc':norm,'dipole_ICRS_direction':direction,
            'STF5_coefficients_km_s_Mpc':coeff[4:].tolist(),
            'STF2_frobenius_km_s_Mpc':frob,
            'STF2_matrix_km_s_Mpc':Q.tolist(),
            'working_design_condition':float(fit_info['cond']),
            'fit_weighted_n_eff':float(fit_info['weighted_n_eff']),
            'fit_weighted_distance_n_eff':float(fit_info['weighted_distance_n_eff']),
            'source_window_support_count':int(fit_info['nactive']),
            'WLS_identity_max_residual':float(fit_info['identity'])}


def compute(source_path:Path)->tuple[dict,dict]:
    src=H.source(source_path)
    d=H.proxy_distance(src.mu);sig=H.working_sigma(d,src.e_mu);vel=H.C_KM_S*src.z
    X=H.velocity_design(d,src.n)
    results=[];linear=[];weights=[];theta=[];normal_only=[];noise_regression=[]
    for center in H.CENTERS:
        w=H.window(src.z,sig,center,n=src.n)
        o=H.fit(X,vel,w)
        vals=o['theta'];theta.append(vals);weights.append(w);linear.append(o['A'])
        mon=float(np.dot(w*d,vel)/np.dot(w*d,d))
        normal_only.append(mon)
        b=H.source_response(o,src.n,d)
        sigma_c=np.sqrt(np.sum((o['A']*sig[None,:])**2,axis=1))
        fractions={str(m):float(np.dot(w[src.method==m],d[src.method==m]**2)/np.dot(w,d*d)) for m in H.METHODS}
        rec={'z_center':center,'bandwidth':H.WIDTH,
             'theta9':vals.tolist(),
             'unconditional_source_label':'real CF4 group distances/redshifts with assumed noise and angular working basis',
             'conditional_diagonal_std9':sigma_c.tolist(),
             'H01_monopole_only_formula':mon,
             'monopole_multipole_selection_shift':float(vals[0]-mon),
             'source_method_distance_weight_fractions':fractions,
             'bulk_velocity_design_response_9x3_per_Mpc':b['bulk_response_inverse_mpc'].tolist(),
             'bulk_response_dipole_singular_values_inverse_Mpc':np.linalg.svd(b['bulk_response_inverse_mpc'][1:4],compute_uv=False).tolist(),
             'expansion_dipole_identity_max':b['expansion_dipole_identity_max']}
        rec.update(theta_summary(vals,o))
        # Independent QR-vs-SVD source check on first and last z window.
        if center in (H.CENTERS[0],H.CENTERS[-1]):
            solution=lstsq(np.sqrt(w)[:,None]*X,np.sqrt(w)*vel,lapack_driver='gelsd',check_finite=False)[0]
            delta=float(np.max(np.abs(solution-vals)))
            if delta>1e-8:raise AssertionError(f'QR / independent SVD source mismatch: {delta}')
            noise_regression.append({'center':center,'QR_vs_independent_SVD_max_abs':delta})
        results.append(rec)
    A=np.concatenate(linear,axis=0)
    C,R=H.joint_covariance(A,sig)
    # Independent contraction with source sigma^2: explicitly non-diagonal 36 x 36 across windows.
    max_cov_recheck=float(np.max(np.abs(C-(A*sig[None,:]**2)@A.T)))
    if max_cov_recheck>1e-8:raise AssertionError('full covariance independent contraction mismatch')
    eig=np.linalg.eigvalsh(C)
    if eig.min()<-1e-10:raise AssertionError('non-PSD joint conditional covariance')
    # Source-matched north-axis reweighting is only a sensitivity branch; it is NOT a new independent sample.
    north=[]
    for center,base_theta in zip(H.CENTERS,theta):
        wn=H.window(src.z,sig,center,n=src.n,alpha=.6)
        on=H.fit(X,vel,wn,influence=False)
        north.append({'center':center,'theta9':on['theta'].tolist(),
                      'delta_H0':float(on['theta'][0]-base_theta[0]),
                      'delta_dipole_norm':float(np.linalg.norm(on['theta'][1:4]-base_theta[1:4])),
                      'delta_STF5_frob':float(np.linalg.norm(on['theta'][4:]-base_theta[4:]))})
    # Leave one of the four existing group method families out. These are correlated, not heldout validation.
    family=[];patch=[]
    for m in H.METHODS:
        mask=src.method!=m
        stats=[]
        for c,w0,base_theta in zip(H.CENTERS,weights,theta):
            ff=H.fit(X,vel,H.window(src.z,sig,c,active=mask),influence=False)
            stats.append({'center':c,'delta_H0_km_s_Mpc':float(ff['theta'][0]-base_theta[0]),
                          'delta_dipole_L2_km_s_Mpc':float(np.linalg.norm(ff['theta'][1:4]-base_theta[1:4])),
                          'delta_STF5_L2_km_s_Mpc':float(np.linalg.norm(ff['theta'][4:]-base_theta[4:])),
                          'condition':float(ff['cond'])})
        family.append({'family_excluded':m,'excluded_groups':int(np.sum(~mask)),
                       'remaining_groups':int(np.sum(mask)),'windows':stats})
    patches=H.patch_id(src.n)
    for k in range(12):
        mask=patches!=k
        row=[]
        for c,base_theta in zip(H.CENTERS,theta):
            o=H.fit(X,vel,H.window(src.z,sig,c,active=mask),influence=False)
            row.append({'center':c,'delta_H0':float(o['theta'][0]-base_theta[0]),
                        'delta_dipole_norm':float(np.linalg.norm(o['theta'][1:4]-base_theta[1:4])),
                        'delta_STF_norm':float(np.linalg.norm(o['theta'][4:]-base_theta[4:])),
                        'condition':float(o['cond'])})
        patch.append({'ICRS_patch_id':k,'removed_groups':int(np.sum(~mask)),'windows':row})
    theta=np.asarray(theta,float)
    cross_dip=[]
    for j in range(3):
        inds=[9*k+1+j for k in range(len(H.CENTERS))]
        block=R[np.ix_(inds,inds)]
        cross_dip.append({'dipole_axis_ICRS':'xyz'[j], 'correlation_four_windows':block.tolist()})
    # Critical prior H01 anchored selected weights, no reinterpretation of raw CL at high z.
    result={'schema':'htt.sixpaper.P3_H03_source_conditional_tomography/1',
            'paper':'P3','node':'H03',
            'claim_tier':'RELEASED_CF4_GROUPS_WORKING_ANGULAR_TOMOGRAPHY_ONLY',
            'source_SHA256':H.SOURCE_SHA256,'source_groups':len(src.z),
            'common_directions':'ICRS J2000 Cartesian unit n, one real released group per row',
            'four_gaussian_window_centers':list(H.CENTERS),'width_z':H.WIDTH,
            'working_law':'cz_i = d(DMzp_i)*[H_w + D_w.n_i + n_i Q_w n_i], 9D real STF, not physical expansion H(z,n)',
            'weighting':'Gaussian z window / {250^2 + [70*(ln10/5)*d*e_dmzp]^2}; diagonal working velocity scatter only',
            'full_joint_covariance_kind':'inherited same 35970 groups, correlated four windows, assuming diagonal sigma_i^2 across rows',
            'monopole_dipole_STF2_windows':results,
            'joint_covariance_36x36':C.tolist(),
            'joint_correlation_36x36':R.tolist(),
            'cross_window_dipole_correlations':cross_dip,
            'covariance_numerical_checks':{'PSD_min_eigenvalue':float(eig.min()),'PSD_max_eigenvalue':float(eig.max()),
               'QR_vs_independent_SVD':noise_regression,'cross_contract_max_abs':max_cov_recheck},
            'source_method_family_delete_sensitivity':family,
            'fixed_ICRS_12_patch_delete_sensitivity':patch,
            'north_weighted_same_sky_sensitivity':north,
            'sampling_law_limits':{'method_and_calibration_shared_covariance':'UNKNOWN',
               'actual_group_selection':'UNKNOWN', 'physical_peculiar_velocity_field':'UNKNOWN',
               'observer_frame_and_cosmographic_transfer':'UNAVAILABLE',
               'six_paper_publication_status':'NOT_READY_TO_SUBMIT',
               'pvalue_or_Bayes_factor':'NOT_COMPUTED',
               'physical_H_Theta_over3_or_shear':'NOT_MEASURED'},
            'python':platform.python_version(),'numpy':np.__version__,
            'implementation_scope':'H03 empirical fixed-working-law window fits and sensitivities; no native low-ell solver'}
    matrices={'theta4x9':theta,'joint_cov36x36':C,'joint_corr36x36':R,
              'H01_monopole4':np.asarray(normal_only),
              'sigma_assumed_per_group':sig,
              'group_id':src.ids}
    return result,matrices


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=None);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():raise FileExistsError('create-only output directory required')
    val,mat=compute(args.source or discover_source())
    args.output.mkdir(parents=True)
    (args.output/'H03_SOURCE_TOMOGRAPHY.json').write_text(json.dumps(val,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    np.savez_compressed(args.output/'H03_CONDITIONAL_MATRIX.npz',**mat)
    print(json.dumps({'n':val['source_groups'],'windows':len(val['monopole_dipole_STF2_windows']),
                      'H0':[round(x['H0_working_km_s_Mpc'],6) for x in val['monopole_dipole_STF2_windows']],
                      'dipole_norm':[round(x['dipole_norm_km_s_Mpc'],6) for x in val['monopole_dipole_STF2_windows']],
                      'status':'SOURCE_CONDITIONAL_ONLY'}))
if __name__=='__main__':main()
