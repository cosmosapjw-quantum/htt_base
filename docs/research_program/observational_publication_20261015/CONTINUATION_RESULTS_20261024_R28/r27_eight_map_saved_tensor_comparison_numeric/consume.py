"""One GO-bound saved-carrier computation. No raw map access or native projection."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
MAPS = ('30', '44', '70', '100', '143', '217', '353', 'SMICA')
TARGETS = ('44', '70', '100', '217', 'SMICA')
TENSORS = ('E2', 'E3', 'B2', 'B3')
BLOCKS = ((0, 5), (5, 12), (12, 17), (17, 24))
SHAPES = ((3, 3), (3, 3, 3), (3, 3), (3, 3, 3))


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for part in iter(lambda: f.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def require(condition, code):
    if not condition:
        raise RuntimeError(code)


def sealed(ref):
    path = Path(ref['path'])
    require(path.stat().st_size == ref['bytes'] and sha(path) == ref['sha256'],
            'SEALED_INPUT_DRIFT:' + str(path))
    return path


def finite(a, shape, name):
    a = np.asarray(a)
    require(a.shape == shape and a.dtype.kind in 'fiu' and np.isfinite(a).all(),
            'NONFINITE_OR_LAYOUT:' + name)
    return a


def close(a, b, atol=1e-12, rtol=1e-9):
    return np.all(np.abs(a - b) <= atol + rtol * np.abs(b))


def tensor_checks(t, ell, name):
    if ell == 2:
        require(np.array_equal(t, np.swapaxes(t, -1, -2)) or
                close(t, np.swapaxes(t, -1, -2)), 'STF_SYMMETRY:' + name)
        require(close(np.trace(t, axis1=-2, axis2=-1), 0), 'STF_TRACE:' + name)
    else:
        require(close(t, np.swapaxes(t, -1, -2)) and
                close(t, np.swapaxes(t, -2, -3)), 'STF_SYMMETRY:' + name)
        for a, b in ((0, 1), (0, 2), (1, 2)):
            require(close(np.trace(t, axis1=a, axis2=b), 0),
                    'STF_TRACE:' + name)


def load_decoder(ref):
    path = sealed(ref)
    import sys
    sys.path.insert(0, str(REPO / 'htt'))
    sys.path.insert(0, str(REPO / 'htt' / 'src'))
    spec = importlib.util.spec_from_file_location('sealed_full7_math_for_saved8', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(Path(module.__file__).resolve() == path.resolve(), 'MATH_IMPORT_DRIFT')
    return module


def synthetic_controls():
    a = np.zeros((12, 2)); a[0, 0] = 1e-5; a[1, 1] = 2e-5
    b = np.zeros((12, 2)); b[0, 0] = 3e-6; b[1, 1] = -4e-6
    y = a @ np.array([2., -1.]); btarget = b @ np.array([2., -1.]) + 7e-8
    c = np.linalg.lstsq(a, y, rcond=None)[0]
    require(close(c, [2., -1.], 1e-12, 1e-9), 'SYNTHETIC_E_FIT')
    require(np.array_equal(c, np.linalg.lstsq(a, y, rcond=None)[0]) and
            not np.array_equal(btarget, btarget + 1e-7), 'B_INVARIANCE')
    outer = np.multiply.outer(np.r_[y, btarget], np.r_[y, btarget])
    require(outer[1, 12] != 0 and outer[12, 1] != 0 and outer[1, 12] < 0,
            'SYNTHETIC_SIGNED_MIXED_TERM')
    bad = a.copy(); bad[:, 1] = 2 * bad[:, 0]
    s = np.linalg.svd(bad, compute_uv=False)
    prediction = None if s[0] == 0 or s[1] / s[0] <= 1e-8 else b @ np.linalg.lstsq(bad, y, rcond=None)[0]
    require(prediction is None, 'RANK_BRANCH')
    return ['synthetic_signed_mixed_term', 'E_fit_invariant_under_B_change', 'rank_deficiency_absent_prediction']


def figure_signed(c, labels, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    scale = float(np.max(np.abs(c)))
    require(math.isfinite(scale) and scale > 0, 'FIGURE_SCALE')
    fig, ax = plt.subplots(figsize=(16, 6), constrained_layout=True)
    image = ax.imshow(c, cmap='RdBu_r', vmin=-scale, vmax=scale, aspect='auto')
    ax.set_yticks(range(8), [f'{x} GHz' if x != 'SMICA' else 'SMICA benchmark' for x in MAPS])
    ax.set_xticks(range(24), labels, rotation=75, ha='right', fontsize=7)
    ax.set_title('Eight delivered-map signed carriers; SMICA is component separation')
    fig.colorbar(image, ax=ax, label='K_CMB')
    fig.savefig(out / 'signed24.png', dpi=150); plt.close(fig)


def figure_heldout(target, pred, resid, labels, valid, out):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(5, 1, figsize=(14, 14), sharex=True, constrained_layout=True)
    x = np.arange(12)
    for k, name in enumerate(TARGETS):
        ax = axes[k]; ax.axhline(0, lw=.7, color='.5')
        ax.plot(x, target[k], 'o-', label='143-relative target B')
        if valid[k]:
            ax.plot(x, pred[k], 's--', label='E-fit B prediction')
            ax.plot(x, resid[k], 'x:', label='target minus prediction')
        else:
            ax.text(.01, .8, 'ANCHOR_FIT_ILL_CONDITIONED; prediction absent', transform=ax.transAxes)
        ax.set_ylabel(name + '\nK_CMB'); ax.legend(fontsize=7, ncol=3)
    axes[-1].set_xticks(x, labels[12:], rotation=60, ha='right')
    fig.suptitle('All signed heldout B coordinates; algorithmic descriptive comparison')
    fig.savefig(out / 'heldout_B12.png', dpi=150); plt.close(fig)


def figure_cross(g, h, out):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(14, 9), constrained_layout=True)
    for ax, title, m in zip(axes.flat, ('G E2', 'G E3', 'G B2', 'G B3', 'H ell2 E/B', 'H ell3 E/B'),
                            (*g, *h)):
        scale = float(np.max(np.abs(m))) or 1.
        im = ax.imshow(m, cmap='RdBu_r', vmin=-scale, vmax=scale)
        ax.set_title(title + ' deterministic product')
        ax.set_xticks(range(8), MAPS, rotation=45, ha='right', fontsize=7)
        ax.set_yticks(range(8), MAPS, fontsize=7)
        fig.colorbar(im, ax=ax, label='K_CMB²')
    fig.savefig(out / 'cross_terms.png', dpi=150); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', required=True); ap.add_argument('--output', required=True)
    args = ap.parse_args()
    input_path = Path(args.input)
    inp = json.loads(input_path.read_text())
    from threadpoolctl import threadpool_info
    pools = threadpool_info()
    require(all(p.get('num_threads') == 1 for p in pools), 'LOADED_THREADPOOL_NOT_SINGLE_THREAD')
    require(inp['task_id'] == 'R27-EIGHT-MAP-SAVED-TENSOR-COMPARISON', 'TASK_ID')
    require(inp['source_sha256']['consume.py'] == sha(Path(__file__)), 'SOURCE_DRIFT')
    contract = json.loads(sealed(inp['contract']).read_text())
    require(contract['task_id'] == inp['task_id'] and contract['method']['map_order'] == list(MAPS), 'CONTRACT_DRIFT')
    refs = inp['frozen_inputs']
    for ref in refs.values(): sealed(ref)
    old_math = load_decoder(refs['saved_math'])
    old = json.loads(Path(refs['seven_descriptive']['path']).read_text())
    require(old['selected_support_count'] == 30021 and old['S7_equals_S4_observed'] is True,
            'SEVEN_SUPPORT_METADATA')
    require(old['SMICA_status'] == 'OPTIONAL_COMPARATOR_NOT_DELIVERED_FAILED_ONE_USE',
            'HISTORICAL_SMICA_STATUS_DRIFT')
    require(json.loads(Path(refs['smica_review_result']['path']).read_text())['numerical_component_decision'] ==
            'CONDITIONAL_PASS_EXACT_RELEASED_PRODUCT_DELIVERED_MAP_ONLY_FOR_REUSE', 'SMICA_REUSE_NOT_QUALIFIED')
    controls = synthetic_controls()
    with np.load(refs['seven_carrier']['path'], allow_pickle=False) as s, \
         np.load(refs['smica_carrier']['path'], allow_pickle=False) as sm, \
         np.load(refs['support']['path'], allow_pickle=False) as support:
        require(set(s.files) == {'bands_GHz','frequency_canonical_7x24','reference143_bands_GHz',
                'reference143_contrasts_6x24','coordinate_labels','E2_stf','E3_stf','B2_stf','B3_stf',
                's7_support_ring64','anchor_E','anchor_B','target_bands_GHz','target_E','target_B',
                'coefficients_E_fit','prediction_B','residual_E','residual_B','prediction_valid'}, 'FULL7_KEYS')
        require(set(sm.files) == {'canonical24','E2','E3','B2','B3'}, 'SMICA_KEYS')
        require(list(s['bands_GHz']) == [30,44,70,100,143,217,353] and
                list(s['target_bands_GHz']) == [44,70,100,217], 'OLD_ORDER')
        labels = s['coordinate_labels'].astype(str)
        require(labels.shape == (24,) and list(labels) == old['coordinate_labels'], 'COORDINATE_LABELS')
        c7 = finite(s['frequency_canonical_7x24'], (7,24), 'FULL7')
        c8 = finite(sm['canonical24'], (24,), 'SMICA')
        require(np.array_equal(c7, np.asarray(old['frequency_canonical_7x24_K_CMB'])), 'SEVEN_JSON_CARRIER')
        require(np.array_equal(s['reference143_contrasts_6x24'],
                np.asarray(old['reference143_contrasts_6x24_K_CMB'])), 'SEVEN_JSON_CONTRAST')
        support_ix = s['s7_support_ring64']
        mask = support['s7_mask_ring64'].astype(bool)
        require(support_ix.shape == (30021,) and np.array_equal(support_ix, np.flatnonzero(mask)) and
                np.array_equal(mask, support['selected_mask_ring64'].astype(bool)), 'SUPPORT_DRIFT')
        c = np.vstack((c7, c8))
        tensors = {}
        for name, shape, ell in zip(TENSORS, SHAPES, (2,3,2,3)):
            old_t = finite(s[name+'_stf'], (7,)+shape, 'FULL7_'+name)
            new_t = finite(sm[name], shape, 'SMICA_'+name)
            require(np.array_equal(old_t, np.asarray(old[name+'_stf'])), 'SEVEN_JSON_STF_'+name)
            t = np.concatenate((old_t, new_t[None]), axis=0)
            for i in range(8):
                tensor_checks(t[i], ell, name+MAPS[i])
                expected = old_math.decode_stf(c[i], REPO)[TENSORS.index(name)]
                require(close(t[i], expected), 'STF_DECODER_PARITY:'+name+MAPS[i])
            tensors[name] = t
        ae = finite(s['anchor_E'], (12,2), 'AE'); ab = finite(s['anchor_B'], (12,2), 'AB')
        require(np.array_equal(ae, np.asarray(old['crossprediction']['anchor_E_12x2_K_CMB'])) and
                np.array_equal(ab, np.asarray(old['crossprediction']['anchor_B_12x2_K_CMB'])), 'OLD_ANCHOR_JSON')
        d143 = c - c[4]
        dsm = c - c[7]
        require(np.array_equal(d143[[0,1,2,3,5,6]], s['reference143_contrasts_6x24']), 'OLD_D143')
        require(np.array_equal(ae, np.column_stack((d143[0,:12], d143[6,:12]))) and
                np.array_equal(ab, np.column_stack((d143[0,12:], d143[6,12:]))), 'FIXED_ANCHORS')
        old_target = finite(s['target_B'], (4,12), 'OLD_TARGET_B')
        old_pred = finite(s['prediction_B'], (4,12), 'OLD_PRED_B')
        old_resid = finite(s['residual_B'], (4,12), 'OLD_RESID_B')
        old_e = finite(s['target_E'], (4,12), 'OLD_TARGET_E')
        old_re = finite(s['residual_E'], (4,12), 'OLD_RESID_E')
        old_coef = finite(s['coefficients_E_fit'], (4,2), 'OLD_COEF')
        old_valid = s['prediction_valid'].astype(bool)
        require(old_valid.shape == (4,) and old_valid.all(), 'OLD_FIT_VALIDITY')
        require(np.array_equal(old_e, d143[[1,2,3,5],:12]) and
                np.array_equal(old_target, d143[[1,2,3,5],12:]), 'OLD_TARGET_IDENTITY')
        for k, key in enumerate(TARGETS[:4]):
            row = old['crossprediction']['targets'][key]
            for arr, field in ((old_coef[k], 'coefficients'), (old_pred[k], 'B_prediction_12_K_CMB'),
                               (old_re[k], 'E_residual_12_K_CMB'), (old_resid[k], 'B_residual_12_K_CMB')):
                require(np.array_equal(arr, np.asarray(row[field])), 'OLD_FIT_JSON:'+key+field)
        singular = np.linalg.svd(ae, compute_uv=False)
        ratio = float(singular[1]/singular[0]) if singular[0] > 0 else 0.
        require(close(singular, old['crossprediction']['singular_values_K_CMB'], 1e-15, 1e-12) and
                abs(ratio - old['crossprediction']['s2_over_s1']) < 1e-12, 'SINGULAR_DRIFT')
        rank_ok = ratio > 1e-8
        target_e = np.vstack((old_e, d143[7,:12]))
        target_b = np.vstack((old_target, d143[7,12:]))
        dt = {name: t - t[4] for name,t in tensors.items()}
        ds = {name: t - t[7] for name,t in tensors.items()}
        o = c[:,None,:,None] * c[None,:,None,:]
        g = np.stack([c[:,a:b] @ c[:,a:b].T for a,b in BLOCKS])
        h = np.stack([c[:,a:b] @ c[:,12+a:12+b].T for a,b in ((0,5),(5,12))])
        require(o.shape == (8,8,24,24) and np.array_equal(o, o.transpose(1,0,3,2)) and
                g.shape == (4,8,8) and h.shape == (2,8,8), 'CROSS_LAYOUT')
        # All old fit values are copied, never recomputed. No NaN placeholder is serialized.
        arrays = dict(map_ids=np.asarray(MAPS), coordinate_labels=labels, C=c,
                      support_ring64=support_ix, D143=d143, DSMICA=dsm,
                      anchor_E=ae, anchor_B=ab, target_ids=np.asarray(TARGETS),
                      target_E=target_e, target_B=target_b, O=o, G=g, H=h,
                      singular_values=singular, singular_ratio=np.asarray(ratio),
                      prediction_valid=np.r_[old_valid, rank_ok])
        for name in TENSORS:
            arrays[name+'_stf'] = tensors[name]
            arrays['D143_'+name+'_stf'] = dt[name]
            arrays['DSMICA_'+name+'_stf'] = ds[name]
        result = {'schema':'htt.eight_map_saved_tensor_descriptive/1', 'task_id':inp['task_id'],
                  'map_ids':list(MAPS), 'coordinate_labels':labels.tolist(), 'unit':'K_CMB',
                  'carrier_8x24_K_CMB':c.tolist(), 'D143_8x24_K_CMB':d143.tolist(),
                  'DSMICA_8x24_K_CMB':dsm.tolist(), 'target_ids':list(TARGETS),
                  'target_B_5x12_K_CMB':target_b.tolist(),
                  'anchor_E_12x2_K_CMB':ae.tolist(), 'anchor_B_12x2_K_CMB':ab.tolist(),
                  'singular_values_K_CMB':singular.tolist(), 'singular_ratio':ratio,
                  'G_4x8x8_K_CMB2':g.tolist(), 'H_2x8x8_K_CMB2':h.tolist(),
                  'cross_outer':'FULL8_COMPARISON.npz:O; uncentered deterministic K_CMB^2, not covariance',
                  'old_four_target_rows':old['crossprediction']['targets'],
                  'old_seven_frequency_image':old['computational_frequency_image'],
                  'historical_smica_resource_status':'HOLD_ORIGINAL_TIMING_CAP_EVIDENCE_UNAVAILABLE',
                  'original_full8_status':'HOLD_NATIVE_FIRST_FAILURE',
                  'scientific_admission':'HOLD', 'null_calibration':'ABSENT',
                  'loaded_threadpools':pools,
                  'interpretation':'Finite delivered-map signed coordinates on S7; algorithmic E-to-B holdout only. Shared sky, mask leakage, different response and cross-map noise are unmodelled. SMICA is a component-separation benchmark, not a GHz frequency or ground truth.',
                  'checks':controls+['sealed_small_inputs','saved_seven_exact_reuse','decoder_STF_symmetry_trace','both_signed_contrasts','cross_outer_layout']}
        if rank_ok:
            alpha = np.linalg.lstsq(ae, target_e[4], rcond=None)[0]
            pe = ae @ alpha; pb = ab @ alpha
            re = target_e[4]-pe; rb = target_b[4]-pb
            arrays['coefficients_E_fit'] = np.vstack((old_coef,alpha))
            arrays['prediction_B'] = np.vstack((old_pred,pb))
            arrays['residual_E'] = np.vstack((old_re,re))
            arrays['residual_B'] = np.vstack((old_resid,rb))
            arrays['SMICA_absolute_prediction_B'] = c[4,12:]+pb
            for name in ('B2','B3'):
                k = 2 if name == 'B2' else 3
                predicted = old_coef[:,0,None,None] * dt[name][0] + old_coef[:,1,None,None] * dt[name][6] if k == 2 else old_coef[:,0,None,None,None] * dt[name][0] + old_coef[:,1,None,None,None] * dt[name][6]
                sm_pred = alpha[0]*dt[name][0] + alpha[1]*dt[name][6]
                predicted = np.concatenate((predicted,sm_pred[None]),axis=0)
                arrays['prediction_'+name+'_stf'] = predicted
                arrays['residual_'+name+'_stf'] = dt[name][[1,2,3,5,7]]-predicted
                arrays['SMICA_absolute_prediction_'+name+'_stf'] = tensors[name][4]+sm_pred
                for krow, vec in enumerate(arrays['prediction_B']):
                    q = np.r_[np.zeros(12),vec]
                    decoded = old_math.decode_stf(q,REPO)[TENSORS.index(name)]
                    require(close(predicted[krow],decoded), 'PREDICTED_STF_DECODE:'+name+TARGETS[krow])
            result['SMICA_fit']={'conditioning':'RANK2_DESCRIPTIVE','alpha':alpha.tolist(),
                                'target_E_12_K_CMB':target_e[4].tolist(),
                                'target_B_12_K_CMB':target_b[4].tolist(),
                                'prediction_B_12_K_CMB':pb.tolist(),
                                'absolute_prediction_B_12_K_CMB':arrays['SMICA_absolute_prediction_B'].tolist(),
                                'residual_E_12_K_CMB':re.tolist(), 'residual_B_12_K_CMB':rb.tolist()}
            result['all_five_B_prediction_5x12_K_CMB']=arrays['prediction_B'].tolist()
            result['all_five_B_residual_5x12_K_CMB']=arrays['residual_B'].tolist()
            result['checks'].append('new_SMICA_E_only_fit')
        else:
            result['SMICA_fit']={'conditioning':'ANCHOR_FIT_ILL_CONDITIONED','prediction':None}
    out = Path(args.output); out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(out/'FULL8_COMPARISON.npz',**arrays)
    figure_signed(c,labels,out)
    figure_heldout(target_b,arrays.get('prediction_B'),arrays.get('residual_B'),labels,
                   arrays['prediction_valid'],out)
    figure_cross(g,h,out)
    # Actual output readback is mandatory for this new numerical candidate.
    with np.load(out/'FULL8_COMPARISON.npz',allow_pickle=False) as check:
        require(set(check.files)==set(arrays) and np.array_equal(check['C'],c) and
                np.array_equal(check['G'],g) and np.array_equal(check['H'],h), 'OUTPUT_NPZ_READBACK')
        if rank_ok:
            require(np.array_equal(check['prediction_B'],np.asarray(result['all_five_B_prediction_5x12_K_CMB'])), 'NPZ_JSON_PARITY')
    for name in ('signed24.png','heldout_B12.png','cross_terms.png'):
        require((out/name).stat().st_size>1000,'FIGURE_MISSING:'+name)
    (out/'DESCRIPTIVE_RESULT.json').write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n')
    sm = result['SMICA_fit']
    report = ('# Eight saved-carrier descriptive comparison\n\n'
              'Eight signed 24-coordinate delivered-map rows share the selected 30,021-cell support. SMICA is a component-separation benchmark. Both 143-relative and SMICA-relative complete signed contrasts, complete STF tensors, and deterministic coordinate products are saved.\n\n'
              f"Fixed 30/353 E anchors relative to 143 have singular ratio {ratio:.17g}. "
              + (f"The SMICA E-only coefficients are {sm['alpha']}; its complete B residual norm is {float(np.linalg.norm(arrays['residual_B'][4])):.17g} K_CMB.\n\n" if rank_ok else 'The anchor fit is ill conditioned, so its B prediction is absent.\n\n')
              + 'G and H are signed contractions of observed finite coordinates; O is an uncentered outer product, not estimated covariance. The B comparison is algorithmic and has no null calibration. Different map response, masked-sky leakage, shared sky, and cross-map noise remain unmodelled. The original SMICA timing/resource HOLD and original full8 failure persist. No native solver, physical F/MES, calibrated Pi, true-sky E/B, or family claim follows.\n')
    (out/'REPORT.md').write_text(report)
    print(json.dumps({'status':'CANDIDATE_PENDING_INDEPENDENT_CHECK_AND_REVIEW','files':sorted(p.name for p in out.iterdir())}),flush=True)


if __name__=='__main__': main()
