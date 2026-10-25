"""Author's unexecuted Decimal oracle proposal; never independent review evidence."""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import json
from pathlib import Path

import numpy as np

MAPS = ('30','44','70','100','143','217','353','SMICA')
BLOCKS = ((0,5),(5,12),(12,17),(17,24))


def fail(code): raise RuntimeError(code)
def near(actual, reference, atol, rtol, code):
    if not np.all(np.isfinite(actual)) or not np.all(np.isfinite(reference)) or not np.all(np.abs(actual-reference)<=atol+rtol*np.abs(reference)):
        fail(code)


def decimal_fit(a, y):
    with localcontext() as ctx:
        ctx.prec=50
        d=lambda x:Decimal.from_float(float(x))
        a00=sum((d(a[i,0])*d(a[i,0]) for i in range(12)),Decimal(0))
        a01=sum((d(a[i,0])*d(a[i,1]) for i in range(12)),Decimal(0))
        a11=sum((d(a[i,1])*d(a[i,1]) for i in range(12)),Decimal(0))
        b0=sum((d(a[i,0])*d(y[i]) for i in range(12)),Decimal(0))
        b1=sum((d(a[i,1])*d(y[i]) for i in range(12)),Decimal(0))
        det=a00*a11-a01*a01
        if det == 0: fail('DECIMAL_ANCHOR_SINGULAR')
        return np.asarray((float((b0*a11-b1*a01)/det),float((a00*b1-a01*b0)/det)))


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    inp=json.loads(Path(args.input).read_text()); out=Path(args.output)
    result=json.loads((out/'DESCRIPTIVE_RESULT.json').read_text())
    with np.load(inp['frozen_inputs']['seven_carrier']['path'],allow_pickle=False) as old, \
         np.load(inp['frozen_inputs']['smica_carrier']['path'],allow_pickle=False) as sm, \
         np.load(out/'FULL8_COMPARISON.npz',allow_pickle=False) as got:
        if list(got['map_ids'])!=list(MAPS):fail('MAP_ORDER')
        c=got['C'];d=got['D143'];ds=got['DSMICA']
        if c.shape!=(8,24) or not np.array_equal(c[:7],old['frequency_canonical_7x24']) or not np.array_equal(c[7],sm['canonical24']):fail('SOURCE_CARRIER_PARITY')
        if not np.array_equal(d,c-c[4]) or not np.array_equal(ds,c-c[7]):fail('REFERENCE_SIGN')
        if not np.array_equal(d[4],np.zeros(24)) or not np.array_equal(ds[7],np.zeros(24)):fail('SELF_REFERENCE_ZERO')
        if not np.array_equal(got['anchor_E'],old['anchor_E']) or not np.array_equal(got['anchor_B'],old['anchor_B']):fail('ANCHOR_COPY')
        for key in ('target_E','target_B','coefficients_E_fit','prediction_B','residual_E','residual_B'):
            if key not in got or not np.array_equal(got[key][:4],old[key]):fail('OLD_FIT_COPY:'+key)
        for key in ('E2','E3','B2','B3'):
            t=got[key+'_stf']
            if not np.array_equal(t[:7],old[key+'_stf']) or not np.array_equal(t[7],sm[key]):fail('TENSOR_COPY:'+key)
            if not np.array_equal(got['D143_'+key+'_stf'],t-t[4]) or not np.array_equal(got['DSMICA_'+key+'_stf'],t-t[7]):fail('TENSOR_CONTRAST:'+key)
        if not np.array_equal(got['support_ring64'],old['s7_support_ring64']):fail('SUPPORT_COPY')
        a=old['anchor_E'];ab=old['anchor_B'];y=d[7,:12];yb=d[7,12:]
        if got['prediction_valid'].shape!=(5,) or not got['prediction_valid'].all():fail('PREDICTION_VALIDITY')
        alpha=decimal_fit(a,y)
        near(got['coefficients_E_fit'][4],alpha,1e-10,1e-9,'DECIMAL_ALPHA')
        prediction=np.asarray([sum(float(ab[i,j])*float(alpha[j]) for j in range(2)) for i in range(12)])
        er=np.asarray([float(y[i])-sum(float(a[i,j])*float(alpha[j]) for j in range(2)) for i in range(12)])
        br=yb-prediction
        near(got['prediction_B'][4],prediction,1e-12,1e-9,'DECIMAL_B_PREDICTION')
        near(got['residual_E'][4],er,1e-12,1e-9,'DECIMAL_E_RESIDUAL')
        near(got['residual_B'][4],br,1e-12,1e-9,'DECIMAL_B_RESIDUAL')
        near(got['SMICA_absolute_prediction_B'],c[4,12:]+prediction,1e-12,1e-9,'ABSOLUTE_B_SIGN')
        for key in ('B2','B3'):
            t=got['D143_'+key+'_stf'];pred=got['prediction_'+key+'_stf'];res=got['residual_'+key+'_stf']
            for i,row in enumerate((1,2,3,5,7)):
                coeff=got['coefficients_E_fit'][i]
                expected=coeff[0]*t[0]+coeff[1]*t[6]
                near(pred[i],expected,1e-12,1e-9,'PRED_TENSOR:'+key+str(i))
                near(res[i],t[row]-expected,1e-12,1e-9,'RES_TENSOR:'+key+str(i))
            near(got['SMICA_absolute_prediction_'+key+'_stf'],got[key+'_stf'][4]+pred[4],1e-12,1e-9,'ABS_TENSOR:'+key)
        o=got['O'];g=got['G'];h=got['H']
        if o.shape!=(8,8,24,24) or g.shape!=(4,8,8) or h.shape!=(2,8,8):fail('CROSS_SHAPES')
        for i in range(8):
            for j in range(8):
                for x in range(24):
                    for z in range(24):
                        near(np.asarray(o[i,j,x,z]),np.asarray(float(c[i,x])*float(c[j,z])),1e-22,1e-10,'OUTER_PRODUCT')
                        if o[i,j,x,z]!=o[j,i,z,x]:fail('OUTER_TRANSPOSE')
                for k,(a0,b0) in enumerate(BLOCKS):
                    ref=sum(float(c[i,x])*float(c[j,x]) for x in range(a0,b0))
                    near(np.asarray(g[k,i,j]),np.asarray(ref),1e-22,1e-10,'G_CONTRACTION')
                for k,(a0,b0) in enumerate(BLOCKS[:2]):
                    ref=sum(float(c[i,x])*float(c[j,12+x]) for x in range(a0,b0))
                    near(np.asarray(h[k,i,j]),np.asarray(ref),1e-22,1e-10,'H_CONTRACTION')
        if not np.array_equal(c,np.asarray(result['carrier_8x24_K_CMB'])) or not np.array_equal(g,np.asarray(result['G_4x8x8_K_CMB2'])) or not np.array_equal(h,np.asarray(result['H_2x8x8_K_CMB2'])):fail('JSON_NPZ_PARITY')
        near(np.asarray(result['SMICA_fit']['alpha']),alpha,1e-10,1e-9,'JSON_ALPHA')
    check={'status':'AUTHOR_DECIMAL_ORACLE_RESULT_NOT_INDEPENDENT','decimal_precision_digits':50,
           'source':'exact binary64 inputs converted with Decimal.from_float',
           'tolerances':{'alpha':[1e-10,1e-9],'coordinate_and_tensor_K_CMB':[1e-12,1e-9],
                         'cross_K_CMB2':[1e-22,1e-10]},
           'checked':['seven_exact_reuse','SMICA_exact_copy','both_reference_signs','decimal_E_fit',
                      'all12_B','complete_prediction_tensors','all_outer_products','G_and_H_scalar_contractions','JSON_NPZ_parity'],
           'claim_scope':'author proposal only; fresh reviewer must run an independently authored check'}
    (out/'author_numeric_check.json').write_text(json.dumps(check,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':check['status']}),flush=True)


if __name__=='__main__':main()
