"""Source-mode bridge falsifiers and declared D/Sigma sensitivity."""
from __future__ import annotations

import json
import math

import numpy as np

import run_correlated as r

def main():
    with np.load(r.SOURCE,allow_pickle=False) as z:
        source={k:z[k] for k in ['z_CMB','dmzp','n_J2000','method_family','group_id']}
    with np.load(r.OPERATOR,allow_pickle=False) as z:
        A=z['A_raw'];AN=z['AN'];ids=z['group_id'];theta=z['theta36']
    r.require(np.array_equal(ids,source['group_id']),'source IDs bridge')
    chi,g,*_=r.old.background(source['z_CMB'],64)
    x=chi[:,None]*source['n_J2000'];n=source['n_J2000']
    with np.load(r.EXTERNAL/'RESULT_MATRICES.npz') as z:
        PV=z['pv_total'][:36,:36];K=z['method_K'];Sigma=z['method_Sigma'];baseline=z['baseline']
    # One positive quadrature node is a full N-row factor with physical units.
    amp,_=r.old.power_amplitude()
    k,wk=r.old.cc_rule(32,*r.old.BANDS[0]);_,_,u,wu=r.old.angular_rule(53)
    idx=3;ui=11;direction=u[ui];kv=k[idx]
    amplitude=math.sqrt(wk[idx]*r.old.power(kv,amp)*wu[ui]/(4*math.pi)/(2*math.pi**2))
    phase=kv*(x@direction)
    vc=amplitude*g*(n@direction)*np.exp(1j*phase)
    V=np.column_stack((vc.real,vc.imag))
    bridged=r.transport_covariance(A,np.zeros(len(g)),V,
        ownership={'independent':['zero fixture remainder'],
                   'correlated':['one positive common Gaussian Fourier mode']})
    exact=A@vc
    mode_err=float(np.max(abs(bridged['projected_factor'][:,0]+1j*bridged['projected_factor'][:,1]-exact)))
    r.require(mode_err<1e-9,'bridge projected Fourier mode')
    h=np.array([17.,-23.,31.]);relative=np.column_stack((AN,-AN))
    common_null=float(np.max(abs(relative@np.r_[h,h])))
    r.require(common_null<1e-12,'source-observer common null')
    d=10**((source['dmzp']-25)/5)
    method_monopole=float(np.max(abs(K@np.ones(4)-A@d)))
    r.require(method_monopole<1e-12,'method mean-design sum equals monopole')
    probes=np.array([[.005*r.old.H,1.,0.,0.],[.018*r.old.H,0.,1.,0.],
                     [.044*r.old.H,0.,0.,1.]])
    direct=r.direct_modes(probes,x,n,g,A)
    rng=np.random.default_rng(360202);perm=rng.permutation(len(g))
    permuted=r.direct_modes(probes,x[perm],n[perm],g[perm],A[:,perm])
    permutation_error=float(np.max(abs(direct-permuted)))
    r.require(permutation_error<1e-10,'aligned source permutation')
    half=len(g)//2
    halves=[r.direct_modes(probes,x[s],n[s],g[s],A[:,s])
            for s in (slice(0,half),slice(half,None))]
    cross=float(np.linalg.norm(np.outer(halves[0][0].real,halves[1][0].real)+
                               np.outer(halves[1][0].real,halves[0][0].real)))
    r.require(cross>0,'nonzero common-field source cross term')
    with np.load(r.EXTERNAL/'STAGE_C.npz') as z: C=z['total']
    cross_window=float(np.linalg.norm(C[:9,9:18]))
    cross_smoothing=float(np.linalg.norm(C[:36,36:72]))
    r.require(cross_window>0 and cross_smoothing>0,'cross windows and smoothing')
    # Conditional law axes are stipulations; no empirical amplitude is inferred.
    D150=np.full(len(g),150.**2)
    own={'independent':['stipulated independent source law'],
         'calibration':['stipulated method mean-design offsets']}
    transport=r.transport_covariance(A,D150,calibration_response=K,
        calibration_covariance=Sigma,ownership=own)
    CD=transport['independent'];CK=transport['calibration']
    cases=[]
    for sd in (75,150,300):
        for method_sd in (.2,.4,.8):
            c=PV+(sd/150)**2*CD+(method_sd/.4)**2*CK
            fit={name:r.gls_svd(theta,X,c,relative_rank_tolerance=1e-10)
                 for name,X in {
                    'shared_monopole':np.tile(np.eye(9)[:,0],4)[:,None],
                    'shared_nine_coordinate_mean':np.tile(np.eye(9),(4,1))}.items()}
            cases.append({'stipulated_source_SD_km_s':sd,
                'stipulated_method_offset_SD_km_s_Mpc':method_sd,
                'total_trace':float(np.trace(c)),
                'minimum_eigenvalue':float(np.linalg.eigvalsh(c)[0]),
                'shared_monopole_chi2':fit['shared_monopole']['statistic'],
                'shared_nine_chi2':fit['shared_nine_coordinate_mean']['statistic']})
    controls={'schema':'htt.r36.cf4_correlated_controls/1',
        'source_mode_bridge_max_abs':mode_err,
        'source_observer_relative_common_null_max_abs':common_null,
        'method_mean_design_monopole_identity_max_abs':method_monopole,
        'aligned_source_permutation_max_abs':permutation_error,
        'common_field_split_source_cross_norm':cross,
        'cross_window_frobenius':cross_window,'cross_smoothing_frobenius':cross_smoothing,
        'sample_covariance_if_N64_p36':{
            'inverse_unbiased_factor':26/63,
            'diagonal_fractional_SD_under_Gaussian_Wishart':math.sqrt(2/63),
            'off_diagonal_entry_SD':'sqrt((C_ij^2+C_ii*C_jj)/63)',
            'empirical_selected_mocks':'UNAVAILABLE',
            'actual_source_population_coverage':'UNKNOWN'},
        'conditional_D_Sigma_sensitivity':cases,
        'omitted_PV_bands':'UNKNOWN','cross_PV_calibration_sources':'UNKNOWN',
        'magnitude_zero_point_full_estimator_derivative':'UNKNOWN',
        'baseline_working_covariance_trace':float(np.trace(baseline)),
        'baseline_is_independent_noise':False}
    r.write_json(r.HERE/'CONTROLS.json',controls)
    result=json.loads((r.HERE/'RESULT.json').read_text())
    result['controls']='CONTROLS.json'
    result['footprint_method_sensitivity']='SENSITIVITY.json'
    result['sample_covariance_uncertainty']='CONTROLS.json#sample_covariance_if_N64_p36'
    r.write_json(r.HERE/'RESULT.json',result)
    print(json.dumps({'bridge_error':mode_err,'permutation_error':permutation_error,
                      'cross_window':cross_window,'cross_smoothing':cross_smoothing}))

if __name__=='__main__':main()
