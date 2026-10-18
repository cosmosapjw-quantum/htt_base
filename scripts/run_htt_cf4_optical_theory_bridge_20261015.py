#!/usr/bin/env python3
"""Actual Cosmicflows-4 angular/depth source mapping to HTT optical inverse rank.

NEVER a physical source-velocity/geodesicity/acceleration fit: CF4 supplies a
group distance modulus and CMB-frame transformed recession velocity proxy,
not absolute vertex redshift intercept or source-congruence derivatives.
Weights based on released distance-modulus errors are design stress only,
not a calibrated redshift+distance likelihood.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np

from obsstat.catalogs.cf4_raw import load_authenticated_cf4_raw_groups
from obsstat.optical_depth_design_bridge import optical_depth_capability

ROOT = Path(__file__).resolve().parents[1]
# Reuse the actual executed CF4 source-subset receipt rather than retyping
# its long source-byte digests in another script.
SOURCE_RECEIPT = ROOT / ('docs/observational_reboot_20261014/results/cf4/'
                         'selected_v2/source_subset_receipt.json')
RECEIPT = json.loads(SOURCE_RECEIPT.read_text())
EXPECTED = {
    tag: RECEIPT['source_files'][f'workdir/raw/cf4_full/{tag}.dat.gz']['sha256']
    for tag in ('table3', 'table4')
}
C_KM_S=299792.458


def raw_selection(p):
    cat=load_authenticated_cf4_raw_groups(
        p/'table3.dat.gz',p/'table4.dat.gz',
        expected_table3_sha256=EXPECTED['table3'],
        expected_table4_sha256=EXPECTED['table4'])
    eligible=cat.primary_domain_mask(z_min=.01,z_max=.1,c_km_s=C_KM_S)
    redshift=cat.vcmb_km_s[eligible]/C_KM_S
    ra=np.deg2rad(cat.ra_deg[eligible])
    dec=np.deg2rad(cat.dec_deg[eligible])
    n=np.stack([np.cos(dec)*np.cos(ra),np.cos(dec)*np.sin(ra),np.sin(dec)],axis=1)
    dm=cat.dmzp[eligible]
    sig=cat.e_dmzp[eligible]
    # Diagnostic only. Vcmb/c is a frame-derived redshift proxy, not the
    # absolute optical endpoint redshift needed in the GR local inverse.
    luminosity=10**((dm-25)/5)
    proxy=luminosity/(1+redshift)**2
    if not np.all(np.isfinite(proxy)) or np.any(proxy<=0):
        raise ValueError("invalid fiducial d_A proxy")
    return cat, eligible, n, proxy, sig, cat.method_family[eligible]


def run(input_root, output):
    if output.exists():
        raise ValueError('fresh output directory required')
    t=time.perf_counter()
    cat, eligible, n, depth, errs, method=raw_selection(input_root)
    assert len(np.unique(cat.group_id[eligible]))==len(n)
    reference=float(np.median(depth))
    quant=np.quantile(depth,[.49,.50,.51])
    subsets={
       'all_z001_010':np.ones(len(n),bool),
       'dAproxy_20_200_Mpc':(depth>=20)&(depth<=200),
       'central_2pct_depth':(depth>=quant[0])&(depth<=quant[2]),
       'lower_depth_half':depth<=quant[1],
       'upper_depth_half':depth>quant[1],
       'FP_only':method=='FP',
       'TF_only':method=='TF',
       'SN_only':method=='SN',
    }
    if errs.min()<=0:
        raise ValueError('released distance modulus errors must be positive')
    wref=float(np.median(errs))
    rows=[]
    for name,subset in subsets.items():
        if int(np.count_nonzero(subset))<15:
            continue
        equal=optical_depth_capability(n[subset],depth[subset],
            distance_reference=reference,method_groups=method[subset])
        diagonal=optical_depth_capability(n[subset],depth[subset],
            distance_reference=reference,
            row_weights=wref/errs[subset],method_groups=method[subset])
        rows.append({'subset':name,'n':int(np.count_nonzero(subset)),
             'method_counts':{label:int(np.count_nonzero(method[subset]==label))
                              for label in sorted(set(method[subset]))},
             'depth_min_median_max_Mpc':list(map(float,
                              (depth[subset].min(),np.median(depth[subset]),depth[subset].max()))),
             'eDM_min_median_max_mag':list(map(float,
                              (errs[subset].min(),np.median(errs[subset]),errs[subset].max()))),
             'equal_weight':equal,'diagonal_eDM_weight_stress':diagonal})
    if rows[0]['equal_weight']['design_rank']!=13:
        raise ValueError('full-domain optical design unexpectedly rank deficient')
    if rows[0]['equal_weight']['method_projected_rank']!=12:
        raise ValueError('free-method offset must remove global intercept direction')
    data={
       'schema':'htt.theory-to-CF4-optical-design/1',
       'scientific_status':'EXECUTED_REAL_CF4_GEOMETRY_ONLY_NOT_OPTICAL_PHYSICS',
       'source_release':'Tully et al. 2023, ApJ 944 94, CDS J/ApJ/944/94',
       'raw_path_root':str(input_root),
       'source_gzip_sha256':cat.source_hashes,
       'source_receipt_sha256':hashlib.sha256(SOURCE_RECEIPT.read_bytes()).hexdigest(),
       'full_group_id_sha256':cat.row_id_sha256,
       'selected_group_id_sha256':cat.selected_row_sha256(eligible),
       'total_raw_groups':cat.row_count,
       'selected_z_proxy_001_010':len(n),
       'selection':'finite DMzp/eDMzp, CMB-frame Vcmb/c in [0.01,0.10], valid equatorial RA/DEC',
       'distance_contract':'proxy dA = 10^((DMzp-25)/5)/(1+Vcmb/c)^2 Mpc; NOT a measured absolute vertex-distance slope',
       'sky_contract':'J2000 equatorial RA/DEC from authenticated Table3; no conflation with Galactic CMB frame',
       'free_design':'13 unconstrained coefficients [E4,(r/rref)E9] before physical mass-shell tangent 12',
       'weights':'equal or w=(median e_DMzp)/e_DMzp; latter is a design stress, NOT error law for z or correlated likelihood',
       'hypothetical_nuisance':'one completely free additive calibration offset for each method-family (not empirically estimated)',
       'missing_for_physics':['observed absolute directional redshift intercept near vertex',
          'joint true dA/redshift errors and selection law','physical smooth congruence anchor',
          'finite-distance optical remainder/curvature segment bounds',
          'source/calibration cross covariance and ensemble null'],
       'reference_distance_Mpc':reference,
       'validation':{'unique_selected_ids':bool(len(np.unique(cat.group_id[eligible]))==len(n)),
                     'unit_sky_max_deviation':float(np.max(abs(np.sum(n*n,axis=1)-1))),
                     'strictly_positive_modulus_errors':bool(np.all(errs>0))},
       'elapsed_seconds':time.perf_counter()-t,
       'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
       'rows':rows,
    }
    output.mkdir(parents=True)
    (output/'result.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    table=['# Cosmicflows-4 실제 관측방향/깊이와 HTT 광학 역산의 정보 구조',
        '','관측자료: 원본 38,053 groups; 조건을 만족하는 ' + str(len(n)) + ' groups.',
        '','**결과 등급:** SOURCE-BOUND geometric design only. 물리적 optical inverse 또는 geodesicity 검정이 아님.',
        '',
        '| subset | N | principal sine (equal) | principal sine (eDM weight) | method dipole overlap (eDM weight) |',
        '|---|---:|---:|---:|---:|']
    for r in rows:
        a=r['equal_weight'];b=r['diagonal_eDM_weight_stress']
        table.append(f"| {r['subset']} | {r['n']} | {a['weakest_principal_sine']:.6g} | {b['weakest_principal_sine']:.6g} | {b['method_dipole_squared_design_overlap']:.6g} |")
    table.extend(['', '지금의 rank13은 실제 Einstein congruence 제약·확률법칙을 역산한 것이 아니다.',
       '기하학적 rank가 존재해도 depth가 거의 상수이면 절편과 기울기 공간이 근접해 수치 식별성이 취약하다.',
       '자유로운 방법별 영점 nuisance의 열공간에는 전역 상수 절편이 포함되어 rank가 12로 감소한다.',
       '거리계수 오차는 redshift의 Gaussian 오차가 아니므로 가중 분석을 Fisher 측정으로 부르지 않는다.',
       '이후 실제 redshift-dA joint latent/selection/calibration law를 CF4 provider와 결합해야 한다.'])
    (output/'REPORT_KO.md').write_text('\n'.join(table)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    names=[r['subset'] for r in rows]
    xx=np.arange(len(rows))
    e=np.array([r['equal_weight']['weakest_principal_sine'] for r in rows])
    w=np.array([r['diagonal_eDM_weight_stress']['weakest_principal_sine'] for r in rows])
    axs[0].plot(xx,e,'o-',label='equal')
    axs[0].plot(xx,w,'s-',label='eDM design weight')
    axs[0].set(ylabel='smallest intercept/slope principal sine',ylim=(0,1))
    axs[0].legend(fontsize=8)
    dip=np.array([r['diagonal_eDM_weight_stress']['method_dipole_squared_design_overlap'] for r in rows])
    axs[1].bar(xx,dip)
    axs[1].set(ylabel='method-offset dipole overlap (squared)',ylim=(0,1))
    for ax in axs:
        ax.set_xticks(xx)
        ax.set_xticklabels(names,rotation=40,ha='right',fontsize=8)
    for ext in ('png','pdf'):
        fig.savefig(output/f'optical_design_ability.{ext}',dpi=160)
    plt.close(fig)
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input-root',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    x=run(args.input_root,args.output_dir)
    print(json.dumps({'status':x['scientific_status'],'groups':x['selected_z_proxy_001_010'],
       'seconds':x['elapsed_seconds'],
       'subsets':[{r['subset']:{k:r['diagonal_eDM_weight_stress'][k] for k in (
         'design_rank','method_projected_rank','weakest_principal_sine',
         'method_dipole_squared_design_overlap')}} for r in x['rows']]},indent=2))
