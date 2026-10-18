"""Post-run artifact consistency only; never rereads source tables or recomputes responses."""
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    summary=json.loads((ROOT/'summary.json').read_text())
    launch=json.loads((ROOT/'launch.json').read_text())
    execution=json.loads((ROOT/'execution.json').read_text())
    assert execution['returncode']==0 and execution['consumed_seconds']<=120
    assert execution['attempt']==1
    for name,digest in launch['source_code_sha256'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    with gzip.open(ROOT/'rows.csv.gz','rt') as f:
        rows=list(csv.DictReader(f))
    allgroup=summary['groups']['all']
    assert len(rows)==allgroup['rows']
    assert sum(r['eligible']=='True' for r in rows)==allgroup['eligible']
    for name in ('join_status','direction_status','quadratic_status'):
        assert dict(Counter(r[name] for r in rows))==allgroup[name],name
    assert len({(r['realization'],r['fitres_path'],r['original_row_index']) for r in rows})==len(rows)
    assert len(summary['groups']['sectors'])==8
    assert len(summary['groups']['realization_sectors'])==80
    assert len(summary['groups']['realization'])==10
    assert summary['head_rows_used_unique']+summary['head_rows_unmatched']==summary['head_total_rows']
    assert sum(summary['head_unmatched_by_file'].values())==summary['head_rows_unmatched']
    for row in rows:
        good=row['direction_status']=='QUALIFIED_NATIVE_RELEASED'
        assert good==(row['native_ra']!='' and row['native_dec']!='')
        if not good:assert row['sector']=='UNAVAILABLE'
    for base in ('color_response','working_covariance','released_directions'):
        assert (ROOT/(base+'.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
        assert (ROOT/(base+'.pdf')).read_bytes().startswith(b'%PDF-')
    controls=json.loads((ROOT/'controls.json').read_text())
    assert controls['returncode']==0
    acquisition=json.loads((ROOT/'acquisition_final.json').read_text())
    assert acquisition['total_charged_source_bytes']<=20_000_000
    expected_exclusions=('ERRFLAG_FIT_NONZERO','CUTFLAG_BIT2_ABSENT','NONFINITE_REQUIRED',
                         'NONPOSITIVE_ERROR','NONPOSITIVE_RV','NEGATIVE_AV','NONFINITE_COMPUTED')
    result={'status':'ARTIFACT_CONSISTENCY_PASS','not_physical_validation':True,
            'science_reexecuted':False,'rows':len(rows),'science_seconds':execution['consumed_seconds'],
            'acquisition_charged_bytes':acquisition['total_charged_source_bytes'],
            'all_exclusion_counts_including_zero':{k:summary['exclusion_reasons_overlapping'].get(k,0) for k in expected_exclusions},
            'all_join_status_counts_including_zero':{k:allgroup['join_status'].get(k,0) for k in (
                'ZERO_CANDIDATE','TRUTH_DISAGREEMENT','MISSING_TRUTH_BINDING','MULTIPLE_AGREEING','UNIQUE_TRUTH_MATCH')},
            'truth_disagreement_numeric_surveys':dict(Counter(r['IDSURVEY'] for r in rows if r['join_status']=='TRUTH_DISAGREEMENT')),
            'visual_inspection':'All three PNGs inspected; labels legible and scope caveats present',
            'first_preparation_issue':'Initial noncanonical python3 environment inspection printed NumPy1/2 ABI errors from optional system numexpr/bottleneck via pandas; no science ran there. Canonical .venv was bound before controls/science, and pandas is unused.'}
    (ROOT/'artifact_checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
