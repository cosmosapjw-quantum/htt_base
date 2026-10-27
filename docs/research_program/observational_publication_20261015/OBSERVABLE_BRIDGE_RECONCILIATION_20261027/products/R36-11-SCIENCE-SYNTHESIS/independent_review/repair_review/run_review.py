import datetime, hashlib, json, os, pathlib, re, runpy, shutil, subprocess, sys, traceback

ROOT=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_synthesis_repair_fresh_review')
CAND=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS/repair_01'
PY=ROOT/'.venv/bin/python'
PLAN=json.loads((CAND/'APPLICATION_PLAN.json').read_text())
ORIGINAL=pathlib.Path(PLAN['destination'])
FIX=OUT/'fixture/P4'
records=[]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
def tree(p): return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def write(name,obj): (OUT/name).write_text(json.dumps(obj,indent=2)+'\n')
def run(name,cmd,expected=0,cwd=ROOT):
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    r=subprocess.run(list(map(str,cmd)),cwd=cwd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
    so=OUT/(name+'.stdout'); se=OUT/(name+'.stderr');so.write_text(r.stdout);se.write_text(r.stderr)
    records.append({'name':name,'command':list(map(str,cmd)),'cwd':str(cwd),'start_utc':started,'exit':r.returncode,'expected_exit':expected,'stdout':str(so),'stderr':str(se),'stdout_sha256':sha(so),'stderr_sha256':sha(se)})
    write('RAW_RECEIPT.json',{'commands':records,'candidate_identity':'sha256:'+sha(CAND/'ARTIFACT_MANIFEST.json'),'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','science_producer_runs':0,'production_writes':0,'fixture':str(FIX),'phase':'RUNNING'})
    assert r.returncode==expected,(name,r.returncode,r.stderr[-2000:])
    return r

try:
    assert sha(CAND/'ARTIFACT_MANIFEST.json')=='83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519'
    manifest=json.loads((CAND/'ARTIFACT_MANIFEST.json').read_text())
    bindings=[]
    for f in manifest['artifacts']:
        p=CAND/f['path'];actual=sha(p)
        assert actual==f['sha256'],('manifest hash',str(p))
        assert p.stat().st_size==f['bytes'],('manifest size',str(p))
        bindings.append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size})
    contract=json.loads((CAND/'candidate/R32-06-P4-DESIGN/report/r36_11/SOURCE_CONTRACT.json').read_text())
    sources=[]
    for key,b in contract['source_bindings'].items():
        p=pathlib.Path(b['path']);assert sha(p)==b['sha256'],('frozen source',key)
        sources.append({'key':key,**b})
    write('IDENTITY_CHECKS.json',{'manifest_sha256':sha(CAND/'ARTIFACT_MANIFEST.json'),'manifest_artifacts':bindings,'frozen_sources':sources})
    before=tree(ORIGINAL);write('PRODUCTION_BEFORE.json',before)
    assert not FIX.exists(),'preserve previous fixture'
    FIX.parent.mkdir(parents=True)
    shutil.copytree(ORIGINAL,FIX)
    for rel,b in PLAN['files'].items(): assert sha(FIX/rel)==b['preimage_sha256'],rel
    helper="import pathlib,runpy,sys,json; m=runpy.run_path(sys.argv[1]); print(json.dumps({'changed':m['apply'](pathlib.Path(sys.argv[2]))},indent=2))"
    apply=[PY,'-B','-c',helper,CAND/'apply_candidate.py',FIX]
    r=run('01_apply',apply);assert len(json.loads(r.stdout)['changed'])==24
    run('02_assemble',[PY,'-B',FIX/'report/r36_11/assemble.py'])
    run('03_check_before_build',[PY,'-B',FIX/'report/r36_11/check.py'])
    run('04_build',['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','-cd',FIX/'report/main.tex'])
    run('05_check_after_build',[PY,'-B',FIX/'report/r36_11/check.py'])
    r=run('06_apply_idempotent',apply);assert json.loads(r.stdout)['changed']==[]
    r=run('07_pdfinfo',['pdfinfo',FIX/'report/main.pdf']);assert re.search(r'Pages:\s+24',r.stdout)
    run('08_pdftext',['pdftotext','-layout',FIX/'report/main.pdf',OUT/'fixture_pdf.txt'])
    # Directly exercise the exact production applier's full preflight and atomic rejection.
    target_file=FIX/'science/MANUSCRIPT.md';saved=target_file.read_bytes();target_file.write_bytes(saved+b'\nREVIEW_WRONG_SOURCE\n')
    tampered=tree(FIX)
    r=run('09_wrong_apply_preimage',apply,1);assert 'destination drift' in r.stderr;assert tree(FIX)==tampered
    target_file.write_bytes(saved)
    # All six sealed replaced preimages and all six applied identities must be checked after application.
    expected=json.loads((FIX/'report/r36_11/EXPECTED_APPLIED.json').read_text())
    preimage_probes=[]
    for i,key in enumerate(expected):
        source=pathlib.Path(contract['source_bindings'][key]['path']);rel=source.relative_to(ORIGINAL)
        baseline=FIX/'report/r36_11/baseline'/rel;old=baseline.read_bytes();baseline.write_bytes(old+b'\nREVIEW_PREIMAGE_DRIFT\n')
        r=run('10_baseline_'+str(i),[PY,'-B',FIX/'report/r36_11/check.py'],1);assert 'baseline drift' in r.stderr
        r=run('11_assemble_baseline_'+str(i),[PY,'-B',FIX/'report/r36_11/assemble.py'],1);assert 'source identity' in r.stderr
        baseline.write_bytes(old)
        live=FIX/rel;oldlive=live.read_bytes();live.write_bytes(oldlive+b'\nREVIEW_APPLIED_DRIFT\n')
        r=run('12_applied_'+str(i),[PY,'-B',FIX/'report/r36_11/check.py'],1);assert 'applied source drift' in r.stderr
        live.write_bytes(oldlive)
        preimage_probes.append({'source_key':key,'relative_path':str(rel),'baseline_guard':'PASS','assembler_baseline_guard':'PASS','applied_guard':'PASS'})
    wrong=OUT/'outside_target'
    r=run('13_wrong_cli_path',[PY,'-B',CAND/'apply_candidate.py','--apply-reviewed-candidate','--test-target',wrong],1)
    assert 'fixture target outside external repair directory' in r.stderr and not wrong.exists()
    for script in ['assemble.py','check.py']:
        r=run('14_wrong_target_'+script,[PY,'-B',FIX/'report/r36_11'/script,'--target',wrong],1);assert 'wrong target path' in r.stderr and not wrong.exists()
    run('15_final_check',[PY,'-B',FIX/'report/r36_11/check.py'])
    for rel,b in PLAN['files'].items():assert sha(FIX/rel)==b['final_sha256'],('postbuild overlay drift',rel)
    original_json={p.name:sha(p) for p in (ORIGINAL/'report').glob('*.json')}
    assert len(original_json)==10
    for name,digest in original_json.items():assert sha(FIX/'report'/name)==digest,('old JSON',name)
    for name in ['figure1_spectra.pdf','figure2_leverage_precision.pdf','figure3_error_bound.pdf']:
        assert sha(ORIGINAL/'report'/name)==sha(FIX/'report'/name)
    old=(ORIGINAL/'report/body.tex').read_text();new=(FIX/'report/body.tex').read_text()
    eq=lambda x:re.findall(r'\\\[.*?\\\]',x,re.S)
    assert len(eq(old))>=27 and eq(old)[:27]==eq(new)[:27]
    oldmd=(ORIGINAL/'report/manuscript_generated.md').read_text();newmd=(FIX/'report/manuscript_generated.md').read_text()
    assert oldmd.split('## Generated numerical appendix tables')[1]==newmd.split('## Generated numerical appendix tables')[1]
    after=tree(ORIGINAL);write('PRODUCTION_AFTER.json',after);assert after==before
    write('WORKFLOW_RESULT.json',{'status':'PASS','manifest_files_verified':len(bindings),'source_bindings_verified':len(sources),'overlay_files':len(PLAN['files']),'sealed_preimage_probes':preimage_probes,'original_json_unchanged':original_json,'old_equations_1_27_unchanged':True,'old_generated_appendix_unchanged':True,'old_three_figures_unchanged':True,'production_tree_unchanged':True,'pdf_pages':24,'idempotent_after_build':True,'scope':'disposable manuscript fixture; unchanged apply(target), CLI path guard separately checked'})
    receipt=json.loads((OUT/'RAW_RECEIPT.json').read_text());receipt['phase']='COMPLETE';receipt['status']='PASS';receipt['workflow_result_sha256']=sha(OUT/'WORKFLOW_RESULT.json');write('RAW_RECEIPT.json',receipt)
    print(json.dumps({'status':'PASS','commands':len(records),'fixture':str(FIX)},indent=2))
except BaseException:
    (OUT/'FIRST_FAILURE.txt').write_text(traceback.format_exc())
    raise
