from pathlib import Path
import urllib.request,urllib.error,json,hashlib,time,shutil,datetime,concurrent.futures
O=Path('/mnt/extdrive/workdir/htt_open_data/r36_atlas_source_preparation');(O/'responses').mkdir(exist_ok=True)
def fetch(item):
 key,url=item;t=time.monotonic();dest=O/'responses'/key;rec={'key':key,'url':url,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'authentication':'none','purpose':'public primary metadata/source inventory; no solver or model execution'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'HTT-source-metadata-intake','Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})
  try:r=urllib.request.urlopen(req,timeout=25)
  except urllib.error.HTTPError as e:r=e
  rec.update(status=r.status,final_url=r.geturl(),headers=dict(r.headers));h=hashlib.sha256();size=0
  with r, dest.open('xb') as f:
   while True:
    assert shutil.disk_usage(O).free>2*1024**3,'verified 2GiB reserve reached';b=r.read(1024*1024)
    if not b:break
    f.write(b);h.update(b);size+=len(b)
  rec.update(path=str(dest),bytes=size,sha256=h.hexdigest())
 except Exception as e:rec.update(error=type(e).__name__+': '+str(e))
 rec['elapsed_seconds']=time.monotonic()-t;(O/'responses'/(key+'.receipt.json')).write_text(json.dumps(rec,indent=2)+'\n');return rec
if __name__=='__main__':
 items=[('anilos_repo.json','https://api.github.com/repos/jgvicente/AniLoS'),('anilos_pinned_tree.json','https://api.github.com/repos/jgvicente/AniLoS/git/trees/9b7a2611882dcca80a1491bcad2b8f05635faca7?recursive=1'),('anilos_releases.json','https://api.github.com/repos/jgvicente/AniLoS/releases?per_page=100'),('anilos_tags.json','https://api.github.com/repos/jgvicente/AniLoS/tags?per_page=100'),('anilos_branches.json','https://api.github.com/repos/jgvicente/AniLoS/branches?per_page=100'),('aniclass_repo.json','https://api.github.com/repos/pitrou/AniCLASS'),('bianchi_repo.json','https://api.github.com/repos/astro-informatics/bianchi'),('zenodo48653.json','https://zenodo.org/api/records/48653'),('zenodo48654.json','https://zenodo.org/api/records/48654')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for r in pool.map(fetch,items):print(json.dumps({k:r[k] for k in ['key','status','bytes','error'] if k in r}),flush=True)
