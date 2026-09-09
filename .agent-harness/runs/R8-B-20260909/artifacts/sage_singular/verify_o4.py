"""Exact O4 verification; execute with sage -python. Stdout is one JSON document."""
import hashlib
import itertools
import json
import subprocess
from pathlib import Path
from sage.all import QQ, PolynomialRing, NumberField
from sage.version import version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CONTRACT_SHA = '430f325399b7caf0e7513cccec64e5bdae114ecafa5ce039747e373936c82f9d'
contract_path = ROOT / '.agent-harness/runs/R8-B-20260909/CAS_CONTRACT.json'
assert hashlib.sha256(contract_path.read_bytes()).hexdigest() == CONTRACT_SHA
contract = json.loads(contract_path.read_text())
for source in contract['identity']['source_input_hashes']:
    assert hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest() == source['sha256']
assert version == '10.9', version
singular_version = subprocess.run(['/usr/bin/Singular', '--version'], capture_output=True, text=True, check=True).stdout.splitlines()[0]
assert 'version 4.3.2 ' in singular_version, singular_version
# Rational coefficients and one algebraic extension I^2=-1; no numerical complex arithmetic.
T = PolynomialRing(QQ, 't')
K = NumberField(T.gen()**2+1, 'I')
I = K.gen()
names = ['A']+[f'{v}{j}' for v in 'uvw' for j in range(1,4)]+['z']
R = PolynomialRing(K, names, order='degrevlex')
A, *rest = R.gens()
u, v, w, z = rest[:3], rest[3:6], rest[6:9], rest[9]
perms = list(itertools.permutations(range(3)))
idx2 = list(itertools.product(range(3), repeat=2))
idx3 = list(itertools.product(range(3), repeat=3))
dot = lambda x,y: sum(a*b for a,b in zip(x,y))

def stf2(a,x,y):
    return {(i,j): a*((x[i]*y[j]+y[i]*x[j])/2-(i==j)*dot(x,y)/3) for i,j in idx2}

def stf3(a,x,y,t):
    vectors = (x,y,t)
    b = [(dot(x,y)*t[k]+dot(x,t)*y[k]+dot(y,t)*x[k])/3 for k in range(3)]
    out = {}
    for i,j,k in idx3:
        raw = sum(vectors[p[0]][i]*vectors[p[1]][j]*vectors[p[2]][k] for p in perms)/6
        out[i,j,k] = a*(raw-((i==j)*b[k]+(i==k)*b[j]+(j==k)*b[i])/5)
    return out

Q, O = stf2(A,u,v), stf3(A,u,v,w)
residuals = {key: [] for key in contract['target']['exact_test_obligations']}
qres, ores, nres = residuals.values()
qres.extend(Q[i,j]-Q[j,i] for i,j in idx2)
qres.append(sum(Q[i,i] for i in range(3)))
for alternate in (stf2(A,v,u), stf2(-A,[-x for x in u],v)):
    qres.extend(Q[key]-alternate[key] for key in idx2)
qres.extend(stf2(R.zero(),u,v).values())
for key in idx3:
    ores.extend(O[key]-O[tuple(key[p] for p in perm)] for perm in perms)
ores.extend(sum(O[i,i,k] for i in range(3)) for k in range(3))
for perm in perms:
    alt = stf3(A,*[(u,v,w)[p] for p in perm])
    ores.extend(O[key]-alt[key] for key in idx3)
alt = stf3(-A,[-x for x in u],v,w)
ores.extend(O[key]-alt[key] for key in idx3)
ores.extend(stf3(R.zero(),u,v,w).values())
n = [1-z*z,I*(1+z*z),2*z]
nres.extend([dot(n,n), sum(Q[i,j]*n[i]*n[j] for i,j in idx2)-A*dot(u,n)*dot(v,n), sum(O[i,j,k]*n[i]*n[j]*n[k] for i,j,k in idx3)-A*dot(u,n)*dot(v,n)*dot(w,n)])
sage_checks = {key: all(f == 0 for f in values) for key,values in residuals.items()}
# Independently construct unreduced formulas as strings for the external Singular engine.
# This does NOT export Sage-reduced residuals (which would only check zero==zero).
def sdot(x,y):
    return '('+'+'.join(f'({a})*({b})' for a,b in zip(x,y))+')'
def sq(a,x,y,i,j):
    return f'({a})*((({x[i]})*({y[j]})+({y[i]})*({x[j]}))/2-{int(i==j)}*{sdot(x,y)}/3)'
def so(a,x,y,t,i,j,k):
    b = [f'({sdot(x,y)}*({t[h]})+{sdot(x,t)}*({y[h]})+{sdot(y,t)}*({x[h]}))/3' for h in range(3)]
    vs=(x,y,t)
    raw='('+'+'.join(f'({vs[p[0]][i]})*({vs[p[1]][j]})*({vs[p[2]][k]})' for p in perms)+')/6'
    return f'({a})*({raw}-({int(i==j)}*({b[k]})+{int(i==k)}*({b[j]})+{int(j==k)}*({b[i]}))/5)'
su,sv,sw = [[f'{x}{j}' for j in range(1,4)] for x in 'uvw']
sQ=lambda a,x,y: {key:sq(a,x,y,*key) for key in idx2}
sO=lambda a,x,y,t: {key:so(a,x,y,t,*key) for key in idx3}
qq,oo=sQ('A',su,sv),sO('A',su,sv,sw)
sres=[[],[],[]]
sres[0].extend(f'({qq[i,j]})-({qq[j,i]})' for i,j in idx2)
sres[0].append('+'.join(qq[i,i] for i in range(3)))
for alt in (sQ('A',sv,su), sQ('-A',['-'+x for x in su],sv)):
    sres[0].extend(f'({qq[key]})-({alt[key]})' for key in idx2)
sres[0].extend(sQ('0',su,sv).values())
for key in idx3:
    sres[1].extend(f'({oo[key]})-({oo[tuple(key[p] for p in perm)]})' for perm in perms)
sres[1].extend('+'.join(oo[i,i,k] for i in range(3)) for k in range(3))
for perm in perms:
    alt=sO('A',*[(su,sv,sw)[p] for p in perm])
    sres[1].extend(f'({oo[key]})-({alt[key]})' for key in idx3)
alt=sO('-A',['-'+x for x in su],sv,sw)
sres[1].extend(f'({oo[key]})-({alt[key]})' for key in idx3)
sres[1].extend(sO('0',su,sv,sw).values())
sn=['(1-z^2)','(I*(1+z^2))','(2*z)']
sres[2].append(sdot(sn,sn))
sres[2].append('+'.join(f'({qq[i,j]})*{sn[i]}*{sn[j]}' for i,j in idx2)+f'-A*{sdot(su,sn)}*{sdot(sv,sn)}')
sres[2].append('+'.join(f'({oo[i,j,k]})*{sn[i]}*{sn[j]}*{sn[k]}' for i,j,k in idx3)+f'-A*{sdot(su,sn)}*{sdot(sv,sn)}*{sdot(sw,sn)}')
lines=['ring r=(0,I),('+','.join(names)+'),dp;', 'minpoly=I^2+1;', 'int failures;', 'poly residual;']
for label, expressions in zip(residuals,sres):
    lines.append('failures=0;')
    for exp in expressions:
        lines += [f'residual={exp};','if (residual!=0) { failures=failures+1; }']
    lines.append(f'print("{label}:"+string(failures));')
lines.append('quit;')
singular_source='\n'.join(lines)+'\n'
(HERE/'verify_o4.sing').write_text(singular_source)
proc=subprocess.run(['/usr/bin/Singular','-q',str(HERE/'verify_o4.sing')],capture_output=True,text=True,timeout=300)
(HERE/'singular_stdout.txt').write_text(proc.stdout)
(HERE/'singular_stderr.txt').write_text(proc.stderr)
expected=[f'{key}:0' for key in residuals]
assert proc.returncode == 0 and proc.stdout.splitlines() == expected and not proc.stderr, (proc.returncode,proc.stdout,proc.stderr)
singular_checks={key:True for key in residuals}
payload={'checks':{key:sage_checks[key] and singular_checks[key] for key in residuals}, 'domain_assumption_diff':[], 'counterexample':None, 'contract_sha256':CONTRACT_SHA, 'axis':'sage_singular', 'sage_checks':sage_checks,'singular_checks':singular_checks,'residual_counts':{key:len(values) for key,values in residuals.items()}, 'tool_versions':{'sage':version,'singular':'4.3.2'},'coefficient_domain':'Q(I)[A,u1,u2,u3,v1,v2,v3,w1,w2,w3,z], I^2=-1', 'monomial_order':'degrevlex / Singular dp','localization':'none; only fixed rational divisors 2,3,5,6','singular_loci':'A=0 and coincident vectors included'}
assert all(payload['checks'].values()), payload
serialized=json.dumps(payload,sort_keys=True,indent=2)+'\n'
(HERE/'checks.json').write_text(serialized)
print(serialized,end='')
