import concurrent.futures, hashlib, importlib.util, json, os, shutil, sys, threading, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / 'package'
MANIFEST = json.loads((PACKAGE / 'manifest.json').read_text())
BASE = 'https://raw.githubusercontent.com/cosmosapjw-quantum/htt_base/57ecfe2176bf8be28327edf500a4ca5136c6b15b/docs/project_catalog/database/'
LOG = ROOT / 'intake.jsonl'
LOCK = threading.Lock()
START = time.monotonic()

def emit(**data):
    data.update(elapsed_s=round(time.monotonic()-START,3),free_bytes=shutil.disk_usage(ROOT).free)
    line=json.dumps(data,ensure_ascii=False)
    with LOCK:
        with LOG.open('a') as f: f.write(line+'\n')
        print(line,flush=True)

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def acquire(part):
    name=part['name']
    if Path(name).name!=name: raise ValueError('invalid manifest path')
    out=PACKAGE/name
    if out.exists() and out.stat().st_size==part['bytes'] and digest(out)==part['sha256']:
        emit(stage='part_reused',part=name,bytes=part['bytes']); return
    for attempt in range(1,4):
        temp=PACKAGE/(name+'.download')
        try:
            req=urllib.request.Request(BASE+name+'?catalog_full=57ecfe21',headers={'Accept-Encoding':'identity'})
            h=hashlib.sha256(); total=0
            with urllib.request.urlopen(req,timeout=60) as response, temp.open('wb') as f:
                if response.status!=200: raise RuntimeError('unexpected HTTP '+str(response.status))
                for block in iter(lambda:response.read(1024*1024),b''):
                    total+=len(block)
                    if total>part['bytes']: raise RuntimeError('oversized response')
                    if shutil.disk_usage(ROOT).free<8*2**30: raise RuntimeError('8 GiB free-space floor')
                    f.write(block); h.update(block)
            if total!=part['bytes'] or h.hexdigest()!=part['sha256']: raise RuntimeError('size/hash mismatch')
            os.replace(temp,out)
            emit(stage='part_verified',part=name,bytes=total,sha256=h.hexdigest(),attempt=attempt)
            return
        except Exception as e:
            emit(stage='part_error',part=name,attempt=attempt,error=repr(e))
            if temp.exists(): temp.unlink()
            if attempt==3: raise

def main():
    expected=sum(p['bytes'] for p in MANIFEST['parts'])
    required=2*expected+MANIFEST['database_bytes']+8*2**30
    emit(stage='preflight',commit='57ecfe2176bf8be28327edf500a4ca5136c6b15b',compressed_bytes=expected,database_bytes=MANIFEST['database_bytes'],workers=4,required_free_bytes=required)
    if shutil.disk_usage(ROOT).free<required: raise RuntimeError('insufficient conservative space')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(acquire,MANIFEST['parts']))
    emit(stage='all_parts_verified',count=len(MANIFEST['parts']))
    spec=importlib.util.spec_from_file_location('original_package',ROOT/'support/original_package.py')
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    emit(stage='restore_started',implementation_sha256=digest(ROOT/'support/original_package.py'))
    output=ROOT/'catalog.sqlite'
    if output.exists(): raise RuntimeError('refuse to overwrite restored database')
    mod.restore(PACKAGE,output)
    emit(stage='restore_verified',bytes=output.stat().st_size,sha256=MANIFEST['database_sha256'])

if __name__=='__main__':
    try: main()
    except Exception as e:
        emit(stage='failed',error=repr(e)); raise
