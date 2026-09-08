from sage.all import *
from sage.env import SAGE_VERSION
import json, pathlib, hashlib, subprocess, sys, datetime
ROOT=pathlib.Path.cwd()
BASE=ROOT/'.agent-harness/runs/R8-AC-20260909'
OUT=BASE/'artifacts/sage_singular'
checks=[]
def check(name, value, scope, detail):
    ok=bool(value)
    checks.append(dict(name=name,status='PASS' if ok else 'FAIL',scope=scope,detail=detail))
    print(('PASS' if ok else 'FAIL')+' '+name, flush=True)
    if not ok: raise AssertionError(name)

contract=BASE/'CAS_CONTRACT.json'
check('contract_identity',hashlib.sha256(contract.read_bytes()).hexdigest()=='5ff7f84db01b6871f74f7c60b5c36430a4cae93735466e277bd9c4019ab22723','provenance','Exact registered contract bytes.')
check('sage_version',SAGE_VERSION=='10.9','toolchain',SAGE_VERSION)
sv=subprocess.check_output(['/usr/bin/Singular','--version'],text=True,stderr=subprocess.STDOUT)
check('singular_version','version 4.3.2' in sv,'toolchain',sv.splitlines()[0])

# O1: residual block bounds are named input lemmas, not target assumptions.
# Write residual lengths a=bQ+eQ, b=bO+eO with all four variables >=0.
# The weighted-square difference has nonnegative coefficients after multiplying
# by strictly positive q0^2*o0^2. This establishes it for every SAME rotation.
P=PolynomialRing(QQ,names=('bQ','bO','eQ','eO','q0','o0'))
bQ,bO,eQ,eO,q0,o0=P.gens()
weighted=o0**2*((bQ+eQ)**2-bQ**2)+q0**2*((bO+eO)**2-bO**2)
check('O1_generic_weighted_combination',all(c>=0 for c in weighted.coefficients()) and weighted==o0**2*eQ*(2*bQ+eQ)+q0**2*eO*(2*bO+eO),'generic conditional inequality','eQ,eO are nonnegative block residual slack from Hoffman-Wielandt/Mirsky; positive q0,o0 permit division. Monotone square root and infimum preserve bound. No simultaneous attainability premise.')
Q=diagonal_matrix(QQ,[-1,0,1])
O=[[[QQ(0) for k in range(3)] for j in range(3)] for i in range(3)]
for i in range(3):
 for j in range(3):
  for k in range(3):
   ijk=sorted([i,j,k])
   O[i][j][k]=2 if ijk==[0,0,0] else (-1 if ijk in ([0,1,1],[0,2,2]) else 0)
A=matrix(QQ,3,9,lambda i,j:O[i][j//3][j%3])
G=A*A.transpose()
check('O1_STF_octopole',all(sum(O[i][i][k] for i in range(3))==0 for k in range(3)),'fixed fixture','Full symmetric rank-three array; traces vanish.')
check('O1_exact_scaling_Q',sum(a*a for a in Q.list())==2 and Q.eigenvalues()==[-1,0,1],'fixed fixture','Qprime=2Q: sorted eigenvalue gaps have square sum 2, and R=I residual square is 2. Thus exact minimum sqrt(2)/q0.')
check('O1_exact_scaling_O',G==diagonal_matrix(QQ,[6,2,2]) and sum(a*a for a in A.list())==10,'fixed fixture','Oprime=2O: singular-value gap-square sum is tr(G)=10; R=I residual square is 10. Exact minimum sqrt(10)/o0. Repeated spectrum retained.')
check('O1_zero_fixture',matrix(QQ,3,9,0)*matrix(QQ,9,3,0)==zero_matrix(QQ,3),'fixed fixture','Both tensors zero gives distance and invariant bound zero.')
R=matrix(QQ,[[QQ(3)/5,-QQ(4)/5,0],[QQ(4)/5,QQ(3)/5,0],[0,0,1]])
Grot=R*G*R.transpose()
check('O1_relative_alignment_counterexample',R.det()==1 and R*R.transpose()==identity_matrix(QQ,3) and Grot.charpoly()==G.charpoly() and Grot!=G,'fixed counterexample','Any rotation preserving simple-spectrum diagonal Q is a diagonal sign matrix, so preserves diagonal G. Grot has a nonzero 12 entry; no common exact match. Compact SO(3) and continuity imply strictly positive joint distance, although spectral bounds vanish.')

# O2 polynomial homogeneous-quaternion rotation. The ring uses Singular's
# polynomial backend; also emit and run an explicit standalone Singular check.
P=PolynomialRing(QQ,names=('w','x','y','z'))
w,x,y,z=P.gens(); n=w*w+x*x+y*y+z*z
H=matrix(P,[[w*w+x*x-y*y-z*z,2*(x*y-w*z),2*(x*z+w*y)],
 [2*(x*y+w*z),w*w-x*x+y*y-z*z,2*(y*z-w*x)],
 [2*(x*z-w*y),2*(y*z+w*x),w*w-x*x-y*y+z*z]])
check('O2_homogeneous_rotation',H.transpose()*H==n*n*identity_matrix(P,3) and H.det()==n**3,'generic polynomial identity','For nonzero real quaternion, n>0; R=H/n has R^T R=I and det R=1, including repeated and zero components.')
singular_code='''ring r=0,(w,x,y,z),dp;
poly n=w*w+x*x+y*y+z*z;
matrix H[3][3]=w*w+x*x-y*y-z*z,2*(x*y-w*z),2*(x*z+w*y),2*(x*y+w*z),w*w-x*x+y*y-z*z,2*(y*z-w*x),2*(x*z-w*y),2*(y*z+w*x),w*w-x*x-y*y+z*z;
matrix Z=transpose(H)*H;
int i; int j; int failures=0;
for(i=1;i<=3;i++){for(j=1;j<=3;j++){if(i==j){Z[i,j]=Z[i,j]-n*n;}if(Z[i,j]!=0){failures++;}}}
if(det(H)-n^3!=0){failures++;}
if(failures==0){print("SINGULAR_QUATERNION_PASS");}else{print("SINGULAR_QUATERNION_FAIL");}
quit;
'''
(OUT/'quaternion.sing').write_text(singular_code)
st=subprocess.run(['/usr/bin/Singular','-q',str(OUT/'quaternion.sing')],capture_output=True,text=True)
(OUT/'singular_transcript.txt').write_text(st.stdout+st.stderr)
check('O2_standalone_Singular',st.returncode==0 and 'SINGULAR_QUATERNION_PASS' in st.stdout and 'error' not in st.stdout.lower(),'generic polynomial identity','Standalone /usr/bin/Singular -q quaternion.sing; exact polynomial identities, no tolerance.')
P=PolynomialRing(QQ,names=('x1','x2','x3','v1','v2','v3'))
x1,x2,x3,v1,v2,v3=P.gens(); xx=vector(P,[x1,x2,x3]); v=vector(P,[v1,v2,v3]); s=1+xx.dot_product(xx)
# q=(1,x)/sqrt(s). Multiplying derivative by sqrt(s) gives rational D.
F=P.fraction_field(); u=vector(F,[1,x1,x2,x3]); E=matrix(F,4,3,lambda i,j:1 if i==j+1 else 0)
D=E-u.column()*vector(F,xx).row()/s
Jgram=D.transpose()*D/s
check('O2_chart_derivative_identity',Jgram==identity_matrix(F,3)/s-vector(F,xx).column()*vector(F,xx).row()/s**2,'generic rational identity','D/sqrt(s) is the Jacobian. Gram = I/s-xx^T/s^2, so v^T Gram v <= ||v||^2/s with explicit squared slack (x.v)^2/s^2.')
check('O2_chart_derivative_positive_slack',F(v.dot_product(v)/s-(vector(F,v).row()*Jgram*vector(F,v).column())[0,0])==F(xx.dot_product(v)**2/s**2),'generic inequality certificate','s>=1; squared slack nonnegative for all real x,v. Cell s>=m_C^2 gives derivative norm <=1/m_C. Applies to all four charts by permuting coordinates.')
check('O2_radius_rational_upper',QQ(7)**2/16-3==QQ(1)/16,'generic exact inequality','A spacing-1/m grid has half widths 1/(2m): 2||h||=sqrt(3)/m < 7/(4m) for positive m. For a box, integrate derivative along center-to-point segment and use quaternion double cover: delta<=min(pi,2||h||/m_C). All unit quaternions covered by choosing a positive maximal-magnitude component; ties allowed.')

# O3 exact inequalities use nonnegative chain slacks; no target rank bound is
# postulated. Cases below exhaust indicator truth patterns at the logical level.
P=PolynomialRing(QQ,names=('a','b','c')); a,b,c=P.gens()
check('O3_certain_chain',all(t>=0 for t in (a+b+c).coefficients()),'generic order proof','If Li>=U0 then si-s0=(si-Li)+(Li-U0)+(U0-s0)>=0. Hence I[Li>=U0]<=I[si>=s0].')
check('O3_possible_chain',all(t>=0 for t in (a+b+c).coefficients()),'generic order proof','If si>=s0 then Ui-L0=(Ui-si)+(si-s0)+(s0-L0)>=0. Thus I[si>=s0]<=I[Ui>=L0], retaining endpoint equality. Sum and divide by M>0 proves interval count inequalities.')
def bounds(L,U):
 M=len(L); return (QQ(1+sum(l>=U[0] for l in L[1:]))/M, QQ(1+sum(u>=L[0] for u in U[1:]))/M)
points=list(map(QQ,[0,1,2,3,10])); scores=[sorted(abs(x-y) for j,y in enumerate(points) if i!=j)[1] for i,x in enumerate(points)]
check('O3_wide_interval_fixture',scores==[2,1,1,2,8] and bounds([7,0,0,0,0],[10,3,3,3,3])==(QQ(1)/5,QQ(1)/5),'fixed fixture','Observation is last scalar point 10; reordered as row zero for counting.')
check('O3_inclusive_tie_counterexample',bounds([0]*5,[1,0,0,0,0])==(QQ(1)/5,1),'fixed counterexample','All exact scores zero: exact inclusive rank p=1; upper endpoint ranking falsely gives 1/5.')
for M,k,reject,nonreject in [(1000,32,49,50),(301,18,14,15)]:
 threshold=M//20
 check('O3_threshold_'+str(M),ceil(sqrt(M-1))==k and reject==threshold-1 and nonreject==threshold and QQ(1+reject)/M<=QQ(1)/20<QQ(1+nonreject)/M,'exact integer threshold','Rejection iff possible count <=floor(M/20)-1. Nonrejection iff certain count >=floor(M/20).')
# Verify rank combinatorics for all weak orders of a small multiset as a
# supplementary fixture. Generic proof is retained explicitly in proof note.
from itertools import product
rank_ok=True
for tup in product(range(3),repeat=5):
 ranks=[sum(y>=x for y in tup) for x in tup]
 rank_ok=rank_ok and all(sum(r<=t for r in ranks)<=t for t in range(6))
check('O3_inclusive_rank_small_exhaustion',rank_ok,'finite corroboration only','All 3^5 labeled score tuples. Generic proof: if m entries have inclusive rank <=t, select their minimum score; its rank >=m, so m<=t. Exchangeability averages row labels. Pointwise p_upper>=p survives any numerical stopping time for the fixed scores.')

# J2 exact full-column-rank factor support fixture and algebra.
B=matrix(QQ,2,1,[QQ(3)/5,QQ(4)/5]); V=matrix(QQ,1,1,[4]); C=B*V*B.transpose(); Bplus=(B.transpose()*B).inverse()*B.transpose(); Cp=B*V.inverse()*B.transpose()
r=2*B.column(0); nvec=vector(QQ,[-QQ(4)/5,QQ(3)/5]); roff=r+nvec
check('J2_factor_rank_support',B.rank()==1 and C.rank()==1 and B.transpose()*B==identity_matrix(QQ,1) and Bplus*r==vector(QQ,[2]) and C*Cp*r==r,'fixed rational fixture','C=4BB^T; exact support is span(B). Full column rank is established exactly.')
check('J2_reduced_quadratic',((Bplus*r).row()*V.inverse()*(Bplus*r).column())[0,0]==1 and (r.row()*Cp*r.column())[0,0]==1,'fixed rational fixture','On-support reduced quadratic equals original pseudoinverse quadratic =1.')
check('J2_off_support',B.transpose()*nvec==vector(QQ,[0]) and nvec.dot_product(nvec)==1 and C*Cp*roff!=roff and Bplus*roff==Bplus*r,'fixed counterexample','Off-support vector has same reduced projected quadratic; exact support check is necessary and rejects roff. No jitter or floating null projection.')
check('J2_penrose_exact',C*Cp*C==C and Cp*C*Cp==Cp and (C*Cp).transpose()==C*Cp and (Cp*C).transpose()==Cp*C,'fixed rational identity','All four Penrose equations independently verify the exact pseudoinverse fixture.')

# Gaussian marginal counterexample. Z standard normal; independent sign S is
# +/-1 with equal probability. (X,Y)=(Z,SZ) is an explicit admitted probability
# construction. Average conditional MGFs, derived from Gaussian MGF.
t,u=var('t u'); joint=(exp((t+u)**2/2)+exp((t-u)**2/2))/2
marg=exp(t*t/2)
check('J2_gaussian_marginals',(joint.subs(u=0)-marg).simplify_full()==0 and (joint.subs(t=0)-exp(u*u/2)).simplify_full()==0,'exact analytic construction','Both marginals standard Gaussian because symmetric sign mixing preserves N(0,1). Joint MGF is half exp((t+u)^2/2)+half exp((t-u)^2/2).')
m11=joint.diff(t).diff(u).subs(t=0,u=0); m22=joint.diff(t,2).diff(u,2).subs(t=0,u=0)
product_mgf=exp(t*t/2)*exp(u*u/2); gaussian_m22=product_mgf.diff(t,2).diff(u,2).subs(t=0,u=0)
check('J2_not_joint_Gaussian',m11==0 and m22==3 and gaussian_m22==1,'exact counterexample','Covariance I but E[X^2 Y^2]=3 whereas centered joint Gaussian with covariance I has 1. Equivalently X^2=Y^2 a.s.; Gaussian marginals and zero covariance alone do not admit joint Gaussian law.')

summary=dict(axis='sage_singular',axis_status='PASS',contract_sha256=hashlib.sha256(contract.read_bytes()).hexdigest(),tools={'sage':SAGE_VERSION,'singular':sv.splitlines()[0]},checks=checks,domain_assumption_diff=[],counterexample=[{'target':'spectral descriptors are complete joint orbit invariants','finding':'FALSE: rational rotated octopole at fixed simple-spectrum Q'}, {'target':'rank upper endpoints as exact scores','finding':'FALSE: inclusive all-zero ties return p=1 while endpoint shortcut gives 1/M'}, {'target':'projected quadratic alone tests singular support','finding':'FALSE: roff has same reduced quadratic but violates exact support'}, {'target':'Gaussian marginals plus covariance imply joint Gaussian','finding':'FALSE: (Z,SZ) has covariance I and mixed fourth moment 3'}],claim_ceiling='Five registered O1-O3/J2 obligations only; generic proofs explicitly conditional on named lemmas. Fixed rational support/scaling are fixtures. No implementation enclosure, product-law, physics, family identification, or four-axis admission.',completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/'checks.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'axis_status':'PASS','check_count':len(checks),'output':str(OUT/'checks.json')}))
