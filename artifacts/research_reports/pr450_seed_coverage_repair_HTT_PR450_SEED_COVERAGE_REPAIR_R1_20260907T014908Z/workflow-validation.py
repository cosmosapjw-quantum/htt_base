from pathlib import Path
import hashlib
import json

path = Path('/mnt/sn850x2t/htt_base_e2e/HTT_PR450_SEED_COVERAGE_REPAIR_R1_20260907T014908Z/evidence/REGISTERED_SURVIVOR_SURFACE.json')
value = json.loads(path.read_text(encoding='ascii'))
assert value['schema'] == 'htt.registered_survivor_surface.v1'
assert value['source']['commit'] == '463f0999949bf8534c60ad7973b7342705c2e3d6'
assert value['source']['git_blob'] == '56af1713ef8c4718598e10012819d5ab62c6e37a'
assert value['coverage'] == {
    'exact_or_conditional_broad': 24,
    'synthetic_broad': 8,
    'broad_total': 32,
    'scoped_children': 5,
    'registered_total': 37,
    'included_total': 36,
    'deferred_total': 1,
    'excluded_total': 0,
    'missing_disposition_count': 0,
    'duplicate_candidate_id_count': 0,
}
assert value['unique_theorem_count'] is None
assert value['release_authority'] is False
assert value['observed_data_used'] is False
assert len({row['candidate_id'] for row in value['candidates']}) == 37
assert sum(row['candidate_id'] == 'PR284_NEW:FINITE-REGISTERED-PATH' and row['triage_disposition'] == 'DEFERRED' for row in value['candidates']) == 1
receipt = {
    'schema': 'htt.registered_survivor_surface.execution_receipt.v1',
    'source_commit': value['source']['commit'],
    'source_git_blob': value['source']['git_blob'],
    'surface_content_id': value['content_id'],
    'surface_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'coverage': value['coverage'],
    'release_authority': False,
    'observational_data_used': False,
    'terminal': 'PASS_REGISTERED_SURVIVOR_SURFACE_TRIAGE',
}
Path('/mnt/sn850x2t/htt_base_e2e/HTT_PR450_SEED_COVERAGE_REPAIR_R1_20260907T014908Z/evidence/EXECUTION_RECEIPT.json').write_text(
    json.dumps(receipt, indent=2, sort_keys=True) + '\n',
    encoding='ascii',
)
