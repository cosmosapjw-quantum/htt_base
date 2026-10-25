#!/usr/bin/env python3
"""Generate paper-facing tables and vector figures from retained finite results."""
from pathlib import Path
import csv, hashlib, json
import numpy as np
from scipy.stats import chi2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'reuse';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'svg.fonttype':'none','svg.hashsalt':'HTT-R32-reuse','axes.spines.top':False,'axes.spines.right':False})
source=ROOT/'evidence/output/physical_results.json'
data=json.loads(source.read_text())
fits=data['fits']
rows=[]
for name,fit in fits.items():
    assert abs(chi2.sf(fit['T'],fit['df'])-fit['chi2_tail_if_working_Gaussian'])<1e-12
    rows.append({'model':name,'T_full':fit['T'],'df':fit['df'],'tail_working_Gaussian':fit['chi2_tail_if_working_Gaussian'],
        'T_block_diagonal':fit['block_diagonal_covariance_T'],'unrestricted_eta95':fit['minimum_whitened_mean_budget95']})
with (OUT/'H03_TABLE.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

fig,ax=plt.subplots(figsize=(6.8,4.0))
eta=np.linspace(0,6,301)
for row in rows:
    ax.plot(eta,np.maximum(0,np.sqrt(row['T_full'])-eta)**2/chi2.ppf(.95,row['df']),label=row['model'].replace('_',' '))
ax.axhline(1,color='black',linestyle='--',linewidth=.8,label='fixed 95% working-law threshold')
ax.set(xlabel='Allowed whitened mean discrepancy $\\eta$',ylabel='Residual / fixed adequacy threshold',ylim=(0,6.0),xlim=(0,6))
ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'h03_discrepancy.svg',metadata={'Date':None});plt.close(fig)

# An attained chirality witness, not an observational CMB realization.
Q=np.diag([-1/np.sqrt(2),0,1/np.sqrt(2)])
w=np.array([np.sqrt(10)/4,1,np.sqrt(10)/4]);I=np.eye(3);qw=Q@w
O=(np.einsum('i,jk->ijk',w,Q)+np.einsum('j,ik->ijk',w,Q)+np.einsum('k,ij->ijk',w,Q))/3
O-=2/15*(np.einsum('ij,k->ijk',I,qw)+np.einsum('ik,j->ijk',I,qw)+np.einsum('jk,i->ijk',I,qw))
v=np.einsum('ijk,jk->i',O,Q)
raw=np.linalg.det(np.column_stack([v,Q@v,Q@Q@v]));bound=4*np.sqrt(2)/135
assert abs(np.linalg.norm(O)-1)<1e-12 and abs(raw/bound-1)<1e-12
M=np.trace(Q@Q)*I/3+2*Q@Q/5
assert abs(v@np.linalg.solve(M,v)-1)<1e-12
fig,axs=plt.subplots(1,2,figsize=(7.5,3.3))
t=np.linspace(0,2*np.pi,400)
axs[0].plot(np.sqrt(M[0,0])*np.cos(t),np.sqrt(M[1,1])*np.sin(t));axs[0].scatter([v[0]],[v[1]],color='#b33c4a')
axs[0].set(xlabel='$v_1$',ylabel='$v_2$',title='Projection of contraction image',aspect='equal')
u=np.linspace(-1,1,201)
axs[1].plot(u,u**3);axs[1].scatter([-1,1],[-1,1],color='#b33c4a')
axs[1].set(xlabel='Octupole scale $s$',ylabel='$\\chi(Q,sO) / C$',title='Attained endpoints; $C=4\\sqrt{2}/135$')
fig.tight_layout();fig.savefig(OUT/'qo_attainment.svg',metadata={'Date':None});plt.close(fig)

norm=.03265680189320023
r=np.linspace(0,.06,301)
fig,ax=plt.subplots(figsize=(6.3,3.8))
ax.plot(r,np.maximum(0,norm-r)/np.sqrt(6),label='conditional lower bound')
ax.plot(r,(norm+r)/np.sqrt(6),label='conditional upper bound')
ax.axvline(norm,color='gray',linestyle='--',label='apparent tensor norm')
ax.set(xlabel='Assumed qualified dimensionless error radius $r_Q$',ylabel='$\\Sigma$ interval endpoint',title='Fixed exact $H$: physical-response assumption required')
ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'shear_error_frontier.svg',metadata={'Date':None});plt.close(fig)
result={'scope':'Reused scientific seeds, not new survey evidence or new original42 completion',
 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'H03':rows,
 'QO_extremizer':{'Q':Q.tolist(),'O':O.tolist(),'v':v.tolist(),'chirality':float(raw),'sharp_constant':bound,'normalized_chirality':float(raw/bound),'ellipsoid_radius_squared':float(v@np.linalg.solve(M,v))},
 'CF4_error_frontier':{'apparent_dimensionless_STF_norm':norm,'physical_response_identity_assumed':True,'error_radius_estimated_from_data':False},
 'figure_scope':{'h03_discrepancy':'Exact unrestricted whitened-ball sensitivity under the retained Gaussian covariance; no empirical discrepancy bound.',
 'qo_attainment':'Deterministic algebraic example and contraction-image projection.',
 'shear_error_frontier':'Conditional physical bound versus an assumed error budget; no measured cosmic shear interval.'}}
(OUT/'REUSE_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'PASS_REUSE_CONSUMER','models':len(rows),'vector_figures':3,'new_original42_completions':0}))
