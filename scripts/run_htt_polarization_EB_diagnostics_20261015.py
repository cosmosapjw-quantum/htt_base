#!/usr/bin/env python3
"""Actual Planck PR3 cut-sky finite-spin-2 low-ell E/B cross-products.

These are real finite-basis E and B projections of source Q/U, with a
single common polarization mask; no physical primordial B, parity
violation or lowE Planck likelihood is inferred. Spin sky-frame fixed.
"""
from __future__ import annotations
import argparse,json,time,resource
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/research_program/theory_obs_application_20261015/loop5/results/planck_multisplit_spin_v1/retained_common_support_coefficients.npz'


def run(out):
    if out.exists():raise ValueError('create-only scientific result')
    start=time.perf_counter()
    with np.load(SOURCE,allow_pickle=False) as f:
        names=list(f['names_EB'])
        arr=np.asarray(f['coeff_EB'],float)
        meta=json.loads(str(f['column_spin_metadata_json']))
    if len(names)!=8 or arr.shape!=(8,64) or len(meta)!=64:
        raise ValueError('spin2 source products/schema mismatch')
    x=dict(zip(names,arr))
    groups={}
    for name,row in x.items():
        spectra=[]
        for ell in range(2,6):
            ids_E=[i for i,j in enumerate(meta) if j['ell']==ell and j['E_or_B']=='E']
            ids_B=[i for i,j in enumerate(meta) if j['ell']==ell and j['E_or_B']=='B']
            if len(ids_E)!=2*ell+1 or len(ids_B)!=len(ids_E):
                raise ValueError('physical real spin convention map drift')
            E=row[ids_E];B=row[ids_B]
            p=2*ell+1
            spectra.append({
                'ell':ell,'E_auto_microK2':float(E@E/p),
                'B_auto_microK2':float(B@B/p),
                'EB_cross_microK2':float(E@B/p),
                'B_to_E_auto_ratio':float((B@B)/(E@E)) if E@E>0 else None,
                'EB_bound_Cauchy_ratio':float((E@B)**2/((E@E)*(B@B))) if E@E>0 and B@B>0 else None
            })
        groups[name]=spectra
    cross={}
    for label,(one,two) in {
       'SMICA_HM':('SMICA_HM1','SMICA_HM2'),
       'SMICA_OE':('SMICA_OE1','SMICA_OE2'),
       'NILC_HM':('NILC_HM1','NILC_HM2')
       }.items():
        outell=[]
        for ell in range(2,6):
            e=[i for i,j in enumerate(meta) if j['ell']==ell and j['E_or_B']=='E']
            b=[i for i,j in enumerate(meta) if j['ell']==ell and j['E_or_B']=='B']
            a=x[one];d=x[two]
            outell.append({
                'ell':ell,
                'E_split_cross_microK2':float(a[e]@d[e]/len(e)),
                'B_split_cross_microK2':float(a[b]@d[b]/len(b)),
                'EB_symmetric_split_cross_microK2':float((a[e]@d[b]+d[e]@a[b])/(2*len(e))),
                'E_split_halfdifference_power_microK2':float(np.sum((a[e]-d[e])**2)/(4*len(e))),
                'B_split_halfdifference_power_microK2':float(np.sum((a[b]-d[b])**2)/(4*len(b))),
            })
        cross[label]=outell
    result={
       'schema':'htt.actual-PR3-finite-spin2-lowell-eb/1',
       'status':'SAME_SKY_FINITE_CUTSKY_EB_IMAGES_NOT_PHYSICAL_LOWELL_EE_BB_EB_INFERENCE',
       'source_coefficients':str(SOURCE.relative_to(ROOT)),
       'source_map_methods':names,
       'n_real_spin2_coefficients':64,
       'ell_span':[2,5],
       'per_map_EE_BB_EB':groups,
       'split_cross_EE_BB_EB':cross,
       'warning':'finite low-L Q/U masked WLS excludes high ell and true Planck beam/noise, hence EB may reflect mask leakage, residual foregrounds and processing; no parity-violation/primordial B claim',
       'elapsed_seconds':time.perf_counter()-start,
       'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# PR3 실제 Q/U의 finite low-ell E/B 관측계수: 소스 보존 연구',
         '', '같은 NSIDE64 편광 신뢰 mask와 동일한 64차원 spin-2 joint LS를 사용함.',
         '발표한 full-mission CMB EE/BB likelihood나 parity-violation 결과가 아님.',
         '','| ell | SMICA_FULL E-auto | SMICA_FULL B-auto | SMICA_FULL EB-cross |',
         '|---:|---:|---:|---:|']
    for row in groups['SMICA_FULL']:
        lines.append(f"| {row['ell']} | {row['E_auto_microK2']:.6g} | {row['B_auto_microK2']:.6g} | {row['EB_cross_microK2']:.6g} |")
    lines+=['','| split | E half-diff total power sum | B half-diff total power sum |',
            '|---|---:|---:|']
    for key,v in cross.items():
        lines.append(f"| {key} | {sum(x['E_split_halfdifference_power_microK2'] for x in v):.6g} | {sum(x['B_split_halfdifference_power_microK2'] for x in v):.6g} |")
    lines+=['','EB is odd under parity only in a fully specified physical spin basis; a finite cut-sky and unmodeled high-ell leak destroys naive parity-null interpretation.',
       'Foreground/component-separation differences must be carried as common-source responses rather than independent cosmic signals.']
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({
        'status':result['status'],
        'SMICA_FULL':[{'ell':r['ell'],'EE':r['E_auto_microK2'],'BB':r['B_auto_microK2'],'EB':r['EB_cross_microK2']} for r in groups['SMICA_FULL']],
        'split_B_diff_powers':{key:sum(v['B_split_halfdifference_power_microK2'] for v in x) for key,x in cross.items()}
    },indent=2))
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    run(args.output_dir)
