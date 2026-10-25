#!/usr/bin/env python3
"""Prescribed analytic illustration and retained-input consumer; no integration."""
from pathlib import Path
import hashlib, json, re, itertools, sys, subprocess, time, datetime, csv, os
os.environ.setdefault('SOURCE_DATE_EPOCH','1792886400')
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'.git').exists())
BASE=HERE.parents[2]
SCI=HERE.parent/'science'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
for p in ('figures','generated','raw'): (HERE/p).mkdir(exist_ok=True)
TOL=1e-12
INPUTS={}
for name,digest in {'MANUSCRIPT.md':'de41872977f19f5040dc21a6bda9c3b7a84d4f05ed837c53f3b539b5b0353ac0','BUILD_CONTRACT.md':'67c8e7d7b63a067fc65f9735ad4a90e1393e201b7c81eb0e4356be760d539a03','RESEARCH_NOTE.md':'badc957d7e714306db30ba163cab350669f68106aa9e8e3ca38410f9aec4716f'}.items():
    assert sha(SCI/name)==digest, name
    INPUTS[str((SCI/name).relative_to(ROOT))]=digest
manifest=json.loads((BASE/'EVIDENCE_MANIFEST.json').read_text())
for suffix in ('evidence/baseline/output/geometry_checks.json','evidence/baseline/research/theory_bridge_result.json'):
    p=BASE/suffix
    item=next(x for x in manifest['files'] if x['path']==str(p.relative_to(ROOT)))
    assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes'],suffix
    INPUTS[item['path']]=sha(p)
INPUTS[str((BASE/'EVIDENCE_MANIFEST.json').relative_to(ROOT))]=sha(BASE/'EVIDENCE_MANIFEST.json')
checks={}
def check(name,error):
    value=float(np.max(np.abs(error)))
    checks[name]={'max_abs_error':value,'absolute_tolerance':TOL,'passed':value<=TOL}
    assert value<=TOL,(name,value)
Q=np.diag([-1/np.sqrt(2),0,1/np.sqrt(2)])
w=np.array([np.sqrt(10)/4,1,np.sqrt(10)/4])
def lift(Q,w):
    O=np.zeros((3,3,3)); qw=Q@w
    for i,j,k in itertools.product(range(3),repeat=3):
        O[i,j,k]=(w[i]*Q[j,k]+w[j]*Q[i,k]+w[k]*Q[i,j])/3-2/15*((i==j)*qw[k]+(i==k)*qw[j]+(j==k)*qw[i])
    return O
O=lift(Q,w); R=np.diag([-1,1,1]); Qm=R@Q@R.T
Om=np.einsum('ia,jb,kc,abc->ijk',R,R,R,O)
def invariants(Q,O):
    v=np.einsum('ijk,jk->i',O,Q); t=np.sum(Q*Q); o=np.linalg.norm(O)
    chi=np.linalg.det(np.column_stack([v,Q@v,Q@Q@v]))
    return v,float(135*chi/(4*np.sqrt(2)*t**3*o**3))
v,C=invariants(Q,O); vm,Cm=invariants(Qm,Om)
check('Q_trace',np.trace(Q));check('O_trace',np.einsum('iik->k',O))
for perm in itertools.permutations(range(3)): check('O_symmetry_'+''.join(map(str,perm)),O-O.transpose(perm))
for name,tensor in [('Q',Q),('O',O),('Q_mirror',Qm),('O_mirror',Om)]: check(name+'_norm',np.linalg.norm(tensor)-1)
check('C_positive',C-1); check('C_negative',Cm+1)
check('contraction',v-np.array([2*np.sqrt(10)/15,1/3,2*np.sqrt(10)/15]))
ret=json.loads((BASE/'evidence/baseline/output/geometry_checks.json').read_text())['witness']
for k,val in [('Q_frobenius_norm',np.linalg.norm(Q)),('O_frobenius_norm',np.linalg.norm(O)),('Q_mirror_frobenius_norm',np.linalg.norm(Qm)),('O_mirror_frobenius_norm',np.linalg.norm(Om)),('C',C),('C_mirror',Cm)]: check('retained_'+k,val-ret[k])
plt.rcParams.update({'font.size':10,'axes.labelsize':10,'savefig.bbox':'tight','pdf.fonttype':42})
meta={'Creator':'retained-input consumer reproduce.py','CreationDate':None,'ModDate':None}
fig,ax=plt.subplots(1,2,figsize=(9,3.6),layout='constrained')
theta=np.linspace(0,2*np.pi,361); radius=np.sqrt(2/3)
ax[0].fill(radius*np.cos(theta),radius*np.sin(theta),color='#dce6ef');ax[0].plot(radius*np.cos(theta),radius*np.sin(theta),color='#526a84')
for x,y in itertools.product([-1,1],repeat=2): ax[0].scatter(x/np.sqrt(3),y/np.sqrt(3),color=('#b44432' if x*y>0 else '#245e9c'),s=55,zorder=3)
ax[0].scatter([],[],color='#b44432',label=r'$z_1z_2z_3>0$');ax[0].scatter([],[],color='#245e9c',label=r'$z_1z_2z_3<0$');ax[0].legend(fontsize=8,loc='upper center',ncol=2,frameon=False)
ax[0].axhline(0,color='gray',lw=.5);ax[0].axvline(0,color='gray',lw=.5)
ax[0].set(xlim=(-.95,.95),ylim=(-.95,.95),xlabel=r'$z_1$',ylabel=r'$z_2$',title=r'(a) Section $z_3=1/\sqrt{3}$',aspect='equal')
r=np.linspace(0,1/6,400); E=np.sqrt(np.maximum(0,(1-6*r)*(1+3*r/40)))
ax[1].fill_between(r,-E,E,color='#dce6ef');ax[1].plot(r,E,color='#b44432');ax[1].plot(r,-E,color='#245e9c');ax[1].scatter([0,0,1/6],[1,-1,0],s=25,color='black',zorder=3)
ax[1].set(xlabel=r'$r=j^2/t^3$',ylabel=r'$\mathcal{C}$',xlim=(-.005,.172),ylim=(-1.1,1.1),title='(b) Sharp signed shape envelope')
fig.savefig(HERE/'figures/geometry.pdf',metadata=meta);plt.close(fig)
lon=np.linspace(-np.pi,np.pi,241);lat=np.linspace(-np.pi/2,np.pi/2,121);L,B=np.meshgrid(lon,lat)
n=np.array([np.cos(B)*np.cos(L),np.cos(B)*np.sin(L),np.sin(B)])
def field(Q,O,n): return np.einsum('ij,i...,j...->...',Q,n,n)+np.einsum('ijk,i...,j...,k...->...',O,n,n,n)
f=field(Q,O,n);fm=field(Qm,Om,n);check('field_reflection',fm-field(Q,O,np.einsum('ij,j...->i...',R,n)))
fig,axs=plt.subplots(1,2,figsize=(10,3.5),subplot_kw={'projection':'mollweide'},layout='constrained');lim=max(np.max(np.abs(f)),np.max(np.abs(fm)))
for a,vals,title in zip(axs,[f,fm],[r'(a) Analytic witness, $\mathcal{C}=+1$',r'(b) Reflected witness, $\mathcal{C}=-1$']):
    im=a.pcolormesh(L,B,vals,cmap='RdBu_r',vmin=-lim,vmax=lim,shading='auto',rasterized=True);a.grid(alpha=.35);a.set_title(title,pad=14);a.set_xticklabels([]);a.set_yticklabels([])
fig.colorbar(im,ax=axs,orientation='horizontal',shrink=.65,pad=.05,label=r'$Q_*:nn+O_*:nnn$ (unit-tensor field)')
fig.savefig(HERE/'figures/extremizer.pdf',metadata=meta);plt.close(fig)
opt=json.loads((BASE/'evidence/baseline/research/theory_bridge_result.json').read_text());rows=opt['rows'];assert len(rows)==45
cols={k:np.array([r[k] for r in rows]) for k in rows[0]}
assert all(np.all(np.isfinite(x)) for x in cols.values());assert np.all(np.diff(cols['amplitude'])>0)
kappa=5/np.log(10)
expected=np.sqrt(35/2)*kappa*cols['epsilon_upper']**3/(3*(1-cols['epsilon_upper']))
check('epsilon_formula',cols['epsilon_upper']-1.6*cols['amplitude'])
assert np.all(np.abs(cols['remainder_bound']-expected)<=TOL*np.maximum(1,np.abs(expected)))
assert np.all(cols['coupled_remainder_norm']<=cols['remainder_bound']+TOL*np.maximum(1,np.abs(expected)))
checks['all_45_finite_monotone_and_bounds']={'passed':True,'rows':45,'scalar_tolerance':'1e-12*max(1,abs(expected))'}
fig,axs=plt.subplots(1,2,figsize=(10,3.9),layout='constrained');a=cols['amplitude']
for key,label,color,ls in [('coupled_exact_norm','Coupled: exact logarithm','#245e9c','-'),('coupled_quadratic_norm','Coupled: quadratic','#b44432','--'),('pure_dipole_exact_norm','Pure dipole: exact logarithm','#39804b','-'),('pure_dipole_cubic_norm','Pure dipole: cubic','#9c6ba8','--')]: axs[0].loglog(a,cols[key],label=label,color=color,ls=ls)
axs[1].loglog(a,cols['coupled_remainder_norm'],label='Actual coupled remainder',color='#245e9c');axs[1].loglog(a,cols['remainder_bound'],label=r'Analytic bound $E_3(\epsilon)$',color='#b44432',ls='--')
for i,axis in enumerate(axs): axis.set(xlabel=r'Dimensionless amplitude $a$',ylabel='Frobenius norm (magnitude)',title=['(a) Synthetic octupole response','(b) Synthetic coupled remainder'][i]);axis.grid(True,which='both',alpha=.15);axis.legend(fontsize=8)
fig.savefig(HERE/'figures/optical.pdf',metadata=meta);plt.close(fig)
selected=[rows[i] for i in [0,11,22,33,44]]
with (HERE/'generated/optical_rows.csv').open('w') as fcsv:
    writer=csv.DictWriter(fcsv,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
def fmt(x):
    s=f'{x:.5e}'; m,e=s.split('e');return rf'${m}\times10^{{{int(e)}}}$'
table=r'''\begin{table}[htb]
\caption{Five retained synthetic local-response amplitudes. The amplitude $a$ is dimensionless; all other entries are full ordered-index Frobenius norms in magnitude units. The remainder is relative to the quadratic coupling, and the bound is $E_3(1.6a)$.}\label{tab:optical}
\begin{ruledtabular}
\begin{tabular}{ccccc}
$a$ & Exact coupled & Quadratic & Remainder & Bound \\
'''
for row in selected: table+=' & '.join(fmt(row[k]) for k in ['amplitude','coupled_exact_norm','coupled_quadratic_norm','coupled_remainder_norm','remainder_bound'])+r' \\'+'\n'
table+=r'\end{tabular}\end{ruledtabular}\end{table}'+'\n';(HERE/'generated/optical_table.tex').write_text(table)
dump(HERE/'generated/checks.json',checks)
dump(HERE/'generated/summary.json',{'scope':opt['scope'],'row_count':45,'selected_zero_based_indices':[0,11,22,33,44],'selected_rows':selected,'max_retained_two_grid_tensor_difference':opt['max_quadrature_tensor_difference'],'quadrature':opt['quadrature'],'quadrature_status':'retained consistency comparison, not a rigorous error bound','exact_rational_checks_retained_count':len(opt['exact_rational_checks']),'Q':Q.tolist(),'O':O.tolist(),'Q_mirror':Qm.tolist(),'O_mirror':Om.tolist(),'contraction':v.tolist(),'C':C,'C_mirror':Cm})
# Translate the frozen scientific source; mathematics and numbered tags remain literal.
source=(SCI/'MANUSCRIPT.md').read_text();body=source.split('## References for bibliography generation')[0]
body=body.replace('–','--').replace('—','---').replace('’',"'").replace('“','``').replace('”',"''").replace('≤',r'$\le$')
lines=body.splitlines();title=lines.pop(0)[2:];body='\n'.join(lines)
body=body.replace('## Abstract','\\begin{abstract}').replace('## 1. Introduction','\\end{abstract}\n\\maketitle\n\\section{Introduction}')
body=re.sub(r'^## \d+\. (.+)$',r'\\section{\1}',body,flags=re.M)
body=re.sub(r'^### (.+)$',r'\\subsection{\1}',body,flags=re.M)
body=re.sub(r'\*\*(.+?)\*\*',r'\\textbf{\1}',body)
body=body.replace('*Proof.*',r'\emph{Proof.}').replace(r'\square',r'\Box')
body=re.sub(r'\[([A-Za-z]+\d+(?:, [A-Za-z]+\d+)*)\]',lambda m:r'\cite{'+m.group(1).replace(' ','')+'}',body)
body=re.sub(r'\\\[(.*?)\\\]',lambda m:r'\begin{equation}'+m.group(1)+r'\end{equation}',body,flags=re.S)
# Preserve exact numbering and literal displayed math, while allowing the widest displays to scale if necessary.
assert sorted(map(int,re.findall(r'\\tag\{(\d+)\}',body)))==list(range(1,42))
body=body.replace('Figure 1 shows',r'Figure~\ref{fig:geometry} shows').replace('Figure 2 displays',r'Figure~\ref{fig:extremizer} displays').replace('Figure 3 uses',r'Figure~\ref{fig:optical} uses').replace('Table 1 gives',r'Table~\ref{tab:optical} gives')
captions=[('geometry','Attained contraction geometry. At fixed quadrupole and octupole norm the normalized contraction vector fills the unit ball. The displayed section contains four of the eight simple-spectrum extremizers; the remaining four lie in the opposite section. The fixed-norm fibre is a translated three-sphere in the interior and a singleton on the boundary. The right panel shows the sharp signed shape envelope, which reaches both global endpoints at a zero-cubic-trace quadrupole and vanishes at repeated eigenvalues. The coordinates are dimensionless analytic quantities, not sample probabilities.'),('extremizer','An analytic pair attaining the sharp constant and its mirror. Both STF tensors have unit Frobenius norm. Reflection preserves their norms and reverses the determinant coordinate. The fields illustrate the algebraic theorem; the exact logarithmic optical response has its separately stated amplitude and remainder restrictions. These unit-tensor angular fields are synthetic illustrations in the specified common Euclidean frame.'),('optical','Nonlinear local magnitude response for the specified synthetic acceleration and shear. The coupled octupole is quadratic at small common amplitude, whereas the pure-dipole response begins at cubic order. The right panel compares the saved exact-logarithm projection error with its analytic finite angular envelope. Curves consume the retained 45-row quadrature result; finite-redshift propagation and observational errors are separate inputs. All norm ordinates are in magnitude units; amplitude is dimensionless, and the response uses the same source and observer congruence.')]
def figure(name,caption):return '\n'+r'\begin{figure}[htb]\centering'+'\n'+rf'\includegraphics[width=\linewidth]{{figures/{name}.pdf}}'+'\n'+rf'\caption{{{caption}}}\label{{fig:{name}}}'+'\n'+r'\end{figure}'+'\n'
body=body.replace(r'\subsection{Relation to a conventional tensor covariant}',figure(*captions[0])+figure(*captions[1])+r'\subsection{Relation to a conventional tensor covariant}')
body=body.replace('The theorem, response and inverse concern',figure(*captions[2])+r'\input{generated/optical_table.tex}'+'\n\nThe theorem, response and inverse concern')
preamble=r'''\documentclass[aps,prd,reprint,onecolumn,11pt,nofootinbib,notitlepage]{revtex4-2}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,bm,graphicx}
\setlength{\emergencystretch}{4em}
\usepackage[colorlinks=true,citecolor=blue,linkcolor=blue,urlcolor=blue]{hyperref}
\begin{document}
'''
tex=preamble+'\\title{'+title+'}\n'+r'\author{Anonymous review draft}\noaffiliation'+'\n'+body+'\n'+r'\bibliographystyle{apsrev4-2}\bibliography{references}'+'\n'+r'\end{document}'+'\n'
(HERE/'main.tex').write_text(tex)
commands=[]
if '--build' in sys.argv:
    cmd=['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error','main.tex'];start=time.monotonic();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc=subprocess.run(cmd,cwd=HERE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    (HERE/'raw/latexmk.stdout').write_text(proc.stdout)
    commands.append({'argv':cmd,'cwd':str(HERE),'started_utc':stamp,'duration_seconds':time.monotonic()-start,'exit_code':proc.returncode,'output':'raw/latexmk.stdout'})
    dump(HERE/'raw/commands.json',commands)
    if proc.returncode: print(proc.stdout[-7000:]);sys.exit(proc.returncode)
    log=(HERE/'main.log').read_text(errors='replace')+'\n'+(HERE/'main.blg').read_text(errors='replace');warnings=[s for s in log.splitlines() if any(k in s for k in ['Warning','Overfull','Underfull','undefined','multiply defined'])]
    fatal=[s for s in warnings if any(k in s.lower() for k in ['undefined','multiply defined'])];assert not fatal,fatal
    forbidden=['Bianchi geometry detected','Bianchi family identified','model-independent truth certificate','MIO posterior','TSC full solver','external transfer validated as native']
    assert not any(s in tex for s in forbidden)
    artifact_paths=['reproduce.py','main.tex','main.pdf','references.bib','main.bbl','generated/checks.json','generated/summary.json','generated/optical_rows.csv','generated/optical_table.tex','figures/geometry.pdf','figures/extremizer.pdf','figures/optical.pdf','raw/latexmk.stdout','raw/commands.json','README.md']
    result={'schema':'htt.prescribed_manuscript_build/1','task_id':'R32-01-QO-METHODS','packet_id':'336da055d13b09becf16c2600dbc305d646af22fbe33643002ada390ea11daae','source_head':'5da49ec48afd10f7bfaf1b38e950a1193df55b60','executor':{'requested_model':'gpt-6.1-sol','requested_effort':'medium','observed_runtime':'UNKNOWN'},'owner':'obsstat/common; optical diagnostic interpretation mio','claim_tier':'C0 deterministic/conditional','transfer_source':'none','scope':'prescribed retained-input consumer and complete methods manuscript build','scientific_admission':'PENDING_AUTHOR_BINDING_AND_FRESH_INDEPENDENT_REVIEW','original42_acceptance_effect':'none','sky_support_status':'analytic and full-sphere synthetic local response','null_mock_status':'no sampling law or empirical null calibration supplied','inputs':INPUTS,'artifacts':{p:{'sha256':sha(HERE/p),'bytes':(HERE/p).stat().st_size} for p in artifact_paths},'equation_tags':list(range(1,42)),'figures':3,'retained_rows':45,'commands':commands,'warnings':warnings,'checks_passed':all(x['passed'] for x in checks.values()),'environment':{'python':sys.version,'numpy':np.__version__,'matplotlib':matplotlib.__version__},'caveats':['Quadrature agreement is consistency evidence, not a rigorous integration error bound.','Analytic witness checks implement displayed formulas; manuscript proofs support general statements.','No catalogue, processed-map, solver, ODE, SVD, or quadrature reintegration was performed.']}
    dump(HERE/'RESULT.json',result)
    (HERE/'BUILD_REPORT.md').write_text('# Build status\n\nComplete candidate built with latexmk; scientific admission awaits independent review.\n\n## Entrypoint and included files\n\nmain.tex; generated/optical_table.tex; references.bib; three generated figures.\n\n## Commands run\n\n`python3 reproduce.py --build` (see raw/commands.json for LaTeX subprocess timing and raw/latexmk.stdout).\n\n## Errors and warnings\n\n'+('\n'.join(warnings) or 'None.')+'\n\n## Missing figures and missing figure sources\n\nNone; all three figures generated by reproduce.py.\n\n## Citation/reference status\n\nSeven primary references; no undefined citations or references.\n\n## Claim-language risks\n\nDeterministic/conditional methods only; no observed-sky or scientific-admission claim.\n\n## Required manuscript fixes\n\nFresh independent review remains pending.\n')
print(json.dumps({'checks':len(checks),'passed':True,'figures':3,'rows':45,'tex':str(HERE/'main.tex')}))
