#!/usr/bin/env python3
"""Read-only R36-08 independent checks; never invokes producer main or writes products."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import scipy
from scipy.integrate import quad
from scipy.linalg import solve_triangular
from scipy.stats import chi2

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
P = ROOT / 'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-08-PUBLIC-SN'
D = Path('/mnt/extdrive/workdir/htt_open_data/bridge20261027/pantheon')
X = Path('/mnt/extdrive/workdir/htt_open_data/r36_public_sn_actual')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b,rtol=1e-9,atol=1e-10): np.testing.assert_allclose(a,b,rtol=rtol,atol=atol)

expected = {
 P/'CANDIDATE_MANIFEST.json':'efeb05dfe755f47c48c994d1684312659277816a3f7294f6d76f63f27f9f046c',
 X/'RETURN.json':'98fb262093675aa3a9471a60ba9d2fb8aad854fc4a0342f8f19e3928cd0836a7',
 Path('/mnt/extdrive/workdir/htt_open_data/r36_scientific_contract_preparation/R36-08.json'):'6f8c24d0deec3c54c4e44bc3b23f0f514f4cacbf45bc8f4ee6d9a6eb61fbe715',
 Path('/mnt/extdrive/workdir/htt_open_data/r36_public_sn_covariance_repair/REPAIR_DECISION.json'):'3cd28db0b16f66baef4175c5dfe80f6af0f0522465931ac4fdea315cf92e4ab3',
}
for p,h in expected.items(): assert sha(p)==h, str(p)
manifest=json.loads((P/'CANDIDATE_MANIFEST.json').read_text())
for f in manifest['files']:
 p=Path(f['path']); assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],str(p)
receipt=json.loads((X/'RAW_RECEIPT.json').read_text())
for f in receipt['logs']:
 p=Path(f['path']); assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],str(p)
R=json.loads((P/'RESULT.json').read_text())
raw=json.loads((X/'RESULT_RAW.json').read_text())
first=json.loads((X/'COVARIANCE_FIRST_FAILURE.json').read_text())
for f in R['source']['inputs'].values():
 p=Path(f['path']); b=p.read_bytes()
 assert len(b)==f['bytes'] and sha(p)==f['sha256']
 assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==f['git_blob_sha1']
rows=np.genfromtxt(D/'Pantheon+SH0ES.dat',names=True,dtype=None,encoding='utf-8')
c=np.loadtxt(D/'Pantheon+SH0ES_STAT+SYS.cov')
assert len(rows)==1701 and c[0]==1701 and c.size==1+1701**2 and np.isfinite(c).all()
C=c[1:].reshape(1701,1701)
keys='\n'.join(f'{i}|{rows["CID"][i]}|{rows["IDSURVEY"][i]}' for i in range(1701))
assert hashlib.sha256(keys.encode()).hexdigest()==R['source']['row_key_sha256']
asym=np.abs(C-C.T); tol=64*np.finfo(float).eps*1701*np.max(np.abs(C))
pairs=np.argwhere(np.triu(asym>tol,1))
assert len(pairs)==389 and np.count_nonzero(asym>tol)==778
assert C[84,97]==.00048592 and C[97,84]==.00048595
report={'environment':{'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__},
 'candidate_files_verified':len(manifest['files']),'producer_raw_logs_verified':len(receipt['logs']),
 'global_asymmetry':{'maximum':float(asym.max()),'threshold':float(tol),'pairs':len(pairs)},'cohorts':{}}

# Independent explicit polynomial angular design, not consumer.design.
def independent_design(t):
 ra=np.deg2rad(t['RA']); dec=np.deg2rad(t['DEC'])
 nx=np.cos(dec)*np.cos(ra); ny=np.cos(dec)*np.sin(ra); nz=np.sin(dec)
 F=np.column_stack((nx,ny,nz,(nx*nx-ny*ny)/np.sqrt(2),
    (nx*nx+ny*ny-2*nz*nz)/np.sqrt(6),np.sqrt(2)*nx*ny,
    np.sqrt(2)*nx*nz,np.sqrt(2)*ny*nz))
 high=t['zHD']>=.06
 return np.column_stack((np.ones(len(t)),high.astype(float),F*(~high)[:,None],F*high[:,None]))

for key,lower,counts in [('primary',.0233,(490,342,148,62)),('lower_z_sensitivity',.01,(705,557,148,114))]:
 finite=np.ones(1701,dtype=bool)
 for name in ('RA DEC zHD zHDERR zCMB zCMBERR zHEL zHELERR m_b_corr IS_CALIBRATOR USED_IN_SH0ES_HF VPEC VPECERR').split(): finite &= np.isfinite(rows[name])
 idx=np.flatnonzero((rows['IS_CALIBRATOR']==0)&(rows['zHD']>=lower)&(rows['zHD']<=.15)&finite)
 t=rows[idx]; high=t['zHD']>=.06
 assert (len(t),sum(~high),sum(high),len(t)-len(set(t['CID'])))==counts
 assert idx.tolist()==raw[key]['original_indices']==[z['index'] for z in first['cohorts'][str(lower)]['row_ids']]
 assert not np.isin(pairs,idx).any()
 S=C[np.ix_(idx,idx)]; assert np.array_equal(S,S.T)
 L=np.linalg.cholesky(S)
 eig=float(np.linalg.eigvalsh(S)[0]); close(eig,R[key]['covariance']['min_eigenvalue_mag2'])
 q=R[key]; f=q['fits']['full']; b=np.array(f['coefficients_mag']); V=np.array(f['covariance_mag2'])
 assert np.all(np.linalg.eigvalsh(V)>0)
 assert f['rank']==16 and f['nuisance_rank']==2
 close(V,q['full_16x16_covariance_mag2']); close(b[:8],q['low_8_mag']); close(b[8:],q['high_8_mag'])
 H=np.column_stack((-np.eye(8),np.eye(8)))
 close(H@b,q['high_minus_low_8_mag']); close(H@V@H.T,q['high_minus_low_8x8_covariance_mag2'])
 close(b@np.linalg.solve(V,b),f['delta_T'])
 close(f['T_null']-f['T_full'],f['delta_T'])
 close(f['T_null'],q['fits']['null']['T'])
 close(chi2.sf(f['delta_T'],16),f['p_chi2_conditional'])
 close(chi2.isf(.05,16),q['simultaneous_95pct_16D_ellipsoid_squared_radius'])
 assert q['fits']['null']['T']>=q['fits']['dipole']['T_full']>=f['T_full']
 assert [q['fits']['null']['rank'],q['fits']['dipole']['rank']+2,f['rank']+2]==[2,8,18]
 for v in (b[3:8],b[11:16]):
  a,d,e,g,h=v
  T=np.array([[a/np.sqrt(2)+d/np.sqrt(6),e/np.sqrt(2),g/np.sqrt(2)],
              [e/np.sqrt(2),-a/np.sqrt(2)+d/np.sqrt(6),h/np.sqrt(2)],
              [g/np.sqrt(2),h/np.sqrt(2),-2*d/np.sqrt(6)]])
  close(np.trace(T),0); close(np.sum(T*T),v@v)
 quad_checks=[]
 saved_y=np.array(raw[key]['plot']['magnitude_residual'])
 for j in np.linspace(0,len(t)-1,7,dtype=int):
  integ,err=quad(lambda z:1/np.sqrt(.3153*(1+z)**3+.6847),0,t['zHD'][j],epsabs=1e-13,epsrel=1e-13)
  y=t['m_b_corr'][j]-5*np.log10((1+t['zHEL'][j])*integ)
  close(y,saved_y[j],rtol=0,atol=1e-10); quad_checks.append(abs(y-saved_y[j]))
 report['cohorts'][key]={'n':len(t),'counts':list(map(int,counts)),'exact_symmetry':True,'min_eigenvalue':eig,
    'quadrature_spot_check_max_residual_mag':max(quad_checks),'Wald_equals_deltaT':float(b@np.linalg.solve(V,b)),
    'full_rank':16,'null_full_df':[len(t)-2,len(t)-18],
    'contrast_cross_bin_max_abs_covariance_mag2':float(np.max(np.abs(V[:8,8:]))) }
 if key=='primary':
  # One focused real-cohort independent full QR check. Saved residuals are already
  # source-joined above and quadrature spot checked. No producer or survey replay.
  Z=independent_design(t); Zw=solve_triangular(L,Z,lower=True)
  yw=solve_triangular(L,saved_y,lower=True)
  Q,U=np.linalg.qr(Zw,mode='reduced'); bhat=np.linalg.solve(U,Q.T@yw)
  Ui=np.linalg.solve(U,np.eye(18)); cov=Ui@Ui.T
  close(bhat[2:],b); close(cov[2:,2:],V)
  close(np.linalg.norm(yw-Zw@bhat)**2,f['T_full'])
  close(np.max(np.sum(Q*Q,axis=1)),f['max_whitened_leverage'])
  report['primary_independent_QR']={'max_coefficient_error_mag':float(np.max(abs(bhat[2:]-b))),
      'max_covariance_error_mag2':float(np.max(abs(cov[2:,2:]-V))),
      'chi_square_residual':float(np.linalg.norm(yw-Zw@bhat)**2)}
  primary_surveys,primary_counts=np.unique(t['IDSURVEY'],return_counts=True)

robust=json.loads((P/'SURVEY_ROBUSTNESS.json').read_text())
assert len(robust['surveys'])==len(primary_surveys)==16
for rec,survey,count in zip(robust['surveys'],primary_surveys,primary_counts):
 assert rec['deleted_IDSURVEY']==survey and rec['deleted_rows']==count
 assert rec['remaining_rows']==490-count and rec['rank']==16
 close(chi2.sf(rec['delta_T'],16),rec['conditional_p'])
close(min(r['delta_T'] for r in robust['surveys']),robust['minimum_delta_T'])
close(max(r['delta_T'] for r in robust['surveys']),robust['maximum_delta_T'])
report['leave_survey_saved_evidence']={'records':16,'row_deletions_and_chi_square_tails':'PASS',
 'delta_T_range':[robust['minimum_delta_T'],robust['maximum_delta_T']],
 'all_16_fits_rerun':False}

# Execute only the author's small fixture, whose import does not invoke main.
spec=importlib.util.spec_from_file_location('candidate_fixture',P/'test_consumer.py')
test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
report['candidate_fixture']='PASS'
report['review_scope']='selected data validation, saved statistic algebra, one primary QR check and small fixture; no full producer reanalysis'
report['result']='PASS_CONDITIONAL_NUMERICAL_CHECKS'
print(json.dumps(report,indent=2))
