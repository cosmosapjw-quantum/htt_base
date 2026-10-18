#!/usr/bin/env python3
"""Legacy three-layer pushforward with ACTUAL published 2009 vs 2023 windows.

These scalar speed Gaussian conversions are illustrative conditional
bookkeeping, not an actual CF4 group source-vs-observer congruence tilt,
and the resulting occupancy is not a measured beyond-FLRW geometry.
"""
from __future__ import annotations
import argparse,hashlib,json,time,zipfile,resource
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obsstat.legacy_defect_conditional_bridge import (
 scalar_proxy_from_Cl,mes_scenario_ceiling,legacy_pushforward_of_external_bulk_proxy)

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results'
ARCHIVE=ROOT/'old_version/HTT.zip'
PDF=ROOT/'old_version/main_FINAL.pdf'
PLANCK=ROOT/'docs/research_program/theory_obs_application_20261015/loop5/results/planck_multisplit_spin_v1/result.json'
CF4=DIR/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2'
V2SHA='3696f806b2639be1f9ea0fc17e96e89124a8ec5802e58dd7a31b710667e6d8c3'
PDFSHA='c1aefb6ab9d27b423a75274cb6887fe6cb494b7f21e1e2f750577b43c07e0942'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

def run(out):
    if out.exists():raise ValueError('create only')
    start=time.perf_counter()
    if sha(ARCHIVE)!=V2SHA or sha(PDF)!=PDFSHA:raise ValueError('legacy primary source changed')
    with zipfile.ZipFile(ARCHIVE) as z:
        old=json.loads(z.read('HTT/data/obs_defaults.json'))
        ev=json.loads(z.read('HTT/outputs/pipeline_evidence.json'))
    assert old['dipole_observations']['cf4_watkins_2023']['beta']==.001334
    source=json.loads(PLANCK.read_text())
    cf4=json.loads((CF4/'result.json').read_text())
    assert len(source['selected_original_T_and_P_features'])==9 and cf4['n_z01_10']==35970
    reported_bulk={
      'WFH_2009_COMPOSITE_50hMpc':{'v':407.,'sv':81.,'window':'50 h^-1 Mpc Gaussian; 4481 COMPOSITE; DOI 10.1111/j.1365-2966.2008.14089.x'},
      'CF4_2023_150hMpc':{'v':387.,'sv':28.,'window':'150 h^-1 Mpc MV, 2023 CF4 Table1; DOI 10.1093/mnras/stad1984'},
      'CF4_2023_200hMpc':{'v':419.,'sv':36.,'window':'200 h^-1 Mpc MV, 2023 CF4 Table1; DOI 10.1093/mnras/stad1984'},
    }
    dipole={
      'CMB_total_dipole_beta_dominated':{
         'e1':float(np.linalg.norm(json.loads((ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json').read_text())['beta_xyz'])),
         'meaning':'observer Doppler dominated total CMB dipole; NOT necessarily fundamental intrinsic radiation source'},
      'legacy_S3_matter_number_counts_NOT_CMB':{
         'e1':.001476,'meaning':'original model S3 source is number-count anomaly, NOT CMB radiation temperature epsilon1'},
      'zero_CMB_intrinsic_dipole_sensitivity_only':{
         'e1':0.,'meaning':'zero intrinsic dipole assuming observed dipole entirely kinematic; hypothetical physical scenario'}
    }
    all_maps={}
    rows=[]
    for name,entry in source['selected_original_T_and_P_features'].items():
        spectrum=entry['temperature_tensors']
        eps2=float(scalar_proxy_from_Cl(spectrum[0],2))
        eps3=float(scalar_proxy_from_Cl(spectrum[1],3))
        all_maps[name]={'C2':spectrum[0],'C3':spectrum[1],
                        'epsilon2_explicit_sqrtCl_over_T0':eps2,
                        'epsilon3_explicit_sqrtCl_over_T0':eps3}
        for dkey,dval in dipole.items():
            bound=mes_scenario_ceiling(dval['e1'],eps2,eps3)
            for key,flow in reported_bulk.items():
                tr=legacy_pushforward_of_external_bulk_proxy(
                    flow['v'],flow['sv'],eps2,eps3,eps1_ref=dval['e1'],
                    draws=50000,seed=20261015)
                rows.append({'planck_processing_name':name,'dipole_scenario':dkey,
                   'bulk_flow_survey_window':key,'bound':bound,'conditional_pushforward':tr})
    central=next(r for r in rows if r['planck_processing_name']=='SMICA_FULL'
       and r['dipole_scenario']=='CMB_total_dipole_beta_dominated'
       and r['bulk_flow_survey_window']=='CF4_2023_200hMpc')
    ceil=central['bound']['Sigma2_max']
    with np.load(CF4/'conditional_fiducial_stf2_proxy_draws.npz',allow_pickle=False) as f:
        a=np.asarray(f['five_stf_shear_proxy'],float)
    proxy_shear2=np.sum(a*a,axis=1)/6
    ratio=np.quantile(proxy_shear2/ceil,[.025,.16,.5,.84,.975])
    result={
     'schema':'htt.legacy-kinematical-defect-3layer-actual-CF4-Planck-source-bridge/1',
     'scientific_status':'EXECUTED_CONDITIONAL_EXPLORATORY_PUSHFORWARD_NO_PHYSICAL_BIANCHI_POSTERIOR',
     'uploaded_legacy_main_FINAL_pdf_sha256':PDFSHA,
     'uploaded_legacy_HTT_zip_sha256':V2SHA,
     'uploaded_code_package_zip_sha256':'f3a27b49972c3139824a72faf97ce7fff1b96f487c9d2669f1ebc606fd9dee66',
     'old_version_HTT_zip_still_mislabels_old_bulk_as_CF4':old['dipole_observations']['cf4_watkins_2023'],
     'attached_later_code_package_explicitly_labels_2009_COMPOSITE_correction':True,
     'reference_legacy_FLRW_tilt_evidence_metadata':next(x for x in ev if x['tag']=='FLRW_tilt'),
     'reported_bulk_inputs_all_distinct_window':reported_bulk,
     'reported_dipole_scenarios_with_admissibility':dipole,
     'actual_same_sky_planck_map_multipole_scalar_conventions':all_maps,
     'source_scenario_pushforwards':rows,
     'fiducial_2023_CF4_R200_scenario':central,
     'naive_application_of_actual_CF4_angular_STF2_proxy_to_legacy_MES_ceiling':{
       'ratio_025_16_50_84_975':ratio.tolist(),
       'assumption':'ASSUME actual CF4 angular Hubble residual is global Bianchi geometry shear solely for falsification stress test',
       'result_scope':'INVALID_PHYSICAL_MAPPING, NOT A MES REJECTION OR COSMIC_SHEAR_DETECTION'},
     'actual_shear_vorticity_acceleration_background_posterior':'NOT_IDENTIFIED_BY_THE_USED_SOURCE_DATA',
     'velocity_to_global_tilt_model':'HYPOTHETICAL ONLY; different survey radius bulk-flow not global background tilt',
     'CMB_dipole_MES_caveat':'actual observer Doppler dipole may be local; number-count dipole cannot replace CMB epsilon1 without derived physical transfer',
     'same_sky_maps_statistical_independence':'NONE; nine source processing choices are one sky',
     'output_type':'prior/assumption-conditioned deterministic distribution, not reconstructed old dynesty posterior or new Bayes evidence',
     'wall_seconds':time.perf_counter()-start,'peak_rss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# Legacy x→Q→Π의 실제 Planck·CF4 조건부 전달',
      '','사용자가 준 main_FINAL.pdf의 2.7, 6, 7.8절의 수학적 map을 그대로 유지하되 새 관측물리 해석은 보류.',
      '첨부 최신 code_package의 obs_defaults.json에는 기존 400±80 km/s 출처가 2009 COMPOSITE라고 명시돼 있다.',
      '2009 원본과 Watkins CF4 2023 R150/R200은 서로 다른 survey window이며 후자끼리는 독립 표본이 아니다.',
      '',
      '| source window | 1D mean±sigma km/s |', '|---|---:|']
    for key,bb in reported_bulk.items():lines.append(f"| {key} | {bb['v']}±{bb['sv']} |")
    lines+=['','## 실제 SMICA full의 C2,C3 scalar rms, flat/orthogonal legacy x=Ωtilt 예시',
      '| source | epsilon1 assignment | x_median | x_max | Q_median | Pi(Q>0.05) |',
      '|---|---|---:|---:|---:|---:|']
    for row in rows:
        if row['planck_processing_name']!='SMICA_FULL':continue
        x=row['conditional_pushforward']
        lines.append(f"| {row['bulk_flow_survey_window']} | {row['dipole_scenario']} | {x['x_quantiles'][2]:.5g} | {x['MES_ceiling']:.5g} | {x['occupancy_quantiles'][2]:.5g} | {x['exceedance_probability_by_threshold']['0.05']:.4g} |")
    lines +=['',f"실제 CF4 local angular STF proxy Sigma²를 무비판적으로 동종 배경 shear로 등치하면 MES ceiling 대비 형식적 비율 median={ratio[2]:.4g}, 95%=[{ratio[0]:.4g},{ratio[4]:.4g}].",
      '이 불일치는 legacy MES 위반 검출이 아니라 survey/structure/nuisance 포함 local angular residual을 global background shear라고 잘못 식별하는 가정을 검증한 예제다.',
      'W2·A2의 상한은 posterior가 아니며, 본 데이터는 geometry-frame omega/4-accel의 진짜 likelihood를 제공하지 않는다.',
      '같은 Planck 하늘을 처리한 9개 map의 epsilon_l은 독립 관측이 아니다.',
      'Legacy S3 number-count epsilon1은 이론적 MES CMB epsilon1이 아니며 cross-domain transfer 없이는 MES bound 입력으로 승인할 수 없다.',
      '2009+2023 bulk 자료는 별개 surveys/windows이므로 합산 독립 likelihood를 만들지 않았다.']
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    fig,axs=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
    pick=[r for r in rows if r['planck_processing_name']=='SMICA_FULL' and r['dipole_scenario']=='CMB_total_dipole_beta_dominated']
    for j,row in enumerate(pick):
        a=row['conditional_pushforward']['occupancy_quantiles']
        axs[0].plot([a[0],a[-1]],[j,j],linewidth=2)
        axs[0].plot([a[2]],[j],marker='o')
    axs[0].set_yticks(range(3),[r['bulk_flow_survey_window'] for r in pick],fontsize=7)
    axs[0].set(xlabel='Illustrative Q median and 95% range',
               title='Published speed windows: not homogeneous cosmic tilt')
    for dkey,dd in dipole.items():
        val=[mes_scenario_ceiling(dd['e1'],s['epsilon2_explicit_sqrtCl_over_T0'],s['epsilon3_explicit_sqrtCl_over_T0'])['Sigma2_max'] for s in all_maps.values()]
        axs[1].plot([min(val),max(val)],[dkey,dkey],linewidth=2,marker='o')
    axs[1].set_xscale('log')
    axs[1].set(xlabel='Legacy Sigma2 ceiling (explicit epsilon source)',title='Nine same-sky Planck processing choices')
    axs[1].tick_params(axis='y',labelsize=7)
    fig.savefig(out/'legacy_conditioned_defect_and_MES_source_sensitivity.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'n_scenario_rows':len(rows),'central':{
      'source':central['bulk_flow_survey_window'],
      'tilt_defect_median':central['conditional_pushforward']['x_quantiles'][2],
      'Q_median':central['conditional_pushforward']['occupancy_quantiles'][2],
      'MES_ceiling':ceil},
      'naive_localSTF_over_backgroundMES_median':ratio[2],
      'wall_seconds':result['wall_seconds']},indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    run(a.output_dir)
