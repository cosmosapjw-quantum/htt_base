"""R75 P5 generic Bianchi Lie/Codazzi + physical five-view finite verification.

Read-only R49 historical convention atlas and 4000 thinned conditional posterior.
Computes exact Lie rank, DEC tilt inversion, signed STF morphology, and
source-conditional shape pushforward. NOT a full Einstein-Boltzmann solver,
family likelihood, cosmological detection or independently calibrated PTE.

Run from htt_base root:
 PYTHONPATH=. PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -B docs/research_program/observational_publication_20261015/R75_P5_LIE_TILT_FIVEVIEW_20261119/verify_p5.py
"""
from pathlib import Path
import hashlib,json
import numpy as np
import sympy as sp
from scipy.integrate import quad
from scipy.special import roots_legendre

R=Path("docs/research_program/observational_publication_20261015")
R49=R/"R49_GENERAL_TILTED_BIANCHI_20261112"
ATLAS=R49/"BIANCHI_CONVENTION_BRIDGE.json"
RECEIPT=R49/"GBI08_PRODUCTION_INFERENCE_RECEIPT.json"
CHAIN=Path("/mnt/extdrive/workdir/r49_chains/r49_joint_posterior_chains.npz")
C=299792458.0
G=6.67430e-11

def sha256(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def tensor(x):
    x=np.asarray(x,float);assert x.shape[-1]==5
    z=np.zeros(x.shape[:-1]+(3,3),float)
    z[...,0,0]=x[...,0];z[...,1,1]=x[...,1]
    z[...,2,2]=-x[...,0]-x[...,1]
    z[...,0,1]=z[...,1,0]=x[...,2]
    z[...,0,2]=z[...,2,0]=x[...,3]
    z[...,1,2]=z[...,2,1]=x[...,4]
    return z

def L_mat(a,n):
    """Canonical x=(s11,s22,s12,s13,s23), diagonal N, a along e1."""
    a=np.asarray(a,float);n=np.asarray(n,float)
    assert np.max(abs(a[1:]))==0
    # class A can have general N diagonal; class B forces n1=0
    if abs(a[0])>0:assert abs(n[0])<1e-14*max(1.,np.max(abs(n)))
    A=float(a[0]);n1,n2,n3=n
    return np.array([[-3*A,0,0,0,n3-n2],
                     [0,0,-3*A,n1-n3,0],
                     [0,0,n2-n1,-3*A,0]],float)

def direct_C(S,a,N):
    Ndiag=np.diag(N) if np.ndim(N)==2 else np.asarray(N,float)
    return np.array([-3*sum(S[i,j]*a[j] for j in range(3))+
          sum(int(sp.LeviCivita(i,j,k))*S[j,k]*Ndiag[k]
              for j in range(3) for k in range(3)) for i in range(3)],float)

def rank_scale(M):
    s=np.linalg.svd(M,compute_uv=False)
    return int(np.sum(s>1e-10*s[0])) if s.size and s[0]>0 else 0

def shape(S):
    """STF signed shape invariant stable under small source amplitudes."""
    S=np.asarray(S,float)
    amp=np.max(abs(S),axis=(-2,-1))
    if np.any(amp<=0):raise ValueError("zero STF chi undefined")
    T=S/amp[...,None,None]
    I2=np.trace(T@T,axis1=-2,axis2=-1)
    I3=np.trace(T@T@T,axis1=-2,axis2=-1)
    chi=np.sqrt(6)*I3/(I2**1.5)
    assert np.max(abs(chi))<1+1e-9
    return chi

def fullsky_F_from_eigenvalues(e,nodes=192):
    """Vectorized 1D exact sphere-integral quadrature in ellipsoidal eigenframe."""
    e=np.atleast_2d(np.asarray(e,float))
    l1,l2,l3=e[:,0],e[:,1],e[:,2]
    assert np.all(l1<0) and np.all(l3>0)
    ta=np.sqrt(-l1/(l3-l1))
    tb=np.where(l2<0,np.sqrt(np.maximum(0.,-l2/(l3-l2))),0.)
    x,w=roots_legendre(nodes)
    t=tb[:,None]+(ta-tb)[:,None]*(1+x[None,:])/2
    den=(l2-l1)[:,None]*(1-t*t)
    num=l2[:,None]*(1-t*t)+l3[:,None]*t*t
    ratio=np.divide(num,den,out=np.ones_like(num),where=(abs(den)>1e-25))
    val=2/np.pi*np.arcsin(np.sqrt(np.clip(ratio,0,1)))
    integ=(ta-tb)*(.5*np.sum(w[None,:]*val,axis=1))
    f=1-ta+integ
    return f

def symbolic_and_convention():
    a,n1,n2,n3=sp.symbols('a n1 n2 n3',real=True)
    s1,s2,s12,s13,s23=sp.symbols('s1 s2 s12 s13 s23',real=True)
    S=sp.Matrix([[s1,s12,s13],[s12,s2,s23],[s13,s23,-s1-s2]])
    aa=sp.Matrix([a,0,0]);N=sp.diag(n1,n2,n3)
    X=sp.Matrix([-3*sum(S[i,j]*aa[j] for j in range(3))+
        sum(sp.LeviCivita(i,j,k)*S[j,k]*N[k,k]
            for j in range(3) for k in range(3)) for i in range(3)])
    m=X.jacobian([s1,s2,s12,s13,s23])
    assert sp.simplify(m[0,4]-(n3-n2))==0
    assert sp.simplify(m[1,3]-(n1-n3))==0
    det=sp.factor(m.extract([1,2],[2,3]).det().subs(n1,0))
    assert sp.simplify(det-(9*a*a+n2*n3))==0
    # exceptional source restrictions exact
    m_exc=m.subs({a:1,n1:0,n2:3,n3:-3})
    assert m_exc.rank()==2
    assert (sp.Matrix([[0,3,3]])*m_exc)==sp.zeros(1,5)
    vec=sp.Matrix([-2,0,0,0,1])
    assert m_exc*vec==sp.zeros(3,1)
    return {"symbolic_Class_B_lower_block_determinant":str(det),
            "symbolic_exceptional_exact_rank":m_exc.rank(),
            "symbolic_exceptional_zero_total_flux_shear":list(map(int,vec)),
            "symbolic_left_null_flux":[0,3,3],
            "direct_Lie_bracket_to_C_5D":"checked by symbolic Jacobian"}

def class_atlas():
    d=json.loads(ATLAS.read_text())
    assert d["verification"]["all_passed"]
    reports=d["verification"]["reports"]
    cases={}
    for name,v in reports.items():
        a=np.asarray(v["a_ver2_proper"],float)
        n=np.asarray(v["n_diag_ver2_proper"],float)
        m=L_mat(a,n)
        s=np.linalg.svd(m,compute_uv=False)
        rk=rank_scale(m)
        # direct indexed contraction vs the linear matrix on random tracefree shear
        rng=np.random.default_rng(77)
        for _ in range(8):
            x=rng.normal(size=5)
            np.testing.assert_allclose(m@x,direct_C(tensor(x),a,n),atol=1e-12)
        if name=="VI_minus_1_over_9":assert rk==2
        if name=="V":assert rk==3
        if name in ("FLRW","I","IX"):assert rk==0
        cases[name]={
          "class_label":v["class_label"],"source_h":v.get("h_parameter"),
          "a_a_ver2":a.tolist(),"Ndiag_ver2":n.tolist(),
          "Codazzi_signed_STF5_to_normal_flux_rank":rk,
          "shear_kernel_dimension":5-rk,
          "singular_values":s.tolist(),
          "source_jacobi_residual":v["jacobi_residual"],
          "comment":"R49 convention source a,N are example geometric settings, not actual posterior matter density/tilt fit"}
    return cases

def tilt_and_morphology():
    qvalues=[]
    for w in [0.,1/3,1.]:
        for beta in [0.,.001,.15,.6,.9]:
            q=(1+w)*beta/(1+w*beta**2)
            b_inv=2*q/((1+w)+np.sqrt((1+w)**2-4*w*q*q))
            assert abs(beta-b_inv)<3e-14,(w,beta,b_inv)
            qvalues.append({"w":w,"beta":beta,"Q_Lie":q,"reconstructed_beta":b_inv})
    x_V=np.array([0.,.3,0.,0.,.09]) # Sigma_11=0, sigma_12=sigma_13=0
    m_V=L_mat([.2,0,0],[0,0,0])
    assert np.linalg.norm(m_V@x_V)<1e-14
    sV=tensor(x_V)
    chi_V=float(shape(sV))
    assert abs(chi_V)<1e-14
    fV=float(fullsky_F_from_eigenvalues(np.linalg.eigvalsh(sV))[0])
    assert abs(fV-.5)<3e-8  # 192-node quadrature endpoint error; exact symmetry gives 1/2
    mVI=L_mat([1,0,0],[0,3,-3])
    xVI=np.array([-2.,0.,0.,0.,1.])
    assert np.linalg.norm(mVI@xVI)<1e-14
    svi=tensor(xVI)
    chiVI=float(shape(svi))
    assert abs(chiVI-(6*np.sqrt(6)/(10**1.5)))<1e-13
    fVI=float(fullsky_F_from_eigenvalues(np.linalg.eigvalsh(svi))[0])
    assert abs(fVI-.5)>.02
    # tilted Type V j/rho=.1, c=8piG=1 and  rho_N=1; physical a=0.1 e3.
    sig=np.diag([-.16666666666666666,-.16666666666666666,.3333333333333333])
    a=np.array([0.,0.,.1]);n=np.zeros(3)
    cv=direct_C(sig,a,n)
    assert np.linalg.norm(cv-np.array([0,0,-.1]))<1e-14
    h2=(2+.06+np.trace(sig@sig))/6
    assert h2>0
    cval=float(shape(sig))
    assert abs(cval-1)<1e-14
    # Type I counterflow two opposite streams normal rho_total=1, β=0.2 each
    beta=.2
    v=np.array([0.,0.,1.])
    pi_total=beta**2*(np.outer(v,v)-np.eye(3)/3)
    assert np.linalg.norm(pi_total)>0
    assert np.linalg.norm(np.array([.5*beta,-.5*beta]))>0
    return {"single_fluid_Q_beta_inverse_checks":qvalues,
            "Type_V_no_total_flux":{"x_stf5":x_V.tolist(),"chi":chi_V,"F_Omega":fV},
            "exceptional_VI_m1_9_no_total_flux":{"x_stf5":xVI.tolist(),"chi":chiVI,"F_Omega":fVI},
            "Type_V_tilted_instantaneous_compatibility":{"normal_flux_divergence_C":cv.tolist(),
              "normal_rho":1.,"normal_dust_beta_z":.1,"Hamiltonian_H_squared_in_c_8piG_1_units":float(h2),
              "signed_chi":cval,"not_a_global_solution":True},
            "Type_I_two_counter_streams":{"total_normal_j":0.,"individual_beta":[beta,-beta],
              "total_anisotropic_stress":pi_total.tolist(),"physical_takeaway":"j=0 does not imply all beta_s=0"}}

def so3_covariance_check():
    from scipy.spatial.transform import Rotation
    rng=np.random.default_rng(7300)
    epsilon=np.zeros((3,3,3),int)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                epsilon[i,j,k]=int(sp.LeviCivita(i,j,k))
    err=0.
    for _ in range(40):
        v=rng.normal(size=5);S=tensor(v)
        mat=rng.normal(size=(3,3));N=.5*(mat+mat.T)
        a=rng.normal(size=3)
        a/=np.linalg.norm(a)
        P=np.eye(3)-np.outer(a,a)
        N=P@N@P
        c0=-3*S@a+np.einsum("ijk,jl,lk->i",epsilon,S,N)
        rot=Rotation.random(random_state=rng).as_matrix()
        Sr=rot@S@rot.T; Nr=rot@N@rot.T; ar=rot@a
        cr=-3*Sr@ar+np.einsum("ijk,jl,lk->i",epsilon,Sr,Nr)
        err=max(err,float(np.linalg.norm(cr-rot@c0)))
    assert err<5e-13
    return {"samples_SO3":40,"max_rotation_equivariance_error":err,
            "Lie_rank_and_Q_Lie_invariant_under_proper_rotation":True}

def check_vectorized_area():
    rng=np.random.default_rng(501)
    for _ in range(12):
        x=rng.normal(size=5)
        ee=np.linalg.eigvalsh(tensor(x))
        ff=float(fullsky_F_from_eigenvalues(ee)[0])
        l1,l2,l3=ee
        ta=np.sqrt(-l1/(l3-l1))
        tb=np.sqrt(-l2/(l3-l2)) if l2<0 else 0.
        def h(t):
            num=l2*(1-t*t)+l3*t*t
            den=(l2-l1)*(1-t*t)
            return 2/np.pi*np.arcsin(np.sqrt(np.clip(num/den,0,1)))
        fquad=1-ta+quad(h,tb,ta,epsabs=1e-12,epsrel=1e-12,limit=200)[0]
        assert abs(ff-fquad)<2e-5
        opposite=float(fullsky_F_from_eigenvalues(np.linalg.eigvalsh(-tensor(x)))[0])
        assert abs(ff+opposite-1)<1e-5
    return True

def posterior_geometry():
    receipt=json.loads(RECEIPT.read_text())
    assert sha256(CHAIN)==receipt["chains_sha256"]
    with np.load(CHAIN,allow_pickle=False) as z:
        draw=np.asarray(z["posterior_draws_thinned"],float)
        names=list(map(str,z["param_names"]))
    assert draw.shape==(4000,24)
    assert names[:5]==["sigma_xx","sigma_yy","sigma_xy","sigma_xz","sigma_yz"]
    sig=draw[:,:5]; S=tensor(sig)
    cart_metric=np.array([[2,1,0,0,0],[1,2,0,0,0],[0,0,2,0,0],[0,0,0,2,0],[0,0,0,0,2]],float)
    norm_G=np.sqrt(np.einsum("ni,ij,nj->n",sig,cart_metric,sig))
    norm_tr=np.sqrt(np.trace(S@S,axis1=1,axis2=2))
    np.testing.assert_allclose(norm_G,norm_tr,rtol=2e-13,atol=1e-16)
    assert abs(np.mean(norm_G)-receipt["htt_five_views_single_posterior"]["x_summary"]["sigma_gram_norm_mean"])<5e-13
    chi=shape(S)
    eig=np.linalg.eigvalsh(S)
    f=fullsky_F_from_eigenvalues(eig)
    assert np.all((f>0)&(f<1))
    def quant(v):return [float(x) for x in np.quantile(v,[.05,.16,.5,.84,.95])]
    # Reuse the same source posterior, not a new likelihood or family inference.
    ppc=receipt["ppc_per_probe"]
    return {
      "R49_historical_production_claim_tier":receipt["claim_tier"],
      "R49_family_adjudication_status":receipt["family_adjudication_status"],
      "source_chain_sha256":sha256(CHAIN),
      "n_source_posterior_draws":len(sig),"parameter_names_5":names[:5],
      "posterior_shear_frobenius_mean":float(np.mean(norm_G)),
      "posterior_shear_signed_chi_quantiles_05_16_50_84_95":quant(chi),
      "posterior_shear_intrinsic_fullsky_FOmega_quantiles_05_16_50_84_95":quant(f),
      "source_shape_frac_chi_positive":float(np.mean(chi>0)),
      "source_shape_frac_FOmega_below_half":float(np.mean(f<.5)),
      "source_PP_bad_probes":{
          p:{"ppc_p":ppc[p]["ppc_pvalue"],"chi2_per_dof":ppc[p]["chi2_per_dof"]}
          for p in ("CMB","Gaia","CF4")},
      "source_prior_Q_shear_anchor":receipt["htt_five_views_single_posterior"]["Q_anchors"]["shear_sigma"]["status"],
      "source_model_limit":"R49 transfer conditional posterior only; F is source-posterior pushforward of normal-tensor geometry, not physical observed sky/independent cosmological detection"
    }

def main():
    assert check_vectorized_area()
    sym=symbolic_and_convention()
    atlas=class_atlas()
    tests=tilt_and_morphology()
    posterior=posterior_geometry()
    return {"schema":"htt.r75.p5_lie_tilt_physical_fiveview/1",
      "source_hashes":{"R49_atlas":sha256(ATLAS),"R49_production_receipt":sha256(RECEIPT),
        "R49_historical_chain":sha256(CHAIN)},
      "convention":"Cartesian STF5 xx,yy,xy,xz,yz; n_z=-xx-yy; Lie a,N m^-1 and sigma s^-1, epsilon123 +1; dimensionless Σ and cA/H",
      "symbolic":sym,"SO3_covariance":so3_covariance_check(),"source_all_Bianchi_atlas":atlas,
      "synthetic_validations":tests,
      "actual_R49_source_posterior_geometry":posterior,
      "scope":"exact algebra, 4000 source-conditional posterior shape pushforward and limited instantaneous Einstein constraints; no new calibrated Bianchi family likelihood or full solution"}
if __name__=="__main__":
    print(json.dumps(main(),indent=2,ensure_ascii=False))
