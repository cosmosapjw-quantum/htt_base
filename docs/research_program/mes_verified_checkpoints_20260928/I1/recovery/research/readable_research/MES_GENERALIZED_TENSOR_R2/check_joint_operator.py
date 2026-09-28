"""Exact finite sphere checks; no cosmological evolution and no real sky data."""
import itertools, json, math, platform
from pathlib import Path
import sympy as sp
import numpy as np

OUT=Path(__file__).resolve().parent
x,y,z=sp.symbols('x y z', real=True)
e=sp.Matrix([x,y,z]); coords=(x,y,z); I=sp.eye(3)

def avg(p):
    total=0
    for powers,coeff in sp.Poly(sp.expand(p),*coords).terms():
        if any(v%2 for v in powers): continue
        total += coeff*sp.prod(sp.factorial2(v-1) for v in powers)/sp.factorial2(sum(powers)+1)
    return sp.simplify(total)

def avmat(m): return m.applyfunc(avg)
def grad(p): return sp.Matrix([sp.diff(p,v) for v in coords])
def stf(m): return (m+m.T)/2-sp.trace(m)*I/3

H=sp.Rational(2,7)
S=sp.Matrix([[1,2,0],[2,-2,1],[0,1,1]])/11
a=sp.Matrix([2,-1,3])/13
om=sp.Matrix([-1,2,1])/17
Pe=I-e*e.T
R=H+(a.dot(e))+(e.dot(S*e))
V=-Pe*(a+S*e)-om.cross(e)
E=e*e.T-I/3
identities={
 'optical_H':avg(R)-H,
 'optical_a':avmat(3*e*R)-a,
 'optical_S':avmat(sp.Rational(15,2)*E*R)-S,
 'optical_omega':avmat(-sp.Rational(3,2)*e.cross(V))-om,
 'angular_a':avmat(-sp.Rational(3,2)*V)-a,
 'angular_S':-5*stf(avmat(e*V.T))-S,
 'R_norm':avg(R**2)-(H**2+a.dot(a)/3+2*sp.trace(S*S)/15),
 'V_norm':avg(V.dot(V))-(2*a.dot(a)/3+sp.trace(S*S)/5+2*om.dot(om)/3),
}
def zero(v):
    return all(sp.simplify(x)==0 for x in v) if isinstance(v,sp.MatrixBase) else sp.simplify(v)==0
assert all(zero(v) for v in identities.values())

# B positive on sphere by the coefficient absolute-sum bound B>=23/50.
B=1+(x+2*y-z)/20+(x*x+2*y*y-3*z*z)/25+x*y*z/10
assert avg(B)==1
tests=[]
for deg in range(5):
    for ix in range(deg+1):
        for iy in range(deg-ix+1):
            tests.append((deg,x**ix*y**iy*z**(deg-ix-iy)))
SB=[]
for m in [sp.diag(1,-1,0),sp.diag(1,1,-2),
          sp.Matrix([[0,1,0],[1,0,0],[0,0,0]]),
          sp.Matrix([[0,0,1],[0,0,0],[1,0,0]]),
          sp.Matrix([[0,0,0],[0,0,1],[0,1,0]])]: SB.append(m)
Z=sp.zeros(3); zv=sp.zeros(3,1)
columns=[(sp.Integer(1),Z,zv,zv)]
columns += [(0,s,zv,zv) for s in SB]
columns += [(0,Z,I[:,i],zv) for i in range(3)]
columns += [(0,Z,zv,I[:,i]) for i in range(3)]

def response(brightness,verify=False):
    cols=[]
    for hh,ss,aa,oo in columns:
        s=e.dot(ss*e); ae=aa.dot(e)
        w=Pe*(aa+ss*e)+oo.cross(e)
        strong=-w.dot(grad(brightness))+4*(hh+s+ae)*brightness
        col=[]
        for ell,psi in tests:
            weak=((aa+ss*e+oo.cross(e)).dot(grad(psi))
                 +(4*hh+(1-ell)*s+(2-ell)*ae)*psi)
            val=avg(brightness*weak)
            if verify: assert sp.simplify(avg(psi*strong)-val)==0
            col.append(val)
        cols.append(col)
    return sp.Matrix.hstack(*map(sp.Matrix,cols))

Aiso=response(sp.Integer(1),True)
Agen=response(B,True)
rankiso=Aiso.rank(); rankgen=Agen.rank()
assert rankiso==9
assert rankgen==12
assert Aiso[:,9:12]==sp.zeros(len(tests),3)

# Low moments checked independently against explicit moment formulas.
rho=avg(B); M1=avmat(B*e); M2=avmat(B*e*e.T)
Pi=stf(M2); q=e.dot(S*e)
LB=S*M2+M2*S-avmat(B*q*e*e.T)-I*sp.trace(M2*S)/3
Rom=sp.Matrix([[0,-om[2],om[1]],[om[2],0,-om[0]],[-om[1],om[0],0]])
strong=-(Pe*(a+S*e)+om.cross(e)).dot(grad(B))+4*(H+q+a.dot(e))*B
low_checks=[avg(strong)-(4*H*rho+sp.trace(S*M2)+2*a.dot(M1)),
 avmat(e*strong)-(4*H*M1+S*M1+om.cross(M1)+(rho*I+M2)*a),
 stf(avmat(e*e.T*strong))-(4*H*Pi+LB+2*stf(a*M1.T)+Rom*M2-M2*Rom)]
assert all(zero(v) for v in low_checks)

# A single power C_ell cannot encode eigenvalue shape of an STF quadrupole.
K1=sp.diag(1,-1,0); K2=sp.diag(1,1,-2)/sp.sqrt(3)
def shape(K): return sp.simplify(sp.sqrt(6)*sp.trace(K**3)/sp.trace(K*K)**sp.Rational(3,2))
assert sp.trace(K1*K1)==sp.trace(K2*K2)==2
assert shape(K1)==0 and shape(K2)==-1

# Analytic redshift template identifiability; g(z) is a declared toy template.
g_same=np.array([1.,1.,1.]); g_var=np.array([0.,.5,1.])
def zd(g): return np.vstack([np.hstack([np.eye(3),v*np.eye(3)]) for v in g])
rank_same=int(np.linalg.matrix_rank(zd(g_same)))
rank_var=int(np.linalg.matrix_rank(zd(g_var)))
assert rank_same==3 and rank_var==6

# Joint data-denominator propagation: ratio exactly constant under shared factor.
rng=np.random.default_rng(20260920)
shared=rng.normal(size=20000)
rat_shared=np.exp(shared)/(2*np.exp(shared))
rat_ind=np.exp(shared)/(2*np.exp(rng.normal(size=20000)))
assert np.max(np.abs(rat_shared-.5))==0

results={
 'status':'PASS_SCOPED_EXACT_AND_SYNTHETIC_CHECKS',
 'python':platform.python_version(),'sympy':sp.__version__,'numpy':np.__version__,
 'sphere_measure':'average dOmega/(4pi); exact rational polynomial integration',
 'optical_inverse_and_norm_identities':{k:zero(v) for k,v in identities.items()},
 'positive_B_lower_bound':'23/50',
 'weak_strong_equalities':2*len(tests)*len(columns),
 'rows':len(tests),'columns':len(columns),
 'exact_isotropic_rank':rankiso,'exact_anisotropic_rank':rankgen,
 'rank_claim':'Examples for kinematic block with known residual, NOT observational identifiability',
 'low_moment_identities':list(map(zero,low_checks)),
 'equal_quadrupole_power_shapes':[str(shape(K1)),str(shape(K2))],
 'declared_redshift_template_rank':{'constant':rank_same,'varying':rank_var},
 'shared_denominator_example':{'shared_ratio_std':float(rat_shared.std()),'incorrect_independent_ratio_std':float(rat_ind.std())},
 'actual_CMB_inference':False,'ODE_PDE_Boltzmann_evolution':False,
}
(OUT/'evidence'/'JOINT_OPERATOR_CHECKS.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
