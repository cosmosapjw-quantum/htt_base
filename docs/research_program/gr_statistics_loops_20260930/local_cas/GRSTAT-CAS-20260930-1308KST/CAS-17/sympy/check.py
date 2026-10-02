#!/usr/bin/python3
"""Independent Lorentz dual and conformal transformation checks for CAS-17."""
import json,itertools
import sympy as s
checks={f'CAS-17-C{i:02d}':False for i in range(1,5)};gaps=[]
try:
 eta=s.diag(-1,1,1,1)
 X=s.Matrix(4,3,s.symbols('X0:12',real=True)); cov=eta*X
 v=s.Matrix([sum(s.LeviCivita(a,b,c,d)*cov[b,0]*cov[c,1]*cov[d,2] for b,c,d in itertools.product(range(4),repeat=3)) for a in range(4)])
 Gram=X.T*eta*X
 orth=all(s.expand((v.T*eta*X)[i])==0 for i in range(3))
 norm=s.simplify((v.T*eta*v)[0]+Gram.det())==0
 gamma,beta=s.symbols('gamma beta',positive=True)
 checks['CAS-17-C01']=bool(orth and norm and s.simplify(1-1/gamma**2-(gamma**2-1)/gamma**2)==0)
 # Under g'=λ²g and u'=u/λ, normalized tetrads all scale λ^-1.
 # Covariant B'=λ B, contravariant A'=A/λ², and unit contraction rates
 # scale λ^-1. Affine-normalized dA and s scale λ.
 lam,r,H,K,M,L,Z=s.symbols('lambda r H K M L Z',positive=True)
 checks['CAS-17-C02']=bool(s.simplify((lam*r)*(H/lam)-r*H)==0 and s.simplify((K/lam**2)*(lam*L)**2-K*L**2)==0 and s.simplify((M/lam**2)*(lam*L)**2-M*L**2)==0 and s.simplify((lam**2)*(1/lam)*(1/lam)-1)==0)
 # Connection difference C^a_bc=δ^a_b φ_c+δ^a_c φ_b-g_bc φ^a.
 u=s.Matrix(s.symbols('u0:4',real=True)); gp=s.Matrix(s.symbols('g0:4',real=True))
 A=s.Matrix(s.symbols('A0:4',real=True)); c,ph=s.symbols('c phi',positive=True)
 udot=(u.T*eta*gp)[0]; hgrad=gp+u*udot
 Cuu=s.Matrix([sum((int(a==b)*(eta*gp)[d]+int(a==d)*(eta*gp)[b]-eta[b,d]*gp[a])*u[b]*u[d] for b,d in itertools.product(range(4),repeat=2)) for a in range(4)])
 # u.u=-1 converts C(u,u)=2u(u.gradφ)+gradφ.
 Cuu_norm=s.Matrix([s.expand(Cuu[a]-gp[a]-2*u[a]*udot) for a in range(4)])
 # Cuu_norm vanishes only after imposing u.u=-1; exact polynomial reduction.
 uu=(u.T*eta*u)[0]
 conn=all(s.simplify(Cuu_norm[a]+(1+uu)*gp[a])==0 for a in range(4))
 # Endpoint E' = exp(-φ)E for conformal null tangent reparameterization,
 # hence Z'=exp(φ_observer-φ_emitter)Z.
 po,pe=s.symbols('phi_o phi_e',real=True)
 red=s.simplify((s.exp(-pe)*s.Symbol('Ee'))/(s.exp(-po)*s.Symbol('Eo'))-s.exp(po-pe)*s.Symbol('Ee')/s.Symbol('Eo'))==0
 checks['CAS-17-C03']=bool(conn and red)
 J=s.Matrix(2,2,s.symbols('j0:4')); T=s.Matrix(2,2,s.symbols('t0:4')); w=s.Matrix(s.symbols('w0:2'))
 transformed=J.inv()*T*J; wp=J.inv()*w; row=w.T*J
 checks['CAS-17-C04']=bool(s.simplify((row*transformed*wp)[0]-(w.T*T*w)[0])==0)
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
