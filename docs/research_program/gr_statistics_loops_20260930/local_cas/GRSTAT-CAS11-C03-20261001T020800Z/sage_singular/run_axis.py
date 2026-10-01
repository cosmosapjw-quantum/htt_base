#!/usr/bin/python3
"""Execute the independent SageMath + Singular algebra kernels and emit one JSON payload."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
HERE = Path(__file__).resolve().parent
CONTRACT = ROOT / 'docs/research_program/gr_statistics_loops_20260930/cas_corr_followup_20260930/intake/contracts/CAS11-C03-WEIGHTED-PROJECTION.json'
EXPECTED_CONTRACT_SHA = 'a97dc88082095ba636d326ea390cf629b86ca333577a27638c83c2b7f9a55794'
OBLIGATION = 'CAS11-C03-WEIGHTED-PROJECTION'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def execute(label, argv, marker, timeout=120):
    rec = {'argv': argv, 'cwd': str(ROOT), 'timeout_seconds': timeout,
           'started_at': datetime.now(timezone.utc).isoformat()}
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                           timeout=timeout, check=False)
        rec.update(exit_code=p.returncode, stdout=p.stdout, stderr=p.stderr,
                   marker_found=marker in p.stdout.splitlines())
    except subprocess.TimeoutExpired as exc:
        rec.update(exit_code=None, timeout=True,
                   stdout=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or ''),
                   stderr=(exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr, bytes) else (exc.stderr or ''),
                   marker_found=False)
    except OSError as exc:
        rec.update(exit_code=None, launch_error=str(exc), stdout='', stderr='', marker_found=False)
    rec['completed_at'] = datetime.now(timezone.utc).isoformat()
    (HERE / f'{label}.stdout.log').write_text(rec['stdout'])
    (HERE / f'{label}.stderr.log').write_text(rec['stderr'])
    return rec

def main():
    expected_head = 'eb759602a94e4377ca3d0a5d272dd822b6f32783'
    source = {name: sha(HERE / name) for name in ('PROOF.md','proof.sage','proof.sing','run_axis.py')}
    try:
        head = subprocess.run(['/usr/bin/git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    except Exception as exc:
        head = f'UNKNOWN: {exc}'
    identity_ok = ROOT == Path.cwd() and head == expected_head and sha(CONTRACT) == EXPECTED_CONTRACT_SHA
    engines = {}
    if identity_ok:
        engines['sage_version'] = execute('sage_version', ['/usr/local/bin/sage','--version'], 'SageMath version 10.9, Release Date: 2026-05-04')
        engines['singular_version'] = execute('singular_version', ['/usr/bin/Singular','-v'], 'SINGULAR_VERSION_MARKER_UNUSED')
        engines['sage'] = execute('sage', ['/usr/local/bin/sage',str(HERE/'proof.sage')], 'SAGE_ALL_OK')
        engines['singular'] = execute('singular', ['/usr/bin/Singular','-q',str(HERE/'proof.sing')], 'SINGULAR_ALL_OK')
    generated_sage = HERE / 'proof.sage.py'
    if generated_sage.is_file():
        source['proof.sage.py'] = sha(generated_sage)
    ok = identity_ok and all(engines.get(k,{}).get('exit_code') == 0 and engines[k].get('marker_found')
                            for k in ('sage_version','sage','singular')) and engines.get('singular_version',{}).get('exit_code') == 0 and generated_sage.is_file()
    receipt = {'axis':'sage_singular','contract_sha256':EXPECTED_CONTRACT_SHA,'head_expected':expected_head,
               'head_observed':head,'identity_ok':identity_ok,'source_sha256':source,
               'engines':engines,'proof_coverage':'PROOF.md arbitrary finite dimension, all subspaces/families and degenerate branches; exact CAS kernels in fixed generic symbolic sizes',
               'statement_alignment':'exact CAS11-C03 finite real positive-definite weighted projection target; no added invertibility of R',
               'completed_at':datetime.now(timezone.utc).isoformat(), 'all_closed':bool(ok)}
    (HERE/'ENGINE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    if ok:
        payload = {'checks':{OBLIGATION:True},'domain_assumption_diff':[],'counterexample':None}
        print(json.dumps(payload,separators=(',',':')))
        return 0
    print(json.dumps({'checks':{},'domain_assumption_diff':[], 'counterexample':None,
                      'error':'engine, marker, source or identity inconclusive'},separators=(',',':')))
    return 2

if __name__ == '__main__':
    sys.exit(main())
