import importlib.util,sys,json,hashlib,time
from pathlib import Path
from dataclasses import replace
import numpy as np
r=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');sys.path.insert(0,str(r/'scripts'))
import run_reboot_cf4_selected as d
p=r/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json';packet,sample,sources=d.intake(r,p)
o=r/'docs/observational_reboot_20261014/results/cf4/quadrature_refinement_v1';o.mkdir(exist_ok=True)
from scipy.special import logsumexp
start=time.monotonic()
def terms(law,t):
 f,z=law.row_terms(t);num=logsumexp(law.log_eta_w+f.sum(0));den=logsumexp(law.log_eta_w+z.sum(0));return {'numerator':float(num),'normalizer':float(den),'logL':float(num-den)}
rows=[]
for i in (2,5):
 oldp=r/f'docs/observational_reboot_20261014/results/cf4/selected_v2/sensitivity_{i:02d}.json';old=json.loads(oldp.read_text());scenario=replace(d.Scenario(**packet['baseline']),**old['change']);theta=old['fit']['best']['theta'];grids=[]
 for nx,ne in ((256,64),(384,96),(512,128)):
  law=d.SelectedLaw(sample,scenario,nx,ne);grids.append({'orders':[nx,ne],**terms(law,theta)})
 row={'index':i,'change':old['change'],'original_path':str(oldp),'original_sha256':d.digest(oldp),'original_failed_delta':old['refined_abs_logL_difference'],'old_theta':theta,'old_theta_grids':grids,'threshold':1e-6,'hard_cap':[512,128]}
 if abs(grids[-1]['logL']-grids[-2]['logL'])<1e-6:
  fit=law.fit(starts=[theta],maxiter=400);best=fit['best'];new=best['theta'];fine=terms(law,new);coarse=terms(d.SelectedLaw(sample,scenario,384,96),new);delta=abs(fine['logL']-coarse['logL']);row.update(fit=fit,new_theta_fine=fine,new_theta_coarse=coarse,refined_abs_logL_difference=delta,objective_improvement_512=fine['logL']-grids[-1]['logL'],boundary=bool(np.any(np.isclose(new,[40,-1500,-1500,-1500]))or np.any(np.isclose(new,[110,1500,1500,1500]))),status='ACCEPTED_CONDITIONAL_QUADRATURE' if best['success'] and delta<1e-6 else 'QUADRATURE_UNRESOLVED')
 else:row['status']='QUADRATURE_UNRESOLVED'
 rows.append(row);d.write_json(o/f'refinement_{i:02d}.json',row)
d.write_json(o/'result.json',{'task':'RB07','source':sources,'refinements':rows,'authority':'Astra/xhigh read-only bounded refinement approval, observedUNKNOWN','seconds':time.monotonic()-start,'code_sha256':d.digest(Path(__file__)),'law_sha256':d.digest(d.module_path),'claim':'same conditional models and1e-6criterion; no tolerancechange'})
(o/'refine_rb07.py').write_text(Path(__file__).read_text());print([(x['index'],x['status'])for x in rows])
