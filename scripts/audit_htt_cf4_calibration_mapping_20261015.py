#!/usr/bin/env python3
"""Release-level CF4 DMav->DMzp source identity audit, NOT an estimator input.

Directly reads authenticated CDS fixed-width Table3 after verifying exact
table3 byte identity. Distinguishes total grouped source cohort and
method-specific SN Ia source, tracks large-scale global fixed offset.
Never treats postprocessed DMav and DMzp as independent observations.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
import collections

import numpy as np
from common.cf4_manifest import TABLE3_COLUMNS

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'docs/generated/pr144_cf4_manifest.json'
FIXED=ROOT/'docs/observational_reboot_20261014/results/cf4/selected_v2/source_subset_receipt.json'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def run(raw,out):
    if out.exists():raise ValueError('create-only output needed')
    path=raw/'table3.dat'
    expected=json.loads(MANIFEST.read_text())['tables']['table3']['file_sha256']
    if sha(path)!=expected:
        raise ValueError('CDS VizieR Table3 source-byte mismatch')
    f={c.label:c for c in TABLE3_COLUMNS}
    ids=set(json.loads(FIXED.read_text())['selected_group_ids'])
    total=0
    good=0
    shift_count=collections.Counter()
    exceptional=[]
    selected=[]
    calibration_overlaps=[]
    missing=0
    missing_calibrator=0
    for row in path.open(encoding='utf-8'):
        if not row.strip():continue
        total+=1
        gid=int(f['1PGC'].value(row))
        dmav=f['DMav'].value(row)
        edmav=f['e_DMav'].value(row)
        dmzp=f['DMzp'].value(row)
        dmSN=f['DMsnIa'].value(row)
        nSN=f['o_DMsnIa'].value(row)
        dmcal=f['DMcal'].value(row)
        valid=(dmav is not None and edmav is not None and dmav>0 and edmav>0)
        if valid:
            good+=1
            delta=round(dmzp-dmav,3)
            shift_count[delta]+=1
            if delta!=-.147:
                exceptional.append({'group_id':gid,'difference_mag':delta})
        else:
            missing+=1
            missing_calibrator+=int(dmcal is not None and dmcal>0)
        if valid and dmcal is not None and dmcal>0:
            calibration_overlaps.append({
                'group_id':gid,
                'direct_calibrator_DMcal_mag':float(dmcal),
                'averaged_methods_DMav_mag':float(dmav),
                'direct_minus_arbitrary_mag':float(dmcal-dmav),
                'reported_method_average_sigma_mag':float(edmav),
                'n_calibrator_galaxies':f['o_DMcal'].value(row),
                'SN_group_indicator_count':f['o_DMsnIa'].value(row)
            })
        if gid in ids:
            selected.append({
                'group_id':gid,'DMzp':dmzp,'DMav':dmav,
                'DMsnIa':dmSN,'e_DMav':edmav,
                'n_SN':nSN,'method_vs_group_offset':
                    None if dmSN is None or dmav is None else round(dmav-dmSN,3),
                'release_group_zeropoint_offset':
                    None if dmav is None else round(dmzp-dmav,3)
            })
    if total!=38053 or good!=37825 or missing!=228 or len(selected)!=24:
        raise ValueError('source release census changed unexpectedly')
    if set(shift_count)!={-.147} or exceptional:
        raise ValueError('expected exact reported global release offset not satisfied')
    selected_diff=collections.Counter(e['method_vs_group_offset'] for e in selected)
    if selected_diff!={0.:22,-.275:1,-.179:1}:
        raise ValueError('selected cohort method-to-group discrepancy drift')
    diffs=np.array([row['direct_minus_arbitrary_mag'] for row in calibration_overlaps])
    rng=np.random.default_rng(20261015)
    boots=np.median(diffs[rng.integers(0,len(diffs),size=(2000,len(diffs)))],axis=1)
    overlap_diagnostics={
       'n_both_direct_calibrator_and_method_mean':len(diffs),
       'n_direct_only':missing_calibrator,
       'direct_calibrator_total':len(diffs)+missing_calibrator,
       'median_DMcal_minus_DMav_mag':float(np.median(diffs)),
       'mean_DMcal_minus_DMav_mag':float(np.mean(diffs)),
       'mad_about_median_mag':float(np.median(abs(diffs-np.median(diffs)))),
       'percentiles_5_25_50_75_95_mag':np.quantile(diffs,[.05,.25,.5,.75,.95]).tolist(),
       'iid_groups_bootstrap_median_percentiles_025_975_descriptive_only':np.quantile(boots,[.025,.975]).tolist(),
       'n_SN_overlap_with_direct_calibrator':int(sum(row['SN_group_indicator_count'] not in (None,0) for row in calibration_overlaps)),
       'group_overlap_rows':calibration_overlaps,
       'absence':'e_DMcal direct calibrator uncertainty and inter-galaxy/group covariance NOT supplied by Table3; bootstrap does not validate physical calibration prior'
    }
    assert len(diffs)==108 and overlap_diagnostics['n_SN_overlap_with_direct_calibrator']==42
    result={
        'schema':'htt.release-CF4-global-zeropoint-calibration-map/1',
        'status':'ACTUAL_FULL_RELEASE_DMAV_DMZP_MAPPING_VERIFIED_NO_POSTERIOR',
        'raw_root':str(raw),
        'table3_plain_sha256':expected,
        'readme_sha256':sha(raw/'ReadMe'),
        'source_columns':['Table3 DMav, e_DMav, DMzp, DMsnIa, o_DMsnIa, DMcal (source auditing only)'],
        'n_total_rows':total,
        'n_groups_with_positive_DMav_e_DMav':good,
        'n_groups_without_positive_DMav_e_DMav':missing,
        'missing_average_rows_with_positive_DMcal':missing_calibrator,
        'reported_0p001mag_DMZP_minus_DMAV_counts':{str(k):v for k,v in shift_count.items()},
        'universality_scope':'ALL released groups with positive DMav and e_DMav at published 0.001 mag precision, NOT universal method/channel prior',
        '22_of_24_group_SNIa_method_match':22,
        'cohort_DMAV_minus_DMsnIa_histogram':{str(k):v for k,v in sorted(selected_diff.items())},
        'fixed_SN_only_group_rows':sorted(selected,key=lambda r:r['group_id']),
        'empirical_group_level_calibrator_overlap':overlap_diagnostics,
        'dependence_warning':'do not count DMav, DMzp, method SN average as independent observations; requires physical joint covariance and true source data',
        'not':'no absolute distance/H0, real calibration uncertainty, instrument independent source motion, physical CF4 selection function'
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    report=['# CF4 실제 38,053개 그룹 공통 거리척도 mapping 조사',
        '','Table 3: '+str(total)+' rows; positive DMav/e_DMav '+str(good)+' groups.',
        f'나머지 {missing} 그룹은 지정한 중간 group-mean 채널이 없어 직접 source 여부를 별도로 구별한다.',
        f'이 중 양의 직접 calibrator DMcal을 갖는 그룹 수 {missing_calibrator}.',
        '',
        f'**모든 {good}개 유효 행에서 published precision DMzp−DMav = −0.147 mag.**',
        '이는 publication-format deterministic affine relation이지 진짜 distance distribution의 무오차 공분산을 확정한 것은 아니다.',
        '동일 data를 독립 Gaussian likelihood로 여러 번 사용하면 필연적으로 정보 중복이 생긴다.',
        '','선택 24개 그룹의 DMav−DMsnIa: 22개 0, 나머지 두 그룹 −0.275, −0.179 mag.',
        '이 두 변형의 멤버/방법 결합 원인은 Table 3에 제공된 method flags만으로 인증되지 않았다.',
        '실제 환산 전에 Table2 host/method-level source and calibration provenance 연결이 필요하다.',
        '', '## 직접 calibrator와 그룹 결합값의 실측 overlap',
        f"두 채널이 모두 제공된 그룹은 {len(diffs)}개이고, SN Ia 관측도 가진 그룹은 {overlap_diagnostics['n_SN_overlap_with_direct_calibrator']}개다.",
        f"DMcal−DMav의 단순 중앙값은 {overlap_diagnostics['median_DMcal_minus_DMav_mag']:.4f} mag, 중앙절대편차는 {overlap_diagnostics['mad_about_median_mag']:.4f} mag.",
        '이 값은 결과를 보고 선택한 방법별/그룹별 overlap 진단이지 개별 측정의 independent calibrated posterior가 아니다.',
        'Table3에는 DMcal의 그룹별 불확실도 및 event-level cross-covariance가 없고, DMav는 이미 결합된 measurement다.',
        '표본 bootstrap은 독립 그룹을 가정한 기술적 민감도이며 별도 거리척도 정밀도 인증으로 사용하지 않는다.',
        '', '원전: Tully et al. 2023, CDS J/ApJ/944/94 ReadMe Note 1–5.',
        '']
    (out/'REPORT_KO.md').write_text('\n'.join(report))
    print(json.dumps({'n':total,'n_valid':good,'n_missing_mean':missing,
        'n_missing_has_cal':missing_calibrator,
        'offset_distribution':result['reported_0p001mag_DMZP_minus_DMAV_counts'],
        'method_disagreements':result['cohort_DMAV_minus_DMsnIa_histogram'],
        'overlap_n':len(diffs),'overlap_median_mag':float(np.median(diffs))},indent=2))
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--raw-root',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    run(args.raw_root,args.output_dir)
