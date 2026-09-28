"""Package selected research evidence; no scientific calculation or remote writes."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent
selected = set()

def add(path):
    path = ROOT / path
    if path.is_dir():
        selected.update(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    elif path.is_file():
        selected.add(path)
    else:
        raise FileNotFoundError(path)

for name in ('HTT_MES_CONTINUATION_20260928_KO.md',
             'HTT_MES_NEXT_THEORY_PROMPT_20260928_KO.md',
             'CONTINUATION_PACKAGE_README.md', 'build_continuation_package.py',
             'integration_i1', 'harness'):
    add(name)
for p in (ROOT / 'recovery').iterdir():
    if p.is_file():
        selected.add(p)
for name in ('early_selected', 'latest_loops', 'remote_sources',
             'remote_sources_r10_local', 'remote_sources_r10_review'):
    add('recovery/' + name)
for p in (ROOT / 'recovery/research').iterdir():
    if p.name != 'history':
        add(p.relative_to(ROOT))
for p in (ROOT / 'recovery/catalog').iterdir():
    if p.name != 'exports':
        add(p.relative_to(ROOT))
for name in ('schema.sql', 'verification.json', 'scan_summary.json', 'sources.jsonl.gz', 'meta.jsonl.gz'):
    add('recovery/catalog/exports/' + name)

decision_path = ROOT / 'integration_i1/INDEPENDENT_DECISION.json'
decision = json.loads(decision_path.read_text())
candidate_path = ROOT / 'integration_i1/TARGET_RESPONSE_THEORY_KO.md'
candidate_sha = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
assert candidate_sha in json.dumps(decision), 'Final candidate identity not bound by independent decision'
assert decision['decision'] == 'DEFENDED_CONDITIONAL'
intake = json.loads((ROOT / 'recovery/BACKUP_INTAKE.json').read_text())
origins = [{k: item[k] for k in ('archive', 'sha256', 'bytes')} for item in intake]
state = {
    'schema': 'htt_mes.i1_continuation_state.v1',
    'date': '2026-09-28',
    'base_main': 'cc162c804eecb3c588efc6edadbe057a8a67301f',
    'base_tree': 'f14a536e7934d99bbe67489d1b81e5da0079cb09',
    'candidate_sha256': candidate_sha,
    'independent_decision': decision['decision'],
    'claim_ceiling': 'conditional external analytic continuation',
    'preserved_gates': decision['preserved_gates'],
    'next_action': 'source-supported same-state residual target budget or explicit identified quotient/minimal blocker',
    'completed': ['backup_integrity', 'all_branch_ref_inventory', 'main_tree_inventory',
                  'catalog_reuse_without_db_restore', 'selected_historical_and_current_source_reads',
                  'I1_derivation', 'bounded_actual_symbolic_calculation', 'independent_conditional_review'],
    'not_claimed': ['full_repository_scientific_audit', 'all_archive_full_semantic_read',
                    'full_conversation_transcript_recovery', 'academic_novelty',
                    'empirical_constraint', 'production_implementation'],
    'remote_mutations': 0,
    'database_downloaded_or_restored': False
}
state_path = ROOT / 'integration_i1/state/RESEARCH_STATE.json'
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n')
selected.add(state_path)
provenance = {
    'schema': 'htt_mes.continuation_package.v1',
    'created_date': '2026-09-28',
    'original_archives': origins,
    'base_main': state['base_main'],
    'base_tree': state['base_tree'],
    'candidate_sha256': candidate_sha,
    'independent_decision': decision['decision'],
    'scope': 'Compact current handoff plus selected source evidence and complete metadata inventories; not a replacement for original backups.',
    'omitted_original_content': ['input ZIP files', 'recovery/research/history archive collection',
                                 'complete catalog exports except small schema/verification/source metadata'],
    'query_restore_note': 'query_exports.py needs original 03_CATALOG exports; narrowed locators and topic JSON are included.',
    'payload_files': len(selected) + 1,
    'manifest_note': 'MANIFEST.sha256 covers all other entries, including this provenance file; hashes establish byte identity only.'
}
provenance_path = ROOT / 'PACKAGE_PROVENANCE.json'
provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n')
selected.add(provenance_path)
ordered = sorted(selected, key=lambda p: p.relative_to(ROOT).as_posix())
manifest = ''.join(hashlib.sha256(p.read_bytes()).hexdigest() + '  ' + p.relative_to(ROOT).as_posix() + '\n' for p in ordered)
package_path = ROOT / 'HTT_MES_CONTINUATION_I1_20260928.zip'
with zipfile.ZipFile(package_path, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for p in ordered:
        archive.write(p, p.relative_to(ROOT).as_posix())
    archive.writestr('MANIFEST.sha256', manifest)
with zipfile.ZipFile(package_path) as archive:
    assert archive.testzip() is None
    rows = archive.read('MANIFEST.sha256').decode().splitlines()
    for row in rows:
        expected, path = row.split('  ', 1)
        assert hashlib.sha256(archive.read(path)).hexdigest() == expected, path
    assert len(rows) + 1 == len(archive.namelist())
receipt = {
    'package': package_path.name,
    'bytes': package_path.stat().st_size,
    'sha256': hashlib.sha256(package_path.read_bytes()).hexdigest(),
    'payload_files': len(rows),
    'entries_including_manifest': len(rows) + 1,
    'zip_crc': 'PASS',
    'all_payload_sha256': 'PASS',
    'current_candidate_matches_independent_decision': True
}
(ROOT / 'PACKAGE_VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
(ROOT / (package_path.name + '.sha256')).write_text(receipt['sha256'] + '  ' + package_path.name + '\n')
print(json.dumps(receipt, indent=2))
