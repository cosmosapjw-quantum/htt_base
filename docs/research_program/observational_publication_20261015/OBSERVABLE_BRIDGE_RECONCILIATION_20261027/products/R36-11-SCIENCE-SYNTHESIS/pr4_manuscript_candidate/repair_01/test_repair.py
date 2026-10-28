"""Bounded F1/F2 deterministic synthetic regressions; no final source return."""
import copy,json,pathlib,subprocess,sys
import pytest
A=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(A));import assemble as a;import test_assemble as f

def context_for(out,result=None,response=None):
 out.mkdir(exist_ok=True);(out/'.SYNTHETIC_UNIT_FIXTURE').write_text('Synthetic unit data only; not an actual candidate binding or controller verdict.\n')
 result=result or f.synthetic_result();response=response or f.synthetic_response()
 paths={}
 for key,value in [('inventory',{'fixture_only':True,'rows':'synthetic100'}),('scope',{'fixture_only':True,'beam':'UNKNOWN'}),('receipt',{'fixture_only':True,'not_a_formal_source_return':True})]:
  paths[key]=out/(key+'.json');a.dump(paths[key],value)
 return {'payload':a.extract_cached_result(result,result['observed']),'response':response,'binding':{'source_candidate_identity':'SYNTHETIC_UNIT_NOT_A_CANDIDATE','publication_export_sha256':'SYNTHETIC_UNIT_NOT_AN_EXPORT','qualified_observed_replay_row_sha256':'SYNTHETIC_UNIT_NOT_A_BOUND_OBSERVATION'},'index':{'fixture_only':True,'roles':{'raw_input_inventory':'inventory','source_scope_note':'scope','source_receipts':['receipt']}},'paths':paths}

def render(context,out):
 a.render_unit_fixture(context['payload']['source_result'],context['response'],(A/'MANUSCRIPT_ADDITIONS.md').read_text(),out)
 a.dump(out/'NUMERICAL_SUPPLEMENT.json',a.numerical_supplement(context));a.dump(out/'NUMBER_FIGURE_MAP.json',a.map_for_products(context,out))
 (out/'references.bib').write_text(''.join('@misc{'+k+',title={Synthetic citation marker only}}\n' for k in ['NPIPE2020','ESA_SIMULATION','PLA_PRODUCTS']))

def test_complete_real_shape_supplement_and_missing_file(tmp_path):
 c=context_for(tmp_path);render(c,tmp_path);assert a.check_rendered_products(c,tmp_path)['pdf_verification']=='UNVERIFIED_PREBUILD'
 p=tmp_path/'NUMERICAL_SUPPLEMENT.json';j=a.strict_json(p)
 assert len(j['complete_cached_result']['source_result']['mc_rows'])==100 and j['source_binding']==c['binding']
 p.unlink()
 with pytest.raises(ValueError,match='missing complete numerical supplement'):a.check_rendered_products(c,tmp_path)

@pytest.mark.parametrize('mutation',[lambda j:j['complete_cached_result']['source_result']['observed'].__setitem__(a.FIELDS[1],{}),lambda j:j['complete_cached_result']['source_result']['mc_rows'][99][a.FIELDS[1]].pop('4,-4'),lambda j:j['complete_mask_response']['columns'][2][a.FIELDS[1]].pop('2,-1'),lambda j:j.__setitem__('source_candidate_identity','WRONG'),lambda j:j.__setitem__('publication_export_identity','WRONG'),lambda j:j['source_binding'].__setitem__('qualified_observed_replay_row_sha256','WRONG'),lambda j:j['all_original_source_receipts'].__setitem__('receipt',{}),lambda j:j['raw_input_inventory'].clear()])
def test_lossless_supplement_mutation_rejected(tmp_path,mutation):
 c=context_for(tmp_path);render(c,tmp_path);p=tmp_path/'NUMERICAL_SUPPLEMENT.json';j=a.strict_json(p);mutation(j);a.dump(p,j)
 with pytest.raises(ValueError,match='complete lossless numerical supplement parity'):a.check_rendered_products(c,tmp_path)

def test_current_binding_mutation_rejected(tmp_path):
 c=context_for(tmp_path);render(c,tmp_path);c['binding']['publication_export_sha256']='DIFFERENT'
 with pytest.raises(ValueError,match='complete lossless numerical supplement parity'):a.check_rendered_products(c,tmp_path)

def test_explicit_postbuild_requires_PDF(tmp_path):
 c=context_for(tmp_path);render(c,tmp_path)
 with pytest.raises(ValueError,match='missing PDF'):a.check_rendered_products(c,tmp_path,built=True)

def test_synthetic_format_has_full_lossless_check(tmp_path):
 c=context_for(tmp_path);a.render_unit_fixture(c['payload']['source_result'],c['response'],(A/'MANUSCRIPT_ADDITIONS.md').read_text(),tmp_path)
 (tmp_path/'references.bib').write_text(''.join('@misc{'+k+',title={Synthetic citation marker}}\n' for k in ['NPIPE2020','ESA_SIMULATION','PLA_PRODUCTS']))
 simple={'payload':c['payload'],'response':c['response']};assert a.check_rendered_products(simple,tmp_path,fixture_only=True,built=False)
 j=a.strict_json(tmp_path/'NUMERICAL_SUPPLEMENT.json');j['complete_cached_result']['source_result']['observed'][a.FIELDS[1]]={};a.dump(tmp_path/'NUMERICAL_SUPPLEMENT.json',j)
 with pytest.raises(ValueError,match='supplement parity'):a.check_rendered_products(simple,tmp_path,fixture_only=True,built=False)
