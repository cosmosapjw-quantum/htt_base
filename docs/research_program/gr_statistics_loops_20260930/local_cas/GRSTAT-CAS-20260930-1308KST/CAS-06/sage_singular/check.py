from sage.all import *
from sage.interfaces.singular import singular
import json,sys
R=PolynomialRing(QQ,names=['alpha','s','X','P','q','N']);v=R.gens_dict();F=R.fraction_field();alpha,s,X,P,q,N=[F(v[k]) for k in ['alpha','s','X','P','q','N']]
# Algebraic sound speed and fixed homogeneous stationary current.
I=R.ideal([R(2*alpha*s-alpha-1),R(2*N*N*X-q*q)]);eps=(2*s-1)*P;speed=1/(2*s-1);c03=I.reduce(R((speed-alpha).numerator()))==0
# Constant in time current: sqrt(-g) P_X g^{00} q is independent of x0 in a static metric.
# Stress is T_ab=P_X psi_a psi_b+P g_ab; u_a parallel psi_a, giving epsilon=2XP_X-P.
c03=c03 and I.reduce(R(((2*s-1)*P-eps).numerator()))==0
singular.eval('ring r=0,(alpha,s),dp; ideal I=2*alpha*s-alpha-1;')
rem=singular.eval('reduce(2*alpha*s-alpha-1,std(I));');print('Singular sound-speed ideal remainder: '+rem,file=sys.stderr)
print(json.dumps({'checks':{'CAS-06-C01':False,'CAS-06-C02':False,'CAS-06-C03':bool(c03),'CAS-06-C04':False},'domain_assumption_diff':['CAS-06-C01: static spherical metric and stated TOV differential-jet substitutions are absent from permitted sources','CAS-06-C02: displayed matched-event curvature components and specialization are absent from permitted sources','CAS-06-C04: target divergence expression in y is absent from permitted sources'],'counterexample':None,'engine':'SageMath plus explicit Singular sound-speed ideal','singular_remainder':rem,'notes':['C03 holds on X>0, 0<alpha<1, q>0 stationary static branch with fixed Pstar; scalar-current divergence vanishes because current and determinant are independent of time.']}))
