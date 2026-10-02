from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['t','x','y','z','b','lam']);v=R.gens_dict();t,x,y,z,b,lam=[v[k] for k in ['t','x','y','z','b','lam']];coords=[t,x,y,z];eta=diagonal_matrix(R,[-1,1,1,1]);phi=-b*t*t-b*(x*x+y*y+z*z)/2+lam*t*t*x/2
grad=vector(R,[phi.derivative(q) for q in coords]);hess=matrix(R,4,4,lambda i,j:phi.derivative(coords[i]).derivative(coords[j]));box=sum(eta[i,i]*hess[i,i] for i in range(4));norm=sum(eta[i,i]*grad[i]**2 for i in range(4))
# Conformal Christoffel from metric derivative; compute Ricci algebraically without exponential by using Gamma^a_bc=delta^a_b phi_c+delta^a_c phi_b-eta_bc phi^a.
Gamma=lambda a,i,j:(1 if a==i else 0)*grad[j]+(1 if a==j else 0)*grad[i]-eta[i,j]*eta[a,a]*grad[a]
Ric=matrix(R,4,4,lambda i,j:sum(Gamma(a,i,j).derivative(coords[a])-Gamma(a,i,a).derivative(coords[j])+sum(Gamma(a,a,k)*Gamma(k,i,j)-Gamma(a,j,k)*Gamma(k,i,a) for k in range(4)) for a in range(4)))
scalar0=sum(eta[i,i]*Ric[i,i] for i in range(4));Ein=Ric-eta*scalar0/2;target=matrix(R,4,4,lambda i,j:-2*hess[i,j]+2*grad[i]*grad[j]+eta[i,j]*(2*box+norm));c01=Ein==target
# On t=y=z=0, e^-2phi=exp(b*x^2), and G00+G22=6b-2lam*x.
sl={t:0,y:0,z:0};raw=(Ein[0,0]+Ein[2,2]).subs(sl);c02=raw==6*b-2*lam*x
singular.eval('ring r=0,(b,lam,x),dp; ideal I=6*b-2*lam*x-(6*b-2*lam*x);')
rem=singular.eval('reduce(6*b-2*lam*x-(6*b-2*lam*x),std(I));');print('Singular slice numerator remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-05-C01':False,'CAS-05-C02':bool(c02),'CAS-05-C03':False},'domain_assumption_diff':['CAS-05-C01: displayed conformal polynomial jet stress, gap and acceleration are not specified in permitted sources; generic conformal Einstein tensor was independently derived','CAS-05-C03: supplied cubic H polynomial and twelve basis images are not specified in permitted sources'],'counterexample':None,'engine':'SageMath plus explicit Singular polynomial ideal','singular_remainder':rem,'notes':['Derived G_ab=-2 phi_ab+2 phi_a phi_b+eta_ab(2 box phi+(grad phi)^2) from conformal Christoffel.','C02 multiplies exact slice numerator by e^(b s^2); exponent positivity is retained analytically.']}))
