#!/usr/bin/python3
"""Independent finite conformal and cubic-jet checks for CAS-05."""
import json
import sympy as s
checks={f'CAS-05-C{i:02d}':False for i in range(1,4)}
gaps=[]
try:
 t,x,y,z=s.symbols('t x y z',real=True); X=(t,x,y,z)
 b,l,Lam,kappa,c=s.symbols('b lambda Lambda kappa c',positive=True)
 eta=s.diag(-1,1,1,1)
 phi=-b*t*t-b*(x*x+y*y+z*z)/2+l*t*t*x/2
 grad=s.Matrix([s.diff(phi,v) for v in X]); box=sum(eta[i,i]*s.diff(phi,X[i],2) for i in range(4)); grad2=(grad.T*eta*grad)[0]
 G=s.Matrix(4,4,lambda i,j:s.expand(-2*s.diff(phi,X[i],X[j])+2*grad[i]*grad[j]+2*eta[i,j]*box+eta[i,j]*grad2))
 # Direct conformal Ricci derivation from Γ(g=e^{2φ}η). The known conformal
 # formula is recomputed here by contractions of Γ with symbolic first/second jets.
 p=s.symbols('p0:4'); h=s.Matrix(4,4,s.symbols('h0:16')); h=(h+h.T)/2
 Gamma=[[[int(i==j)*p[k]+int(i==k)*p[j]-eta[j,k]*eta[i,i]*p[i] for k in range(4)] for j in range(4)] for i in range(4)]
 # Ricci = ∂αΓ^α_{ij}-∂jΓ^α_{iα}+Γ^α_{αβ}Γ^β_{ij}-Γ^α_{jβ}Γ^β_{iα}
 d=lambda expr,k:sum(s.diff(expr,p[a])*h[a,k] for a in range(4))
 Ric=s.Matrix(4,4,lambda i,j:s.expand(sum(d(Gamma[a][i][j],a)-d(Gamma[a][i][a],j)+sum(Gamma[a][a][v]*Gamma[v][i][j]-Gamma[a][j][v]*Gamma[v][i][a] for v in range(4)) for a in range(4))))
 scalar=s.expand(sum(eta[i,i]*Ric[i,i] for i in range(4)))
 Gderived=s.Matrix(4,4,lambda i,j:s.expand(Ric[i,j]-eta[i,j]*scalar/2))
 Gtarget=s.Matrix(4,4,lambda i,j:-2*h[i,j]+2*p[i]*p[j]+2*eta[i,j]*sum(eta[a,a]*h[a,a] for a in range(4))+eta[i,j]*sum(eta[a,a]*p[a]**2 for a in range(4)))
 formula=all(s.simplify(Gderived[i,j]-Gtarget[i,j])==0 for i in range(4) for j in range(4))
 at0={v:0 for v in X}
 G0=G.subs(at0)
 stress=G0==s.diag(6*b,0,0,0)
 # Lambda term gives ε=(6b-Lambda)/κ and p=Lambda/κ, gap=6b/κ.
 # The acceleration of the selected eigenframe needs its smooth eigenjet;
 # this script does not derive that eigenjet, so the whole C01 stays false.
 gaps.append('C01: conformal Einstein tensor and origin stress checked, but energy-frame eigenjet and A1=c^2 lambda/(3b) were not independently derived.')
 checks['CAS-05-C01']=False
 slice0={t:0,x:s.symbols('s',real=True),y:0,z:0}; ss=s.symbols('s',real=True)
 # ε+p2=e^{-2φ}(G00+G22)/κ; cosmological terms cancel.
 checks['CAS-05-C02']=bool(formula and stress and s.simplify((G[0,0]+G[2,2]).subs(slice0)- (6*b-2*l*ss))==0)

 q=s.Matrix(s.symbols('q0:3',real=True)); M=s.Matrix(3,3,s.symbols('m0:9',real=True)); S=(M+M.T)/2; W=(M-M.T)/2
 v=s.Matrix([x,y,z]); r2=v.dot(v)
 H=s.zeros(4)
 for i in range(3):
  H[0,i+1]=H[i+1,0]=-t*r2*q[i]/2-r2*(W*v)[i]/5
  for j in range(3):
   H[i+1,j+1]=-int(i==j)*t*(v.dot(S*v))/2
 htrace=sum(eta[i,i]*H[i,i] for i in range(4))
 def boxf(f): return sum(eta[a,a]*s.diff(f,X[a],2) for a in range(4))
 def dRic(i,j):
  return s.expand((sum(eta[a,a]*(s.diff(H[a,j],X[a],X[i])+s.diff(H[a,i],X[a],X[j])) for a in range(4))-boxf(H[i,j])-s.diff(htrace,X[i],X[j]))/2)
 dR=sum(eta[i,i]*dRic(i,i) for i in range(4))
 dG=s.Matrix(4,4,lambda i,j:s.expand(dRic(i,j)-eta[i,j]*dR/2))
 image=all(s.simplify(dG[0,i+1]-(q[i]*t+(M*v)[i]))==0 for i in range(3))
 jet=all(s.diff(H[i,j],X[a],X[d]).subs(at0)==0 and H[i,j].subs(at0)==0 and s.diff(H[i,j],X[a]).subs(at0)==0 for i in range(4) for j in range(4) for a in range(4) for d in range(4))
 bianchi=all(s.simplify(sum(eta[a,a]*s.diff(dG[a,j],X[a]) for a in range(4)))==0 for j in range(4))
 checks['CAS-05-C03']=bool(image and jet and bianchi)
 if not checks['CAS-05-C03']:
  gaps.append('C03: cubic H failed at least one exact image, second-jet, or linear Bianchi check.')
except Exception as exc:
 gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
