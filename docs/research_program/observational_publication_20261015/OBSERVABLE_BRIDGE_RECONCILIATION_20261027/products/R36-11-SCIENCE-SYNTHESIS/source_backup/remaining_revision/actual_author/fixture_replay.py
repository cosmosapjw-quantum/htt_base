import pathlib,json,hashlib,shutil,subprocess,sys
HERE=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');candidate=HERE/'candidate';fixture=HERE/(sys.argv[1] if len(sys.argv)>1 else 'small_manuscript_fixture');fixture.mkdir(exist_ok=True)
c=json.loads((HERE/'EDITOR_CONTRACT.json').resolve().read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bindings={b['repo_relative_path']:b for b in c['source_bindings'].values()};bindings.update(c['production_preimages_and_retained_artifacts'])
for rel,b in bindings.items():
 dst=fixture/rel;src=repo/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():
  if b.get('mutable_in_overlay'):shutil.copyfile(src,dst)
  else:dst.symlink_to(src)
# Only directly retained build support. It stays immutable and symlinked to the original files.
for plan in c['publication_plan'][:2]:
 for folder in ['figures','generated'] if plan['key']=='H03' else ['report/figures']:
  for src in (repo/plan['root']/folder).glob('*'):
   if src.is_file():
    dst=fixture/plan['root']/folder/src.name;dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():dst.symlink_to(src)
records=[]
def run(label,cmd):
 result=subprocess.run(cmd,cwd=repo,capture_output=True,text=True);(HERE/'raw'/(fixture.name+'_'+label+'.stdout')).write_text(result.stdout);(HERE/'raw'/(fixture.name+'_'+label+'.stderr')).write_text(result.stderr)
 records.append({'stage':label,'argv':list(map(str,cmd)),'cwd':str(repo),'exit_code':result.returncode});(HERE/'FIXTURE_REPLAY.json').write_text(json.dumps(records,indent=2)+'\n')
 if result.returncode:raise RuntimeError(label+' failed')
 return result.stdout
python=str(repo/'.venv/bin/python');entry=HERE/'publication_overlay.py';manifest=candidate/'OVERLAY_MANIFEST.json';mh=sha(manifest)
run('apply_first',[python,str(entry),'apply','--manifest',str(manifest),'--repo',str(fixture),'--reviewed-manifest-sha256',mh])
s=fixture/c['publication_plan'][0]['root']/'r36_bridge';installed=s/'publication_overlay.py';contract=s/'EDITOR_CONTRACT.json'
common=['--contract',str(contract),'--repo',str(fixture),'--output-root',str(fixture)]
run('installed_assemble',[python,str(installed),'assemble']+common)
run('installed_check',[python,str(installed),'check']+common+['--falsifiers'])
for plan in c['publication_plan']:
 run('build_'+plan['key'],['latexmk','-cd','-pdf','-interaction=nonstopmode','-halt-on-error','-file-line-error',str(fixture/plan['root']/plan['main'])])
run('installed_built_check',[python,str(installed),'check']+common+['--built-pdfs','--falsifiers'])
parity={}
for plan in c['publication_plan']:
 rel=plan['root']+'/'+plan['output']
 def text(p):return subprocess.run(['pdftotext','-layout',str(p),'-'],capture_output=True,check=True).stdout
 a,b=text(candidate/rel),text(fixture/rel);assert a==b,('PDF text parity',plan['key']);parity[plan['key']]={'text_sha256':hashlib.sha256(a).hexdigest(),'exact_text_equal':True,'candidate_pdf_sha256':sha(candidate/rel),'rebuilt_pdf_sha256':sha(fixture/rel),'pdf_byte_identity_is_packaging':True}
(HERE/'PDF_TEXT_PARITY.json').write_text(json.dumps(parity,indent=2)+'\n')
second=json.loads(run('apply_second',[python,str(entry),'apply','--manifest',str(manifest),'--repo',str(fixture),'--reviewed-manifest-sha256',mh]));assert second['changed_targets']==0
print('Small fixture applied -> installed assembler -> current check ->3 builds ->current check ->PDF text parity ->second apply zero changes PASS')
