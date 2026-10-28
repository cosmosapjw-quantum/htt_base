#!/usr/bin/env python3
"""Bounded P6 cached-source document consumer. No scientific producers are called."""
import argparse,copy,csv,hashlib,importlib.util,io,json,pathlib,re,shutil,subprocess,sys,tempfile
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
CONTRACT_SHA='54362612409de22c86aebff678df11da462dc4fc38042deb382fa0582e55a22c'
PROSE_SHA='432f6fe92c505f68f0486c043d96cc452e86a3f0b0ce21e5600c360c490b3f2a'
AUTHOR='/root/r36_optical_manuscript_code'
def require(ok,s):
 if not ok:raise ValueError(s)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def load(p):return json.loads(p.read_text())
def pointer(j,p):
 for k in p.strip('/').split('/'):j=j[int(k)] if isinstance(j,list) else j[k]
 return j
def pdfhash(p):return hashlib.sha256(subprocess.run(['pdftotext','-layout',str(p),'-'],check=True,capture_output=True).stdout).hexdigest()
def relroot(c):return pathlib.Path(c['publication_plan']['root'])
def support(c,out):return out/relroot(c)/c['publication_plan']['new_directory']
def checkedpath(root,rel):
 p=pathlib.Path(rel);require(not p.is_absolute() and '..' not in p.parts,'unsafe manifest path');return root/p

def eligibility(c,paths,formal=None):
 j=load(paths['04_formal_return']) if formal is None else formal
 for k,v in c['qualification_gate']['required_exact_fields'].items():require(j.get(k)==v,'formal source eligibility '+k)
 require(j['agent_id']!=load(paths['04_result'])['agent_id'],'independent source reviewer')
 require(sha(paths['04_formal_raw'])==c['source_bindings']['04_formal_raw']['sha256'],'bound raw source receipt')
 for k in ['p6_publication','p6_formal_return']:
  require(c['qualified_p6']['candidate_identity'].split(':')[-1] in json.dumps(load(paths[k])),'P6 qualification identity')

def validate(c,repo,out):
 s=support(c,out);post=load(s/'EXPECTED_APPLIED.json') if (s/'EXPECTED_APPLIED.json').exists() else {};texts=load(s/'EXPECTED_PDF_TEXT.json') if (s/'EXPECTED_PDF_TEXT.json').exists() else {}
 def resolve(rel,b):
  p=repo/rel
  if p.is_file() and sha(p)==b['sha256']:return p
  q=s/'baseline'/rel
  require(q.is_file() and sha(q)==b['sha256'],'immutable preimage '+rel)
  require(p.is_file() and (sha(p)==post.get(rel) or (p.suffix=='.pdf' and rel in texts and pdfhash(p)==texts[rel])),'unexpected live overlay mutation '+rel)
  return q
 paths={}
 for k,b in c['source_bindings'].items():
  rel=b['path'];p=pathlib.Path(rel)
  if p.is_absolute():
   if not (p.is_file() and sha(p)==b['sha256']):p=s/'source_backup'/k
   require(p.is_file() and sha(p)==b['sha256'],'immutable external source '+k)
   paths[k]=p
  else:paths[k]=resolve(rel,b)
 eligibility(c,paths)
 old=load(paths['p6_result'])['manifest'];encoded=json.dumps(old,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
 require(hashlib.sha256(encoded).hexdigest()==c['historical_manifest_resolution']['canonical_manifest_sha256'],'P6 canonical manifest')
 for b in old['sources']:resolve(b['path'],b)
 for b in old['outputs']:resolve(str(relroot(c)/'repair_01'/b['path']),b)
 prior=load(paths['prior_three_document_manifest'])
 for b in prior['files']:
  p=checkedpath(repo,b['path']);require(p.is_file() and (sha(p)==b['postimage_sha256'] or (b.get('pdf_text_sha256') and pdfhash(p)==b['pdf_text_sha256'])),'prior publication sentinel '+b['path'])
 return paths

def nums(c,paths):
 n={}
 for b in c['number_table']:
  loc=b['locator']
  if isinstance(loc,dict):
   rows=list(csv.DictReader(io.StringIO(paths[b['source']].read_text())));v=next(x[loc['value_column']] for x in rows if x[loc['column']]==loc['equals'])
  else:v=pointer(load(paths[b['source']]),loc)
  require(v==b['value'],'number locator '+b['id']);n[b['id']]={'source':b['source'],'locator':loc,'value':v,'scope':b['scope']}
 return n

def supplement(c,paths):
 j=load(paths['04_result']);data={k:copy.deepcopy(j[k]) for k in c['full_precision_supplement']['copy_subtrees']}
 spec=importlib.util.spec_from_file_location('frozen_optical_basis',paths['04_module']);m=importlib.util.module_from_spec(spec);sys.dont_write_bytecode=True;spec.loader.exec_module(m)
 for k in ['B2','B3']:data[k]=getattr(m,k).tolist()
 data['coordinate_order']=['fitted d_x','fitted d_y','fitted d_z']+['O_'+str(i) for i in range(1,8)]
 data['coordinate_units']=c['full_precision_supplement']['coordinate_units'];data['tensor_S']=pointer(load(paths['p6_results']),'/cf4_calibration_quotient/apparent_tensor_dimensionless')
 L=np.einsum('aijk,jk->ai',np.array(data['B3']),np.array(data['tensor_S']));A=np.column_stack((-(5.0/np.log(10.0))*L,np.eye(7)))
 data['L_S_7x3']=L.tolist();data['residual_operator_A_7x10']=A.tolist()
 computed=A@np.array(data['synthetic_source_design']['summary_covariance'])@A.T
 require(np.allclose(computed,data['synthetic_source_design']['residual_covariance'],rtol=1e-12,atol=1e-22),'cached covariance parity')
 data['cached_covariance_parity']={'rtol':1e-12,'atol_mag2':1e-22,'max_absolute_difference_mag2':float(np.max(np.abs(computed-np.array(data['synthetic_source_design']['residual_covariance'])))),'status':'PASS'}
 data['scope']='Specified synthetic96 source covariance at fixed S; no empirical CF4 joint covariance or physical parameter confidence region.'
 data['source04_identity']=c['qualification_gate']['required_exact_fields']['candidate_identity']
 return data

def semantics(c,paths,data):
 original=load(paths['04_result'])
 for k in c['full_precision_supplement']['copy_subtrees']:require(data[k]==original[k],'exact cached subtree '+k)
 for k,shape in c['full_precision_supplement']['expected_shapes'].items():require(np.shape(pointer(data,k))==tuple(shape),'signed/matrix shape '+k)
 require(np.any(np.array(data['synthetic_source_design']['summary_covariance'])[:3,3:]!=0),'nonzero synthetic cross block')
 for b in c['certificate_cases']:
  v=pointer(data,b['locator'])
  for k,w in b['expected_table'].items():require(v.get(k)==w,'certificate '+b['label']+' '+k)
 # Basis equality is deterministic export only; never call profile or fitting functions.
 expected=supplement(c,paths)
 require(data==expected,'full signed coordinates covariance basis identity')
 return True

def convert(s):
 s=s.replace('–','--').replace('—','---').replace('−','-').replace('’',"'")
 s=s.replace('[QOMethods]',r'\cite{QOMethods}').replace('[Maartens2024]',r'\cite{Maartens2024}')
 return subprocess.run(['pandoc','-f','markdown+raw_tex+tex_math_single_backslash','-t','latex'],input=s,text=True,check=True,capture_output=True).stdout

def table(caption,headers,rows,label):
 return '\n\\begin{table}[htbp]\n\\centering\\small\n\\caption{'+caption+'}\\label{'+label+'}\n\\begin{tabular}{'+'l'*len(headers)+'}\n\\hline\n'+' & '.join(headers)+r' \\'+'\n\\hline\n'+'\n'.join(' & '.join(x for x in row)+r' \\' for row in rows)+'\n\\hline\n\\end{tabular}\n\\end{table}\n'
def appendix(c,paths,prose):
 blocks=re.findall(r'^\*\*Manuscript text\*\*\s*$(.*?)^\*\*End manuscript text\*\*\s*$',prose,re.M|re.S);require(len(blocks)==1,'one frozen public block');s=blocks[0]
 def fig(m):
  body=m[0];name=next(x for x in ['JOINT_RESPONSE.pdf','SOURCE_AND_FINITE_Z.pdf'] if x in body);cap=body.split('Caption:',1)[1].rstrip(']').strip()
  return '\n\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=0.94\\linewidth]{r36_optical/'+name+'}\n\\caption{'+cap+'}\n\\end{figure}\n'
 s=re.sub(r'\[Include sealed .*?\]',fig,s,flags=re.S)
 j=load(paths['04_result'])
 def tab(m):
  body=m[0];cap=body.split('Caption:',1)[1].rstrip(']').strip();cap=convert(cap).strip()
  if 'OPTICAL-SIGNED' in body:
   rows=[[r'$d_'+a+'$',f'{v:+.15g}','dimensionless'] if i<3 else [r'$O_'+str(i-2)+'$',f'{v:+.15g}','mag'] for i,(a,v) in enumerate(zip(['x','y','z']+['']*7,j['synthetic_source_design']['full_signed_summary']))]
   return table(cap,['Fitted coordinate','Signed value','Unit'],rows,'tab:opticalsigned')
  rows=[]
  for b in c['certificate_cases']:
   v=pointer(j,b['locator']);vals=[('---' if v.get(k) is None else repr(v[k])) for k in ['certified_lower_bound','certified_upper_bound','budget']]
   result='Empty' if v['physical_set_empty'] else 'Compatible' if v['compatible'] else 'Incompatible'
   rows.append([b['label']]+vals+[result])
  return table(cap,['Case','Lower','Upper',r'$B$','Result'],rows,'tab:opticalcertificates').replace(r'\begin{tabular}',r'\resizebox{\linewidth}{!}{\begin{tabular}').replace(r'\end{tabular}',r'\end{tabular}}')
 s=re.sub(r'\[Generate .*?\]',tab,s,flags=re.S);require('[Generate' not in s and '[Include' not in s,'expanded directives')
 tex=convert(s).replace(r'\subsection{',r'\section{').replace(r'\subsubsection{',r'\subsection{')
 # Add appendix equation tags only, leaving the 35 old tags untouched.
 count=[0]
 def eq(m):count[0]+=1;return '\\begin{equation}\n'+m[1].strip()+r'\tag{A'+str(count[0])+'}\n\\end{equation}'
 tex=re.sub(r'\\\[(.*?)\\\]',eq,tex,flags=re.S)
 return tex

def copyfile(src,dst):
 if src.resolve()==dst.resolve():return
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def assemble(c,repo,out,contractpath):
 s=support(c,out);require(out!=repo or (s/'EXPECTED_APPLIED.json').exists(),'production assemble requires installed reviewed overlay')
 paths=validate(c,repo,out);num=nums(c,paths);data=supplement(c,paths);semantics(c,paths,data)
 prose=HERE/'MANUSCRIPT_ADDITIONS.md';require(sha(prose)==PROSE_SHA,'frozen author text')
 for k in ['p6_main','p6_pdf']:
  rel=c['source_bindings'][k]['path'];copyfile(paths[k],s/'baseline'/rel)
 report=out/relroot(c)/'repair_01/report';original=repo/relroot(c)/'repair_01/report'
 for folder in ['generated','figures']:
  for p in (original/folder).rglob('*'):
   if p.is_file():copyfile(p,report/folder/p.relative_to(original/folder))
 copyfile(paths['p6_references'],report/'references.tex')
 copyfile(contractpath,s/'EDITOR_CONTRACT.json');copyfile(prose,s/'MANUSCRIPT_ADDITIONS.md');copyfile(pathlib.Path(__file__),s/'publication_overlay.py')
 for k in c['source_bindings']:
  if pathlib.Path(c['source_bindings'][k]['path']).is_absolute():copyfile(paths[k],s/'source_backup'/k)
 for k,name in [('04_joint_figure','JOINT_RESPONSE.pdf'),('04_source_figure','SOURCE_AND_FINITE_Z.pdf')]:copyfile(paths[k],s/name)
 old=paths['p6_main'].read_text();p=c['publication_plan'];require(old.count(p['insertion_anchor'])==1,'unique insertion anchor');write(report/'main.tex',old.replace(p['insertion_anchor'],p['replacement']))
 write(s/'appendix.tex',appendix(c,paths,prose.read_text()));dump(s/'NUMERICAL_SUPPLEMENT.json',data)
 dump(s/'NUMBER_FIGURE_MAP.json',{'owner':'manuscript','scope':'conditional optical response, cached synthetic controls','claim_tier':'C0','transfer_source':'none','numbers':num,'certificate_cases':c['certificate_cases'],'figures':{k:c['source_bindings'][k] for k in ['04_joint_figure','04_source_figure']},'original_acceptances_unchanged':True})
 write(out/relroot(c)/p['reader_entry'],'# Current optical paper\n\nThe qualified repaired baseline is extended by the conditional appendix in `repair_01/report/main.pdf`.\n\nCurrent cached-source assembly/check: `python3 repair_01/report/r36_optical/publication_overlay.py assemble|check --contract repair_01/report/r36_optical/EDITOR_CONTRACT.json --repo REPO --output-root REPO`. Build with `latexmk -pdf -interaction=nonstopmode -halt-on-error -cd -outdir=r36_optical/build repair_01/report/main.tex`, then copy the new build PDF to main.pdf. Historical build_source.py recreates the old paper.\n\nSource qualification, manuscript review, installation and scientific admission remain separate. Missing empirical covariance, source/frame transfer and physical error bounds remain unavailable.\n')
 print(json.dumps({'assembled':'P6 cached appendix','production_applied':False}))

def falsifiers(c,repo,out,paths):
 results=[]
 def fails(name,call):
  try:call()
  except (ValueError,KeyError,IndexError) as e:results.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise ValueError('accepted negative control '+name)
 for k,v in [('acceptance_met',False),('candidate_identity','sha256:wrong'),('qualified_products',[])]:
  j=load(paths['04_formal_return']);j[k]=v;fails('formal_'+k,lambda:eligibility(c,paths,j))
 data=load(support(c,out)/'NUMERICAL_SUPPLEMENT.json')
 for name,modify in [('drop_signed_component',lambda j:j['synthetic_source_design']['full_signed_summary'].pop()),('reorder_signed_component',lambda j:j['synthetic_source_design']['full_signed_summary'].reverse()),('covariance_cross_block',lambda j:[j['synthetic_source_design']['summary_covariance'][i].__setitem__(slice(3,10),[0.]*7) for i in range(3)])]:
  bad=copy.deepcopy(data);modify(bad);fails(name,lambda:semantics(c,paths,bad))
 for name,modify in [('numeric_change',lambda j:j['finite_z_example'].__setitem__('bad',1)),('basis_change',lambda j:j['B3'][0][0][0].__setitem__(0,99))]:
  bad=copy.deepcopy(data);modify(bad);fails(name,lambda:semantics(c,paths,bad))
 fails('unsafe_absolute_path',lambda:checkedpath(repo,'/tmp/escape'));fails('unsafe_parent_path',lambda:checkedpath(repo,'../escape'))
 # Bounded symlink fixture: only the exact source and historical bindings, never a checkout copy.
 with tempfile.TemporaryDirectory(prefix='p6_negative_',dir=HERE) as td:
  fixture=pathlib.Path(td);rels=[b['path'] for b in c['source_bindings'].values() if not pathlib.Path(b['path']).is_absolute()]
  old=load(paths['p6_result'])['manifest'];rels += [b['path'] for b in old['sources']]+[str(relroot(c)/'repair_01'/b['path']) for b in old['outputs']]+[b['path'] for b in load(paths['prior_three_document_manifest'])['files']]
  for rel in set(rels):
   p=fixture/rel;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(repo/rel)
  for name,key in [('wrong_source','04_result'),('unexpected_live_tex','p6_main')]:
   p=fixture/c['source_bindings'][key]['path'];p.unlink();p.write_text('wrong live bytes');fails(name,lambda:validate(c,fixture,out));p.unlink();p.symlink_to(repo/c['source_bindings'][key]['path'])
 return results

def check(c,repo,out,built=False,negative=False):
 paths=validate(c,repo,out);s=support(c,out);data=load(s/'NUMERICAL_SUPPLEMENT.json');semantics(c,paths,data)
 require(load(s/'NUMBER_FIGURE_MAP.json')['numbers']==nums(c,paths),'current number map')
 report=out/relroot(c)/'repair_01/report';original=repo/relroot(c)/'repair_01/report'
 for folder in ['generated','figures']:
  for f in (original/folder).rglob('*'):
   if f.is_file():require(sha(report/folder/f.relative_to(original/folder))==sha(f),'retained candidate support')
 require(sha(report/'references.tex')==c['source_bindings']['p6_references']['sha256'],'immutable bibliography')
 require((s/'appendix.tex').read_text()==appendix(c,paths,(s/'MANUSCRIPT_ADDITIONS.md').read_text()),'exact public text and generated table bytes')
 p=c['publication_plan'];old=paths['p6_main'].read_text();new=(out/relroot(c)/p['main']).read_text();require(new==old.replace(p['insertion_anchor'],p['replacement']),'one appendix invocation preserves original bytes')
 require(new.replace(p['replacement'],p['insertion_anchor'])==old and len(re.findall(r'\\tag\{',old))==35,'all35 original tags and byte recovery')
 for k,name in [('04_joint_figure','JOINT_RESPONSE.pdf'),('04_source_figure','SOURCE_AND_FINITE_Z.pdf')]:require(sha(s/name)==c['source_bindings'][k]['sha256'],'sealed figure')
 result={'cached_semantics':'PASS','old_manifest_resolution':'PASS','original35_tags_and_bytes':'PASS','signed_coordinates':10,'certificate_cases':9,'sealed_figures':2,'production_applied':False,'observed_executor':'UNKNOWN','scientific_admission':False}
 if negative:result['falsifiers']=falsifiers(c,repo,out,paths)
 if built:
  pdf=out/relroot(c)/p['pdf'];log=(s/'build/main.log').read_text();require(not re.search(r'undefined references|Citation .* undefined|Reference .* undefined|LaTeX Error|Overfull \\hbox',log),'new build diagnostics')
  txt=subprocess.run(['pdftotext','-layout',str(pdf),'-'],check=True,capture_output=True,text=True).stdout;require('??' not in txt and 'Joint optical residuals' in txt,'PDF text content')
  result['pdf']={'sha256':sha(pdf),'text_sha256':pdfhash(pdf),'pages':int(re.search(r'Pages:\s+(\d+)',subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True).stdout)[1])};write(HERE/'raw/pdftext.txt',txt)
 dump(HERE/'CHECK_RESULT.json',result);print(json.dumps(result,indent=2));return result

def seal(c,repo,out):
 check(c,repo,out,True,True);s=support(c,out);p=c['publication_plan'];rels=[str(relroot(c)/p[k]) for k in ['main','pdf']]
 dump(s/'EXPECTED_APPLIED.json',{r:sha(out/r) for r in rels});dump(s/'EXPECTED_PDF_TEXT.json',{rels[1]:pdfhash(out/rels[1])})
 files={r:out/r for r in rels};r=str(relroot(c)/p['reader_entry']);files[r]=out/r
 for f in s.rglob('*'):
  if f.is_file() and 'build' not in f.relative_to(s).parts and f.name!='CHECK_RESULT.json' and 'raw' not in f.relative_to(s).parts:files[str(f.relative_to(out))]=f
 entries=[]
 for r,f in sorted(files.items()):
  pre=c['historical_manifest_resolution']['preimages'].get(r);e={'path':r,'preimage_sha256':pre['sha256'] if pre else None,'postimage_sha256':sha(f),'bytes':f.stat().st_size}
  if r==rels[1]:e['pdf_text_sha256']=pdfhash(f)
  entries.append(e)
 dump(out/'OVERLAY_MANIFEST.json',{'schema':'htt.p6_optical_publication_overlay/1','contract_sha256':CONTRACT_SHA,'files':entries,'source_bindings':c['source_bindings'],'actual_agent_id':AUTHOR,'requested_executor':'gpt-6.1-sol/medium','observed_executor':'UNKNOWN','framer_agent':c['author']['agent'],'review':'PENDING_FRESH_INDEPENDENT_ASTRA','production_applied':False,'scientific_admission':False,'original_acceptances_unchanged':True})
 print('SEALED_MANIFEST_SHA256',sha(out/'OVERLAY_MANIFEST.json'))

def apply(manifest,repo,reviewed,reviewreturn):
 require(sha(manifest)==reviewed,'reviewed manifest identity');m=load(manifest);r=load(reviewreturn)
 require(r.get('candidate_identity')=='sha256:'+reviewed and r.get('outcome')=='success' and r.get('acceptance_met') is True and r.get('review_status') in ['PASS_SCOPED_CONDITIONAL','PASS_SCOPED','SCOPED_PASS'],'independent manuscript review binding')
 require(r.get('agent_id') not in [None,AUTHOR,m['framer_agent']],'fresh nonauthor reviewer')
 # Test returns are valid solely within the explicitly named disposable fixture.
 if r.get('fixture_only'):require(str(repo)==r.get('fixture_root') and (repo/'.P6_DISPOSABLE_FIXTURE').is_file(),'test return cannot authorize primary checkout')
 root=manifest.parent;ce=next(x for x in m['files'] if x['path'].endswith('/r36_optical/EDITOR_CONTRACT.json'));cp=checkedpath(root,ce['path']);require(sha(cp)==CONTRACT_SHA,'apply contract identity');c=load(cp)
 allowed=relroot(c);srel=allowed/c['publication_plan']['new_directory'];mutable={str(allowed/c['publication_plan'][x]) for x in ['main','pdf','reader_entry']}
 for b in m['files']:
  rel=pathlib.Path(b['path']);checkedpath(root,str(rel));require(str(rel) in mutable or srel in rel.parents,'P6 allowed overlay path')
 validate(c,repo,root);actions=[]
 for b in m['files']:
  src=checkedpath(root,b['path']);dst=checkedpath(repo,b['path']);require(dst.parent.resolve().is_relative_to(repo),'target parent symlink escape');require(src.is_file() and sha(src)==b['postimage_sha256'],'candidate postimage '+b['path'])
  if dst.exists():
   if sha(dst)==b['postimage_sha256'] or (b.get('pdf_text_sha256') and pdfhash(dst)==b['pdf_text_sha256']):continue
   require(b['preimage_sha256'] is not None and sha(dst)==b['preimage_sha256'],'unexpected live overlay mutation '+b['path'])
  else:require(b['preimage_sha256'] is None,'missing preimage')
  actions.append((src,dst))
 for src,dst in actions:
  # Break fixture symlinks rather than following them into the real checkout.
  if dst.is_symlink():dst.unlink()
  copyfile(src,dst)
 result={'changed_targets':len(actions),'manifest_sha256':reviewed};print(json.dumps(result));return result

def main():
 parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
 for action in ['assemble','check','seal']:
  p=sub.add_parser(action);p.add_argument('--contract',type=pathlib.Path,required=True);p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--output-root',type=pathlib.Path,required=True)
  if action=='check':p.add_argument('--built-pdfs',action='store_true');p.add_argument('--falsifiers',action='store_true')
 p=sub.add_parser('apply');p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--reviewed-manifest-sha256',required=True);p.add_argument('--review-return',type=pathlib.Path,required=True)
 a=parser.parse_args()
 if a.action=='apply':apply(a.manifest.resolve(),a.repo.resolve(),a.reviewed_manifest_sha256,a.review_return.resolve());return
 require(sha(a.contract)==CONTRACT_SHA,'frozen contract identity');c=load(a.contract);repo=a.repo.resolve();out=a.output_root.resolve()
 if a.action=='assemble':assemble(c,repo,out,a.contract.resolve())
 elif a.action=='check':check(c,repo,out,a.built_pdfs,a.falsifiers)
 else:seal(c,repo,out)
if __name__=='__main__':main()
