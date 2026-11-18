"""Finite-ray Sachs Jacobi and tilted perfect-fluid focusing: exact/ODE toy checks.
Optical tidal matrix T has units lambda^-2 (lambda chosen as length); all
displayed dimensionless values use lambda/length_unit=1 only.
No fitted CF4 or Bianchi global solution.
"""
import json
import numpy as np
from scipy.integrate import solve_ivp
from numpy.polynomial.legendre import leggauss,legval

def constant_tidal_jacobi(a,b,L=1.):
    """Solve J''=-diag(a,b)J with vertex J(0)=0, J'(0)=Id."""
    def ode(t,x):
        return [x[2],x[3],-a*x[0],-b*x[1]]
    sol=solve_ivp(ode,(0,L),[0.,0.,1.,1.],rtol=1e-12,atol=1e-14)
    y=sol.y[:,-1]
    assert y[0]>0 and y[1]>0
    return float(np.sqrt(y[0]*y[1]))

def closed_j(k,L=1.):
    if abs(k)<1e-14:return L
    if k>0:return float(np.sin(np.sqrt(k)*L)/np.sqrt(k))
    return float(np.sinh(np.sqrt(-k)*L)/np.sqrt(-k))

def lcoeff(w,y,ell):
    return float((2*ell+1)/2*np.sum(w*y*legval(x,[0]*ell+[1])))

def main():
    L=1.
    tests=[]
    for eps in [.2,.1,.05,.025]:
        DA=constant_tidal_jacobi(eps,-eps,L)
        DA_ex=np.sqrt(closed_j(eps,L)*closed_j(-eps,L))
        assert abs(DA-DA_ex)<2e-12
        finite_deficit=1-DA
        series_deficit=eps**2*L**4/180
        assert abs(finite_deficit-series_deficit)<5e-5*eps**2
        tests.append({"weyl_epsilon":eps,"DA_over_affine":DA,"deficit":finite_deficit,
                      "quadratic_epsilon2_prediction":series_deficit})
    ricci=[]
    for k in [.2,.1,.05]:
        DA=constant_tidal_jacobi(k,k,L)
        DA_ex=closed_j(k,L)
        assert abs(DA-DA_ex)<2e-12
        ricci.append({"trace_k":k,"DA":DA,"linear_deficit_pred":k/6,
                      "exact_deficit":1-DA})
    # For future-pointing k=omega(N+e), U=c*Gamma(N+beta e_z),
    # Rkk/(8piG/c4*(rho+p)*omega^2) = Gamma^2 (1-beta mu)^2.
    global x
    x,w=leggauss(64)  # exact for degree<=4 integrands; avoid 400-node float cancellation
    beta=.3; gamma2=1/(1-beta**2)
    single=gamma2*(1-beta*x)**2
    double=gamma2*((1-beta*x)**2+(1+beta*x)**2)
    A=[(2*l+1)/2*float(w@(single*legval(x,[0]*l+[1]))) for l in range(3)]
    B=[(2*l+1)/2*float(w@(double*legval(x,[0]*l+[1]))) for l in range(3)]
    A_exact=[gamma2*(1+beta**2/3),-2*gamma2*beta,2*gamma2*beta**2/3]
    B_exact=[2*gamma2*(1+beta**2/3),0.,4*gamma2*beta**2/3]
    np.testing.assert_allclose(A,A_exact,atol=5e-14,rtol=1e-12)
    np.testing.assert_allclose(B,B_exact,atol=5e-14,rtol=1e-12)
    return {
       "schema":"htt.r69.p1_optical_tilt_consistency/1",
       "constant_tidal_toy":{"weyl_pure_tracefree":tests,"ricci_isotropic":ricci},
       "tilt_two_perfect_fluids":{
          "beta":beta,"gamma2":gamma2,
          "one_fluid_P0_P1_P2":A,
          "equal_opposite_two_fluids_P0_P1_P2":B,
          "two_fluid_normal_momentum_sum":"exactly zero for equal enthalpy and opposite beta",
          "two_fluid_quadrupole_coefficient_over_2fluid_monopole":B[2]/B[0],
          "remark":"local null contraction only; source-specific GR geometry and null geodesics not solved"},
       "c_G":"restored in analytic report; code normalizes k=omega(N+e), eps and lambda",
       "status":"ODE solver agrees with exact constant-tidal Jacobi; analytical Legendre low multipoles agree with quadrature; no observational inference"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2))
