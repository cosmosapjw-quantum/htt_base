"""SYNTHETIC_UNIT_FIXTURE: exact F2 response-figure residual closeout."""
import hashlib,json,pathlib,shutil,subprocess,sys
import numpy as np
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
import assemble as a
import test_assemble as f
out=ROOT/'rendered_probe';out.mkdir(exist_ok=True);(out/'.SYNTHETIC_UNIT_FIXTURE').write_text('Synthetic same-scalar/changed-response current-output probe only.\n')
result=f.synthetic_result();response=f.synthetic_response();result['observed']['features']['J234']=.6;result['observed']['T_abs_J234']=.6;result['rank']=a.rank_summary(.6,[r['T_abs_J234'] for r in result['mc_rows']]);prose=(ROOT/'code/MANUSCRIPT_ADDITIONS.md').read_text()
meta=ROOT/'synthetic_context';meta.mkdir(exist_ok=True)
for name in ['inventory','scope','receipt']:a.dump(meta/(name+'.json'),{'fixture_only':'SYNTHETIC_UNIT_FIXTURE','role':name})
context={'payload':a.extract_cached_result(result,result['observed']),'response':response,'binding':{'source_candidate_identity':'SYNTHETIC_UNIT_FIXTURE_NOT_A_CANDIDATE','publication_export_sha256':'SYNTHETIC_UNIT_FIXTURE_NOT_AN_EXPORT','qualified_observed_replay_row_sha256':'SYNTHETIC_UNIT_FIXTURE_NOT_AN_OBSERVED_ROW'},'index':{'roles':{'raw_input_inventory':'inventory','source_scope_note':'scope','source_receipts':['receipt']}},'paths':{name:meta/(name+'.json') for name in ['inventory','scope','receipt']}}
summary={'fixture_only':'SYNTHETIC_UNIT_FIXTURE','actual_scientific_qualification':False}
def render():
 a.render_unit_fixture(result,response,prose,out);shutil.copyfile(ROOT/'code/references.bib',out/'references.bib');context['payload']=a.extract_cached_result(result,result['observed']);context['response']=response;a.dump(out/'NUMERICAL_SUPPLEMENT.json',a.numerical_supplement(context));a.dump(out/'NUMBER_FIGURE_MAP.json',a.map_for_products(context,out))
def checked():return a.check_rendered_products(context,out)
def text():return subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],capture_output=True,text=True,check=True).stdout
def page(name):
 shutil.copyfile(out/'main.pdf',ROOT/(name+'.pdf'));subprocess.run(['pdftoppm','-f','4','-singlefile','-r','60','-png',str(ROOT/(name+'.pdf')),str(ROOT/name)],check=True,capture_output=True);return np.array(Image.open(ROOT/(name+'.png')))
render();summary['prebuild']=checked()
initial=subprocess.run(['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=out,capture_output=True,text=True);(ROOT/'initial_build.log').write_text(initial.stdout+initial.stderr);assert initial.returncode==0
summary['old_response_verified']=checked();oldpdf=(out/'main.pdf').read_bytes();oldtext=text();oldpage=page('old_response')
for field in a.FIELDS:
 for key,v in response['columns'][1][field].items():response['columns'][1][field][key]=[-v[0],-v[1]]
render();summary['changed_response_verifier_build']=checked();currentpage=page('current_response');currenttext=text();summary['same_scalar_pdf_text_equal']=oldtext==currenttext;summary['old_vs_current_changed_pixels']=int(np.count_nonzero(np.any(oldpage!=currentpage,axis=-1)));assert summary['old_vs_current_changed_pixels']>0
(out/'main.pdf').write_bytes(oldpdf);summary['restored_pdf_is_exact_old_bytes']=a.sha(out/'main.pdf')==hashlib.sha256(oldpdf).hexdigest();before=(out/'main.verify-build.log').stat().st_mtime_ns
summary['restored_old_pdf_verification']=checked();after=(out/'main.verify-build.log').stat().st_mtime_ns;summary['verifier_executed_new_build']=after>before
rebuiltpage=page('after_verification');summary['after_verification_vs_current_changed_pixels']=int(np.count_nonzero(np.any(rebuiltpage!=currentpage,axis=-1)));summary['after_verification_vs_old_changed_pixels']=int(np.count_nonzero(np.any(rebuiltpage!=oldpage,axis=-1)))
assert summary['after_verification_vs_current_changed_pixels']==0 and summary['after_verification_vs_old_changed_pixels']>0
assert text()==currenttext;shutil.copyfile(out/'main.verify-build.log',ROOT/'restored_old_pdf_force_build.log')
# F1 precedes the build; keep closed-path coverage narrow.
supp=out/'NUMERICAL_SUPPLEMENT.json';saved=supp.read_bytes();j=json.loads(saved);j['complete_cached_result']['source_result']['observed'][a.FIELDS[1]]={};a.dump(supp,j);before=(out/'main.verify-build.log').stat().st_mtime_ns
try:checked();raise AssertionError('F1 signed-B loss accepted')
except ValueError as e:summary['F1_signed_B_deletion_rejected']=str(e)
assert (out/'main.verify-build.log').stat().st_mtime_ns==before;supp.write_bytes(saved);summary['F1_rejected_before_build']=True
# No-op regeneration and real metadata-varying forced build remain allowed.
beforetext=text();beforehash=a.sha(out/'main.pdf');render();summary['no_op_verification']=checked();summary['metadata_rebuild_text_equal']=text()==beforetext;summary['metadata_rebuild_pdf_bytes_changed']=a.sha(out/'main.pdf')!=beforehash;assert summary['metadata_rebuild_text_equal']
# Actual pending binding cannot reach the new force-build branch.
cp=subprocess.run([sys.executable,'-B',str(ROOT/'code/assemble.py'),'--binding',str(ROOT/'code/FINAL_SOURCE_BINDING.json'),'--check','--built-pdf'],capture_output=True,text=True);(ROOT/'actual_pending_cli.log').write_text(cp.stdout+cp.stderr);summary['actual_pending_cli_exit']=cp.returncode;summary['pending_verifier_build_log_absent']=not (ROOT/'code/main.verify-build.log').exists();assert cp.returncode==3 and summary['pending_verifier_build_log_absent']
# A real failed current build must not issue VERIFIED_CURRENT_BUILD.
tex=out/'main.tex';savedtex=tex.read_bytes();tex.write_bytes(savedtex.replace(b'\\maketitle',b'\\maketitle\\SYNTHETICUNDEFINEDCOMMAND'))
try:a.verify_current_pdf(context,out);raise AssertionError('invalid current TeX build accepted')
except ValueError as e:summary['actual_build_failure_rejected']=str(e)
shutil.copyfile(out/'main.verify-build.log',ROOT/'intentional_build_failure_first.log');tex.write_bytes(savedtex)
summary['resolved_findings']=['F1','F2'];summary['residual_findings']=[]
(ROOT/'CLOSEOUT_PROBE.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
