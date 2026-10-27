"""Finite checks for v15 number-energy / observer / beam bridges.

No transport solver or ODE. All temperatures/energies below are dimensionless
ratios to a fixed reference; physical c,hbar,k_B are restored in the note.
"""
from pathlib import Path
from fractions import Fraction
import json
import math
import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[1]
def rmin(r):
    return 256*r**3*(r*r+r+1)**3/(27*(r**3+r*r+r+1)**4)
def pstar(r):
    return (3*r*r+2*r+1)/((r**3+r*r+r+1)*(r*r+r+1))
def mixratio(t,w):
    return float(np.dot(w,t**3)**4/np.dot(w,t**4)**3)
def I(k,eta):
    def f(x):
        if x>700: return 0.
        if x==0: return 0.
        return x**k/math.expm1(x-eta)
    return quad(f,0,np.inf,epsabs=2e-12,epsrel=2e-12,limit=160)[0]
def Qbe(eta):
    return I(2,eta)**4/I(3,eta)**3
QC=Qbe(0)
def invQbe(q):
    if q==QC:return 0.
    return float(brentq(lambda eta: Qbe(eta)-q,-80,0,xtol=1e-12))

# The r=2 extremizer can be checked with exact rational arithmetic.
r=Fraction(2);p=Fraction(17,105)
exact=(1+p*(r**3-1))**4/(1+p*(r**4-1))**3
expected=Fraction(702464,1366875)
assert exact==expected

rng=np.random.default_rng(20261026)
random_error=0.
endpoint=[]
for r in [1.01,1.1,1.2,2.,4.,10.]:
    p=pstar(r);R=mixratio(np.array([1.,r]),np.array([1-p,p]))
    assert abs(R-rmin(r))<1e-13
    assert 0<p<1 and 0<R<=1
    endpoint.append({"temperature_ratio":r,"hot_weight":p,"Rmin":R,
                     "Planck_calibrated_eta_lower":invQbe(QC*R)})
    for _ in range(200):
        t=np.exp(rng.uniform(0,math.log(r),6));w=rng.dirichlet(np.ones(6))
        val=mixratio(t,w)
        assert rmin(r)-2e-14<=val<=1+2e-14
        for scale in [.3,3.,100.]:
            random_error=max(random_error,abs(mixratio(scale*t,w)-val))
assert random_error<2e-14

# Full-sky Doppler moment quadratures against exact closed forms.
boost=[]
for beta in [.00123,.1,.4,.7]:
    gam=1/math.sqrt(1-beta*beta)
    mom=lambda k:quad(lambda mu:(gam*(1-beta*mu))**(-k)/2,
                     -1,1,epsabs=1e-12,epsrel=1e-12)[0]
    m3,m4=mom(3),mom(4)
    exact3=gam;exact4=gam**2*(1+beta**2/3)
    R=m3**4/m4**3;closed=(1-beta**2)/(1+beta**2/3)**3
    assert abs(m3-exact3)<1e-12 and abs(m4-exact4)<1e-12
    assert abs(R-closed)<1e-12
    assert rmin((1+beta)/(1-beta))-1e-12<=R<=1
    boost.append({"beta":beta,"mean_D3":m3,"mean_D4":m4,
                  "Qmean_over_Q0":R,"effective_BE_eta":invQbe(QC*R)})

# Arbitrary thermochemical MB angular field: exact weight-zero quotient
# under the full aberration map. No small-beta expansion is used.
mu=np.linspace(-1,1,501);beta=.36;gamma=1/math.sqrt(1-beta**2)
mu0=(mu-beta)/(1-beta*mu)
T=1+.12*mu0+.05*(3*mu0**2-1)/2
eta=-1+.15*mu0
N=2*np.exp(eta)*T**3;E=6*np.exp(eta)*T**4
D=1/(gamma*(1-beta*mu))
Np=D**3*N;Ep=D**4*E
Qold=N**4/E**3;Qnew=Np**4/Ep**3
quotient_relerr=float(np.max(abs(Qnew/Qold-1)))
assert quotient_relerr<4e-15

# Local response rank and retained population contrast.
H=np.array([[3.,3.,1.],[4.,4.,1.]]) # boost, intrinsic temperature, eta
contrast=np.array([4.,-3.])
assert np.linalg.matrix_rank(H)==2
assert np.allclose(H@np.array([1.,-1.,0.]),0)
assert np.allclose(contrast@H,[0,0,1])
# Unknown common fractional calibration occupies the same MB eta column.
Hgain=np.column_stack([H,np.ones(2)])
assert np.allclose(Hgain@np.array([0.,0.,1.,-1.]),0)
sig=1e-3;C=sig**2*np.array([[1,.9],[.9,1]])
var=float(contrast@C@contrast)
assert abs(var-3.4e-6)<1e-18

result={
 "status":"PASS_SCOPED_FINITE_CHECKS",
 "seed":20261026,"random_positive_beam_cases":1200,
 "max_scale_invariance_error":random_error,
 "sharp_r2_fraction":str(exact),"endpoint_beams":endpoint,
 "fullsky_boost_cases":boost,"max_pointwise_quotient_relative_error":quotient_relerr,
 "response_rank":2,"population_target_identifiable":True,
 "unknown_common_MB_calibration_identifiable":False,
 "correlated_population_contrast_variance":var,
 "scope":"dimensionless toy and finite algebra only; no observational fit or ODE"
}
out=ROOT/"cas/paper_ii_check_python.json";out.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps(result,indent=2))
