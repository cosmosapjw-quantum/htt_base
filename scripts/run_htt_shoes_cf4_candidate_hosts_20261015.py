#!/usr/bin/env python3
"""Source-qualified CF4 Cepheid galaxy to SH0ES field astrometry CANDIDATES.

31-37 group-to-source correspondences from J2000 RA/Dec may narrow the
matching problem, but positional overlap alone is NEVER accepted as
authenticated same Cepheid host/event/anchor covariance.
"""
from __future__ import annotations
import argparse,hashlib,json,collections,time
from pathlib import Path
import numpy as np
from obsstat.htt_shoes_cf4_astrometric_join import (
    parse_shoes_cepheid_table_line,nearest_catalogue_source)

ROOT=Path(__file__).resolve().parents[1]
SHOES=Path('/mnt/extdrive/workdir/raw/shoes2022_calibration_reference_20261015/table2.tex')
CF4=Path('/mnt/extdrive/workdir/raw/cf4_full/table2.dat')
PREVIOUS=ROOT/'docs/research_program/theory_obs_application_20261015/loop4/results/cf4_galaxy_calibrator_join_v1/result.json'
INTAKE=Path('/mnt/extdrive/workdir/raw/HTT_ADDITIONAL_DATA_INTAKE_20261015.json')


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for q in iter(lambda:f.read(8<<20),b''):h.update(q)
    return h.hexdigest()


def val(s,a,b):
    q=s[a-1:b].strip()
    return float(q) if q else None


def run(out,cut_arcmin=4.):
    if out.exists():raise ValueError('create-only observed candidate mapping')
    t=time.perf_counter()
    published=json.loads(PREVIOUS.read_text())
    intake=json.loads(INTAKE.read_text())
    expected_shoes=next(q['sha256'] for q in intake['items'] if q['key']=='shoes_2022_table2')
    if sha(SHOES)!=expected_shoes or sha(CF4)!=published['table2_plain_sha256']:
        raise ValueError('source byte identity SH0ES/CF4 mismatch')
    hosts=collections.defaultdict(list)
    for line in SHOES.open():
        row=parse_shoes_cepheid_table_line(line)
        if row is None:continue
        key,ra,dec=row
        hosts[key].append((ra,dec))
    galaxies=[]
    for line in CF4.open():
        m=val(line,114,119);e=val(line,121,125)
        if m is None or e is None or m<=0 or e<=0:continue
        galaxies.append({
            'PGC':int(line[:7]),'1PGC_group':int(line[8:15]),
            'RA_J2000_deg':float(line[137:145]),
            'DEC_J2000_deg':float(line[146:154]),
            'CF4_DMceph_mag':m,'CF4_e_DMceph_mag':e
        })
    if len(hosts)!=41 or len(galaxies)!=69:
        raise ValueError('actual SH0ES host / CF4 Cepheid cohort changed')
    sky=[(q['RA_J2000_deg'],q['DEC_J2000_deg']) for q in galaxies]
    outcomes=[]
    for name,entries in sorted(hosts.items()):
        mat=nearest_catalogue_source(entries,sky,cut_arcmin=cut_arcmin)
        match=galaxies[mat['nearest_index']]
        row={
            'SH0ES_field_label':name,
            'n_SH0ES_wfc3_Cepheid_star_rows':len(entries),
            'angular_match':mat,
            'candidate_CF4_individual_galaxy':match if mat['status']=='POSITION_CANDIDATE' else None,
            'nearest_CF4_Cepheid_row_for_audit_only':match if mat['status']!='POSITION_CANDIDATE' else None,
        }
        outcomes.append(row)
    good=[r for r in outcomes if r['angular_match']['status']=='POSITION_CANDIDATE']
    ambiguous=[r for r in outcomes if r['angular_match']['status']=='AMBIGUOUS_WITHIN_CUT']
    notfound=[r for r in outcomes if r['angular_match']['status']=='NO_MATCH_WITHIN_CUT']
    unique_hosts={r['SH0ES_field_label'] for r in good}
    gids=collections.defaultdict(list)
    for r in good:
        gids[r['candidate_CF4_individual_galaxy']['1PGC_group']].append(r['SH0ES_field_label'])
    group_collisions={str(k):v for k,v in sorted(gids.items()) if len(v)>1}
    known=[r['angular_match']['first_distance_arcmin'] for r in good]
    nearestsecond=[r['angular_match']['second_distance_arcmin'] for r in good]
    summary={
        'schema':'htt.SH0ES_to_CF4_positional_candidate_source_map/1',
        'scientific_status':'ACTUAL_SOURCE_ASTROMETRY_CANDIDATES_NOT_CERTIFIED_HOST_IDENTITIES',
        'source_url_shoes':'https://github.com/PantheonPlusSH0ES/DataRelease/tree/main/SH0ES_Data',
        'source_url_cf4':'https://cdsarc.u-strasbg.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html&tex=true',
        'source_hashes':{str(SHOES):expected_shoes,str(CF4):published['table2_plain_sha256']},
        'n_SH0ES_Cepheid_source_fields':len(hosts),
        'n_SH0ES_source_star_positions':sum(map(len,hosts.values())),
        'n_CF4_galaxies_with_positive_Cepheid_moduli_and_sigma':len(galaxies),
        'match_cut_arcmin':cut_arcmin,
        'n_unique_position_candidates':len(good),
        'n_ambiguous_within_cut':len(ambiguous),
        'n_outside_cut':len(notfound),
        'not_position_matched_labels':[r['SH0ES_field_label'] for r in notfound],
        'candidate_nearest_distance_arcmin_median_max':[float(np.median(known)),float(np.max(known))],
        'candidate_second_nearest_distance_arcmin_min':float(np.min(nearestsecond)),
        'n_candidate_CF4_unique_group_ids':len(gids),
        'multi_SH0ES_host_same_CF4_group_candidates':group_collisions,
        'candidates':outcomes,
        'cross_catalogue_anchor_covariance':'NOT_RECONSTRUCTED_NEEDS_AUTHENTICATED_HOST_AND_EVENT_IDENTITY_AND_METHOD_SHARED_ERRORS',
        'rule':'spherical J2000 centroid of SH0ES Cepheids against CF4 Table2 individual Cepheid host galaxy positions; threshold and runner prespecified for THIS exploratory source mapping',
        'warning':'positional candidate even at <0.5 arcmin does not certify identical Cepheid events, common zero points, SH0ES L column ordering, group aggregation or nonzero cross covariance',
        'seconds':time.perf_counter()-t,
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    lines=['# SH0ES Cepheid host 와 CF4 실제 Cepheid 관측은하: 천구 위치 대응 감사',
     '', f"SH0ES Table2 WFC3-IR host {len(hosts)} labels; CF4 실제 Cepheid galaxy {len(galaxies)}.",
     f"Joint J2000 4 arcmin criterion: candidates {len(good)}, unresolved {len(notfound)}, ambiguous {len(ambiguous)}.",
     f"Candidate common CF4 1PGC group collisions: {group_collisions}.",
     '', '| SH0ES Field | n Cepheids | nearest CF4 PGC | parent 1PGC | angular separation arcmin |',
     '|---|---:|---:|---:|---:|']
    for r in good:
        mat=r['angular_match'];k=r['candidate_CF4_individual_galaxy']
        lines.append(f"| {r['SH0ES_field_label']} | {r['n_SH0ES_wfc3_Cepheid_star_rows']} | {k['PGC']} | {k['1PGC_group']} | {mat['first_distance_arcmin']:.4g} |")
    lines+=['','Unmatched or outside cutoff: '+', '.join(r['SH0ES_field_label'] for r in notfound)+'.',
            'These matches are ASTROMETRIC CANDIDATES, not verified shared source/event identity. Do not infer physical correlations, zero-point priors or H0 from these rows alone.',
            'Next direct task: verify host names/cross IDs with independent source catalogue and bind SH0ES 47 parameter host coordinates to released event/covariance model; then insert CF4 group membership cross covariance.']
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':summary['scientific_status'],'SHOES_hosts':len(hosts),'CF4_Cepheid_galaxies':len(galaxies),
        'candidate_position_matched':len(good),'ambiguous':len(ambiguous),
        'notmatched':summary['not_position_matched_labels'],
        'candidate_group_collisions':group_collisions,
        'max_sep_arcmin':summary['candidate_nearest_distance_arcmin_median_max'][1],
        'min_second_nearest_arcmin':summary['candidate_second_nearest_distance_arcmin_min']},ensure_ascii=False,indent=2))
    return summary


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--output-dir',type=Path,required=True)
    a.add_argument('--max-separation-arcmin',type=float,default=4.)
    z=a.parse_args()
    run(z.output_dir,cut_arcmin=z.max_separation_arcmin)
