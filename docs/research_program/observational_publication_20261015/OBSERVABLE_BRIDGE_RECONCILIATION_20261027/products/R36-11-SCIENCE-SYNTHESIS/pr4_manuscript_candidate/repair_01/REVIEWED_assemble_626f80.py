#!/usr/bin/env python3
"""PR4 P2 companion: cached-only extraction, never maps, fits or producers.

A pending binding prevents all final assembly. Synthetic unit fixtures exercise
pure functions only and cannot create an eligible formal science return.
"""
import argparse,csv,hashlib,io,json,math,pathlib,re,subprocess,sys
import numpy as np
from scipy.stats import beta
HERE=pathlib.Path(__file__).resolve().parent
EDITOR_SHA='5acd1188f3eeeb15002f2ff2cdec6825589b3a9944829c3d297b8f0c0e344d49'
PROSE_SHA='61e879fcf53a9c3c069f2cee45bf78afd542b0308a55f36cf70b7755c75efe62'
SCIENCE_SHA='fa08a55ccbf7a5e488cfc2866f0138d0682d3732fe01a785870f8adf9fc677d4'
ROW_SCHEMA='htt.r36_pr4_commander_map_morphology/1'
FULL_SCHEMA='htt.r36_pr4_commander_morphology_result/1'
COEFF_KEYS={f'{ell},{m}' for ell in [2,3,4] for m in range(-ell,ell+1)}
FIELDS=['E_l2_l3_l4_full_signed_m','B_l2_l3_l4_full_signed_m']
REQUIRED=['qualified_result_path','qualified_result_sha256','source_candidate_identity','source_candidate_manifest_path','source_candidate_manifest_sha256','formal_source_return_path','formal_source_return_sha256','independent_scientific_reviewer_identity','qualified_observed_replay_row_path','qualified_observed_replay_row_sha256','replay_comparison_receipt_path','replay_comparison_receipt_sha256']
class PendingSourceQualification(ValueError):pass
def require(ok,label):
 if not ok:raise ValueError(label)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def strict_json(p):
 def bad(x):raise ValueError('nonfinite JSON '+x)
 return json.loads(pathlib.Path(p).read_text(),parse_constant=bad)
def dump(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def canonical(j):return json.dumps(j,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def finite(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def protected_binding(binding):
 missing=[k for k in REQUIRED if not binding.get(k)]
 if missing:raise PendingSourceQualification('PENDING_SOURCE_QUALIFICATION: missing '+', '.join(missing))
 require(binding.get('editor_contract_sha256')==EDITOR_SHA,'editor contract binding')
 # Author status and current download count never stand in for source review.
 require(binding.get('status')=='QUALIFIED_FINAL_SOURCE_BOUND','PENDING_SOURCE_QUALIFICATION: binding not qualified')
 for stem in ['qualified_result','source_candidate_manifest','formal_source_return','qualified_observed_replay_row','replay_comparison_receipt']:
  p=pathlib.Path(binding[stem+'_path']);require(p.suffix=='.json','small cached JSON required: '+stem)
  require(p.is_file() and sha(p)==binding[stem+'_sha256'],'exact cached source identity '+stem)
 require(pathlib.Path(binding['qualified_result_path']).name=='COMMANDER_RESULT.json','final Commander result required; no pilot/030 result')
 require(binding['source_candidate_identity']=='sha256:'+binding['source_candidate_manifest_sha256'],'candidate manifest identity')
 return binding

def cp_interval(k,B=100):
 require(type(B) is int and B==100 and type(k) is int and 0<=k<=B,'fixed100 binomial counts')
 return [0.0 if k==0 else float(beta.ppf(.025,k,B-k+1)),1.0 if k==B else float(beta.ppf(.975,k+1,B-k))]
def rank_summary(Tobs,values):
 require(finite(Tobs) and Tobs>=0,'finite nonnegative observed T')
 require(len(values)==100 and all(finite(v) and v>=0 for v in values),'exactly100 finite cached T values')
 k=sum(v>=Tobs for v in values);lo,hi=cp_interval(k)
 require((hi-lo)/2<=.105,'fixed CP precision')
 return {'inclusive_tail_count_k':k,'B':100,'p_rank':(1+k)/101,'empirical_tail_k_over_B':k/100,'clopper_pearson_95':[lo,hi],'interval_half_width':(hi-lo)/2,'ties_included':True}

def coefficients(obj,nonzero_E=False):
 for field in FIELDS:
  j=obj[field];require(set(j)==COEFF_KEYS,'complete signed E/B index set')
  for key,v in j.items():require(isinstance(v,list) and len(v)==2 and all(finite(x) for x in v),'finite complex coefficient '+key)
  for ell in [2,3,4]:
   scale=math.sqrt(sum(abs(complex(*j[f'{ell},{m}']))**2 for m in range(-ell,ell+1)))
   if nonzero_E and field==FIELDS[0]:require(scale>0,'zero E multipole invalid')
   for m in range(0,ell+1):
    a=complex(*j[f'{ell},{m}']);b=complex(*j[f'{ell},{-m}']);error=abs(b-((-1)**m)*a.conjugate())
    require(error==0 if scale==0 else error/scale<=1e-12,'normalized reality relation')
 return obj

def check_row(row,reference,expected_id):
 require(row['schema']==ROW_SCHEMA and row['task_id']==reference['task_id'] and row['packet_id']==reference['packet_id'] and row['input_identity']==reference['input_identity'],'row exact task/packet/input')
 require(row['contract_sha256']==SCIENCE_SHA,'row science source seal')
 require(row['kind']==('observed' if expected_id is None else 'mc') and row['mc_id']==expected_id,'exact prescribed ID/kind')
 require(row['mask']==reference['mask'],'identical source/mask/operator geometry')
 require(row['consumer_source_sha256']==reference['consumer_source_sha256'] and row['feature_source']==reference['feature_source'],'row consumer/feature/power seals')
 expected=dict(reference['operator']);expected['input_conversion_to_K_CMB']=1 if expected_id is None else 1e-6
 require(row['operator']==expected,'identical operator/frame/unit conventions')
 source=row['source'];require(re.fullmatch('[0-9a-f]{64}',source.get('sha256','')) and source.get('receipt') and source.get('path'),'whole-file source/receipt reference')
 if expected_id is not None:
  require(source.get('mc_id')==expected_id and source.get('size_bytes')==603990720 and source.get('role')=='processed Commander FULL MC sky','prescribed whole-file MC source')
  require(pathlib.Path(source['path']).name==f'npipe6v20_commander_cmb_2048_mc_{expected_id:04d}_005a.fits','prescribed FULL005a product')
 coefficients(row,True)
 J=row['features']['J234'];T=row['T_abs_J234'];require(finite(J) and finite(T) and abs(T-abs(J))<=1e-12,'T=abs(signed J)')
 for ell in [2,3,4]:
  a=row[FIELDS[0]];power=sum(abs(complex(*a[f'{ell},{m}']))**2 for m in range(-ell,ell+1))/(2*ell+1)
  cached=row['features']['C_ell_K_CMB2'][str(ell)]
  require(finite(cached) and (cached==0 if power==0 else abs(cached/power-1)<=1e-12),'cached E power parity')
 controls=row['controls'];require(controls['limit']==1e-12 and controls['errors'] and all(finite(v) and 0<=v<=1e-12 for v in controls['errors'].values()),'frozen output controls')
 if expected_id in [None,300]:
  stability=row['stability'];require(stability['limit']==1e-10 and finite(stability['relative_joint_EB_norm_residual']) and 0<=stability['relative_joint_EB_norm_residual']<=1e-10,'observed0300 native coefficient stability')
 return row

def extract_cached_result(result,observed):
 require(result['schema']==FULL_SCHEMA,'final result schema')
 require(result['fixed_mc_ids']==list(range(300,400)) and result['independent_null_units']==100,'fixed0300..0399 whole ensemble')
 require(result['observed']==observed,'qualified replay selection; historical unbound observed row forbidden')
 require(result['task_id']==observed['task_id'] and result['packet_id']==observed['packet_id'] and result['input_identity']==observed['input_identity'],'result source identities')
 require(result['contract_sha256']==SCIENCE_SHA,'result science seal')
 check_row(observed,observed,None);rows=result['mc_rows']
 require(len(rows)==100 and sorted(r['mc_id'] for r in rows)==list(range(300,400)),'100 unique prescribed IDs')
 for row in rows:check_row(row,observed,row['mc_id'])
 rank=rank_summary(observed['T_abs_J234'],[r['T_abs_J234'] for r in rows]);cached=result['rank']
 require(set(cached)==set(rank),'complete rank fields')
 for key,value in rank.items():
  if isinstance(value,(bool,int)):require(type(cached[key]) is type(value) and cached[key]==value,'exact count/tie '+key)
  else:require(np.allclose(cached[key],value,rtol=0,atol=1e-12),'cached scalar parity '+key)
 # Full lossless source object retained; scalar index does not replace E/B or controls.
 return {'source_result':result,'qualified_observed_selection':observed,'derived_rank':rank}

def survival_data(values):
 require(len(values)==100 and all(finite(v) and v>=0 for v in values),'survival fixed100 values')
 thresholds=sorted(set(values));return {'thresholds':thresholds,'inclusive_counts':[sum(v>=t for v in values) for t in thresholds],'B':100}
def response_data(response):
 columns=response['columns'];require([r['label'] for r in columns]==['E2_m0','E3_m1_real','B4_m2_imag'],'three prescribed columns')
 require(response['linearity_limit']==1e-10 and finite(response['linearity_relative_joint_EB_residual']) and 0<=response['linearity_relative_joint_EB_residual']<=1e-10 and response['masked_pixels_exactly_zero'] is True,'cached mask linearity/zero controls')
 values=[];labels=[]
 for field in FIELDS:
  for ell in [2,3,4]:
   for m in range(0,ell+1):
    for component in ([0] if m==0 else [0,1]):
     labels.append(field[0]+str(ell)+':'+str(m)+('' if m==0 else ' Re' if component==0 else ' -Im'))
     values.append([float(col[field][f'{ell},{m}'][component])*(1 if m==0 else math.sqrt(2)*(1 if component==0 else -1)) for col in columns])
 for col in columns:coefficients(col)
 require(np.shape(values)==(42,3),'complete42real EB response display')
 return {'coordinate_order':labels,'values':values,'columns':[c['label'] for c in columns],'scope':'three selected columns only, no full matrix or rank'}

def csv_index(result):
 stream=io.StringIO();writer=csv.writer(stream,lineterminator='\n');writer.writerow(['id','source_sha256','signed_J234','T_abs_J234','descriptive_axis_status'])
 for row in [result['observed']]+sorted(result['mc_rows'],key=lambda j:j['mc_id']):writer.writerow(['observed' if row['kind']=='observed' else f"{row['mc_id']:04d}",row['source']['sha256'],repr(row['features']['J234']),repr(row['T_abs_J234']),row['features'].get('axis_status','UNAVAILABLE')])
 return stream.getvalue()

def public_text(prose):
 pieces=prose.split('<!-- BEGIN PROPOSED PUBLIC TEXT -->');require(len(pieces)==2,'one public text block');return pieces[1].split('<!-- END PROPOSED PUBLIC TEXT -->')[0].strip()
def tex_template(prose):
 text=public_text(prose);title=text.splitlines()[0].lstrip('# ');text='\n'.join(text.splitlines()[1:]).strip()
 captions={}
 for n in [1,2]:
  m=re.search(r'^Figure '+str(n)+r'\. (.+)$',text,re.M);require(m is not None,'frozen figure caption');captions[n]=m[1];text=text[:m.start()]+text[m.end():]
 mapping={'T_OBS':'Tobs','K':'K','K_OVER_B':'Empirical','P_RANK':'Rank','CP_LOW':'CPlow','CP_HIGH':'CPhigh','CP_HALF_WIDTH':'CPhalf'}
 # Preserve the frozen wording and replace numerical slots by gated TeX macros.
 text=text.replace('**[PENDING_FINAL_CP_LOW, PENDING_FINAL_CP_HIGH]**',r'\( [\PRFourCPlow,\PRFourCPhigh] \)')
 for key,macro in mapping.items():text=text.replace('**[PENDING_FINAL_'+key+']**',r'\PRFour'+macro+'{}')
 require('PENDING_FINAL' not in text,'known slots only')
 text=text.replace('The data products and processing genealogy are documented by the NPIPE release and the Planck Legacy Archive.','The data products and processing genealogy are documented by the NPIPE release and the Planck Legacy Archive'+r'~\cite{NPIPE2020,ESA_SIMULATION,PLA_PRODUCTS}.')
 text=text.replace('The delivered resolution is described as nominally 5 arcmin. No additional smoothing, beam inversion, noise subtraction or scalar transfer correction is applied. These coefficients retain the released processing response and the extra mask response.', 'We use the delivered maps without additional smoothing, beam inversion or noise subtraction. No scalar effective beam is specified or inferred; the delivered processing response and the additional mask response are retained.')
 tex=subprocess.run(['pandoc','-f','markdown+raw_tex+tex_math_single_backslash','-t','latex','--shift-heading-level-by=-1'],input=text,text=True,capture_output=True,check=True).stdout
 tex=re.sub(r'\\texttt\{([^}]+)\}',lambda m:r'\nolinkurl{'+m[1].replace(r'\_', '_')+'}',tex)
 figs=''
 for n,name in [(1,'morphology_survival.pdf'),(2,'mask_response_columns.pdf')]:
  cap=captions[n].replace('_',r'\_');figs+='\n\\begin{figure}[htbp]\n\\centering\\includegraphics[width=.95\\linewidth,height=.72\\textheight,keepaspectratio]{figures/'+name+'}\n\\caption{'+cap+'}\n\\end{figure}\n'
 return r'''\documentclass[aps,prd,reprint,onecolumn,nofootinbib]{revtex4-2}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,graphicx,booktabs}
\usepackage{xurl}\usepackage[colorlinks=true]{hyperref}
\setlength{\emergencystretch}{4em}
\InputIfFileExists{generated/numbers.tex}{}{\PackageError{PR4}{PENDING_SOURCE_QUALIFICATION}{Final qualified MC100 source required.}\stop}
\begin{document}
\title{'''+title+r'''}
\author{Conditional methods research draft}\noaffiliation
\maketitle
'''+tex+'\n'+r'\input{generated/methods_table.tex}'+'\n'+r'\input{generated/results_table.tex}'+'\n'+figs+'\n'+r'\bibliographystyle{apsrev4-2}\bibliography{references}'+'\n'+r'\end{document}'+'\n'

def numbers_tex(rank,Tobs):
 values={'Tobs':Tobs,'K':rank['inclusive_tail_count_k'],'Empirical':rank['empirical_tail_k_over_B'],'Rank':rank['p_rank'],'CPlow':rank['clopper_pearson_95'][0],'CPhigh':rank['clopper_pearson_95'][1],'CPhalf':rank['interval_half_width']}
 return '\n'.join(r'\newcommand{\PRFour'+k+'}{'+(str(v) if type(v) is int else f'{v:.12g}')+'}' for k,v in values.items())+'\n'
def tables_tex(result):
 methods=r'''\begin{table}[htbp]\centering\small
\caption{The specified released product and common mask-and-analysis operator. No upstream transfer matrix is reconstructed.}
\begin{tabular}{ll}\toprule
Observed product & Commander FULL, polarization NSIDE2048\\
Simulation products & npipe6v20 Commander FULL005a, IDs0300--0399\\
Frame/convention & Galactic/COSMO\\
Output coefficients & Full signed E/B, $\ell=2,3,4$, K\_CMB\\
Mask & Lollipop binary NSIDE16, 1273/3072 retained\\
Lift and analysis & NESTED parent--child lift, RING spin2, $\ell_{\max}=4$\\
Extra smoothing/deconvolution & None\\\bottomrule\end{tabular}\end{table}
'''
 results=r'''\begin{table}[htbp]\centering\small
\caption{Fixed100 processed-map working-law comparison. The95\% interval concerns the simulation-tail probability; observed/simulated exchangeability is an additional rank assumption.}
\begin{tabular}{llllllll}\toprule
$T_{\rm obs}$ & $k$ & $B$ & $k/B$ & $(1+k)/101$ & CP low & CP high & Half-width\\\midrule
\PRFourTobs & \PRFourK & 100 & \PRFourEmpirical & \PRFourRank & \PRFourCPlow & \PRFourCPhigh & \PRFourCPhalf\\\bottomrule
\end{tabular}\end{table}
'''
 return methods,results.replace(r'\begin{tabular}',r'\resizebox{\linewidth}{!}{\begin{tabular}').replace(r'\end{tabular}',r'\end{tabular}}')
def plot_figures(result,response,out,fixture_only=False):
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 out.mkdir(parents=True,exist_ok=True)
 values=[r['T_abs_J234'] for r in result['mc_rows']];data=survival_data(values);Tobs=result['observed']['T_abs_J234'];rank=result['rank']
 # Inclusive survival at each distinct threshold. On (t_i,t_{i+1}],
 # count(T>=t_{i+1})/100 is represented by a pre-step and filled threshold dots.
 thresholds=data['thresholds'];span=max(max(thresholds+[Tobs])-min(thresholds+[Tobs]),1e-6);left=min(thresholds+[Tobs])-.03*span;right=max(thresholds+[Tobs])+.03*span
 x=[left]+thresholds+[right];y=np.array([100]+data['inclusive_counts']+[0])/100
 fig,ax=plt.subplots(figsize=(7.5,4.8),constrained_layout=True);ax.step(x,y,where='pre',color='#315d85');ax.scatter(x,y,s=7,color='#315d85');ax.axvline(Tobs,color='#b34036',label='Observed threshold')
 ax.set(xlabel=r'$T=|J_{234}|$',ylabel='Inclusive empirical survival fraction',ylim=(-.02,1.03));ax.legend();ax.text(.98,.96,f"k/100 = {rank['inclusive_tail_count_k']}/100\n(1+k)/101 = {rank['p_rank']:.8g}",ha='right',va='top',transform=ax.transAxes)
 if fixture_only:ax.set_title('SYNTHETIC UNIT FIXTURE — not a PR4 result')
 fig.savefig(out/'morphology_survival.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
 responseplot=response_data(response);M=np.array(responseplot['values']);lim=float(np.max(np.abs(M)));require(lim>0,'nonzero selected response display')
 fig,ax=plt.subplots(figsize=(6.3,9.2),constrained_layout=True);im=ax.imshow(M,aspect='auto',cmap='RdBu_r',vmin=-lim,vmax=lim);ax.set_xticks(range(3),responseplot['columns']);ax.set_yticks(range(42),responseplot['coordinate_order'],fontsize=8)
 ax.set_ylabel('E2,E3,E4,B2,B3,B4; m0 then sqrt(2)Re, -sqrt(2)Im');fig.colorbar(im,ax=ax,label='Selected signed unit-mode response')
 if fixture_only:ax.set_title('SYNTHETIC UNIT FIXTURE — three columns only',fontsize=9)
 fig.savefig(out/'mask_response_columns.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
 return {'survival':data,'response':responseplot}
def render_unit_fixture(result,response,prose,out):
 """Isolated tool exercise; no formal source/RETURN eligibility is fabricated."""
 require((out/'.SYNTHETIC_UNIT_FIXTURE').is_file(),'isolated labelled unit fixture required')
 extracted=extract_cached_result(result,result['observed']);figdata=plot_figures(result,response,out/'figures',True)
 tex=tex_template(prose).replace(r'\author{Conditional methods research draft}',r'\author{SYNTHETIC UNIT FIXTURE -- NOT A PR4 RESULT}')
 tex=tex.replace(r'\maketitle',r'\maketitle'+'\n'+r'\noindent\textbf{All numerical rows, curves and response columns in this document are deterministic synthetic unit fixtures. No scientific qualification or PR4 result is represented.}')
 (out/'main.tex').write_text(tex);(out/'generated').mkdir(exist_ok=True)
 (out/'generated/numbers.tex').write_text('% SYNTHETIC UNIT FIXTURE ONLY\n'+numbers_tex(result['rank'],result['observed']['T_abs_J234']))
 for name,text in zip(['methods_table.tex','results_table.tex'],tables_tex(result)):(out/'generated'/name).write_text('% SYNTHETIC UNIT FIXTURE ONLY\n'+text)
 (out/'generated/all_draws.csv').write_text(csv_index(result));dump(out/'NUMERICAL_SUPPLEMENT.json',{'fixture_only':True,'complete_cached_result':extracted,'complete_response':response,'figure_data':figdata})
 return figdata

CLARIFICATION_SHA='2e1de6ef50bdd5324a4436a55ed51adc51a986ad44613d253ca2c21c80b2465d'
EXTRA_BINDING=['publication_export_path','publication_export_sha256','source_packet_id','review_packet_id','formal_raw_receipt_path','formal_raw_receipt_sha256']
def export_path(root,rel):
 p=pathlib.Path(rel);require(not p.is_absolute() and '..' not in p.parts,'EXPORT_BINDING_HOLD: relative path escape')
 q=root/p;require(q.resolve().is_relative_to(root.resolve()),'EXPORT_BINDING_HOLD: symlink escape');return q

def validate_export(binding,editor):
 for k in EXTRA_BINDING:
  if not binding.get(k):raise PendingSourceQualification('PENDING_SOURCE_QUALIFICATION: missing '+k)
 indexpath=pathlib.Path(binding['publication_export_path']);require(indexpath.suffix=='.json' and indexpath.is_file() and sha(indexpath)==binding['publication_export_sha256'],'EXPORT_BINDING_HOLD: index identity');root=indexpath.parent;index=strict_json(indexpath)
 require(index['schema']=='htt.r36.pr4_morphology_publication_export/1' and index['source_candidate_identity']==binding['source_candidate_identity'],'EXPORT_BINDING_HOLD: export candidate identity')
 ref=index['source_manifest'];manifestpath=export_path(root,ref['relative_path']);require(manifestpath==pathlib.Path(binding['source_candidate_manifest_path']),'EXPORT_BINDING_HOLD: selected manifest copy')
 require(manifestpath.stat().st_size==ref['bytes'] and sha(manifestpath)==ref['sha256']==binding['source_candidate_manifest_sha256'],'EXPORT_BINDING_HOLD: exact manifest bytes');manifest=strict_json(manifestpath)
 required=['schema','task_id','packet_id','input_identity','agent_id','owner','scope','claim_tier','transfer_source','qualification_status','acceptance_met','qualified_products','source_bindings','candidate_files'];require(all(k in manifest for k in required),'EXPORT_BINDING_HOLD: canonical manifest structure')
 require(manifest['task_id']==editor['source_task'] and manifest['packet_id']==editor['source_packet_id']==binding['source_packet_id'] and manifest['input_identity']==editor['source_input_identity'],'EXPORT_BINDING_HOLD: source task/packet/input')
 require(isinstance(index['files'],dict) and isinstance(index['roles'],dict),'EXPORT_BINDING_HOLD: files/roles objects');paths={};originals={};expected_fields={'manifest_section','manifest_key','original_path','relative_path','sha256','bytes'}
 for key,b in index['files'].items():
  require(set(b)==expected_fields and b['manifest_section'] in ['candidate_files','source_bindings'],'EXPORT_BINDING_HOLD: exact file entry')
  entry=manifest[b['manifest_section']][b['manifest_key']];require(entry['path']==b['original_path'] and entry['sha256']==b['sha256'] and entry['bytes']==b['bytes'],'EXPORT_BINDING_HOLD: canonical entry equality')
  q=export_path(root,b['relative_path']);require(q.is_file() and q.stat().st_size==b['bytes'] and sha(q)==b['sha256'],'EXPORT_BINDING_HOLD: payload byte identity')
  require(q.suffix not in ['.fits','.bin'] and not q.name.endswith('.partial'),'EXPORT_BINDING_HOLD: no raw maps in cached export');paths[key]=q;originals[key]=b['original_path']
 roles=index['roles']
 for k in ['result','observed_row','mask_response_json','mask_response_npz','raw_input_inventory','observed_replay_parity','observed_replay_run','scientific_contract','source_scope_note']:require(roles.get(k) in paths,'EXPORT_BINDING_HOLD: required role '+k)
 require(len(roles['mc_rows'])==100 and len(set(roles['mc_rows']))==100 and all(k in paths for k in roles['mc_rows']),'EXPORT_BINDING_HOLD: ordered100 row exports')
 require(isinstance(roles['source_receipts'],list) and roles['source_receipts'] and all(k in paths for k in roles['source_receipts']),'EXPORT_BINDING_HOLD: source receipt coverage')
 require(paths[roles['result']]==pathlib.Path(binding['qualified_result_path']) and paths[roles['observed_row']]==pathlib.Path(binding['qualified_observed_replay_row_path']) and paths[roles['observed_replay_parity']]==pathlib.Path(binding['replay_comparison_receipt_path']),'EXPORT_BINDING_HOLD: role-selected sources')
 require(sha(paths[roles['scientific_contract']])==SCIENCE_SHA,'science contract export identity')
 require(sha(paths[roles['observed_row']])==editor['selected_observed_replay']['row']['sha256'] and sha(paths[roles['observed_replay_parity']])==editor['selected_observed_replay']['author_parity_receipt']['sha256'] and sha(paths[roles['observed_replay_run']])==editor['selected_observed_replay']['run_receipt']['sha256'],'EXPORT_BINDING_HOLD: exact reviewed replay/parity/run')
 require('METADATA_AND_REVIEWED_RECEIPTS_ONLY' in str(index['raw_inputs_policy']),'EXPORT_BINDING_HOLD: cached-only source policy')
 return index,manifest,paths,originals

def formal_source_gate(binding,editor,manifest,formal):
 equalities={'task_id':editor['source_task'],'source_packet_id':editor['source_packet_id'],'input_identity':editor['source_input_identity'],'outcome':'success','acceptance_met':True,'review_status':'PASS_SCOPED_CONDITIONAL','substantive_failure':False,'candidate_identity':binding['source_candidate_identity'],'publication_export_identity':'sha256:'+binding['publication_export_sha256'],'packet_id':binding['review_packet_id']}
 for k,v in equalities.items():require(type(formal.get(k)) is type(v) and formal[k]==v,'SOURCE_QUALIFICATION_PENDING_OR_MISMATCH: '+k)
 require('pr4_morphology_result' in formal.get('qualified_products',[]),'SOURCE_QUALIFICATION_PENDING_OR_MISMATCH: exact product')
 if 'phase' in formal:require(formal['phase']=='review','SOURCE_QUALIFICATION_PENDING_OR_MISMATCH: phase')
 require(formal.get('agent_id')==binding['independent_scientific_reviewer_identity'] and formal['agent_id'] not in [None,manifest['agent_id'],editor['provenance']['author']],'SOURCE_QUALIFICATION_PENDING_OR_MISMATCH: independent author/reviewer')
 if formal.get('findings')!=[]:raise PendingSourceQualification('PENDING_SOURCE_QUALIFICATION: NARROW_REVIEW_FINDINGS_ADAPTER_PENDING; actual reviewer resolution/nonblocking field format needed, not a scientific rejection of nonblocking caveats')
 p=pathlib.Path(binding['formal_raw_receipt_path']);require(p.suffix=='.json' and p.is_file() and sha(p)==binding['formal_raw_receipt_sha256']==formal.get('raw_receipt_sha256'),'SOURCE_QUALIFICATION_PENDING_OR_MISMATCH: raw reviewer receipt')
 return formal

def receipt_coherence(result,index,paths,originals):
 receipts={originals[k]:strict_json(paths[k]) for k in index['roles']['source_receipts'] if paths[k].suffix=='.json'}
 for row in result['mc_rows']:
  source=row['source'];verified=receipts.get(source['receipt']);require(verified is not None and verified.get('sha256')==source['sha256'],'EXPORT_BINDING_HOLD: verified whole-file receipt')
  item=verified['item'];require(item['id']==row['mc_id'] and item['filename']==pathlib.Path(source['path']).name and item['bytes']==source['size_bytes'],'EXPORT_BINDING_HOLD: receipt ID/name/length')
  cat=item['catalog_row'];require(cat['RELEASE__NAME']=='PR4' and cat['SIMULATED_MAP__VERSION_MAP']=='npipe6v20' and cat['SIMULATED_MAP__COMP_SEP_METHOD']=='commander' and cat['SIMULATED_MAP__PERIOD']=='full','EXPORT_BINDING_HOLD: official product genealogy')
  completed=receipts.get(str(pathlib.Path(verified['attempt'])/'RETURN.json'));require(completed is not None and completed.get('status')=='COMPLETE' and completed.get('clean_eof') is True and completed.get('http_status')==200 and completed.get('sha256')==source['sha256'] and completed.get('response_bytes_retained')==source['size_bytes'],'EXPORT_BINDING_HOLD: original completed acquisition')
 # No source.path/raw FITS is ever opened by this consumer.
 return True

def ensure_final_adapter(binding):
 protected_binding(binding)
 editorpath=HERE/'EDITOR_CONTRACT.json';require(editorpath.is_file() and sha(editorpath)==EDITOR_SHA,'frozen local editor contract');editor=strict_json(editorpath)
 clarificationpath=HERE/'INTERFACE_CLARIFICATION.json';require(clarificationpath.is_file() and sha(clarificationpath)==CLARIFICATION_SHA,'frozen interface clarification')
 index,manifest,paths,originals=validate_export(binding,editor);formal_source_gate(binding,editor,manifest,strict_json(binding['formal_source_return_path']))
 roles=index['roles'];science_provenance=strict_json(paths[roles['scientific_contract']])['provenance'];contributors=[science_provenance.get(k) for k in ['science_author','actual_implementation_owner','prior_intake_contributor']];require(binding['independent_scientific_reviewer_identity'] not in contributors,'SOURCE_QUALIFICATION_PENDING_OR_MISMATCH: science contributor cannot self-review');result=strict_json(paths[roles['result']]);observed=strict_json(paths[roles['observed_row']]);data=extract_cached_result(result,observed)
 for expected,key,row in zip(range(300,400),roles['mc_rows'],sorted(result['mc_rows'],key=lambda j:j['mc_id'])):require(strict_json(paths[key])==row and row['mc_id']==expected,'EXPORT_BINDING_HOLD: exact101 individual row payloads')
 response=strict_json(paths[roles['mask_response_json']]);require(response['mask']==observed['mask'] and response['contract_sha256']==SCIENCE_SHA and response['packet_id']==editor['source_packet_id'],'EXPORT_BINDING_HOLD: same mask/contract/packet response');require(response['npz']['sha256']==sha(paths[roles['mask_response_npz']]),'EXPORT_BINDING_HOLD: bound response NPZ');response_data(response);receipt_coherence(result,index,paths,originals)
 scope=strict_json(paths[roles['source_scope_note']]);require(scope.get('commander_effective_beam_status')=='UNKNOWN' and scope.get('descriptor_citation_status')=='UNVERIFIED' and scope.get('numerically_used') is False,'EXPORT_BINDING_HOLD: delivered-map response scope')
 return {'binding':binding,'index':index,'manifest':manifest,'payload':data,'response':response,'paths':paths}

def map_for_products(context,out):
 result=context['payload']['source_result'];response=context['response'];rank=context['payload']['derived_rank']
 return {'source_candidate_identity':context['binding']['source_candidate_identity'],'publication_export_identity':'sha256:'+context['binding']['publication_export_sha256'],'qualified_observed_row_sha256':context['binding']['qualified_observed_replay_row_sha256'],'numbers':{'T_obs':result['observed']['T_abs_J234'],'rank':rank},'figure_data':{'survival':survival_data([r['T_abs_J234'] for r in result['mc_rows']]),'response':response_data(response)},'figures':{name:{'sha256':sha(out/'figures'/name),'bytes':(out/'figures'/name).stat().st_size} for name in ['morphology_survival.pdf','mask_response_columns.pdf']},'scope':'processed Commander working law; no physical beam/null/radiation/shear/family inference'}
def render_final_products(context,out):
 result=context['payload']['source_result'];response=context['response'];plot_figures(result,response,out/'figures')
 (out/'generated').mkdir(exist_ok=True);(out/'generated/numbers.tex').write_text(numbers_tex(context['payload']['derived_rank'],result['observed']['T_abs_J234']))
 for name,text in zip(['methods_table.tex','results_table.tex'],tables_tex(result)):(out/'generated'/name).write_text(text)
 (out/'generated/all_draws.csv').write_text(csv_index(result));(out/'main.tex').write_text(tex_template((out/'MANUSCRIPT_ADDITIONS.md').read_text()))
 roles=context['index']['roles'];dump(out/'NUMERICAL_SUPPLEMENT.json',{'complete_cached_result':context['payload'],'complete_mask_response':response,'raw_input_inventory':strict_json(context['paths'][roles['raw_input_inventory']]),'source_scope':strict_json(context['paths'][roles['source_scope_note']]),'source_candidate_identity':context['binding']['source_candidate_identity'],'source_export_index':context['index'],'all_original_source_receipts':{k:strict_json(context['paths'][k]) for k in roles['source_receipts'] if context['paths'][k].suffix=='.json'}})
 dump(out/'NUMBER_FIGURE_MAP.json',map_for_products(context,out))

def check_rendered_products(context,out,fixture_only=False):
 result=context['payload']['source_result'];response=context['response'];rank=context['payload']['derived_rank']
 require((out/'generated/numbers.tex').read_text().removeprefix('% SYNTHETIC UNIT FIXTURE ONLY\n')==numbers_tex(rank,result['observed']['T_abs_J234']),'all-row number parity')
 for name,text in zip(['methods_table.tex','results_table.tex'],tables_tex(result)):require((out/'generated'/name).read_text().removeprefix('% SYNTHETIC UNIT FIXTURE ONLY\n')==text,'all-row table parity')
 require((out/'generated/all_draws.csv').read_text()==csv_index(result),'all101 CSV parity')
 tex=(out/'main.tex').read_text();body=tex.split(r'\begin{document}',1)[1];require('PENDING' not in body and 'ideal_U' not in body,'no pending result or idealU overlay')
 for name in ['morphology_survival.pdf','mask_response_columns.pdf']:require((out/'figures'/name).is_file(),'missing figure '+name)
 citations=set(k for block in re.findall(r'\\cite\{([^}]+)\}',tex) for k in block.split(','));bib=(out/'references.bib').read_text();keys=set(re.findall(r'@\w+\{([^,]+),',bib));require(citations<=keys,'missing bibliography citation')
 if not fixture_only:require(strict_json(out/'NUMBER_FIGURE_MAP.json')==map_for_products(context,out),'all cached number/figure source identities')
 if (out/'main.pdf').exists():
  logfile=out/'main.log';require(logfile.is_file(),'new PDF requires current build log');log=logfile.read_text();require(not re.search(r'undefined references|Citation .* undefined|Reference .* undefined|LaTeX Error|Overfull \\hbox|Float too large',log),'new PDF diagnostics')
  text=subprocess.run(['pdftotext','-layout',str(out/'main.pdf'),'-'],check=True,capture_output=True).stdout;require(b'??' not in text,'unresolved PDF text')
 return True

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binding',type=pathlib.Path,required=True);p.add_argument('--check',action='store_true');a=p.parse_args()
 try:
  context=ensure_final_adapter(strict_json(a.binding))
  if not a.check:render_final_products(context,HERE)
  check_rendered_products(context,HERE)
 except PendingSourceQualification as e:print(str(e),file=sys.stderr);return 3
 return 0
if __name__=='__main__':sys.exit(main())
