"""F2 actual .2->.6 synthetic build consumption regression, metadata parity."""
import copy,hashlib,json,pathlib,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P));from test_repair import a,f,context_for,render
out=P/'current_synthetic_build_02';out.mkdir(exist_ok=False);c=context_for(out);render(c,out);evidence={'fixture_only':True,'no_actual_scientific_qualification':True}
def write(name,text):(P/name).write_text(text)
def build(name):
 argv=['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'];p=subprocess.run(argv,cwd=out,capture_output=True,text=True);write(name,p.stdout+p.stderr);assert p.returncode==0,(name,p.returncode);return argv
before_ready=a.check_rendered_products(c,out,built=False);assert before_ready['pdf_verification']=='UNVERIFIED_PREBUILD';build('current_02_build.log');assert a.check_rendered_products(c,out,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD'
old_pdf=a.sha(out/'main.pdf');old_text=subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],check=True,capture_output=True).stdout;(P/'synthetic_02_before.layout.txt').write_bytes(old_text)
result=copy.deepcopy(c['payload']['source_result']);result['observed']['features']['J234']=.6;result['observed']['T_abs_J234']=.6;result['rank']=a.rank_summary(.6,[r['T_abs_J234'] for r in result['mc_rows']]);c['payload']=a.extract_cached_result(result,result['observed']);render(c,out)
assert a.sha(out/'main.pdf')==old_pdf
assert a.check_rendered_products(c,out,built=False)['pdf_verification']=='UNVERIFIED_PREBUILD'
try:a.check_rendered_products(c,out)
except ValueError as e:
 evidence['stale_PDF_after_02_to_06_rejected']=str(e);write('stale_current_PDF_rejection.log',str(e)+'\n')
else:raise AssertionError('stale PDF accepted')
# Independently demonstrate current numerical text check rejects the old numbers,
# even without relying solely on consumed-input identity.
current_verify=a.verify_current_pdf
source=a.__dict__
assert b'observed value is 0.2' in b' '.join(old_text.split())
build('current_06_forced_build.log');checked=a.check_rendered_products(c,out,built=True);assert checked['pdf_verification']=='VERIFIED_CURRENT_BUILD'
new_text=subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],check=True,capture_output=True).stdout;(P/'synthetic_06_after.layout.txt').write_bytes(new_text);assert b'observed value is 0.6, with 0 inclusive exceedances' in b' '.join(new_text.split());assert b'plus-one rank is 0.00990099009901' in b' '.join(new_text.split())
# Byte-identical source regeneration must not require an unnecessary rebuild.
render(c,out);assert a.check_rendered_products(c,out,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';evidence['no_op_generation_preserves_current_verification']=True
# The native dependency record catches changes to TeX, tables, figures and bib,
# including a changed response image with unchanged displayed T/k/p.
for rel in ['main.tex','generated/methods_table.tex','figures/mask_response_columns.pdf','references.bib']:
 p=out/rel;original=p.read_bytes();p.write_bytes(original+b'\n% synthetic dependency change\n')
 try:a.verify_current_pdf(c,out)
 except ValueError as e:evidence['dependency_rejected_'+rel]=str(e)
 else:raise AssertionError('changed input accepted '+rel)
 p.write_bytes(original)
assert a.check_rendered_products(c,out,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD'
prior=a.sha(out/'main.pdf');build('current_06_metadata_rebuild.log');assert a.check_rendered_products(c,out,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD'
last_text=subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],check=True,capture_output=True).stdout;assert last_text==new_text
# Swap a semantically obsolete PDF into an otherwise current dependency tree.
# The existing log/FDB cannot make its obsolete numbers current.
p=out/'main.pdf';current=p.read_bytes();p.write_bytes((P/'old_failure_reproduction/rendered_probe/main.pdf').read_bytes())
try:a.verify_current_pdf(c,out)
except ValueError as e:evidence['obsolete_numeric_PDF_rejected_even_with_current_dependency_record']=str(e)
else:raise AssertionError('obsolete numeric PDF accepted')
p.write_bytes(current)
evidence.update({'prebuild_status':before_ready,'postbuild_status':checked,'old_Tobs':.2,'current_Tobs':.6,'current_k':0,'current_p_rank':1/101,'actual_forced_current_build':'PASS','metadata_only_rebuild_text_parity':True,'before_metadata_pdf_sha256':prior,'after_metadata_pdf_sha256':a.sha(out/'main.pdf'),'metadata_PDF_bytes_changed':prior!=a.sha(out/'main.pdf'),'current_text_sha256':hashlib.sha256(new_text).hexdigest(),'actual_MC_source_consumed':False})
a.dump(P/'REBUILD_REGRESSION_RESULT.json',evidence);print(json.dumps(evidence,indent=2))
