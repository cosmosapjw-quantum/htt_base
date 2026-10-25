import json, hashlib, math
from pathlib import Path
import numpy as np
P=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r35_p5_fresh_independent_review')
d=np.load(P/'arrays.npz',allow_pickle=False); checks={}
def close(name,a,b,tol=2e-12):
    e=float(np.max(np.abs(np.asarray(a)-np.asarray(b))));assert e<=tol,(name,e)
    checks[name]={'max_abs_error':e,'tolerance':tol,'pass':True}
K=d['fixed_boundary_K'];w=d['fixed_boundary_w'];Om=d['fixed_boundary_Omega'];b=d['fixed_boundary_beta'];g=1/(1-b*b)
E=(1+w)*Om*g*b*b;z=(1+w)*Om*g*b/(2*np.sqrt(K))
close('fixed_density',d['fixed_boundary_Omega_n'],Om*((1+w)*g-w))
close('fixed_tilt_energy',d['fixed_boundary_E_tilt'],E)
close('fixed_pressure',d['fixed_boundary_pressure'],w*Om+E/3)
f=np.zeros((len(K),3));f[:,2]=(1+w)*Om*g*b
close('fixed_flux',d['fixed_boundary_flux'],f)
bc=np.zeros((len(K),3));bc[:,2]=b;close('fixed_chart',d['fixed_boundary_beta_chart'],bc,0)
close('fixed_sigma_squared',d['fixed_boundary_Sigma2'],z*z)
close('fixed_lambda',d['fixed_boundary_Omega_Lambda'],1-K-z*z-Om*((1+w)*g-w))
K=d['envelope_K'];v=float(d['envelope_vmax']);ew=d['envelope_w'][:,None]
# Original rest-density root instead of the producer's stored r-root.
A=(1+ew)**2*v*v/(4*K*(1-v*v)**2);B=(1+ew*v*v)/(1-v*v)
Om=2*(1-K)/(B+np.sqrt(B*B+4*A*(1-K)))
close('envelope_from_rest_density_quadratic',d['envelope_z'],np.sqrt(A)*Om)
close('envelope_squared',d['envelope_sigma2'],A*Om*Om)
close('envelope_supremum',d['envelope_ultrarelativistic'],(1-np.sqrt(K))**2,0)
assert np.all(np.diff(d['envelope_sigma2'],axis=0)>=0)
assert np.all(d['envelope_sigma2']<d['envelope_ultrarelativistic'])
checks['envelope_order_and_strictness']={'pass':True}
# Fixed-density equality branch d=0 and fixed-Lambda equality on a tiny independent grid.
eq=[]
for K,Om,w,Lambda in ((.4,.6,0.,0.),(.2,.3,1/3,.1),(.5,.1,1.,.3)):
    C=(1+w)*Om;a=C*C/(4*K);b=C+a;rem=1-K-Om-Lambda
    t=2*rem/(b+math.sqrt(b*b+4*a*rem));v=math.sqrt(t/(1+t))
    residual=K+Om+C*t+a*t*(1+t)+Lambda-1
    assert abs(residual)<2e-12
    if rem==0: assert v==0
    eq.append({'K':K,'Omega':Om,'w':w,'Omega_Lambda':Lambda,'beta_magnitude':v,'residual':residual})
checks['fixed_lambda_equality_branch']={'pass':True,'cases':eq}
result=json.loads((P/'RESULT.json').read_text())
assert all(result['undefined_sectors'][x]['value'] is None and result['undefined_sectors'][x]['status']=='NOT_EVALUABLE' for x in ('x_C','Q','F','Pi','G_F'))
assert all(result[x] is False for x in ('acceptance_passed','original_acceptance_passed','promotes_original_acceptance'))
assert result['qualified_product'] is None and result['qualified_products']==[]
checks['claim_ceiling_and_undefined_sectors']={'pass':True}
out={'status':'PASS','checks':checks,'check_count':len(checks),'array_sha256':hashlib.sha256((P/'arrays.npz').read_bytes()).hexdigest()}
(OUT/'raw/supplementary_probes.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'status':'PASS','check_count':len(checks)}))
