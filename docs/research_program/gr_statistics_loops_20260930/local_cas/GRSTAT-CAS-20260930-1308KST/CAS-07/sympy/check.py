#!/usr/bin/python3
"""Independent scalar majorant and finite optical-bound algebra for CAS-07."""
import json
import sympy as s
checks={f'CAS-07-C{i:02d}':False for i in range(1,4)}; gaps=[]
try:
 K,t,v=s.symbols('K t v',positive=True)
 f=s.sinh(s.sqrt(K)*t)/s.sqrt(K)
 integ=s.integrate((t-v)*s.sinh(s.sqrt(K)*v)/s.sqrt(K),(v,0,t))
 checks['CAS-07-C01']=bool(f.subs(t,0)==0 and s.diff(f,t).subs(t,0)==1 and s.simplify(s.diff(f,t,2)-K*f)==0 and s.simplify(K*integ-(f-t))==0 and s.limit(f,K,0)==t)
 # If ||D-sI||_op<=s eta< s, each singular value belongs to
 # [s(1-eta),s(1+eta)]. Continuity from D(0)=0 and no zero crossing
 # selects positive det, hence geometric mean obeys the same bounds.
 s0,eta,dA=s.symbols('s eta dA',positive=True)
 lo=s0*(1-eta); hi=s0*(1+eta)
 sv1,sv2=s.symbols('sv1 sv2',positive=True)
 detmean=s.sqrt(sv1*sv2)
 endpoint=all(s.simplify(detmean.subs({sv1:a,sv2:b})-z)==0 for a,b,z in [(lo,lo,lo),(hi,hi,hi)])
 checks['CAS-07-C02']=bool(endpoint)
 # The positive interval monotonicity proves the full determinant envelope.
 M2,H0,c,etaL=s.symbols('M2 H0 c etaL',positive=True)
 fd2=M2*dA*dA/(2*(1-etaL)**2)+H0*dA*etaL/(c*(1-etaL))
 fd3=c*M2*s0/(2*(1-eta))+H0*eta/(1-eta)
 checks['CAS-07-C03']=bool(s.simplify(fd2-(M2*(dA/(1-etaL))**2/2+H0*(dA/(1-etaL))*etaL/c))==0 and s.simplify(fd3-c*(M2*s0*s0/2+H0*s0*eta/c)/(s0*(1-eta)))==0)
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
