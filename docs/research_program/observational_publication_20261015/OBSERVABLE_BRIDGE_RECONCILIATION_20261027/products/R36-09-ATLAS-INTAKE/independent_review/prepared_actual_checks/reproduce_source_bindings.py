#!/usr/bin/env python3
"""Source binding and source-semantics supplement. Small pinned text fetches only."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,urllib.request,traceback
OUT=Path(__file__).resolve().parent
RESP=Path('/mnt/extdrive/workdir/htt_open_data/r36_atlas_source_preparation/responses')
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(b):return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()
trees={n:json.loads((RESP/n).read_bytes()) for n in ['anilos_pinned_tree.json','vicente_aniclass_tree.json','bianchi_tree.json']}
r={'utc':datetime.now(timezone.utc).isoformat(),'source_bindings':[],'primary_documents':[],'failures':[],'new_network_bytes':0}
try:
 for name in ['aniclass_README.md','aniclass_bianchi.ini','aniclass_example.ipynb','anilos_source.py','anilos_example.ipynb','anilos_figures_paper.ipynb']:
  p=RESP/name;b=p.read_bytes();matches=[{'tree':tree,'path':x['path']} for tree,d in trees.items() for x in d['tree'] if x['sha']==blob(b)]
  r['source_bindings'].append({'local_path':str(p),'sha256':sha(b),'git_blob':blob(b),'matches':matches})
  assert len(matches)==1,(name,matches)
 p=Path('/mnt/extdrive/workdir/htt_open_data/external_transfer/bianchi_v1_1_1c90b98/README.txt');b=p.read_bytes()
 match=[x for x in trees['bianchi_tree.json']['tree'] if x['path']=='README.txt'][0]
 assert blob(b)==match['sha']
 r['primary_documents'].append({'path':str(p),'sha256':sha(b),'git_blob':blob(b),'text':b.decode()})
 for rel,outname in [('explanatory.ini','primary_explanatory.ini'),('external/external_Pk/README.md','primary_external_Pk_README.md')]:
  url='https://raw.githubusercontent.com/jgvicente/aniclass/be1e43fcb1d7549710ba3ca2baa74bb0216bd228/'+rel
  p=OUT/outname
  if p.exists():b=p.read_bytes();reused=True
  else:
   with urllib.request.urlopen(url,timeout=30) as response:b=response.read(200000)
   p.write_bytes(b);r['new_network_bytes']+=len(b);reused=False
  match=[x for x in trees['vicente_aniclass_tree.json']['tree'] if x['path']==rel][0]
  assert blob(b)==match['sha'] and len(b)==match['size']
  lines=b.decode().splitlines();needles=['dNdz_selection','dNdz_evolution','ncdm_psd_filenames','tuple','floating point numbers']
  excerpts=[{'line':i+1,'text':'\n'.join(lines[max(0,i-5):min(len(lines),i+4)])} for i,s in enumerate(lines) if any(n in s for n in needles)]
  r['primary_documents'].append({'url':url,'local_path':str(p),'sha256':sha(b),'git_blob':blob(b),'source_identity_verified':True,'cache_reused':reused,'bytes':len(b),'excerpts':excerpts})
 nb=json.loads((RESP/'anilos_figures_paper.ipynb').read_bytes())
 r['timing_source_cells']=[{'cell':i,'source':''.join(nb['cells'][i]['source'])} for i in [43,44,45,47,48,49,50]]
except Exception as e:r['failures'].append({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()})
p=OUT/'SOURCE_BINDINGS_RAW.json'
if p.exists():p=OUT/('SOURCE_BINDINGS_RAW_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
p.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':sha(p.read_bytes()),'bindings':len(r['source_bindings']),'documents':len(r['primary_documents']),'new_network_bytes':r['new_network_bytes'],'failures':r['failures']},indent=2))
