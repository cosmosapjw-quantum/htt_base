"""Window-matched low-band fits from archived moments, not a cosmic E/B map.

Only raw RHS column 0 is reused. Reconstruction/residual RHS require an
additional windowed moment that the current native report does not contain.
"""
import argparse
import json
from pathlib import Path
import numpy as np

NAMES = ('common', 'three_way_intersection')
INJECTION_SHA = '3543a0de7d147e13e0ee30d80f64f36966439dfd027ef9fe8398065c1ca31414'


def arr(x, ndim):
    a = np.asarray(x)
    if a.ndim != ndim or a.dtype.kind not in 'fiu':
        raise ValueError('REAL_ARRAY_SHAPE_OR_TYPE')
    a = a.astype(float, copy=False)
    if not np.isfinite(a).all():
        raise ValueError('NONFINITE_INPUT')
    return a


def norm(x):
    a = np.asarray(x, dtype=float)
    scale = float(np.max(np.abs(a))) if a.size else 0.
    value = float(scale*np.linalg.norm(a/scale)) if scale else 0.
    if not np.isfinite(value):
        raise ValueError('NORM_RANGE')
    return value


def close(a, b, label, reference=0.):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError(label)
    error = norm(a-b)/max(norm(a), norm(b), reference, np.finfo(float).tiny)
    if error > 2e-9:
        raise ValueError(label)
    return error


def matched_pair(grams, holes, rhs):
    """Apply the new raw-data estimator and an exact centered decomposition."""
    if any(set(x) != set(NAMES) for x in (grams, holes, rhs)):
        raise ValueError('TWO_MATCHED_REGIONS_REQUIRED')
    g = {k:arr(grams[k], 2) for k in NAMES}
    c = {k:arr(holes[k], 2) for k in NAMES}
    b = {k:arr(rhs[k], 1) for k in NAMES}
    n = b[NAMES[0]].size
    if not 1 <= n <= 64 or any(g[k].shape != (n,n) or c[k].shape != (n,n) or b[k].shape != (n,) for k in NAMES):
        raise ValueError('MOMENT_SHAPE_RAW_VECTOR_ONLY')
    scale = max(norm(x) for x in g.values())
    if not scale:
        raise ValueError('ZERO_GRAM')
    slack = 512*np.finfo(float).eps*scale
    if any(norm(x-x.T) > slack for x in (*g.values(), *c.values())):
        raise ValueError('ASYMMETRIC_MOMENT')
    g = {k:(v+v.T)/2 for k,v in g.items()}
    c = {k:(v+v.T)/2 for k,v in c.items()}
    h = {k:g[k]-c[k] for k in NAMES}
    for x in (c[NAMES[0]], c[NAMES[1]], c[NAMES[0]]-c[NAMES[1]],
              g[NAMES[0]]-g[NAMES[1]], h[NAMES[0]]-h[NAMES[1]]):
        if np.linalg.eigvalsh(x)[0] < -slack:
            raise ValueError('NON_NESTED_BINARY_MOMENTS')
    old, new, response, controls = {}, {}, {}, {}
    for k in NAMES:
        for matrix in (g[k], h[k]):
            ev = np.linalg.eigvalsh(matrix)
            if ev[0] <= slack or ev[-1]/ev[0] > 1e8:
                raise ValueError('GRAM_NOT_IDENTIFIABLE')
        old[k] = np.linalg.solve(g[k], b[k])
        new[k] = np.linalg.solve(h[k], b[k])
        response[k] = np.linalg.solve(g[k], h[k])
        transform = np.linalg.solve(h[k], g[k])
        close(response[k]@new[k], old[k], 'RESPONSE_IDENTITY')
        close(h[k]@new[k], b[k], 'NORMAL_EQUATION', norm(h[k])*norm(new[k]))
        controls[k] = {'condition': float(np.linalg.cond(h[k], 2)),
                       'old_to_matched_gain': float(np.linalg.norm(transform, 2))}
    kc, kt = NAMES
    d0 = old[kt]-old[kc]
    d1 = new[kt]-new[kc]
    part1 = (response[kt]-response[kc])@((new[kt]+new[kc])/2)
    part2 = ((response[kt]+response[kc])/2)@d1
    error = close(d0, part1+part2, 'CENTERED_CONTRAST_IDENTITY', norm(old[kt])+norm(old[kc]))
    return {'original':old, 'matched':new, 'responses':response, 'controls':controls,
            'original_contrast':d0, 'matched_contrast':d1,
            'response_difference_on_mean_fit':part1,
            'mean_response_on_fit_difference':part2, 'closure_relative':error}


def analyze(native_path, injection_path):
    import l01_native_residual_visibility as previous
    import l01_windowed_low_injections as injection
    if previous.digest(previous.native.__file__) != previous.PRODUCER_SHA256 or previous.digest(injection.__file__) != INJECTION_SHA:
        raise ValueError('UNSUPPORTED_DEPENDENCY_BYTES')
    old, old_sha = previous.read_report(native_path)
    check, injection_sha = previous.read_report(injection_path)
    previous.analyze_report(old)
    expected = {'schema':injection.SCHEMA, 'status':'PASS_FINITE_LOW_SOURCE_WINDOW_RESPONSE',
                'native_report_sha256':old_sha, 'source_window_sha256':old['native_window_sha256'],
                'native_receipt_sha256':previous.NATIVE_RECEIPT_SHA,
                'code_sha256':INJECTION_SHA, 'nside':old['nside'],
                'input_ells':[2,3,4,5], 'output_ells':[2,3,4,5],
                'source_model':'INJECTED_DELIVERED_LOW_BAND_FIELD_A_C_NOT_MEASURED_COSMIC_COEFFICIENTS',
                'original_estimator_changed':False, 'matched_control_applied_to_observed_data':False,
                'paper_gate':'NOT_READY_TO_SUBMIT'}
    if any(check.get(k) != v for k,v in expected.items()):
        raise ValueError('REPORT_SOURCE_BINDING_MISMATCH_NOT_DATA_CORRUPTION_CLAIM')
    g = {k:arr(old['solver_states'][k]['gram'],2) for k in NAMES}
    b = {k:arr(old['solver_states'][k]['rhs'],2)[:,0] for k in NAMES}
    c = check['hole_moments']
    replay = injection.response_from_holes(g,c)
    for k in NAMES:
        close(replay['responses'][k],check['responses'][k],'ARCHIVED_RESPONSE_MISMATCH')
    close(replay['difference'],check['two_mask_difference'],'ARCHIVED_DIFFERENCE_MISMATCH')
    result = matched_pair(g,c,b)
    for k in NAMES:
        close(result['original'][k],arr(old['solver_states'][k]['coefficients'],2)[:,0],'RAW_RHS_REPLAY_MISMATCH')
    summary = {}
    for name, ix in previous.groups().items():
        d0, d1 = result['original_contrast'][ix], result['matched_contrast'][ix]
        a, b = result['response_difference_on_mean_fit'][ix], result['mean_response_on_fit_difference'][ix]
        summary[name] = {'original_contrast_norm_K_CMB':norm(d0),
                         'matched_contrast_norm_K_CMB':norm(d1),
                         'estimator_change_norm_K_CMB':norm(d1-d0),
                         'matched_over_original_norm':norm(d1)/norm(d0) if norm(d0) else None,
                         'centered_term1_energy_K_CMB2':float(a@a),
                         'centered_term2_energy_K_CMB2':float(b@b),
                         'centered_interference_K_CMB2':float(2*(a@b))}
    def plain(x):
        if isinstance(x,np.ndarray): return x.tolist()
        if isinstance(x,dict): return {k:plain(v) for k,v in x.items()}
        return x
    return {'schema':'htt.L01_matched_raw_window_fit/1', 'status':'PASS_MATCHED_RAW_WINDOW_FIT',
            'product':old['product'], 'units':'K_CMB', 'components':summary,
            'estimates':plain(result), 'native_report_sha256':old_sha,
            'injection_report_sha256':injection_sha, 'source_sha256':old['source']['sha256'],
            'new_estimator_not_correction_of_old':True,
            'centered_terms_are_causal_sources':False, 'reconstructed_or_residual_RHS_used':False,
            'native_maps_replayed':False, 'physical_EB_recovered':False,
            'noise_covariance':None, 'p_value':None, 'paper_gate':'NOT_READY_TO_SUBMIT'}


def self_test():
    a = np.array([[1.,0.],[0.,1.],[1.,1.],[1.,-1.]])
    masks = [np.ones(4,dtype=bool),np.array([1,1,0,1],dtype=bool)]
    w = masks[1]; v = np.array([2.,3.,9.,-4.])
    g = {k:a[q].T@a[q] for k,q in zip(NAMES,masks)}
    c = {k:a[q&~w].T@a[q&~w] for k,q in zip(NAMES,masks)}
    b = {k:a[q].T@(w*v)[q] for k,q in zip(NAMES,masks)}
    r = matched_pair(g,c,b)
    for k,q in zip(NAMES,masks):
        np.testing.assert_allclose(r['matched'][k],np.linalg.lstsq(a[q&w],v[q&w],rcond=None)[0],rtol=1e-13,atol=1e-14)
    np.testing.assert_allclose(r['original_contrast'],[5/3,5/3])
    np.testing.assert_allclose(r['matched_contrast'],[0.,0.],atol=1e-14)
    print('PASS_MANUFACTURED_MATCHED_FIT_NOT_NATIVE_DATA')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-report'); ap.add_argument('--injection-report'); ap.add_argument('--out')
    ap.add_argument('--self-test',action='store_true')
    args = ap.parse_args()
    if args.self_test:
        self_test(); return 0
    if not all((args.native_report,args.injection_report,args.out)):
        ap.error('--native-report, --injection-report and --out are required')
    try:
        import l01_native_residual_visibility as previous
        result = analyze(args.native_report,args.injection_report)
        result['analysis_code_sha256'] = previous.digest(__file__)
        previous.write_new(args.out,result)
        print(json.dumps({'status':result['status'],'components':result['components'],
                          'controls':result['estimates']['controls'],'out':args.out,
                          'paper_gate':result['paper_gate']},indent=2,allow_nan=False))
    except (ValueError,OSError,ImportError,KeyError,TypeError,OverflowError,FloatingPointError,np.linalg.LinAlgError) as exc:
        print(json.dumps({'status':'BLOCKED','error':str(exc)})); return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
