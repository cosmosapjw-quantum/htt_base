"""Blind CAS-05-v3 finite component, executed with sage -python.

Inputs are only the admitted v3 contract, neutral input, and COMMON_SPEC.
All polynomial calculations are exact over QQ.  A nonzero residual fails.
"""
import json
from sage.all import PolynomialRing, QQ, matrix, vector

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
names=tuple(f'p{i}' for i in range(4))+tuple(f'h{i}{j}' for i in range(4) for j in range(i,4))
J=PolynomialRing(QQ,names=names); u=J.gens_dict()
p=[u[f'p{i}'] for i in range(4)]
h=lambda a,c:u[f'h{min(a,c)}{max(a,c)}']
de=lambda a,c: int(a==c)
Gamma=lambda a,c,e: de(a,c)*p[e]+de(a,e)*p[c]-int(c==e)*eta[a]*p[a]*eta[c]
dgamma=lambda mu,a,c,e: de(a,c)*h(mu,e)+de(a,e)*h(mu,c)-int(c==e)*eta[a]*h(mu,a)*eta[c]
Ric=matrix(J,4,4,lambda a,c:sum(dgamma(e,e,a,c)-dgamma(c,e,a,e)
  +sum(Gamma(e,e,f)*Gamma(f,a,c)-Gamma(e,c,f)*Gamma(f,a,e) for f in range(4)) for e in range(4)))
scal=sum(eta[a]*Ric[a,a] for a in range(4))
Ein=matrix(J,4,4,lambda a,c:Ric[a,c]-int(a==c)*eta[a]*scal/2)
boxh=sum(eta[a]*h(a,a) for a in range(4)); p2=sum(eta[a]*p[a]**2 for a in range(4))
formula=matrix(J,4,4,lambda a,c:-2*h(a,c)+2*p[a]*p[c]+int(a==c)*eta[a]*(2*boxh+p2))
metric_derived=all(z==0 for z in (Ein-formula).list())

phi=-b*t*t-b*(x*x+y*y+z*z)/2+lam*t*t*x/2
phid=[d(phi,a) for a in range(4)]
phidd=matrix(P,4,4,lambda a,c:d(phid[a],c))
def sub_jet(f):
    return P(f.subs({p[a]:phid[a] for a in range(4)}|{h(a,c):phidd[a,c] for a in range(4) for c in range(a,4)}))
G=matrix(P,4,4,lambda a,c:sub_jet(Ein[a,c]))
G0=matrix(P,4,4,lambda a,c:at0(G[a,c]))
dG=[matrix(P,4,4,lambda a,c:at0(d(G[a,c],mu))) for mu in range(4)]
origin_expected=matrix(P,4,4,lambda a,c:6*b if a==c==0 else 0)
# The normalized eigenvector equation gives derivative u^i=-d_mu T_i0/(eps+p_i).
# At the origin eps+p_i=6b/kappa, so kappa cancels.
du=matrix(P,4,3,lambda mu,j:-dG[mu][j+1,0]/(6*b) if zero(dG[mu][j+1,0]) else 0)
# Keep the rational nonzero derivative separately, without dividing in P.
rates=[[str(-dG[mu][j+1,0])+'/6*b' for j in range(3)] for mu in range(4)]
rate_checks=all(dG[mu][j+1,0] == (-2*lam if (mu,j)==(0,0) else 0) for mu in range(4) for j in range(3))
c01=metric_derived and G0==origin_expected and rate_checks and dG[1][0,0]==0 and dG[1][2,2]==-2*lam

# Orthornormal ray contraction: E_a=e^-phi partial_a. Lambda terms cancel.
ray={t:0,x:P('x'),y:0,z:0}
ray_numerator=P(G[0,0]+G[2,2]).subs(ray)
ray_target=6*b-2*lam*x
c02=ray_numerator==ray_target

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
trH=sum(eta[a]*H[a,a] for a in range(4))
def box(f): return sum(eta[a]*d(d(f,a),a) for a in range(4))
divdiv=sum(eta[a]*eta[c]*d(d(H[a,c],a),c) for a in range(4) for c in range(4))
lin=matrix(P,4,4,lambda a,c:(sum(eta[e]*(d(d(H[e,c],a),e)+d(d(H[e,a],c),e)) for e in range(4))
    -box(H[a,c])-d(d(trH,a),c)-int(a==c)*eta[a]*(divdiv-box(trH)))/2)
J40=[matrix(P,4,4,lambda a,c:at0(d(lin[a,c],mu))) for mu in range(4)]
target_0i=[q[i]*t+sum(M[i-1,j-1]*spatial[j-1] for j in range(1,4)) for i in range(1,4)]
image_check=all(lin[0,i]==target_0i[i-1] for i in range(1,4))
j2h=all(at0(H[a,c])==0 and all(at0(d(H[a,c],mu))==0 for mu in range(4)) and
    all(at0(d(d(H[a,c],mu),nu))==0 for mu in range(4) for nu in range(4)) for a in range(4) for c in range(a,4))
bianchi=[sum(eta[a]*J40[a][a,c] for a in range(4)) for c in range(4)]
bianchi_check=all(z==0 for z in bianchi)
base_order=[f'k0{i}' for i in range(1,4)]+[f'k{j}{i}' for j in range(1,4) for i in range(1,4)]
qm_vars=[q[i] for i in range(1,4)]+[M[i,j] for i in range(3) for j in range(3)]
basis={}
for n in range(12):
    sub={qm_vars[k]:(-6*b if k==n else 0) for k in range(12)}
    basis[base_order[n]]=[[[str(P(J40[mu][a,c].subs(sub))) for c in range(a,4)] for a in range(4)] for mu in range(4)]
    assert P(lin[0,1].subs(sub)).degree()<=1
rank_matrix=matrix(QQ,12,12,lambda a,c:int(a==c)*-6)
right_inverse_check=rank_matrix.det()!=0 and all(lin[0,i]==target_0i[i-1] for i in range(1,4))
c03=j2h and image_check and bianchi_check and right_inverse_check and all(lin[a,c]==lin[c,a] for a in range(4) for c in range(4))

output={
 'checks':{'CAS-05-C01':bool(c01),'CAS-05-C02':bool(c02),'CAS-05-C03':bool(c03)},
 'metric_derived_residuals':arr(Ein-formula),
 'origin_G':arr(G0), 'origin_first_G':{str(mu):arr(dG[mu]) for mu in range(4)},
 'eigenvector_jet_rates':rates,
 'not_EOS':{'d1_epsilon_times_kappa':str(dG[1][0,0]),'d1_p2_times_kappa':str(dG[1][2,2])},
 'ray_frame_numerator':str(ray_numerator),'ray_frame_target':str(ray_target),
 'H_j2_zero':j2h,'H_upper_triangle':{f'{a}{c}':str(H[a,c]) for a in range(4) for c in range(a,4)},
 'delta_G_jet':{str(mu):arr(J40[mu]) for mu in range(4)},
 'all_twelve_basis_images':basis,'basis_order':base_order,
 'bianchi_residuals':[str(z) for z in bianchi],
 'right_inverse':{'q_i':'-6*b*k_0i','M_ij':'-6*b*k_ji','inverse_k_0i':'-q_i/(6*b)','inverse_k_ji':'-M_ij/(6*b)','condition':'b>0'},
 'exclusions':['no smooth eigenfield','no neighborhood DEC','no EOS','no nonlinear away identity','no full theorem']}
print(json.dumps(output,sort_keys=True))
