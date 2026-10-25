from pathlib import Path
import json, hashlib, importlib.util, sys, platform, math, collections
import numpy as np
import sympy as sp
import mpmath as mp
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_fourth_repair_fresh_review')
PA=ROOT/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
CAND=PA/'products/R32-04-BANDPASS-BOUNDS/repair_04'
PACKET=Path('/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/NEXT_AFTER_BP_FOURTH_REPAIR.json')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda name,obj:(OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
pkt=json.loads(PACKET.read_text()); ack=json.loads((PACKET.parent/'BP_FOURTH_REPAIR_REVIEW_ACTUAL_ACK_GO.json').read_text())
assert ack['acknowledged'] and ack['go'] and ack['agent_id']=='/root/rc_7c8579ab3edafb11'
assert all(pkt[k]==ack[k] for k in ('packet_id','input_identity','candidate_identity'))
assert pkt['candidate_identity']=='sha256:'+sha(CAND/'ARTIFACT_MANIFEST.json')
man=json.loads((CAND/'ARTIFACT_MANIFEST.json').read_text())
manifest_checks=[]
for x in man['files']:
 p=CAND/x['path']; v={'path':x['path'],'sha256':sha(p),'size_bytes':p.stat().st_size}
 assert v['sha256']==x['sha256'] and v['size_bytes']==x['size_bytes']; manifest_checks.append(v)
spec=importlib.util.spec_from_file_location('reviewed_candidate',CAND/'consumer.py'); c=importlib.util.module_from_spec(spec); spec.loader.exec_module(c)
assert sha(c.SOURCE)==c.SOURCE_SHA
write('raw/BINDING.json',dict(packet={k:pkt[k] for k in ('campaign','task_id','attempt','phase','packet_id','input_identity','candidate_identity','frontier_identity','task_spec_identity')},ack=ack,manifest_checks=manifest_checks,consumer_sha256=sha(CAND/'consumer.py'),source_sha256=sha(c.SOURCE),environment={'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,'sympy':sp.__version__,'mpmath':mp.__version__},requested_runtime=pkt['route']['requested'],observed_runtime='UNKNOWN'))
source=json.loads(c.SOURCE.read_text())['branches']
R=lambda x:sp.Rational(*float(x).as_integer_ratio())
M=lambda q:mp.mpf(int(q.p))/int(q.q)
serialize=lambda o:json.loads(json.dumps({k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in o.items()},allow_nan=False))
records=[]; errors=[]; structural=[]
single=np.zeros(24); single[0]=1
mixed=np.array([(-1.)**j*(j+1)/24 for j in range(24)]); mixed/=np.linalg.norm(mixed)
for name in c.BRANCHES:
 F=np.array(source[name]['F2']['matrix_7xk']); a=np.ones(7)
 for metric,d in [('raw_identity',np.ones(9)),('common_reference',c.D)]:
  sol=c.solve_metric(F,a,d)
  G=sp.Matrix([[R(F[i,j])/R(d[j]) for j in range(9)] for i in range(7)])
  A=G[1:,:]-sp.ones(6,1)*G[0,:]
  W=(A*A.T).inv(method='DM'); h=G[0,:]*A.T
  ell2=1/((G[0,:]*G[0,:].T)[0]-(h*W*h.T)[0])
  def reference(Y):
   j0=sp.Rational(0); center=[]
   for j in range(24):
    y=sp.Matrix([R(x) for x in Y[:,j]])
    v=y[1:,:]-sp.ones(6,1)*y[0]
    j0+=(v.T*W*v)[0]; center.append(y[0]-(h*W*v)[0])
   return j0,center
  # All 12 immutable branch/metric pairs; normal scales and narrow BP-05 range controls.
  for scale,perturb in [(1.,1e-4),(1e-148,1e-4),(1e-150,1e-12)]:
   for carrier_name,carrier in [('single',single),('mixed',mixed)]:
    Y=np.tile(scale*carrier,(7,1)); Y[0,0]+=scale*perturb; Y[6,0]-=scale*perturb
    if carrier_name=='mixed':Y[0,13]+=scale*perturb/2; Y[6,13]-=scale*perturb/2
    j0,center=reference(Y)
    with mp.workdps(130): base=float(mp.sqrt(M(j0)))
    for factor in [.5,2.]:
     rho=base*factor; o=serialize(c.identified(Y,F,a,d,sol,rho)); budget=R(rho)**2
     rec=dict(branch=name,metric=metric,scale=scale,perturb=perturb,carrier=carrier_name,rho_hex=rho.hex(),factor=factor,status=o['status'])
     if o['status']=='EMPTY':
      if not budget<j0: errors.append(dict(rec,error='false EMPTY'))
     elif o['status']=='BALL':
      with mp.workdps(130):
       b=M(budget); jj=M(j0); ee=M(ell2); rr=mp.mpf(o['radius']); cc=[M(q) for q in center]
       dc=mp.sqrt(sum((mp.mpf(o['center'][j])-cc[j])**2 for j in range(24)))
       low=jj+ee*(rr-dc)**2; high=jj+ee*(rr+dc)**2; tol=mp.mpf('1e-9')*max(b,jj)
       err=max(abs(high-b),abs(low-b)); ratio=err/tol
       rec.update(sphere_error_over_policy=str(ratio),center_cost_over_budget=str((jj+ee*dc**2)/b),radius_hex=o['radius'].hex())
       if rr<=0 or ratio>1 or b<=jj:errors.append(dict(rec,error='BALL geometry policy violation'))
       bound=mp.mpf(o['geometry_error']['budget_image_error_bound'])
       rec['sphere_error_over_reported_bound']=str(err/bound)
       if err>bound:errors.append(dict(rec,error='understated image bound'))
       maxw=mp.mpf(0)
       dirs=[np.eye(24)[j] for j in range(24)]+[mixed]
       for direction in dirs:
        for sign in [-1,1]:
         point=np.array(o['center'])+sign*o['radius']*direction
         cost=jj+ee*sum((mp.mpf(float(point[j]))-cc[j])**2 for j in range(24))
         maxw=max(maxw,abs(cost-b)/tol)
       rec['max_rounded_witness_error_over_policy']=str(maxw)
       if maxw>1:errors.append(dict(rec,error='rounded boundary witness violation'))
     else:
      assert o['status'] in ['NUMERIC_RANGE_HOLD','NUMERIC_BOUNDARY_HOLD','BOUNDARY_UNCERTAIN']
      assert o['radius'] is None and o['radius_uncertainty']['reason']
     records.append(rec)
  # Adjacent structural subnormal budgets: finite binary64 radii can still lose the fixed policy.
  for rho in [float.fromhex('0x0.0000000000001p-1022'),float.fromhex('0x0.0000000000040p-1022'),float.fromhex('0x0.00000000007e8p-1022'),1e-310,1e-300,1.]:
   Y=np.zeros((7,24)); o=serialize(c.identified(Y,F,a,d,sol,rho)); rec=dict(branch=name,metric=metric,Y='exact zero 7x24',rho_hex=rho.hex(),status=o['status'],radius_hex=o['radius'].hex() if o['radius'] is not None else None,radius_uncertainty=o['radius_uncertainty'])
   if o['status']=='BALL':
    ratio=ell2*R(o['radius'])**2/R(rho)**2
    rec.update(exact_cost_over_budget=str(sp.N(ratio,60)),error_over_fixed_policy=str(sp.N(abs(ratio-1)*10**9,60)),exact_policy_violation=bool(abs(ratio-1)>sp.Rational(1,10**9)),positive_radius=bool(o['radius']>0))
    if rec['exact_policy_violation']:
     rec['error']='structural BALL radius violates unchanged policy'
   else: assert o['status']=='NUMERIC_RANGE_HOLD' and o['radius'] is None
   structural.append(rec)
  for Y in [np.zeros((7,24)),np.tile(mixed,(7,1))]:
   o=serialize(c.identified(Y,F,a,d,sol,0.)); assert o['status'] in ['SINGLETON_EXACT_ZERO','SINGLETON_EXACT_STRUCTURAL'] and o['radius']==0.
  if name=='A_BT_1e-06' and metric=='raw_identity':
   rho=float.fromhex('0x0.00000000007e8p-1022'); o=serialize(c.identified(np.zeros((7,24)),F,a,d,sol,rho)); ratio=ell2*R(o['radius'])**2/R(rho)**2
   counter=dict(finding_id='BP-05-STRUCTURAL-RANGE-REMAINS',class_='numeric',source_sha256=c.SOURCE_SHA,candidate_identity=pkt['candidate_identity'],consumer_sha256=sha(CAND/'consumer.py'),branch=name,metric=metric,Y='exact zero 7x24',a='exact seven ones',rho_hex=rho.hex(),reported_status=o['status'],reported_radius_hex=o['radius'].hex(),reported_J0=o['J0'],reported_center='exact zero 24',reported_radius_uncertainty=o['radius_uncertainty'],exact_ell_squared=str(sp.N(ell2,70)),exact_cost_over_budget=str(sp.N(ratio,70)),relative_budget_excess=str(sp.N(ratio-1,70)),error_over_fixed_policy=str(sp.N((ratio-1)*10**9,70)),exact_rational_violation=bool(ratio>1+sp.Rational(1,10**9)),serialized_witness='s[0]=reported radius, all other coordinates zero; exactly representable',mathematics='G=F diag(d)^-1; A=G[1:,:]-ones(6,1)G[0,:]; W=(A A.T)^-1; h=G[0,:] A.T; ell2=1/(g0 g0.T-h W h.T). At Y=0, exact J(s)=ell2*||s||^2. Cost/rho2 is an exact rational comparison, with no binary64 squared quantities.')
   counter['ell2_fraction']=[str(ell2.p),str(ell2.q)]; counter['cost_ratio_fraction']=[str(ratio.p),str(ratio.q)]
   write('raw/STRUCTURAL_COUNTEREXAMPLE.json',counter)
summary=dict(generic_count=len(records),generic_status_counts=dict(collections.Counter(x['status'] for x in records)),generic_failures=errors,structural_count=len(structural),structural_policy_violations=sum(bool(x.get('exact_policy_violation')) for x in structural),max_generic_sphere_error_over_policy=max((float(x.get('sphere_error_over_policy',0)) for x in records),default=0),max_generic_witness_error_over_policy=max((float(x.get('max_rounded_witness_error_over_policy',0)) for x in records),default=0))
write('raw/INDEPENDENT_RANGE_AUDIT.json',dict(summary=summary,generic=records,structural=structural))
print(json.dumps(summary,indent=2))
# Exact original BP-05 and BP-04 inputs are reused solely as bounded regression falsifiers.
checks=[]
F=np.array(source['A_BT_1e-06']['F2']['matrix_7xk']); a=np.ones(7); d=np.ones(9); sol=c.solve_metric(F,a,d)
for name,old in [('BP05',Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_third_repair_fresh_review/RESULT.json'))]:
 q=json.loads(old.read_text())['counterexample'];Y=np.zeros((7,24));Y[:,0]=[float.fromhex(x) for x in q['Y_col0_hex']];o=serialize(c.identified(Y,F,a,d,sol,float.fromhex(q['rho_hex'])));assert o['status']=='NUMERIC_RANGE_HOLD' and o['radius'] is None;checks.append(dict(case=name,output=o))
q=json.loads((CAND/'RESULT.json').read_text())['bp04_serialized_geometry'];Y=np.zeros((7,24));Y[:,0]=[float.fromhex(x) for x in q['Y_col0_hex']];o=serialize(c.identified(Y,F,a,d,sol,float.fromhex(q['rho_hex'])));assert o['status']=='NUMERIC_BOUNDARY_HOLD' and o['radius'] is None;checks.append(dict(case='BP04',output=o))
Y=np.zeros((7,24));Y[0,0]=1
for rho in [sys.float_info.max,math.inf,math.nan,-1.]:
 try:c.identified(Y,F,a,d,sol,rho)
 except ValueError:checks.append(dict(case='domain',rho=str(rho),status='ValueError'))
 else:raise AssertionError('nonfinite/overflow budget accepted')
Y[:]=sys.float_info.max/2;Y[6,0]=np.nextafter(Y[6,0],math.inf);o=serialize(c.identified(Y,F,a,d,sol,1.));assert o['status']=='NUMERIC_RANGE_HOLD';checks.append(dict(case='finite norm overflow',output=o))
write('raw/REGRESSION_CONTROLS.json',checks)
old=CAND.parent/'repair_03';new_result=json.loads((CAND/'RESULT.json').read_text());old_result=json.loads((old/'RESULT.json').read_text());parity=[]
for b in c.BRANCHES:
 for metric in ['common_reference','raw_identity']:
  assert new_result['branches'][b][metric]==old_result['branches'][b][metric];parity.append(dict(branch=b,metric=metric,compact_exact=True))
for p in sorted((CAND/'report/generated').glob('*')):
 assert p.read_bytes()==(old/'report/generated'/p.name).read_bytes()
 parity.append(dict(path=str(p.relative_to(CAND)),sha256=sha(p),bytes_equal=True))
write('raw/PARITY.json',parity)
for x in manifest_checks:assert sha(CAND/x['path'])==x['sha256']
assert 'sha256:'+sha(CAND/'ARTIFACT_MANIFEST.json')==pkt['candidate_identity']
print('manifest final identity verified; prior BP04/BP05, domain controls, compact/NPZ/table parity pass')
