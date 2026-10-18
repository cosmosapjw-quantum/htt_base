"""Record preparation controls or start the single cumulative science allocation."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parent
REPO=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
RAW=Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/source_null_20261018')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(name,data):(ROOT/name).write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def git(*args):return subprocess.check_output(['git',*args],cwd=REPO,text=True).strip()


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['controls','science','freeze']);args=p.parse_args()
    if Path(sys.executable).absolute()!=REPO/'.venv/bin/python':
        raise RuntimeError('Canonical .venv/bin/python invocation required')
    if args.action=='freeze':
        if not (ROOT/'execution.json').exists():raise RuntimeError('No execution receipt')
        files={p.name:{'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.iterdir())
               if p.is_file() and p.name not in {'CANDIDATE.json'} and not p.name.startswith('REVIEW')}
        save('CANDIDATE.json',{'files':files,'scope':'candidate before later independent review',
                               'git_head_at_freeze':git('rev-parse','HEAD'),'review_status':'PENDING',
                               'science_state':'DIAGNOSTIC_ONLY; mB/H02/S02 HOLD; original nodes unchanged'})
        return
    env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',
             NUMEXPR_NUM_THREADS='2',VECLIB_MAXIMUM_THREADS='2',MPLBACKEND='Agg',PYTHONDONTWRITEBYTECODE='1')
    with tempfile.TemporaryDirectory(prefix='pantheon-mpl-') as mpl:
        env['MPLCONFIGDIR']=mpl
        if args.action=='controls':
            log=ROOT/'controls.json'
            if log.exists():raise RuntimeError('Preserve prior controls; review before another attempt')
            cmd=[sys.executable,'-B',str(ROOT/'test_controls.py')]
            start=time.monotonic();r=subprocess.run(cmd,cwd=REPO,env=env,capture_output=True,text=True)
            (ROOT/'controls.stdout.txt').write_text(r.stdout);(ROOT/'controls.stderr.txt').write_text(r.stderr)
            save('controls.json',{'command':cmd,'cwd':str(REPO),'returncode':r.returncode,
                                  'elapsed_seconds':time.monotonic()-start,
                                  'source_sha256':{n:sha(ROOT/n) for n in ('campaign.py','test_controls.py')},
                                  'classification':'Generated fixtures only, no physical acceptance'})
            print(r.stdout+r.stderr);sys.exit(r.returncode)
        if (ROOT/'launch.json').exists() or (ROOT/'execution.json').exists():
            raise RuntimeError('Science allocation already started; no reset or automatic rerun')
        controls=json.loads((ROOT/'controls.json').read_text())
        if controls['returncode']!=0 or any(sha(ROOT/n)!=s for n,s in controls['source_sha256'].items()):
            raise RuntimeError('Controls absent/failed or code changed')
        import numpy,scipy,astropy,matplotlib
        acquisition=json.loads((ROOT/'acquisition.json').read_text())
        known={str(Path(e['local'])) for e in acquisition['framing']+acquisition['entries']}
        new=[{'local':str(p),'size':p.stat().st_size,'sha256':sha(p)} for p in sorted(RAW.rglob('*')) if p.is_file() and str(p) not in known]
        final_bytes=acquisition['charged_source_bytes']+sum(x['size'] for x in new)
        if final_bytes>acquisition['cap_bytes']:raise RuntimeError('Acquisition cap exceeded')
        save('acquisition_final.json',{'original_receipt_sha256':sha(ROOT/'acquisition.json'),
                                      'original_charged_bytes':acquisition['charged_source_bytes'],
                                      'supplemental_framer_source_files':new,'total_charged_source_bytes':final_bytes,
                                      'cap_bytes':20_000_000,'new_HTTP_bytes_this_executor':acquisition['http_body_bytes'],
                                      'reuse_unique_bytes':acquisition['reused_fitres']['size'],
                                      'all_original_source_identities_verified_before_science':True})
        # Verify every acquired or reused immutable source against its recorded identity.
        for e in acquisition['framing']+acquisition['entries']:
            if sha(e['local'])!=e['sha256']:raise RuntimeError('Source identity changed: '+e['local'])
        cmd=[sys.executable,'-B',str(ROOT/'campaign.py')]
        launch={'command':cmd,'cwd':str(REPO),'git_head':git('rev-parse','HEAD'),
                'git_branch':git('branch','--show-current'),'git_status':git('status','--short'),
                'utc':datetime.now(timezone.utc).isoformat(),'interpreter':sys.executable,
                'resolved_interpreter':str(Path(sys.executable).resolve()),'python_version':sys.version,
                'package_versions':{m.__name__:m.__version__ for m in (numpy,scipy,astropy,matplotlib)},
                'thread_environment':{k:env[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')},
                'contract_sha256':sha(ROOT/'CONTRACT.md'),'coordinate_amendment_sha256':sha(ROOT/'COORDINATE_SOURCE_AMENDMENT.md'),
                'direction_rule':'SNANA_FLOAT32_PROMOTED_TO_FITS_FLOAT64',
                'source_code_sha256':{n:sha(ROOT/n) for n in ('campaign.py','acquire.py','test_controls.py','run.py')},
                'acquisition_final_sha256':sha(ROOT/'acquisition_final.json'),
                'requested_model':'gpt-6.1-sol/high','observed_runtime':'UNKNOWN',
                'cumulative_hard_timeout_seconds':120,'previous_science_seconds':0,
                'source_identity_reverified':True}
        save('launch.json',launch)
        save('execution.json',{'state':'STARTED','command':cmd,'utc_started':launch['utc'],
                               'allocation_seconds':120,'consumed_seconds':'UNKNOWN_WHILE_RUNNING','attempt':1})
        start=time.monotonic()
        try:
            r=subprocess.run(cmd,cwd=REPO,env=env,capture_output=True,text=True,timeout=120)
            elapsed=time.monotonic()-start
            (ROOT/'science.stdout.txt').write_text(r.stdout);(ROOT/'science.stderr.txt').write_text(r.stderr)
            receipt={'state':'RETURNED','returncode':r.returncode,'consumed_seconds':elapsed,
                     'remaining_seconds':max(0,120-elapsed),'attempt':1,'command':cmd,
                     'launch_sha256':sha(ROOT/'launch.json'),'stdout_sha256':sha(ROOT/'science.stdout.txt'),
                     'stderr_sha256':sha(ROOT/'science.stderr.txt'),'no_automatic_replay':True}
            save('execution.json',receipt);print(json.dumps(receipt,indent=2));print(r.stdout+r.stderr)
            sys.exit(r.returncode)
        except subprocess.TimeoutExpired as exc:
            (ROOT/'science.stdout.txt').write_bytes(exc.stdout or b'');(ROOT/'science.stderr.txt').write_bytes(exc.stderr or b'')
            save('execution.json',{'state':'TIMEOUT','consumed_seconds':120,'remaining_seconds':0,'attempt':1,'command':cmd,
                                   'raw_failure':'TimeoutExpired','launch_sha256':sha(ROOT/'launch.json')})
            raise


if __name__=='__main__':main()
