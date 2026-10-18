#!/usr/bin/env python3
"""Actual 24 published grouped SN Ia moduli: shared-calibration gauge study.

The exact Gaussian identities and selected-condition differences are executed
with release-literal observations. Not a cosmological H0, anisotropy or
physical selected survey likelihood: SN group selection, latent group velocity,
source selection and full released calibration covariance remain unmeasured.
"""
from __future__ import annotations

import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np

from obsstat.catalogs.cf4_raw import load_authenticated_cf4_raw_groups
from obsstat.cf4_shared_selected_law import (
    uncalibrated_distance_model,combined_distance_uncertainty,
    shared_calibration_gaussian_logpdf,profiled_common_offset_chisq,
    fit_intercept_and_dipole,gaussian_preselection_loglik,
    gaussian_slot_conditioned_loglik
)

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/'docs/observational_reboot_20261014/results/cf4/selected_v2/source_subset_receipt.json'
C_KM_S=299792.458


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()


def run(input_root,out):
    if out.exists():raise ValueError('fresh output directory required')
    t0=time.perf_counter()
    meta=json.loads(RECEIPT.read_text())
    src=meta['source_files']
    cat=load_authenticated_cf4_raw_groups(
        input_root/'table3.dat.gz',input_root/'table4.dat.gz',
        expected_table3_sha256=src['workdir/raw/cf4_full/table3.dat.gz']['sha256'],
        expected_table4_sha256=src['workdir/raw/cf4_full/table4.dat.gz']['sha256'])
    allowed=set(int(x) for x in meta['selected_group_ids'])
    idx=np.flatnonzero(np.isin(cat.group_id,np.array(sorted(allowed))))
    if len(idx)!=len(allowed)!=24 or set(cat.group_id[idx].tolist())!=allowed:
        raise ValueError('historic fixed CF4 cohort identity drift')
    if any(int(np.any(np.asarray(cat.selection[k])[idx]>0)) for k in
           ('o_DMfp','o_DMtf','o_DMsbfo','o_DMsbfi','o_DMcal')):
        raise ValueError('selected SNIa-only method cohort contract breached')
    y=np.asarray(cat.selection['DMsnIa'][idx],dtype=float)
    err=np.asarray(cat.selection['e_DMsnIa'][idx],dtype=float)
    v=np.asarray(cat.vcmb_km_s[idx],dtype=float)
    ra=np.deg2rad(cat.ra_deg[idx])
    dec=np.deg2rad(cat.dec_deg[idx])
    n=np.stack((np.cos(dec)*np.cos(ra),
                np.cos(dec)*np.sin(ra),np.sin(dec)),axis=1)
    delta=np.round(np.asarray(cat.dmzp[idx]-y),3)
    delta_values,delta_counts=np.unique(delta,return_counts=True)
    common={f'{value:+.3f}':int(count) for value,count in zip(delta_values,delta_counts)}
    comparison={
        'exact_published_decimal_offset_histogram_mag':common,
        'paired_observations_not_independent':True,
        'released_e_DMsnIa_min_median_max_mag':[float(err.min()),float(np.median(err)),float(err.max())],
        'published_group_count':int(cat.row_count),
        'selected_cohort_count':len(idx),
        'selected_cohort_hash_prior':meta['packet_sha256'],
        'selected_ids_sha256_sorted':hashlib.sha256(np.asarray(cat.group_id[idx],dtype='<i8').tobytes()).hexdigest(),
        'distinct_rows_not_common_-0.147':[
            {'id':int(cat.group_id[i]),'Delta_DMZP_minus_DMsnIa_mag':float(delta[j])}
            for j,i in enumerate(idx) if not np.isclose(delta[j],-.147,rtol=0,atol=1e-9)],
        'source_columns':['table3: DMsnIa, e_DMsnIa, o_DMsnIa, Vcmb, RAdeg, DEdeg',
                          'table4: DMzp, e_DMzp; DESCRIPTIVE DEPENDENT COMPARISON ONLY'],
    }
    ref=70.
    baseline=uncalibrated_distance_model(v,ref)
    observations=[]
    for sigma_v in (0.,150.,300.,500.):
        sig=combined_distance_uncertainty(err,v,sigma_v)
        morph=fit_intercept_and_dipole(y-baseline,n,sig)
        prof=[profiled_common_offset_chisq(y,uncalibrated_distance_model(v,H),sig)
              for H in (65.,70.,75.,80.)]
        if np.max(np.abs(np.asarray(prof)-prof[0]))>1e-10:
            raise ValueError('free shared zero-point must be exactly H gauge invariant')
        morph['dipole_covariance']=np.asarray(morph['dipole_covariance']).tolist()
        observations.append({
          'scenario_velocity_width_km_s':sigma_v,
          'sample_only_WLS_intercept_and_angular_dipole':morph,
          'profiled_intercept_chisq_invariant_under_proxy_H':prof,
          'model_restriction':'fixed vCMB/c proxy, first-order velocity-modulus scatter; no physical ray, no selected-survey sampling law'})
    shared=[]
    lower=np.full(len(y),31.)
    upper=np.full(len(y),35.6)
    if not np.all((y>=lower)&(y<=upper)):
        raise ValueError('counterfactual fixed method modulus sensitivity support not covering data')
    for tau in (0.,.05,.10,.30):
        sig=combined_distance_uncertainty(err,v,300.)
        normal=shared_calibration_gaussian_logpdf(y,baseline,sig,tau)
        pre=gaussian_preselection_loglik(y,baseline,sig,tau,lower,upper,nquad=96)
        slot=gaussian_slot_conditioned_loglik(y,baseline,sig,tau,lower,upper,nquad=96)
        shared.append({
          'assumed_sigma_shared_zero_mag':tau,
          'implied_sigma_log_H_scale_ln':float(np.log(10)/5*tau),
          'conditional_joint_normal_logpdf':normal,
          'counterfactual_cut_[31,35.6]_preselection_loglik':pre,
          'counterfactual_cut_[31,35.6]_slotconditioned_loglik':slot,
          'loglaw_difference_pre_minus_slot':pre-slot,
          'model_role':'illustration under assumed Gaussian population/cut; not CF4 observed survey selection or calibrated likelihood'
        })
    result={
      'schema':'htt.CF4-release-method-calibration-gauge/1',
      'status':'ACTUAL_CF4_METHOD_DATA_PLUS_EXACT_CALIBRATION_GAUGE_AND_COUNTERFACTUAL_SELECTION',
      'scope':'24 actual SNIa-group raw method modulus observations; observed cohort selected through historical DMzp and method flags',
      'not':'not a measured H0, source acceleration, physical q, anisotropy, unique shear or calibrated full-survey selection',
      'source_commit':'13d8d85fa470d645d008986e8f77d8d0f70fdf54',
      'raw_root':str(input_root),
      'source_sha256':cat.source_hashes,
      'raw_release_readme_sha256':digest(input_root/'ReadMe'),
      'subset_receipt_sha256':digest(RECEIPT),
      'sample':comparison,
      'model':{
        'reference_proxy_scale_km_s_Mpc':ref,
        'distance_model':'mu_reference=25+5 log10(Vcmb_km_s / H_reference), with CMB-frame reported group Vcmb, not local source redshift',
        'measurement_model':'one raw method SN Ia modulus per group, sigma_i=e_DMsnIa release; optional independent peculiar velocity scenario sigma_mag=(5/ln10)sigma_v/Vcmb',
        'shared_calibration':'eta~N(0,tau^2) counterfactual prior; tau not inferred from these selected data',
        'gauge':'for unanchored eta and unanchored Hscale, only eta-5log10(H/Href) identified; profiling eta gives H-invariant objective',
        'selection_counterfactual':'for demonstration only, independent per-slot *method modulus* [31,35.6] mag truncation; NOT actual historical DMzp eligibility 31..35; both shared preselection and slot-conditioning coherent but DIFFERENT sampling experiments',
        'physical_full_law_required':['individual survey-source eligibility conditioned on raw observations, not the published resultant DMzp',
          'shared SNIa absolute calibration/Cepheid-TRGB-Maser covariance and group/event overlap',
          'latent source motion redshift and distances on a single observer/source congruence',
          'actual selection normalization of full group-parent catalog, preselection shared eta',
          'finite-optical-distance Jacobi remainder with valid units and source frame']
       },
       'velocity_scenarios':observations,'zero_priors_and_selection_scenarios':shared,
       'elapsed_seconds':time.perf_counter()-t0,
       'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    doc=['# 실제 CF4 SNIa method field 공유 영점·선택법칙 분석',
       '',
       f"원자료: 그룹 {cat.row_count}, 저장된 정확한 SNIa-only 24개 그룹.",
       'DMzp와 method-specific DMsnIa는 공유 원본의 의존 파생물이며 독립 data likelihood를 곱하면 안 된다.',
       '',
       '| Published delta DMzp-DMsnIa (mag) | Group count |',
       '|---:|---:|']
    for val,count in common.items():doc.append(f'| {val} | {count} |')
    doc +=['','### 원본 Method-only 오류 및 속도폭 시나리오',
      '| Extra radial velocity σv (km/s) | Dipole norm in magnitude residual | Intercept-profile χ² |',
      '|---:|---:|---:|']
    for v in observations:
        m=v['sample_only_WLS_intercept_and_angular_dipole']
        doc.append(f"| {v['scenario_velocity_width_km_s']} | {m['dipole_norm_mag']:.5g} | {v['profiled_intercept_chisq_invariant_under_proxy_H'][0]:.4g} |")
    doc +=['','η shared calibration prior = 0, .05, .1, .3 mag is a *hypothetical input*; unspecified actual release cross-method calibration is not reconstructed.',
       'Hreference in the displayed formula is a redshift velocity/distance proxy. With unrestricted zero point, profile likelihood exactly independent of this H reference.',
       '',
       '| Assumed sigma_eta (mag) | Implied relative log-distance-scale sigma | Pre-minus-slot selected log likelihood (counterfactual) |',
       '|---:|---:|---:|']
    for v in shared:
        doc.append(f"| {v['assumed_sigma_shared_zero_mag']} | {v['implied_sigma_log_H_scale_ln']:.6g} | {v['loglaw_difference_pre_minus_slot']:.6g} |")
    doc +=['','The preselection/slot comparison uses counterfactual selection in method modulus [31,35.6], NOT the actual outcome-selected DMzp 31..35 + hash ordering. Do not use the resulting likelihood as a CF4 cosmological posterior.',
      'Direct fit of angular residual is a fixed-cohort phenomenological morphology, not generalized GR shear/acceleration/geodesicity.',
      'Exact Etherington reciprocity is an *upstream same-source-congruence requirement* for a future physical distance model, not implemented by using a crude Vcmb/Href proxy.',
      'Required next independent sources: per-survey selection flags and flux limits, SN event group membership, cross-method calibration covariance, source-frame true redshift and velocity law.']
    (out/'REPORT_KO.md').write_text('\n'.join(doc)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.5,3.6),layout='constrained')
    xs=[v['scenario_velocity_width_km_s'] for v in observations]
    ys=[v['sample_only_WLS_intercept_and_angular_dipole']['dipole_norm_mag'] for v in observations]
    ax.plot(xs,ys,marker='o')
    ax.set(xlabel='Assumed extra independent radial-velocity width [km/s]',
           ylabel='Fixed-cohort residual dipole norm [mag]',
           title='Scenario only: source-bound CF4 SN Ia method channel')
    fig.savefig(out/'cf4_snia_method_scenario.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'status':result['status'],'release_calibration_hist':common,
          'gauge_chisq_by_velocity_width':[(v['scenario_velocity_width_km_s'],v['profiled_intercept_chisq_invariant_under_proxy_H'][0]) for v in observations],
          'selection_law_pre_minus_slot':[v['loglaw_difference_pre_minus_slot'] for v in shared],
          's':result['elapsed_seconds']},indent=2))
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--raw-root',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    run(args.raw_root,args.output_dir)
