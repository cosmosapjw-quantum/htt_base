import os,pathlib
OUT=pathlib.Path(__file__).resolve().parent
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MPLCONFIGDIR=str(OUT/'mpl'))
import importlib.util,json,math,hashlib
import numpy as np
import sympy as sp
import mpmath as mp
mp.mp.dps=140
C=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-04-BANDPASS-BOUNDS/repair_05')
s=importlib.util.spec_from_file_location('actual_candidate',C/'consumer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert hashlib.sha256(pathlib.Path(m.__file__).read_bytes()).hexdigest()=='61eeec1f35728f6dddd786e63485f22286c44bfe883a27757688092f782f52d1'
source=json.loads(m.SOURCE.read_text())['branches'];records=[]
R=lambda x:sp.Rational(*float(x).as_integer_ratio());H=sp.zeros(6,7)
for i in range(6):H[i,i]=1;H[i,6]=-1
for b in m.BRANCHES:
 F=np.array(source[b]['F2']['matrix_7xk']);a=np.ones(7)
 for metric,d in [('common',m.D),('raw',np.ones(9))]:
  G=sp.Matrix([[R(F[i,j])/R(d[j]) for j in range(9)] for i in range(7)]);K=G*G.T;W=(H*K*H.T).inv(method='DM');h=K[6,:]*H.T
  e2=1/(K[6,6]-(h*W*h.T)[0]);sol=m.solve_metric(F,a,d)
  for carrier in ['zero','mixed24']:
   center=np.zeros(24) if carrier=='zero' else np.array([(-1)**j*(j+1)/16 for j in range(24)])
   for rho in [1e-310,1e-315]:
    o=m.identified(np.tile(center,(7,1)),F,a,d,sol,rho);record=dict(branch=b,metric=metric,carrier=carrier,rho_hex=rho.hex(),status=o['status'])
    if rho==1e-310:assert o['status']=='BALL',record
    if o['status']=='BALL':
     r=o['radius'];assert 0<r<np.finfo(float).tiny
     discrepancy=abs(e2*R(r)**2-R(rho)**2);rel=discrepancy/R(rho)**2
     assert rel<=sp.Rational(1,10**9),record
     bound=o['geometry_error']['budget_image_error_bound'];assert isinstance(bound,str) and mp.mpf(bound)>0
     assert mp.mpf(int(discrepancy.p))/int(discrepancy.q)<=mp.mpf(bound)
     assert o['geometry_error']['bound_encoding']['budget_image_error_bound']=='decimal_string_upward'
     record.update(radius_hex=r.hex(),relative_discrepancy=str(mp.mpf(int(rel.p))/int(rel.q)),positive_encoded_bound=bound)
    else:assert o['status']=='NUMERIC_RANGE_HOLD' and o['radius'] is None and o['radius_uncertainty']['reason'],record
    records.append(record)
(OUT/'subnormal_positive_result.json').write_text(json.dumps(dict(case_count=len(records),failures=[],records=records),indent=2)+'\n')
print(json.dumps(dict(case_count=len(records),balls=sum(r['status']=='BALL' for r in records),holds=sum(r['status']=='NUMERIC_RANGE_HOLD' for r in records),max_relative_discrepancy=max(float(r.get('relative_discrepancy',0)) for r in records),failures=[]),indent=2))
