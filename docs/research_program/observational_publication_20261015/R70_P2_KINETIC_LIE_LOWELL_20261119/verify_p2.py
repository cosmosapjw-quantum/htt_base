"""R70-P2 finite evidence: Lie-Cartan photon streaming, first-two-moment nonclosure,
and actual R66 finite-band Commander signed STF readout.

This is NOT a native Einstein-Boltzmann solver or an actual Commander null analysis.
Run from htt_base root with .venv and PYTHONPATH=. ; input R66 unchanged.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import sympy as sp
from scipy.integrate import quad
from numpy.polynomial.legendre import leggauss, legval
from scripts.r68.fiveview_geometry import stf_matrix, stf_shape

SOURCE=Path("docs/research_program/observational_publication_20261015/R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json")
EPS=sp.LeviCivita

def symbolic_koszul():
    q=sp.Matrix(sp.symbols("x y z",real=True))
    a=sp.Matrix(sp.symbols("a0:3"))
    n=sp.Matrix([[sp.Symbol("n00"),sp.Symbol("n01"),sp.Symbol("n02")],
       [sp.Symbol("n01"),sp.Symbol("n11"),sp.Symbol("n12")],
       [sp.Symbol("n02"),sp.Symbol("n12"),sp.Symbol("n22")]])
    def C(i,j,k):
        return sum(EPS(j,k,l)*n[l,i] for l in range(3))+a[j]*int(i==k)-a[k]*int(i==j)
    def Gamma(i,k,j):
        return (C(i,j,k)-C(j,k,i)+C(k,i,j))/2
    geod=sp.Matrix([sp.expand(sum(Gamma(i,k,j)*q[j]*q[k] for j in range(3) for k in range(3))) for i in range(3)])
    target=q.cross(n*q)+a-q*(a.dot(q))
    resid=[sp.factor(geod[i]-target[i]-a[i]*(q.dot(q)-1)) for i in range(3)]
    assert resid==[0,0,0]
    return {"koszul_residual_after_unit_sphere_constraint":list(map(str,resid)),
       "unconstrained_difference":"a_i*(u_i*u_i-1); zero on |u|=1"}

def v_sky(u,sigma,a,N,c=1.):
    h=float(u@sigma@u)
    return -(sigma@u-h*u)-c*(a-u*np.dot(a,u)+np.cross(u,N@u))

def sphere_div_numeric(u,sigma,a,N,c=1.):
    tmp=np.array([0.,0.,1.]) if abs(u[2])<.85 else np.array([1.,0.,0.])
    e1=np.cross(u,tmp);e1/=np.linalg.norm(e1);e2=np.cross(u,e1)
    h=2e-6
    out=0.
    for ee in (e1,e2):
        p=u+h*ee;p/=np.linalg.norm(p)
        m=u-h*ee;m/=np.linalg.norm(m)
        out+=np.dot(ee,v_sky(p,sigma,a,N,c)-v_sky(m,sigma,a,N,c))/(2*h)
    return out

def quadrature_geometry():
    rng=np.random.default_rng(39)
    sigma=np.array([[.02,.005,-.001],[.005,-.01,.007],[-.001,.007,-.01]])
    a=np.array([-.03,0.,0.])
    N=np.diag([0.,.02,.07]) # N a=0, generic Bianchi class B
    assert np.allclose(N@a,np.zeros(3))
    maximum_tangency=0.;maximum_div=0.
    for _ in range(40):
        u=rng.normal(size=3);u/=np.linalg.norm(u)
        v=v_sky(u,sigma,a,N)
        maximum_tangency=max(maximum_tangency,abs(u@v))
        numerical=sphere_div_numeric(u,sigma,a,N)
        analytic=3*float(u@sigma@u)+2*float(a@u)
        maximum_div=max(maximum_div,abs(numerical-analytic))
    assert maximum_tangency<1e-14
    assert maximum_div<3e-9,maximum_div
    # curvature-only B2 is solenoidal, isotropic structure N∝I is zero.
    u=np.array([.4,.6,np.sqrt(.48)])
    N2=np.diag([.3,0,0])
    v2=v_sky(u,np.zeros((3,3)),np.zeros(3),N2)
    np.testing.assert_allclose(v2,-np.cross(u,N2@u),atol=1e-14)
    np.testing.assert_allclose(v_sky(u,np.zeros((3,3)),np.zeros(3),.8*np.eye(3)),0,atol=1e-14)
    av=np.array([-1.,0.,0.])
    vv=v_sky(u,np.zeros((3,3)),av,np.zeros((3,3)))
    np.testing.assert_allclose(vv[0],1-u[0]**2,atol=1e-14)
    return {"generic_class_B_max_sky_tangency_residual":maximum_tangency,
            "generic_class_B_max_divergence_residual":maximum_div,
            "type_II_n_diag_0p3_sky_drift":v2.tolist(),
            "type_V_a_minus_e1_sky_drift":vv.tolist(),
            "N_proportional_to_I_is_zero":True}

def first_moment_test():
    z,w=leggauss(48);phi=2*np.pi*np.arange(96)/96
    zz,pp=np.meshgrid(z,phi,indexing="ij")
    u=np.stack([np.sqrt(1-zz**2)*np.cos(pp),np.sqrt(1-zz**2)*np.sin(pp),zz],axis=-1).reshape(-1,3)
    weights=(w[:,None]*np.ones((1,len(phi)))/(2*len(phi))).reshape(-1)
    sigma=np.array([[.03,.008,0.],[.008,-.02,.004],[0.,.004,-.01]])
    a=np.array([-.02,0,0]);N=np.diag([0.,.07,-.03])
    V=np.array([v_sky(v,sigma,a,N) for v in u])
    Snn=np.einsum("ni,ij,nj->n",u,sigma,u)
    D=Snn-2*u@a
    f_dot=np.einsum("n,ni->i",weights,V-u*D[:,None])
    S_dot=np.einsum("n,ni,nj->ij",weights,V,u)+np.einsum("n,ni,nj->ij",weights,u,V) \
      -np.einsum("n,ni,nj->ij",weights*D,u,u)
    S_dot=.5*(S_dot+S_dot.T)
    np.testing.assert_allclose(f_dot,np.zeros(3),atol=3e-14)
    np.testing.assert_allclose(S_dot,-8*sigma/15,atol=3e-14)
    assert abs(np.trace(S_dot))<3e-14
    return {"initial_isotropic_photon_flux_dot":f_dot.tolist(),
            "initial_isotropic_photon_stress_dot":S_dot.tolist(),
            "prediction_minus_8sigma_over_15_residual":float(np.linalg.norm(S_dot+8*sigma/15))}

def smooth_ell4_nonclosure():
    z,w=leggauss(96)
    P4=legval(z,[0,0,0,0,1])
    h=z*z-1/3
    ss=.07
    out=[]
    for epsilon in (0.,.5,1.):
        density=1+epsilon*P4
        assert np.min(density)>0
        m2=.5*np.dot(w,density*z*z)
        m4=.5*np.dot(w,density*z**4)
        # moment evolution under homogeneous Bianchi I with axial sigma
        Vgrad_h=-2*ss*z*z*(1-z*z)
        q=ss*h
        dotSzz=.5*np.dot(w,density*(Vgrad_h-h*q))
        prediction=-16*ss/45+8*epsilon*ss/315
        cap=.1+.05707125*epsilon
        # direct integral: even-sky cap |z|>.9
        direct_cap=quad(lambda x:(1+epsilon*legval(x,[0,0,0,0,1])),.9,1,epsabs=1e-13)[0]
        np.testing.assert_allclose([m2,m4,dotSzz,direct_cap],
             [1/3,1/5+8*epsilon/315,prediction,cap],atol=8e-14,rtol=0)
        out.append({"epsilon":epsilon,"m0_flux":0.,
                    "STF5_same_zero":True,"m2zz":m2,"m4zz":m4,
                    "Szz_dot_per_second":dotSzz,"Szz_dot_formula":prediction,
                    "physical_cap_energy_fraction_abs_mu_greater_0p9":direct_cap})
    return out

def exact_area(S):
    l1,l2,l3=np.linalg.eigvalsh(S)
    assert l1<0<l3
    ta=np.sqrt(-l1/(l3-l1))
    tb=np.sqrt(-l2/(l3-l2)) if l2<0 else 0.
    if abs(l2-l1)<1e-14*max(abs(l1),abs(l3)):return float(1-ta)
    def q(t):
        den=(l2-l1)*(1-t*t)
        v=(l2*(1-t*t)+l3*t*t)/den
        return 2/np.pi*np.arcsin(np.sqrt(np.clip(v,0,1)))
    return float(1-ta+quad(q,tb,ta,epsabs=1e-11,epsrel=1e-11,limit=300)[0])

def r66_signed_source_sensitivity():
    obj=json.loads(SOURCE.read_text())
    assert obj["qualified_actual_Commander_temperature_MC_count"]==0
    assert obj["status"]=="ACTUAL_OBSERVATIONS_IDEAL_REFERENCE_COMPLETE"
    d=np.asarray(obj["DQ_uK"],float)
    T0=obj["T0_K"]*1e6
    result={}
    for release in ("PR3","PR4"):
        b=obj["operators"]["n64_l6"]["maps"][release]
        q=np.array(b["full"]["stf5_uK"])
        quo=np.array(b["quotient"]["stf5_uK"])
        alpha0=float(q@d/(d@d))
        np.testing.assert_allclose(q-alpha0*d,quo,atol=1e-11)
        values=[]
        for alpha in (-2.,-1.,0.,1.,2.):
            qtest=q-alpha*d
            S=(8/(15*T0))*stf_matrix(qtest)
            shape=stf_shape(S)
            energy=float(max(0.,-3*np.linalg.eigvalsh(S)[0]))
            values.append({"alpha_fixed_comparator":alpha,"signed_chi":float(shape["signed_chi"]),
              "F_solid_angle_positive_quadrupole":exact_area(S),
              "Q_stress_only_radiation_body":energy,
              "full_flux_measured":False})
        result[release]={"observed_full_STF5_uK":q.tolist(),
          "observed_DQ_quotient_STF5_uK":quo.tolist(),
          "best_projection_coefficient":alpha0,
          "raw_full_signed_chi":float(stf_shape(stf_matrix(q))["signed_chi"]),
          "raw_full_F_solid_angle":exact_area(stf_matrix(q)),
          "unknown_DQ_amplitude_sensitivity":values,
          "meaning":"Same source finite-band released-temperature signed tensor; alpha is not inferred and quotient is not a physical rest-frame tensor."}
    return {"R66_source_json_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      "released_temperature_carrier_sha256":obj["carrier_sha256"],
      "source_qualified_physical_PTE":bool(obj["physical_PTE_qualified"]),
      "source_MC_count":obj["qualified_actual_Commander_temperature_MC_count"],
      "ell6_to_ell8_PR4_quotient_relative_shift":obj["controls"]["n64_l8"]["relative_quotient_shift"],
      "nside64_to128_PR4_quotient_relative_shift":obj["controls"]["n128_l6"]["relative_quotient_shift"],
      "releases":result}

def main():
    return {"schema":"htt.r70.p2_theory_checks/1","date":"2026-11-19",
    "intent":"finite algebraic and source readout checks, no cosmological detection",
    "symbolic":symbolic_koszul(),
    "sky_velocity":quadrature_geometry(),
    "initial_isotropic_kinetic":first_moment_test(),
    "higher_multipole_nonautonomy":smooth_ell4_nonclosure(),
    "R66_actual_signed_source":r66_signed_source_sensitivity(),
    "tests":"all assertions checked at execution; no independent suite or native GR solver"}

if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False))
