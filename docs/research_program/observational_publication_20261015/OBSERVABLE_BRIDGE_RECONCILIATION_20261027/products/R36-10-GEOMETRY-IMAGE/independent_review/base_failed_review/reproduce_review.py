"""Independent bounded review. Reads candidate; writes only its own external folder.
No producer main(), archived campaign, ODE, or old CAS validator is executed.
"""
from pathlib import Path
import json, csv, hashlib, importlib.util, sys, math, traceback
import numpy as np
import sympy as sp
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path(__file__).resolve().parent
P=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-10-GEOMETRY-IMAGE'
C=Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_contract_preparation/IMPLEMENTATION_CONTRACT.json')
result=json.loads((P/'RESULT.json').read_text()); table=json.loads((P/'TABLE.json').read_text()); contract=json.loads(C.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw={'reviewer':'/root/r36_geometry_fresh_review','python':sys.version,'numpy':np.__version__,'sympy':sp.__version__,'candidate_sha256':sha(P/'RESULT.json'),'contract_sha256':sha(C),'checks':{},'findings':[]}
assert raw['candidate_sha256']=='54ae8c59cb6c0d144cb9798079f357bdfba6254694cb416bf5a14f3a59160423'
assert raw['contract_sha256']=='76e2c762c4e9fbf4d27ac1af8521c3138edefb138f62e292c776ca83d67bf6b5'
assert all(sha(Path(x['path']))==x['sha256'] and Path(x['path']).stat().st_size==x['bytes'] for x in contract['source_bindings'])
receipt=json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_actual/RAW_RECEIPT.json').read_text())
assert all(sha(Path(x['path']))==x['sha256'] and Path(x['path']).stat().st_size==x['size'] for x in receipt['product_files'])
raw['checks']['identities']={'source_count':len(contract['source_bindings']),'receipt_products':len(receipt['product_files']),'all_match':True}
# Orthonormal coordinate bases built independently.
sq2=math.sqrt(2); eye3=np.eye(3)
NB=np.zeros((6,3,3)); NB[0,0,0]=NB[1,1,1]=NB[2,2,2]=1
for k,(i,j) in enumerate([(0,1),(0,2),(1,2)],3):NB[k,i,j]=NB[k,j,i]=1/sq2
SB=np.array([np.diag([1.,-1,0])/sq2,np.diag([1.,1,-2])/math.sqrt(6),*NB[3:]])
def sv(a): return np.einsum('kij,ij->k',NB,a)
def un(z):return np.einsum('k,kij->ij',z[:6],NB),z[6],np.einsum('k,kij->ij',z[7:],SB)
def ric(n):return 2*(n@n)-np.trace(n)*n+(np.trace(n)**2/2-np.sum(n*n))*eye3
def dr(n,d):return 2*(n@d+d@n)-np.trace(d)*n-np.trace(n)*d+(np.trace(n)*np.trace(d)-2*np.sum(n*d))*eye3
def hr(d,e):return 2*(d@e+e@d)-np.trace(d)*e-np.trace(e)*d+(np.trace(d)*np.trace(e)-2*np.sum(d*e))*eye3
def flux(n,s):
 a=n@s
 return np.array([a[1,2]-a[2,1],a[2,0]-a[0,2],a[0,1]-a[1,0]])
def y(z):
 n,h,s=un(z);r=ric(n)
 return np.r_[sv(r),3*h*h-np.sum(s*s)/2+np.trace(r)/2,flux(n,s)]
def analytical(z):
 n,h,s=un(z);directions=[un(v) for v in np.eye(12)]; J=np.zeros((10,12));H=np.zeros((10,12,12))
 for i,(d,k,t) in enumerate(directions):
  rr=dr(n,d);J[:,i]=np.r_[sv(rr),6*h*k-np.sum(s*t)+np.trace(rr)/2,flux(d,s)+flux(n,t)]
  for j,(e,l,u) in enumerate(directions):
   rr=hr(d,e);H[:,i,j]=np.r_[sv(rr),6*k*l-np.sum(t*u)+np.trace(rr)/2,flux(d,u)+flux(e,t)]
 return J,H
L=np.diag([.05]*7+[.01]*5);L[7,5]=.005
raw['checks']['derivatives_svd_bounds']={}
for name,im in table['images'].items():
 z=np.array(im['z0']);J,H=analytical(z);sj=np.array(im['joint_J']);sh=np.array(im['joint_H'])
 errJ=np.linalg.norm(J-sj);errH=np.linalg.norm(H-sh)
 assert errJ<1e-12 and errH<1e-12
 assert np.linalg.norm(y(z)-np.array(im['Y0']))<1e-12
 svds={}
 for key,A in [('joint_svd',J),('geometry_svd',J[:6,:6])]:
  d=im[key];U=np.array(d['left_singular_coordinates']).T;VT=np.array(d['right_singular_coordinates']);sing=np.array(d['singular_values']);r=d['rank'];q=len(sing)
  recon=np.linalg.norm(A-U[:,:q]@np.diag(sing)@VT[:q]);null=np.linalg.norm(A@VT[r:].T)
  assert recon<1e-12 and null<1e-12
  assert np.linalg.norm(U.T@U-np.eye(U.shape[1]))<1e-12 and np.linalg.norm(VT@VT.T-np.eye(VT.shape[0]))<1e-12
  svds[key]={'rank':r,'reconstruction_error':recon,'null_residual':null}
 bounderr=0.
 dirs=[np.eye(10)[k] for k in range(10)]+[np.r_[np.ones(3),np.zeros(7)],np.r_[sv(np.diag([-1.,2,-1])/math.sqrt(6)),np.zeros(4)]]
 saved=im['bounds10']+[im['scalar_bound'],im['x_D_bound']]
 for w,b in zip(dirs,saved):
  a=np.linalg.norm(L.T@J.T@w); h=np.einsum('k,kij->ij',w,H);bq=.5*max(abs(np.linalg.eigvalsh(L.T@h@L)))
  bounderr=max(bounderr,abs(a-b['linear']),abs(bq-b['quadratic']))
  assert abs(a-b['linear'])<1e-12 and abs(bq-b['quadratic'])<1e-12
 raw['checks']['derivatives_svd_bounds'][name]={'J_error':errJ,'H_error':errH,'bound_error':bounderr,'svd':svds,'energy_lower_bound':im['bounds10'][6]['center']-im['bounds10'][6]['radius'],'h_lower_bound':z[6]-np.linalg.norm(L[6])}
# Independently consume all saved points rather than regenerate the producer.
probes=[json.loads(x) for x in (P/'UNCERTAINTY_PROBES.jsonl').read_text().splitlines()]
maxdirect=maxtaylor=maxlinear=0.;bycenter={k:[] for k in table['images']}
for p in probes:
 im=table['images'][p['center']];z0=np.array(im['z0']);z=np.array(p['z']);xi=np.array(p['xi']);d=L@xi;J,H=analytical(z0)
 assert np.linalg.norm(z-z0-d)<1e-13 and np.linalg.norm(xi)<=1+1e-14
 direct=y(z);linear=y(z0)+J@d;quadratic=linear+.5*np.einsum('i,kij,j->k',d,H,d)
 maxdirect=max(maxdirect,float(np.linalg.norm(direct-p['directY'])));maxtaylor=max(maxtaylor,float(np.linalg.norm(direct-quadratic)));maxlinear=max(maxlinear,float(np.linalg.norm(linear-p['linearY'])))
 assert np.linalg.norm(quadratic-p['quadraticY'])<1e-12
 bycenter[p['center']].append(tuple(xi))
assert maxdirect<1e-12 and maxtaylor<1e-12 and maxlinear<1e-12
assert all(len(x)==577 and len(set(x))==577 for x in bycenter.values())
raw['checks']['saved_probes']={'count':len(probes),'max_direct_error':maxdirect,'max_exact_quadratic_residual':maxtaylor,'max_saved_tangent_error':maxlinear,'unique_per_center':{k:len(set(v)) for k,v in bycenter.items()}}
# Compare direct connection implementation to independent Ricci and 3D Riemann oracles.
spec=importlib.util.spec_from_file_location('r36_candidate',P/'geometry_image.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
Rz=np.array([[.6,-.8,0],[.8,.6,0],[0,0,1.]])
Rx=np.array([[1.,0,0],[0,5/13,-12/13],[0,12/13,5/13]])
def riemann3(r):
 R=np.zeros((3,3,3,3));scalar=np.trace(r);g=np.eye(3)
 for l in range(3):
  for b in range(3):
   for i in range(3):
    for j in range(3):
     R[l,b,i,j]=g[l,i]*r[b,j]+g[b,j]*r[l,i]-g[l,j]*r[b,i]-g[b,i]*r[l,j]-scalar/2*(g[l,i]*g[b,j]-g[l,j]*g[b,i])
 return R
s=np.array([[.1,.02,-.01],[.02,-.05,.03],[-.01,.03,-.05]])
N=np.diag([0.,.7,1.1]);a=np.array([.3,0,0]);r=np.diag([-.26,-.54,.18]);r[1,2]=r[2,1]=-.12
# Independent canonical formula for mixed class-B.
r=np.diag([.5*(N[i,i]**2-(N[(i+1)%3,(i+1)%3]-N[(i+2)%3,(i+2)%3])**2)-2*.3**2 for i in range(3)]);r[1,2]=r[2,1]=-.12
maxframe=0.;scalerecord=[]
for rot in [np.eye(3),Rz,Rx,Rx@Rz]:
 n=rot@N@rot.T;aa=rot@a;ss=rot@s@rot.T;rr=rot@r@rot.T;qq=3*ss@aa+flux(n,ss)
 ee=12-np.sum(ss*ss)/2+np.trace(rr)/2
 got=m.frame(n,aa,2,ss,ee,qq)
 err=max(np.linalg.norm(got['ricci']-rr),np.linalg.norm(got['riemann']-riemann3(rr)),np.linalg.norm(got['codazzi']-qq));maxframe=max(maxframe,float(err));assert err<1e-12
 for u in [1e-30,1e-26,1e-22]:
  scaled=m.frame(n*u,aa*u,2*u,ss*u,ee*u*u,qq*u*u)
  er=float(np.linalg.norm(scaled['ricci']/u**2-rr));assert er<1e-12
  assert np.count_nonzero(scaled['ricci'])>0
  scalerecord.append({'u':u,'normalized_ricci_error':er,'rotation_index':len(scalerecord)//3})
raw['checks']['frame']={'max_ricci_riemann_codazzi_error':maxframe,'mixed_q':(3*s@a+flux(N,s)).tolist(),'dimensional_controls':scalerecord}
# Exact ranks independent of floating SVD, using rational (invertibly rescaled) coordinates.
x=sp.symbols('n11 n22 n33 n12 n13 n23 h s11 s22 s12 s13 s23');n=sp.Matrix([[x[0],x[3],x[4]],[x[3],x[1],x[5]],[x[4],x[5],x[2]]]);ss=sp.Matrix([[x[7],x[9],x[10]],[x[9],x[8],x[11]],[x[10],x[11],-x[7]-x[8]]]);rr=2*n*n-sp.trace(n)*n+(sp.trace(n)**2/2-sp.trace(n*n))*sp.eye(3);ns=n*ss
Y=sp.Matrix([rr[0,0],rr[1,1],rr[2,2],rr[0,1],rr[0,2],rr[1,2],3*x[6]**2-sp.trace(ss*ss)/2+sp.trace(rr)/2,ns[1,2]-ns[2,1],ns[2,0]-ns[0,2],ns[0,1]-ns[1,0]])
J=Y.jacobian(x);ranks={}
for name,diag in [('II',[1,0,0]),('VII0matched',[0,2,1]),('I',[0,0,0]),('flatVII0',[0,1,1])]:
 sub=dict(zip(x,[*diag,0,0,0,2,sp.Rational(1,10),sp.Rational(-1,20),0,0,0]));actual=J.subs(sub)
 zero=dict(sub);zero[x[7]]=zero[x[8]]=0;specified=J.subs(zero)
 ranks[name]={'geometry_rank':actual[:6,:6].rank(),'actual_nonzero_shear_joint_rank':actual.rank(),'zero_shear_joint_rank':specified.rank()}
raw['checks']['exact_ranks']=ranks
# Frozen flat centers must contain S=0 (not the matched-pair shear).
for name in ['I','flatVII0']:
 im=table['images'][name];n,h,ss=un(np.array(im['z0']))
 if np.any(ss):raw['findings'].append({'id':'R36-GEO-01','center':name,'specified_S_bar':np.zeros((3,3)).tolist(),'actual_S_bar':ss.tolist(),'specified_density':12.,'actual_density':im['Y0'][6],'specified_joint_rank':ranks[name]['zero_shear_joint_rank'],'actual_joint_rank':im['joint_svd']['rank']})
# LRS conversion checked against retained signed full rows; no old producer runs.
cp=ROOT/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report/joint_image.csv'
orig=list(csv.DictReader(cp.open()));converted=[json.loads(l) for l in (P/'LRS280.jsonl').read_text().splitlines()];perm=np.array([[0.,0,1],[1,0,0],[0,1,0]]);kap=8*math.pi*6.67430e-11/299792458.**4;ec=12*1e-52/kap
maxlrs=0.;vac=0
for o,c in zip(orig,converted):
 sh=np.array([[float(o[f'shear_{i}{j}']) for j in 'xyz'] for i in 'xyz']);pi=np.array([[float(o[f'pi_{i}{j}']) for j in 'xyz'] for i in 'xyz']);f=np.array([float(o[f'flux_{i}']) for i in 'xyz'])
 expect={'S_bar':2*perm@sh@perm.T,'q_J_m3':ec*perm@f,'pi_J_m3':ec*perm@pi@perm.T,'epsilon_N_J_m3':ec*float(o['Omega_n']),'pressure_J_m3':ec*float(o['pressure'])}
 for k,v in expect.items():
  v=np.asarray(v);er=np.linalg.norm(np.asarray(c[k])-v);scale=np.linalg.norm(v);rel=er/scale if scale else er;assert rel<1e-12;maxlrs=max(maxlrs,float(rel))
 beta=float(o['beta']);assert beta==c['beta_speed_v_over_c'] and abs(beta)<1
 if o['matter_velocity_status']=='UNDEFINED_ABSENT_MATTER':vac+=1;assert c['beta_physical'] is None
 assert c['normal_vorticity_status']=='HYPERSURFACE_ORTHOGONAL' and c['matter_vorticity_status']=='NOT_DETERMINED'
assert len(orig)==len(converted)==280 and np.linalg.det(perm)==1
raw['checks']['lrs']={'rows':len(orig),'vacuum_rows':vac,'max_conversion_relative_error':maxlrs,'proper_permutation':True}
# Exact flat degeneracy controls and nonconstant second-order image.
f=np.diag([0.,1,1]);tangent=np.zeros((3,3));tangent[0,1]=tangent[1,0]=-1
assert np.linalg.norm(dr(f,tangent))==0 and np.linalg.norm(ric(f+.25*tangent))>0
assert all(np.linalg.norm(ric(t*np.diag([1.,0,0])))>0 for t in [.5,.25,.125])
raw['checks']['nonlinear_flat']={'flat_tangent_kernel_norm':float(np.linalg.norm(dr(f,tangent))),'straight_tangent_ricci_norm_at_quarter':float(np.linalg.norm(ric(f+.25*tangent))),'radial_flat_kernel':float(np.linalg.norm(dr(f,f)))}
raw['overall']='HOLD_ONE_FROZEN_CENTER_MISMATCH' if raw['findings'] else 'PASS_SCOPED'
(OUT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(raw,indent=2)+'\n')
print(json.dumps(raw,indent=2))
