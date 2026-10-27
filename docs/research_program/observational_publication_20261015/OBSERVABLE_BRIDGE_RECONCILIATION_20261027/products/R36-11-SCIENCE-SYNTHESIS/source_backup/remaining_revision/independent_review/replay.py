from pathlib import Path
import json,hashlib,shutil,subprocess,os
ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r36_remaining_manuscript_fresh_review');repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');pkg=repo/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS/remaining_manuscript_candidate';candidate=pkg/'candidate';fixture=ROOT/'fixture';c=json.loads((pkg/'EDITOR_CONTRACT.json').read_text());manifest=candidate/'OVERLAY_MANIFEST.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(manifest)=='d8455ea2d8d33ee17ce07deca7dec58aa8773a0a39251c84609211f3a0575abb'
assert sha(pkg/'EDITOR_CONTRACT.json')=='a1f4f3e6508c2b1e69af9deb619977de4f45bb48ca07ea15822f3087a07db783'
bindings={b['repo_relative_path']:b for b in c['source_bindings'].values()};bindings.update(c['production_preimages_and_retained_artifacts']);pre={}
for rel,b in bindings.items():
 src=repo/rel;assert sha(src)==b['sha256'],rel;dst=fixture/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);pre[rel]=sha(src)
for plan in c['publication_plan'][:2]:
 for folder in ['figures','generated'] if plan['key']=='H03' else ['report/figures']:
  for src in (repo/plan['root']/folder).glob('*'):
   if src.is_file():
    dst=fixture/plan['root']/folder/src.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
(ROOT/'PREIMAGE_SEALS.json').write_text(json.dumps(pre,indent=2)+'\n')
env=dict(os.environ,OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(ROOT/'tmp'));records=[]
def run(label,cmd):
 r=subprocess.run(list(map(str,cmd)),cwd=repo,env=env,capture_output=True,text=True);(ROOT/'raw'/f'{label}.stdout').write_text(r.stdout);(ROOT/'raw'/f'{label}.stderr').write_text(r.stderr);records.append({'stage':label,'argv':list(map(str,cmd)),'returncode':r.returncode});(ROOT/'REPLAY.json').write_text(json.dumps(records,indent=2)+'\n');print(label,r.returncode,flush=True);assert r.returncode==0,label;return r.stdout
py=repo/'.venv/bin/python';entry=pkg/'publication_overlay.py'
run('01_apply',[py,entry,'apply','--manifest',manifest,'--repo',fixture,'--reviewed-manifest-sha256',sha(manifest)])
s=fixture/c['publication_plan'][0]['root']/'r36_bridge';installed=s/'publication_overlay.py';common=['--contract',s/'EDITOR_CONTRACT.json','--repo',fixture,'--output-root',fixture]
run('02_installed_assemble',[py,installed,'assemble',*common]);run('03_installed_check',[py,installed,'check',*common,'--falsifiers'])
for i,plan in enumerate(c['publication_plan']):run(f'0{i+4}_build_{plan["key"]}',['latexmk','-cd','-pdf','-interaction=nonstopmode','-halt-on-error','-file-line-error',fixture/plan['root']/plan['main']])
run('07_built_check',[py,installed,'check',*common,'--built-pdfs','--falsifiers'])
parity={}
for plan in c['publication_plan']:
 rel=plan['root']+'/'+plan['output'];a=subprocess.check_output(['pdftotext','-layout',str(candidate/rel),'-']);b=subprocess.check_output(['pdftotext','-layout',str(fixture/rel),'-']);assert a==b;parity[plan['key']]={'text_sha256':hashlib.sha256(a).hexdigest(),'identical_text':True};(ROOT/'raw'/(plan['key']+'.txt')).write_bytes(b)
(ROOT/'PDF_PARITY.json').write_text(json.dumps(parity,indent=2)+'\n')
r=json.loads(run('08_second_apply',[py,entry,'apply','--manifest',manifest,'--repo',fixture,'--reviewed-manifest-sha256',sha(manifest)]));assert r['changed_targets']==0
for rel,h in pre.items():assert sha(repo/rel)==h,rel
print('PASS entire independent 3-document replay',flush=True)
