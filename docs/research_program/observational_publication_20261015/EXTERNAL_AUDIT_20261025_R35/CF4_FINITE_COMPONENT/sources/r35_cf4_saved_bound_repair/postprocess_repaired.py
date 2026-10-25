"""Saved-artifact-only CF4 bound repair. Requires fresh controller ACK/GO.

No producer, background, Bessel, window, or FINUFFT evaluation occurs here.
Outputs are correction sidecars; the reviewed candidate is never overwritten.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import time

import numpy as np

BASE = Path('/mnt/extdrive/workdir/htt_open_data')
SOURCE = BASE / 'r30_cf4_pv_tensor_numeric/fast_window_fixture_repair'
RUN = SOURCE / 'actual_run'
OUT = Path(__file__).resolve().parent
REVIEW = BASE / 'r32_cf4_fresh_scientific_review'
EXPECTED = {
    'review': 'f52aa5f6a7fd9aa858a7e689be2dbd9d150c7ee07e9ac79659f596268357f267',
    'result': 'ae5d4a97c433c998e5777e6c4372ccb3dd3f800d29d5a52576fc183ea2fc5985',
    'source': '5caaa72323858622bc1b3bd62159ba67e527f4204a73871ee310181be542c82f',
}
U = 2.0**-53
TINY = np.nextafter(0., 1.)
AMP = 765245.0820764016
DIRECT_NAMES = (
    'o35_b0_k0x1.acd9661a17d9ep-7.npz',
    'o35_b0_k0x1.b6450588a5f25p-7.npz',
    'o35_b0_k0x1.b97353b4b2faap-7.npz',
)


def require(ok, message):
    if not bool(ok):
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def load(path):
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def upward(x):
    return np.nextafter(x, np.inf)


def upmul(a, b):
    """Outward product of nonnegative binary64 values; fail on underflow."""
    aa=np.asarray(a); bb=np.asarray(b)
    require(np.all(np.isfinite(aa)) and np.all(np.isfinite(bb)) and
            np.all(aa>=0) and np.all(bb>=0), 'POSITIVE_PRODUCT_DOMAIN')
    value=aa*bb
    require(np.all(np.isfinite(value)), 'POSITIVE_PRODUCT_OVERFLOW')
    require(not np.any((aa!=0)&(bb!=0)&(value==0)), 'POSITIVE_PRODUCT_UNDERFLOW_HOLD')
    return np.where(value==0,0,upward(value))


def upadd(a, b):
    """Outward sum of nonnegative binary64 values."""
    aa=np.asarray(a); bb=np.asarray(b)
    require(np.all(np.isfinite(aa)) and np.all(np.isfinite(bb)) and
            np.all(aa>=0) and np.all(bb>=0), 'POSITIVE_SUM_DOMAIN')
    value=aa+bb
    require(np.all(np.isfinite(value)), 'POSITIVE_SUM_OVERFLOW')
    return np.where(value==0,0,upward(value))


def dot3_up(left, right):
    """Every product and addition in a three-component positive dot is outward."""
    return upadd(upadd(upmul(left[...,0,None],right[0]),
                       upmul(left[...,1,None],right[1])),
                 upmul(left[...,2,None],right[2]))


def positive_reduce_up(terms, axis, count):
    """Nonnegative sum: <= count-1 additions, enclosed by gamma_(count+2)."""
    require(np.all(np.isfinite(terms)) and np.all(terms>=0), 'POSITIVE_REDUCTION_DOMAIN')
    total=np.sum(terms,axis=axis)
    require(np.all(np.isfinite(total)), 'POSITIVE_REDUCTION_OVERFLOW')
    require(not np.any((total==0)&np.any(terms!=0,axis=axis)),
            'POSITIVE_REDUCTION_UNDERFLOW_HOLD')
    return upmul(total,upadd(1.,gamma(count+2)))


def gamma(n):
    v = n * U
    require(v < 1, 'GAMMA_DOMAIN')
    return math.nextafter(v / (1-v), math.inf)


def rational_up(q):
    """Small exact positive dyadic sum to an upward binary64 enclosure."""
    require(q >= 0, 'NEGATIVE_ABSOLUTE_SUM')
    v = float(q)
    require(math.isfinite(v), 'ABSOLUTE_SUM_OVERFLOW')
    return math.nextafter(v, math.inf) if Fraction.from_float(v) < q else v


def validate_sources():
    preparation=json.loads((OUT/'PREPARATION.json').read_text())
    for item in preparation['frozen_reads']:
        require(digest(Path(item['path'])) == item['sha256'],
                'PREPARATION_SOURCE_DRIFT '+item['path'])
    paths = {'review': REVIEW/'RESULT.json', 'result': RUN/'RESULT.json',
             'source': SOURCE/'fast_science.py'}
    for name, path in paths.items():
        require(digest(path) == EXPECTED[name], 'SOURCE_DRIFT '+name)
    raw = json.loads((REVIEW/'RAW_OUTCOME.json').read_text())
    for item in raw['evidence']:
        path = Path(item['path'])
        if path.name in {'PRODUCT.npz','SENSITIVITY.npz','TARGETS.npz',
                         'EXACT_REFERENCE_SUMS.json','STAGE_A.npz','STAGE_B.npz',
                         'STAGE_C.npz','DIRECT_CONTROLS.json'}:
            require(digest(path) == item['sha256'], 'FROZEN_ARTIFACT_DRIFT '+path.name)
    result = json.loads(paths['result'].read_text())
    require(result['final_stage'] == 'C' and result['amplitude'] == AMP,
            'CANDIDATE_STAGE_OR_AMPLITUDE')
    return result, raw


def corrected_roundoff(target, product, factor, exact, high, old_roundoff):
    L = factor['L_binary64']; nr = factor['nonreference_row_index']; refs = factor['difference_reference_row_index']
    jg = product['j'] * product['g']; n = product['n_J2000']; b = jg[:,None] * n
    require(L.shape == (5,len(nr)) and len(nr) == len(refs) == 35019,
            'FIXED_OPERATOR_SHAPE')
    require(np.all(np.isfinite(b)) and np.all(np.isfinite(L)), 'NONFINITE_COEFFICIENT_INPUT')
    require(not np.any((b == 0) & (jg[:,None] != 0) & (n != 0)),
            'SOURCE_VECTOR_UNDERFLOW_HOLD')
    unique = np.unique(refs)
    evidence = exact['sums']; require(len(unique) == 6 and len(evidence) == 5,
                                      'REFERENCE_COUNT')
    scales = np.empty((5,3)); witness = None
    term_count = max(sum(len(evidence[a][h]['expansion_hex']) for h in range(6)) for a in range(5))
    for a in range(5):
        for d in range(3):
            total = Fraction()
            for h,row in enumerate(unique):
                entry = evidence[a][h]
                require(entry['row'] == int(row), f'REFERENCE_MAPPING a={a} h={h}')
                numerator = int(entry['numerator_at_2_minus_1074'])
                expansion = [float.fromhex(v) for v in entry['expansion_hex']]
                require(sum((Fraction.from_float(v) for v in expansion), Fraction()) ==
                        Fraction(numerator, 1<<1074), f'EXPANSION_IDENTITY a={a} h={h}')
                for v in expansion:
                    term = abs(Fraction.from_float(v) * Fraction.from_float(float(b[row,d])))
                    total += term
                    if (a,d,h) == (0,1,1) and v.hex() == '0x1.4bc1c2a1a09efp-12':
                        witness = {'a':a,'d':d,'h':h,'catalogue_row':int(row),
                                   'single_abs_term_lower_binary64':float(term),
                                   'single_abs_term_upper_binary64':rational_up(term)}
            scales[a,d] = rational_up(total)
    require(witness is not None and witness['catalogue_row'] == 5937 and
            witness['single_abs_term_lower_binary64'] > 9.6e-7,
            'REVIEW_WITNESS_NOT_REPRODUCED')
    # Each binary64 coefficient product is enclosed upward by one adjacent float;
    # fsum has at most one final rounding, enclosed by one further upward step.
    q = np.empty((5,3))
    for a in range(5):
        for d in range(3):
            x = L[a] * b[nr,d]
            require(np.all(np.isfinite(x)), 'NONFINITE_COEFFICIENT')
            require(not np.any((x == 0) & (L[a] != 0) & (b[nr,d] != 0)),
                    'COEFFICIENT_UNDERFLOW_HOLD')
            q[a,d] = math.nextafter(math.fsum(map(float, upward(abs(x)))), math.inf)
    qsaved = np.asarray(json.loads((RUN/'RESULT.json').read_text())['roundoff']['q_ad'])
    require(np.all(q >= qsaved), 'RECOMPUTED_Q_BELOW_SAVED_Q')
    vec = abs(target[:,1:]); xmax = upward(np.max(abs(product['positions']),axis=0))
    dot = dot3_up(vec,xmax[:,None])[:,0]
    phase = upmul(upmul(upmul(2.,gamma(8)),target[:,0]),dot)
    base = upadd(upmul(gamma(4),q),upmul(gamma(2*term_count+8),scales))
    projection = dot3_up(vec,upadd(q,scales).T)
    raw_corrected = upadd(upadd(dot3_up(vec,base.T),
                                    upmul(phase[:,None],projection)),
                             upadd(upmul(gamma(8),projection),4096*TINY))
    require(np.all(np.isfinite(raw_corrected)) and np.all(raw_corrected>=0),
            'RAW_CORRECTED_ROUNDOFF_INVALID')
    roundoff = upward(np.maximum(raw_corrected,old_roundoff))
    require(np.all(np.isfinite(roundoff)) and np.all(roundoff >= old_roundoff),
            'OPERATIVE_ROUNDOFF_NOT_CONSERVATIVE')
    ratio = projection / np.maximum(abs(high), np.finfo(float).tiny)
    return roundoff, raw_corrected, {'reference_rows':unique.tolist(), 'reference_abs_scales':scales.tolist(),
                      'q_ad_upper':q.tolist(), 'witness':witness,
                      'reference_term_count_max':term_count,
                      'cancellation_ratio_max_finite':float(np.max(ratio[np.isfinite(ratio)])),
                      'cancellation_ratio_nonfinite_count':int(np.sum(~np.isfinite(ratio))),
                      'coefficient_underflow_checked':True,
                      'roundoff_max':float(np.max(roundoff)),
                      'raw_corrected_roundoff_max':float(np.max(raw_corrected)),
                      'old_roundoff_max':float(np.max(old_roundoff))}


def selection(target, high, maps, product, factor):
    """Reconstruct all deterministic direct targets from retained fields."""
    keymap = {tuple(float(v).hex() for v in row):i for i,row in enumerate(target)}
    chosen = set()
    previous = SOURCE.parent/'normalization_repair/actual_run/spectral'
    for name in DIRECT_NAMES:
        z = load(previous/name)
        k = float(z['k'])
        for direction in z['sample_u']:
            key = (k.hex(), *(float(v).hex() for v in direction))
            require(key in keymap, 'SAVED_SAMPLE_TARGET_ABSENT')
            chosen.add(keymap[key])
    for band in maps['A']:
        for k in (band['k'][0],band['k'][-1]):
            for direction in band['directions'][:4]:
                key=(float(k).hex(),*(float(v).hex() for v in direction))
                require(key in keymap, 'ENDPOINT_TARGET_ABSENT')
                chosen.add(keymap[key])
    L=factor['L_binary64'];nr=factor['nonreference_row_index'];refs=factor['difference_reference_row_index']
    n=product['n_J2000'];jg=product['j']*product['g']
    for label in ('A','C'):
        indices=np.unique(np.concatenate([band['indices'].ravel() for band in maps[label]]))
        directions=maps[label][0]['directions']; scales=np.empty((len(directions),5))
        for start in range(0,len(directions),32):
            ub=directions[start:start+32]
            left=abs(jg[nr,None]*(n[nr]@ub.T))
            right=abs(jg[refs,None]*(n[refs]@ub.T))
            scales[start:start+len(ub)]=(abs(L)@(left+right)).T
        lookup={tuple(float(v).hex() for v in u):i for i,u in enumerate(directions)}
        which=np.asarray([lookup[tuple(float(v).hex() for v in target[idx,1:])]
                          for idx in indices])
        for a in range(5):
            magnitude=abs(high[indices,a])
            chosen.add(int(indices[int(np.argmax(magnitude))]))
            scale=scales[which,a]
            score=np.divide(magnitude,scale,out=np.full_like(magnitude,np.inf),where=scale>0)
            chosen.add(int(indices[int(np.argmin(score))]))
    old=json.loads((RUN/'DIRECT_CONTROLS.json').read_text())
    checked={int(row['index']) for row in old['oracle_targets']}
    return {'rederived_count':len(chosen),'direct_checked_count':len(checked),
            'exact_set_equal':chosen==checked,
            'missing_direct_ids':sorted(chosen-checked),
            'extra_direct_ids':sorted(checked-chosen)}


def maps_from_saved(target, stages, inventory):
    # The fixed angular weights/directions are generated only from the frozen
    # Lebedev quadrature rule; no scientific producer calculation is invoked.
    import sys
    sys.path.insert(0,str(SOURCE))
    import science as s
    maps={}
    for label,order in [('A',35),('B',53),('C',53)]:
        _,_,directions,weights=s.angular_rule(order)
        group=[]
        for band in (0,1):
            idx=inventory[f'{label}_band{band}_indices']
            require(idx.shape==(len(stages[label][f'k{band+1}']),len(directions)),
                    'MAP_SHAPE '+label)
            require(np.array_equal(target[idx,1:].view(np.uint64),
                                   np.broadcast_to(directions, target[idx,1:].shape).view(np.uint64)),
                    'MAP_DIRECTION '+label)
            require(np.array_equal(target[idx,0],
                                   np.broadcast_to(stages[label][f'k{band+1}'][:,None],idx.shape)),
                    'MAP_K '+label)
            group.append({'indices':idx,'directions':directions,
                          'weights':weights/(4*math.pi),
                          'k':stages[label][f'k{band+1}'],
                          'radial':stages[label][f'w{band+1}']})
        maps[label]=group
    return s,maps


def spectral_bound(high,err,band):
    z=high[band['indices']]; e=err[band['indices']]; w=band['weights']
    A=np.einsum('t,nta,ntb->nab',w,z,z.conj()).real
    require(np.all(np.isfinite(e)) and np.all(e>=0) and np.all(w>=0),
            'SPECTRAL_BOUND_DOMAIN')
    az=upward(abs(z))
    x=az[:,:,:,None]; y=az[:,:,None,:]
    ex=e[:,:,:,None]; ey=e[:,:,None,:]
    terms=upadd(upadd(upmul(x,ey),upmul(ex,y)),upmul(ex,ey))
    weighted=upmul(terms,w[None,:,None,None])
    B=positive_reduce_up(weighted,axis=1,count=len(w))
    return A,B


def joint_bound(s,band,bounds):
    out=np.zeros((15,15))
    inverse_denominator=upward(1/(2*math.pi**2))
    for k,w,m in zip(band['k'],band['radial'],bounds):
        require(w>=0 and np.all(np.isfinite(m)) and np.all(m>=0),
                'JOINT_BOUND_DOMAIN')
        smooth=upward(np.exp(-.5*(k*s.RADII/s.H)**2))
        radial=upmul(smooth[:,None],smooth[None,:])
        factor=upmul(upmul(float(w),upward(float(s.power(k,AMP)))),inverse_denominator)
        block=upmul(radial[:,:,None,None],m[None,None,:,:]).transpose(0,2,1,3).reshape(15,15)
        out=upadd(out,upmul(factor,block))
    return out


def metrics(stages,bounds):
    reports=[]; allpass=True
    for label in ('A','B','C'):
        for bi in (0,1,2):
            mat=(stages[label]['band1'],stages[label]['band2'],stages[label]['total'])[bi]
            bound=(bounds[label][0],bounds[label][1],bounds[label][0]+bounds[label][1])[bi]
            sd=np.sqrt(np.diag(mat)); require(np.all(sd>0),'NONPOSITIVE_DIAGONAL')
            entry=float(np.max(bound/np.outer(sd,sd)))
            blocks=[];ok=entry<=5e-5
            for r in range(3):
                sl=slice(5*r,5*r+5); x=mat[sl,sl];e=bound[sl,sl]
                eig,vec=np.linalg.eigh(x);keep=eig>1e-10*eig[-1]
                require(np.any(keep),'EMPTY_SUPPORT')
                inv=(vec[:,keep]/np.sqrt(eig[keep]))@vec[:,keep].T
                fro=float(np.linalg.norm(e)/np.linalg.norm(x))
                white=float(np.linalg.norm(abs(inv)@e@abs(inv),2))
                blocks.append({'radius':r,'relative_frobenius':fro,'whitened_spectral':white})
                ok &= fro<=3e-5 and white<=2e-4
            reports.append({'stage':label,'matrix':bi,'max_normalized_entry':entry,
                            'blocks':blocks,'pass':bool(ok)})
            allpass &= ok
    for early,late in [('A','B'),('B','C')]:
        for bi in (0,1,2):
            A=(stages[early]['band1'],stages[early]['band2'],stages[early]['total'])[bi]
            B=(stages[late]['band1'],stages[late]['band2'],stages[late]['total'])[bi]
            EA=(bounds[early][0],bounds[early][1],bounds[early][0]+bounds[early][1])[bi]
            EB=(bounds[late][0],bounds[late][1],bounds[late][0]+bounds[late][1])[bi]
            D=B-A;E=EA+EB;sd=np.sqrt(np.diag(B)); require(np.all(sd>0),'NONPOSITIVE_LATE_DIAGONAL')
            entry=float(np.max((abs(D)+E)/np.outer(sd,sd)));blocks=[];ok=entry<=.005
            for r in range(3):
                sl=slice(5*r,5*r+5);x=B[sl,sl];d=D[sl,sl];e=E[sl,sl]
                eig,vec=np.linalg.eigh(x);old=np.linalg.eigvalsh(A[sl,sl]);ts=(1e-12,1e-10,1e-8)
                ranks=[int(sum(eig>t*eig[-1])) for t in ts];oldr=[int(sum(old>t*old[-1])) for t in ts]
                keep=eig>1e-10*eig[-1]; support=len(set(ranks))==1 and ranks==oldr and np.any(keep)
                if support:
                    inv=(vec[:,keep]/np.sqrt(eig[keep]))@vec[:,keep].T
                    fro=float((np.linalg.norm(d)+np.linalg.norm(e))/np.linalg.norm(x))
                    white=float(np.linalg.norm(inv@d@inv,2)+np.linalg.norm(abs(inv)@e@abs(inv),2))
                else:fro=white=math.inf
                blocks.append({'radius':r,'ranks':ranks,'earlier_ranks':oldr,
                               'relative_frobenius':fro,'whitened_spectral':white,
                               'pass':bool(support and fro<=.003 and white<=.02)})
                ok &= blocks[-1]['pass']
            reports.append({'comparison':early+late,'matrix':bi,'max_normalized_entry':entry,
                            'blocks':blocks,'pass':bool(ok)})
            allpass &= ok
    return reports,bool(allpass)


def main(go_path):
    go=json.loads(Path(go_path).read_text())
    require(go.get('controller_go') is True and go.get('actual_ack') is True and
            go.get('candidate_sha256') == EXPECTED['result'], 'MISSING_FRESH_ACK_GO')
    result,raw=validate_sources()
    inventory=load(RUN/'TARGETS.npz');target=inventory['targets']
    product=load(RUN/'PRODUCT.npz');saved=load(RUN/'SENSITIVITY.npz')
    low=load(RUN/'WINDOWS_EPS_1e-09.npz');high=load(RUN/'WINDOWS_EPS_1e-12.npz')
    require(all(np.array_equal(x['targets'].view(np.uint64),target.view(np.uint64))
                for x in (saved,low,high)), 'TARGET_BYTE_VALUES_DRIFT')
    require(np.array_equal(saved['low'].view(np.uint64),low['window'].view(np.uint64)) and
            np.array_equal(saved['high'].view(np.uint64),high['window'].view(np.uint64)),
            'SAVED_WINDOW_VALUES_DRIFT')
    bindings=json.loads((BASE/'r30_cf4_pv_tensor_framing/INPUT_BINDINGS.json').read_text())
    factor_binding=bindings['immutable_numeric_inputs']['corrected_factor']
    require(digest(Path(factor_binding['path'])) == factor_binding['sha256'],
            'CORRECTED_FACTOR_DRIFT')
    factor=load(Path(factor_binding['path']))
    exact=json.loads((RUN/'EXACT_REFERENCE_SUMS.json').read_text())
    roundoff,raw_corrected,meta=corrected_roundoff(
        target,product,factor,exact,high['window'],saved['roundoff'])
    sens=upadd(upmul(10.,upward(abs(high['window']-low['window']))),roundoff)
    stages={label:load(RUN/f'STAGE_{label}.npz') for label in ('A','B','C')}
    s,maps=maps_from_saved(target,stages,inventory)
    target_check=selection(target,high['window'],maps,product,factor)
    require(target_check['exact_set_equal'] and target_check['rederived_count']==42,
            'DIRECT_TARGET_SET_MISMATCH '+json.dumps(target_check))
    corrected={};spectral={};all_entry=[]
    for label in ('A','B','C'):
        bb=[]
        for bi,band in enumerate(maps[label]):
            A,B=spectral_bound(high['window'],sens,band)
            original=stages[label][f'A{bi+1}']
            require(A.shape==original.shape and np.max(abs(A-original))<=
                    1e-12*max(float(np.max(abs(original))),1e-30),
                    'SAVED_SPECTRUM_MISMATCH '+label+str(bi))
            jb=joint_bound(s,band,B)
            bb.append(jb);spectral[f'{label}_BA{bi+1}']=B
            all_entry.append({'stage':label,'band':bi,'BA_max':float(np.max(B)),
                              'old_BA_max':float(np.max(stages[label][f'BA{bi+1}'])),
                              'corrected_joint_bound_max':float(np.max(jb)),
                              'old_joint_bound_max':float(np.max(stages[label][f'bound{bi+1}']))})
        corrected[label]=bb
    report,passed=metrics(stages,corrected)
    # Preserve all five STF and full 15-joint covariance arrays by identity:
    # the sidecar holds only corrected envelopes; the frozen product is untouched.
    np.savez_compressed(OUT/'CORRECTED_BOUNDS.npz',roundoff=roundoff,
                        raw_corrected_roundoff=raw_corrected,old_roundoff=saved['roundoff'],
                        sensitivity=sens,
                        **spectral,**{f'{k}_bound{bi+1}':v[bi] for k,v in corrected.items() for bi in (0,1)})
    payload={'status':'SAVED_BOUND_REPAIRED_PENDING_INDEPENDENT_CLOSEOUT' if passed else
             'NUMERICAL_METHOD_ACCURACY_HOLD',
             'source_result_sha256':EXPECTED['result'],'review_sha256':EXPECTED['review'],
             'candidate_unchanged':True,'scientific_admission':False,
             'H02':'HOLD','H04':'HOLD','global_rigorous_type3_error_enclosure':'NOT_ESTABLISHED',
             'target_selection':target_check,'roundoff':meta,'all_entry_comparisons':all_entry,
             'original_gates':report,'all_original_gates_pass':passed,
             'old_failed_bound_source':'REFERENCE_ROUNDOFF_SOURCE_INDEX_MISMATCH',
             'corrected_bounds_sha256':digest(OUT/'CORRECTED_BOUNDS.npz'),
             'unchanged_product_sha256':digest(RUN/'PRODUCT.npz')}
    (OUT/'RESULT.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    return payload


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--go',required=True)
    args=ap.parse_args();start=time.monotonic()
    try:
        result=main(args.go)
        code=0 if result['all_original_gates_pass'] else 1
    except BaseException as exc:
        result={'status':'HOLD','first_failure':f'{type(exc).__name__}: {exc}',
                'scientific_admission':False}
        (OUT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
        code=1
    (OUT/'RUN_RECEIPT.json').write_text(json.dumps({'elapsed_seconds':time.monotonic()-start,
        'command':'postprocess.py --go '+args.go,'status':result['status'],
        'candidate_sha256':EXPECTED['result']},indent=2)+'\n')
    print(json.dumps({'status':result['status'],'elapsed_seconds':time.monotonic()-start}))
    raise SystemExit(code)
