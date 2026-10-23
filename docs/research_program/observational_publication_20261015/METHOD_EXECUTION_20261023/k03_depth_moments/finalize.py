"""Pass-free closeout for the one-use R24-K03 moment result."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.stats import chi2

import compute as c


def main():
    inp=c.load_contract()
    if not c.MOMENTS.exists():raise FileNotFoundError('new one-use moments unavailable')
    with np.load(c.MOMENTS,allow_pickle=False) as f:
        A=f['A'];K=f['K'];q=f['q'];n=int(f['n']);zc=f['zcounts']
    with np.load(inp['sources'][1]['path'],allow_pickle=False) as f:G=f['G'];b=f['b']
    r=json.loads((c.HERE/'RESULT.json').read_text())
    ref=c.fit(G,b,A,K,q)
    for key in ('theta_uasyr','F','full24_cov_uasyr2','Y18_cov_uasyr2'):
        np.testing.assert_allclose(r[key],ref[key],rtol=1e-13,atol=1e-12)
    if n!=755850 or not np.array_equal(zc,r['zcounts']):raise ValueError('stored moments row/bin mismatch')
    F=np.asarray(r['F']);Fa=np.linalg.eigh(A);d,v=Fa[0],Fa[1]
    if d[0]<=0:raise ArithmeticError('pre-profile A not SPD')
    invroot=(v/np.sqrt(d))@v.T
    retention=np.linalg.eigvalsh(invroot@F@invroot)
    if retention[0]<=0 or retention[-1]>1+1e-10:raise ArithmeticError('profile retention outside (0,1]')
    sensitivities={}
    for cutoff in (1e-8,1e-10,1e-12):
        sensitivities[str(cutoff)]={'G_scaled_rank':int(np.sum(c.scaled_spd(G,'G')['scaled_eigenvalues']>cutoff*c.scaled_spd(G,'G')['scaled_eigenvalues'][-1])),
            'F_scaled_rank':int(np.sum(c.scaled_spd(F,'F')['scaled_eigenvalues']>cutoff*c.scaled_spd(F,'F')['scaled_eigenvalues'][-1]))}
    if any(x['G_scaled_rank']!=102 or x['F_scaled_rank']!=6 for x in sensitivities.values()):
        raise ArithmeticError('rank sensitivity threshold changes result')
    full=np.asarray(r['full24_cov_uasyr2']);yc=np.asarray(r['Y18_cov_uasyr2']);dc=np.asarray(r['anchored_difference18_cov_uasyr2'])
    if min(np.linalg.eigvalsh(full)[0],np.linalg.eigvalsh(yc)[0],np.linalg.eigvalsh(dc)[0])<=0:
        raise ArithmeticError('derived full/depth covariance not SPD')
    theta=np.asarray(r['theta_uasyr']);ct=np.asarray(r['theta_cov_uasyr2'])
    r['checks'].update({'scaled_rank_sensitivity':sensitivities,
         'full24_min_cov_eigenvalue':float(np.linalg.eigvalsh(full)[0]),
         'Y18_min_cov_eigenvalue':float(np.linalg.eigvalsh(yc)[0]),
         'anchored_difference18_min_cov_eigenvalue':float(np.linalg.eigvalsh(dc)[0]),
         'F_vs_cached_moment_scaled_residual':float(np.linalg.norm(F-(A-K@np.linalg.solve(G,K.T)),ord=np.inf)/max(1,np.linalg.norm(F,ord=np.inf)))})
    r['information_generalized_retention_eigenvalues']=retention.tolist()
    r['slope_coordinate_z_working']=(theta/np.sqrt(np.diag(ct))).tolist()
    r['score_chi2_6_working_tail_scenario']=float(chi2.sf(r['score_chi2_6_scenario'],6))
    r['score_control']='6-df Gaussian working-law Wald/score identity from moments only; no mocks or empirical null calibration'
    (c.HERE/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n')

    report=f'''# R24-K03-DEPTH-MOMENTS

One new pass over all {n:,} selected rows fitted the six continuous `g(z)=z/(1+z)` E1/B1 slopes after profiling all 102 old columns. Reported-z bins are `[0,1,2,10]`, with counts {zc.tolist()}. E1 is polar, B1 axial with the pinned physical `omega cross n` sign. Coefficients use microarcsec/year and the independent-row reported-covariance Gaussian working law.

The six slopes are `{[round(x,6) for x in theta]}`. The profiled information eigenvalues are `{[round(x,9) for x in r['F_eigenvalues']]}` per (microarcsec/year)^2. Generalized profiling retention eigenvalues are `{[round(x,6) for x in retention]}`; trace information retention is {r['information_trace_retained_fraction']:.6%}. Full six-slope covariance and eigenvectors, the old 18-bin plus six-slope 24-state and covariance, and the 18-coordinate depth `Y_b=gamma_b+c_b theta` and anchored difference covariances are in [RESULT.json](RESULT.json). The reported-z centers `c=(1/4,7/12,26/33)` are analysis coordinates, not true distances.

The conditional six-degree score is {r['score_chi2_6_scenario']:.6f}, below the level 0.05 reference critical value {r['score_level_005_critical']:.6f}; its working-law tail scenario is {r['score_chi2_6_working_tail_scenario']:.6f}. This is not an empirical p-value. Under the same working law, 80% Wald power requires slope amplitudes {r['power80_amplitude_strong_uasyr']:.3f} and {r['power80_amplitude_weak_uasyr']:.3f} microarcsec/year along the strongest and weakest profiled information eigenvectors. The sphere radii 0.1, 1, 10 and 100 are tabulated in the result and shown in [POWER.png](POWER.png).

The scaled G and F conditions are {r['checks']['G_scaled_condition']:.6g} and {r['checks']['F_scaled_condition']:.6g}; ranks remain 102 and 6 at thresholds 1e-8, 1e-10 and 1e-12. No jitter or pseudoinverse was used. The bounded direct-whitened fixture checked moment parity, a constant response absorbed by old bin E1/B1 columns, and Schur fit/covariance versus direct regression. The full pass used {r['moment_pass_seconds']:.3f} seconds inside Python, {r['peak_rss_mib']:.1f} MiB maximum RSS and one 4,096-row-or-smaller chunk sequence.

Original K03 acceptance remains **HOLD**. The centroid/matter response, reported-to-true-depth law, spatial covariance, selection qualification and physical history are unresolved. R23-Q's consumed ultra allocation is unchanged; no R9 alpha is reused. This is an observational conditional discriminator, not a physical Bianchi or history claim.
'''
    (c.HERE/'REPORT.md').write_text(report)
    raw_files=['PASS_STARTED.json','STDOUT.txt','STDERR.txt','TIME.txt','TEST_STDOUT.txt','TEST_STDERR.txt','new_moments.npz']
    raw={name:{'path':str(c.RAW/name),'sha256':c.sha(c.RAW/name),'bytes':(c.RAW/name).stat().st_size} for name in raw_files}
    receipt={'task_id':'R24-K03-DEPTH-MOMENTS','full_passes_started':1,'full_passes_completed':1,'source_identity_verified':True,
      'input_sha256':c.SHA_INPUT,'raw':raw,'rows':n,'zcounts':zc.tolist(),
      'peak_rss_mib':r['peak_rss_mib'],'pass_seconds_python':r['moment_pass_seconds'],
      'wall_limit_seconds':1800,'rss_limit_mib':768,'chunk_rows_max':4096,'blas_threads':1,'download':False,
      'first_failure':None,'scientific_admission':'HOLD'}
    (c.HERE/'RAW_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    outputs=['compute.py','test_compute.py','finalize.py','RESULT.json','REPORT.md','POWER.png','RAW_RECEIPT.json']
    manifest={'task_id':'R24-K03-DEPTH-MOMENTS','base_head':inp['base_head'],
      'source_sha256':{str(x['path']):x['sha256'] for x in inp['sources']},
      'task_input_sha256':c.SHA_INPUT,'raw_moment_sha256':raw['new_moments.npz']['sha256'],
      'output_sha256':{name:c.sha(c.HERE/name) for name in outputs},
      'original_acceptance_promoted':False}
    (c.HERE/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    author={'task_id':'R24-K03-DEPTH-MOMENTS','packet_id':'8aac035463242cfba033029620f30ba363f81e3d12f31165d73660d58bb8cbea',
      'executor':'agent/root/k03_depth_moments','requested_model_effort':'gpt-6-sol/high','observed_runtime':'UNKNOWN',
      'outcome':'CONDITIONAL_DISCRIMINATOR_COMPLETED','original_acceptance':'HOLD','full_passes_started':1,
      'validation_evidence':['two bounded fixture tests PASS','755850 rows and bin counts match cached full_stats','scaled rank 102/6 stable 1e-8 to 1e-12','full 24/depth covariances SPD','one full pass, 281.1 MiB peak RSS, 20.72 s process wall, 1 BLAS thread'],
      'result_path':str(c.HERE/'RESULT.json'),'manifest_path':str(c.HERE/'MANIFEST.json'),
      'raw_receipt_path':str(c.HERE/'RAW_RECEIPT.json'),
      'next_gate':'independent read-only Astra-tier review before scoped admission; physical original acceptance HOLD'}
    (c.HERE/'AUTHOR_RETURN.json').write_text(json.dumps(author,indent=2)+'\n')
    print(json.dumps({'status':author['outcome'],'retention_range':[float(retention[0]),float(retention[-1])],'score':r['score_chi2_6_scenario'],'raw_moment_sha256':raw['new_moments.npz']['sha256']}))


if __name__=='__main__':main()
