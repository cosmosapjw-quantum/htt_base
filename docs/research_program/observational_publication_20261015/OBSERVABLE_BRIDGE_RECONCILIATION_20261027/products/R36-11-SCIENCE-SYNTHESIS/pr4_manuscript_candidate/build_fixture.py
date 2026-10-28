"""One bounded synthetic document-tool fixture, never a formal source binding."""
import hashlib,json,pathlib,shutil,subprocess,sys
A=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(A));import assemble as a;from test_assemble import synthetic_result,synthetic_response
F=A/'isolated_synthetic_unit_fixture';F.mkdir(exist_ok=True);(F/'.SYNTHETIC_UNIT_FIXTURE').write_text('No empirical rows, actual source binding or formal science return.\n');prose=(A/'MANUSCRIPT_ADDITIONS.md').read_text();j=synthetic_result();r=synthetic_response();data=a.render_unit_fixture(j,r,prose,F)
(F/'references.bib').write_text(''.join('@misc{'+key+',title={Synthetic unit citation marker, not a verified bibliography}}\n' for key in ['NPIPE2020','ESA_SIMULATION','PLA_PRODUCTS','PR4Resolution']))
first={str(p.relative_to(F)):a.sha(p) for p in F.rglob('*') if p.is_file()};a.render_unit_fixture(j,r,prose,F);second={str(p.relative_to(F)):a.sha(p) for p in F.rglob('*') if p.is_file()};assert first==second,'synthetic cached render idempotence'
args=['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'];run=subprocess.run(args,cwd=F,capture_output=True,text=True);(A/'raw/synthetic_build_first.log').write_text(run.stdout+run.stderr);assert run.returncode==0
log=(F/'main.log').read_text();import re
assert not re.search(r'undefined references|Citation .* undefined|Reference .* undefined|LaTeX Error|Overfull \\hbox',log),'synthetic final diagnostics'
def text():return subprocess.run(['pdftotext','-layout',str(F/'main.pdf'),'-'],capture_output=True,check=True).stdout
before=text();pdf1=a.sha(F/'main.pdf');assert b'SYNTHETIC UNIT FIXTURE' in before and b'??' not in before
run=subprocess.run(['latexmk','-g',*args[1:]],cwd=F,capture_output=True,text=True);(A/'raw/synthetic_metadata_rebuild.log').write_text(run.stdout+run.stderr);assert run.returncode==0;assert before==text(),'metadata rebuild PDF text parity'
(F/'fixture.layout.txt').write_bytes(before)
a.dump(A/'SYNTHETIC_FIXTURE_RESULT.json',{'scope':'SYNTHETIC UNIT FIXTURE ONLY, not a PR4 source qualification or candidate result','complete100_pure_function_extraction':'PASS','render_data_and_figure_idempotence':first==second,'isolated_TeX_build':'PASS','metadata_rebuild_text_parity':'PASS','before_pdf_sha256':pdf1,'after_pdf_sha256':a.sha(F/'main.pdf'),'text_sha256':hashlib.sha256(before).hexdigest(),'no_real_data_rows_consumed':True,'formal_review_mocked':False,'actual_candidate_PDF_created':False})
print('SYNTHETIC_UNIT_FIXTURE_COMPLETE')
