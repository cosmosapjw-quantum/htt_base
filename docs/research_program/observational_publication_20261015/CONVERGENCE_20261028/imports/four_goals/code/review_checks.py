"""One bounded independent check of selected high-impact claims.

Own outputs only; no imports of production scripts, ODE, data fit or remote write.
"""
from pathlib import Path
import json
from fractions import Fraction as F
from math import prod
import numpy as np
from scipy.linalg import expm
from scipy.stats import ncx2

ROOT = Path(__file__).resolve().parents[1]
rng = np.random.default_rng(109282026)
class Poly:
    """Sparse exact rational polynomials; eight variables suffice for both checks."""
    def __init__(self, terms=0):
        self.terms = {k:F(v) for k,v in terms.items() if v} if isinstance(terms,dict) else ({(0,)*8:F(terms)} if terms else {})
    def __add__(self, other):
        other = other if isinstance(other,Poly) else Poly(other)
        result=self.terms.copy()
        for k,v in other.terms.items():result[k]=result.get(k,0)+v
        return Poly(result)
    __radd__=__add__
    def __neg__(self):return Poly({k:-v for k,v in self.terms.items()})
    def __sub__(self,other):return self+-other
    def __rsub__(self,other):return -self+other
    def __mul__(self,other):
        if isinstance(other,np.ndarray):return NotImplemented
        other=other if isinstance(other,Poly) else Poly(other)
        result={}
        for a,av in self.terms.items():
            for b,bv in other.terms.items():
                k=tuple(x+y for x,y in zip(a,b));result[k]=result.get(k,0)+av*bv
        return Poly(result)
    __rmul__=__mul__
    def __truediv__(self,other):return self*F(1,other)
    def __pow__(self,k):
        result=Poly(1)
        for _ in range(k):result=result*self
        return result

def variable(i):return Poly({tuple(int(j==i) for j in range(8)):1})
x,y,z=[variable(i) for i in range(3)]
nv=np.array([x,y,z],dtype=object)
eye=np.eye(3,dtype=int).astype(object)
screen=eye-np.outer(nv,nv)
def double_factorial(k):return prod(range(k,0,-2))

def sphere_average(expr):
    result = 0
    expr=expr if isinstance(expr,Poly) else Poly(expr)
    for powers, coefficient in expr.terms.items():
        if any(k % 2 for k in powers):
            continue
        result += coefficient * F(prod(double_factorial(k-1) for k in powers),double_factorial(sum(powers)+1))
    return result
average_matrix=np.vectorize(sphere_average,otypes=[object])
def exact_rank(array):
    a=[[F(v) for v in row] for row in array.tolist()];r=0
    for c in range(len(a[0])):
        piv=next((i for i in range(r,len(a)) if a[i][c]),None)
        if piv is None:continue
        a[r],a[piv]=a[piv],a[r];value=a[r][c];a[r]=[v/value for v in a[r]]
        for i in range(r+1,len(a)):
            if a[i][c]:
                value=a[i][c];a[i]=[v-value*w for v,w in zip(a[i],a[r])]
        r+=1
        if r==len(a):break
    return r

stf = [np.diag([1,-1,0]).astype(object), np.diag([1,1,-2]).astype(object)]
for i,j in [(0,1),(0,2),(1,2)]:
    a = np.zeros((3,3),dtype=object); a[i,j] = a[j,i] = 1; stf.append(a)

def matrix_coordinates(m):
    return list(m.diagonal()) + [m[0,1],m[0,2],m[1,2]] + [0,0,0]

energy = []
for i in range(5):
    for j in range(i,5):
        energy.append(nv@(stf[i]@stf[j]+stf[j]@stf[i])@nv
                      -(nv@stf[i]@nv)*(nv@stf[j]@nv))

# Homogeneous quartics span all intensity l=0,2,4 on the sphere: 15 dims.
columns = []
for a in range(5):
    for b in range(5-a):
        f = x**a*y**b*z**(4-a-b)
        m = average_matrix(screen*f/2)
        columns.append(matrix_coordinates(m)+[sphere_average(f*q) for q in energy])
for s in stf:
    f = screen@s@screen-screen*np.trace(screen@s@screen)/2
    m = average_matrix(f)
    columns.append(matrix_coordinates(m)+[0]*15)
# i epsilon_ijk n_k (n.v) is a screen-supported circular perturbation.
for k in range(3):
    cross = np.array([[0,-z,y],[z,0,-x],[-y,x,0]],dtype=object)*nv[k]
    m = average_matrix(cross)
    columns.append([0]*6+[m[0,1],m[0,2],m[1,2]]+[0]*15)
carrier = np.array(columns,dtype=object).T
assert exact_rank(carrier) == 23
assert exact_rank(carrier[9:,:15]) == 15
assert exact_rank(carrier[:9,:]) == 9

# Gain spectrum from exact normalized angular integration.
hermitian_basis = [np.diag(v).astype(object) for v in np.eye(3,dtype=int)] + stf[2:]
gain_errors = []
for m in hermitian_basis:
    actual = average_matrix(F(3,2)*(screen@m@screen))
    expected = F(3,5)*m+F(1,10)*m.T+F(np.trace(m),10)*eye
    gain_errors.append(bool(np.all(actual == expected)))
assert all(gain_errors)

# Exact l=4 response difference in an orthonormal STF basis; 4*pi integral.
norms = [np.sqrt(float(np.trace(a@a))) for a in stf]
p4 = (35*z**4-30*z**2+3)/8
delta = np.zeros((5,5))
for i in range(5):
    for j in range(5):
        q = nv@(stf[i]@stf[j]+stf[j]@stf[i])@nv-(nv@stf[i]@nv)*(nv@stf[j]@nv)
        delta[i,j] = 4*np.pi*float(F(6,5)*sphere_average(p4*q))/(norms[i]*norms[j])
delta_eigen = np.linalg.eigvalsh(delta).tolist()
delta_norm = max(map(abs,delta_eigen))

# The ideal spatial maps' ranks precede all internal detector bookkeeping.
directions = np.array([[1,0,0],[0,1,0],[0,0,1],[1,1,0],[1,0,1],[0,1,1],[1,1,1]],float)
directions /= np.linalg.norm(directions,axis=1)[:,None]
radial = np.array([np.outer(n,n).ravel() for n in directions])
tangent = np.vstack([np.vstack([np.outer(v,n).ravel() for v in np.eye(3)-np.outer(n,n)]) for n in directions])
spatial_ranks = [int(np.linalg.matrix_rank(radial)),int(np.linalg.matrix_rank(tangent)),int(np.linalg.matrix_rank(np.vstack([radial,tangent])))]
assert spatial_ranks == [6,8,9]

# Internal phase transport preserves a helicity analyzer; SU(2) conversion can mix.
sig = np.array([[[0,1],[1,0]],[[0,-1j],[1j,0]],[[1,0],[0,-1]]],complex)
phase_axes=[];conversion_axes=[]
for angle in [.0,.3,.7,1.1]:
    phase=expm(1j*angle*sig[2]);convert=expm(1j*angle*sig[1])
    for collection,u in [(phase_axes,phase),(conversion_axes,convert)]:
        v=u.conj().T@sig[2]@u
        collection.append([np.trace(s@v).real/2 for s in sig])
phase_rank=int(np.linalg.matrix_rank(phase_axes,tol=1e-12))
conversion_rank=int(np.linalg.matrix_rank(conversion_axes,tol=1e-12))
assert phase_rank == 1 and conversion_rank == 2

# New goal3 fixed-Q sign radius, checked by attaining all three hyperplanes.
qmat=np.diag([-1/np.sqrt(2),0,1/np.sqrt(2)])
def qlift(v):
    result=np.zeros((3,3,3));qv=qmat@v
    for i in range(3):
        for j in range(3):
            for k in range(3):
                result[i,j,k]=(qmat[i,j]*v[k]+qmat[i,k]*v[j]+qmat[j,k]*v[i])/3
                result[i,j,k]-=2*((i==j)*qv[k]+(i==k)*qv[j]+(j==k)*qv[i])/15
    return result
octupole=qlift(np.array([np.sqrt(10)/4,1,np.sqrt(10)/4]))
v0=np.einsum('ijk,jk->i',octupole,qmat)
metric_q=np.eye(3)/3+2*qmat@qmat/5
radius=np.abs(v0)/np.sqrt(np.diag(metric_q));chir_res=[];radius_res=[]
for i in range(3):
    correction=-v0[i]/metric_q[i,i]*qlift(np.eye(3)[i])
    vend=np.einsum('ijk,jk->i',octupole+correction,qmat)
    chir_res.append(abs(np.linalg.det(np.column_stack([vend,qmat@vend,qmat@qmat@vend]))))
    radius_res.append(abs(np.linalg.norm(correction)-radius[i]))
assert max(chir_res)<1e-15 and max(radius_res)<1e-15

# Matrix CBL decomposition checked with arbitrary independent Hermitian jets.
# d>0 and W>0 are local jets, not fitted transfer or geometry.
jordan=lambda a,b:(a@b+b@a)/2
residuals=[]
for _ in range(50):
    raw=rng.normal(size=(3,3))+1j*rng.normal(size=(3,3))
    w=raw@raw.conj().T+np.eye(3)
    jet=[]
    for k in range(2):
        raw=rng.normal(size=(3,3))+1j*rng.normal(size=(3,3));jet.append((raw+raw.conj().T)/2)
    w1,w2=jet;d,dp,dpp,h,hp=rng.uniform(.1,1.1,size=5)
    dm=d*w;dm1=dp*w+d*w1;dm2=dpp*w+2*dp*w1+d*w2
    scalar=1+h*h*(d*dpp-dp*dp)+h*hp*d*dp
    left=np.eye(3)+h*h*(jordan(dm,dm2)-dm1@dm1)+h*hp*jordan(dm,dm1)
    right=np.eye(3)+(scalar-1)*w@w+d*d*(h*h*(jordan(w,w2)-w1@w1)+h*hp*jordan(w,w1))
    residuals.append(float(np.linalg.norm(left-right)/max(1,np.linalg.norm(left),np.linalg.norm(right))))
assert max(residuals)<1e-12

# Exact symbolic scalar opacity relation, treating derivatives as independent jets.
d,d1,d2,t1,t2,h,h1=[variable(i) for i in range(7)]
# Cancel the common positive exp(t)/c^2 factor first.
dr1=d1+d*t1/2;dr2=d2+d1*t1+d*t2/2+d*t1*t1/4
opacity_residual=h*h*(d*dr2-dr1*dr1)+h*h1*d*dr1-(h*h*(d*d2-d1*d1)+h*h1*d*d1)-d*d*(h*h*t2+h*h1*t1)/2
assert not opacity_residual.terms

# Choi rank1 does not give a unitary channel without TP (square equal dims).
k=np.diag([.5,.25]);vec=k.ravel(order='F');choi=np.outer(vec,vec)
filter_rank=int(np.linalg.matrix_rank(choi));tp_residual=float(np.linalg.norm(k.T@k-np.eye(2)))
assert filter_rank == 1 and tp_residual > .1

# Joint-error support and exact worst-bias Gaussian radius, independent fixture.
n,p,q,kdim=11,4,2,3
raw=rng.normal(size=(n,n));cov=raw@raw.T+np.eye(n)
vals,vecs=np.linalg.eigh(cov);white=(vecs/np.sqrt(vals))@vecs.T
j=rng.normal(size=(n,p));nu=rng.normal(size=(n,q));b=rng.normal(size=(n,kdim))
qw=np.linalg.qr(white@nu,mode='reduced')[0];m=np.eye(n)-qw@qw.T;a=m@white@j
info=a.T@a;vals,vecs=np.linalg.eigh(info);iroot=(vecs/np.sqrt(vals))@vecs.T
metric=np.diag([.7,2.,5.]);error_map=iroot@a.T@m@white@b@np.diag(1/np.sqrt(np.diag(metric)))
u,s,vh=np.linalg.svd(error_map,full_matrices=False)
attainment=abs(float(np.linalg.norm(error_map@vh[0]))-float(s[0]))
coverage=[]
for bound in [0,.5,1,2,4]:
    critical=float(ncx2.ppf(.95,p,bound*bound))
    probs=[float(ncx2.cdf(critical,p,actual*actual)) for actual in np.linspace(0,bound,21)]
    coverage.append({'bias_bound':bound,'minimum_exact_coverage':min(probs),'critical_radius':np.sqrt(critical)})
assert min(a['minimum_exact_coverage'] for a in coverage)>.95-1e-13

out={'schema':'htt.independent_review_checks/1','seed':109282026,'production_scripts_imported':False,
     'exact_carrier':{'shape':list(carrier.shape),'joint_rank':exact_rank(carrier),'intensity_shear_rank':exact_rank(carrier[9:,:15]),'gain_rank':exact_rank(carrier[:9,:]),'linear_only_joint_rank':exact_rank(carrier[:,:20]),'gain_symmetric_identity_exact':all(gain_errors)},
     'positive_sky_delta_L':{'eigenvalues_from_exact_angular_moments':delta_eigen,'operator_norm':delta_norm,'production_difference':abs(delta_norm-.5744626566564465)},
     'kinematic_spatial_ranks_H_Q_both':spatial_ranks,'path_analyzer_ranks':{'helicity_phase_only':phase_rank,'calibrated_SU2_conversion':conversion_rank},
     'fixed_Q_chirality_radius':{'radius':float(min(radius)),'predicted_sharp_radius':float(1/np.sqrt(3)),'attaining_zero_chirality_max_residual':max(chir_res),'distance_attainment_max_error':max(radius_res)},
     'matrix_CBL_max_relative_residual':max(residuals),'scalar_opacity_identity_exact':not opacity_residual.terms,
     'nonunitary_rank1_filter':{'Choi_rank':filter_rank,'TP_Frobenius_residual':tp_residual},
     'joint_bias_bound_attainment_error':attainment,'noncentral_ball_exact_coverage':coverage,
     'source_provenance_correction':'Rendered MF02 p17 Eq1.6.8 is multiplicative f0(E)[I+epsilon(n.e)sigma3]. Additive text in extraction/pasted proposal must not be attributed to original PDF.',
     'execution_repair':{'initial':'Default Python failed: no sympy','diagnostic_retry':'Primary Python also lacks sympy','substantive_repair':'Replaced SymPy with local exact Fraction polynomial arithmetic and Gaussian elimination; no installation needed'},
     'scope':'Selected independent exact algebra and finite numerical checks; no observational test, ODE, promotion or push.'}
(ROOT/'lanes/INDEPENDENT_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
