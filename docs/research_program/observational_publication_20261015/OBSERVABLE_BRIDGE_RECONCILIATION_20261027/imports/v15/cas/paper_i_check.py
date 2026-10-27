"""Finite, solver-free checks for Paper I reuse bridge; no observations."""
from pathlib import Path
import json, math
import numpy as np
from scipy.integrate import quad

rows=[]
for a in [-.99,-.9,-.5,-.1,.1,.5,1.,1.5,1.9,1.99]:
    def w(mu): return 1+a*(3*mu*mu-1)/2
    delta=1-quad(lambda mu:w(mu)**.75,0,1,epsabs=2e-13,epsrel=2e-13)[0]
    V=2*abs(a)/(3*math.sqrt(3))
    eigen=[(56-10*a)/105]*2+[(56+5*a)/105]*2+[(56+10*a)/105]
    eta=math.sqrt(8*delta/3)
    actual_error=max(abs(x-8/15) for x in eigen)
    assert delta+2e-13>=3*V*V/32
    assert actual_error<=V/2+2e-13<=eta+3e-13
    assert min(eigen)>0
    rows.append({'a':a,'delta':delta,'L1_contrast':V,'actual_lambda_min_over_rho':min(eigen),
                 'entropy_lambda_lower_over_rho':8/15-eta,'actual_operator_error_over_rho':actual_error,
                 'centered_L1_error_bound_over_rho':V/2,'entropy_error_bound_over_rho':eta})
# A stronger anisotropy family shows that a failed entropy certificate is inconclusive.
mu,gw=np.polynomial.legendre.leggauss(160)
phi_grid=np.arange(32)*2*np.pi/32
MU,PH=np.meshgrid(mu,phi_grid,indexing='ij')
N=np.stack([np.sqrt(1-MU**2)*np.cos(PH),np.sqrt(1-MU**2)*np.sin(PH),MU],axis=-1)
T=np.array([np.diag([1,-1,0])/np.sqrt(2),np.diag([-1,-1,2])/np.sqrt(6),
            [[0,1/np.sqrt(2),0],[1/np.sqrt(2),0,0],[0,0,0]],
            [[0,0,1/np.sqrt(2)],[0,0,0],[1/np.sqrt(2),0,0]],
            [[0,0,0],[0,0,1/np.sqrt(2)],[0,1/np.sqrt(2),0]]])
TN=np.einsum('aij,...j->...ai',T,N)
NTN=np.einsum('...i,...ai->...a',N,TN)
Bop=2*np.einsum('...ai,...bi->...ab',TN,TN)-np.einsum('...a,...b->...ab',NTN,NTN)
strong=[]
for k in [1.,3.,8.,20.]:
    un=np.exp(k*mu**2)
    w=un/np.dot(gw/2,un)
    delta=1-np.dot(gw/2,w**.75)
    L=np.einsum('i,ijab->ab',gw*w/(2*32),Bop)
    eig=np.linalg.eigvalsh(L)
    bound=8/15-math.sqrt(8*delta/3)
    assert eig.min()>0
    strong.append({'k':k,'delta':float(delta),'actual_lambda_min_over_rho':float(eig.min()),
                   'entropy_lambda_lower_over_rho':bound})
assert strong[-1]['entropy_lambda_lower_over_rho']<0
# Exact analytical local coefficient ratios checked by decreasing amplitudes.
small=[]
for a in [1e-2,3e-3,1e-3]:
    delta=1-quad(lambda mu:(1+a*(3*mu*mu-1)/2)**.75,0,1,epsabs=2e-14,epsrel=2e-14)[0]
    pi_norm2=2*a*a/75
    small.append({'a':a,'delta_over_pi_norm2':delta/pi_norm2,'limit':45/64})
assert abs(small[-1]['delta_over_pi_norm2']-45/64)<1e-4
# Pointwise scalar inequality across wide contrasts; stable log/expm1 near1.
u=np.r_[np.geomspace(1e-8,.95,900),np.geomspace(1.05,1e8,900),[1.]]
phi=-np.expm1(.75*np.log(u))+.75*(u-1)
D=(7+5*u)/12
res=phi-3*(u-1)**2/(32*D)
assert res.min()>-2e-14
receipt={'method':'SciPy quad of exact axisymmetric brightness family; analytic Loop-A response eigenvalues; broad finite pointwise scalar-inequality checks',
         'scope':'Analytic toy; no measured data, no ODE or transport solve',
         'family':'I=rho/(4pi)*(1+a P2), -1<a<2',
         'threshold_delta':8/75,'rows':rows,'strong_anisotropy_family':strong,'local_quadrupole_cost':small,
         'pointwise_test_minimum_residual':float(res.min()),
         'pointwise_test_range':[1e-8,1e8],
         'tolerances':{'quadrature_epsabs':2e-13,'quadrature_epsrel':2e-13,'inequality_roundoff_allowance':3e-13}}
Path(__file__).with_name('paper_i_check_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'threshold':8/75,'rows':rows,'strong_anisotropy_family':strong,'local_quadrupole_cost':small},indent=2))
