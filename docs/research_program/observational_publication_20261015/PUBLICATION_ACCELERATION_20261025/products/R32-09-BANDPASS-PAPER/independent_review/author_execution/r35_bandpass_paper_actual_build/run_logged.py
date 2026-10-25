import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
name,cwd,*command=sys.argv[1:]
root=Path(cwd);raw=root/'raw';raw.mkdir(exist_ok=True)
assert not (raw/f'{name}.receipt.json').exists(), 'preserve prior receipts'
preimages={}
for p in list(root.glob('*.py'))+list((root/'report').glob('*.tex')):
    target=raw/f'{name}.{p.name}.source';target.write_bytes(p.read_bytes());preimages[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
start=time.time();startutc=datetime.datetime.now(datetime.timezone.utc).isoformat()
env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['MPLCONFIGDIR']='/mnt/extdrive/workdir/htt_open_data/r35_bandpass_paper_actual_build/matplotlib'
with (raw/f'{name}.stdout').open('wb') as stdout,(raw/f'{name}.stderr').open('wb') as stderr:
    proc=subprocess.run(command,cwd=root,env=env,stdout=stdout,stderr=stderr,timeout=600)
r={'command':command,'cwd':str(root),'started_utc':startutc,'duration_seconds':time.time()-start,'exit_code':proc.returncode,'source_preimages_sha256':preimages,'stdout':str(raw/f'{name}.stdout'),'stderr':str(raw/f'{name}.stderr')}
(raw/f'{name}.receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2));print((raw/f'{name}.stdout').read_text()[-2000:]);print((raw/f'{name}.stderr').read_text()[-1200:]);sys.exit(proc.returncode)
