"""Exact same-scalar/different-response PDF regression; synthetic unit data only."""
import ast,copy,hashlib,json,pathlib,shutil,subprocess,sys
P=pathlib.Path(__file__).parent;A=P.parents[1];sys.path.insert(0,str(A));import assemble as a;import test_assemble as f
from PIL import Image
import numpy as np
out=P/'fixed_probe';out.mkdir(exist_ok=False);(out/'.SYNTHETIC_UNIT_FIXTURE').write_text('SYNTHETIC UNIT FIXTURE ONLY; no actual source or candidate\n');prose=(A/'MANUSCRIPT_ADDITIONS.md').read_text();j=f.synthetic_result();response=f.synthetic_response();j['observed']['features']['J234']=.6;j['observed']['T_abs_J234']=.6;j['rank']=a.rank_summary(.6,[x['T_abs_J234'] for x in j['mc_rows']]);c={'payload':a.extract_cached_result(j,j['observed']),'response':response}
def render():
 a.render_unit_fixture(j,response,prose,out);shutil.copyfile(A/'prepared/pr4_morphology_supplement/references.bib',out/'references.bib')
def text(p):return subprocess.run(['pdftotext','-layout',str(p),'-'],check=True,capture_output=True).stdout
def pixels(p,label):
 target=P/label;subprocess.run(['pdftoppm','-f','4','-singlefile','-r','60','-png',str(p),str(target)],check=True,capture_output=True);return np.array(Image.open(target.with_suffix('.png')))
def directbuild(name):
 run=subprocess.run(['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=out,capture_output=True,text=True);(P/name).write_text(run.stdout+run.stderr);assert run.returncode==0
render();ready=a.check_rendered_products(c,out,fixture_only=True,built=False);assert ready['pdf_verification']=='UNVERIFIED_PREBUILD';directbuild('FIXED_INITIAL_BUILD.log');assert a.check_rendered_products(c,out,fixture_only=True,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';old=(out/'main.pdf').read_bytes();(P/'fixed_saved_old.pdf').write_bytes(old);oldtext=text(out/'main.pdf');oldpixels=pixels(out/'main.pdf','fixed_old_response')
for field in a.FIELDS:
 for key,v in response['columns'][1][field].items():response['columns'][1][field][key]=[-v[0],-v[1]]
render();directbuild('FIXED_CHANGED_RESPONSE_BUILD.log');assert a.check_rendered_products(c,out,fixture_only=True,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';current=(out/'main.pdf').read_bytes();(P/'fixed_saved_current.pdf').write_bytes(current);newtext=text(out/'main.pdf');newpixels=pixels(out/'main.pdf','fixed_current_response');changed=int(np.count_nonzero(np.any(oldpixels!=newpixels,axis=-1)));assert oldtext==newtext and changed>0
# Exact counterexample: current fdb/fls/log and all input files, restore old PDF only.
(out/'main.pdf').write_bytes(old);restored=a.sha(out/'main.pdf');status=a.check_rendered_products(c,out,fixture_only=True,built=True);assert status['pdf_verification']=='VERIFIED_CURRENT_BUILD';afterpixels=pixels(out/'main.pdf','fixed_after_restore_verify');assert np.array_equal(afterpixels,newpixels) and not np.array_equal(afterpixels,oldpixels);assert text(out/'main.pdf')==newtext
# No-op generation and metadata-only variation remain permitted. Pixel/text parity
# assesses content; a changed metadata hash is not treated as scientific failure.
render();assert a.check_rendered_products(c,out,fixture_only=True,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';noop_pixels=pixels(out/'main.pdf','fixed_after_noop');assert np.array_equal(noop_pixels,newpixels)
priorhash=a.sha(out/'main.pdf');prior_text=text(out/'main.pdf');directbuild('FIXED_METADATA_REBUILD.log');assert a.check_rendered_products(c,out,fixture_only=True,built=True)['pdf_verification']=='VERIFIED_CURRENT_BUILD';assert text(out/'main.pdf')==prior_text;assert np.array_equal(pixels(out/'main.pdf','fixed_after_metadata'),newpixels)
# The supplied F1 lossless check must still reject before any verifier build.
supp=out/'NUMERICAL_SUPPLEMENT.json';supold=supp.read_bytes();mut=a.strict_json(supp);mut['complete_cached_result']['source_result']['observed'][a.FIELDS[1]]={};a.dump(supp,mut)
try:a.check_rendered_products(c,out,fixture_only=True,built=True)
except ValueError as e:assert 'supplement parity' in str(e)
else:raise AssertionError('F1 regressed')
supp.write_bytes(supold)
oldsource=P/'preimages/author/assemble.py';get=lambda p:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)};before,after=get(oldsource),get(A/'assemble.py');changes=[k for k in before if before[k]!=after.get(k)];assert changes==['verify_current_pdf'];assert set(before)==set(after)
result={'fixture_only':True,'actual_source_consumed':False,'old_counterexample_reproduced_before_edit':a.strict_json(P/'FIRST_COUNTEREXAMPLE.json'),'same_T_k_p':True,'same_PDF_text_despite_changed_figure':oldtext==newtext,'response_pixels_changed':changed,'verification_after_restoring_old_PDF':status,'forced_verification_restored_current_figure':np.array_equal(afterpixels,newpixels),'old_response_not_retained':not np.array_equal(afterpixels,oldpixels),'restored_old_pdf_sha256':restored,'verified_pdf_sha256':a.sha(out/'main.pdf'),'no_op_generation_pixel_parity':True,'metadata_rebuild_text_and_pixel_parity':True,'metadata_byte_identity_required':False,'F1_still_rejects_observed_B_loss':True,'only_changed_function':changes,'closed_F1_and_scientific_gate_AST_unchanged':True}
a.dump(P/'FIGURE_FIX_RESULT.json',result);print(json.dumps(result,indent=2))
