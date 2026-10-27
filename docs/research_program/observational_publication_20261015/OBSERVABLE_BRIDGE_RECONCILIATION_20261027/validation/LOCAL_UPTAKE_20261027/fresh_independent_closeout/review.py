import copy
import csv
import decimal
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT = Path(__file__).parent
AUTHOR = OUT.parent / 'r36_intake_serialization_repair'
CONTRACT = OUT.parent / 'r36_blind_intake_binding_review/REPAIR_CONTRACT.json'
REL = 'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0')
raw = []
checks = {}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def identify(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': digest(data)}

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def command(name, argv, retain=False):
    started = time.monotonic()
    p = subprocess.run(argv, cwd=ROOT, env=ENV, capture_output=True)
    receipt = {'name': name, 'argv': argv, 'exit_code': p.returncode,
               'seconds': time.monotonic() - started,
               'stdout_sha256': digest(p.stdout), 'stderr_sha256': digest(p.stderr)}
    if retain:
        for stream in ('stdout', 'stderr'):
            target = OUT / (name + '.' + stream)
            target.write_bytes(getattr(p, stream))
            receipt[stream + '_path'] = str(target)
    elif len(p.stdout) + len(p.stderr) < 3000:
        receipt.update(stdout=p.stdout.decode(), stderr=p.stderr.decode())
    raw.append(receipt)
    write('RAW_RECEIPT.json', raw)
    assert p.returncode == 0, receipt
    return p.stdout

def changes(a, b, pointer=''):
    if type(a) != type(b):
        return [pointer]
    if isinstance(a, dict):
        assert a.keys() == b.keys(), pointer
        return [p for k in a for p in changes(a[k], b[k], pointer + '/' + k)]
    if isinstance(a, list):
        assert len(a) == len(b), pointer
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in changes(x, y, pointer + '/' + str(i))]
    return [] if a == b else [pointer]

def main():
    assert digest(CONTRACT.read_bytes()) == '019ad3396b0b732bf40149d69ddf84fc9652f28f3a48288282e542ca424af7b9'
    c = json.loads(CONTRACT.read_bytes())
    allowed = c['allowed_repository_paths']
    state_path = ROOT / c['state_at_review']['path']
    index_path = ROOT / command('index_path', ['git', 'rev-parse', '--git-path', 'index']).decode().strip()
    state_before, index_before = state_path.read_bytes(), index_path.read_bytes()
    assert identify(state_path) == {k: c['state_at_review'][k] for k in ('bytes', 'sha256')}
    assert command('head', ['git', 'rev-parse', 'HEAD']).decode().strip() == c['base']['HEAD']
    assert command('branch', ['git', 'branch', '--show-current']).decode().strip() == c['base']['branch']
    assert command('origin', ['git', 'remote', 'get-url', 'origin']).decode().strip() == c['base']['origin']
    status_before = command('status_before', ['git', 'status', '--porcelain=v1', '-z'], True)
    assert not command('staged_before', ['git', 'diff', '--cached', '--name-only', '-z'])
    before, after = {}, {}
    for row in c['preimages_and_exact_target_identities']:
        path = row['before']['path']
        original = AUTHOR / 'approved_repair_preimages' / path
        assert identify(original) == {k: row['before'][k] for k in ('bytes', 'sha256')}, path
        before[path] = original.read_bytes()
        after[path] = (ROOT / path).read_bytes()
        assert identify(ROOT / path) == {k: row['after'][k] for k in ('bytes', 'sha256')}, path
        assert command('head_blob_' + str(len(before)), ['git', 'show', 'HEAD:' + path]) == before[path], path
    checks['six_candidate_identities'] = [x['after'] for x in c['preimages_and_exact_target_identities']]
    checks['six_preimages_equal_frozen_HEAD'] = True

    def other_status(value):
        return sorted(x for x in value.split(b'\0') if x and x[3:].decode() not in allowed)

    assert other_status(status_before) == other_status((AUTHOR / 'REPAIR_STATUS_BEFORE.stdout').read_bytes())
    assert status_before == (AUTHOR / 'REPAIR_STATUS_AFTER.stdout').read_bytes()
    for row in c['exact_changes']:
        if 'append_text' in row:
            p = row['path']
            assert after[p] == before[p] + row['append_text'].encode(), p
    csv_path = REL + '/imports/v15/cas/response_frontier.csv'
    a, b = before[csv_path], after[csv_path]
    assert a.count(b'\r') == 0 and a.count(b'\n') == 241
    assert b == a.replace(b'\n', b'\r\n') and b.count(b'\r\n') == 241
    tokens_a = list(csv.reader(io.StringIO(a.decode(), newline='')))
    tokens_b = list(csv.reader(io.StringIO(b.decode(), newline='')))
    assert tokens_a == tokens_b and len(tokens_a) == 241 and all(len(x) == 6 for x in tokens_a)
    checks['csv'] = {'rows_including_header': 241, 'columns_each': 6, 'exact_tokens_equal': True,
                     'only_LF_to_CRLF': True, 'CRLF_count': 241}
    e, f, d, h = [REL + '/' + name for name in ('EVIDENCE_MANIFEST.json', 'FRONTIER.json', 'DELIVERY_MANIFEST.json', 'HANDOFF_CURRENT_SESSION.md')]
    old_e, new_e = json.loads(before[e]), json.loads(after[e])
    assert changes(old_e, new_e) == ['/files/155/sha256', '/files/155/bytes']
    source = c['protected_inputs'][0]
    assert new_e['files'][155] == source and len(new_e['files']) == 156
    expected_e_bytes = before[e].replace(old_e['files'][155]['sha256'].encode(), source['sha256'].encode()).replace(b'"bytes": 111343', b'"bytes": 111342')
    assert after[e] == expected_e_bytes
    old_f, new_f = json.loads(before[f]), json.loads(after[f])
    assert len(new_f['tasks']) == 11
    permitted = [v for i in range(11) for v in (f'/tasks/{i}/input_identity', f'/tasks/{i}/input_sources/0/sha256')]
    actual = changes(old_f, new_f)
    assert actual == permitted
    assert after[f] == before[f].replace(digest(before[e]).encode(), digest(after[e]).encode())
    for task in new_f['tasks']:
        assert task['input_identity'] == 'sha256:' + digest(after[e])
        assert task['input_sources'][0]['sha256'] == digest(after[e])
    old_d, new_d = json.loads(before[d]), json.loads(after[d])
    expected_d = copy.deepcopy(old_d)
    for row in expected_d['files']:
        if row['path'] in (e, f, h):
            row.update(sha256=digest(after[row['path']]), bytes=len(after[row['path']]))
    assert new_d == expected_d and len(new_d['files']) == 196
    assert after[d] == (json.dumps(expected_d, indent=2, ensure_ascii=False) + '\n').encode()
    checks['structured_delta'] = {'evidence': changes(old_e, new_e), 'frontier': actual, 'delivery': changes(old_d, new_d),
                                  'all_other_fields_unchanged': True, 'existing_text_and_formatting_preserved': True}

    source_bytes = (ROOT / source['path']).read_bytes()
    assert digest(source_bytes + b'\n') == old_e['files'][155]['sha256']
    def pairs(rows):
        result = {}
        for key, value in rows:
            assert key not in result, key
            result[key] = value
        return result
    parse = dict(parse_float=decimal.Decimal, parse_int=decimal.Decimal, object_pairs_hook=pairs)
    assert json.loads(source_bytes, **parse) == json.loads(source_bytes + b'\n', **parse)
    checks['H03'] = {'unchanged_source_sha256': digest(source_bytes), 'historical_plus_LF_sha256': digest(source_bytes + b'\n'),
                     'exact_Decimal_JSON_parity': True, 'tolerance': 'zero', 'duplicate_keys_absent': True}
    for row in c['protected_inputs']:
        assert identify(ROOT / row['path']) == {k: row[k] for k in ('bytes', 'sha256')}, row['path']
    historical_tracked_diff = command('historical_tracked_diff', ['git', 'diff', '--name-only', 'HEAD', '--',
        'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025', REL]).decode().splitlines()
    assert set(historical_tracked_diff) == set(allowed) - {'.gitattributes'}
    closures = {}
    for name, count in [('EVIDENCE_MANIFEST.json', 156), ('IMPORT_MANIFEST.json', 120), ('DELIVERY_MANIFEST.json', 196)]:
        manifest = json.loads((ROOT / REL / name).read_bytes())
        assert len(manifest['files']) == count
        assert len({r['path'] for r in manifest['files']}) == count
        for row in manifest['files']:
            assert identify(ROOT / row['path']) == {k: row[k] for k in ('bytes', 'sha256')}, row['path']
        closures[name] = {'verified': count, 'total': count}
    checks['manifest_closure'] = closures

    baseline = OUT.parent / 'r35_publication_acceleration_uptake'
    protected = json.loads((baseline / 'GRSTAT_BEFORE.json').read_bytes())
    assert len(protected) == 752
    for path, row in protected.items():
        assert identify(ROOT / path) == {k: row[k] for k in ('bytes', 'sha256')}, path
    modes = json.loads((baseline / 'INDEX_PUBLISHED_METADATA_NORMALIZATION.json').read_bytes())
    mode_observations = []
    for row in modes:
        path = ROOT / row['argv'][-1].split(',', 2)[-1]
        stat = path.lstat()
        observed = {'mode': stat.st_mode, 'inode': stat.st_ino, 'symlink': path.is_symlink(),
                    'link': os.readlink(path) if path.is_symlink() else None}
        assert observed == row['filesystem_before'], str(path)
        mode_observations.append({'path': str(path), **observed})
    checks['preservation'] = {'protected_files_verified': len(protected), 'protected_bytes': sum(x['bytes'] for x in protected.values()),
                              'mode_and_symlink': mode_observations, 'unrelated_dirty_status_equal_author_before': True,
                              'old_R32_and_historical_receipts_unchanged': True}
    failure_rows = []
    for row in c['raw_failure_to_retain']:
        current = identify(Path(row['path']))
        if 'sha256' in row:
            assert current['sha256'] == row['sha256']
        failure_rows.append({'path': row['path'], **current})
    failure_receipt = json.loads((AUTHOR / 'FIRST_PREFLIGHT.json').read_bytes())
    failure_stderr = (AUTHOR / 'FIRST_PREFLIGHT.stderr').read_bytes()
    assert failure_receipt['exit_code'] == 1 and b'changed evidence: ' + csv_path.encode() in failure_stderr
    diagnosis = json.loads((AUTHOR / 'DIAGNOSIS_STOP.json').read_bytes())
    comparisons = json.loads((AUTHOR / 'ALL_156_MANIFEST_COMPARISONS.json').read_bytes())
    assert diagnosis['matching'] == 154 and len(diagnosis['mismatches']) == 2
    assert sum(not x['current_matches_manifest'] for x in comparisons) == 2
    assert {x['path'] for x in diagnosis['mismatches']} == {csv_path, source['path']}
    checks['historical_failures'] = {'actual_failed_preflight_commands': 1, 'diagnostic_mismatches': 2, 'preserved': failure_rows}

    attr = command('attributes', ['git', 'check-attr', 'text', '--', csv_path]).decode().strip()
    assert attr == csv_path + ': text: unset'
    filtered = command('filtered_blob', ['git', 'hash-object', '--path=' + csv_path, csv_path]).decode().strip()
    plain = command('unfiltered_blob', ['git', 'hash-object', '--no-filters', csv_path]).decode().strip()
    calculated = hashlib.sha1(b'blob ' + str(len(after[csv_path])).encode() + b'\0' + after[csv_path]).hexdigest()
    assert filtered == plain == calculated == '108f872fe9e919fc9521584ada607158fc5f87a9'
    checks['git_CSV_filters'] = {'text_attribute': 'unset', 'filtered_blob_oid': filtered, 'unfiltered_blob_oid': plain,
                               'independently_calculated_blob_oid': calculated, 'CRLF_preserved': True}
    diff = command('EXACT_SIX_FILE_DIFF', ['git', 'diff', '--binary', '--no-ext-diff', '--'] + allowed, True)
    assert diff == (AUTHOR / 'REPAIR_EXACT_DIFF.stdout').read_bytes()
    assert digest(diff) == '373af66c24764d8ebe05b32ae8637dfbc8f2c77712b09194ff6523687696636f'
    checks['exact_candidate_six_file_diff_sha256'] = digest(diff)
    write('CHECKS_BEFORE_PREFLIGHT.json', checks)

    state = json.loads(state_before)
    assert (len(state['tasks']), len(state['packets']), len(state['events'])) == (98, 201, 677)
    assert not any(key.startswith('R36-') for key in state['tasks'])
    assert not any(x['frontier']['frontier_id'] == new_f['frontier_id'] for x in state.get('frontiers', []))
    preflight = json.loads(command('ACTUAL_PREFLIGHT', ['.venv/bin/python', 'scripts/codex_harness/publication_frontier_preflight.py',
        '--state', str(state_path.relative_to(ROOT)), '--frontier', f, '--manifest', e], True))
    roots = [x['id'] for x in new_f['tasks'] if x['requires'] == {'all': []}]
    assert len(roots) == 9 and preflight['candidate_root_tasks'] == roots
    assert preflight['status'] == 'APPEND_READY' and preflight['writes_state'] is False
    assert preflight['evidence_files_verified'] == 156 and preflight['state_observed'] is True
    assert state_path.read_bytes() == state_before
    assert index_path.read_bytes() == index_before
    assert command('status_after', ['git', 'status', '--porcelain=v1', '-z'], True) == status_before
    assert command('head_after', ['git', 'rev-parse', 'HEAD']).decode().strip() == c['base']['HEAD']
    assert index_path.read_bytes() == index_before
    for row in c['preimages_and_exact_target_identities']:
        assert (ROOT / row['after']['path']).read_bytes() == after[row['after']['path']]
    for row in c['protected_inputs']:
        assert identify(ROOT / row['path']) == {k: row[k] for k in ('bytes', 'sha256')}
    for row in failure_rows:
        assert identify(Path(row['path'])) == {k: row[k] for k in ('bytes', 'sha256')}
    checks['actual_preflight'] = preflight
    checks['state_and_index'] = {'STATE_sha256': digest(state_before), 'STATE_bytes': len(state_before),
                               'index_sha256': digest(index_before), 'STATE_and_index_bytes_unchanged': True,
                               'tasks': 98, 'packets': 201, 'events': 677, 'R36_tasks_or_frontiers': 0,
                               'campaign_route_task_history_cost_bytes_unchanged': True}
    checks['decision'] = 'APPROVE'
    write('CHECKS.json', checks)
    print(json.dumps({'decision': 'APPROVE', 'diff_sha256': digest(diff), 'manifest_closure': closures,
                      'preflight': preflight['status'], 'roots': len(roots), 'protected_files': len(protected)}))

try:
    main()
except Exception as exc:
    write('REVIEW_CHECK_FAILURE.json', {'error': repr(exc), 'completed_checks': checks})
    raise
