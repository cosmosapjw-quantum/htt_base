"""Blind CAS-05-v3 finite component, executed with sage -python.

Inputs are only the admitted v3 contract, neutral input, and COMMON_SPEC.
All polynomial calculations are exact over QQ.  A nonzero residual fails.
"""
import json
from sage.all import PolynomialRing, QQ, matrix, SR, exp

P = PolynomialRing(QQ, names=("b","lam","t","x","y","z") + tuple(f"q{i}" for i in range(1,4)) + tuple(f"m{i}{j}" for i in range(1,4) for j in range(1,4)))
v = P.gens_dict(); b=v['b']; lam=v['lam']; X=[v[n] for n in ('t','x','y','z')]
t,x,y,z=X; q=[0]+[v[f'q{i}'] for i in range(1,4)]
M=matrix(P,3,3,[v[f'm{i}{j}'] for i in range(1,4) for j in range(1,4)])
eta=[-1,1,1,1]

def d(f,a): return f.derivative(X[a])
def at0(f): return P(f).subs({w:0 for w in X})
def zero(f): return P(f)==0
def arr(A): return [[str(z) for z in row] for row in A]

# Formal conformal Christoffel/Ricci calculation.  p_a and h_ab are free jet
# variables; no target Einstein formula is put into the curvature construction.
names=('E',)+tuple(f'p{i}' for i in range(4))+tuple(f'h{i}{j}' for i in range(4) for j in range(i,4))
J=PolynomialRing(QQ,names=names); u=J.gens_dict(); E=u['E']; K=J.fraction_field()
p=[u[f'p{i}'] for i in range(4)]
h=lambda a,c:u[f'h{min(a,c)}{max(a,c)}']
de=lambda a,c: int(a==c)
metric=lambda a,c:K(E*eta[a]) if a==c else K(0)
metric_inv=lambda a,c:K(eta[a]/E) if a==c else K(0)
metric_d=lambda mu,a,c:K(2*E*p[mu]*eta[a]) if a==c else K(0)
Gamma=lambda a,c,e:sum(metric_inv(a,f)*(metric_d(c,f,e)+metric_d(e,f,c)-metric_d(f,c,e))/2 for f in range(4))
dgamma=lambda mu,a,c,e:K(2*E*p[mu])*K(Gamma(a,c,e)).derivative(E)+sum(h(mu,f)*K(Gamma(a,c,e)).derivative(p[f]) for f in range(4))
gamma_formula=lambda a,c,e:de(a,c)*p[e]+de(a,e)*p[c]-int(c==e)*eta[a]*p[a]*eta[c]
gamma_derived=all(Gamma(a,c,e)==gamma_formula(a,c,e) for a in range(4) for c in range(4) for e in range(4))
Ric=matrix(K,4,4,lambda a,c:sum(dgamma(e,e,a,c)-dgamma(c,e,a,e)
  +sum(Gamma(e,e,f)*Gamma(f,a,c)-Gamma(e,c,f)*Gamma(f,a,e) for f in range(4)) for e in range(4)))
scal=sum(eta[a]*Ric[a,a] for a in range(4))
Ein=matrix(K,4,4,lambda a,c:Ric[a,c]-int(a==c)*eta[a]*scal/2)
boxh=sum(eta[a]*h(a,a) for a in range(4)); p2=sum(eta[a]*p[a]**2 for a in range(4))
formula=matrix(K,4,4,lambda a,c:-2*h(a,c)+2*p[a]*p[c]+int(a==c)*eta[a]*(2*boxh+p2))
metric_derived=gamma_derived and all(z==0 for z in (Ein-formula).list())

phi=-b*t*t-b*(x*x+y*y+z*z)/2+lam*t*t*x/2
phid=[d(phi,a) for a in range(4)]
phidd=matrix(P,4,4,lambda a,c:d(phid[a],c))
def sub_jet(f):
    return P(J(f).subs({E:1}|{p[a]:phid[a] for a in range(4)}|{h(a,c):phidd[a,c] for a in range(4) for c in range(a,4)}))
G=matrix(P,4,4,lambda a,c:sub_jet(Ein[a,c]))
G0=matrix(P,4,4,lambda a,c:at0(G[a,c]))
dG=[matrix(P,4,4,lambda a,c:at0(d(G[a,c],mu))) for mu in range(4)]
origin_expected=matrix(P,4,4,lambda a,c:6*b if a==c==0 else 0)
# Exact differentiated *normalized* eigenvector equation.  g'=0 at 0,
# so normalization gives du^0=0, and T^a_b has diagonal (-eps,p,p,p).
TR=PolynomialRing(QQ,names=('bb','ll','Lambda','kappa','c'))
tv=TR.gens_dict(); bb=tv['bb']; ll=tv['ll']; Lambda=tv['Lambda']; kappa=tv['kappa']; cc=tv['c']; TF=TR.fraction_field()
toT=lambda f:TR(str(f).replace('lam','ll').replace('b','bb'))
eps=TF((6*bb-Lambda)/kappa); pressure=TF(Lambda/kappa); gap=eps+pressure
du=[[TF(ll/(3*bb)) if (mu,a)==(0,1) else TF(0) for a in range(4)] for mu in range(4)]
deps=[TF(toT(dG[mu][0,0])/kappa) for mu in range(4)]
eig_residual=[]
for mu in range(4):
    eig_residual.append([TF(eta[a]*toT(dG[mu][a,0])/kappa+(pressure if a else -eps)*du[mu][a]
        +eps*du[mu][a]+(deps[mu] if a==0 else 0)) for a in range(4)])
normalization_residual=[-2*du[mu][0] for mu in range(4)]
acceleration=TF(cc*cc*du[0][1])
stress_checks=(TF(toT(G0[0,0])-Lambda)/kappa==eps and
    all(TF(toT(G0[i,i])+Lambda)/kappa==pressure for i in range(1,4)) and
    gap==TF(6*bb/kappa))
rate_checks=all(z==0 for row in eig_residual for z in row) and all(z==0 for z in normalization_residual)
non_eos_check=(toT(dG[1][0,0])==0 and toT(dG[1][2,2])==-2*ll and ll!=0)
c01=metric_derived and G0==origin_expected and stress_checks and rate_checks and acceleration==TF(cc*cc*ll/(3*bb)) and non_eos_check

# Orthornormal ray contraction: E_a=e^-phi partial_a. Lambda terms cancel.
ray={t:0,y:0,z:0}
ray_numerator=P(G[0,0]+G[2,2]).subs(ray)
ray_target=6*b-2*lam*x
phi_ray=P(phi.subs(ray))
frame_ray=exp(-2*SR(phi_ray))*SR(ray_numerator)
frame_target=exp(SR(b*x*x))*SR(ray_target)
lambda0=ray_numerator.subs({lam:0})
root_residual=P.fraction_field()(ray_numerator).subs({x:3*b/lam})
c02=(ray_numerator==ray_target and -2*phi_ray==b*x*x and
     bool((frame_ray-frame_target).simplify_full()==0) and lambda0==6*b and root_residual==0)

# Metric three-jet: exp(2 phi0)eta+H and eta+2phi0 eta+H have
# identical derivatives through order three at 0. Background has no cubic
# part; H is homogeneous cubic, so first curvature jet is flat linearized G[H].
r2=x*x+y*y+z*z; spatial=[x,y,z]
S=(M+M.transpose())/2; W=(M-M.transpose())/2
F=sum(S[i,j]*spatial[i]*spatial[j] for i in range(3) for j in range(3))
H=matrix(P,4,4,lambda a,c:0)
for i in range(1,4):
    H[0,i]=-t*r2*q[i]/2-r2*sum(W[i-1,j-1]*spatial[j-1] for j in range(1,4))/5
    H[i,0]=H[0,i]
    H[i,i]=-t*F/2
# Derive both baseline and perturbed Einstein jets directly from metric
# derivatives, connection, Ricci and scalar.  Since dg(0)=0, Gamma(0)=0;
# derivative-of-inverse times dg and Gamma*Gamma vanish through first order.
phi0=-b*t*t-b*r2/2
gbase=matrix(P,4,4,lambda a,c:eta[a]*(1+2*phi0) if a==c else 0)
gpert=gbase+H
def geometric_jets(metric):
    dg0=[matrix(P,4,4,lambda a,c:at0(d(metric[a,c],mu))) for mu in range(4)]
    assert all(z==0 for A in dg0 for z in A.list())
    def dgamm(mu,a,c,e):
        return eta[a]*(at0(d(d(metric[a,e],mu),c))+at0(d(d(metric[a,c],mu),e))-at0(d(d(metric[c,e],mu),a)))/2
    def ddgamm(mu,nu,a,c,e):
        return eta[a]*(at0(d(d(d(metric[a,e],mu),nu),c))+at0(d(d(d(metric[a,c],mu),nu),e))-at0(d(d(d(metric[c,e],mu),nu),a)))/2
    R0=matrix(P,4,4,lambda a,c:sum(dgamm(e,e,a,c)-dgamm(c,e,a,e) for e in range(4)))
    R1=[matrix(P,4,4,lambda a,c:sum(ddgamm(mu,e,e,a,c)-ddgamm(mu,c,e,a,e) for e in range(4))) for mu in range(4)]
    scalar0=sum(eta[a]*R0[a,a] for a in range(4))
    scalar1=[sum(eta[a]*R1[mu][a,a] for a in range(4)) for mu in range(4)]
    return (matrix(P,4,4,lambda a,c:R0[a,c]-int(a==c)*eta[a]*scalar0/2),
      [matrix(P,4,4,lambda a,c:R1[mu][a,c]-int(a==c)*eta[a]*scalar1[mu]/2) for mu in range(4)])
base0,base1=geometric_jets(gbase)
pert0,pert1=geometric_jets(gpert)
trH=sum(eta[a]*H[a,a] for a in range(4))
def box(f): return sum(eta[a]*d(d(f,a),a) for a in range(4))
divdiv=sum(eta[a]*eta[c]*d(d(H[a,c],a),c) for a in range(4) for c in range(4))
lin=matrix(P,4,4,lambda a,c:(sum(eta[e]*(d(d(H[e,c],a),e)+d(d(H[e,a],c),e)) for e in range(4))
    -box(H[a,c])-d(d(trH,a),c)-int(a==c)*eta[a]*(divdiv-box(trH)))/2)
J40=[matrix(P,4,4,lambda a,c:at0(d(lin[a,c],mu))) for mu in range(4)]
geometry_jet_check=(base0==origin_expected and pert0==base0 and
    all(z==0 for A in base1 for z in A.list()) and
    all(pert1[mu]-base1[mu]==J40[mu] for mu in range(4)))
target_0i=[q[i]*t+sum(M[i-1,j-1]*spatial[j-1] for j in range(1,4)) for i in range(1,4)]
image_check=all(lin[0,i]==target_0i[i-1] for i in range(1,4))
j2h=all(at0(H[a,c])==0 and all(at0(d(H[a,c],mu))==0 for mu in range(4)) and
    all(at0(d(d(H[a,c],mu),nu))==0 for mu in range(4) for nu in range(4)) for a in range(4) for c in range(a,4))
bianchi=[sum(eta[a]*J40[a][a,c] for a in range(4)) for c in range(4)]
bianchi_check=all(z==0 for z in bianchi)
base_order=[f'k0{i}' for i in range(1,4)]+[f'k{j}{i}' for j in range(1,4) for i in range(1,4)]
qm_vars=[q[i] for i in range(1,4)]+[M[i,j] for i in range(3) for j in range(3)]
basis={}
for label in base_order:
    mu=int(label[1]); i=int(label[2]); selected=q[i] if mu==0 else M[i-1,mu-1]
    sub={v:(-6*b if v==selected else 0) for v in qm_vars}
    basis[label]=[[[str(P(J40[nu][a,c].subs(sub))) for c in range(a,4)] for a in range(4)] for nu in range(4)]
    assert all(d(d(P(lin[0,i].subs(sub)),a),c)==0 for i in range(1,4) for a in range(4) for c in range(4))
# Universal arbitrary-k substitution, with neutral transpose M_ij=-6b*k_ji.
KR=PolynomialRing(QQ,names=('b',)+tuple(base_order)); kv=KR.gens_dict(); kb=kv['b']; KF=KR.fraction_field()
images=[]
for name in P.variable_names():
    if name=='b': images.append(kb)
    elif name.startswith('q'): images.append(-6*kb*kv['k0'+name[1:]])
    elif name.startswith('m'): images.append(-6*kb*kv['k'+name[2]+name[1]])
    else: images.append(KR(0))
toK=P.hom(images,KR)
induced_eigen_residuals=[[KF(6*kb*kv[f'k{mu}{i}']+toK(J40[mu][0,i])) for i in range(1,4)] for mu in range(4)]
right_inverse_check=(all(z==0 for row in induced_eigen_residuals for z in row) and
    all(lin[0,i]==target_0i[i-1] for i in range(1,4)) and
    all(P(J40[nu][0,j].subs({v:(-6*b if v==(q[i] if mu==0 else M[i-1,mu-1]) else 0) for v in qm_vars}))==
        (-6*b if (nu,j)==(mu,i) else 0) for mu in range(4) for i in range(1,4) for nu in range(4) for j in range(1,4)))
c03=j2h and geometry_jet_check and image_check and bianchi_check and right_inverse_check and all(lin[a,c]==lin[c,a] for a in range(4) for c in range(4))

output={
 'checks':{'CAS-05-C01':bool(c01),'CAS-05-C02':bool(c02),'CAS-05-C03':bool(c03)},
 'metric_derived_residuals':arr(Ein-formula),'metric_derived_christoffel':gamma_derived,
 'origin_G':arr(G0), 'origin_first_G':{str(mu):arr(dG[mu]) for mu in range(4)},
 'stress_origin':{'epsilon':str(eps),'p_i':str(pressure),'gap':str(gap),'Lambda':str(Lambda),'kappa':str(kappa)},
 'eigenvector_jet_rates':[[str(du[mu][i]) for i in range(4)] for mu in range(4)],
 'normalized_eigenvector_jet_residuals':[[str(z) for z in row] for row in eig_residual],
 'normalization_jet_residuals':[str(z) for z in normalization_residual],
 'acceleration_A1':str(acceleration),
 'not_EOS':{'d1_epsilon':str(deps[1]),'d1_p2':str(TF(toT(dG[1][2,2])/kappa)),'nonzero_when':'lambda != 0'},
 'ray_frame_numerator':str(ray_numerator),'ray_frame_target':str(ray_target),
 'ray_phi':str(phi_ray),'orthonormal_frame_expression':str(frame_ray),
 'lambda0_ray_numerator':str(lambda0),'radius_root_condition':'lambda != 0','radius_root':'3*b/lambda','radius_root_residual':str(root_residual),
 'H_j2_zero':j2h,'H_upper_triangle':{f'{a}{c}':str(H[a,c]) for a in range(4) for c in range(a,4)},
 'metric_connection_ricci_jet_check':geometry_jet_check,
 'delta_G_jet':{str(mu):arr(J40[mu]) for mu in range(4)},
 'all_twelve_basis_images':basis,'basis_order':base_order,
 'bianchi_residuals':[str(z) for z in bianchi],
 'induced_eigenvector_jet_residuals':[[str(z) for z in row] for row in induced_eigen_residuals],
 'right_inverse':{'q_i':'-6*b*k_0i','M_ij':'-6*b*k_ji','inverse_k_0i':'-q_i/(6*b)','inverse_k_ji':'-M_ij/(6*b)','condition':'b>0'},
 'exclusions':['no smooth eigenfield','no neighborhood DEC','no EOS','no nonlinear away identity','no full theorem']}
print(json.dumps(output,sort_keys=True))
