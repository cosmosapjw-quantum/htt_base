import copy,json,pathlib,shutil,subprocess,sys
P=pathlib.Path(__file__).parent;sys.path.insert(0,str(P/'old_code'));import assemble as a;import test_assemble as f
out=P/'old_probe';out.mkdir();(out/'.SYNTHETIC_UNIT_FIXTURE').write_text('SYNTHETIC UNIT FIXTURE ONLY\n');prose=(P/'old_code/MANUSCRIPT_ADDITIONS.md').read_text();j=f.synthetic_result();r=f.synthetic_response();j['observed']['features']['J234']=.6;j['observed']['T_abs_J234']=.6;j['rank']=a.rank_summary(.6,[x['T_abs_J234'] for x in j['mc_rows']]);c={'payload':a.extract_cached_result(j,j['observed']),'response':r}
def render():
 a.render_unit_fixture(j,r,prose,out);shutil.copyfile(P/'old_code/references.bib',out/'references.bib')
def build(name):
 p=subprocess.run(['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=out,capture_output=True,text=True);(P/name).write_text(p.stdout+p.stderr);assert p.returncode==0
render();build('old_figure_build.log');assert a.check_rendered_products(c,out,fixture_only=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';old=(out/'main.pdf').read_bytes();(P/'saved_old_response.pdf').write_bytes(old)
for field in a.FIELDS:
 for key,v in r['columns'][1][field].items():r['columns'][1][field][key]=[-v[0],-v[1]]
render();build('changed_figure_build.log');current=(out/'main.pdf').read_bytes();(P/'saved_current_response.pdf').write_bytes(current);assert a.check_rendered_products(c,out,fixture_only=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';(out/'main.pdf').write_bytes(old)
status=a.check_rendered_products(c,out,fixture_only=True);result={'fixture_only':True,'same_T_k_p':True,'signed_second_response_column_negated':True,'old_PDF_restored_with_current_dependencies':True,'old_PDF_wrongly_verified':status,'old_and_current_PDF_differ':old!=current};a.dump(P/'FIRST_COUNTEREXAMPLE.json',result);print(json.dumps(result,indent=2));assert status['pdf_verification']=='VERIFIED_CURRENT_BUILD'
