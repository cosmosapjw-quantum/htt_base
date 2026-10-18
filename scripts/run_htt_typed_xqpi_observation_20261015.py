#!/usr/bin/env python3
"""Real-source Planck/CF4 scenario statistics with PR124 and PR521 contracts.

A conditional Gaussian published-window velocity law becomes a legacy x,Q,Pi
law ONLY on the explicitly assumed bulk=homogeneous-tilt branch. This
does not measure physical Bianchi kinematics, signed x or total filling.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,resource,sys,time
from pathlib import Path
import numpy as np
from htt.infer.conditional_legacy_pushforward import ConditionalDraw,conditional_legacy_image
from obsstat.typed_xqpi_observation_bridge import (
    paired_velocity_quantile_atoms,conditionally_matter_tilt,analytic_conditional_tail,
    nine_same_sky_geodesic_anchor_scenarios,get_legacy_ceiling,strict_known_pi,
)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/legacy_defect_actual_source_bridge_v1/result.json'
DIPOLE=ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json'
R2=ROOT/'docs/observational_upgrade_r2/R2-04'
ADAPT=R2/'sources/code/legacy_adapter.py'
LEGACY=R2/'sources/sources/HTT/HTT'
RETURN=R2/'RETURN.json'
THRESH=(.01,.05,.1,.5,1.)
N=2048
OM=.3153

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):h.update(block)
    return h.hexdigest()

def adapter():
    locked=json.loads(RETURN.read_text())['files_sha256']
    code={
      'docs/observational_upgrade_r2/R2-04/sources/code/legacy_adapter.py':ADAPT,
      'docs/observational_upgrade_r2/R2-04/sources/sources/HTT/HTT/htt/ssot.py':LEGACY/'htt/ssot.py',
      'docs/observational_upgrade_r2/R2-04/sources/sources/HTT/HTT/htt/bounds.py':LEGACY/'htt/bounds.py',
    }
    for key,p in code.items():
        if sha(p)!=locked[key]:
            raise ValueError('PR521 locked source bytes changed '+key)
    spec=importlib.util.spec_from_file_location('scoped_r204_legacy_adapter_for_xqpi',ADAPT)
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    spec.loader.exec_module(mod)
    return mod.LegacyAdapter(LEGACY,mod.AnalysisContract(
        'typed-legacy-scenario-loop7',
        'hypothetical-homogeneous-matter-geometry-tilt',
        'flat-comparator',
        'legacy-VA02-defect-identity',
        'published-speed-gaussian-scenario-not-posterior'),
        expected_hashes={'htt/ssot.py':sha(LEGACY/'htt/ssot.py'),
                         'htt/bounds.py':sha(LEGACY/'htt/bounds.py')})

def quants(x):
    return [float(t) for t in np.quantile(x,(.025,.16,.5,.84,.975))]

def run(destination):
    if destination.exists():
        raise ValueError('create-only destination needed')
    ti=time.perf_counter()
    source=json.loads(SOURCE.read_text())
    maps=source['actual_same_sky_planck_map_multipole_scalar_conventions']
    windows=source['reported_bulk_inputs_all_distinct_window']
    if len(maps)!=9 or set(windows)!={'WFH_2009_COMPOSITE_50hMpc',
                        'CF4_2023_150hMpc','CF4_2023_200hMpc'}:
        raise ValueError('actual observational source windows changed')
    e1=float(np.linalg.norm(json.loads(DIPOLE.read_text())['beta_xyz']))
    modern=nine_same_sky_geodesic_anchor_scenarios(maps)
    frozen=adapter()
    allrows={}
    audit={}
    for key,w in windows.items():
        ids,v=paired_velocity_quantile_atoms(w['v'],w['sv'],N)
        mass=np.full(N,1/N)
        ot=conditionally_matter_tilt(v,OM)
        allrows[key]={}
        for mapkey,me in maps.items():
            denom=get_legacy_ceiling(e1,me['epsilon2_explicit_sqrtCl_over_T0'],
                                         me['epsilon3_explicit_sqrtCl_over_T0'])
            analytical={str(q):analytic_conditional_tail(q,w['v'],w['sv'],OM,denom) for q in THRESH}
            sampled={str(q):strict_known_pi(ot,mass,denom,q) for q in THRESH}
            if max(abs(analytical[str(q)]-sampled[str(q)]) for q in THRESH)>1/N+1e-12:
                raise ArithmeticError('independent analytic Gaussian CDF check failed')
            allrows[key][mapkey]={
              'bulk_source_reported_km_s':w,
              'model':'Scenario V=max(0,N(mu,sd)); beta_global assumed V/c; Sigma2=W2=curvature=0 by fiat',
              'legacy_historical_shear_only_denominator':denom,
              'legacy_conditional_Q_quantiles':quants(ot/denom),
              'legacy_conditional_x_quantiles':quants(ot),
              'analytic_tail':analytical,'same_latents_midpoint_tail':sampled,
              'PR124_typed_geodesic_shear_proxy':modern[mapkey]['registered_geodesic_sigma_sector_anchor'],
              'admission':'SCENARIO_DIAGNOSTIC_ONLY',
            }
        denom=allrows[key]['SMICA_FULL']['legacy_historical_shear_only_denominator']
        draws=tuple(ConditionalDraw(latent,0.,0.,float(tilt),0.,denom,identifiable=True)
                    for latent,tilt in zip(ids,ot))
        joint=conditional_legacy_image(draws,frozen,
              source_id='PUBLISHED_SPEED_'+key,joint_id='PUBLISHED_PAIRED_SPEED_'+key,
              weights=tuple(mass),law_kind='SAMPLING',q_thresholds=THRESH)
        if (joint['law_kind']!='SAMPLING' or joint['x'].undefined_mass!=0
            or joint['Q'].undefined_mass!=0 or tuple(joint['draw_ids'])!=ids):
            raise ArithmeticError('R2-04 identity/measure contract violated')
        for q,item in zip(THRESH,joint['Pi_intervals']):
            if not np.isclose(item['lower'],allrows[key]['SMICA_FULL']['same_latents_midpoint_tail'][str(q)],atol=1e-12,rtol=0):
                raise ArithmeticError('R2-04 strict boundary law diverged')
        # Missing actual geometry-sector fields cannot be filled by zeros.
        unknown=tuple(ConditionalDraw(latent,None,None,None,None,None,identifiable=False) for latent in ids)
        unspecified=conditional_legacy_image(unknown,frozen,
              source_id='PUBLISHED_SPEED_'+key,joint_id='UNIDENTIFIED_PHYSICAL_DEFECT_'+key,
              weights=tuple(mass),law_kind='SAMPLING',q_thresholds=THRESH)
        if (unspecified['x'].undefined_mass!=1 or unspecified['Q'].undefined_mass!=1 or
            any((item['lower'],item['upper'])!=(0.,1.) for item in unspecified['Pi_intervals'])):
            raise ArithmeticError('missing physical sector mass improperly dropped')
        audit[key]={
          'source':'PR521 frozen LegacyAdapter.departure_pushforward + FiniteJointSource',
          'number_of_matched_atoms':len(ids),
          'law_kind':joint['law_kind'],'frozen_adapter_hashes':joint['source_sha256'],
          'actual_PR521_finite_Pi_lower_by_threshold':{
            str(q):float(item['lower']) for q,item in zip(THRESH,joint['Pi_intervals'])},
          'strict_event_boundary_masses':{
            str(q):float(item['known_boundary_mass']) for q,item in zip(THRESH,joint['Pi_intervals'])},
          'physical_unknown_x_mass':unspecified['x'].undefined_mass,
          'physical_unknown_Q_mass':unspecified['Q'].undefined_mass,
          'physical_Pi_unidentified_intervals':[
            {'threshold':float(q),'lower':p['lower'],'upper':p['upper']}
            for q,p in zip(THRESH,unspecified['Pi_intervals'])],
        }
    source_spread={}
    for key,sub in allrows.items():
        source_spread[key]={str(q):[float(min(z['analytic_tail'][str(q)] for z in sub.values())),
                                    float(max(z['analytic_tail'][str(q)] for z in sub.values()))]
                            for q in THRESH}
    result={
      'schema':'htt.typed_pr248_258_and_pr521_xqpi_actual_inputs/1',
      'science_status':'ACTUAL_MAPS_REPORTED_SPEEDS_CONDITIONAL_HISTORICAL_XQPI_ONLY_NOT_COSMOLOGICAL_POSTERIOR',
      'source_prs':['https://github.com/cosmosapjw-quantum/htt_base/pull/360',
                    'https://github.com/cosmosapjw-quantum/htt_base/pull/362',
                    'https://github.com/cosmosapjw-quantum/htt_base/pull/363',
                    'https://github.com/cosmosapjw-quantum/htt_base/pull/364',
                    'https://github.com/cosmosapjw-quantum/htt_base/pull/521'],
      'parent_loop6_sha256':sha(SOURCE),'PR521_Return_sha256':sha(RETURN),
      'registered_PR124_MES_table_sha256':sha(ROOT/'docs/generated/pr124_mes_authority_table.json'),
      'dipole_source_sha256':sha(DIPOLE),
      'active_PR124_geodesic_algebraic_e1_zero_scenarios':modern,
      'source_legacy_bulk_scenario_by_same_sky_planck_map':allrows,
      'PR521_matched_finite_joint_pushforward':audit,
      'same_sky_processing_tail_minmax_not_independent_CMB_realizations':source_spread,
      'n_velocity_windows':len(windows),
      'n_correlated_same_sky_planck_products':len(maps),
      'scenario_count':sum(map(len,allrows.values())),
      'per_window_same_latent_atoms':N,
      'source_assumptions':[
       'Legacy historical observed solar-motion dipole e1 used only to reproduce old shear denominator; not accepted MES geodesic residual e1',
       'Observed nine Planck maps are same-sky correlated alternative processing, all share velocity-latent IDs',
       'Reported Gaussian V speed magnitudes truncated at zero, not a physical joint posterior',
       'CF4 R150 and R200 share real survey and cannot be multiplied as independent sources',
       'Uniform matter/geometry tilt beta=V/c from finite window is unverified (not measured)',
       'Sigma2=W2=curvature=0 are hypotheses for toy conditional branch, not observational determinations',
       'Geodesic verified MES shear/vorticity anchors are separate one-way channel stresses and no total x ceiling',
       'Planck eps_l measured as sqrt(Cl)/T0 are not the covariant almost-EGS bounded multipoles plus derivatives'],
      'physical_posteriors':{
        'geometry_frame_shear':None,'geometry_frame_vorticity':None,
        'matter_frame_four_acceleration':None,'homogeneous_tilt':None,
        'full_signed_x':None,'admissible_total_filling_Q':None,
        'physical_exceedance_Pi':None,'cosmological_Bayes_factor':None},
      'runtime_seconds':time.perf_counter()-ti,
      'runtime_peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    destination.mkdir(parents=True)
    (destination/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    qt=np.linspace(0,.24,241)
    for key,w in windows.items():
        den=allrows[key]['SMICA_FULL']['legacy_historical_shear_only_denominator']
        ax.plot(qt,[analytic_conditional_tail(q,w['v'],w['sv'],OM,den) for q in qt],label=key)
    ax.set(xlabel='Threshold historical Q (signed x / shear-only ceiling)',
           ylabel='Scenario conditional probability Q > threshold',
           title='PR521 finite Gaussian published-window scenarios; no physical posterior')
    ax.legend(fontsize=8)
    fig.savefig(destination/'conditional_exceedance_three_published_windows.png',dpi=170)
    plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    xx=np.arange(len(modern)); names=list(modern)
    ax.plot(xx,[modern[n]['registered_geodesic_sigma_sector_anchor'] for n in names],
            marker='o',label='PR124 shear geodesic algebraic anchor')
    ax.plot(xx,[modern[n]['registered_geodesic_omega_sector_anchor'] for n in names],
            marker='x',label='PR124 vorticity geodesic algebraic anchor')
    ax.set_yscale('log');ax.set_xticks(xx,names,rotation=38,ha='right')
    ax.set(ylabel='Dimensionless squared bound; eps1=0 scenario (NOT physical)',
           title='Same sky Planck processing source: MES geodesic algebraic sensitivity')
    ax.legend(fontsize=8)
    fig.savefig(destination/'registered_mes_geodesic_same_sky_source_sensitivity.png',dpi=170)
    plt.close(fig)
    report=[
      '# 최신 PR typed x/Q/Pi 실제 관측입력 적용 (conditional, 2026-10-15)',
      '',
      'PR #360 (248–252), #362–364, #521와 PR124 exact geodesic MES를 연결했다.',
      'PR521 immutable archived code를 실제로 호출, 2048 paired finite atoms per window를 이용해 signed x, Q, strict Pi를 계산했다.',
      '이 값은 관측자료 원천에 근거한 **조건부 시나리오 분포**이며 실제 geometry-field posterior가 아니다.',
      '',
      '| published source window | conditional median historical Q | exact Pi(Q>0.1) | PR521 finite Pi(Q>0.1) |',
      '|---|---:|---:|---:|']
    for k in windows:
        row=allrows[k]['SMICA_FULL']
        report.append(f"| {k} | {row['legacy_conditional_Q_quantiles'][2]:.7g} | {row['analytic_tail']['0.1']:.7g} | {audit[k]['actual_PR521_finite_Pi_lower_by_threshold']['0.1']:.7g} |")
    report.extend([
      '','PR521 adapter full sectors unknown -> x and Q undefined mass=1, Pi=[0,1] for all selected thresholds.',
      'This distinction is *no identified full posterior*, not evidence that all physical Q values are equally probable.',
      'Legacy e1 total CMB solar-motion and source sqrtCl/T0 are NOT registered geodesic MES covariant epsilon prior.',
      'Registered PR124 uses shear Bsigma=(5/3)e1+3e2+(3/7)e3; geodesic vorticity Bomega=(10/3)e1+(2/15)e2, acceleration and curvature NO_MES_ANCHOR.',
      'The legacy shear denominator cannot physically normalize tilt, curvature and vorticity as a universal total-x ceiling.',
      'WFH 2009 composite 407±81 km/s must not be mislabeled 2023 CF4. CF4 2023 R150 and R200 share raw sources and are correlated.',
      'Same sky 9 Planck alternative map products must not be counted as nine independent CMB samples.',
      'No current Bianchi H0/beta/shear/omega/dot-u posterior, no cosmological evidence, no observed Pi is claimed.'
    ])
    (destination/'REPORT_KO.md').write_text('\n'.join(report)+'\n')
    print(json.dumps({
      'status':result['science_status'],
      'window_results':{
         key:{'Q_median':allrows[key]['SMICA_FULL']['legacy_conditional_Q_quantiles'][2],
               'Pi_Qgreater_0p1_exact':allrows[key]['SMICA_FULL']['analytic_tail']['0.1'],
               'Pi_Qgreater_0p1_R204':audit[key]['actual_PR521_finite_Pi_lower_by_threshold']['0.1'],
               'unknown_mass':audit[key]['physical_unknown_Q_mass']}
         for key in windows},
      'n_scenarios':result['scenario_count'],
      'MES_sigma_range':[
        min(v['registered_geodesic_sigma_sector_anchor'] for v in modern.values()),
        max(v['registered_geodesic_sigma_sector_anchor'] for v in modern.values())],
      'runtime_sec':result['runtime_seconds']
    },indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args()
    run(a.output_dir)
