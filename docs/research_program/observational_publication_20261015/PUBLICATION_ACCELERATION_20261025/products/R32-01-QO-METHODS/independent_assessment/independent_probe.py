"""Small independent arithmetic/source-consumption probe; no quadrature or CAS."""
from pathlib import Path
from fractions import Fraction as F
from itertools import product, permutations
import csv, datetime, hashlib, json, math, time

start=time.perf_counter()
stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
base=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025')
report=base/'products/R32-01-QO-METHODS/report'
out=Path(__file__).resolve().parent
I=range(3)
triples=list(product(I, repeat=3))
def mm(A,B): return [[sum(A[i][k]*B[k][j] for k in I) for j in I] for i in I]
def mv(A,v): return [sum(A[i][j]*v[j] for j in I) for i in I]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def det(A): return sum((-1)**sum(p[i]>p[j] for i in I for j in I if i<j)*math.prod(A[i][p[i]] for i in I) for p in permutations(I))
def chi(Q,v):
    qv=mv(Q,v); qqv=mv(Q,qv)
    return det([[v[i],qv[i],qqv[i]] for i in I])
def lift(Q,w):
    qw=mv(Q,w)
    return {(i,j,k):(w[i]*Q[j][k]+w[j]*Q[i][k]+w[k]*Q[i][j])/3-F(2,15)*((i==j)*qw[k]+(i==k)*qw[j]+(j==k)*qw[i]) for i,j,k in triples}
def contract(Q,O): return [sum(O[i,j,k]*Q[j][k] for j in I for k in I) for i in I]
def eps(a,b,c):
    return 0 if len({a,b,c})<3 else (-1)**sum(p>q for p,q in [(a,b),(a,c),(b,c)])
def cross(Q):
    Q2=mm(Q,Q)
    return {key:sum(Q2[i][a]*eps(a,j,b)*Q[b][k] for i,j,k in permutations(key) for a in I for b in I)/6 for key in triples}

controls=[]
for rawQ in [((1,2,0),(2,-1,1),(0,1,0)),((-1,0,0),(0,0,0),(0,0,1)),((1,0,0),(0,1,0),(0,0,-2)),((0,0,0),(0,0,0),(0,0,0))]:
    Q=[[F(x) for x in row] for row in rawQ]; w=[F(2),F(-3),F(5)]
    Q2=mm(Q,Q); Q3=mm(Q2,Q); t=sum(x*x for row in Q for x in row); j=sum(Q3[i][i] for i in I)
    M=[[t*F(i==k,3)+F(2,5)*Q2[i][k] for k in I] for i in I]
    O=lift(Q,w); v=contract(Q,O); K=cross(Q)
    assert all(sum(O[i,i,k] for i in I)==0 for k in I)
    assert all(O[key]==O[p] for key in triples for p in permutations(key))
    assert v==mv(M,w)
    assert sum(x*x for x in O.values())==dot(w,mv(M,w))
    assert det(M)==F(64,675)*t**3+F(8,1125)*j*j
    assert sum(K[i,jj,k]*v[i]*v[jj]*v[k] for i,jj,k in triples)==chi(Q,v)
    assert 12*sum(x*x for x in K.values())==t**3-6*j*j
    controls.append({'Q':rawQ,'t':str(t),'j':str(j),'chi':str(chi(Q,v)),'exact_identities':True})

# Bound (35), finite controls only. General validity follows from seven
# determinant terms and Hadamard, reviewed separately in REVIEW.md.
ratios=[]
for diag in [(1,-1,0),(1,1,-2),(-3,1,2)]:
    Q=[[F(diag[i] if i==j else 0) for j in I] for i in I]
    op=max(map(abs,diag))
    for delta in [(F(1,10),0,0),(F(-1,20),F(2,25),F(1,30)),(F(1),F(-2),F(3))]:
        v0=[F(1,3),F(-2,5),F(5,7)]; v=[x+y for x,y in zip(v0,delta)]
        h=math.sqrt(float(dot(delta,delta))); n=math.sqrt(float(dot(v0,v0)))
        bound=op**3*((n+h)**3-n**3)
        ratio=abs(float(chi(Q,v)-chi(Q,v0)))/bound
        assert ratio<=1+1e-14
        ratios.append(ratio)

result=json.loads((report/'RESULT.json').read_text())
hashes={}
for p,entry in result['artifacts'].items():
    path=report/p
    actual=hashlib.sha256(path.read_bytes()).hexdigest()
    assert actual==entry['sha256'],p
    hashes[p]=actual
for p,expected in result['inputs'].items():
    path=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')/p
    assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,p
payload=json.loads((base/'evidence/baseline/research/theory_bridge_result.json').read_text())
rows=payload['rows']
with (report/'generated/optical_rows.csv').open() as fh:
    exported=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(fh)]
assert rows==exported
summary=json.loads((report/'generated/summary.json').read_text())
assert summary['selected_rows']==[rows[i] for i in [0,11,22,33,44]]
assert len(rows)==45
previous=0
kappa=5/math.log(10)
errors=[]
for row in rows:
    a=row['amplitude']; e=1.6*a
    assert a>previous; previous=a
    assert all(math.isfinite(x) for x in row.values())
    E3=math.sqrt(35/2)*kappa*e**3/(3*(1-e))
    # Direct independent norm formula for d0=(1,2,3)/sqrt(14), S0=(.6,-.2,-.4):
    # S0:S0=.56; |S0 d0|^2=(.36+.16+1.44)/14=.14.
    quadratic=kappa*a*a*math.sqrt(.56/3+2*.14/5)
    cubic=kappa*a**3*math.sqrt(2/5)/3
    errors.append(max(abs(E3-row['remainder_bound']),abs(quadratic-row['coupled_quadratic_norm']),abs(cubic-row['pure_dipole_cubic_norm'])))
    assert errors[-1]<1e-12
    assert row['coupled_remainder_norm']<=E3
assert max(row['quadrature_difference'] for row in rows)==payload['max_quadrature_tensor_difference']
table=(report/'generated/optical_table.tex').read_text()
for i in [0,11,22,33,44]:
    for k in ['amplitude','coupled_exact_norm','coupled_quadratic_norm','coupled_remainder_norm','remainder_bound']:
        m,e=f'{rows[i][k]:.5e}'.split('e')
        assert f'{m}\\times10^{{{int(e)}}}' in table
probe={'status':'PASS_FINITE_ARITHMETIC_AND_SOURCE_CONSUMPTION','started_utc':stamp,'duration_seconds':time.perf_counter()-start,'exact_fraction_controls':controls,'determinant_margin_control_count':len(ratios),'maximum_margin_ratio':max(ratios),'retained_optical_rows':45,'max_analytic_scalar_error':max(errors),'all_candidate_artifact_hashes_match':True,'all_bound_input_hashes_match':True,'candidate_result_sha256':hashlib.sha256((report/'RESULT.json').read_bytes()).hexdigest(),'candidate_pdf_sha256':hashes['main.pdf'],'candidate_tex_sha256':hashes['main.tex'],'limits':'Finite arithmetic supports direct proof review; no general theorem inferred from tests. No quadrature, old provenance replay, CAS, solver or ODE executed.'}
(out/'probe_result.json').write_text(json.dumps(probe,indent=2)+'\n')
print(json.dumps(probe,indent=2))
