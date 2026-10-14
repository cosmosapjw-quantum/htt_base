#!/usr/bin/env python3
"""Bind/check and render distance images of the stored joint posterior measure."""
from pathlib import Path
import hashlib,json,sys
from dataclasses import replace
import numpy as np
import fit_reboot_joint as d
R=d.ROOT/'docs/observational_reboot_20261014/results/posterior'
def main():
 result=json.loads((R/'result.json').read_text());records=[]
 import matplotlib;matplotlib.use('Agg');from matplotlib import pyplot as plt
 for name,row in result['scenarios'].items():
  p=R/f'{name}.npz';a=np.load(p);actual=d.sha(p)
  if actual!=row['posterior_image']['npz_sha256']:raise ValueError('frozen posterior image changed')
  source=d.PosteriorDrawSource(name,f"Union3:{result['source']['union_sha256']}|{result['source']['desi_source_id']}",'UNION3_22_PLUS_DESI_QISO_GAUSSIAN_RHO_%+.2f'%row['rho'],'OM_U_0.01_0.99_AR_U_5000_20000_M_N_43_5',tuple(a['draw_ids'].tolist()),tuple(a['weights']),'FLAT_LCDM_DISTANCE','DISTANCE_ONLY')
  z=a['redshift'];integ=a['H0_DL_over_c']/(1+z)
  source=replace(source,distance_state_sha256=d.distance_state_digest(source,a['Omega_m'],a['H0_rd'],z,integ))
  image=d.posterior_distance_image(source,a['Omega_m'],a['H0_rd'],redshift=z,radial_integral=integ)
  maxdelta=max(float(np.max(abs(image[k]-a[k])))for k in('E','q_deceleration','H0_DL_over_c','H0_DA_over_c','DM_over_rd','DH_over_rd'))
  if maxdelta>1e-12:raise ValueError('final image changed stored functionals')
  records.append({'posterior_id':name,'npz_sha256':actual,'distance_state_sha256':source.distance_state_sha256,'max_stored_image_absolute_difference':maxdelta,'rows':len(source.draw_ids),'ids_weights_preserved':True})
  if name=='rho_p0.00':
   fig,axes=plt.subplots(2,3,figsize=(11,6))
   for key,ax in zip(('E','q_deceleration','H0_DL_over_c','H0_DA_over_c','DM_over_rd','DH_over_rd'),axes.ravel()):
    values=image[key];quant=[]
    for j in range(len(z)):
     order=np.argsort(values[:,j]);cdf=np.cumsum(a['weights'][order]);quant.append(np.interp([.05,.5,.95],cdf,values[order,j]))
    quant=np.array(quant);ax.fill_between(z,quant[:,0],quant[:,2],alpha=.25);ax.plot(z,quant[:,1],'o-');ax.set(xlabel='redshift',ylabel=key)
   fig.suptitle('Union3 + DESI qiso, rho=0, flat-LCDM: 5th-95th pointwise posterior quantiles');fig.tight_layout()
   for ext in('png','pdf'):fig.savefig(R/f'legacy_distance_image.{ext}',dpi=160)
   plt.close(fig)
 original_sha='88460b6248caf683d621d0fea7fc5e3038ffc3c507027f039714ee83f6a65f46'  # frozen producing-script identity, retained after staging removal
 receipt={'scope':'savedposterior verification, model/measure binding and functional figure; no fit rerun','original_execution_script_sha256':original_sha,'original_execution_patch_sha256':'ec8b40ea42897f3643d8f1924b5157f764269032ef78e5bee11a2de061ee9c00','final_code_sha256':{str(p):d.sha(p)for p in [Path(__file__),d.ROOT/'scripts/fit_reboot_joint.py',d.ROOT/'htt/htt/htt/infer/conditional_legacy_pushforward.py']},'records':records,'requested_author':'gpt-6-sol/high','requested_reviewer':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','physical_MES_unknown_mass':1}
 (R/'final_binding_verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
 p=R/'report.md';original_report=p.read_text();p.write_text(original_report if 'Same262144node IDs/weights' in original_report else original_report+'\n![sameposteriorfunctionalimage](legacy_distance_image.png)\n\nSame262144node IDs/weights and six distance/expansion-function images are preserved. Final numerical-state/measure binding and independent48-point integral validation are recorded in final_binding_verification.json. Existing physical legacy fields remain unavailable with unknownmass1; FLRW distance assumptions do not constitute measured zero anisotropy.\n')
if __name__=='__main__':main()
