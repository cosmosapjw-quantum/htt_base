"""Synthetic, deterministic unit fixtures. No source/controller return is mocked."""
import copy,hashlib,importlib.util,json,math,pathlib,subprocess,sys
import numpy as np
import pytest
from scipy.stats import binom
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import assemble as a

def fixture_coefficients(scale=1):
 out={}
 for ell in [2,3,4]:
  out[f'{ell},0']=[scale*(ell+1)/100,0.]
  for m in range(1,ell+1):
   z=scale*complex((ell+m)/100,m/100);out[f'{ell},{m}']=[z.real,z.imag];neg=(-1)**m*z.conjugate();out[f'{ell},{-m}']=[neg.real,neg.imag]
 return out

def synthetic_row(mc_id):
 E=fixture_coefficients();B=fixture_coefficients(.2)
 J=.2 if mc_id is None else ((mc_id-300)%11)/25
 return {'schema':a.ROW_SCHEMA,'fixture_only':True,'task_id':'SYNTHETIC_UNIT_TASK','packet_id':'SYNTHETIC_UNIT_PACKET','input_identity':'SYNTHETIC_UNIT_INPUT','contract_sha256':a.SCIENCE_SHA,'kind':'observed' if mc_id is None else 'mc','mc_id':mc_id,'source':{'path':'synthetic/observed.not_fits' if mc_id is None else f'synthetic/npipe6v20_commander_cmb_2048_mc_{mc_id:04d}_005a.fits','sha256':hashlib.sha256(str(mc_id).encode()).hexdigest(),'receipt':'synthetic/not_a_whole_file_receipt.json','size_bytes':603990720,'role':'processed Commander FULL MC sky','mc_id':mc_id},'mask':{'source':'SYNTHETIC_ONLY','sha256':'synthetic_mask'},'consumer_source_sha256':'synthetic_consumer','feature_source':{'sha256':'synthetic_feature'},'operator':{'frame':'GALACTIC','units':'K_CMB','input_conversion_to_K_CMB':1 if mc_id is None else 1e-6},a.FIELDS[0]:E,a.FIELDS[1]:B,'features':{'J234':J,'C_ell_K_CMB2':{str(ell):sum(abs(complex(*E[f'{ell},{m}']))**2 for m in range(-ell,ell+1))/(2*ell+1) for ell in [2,3,4]},'axis_status':'ABSTAIN_SYNTHETIC'},'T_abs_J234':abs(J),'controls':{'limit':1e-12,'errors':{'synthetic_algebra':0.}},'stability':{'limit':1e-10,'relative_joint_EB_norm_residual':0.}}

def synthetic_result():
 obs=synthetic_row(None);rows=[synthetic_row(i) for i in range(300,400)]
 return {'schema':a.FULL_SCHEMA,'fixture_only':True,'task_id':obs['task_id'],'packet_id':obs['packet_id'],'input_identity':obs['input_identity'],'contract_sha256':a.SCIENCE_SHA,'fixed_mc_ids':list(range(300,400)),'independent_null_units':100,'observed':obs,'mc_rows':rows,'rank':a.rank_summary(obs['T_abs_J234'],[r['T_abs_J234'] for r in rows])}

def synthetic_response():
 return {'fixture_only':True,'columns':[{'label':label,a.FIELDS[0]:fixture_coefficients(i+1),a.FIELDS[1]:fixture_coefficients(-.2*(i+1))} for i,label in enumerate(['E2_m0','E3_m1_real','B4_m2_imag'])],'linearity_limit':1e-10,'linearity_relative_joint_EB_residual':0.,'masked_pixels_exactly_zero':True}

def test_complete100_fixture_and_B_retained():
 j=synthetic_result();out=a.extract_cached_result(j,j['observed']);assert out['source_result']==j;assert out['source_result']['observed'][a.FIELDS[1]]==j['observed'][a.FIELDS[1]]
 assert len(a.csv_index(j).splitlines())==102

@pytest.mark.parametrize('mutation',[lambda j:j['mc_rows'].pop(),lambda j:j['mc_rows'].__setitem__(99,copy.deepcopy(j['mc_rows'][0])),lambda j:j['mc_rows'][99].__setitem__('mc_id',400),lambda j:j['mc_rows'][0]['operator'].__setitem__('frame','WRONG'),lambda j:j['mc_rows'][0]['operator'].__setitem__('units','uK'),lambda j:j['mc_rows'][0]['mask'].__setitem__('sha256','wrong'),lambda j:j['mc_rows'][0].__setitem__('consumer_source_sha256','wrong'),lambda j:j['mc_rows'][0].__setitem__('contract_sha256','wrong'),lambda j:j['mc_rows'][0][a.FIELDS[0]].pop('2,-1'),lambda j:j['mc_rows'][0][a.FIELDS[1]]['3,-1'].__setitem__(0,99.),lambda j:j['mc_rows'][0][a.FIELDS[0]]['2,0'].__setitem__(0,float('nan')),lambda j:j['mc_rows'][0].__setitem__('T_abs_J234',.999),lambda j:j['mc_rows'][0]['source'].__setitem__('sha256','unknown'),lambda j:j['mc_rows'][0]['source'].__setitem__('path','wrong_005b.fits')])
def test_bad_rows_reject(mutation):
 j=synthetic_result();mutation(j)
 with pytest.raises(ValueError):a.extract_cached_result(j,j['observed'])

def test_zero_E_reject():
 j=synthetic_result()
 for key in list(j['mc_rows'][0][a.FIELDS[0]]):
  if key.startswith('2,'):j['mc_rows'][0][a.FIELDS[0]][key]=[0.,0.]
 with pytest.raises(ValueError,match='zero E'):a.extract_cached_result(j,j['observed'])

def test_unbound_old_observed_reject():
 j=synthetic_result();old=copy.deepcopy(j['observed']);old['consumer_source_sha256']='UNKNOWN_HISTORICAL'
 with pytest.raises(ValueError,match='qualified replay'):a.extract_cached_result(j,old)

def test_ties_and_rank_are_distinct():
 values=[.1]*63+[.2]*17+[.3]*20;r=a.rank_summary(.2,values)
 assert r['inclusive_tail_count_k']==37 and r['empirical_tail_k_over_B']==.37 and r['p_rank']==38/101
 s=a.survival_data(values);assert s['inclusive_counts']==[100,37,20]

@pytest.mark.parametrize('k',[0,37,100])
def test_CP_independent_binomial_tail_equations(k):
 lo,hi=a.cp_interval(k)
 if k==0:assert lo==0 and abs(hi-(1-.025**.01))<1e-12
 else:assert abs(binom.sf(k-1,100,lo)-.025)<1e-12
 if k==100:assert hi==1 and abs(lo-.025**.01)<1e-12
 else:assert abs(binom.cdf(k,100,hi)-.025)<1e-12

@pytest.mark.parametrize('k',[-1,101,1.5])
def test_CP_invalid_counts(k):
 with pytest.raises(ValueError):a.cp_interval(k)

def test_wrong_pseudocount_CP_reject():
 j=synthetic_result();j['rank']['clopper_pearson_95'][0]=float(__import__('scipy').stats.beta.ppf(.025,1+j['rank']['inclusive_tail_count_k'],101-j['rank']['inclusive_tail_count_k']+1))
 with pytest.raises(ValueError):a.extract_cached_result(j,j['observed'])

def test_response42_signed_coordinates_and_B():
 j=synthetic_response();d=a.response_data(j);assert np.shape(d['values'])==(42,3)
 assert d['coordinate_order'][21].startswith('B2');assert d['values'][2][0]==-math.sqrt(2)*.01
 assert any(any(x!=0 for x in row) for row in d['values'][21:])

def test_response_negative_m_loss_reject():
 j=synthetic_response();j['columns'][0][a.FIELDS[1]].pop('4,-4')
 with pytest.raises(ValueError):a.response_data(j)

@pytest.mark.parametrize('binding',[{}, {'status':'AUTHOR_PASS'}, {'qualified_result_path':'RESULT.json','qualified_result_sha256':'unknown'}])
def test_pending_source_fails_before_outputs(binding,tmp_path):
 before=list(tmp_path.iterdir())
 with pytest.raises(a.PendingSourceQualification,match='PENDING_SOURCE_QUALIFICATION'):a.ensure_final_adapter(binding)
 assert list(tmp_path.iterdir())==before

def test_template_no_result_bytes_and_gate():
 prose=(pathlib.Path(__file__).parent/'MANUSCRIPT_ADDITIONS.md').read_text();tex=a.tex_template(prose)
 assert 'PENDING_SOURCE_QUALIFICATION' in tex and r'\PRFourTobs{}' in tex
 assert 'R36-' not in tex and 'PROPOSED PUBLIC TEXT' not in tex and 'placement' not in tex
 assert tex.count(r'\includegraphics')==2

def test_bound_export_path_traversal_and_symlink_reject(tmp_path):
 with pytest.raises(ValueError):a.export_path(tmp_path,'../escape')
 with pytest.raises(ValueError):a.export_path(tmp_path,'/absolute')
 (tmp_path/'escape').symlink_to(tmp_path.parent)
 with pytest.raises(ValueError):a.export_path(tmp_path,'escape/somewhere')

def test_restricted_beam_wording_preserves_frozen_source():
 prose=(pathlib.Path(__file__).parent/'MANUSCRIPT_ADDITIONS.md').read_text();assert a.sha(pathlib.Path(__file__).parent/'MANUSCRIPT_ADDITIONS.md')==a.PROSE_SHA
 tex=a.tex_template(prose);assert '5 arcmin' not in tex and 'No scalar effective beam is specified or inferred' in tex
 assert 'nominally 5 arcmin' in prose

def test_rendered_fixture_missing_figure_citation_pending_and_numeric_reject(tmp_path):
 (tmp_path/'.SYNTHETIC_UNIT_FIXTURE').write_text('SYNTHETIC ONLY');j=synthetic_result();r=synthetic_response();prose=(pathlib.Path(__file__).parent/'MANUSCRIPT_ADDITIONS.md').read_text();a.render_unit_fixture(j,r,prose,tmp_path)
 bib=''.join('@misc{'+k+',title={Synthetic citation}}\n' for k in ['NPIPE2020','ESA_SIMULATION','PLA_PRODUCTS']);(tmp_path/'references.bib').write_text(bib);context={'payload':a.extract_cached_result(j,j['observed']),'response':r};assert a.check_rendered_products(context,tmp_path,True)
 p=tmp_path/'figures/morphology_survival.pdf';raw=p.read_bytes();p.unlink()
 with pytest.raises(ValueError,match='missing figure'):a.check_rendered_products(context,tmp_path,True)
 p.write_bytes(raw);(tmp_path/'references.bib').write_text('')
 with pytest.raises(ValueError,match='missing bibliography'):a.check_rendered_products(context,tmp_path,True)
 (tmp_path/'references.bib').write_text(bib);p=tmp_path/'main.tex';old=p.read_text();p.write_text(old.replace(r'\maketitle',r'\maketitle PENDING_FINAL_VALUE'))
 with pytest.raises(ValueError,match='pending'):a.check_rendered_products(context,tmp_path,True)
 p.write_text(old);p=tmp_path/'generated/numbers.tex';p.write_text('wrong numbers')
 with pytest.raises(ValueError,match='number parity'):a.check_rendered_products(context,tmp_path,True)

def test_other_product_formal_return_is_not_PR4_qualification():
 # Negative-only example of a real differently scoped return. No eligible
 # future PR4 controller result or actual candidate binding is fabricated.
 other={'task_id':'R36-04-OPTICAL-JOINT','outcome':'success','acceptance_met':True,'review_status':'PASS_SCOPED_CONDITIONAL','substantive_failure':False,'qualified_products':['optical_joint_response']}
 editor={'source_task':'R36-06-PR4-MORPHOLOGY','source_packet_id':'source_packet','source_input_identity':'source_input','provenance':{'author':'synthetic_framer'}}
 binding={'source_candidate_identity':'NOT_AN_ACTUAL_CANDIDATE','publication_export_sha256':'NOT_AN_ACTUAL_EXPORT','review_packet_id':'review_packet'}
 with pytest.raises(ValueError,match='task_id'):a.formal_source_gate(binding,editor,{'agent_id':'synthetic_author'},other)

def test_strict_nonfinite_json(tmp_path):
 p=tmp_path/'small.json';p.write_text('{"T":NaN}')
 with pytest.raises(ValueError,match='nonfinite'):a.strict_json(p)
