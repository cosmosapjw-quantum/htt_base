#!/usr/bin/env python3
"""Build small source-locked *conditional* Planck low-l leakage diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform

import numpy as np
from finite_power_envelope import (
    ELLS,SOURCE_SHA256,source_operator,locate_source,shell_slice,shell_gram,
    independent_power_covariance,sharp_ellipsoid_bound,
    shared_mode_correlated_covariance,correlation_agnostic_bound,
    leak_trace_fractions,default_templates)

HERE=Path(__file__).resolve().parents[1]
SOURCE=locate_source(HERE)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise FileExistsError('create-only output directory; existing results immutable')
    K=source_operator(args.source)
    case_results=[]
    saved={'source_K_retained_32x253':K}
    for name,values in default_templates().items():
        C=independent_power_covariance(K,values)
        spectrum=np.linalg.eigvalsh(C)
        radii={ell:float(np.sqrt((2*ell+1)*values[ell])) for ell in ELLS}
        b=sharp_ellipsoid_bound(K,radii)
        correlation={}
        for rho in (0.,0.25,0.5,1.):
            cov=shared_mode_correlated_covariance(K,values,rho)
            e=np.linalg.eigvalsh(cov)
            correlation[str(rho)]={'leading_std':float(np.sqrt(max(e[-1],0.))),
                                   'trace':float(np.trace(cov)),
                                   'eigenvalue_min':float(e[0])}
        fractions=leak_trace_fractions(K,values)
        individual=[{'ell':int(l),'power_Cell_input':float(values[l]),
          'variance_trace_contribution':float(np.trace(shell_gram(K)[l])*values[l]),
          'trace_fraction':float(fractions[l])} for l in ELLS]
        report={'template_name':name,'input_Cell_units':'DECLARED_SCENARIO_VARIANCE_PER_REAL_HARMONIC_COORDINATE',
           'input_Cell':{str(l):float(values[l]) for l in ELLS},
           'independent_shell_covariance':{
               'total_variance_trace':float(np.trace(C)),
               'leading_std':float(np.sqrt(max(spectrum[-1],0))),
               'all_eigenvalues':spectrum.tolist(),
               'min_eigenvalue':float(spectrum[0]),
               'fraction_from_ell6_7':float(fractions[6]+fractions[7]),
               'per_shell_contributions':individual},
           'sharp_ellipsoid':{
               'radii_formula':'R_l=sqrt((2l+1)*C_l); sum ||a_l||^2/R_l^2 <=1; not a probability credible region',
               'sharp_output_norm':b['sharp_bound'],
               'constructed_witness_ellipsoid_norm':b['ellipsoid_norm_of_witness'],
               'constructed_witness_leakage_norm':b['achieved_leakage']},
           'manufactured_cross_shell_rho':correlation,
           'correlation_agnostic_sqrt_largest_output_variance_upper':correlation_agnostic_bound(K,values)}
        case_results.append(report)
        saved['C_'+name]=C
        saved['ELLIPSOID_GRAM_'+name]=b['gram']
    result={
      'schema':'htt.C8.SMICA.source_bound_finite_power_envelopes/1',
      'date_kst':'2026-10-16',
      'source_sha256':SOURCE_SHA256,
      'source_identity_kind':'BYTE_IDENTITY_FROZEN_PR536_K6_16',
      'source_pr':'https://github.com/cosmosapjw-quantum/htt_base/pull/536',
      'continuation_pr':'https://github.com/cosmosapjw-quantum/htt_base/pull/537',
      'math_contract':'Cov(delta a_low)=K Cov(a_high) K^T; sharp ellipsoid = sqrt(lambda_max(sum R_l^2 K_l K_l^T))',
      'operator_layout':'32 retained real orthonormal ell2..5,253 source high ell6..16',
      'source_operator_norm':float(np.linalg.norm(K,2)),
      'source_operator_frobenius_square':float(np.linalg.norm(K,'fro')**2),
      'source_observed_coefficients':'NO_HIGH_ELL_SOURCE_AMPLITUDE_INCLUDED',
      'cases':case_results,
      'claim_status':'SOURCE_BOUND_MASK_GEOMETRY_PLUS_DECLARED_SYNTHETIC_C_L_SCENARIOS_ONLY',
      'scope_limits':{
         'source_mask_geometry':'AUTHENTICATED_PRIOR_PR536_OPERATOR_ONLY',
         'actual_ell6_16_C_l':'UNKNOWN_NOT_SUPPLIED',
         'actual_ell17_32_K':'NOT_AVAILABLE_IN_SANDBOX',
         'ell_gt32_tail':'UNKNOWN',
         'beam_foreground_component_separation_E2E':'UNKNOWN',
         'covariant_egs_multipole_derivative':'UNKNOWN',
         'physical_bianchi_tilt_shear':'HOLD',
         'observational_detection_significance':'NOT_ADMITTED'},
      'runtime':{'python':platform.python_version(),'numpy':np.__version__}}
    args.output.mkdir(parents=True,exist_ok=False)
    with (args.output/'RESULT.json').open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    np.savez_compressed(args.output/'CONDITIONAL_32x32_COVARIANCE.npz',**saved)
    print(json.dumps({'status':'SOURCE_GATED_FINITE_POWER_ENVELOPE_COMPLETE',
       'source_SHA256':SOURCE_SHA256,'n_scenarios':len(case_results),
       'white_trace':case_results[0]['independent_shell_covariance']['total_variance_trace'],
       'white_ell6_7_fraction':case_results[0]['independent_shell_covariance']['fraction_from_ell6_7']},allow_nan=False))

if __name__=='__main__':main()
