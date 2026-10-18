#!/usr/bin/env python3
"""Observed CF4 grouped directions/depth q-response nonidentification certificate.

No q_cat estimate, no cosmological acceleration, no changed prospective gate.
Calculates additional *idealized* Fisher-normalized information that would
mathematically lift weakest residual response, and source-maps all inputs.
"""
from __future__ import annotations
import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np
from obsstat.catalogs.cf4_raw import load_authenticated_cf4_raw_groups
from obsstat.directional_cosmography import (DirectionalCosmographyConfig,
    prepare_directional_catalogue,_build_fold_models,_weighted_residualize,
    _minimum_information_ratio,_response_identifiability)
from obsstat.cf4_q_information_budget import information_budget
ROOT=Path(__file__).resolve().parents[1]
CF4_RECEIPT=ROOT/'docs/observational_reboot_20261014/results/cf4/selected_v2/source_subset_receipt.json'
PR179=ROOT/'docs/generated/pr179_directional_cosmography_result.json'


def run(raw_root,output):
    if output.exists(): raise ValueError('create-only output root')
    start=time.perf_counter()
    src=json.loads(CF4_RECEIPT.read_text())['source_files']
    h3=src['workdir/raw/cf4_full/table3.dat.gz']['sha256']
    h4=src['workdir/raw/cf4_full/table4.dat.gz']['sha256']
    cat=load_authenticated_cf4_raw_groups(
        raw_root/'table3.dat.gz',raw_root/'table4.dat.gz',
        expected_table3_sha256=h3,expected_table4_sha256=h4)
    cfg=DirectionalCosmographyConfig(null_draws=3)
    obs=prepare_directional_catalogue(cat,cfg)
    models=_build_fold_models(obs)
    existing=json.loads(PR179.read_text())
    disposition=_response_identifiability(obs,models,cfg)
    if disposition['analysis_branch']!='H_ONLY' or not disposition['q_withheld']:
        raise ValueError('prospective q status changed unexpectedly')
    evidence=[]
    for model in models:
        ix=model.train
        w=1/obs.sigma[ix]**2
        theta=obs.direction[ix]
        z=obs.z[ix]
        target=np.column_stack([theta,z[:,None]*theta])
        norms=np.sqrt(np.sum(w[:,None]*target*target,axis=0))
        target=target/norms
        hraw,qraw=target[:,:3],target[:,3:]
        cubic=(z*z)[:,None]*theta
        cubic=cubic/np.sqrt(np.sum(w[:,None]*cubic*cubic,axis=0))
        full_nuisance=np.column_stack((model.reduced_train,hraw,cubic))
        qres=_weighted_residualize(qraw,full_nuisance,w)
        gram_raw=qraw.T@(w[:,None]*qraw)
        gram_cond=qres.T@(w[:,None]*qres)
        budget=information_budget(gram_raw,gram_cond,
                                  minimum_retained_fraction=cfg.minimum_information_q_cubic)
        registered_ratio=_minimum_information_ratio(qraw,qres,w)
        old=existing['response_identifiability']['folds'][model.fold_id]
        np.testing.assert_allclose(registered_ratio,
           old['retained_information_q_directional_cubic'],atol=5e-13,rtol=1e-11)
        evidence.append({
          'fold':model.fold_id,
          'train_rows':int(len(ix)),
          'q_status':'WITHHELD_REGISTERED_PROSPECTIVE_GATE_UNCHANGED',
          'registered_current_weakest_eigenvalue_ratio':registered_ratio,
          'registered_q_cubic_canonical_correlation':
                disposition['folds'][model.fold_id]['q_directional_cubic_canonical_correlation'],
          'invariant_generalized_gram_info':budget,
          'raw_gram_determinant':float(np.linalg.det(gram_raw)),
          'retained_gram_determinant':float(np.linalg.det(gram_cond)),
        })
    result={
      'schema':'htt.cf4-q-nuisance-information-budget/1',
      'status':'ACTUAL_CF4_GEOMETRY_QUANTIFIED_INPUT_BLOCKER_NOT_RESOLVED_PHYSICALLY',
      'input_raw_root':str(raw_root),
      'source_sha256_gzip':cat.source_hashes,
      'source_receipt_sha256':hashlib.sha256(CF4_RECEIPT.read_bytes()).hexdigest(),
      'pr179_result_sha256':hashlib.sha256(PR179.read_bytes()).hexdigest(),
      'selected_group_id_sha256':obs.selected_row_sha256,
      'n_original_groups':cat.row_count,'n_filtered':obs.n,
      'existing_registered_analysis_branch':disposition['analysis_branch'],
      'all_q_fold_admitted':bool(disposition['q_pass_all_folds']),
      'nuisance':'Registered PR179 nuisance (method offsets/slopes, error, sky density, H dipole), plus z^2 n cubic response.',
      'basis_invariant_certificate':'Generalized eig(G_retained,G_raw), not registered min(lambda)/min(lambda) ratio; auxiliary evidence only.',
      'info_floor_target':'Hypothetical independent orthogonal source in raw Fisher-normalised parameter coordinates to lift to frozen q_cubic floor; not observed',
      'physical_q_posterior_status':'NOT_AVAILABLE',
      'source_condition':'actual data primary allowlisted Vcmb/DMzp/eDMzp, angular position, method mix; no cosmological/selection covariance model',
      'measurements_to_close':['Independent directional redshift-distance contrast not collinear with nuisance/cubic.',
                               'Calibrated per-method selection/calibration with joint likelihood and cross-covariance.',
                               'Physical local absolute redshift intercept/finite-distance remainder and congruence derivative law.'],
      'folds':evidence,'seconds':time.perf_counter()-start,
      'rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output.mkdir(parents=True)
    (output/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    report=['# CF4 방향 Q/가속도 유사 통계의 정보 결손 계량',
      '', '**결론:** 실제 CF4에서는 등록된 q_cat gate가 여전히 WITHHELD다. 점추정 또는 p-value를 내지 않는다.',
      '',
      '| Fold | 등록 q 정보잔여비율 | 재매개화 불변 최약 상대 Fisher 정보 | 목표 0.05까지의 정규화 추가 정보 trace |',
      '|---|---:|---:|---:|']
    for r in evidence:
        inf=r['invariant_generalized_gram_info']
        report.append(f"| {r['fold']} | {r['registered_current_weakest_eigenvalue_ratio']:.6g} | {inf['weakest_relative_information']:.6g} | {inf['normalized_minimum_added_information_trace']:.6g} |")
    report +=['','현재 관측 템플릿 행렬에서 계산한 상대정보 고유값은 모델의 nuisance, 부호, 단위와 불변성에 조건부.',
       '기준 0.05는 기존 PR179의 사전 등록 임계비율을 새로운 generalized eigen geometric target으로 옮긴 **가상 정보제공자 설계 기준**이지 기존 gate의 소급 수정이 아니다.',
       '스칼라 basis 회전/재매개화는 실제 부족한 관측 정보의 독립된 증가를 만들지 않는다.',
       '외부 independent directional channel, 실제 selection/calibration likelihood, physical congruence response 없이는 q를 과학적 결론으로 승격하지 않는다.',
       '기존 H_ONLY conditional result와 등록된 prospective verdict를 불변 보존했다.']
    (output/'REPORT_KO.md').write_text('\n'.join(report)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7,3.5),layout='constrained')
    x=np.arange(len(evidence))
    vals=[r['invariant_generalized_gram_info']['relative_information_eigenvalues'] for r in evidence]
    arr=np.asarray(vals)
    for i in range(3):ax.plot(x,arr[:,i],marker='o',label=f'generalized eig {i+1}')
    ax.axhline(.05,ls='--',color='gray',label='hypothetical floor')
    ax.set(xlabel='Crossfit fold',ylabel='Fisher information fraction',ylim=(0,max(.25,float(arr.max())*1.05)),xticks=x)
    ax.legend(fontsize=7)
    fig.savefig(output/'cf4_q_info_eigenvalues.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'status':result['status'],
      'n_filtered':result['n_filtered'],
      'registration':result['existing_registered_analysis_branch'],
      'folds':[(r['fold'],
       r['registered_current_weakest_eigenvalue_ratio'],
       r['invariant_generalized_gram_info']['weakest_relative_information'],
       r['invariant_generalized_gram_info']['normalized_minimum_added_information_trace'])
       for r in evidence],
       'elapsed_s':result['seconds']},indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input-root',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    parser.add_argument('--output-dir',type=Path,required=True)
    opt=parser.parse_args()
    run(opt.input_root,opt.output_dir)
