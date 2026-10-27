import json, pathlib, re, hashlib
import numpy as np
import scipy
from scipy.stats import chi2,ncx2

OUT=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_synthesis_repair_fresh_review')
FIX=OUT/'fixture/P4'
p=json.loads((FIX/'report/pm_history_supplement.json').read_text())
s=(FIX/'science/MANUSCRIPT.md').read_text()
assert p['source']['selected_rows']==755850
results={'numpy':np.__version__,'scipy':scipy.__version__,'scope':'algebraic consistency and transcription of retained products, no producer rerun','profiles':{},'histories':[]}
infos={}
for name,n in [('primary_spin_glide6',6),('all97_sensitivity',97)]:
    q=p['gram'][name];I=np.array(q['profile']['information']);C=np.array(q['joint']['full5_covariance']);cov=np.array(q['joint']['joint_covariance']);score=np.array(q['joint']['joint_score']);coef=np.array(q['joint']['joint_gls_coefficients']);ev=np.array(q['profile']['eigenvalues']);V=np.array(q['profile']['eigenvectors']);cross=np.array(q['joint']['joint_signal_nuisance_covariance'])
    assert I.shape==(5,5) and cov.shape==(n+5,n+5) and cross.shape==(5,n)
    residuals={'information_covariance_maxabs':float(np.max(np.abs(I@C-np.eye(5)))), 'eigenbasis_maxabs':float(np.max(np.abs(I@V-V*ev))), 'joint_covariance_signal_maxabs':float(np.max(np.abs(cov[:5,:5]-C))), 'joint_crosscovariance_maxabs':float(np.max(np.abs(cov[:5,5:]-cross))), 'joint_score_to_coefficient_maxabs':float(np.max(np.abs(cov@score-coef)))}
    assert max(residuals.values())<1e-10,residuals
    assert np.all(ev>0) and q['profile']['rank']==5 and q['profile']['nuisance_rank']==n
    assert np.linalg.norm(cross)>0
    a=np.array(q['joint']['selected_sample_full5_coefficients_uasyr']);assert np.array_equal(a,coef[:5])
    displayed='| '+str(n)+' | '+' | '.join(f'{x:.6f}' for x in a)+' |';assert displayed in s
    radii=np.sqrt(p['power_frontier']['lambda80']/ev[[4,0]])
    assert ' | '+f'{radii[0]:.5f} / {radii[1]:.5f}'+' |' in s
    assert ', '.join(f'{x:.6g}' for x in ev) in s
    results['profiles'][name]={'nuisance_dimension':n,'rank':5,'coefficients':a.tolist(),'radii_best_worst':radii.tolist(),'residuals':residuals,'nonzero_cross_covariance_frobenius':float(np.linalg.norm(cross))}
    infos[name]=I
order=np.linalg.eigvalsh(infos['primary_spin_glide6']-infos['all97_sensitivity']);assert np.all(order>0);results['information_loss_eigenvalues']=order.tolist()
for h in p['history_images']:
    k=h['k'];R=np.array(h['response_5x10']);IH=np.array(h['information_10x10']);Z=np.array(h['null_columns_10x5']);expectedR=np.concatenate((k*np.eye(5),-np.eye(5)),axis=1)
    assert np.array_equal(R,expectedR) and np.array_equal(Z,np.concatenate((np.eye(5),k*np.eye(5)),axis=0))
    rel=float(np.linalg.norm(IH-R.T@infos['primary_spin_glide6']@R)/max(1,np.linalg.norm(IH)))
    nr=float(np.linalg.norm(IH@Z)/max(1,np.linalg.norm(IH)))
    assert rel<1e-12 and nr<1e-12 and np.linalg.matrix_rank(IH,tol=1e-10*np.linalg.norm(IH,2))==5
    assert np.array_equal(IH[:5,5:],np.array(h['endpoint_derivative_cross_5x5']))
    results['histories'].append({'kappa':k,'rank':5,'history_congruence_relative':rel,'null_residual_relative':nr})
for f in p['history_family_q_equals_s']:assert f['signed_gain']==f['k']-1 and f['power_multiplier']==(f['k']-1)**2
power=p['power_frontier'];threshold=power['chi2_threshold'];lam=power['lambda80']
assert abs(chi2.sf(threshold,5)-.05)<1e-12 and abs(ncx2.sf(threshold,5,lam)-.8)<1e-12
griderrors=[]
for row in power['grid']:
    r=row['rho_uasyr'];assert abs(row['sphere_rms_uasyr']-r/np.sqrt(5))<1e-12
    for direction,ev in [('best',power['eigenvalues'][-1]),('worst',power['eigenvalues'][0])]:
        assert abs(row['lambda_'+direction]-r*r*ev)<1e-10
        err=abs(row['power_'+direction]-ncx2.sf(threshold,5,r*r*ev));assert err<1e-12;griderrors.append(err)
results['power']={'alpha_check':float(chi2.sf(threshold,5)),'lambda80_power':float(ncx2.sf(threshold,5,lam)),'grid_max_abs_error':float(max(griderrors)),'radii':[r['rho_uasyr'] for r in power['grid']],'caption':'evaluated markers, connecting segments only guides, thresholds from table and Eq 35'}
E=np.array(p['response']['basis_matrices']);assert np.max(np.abs(np.einsum('aij,bij->ab',E,E)-np.eye(5)))<1e-12
assert np.max(np.abs(E-E.transpose(0,2,1)))==0 and np.max(np.abs(np.trace(E,axis1=1,axis2=2)))==0
results['basis']='five Frobenius orthonormal STF components, signs retained'
results['status']='PASS'
(OUT/'RETAINED_SCIENCE_CHECKS.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
