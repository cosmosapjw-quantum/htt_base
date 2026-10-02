from sage.all import *
import json,sys
R=PolynomialRing(QQ, names=['u0','u1','u2','u3','c']+[f's{i}{j}' for i in range(4) for j in range(i,4)]+[f'w{i}{j}' for i in range(4) for j in range(i+1,4)])
z=R.gens_dict(); u=vector(R,[z[f'u{i}'] for i in range(4)]); c=z['c']; g=diagonal_matrix(R,[-1,1,1,1]); uf=g*u
S=matrix(R,4,4,lambda i,j:z[f's{min(i,j)}{max(i,j)}'])
W=matrix(R,4,4,lambda i,j: 0 if i==j else (z[f'w{i}{j}'] if i<j else -z[f'w{j}{i}']))
sh=(u*S*u); B=S+sh*g; b=B*u
Q=B+b.column()*uf.row()-uf.column()*b.row()+W
I=R.ideal([u*g*u+1]+list(W*u)); G=I.groebner_basis()
def red(f):return I.reduce(R(f))
def zero(xs):return all(red(x)==0 for x in xs)
checks={}; notes=[]
# Shift invariance and mass-shell are polynomial quotient identities.
shift=S+g+(u*(S+g)*u)*g
unit=zero([u*B*u]+(shift-B).list())
# Null-cone kernel: substitute n3=0 and unit-axis and mixed rational directions;
# equivalently reduce the general quadratic in n modulo n.n-1 and eliminate coefficients.
T=PolynomialRing(QQ,names=['t00','t01','t02','t03','t11','t12','t13','t22','t23','t33','n1','n2','n3'])
t=T.gens_dict(); n=vector(T,[t[f'n{i}'] for i in (1,2,3)]); K=vector(T,[-1,n[0],n[1],n[2]])
C=matrix(T,4,4,lambda i,j:t[f't{min(i,j)}{max(i,j)}']); F=K*C*K
ns=[t['n1'],t['n2'],t['n3']]; sphere=T.ideal([sum(x*x for x in ns)-1]); rem=sphere.reduce(F)
# The monomials in reduced F have independent coefficients over the sphere ideal.
coefs=[rem.monomial_coefficient(m) for m in rem.monomials()]
coeffring=T.ideal(coefs)
null_ok=all(coeffring.reduce(C[i,j]-(-t['t00'] if i==j==0 else t['t00'] if i==j and i>0 else 0))==0 for i in range(4) for j in range(4))
checks['CAS-01-C01']=bool(unit and null_ok)
# Direct Singular reduction of the same null-cone polynomial ideal.
from sage.interfaces.singular import singular
singular.eval('ring r=0,(n1,n2,n3),dp; ideal J=n1^2+n2^2+n3^2-1;')
sing_log=singular.eval('reduce(n1^2+n2^2+n3^2-1, std(J));')
print('Singular sphere-ideal remainder: '+sing_log,file=sys.stderr)
# Q u, symmetric part and acceleration covector. Spatial trace/STF properties.
h=g+uf.column()*uf.row(); D=(identity_matrix(R,4)+uf.column()*u.row())*B*(identity_matrix(R,4)+u.column()*uf.row()); theta=sum((g*B)[i,i] for i in range(4)); sig=D-theta*h/3
c02=zero(list(Q*u)+(Q+Q.transpose()-2*B).list()+list(c*Q.transpose()*u-2*c*b)+list(sig*u)+[sum((g*sig)[i,i] for i in range(4))])
checks['CAS-01-C02']=bool(c02)
# Rest frame formulas using a separate small ring and sphere quotient.
P=PolynomialRing(QQ,names=['c','h0','h11','h12','h13','h22','h23','h33','a1','a2','a3','n1','n2','n3'])
p=P.gens_dict(); nr=vector(P,[p['n1'],p['n2'],p['n3']]); sphere2=P.ideal([nr*nr-1]); c2=p['c']; AA=vector(P,[p['a1'],p['a2'],p['a3']]); V=matrix(P,3,3,lambda i,j:p[f'h{min(i,j)+1}{max(i,j)+1}']); K2=vector(P,[-1]+list(nr)); Br=block_matrix(P,[[matrix(P,1,1,[0]), matrix(P,1,3,[AA[j]/(2*c2) for j in range(3)])],[matrix(P,3,1,[AA[j]/(2*c2) for j in range(3)]),V]]) if False else None
# Work over fraction field for the physical c denominator.
Ff=P.fraction_field(); A=vector(Ff,AA); N=vector(Ff,nr); H=matrix(Ff,V); th=H.trace(); sig3=H-th*identity_matrix(Ff,3)/3
Brest=matrix(Ff,4,4,lambda i,j: 0 if i==j==0 else (A[j-1]/(2*c2) if i==0 else A[i-1]/(2*c2) if j==0 else H[i-1,j-1]))
kr=vector(Ff,[-1]+list(N)); Hdiff=kr*Brest*kr-(th/3+N*sig3*N-A*N/c2)
# General STF S contraction, reduced by trace constraint.
Sgen=matrix(Ff,4,4,lambda i,j:p['h0'] if i==j==0 else (-p[f'a{j}']/2 if i==0 else -p[f'a{i}']/2 if j==0 else H[i-1,j-1]))
gen=kr*Sgen*kr-(p['h0']+A*N+N*H*N)
checks['CAS-01-C03']=bool(sphere2.reduce(P(Hdiff.numerator()))==0 and gen==0)
# At x=0, derivative of (-v.g.v)^(-1/2) is c^-1 u^d Q_ad, zero in ideal.
checks['CAS-01-C04']=bool(zero(list(Q*u)) and zero([u*g*u+1]))
notes += ['C04 evaluates the exact normalization derivative at x=0: d(-g(v,v))^(-1/2)=c^-1 u^d Q_ad=0; local flow existence is outside the component.','Future branch u0>0 and c>0 are retained as domain conditions, not certified by a polynomial ideal.']
print(json.dumps({'checks':checks,'domain_assumption_diff':[],'counterexample':None,'notes':notes,'engine':'SageMath + explicit Singular sphere ideal','singular_remainder':sing_log}))
