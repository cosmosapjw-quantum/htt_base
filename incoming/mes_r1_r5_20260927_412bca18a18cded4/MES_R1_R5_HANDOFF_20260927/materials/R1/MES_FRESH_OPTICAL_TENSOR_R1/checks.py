"""Bounded research checks; no data analysis and no ODE/PDE evolution."""
import json
from pathlib import Path
import numpy as np
from numpy.polynomial.legendre import leggauss, Legendre

root = Path(__file__).resolve().parent
mu, w = leggauss(32)
phi = np.arange(64)*2*np.pi/64
mm, pp = np.meshgrid(mu, phi, indexing='ij')
n = np.stack([np.sqrt(1-mm**2)*np.cos(pp), np.sqrt(1-mm**2)*np.sin(pp), mm], axis=-1).reshape(-1,3)
weight = np.broadcast_to(w[:,None]/128, mm.shape).reshape(-1)
def avg(x): return np.einsum('n,n...->...', weight, x)
def exp_sym(a):
    val, vec = np.linalg.eigh(a)
    return (vec*np.exp(val))@vec.T
def log_sym(a):
    val, vec = np.linalg.eigh(a)
    if np.min(val)<=0: raise ValueError('not positive definite')
    return (vec*np.log(val))@vec.T
def reconstruct(temperature):
    y=temperature**-2
    return avg(y)*np.eye(3)+7.5*avg(y[:,None,None]*(n[:,:,None]*n[:,None,:]-np.eye(3)/3))
def norm(a): return np.linalg.norm(a)
def shape(a): return np.sqrt(6)*np.trace(a@a@a)/np.trace(a@a)**1.5
rng=np.random.default_rng(7092026)
rot,_=np.linalg.qr(rng.normal(size=(3,3)))
if np.linalg.det(rot)<0: rot[:,0]*=-1
stf=rot@np.diag([0.7,-0.2,-0.5])@rot.T
temp=2.7255/np.sqrt(np.einsum('ni,ij,nj->n',n,exp_sym(2*stf),n))
rec=reconstruct(temp)
expected=exp_sym(2*stf)/2.7255**2
krecovered=0.5*log_sym(rec/np.linalg.det(rec)**(1/3))
cal_rec=reconstruct(temp*1.037)
cal_k=0.5*log_sym(cal_rec/np.linalg.det(cal_rec)**(1/3))
s1=np.diag([1.,-1.,0.]);s2=np.diag([1.,1.,-2.])/np.sqrt(3)
expansion=[]
ell4=[]
for amp in [0.04,0.02,0.01,0.005]:
    k=amp*s1
    t=1/np.sqrt(np.einsum('ni,ij,nj->n',n,exp_sym(2*k),n))
    theta=t/avg(t)-1
    ss=np.einsum('ni,ij,nj->n',n,k,n)
    rr=np.einsum('ni,ij,nj->n',n,k@k,n)
    approx=-ss-rr+1.5*ss**2+2*np.trace(k@k)/15
    expansion.append({'amplitude':amp,'rms_remainder':float(np.sqrt(avg((theta-approx)**2)))})
    ka=amp*np.diag([-0.5,-0.5,1.])
    ta=1/np.sqrt(np.einsum('ni,ij,nj->n',n,exp_sym(2*ka),n))
    c4=9*avg((ta/avg(ta)-1)*Legendre.basis(4)(n[:,2]))
    ell4.append({'amplitude':amp,'P4_coefficient_over_amp_squared':float(c4/amp**2),'predicted_limit':27/35})
ratios=[expansion[i]['rms_remainder']/expansion[i+1]['rms_remainder'] for i in range(3)]
checks={
    'exact_inverse_relative_error':float(norm(rec-expected)/norm(expected)),
    'log_strain_absolute_error':float(norm(krecovered-stf)),
    'calibration_invariance_error':float(norm(cal_k-stf)),
    'quadratic_moment_error':float(abs(avg(np.einsum('ni,ij,nj->n',n,s1,n)**2)-2*np.trace(s1@s1)/15)),
    'morphology_same_norm':bool(np.allclose(norm(s1),norm(s2))),
    'morphology_chi_values':[float(shape(s1)),float(shape(s2))],
    'second_order_expansion':expansion,
    'remainder_halving_ratios':ratios,
    'axisymmetric_ell4':ell4,
    'source_model':'synthetic isotropic Planck source; finite anisotropic endpoint metric',
    'real_data_used':False,
    'evolution_integrator_used':False,
    'interpretation':'finite checks complement direct derivation; not a global proof or observational fit'
}
assert checks['exact_inverse_relative_error']<1e-12
assert checks['log_strain_absolute_error']<1e-12
assert checks['calibration_invariance_error']<1e-12
assert checks['quadratic_moment_error']<1e-14
assert checks['morphology_same_norm']
assert np.allclose(checks['morphology_chi_values'],[0.,-1.])
assert all(7.8<r<8.2 for r in ratios)
assert abs(ell4[-1]['P4_coefficient_over_amp_squared']-27/35)<0.003
checks['status']='FINITE_CHECKS_PASSED'
(root/'evidence').mkdir(exist_ok=True)
(root/'evidence/finite_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
