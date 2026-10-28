"""SYNTHETIC_UNIT_FIXTURE: same-unit F1/F2 independent closeout."""
import copy,hashlib,json,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'code'))
import assemble as a
import test_assemble as f
out=ROOT/'rendered_probe';out.mkdir(exist_ok=True)
(out/'.SYNTHETIC_UNIT_FIXTURE').write_text('F1/F2 closeout: synthetic numbers and response only.\n')
prose=(ROOT/'code/MANUSCRIPT_ADDITIONS.md').read_text();result=f.synthetic_result();response=f.synthetic_response()
meta=ROOT/'synthetic_context';meta.mkdir(exist_ok=True)
for name in ['inventory','scope','receipt']:a.dump(meta/(name+'.json'),{'fixture_only':'SYNTHETIC_UNIT_FIXTURE','role':name})
context={'payload':a.extract_cached_result(result,result['observed']),'response':response,'binding':{'source_candidate_identity':'SYNTHETIC_UNIT_FIXTURE_NOT_A_CANDIDATE','publication_export_sha256':'SYNTHETIC_UNIT_FIXTURE_NOT_AN_EXPORT','qualified_observed_replay_row_sha256':'SYNTHETIC_UNIT_FIXTURE_NOT_AN_OBSERVED_ROW'},'index':{'roles':{'raw_input_inventory':'inventory','source_scope_note':'scope','source_receipts':['receipt']}},'paths':{name:meta/(name+'.json') for name in ['inventory','scope','receipt']}}
summary={'fixture_only':'SYNTHETIC_UNIT_FIXTURE','actual_scientific_qualification':False,'findings':{}}
def render():
    a.render_unit_fixture(result,response,prose,out)
    shutil.copyfile(ROOT/'code/references.bib',out/'references.bib')
    context['payload']=a.extract_cached_result(result,result['observed']);context['response']=response
    # Labelled fixture, production-shaped payload for the production check branch.
    a.dump(out/'NUMERICAL_SUPPLEMENT.json',a.numerical_supplement(context))
    a.dump(out/'NUMBER_FIGURE_MAP.json',a.map_for_products(context,out))
def checked():return a.check_rendered_products(context,out)
def reject(name,fn):
    try:fn()
    except ValueError as e:summary[name]={'rejected':True,'error':str(e)};return
    raise AssertionError('Expected rejection: '+name)
def build(name):
    p=subprocess.run(['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=out,capture_output=True,text=True)
    (ROOT/(name+'.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,(name,p.returncode)
    return checked()
def pdftext():return subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],capture_output=True,text=True,check=True).stdout
render();summary['prebuild']=checked();supp=out/'NUMERICAL_SUPPLEMENT.json';saved=supp.read_bytes();supp.unlink();reject('F1_missing_supplement',checked);supp.write_bytes(saved)
mutations={
 'F1_missing_observed_B':lambda j:j['complete_cached_result']['source_result']['observed'].__setitem__(a.FIELDS[1],{}),
 'F1_missing_simulation_B':lambda j:j['complete_cached_result']['source_result']['mc_rows'][19].__setitem__(a.FIELDS[1],{}),
 'F1_changed_response':lambda j:j['complete_mask_response']['columns'][0][a.FIELDS[0]]['2,0'].__setitem__(0,99),
 'F1_changed_binding':lambda j:j['source_binding'].__setitem__('source_candidate_identity','DIFFERENT_SYNTHETIC_BINDING'),
 'F1_changed_export':lambda j:j.__setitem__('publication_export_identity','DIFFERENT_SYNTHETIC_EXPORT'),
 'F1_missing_receipts':lambda j:j.__setitem__('all_original_source_receipts',{}),
}
for name,mutation in mutations.items():
    j=json.loads(saved);mutation(j);a.dump(supp,j);reject(name,checked);supp.write_bytes(saved)
summary['first_build']=build('build_T02_first');oldnumeric_pdf=(out/'main.pdf').read_bytes()
result['observed']['features']['J234']=.6;result['observed']['T_abs_J234']=.6;result['rank']=a.rank_summary(.6,[r['T_abs_J234'] for r in result['mc_rows']]);render();reject('F2_exact_stale_02_to_06',checked)
summary['rebuilt_T06']=build('build_T06_first');newnumeric_pdf=(out/'main.pdf').read_bytes()
(out/'main.pdf').write_bytes(oldnumeric_pdf);reject('F2_old_numeric_PDF_current_dependency_record',checked);(out/'main.pdf').write_bytes(newnumeric_pdf)
render();summary['no_op_reassembly']=checked()
for name in ['main.tex','generated/methods_table.tex','figures/mask_response_columns.pdf','references.bib']:
    p=out/name;raw=p.read_bytes();p.write_bytes(raw+b'\n% SYNTHETIC_UNIT_FIXTURE change\n');reject('F2_changed_dependency_'+name,lambda:a.verify_current_pdf(context,out));p.write_bytes(raw)
text_before=pdftext();hash_before=a.sha(out/'main.pdf');summary['metadata_rebuild']=build('build_T06_metadata');text_after=pdftext()
summary['metadata_only_pdf_bytes_changed']=hash_before!=a.sha(out/'main.pdf');summary['metadata_rebuild_text_equal']=text_before==text_after
assert text_before==text_after
# Same F2 output/build association boundary: an older PDF with equal scalar
# paragraph but a different signed response image must not pass current build.
oldfigure_pdf=(out/'main.pdf').read_bytes();(ROOT/'old_response.pdf').write_bytes(oldfigure_pdf)
for field in a.FIELDS:
    for key,v in response['columns'][1][field].items():response['columns'][1][field][key]=[-v[0],-v[1]]
render();reject('F2_unbuilt_changed_response',checked)
summary['rebuilt_changed_response']=build('build_changed_response_first');currentfigure_pdf=(out/'main.pdf').read_bytes();(ROOT/'current_response.pdf').write_bytes(currentfigure_pdf)
currenttext=pdftext();(out/'main.pdf').write_bytes(oldfigure_pdf);oldtext=pdftext()
try:
    status=checked();summary['F2_old_figure_PDF_current_dependency_record']={'accepted':True,'status':status}
except ValueError as e:summary['F2_old_figure_PDF_current_dependency_record']={'accepted':False,'error':str(e)}
summary['same_scalar_different_response_pdf_text_equal']=oldtext==currenttext
summary['old_response_pdf_sha256']=hashlib.sha256(oldfigure_pdf).hexdigest();summary['current_response_pdf_sha256']=hashlib.sha256(currentfigure_pdf).hexdigest()
for name in ['old_response','current_response']:
    subprocess.run(['pdftoppm','-f','4','-singlefile','-r','60','-png',str(ROOT/(name+'.pdf')),str(ROOT/name)],check=True,capture_output=True)
from PIL import Image
import numpy as np
oldpixels=np.array(Image.open(ROOT/'old_response.png'));newpixels=np.array(Image.open(ROOT/'current_response.png'))
summary['response_page_changed_pixels']=int(np.count_nonzero(np.any(oldpixels!=newpixels,axis=-1)))
summary['response_page_shape']=list(oldpixels.shape)
(ROOT/'CLOSEOUT_PROBE.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if summary['F2_old_figure_PDF_current_dependency_record']['accepted']:
    raise AssertionError('F2 residual: old response figure PDF accepted with current dependency records and unchanged scalar paragraph')
