"""Independent saved-factor reviewer. No author module is imported.

Actual values use integer accumulators at denominator 2**2148 and evaluate
L[:,j]*(y[i]-y[reference]) directly. Author uses Fraction correction sums.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
DEN = 1 << 2148
SUM_DEN = 1 << 1074

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def pair(x):
    n, d = float(x).as_integer_ratio()
    return n, d.bit_length() - 1

def diff_pair(x, y):
    nx, ex = pair(x)
    ny, ey = pair(y)
    e = max(ex, ey)
    return (nx << (e-ex)) - (ny << (e-ey)), e

def exact(x):
    return Fraction(*float(x).as_integer_ratio())

def encoded(x):
    return [str(x.numerator), str(x.denominator)]

def decode(x):
    return Fraction(int(x[0]), int(x[1]))

def direct(l, y, nonrefs, refs):
    accum = [0] * 5
    for j, (i, r) in enumerate(zip(nonrefs, refs)):
        ny, ey = diff_pair(y[i], y[r])
        for a in range(5):
            nk, ek = pair(l[a, j])
            accum[a] += (nk * ny) << (2148-ek-ey)
    return [Fraction(n, DEN) for n in accum]

def assert_bits(a, b, what):
    assert a.dtype == b.dtype and a.shape == b.shape, what + ': shape/dtype'
    assert a.tobytes() == b.tobytes(), what + ': bits'

def main():
    binding = json.loads((HERE / 'REVIEW_INPUT.json').read_text())
    assert binding['controller_go'] is True
    for role, obj in binding['bindings'].items():
        assert sha(obj['path']) == obj['sha256'], 'SHA_MISMATCH:' + role
    paths = binding['bindings']
    srcpath = paths['source_carrier']['path']
    factorpath = paths['candidate_factor']['path']
    candidate = json.loads(Path(paths['candidate_result']['path']).read_text())
    parent = json.loads(Path(paths['source_result']['path']).read_text())
    assert candidate['source']['carrier_sha256'] == sha(srcpath)
    assert candidate['source']['result_sha256'] == sha(paths['source_result']['path'])
    with np.load(srcpath, allow_pickle=False) as z, np.load(factorpath, allow_pickle=False) as f:
        ids, support = z['group_id'], z['selected_support_7']
        singleton, mixed = z['active_singleton_mask'], z['mixed_zero_leverage_mask']
        k, y, d, b, n = (z[name] for name in ['K', 'y', 'd', 'B', 'N'])
        assert ids.shape == (35970,) and ids.dtype == np.int64
        assert len(set(map(int, ids))) == 35970
        assert hashlib.sha256(ids.astype('<i8', copy=False).tobytes()).hexdigest() == 'f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88'
        assert tuple(map(str, z['channel_names'])) == ('SNIa','FP','TFR','SBFm','SBFir','SNII','DirectCal')
        assert support.shape == (35970, 7) and support.dtype == np.bool_
        assert np.array_equal(singleton, support.sum(axis=1) == 1)
        assert np.array_equal(mixed, support.sum(axis=1) > 1)
        assert int(singleton.sum()) == 35026 and int(mixed.sum()) == 944
        assert np.all(support.sum(axis=1) >= 1)
        assert k.shape == (5,35970) and b.shape == (35970,5) and n.shape == (35970,14)
        assert y.shape == d.shape == (35970,) and np.all(d > 0)
        assert all(a.dtype == np.float64 and np.isfinite(a).all() for a in [k,y,d,b,n,z['STF_basis_5x3x3']])
        assert np.all(k[:, mixed] == 0)
        assert np.array_equal(z['C'], (support & singleton[:,None]).astype(np.float64))
        for name in ['group_id','selected_support_7','active_singleton_mask','mixed_zero_leverage_mask','extra_zero_leverage_mask','channel_names','STF_basis_5x3x3']:
            assert_bits(f[name],z[name],name)
        assert_bits(f['y_binary64'], y, 'y')
        assert_bits(f['d_binary64'], d, 'd')
        refs = np.full(7, -1, dtype=np.int64)
        channels = np.full(35970, -1, dtype=np.int64)
        counts=[]
        for c in range(7):
            indices = np.flatnonzero(singleton & support[:,c])
            counts.append(int(len(indices)))
            if len(indices):
                order = np.lexsort((ids[indices],d[indices]))
                refs[c] = indices[order[0]]
                channels[indices] = c
        reference_set = set(map(int, refs[refs >= 0]))
        nonrefs = np.asarray([i for i in range(35970) if singleton[i] and i not in reference_set],dtype=np.int64)
        refrows=refs[channels[nonrefs]]
        assert np.array_equal(f['reference_row_by_channel'],refs)
        assert np.array_equal(f['nonreference_row_index'],nonrefs)
        assert np.array_equal(f['nonreference_channel'],channels[nonrefs])
        assert np.array_equal(f['difference_reference_row_index'],refrows)
        assert candidate['index_base'] == 0
        assert candidate['reference_row_by_channel'] == refs.tolist()
        assert candidate['reference_group_id_by_channel'] == [None if r < 0 else int(ids[r]) for r in refs]
        assert candidate['channel_row_counts'] == counts
        assert candidate['nonreference_count'] == len(nonrefs)
        l=f['L_binary64']
        assert_bits(l,k[:,nonrefs],'L')
        assert np.any(l != 0), 'NO_NONTRIVIAL_FUNCTIONAL'
        # Integer support identity: each D row sees exactly the same one-hot row.
        assert np.array_equal(support[nonrefs], support[refrows])
        assert np.all(singleton[nonrefs]) and np.all(singleton[refrows])
        direct_b = direct(l,y,nonrefs,refrows)
        assert direct_b == [decode(x) for x in candidate['exact_b_fact']], 'DIRECT_EXACT_B_MISMATCH'
        # Independent old contractions and sums are integer dyadic accumulations.
        old_accum = [0]*5
        channel_accum = [[0]*5 for _ in range(7)]
        for i in range(35970):
            ny, ey = pair(y[i])
            c = int(channels[i])
            for a in range(5):
                nk, ek = pair(k[a,i])
                old_accum[a] += (nk*ny) << (2148-ek-ey)
                if c >= 0:
                    channel_accum[c][a] += nk << (1074-ek)
        old = [Fraction(x,DEN) for x in old_accum]
        sums = [[Fraction(x,SUM_DEN) for x in row] for row in channel_accum]
        correction = [direct_b[a]-old[a] for a in range(5)]
        identity_correction = [-sum((sums[c][a]*exact(y[r]) for c,r in enumerate(refs) if r>=0),Fraction(0)) for a in range(5)]
        assert correction == identity_correction
        price=sum((exact(d[r])*sum((v*v for v in sums[c]),Fraction(0)) for c,r in enumerate(refs) if r>=0),Fraction(0))
        assert old == [decode(x) for x in candidate['exact_old_Khat_y']]
        assert sums == [[decode(x) for x in row] for row in candidate['exact_channel_sums_7x5']]
        assert correction == [decode(x) for x in candidate['exact_change_b_fact_minus_old']]
        assert price == decode(candidate['exact_delta_D_sq'])
        display=np.asarray(candidate['display_b_fact'],dtype=np.float64)
        assert display.shape==(5,) and np.isfinite(display).all()
        assert [exact(v)-x for v,x in zip(display,direct_b)] == [decode(x) for x in candidate['exact_display_minus_b_fact']]
        assert [exact(v)-x for v,x in zip(z['b_min'],old)] == [decode(x) for x in candidate['exact_parent_b_min_minus_old']]
        assert np.array_equal(np.asarray(candidate['parent_b_min_binary64']),z['b_min'])
        tensor = np.einsum('a,aij->ij',display,z['STF_basis_5x3x3'])
        assert tensor.shape == (3,3) and np.array_equal(tensor,np.asarray(candidate['complete_3x3_tensor_display_in_saved_basis']))
        # Whole numerical diagnostics re-evaluated from saved factor, no refit.
        kb=l @ (b[nonrefs]-b[refrows]); kn=l @ (n[nonrefs]-n[refrows])
        resp=candidate['response_numerical']
        assert np.array_equal(kb,np.asarray(resp['KB'])) and np.array_equal(kn,np.asarray(resp['KN']))
        assert resp['KB_minus_I_fro']==float(np.linalg.norm(kb-np.eye(5)))
        assert resp['KN_fro']==float(np.linalg.norm(kn))
        for name,mat in [('KB',kb),('KN',kn)]:
            sv=np.linalg.svd(mat,compute_uv=False)
            assert np.array_equal(sv,np.asarray(resp[name+'_singular_values']))
            assert resp[name+'_rank_relative_tolerance']=={f'{tol:.0e}':int(np.sum(sv>tol*sv[0])) for tol in (1e-12,1e-10,1e-8)}
        # Reconcile new exact reference coefficients and complete zero leverage.
        new_zero=mixed.copy()
        new_zero[nonrefs]=np.all(l==0,axis=0)
        for c,r in enumerate(refs):
            if r>=0:
                new_zero[r]=all(sums[c][a]-exact(k[a,r])==0 for a in range(5))
        extra_new=new_zero & ~mixed
        assert np.array_equal(extra_new,f['extra_zero_leverage_mask']), 'NEW_ZERO_LEVERAGE_MASK_MISMATCH'
        # Combined row/channel relabeling preserves physical reference mapping.
        p=np.arange(35970)[::-1]
        q=np.asarray([6,2,0,5,3,1,4])
        for newc,oldc in enumerate(q):
            indices=np.flatnonzero(singleton[p] & support[p][:,q][:,newc])
            if len(indices):
                picked=indices[np.lexsort((ids[p[indices]],d[p[indices]]))[0]]
                assert p[picked] == refs[oldc]
        # Independent exact arithmetic boundary witness, not an estimator rerun.
        sub=np.nextafter(0.,1.)
        toy_l=np.zeros((5,2)); toy_l[0,0]=1.;toy_l[1,1]=sub
        toy_y=np.asarray([sub,-sub,1.,0.])
        toy=direct(toy_l,toy_y,np.asarray([0,2]),np.asarray([1,3]))
        assert toy[0]==Fraction(2,1<<1074) and toy[1]==Fraction(1,1<<1074)
        tiny=Fraction(1,1<<1074)
        assert tiny != 0 and tiny*tiny*Fraction(1<<2148) == 1
        all_zero_differences=np.zeros((5,1))
        all_zero_differences[0,0]=sub
        assert direct(all_zero_differences,np.asarray([1.,1.]),np.asarray([0]),np.asarray([1])) == [Fraction(0)]*5
        output={
          'status':'ALL_INDEPENDENT_CHECKS_PASSED','source_rows':35970,
          'environment':{'executable':sys.executable,'python_version':sys.version,'numpy_version':np.__version__,'numpy_file':np.__file__,'cwd':str(Path.cwd())},
          'singleton_rows':35026,'mixed_rows':944,'nonreference_count':len(nonrefs),
          'channel_counts':counts,'reference_group_ids':[int(ids[r]) if r>=0 else None for r in refs],
          'independent_algorithm':'direct integer dyadic L*(y_i-y_ref), denominator 2^2148; no author import',
          'exact_b_fact':[encoded(v) for v in direct_b],
          'display_b_fact':display.tolist(),'exact_correction':[encoded(v) for v in correction],
          'correction_display':[float(v) for v in correction],
          'exact_delta_D_sq':encoded(price),'delta_D_sq_display':float(price),
          'nonzero_channel_sums':sum(v!=0 for row in sums for v in row),
          'extra_new_exact_zero_leverage_count':int(extra_new.sum()),
          'direct_correction_exact_parity':True,'bit_preserved_L':True,
          'integer_support_identity':True,'combined_row_channel_permutation':True,
          'subnormal_and_tiny_nonzero_scope':True,'response_numerical':resp,
          'complete_3x3_tensor_display':tensor.tolist(),
          'source_parent_rank_scope':parent['signal']['rank_scope'],
          'source_parent_rank':parent['signal']['rank'],
          'rounding_materialized_matrix_exact_claim':False,
          'source_and_candidate_hashes_unchanged':all(sha(o['path'])==o['sha256'] for o in paths.values()),
        }
        assert output['source_and_candidate_hashes_unchanged']
    (HERE/'NUMERIC_CHECK.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'status':output['status'],'direct_exact_components':5,'delta_D_sq':output['delta_D_sq_display']}),flush=True)

if __name__=='__main__':
    main()
