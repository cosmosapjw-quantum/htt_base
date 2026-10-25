"""Independent saved-float review. Run once only after controller ACK.

No producer/author-oracle imports, native map reads, fits of old targets, or plots.
STF parity uses homogeneous harmonic polynomial coefficients divided by tensor
monomial multiplicity. Decimal50 arithmetic starts from exact binary64 values.
"""
import argparse
import hashlib
import itertools
import json
import math
import os
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 50
D = Decimal
PI = D('3.1415926535897932384626433832795028841971693993751')
BASE = Path('/mnt/extdrive/workdir/htt_open_data/r27_eight_map_saved_tensor_comparison_numeric')
HERE = Path(__file__).resolve().parent
NAMES = ('E2', 'E3', 'B2', 'B3')
BLOCKS = ((0,5),(5,12),(12,17),(17,24))
MAPS = ['30','44','70','100','143','217','353','SMICA']
TARGETS = ['44','70','100','217','SMICA']
stats = {}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def must(ok, label):
    if not bool(ok):
        raise AssertionError(label)


def dec(x):
    return D.from_float(float(x))


def comp(observed, expected, label, atol='1e-12', rtol='1e-9'):
    import numpy as np
    o = np.asarray(observed, dtype=object)
    e = np.asarray(expected, dtype=object)
    must(o.shape == e.shape, label + ':shape')
    worst = D(0)
    rel = D(0)
    for x,y in zip(o.flat,e.flat):
        x = dec(x)
        y = y if isinstance(y,D) else dec(y)
        diff = abs(x-y)
        limit = D(atol)+D(rtol)*abs(y)
        worst = max(worst,diff)
        rel = max(rel,diff/limit)
        must(diff <= limit, f'{label}:diff={diff}:allowed={limit}')
    stats[label] = {'n':o.size,'max_abs_error':str(worst),'max_tolerance_fraction':str(rel)}


def tensor(q,ell):
    """Polynomial coefficient extraction, independent of the saved decoder."""
    q = [v if isinstance(v,D) else dec(v) for v in q]
    root2 = D(2).sqrt()
    r = [q[0]]
    for i in range(1,len(q)):
        r.append(q[i]/(root2 if i%2 else -root2))
    if ell == 2:
        a,r1,i1,r2,i2 = r
        z0=(D(5)/(16*PI)).sqrt(); z1=(D(15)/(8*PI)).sqrt(); z2=(D(15)/(32*PI)).sqrt()
        p={(0,0):-z0*a+2*z2*r2,(1,1):-z0*a-2*z2*r2,(2,2):2*z0*a,
           (0,1):-4*z2*i2,(0,2):-2*z1*r1,(1,2):2*z1*i1}
    else:
        a,r1,i1,r2,i2,r3,i3=r
        z0=(D(7)/(16*PI)).sqrt(); z1=(D(21)/(64*PI)).sqrt()
        z2=(D(105)/(32*PI)).sqrt(); z3=(D(35)/(64*PI)).sqrt()
        p={(0,0,0):2*z1*r1-2*z3*r3,(0,0,1):-2*z1*i1+6*z3*i3,
           (0,0,2):-3*z0*a+2*z2*r2,(0,1,1):2*z1*r1+6*z3*r3,
           (0,1,2):-4*z2*i2,(0,2,2):-8*z1*r1,
           (1,1,1):-2*z1*i1-2*z3*i3,(1,1,2):-3*z0*a-2*z2*r2,
           (1,2,2):8*z1*i1,(2,2,2):2*z0*a}
    import numpy as np
    out=np.empty((3,)*ell,dtype=object)
    for ix in itertools.product(range(3),repeat=ell):
        key=tuple(sorted(ix)); multiplicity=math.factorial(ell)
        for j in range(3): multiplicity //= math.factorial(key.count(j))
        out[ix]=p[key]/multiplicity
    return out


def main(args):
    # NumPy is used solely as a safe NPZ reader/shape container, never a fitter.
    import numpy as np
    from threadpoolctl import threadpool_info
    pools=threadpool_info()
    must(all(p['num_threads']==1 for p in pools),'threadpool_count')
    binding=json.loads(Path(args.binding).read_text())
    for item in binding['sealed_files']:
        must(sha(item['path'])==item['sha256'],'seal:'+item['path'])
        if 'bytes' in item: must(Path(item['path']).stat().st_size==item['bytes'],'size:'+item['path'])
    inp=json.loads((BASE/'INPUT.json').read_text())
    contract=json.loads(Path(inp['contract']['path']).read_text())
    for item in [inp['contract'],*inp['frozen_inputs'].values()]:
        must(sha(item['path'])==item['sha256'],'frozen:'+item['path'])
        must(Path(item['path']).stat().st_size==item['bytes'],'frozen_size:'+item['path'])
    refs=inp['frozen_inputs']
    with np.load(refs['seven_carrier']['path'],allow_pickle=False) as f:
        old={k:f[k] for k in f.files}
    with np.load(refs['smica_carrier']['path'],allow_pickle=False) as f:
        sm={k:f[k] for k in f.files}
    with np.load(refs['support']['path'],allow_pickle=False) as f:
        support={k:f[k] for k in f.files}
    with np.load(BASE/'run/products/FULL8_COMPARISON.npz',allow_pickle=False) as f:
        out={k:f[k] for k in f.files}
    js=json.loads((BASE/'run/products/DESCRIPTIVE_RESULT.json').read_text())
    supplement=json.loads(Path(binding['metadata_repair_descriptive_path']).read_text())
    must(all(k in supplement and supplement[k]==v for k,v in js.items()),'supplement_preserves_every_original_JSON_key')
    oldjs=json.loads(Path(refs['seven_descriptive']['path']).read_text())
    must(out['map_ids'].tolist()==MAPS and js['map_ids']==MAPS,'map_order')
    must(out['target_ids'].tolist()==TARGETS and js['target_ids']==TARGETS,'target_order')
    labels=[f'{name}:{suffix}' for name,ell in zip(NAMES,(2,3,2,3))
            for suffix in ['m0',*[v for m in range(1,ell+1) for v in (f'sqrt2Re{m}',f'-sqrt2Im{m}')]]]
    must(out['coordinate_labels'].tolist()==labels==old['coordinate_labels'].tolist()==js['coordinate_labels'],'coordinate_labels')
    for key,v in out.items():
        if v.dtype.kind in 'fiu': must(np.isfinite(v).all(),'finite:'+key)
    c=out['C']; must(c.shape==(8,24),'C_shape')
    must(np.array_equal(c[:7],old['frequency_canonical_7x24']),'exact_seven_C')
    must(np.array_equal(c[7],sm['canonical24']),'exact_SMICA_C')
    must(np.array_equal(c,js['carrier_8x24_K_CMB']),'C_json')
    ix=out['support_ring64']; must(ix.shape==(30021,),'support_shape')
    must(np.array_equal(ix,old['s7_support_ring64']),'support_exact_reuse')
    must(np.array_equal(ix,np.flatnonzero(support['s7_mask_ring64'])),'support_mask')
    must(np.array_equal(support['s7_mask_ring64'],support['selected_mask_ring64']),'S7_S4')
    for name,ref in [('D143',4),('DSMICA',7)]:
        expected=[[dec(c[i,j])-dec(c[ref,j]) for j in range(24)] for i in range(8)]
        comp(out[name],expected,name)
        must(np.array_equal(out[name][ref],np.zeros(24)),name+'_self_zero')
        must(np.array_equal(out[name],js[name+'_8x24_K_CMB']),name+'_json')
    for name,(a,b),ell in zip(NAMES,BLOCKS,(2,3,2,3)):
        t=out[name+'_stf']; must(t.shape==(8,)+(3,)*ell,'tensor_shape:'+name)
        must(np.array_equal(t[:7],old[name+'_stf']),'exact_seven_STF:'+name)
        must(np.array_equal(t[7],sm[name]),'exact_SMICA_STF:'+name)
        for i in range(8):
            comp(t[i],tensor(c[i,a:b],ell),'polynomial_STF:'+name+MAPS[i])
            for perm in itertools.permutations(range(ell)):
                comp(t[i],t[i].transpose(perm),'symmetry:'+name+MAPS[i]+str(perm))
            for left,right in itertools.combinations(range(ell),2):
                comp(np.trace(t[i],axis1=left,axis2=right),np.zeros(() if ell==2 else 3),'trace:'+name+MAPS[i]+str((left,right)))
        for contrast,ref in [('D143',4),('DSMICA',7)]:
            expected=np.empty(t.shape,dtype=object)
            for index in np.ndindex(t.shape):
                expected[index]=dec(t[index])-dec(t[(ref,)+index[1:]])
            comp(out[contrast+'_'+name+'_stf'],expected,contrast+'_STF:'+name)
    ae=out['anchor_E']; ab=out['anchor_B']
    for key in ('anchor_E','anchor_B'):
        must(out[key].shape==(12,2) and np.array_equal(out[key],old[key]),'exact:'+key)
    comp(ae,[[dec(c[m,j])-dec(c[4,j]) for m in (0,6)] for j in range(12)],'E_anchors')
    comp(ab,[[dec(c[m,j+12])-dec(c[4,j+12]) for m in (0,6)] for j in range(12)],'B_anchors')
    for key in ('target_E','target_B','coefficients_E_fit','prediction_B','residual_E','residual_B','prediction_valid'):
        must(np.array_equal(out[key][:4],old[key]),'exact_old_fit:'+key)
    must(out['prediction_valid'].tolist()==[True]*5,'valid_predictions')
    must(js['old_four_target_rows']==oldjs['crossprediction']['targets'],'old_fit_json_reuse')
    must(js['old_seven_frequency_image']==oldjs['computational_frequency_image'],'seven_scalar_reuse')
    comp(out['singular_values'],oldjs['crossprediction']['singular_values_K_CMB'],'singular_reuse','1e-15','1e-12')
    comp(out['singular_ratio'],oldjs['crossprediction']['s2_over_s1'],'ratio_reuse','1e-12','0')
    must(float(out['singular_ratio'])>1e-8,'rank_threshold')
    # Decimal50 exact-input normal equations, exclusively target E.
    x0=[dec(v) for v in ae[:,0]]; x1=[dec(v) for v in ae[:,1]]
    y=[dec(v) for v in out['target_E'][4]]
    a=sum(v*v for v in x0); b=sum(u*v for u,v in zip(x0,x1)); d=sum(v*v for v in x1)
    z0=sum(u*v for u,v in zip(x0,y)); z1=sum(u*v for u,v in zip(x1,y)); det=a*d-b*b
    must(det>0,'positive_normal_determinant')
    alpha=[(d*z0-b*z1)/det,(a*z1-b*z0)/det]
    comp(out['coefficients_E_fit'][4],alpha,'Decimal50_alpha','1e-10','1e-9')
    comp(js['SMICA_fit']['alpha'],alpha,'Decimal50_alpha_json','1e-10','1e-9')
    for field,offset in [('target_E',0),('target_B',12)]:
        comp(out[field],[[dec(c[i,j+offset])-dec(c[4,j+offset]) for j in range(12)] for i in (1,2,3,5,7)],field)
    pred=[dec(ab[j,0])*alpha[0]+dec(ab[j,1])*alpha[1] for j in range(12)]
    re=[y[j]-x0[j]*alpha[0]-x1[j]*alpha[1] for j in range(12)]
    rb=[dec(out['target_B'][4,j])-pred[j] for j in range(12)]
    absb=[dec(c[4,j+12])+pred[j] for j in range(12)]
    for field,expected in [('prediction_B',pred),('residual_E',re),('residual_B',rb)]:
        comp(out[field][4],expected,'Decimal50_'+field)
    comp(out['SMICA_absolute_prediction_B'],absb,'Decimal50_absolute_B')
    for field,npkey in [('all_five_B_prediction_5x12_K_CMB','prediction_B'),('all_five_B_residual_5x12_K_CMB','residual_B'),('target_B_5x12_K_CMB','target_B')]:
        must(np.array_equal(out[npkey],js[field]),'json:'+field)
    for field,expected in [('target_E_12_K_CMB',y),('prediction_B_12_K_CMB',pred),('residual_E_12_K_CMB',re),('residual_B_12_K_CMB',rb),('absolute_prediction_B_12_K_CMB',absb)]:
        comp(js['SMICA_fit'][field],expected,'SMICA_json:'+field)
    for name,ell,sl in [('B2',2,slice(0,5)),('B3',3,slice(5,12))]:
        for k,idx in enumerate((1,2,3,5,7)):
            coef=alpha if k==4 else [dec(v) for v in old['coefficients_E_fit'][k]]
            dt=out['D143_'+name+'_stf']; expected=np.empty((3,)*ell,dtype=object)
            for index in np.ndindex(expected.shape):
                expected[index]=coef[0]*dec(dt[(0,)+index])+coef[1]*dec(dt[(6,)+index])
            comp(out['prediction_'+name+'_stf'][k],expected,'predicted_STF:'+name+TARGETS[k])
            comp(out['prediction_'+name+'_stf'][k],tensor(out['prediction_B'][k,sl],ell),'predicted_polynomial:'+name+TARGETS[k])
            residual=np.empty(expected.shape,dtype=object)
            for index in np.ndindex(expected.shape): residual[index]=dec(dt[(idx,)+index])-expected[index]
            comp(out['residual_'+name+'_stf'][k],residual,'residual_STF:'+name+TARGETS[k])
        comp(out['SMICA_absolute_prediction_'+name+'_stf'],tensor(absb[sl],ell),'absolute_STF:'+name)
    # All 36,864 outer entries, including every cross-ell/E/B block.
    must(out['O'].shape==(8,8,24,24),'O_shape')
    outer=np.empty((8,8,24,24),dtype=object)
    cd=[[dec(v) for v in row] for row in c]
    for i,j,a,b in np.ndindex(outer.shape): outer[i,j,a,b]=cd[i][a]*cd[j][b]
    comp(out['O'],outer,'all_outer_products','1e-22','1e-10')
    must(np.array_equal(out['O'],out['O'].transpose(1,0,3,2)),'outer_exchange')
    g=[[[sum(cd[i][k]*cd[j][k] for k in range(a,b)) for j in range(8)] for i in range(8)] for a,b in BLOCKS]
    h=[[[sum(cd[i][k]*cd[j][k+12] for k in range(a,b)) for j in range(8)] for i in range(8)] for a,b in BLOCKS[:2]]
    comp(out['G'],g,'scalar_G','1e-22','1e-10'); comp(out['H'],h,'scalar_H','1e-22','1e-10')
    must(np.array_equal(out['G'],js['G_4x8x8_K_CMB2']),'G_json')
    must(np.array_equal(out['H'],js['H_2x8x8_K_CMB2']),'H_json')
    worst=max(stats.items(),key=lambda row:D(row[1]['max_tolerance_fraction']))
    result={'status':'PASS_INDEPENDENT_STORED_FLOAT_MATHEMATICS_ONLY','decimal_precision':50,
            'alpha_decimal50':[str(v) for v in alpha],'normal_determinant':str(det),
            'comparisons':stats,'worst_comparison':worst,'loaded_threadpools':pools,
            'input_sha256':sha(BASE/'INPUT.json'),'binding_sha256':sha(args.binding),
            'checker_sha256':sha(__file__),'producer_or_author_oracle_imported':False,
            'metadata_repair_descriptive_sha256':sha(binding['metadata_repair_descriptive_path']),
            'metadata_repair_original_keys_unchanged':True,
            'old_fits_rerun':False,'native_projection_rerun':False,
            'scalar_replacement':False,'scientific_admission':'HOLD',
            'scope':'Saved binary64 algebra only; inherited masked delivered-map/source conditions and resource HOLD remain.'}
    (HERE/'NUMERICAL_CHECKS.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'worst_comparison':worst,'alpha':result['alpha_decimal50']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--binding',required=True);args=p.parse_args()
    try: main(args)
    except BaseException as e:
        (HERE/'NUMERICAL_FIRST_FAILURE.json').write_text(json.dumps({'type':type(e).__name__,'message':str(e),'completed_comparisons':stats},indent=2)+'\n')
        raise
