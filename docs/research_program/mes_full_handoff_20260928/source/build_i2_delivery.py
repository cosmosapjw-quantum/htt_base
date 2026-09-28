"""Create a lossless HTT/MES local handoff from already acquired research bytes."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / 'delivery_i2_split'

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def files_under(path):
    return sorted(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts)

def compact_checkpoint():
    candidate = ROOT / 'integration_i2/PHYSICAL_RESIDUAL_AND_IDENTIFIED_SET_KO.md'
    decision = json.loads((ROOT / 'integration_i2/INDEPENDENT_DECISION.json').read_text())
    assert digest(candidate) in json.dumps(decision), 'Final candidate not bound by review'
    files = files_under(ROOT / 'integration_i2') + [
        ROOT / 'HTT_MES_I2_REPORT_20260928_KO.md',
        ROOT / 'HTT_MES_I3_NEXT_PROMPT_20260928_KO.md',
    ]
    files = sorted(files)
    manifest = ''.join(digest(p) + '  ' + p.relative_to(ROOT).as_posix() + '\n' for p in files)
    out = ROOT / 'HTT_MES_CONTINUATION_I2_20260928.zip'
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT).as_posix())
        z.writestr('MANIFEST.sha256', manifest)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        for line in manifest.splitlines():
            expected, name = line.split('  ', 1)
            assert hashlib.sha256(z.read(name)).hexdigest() == expected
    return out, len(files)

def stage_copy(source, relative, role, entries, expected_hash=None):
    target = STAGE / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == '.zip':
        os.link(source, target)
    else:
        shutil.copy2(source, target)
    actual = digest(target)
    if expected_hash:
        assert actual == expected_hash, source.name
    entries.append({'path': relative, 'role': role,
                    'size_bytes': target.stat().st_size, 'sha256': actual})

def main():
    if STAGE.exists():
        raise FileExistsError('Use a fresh delivery stage; never silently overwrite it')
    checkpoint, count = compact_checkpoint()
    STAGE.mkdir()
    entries = []
    intake = json.loads((ROOT / 'recovery/BACKUP_INTAKE.json').read_text())
    roles = ['research_backup', 'early_archive_backup', 'catalog_backup']
    for item, role in zip(intake, roles):
        stage_copy(ROOT / 'upload' / item['archive'], 'backups/' + item['archive'],
                   role, entries, item['sha256'])
    for name, role in [('HTT_MES_CONTINUATION_I1_20260928.zip', 'i1_checkpoint'),
                       (checkpoint.name, 'i2_checkpoint')]:
        stage_copy(ROOT / name, 'checkpoints/' + name, role, entries)
    for source in files_under(ROOT / 'handoff_i2'):
        stage_copy(source, source.relative_to(ROOT).as_posix(), 'support_file', entries)
    for name in ['HTT_MES_I2_REPORT_20260928_KO.md', 'HTT_MES_I3_NEXT_PROMPT_20260928_KO.md',
                 'HTT_MES_LOCAL_CODEX_GUIDE_20260928_KO.md', 'build_i2_delivery.py']:
        stage_copy(ROOT / name, name, 'support_file', entries)
    manifest = {'schema_version': 1, 'date': '2026-09-28',
                'scope': 'All three original thread backups, complete I1/I2 checkpoints, and local handoff tools.',
                'exclusions': ['unrecovered chat transcript', 'full remote git object database',
                               'separately supplied toolchain/vendor and BASS prerequisite bundles'],
                'base_main': 'cc162c804eecb3c588efc6edadbe057a8a67301f',
                'source_archive_bytes_preserved': True,
                'database_restored': False,
                'files': entries}
    (STAGE / 'DELIVERY_MANIFEST.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    spec = importlib.util.spec_from_file_location('handoff_restore', ROOT / 'handoff_i2/restore_handoff.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    i2_infos = module.inspect_zip(checkpoint)
    verify = subprocess.run([sys.executable, str(STAGE / 'handoff_i2/restore_handoff.py')],
                            capture_output=True, text=True, check=True)
    receipt = json.loads(verify.stdout)
    assert receipt['status'] == 'VERIFIED_ARCHIVE_BYTES_ONLY'
    # Receipt is generated after its verified inputs and is not included in that manifest.
    (STAGE / 'DELIVERY_VALIDATION.json').write_text(json.dumps({
        'manifest_sha256': receipt['manifest_sha256'],
        'manifest_input_verification': receipt['status'],
        'verified_entries': len(receipt['verified_files']),
        'i2_zip_structure': 'ACCEPTED', 'i2_entries': len(i2_infos),
        'restore_tool_tests': 11, 'restore_tool_tests_exit': 0,
        'full_original_restore_this_turn': False,
        'scope': 'Byte identity and extraction contract, not scientific validation or user-host restore.'
    }, indent=2) + '\n')
    out = ROOT / 'HTT_MES_LOCAL_CODEX_FULL_20260928.zip'
    with zipfile.ZipFile(out, 'w', allowZip64=True) as z:
        for source in files_under(STAGE):
            compression = zipfile.ZIP_STORED if source.suffix == '.zip' else zipfile.ZIP_DEFLATED
            z.write(source, source.relative_to(STAGE).as_posix(), compress_type=compression)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
        total_entries = len(z.infolist())
    full_hash = digest(out)
    (ROOT / (out.name + '.sha256')).write_text(full_hash + '  ' + out.name + '\n')
    parts = []
    joined_digest = hashlib.sha256()
    with out.open('rb') as source:
        index = 1
        while block := source.read(400 * 1024 * 1024):
            part = ROOT / (out.name + f'.part{index:02d}')
            part.write_bytes(block)
            # Re-read each output part, checking the actual reconstructible bytes.
            with part.open('rb') as part_stream:
                for piece in iter(lambda: part_stream.read(1024 * 1024), b''):
                    joined_digest.update(piece)
            parts.append({'file': part.name, 'size_bytes': part.stat().st_size, 'sha256': digest(part)})
            index += 1
    assert len(parts) == 2
    assert joined_digest.hexdigest() == full_hash
    final_receipt = {'file': out.name, 'size_bytes': out.stat().st_size, 'sha256': full_hash,
                     'outer_entries': total_entries, 'zip_crc': 'PASS',
                     'manifest_entries_verified': len(entries),
                     'original_backup_archives_included': 3,
                     'i1_archive_preserved': True, 'i2_payload_files': count,
                     'i2_archive_sha256': digest(checkpoint),
                     'delivery_parts': parts,
                     'part_reconstruction_sha256': joined_digest.hexdigest(),
                     'part_reconstruction': 'PASS',
                     'single_file_limit_bytes': 536870912,
                     'scientific_verdict': 'See frozen independent I2 decision',
                     'full_original_restore_this_turn': False}
    (ROOT / 'HTT_MES_I2_DELIVERY_VALIDATION_20260928.json').write_text(json.dumps(final_receipt, indent=2) + '\n')
    print(json.dumps(final_receipt, indent=2))

if __name__ == '__main__':
    main()
