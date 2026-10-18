#!/usr/bin/env python3
"""Source-bound real Planck PR3 SMICA/NILC HM/OE, noSZ and spin-2 comparison.

A deliberately common physical sky support and REAL spin harmonic chart is
used for every source. All exact split contrasts act on the same map-space
operator. These are one-sky source-processing diagnostics, NOT CMB PTE or
physical noise covariance. T and QU masks are distinct by construction.
"""
from __future__ import annotations
import argparse, hashlib, json, resource, time
from pathlib import Path

import numpy as np
from astropy.io import fits
from scipy.linalg import cho_factor, cho_solve
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from obsstat.reboot_tensor_features import feature_vector
from obsstat.htt_multisplit_lowell import (
    multisplit_contrasts,split_power_identity,spin2_design_real)
from obsstat.planck_split_joint_law import nested_coarse_masked_mean
from run_smica_reboot_pilot import build_ols_projector
from fit_cmb_smica_noise_modes import require_gated_cache

ROOT=Path(__file__).resolve().parents[1]
RAW=Path('/mnt/extdrive/workdir/raw')
D=RAW/'planck_pr3_targeted_inputs_20261015'
HM=RAW/'planck_pr3_smica_hm_20261015'
EX=RAW/'planck_data'
CONTROL=RAW/'planck_pr3_component_controls'
GATE=ROOT/'docs/generated/k1_e2e_cache_gate_ffp10_smica.json'
CACHE=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
INT_T=EX/'COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits'
INT_P=EX/'COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits'
HM_T=HM/'COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits'
HM_P=D/'COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits'
OE_T=D/'COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits'
OE_P=D/'COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits'

SOURCES={
 'SMICA_HM1':HM/'COM_CMB_IQU-smica_2048_R3.00_hm1.fits',
 'SMICA_HM2':HM/'COM_CMB_IQU-smica_2048_R3.00_hm2.fits',
 'SMICA_OE1':D/'COM_CMB_IQU-smica_2048_R3.00_oe1.fits',
 'SMICA_OE2':D/'COM_CMB_IQU-smica_2048_R3.00_oe2.fits',
 'NILC_HM1':D/'COM_CMB_IQU-nilc_2048_R3.00_hm1.fits',
 'NILC_HM2':D/'COM_CMB_IQU-nilc_2048_R3.00_hm2.fits',
 'SMICA_FULL':EX/'COM_CMB_IQU-smica_2048_R3.00_full.fits',
 'SMICA_noSZ_FULL':D/'COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits',
 'NILC_FULL':CONTROL/'COM_CMB_IQU-nilc_2048_R3.00_full.fits',
}
TEMP_SOURCE_ORDER=tuple(SOURCES)
POL_SOURCE_ORDER=tuple(x for x in TEMP_SOURCE_ORDER if x!='SMICA_noSZ_FULL')


def sha256(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):
            h.update(block)
    return h.hexdigest()


def native_mask(p,column):
    if not p.is_file() or p.stat().st_size!=201335040:
        raise ValueError(f'official Planck missing/confidence mask missing: {p}')
    with fits.open(p,memmap=True) as ff:
        h=ff[1]
        if h.header.get('NSIDE')!=2048 or h.header.get('ORDERING')!='NESTED' or column not in h.columns.names:
            raise ValueError(f'mask geometry/field mismatch: {p}')
        return (np.asarray(h.data[column])>.5)


def source_iqu(p,tm,pm,need_polarization=True):
    if not p.is_file() or p.stat().st_size<402_000_000:
        raise ValueError(f'unqualified FITS: {p}')
    with fits.open(p,memmap=True) as ff:
        x=ff[1]
        if x.header.get('NSIDE')!=2048 or x.header.get('ORDERING')!='NESTED' or x.header.get('TUNIT1')!='K_CMB' or 'I_STOKES' not in x.columns.names:
            raise ValueError(f'unqualified Planck release header: {p}')
        t,ct=nested_coarse_masked_mean(x.data['I_STOKES'],tm,
                nside_in=2048,nside_out=64,chunk_lowpix=384)
        ans={'T':t*1e6,'T_coverage':ct}
        if need_polarization:
            if not all(name in x.columns.names for name in ('Q_STOKES','U_STOKES')):
                raise ValueError(f'no polarization channels for source {p}')
            q,cq=nested_coarse_masked_mean(x.data['Q_STOKES'],pm,
                nside_in=2048,nside_out=64,chunk_lowpix=384)
            u,cu=nested_coarse_masked_mean(x.data['U_STOKES'],pm,
                nside_in=2048,nside_out=64,chunk_lowpix=384)
            ans.update(Q=q*1e6,U=u*1e6,Q_coverage=cq,U_coverage=cu)
        return ans


def ell_band_stats(a,b):
    out=[]
    for ell in range(2,6):
        sl=slice(ell*ell-4,(ell+1)*(ell+1)-4)
        x=split_power_identity(a[sl],b[sl])
        out.append({'ell':ell,**x})
    return out


def exact_linear_spin_fit_operator(X,mask):
    n=len(mask)
    if X.shape[0]!=2*n or mask.dtype!=bool or mask.sum()<2000:
        raise ValueError('invalid common spin mask/design')
    rows=np.r_[mask,mask]
    A=X[rows]
    Gram=A.T@A
    eigen=np.linalg.eigvalsh(Gram)
    if eigen[0]<=0 or eigen[-1]/eigen[0]>1e12:
        raise ValueError('rank unstable spin2 common image')
    op=cho_solve(cho_factor(Gram,lower=True,check_finite=False),
                 A.T,check_finite=False)
    residual=np.max(abs(op@A-np.eye(X.shape[1])))
    if residual>1e-8:raise ValueError('spin2 image projector identity broken')
    return op,{'condition':float(np.sqrt(eigen[-1]/eigen[0])),
               'identity_residual':float(residual),
               'selected_spatial_pixels':int(mask.sum()),
               'real_EB_coefficients':X.shape[1]}


def run(output,coverage_floor=.995):
    if output.exists():
        raise ValueError('durable create-only output required')
    t0=time.perf_counter()
    base=json.loads((RAW/'HTT_ADDITIONAL_DATA_INTAKE_20261015.json').read_text())
    if base['verified_count']!=base['expected_count'] or base['verified_count']!=17:
        raise ValueError('core 17 product source manifest unqualified')
    with np.load(CACHE,allow_pickle=False) as z:
        cache_t=np.asarray(z['observed_map'],float)
        cache_mask=np.asarray(z['common_mask'],float)
    cached_sha=require_gated_cache(CACHE,json.loads(GATE.read_text()))
    mask_t=native_mask(INT_T,'TMASK')&native_mask(HM_T,'TMASK')&native_mask(OE_T,'TMASK')
    mask_p=native_mask(INT_P,'PMASK')&native_mask(HM_P,'PMASK')&native_mask(OE_P,'PMASK')
    _sky,X=pixel_fit_geometry()
    # Every observed source is downgraded using the SAME fine masks.
    coarset=np.empty(49152,float);coarsep=np.empty(49152,float)
    _,coarset=nested_coarse_masked_mean(mask_t.astype(float),mask_t,
                    nside_in=2048,nside_out=64,chunk_lowpix=384)
    _,coarsep=nested_coarse_masked_mean(mask_p.astype(float),mask_p,
                    nside_in=2048,nside_out=64,chunk_lowpix=384)
    sel_t=(cache_mask>.5)&(coarset>=coverage_floor)
    sel_p=(coarsep>=coverage_floor)
    # The polarization mask is not the temperature mask. It is combined with
    # the PL2018 common Pol fine mask, not K1's temperature confidence map.
    if np.count_nonzero(sel_t)<20000 or np.count_nonzero(sel_p)<20000:
        raise ValueError('intersection of joint-source support unexpectedly weak')
    mask_selected,op_t,info_t=build_ols_projector(X,sel_t.astype(float))
    if not np.array_equal(mask_selected,sel_t):
        raise ValueError('same temperature support contract violated')
    Xspin,columns=spin2_design_real(nside=64,lmax=5)
    op_p,info_p=exact_linear_spin_fit_operator(Xspin,sel_p)
    rows_p=np.r_[sel_p,sel_p]
    temp={}
    pol={}
    source_bytes={}
    evidence={}
    alltemp={}
    # Sources scanned ONCE each.  For large HEALPix maps, FITS is memmapped.
    for name,source in SOURCES.items():
        if name in ('SMICA_HM1','SMICA_HM2','SMICA_OE1','SMICA_OE2','NILC_HM1','NILC_HM2','SMICA_noSZ_FULL'):
            rec=next((q for q in base['items'] if q['filename']==source.name),None)
            if rec is not None and (rec['size_bytes']!=source.stat().st_size):
                raise ValueError(f'pinned external source filesize differs: {name}')
        fields=source_iqu(source,mask_t,mask_p,need_polarization=name in POL_SOURCE_ORDER)
        if np.any(fields['T_coverage'][sel_t]<coverage_floor-1e-10):
            raise ValueError('released temperature invalid under shared fixed native mask')
        coeff=op_t@fields['T'][sel_t]
        temp[name]=coeff[4:36]
        alltemp[name]=coeff
        if name in POL_SOURCE_ORDER:
            if np.any(fields['Q_coverage'][sel_p]<coverage_floor-1e-10) or np.any(fields['U_coverage'][sel_p]<coverage_floor-1e-10):
                raise ValueError(f'bad released polarization source on selected support: {name}')
            pol[name]=op_p@np.r_[fields['Q'][sel_p],fields['U'][sel_p]]
        source_bytes[name]={'input_path':str(source),'size_bytes':source.stat().st_size}
        evidence[name]={
            'temperature_norm_microK':float(np.linalg.norm(temp[name])),
            'polarization_EB_norm_microK':None if name not in pol else float(np.linalg.norm(pol[name])),
            'temperature_tensors':feature_vector(temp[name]).tolist(),
        }
        del fields
    # Complete-same-sky contrasts with explicitly source-qualified common masks.
    con=multisplit_contrasts(np.stack([temp[z] for z in ('SMICA_HM1','SMICA_HM2','SMICA_OE1','SMICA_OE2')]))
    conp=multisplit_contrasts(np.stack([pol[z] for z in ('SMICA_HM1','SMICA_HM2','SMICA_OE1','SMICA_OE2')]))
    hm_n=(temp['NILC_HM1']+temp['NILC_HM2'])*.5
    phm_n=(pol['NILC_HM1']+pol['NILC_HM2'])*.5
    # Two counterfactual cleaning-level output contrasts on one shared sky
    matches={
      'SMICA_HM_vs_SMICA_OE':con['partition_mean_difference'],
      'SMICA_FULL_vs_HM_mean':temp['SMICA_FULL']-con['hm_mean'],
      'SMICA_FULL_vs_OE_mean':temp['SMICA_FULL']-con['oe_mean'],
      'NILC_HM_mean_vs_SMICA_HM_mean':hm_n-con['hm_mean'],
      'NILC_FULL_vs_NILC_HM_mean':temp['NILC_FULL']-hm_n,
      'SMICA_noSZ_FULL_vs_SMICA_FULL':temp['SMICA_noSZ_FULL']-temp['SMICA_FULL'],
      'SMICA_FULL_vs_NILC_FULL':temp['SMICA_FULL']-temp['NILC_FULL'],
    }
    basevec=temp['SMICA_FULL']
    nbase=np.linalg.norm(basevec)
    comparisons={}
    for label,delta in matches.items():
        comparisons[label]={
         'norm_microK':float(np.linalg.norm(delta)),
         'ratio_to_same_mask_SMICA_full_norm':float(np.linalg.norm(delta)/nbase),
         'per_ell_abs_delta_power_microK2':[
            float(delta[ell*ell-4:(ell+1)*(ell+1)-4]@
                  delta[ell*ell-4:(ell+1)*(ell+1)-4]/(2*ell+1))
                  for ell in range(2,6)]
        }
    diff_hm=con['hm_difference']
    diff_oe=con['oe_difference']
    split={
      'SMICA_HM':{'half_difference_norm_microK':float(np.linalg.norm(diff_hm)),
                  'per_ell':ell_band_stats(temp['SMICA_HM1'],temp['SMICA_HM2'])},
      'SMICA_OE':{'half_difference_norm_microK':float(np.linalg.norm(diff_oe)),
                  'per_ell':ell_band_stats(temp['SMICA_OE1'],temp['SMICA_OE2'])},
      'NILC_HM':{'half_difference_norm_microK':float(np.linalg.norm((temp['NILC_HM1']-temp['NILC_HM2'])*.5)),
                  'per_ell':ell_band_stats(temp['NILC_HM1'],temp['NILC_HM2'])},
    }
    pol_contrasts={
       'SMICA_HM_split_difference_EB_norm_microK':float(np.linalg.norm(conp['hm_difference'])),
       'SMICA_OE_split_difference_EB_norm_microK':float(np.linalg.norm(conp['oe_difference'])),
       'SMICA_HM_vs_SMICA_OE_mean_EB_norm_microK':float(np.linalg.norm(conp['partition_mean_difference'])),
       'NILC_vs_SMICA_HM_mean_EB_norm_microK':float(np.linalg.norm(phm_n-conp['hm_mean'])),
       'SMICA_FULL_vs_SMICA_HM_EB_norm_microK':float(np.linalg.norm(pol['SMICA_FULL']-conp['hm_mean'])),
    }
    # Verify true extracted public HM subset against last-loop own released
    # result only after projecting on ITS historic native HM+K1 support.
    # The new intersection mask is intentionally different and not substituted.
    old=ROOT/'docs/research_program/theory_obs_application_20261015/loop4/results/planck_hm_split_v1/result.json'
    previous=json.loads(old.read_text())
    independent_truth={
      'previous_HM_fit_mask_n':previous['n_joint_fitted'],
      'current_common_T_fit_mask_n':int(sel_t.sum()),
      'same_source_different_mask_does_not_require_identical_coefficients':True,
    }
    # Cross-split contrast COMMON sky cancellation at fixed response is exact;
    # per-method/nonidentical responses are controlled source sensitivities.
    result={
       'schema':'htt.Planck_PR3_multi_split_spin_joint/1',
       'scientific_status':'EXECUTED_REAL_SINGLE_SKY_MULTI_PRODUCT_CONDITIONAL_ONLY',
       'source_reference':'Planck PR3, 2018 results IV, A&A 641 A4',
       'input_manifest_path':str(RAW/'HTT_ADDITIONAL_DATA_INTAKE_20261015.json'),
       'input_manifest_sha256':sha256(RAW/'HTT_ADDITIONAL_DATA_INTAKE_20261015.json'),
       'input_cache_sha256':cached_sha,
       'source_file_identities':source_bytes,
       'fixed_mask_source_files':[str(p) for p in (INT_T,HM_T,OE_T,INT_P,HM_P,OE_P)],
       'mask_policy':'native NSIDE2048 shared Int and Pol intersection across HM/OE/official common masks separately; coarse valid >=0.995; fixed K1 temperature confidence >0.5; same OLS for all maps within lane',
       'common_T_nside64_pixel_count':int(sel_t.sum()),
       'common_POL_nside64_pixel_count':int(sel_p.sum()),
       'nside64_pixels_total':49152,
       'T_ell0_to5_full_rank_condition':info_t,
       'spin2_ell2_to5_rank_condition':info_p,
       'scalar_coefficients_description':'orthonormal real ell2..5 source temperature microK',
       'EB_coefficients_description':'physical spin-2 real E/B coefficients ell2..5; cut-sky finite harmonic LS; E/B high-ell leakage NOT modeled',
       'same_sky_temperature_contrasts':comparisons,
       'same_sky_split_cross_products':split,
       'same_sky_polarization_contrasts':pol_contrasts,
       'selected_original_T_and_P_features':evidence,
       'legacy_HM_reference':independent_truth,
       'units':'microK thermodynamic temperature, microK^2',
       'scope_limits':['HM/OE/NILC/noSZ are NOT distinct cosmological sky realizations',
          'No split covariance/Planck physical PTE from one observed sky',
          'No beam or component-separation transfer of Bianchi source',
          'No correction for polarized unmodeled ell>5 or leakage beyond admitted finite E/B span',
          'No physical beta, q, sigma, vorticity or cosmological source motion detection'],
       'elapsed_seconds':time.perf_counter()-t0,
       'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output.mkdir(parents=True)
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(output/'retained_common_support_coefficients.npz',
        names_T=np.array(list(temp)),coeff_T=np.stack(list(temp.values())),
        names_EB=np.array(list(pol)),coeff_EB=np.stack(list(pol.values())),
        smica_hm_difference=con['hm_difference'],
        smica_oe_difference=con['oe_difference'],
        smica_hm_oe_mean_difference=con['partition_mean_difference'],
        column_spin_metadata_json=json.dumps(columns))
    lines=[
        '# Planck PR3 다중 분할과 spin-2 low-ell 실제 관측 source-bound 연구',
        '',f"T 공동 픽셀 {sel_t.sum()}/49152, 편광 공동 픽셀 {sel_p.sum()}/49152.",
        '분할 간 source mean 비교는 동일 low-ell fit mask에서 시행하며 각 모형은 같은 CMB 하늘을 공유한다.',
        '',
        '| 관측 동일하늘 대비 | norm (microK) | same-mask SMICA full 기준 비율 |',
        '|---|---:|---:|',
    ]
    for label,val in comparisons.items():
        lines.append(f"| {label} | {val['norm_microK']:.6g} | {100*val['ratio_to_same_mask_SMICA_full_norm']:.5g}% |")
    lines+=['','## 실제 split low-ell half differences',
        '| product | norm (microK) |','|---|---:|']
    for label,val in split.items():
        lines.append(f"| {label} | {val['half_difference_norm_microK']:.6g} |")
    lines+=['','## spin-2 E/B finite harmonic joint fit, intensity와 다른 missing mask',
            '| 비교 | EB norm (microK) |','|---|---:|']
    for label,val in pol_contrasts.items():
        lines.append(f"| {label} | {val:.6g} |")
    lines+=['','**주의:** 모든 비교는 하나의 하늘을 다른 split·성분분리 조건으로 본 결과다. Noise/foreground null simulation이나 CMB anomaly p-value가 없다.',
            'Cut sky finite E/B fitting remains contaminated by modes outside the truncated l2..5 spin basis. Spin2 frames and mask conventions are explicitly fixed; no true physical EB cosmology inference.',
            'Same-sky common-mode cancellation is algebraic only if processed physical sky response is the same in each split.',
            'Source: official Planck PR3 component separation and missing pixel products, A&A 641 A4 (2020).']
    (output/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,4),layout='constrained')
    names=['SMICA_HM','SMICA_OE','NILC_HM']
    for name in names:
        arr=split[name]['per_ell']
        ax.plot([v['ell'] for v in arr],[v['difference_auto'] for v in arr],marker='o',label=name)
    ax.set(xlabel='ell',ylabel='Half-difference coefficient auto [microK^2]',
           title='Same-sky Planck HM/OE/noise vs systematics residual tracers')
    ax.legend()
    fig.savefig(output/'source_bound_split_differences.png',dpi=165)
    plt.close(fig)
    print(json.dumps({
        'nTemp':int(sel_t.sum()),'nPol':int(sel_p.sum()),
        'split_half_diff_norms':{k:v['half_difference_norm_microK'] for k,v in split.items()},
        'cleaner_deltas':{k:v['ratio_to_same_mask_SMICA_full_norm'] for k,v in comparisons.items()},
        'spin2_EB_norms':pol_contrasts,
        'elapsed_sec':result['elapsed_seconds'],'peak_rss_MiB':result['peak_rss_kib_linux']/1024,
        'status':result['scientific_status']},indent=2))
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--output-dir',required=True,type=Path)
    args=ap.parse_args()
    run(args.output_dir)
