import hashlib,json,pathlib,shutil,subprocess,sys
A=pathlib.Path(__file__).resolve().parent;R=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');C=A/'candidate';F=A/'small_p6_fixture_02';H=A/'publication_overlay.py';contract=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_manuscript_framing/EDITOR_CONTRACT.json');c=json.loads(contract.read_text());p=pathlib.Path(c['publication_plan']['root']);s=p/c['publication_plan']['new_directory'];m=C/'OVERLAY_MANIFEST.json';digest=hashlib.sha256(m.read_bytes()).hexdigest()
def run(name,args):
 r=subprocess.run([str(x) for x in args],capture_output=True,text=True);(A/'raw'/name).write_text(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError(name+' '+str(r.returncode))
 return r.stdout
if F.exists():raise RuntimeError('retain old fixture, choose explicit repair rather than overwrite')
F.mkdir();(F/'.P6_DISPOSABLE_FIXTURE').write_text('Bounded document/source symlinks; synthetic review is fixture-only.\n')
rels=[b['path'] for b in c['source_bindings'].values() if not pathlib.Path(b['path']).is_absolute()]
old=json.loads((R/c['source_bindings']['p6_result']['path']).read_text())['manifest'];rels += [b['path'] for b in old['sources']]+[str(p/'repair_01'/b['path']) for b in old['outputs']]
prior=json.loads((R/c['source_bindings']['prior_three_document_manifest']['path']).read_text());rels += [b['path'] for b in prior['files']]
for folder in ['generated','figures']:
 rels += [str(x.relative_to(R)) for x in (R/p/'repair_01/report'/folder).rglob('*') if x.is_file()]
for rel in sorted(set(rels)):
 q=F/rel;q.parent.mkdir(parents=True,exist_ok=True);q.symlink_to(R/rel)
r=A/'FIXTURE_ONLY_REVIEW_RETURN.json';r.write_text(json.dumps({'candidate_identity':'sha256:'+digest,'outcome':'success','acceptance_met':True,'review_status':'PASS_SCOPED_CONDITIONAL','agent_id':'DISPOSABLE_TEST_REVIEW_NOT_INDEPENDENT_SCIENTIFIC_EVIDENCE','fixture_only':True,'fixture_root':str(F)},indent=2)+'\n')
apply=[sys.executable,'-B',H,'apply','--manifest',m,'--repo',F,'--reviewed-manifest-sha256',digest,'--review-return',r]
first=json.loads(run('fixture_apply_first.json',apply));current=F/s/'publication_overlay.py';cp=F/s/'EDITOR_CONTRACT.json'
args=['--contract',cp,'--repo',F,'--output-root',F]
run('fixture_installed_assemble.log',[sys.executable,'-B',current,'assemble',*args]);run('fixture_installed_check.log',[sys.executable,'-B',current,'check',*args,'--falsifiers'])
run('fixture_installed_build.log',['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','-outdir=r36_optical/build',F/p/'repair_01/report/main.tex']);shutil.copyfile(F/s/'build/main.pdf',F/p/c['publication_plan']['pdf'])
run('fixture_installed_check_built.log',[sys.executable,'-B',current,'check',*args,'--built-pdfs'])
def tx(x):return subprocess.run(['pdftotext','-layout',str(x),'-'],capture_output=True,check=True).stdout
assert tx(F/p/c['publication_plan']['pdf'])==tx(C/p/c['publication_plan']['pdf'])
second=json.loads(run('fixture_apply_second.json',apply));assert second['changed_targets']==0
# Actual forced rebuild: regenerated PDF metadata can differ, reviewed extracted text must remain identical.
run('fixture_metadata_rebuild.log',['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','-outdir=r36_optical/build',F/p/'repair_01/report/main.tex']);shutil.copyfile(F/s/'build/main.pdf',F/p/c['publication_plan']['pdf'])
run('fixture_metadata_check.log',[sys.executable,'-B',current,'check',*args,'--built-pdfs'])
last=json.loads(run('fixture_apply_metadata_second.json',apply));assert last['changed_targets']==0
# An exact old preimage must never excuse unreviewed new TeX bytes after installation.
tex=F/p/c['publication_plan']['main'];saved=tex.read_bytes();tex.write_bytes(saved+b'\n% unauthorized change\n')
bad=subprocess.run([str(x) for x in [sys.executable,'-B',current,'check',*args]],capture_output=True,text=True);(A/'raw/fixture_unexpected_installed_tex.log').write_text(bad.stdout+bad.stderr);assert bad.returncode!=0;tex.write_bytes(saved)
# A fixture-only review cannot be used against the owner's primary checkout.
bad=subprocess.run([str(x) for x in [sys.executable,'-B',H,'apply','--manifest',m,'--repo',R,'--reviewed-manifest-sha256',digest,'--review-return',r]],capture_output=True,text=True);(A/'raw/fixture_return_primary_rejection.log').write_text(bad.stdout+bad.stderr);assert bad.returncode!=0
result={'fixture_only':True,'fixture_review_is_not_independent_approval':True,'primary_checkout_applied':False,'manifest_sha256':digest,'first_apply':first,'installed_assemble_check_build_check':'PASS','PDF_text_parity':'PASS','second_apply':second,'metadata_rebuild_last_apply':last,'unexpected_installed_tex_rejected':True,'fixture_review_on_primary_rejected':True,'original_preimages_resolve_before_and_after':True}
(A/'FIXTURE_REPLAY.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
