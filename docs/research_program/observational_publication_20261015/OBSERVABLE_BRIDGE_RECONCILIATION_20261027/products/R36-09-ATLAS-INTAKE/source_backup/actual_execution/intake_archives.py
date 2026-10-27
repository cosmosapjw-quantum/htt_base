"""Read-only inspection of already published archive bytes; no solver execution."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
PREP = Path('/mnt/extdrive/workdir/htt_open_data/r36_atlas_source_preparation/responses')
SOURCES = [
    ('anilos-0.1.0.whl', 'https://raw.githubusercontent.com/jgvicente/AniLoS/9b7a2611882dcca80a1491bcad2b8f05635faca7/dist/anilos-0.1.0-cp310-cp310-linux_x86_64.whl', 805014, 'git:29d501387478d03add9c4334616d2257f06bef7f'),
    ('anilos-0.1.0.tar.gz', 'https://raw.githubusercontent.com/jgvicente/AniLoS/9b7a2611882dcca80a1491bcad2b8f05635faca7/dist/anilos-0.1.0.tar.gz', 38463523, 'git:212c3b1351369afb11b3d6250111abf2a7c2698a'),
]
for name in ['all_decoupled_plots.zip', 'all_coupled_plots.zip', 'all_coupled_chains.zip', 'all_decoupled_chains.zip']:
    d = json.loads((PREP/'zenodo48653.json').read_text())
    entry = next(x for x in d['files'] if x['key'] == name)
    SOURCES.append((name, entry['links']['self'], entry['size'], entry['checksum']))

def verify(path, size, expected):
    sha256 = hashlib.sha256()
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    if expected.startswith('git:'):
        sha1.update(f'blob {size}\0'.encode())
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            sha256.update(chunk); md5.update(chunk); sha1.update(chunk)
    observed = {'bytes': path.stat().st_size, 'sha256': sha256.hexdigest(), 'md5': md5.hexdigest(), 'git_blob': sha1.hexdigest() if expected.startswith('git:') else None}
    observed['integrity_pass'] = observed['bytes'] == size and (observed['git_blob'] if expected.startswith('git:') else observed['md5']) == expected.split(':',1)[1]
    return observed

def fetch(name, url, size, expected):
    dest = ROOT/'downloads'/name
    dest.parent.mkdir(exist_ok=True)
    if dest.exists():
        v = verify(dest,size,expected)
        if v['integrity_pass']:
            return {'source':url,'path':str(dest),'cache_reuse':True,**v}
        raise RuntimeError(f'existing cache failed integrity: {dest}: {v}')
    if shutil.disk_usage(ROOT).free - size < 2 * 1024**3:
        raise RuntimeError('two GiB reserve would be breached')
    tmp = dest.with_suffix(dest.suffix+'.partial')
    if tmp.exists():
        raise RuntimeError(f'partial exists, inspect before retry: {tmp}')
    req = urllib.request.Request(url, headers={'User-Agent':'htt-r36-atlas-intake/1'})
    start=time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=90) as r, tmp.open('xb') as f:
            response = {'http_status':r.status,'final_url':r.url,'content_type':r.headers.get('Content-Type'),'content_length':r.headers.get('Content-Length')}
            while True:
                chunk = r.read(1<<20)
                if not chunk: break
                f.write(chunk)
        v=verify(tmp,size,expected)
        if not v['integrity_pass']:
            raise RuntimeError(f'download integrity failed: {name}: {v}')
        os.replace(tmp,dest)
        return {'source':url,'path':str(dest),'cache_reuse':False,'elapsed_seconds':time.monotonic()-start,'http':response,**v}
    except BaseException as e:
        (ROOT/'first_failure.json').write_text(json.dumps({'source':url,'name':name,'error':repr(e),'partial':str(tmp),'partial_bytes':tmp.stat().st_size if tmp.exists() else 0},indent=2)+'\n')
        raise

def inventory(path):
    if path.name.endswith('.tar.gz'):
        with tarfile.open(path,'r:gz') as a:
            members=[{'path':m.name,'size':m.size,'kind': 'file' if m.isfile() else 'other'} for m in a.getmembers()]
    else:
        with zipfile.ZipFile(path) as a:
            members=[{'path':m.filename,'size':m.file_size,'compressed_size':m.compress_size,'kind':'dir' if m.is_dir() else 'file'} for m in a.infolist()]
    return {'member_count':len(members),'members':members}

if __name__=='__main__':
    receipts=[]
    for name,url,size,expected in SOURCES:
        rec=fetch(name,url,size,expected)
        receipts.append(rec)
        (ROOT/'downloads.json').write_text(json.dumps(receipts,indent=2)+'\n')
        inv=inventory(Path(rec['path']))
        (ROOT/(name+'.inventory.json')).write_text(json.dumps(inv,indent=2)+'\n')
        print(name,rec['bytes'],rec['integrity_pass'],inv['member_count'],flush=True)
