#!/usr/bin/env python3
"""Actual official Planck SMICA HM1/HM2 intensity split matched-map diagnostics.

Does NOT estimate cosmological parameters or a sampling covariance from one
observed pair. Public hm-missing-pixel mask and existing Planck common mask
are respected. The actual HM1/HM2 CMB product is SOURCE-DERIVED and its
difference is not assumed to remove foreground mean / beam correlations.
"""
from __future__ import annotations

import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np
from astropy.io import fits
import healpy as hp

from obsstat.r7_cmb_product_response import pixel_fit_geometry
from obsstat.planck_split_joint_law import (
    nested_coarse_masked_mean,half_sum_difference)
from run_smica_reboot_pilot import build_ols_projector
from fit_cmb_smica_noise_modes import require_gated_cache

ROOT=Path(__file__).resolve().parents[1]
RAW_DEFAULT=Path('/mnt/extdrive/workdir/raw/planck_pr3_smica_hm_20261015')
FULLCACHE=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
GATE=ROOT/'docs/generated/k1_e2e_cache_gate_ffp10_smica.json'
BASE='COM_CMB_IQU-smica_2048_R3.00_'
MASK='COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits'
BASEURL='https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/maps/component-maps/cmb/'
MASKURL='https://irsa.ipac.caltech.edu/data/Planck/release_3/ancillary-data/masks/'


def sha(path):
    d=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4<<20),b''):
            d.update(block)
    return d.hexdigest()


def _verified_nested_hdu(hdu,expected_columns):
    header=hdu.header
    if (header.get('ORDERING')!='NESTED' or header.get('NSIDE')!=2048
        or header.get('NAXIS2')!=50331648 or
        not set(expected_columns).issubset(set(hdu.columns.names))):
        raise ValueError('native NESTED NSIDE2048 PR3 intensity/coverage format mismatch')
    return header


def masked_reduced_map(hmfits, maskfine, out_nside=64):
    with fits.open(hmfits,memmap=True,do_not_scale_image_data=True) as h:
        hdr=_verified_nested_hdu(h[1],('I_STOKES',))
        if hdr.get('TUNIT1')!='K_CMB':
            raise ValueError('SMICA split I must have K_CMB thermodynamic unit')
        intensity=h[1].data['I_STOKES']
        data,covered=nested_coarse_masked_mean(
           intensity,maskfine,nside_in=2048,nside_out=out_nside,chunk_lowpix=512)
        return data*1e6,covered



def run(raw,out,*,minimum_coverage=.995):
    if out.exists():
        raise ValueError('fresh result output required')
    t=time.perf_counter()
    hm1=raw/(BASE+'hm1.fits')
    hm2=raw/(BASE+'hm2.fits')
    missing=raw/MASK
    expected={hm1:603990720,hm2:603990720,missing:201335040}
    for src,nbytes in expected.items():
        if not src.is_file() or src.stat().st_size!=nbytes:
            raise ValueError(f'qualified official source absent or truncated: {src}')
    with fits.open(missing,memmap=True) as h:
        hdr=_verified_nested_hdu(h[1],('TMASK',))
        fine_mask=np.asarray(h[1].data['TMASK'])>.5
        mask_fraction=float(np.mean(fine_mask))
        a,cov1=masked_reduced_map(hm1,fine_mask)
        b,cov2=masked_reduced_map(hm2,fine_mask)
        # The same source mask intentionally applied to both.
        del fine_mask
    with np.load(FULLCACHE,allow_pickle=False) as src:
        common=np.asarray(src['common_mask'],float)
        full=np.asarray(src['observed_map'],float)
    identity=require_gated_cache(FULLCACHE,json.loads(GATE.read_text()))
    if len(a)!=49152 or len(b)!=49152 or len(common)!=49152:
        raise ValueError('NSIDE64 maps and gated source must match')
    directions, design=pixel_fit_geometry(64)
    keep=(common>.5)&(cov1>=minimum_coverage)&(cov2>=minimum_coverage)
    if int(keep.sum())<1000 or not np.isfinite(a[keep]).all() or not np.isfinite(b[keep]).all():
        raise ValueError('trusted common and half-mission source support insufficient')
    support,P,info=build_ols_projector(design,keep.astype(float))
    if not np.array_equal(support,keep):
        raise ValueError('fit support drift')
    coeff1=(P@a[keep])[4:36]
    coeff2=(P@b[keep])[4:36]
    coeff_full=(P@full[keep])[4:36]
    avg,diff=half_sum_difference(coeff1,coeff2)
    nlens=[5,7,9,11]
    cum=np.cumsum(nlens)[:-1]
    x1=np.split(coeff1,cum);x2=np.split(coeff2,cum)
    xc=np.split(avg,cum);xd=np.split(diff,cum);xf=np.split(coeff_full,cum)
    bands=[]
    for ell,(y1,y2,ym,yd,yfull) in enumerate(zip(x1,x2,xc,xd,xf),start=2):
        bands.append({
          'ell':ell,
          'HM1_C_l_microK2':float(y1@y1/len(y1)),
          'HM2_C_l_microK2':float(y2@y2/len(y2)),
          'split_cross_C_l_microK2':float(y1@y2/len(y1)),
          'half_sum_C_l_microK2':float(ym@ym/len(ym)),
          'half_difference_C_l_microK2':float(yd@yd/len(yd)),
          'published_fullmission_C_l_microK2':float(yfull@yfull/len(yfull)),
          'full_minus_half_sum_coefficient_norm_microK':float(np.linalg.norm(yfull-ym))
        })
    result={
        'schema':'htt.planck-real-HM1-HM2-split-source/1',
        'status':'ACTUAL_PR3_SMICA_HALF_MISSION_DIAGNOSTIC_NOT_PHYSICAL_NULL',
        'date':'2026-10-15',
        'input_products':{
            src.name:{'source_url':BASEURL+src.name if src!=missing else MASKURL+src.name,
                      'bytes':src.stat().st_size,'sha256':sha(src)}
            for src in (hm1,hm2,missing)},
        'full_mission_source':'K1 gated source cache, official SMICA full-mission map already ingested',
        'full_gated_cache_sha256':identity,
        'split_coordinate':'NESTED NSIDE2048 K_CMB to RING NSIDE64 microK, explicit binary HM missing pixel fine mask, nonmissing child mean',
        'mask_policy':'common K1 >.5; each HM missing pixel fine support fraction >= cutoff in each coarse pixel',
        'minimum_native_child_valid_fraction':minimum_coverage,
        'fraction_native_pixels_in_HM_missing_mask':mask_fraction,
        'n_coarse_covered':int(np.count_nonzero(cov1>=minimum_coverage)),
        'n_joint_fitted':int(support.sum()),
        'fitted_mask_fraction':float(np.mean(support)),
        'full_existing_mask_fraction':float(np.mean(common>.5)),
        'joint_fit_condition':info['design_condition'],
        'unit':'microK_CMB and microK_CMB^2',
        'coefficient_geometry':'ORTHONORMAL_REAL_M0_COS_SIN retained ell2..5, simultaneous ell0..5 nuisance fit',
        'diagnostics':{
           'half_sum_full_refit_norm_microK':float(np.linalg.norm(avg)),
           'half_difference_refit_norm_microK':float(np.linalg.norm(diff)),
           'half_minus_full_released_norm_microK':float(np.linalg.norm(avg-coeff_full)),
           'relative_half_minus_full_norm':float(np.linalg.norm(avg-coeff_full)/np.linalg.norm(coeff_full)),
           'source_discrepancy_not_noise_only':True,
        },
        'per_ell':bands,
        'not_estimated':['split noise covariance from one halfmission pair',
                         'actual Planck physical null, CMB anomaly PTE/p-value',
                         'beam/color/component-separation transfer of hypothetical Bianchi sky',
                         'HM1/HM2 independent noise: residual systematics and missing coverage remain'],
        'theory_identity':'m=(y1+y2)/2 and d=(y1-y2)/2; C_m=(C11+C22+C12+C21)/4; C_d=(C11+C22-C12-C21)/4. Correlated/common systematics can cancel in d',
        'seconds':time.perf_counter()-t,
        'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'retained_ell2_5_split_coefficients.npz',
         HM1=coeff1,HM2=coeff2,HM_half_sum=avg,HM_half_difference=diff,
         full_gated_refit=coeff_full)
    lines=['# Planck PR3 실제 SMICA HM1/HM2 half-mission 관측분할',
        '',f"공식 원본 및 HM missing-pixel mask 3종의 크기·SHA-256 확인. 공동 안전 mask의 NSIDE64 픽셀수 {support.sum()}.",
        '',
        '이는 단일 하늘의 두 관측 분할 결과이지 mock ensemble이 아니며, half-difference는 공통 systematic을 검출하지 못할 수 있다.',
        '',
        '| ell | cross HM1xHM2 microK2 | halfdiff auto microK2 | halfsum auto microK2 | full source microK2 |',
        '|---|---:|---:|---:|---:|']
    for row in bands:
        lines.append(f"| {row['ell']} | {row['split_cross_C_l_microK2']:.6g} | {row['half_difference_C_l_microK2']:.6g} | {row['half_sum_C_l_microK2']:.6g} | {row['published_fullmission_C_l_microK2']:.6g} |")
    lines.extend(['','Released split CMBs are not actual time-stream independent noise measurements; HM missing mask is combined with the source common mask, not silently set to zero.',
        'No E2E native split covariance, no Planck scientific null or p-values. The full/half-average difference can include nontrivial compsep weights and transfer, not just random noise.',
        'A physical CMB boost/Bianchi response must pass both split-specific transfer and correlate their latent common foreground/systematic terms.'])
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(7.6,3.7),layout='constrained')
    for label,key in [('cross HM1xHM2','split_cross_C_l_microK2'),
                      ('half difference','half_difference_C_l_microK2'),
                      ('full reference','published_fullmission_C_l_microK2')]:
        ax.plot([r['ell'] for r in bands],[r[key] for r in bands],marker='o',label=label)
    ax.set(xlabel='Multipole ell',ylabel='Coefficient power [microK^2]',
           title='Released Planck PR3 SMICA half-mission direct split diagnostic')
    ax.legend(fontsize=8)
    fig.savefig(out/'halfmission_lowell_split_power.png',dpi=170)
    plt.close(fig)
    print(json.dumps({'status':result['status'],
        'n_safe_pixels':result['n_joint_fitted'],
        'HM_coverage_fine':result['fraction_native_pixels_in_HM_missing_mask'],
        'full_minus_HM_mean_ratio':result['diagnostics']['relative_half_minus_full_norm'],
        'ell':bands,'seconds':result['seconds']},indent=2))
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--raw-root',type=Path,default=RAW_DEFAULT)
    a.add_argument('--output-dir',type=Path,required=True)
    a.add_argument('--minimum-child-coverage',type=float,default=.995)
    args=a.parse_args()
    run(args.raw_root,args.output_dir,minimum_coverage=args.minimum_child_coverage)
