#!/usr/bin/env python3
"""Exercise the reviewed P4 source overlay in an external disposable manuscript fixture."""
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
RAW = pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_science_synthesis_repair_actual')
PLAN = json.loads((HERE / 'APPLICATION_PLAN.json').read_text())
ORIGINAL = pathlib.Path(PLAN['destination'])
TARGET = RAW / 'fixture_04/P4'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def run(name, command, cwd=None, expected=0):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    (RAW / f'{name}.stdout').write_text(result.stdout)
    (RAW / f'{name}.stderr').write_text(result.stderr)
    assert result.returncode == expected, (name, result.returncode, expected, result.stderr[-1000:])
    return {'name': name, 'command': command, 'cwd': str(cwd) if cwd else None, 'exit': result.returncode,
            'stdout': str(RAW / f'{name}.stdout'), 'stderr': str(RAW / f'{name}.stderr')}

assert not TARGET.exists(), 'fixture_04 already exists; preserve first run'
TARGET.parent.mkdir(parents=True)
shutil.copytree(ORIGINAL, TARGET)
for rel, entry in PLAN['files'].items():
    p = TARGET / rel
    assert (sha(p) if p.exists() else None) == entry['preimage_sha256'], rel
records=[]
apply=[sys.executable, str(HERE/'apply_candidate.py'), '--apply-reviewed-candidate', '--test-target', str(TARGET)]
records.append(run('apply_04', apply))
assert len(json.loads((RAW/'apply_04.stdout').read_text())['changed']) == len(PLAN['files'])
records.append(run('assemble_04', [sys.executable, str(TARGET/'report/r36_11/assemble.py')]))
records.append(run('check_before_build_04', [sys.executable, str(TARGET/'report/r36_11/check.py')]))
records.append(run('build_04', ['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-cd',str(TARGET/'report/main.tex')]))
records.append(run('check_after_build_04', [sys.executable, str(TARGET/'report/r36_11/check.py')]))
records.append(run('apply_noop_04', apply))
assert json.loads((RAW/'apply_noop_04.stdout').read_text())['changed']==[]
info=subprocess.run(['pdfinfo',str(TARGET/'report/main.pdf')],text=True,capture_output=True,check=True).stdout
assert 'Pages:           24' in info, info
for name,expected in json.loads((TARGET/'report/r36_11/RETAINED_ORIGINAL.json').read_text()).items():
    assert sha(TARGET/'report'/name)==expected, name
assert sha(TARGET/'report/pm_history_supplement.json') == json.loads((TARGET/'report/r36_11/SOURCE_CONTRACT.json').read_text())['source_bindings']['pm_result']['sha256']
# A changed source and an unrelated target path must be rejected before a write.
BAD=RAW/'fixture_bad_04/P4';BAD.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(ORIGINAL,BAD)
with (BAD/'science/MANUSCRIPT.md').open('a') as f:f.write('\nwrong source sentinel\n')
records.append(run('wrong_source_rejection', [sys.executable,str(HERE/'apply_candidate.py'),'--apply-reviewed-candidate','--test-target',str(BAD)],expected=1))
assert 'destination drift' in (RAW/'wrong_source_rejection.stderr').read_text()
records.append(run('wrong_path_rejection', [sys.executable,str(HERE/'apply_candidate.py'),'--apply-reviewed-candidate','--test-target','/tmp/r36_wrong_target'],expected=1))
assert 'fixture target outside external repair directory' in (RAW/'wrong_path_rejection.stderr').read_text()
assert sha(ORIGINAL/'science/MANUSCRIPT.md') == PLAN['files']['science/MANUSCRIPT.md']['preimage_sha256']
receipt={'task_id':'R36-11-SCIENCE-SYNTHESIS','packet_id':'802f27624f89c741d95571fb1798a640bb28f17e40aba3b5022f6ac03a60d276','input_identity':'sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43','fixture':str(TARGET),'commands':records,'pdf_pages':24,'old_R32_unchanged':True,'scientific_producer_runs':0,'old_P4_numerical_consumer_runs':0,'qualified_products':['observable_bridge_manuscript_update'],'acceptance_met':False}
(RAW/'RAW_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':'PASS','fixture':str(TARGET),'commands':len(records),'pdf_pages':24},indent=2))
