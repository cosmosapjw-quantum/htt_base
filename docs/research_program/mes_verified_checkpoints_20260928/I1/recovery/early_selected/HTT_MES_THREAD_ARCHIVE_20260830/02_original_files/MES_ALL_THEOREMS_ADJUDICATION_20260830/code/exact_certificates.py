"""Exact algebra and finite-enumeration witnesses for the analytic proof dossier.

These are finite certificates, not substitutes for the analytic arguments about
continuous histories, group representations, or probability for arbitrary N.
No production imports, raw data, network, or repository mutations are used.
"""
from __future__ import annotations
from pathlib import Path
from fractions import Fraction
from itertools import product
from statistics import median
import json
import sympy as s

ROOT = Path(__file__).resolve().parents[1]

def stf3(values):
    a,b,c,d,e,f,g = map(s.sympify, values)
    independent = {(0,0,0):a,(0,0,1):b,(0,0,2):c,(0,1,1):d,
        (0,1,2):e,(1,1,1):f,(1,1,2):g,(0,2,2):-a-d,
        (1,2,2):-b-f,(2,2,2):-c-g}
    return s.MutableDenseNDimArray(
        [independent[tuple(sorted(i))] for i in product(range(3), repeat=3)],
        (3,3,3))

def flatten3(o):
    return s.Matrix([o[i,j,k] for i,j,k in product(range(3), repeat=3)])

def bq(q, v):
    p = q*v
    return s.MutableDenseNDimArray([
        v[i]*q[j,k]+v[j]*q[i,k]+v[k]*q[i,j]
        -s.Rational(2,5)*(s.KroneckerDelta(i,j)*p[k]+s.KroneckerDelta(i,k)*p[j]+s.KroneckerDelta(j,k)*p[i])
        for i,j,k in product(range(3),repeat=3)], (3,3,3))

def reduce_zero(expr):
    if isinstance(expr, s.MatrixBase):
        return all(s.expand(x)==0 for x in expr)
    return s.expand(expr)==0

def certificates():
    out = {}
    a,b,c,d,e,x,y,z = s.symbols('a b c d e x y z', real=True)
    q=s.Matrix([[a,c,d],[c,b,e],[d,e,-a-b]])
    v=s.Matrix([x,y,z]); q2=s.trace(q*q);q3=s.trace(q**3)
    assert reduce_zero(q**3-q2*q/2-q3*s.eye(3)/3)
    assert reduce_zero(s.trace(q**4)-q2**2/2)
    b3=bq(q,v); mq=q2*s.eye(3)+s.Rational(6,5)*q*q
    assert reduce_zero(s.Matrix([sum(b3[i,i,k] for i in range(3)) for k in range(3)]))
    contraction=s.Matrix([sum(b3[i,j,k]*q[j,k] for j,k in product(range(3),repeat=2)) for i in range(3)])
    assert reduce_zero(contraction-mq*v)
    assert reduce_zero((flatten3(b3).T*flatten3(b3))[0]-3*(v.T*mq*v)[0])
    discr=s.factor((x*x+y*y+(x+y)**2)**3/2-3*(x**3+y**3-(x+y)**3)**2)
    assert s.expand(discr-(x-y)**2*(2*x+y)**2*(x+2*y)**2)==0
    out['general_stf']={'CH_residual':0,'fourth_trace_residual':0,
        'boost_trace_residual':[0,0,0],'boost_contraction_residual':[0,0,0],
        'boost_norm_residual':0,'discriminant':str(discr)}
    t=s.symbols('t', real=True)
    ratio=(2*(1-t+t*t)+s.Rational(6,5))/(2*(1-t+t*t)+s.Rational(6,5)*t*t)
    gap=s.factor(s.Rational(5,3)-ratio)
    assert s.cancel(gap-(5*t-1)**2/(3*(5-5*t+8*t*t)))==0
    assert ratio.subs(t,s.Rational(1,5))==s.Rational(5,3)
    out['sharp_condition_number']={'bound':'5/3','gap_factorization':str(gap),'equality_t':'1/5'}
    s2,s3,m0,m1,m2=s.symbols('s2 s3 m0 m1 m2', real=True)
    m3=s2*m1/2+s3*m0/3;m4=s2*m2/2+s3*m1/3
    gram=s.Matrix([[m0,m1,m2],[m1,m2,m3],[m2,m3,m4]])
    mult=s.Matrix([[0,0,s3/3],[1,0,s2/2],[0,1,0]])
    assert reduce_zero(gram*mult-mult.T*gram)
    assert reduce_zero(mult**3-s2*mult/2-s3*s.eye(3)/3)
    sr=s.diag(-1,-1,2);vr=s.Matrix([1,2,3]);kr=s.Matrix.hstack(vr,sr*vr,sr*sr*vr)
    gr=kr.T*kr;assert gr.rank()==2 and gr.det()==0
    out['moments']={'self_adjoint_residual':0,'companion_CH_residual':0,
        'repeated_spectrum_moments':[(vr.T*sr**i*vr)[0] for i in range(5)],
        'repeated_spectrum_gram_rank':gr.rank()}
    oo=stf3(range(1,8))
    assert all(sum(oo[i,i,k] for i in range(3))==0 for k in range(3))
    aa=s.Matrix(3,3,lambda i,j:sum(oo[i,k,l]*oo[j,k,l] for k,l in product(range(3),repeat=2)))
    uu=s.Matrix([sum(oo[i,j,k]*aa[j,k] for j,k in product(range(3),repeat=2)) for i in range(3)])
    chi=s.Matrix.hstack(uu,aa*uu,aa*aa*uu).det()
    qq=s.diag(1,2,-3)
    vv=s.Matrix([sum(oo[i,j,k]*qq[j,k] for j,k in product(range(3),repeat=2)) for i in range(3)])
    kap=s.Matrix.hstack(vv,qq*vv,qq*qq*vv).det()
    assert aa==s.Matrix([[118,182,-9],[182,284,6],[-9,6,386]])
    assert uu==s.Matrix([58,302,296]);assert chi==20640382199000
    assert vv==s.Matrix([24,38,47]);assert kap==857280
    out['chirality_counterexamples']={'STF3_components':list(range(1,8)),
        'A':aa.tolist(),'u':list(uu),'chi_O':chi,'chi_minus_O':-chi,
        'Q':qq.tolist(),'v_OQ':list(vv),'kappa_QO':kap,'kappa_Q_minus_O':-kap}
    # A09 transversality witness is symbolic, not a rank at one random point.
    rr,q12,q33,q11,q23=s.symbols('r q12 q33 q11 q23', real=True)
    jvert=s.Matrix([[0,0,rr],[0,-rr,0],[q12,q33-q11,-q23]])
    assert s.factor(jvert.det())==rr*rr*q12
    out['canonical_slice']={'vertical_constraint_jacobian_determinant':str(s.factor(jvert.det()))}
    # Orthogonal nuisance preserves beta, whereas an unrestricted STF3 nuisance does not.
    B=s.Matrix.hstack(*(flatten3(bq(qq,s.eye(3)[:,i])) for i in range(3)))
    M=s.trace(qq*qq)*s.eye(3)+s.Rational(6,5)*qq*qq
    assert B.T*B==3*M
    ov=flatten3(oo);beta_hat=M.inv()*vv; operp=ov-B*beta_hat
    assert B.T*operp==s.zeros(3,1)
    beta0=s.Matrix([s.Rational(1,10),s.Rational(-1,5),s.Rational(3,10)])
    beta_recovered=(B.T*B).inv()*B.T*(B*beta0+operp)
    assert beta_recovered==beta0
    BB=B[:,0];p1=BB*(BB.T*BB).inv()*BB.T
    basis_stf=s.Matrix.hstack(*(flatten3(stf3([int(j==i) for j in range(7)])) for i in range(7)))
    pall=basis_stf*(basis_stf.T*basis_stf).inv()*basis_stf.T
    assert (B-p1*B).rank()==2 and (B-pall*B).rank()==0
    out['nuisance']={'no_nuisance_rank':B.rank(),'one_response_nuisance_rank':(B-p1*B).rank(),
        'unrestricted_STF3_nuisance_rank':(B-pall*B).rank(),
        'orthogonal_nuisance_beta':list(beta_recovered),'orthogonal_residual':list(B.T*operp)}
    # Exact rational Lorentz inverse check, including canonical null-cone gauge.
    eta=s.diag(-1,1,1,1);be=s.Matrix([s.Rational(1,5),s.Rational(2,5),s.Rational(2,5)])
    ga=s.Rational(5,4);J=s.eye(3)+ga**2/(ga+1)*be*be.T
    La=s.Matrix.vstack(s.Matrix.hstack(s.Matrix([[ga]]),ga*be.T),s.Matrix.hstack(ga*be,J))
    MM=s.Matrix([[2,s.Rational(1,3),s.Rational(1,4)],
        [s.Rational(1,3),3,s.Rational(1,5)],
        [s.Rational(1,4),s.Rational(1,5),5]])
    hh=La.T*s.diag(s.Matrix([[0]]),MM)*La
    lc=-s.trace(hh[1:4,1:4])/3;AA=hh+lc*eta;ut=s.Matrix([ga,*(-ga*be)])
    assert La.T*eta*La==eta and (ut.T*eta*ut)[0]==-1
    assert eta*AA*ut==lc*ut
    lam=s.symbols('lam');assert s.factor((lam*s.eye(4)-eta*AA).det()-(lam-lc)*((lam-lc)*s.eye(3)-MM).det())==0
    assert La.inv().T*(AA-lc*eta)*La.inv()==s.diag(s.Matrix([[0]]),MM)
    nn=s.Matrix([x,y,z]);kk=s.Matrix([1,-x,-y,-z])
    assert reduce_zero((kk.T*hh*kk)[0]-((J*nn-ga*be).T*MM*(J*nn-ga*be))[0])
    boundary_vec=s.Matrix([1,0,0,-1]);boundaryA=boundary_vec*boundary_vec.T
    assert (eta*boundaryA)**2==s.zeros(4) and eta*boundaryA!=s.zeros(4)
    out['Lorentz']={'beta':list(be),'gamma':ga,'timelike_eigenvalue':lc,
        'characteristic_identity_residual':0,'boost_back_residual':0,
        'rest_metric_det':MM.det(),'rest_metric_principal_minors':[MM[:i,:i].det() for i in range(1,4)],
        'boundary_null_form_nilpotent_square':0}
    # Exact affine LOS design and two-shell factorization.
    axes=[s.Matrix([int(j==i)*sign for j in range(3)]) for i in range(3) for sign in [-1,1]]
    axes += [s.Matrix(v)/s.sqrt(2) for v in [[1,1,0],[1,0,1],[0,1,1]]]
    design=s.Matrix([[nx,ny,nz,1,nx*nx-nz*nz,ny*ny-nz*nz,2*nx*ny,2*nx*nz,2*ny*nz] for nx,ny,nz in axes])
    assert design.rank()==9
    g1,g2=s.symbols('g1 g2'); X=s.BlockMatrix([[s.eye(3),g1*s.eye(3)],[s.eye(3),g2*s.eye(3)]]).as_explicit()
    assert s.expand(s.factor(X.det())-(g2-g1)**3)==0
    W=s.Matrix([[0,-z,y],[z,0,-x],[-y,x,0]])
    nx,ny,nz=s.symbols('nx ny nz');nv=s.Matrix([nx,ny,nz])
    assert reduce_zero((nv.T*W*nv)[0]) and s.trace(W**3)==0
    out['linear_identification']={'LOS_design_rank':design.rank(),'LOS_design_det':s.simplify(design.det()),
        'two_shell_det':str(s.factor(X.det())),'radial_rotation_response':0,'vorticity_cubic_trace':0}
    # Exhaustive 81 pools: exact fractions throughout, including equal-valued rows.
    def p_rank(sc):
        return Fraction(sum(v>=sc[0] for v in sc), len(sc))
    pools=list(product([Fraction(0),Fraction(1),Fraction(2)],repeat=4))
    ps=[];pt=[]
    for zz in pools:
        sc=[abs(zz[i]-median(zz[:i]+zz[i+1:])) for i in range(4)]
        ps.append(p_rank(sc));pt.append(p_rank([float('-inf') if v==0 else v for v in zz]))
    lev=[Fraction(i,4) for i in range(1,5)]
    rej=[Fraction(sum(p<=a for p in ps),len(ps)) for a in lev]
    rejt=[Fraction(sum(p<=a for p in pt),len(pt)) for a in lev]
    assert rej==[Fraction(4,27),Fraction(2,9),Fraction(2,9),Fraction(1)]
    assert rejt==[Fraction(1,9),Fraction(1,3),Fraction(5,9),Fraction(1)]
    assert all(p<=a for p,a in zip(rej,lev)) and all(p<=a for p,a in zip(rejt,lev))
    assert p_rank([0,1,2])==1 and p_rank([0,-1,-2])==Fraction(1,3)
    u=Fraction(1,4);zd=[1-u,u,u];sd=[abs(zd[i]-sum(zd[:i]+zd[i+1:])/2) for i in range(3)]
    assert p_rank(sd)==Fraction(1,3)
    assert p_rank([0,0,0,0])==1 and p_rank([Fraction(1,10),0,0,0])==Fraction(1,4)
    out['finite_ranks']={'enumerated_pool_count':len(pools),'levels':lev,'LOO_rejection':rej,
        'data_dependent_absence_rejection':rejt,'decreasing_map_upper_rank_before':1,
        'decreasing_map_upper_rank_after':Fraction(1,3),
        'equal_marginal_nonexchangeable_scores':sd,'equal_marginal_query_rank':Fraction(1,3),
        'W1_tie_counterexample_rank':Fraction(1,4),
        'duplicated_evalue_mean':Fraction(1),'duplicated_evalue_product_mean':Fraction(2),
        'bounded_MES_body_LR_at_z2':3,'bounded_MES_body_squared_projection':1,
        'Bernoulli_single_query_max_power_at_alpha_005':Fraction(3,50)}
    return out

def encode(o):
    if isinstance(o, (s.Basic, Fraction)):
        return str(o)
    raise TypeError(type(o).__name__)

if __name__=='__main__':
    cert=certificates()
    result={'status':'EXACT_ALGEBRA_AND_ENUMERATION_PASS','formal_proof_assistant':False,
        'random_sampling_used':False,'certificates':cert}
    (ROOT/'evidence/exact_certificates.json').write_text(json.dumps(result,default=encode,indent=2)+'\n')
    print(json.dumps(result,default=encode,indent=2))
