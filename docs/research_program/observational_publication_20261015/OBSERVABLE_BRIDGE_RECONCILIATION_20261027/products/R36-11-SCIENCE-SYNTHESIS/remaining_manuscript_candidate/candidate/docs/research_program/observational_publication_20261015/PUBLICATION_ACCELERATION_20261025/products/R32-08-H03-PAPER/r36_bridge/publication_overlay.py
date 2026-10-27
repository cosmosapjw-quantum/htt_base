#!/usr/bin/env python3
"""Cached manuscript assembly only; no producer, refit, random sampling or solver."""
import argparse, copy, csv, hashlib, io, json, pathlib, re, shutil, subprocess, sys, tempfile
import numpy as np
HERE=pathlib.Path(__file__).resolve().parent
CONTRACT_SHA='a1f4f3e6508c2b1e69af9deb619977de4f45bb48ca07ea15822f3087a07db783'
PROSE_SHA='354aafea8eb84a21ae9923d680048115cd6d18ce0adacf43c11ff09f96d6c8c3'
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,j): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
def require(ok,label):
 if not ok: raise ValueError(label)
def pointer(obj,p):
 for x in p.strip('/').split('/'):obj=obj[int(x)] if isinstance(obj,list) else obj[x]
 return obj

def pdftextsha(p):
 text=subprocess.run(['pdftotext','-layout',str(p),'-'],capture_output=True,check=True).stdout
 return hashlib.sha256(text).hexdigest()

def support(c,out):return out/c['publication_plan'][0]['root']/'r36_bridge'
def expected(c,out):
 p=support(c,out)/'EXPECTED_APPLIED.json'
 return json.loads(p.read_text()) if p.exists() else {}
def validate(c,repo,out):
 base=support(c,out)/'baseline'; post=expected(c,out)
 textfile=support(c,out)/'EXPECTED_PDF_TEXT.json'; pdftexts=json.loads(textfile.read_text()) if textfile.exists() else {}
 def resolve(rel,b):
  p=repo/rel
  if p.is_file() and sha(p)==b['sha256']:return p
  q=base/rel
  require(q.is_file() and sha(q)==b['sha256'],'immutable source identity '+rel)
  require(p.is_file() and (sha(p)==post.get(rel) or (p.suffix=='.pdf' and rel in pdftexts and pdftextsha(p)==pdftexts[rel])),'unexpected live overlay mutation '+rel)
  return q
 paths={k:resolve(b['repo_relative_path'],b) for k,b in c['source_bindings'].items()}
 for rel,b in c['production_preimages_and_retained_artifacts'].items():
  if b['mutable_in_overlay']:resolve(rel,b)
  else:require((repo/rel).is_file() and sha(repo/rel)==b['sha256'],'retained science '+rel)
 for k,q in c['qualified_inputs'].items():
  status=json.loads(paths[q['qualification_source']].read_text());formal=json.loads(paths[q['formal_return']].read_text())
  require(q['candidate_identity'].split(':')[-1] in json.dumps(status) and q['candidate_identity'].split(':')[-1] in json.dumps(formal),'qualification identity '+k)
 return paths

def load(paths,key):return json.loads(paths[key].read_text())
def matches(v,target):
 if isinstance(target,dict):return all(k in v and matches(v[k],x) for k,x in target.items() if k != "retain_full_left_right_and_null")
 if isinstance(target,list):return len(v)==len(target) and all(matches(a,b) for a,b in zip(v,target))
 return v==target

def numbers(c,paths):
 result={}
 for n in c['number_table']:
  if n['locator'].startswith('NPZ'):continue
  v=pointer(load(paths,n['source']),n['locator']);target=n['value']
  if isinstance(target,dict) and target.get('retain_all_values_from_source'):
   require(np.shape(v)==tuple(target['shape']),'numeric shape '+n['id'])
  else:require(matches(v,target),'numeric locator '+n['id'])
  result[n['id']]={'source':n['source'],'locator':n['locator'],'value':v,'scope':n['scope']}
 return result

def semantics(paths, data=None):
 j=data or {k:load(paths,k) for k in ['01_result','02_result','02_sensitivity','08_result','05_result','10_table']}
 m=np.load(paths['02_matrices']);sub=np.load(paths['02_subset_matrices'])
 for key in ['band1','band2','pv_total']:require(m[key].shape==(108,108),'CF4 full108 scope')
 require(m['conditional_R5'].shape==(36,36) and m['baseline'].shape==(36,36),'CF4 total36 scope')
 require(np.allclose(m['band1']+m['band2'],m['pv_total'],rtol=0,atol=1e-12),'CF4 summed band matrices')
 for name,v in j['02_sensitivity']['results'].items():
  for a,b in enumerate(v['bands_sum_blocks']):
   sl=slice(a*36,(a+1)*36)
   require(abs(np.trace(sub[name][sl,sl])/np.trace(m['pv_total'][sl,sl])-b['trace_ratio_to_full_sample'])<1e-12,'stale CF4 same-radius denominator')
 op=j['01_result']; require(op['operator_shape']==[36,35970],'CF4 operator')
 require(op['source_bulk_response']=='+AN' and op['observer_velocity_response']=='-AN' and np.shape(op['AN_36x3_inverse_Mpc'])==(36,3),'signed source observer coordinates')
 sn=j['08_result']
 for name,N in [('primary',490),('lower_z_sensitivity',705)]:
  v=sn[name];require(v['n_low']+v['n_high']==N and v['fits']['full']['rank']==16,'SN support/rank')
  C=np.array(v['full_16x16_covariance_mag2']);Cdiff=np.array(v['high_minus_low_8x8_covariance_mag2'])
  require(C.shape==(16,16) and Cdiff.shape==(8,8) and np.any(C[:8,8:]!=0),'missing SN cross block')
  require(np.allclose(Cdiff,C[:8,:8]+C[8:,8:]-C[:8,8:]-C[8:,:8],rtol=1e-12,atol=1e-14),'SN contrast covariance')
  require(np.array_equal(np.array(v['high_8_mag'])-v['low_8_mag'],v['high_minus_low_8_mag']),'signed coordinate swap')
  require(v['covariance']['max_symmetry_residual']==0 and v['covariance']['min_eigenvalue_mag2']>0,'SN selected covariance')
 geo=j['10_table'];names=['II','VII0matched','I','flatVII0']
 require([geo['images'][k]['geometry_svd']['rank'] for k in names]==[6,6,0,3],'obsolete geometry rank')
 require([geo['images'][k]['joint_svd']['rank'] for k in names]==[9,10,1,6],'obsolete joint-image rank')
 for k in names:
  v=geo['images'][k];require(np.shape(v['joint_J'])==(10,12) and np.shape(v['joint_H'])==(10,12,12),'full geometry derivatives')
 for k in ['I','flatVII0']:require(not np.any(geo['controls'][k]['S_bar']),'obsolete nonzero flat shear')
 require(len(paths['10_lrs'].read_text().splitlines())==280,'retained LRS280')
 require(round(np.linalg.det([[0,0,1],[1,0,0],[0,1,0]]))==1,'proper cyclic frame')
 rad=j['05_result'];require(len(rad['methods'])==12,'radiation12 entries')
 samples=np.load(paths['05_samples'])
 for v in rad['methods']:
  require(v['calibration_N']==8191 and v['test_N']==4096,'radiation finite sample counts')
  require(np.shape(v['fP_covariance'])==(8,8) and np.any(np.array(v['fP_covariance'])[:3,3:]!=0),'radiation flux stress cross block')
  require('count' in v['A_nonempty_width'] and 'calibration_content' in v,'omitted empty denominator or finite-MC caveat')
  prefix=v['case']+'_'+v['method']
  for target in ['D','A']:
   require(int(np.sum(samples[prefix+'_test_'+target+'_physical_hit']))==v[target+'_physical_target_coverage']['hits'],'radiation saved hit recount')
  widths=samples[prefix+'_test_A_width'];require(np.count_nonzero(np.isfinite(widths))==v['A_nonempty_width']['count'],'radiation empty width denominator')
 for v in rad['response_compression']['L2_L4']:require(np.shape(v['response_matrix_over_rho0'])==(5,5),'radiation full response')
 return j

def esc(s):return str(s).replace('_',r'\_').replace('%',r'\%')
def table(caption,headers,rows,label):
 return '\n\\begin{table}[htbp]\n\\centering\\small\n\\caption{'+caption+'}\\label{'+label+'}\n\\begin{tabular}{'+'l'*len(headers)+'}\n\\toprule\n'+' & '.join(headers)+r' \\'+'\n\\midrule\n'+'\n'.join(' & '.join(str(x) for x in row)+r' \\' for row in rows)+'\n\\bottomrule\n\\end{tabular}\n\\end{table}\n'
def generated(paths,j):
 m=np.load(paths['02_matrices']);t={}
 rows=[]
 for b in csv.DictReader(io.StringIO(paths['02_tables'].read_text())):
  a=[5,10,20].index(int(b['R_hinv_Mpc']));sl=slice(36*a,36*(a+1));require(f"{np.trace(m['band'+b['band']][sl,sl]):.8f}"==f"{float(b['trace_36']):.8f}",'CF4 rendered table-matrix parity')
  rows.append([b['band'],b['R_hinv_Mpc'],f"{float(b['trace_36']):.8f}"])
 for label,key in [('Combined PV','pv_total'),('Inherited working','baseline'),('Stipulated total','conditional_R5')]:rows.append([label,'5',f'{np.trace(m[key][:36,:36]):.8f}'])
 t['CF4-COV']=table(r'Propagated covariance traces in $(\mathrm{km/s/Mpc})^2$. Each band/radius row is its 36-coordinate block; inherited working covariance is separate from the stipulated total.',['Component',r'$R\;(h^{-1}\mathrm{Mpc})$','Trace'],rows,'tab:cf4cov')
 rows=[]
 for name,v in j['02_sensitivity']['results'].items():rows.append([esc(name),str(v['selected_rows'])]+[f"{b['trace_ratio_to_full_sample']:.6f}" for b in v['bands_sum_blocks']])
 t['CF4-FOOTPRINT']=table('PV trace ratios relative to the full sample at the same radius. Subsets overlap.',['Subset','Groups',r'$R=5$',r'$R=10$',r'$R=20$'],rows,'tab:footprint')
 rows=[];signed=[]
 for key,label in [('primary','Primary'),('lower_z_sensitivity','Lower redshift')]:
  v=j['08_result'][key];f=v['fits'];rows.append([label,f"{v['n_low']}/{v['n_high']}"]+[f'{x:.6f}' for x in [f['null']['T'],f['dipole']['T_full'],f['full']['T_full'],f['full']['delta_T'],f['full']['p_chi2_conditional']]])
  for i in range(8):signed.append([label,str(i+1)]+[f'{v[k][i]:+.6f}' for k in ['low_8_mag','high_8_mag','high_minus_low_8_mag']])
 t['SN-FIT']=table('Selected released-magnitude Gaussian comparisons; the total covariance is used once.',['Cohort','Low/high',r'$T_0$',r'$T_{\rm dip}$',r'$T_1$',r'$\Delta T$',r'$p$'],rows,'tab:snfit')+table(r'All signed angular coordinates in mag, ordered $(d_x,d_y,d_z,q_1,\ldots,q_5)$. Full covariance matrices accompany the numerical supplement.',['Cohort','Coordinate','Low','High','High minus low'],signed,'tab:signed')
 rows=[];g=j['10_table']
 for k in ['II','VII0matched','I','flatVII0']:
  v=g['controls'][k];im=g['images'][k];diag=lambda x:'('+','.join(f'{x[i][i]:g}' for i in range(3))+')'
  rows.append([esc(k),diag(v['n_bar']),f"{v['h_bar']:g}",diag(v['S_bar']),f"{v['density_bar']:.4f}",'('+','.join(f'{x:g}' for x in v['mom_bar'])+')',str(im['geometry_svd']['rank']),str(im['joint_svd']['rank'])])
 t['GEO-CENTERS']=table(r'Center coordinates normalized by $u_*$ for $n,h,S$ and $u_*^2$ for $\kappa_g\varepsilon_N,\kappa_gq$. Diagonal tuples display the complete diagonal center tensors; all off-diagonal entries and $a$ vanish. Ranks refer to geometry and joint maps.',['Center',r'$\mathrm{diag}\,n$',r'$h$',r'$\mathrm{diag}\,S$',r'$\kappa_g\varepsilon_N$',r'$\kappa_gq$','Geom.','Joint'],rows,'tab:geo')
 rows=[];width=[]
 for v in j['05_result']['methods']:
  cov=lambda k: f"{v[k]['hits']}/{v[k]['N']} [{v[k]['lower']:.4f},{v[k]['upper']:.4f}]"
  rows.append([esc(v['case']),v['method'],cov('D_physical_target_coverage'),cov('A_physical_target_coverage')])
  width.append([esc(v['case']),v['method'],f"{v['D_width']*1e6:.6f}",f"{v['A_empty_fraction']:.6f}",str(v['A_nonempty_width']['count']),f"{v['A_nonempty_width']['mean']*1e6:.6f}"])
 t['RAD-COVERAGE']=table(r'Physical-target hit counts and finite-test 95-percent Clopper--Pearson intervals. $N=4096$ for every row. Calibration uses 8191 separate draws; calibration-content uncertainty is distinct from these test intervals.',['Case','Method',r'$\mathscr D$ hits/N [interval]',r'$\mathcal A_\gamma$ hits/N [interval]'],rows,'tab:radcoverage')
 t['RAD-WIDTH']=table(r'Dimensionless widths displayed in units of $10^{-6}$. Empty scalar intervals count as noncoverage; only the explicitly counted nonempty intervals enter their mean.',['Case','Method',r'Ball diameter $/10^{-6}$','Empty fraction',r'$N_{\rm nonempty}$',r'Mean width $/10^{-6}$'],width,'tab:radwidth')
 rows=[];eigs=[]
 for v in j['05_result']['response_compression']['L2_L4']:
  rows.append([str(v['nmu']),str(v['L']),f"{v['operator_error_over_rho0']:.8g}",f"{v['entropy_difference_over_Siso']:.8g}"])
  if v['L']==4:eigs.append([str(v['nmu'])]+[f'{x:.10f}' for x in v['response_eigenvalues_over_rho0']])
 t['RAD-RESPONSE']=table(r'Both retained angular quadratures and response errors normalized by $\rho_0$; entropy residuals use the isotropic entropy normalization.',['Quadrature','Rank','Operator error','Entropy residual'],rows,'tab:radresponse')+table(r'All five rank-four response eigenvalues divided by $\rho_0$. Full matrices accompany the numerical supplement.',['Quadrature',r'$\lambda_1$',r'$\lambda_2$',r'$\lambda_3$',r'$\lambda_4$',r'$\lambda_5$'],eigs,'tab:radeigen')
 return t

def convert(s):
 s=s.replace('–','--').replace('—','---').replace('−','-').replace('’',"'")
 # Typography normalization only: source markdown has one lost backslash tab and one comma before dOmega.
 s=s.replace('\tfrac',r'\tfrac').replace(')^2],d\\Omega',')^2]\\,d\\Omega')
 converted=subprocess.run(['pandoc','-f','markdown+raw_tex+tex_math_single_backslash','-t','latex'],input=s,text=True,capture_output=True,check=True).stdout
 converted=re.sub(r'(\{\[\}[^\n]*?),(?=[0-9])',lambda m:m[1]+r',\allowbreak ',converted)
 return re.sub(r'\\hypertarget\{[^}]*\}\{%\n(\\section\{.*?\}\\label\{[^}]*\})\}',lambda m:m[1],converted,flags=re.S)

def blocks(prose):
 return re.findall(r'^\*\*Manuscript text\*\*\s*$(.*?)^\*\*End manuscript text\*\*\s*$',prose,re.S|re.M)

def sections(prose,t):
 b=blocks(prose);require(len(b)==9,'nine frozen author blocks')
 for i,s in enumerate(b):
  def directive(m):
   body=m[0]
   if body.startswith('[Generate'):
    key=next((k for k in t if k in body),None);require(key is not None,'table directive')
    return t[key]+(t['RAD-WIDTH'] if key=='RAD-COVERAGE' else '')
   return body
  s=re.sub(r'\[Generate .*?\]',directive,s,flags=re.S)
  def figure(m):
   body=m[0];k=next(k for k in ['CF4 FIGURE.png','PUBLIC_SN_SIGNED_COORDINATES.pdf','GEOMETRY_IMAGE.pdf','comparison.pdf'] if k in body)
   file={'CF4 FIGURE.png':'cf4_correlation.png','PUBLIC_SN_SIGNED_COORDINATES.pdf':'sn_signed.pdf','GEOMETRY_IMAGE.pdf':'geometry_image.pdf','comparison.pdf':'comparison.pdf'}[k]
   prefix='r36_bridge/' if i in [1,2] else 'r36_geometry/' if i==4 else ''
   cap=body.split('Caption:',1)[1].rstrip(']').strip();cap=esc(cap).replace('h^{-1}',r'$h^{-1}$')
   return '\n\\begin{figure}[htbp]\n\\centering\n\\includegraphics[width=0.95\\linewidth]{'+prefix+file+'}\n\\caption{'+cap+'}\n\\end{figure}\n'
  s=re.sub(r'\[Include sealed .*?\]',figure,s,flags=re.S)
  require('[Generate ' not in s and '[Include sealed' not in s,'unexpanded editorial directive')
  b[i]=convert(s)
 return b

def baseline(c,repo,out):
 base=support(c,out)/'baseline'
 for rel,b in c['production_preimages_and_retained_artifacts'].items():
  if b['mutable_in_overlay']:
   p=base/rel
   if not p.exists():
    require(sha(repo/rel)==b['sha256'],'initial baseline identity');p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(repo/rel,p)
 return base

def assemble(c,repo,out):
 require(not (out==repo and not (support(c,out)/'EXPECTED_APPLIED.json').exists()),'production assemble requires reviewed installed overlay')
 paths=validate(c,repo,out);j=semantics(paths);num=numbers(c,paths);t=generated(paths,j)
 base=baseline(c,repo,out);h,p,r=[out/x['root'] for x in c['publication_plan']];hrel,prel,rrel=[x['root'] for x in c['publication_plan']]
 # Copy only bounded original document support, not a checkout or producer tree.
 for rel,b in c['production_preimages_and_retained_artifacts'].items():
  if rel.startswith(tuple([hrel+'/',prel+'/',rrel+'/'])) and not b['mutable_in_overlay']:
   dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   if dest.resolve()!=(repo/rel).resolve():shutil.copyfile(repo/rel,dest)
 # Retain all directly referenced TeX figure/generated support and bibliography, never execute old generators.
 for plan in c['publication_plan'][:2]:
  src=repo/plan['root'];dst=out/plan['root']
  for folder in ['figures','generated'] if plan['key']=='H03' else ['report/figures']:
   for f in (src/folder).glob('*'):
    if f.is_file():
     q=dst/folder/f.name;q.parent.mkdir(parents=True,exist_ok=True)
     if q.resolve()!=f.resolve():shutil.copyfile(f,q)
  for filename in ['references.bib'] if plan['key']=='H03' else []:
   q=dst/filename
   if not q.exists():shutil.copyfile(src/filename,q)
 s=support(c,out);s.mkdir(parents=True,exist_ok=True)
 contractpath=s/'EDITOR_CONTRACT.json'
 # Preserve exact contract serialization, since hash is an immutable source identity.
 shutil.copyfile(ARGS.contract,contractpath) if ARGS.contract.resolve()!=contractpath.resolve() else None
 prosepath=s/'MANUSCRIPT_ADDITIONS.md'
 srcprose=HERE/'MANUSCRIPT_ADDITIONS.md'
 require(srcprose.exists() and sha(srcprose)==PROSE_SHA,'frozen author prose identity')
 if srcprose.resolve()!=prosepath.resolve():shutil.copyfile(srcprose,prosepath)
 if pathlib.Path(__file__).resolve()!=(s/'publication_overlay.py').resolve():shutil.copyfile(__file__,s/'publication_overlay.py')
 for key,folder,name in [('02_figure',s,'cf4_correlation.png'),('08_figure',s,'sn_signed.pdf'),('10_figure',p/'report/r36_geometry','geometry_image.pdf'),('05_figure',r/'radiation_supplement','comparison.pdf')]:
  folder.mkdir(parents=True,exist_ok=True);shutil.copyfile(paths[key],folder/name)
 b=sections(prosepath.read_text(),t)
 tex=(base/hrel/'main.tex').read_text();tex=tex.replace(r'\end{abstract}',b[0]+'\n'+r'\end{abstract}')
 old='The experiment here consumes only the saved statistics.';require(tex.count(old)==1,'original carrier sentence')
 tex=tex.replace(old,'The original finite-window sensitivity experiment below consumes the saved statistics; the later covariance and supernova sections consume separate retained response products.')
 tex=tex.replace(r'\section{Interpretation and required physical input}',r'\input{r36_bridge/velocity.tex}'+'\n'+r'\input{r36_bridge/supernova.tex}'+'\n'+r'\section{Interpretation and required physical input}')
 tex=tex.replace(r'\section{Reproduction from retained statistics}',b[3]+'\n'+r'\section{Reproduction from retained statistics}')
 tex=tex.replace(r'\usepackage{amsmath,amssymb,graphicx,booktabs}',r'\usepackage{amsmath,amssymb,mathrsfs,graphicx,booktabs}')
 write(h/'main.tex',tex)
 write(s/'velocity.tex',r'\section{Correlated velocity uncertainty through a fixed survey estimator}'+'\n'+b[1])
 write(s/'supernova.tex',r'\section{A released-magnitude angular comparison in two depth bins}'+'\n'+b[2])
 tex=(base/prel/'report/manuscript.tex').read_text();marker=r'\hypertarget{sources-and-reproducibility}{%';require(marker in tex,'P5 insertion marker')
 tex=tex.replace(r'\usepackage{amsmath,amssymb,graphicx,hyperref}',r'\usepackage{amsmath,amssymb,graphicx,hyperref,booktabs}');tex=tex.replace(marker,r'\input{r36_geometry/appendix.tex}'+'\n\n'+marker);write(p/'report/manuscript.tex',tex)
 appendix=r'\section*{Appendix: A spatial-curvature tensor distinguishes equal-scalar initial data}'+'\n'+b[4]
 # Number only new appendix equations A1 onward, preserving all old explicit tags.
 counter=[0]
 def tag(m):counter[0]+=1;return '\\begin{equation}\n'+m[1].strip()+r'\tag{A'+str(counter[0])+'}\n\\end{equation}'
 appendix=re.sub(r'\\\[(.*?)\\\]',tag,appendix,flags=re.S)
 write(p/'report/r36_geometry/appendix.tex',appendix)
 title=re.search(r'\\section\{(.*?)\}',b[5],re.S)[1];abstract=re.sub(r'^\\section\{.*?\}\s*(?:\\label\{.*?\})?','',b[5],count=1,flags=re.S).strip()
 rad=r'''\documentclass[aps,prd,reprint,onecolumn,nofootinbib]{revtex4-2}
\usepackage{amsmath,amssymb,mathrsfs,graphicx,booktabs}
\usepackage[T1]{fontenc}
\begin{document}
\title{'''+title+r'''}
\author{Anonymous research draft}\noaffiliation
\date{27 October 2026}
\begin{abstract}
'''+abstract+'\n'+r'\end{abstract}\maketitle'+'\n'
 for title,txt in zip(['Physical moments and two common-input adapters','Conditional calibration, coverage and widths','The moments needed for the target response'],b[6:]):rad+=r'\section{'+title+'}\n'+txt
 rad+='\n'+r'\begin{thebibliography}{1}'+'\n'+r'\bibitem{source} The source-bound numerical supplement distributed with this manuscript retains the complete moment matrices, common-input comparison statistics and qualification limitations.'+'\n'+r'\end{thebibliography}\end{document}'+'\n'
 write(r/'radiation_supplement/main.tex',rad)
 for rel,directory in [(hrel,s),(rrel,r/'radiation_supplement')]:
  old=(base/rel/'README.md').read_text();add='\n\nCurrent source-bound manuscript entrypoint: '+('`r36_bridge/publication_overlay.py` (assemble/check with the installed `EDITOR_CONTRACT.json`). The retained original experiment, numerical assets and manifests keep their original scope; the added covariance and magnitude sections consume separate qualified cached products.' if rel==hrel else '`radiation_supplement/main.tex`, a separate companion bolometric radiation methods calculation. It uses positive complete-sky synthetic radiation inputs and does not extend the parent finite-bandpass foreground class or supply measured foreground budgets.')+'\n';write(out/rel/'README.md',old+add)
 dump(s/'NUMBER_FIGURE_MAP.json',{'numbers':num,'figures':{k:c['source_bindings'][k] for k in ['02_figure','08_figure','05_figure','10_figure']}})
 dump(s/'NUMERICAL_SUPPLEMENT.json',{'01_operator_result':j['01_result'],'02_result':j['02_result'],'02_sensitivity':j['02_sensitivity'],'08_full_result':j['08_result'],'05_full_result':j['05_result'],'10_full_table':j['10_table'],'full_matrices':{k:c['source_bindings'][k] for k in ['02_matrices','02_subset_matrices','05_samples','10_probes','10_lrs']},'source_scope':'Exact bound cached products; no new likelihood, fit, draws or evolved solution.'})
 for folder,description in [(s,'CF4 covariance and separate released-magnitude comparator'),(p/'report/r36_geometry','Full initial-data tensor image, Jacobian, Hessian and deterministic bounds'),(r/'radiation_supplement','Positive bolometric stress and response methods')]:
  write(folder/'README.md',description+'\n\nThe common installed current consumer is H03/r36_bridge/publication_overlay.py. Run assemble/check with its EDITOR_CONTRACT.json, --repo and --output-root. No historical producer or original complete-output validator is invoked on the revised documents. Source hashes and qualification receipts remain frozen. Full numerical objects and exact locators are in H03/r36_bridge/NUMERICAL_SUPPLEMENT.json and NUMBER_FIGURE_MAP.json. New scientific admission and production application remain pending fresh independent review.\n')
 print('ASSEMBLED: cached statistics, exact frozen sources, original scientific support retained')

def falsifiers(paths,j):
 results=[]
 def trial(label,mutate):
  bad=copy.deepcopy(j);mutate(bad)
  try:semantics(paths,bad)
  except (ValueError,KeyError,AssertionError) as e:results.append({'fixture':label,'rejected':True,'reason':str(e)})
  else:raise ValueError('falsifier accepted '+label)
 trial('stale02_R10_R20_denominator',lambda x:x['02_sensitivity']['results']['exclude_FP']['bands_sum_blocks'][1].update(trace_ratio_to_full_sample=1.0))
 trial('obsolete10_typeI_rank3',lambda x:x['10_table']['images']['I']['joint_svd'].update(rank=3))
 trial('obsolete10_nonzero_flatS',lambda x:x['10_table']['controls']['I']['S_bar'][0].__setitem__(0,0.1))
 trial('missing_SN_crossblock',lambda x:x['08_result']['primary'].__setitem__('full_16x16_covariance_mag2',np.diag(np.diag(x['08_result']['primary']['full_16x16_covariance_mag2'])).tolist()))
 trial('radiation_omitted_nonempty_count',lambda x:x['05_result']['methods'][0]['A_nonempty_width'].pop('count'))
 trial('radiation_omitted_finite_MC',lambda x:x['05_result']['methods'][0].pop('calibration_content'))
 trial('signed_coordinate_swap',lambda x:x['08_result']['primary']['low_8_mag'].reverse())
 # Exercise the actual resolver on a small symlink-backed fixture; no source mutation.
 with tempfile.TemporaryDirectory(prefix='r36-formatter-') as scratch:
  fixture=pathlib.Path(scratch)
  c=json.loads(ARGS.contract.read_text())
  bindings={b['repo_relative_path']:b for b in c['source_bindings'].values()}
  bindings.update(c['production_preimages_and_retained_artifacts'])
  for rel in bindings:
   p=fixture/rel;p.parent.mkdir(parents=True,exist_ok=True);p.symlink_to(ARGS.repo.resolve()/rel)
  for label,rel in [('source_hash_drift',c['source_bindings']['02_result']['repo_relative_path']),('figure_hash_drift',c['source_bindings']['10_figure']['repo_relative_path']),('unexpected_live_overlay_mutation',c['publication_plan'][0]['root']+'/main.tex')]:
   p=fixture/rel;p.unlink();p.write_bytes(b'mutated fixture')
   try:validate(c,fixture,ARGS.output_root.resolve())
   except ValueError as e:results.append({'fixture':label,'rejected':True,'reason':str(e)})
   else:raise ValueError('falsifier accepted '+label)
   p.unlink();p.symlink_to(ARGS.repo.resolve()/rel)
 return results

def check(c,repo,out,built=False,negative=False):
 paths=validate(c,repo,out);j=semantics(paths);num=numbers(c,paths);s=support(c,out)
 require(json.loads((s/'NUMBER_FIGURE_MAP.json').read_text())['numbers']==num,'current numeric source map')
 t=generated(paths,j); b=sections((s/'MANUSCRIPT_ADDITIONS.md').read_text(),t)
 expected_fragments=[(s/'velocity.tex',b[1]),(s/'supernova.tex',b[2])]
 for file,text in expected_fragments:require(text in file.read_text(),'rendered exact generated fragment '+str(file))
 p=out/c['publication_plan'][1]['root'];r=out/c['publication_plan'][2]['root']
 for key in ['GEO-CENTERS']:require(t[key] in (p/'report/r36_geometry/appendix.tex').read_text(),'geometry table bytes')
 for key in ['RAD-COVERAGE','RAD-WIDTH','RAD-RESPONSE']:require(t[key] in (r/'radiation_supplement/main.tex').read_text(),'radiation table bytes')
 for plan in c['publication_plan'][:2]:
  rel=plan['root']+'/'+plan['main'];old=(s/'baseline'/rel).read_text();new=(out/rel).read_text()
  # Every old equation, generated input and figure invocation remains byte-identical.
  patterns=[r'\\\[.*?\\\]',r'\\begin\{equation\}.*?\\end\{equation\}',r'\\begin\{align\*?\}.*?\\end\{align\*?\}',r'\\includegraphics(?:\[.*?\])?\{.*?\}',r'\\input\{generated/.*?\}']
  for pat in patterns:
   for unit in re.findall(pat,old,re.S):require(unit in new,'retained original equation/figure '+rel)
 figures=[('02_figure',s/'cf4_correlation.png'),('08_figure',s/'sn_signed.pdf'),('10_figure',p/'report/r36_geometry/geometry_image.pdf'),('05_figure',r/'radiation_supplement/comparison.pdf')]
 for k,d in figures:require(sha(d)==c['source_bindings'][k]['sha256'],'sealed figure '+k)
 rawsections='\n'.join([b[i] for i in [1,2,4,6,7,8]])
 require(not re.search(r'R36-|gpt-|42/42|Astra|campaign|runtime',rawsections),'internal prose in new physics')
 result={'source_bindings':82,'preimages_and_retained_artifacts':64,'number_locators':len(num),'sealed_figures':4,'cached_semantics':'PASS','old_equations_and_scientific_support':'PASS','new_scientific_acceptance':False,'production_applied':False}
 if negative:result['falsifiers']=falsifiers(paths,j)
 if built:
  pdfs=[]
  for plan in c['publication_plan']:
   pdf=out/plan['root']/plan['output'];require(pdf.is_file(),'missing PDF '+str(pdf));text=subprocess.run(['pdftotext','-layout',str(pdf),'-'],capture_output=True,text=True,check=True).stdout
   require(len(text)>1000 and '??' not in text,'PDF text unresolved reference')
   logfile=(out/plan['root']/plan['main']).with_suffix('.log');log=logfile.read_text()
   require(not re.search(r'undefined references|Citation .* undefined|Reference .* undefined|LaTeX Error|Overfull \\hbox',log),'TeX diagnostics '+plan['key'])
   pdfs.append({'document':plan['key'],'pdf':str(pdf.relative_to(out)),'pdf_sha256':sha(pdf),'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'pages':int(re.search(r'Pages:\s+(\d+)',subprocess.run(['pdfinfo',str(pdf)],capture_output=True,text=True,check=True).stdout)[1])})
   write(HERE/'raw'/('pdftext_'+plan['key']+'.txt'),text)
  result['compiled_pdfs']=pdfs
 dump(HERE/'CHECK_RESULT.json',result);print(json.dumps(result,indent=2))

def seal(c,repo,out):
 check(c,repo,out,True,True);s=support(c,out)
 post={}
 for plan in c['publication_plan']:
  for name in plan['allowed_existing_changes']:
   p=out/plan['root']/name
   if p.exists():post[str(p.relative_to(out))]=sha(p)
  p=out/plan['root']/plan['output'];post[str(p.relative_to(out))]=sha(p)
 dump(s/'EXPECTED_APPLIED.json',post)
 dump(s/'EXPECTED_PDF_TEXT.json',{plan['root']+'/'+plan['output']:pdftextsha(out/plan['root']/plan['output']) for plan in c['publication_plan']})
 files={}
 for plan in c['publication_plan']:
  root=out/plan['root'];allowed=list(plan['allowed_existing_changes'])
  for name in allowed:
   p=root/name
   if p.exists():files[str(p.relative_to(out))]=p
  for p in (root/plan['new_directory']).rglob('*'):
   if p.is_file() and p.suffix not in ['.aux','.log','.out','.fls','.fdb_latexmk','.blg','.bbl','.synctex']:files[str(p.relative_to(out))]=p
 entries=[]
 for rel,p in sorted(files.items()):
  old=c['production_preimages_and_retained_artifacts'].get(rel)
  entry={'path':rel,'preimage_sha256':old['sha256'] if old else None,'postimage_sha256':sha(p),'bytes':p.stat().st_size,'role':'mutable_manuscript' if old else 'new_current_consumer_support'}
  if rel in [x['root']+'/'+x['output'] for x in c['publication_plan']]:entry['pdf_text_sha256']=pdftextsha(p)
  entries.append(entry)
 manifest={'schema':'htt.bounded_publication_overlay/1','work':'existing R36-11 remaining manuscript revision','contract_sha256':CONTRACT_SHA,'acceptance':False,'review':'PENDING_FRESH_INDEPENDENT_ASTRA','requested_executor':'gpt-6.1-sol/medium','observed_executor':'UNKNOWN','framer_agent':c['author']['agent'],'framer_requested_runtime':c['author']['requested_runtime'],'framer_observed_runtime':'UNKNOWN','files':entries,'source_bindings':c['source_bindings'],'original_acceptances':'17/42 unchanged; analytic alternate18/42 separate','production_application':False}
 dump(out/'OVERLAY_MANIFEST.json',manifest);print('SEALED_MANIFEST_SHA256',sha(out/'OVERLAY_MANIFEST.json'))

def apply(manifest,repo,reviewed_sha):
 require(sha(manifest)==reviewed_sha,'reviewed manifest identity')
 m=json.loads(manifest.read_text());root=manifest.parent;actions=[]
 contract_entry=next(b for b in m['files'] if b['path'].endswith('/r36_bridge/EDITOR_CONTRACT.json'));cp=root/contract_entry['path'];require(sha(cp)==m['contract_sha256'],'apply frozen contract');validate(json.loads(cp.read_text()),repo,root)
 # Full preflight precedes every mutation; repeated exact application is a no-op.
 for b in m['files']:
  rel=pathlib.Path(b['path']);require(not rel.is_absolute() and '..' not in rel.parts,'unsafe manifest path')
  src=root/rel;dst=repo/rel;require(src.is_file() and sha(src)==b['postimage_sha256'],'candidate postimage '+str(rel))
  if dst.exists():
   h=sha(dst)
   if h==b['postimage_sha256']:continue
   if b.get('pdf_text_sha256') and pdftextsha(dst)==b['pdf_text_sha256']:continue
   require(b['preimage_sha256'] is not None and h==b['preimage_sha256'],'unexpected live overlay mutation '+str(rel))
  else:require(b['preimage_sha256'] is None,'missing required preimage '+str(rel))
  actions.append((src,dst))
 for src,dst in actions:dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 print(json.dumps({'changed_targets':len(actions),'manifest_sha256':reviewed_sha,'repo':str(repo)}))

parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
for action in ['assemble','check','seal']:
 p=sub.add_parser(action);p.add_argument('--contract',type=pathlib.Path,required=True);p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--output-root',type=pathlib.Path,required=True)
 if action=='check':p.add_argument('--falsifiers',action='store_true');p.add_argument('--built-pdfs',action='store_true')
p=sub.add_parser('apply');p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--repo',type=pathlib.Path,required=True);p.add_argument('--reviewed-manifest-sha256',required=True)
ARGS=parser.parse_args()
if ARGS.action=='apply':apply(ARGS.manifest.resolve(),ARGS.repo.resolve(),ARGS.reviewed_manifest_sha256)
else:
 require(sha(ARGS.contract)==CONTRACT_SHA,'frozen editor contract identity');c=json.loads(ARGS.contract.read_text());repo=ARGS.repo.resolve();out=ARGS.output_root.resolve()
 if ARGS.action=='assemble':assemble(c,repo,out)
 elif ARGS.action=='check':check(c,repo,out,ARGS.built_pdfs,ARGS.falsifiers)
 else:seal(c,repo,out)
