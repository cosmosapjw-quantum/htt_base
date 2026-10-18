"""Actual upstream PGC membership, quality and band contributions; aggregates only.

Release inclusion fractions are not parent detection/targeting probabilities.
No covariance or physical flow is estimated from these membership diagnostics.
"""
from pathlib import Path
import hashlib
import json
import re
import sys
from collections import Counter
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
UPSTREAM = Path('/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018')
CF4 = UPSTREAM.parent/'J_ApJ_944_94'
PREVIOUS = HERE.parent/'H02_EXECUTION_20261018'
SOURCE = ROOT/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
SOURCE_SHA = '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
UPSTREAM_SHA = {'ReadMe':'45fa3cca5346aff29bcf9785e7b08e8ab34b1d67e80b359c0d28bdbd18e42581',
                'table1.dat':'ac679ab4548484b02dc17a1cc09bbe8f0a68f45bd5c44efc7302fcabc32d8926',
                'table4.dat':'f4aa0ba0efe7d7a14f044a76ef37f5a033e2788923d586c2d15ed248939455f2'}
CF4_README_SHA = '2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4'


def sealed(path, expected):
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != expected:
        raise ValueError('immutable source SHA mismatch: '+str(path))
    return blob


def schema(readme, filename):
    section = readme.split('Byte-by-byte Description of file: '+filename+'\n', 1)[1]
    section = section.split('Note (', 1)[0]
    section = section.split('Byte-by-byte Description of file:', 1)[0]
    columns = {}
    pattern = r'^\s*(\d+)(?:-\s*(\d+))?\s+([AIF]\d+(?:\.\d+)?)\s+\S+\s+(\S+)\s+'
    for line in section.splitlines():
        match = re.match(pattern, line)
        if match:
            first, last, fmt, label = match.groups()
            columns[label] = (int(first)-1, int(last or first), fmt[0])
    if 'PGC' not in columns and '1PGC' not in columns:
        raise ValueError('PGC field missing from ReadMe schema')
    return columns


def parse_rows(blob, columns, count, width):
    rows = blob.decode('ascii').splitlines()
    # CDS omits trailing blank fields on some rows: Lrecl is maximum width.
    if len(rows) != count or any(not 7 <= len(row) <= width for row in rows):
        raise ValueError('release row count/width differs from ReadMe')
    parsed = []
    for row in rows:
        entry = {}
        for name, (start, end, kind) in columns.items():
            text = row[start:end].strip()
            entry[name] = None if not text else text if kind == 'A' else int(text) if kind == 'I' else float(text)
        if entry['PGC'] is None:
            raise ValueError('missing source PGC')
        parsed.append(entry)
    ids = [r['PGC'] for r in parsed]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate PGC: ambiguous join')
    return {r['PGC']: r for r in parsed}


def band_class(row):
    optical = any(row[x] is not None for x in ('DM-r','DM-i','DM-z'))
    infrared = row['DM-W1'] is not None
    return 'optical_and_W1' if optical and infrared else 'optical_only' if optical else 'W1_only' if infrared else 'no_band_distance'


def join_status(ids, galaxy, group_ids, selected_ids):
    """Explicitly distinguish absent galaxy, absent group, nonselected and selected."""
    c = Counter()
    for pgc in ids:
        if pgc not in galaxy:
            c['not_in_CF4_galaxy'] += 1
        elif galaxy[pgc]['1PGC'] not in group_ids:
            c['galaxy_group_absent_from_group_release'] += 1
        elif galaxy[pgc]['1PGC'] not in selected_ids:
            c['group_outside_selected'] += 1
        else:
            c['selected_group'] += 1
    return {key:c[key] for key in ('not_in_CF4_galaxy','galaxy_group_absent_from_group_release','group_outside_selected','selected_group')}


def histogram(rows, key):
    return {str(k):v for k,v in sorted(Counter(r[key] for r in rows).items())}


def group_summary(groups, selected, z, sigma, directions):
    """Count each supporting group once, even when several galaxies contribute."""
    support = np.isin(selected, list(groups))
    windows = []
    for name, center in [('all_selected',None),('z025',.025),('z040',.04),('z060',.06),('z080',.08)]:
        kernel = np.ones(len(z)) if center is None else np.exp(-.5*((z-center)/.012)**2)
        weight = kernel/sigma**2
        ws = weight[support]
        windows.append({'window': name, 'supporting_groups':int(support.sum()),
                        'kernel_mass_fraction':float(kernel[support].sum()/kernel.sum()),
                        'working_inverse_variance_mass_fraction':float(ws.sum()/weight.sum()),
                        'effective_support_groups_kish':float(ws.sum()**2/np.dot(ws,ws)) if len(ws) else None,
                        'support_weighted_direction_mean':np.average(directions[support],axis=0,weights=ws).tolist() if len(ws) else None})
    return windows


def run():
    receipt = json.loads((HERE/'ACQUISITION_RECEIPT.json').read_text())
    if {name:meta['sha256'] for name,meta in receipt['sources'].items()} != UPSTREAM_SHA:
        raise ValueError('acquired upstream source binding changed')
    raw = {name: sealed(UPSTREAM/name, meta['sha256']) for name,meta in receipt['sources'].items()}
    readme = raw['ReadMe'].decode('ascii')
    t1 = parse_rows(raw['table1.dat'], schema(readme,'table1.dat'),10737,499)
    t4 = parse_rows(raw['table4.dat'], schema(readme,'table4.dat'),9792,100)
    distance_not_in_data = set(t4)-set(t1)
    measured = {p for p,r in t4.items() if r['DMbest'] is not None}
    old = json.loads((PREVIOUS/'results/h02_actual_centers.json').read_text())
    cfread = sealed(CF4/'ReadMe',CF4_README_SHA).decode('ascii')
    galaxy = parse_rows(sealed(CF4/'table2.dat',old['source_table_sha256']['table2.dat']),schema(cfread,'table2.dat'),55877,190)
    # Reuse source bytes and identities; do not rerun prior coefficient fits.
    sealed(SOURCE,SOURCE_SHA)
    with np.load(SOURCE,allow_pickle=False) as f:
        ids, z, sigma = f['group_id'].copy(),f['z_CMB'].copy(),f['e_dmzp'].copy()
        directions = f['n_J2000'].copy()
        family = f['method_family'].copy()
    group_blob = sealed(CF4/'table3.dat',old['source_table_sha256']['table3.dat'])
    # table3 first column is 1PGC, whereas parser expects PGC; adapt schema label only.
    gc = schema(cfread,'table3.dat')
    gc['PGC'] = gc.pop('1PGC')
    groups = parse_rows(group_blob,gc,38053,190)
    selected_set = set(map(int,ids))
    if len(ids)!=35970 or len(selected_set)!=35970 or not selected_set.issubset(groups):
        raise ValueError('selected group identity or cardinality changed')
    selected_upstream = [pgc for pgc in measured if pgc in t1 and pgc in galaxy and galaxy[pgc]['1PGC'] in selected_set]
    excluded = set(t1)-set(t4)
    cohorts = {'upstream_data_all':list(t1.values()),'in_distance_release':[t1[p] for p in t4 if p in t1],
               'has_DMbest':[t1[p] for p in measured if p in t1],
               'not_in_distance_release':[t1[p] for p in excluded],
               'selected_upstream_distance':[t1[p] for p in selected_upstream]}
    quality = {name:{'n':len(rows),**{key:histogram(rows,key) for key in ('QSflag','QWflag','Rsrc')},
                    'inclination_quantiles_0_50_100':np.quantile([r['Inc'] for r in rows],[0,.5,1]).tolist(),
                    'HI_linewidth_error_over_20':sum(r['e_Wmx']>20 for r in rows),
                    'heliocentric_velocity_over_15000':sum(r['HRV']>15000 for r in rows)} for name,rows in cohorts.items()}
    quality_cells=[]
    for qs in range(6):
        for qw in range(6):
            pgcs={p for p,r in t1.items() if r['QSflag']==qs and r['QWflag']==qw}
            quality_cells.append({'QSflag':qs,'QWflag':qw,'data_count':len(pgcs),
                                  'distance_record_count':len(pgcs&set(t4)),
                                  'has_DMbest_count':len(pgcs&measured),
                                  'selected_measured_count':len(pgcs&set(selected_upstream))})
    routes = {key:{p for p,r in t4.items() if band_class(r)==key} for key in ('optical_and_W1','optical_only','W1_only','no_band_distance')}
    support = {}
    for name,pgcs in {'all_upstream_records':set(t4),'has_DMbest':measured,**routes}.items():
        joined = [p for p in pgcs if p in galaxy and galaxy[p]['1PGC'] in selected_set]
        group_set = {galaxy[p]['1PGC'] for p in joined}
        mask = np.isin(ids,list(group_set))
        support[name] = {'upstream_galaxies':len(pgcs),'selected_galaxies':len(joined),'selected_groups':len(group_set),
                         'selected_partition_groups':{str(label):int(np.sum(mask & (family==label))) for label in np.unique(family)},
                         'selected_galaxies_with_released_CF4_TF_distance':sum(galaxy[p]['DMtf'] is not None for p in joined),
                         'group_released_method_presence':{label:sum(groups[g][field] is not None and groups[g][field]>0 and groups[g][count] is not None and groups[g][count]>0 for g in group_set)
                              for label,field,count in [('CAL','DMcal','o_DMcal'),('SNIA','DMsnIa','o_DMsnIa'),('FP','DMfp','o_DMfp'),('TF','DMtf','o_DMtf')]},
                         'group_positive_modulus_missing_count':{label:sum(groups[g][field] is not None and groups[g][field]>0 and groups[g][count] is None for g in group_set)
                              for label,field,count in [('CAL','DMcal','o_DMcal'),('SNIA','DMsnIa','o_DMsnIa'),('FP','DMfp','o_DMfp'),('TF','DMtf','o_DMtf')]},
                         'windows':group_summary(group_set,ids,z,sigma,directions)}
    # Compare original DMbest with later registered per-galaxy TF only descriptively.
    shifts = {}
    for route, pgcs in routes.items():
        paired = [p for p in pgcs if p in galaxy and galaxy[p]['DMtf'] is not None and t4[p]['DMbest'] is not None]
        delta = [galaxy[p]['DMtf']-t4[p]['DMbest'] for p in paired]
        shifts[route] = {'paired_galaxies':len(paired),'CF4_registered_TF_minus_2020_DMbest_quantiles_0_16_50_84_100_mag':np.quantile(delta,[0,.16,.5,.84,1]).tolist() if delta else None}
    route_sets = {key:{galaxy[p]['1PGC'] for p in val if p in galaxy and galaxy[p]['1PGC'] in selected_set} for key,val in routes.items()}
    output = {'schema':'htt.h02_upstream_selection/1','owner':'htt','scope':'actual release membership and contributor diagnostics',
              'claim_tier':'DIAGNOSTIC_ONLY','transfer_source':'none','H02_acceptance':'HOLD',
              'source_npz_sha256':SOURCE_SHA,'source_table_sha256':old['source_table_sha256'],'CF4_ReadMe_sha256':CF4_README_SHA,
              'upstream_sources':receipt['sources'],'ReadMe_release_date':'21-Apr-2022','upstream_paper':'arXiv:2009.00733v2; 2020ApJ...902..145K',
              'counts':{'data':len(t1),'distance_records':len(t4),'has_DMbest':len(measured),'DMbest_missing':len(t4)-len(measured),'data_not_in_distance':len(excluded),
                        'distance_not_in_data':len(distance_not_in_data),'data_distance_intersection':len(set(t1)&set(t4)),'selected_source_groups':len(ids)},
              'join_status':{name:join_status(pgcs,galaxy,set(groups),selected_set) for name,pgcs in [('data',t1),('distance_records',t4),('has_DMbest',measured),('data_not_in_distance',excluded),('distance_not_in_data',distance_not_in_data)]},
              'quality_and_attenuation':quality,'quality_cells':quality_cells,'band_contributors':support,'registered_release_differences':shifts,
              'optical_W1_only_overlap_selected_groups':len((route_sets['optical_only']|route_sets['optical_and_W1'])&route_sets['W1_only']),
              'band_group_overlap_counts':{left:{right:len(a&b) for right,b in route_sets.items()} for left,a in route_sets.items()},
              'band_rule':'optical if any released r/i/z modulus; W1-only requires no optical modulus and finite W1. DMbest prefers optical. Routes classify measurements; groups can contain multiple routes.',
              'window_rule':'same selected group z_CMB Gaussian kernels, width .012; group counted once per route. Weight kernel/e_DMzp^2 is descriptive pooled-group working weight.',
              'caveats':['Table1 is already quality/inclination selected, not full targeting parent. Counts do not identify selection probabilities.',
                         '947 table1-only PGCs, 2 table4-only PGCs and 11 table4 rows with no DMbest are retained explicitly. No individual rejection reason is inferred.',
                         'Rsrc identifies attenuation input, not telescope or HI-survey membership; per-galaxy HI origin remains unavailable.',
                         'Original published DMbest and later CF4 TF have different calibration/merging versions; paired offsets are not independent calibration errors.',
                         'Group membership alone does not prove each 2020 measurement was ingested unchanged into CF4.',
                         'Shared calibration/velocity covariance, source null pipeline and common angular anchor remain unavailable.'],
              'runtime':{'requested':'gpt-6.1-sol/high','observed':'UNKNOWN','python':sys.version}}
    dest=HERE/'results'
    dest.mkdir(exist_ok=True)
    (dest/'UPSTREAM_SELECTION.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'counts':output['counts'],'join_status':output['join_status'],'band_contributors':{k:{q:v[q] for q in ('upstream_galaxies','selected_galaxies','selected_groups')} for k,v in support.items()}},indent=2))
    return output


if __name__ == '__main__':
    run()
