"""Separate matched-window RAW-data fits from the archived L01 estimator.

Read two existing JSON reports; reuse their source/response validators. No FITS,
PMASK, SHT or noise model. Only raw RHS column 0 is already a W-weighted moment.
Reconstruction and residual columns must NOT be relabeled as matched fits.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import numpy as np
import l01_native_residual_visibility as previous
import l01_windowed_low_injections as injection

SCHEMA = 'htt.L01_matched_window_raw_data_comparison/1'
INJECTION_SHA256 = '3543a0de7d147e13e0ee30d80f64f36966439dfd027ef9fe8398065c1ca31414'
VISIBILITY_SHA256 = '90b31e50f14d51ac7872cb854551056537206325ad1ced5e7ad75502b2995290'
MASKS = injection.MASKS


def _sym(a):
    return (a+a.T)/2


def matched_fit(grams, holes, raw_rhs):
    """S_i=G_i-C_i; beta_i=S_i^-1 b_i; y_i=R_i beta_i.

    The symmetric identity is d_old=DeltaR*mean(beta)+mean(R)*Delta(beta).
    Both terms depend on the fitted data: this is NOT causal contamination
    attribution. Inputs must be raw b_i=omega A.T M_i W x, not unwindowed b.
    """
    response = injection.response_from_holes(grams, holes)
    if set(raw_rhs) != set(MASKS):
        raise ValueError('RAW_RHS_REQUIRES_TWO_MASKS')
    if any(v['status'] != 'FINITE_LOW_MODEL_IDENTIFIABLE'
           for v in response['matched_controls'].values()):
        raise ValueError('MATCHED_MODEL_NOT_IDENTIFIABLE_NO_PSEUDOINVERSE_FALLBACK')
    n = len(response['difference'])
    old, fitted, metadata = {}, {}, {}
    for key in MASKS:
        g = _sym(injection._real(grams[key], 2))
        c = _sym(injection._real(holes[key], 2))
        b = injection._real(raw_rhs[key], 1)
        if b.shape != (n,):
            raise ValueError('RAW_RHS_MUST_BE_ONE_COLUMN')
        s = g-c
        fitted[key] = np.linalg.solve(s,b)
        old[key] = np.linalg.solve(g,b)
        previous._close(s@fitted[key],b,'MATCHED_NORMAL_RESIDUAL',
                        previous._norm(s)*previous._norm(fitted[key])+previous._norm(b),1e-12)
        previous._close(response['responses'][key]@fitted[key],old[key],
                        'RESPONSE_REPARAMETERIZATION_MISMATCH')
        transform = np.linalg.solve(s,g)
        shift = old[key]-fitted[key]
        loss_gaps = (float(shift@s@shift), float(shift@g@shift))
        if not np.isfinite(loss_gaps).all():
            raise ValueError('OBJECTIVE_GAP_NUMERICAL_RANGE')
        metadata[key] = {'matched_gram_condition': response['matched_controls'][key]['condition'],
            'response_inverse_operator_norm': float(np.linalg.norm(transform,2)),
            'matched_coefficients_K_CMB': fitted[key].tolist(),
            'original_coefficients_K_CMB': old[key].tolist(),
            'matched_loss_excess_of_original_K_CMB2': loss_gaps[0],
            'original_loss_excess_of_matched_K_CMB2': loss_gaps[1],
            'loss_reduction_is_physical_accuracy': False,
            'response_inverse_is_noise_covariance': False}
    common, inner = MASKS
    delta = old[inner]-old[common]
    matched_delta = fitted[inner]-fitted[common]
    mean_beta = (fitted[inner]+fitted[common])/2
    mean_response = (response['responses'][inner]+response['responses'][common])/2
    response_term = response['difference']@mean_beta
    matched_term = mean_response@matched_delta
    parent = previous._norm(old[inner])+previous._norm(old[common])
    closure = previous._close(delta,response_term+matched_term,
                              'SYMMETRIC_DECOMPOSITION_FAILED',parent)
    selectors = previous.groups() if n==64 else {'all':np.arange(n)}
    components = {}
    for name, ix in selectors.items():
        d,u,v,z = [q[ix] for q in (delta,response_term,matched_term,matched_delta)]
        nd,nz,nu,nv = map(previous._norm,(d,z,u,v))
        values = [float(q@q) for q in (d,u,v)] + [float(2*(u@v))]
        if not np.isfinite(values).all():
            raise ValueError('ENERGY_NUMERICAL_RANGE')
        energy_scale = max(values[1]+values[2]+abs(values[3]),np.finfo(float).tiny)
        energy_residual = abs(values[0]-sum(values[1:]))/energy_scale
        if energy_residual>2e-9:
            raise ValueError('SYMMETRIC_ENERGY_IDENTITY_FAILED')
        components[name] = {'original_contrast_norm_K_CMB':nd,
            'matched_contrast_norm_K_CMB':nz,
            'matched_over_original_norm':nz/nd if nd else None,
            'response_term_norm_K_CMB':nu,'matched_term_in_old_units_norm_K_CMB':nv,
            'original_energy_K_CMB2':values[0], 'response_term_energy_K_CMB2':values[1],
            'matched_term_energy_K_CMB2':values[2], 'interference_K_CMB2':values[3],
            'energy_identity_relative':energy_residual,
            'response_term_is_physical_contamination_estimate':False}
    return {'matched_coefficients':fitted,'original_coefficients':old,
            'original_contrast_K_CMB':delta.tolist(),
            'matched_contrast_K_CMB':matched_delta.tolist(),
            'response_term_K_CMB':response_term.tolist(),
            'matched_term_in_old_coordinates_K_CMB':matched_term.tolist(),
            'symmetric_closure_relative_to_parent':closure,
            'fit_metadata':metadata,'components':components,'response_replay':response}


def validate_inputs(native, probe):
    """Validate saved source links and numerical response, not a new map replay."""
    previous.analyze_report(native)
    expected = {'schema':injection.SCHEMA,'status':'PASS_FINITE_LOW_SOURCE_WINDOW_RESPONSE',
        'nside':native['nside'],'input_ells':[2,3,4,5],'output_ells':[2,3,4,5],
        'source_model':'INJECTED_DELIVERED_LOW_BAND_FIELD_A_C_NOT_MEASURED_COSMIC_COEFFICIENTS',
        'original_estimator_changed':False,'matched_control_applied_to_observed_data':False,
        'native_observed_QU_reread':False,'native_SHT_run':False,
        'noise_covariance':None,'p_value':None,'infinite_tail_bound':'NOT_ESTABLISHED',
        'paper_gate':'NOT_READY_TO_SUBMIT','code_sha256':INJECTION_SHA256,
        'source_window_sha256':native['native_window_sha256'],
        'native_receipt_sha256':previous.NATIVE_RECEIPT_SHA}
    if not isinstance(probe,dict) or any(probe.get(k)!=v for k,v in expected.items()):
        raise ValueError('LOW_SOURCE_REPORT_CONTRACT_MISMATCH')
    codes={'l01_native_residual_projection':previous.PRODUCER_SHA256,
        'l01_native_residual_visibility':VISIBILITY_SHA256,
        'l01_smica_processed_bands':native['checkpoint']['contract']['analysis_code_sha256']}
    if probe.get('reused_code_sha256') != codes:
        raise ValueError('LOW_SOURCE_REPORT_DEPENDENCY_MISMATCH')
    if not re.fullmatch('[0-9a-f]{64}',str(probe.get('native_report_sha256',''))):
        raise ValueError('NATIVE_LINK_EXPECTED_DIGEST_MALFORMED')
    scan=probe['scan']; npix=12*native['nside']**2
    if scan['total_native_pixels']!=npix or scan['source_pixels_or_estimator_changed'] is not False:
        raise ValueError('LOW_SOURCE_SCAN_CONTRACT_MISMATCH')
    previous._close(scan['native_pixel_area'],4*np.pi/npix,'PIXEL_AREA_MISMATCH',rtol=1e-13)
    retained={}
    for key in MASKS:
        original=scan['original_fit_selected_pixels'][key]
        holes=scan['excluded_source_pixels_in_fit_region'][key]
        if (type(original) is not int or type(holes) is not int or
            original!=native['solver_states'][key]['selected_pixels'] or not 0<=holes<=original):
            raise ValueError('LOW_SOURCE_SCAN_COUNT_MISMATCH')
        retained[key]=original-holes
    if (retained[MASKS[0]]<retained[MASKS[1]] or
        scan['excluded_source_pixels_in_fit_region'][MASKS[0]]<scan['excluded_source_pixels_in_fit_region'][MASKS[1]] or
        scan['design_evaluated_spatial_pixels']!=scan['excluded_source_pixels_in_fit_region'][MASKS[0]]):
        raise ValueError('MATCHED_SUPPORT_NOT_NESTED')
    grams={k:native['solver_states'][k]['gram'] for k in MASKS}
    response=injection.response_from_holes(grams,probe['hole_moments'])
    previous._close(probe['two_mask_difference'],response['difference'],'LOW_SOURCE_RESPONSE_DIFFERENCE_MISMATCH')
    for key in MASKS:
        previous._close(probe['responses'][key],response['responses'][key],'LOW_SOURCE_RESPONSE_MISMATCH')
        saved=probe['matched_controls'][key]; checked=response['matched_controls'][key]
        if saved['status']!=checked['status']:
            raise ValueError('LOW_SOURCE_IDENTIFIABILITY_MISMATCH')
        if checked['status']=='FINITE_LOW_MODEL_IDENTIFIABLE':
            previous._close(saved['condition'],checked['condition'],'MATCHED_CONDITION_MISMATCH')
    return grams,retained


def analyze_reports(native,probe):
    grams,retained=validate_inputs(native,probe)
    # Raw is the only saved column with the extra W required for matched RHS.
    rhs={k:injection._real(native['solver_states'][k]['rhs'],2)[:,0] for k in MASKS}
    r=matched_fit(grams,probe['hole_moments'],rhs)
    previous._close(r['original_contrast_K_CMB'],native['contrast_raw_K_CMB'],
                    'ORIGINAL_RAW_VECTOR_NOT_REPRODUCED',
                    sum(previous._norm(v) for v in r['original_coefficients'].values()))
    for k in MASKS:
        previous._close(r['original_coefficients'][k],
                        np.asarray(native['solver_states'][k]['coefficients'])[:,0],
                        'ORIGINAL_RAW_FIT_NOT_REPRODUCED')
    # Remove internal NumPy objects. Arrays needed for science are explicitly saved.
    for key in ('response_replay','matched_coefficients','original_coefficients'):
        r.pop(key)
    r.update(schema=SCHEMA,status='PASS_MATCHED_WINDOW_RAW_COMPARISON',
        product=native['product'],source_sha256=native['source']['sha256'],
        source_window_sha256=native['native_window_sha256'],native_nside=native['nside'],
        matched_selected_spatial_pixels=retained,
        input_column='RAW_W_TIMES_DELIVERED_QU_ONLY',
        reconstruction_and_residual_columns_reinterpreted=False,
        original_estimator_replaced=False,original_measured_residual_changed=False,
        matched_control_applied_to_raw_moments=True,
        new_native_pixel_scan=False,source_FITS_reread=False,native_SHT_run=False,
        coefficient_space='REAL_ELL2_TO5_EB_FINITE_REGRESSION_NOT_PURE_COSMIC_EB',
        scalar_norms_are_pseudocl=False,noise_covariance=None,p_value=None,
        physical_contamination_fraction=None,infinite_tail_bound='NOT_ESTABLISHED',
        physical_sky_identification=False,paper_gate='NOT_READY_TO_SUBMIT')
    return r


def _canonical(r):
    return json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False)


def load_linked(native_path,probe_path,linked_native_path=None):
    native,current_sha=previous.read_report(native_path)
    probe,probe_sha=previous.read_report(probe_path)
    link=probe.get('native_report_sha256') if isinstance(probe,dict) else None
    if not isinstance(link,str) or not re.fullmatch('[0-9a-f]{64}',link):
        raise ValueError('NATIVE_LINK_EXPECTED_DIGEST_MALFORMED')
    relation='BYTE_IDENTICAL_TO_LINKED_REPORT'
    if current_sha!=link:
        if linked_native_path is None:
            raise ValueError('NATIVE_LINK_BYTE_MISMATCH__SEMANTICS_UNRESOLVED: supply --linked-native-report with originally linked bytes')
        reference,reference_sha=previous.read_report(linked_native_path)
        if reference_sha!=link:
            raise ValueError('REFERENCE_NATIVE_REPORT_BYTE_MISMATCH')
        if _canonical(reference)!=_canonical(native):
            raise ValueError('NATIVE_REPORT_CANONICAL_CONTENT_MISMATCH')
        relation='CANONICAL_JSON_IDENTICAL_TO_BYTE_LINKED_REFERENCE'
    return native,probe,{'native_report_sha256':current_sha,'linked_native_report_sha256':link,
        'injection_report_sha256':probe_sha,'native_link_relation':relation,
        'source_FITS_locks_changed':False}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-report',required=True)
    ap.add_argument('--injection-report',required=True)
    ap.add_argument('--linked-native-report',help='Original byte-linked report, only needed for a reserialized equivalent native JSON')
    ap.add_argument('--out',required=True)
    args=ap.parse_args(argv)
    try:
        if Path(args.out).exists() or Path(args.out).is_symlink():
            raise ValueError('OUTPUT_EXISTS_NOT_OVERWRITTEN')
        versions={injection:INJECTION_SHA256,previous:VISIBILITY_SHA256,
                  previous.native:previous.PRODUCER_SHA256}
        if any(previous.digest(mod.__file__)!=sha for mod,sha in versions.items()):
            raise ValueError('UNSUPPORTED_SOURCE_READER_VERSION')
        native,probe,evidence=load_linked(args.native_report,args.injection_report,args.linked_native_report)
        result=analyze_reports(native,probe)
        result.update(input_evidence=evidence,code_sha256=previous.digest(__file__),
                      dependency_sha256={m.__name__:s for m,s in versions.items()})
        previous.write_new(args.out,result)
    except (ValueError,TypeError,KeyError,OSError,OverflowError,FloatingPointError,np.linalg.LinAlgError) as exc:
        print(json.dumps({'status':'BLOCKED','error_type':type(exc).__name__,'error':str(exc)}),file=sys.stderr)
        return 2
    print(json.dumps({'status':result['status'],'product':result['product'],
        'matched_selected_spatial_pixels':result['matched_selected_spatial_pixels'],
        'components':result['components'],
        'symmetric_closure_relative_to_parent':result['symmetric_closure_relative_to_parent'],
        'native_maps_replayed':False,'out':args.out,'paper_gate':result['paper_gate']},indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
