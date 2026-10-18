#!/usr/bin/env python3
"""Recompute official SH0ES 2022 compact C,L,y analytic GLS source benchmark.

Mixed observables and source parameter order are inherited unchanged
from Riess et al. (2022) DataRelease; NO novel H0/CF4 combined posterior.
Prior-like artificial anchor rows are already part of the released matrix.
"""
from __future__ import annotations

import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np
from astropy.io import fits
from scipy.linalg import cholesky,solve_triangular
from obsstat.htt_shoes_matrix_bridge import (
    whitened_linear_gls,conditional_template_information)

ROOT=Path(__file__).resolve().parents[1]
RAW=Path('/mnt/extdrive/workdir/raw/shoes2022_calibration_reference_20261015')
C=RAW/'allc_shoes_ceph_topantheonwt6.0_112221.fits'
L=RAW/'alll_shoes_ceph_topantheonwt6.0_112221.fits'
Y=RAW/'ally_shoes_ceph_topantheonwt6.0_112221.fits'
REF=RAW/'lstsq_results.txt'
LFS_SHA='a42778672d25df7a559bd2949b1e412b99b2e35dd9a36895f6b38828be019172'


def shasum(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def run(out):
    if out.exists():raise ValueError('create-only GLS result directory')
    t=time.perf_counter()
    if shasum(C)!=LFS_SHA:
        raise ValueError('official SH0ES 2022 Git LFS matrix identity failed')
    q=np.asarray(fits.getdata(Y),dtype=float)
    A=np.asarray(fits.getdata(L),dtype=float).T.copy()
    covariance=np.asarray(fits.getdata(C),dtype=float)
    prior=np.loadtxt(REF)
    if (q.shape!=(3492,) or A.shape!=(3492,47) or covariance.shape!=(3492,3492)
        or prior.shape!=(47,2)):
        raise ValueError('SH0ES 2022 released y,L,C source schema mismatch')
    fit=whitened_linear_gls(q,A,covariance)
    if fit['rank']!=47 or fit['normal_equation_gradient_relative']>1e-9:
        raise ValueError('published basis GLS numerical gradient invalid')
    chol=cholesky(covariance,lower=True,check_finite=False)
    reference_res=solve_triangular(chol,q-A@prior[:,0],lower=True,check_finite=False)
    chisq_reference=float(reference_res@reference_res)
    chi2_delta=chisq_reference-fit['full_chi_squared']
    if chi2_delta < -1e-7:
        raise ValueError('published source benchmark is better than real Cholesky fit')
    # A source-template in actual observation design has zero independent
    # profiled information. A generic all-observations offset can behave
    # differently under a fixed ladder's geometrical anchor rows.
    col=conditional_template_information(A[:,0],A,covariance)
    ones=conditional_template_information(np.ones(len(q)),A,covariance)
    result={
      'schema':'htt.SH0ES_2022_observed_compact_linear_matrix/1',
      'scientific_status':'EXECUTED_SOURCE_BOUND_GLS_NO_NEW_H0_CF4_POSTERIOR',
      'source_release':'PantheonPlusSH0ES/DataRelease commit c447f0fea703fcd0fff57de5000947b5ca81286b',
      'source_file_sha256':{str(p):shasum(p) for p in (C,L,Y,REF)},
      'n_observed_equations':len(q),'n_frozen_parameters':A.shape[1],
      'source_slope_offset':'official source README states Cepheid slope -3.285 pre-subtracted and fitted free slope is a correction; parameter ordering retained unaltered',
      'source_computation':'unregularized full released C Cholesky GLS, no manually invented prior, no covariance rescale',
      'C_full_numerical_cholesky':'PASS',
      'baseline_GLS':{
         'chi2':fit['full_chi_squared'],'dof':fit['residual_dof'],
         'chi2_per_dof':fit['full_chi_squared']/fit['residual_dof'],
         'n_normal_matrix_condition':fit['condition_number_normal_matrix'],
         'normalized_normal_equation_gradient':fit['normal_equation_gradient_relative'],
         'estimate':fit['estimate'].tolist(),
         'standard_errors_from_exact_Fisher_diagonal':fit['estimate_sigma'].tolist(),
      },
      'official_lstsq_results_comparison':{
         'declared_release_result':'lstsq_results.txt (also used as approximate uniform-prior centers in run_mcmc.py)',
         'reference_beta':prior[:,0].tolist(),
         'reference_error':prior[:,1].tolist(),
         'maximum_absolute_coefficient_difference':float(np.max(np.abs(fit['estimate']-prior[:,0]))),
         'median_absolute_coefficient_difference':float(np.median(np.abs(fit['estimate']-prior[:,0]))),
         'max_absolute_diagonal_sigma_difference':float(np.max(np.abs(fit['estimate_sigma']-prior[:,1]))),
         'chi_squared_at_reference_centers':chisq_reference,
         'chi_squared_difference_reference_minus_GLS':chi2_delta,
         'reference_is_exact_same_GLS':'UNVERIFIED; may be different original pipeline weight/priors, code source need author-level correspondence',
         'not':'No adjustments of file values or physical H0 hypothesis to force benchmark agreement'
      },
      'algebraic_gauge_checks':{
        'source_column_0_relative_information_after_profile':col['retained_information_fraction'],
        'generic_all_observation_offset_relative_information_after_profile':ones['retained_information_fraction'],
        'generic_all_observation_offset_template_not_CF4_calibrator':True,
      },
      'unresolved_cross_catalogue_sources':[
       'Observed source/event group host identity loading from 47 SH0ES parameters to CF4 direct/method group anchor records',
       'shared host and SNIa/Cepheid covariance, including Pantheon+SH0ES overlap',
       'CF4 per-method parent and selection normalization and joint source-frame distance/redshift physics'],
      'seconds':time.perf_counter()-t,
      'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'gls_47_parameter_covariance.npz',
        estimate=fit['estimate'],covariance=fit['estimate_covariance'],
        reference=prior[:,0],reference_error=prior[:,1],
        normal_matrix=fit['normal_matrix'])
    doc=['# SH0ES 2022 3492×47 joint linear source matrix: 실제 Cholesky GLS',
      '', '이 계산은 **발표된 동일 SH0ES input의 고정된 원자료 선형 모델**에 대한 numerical fit다.',
      '그룹 CF4와 합친 새로운 H0 또는 추가 독립 거리사다리 관측이 아니다.',
      '',
      f"Cholesky GLS chi2={fit['full_chi_squared']:.9g} for dof={fit['residual_dof']}",
      f"Normal equation relative gradient={fit['normal_equation_gradient_relative']:.6g}",
      f"Normal Fisher condition={fit['condition_number_normal_matrix']:.6g}",
      f"Official distributed lstsq_results center χ²={chisq_reference:.8g}, difference={chi2_delta:.8g}",
      f"Largest absolute coefficient discrepancy={result['official_lstsq_results_comparison']['maximum_absolute_coefficient_difference']:.7g}",
      '',
      '**Scientific blocker:** Published reference centres/sigmas in lstsq_results.txt are not byte-identical to simple unregularized Cholesky GLS of current C,L,y. Distinguish actual center file as approximate broad MCMC prior configuration and check upstream algorithm before claiming publication reproduction.',
      '',
      'An additive template contained in the 47-dimensional A image has zero profiled Fisher information by construction. The all-rows constant template has its own algebraic information fraction, NOT a physical CF4 common-zero-point prior.',
      'A physical CF4 bridge needs explicit source-matched host/event loading and joint covariance before any cross-catalogue prior transfer.']
    (out/'REPORT_KO.md').write_text('\n'.join(doc)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,3.8),layout='constrained')
    x=np.arange(1,48)
    yerr=np.maximum(np.abs(prior[:,1]),1e-5)
    ax.errorbar(x,fit['estimate']-prior[:,0],yerr=fit['estimate_sigma'],
                linestyle='none',capsize=1,markersize=2,fmt='o')
    ax.axhline(0,color='gray',lw=.7)
    ax.set(xlabel='Release-ordered ladder coefficient (1..47)',
           ylabel='GLS minus released benchmark (native parameter units)',
           title='Official SH0ES 2022 C,L,y consistency, not an independent H0 estimate')
    fig.savefig(out/'shoes_gls_reference_discrepancy.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'status':result['scientific_status'],
       'chi2':fit['full_chi_squared'],'dof':fit['residual_dof'],
       'chi2_reference_difference':chi2_delta,
       'max_delta_parameter':result['official_lstsq_results_comparison']['maximum_absolute_coefficient_difference'],
       'relative_source_col0_information':col['retained_information_fraction'],
       'relative_ones_information':ones['retained_information_fraction'],
       'seconds':result['seconds']},ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    run(args.output_dir)
