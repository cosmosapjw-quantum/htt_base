#!/usr/bin/env python3
"""Exact sourced individual-galaxy calibrator fields linked to CF4 groups.

Release ReadMe byte positions only; no independent-calibration posterior,
no scientifically admitted WLS weighting of correlated measurements.
"""
from __future__ import annotations
import argparse,hashlib,collections,json
from pathlib import Path
import numpy as np
from common.cf4_manifest import TABLE3_COLUMNS

ROOT=Path(__file__).resolve().parents[1]
COLS={'TRGB':(103,107,109,112),
      'Cepheid':(114,119,121,125),
      'Maser':(127,131,133,136),
      'SNIa':(42,47,49,52)}
READMESHA='2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4'


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def parse(line,a,b):
    s=line[a-1:b].strip()
    return float(s) if s else None


def run(raw,out):
    if out.exists():raise ValueError('create-only outcome directory required')
    if digest(raw/'ReadMe')!=READMESHA:
        raise ValueError('not the authenticated CF4 catalog ReadMe byte positions')
    source2=raw/'table2.dat'
    rows=collections.defaultdict(list)
    totals=collections.Counter()
    galaxies=0
    for line in source2.open():
        if not line.strip():continue
        galaxies+=1
        group=int(line[8:15])
        pgc=int(line[0:7])
        for name,(m0,m1,e0,e1) in COLS.items():
            modulus=parse(line,m0,m1)
            err=parse(line,e0,e1)
            if modulus is None or err is None or err<=0:continue
            totals[name]+=1
            rows[group].append({'pgc':pgc,'channel':name,
                  'distance_modulus_mag':float(modulus),'reported_sigma_mag':float(err)})
    if galaxies!=55877:
        raise ValueError('Table2 source census changed')
    groups=[]
    missing_ids=[]
    pos_mean_overlap=0
    direct_only=0
    diffs=[]
    odd_sources=[]
    t3={c.label:c for c in TABLE3_COLUMNS}
    for line in (raw/'table3.dat').open():
        gid=int(t3['1PGC'].value(line))
        dmcal=t3['DMcal'].value(line)
        if dmcal is None or dmcal<=0:continue
        dmav=t3['DMav'].value(line)
        eav=t3['e_DMav'].value(line)
        valid=dmav is not None and dmav>0 and eav is not None and eav>0
        direct=[r for r in rows.get(gid,[]) if r['channel'] in ('TRGB','Cepheid','Maser')]
        if valid:pos_mean_overlap+=1
        else:direct_only+=1
        item={
           'group_1PGC':gid,
           'DMcal':float(dmcal),
           'DMav':None if not valid else float(dmav),
           'group_mean_present':bool(valid),
           'direct_galaxy_calibrators':direct,
           'distinct_PGC':len(set(r['pgc'] for r in direct)),
           'n_direct_measurements':len(direct),
        }
        if direct:
            mu=np.array([r['distance_modulus_mag'] for r in direct])
            sig=np.array([r['reported_sigma_mag'] for r in direct])
            proxy=float(np.average(mu,weights=sig**-2))
            d=float(proxy-dmcal)
            item['inverse_individual_error_group_average_proxy_mag']=proxy
            item['proxy_minus_published_group_DMcal_mag']=d
            diffs.append(d)
        else:
            missing_ids.append(gid)
            item['unresolved_group_mapping']='No direct individual calibrator matched by literal Table2 1PGC; inspect original host names/group identifiers'
        groups.append(item)
    delta=np.array(diffs,float)
    nclose=int(np.count_nonzero(np.abs(delta)<=.001))
    if len(groups)!=336 or pos_mean_overlap!=108 or direct_only!=228 or len(diffs)!=311 or len(missing_ids)!=25:
        raise ValueError('calibrator group-level source join changed')
    result={
      'schema':'htt.CF4-direct-galaxy-calibrator-source-join/1',
      'status':'ACTUAL_TABLE2_DIRECT_ERRORS_ACQUIRED_GROUP_MAPPING_PARTIAL',
      'authoritative_primary_source':'Tully et al. 2023 CDS J/ApJ/944/94 Table2+Table3+ReadMe',
      'table2_plain_sha256':digest(source2),
      'table3_plain_sha256':digest(raw/'table3.dat'),
      'readme_sha256':READMESHA,
      'total_individual_galaxy_records':galaxies,
      'individual_method_observation_counts':dict(totals),
      'groups_with_positive_direct_DMcal':len(groups),
      'groups_with_direct_and_average':pos_mean_overlap,
      'groups_direct_only':direct_only,
      'groups_linked_via_literal_1PGC':len(diffs),
      'groups_not_recovered_by_literal_group_join':len(missing_ids),
      'group_id_unresolved':missing_ids,
      'naive_inverse_reported_error_average_proxy_not_released_aggregator':{
         'n_linked_groups':len(diffs),
         'n_within_0p001mag_of_release_DMcal':nclose,
         'fraction_within_0p001mag':nclose/len(diffs),
         'median_abs_difference_mag':float(np.median(abs(delta))),
         'percentile95_abs_difference_mag':float(np.quantile(abs(delta),.95)),
         'maximum_abs_difference_mag':float(np.max(abs(delta))),
         'do_not_promote_to':'true independence or production group calibration; direct methods share anchors and release aggregation may involve additional modeling'
      },
      'source_contract':'published Table2 errors are per galaxy/method marginal values, NOT global SNIa/Cepheid/TRGB covariance or selection function',
      'direct_calibrator_groups':groups,
      'scientific_missing':['uncorrelated calibrator anchors/host event IDs','source-specific period-luminosity and host overlap priors',
         'per-survey selection/magnitude cuts and completeness',
         'joint method/calibrator covariance propagated through group release'],
      'physical_calibration_estimate':'WITHHELD'
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    desc=[
       '# CF4 Table2 개별 직접 보정 관측과 Table3 그룹 결합의 source join',
       '',
       f"Table2 actual individual rows: {galaxies}; method values: {dict(totals)}.",
       f"Group direct calibrator DMcal count: {len(groups)}; same group DMav exists: {pos_mean_overlap}; direct-only: {direct_only}.",
       f"Literal 1PGC group join with at least one individual TRGB/Cepheid/Maser datum: {len(diffs)}/{len(groups)}.",
       f"Unresolved literal group IDs: {len(missing_ids)}. A valid group-level calibration uncertainty cannot be assumed for them.",
       f"Naive inverse individual-error mean vs published DMcal matches <=0.001 mag for {nclose}/{len(diffs)} linked groups.",
       f"95th percentile abs discrepancy: {float(np.quantile(abs(delta),.95)):.5g} mag; maximum {float(np.max(abs(delta))):.5g} mag.",
       '',
       'The released per-galaxy sigma_i is not the covariance among TRGB/Cepheid/Maser methods, LMC calibration or galaxy-group memberships.',
       'Therefore neither the 311 linked groups nor the 108 overlap groups are certified independent absolute zero-point measurements.',
       'For numerical inference, keep the original release group DMcal/DMzp provenance and construct a joint calibrator covariance before treating overlaps as an external zero-point prior.',
    ]
    (out/'REPORT_KO.md').write_text('\n'.join(desc)+'\n')
    print(json.dumps({'status':result['status'],'individuals':galaxies,
         'raw_method_counts':dict(totals),'calibrator_groups':len(groups),
         'linked_groups':len(diffs),'unresolved':len(missing_ids),
         'proxy_weighted_agree_0p001':nclose,'p95_abs_discrepancy':float(np.quantile(abs(delta),.95))},indent=2))
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--raw-root',type=Path,default=Path('/mnt/extdrive/workdir/raw/cf4_full'))
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    run(args.raw_root,args.output_dir)
