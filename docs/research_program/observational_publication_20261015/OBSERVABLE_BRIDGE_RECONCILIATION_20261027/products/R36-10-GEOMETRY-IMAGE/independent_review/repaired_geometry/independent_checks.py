"""Read-only targeted independent R36-10 repair checks; write only review output."""
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import numpy as np
import sympy as sp

OUT = Path(__file__).resolve().parent
REPAIR = Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_repair_actual')
RET = json.loads((REPAIR/'RETURN.json').read_text())
P = Path(RET['result_path']).parent
CONTRACT = Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_contract_preparation/IMPLEMENTATION_CONTRACT.json')
TOL = 4096*np.finfo(float).eps
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def close(x,y,scale=None):
    x,y=np.asarray(x,dtype=float),np.asarray(y,dtype=float)
    if scale is None: scale=np.linalg.norm(x)+np.linalg.norm(y)
    err=float(np.linalg.norm(x-y))
    assert err <= TOL*scale if scale else err==0, (err,scale)
    return err/scale if scale else 0.
assert sha(CONTRACT)=='76e2c762c4e9fbf4d27ac1af8521c3138edefb138f62e292c776ca83d67bf6b5'
assert sha(REPAIR/'RAW_RECEIPT.json')=='b48617edd81b8f51c798a1674486fd2b79f454165e51c14e0e6cc8138c6703e0'
assert sha(P/'RESULT.json')=='ca55901e8b35f163d0c7b011363e364497ba27bea752e142403c9f6d3d37ffa6'
raw=json.loads((REPAIR/'RAW_RECEIPT.json').read_text())
contract=json.loads(CONTRACT.read_text())
for x in raw['product_files']:
    assert sha(x['path'])==x['sha256'] and Path(x['path']).stat().st_size==x['size']
for x in contract['source_bindings']:
    assert sha(x['path'])==x['sha256'] and Path(x['path']).stat().st_size==x['bytes']
assert sha(P.parents[2]/'EVIDENCE_MANIFEST.json')==contract['input_identity'].split(':')[1]
spec=importlib.util.spec_from_file_location('candidate_geometry',P/'geometry_image.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
table=json.loads((P/'TABLE.json').read_text())
old=json.loads((P.parent/'TABLE.json').read_text())

# Independent exact expression in orthonormal tensor coordinates. Differentiate
# symbolically rather than importing the author's polarization implementation.
z=sp.symbols('z0:12',real=True); rt=sp.sqrt
N=sp.Matrix([[z[0],z[3]/rt(2),z[4]/rt(2)],
             [z[3]/rt(2),z[1],z[5]/rt(2)],
             [z[4]/rt(2),z[5]/rt(2),z[2]]])
S=sp.Matrix([[z[7]/rt(2)+z[8]/rt(6),z[9]/rt(2),z[10]/rt(2)],
             [z[9]/rt(2),-z[7]/rt(2)+z[8]/rt(6),z[11]/rt(2)],
             [z[10]/rt(2),z[11]/rt(2),-2*z[8]/rt(6)]])
R=2*N*N-sp.trace(N)*N+(sp.trace(N)**2/2-sp.trace(N*N))*sp.eye(3)
energy=3*z[6]**2-sp.trace(S*S)/2+sp.trace(R)/2
q=[sum(sp.LeviCivita(i,j,k)*N[j,l]*S[k,l] for j in range(3) for k in range(3) for l in range(3)) for i in range(3)]
Y=sp.Matrix([R[0,0],R[1,1],R[2,2],rt(2)*R[0,1],rt(2)*R[0,2],rt(2)*R[1,2],energy,*q]).applyfunc(sp.expand)
J=Y.jacobian(z)
Hs=[sp.hessian(v,z) for v in Y]
Hn=np.array([h.tolist() for h in Hs],dtype=float)
yf=sp.lambdify([z],Y,'numpy');jf=sp.lambdify([z],J,'numpy')
def yfun(v): return np.asarray(yf(v),dtype=float).ravel()
names=['II','VII0matched','I','flatVII0']
centers={}
for name,ns in zip(names,[(1,0,0),(0,2,1),(0,0,0),(0,1,1)]):
    shear=(3/(20*rt(2)),3/(20*rt(6)),0,0,0) if name in names[:2] else (0,)*5
    centers[name]=sp.Matrix([*ns,0,0,0,2,*shear])
L=np.diag([.05]*7+[.01]*5);L[7,5]=.005
ranks={};metrics={};all_bounds={}
for name in names:
    c=centers[name];cv=np.array(c,dtype=float).ravel();sub=dict(zip(z,c))
    exactj=J.subs(sub).applyfunc(sp.simplify);exacty=Y.subs(sub).applyfunc(sp.simplify)
    rj=int(exactj.rank());rg=int(exactj[:6,:6].rank());ranks[name]={'geometry':rg,'joint':rj}
    saved=table['images'][name];jn=np.array(exactj,dtype=float);yn=np.array(exacty,dtype=float).ravel()
    close(saved['z0'],cv);close(saved['Y0'],yn)
    ej=close(saved['joint_J'],jn);eh=close(saved['joint_H'],Hn)
    close(saved['geometry_J'],jn[:6,:6])
    close(m.joint(cv),yn);gj,gh=m.derivatives(cv);close(gj,jn);close(gh,Hn)
    for key,a in [('joint_svd',jn),('geometry_svd',jn[:6,:6])]:
        sv=saved[key];u=np.array(sv['left_singular_coordinates']).T;v=np.array(sv['right_singular_coordinates']);s=np.array(sv['singular_values'])
        close(u.T@u,np.eye(u.shape[1]));close(v@v.T,np.eye(v.shape[0]))
        close(u[:,:len(s)]@np.diag(s)@v[:len(s)],a)
        close(a@v[sv['rank']:].T,np.zeros((a.shape[0],v.shape[0]-sv['rank'])),scale=np.linalg.norm(a))
    assert saved['geometry_svd']['rank']==rg and saved['joint_svd']['rank']==rj
    if name in names[2:]:
        assert saved['Y0'][6]==12 and np.count_nonzero(saved['center_S_bar'])==0
        ctl=table['controls'][name];assert ctl['density_bar']==12 and np.count_nonzero(ctl['S_bar'])==0
        assert np.array_equal(ctl['extrinsic'],-2*np.eye(3))
    # Bound all ten outputs with independent symbolic J,H, plus scalar and D.
    weights=list(np.eye(10));weights += [np.r_[np.ones(3),np.zeros(7)],np.r_[np.array([-1,2,-1])/np.sqrt(6),np.zeros(7)]]
    boundrows=saved['bounds10']+[saved['scalar_bound'],saved['x_D_bound']]
    radii=[]
    for w,b in zip(weights,boundrows):
        linear=np.linalg.norm(L.T@jn.T@w);hw=np.tensordot(w,Hn,axes=1)
        quad=.5*max(abs(np.linalg.eigvalsh(L.T@hw@L)))
        center=float(w@yn);ro=TOL*(abs(center)+linear+quad);rad=linear+quad+ro
        close([b[k] for k in ['center','linear','quadratic','roundoff','radius']],[center,linear,quad,ro,rad])
        radii.append(rad)
    assert cv[6]-np.linalg.norm(L[6])>0 and yn[6]-radii[6]>0
    all_bounds[name]=radii
    metrics[name]={'J_relative_error':ej,'H_relative_error':eh,'energy_lower_bound':float(yn[6]-radii[6]),'h_lower_bound':1.95}
assert [ranks[n]['geometry'] for n in names]==[6,6,0,3]
assert [ranks[n]['joint'] for n in names]==[9,10,1,6]
zi=centers['I'];ji=J.subs(dict(zip(z,zi)));target=sp.zeros(10,12);target[6,6]=12
assert ji==target

rows=[json.loads(l) for l in (P/'UNCERTAINTY_PROBES.jsonl').read_text().splitlines()]
prior=[json.loads(l) for l in (P.parent/'UNCERTAINTY_PROBES.jsonl').read_text().splitlines()]
assert len(rows)==len(prior)==2308
max_probe=0.;match=0;changed=0
for row,base in zip(rows,prior):
    name=row['center'];xi=np.array(row['xi']);cv=np.array(centers[name],dtype=float).ravel();delta=L@xi
    assert len(row['directY'])==len(row['linearY'])==len(row['quadraticY'])==10
    close(row['z'],cv+delta);yn=yfun(cv);jn=np.array(jf(cv),dtype=float)
    direct=yfun(np.array(row['z']));lin=yn+jn@delta;quad=lin+.5*np.einsum('i,kij,j->k',delta,Hn,delta)
    max_probe=max(max_probe,close(row['directY'],direct),close(row['linearY'],lin),close(row['quadraticY'],quad))
    assert np.all(abs(direct-yn)<=np.array(all_bounds[name][:10])+TOL*(np.linalg.norm(direct)+np.linalg.norm(yn)))
    assert row['directY'][:6]==base['directY'][:6]
    assert (row['center'],row['probe'],row['xi'])==(base['center'],base['probe'],base['xi'])
    if name in names[:2]: assert row['directY']==base['directY'];match+=1
    else: changed+=row['directY']!=base['directY']
assert match==changed==1154
for name in names:
    rr=[r for r in rows if r['center']==name];assert len(rr)==577
    assert len({tuple(r['xi']) for r in rr})==577
    counts=[sum(np.isclose(np.linalg.norm(r['xi']),x,rtol=0,atol=1e-15) for r in rr) for x in [0,.5,1]]
    assert counts==[1,288,288]
assert table['matched_orbit_separation']==old['matched_orbit_separation']
assert table['matched_tensor_radius_sum']==old['matched_tensor_radius_sum']
sep=np.linalg.norm(np.sort(np.linalg.eigvalsh(np.diag([.5,-.5,-.5])))-np.sort(np.linalg.eigvalsh(np.diag([-.5,1.5,-1.5]))))
radius=sum(np.linalg.norm(all_bounds[n][:6]) for n in names[:2]);assert sep>radius
close(sep,table['matched_orbit_separation']);close(radius,table['matched_tensor_radius_sum'])

# Selected rational class-B oracle; diagonal Ricci and signed off-diagonal are
# evaluated separately from candidate connection contraction.
a=sp.Rational(3,10);ns=[0,sp.Rational(7,10),sp.Rational(11,10)]
rex=sp.diag(*[(ns[i]**2-(ns[(i+1)%3]-ns[(i+2)%3])**2)/2-2*a*a for i in range(3)])
rex[1,2]=rex[2,1]=a*(ns[1]-ns[2]);assert rex[1,2]==-sp.Rational(3,25)
nm=np.diag([float(x) for x in ns]);av=np.array([float(a),0,0]);sm=np.array([[.1,.02,-.01],[.02,-.05,.03],[-.01,.03,-.05]])
ss=sp.Matrix([[sp.Rational(1,10),sp.Rational(1,50),-sp.Rational(1,100)],[sp.Rational(1,50),-sp.Rational(1,20),sp.Rational(3,100)],[-sp.Rational(1,100),sp.Rational(3,100),-sp.Rational(1,20)]])
nmex=sp.diag(*ns);aex=sp.Matrix([a,0,0]);qex=3*ss*aex+sp.Matrix([sum(sp.LeviCivita(i,j,k)*nmex[j,l]*ss[k,l] for j in range(3) for k in range(3) for l in range(3)) for i in range(3)])
qb=np.array(qex,dtype=float).ravel();eb=float(12-sp.trace(ss*ss)/2+sp.trace(rex)/2)
base=m.frame(nm,av,2.,sm,eb,qb);close(base['ricci'],rex);close(base['momentum'],qb);close(base['codazzi'],qb)
rotations=[np.array([[3/5,-4/5,0],[4/5,3/5,0],[0,0,1]]),np.array([[1,0,0],[0,5/13,-12/13],[0,12/13,5/13]])]
rotations.append(rotations[1]@rotations[0]);scale_metrics=[]
for u in [1e-30,1e-26,1e-22]:
    got=m.frame(nm*u,av*u,2*u,sm*u,eb*u*u,qb*u*u)
    err=close(got['ricci']/u**2,rex);close(got['momentum']/u**2,qb);close(got['codazzi']/u**2,qb)
    assert np.linalg.norm(got['ricci'])>0
    try:m.frame(np.diag([1.,.7,1.1])*u,av*u,2*u,sm*u,eb*u*u,qb*u*u)
    except ValueError as exc: assert str(exc)=='INVALID_JACOBI'
    else: raise AssertionError('tiny Jacobi violation accepted')
    scale_metrics.append({'u_star':u,'Ricci_relative_error':err,'invalid_Jacobi_rejected':True})
for rot in rotations:
    close(np.linalg.det(rot),1.)
    got=m.frame(rot@nm@rot.T,rot@av,2.,rot@sm@rot.T,eb,rot@qb)
    close(got['ricci'],rot@np.array(rex,dtype=float)@rot.T);close(got['momentum'],rot@qb)
    close(got['riemann'],np.einsum('lp,mq,ir,js,pqrs->lmij',rot,rot,rot,rot,base['riemann']))

# All retained bridge rows: only conversion, signed constraints and provenance.
assert sha(P/'LRS280.jsonl')==sha(P.parent/'LRS280.jsonl')=='d0fdfbed607e55bb43cfa0af5c6344e8f3ae5d0bf626d8b68ba8346e75df4921'
lrs=[json.loads(l) for l in (P/'LRS280.jsonl').read_text().splitlines()]
src=list(csv.DictReader(m.CSV.open()));assert len(lrs)==len(src)==280
perm=np.eye(3)[[2,0,1]];vac=0
for row,orig in zip(lrs,src):
    h=2.;unit=12*m.U**2/m.KAPPA
    sm0=np.array([[float(orig[f'shear_{i}{j}']) for j in 'xyz'] for i in 'xyz'])
    pi=np.array([[float(orig[f'pi_{i}{j}']) for j in 'xyz'] for i in 'xyz'])
    flux=np.array([float(orig[f'flux_{i}']) for i in 'xyz'])
    close(row['S_bar'],h*perm@sm0@perm.T);close(row['q_J_m3'],unit*perm@flux)
    close(row['pi_J_m3'],unit*perm@pi@perm.T);close(row['pressure_J_m3'],unit*float(orig['pressure']))
    close(row['epsilon_N_J_m3'],unit*float(orig['Omega_n']))
    close(row['q_J_m3'][0]*m.KAPPA/m.U**2,6*row['a_bar'][0]*h*float(orig['z_s']))
    assert row['matter_velocity_status']==orig['matter_velocity_status']
    if row['matter_velocity_status']=='UNDEFINED_ABSENT_MATTER':assert row['beta_physical'] is None;vac+=1
oldreceipt=json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_actual/RAW_RECEIPT.json').read_text())
for x in oldreceipt['product_files']: assert sha(x['path'])==x['sha256']
pre=Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_actual/RESULT_6878_RECONSTRUCTED_PREIMAGE.json')
assert sha(pre)=='6878b99508cc1b26f3138445f1339788996b03cac6534f45bb930fa23ba256c1'
prej=json.loads(pre.read_text());oldj=json.loads((P.parent/'RESULT.json').read_text());delta=json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r36_geometry_actual/METADATA_DELTA.json').read_text())
for k in delta['scientific_result_fields_equal']:assert prej[k]==oldj[k]
assert not delta['prior_array_hashes_available']
result={'status':'PASS_SCOPED_CHECKS','candidate_identity':RET['candidate_identity'],'source_bindings_verified':13,'candidate_files_verified':9,'old_final_candidate_files_verified':len(oldreceipt['product_files']),
        'exact_sympy_ranks':ranks,'center_derivatives_and_Hessians':metrics,'independent_probe_count':len(rows),'independent_max_probe_relative_error':max_probe,
        'all_Ricci_probes_exact_against_old_final':2308,'matched_joint_probes_exact_against_old_final':match,'flat_joint_probes_changed':changed,
        'bound_separation':float(sep),'bound_tensor_radii_sum':float(radius),'scale_controls':scale_metrics,'proper_rotation_checks':3,
        'mixed_exact_Ricci':str(rex),'mixed_exact_signed_momentum':str(qex),'lrs_rows':280,'vacuum_rows_null_beta':vac,
        'metadata_6878_preimage_verified':True,'old_6878_array_hashes':'UNAVAILABLE_NOT_RETROACTIVELY_VERIFIED',
        'producer_invocations':0,'old_campaign_invocations':0,'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN'}
(OUT/'INDEPENDENT_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
