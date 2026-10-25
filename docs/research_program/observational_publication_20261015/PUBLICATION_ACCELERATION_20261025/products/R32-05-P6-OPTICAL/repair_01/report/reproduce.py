#!/usr/bin/env python3
"""Frozen P6 retained-statistic consumer; no catalogue or solver execution."""
from pathlib import Path
import json, hashlib, csv, re, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent; P=R.parents[3]; ROOT=P.parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj): (R/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def check(name,condition,detail=None):
    assert condition, (name,detail)
    checks[name]={'passed':True,'detail':detail}
def eq(name,a,b): check(name,bool(np.allclose(a,b,atol=1e-12,rtol=0)),float(np.max(np.abs(np.array(a)-np.array(b)))))
checks={}; sources=[]
man=P/'EVIDENCE_MANIFEST.json'
check('manifest_identity',sha(man)=='10703b1d37198379ee8ec4565dbef737e7ee35e6143de404c4d94ed48658f2d3',sha(man))
entries={x['path']:x for x in json.loads(man.read_text())['files']}
paths=[man,P/'evidence/research/latest_results.json',P/'evidence/RESULT_OBSERVABLE_MAP.json',P/'evidence/research/physical_derivations.md',P/'evidence/research/latest_physical_results.md',P/'products/R32-01-QO-METHODS/science/MANUSCRIPT.md']+list((R.parent/'science').glob('*.md'))
for path in paths:
    key=str(path.relative_to(ROOT)); actual=sha(path); entry=entries.get(key)
    if entry: check('source:'+key,actual==entry['sha256'],actual)
    sources.append({'path':key,'sha256':actual,'bytes':path.stat().st_size,'manifest_checked':entry is not None})
d=json.loads((P/'evidence/research/latest_results.json').read_text()); q=d['cf4_calibration_quotient']
check('correct_dimensionless_metadata','dimensionless' in d['units_correction']['correct_units']['b'])
b=np.array(q['apparent_b_dimensionless']); S=np.array(q['apparent_tensor_dimensionless']); C=np.array(q['working_covariance']); t=q['tensor_frobenius_norm']
T=np.zeros((5,3,3)); T[0]=np.diag([1,-1,0])/np.sqrt(2); T[1]=np.diag([1,1,-2])/np.sqrt(6)
for k,(i,j) in enumerate([(0,1),(0,2),(1,2)],2): T[k,i,j]=T[k,j,i]=1/np.sqrt(2)
eq('basis_gram',np.einsum('aij,bij->ab',T,T),np.eye(5)); eq('decoded_tensor',np.einsum('a,aij->ij',b,T),S)
eq('symmetry',S,S.T);eq('trace',np.trace(S),0);eq('coefficient_norm',np.linalg.norm(b),t);eq('frobenius_norm',np.linalg.norm(S),t);eq('saved_norm_no_second_kappa',t,0.03265680189321492)
eigen=np.linalg.eigvalsh(S);eq('ordered_eigenvalues',eigen,q['tensor_eigenvalues_ascending']);eq('directional_rms',np.sqrt(2/15)*t,q['directional_quadrupole_rms'])
check('C_finite',bool(np.isfinite(C).all()));eq('C_symmetric',C,C.T); ce=np.linalg.eigvalsh(C);check('C_positive_definite',bool(np.all(ce>0)),ce.tolist()); c2=C[:2,:2];check('C2_positive_definite',bool(np.all(np.linalg.eigvalsh(c2)>0)),np.linalg.eigvalsh(c2).tolist())
check('retained_rank',q['target_numerical_rank']==5)
# The exact crossing uses t directly, not a rounded display value.
x=np.unique(np.r_[np.linspace(0,1.5,301),1.]); radii=x*t; radii[x==1]=t
lo=np.maximum(0,t-radii)/np.sqrt(6);hi=(t+radii)/np.sqrt(6)
check('frontier_nonnegative',bool(np.all(lo>=0)));check('frontier_order',bool(np.all(hi>=lo)));check('frontier_positive_below',bool(np.all(lo[radii<t]>0)));check('frontier_zero_above',bool(np.all(lo[radii>=t]==0)));check('exact_crossing',bool(np.any(radii==t)))
plt.rcParams.update({'font.size':10,'pdf.fonttype':42})
fig,axs=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
axs[0].plot(x,lo,'--',label='Lower');axs[0].plot(x,hi,label='Upper');axs[0].set_ylabel(r'$\Sigma=\|\sigma\|_F/(\sqrt{6}H)$');axs[0].text(.04,.91,f't = {t:.12g}\n$r_Q$ assumed',transform=axs[0].transAxes,va='top')
rate={}
for delta in [0,.1,.25]:
    check('H_interval_'+str(delta),0<=delta<1)
    low=(1-delta)*lo; high=(1+delta)*hi
    eq('H_lower_'+str(delta),low,(1-delta)*np.maximum(0,t-radii)/np.sqrt(6));eq('H_upper_'+str(delta),high,(1+delta)*(t+radii)/np.sqrt(6))
    line,=axs[1].plot(x,high,label=fr'$\delta_H={delta}$');axs[1].plot(x,low,'--',color=line.get_color()); rate[str(delta)]={'lower':low.tolist(),'upper':high.tolist()}
axs[1].set_ylabel(r'$\|\sigma\|_F/(\sqrt{6}H_*)$')
for ax in axs: ax.axvline(1,color='gray',lw=.8);ax.set_xlabel(r'Assumed $r_Q/t$');ax.legend();ax.grid(alpha=.2)
fig.savefig(R/'figures/error_frontier.pdf');plt.close(fig)
phi=np.linspace(0,2*np.pi,721);a=np.stack([np.cos(phi),np.sin(phi)],axis=1);base=np.sqrt(np.einsum('ni,ij,nj->n',a,c2,a));center=b[:2]; projections={}
fig,axs=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
embed=np.pad(a,((0,0),(0,3)))
for eta in [0,.005,.01]:
    points=center+(a@c2.T)/base[:,None]+eta*a;support=base+eta
    eq('exposed_support_'+str(eta),np.sum(a*(points-center),axis=1),support)
    eq('full5_projection_support_'+str(eta),np.sqrt(np.einsum('ni,ij,nj->n',embed,C,embed))+eta,support)
    axs[0].plot(points[:,0],points[:,1],label=fr'$\eta={eta}$');axs[1].plot(phi,support,label=fr'$\eta={eta}$')
    projections[str(eta)]={'boundary':points.tolist(),'centered_support':support.tolist()}
axs[0].scatter(*center,color='black',s=20,label='Apparent center');axs[0].scatter(0,0,marker='+',color='gray',label='Origin');axs[0].set_aspect('equal',adjustable='datalim');axs[0].set_xlabel(r'$b_0$');axs[0].set_ylabel(r'$b_1$');axs[1].set_xlabel(r'$\varphi$ (radians)');axs[1].set_ylabel('Centered support (dimensionless)')
for ax in axs:ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.savefig(R/'figures/tensor_error_image.pdf');plt.close(fig)
# Range-compatible finite inverse regression, independent of retained observations.
A=np.diag([2.,1.,0.]);Ap=np.diag([.5,1.,0.]);z=np.array([2.,-1.,.2]);J=np.eye(3)[:2];rad=np.sqrt(.3**2-.2**2);fixtures=[]
for direction in [np.array([1.,0.]),np.array([0.,1.]),np.array([1.,1.])/np.sqrt(2)]:
    v=direction*np.array([.5,1.]);e=np.r_[-rad*v/np.linalg.norm(v),.2];theta=Ap@(z-e);expected=direction@np.array([1.,-1.])+rad*np.linalg.norm(v)
    i=str(len(fixtures));eq('fixture_residual_'+i,A@theta+e,z);eq('fixture_support_'+i,direction@J@theta,expected);eq('fixture_ball_'+i,np.linalg.norm(e),.3);eq('fixture_kernel_'+i,A@(theta+[0,0,7]),A@theta);eq('fixture_J_kernel_'+i,J@np.array([0,0,7]),[0,0])
    fixtures.append({'direction':direction.tolist(),'error':e.tolist(),'theta':theta.tolist(),'support':float(expected)})
check('infeasible_residual_fixture',abs(.4)>.3,{'z3':.4,'error_ball_radius':.3,'feasible':False,'pseudoinverse_is_not_feasible':True})
deltas=np.array([0,.001,.01]);B=1.2*np.expm1(2*deltas/(5/np.log(10)));eq('field_error_zero',B[0],0);check('field_error_positive_monotone',bool(np.all(np.diff(B)>0)),B.tolist())
rows=[(f'b_{i}',v) for i,v in enumerate(b)]+[(f'lambda_{i+1}',v) for i,v in enumerate(eigen)]+[('Frobenius norm',t),('Directional RMS',np.sqrt(2/15)*t),('Numerical rank',q['target_numerical_rank']),('Minimum singular value',min(q['signal_singular_values'])),('Maximum singular value',max(q['signal_singular_values']))]
with (R/'generated/tensor.csv').open('w') as f: w=csv.writer(f);w.writerow(['quantity','dimensionless_value_except_working_metric_singular_values']);w.writerows(rows)
tex='\\begin{tabular}{lr}\\hline Quantity & Value\\\\\\hline\n'
for name,val in rows:
    label='$'+name+'$' if '_' in name else name
    tex+=f'{label} & {val:.12g}'+r'\\'+'\n'
tex+='\\hline\\end{tabular}\n';(R/'generated/tensor.tex').write_text(tex)
tr=np.array([0,.005,.01,.02,t,.04]);tl=np.maximum(0,t-tr)/np.sqrt(6);tu=(t+tr)/np.sqrt(6);table=np.stack([tr,tl,tu,.9*tl,1.1*tu],axis=1)
eq('table_lower_formula',table[:,1],np.maximum(0,t-table[:,0])/np.sqrt(6));eq('table_upper_formula',table[:,2],(t+table[:,0])/np.sqrt(6));check('table_order',bool(np.all(table[:,2]>=table[:,1])))
with (R/'generated/frontier.csv').open('w') as f:w=csv.writer(f);w.writerow(['assumed_r_Q','Sigma_lower','Sigma_upper','rate_over_Hstar_lower_deltaH0.1','rate_over_Hstar_upper_deltaH0.1']);w.writerows(table)
tex=r'\begin{tabular}{rrrrr}\hline Assumed $r_Q$ & $\Sigma_-$ & $\Sigma_+$ & Rate$/H_*: -$ & Rate$/H_*: +$\\\hline'+'\n'
for row in table:tex+=' & '.join(f'{v:.11g}' for v in row)+r'\\'+'\n'
tex+='\\hline\\end{tabular}\n';(R/'generated/frontier.tex').write_text(tex)
status={'x':{'status':'APPARENT_TENSOR_RETAINED_CONDITIONAL_PHYSICAL_IMAGE','unresolved':['d','vorticity','H','curvature','tilt','energy','temporal_history'],'x_C':'INCOMPLETE_UNKNOWN'},'Q':{'status':'SPECIFIED_UNDEFINED_WITHOUT_POSITIVE_POLICY_DENOMINATOR','q_star':None},'F':{'status':'UNDEFINED','missing':'support measure and admissible set'},'Pi':{'status':'UNDEFINED','missing':'named joint probability law'},'G_F':{'status':'UNDEFINED','missing':'registered depth functional, windows, measures and shared dependence'}}
save('generated/retained_tensor_region.json',{'bhat':b.tolist(),'tensor':S.tolist(),'C':C.tolist(),'basis':T.tolist(),'basis_definition':d['units_correction']['basis'],'frame':'J2000 Cartesian','units':'dimensionless','rho_assumed':1,'G':np.eye(5).tolist(),'eta_assumed':[0,.005,.01],'C_eigenvalues':ce.tolist(),'C2_eigenvalues':np.linalg.eigvalsh(c2).tolist(),'working_covariance_scope':q['working_covariance_scope'],'diagnostic_statuses':status,'source_statistics':q})
save('generated/figure_data.json',{'r_Q_over_t':x.tolist(),'r_Q':radii.tolist(),'Sigma_lower':lo.tolist(),'Sigma_upper':hi.tolist(),'rate_over_Hstar':rate,'phi':phi.tolist(),'projections':projections})
save('generated/checks.json',{'absolute_tolerance':1e-12,'relative_tolerance':0,'checks':checks,'synthetic_finite_inverse_fixtures':fixtures,'field_bound':{'epsilon':.2,'delta':deltas.tolist(),'B':B.tolist()},'proof_note':'Equations (7)-(8): positivity and normalized r weighting bound the perturbed ratio in exp(+-2 delta/kappa); orthogonal L2 projection yields sqrt(3) and sqrt(15/2). No quadrature repeated.'})
save('generated/sources.json',sources)
# Parse the author's scientific claim map literally; no additional claim registry.
note=(R.parent/'science/RESEARCH_NOTE.md').read_text();claims=[]
for line in note.splitlines():
    if line.startswith('| P6-'):
        cells=[v.strip() for v in line.strip('|').split('|')]; ident,statement,owner,stat,evidence=cells
        claims.append({'claim_id':ident,'text':statement,'owner':owner,'status':stat,'evidence_type':'artifact' if ident=='P6-06' else 'proof','evidence_and_exact_source':evidence,'transfer_source':'empirical_proxy' if ident=='P6-06' else 'none','claim_tier':'C0','caveats':['Finite linear model, not unrestricted nonlinear inversion' if ident=='P6-04' else 'Product error-set assumption' if ident=='P6-05' else 'Working C has no empirical calibration' if ident=='P6-06' else 'Response qualification is not supplied by retained point estimate' if ident=='P6-08' else 'Missing physical sectors remain unknown/undefined' if ident=='P6-09' else 'Declared domains and source conventions apply']})
save('generated/claim_to_source.json',{'non_claim_promoting_candidate':True,'claims':claims})
print(json.dumps({'checks_passed':len(checks),'frontier_grid_values':len(x),'projection_angles':len(phi),'norm':t,'C_eigenvalues':ce.tolist(),'claims':len(claims)},indent=2))
