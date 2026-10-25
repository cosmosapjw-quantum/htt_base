"""Review-owned independent synthesis check; no author module imported."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.stats import chi2
p=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-08-H03-PAPER')
r=Path('/mnt/extdrive/workdir/htt_open_data/r35_h03_paper_fresh_review')
s=json.loads((p/'inputs/evidence/sources/H03_SOURCE_TOMOGRAPHY.json').read_text())
a=json.loads((p/'generated/paper_analysis.json').read_text())
w=s['monopole_dipole_STF2_windows']; y36=np.concatenate([x['theta9'] for x in w]); C36=np.array(s['joint_covariance_36x36'])
I=np.array([9*j+k for j in range(4) for k in (1,2,3)]); J=np.array([j for j in range(36) if j not in I]);y=y36[I];C=C36[np.ix_(I,I)]
R=np.vstack([np.array(x['bulk_velocity_design_response_9x3_per_Mpc'])[1:4] for x in w]);G=np.tile(np.eye(3),(4,1))
def gls(y,C,X):
    lam,V=np.linalg.eigh(C);assert min(lam)>0
    W=(V/np.sqrt(lam)).T;Z=W@X;v=W@y
    beta=np.linalg.lstsq(Z,v,rcond=None)[0];d=v-Z@beta
    return beta,float(d@d),len(y)-np.linalg.matrix_rank(Z)
out={'independence':'Symmetric eigensystem whitening; no author code imported','fits':{},'full36_profile':{}}
for name,X in [('bulk',R),('constant_rate_dipole',G),('bulk_plus_constant_rate',np.column_stack([R,G]))]:
    beta,T,df=gls(y,C,X);ref=a['fits'][name]
    assert abs(T-ref['T'])<1e-9
    assert np.max(abs(beta-np.array(ref['coefficients'])))<1e-8
    assert abs(chi2.sf(T,df)-ref['tail'])<1e-12
    XX=np.zeros((36,X.shape[1]+24));XX[I,:X.shape[1]]=X;XX[J,X.shape[1]:]=np.eye(24)
    b36,T36,df36=gls(y36,C36,XX)
    assert abs(T-T36)<1e-9 and df==df36
    out['fits'][name]={'T':T,'df':df,'tail':float(chi2.sf(T,df)),'coefficients':beta.tolist()}
    out['full36_profile'][name]={'T':T36,'df':df36,'T_difference':T36-T}
B=C.copy()
for i in range(4):
 for j in range(4):
  if i!=j:B[3*i:3*i+3,3*j:3*j+3]=0
_,Tb,df=gls(y,B,np.column_stack([R,G]));assert abs(Tb-a['fits']['block_diagonal']['T'])<1e-9
out['block_diagonal']={'T':Tb,'tail':float(chi2.sf(Tb,df))}
# Explicit Schur conditional covariance differs: source consumed is marginal.
conditional=C-C36[np.ix_(I,J)]@np.linalg.solve(C36[np.ix_(J,J)],C36[np.ix_(J,I)])
_,Tc,_=gls(y,conditional,np.column_stack([R,G]))
carrier=json.loads((p/'generated/source_carrier.json').read_text())
assert np.array_equal(C,np.array(carrier['C_dipole_12x12']))
out['marginal_not_conditional']={'marginal_entry_error':0.,'conditional_covariance_norm_difference':float(np.linalg.norm(C-conditional)),'conditional_counterfactual_T':Tc}
cf=json.loads((p/'inputs/CF4_QUOTIENT.json').read_text());q=np.array(cf['minimum_norm_representative_b']);u,v,xy,xz,yz=q
T=np.array([[u/np.sqrt(2)+v/np.sqrt(6),xy/np.sqrt(2),xz/np.sqrt(2)],[xy/np.sqrt(2),-u/np.sqrt(2)+v/np.sqrt(6),yz/np.sqrt(2)],[xz/np.sqrt(2),yz/np.sqrt(2),-2*v/np.sqrt(6)]])
assert np.max(abs(T-np.array(cf['complete_3x3_tensor'])))<1e-15
assert abs(np.linalg.norm(T)-.03265680189321492)<1e-15
out['cf4']={'norm':float(np.linalg.norm(T)),'eigenvalues':np.linalg.eigvalsh(T).tolist(),'directional_rms':float(np.sqrt(2/15)*np.linalg.norm(T)),'conditional_Sigma':float(np.linalg.norm(T)/np.sqrt(6)),'trace':float(np.trace(T))}
# New consumer output equality: exact deterministic tables and numeric carrier/analysis.
fixtures=r/'fixture'
out['reproduction']={}
for name in ['analysis.json','source_carrier.json','paper_analysis.json','fits.tex','rates.tex','table.tex','matrix_min_budget.csv']:
    equal=(fixtures/'generated'/name).read_bytes()==(p/'generated'/name).read_bytes()
    out['reproduction'][name]={'byte_equal':equal}
    if name.endswith('.json'):
        differences=[]
        def compare(x,y,path=''):
            if isinstance(x,dict):
                assert set(x)==set(y)
                for k in x:compare(x[k],y[k],path+'/'+k)
            elif isinstance(x,list):
                assert len(x)==len(y)
                for k,(v,w) in enumerate(zip(x,y)):compare(v,w,path+f'/{k}')
            elif isinstance(x,(int,float)) and not isinstance(x,bool):
                assert np.isclose(x,y,atol=1e-8,rtol=0), (path,x,y)
                differences.append(abs(x-y))
            else:assert x==y,(path,x,y)
        compare(json.loads((fixtures/'generated'/name).read_text()),json.loads((p/'generated'/name).read_text()))
        out['reproduction'][name]['max_numeric_abs_difference']=max(differences,default=0)
    elif name.endswith('.tex'):
        assert equal
    else:
        import csv
        rows0=list(csv.reader((fixtures/'generated'/name).open()));rows1=list(csv.reader((p/'generated'/name).open()))
        assert len(rows0)==len(rows1)
        dif=[]
        for row0,row1 in zip(rows0,rows1):
            assert len(row0)==len(row1)
            for x,y in zip(row0,row1):
                if x==y:continue
                for v,w in zip(x.split(';'),y.split(';')):
                    dif.append(abs(float(v)-float(w)));assert abs(float(v)-float(w))<1e-8
        out['reproduction'][name]['max_numeric_abs_difference']=max(dif,default=0)
# Table III is copied from preserved complete tensors, not reconstructed from scalar summaries.
physical=json.loads((p/'inputs/evidence/output/physical_results.json').read_text())
out['rate_tensor_keys']=list(physical['rate_tensors'][0])
out['status']='PASS'
(r/'raw/independent_check.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
