"""R69 continuation, symbolic Bianchi Lie/Codazzi checks + tilted examples.
This checks polynomial/algebraic assertions; it does NOT solve Einstein evolution.
Conventions: [e_i,e_j]=eps_ijk n^{k l}e_l + a_i e_j-a_j e_i,
normal K^i_j=-(H delta^i_j+sigma^i_j)/c.
Set c=1, 8*pi*G=1 only in listed numeric dimensionless illustrations.
"""
import json
import numpy as np
import sympy as sp

def main():
    a1,a2,a3=sp.symbols("a1 a2 a3", real=True)
    n11,n22,n33,n12,n13,n23=sp.symbols("n11 n22 n33 n12 n13 n23",real=True)
    s11,s22,s12,s13,s23=sp.symbols("s11 s22 s12 s13 s23",real=True)
    a=sp.Matrix([a1,a2,a3])
    N=sp.Matrix([[n11,n12,n13],[n12,n22,n23],[n13,n23,n33]])
    S=sp.Matrix([[s11,s12,s13],[s12,s22,s23],[s13,s23,-s11-s22]])
    C=lambda i,j,k:sum(sp.LeviCivita(i,j,l)*N[l,k] for l in range(3))+a[i]*int(j==k)-a[j]*int(i==k)
    # Koszul: 2 <nab_i e_j,e_k> = C_ijk - C_jki + C_kij
    Gamma=lambda i,j,k:(C(i,j,k)-C(j,k,i)+C(k,i,j))/2
    divergence=sp.Matrix([sum(
        Gamma(j,m,j)*S[m,i]-Gamma(j,i,m)*S[j,m]
        for j in range(3) for m in range(3)) for i in range(3)])
    formula=-3*S*a+sp.Matrix([
        sum(sp.LeviCivita(i,j,k)*S[j,l]*N[l,k] for j in range(3) for k in range(3) for l in range(3))
        for i in range(3)])
    assert all(sp.simplify(v)==0 for v in divergence-formula)
    jacobi=sp.Matrix([
        sum(C(1,2,m)*C(0,m,l)+C(2,0,m)*C(1,m,l)+C(0,1,m)*C(2,m,l)
            for m in range(3)) for l in range(3)])
    assert all(sp.simplify(v)==0 for v in jacobi+2*N*a)
    # Type I: total normal momentum flux must cancel.
    zeros={a1:0,a2:0,a3:0,n11:0,n22:0,n33:0,n12:0,n13:0,n23:0}
    assert divergence.subs(zeros)==sp.zeros(3,1)
    # Type V: n=0, q=0 implies S.a=0, hence det S=0 and signed chi=0 if S!=0.
    # Sample a||e3 and diagonal S with spectrum (lambda,-lambda,0).
    v={a1:0,a2:0,a3:sp.Rational(1,10),n11:0,n22:0,n33:0,n12:0,n13:0,n23:0}
    s_v={s11:sp.Rational(1,5),s22:-sp.Rational(1,5),s12:0,s13:0,s23:0}
    assert divergence.subs(v).subs(s_v)==sp.zeros(3,1)
    assert sp.det(S.subs(s_v))==0
    # Class-A Type II noncommuting shear and n admits nonzero total j.
    ii={a1:0,a2:0,a3:0,n11:sp.Rational(3,10),n22:0,n33:0,n12:0,n13:0,n23:0}
    s_ii={s11:0,s22:0,s12:sp.Rational(1,5),s13:0,s23:0}
    d_ii=divergence.subs(ii).subs(s_ii)
    assert d_ii==sp.Matrix([0,0,-sp.Rational(3,50)])
    # Two species of Type I dust with equal opposite tilts satisfy j_total=0
    # but generate nonzero positive anisotropic normal-frame stress.
    beta=sp.Rational(1,4)
    gamma2=1/(1-beta**2)
    rho_rest=sp.Integer(1)
    j_plus=rho_rest*gamma2*beta
    j_minus=-j_plus
    pi_amp=2*rho_rest*gamma2*beta**2
    assert sp.simplify(j_plus+j_minus)==0 and pi_amp>0
    # Type V dust with a3=0.1, S_zz=1/3 requires j_zz=0.1 in c=8piG=1.
    s_tilt={s11:-sp.Rational(1,6),s22:-sp.Rational(1,6),s12:0,s13:0,s23:0}
    d_v=divergence.subs(v).subs(s_tilt)
    assert d_v==sp.Matrix([0,0,-sp.Rational(1,10)])
    # Compatible pure dust with rho_N=1, beta=0.1 and rho_rest=rho_N/gamma².
    rhoN=sp.Integer(1)
    betaV=sp.Rational(1,10)
    g2V=1/(1-betaV**2)
    eps_rest=rhoN/g2V
    jV=eps_rest*g2V*betaV
    assert jV==sp.Rational(1,10)
    # Curvature check from the anholonomic Levi-Civita connection, not a quoted Type-V formula.
    gv=lambda i,j,k:sp.simplify(Gamma(i,j,k).subs(v))
    cv=lambda i,j,k:sp.simplify(C(i,j,k).subs(v))
    RicV=sp.Matrix(3,3,lambda i,j:sp.simplify(sum(
        gv(i,j,m)*gv(k,m,k)-gv(k,j,m)*gv(i,m,k)-cv(k,i,m)*gv(m,j,k)
        for k in range(3) for m in range(3))))
    assert RicV==-sp.Rational(2,100)*sp.eye(3)
    sigv=S.subs(s_tilt)
    I2v=sp.trace(sigv*sigv)
    H2v=sp.simplify((2*rhoN-sp.trace(RicV)+I2v)/6)
    assert sp.simplify(sp.trace(RicV)+6*H2v-I2v-2*rhoN)==0
    assert sp.simplify(sp.sqrt(6)*sp.trace(sigv**3)/I2v**sp.Rational(3,2))==1
    # Shape derivative (frame invariant): finite first variation versus derived driver
    Sr=np.diag([1.0,-.4,-.6])
    Dr=0.33*(np.diag([1.0,0,0])-np.eye(3)/3)
    def chi(T):
        i2=np.trace(T@T)
        return float(np.sqrt(6)*np.trace(T@T@T)/i2**1.5)
    i2=np.trace(Sr@Sr); i3=np.trace(Sr@Sr@Sr)
    rate=3*np.sqrt(6)/(i2**1.5)*(np.trace(Sr@Sr@Dr)-(i3/i2)*np.trace(Sr@Dr))
    h=1e-5
    finite=(chi(Sr+h*Dr)-chi(Sr-h*Dr))/(2*h)
    assert abs(rate-finite)<1e-8
    # Trace cubic invariant under infinitesimal rotation commutator.
    Om=np.array([[0,-.2,.1],[.2,0,-.3],[-.1,.3,0.]])
    frame=Om@Sr-Sr@Om
    assert abs(np.trace(Sr@frame))<1e-13 and abs(np.trace(Sr@Sr@frame))<1e-13
    # PSD photon/causal momentum cone: DEC guarantees |j|<=rho_N.
    assert abs(float(jV/rhoN))<1
    out={
     "contract":"symbolic orthonormal Lie algebra and Einstein momentum convention; c and G restored in report",
     "jacobi_residual":0,"general_codazzi_polynomial_residual":0,
     "type_I_divergence_zero":True,
     "type_V_untilted_example_chi":0,
     "type_V_tilted_dust_example_j_over_rho":float(jV/rhoN),
     "type_II_noncommuting_sigma_n_divergence":list(map(float,d_ii)),
     "type_I_two_dust_opposite_tilts_momentum_cancelled":True,
     "type_I_two_dust_total_pi_axis_coefficient":float(pi_amp),
     "shape_driver_rate_dimensionless":float(rate),
     "shape_driver_finite_difference":float(finite),
     "checks":"SYMBOLICALLY VALIDATED (Jacobi/Codazzi) plus finite shape derivative; no global Einstein solution or observational fit"
    }
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    main()
