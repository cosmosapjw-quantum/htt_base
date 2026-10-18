#!/usr/bin/env python3
"""Actual CF4 existing PR179 q gate, stagewise nuisance information ablations.

No physical q estimate, no reclassification of the old H_ONLY gate.
Provenance: authenticated compressed CF4 source and existing registered folds.
"""
from __future__ import annotations
import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np

from obsstat.catalogs.cf4_raw import load_authenticated_cf4_raw_groups
from obsstat.directional_cosmography import (
    DirectionalCosmographyConfig,prepare_directional_catalogue,
    _build_fold_models,_response_identifiability)
from obsstat.cf4_q_nuisance_ablation import compare_nuisance_stages,exact_radial_alias_bound

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/'docs/observational_reboot_20261014/results/cf4/selected_v2/source_subset_receipt.json'
PR179=ROOT/'docs/generated/pr179_directional_cosmography_result.json'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def run(data_root,output):
    if output.exists():raise ValueError('create-only output directory required')
    started=time.perf_counter()
    source=json.loads(RECEIPT.read_text())['source_files']
    groups=load_authenticated_cf4_raw_groups(
        data_root/'table3.dat.gz',data_root/'table4.dat.gz',
        expected_table3_sha256=source['workdir/raw/cf4_full/table3.dat.gz']['sha256'],
        expected_table4_sha256=source['workdir/raw/cf4_full/table4.dat.gz']['sha256'])
    settings=DirectionalCosmographyConfig(null_draws=3)
    prepared=prepare_directional_catalogue(groups,settings)
    models=_build_fold_models(prepared)
    prior=json.loads(PR179.read_text())
    if prior['analysis_branch']!='H_ONLY' or prior['q_cat_withheld'] is not True:
        raise ValueError('registered q gate unexpectedly changed')
    current=_response_identifiability(prepared,models,settings)
    if current['analysis_branch']!='H_ONLY' or not current['q_withheld']:
        raise ValueError('current PR179 response status incompatible')
    result=[]
    for model in models:
        ix=model.train
        weight=prepared.sigma[ix]**-2
        n=prepared.direction[ix]
        z=prepared.z[ix]
        target=np.column_stack((n,z[:,None]*n))
        norms=np.sqrt(np.sum(weight[:,None]*target*target,axis=0))
        hraw=target[:,:3]/norms[:3]
        qraw=target[:,3:]/norms[3:]
        cubic=z[:,None]**2*n
        cubic/=np.sqrt(np.sum(weight[:,None]*cubic*cubic,axis=0))
        base=model.reduced_train
        names=model.nuisance_names
        nonmethod=base[:,[i for i,v in enumerate(names) if not v.startswith('method_')]]
        moff=base[:,[i for i,v in enumerate(names) if v.startswith('method_') and not v.endswith('_by_z')]]
        mslope=base[:,[i for i,v in enumerate(names) if v.startswith('method_') and v.endswith('_by_z')]]
        stages={
          'raw_unrestricted':None,
          'H_only':hraw,
          'cubic_only':cubic,
          'H_plus_cubic':np.column_stack((hraw,cubic)),
          'base_nuisance_only':base,
          'base_plus_H':np.column_stack((base,hraw)),
          'base_plus_cubic':np.column_stack((base,cubic)),
          'registered_base_H_cubic':np.column_stack((base,hraw,cubic)),
          'nonmethod_plus_H_cubic':np.column_stack((nonmethod,hraw,cubic)),
          'nonmethod_methodoffset_H_cubic':np.column_stack((nonmethod,moff,hraw,cubic)),
        }
        r=compare_nuisance_stages(qraw,weight,stages)
        # Matched source scientific gate must not be overwritten.
        old=prior['response_identifiability']['folds'][model.fold_id]
        a=r['stages']['registered_base_H_cubic']['registered_scalar_minimum_information_ratio']
        np.testing.assert_allclose(a,old['retained_information_q_directional_cubic'],
                                   rtol=1e-9,atol=1e-12)
        seq=['raw_unrestricted','base_nuisance_only','base_plus_H','registered_base_H_cubic']
        for before,after in zip(seq,seq[1:]):
            if r['stages'][after]['weakest_relative_information'] > r['stages'][before]['weakest_relative_information']+1e-10:
                raise ValueError('nuisance nesting violated Loewner ordering')
        alias=exact_radial_alias_bound(z,n,weight)
        if alias['exact_identity_max_abs_residual']>1e-13:
            raise ValueError('exact redshift radial alias identity failed')
        result.append({
            'radial_quadratic_alias_envelope':alias,
            'fold':model.fold_id,
            'trained_rows':int(len(ix)),
            'registered_q_cubic_scalar_ratio':float(old['retained_information_q_directional_cubic']),
            'registered_q_response':'WITHHELD',
            'base_nuisance_names':list(names),
            'method_offset_columns':int(moff.shape[1]),
            'method_slope_columns':int(mslope.shape[1]),
            'theory_based_metrics':r['stages'],
            'unrestricted_raw_metric_scope':'weighted Gram of q_cat numerical response, no physical q',
        })
    data={
      'schema':'htt.cf4-q-staged-nuisance-ablation/1',
      'status':'REAL_RAW_CF4_FIVE_FOLD_GAUGE_AND_NUISANCE_DESIGN_ONLY',
      'source_head':'13d8d85fa470d645d008986e8f77d8d0f70fdf54',
      'source_raw_root':str(data_root),
      'sha256_sources':groups.source_hashes,
      'sha256_receipt':sha(RECEIPT),
      'sha256_earlier_result':sha(PR179),
      'selected_id_sha256':prepared.selected_row_sha256,
      'groups_in_raw':groups.row_count,
      'groups_in_PR179_frozen_domain':prepared.n,
      'old_registered_branch':prior['analysis_branch'],
      'old_q_withheld':prior['q_cat_withheld'],
      'projection_law':'within each fold, fixed W=diag(1/sigma_i^2), normalized qraw=z n; stage nuisance no outcome-based fitting',
      'attribution_limit':'stage addition is order-dependent; no unique causal decomposition and no physical source-selection posterior',
      'scientific_status':'all q physical/model admission HOLD_UNCHANGED',
      'records':result,
      'seconds':time.perf_counter()-started,
      'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output.mkdir(parents=True)
    (output/'result.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    stages=[
     'raw_unrestricted','H_only','cubic_only','H_plus_cubic',
     'base_nuisance_only','base_plus_H','base_plus_cubic',
     'registered_base_H_cubic','nonmethod_plus_H_cubic']
    md=[
        '# CF4 기존 Q 누락의 단계별 nuisance 요인 분해',
        '',
        f"실제 원시 CF4 그룹 {groups.row_count}, 등록 PR179 영역 {prepared.n}, 5 fold.",
        '',
        '이 계산은 수치 설계의 Fisher 잔류정보이며, H0/q/가속도 posterior 또는 물리적 식별성 정리가 아니다.',
        '선형 nuisance의 증가 순서에 따라 정보 손실이 달라지므로 각 행은 조건부 시나리오다.',
        '',
        '| 잔류 설계 | 상대 Fisher 최약비율 fold별 (0...4) | 5-fold 평균 |',
        '|---|---|---:|'
    ]
    for key in stages:
        e=[r['theory_based_metrics'][key]['weakest_relative_information'] for r in result]
        md.append('| '+key+' | '+', '.join(f'{v:.5f}' for v in e)+' | '+f'{np.mean(e):.5f}'+' |')
    md.extend(['', '## 정확한 깊이방향 교차항등식',
      'z*n=(z0/2)n+(1/(2z0)) z²n-((z-z0)²/(2z0))n.',
      '이 항등식은 H(n)과 cubic z²n nuisance가 있는 경우 Q=z*n의 잔차를 Δz² 규모로 제어하며, 상대 제곱정보의 작은 shell 상한은 (Δz/z0)^4 규모다.',
      '이는 모든 finite source WLS에서 성립하는 **최적 projection의 상계**이며 현 자료의 실제 Fisher 최약비율과 동일한 지표가 아니다.',
      '| fold | pivot z | actual H+cubic weighted trace fraction | constructive fourth-moment upper bound |',
      '|---|---:|---:|---:|'])
    for r in result:
        a=r['radial_quadratic_alias_envelope']
        md.append(f"| {r['fold']} | {a['pivot_z']:.6g} | {a['actual_best_H_and_cubic_weighted_squared_ratio']:.6g} | {a['constructive_upper_squared_ratio']:.6g} |")
    md.extend(['','같은 fold의 등록 q_cubic 정보비율을 직접 재계산하여 기존 PR179 결과와 1e-9 상대 정밀도로 대조했다.',
       '모든 stage의 매개변수 basis 불변 relative eig와 scalar legacy ratio를 별도로 보존했다.',
       '모든 원래의 q withholding gate/H-only status는 불변이다.',
       'method 보정 nuisance 없이 정보가 늘어나더라도 실제 그 보정이 알려지지 않은 survey law를 무시할 수 있다는 뜻은 아니다.'])
    (output/'REPORT_KO.md').write_text('\n'.join(md)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,4.3),layout='constrained')
    for name in ('base_plus_H','registered_base_H_cubic','nonmethod_plus_H_cubic','base_plus_cubic'):
        vals=[r['theory_based_metrics'][name]['weakest_relative_information'] for r in result]
        ax.plot(range(5),vals,marker='o',label=name)
    ax.set(xlabel='Registered fivefold index',ylabel='Worst Fisher-normalized q information ratio',
          title='Actual CF4 q response: conditional nuisance ablations',xticks=list(range(5)))
    ax.set_yscale('symlog',linthresh=.001)
    ax.legend(fontsize=8)
    fig.savefig(output/'cf4_q_nuisance_fisher.png',dpi=165)
    plt.close(fig)
    print(json.dumps({'status':data['status'],'raw_groups':data['groups_in_raw'],
        'selected':data['groups_in_PR179_frozen_domain'],
        'means':{key:float(np.mean([r['theory_based_metrics'][key]['weakest_relative_information'] for r in result])) for key in stages},
        'alias_bound_mean':float(np.mean([r['radial_quadratic_alias_envelope']['constructive_upper_squared_ratio'] for r in result])),
        'alias_actual_mean':float(np.mean([r['radial_quadratic_alias_envelope']['actual_best_H_and_cubic_weighted_squared_ratio'] for r in result])),
        'elapsed_s':data['seconds']},indent=2))
    return data


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--input-root',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    run(args.input_root,args.output_dir)
