"""Finite archived source-law quotient certificate; no pair traversal or refit.

All input binary64 values are exact dyadics. Dense contractions are enclosed by
componentwise forward error, including input interval radii. Each ordinary
binary64 dot of length n is bounded by gamma_(2n) times its absolute sum,
assuming IEEE round-to-nearest, gradual underflow, and no nonnormal products.
No small residual is used as a proof. All reported bounds are inflated beyond
rounding in their own nonnegative bound arithmetic. The exact algebraic quotient
is applied through rank-three factors; it is never materialized.
"""
from __future__ import annotations
import hashlib, json, math, os, platform, sys, time
from fractions import Fraction
from pathlib import Path
import numpy as np

ROOT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_certificate')
INPUT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_quotient_proposal/INPUT.json')
ARRAY=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/packaged/arrays.npz')
PACKET='b20cec4107786152ef8e4ffbb0097ec83dd4f2a77a31c32c6935fcaf2adf62ff'
EXPECT_INPUT='4df217b0798bbb247523dae173fc4026b966a6208496929477085305a44653ba'
EXPECT_ARRAY='d391a5c49b9205229717d1bc9c900e180be4bea8440023bb52b2517352e8ffe5'
U=2.0**-53
FUDGE=1.0+1.0e-8
MAX_DOT=9512
EXP_TERMS_10=128
EXP_TERMS_88=256
QUANTILE_Q=120
LOW_NORMAL=sys.float_info.min
stages=[]

def record(name, status, **kw):
    stages.append(dict(name=name,status=status,**kw))

def ensure(c, name, **kw):
    record(name, 'PASS' if c else 'HOLD', **kw)
    if not c: raise RuntimeError(name)

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def inflate(x):
    y=np.asarray(x,dtype=np.float64)*FUDGE
    # Exact zeros need no upward step. A step from zero would create an
    # artificial subnormal radius and violate our normal-product premise.
    return np.where(y==0.0,y,np.nextafter(y,np.inf))

def gdot(k):
    z=2*k*U
    assert z<1e-8
    return z/(1-z)

def check_normal_products(*aa):
    """Conservative global test: every nonzero operand >1e-150,
    so any product used by the bounded binary64 kernels is normal."""
    mm=[]
    for a in aa:
        a=np.asarray(a)
        if not np.all(np.isfinite(a)): raise RuntimeError('NONFINITE_OPERAND')
        v=np.abs(a[a!=0])
        if v.size: mm.append(float(v.min()))
    m=min(mm,default=1.0)
    ensure(m>1e-150,'NORMAL_PRODUCT_PREMISE',minimum_nonzero_operand=m,threshold=1e-150)
    return m

class Ball:
    def __init__(self,c,r=0):
        self.c=np.asarray(c,dtype=np.float64)
        self.r=np.broadcast_to(np.asarray(r,dtype=np.float64),self.c.shape).copy()
        assert self.c.ndim==2 and self.c.shape==self.r.shape
        if not np.all(np.isfinite(self.c)) or not np.all(np.isfinite(self.r)) or np.any(self.r<0):
            raise RuntimeError('NONFINITE_INTERVAL')
    @property
    def T(self): return Ball(self.c.T,self.r.T)
    def __add__(self,b):
        c=self.c+b.c
        r=inflate(self.r+b.r+U*(np.abs(self.c)+np.abs(b.c)))
        return Ball(c,r)
    def __sub__(self,b):
        c=self.c-b.c
        r=inflate(self.r+b.r+U*(np.abs(self.c)+np.abs(b.c)))
        return Ball(c,r)
    def __matmul__(self,b):
        k=self.c.shape[1]
        assert k==b.c.shape[0]
        check_normal_products(self.c,self.r,b.c,b.r)
        g=gdot(k)
        c=self.c@b.c
        s=np.abs(self.c)@np.abs(b.c)
        # s/(1-g) dominates the exact sum of absolute exact center products.
        base=g*s/(1-g)
        r=inflate(base+(np.abs(self.c)@b.r)+(self.r@np.abs(b.c))+(self.r@b.r))
        out=Ball(c,r)
        check_normal_products(out.c,out.r)
        return out
    def abs_upper(self): return inflate(np.abs(self.c)+self.r)
    def maxabs_upper(self): return float(inflate(np.max(self.abs_upper())))

def bm(x): return Ball(x,0)

def bound_inf(a):
    return float(inflate(np.max(np.sum(a.abs_upper(),axis=1))))

def inverse_cert(a,name):
    assert a.c.shape[0]==a.c.shape[1]
    n=a.c.shape[0]
    r0=np.linalg.inv(a.c)
    err=bm(np.eye(n))-(a@bm(r0))
    e=bound_inf(err)
    ensure(e<1.0,name+'_NEUMANN',residual_infinity_upper=e)
    rnorm=float(inflate(np.max(np.sum(np.abs(r0),axis=1))))
    rrad=float(inflate((rnorm*e)/(1-e)))
    return Ball(r0,rrad),dict(residual_infinity_upper=e,inverse_entry_radius=rrad)

def scalar(a):
    assert a.c.shape==(1,1)
    return [float(np.nextafter(a.c[0,0]-a.r[0,0],-np.inf)),
            float(np.nextafter(a.c[0,0]+a.r[0,0],np.inf))]

def interval_stat(z,A,R):
    b=A.T@z
    zz=z.T@z
    return zz-(b.T@R@b)

def sf_even_upper(t,df,N):
    # All Fraction operations are exact on endpoints, with exact dyadic input.
    assert t>=0 and df%2==0
    x=t/2
    poly=Fraction(0); term=Fraction(1)
    for j in range(df//2):
        if j: term=term*x/j
        poly+=term
    sn=Fraction(0); term=Fraction(1)
    for j in range(N+1):
        if j: term=term*x/j
        sn+=term
    assert N+2>x
    rem=(term*x/(N+1))/(1-x/Fraction(N+2))
    # exp(x) >= sn, hence exp(-x)*poly <= poly/sn.
    return min(Fraction(1),poly/sn),dict(exp_lower_terms=N,exp_upper_remainder_decimal=float(rem),x_decimal=float(x))

def upward_decimal(q,places=14):
    a=q*10**places
    v=(a.numerator+a.denominator-1)//a.denominator
    return f'{v//10**places}.{v%10**places:0{places}d}'

def source_covariance(F,C):
    n=C.shape[0]
    rows=F.c.shape[0]
    fc=F.c.reshape(rows,n,2); fr=F.r.reshape(rows,n,2)
    check_normal_products(fc,fr,C)
    # Direct two-term block contractions. Both off-diagonal orientations are
    # retained, and the full resulting 88x88 cross-bin covariance is computed.
    cc=np.einsum('ask,skj->asj',fc,C,optimize=False)
    ss=np.einsum('ask,skj->asj',np.abs(fc),np.abs(C),optimize=False)
    rr=np.einsum('ask,skj->asj',fr,np.abs(C),optimize=False)
    rr=inflate(rr+gdot(2)*ss/(1-gdot(2)))
    FC=Ball(cc.reshape(rows,2*n),rr.reshape(rows,2*n))
    return FC@F.T

def summarize(m):
    return {'shape':list(m.c.shape),'center_max_abs':float(np.max(np.abs(m.c))),
            'entry_radius_max':float(np.max(m.r))}

def main():
    t0=time.monotonic()
    ensure(digest(INPUT)==EXPECT_INPUT,'FROZEN_INPUT_SHA')
    ensure(digest(ARRAY)==EXPECT_ARRAY,'ARCHIVE_ARRAY_SHA')
    a=np.load(ARRAY,allow_pickle=False)
    required=['H','X','B','y','C','W','D','d','Cd']
    ensure(all(k in a.files for k in required),'ARCHIVE_KEYS',keys=required)
    H=np.asarray(a['H'],dtype=np.float64).reshape(117,9512)
    X=np.asarray(a['X'],dtype=np.float64).reshape(9512,13)
    B=np.asarray(a['B'],dtype=np.float64).reshape(9512,3)
    y=np.asarray(a['y'],dtype=np.float64).reshape(9512,1)
    C=np.asarray(a['C'],dtype=np.float64).reshape(4756,2,2)
    W=np.asarray(a['W'],dtype=np.float64).reshape(88,117)
    D=np.asarray(a['D'],dtype=np.float64).reshape(117,13)
    d=np.asarray(a['d'],dtype=np.float64).reshape(117,1)
    Cd=np.asarray(a['Cd'],dtype=np.float64).reshape(117,117)
    check_normal_products(H,X,B,y,C,W,D,d,Cd)
    ensure(np.array_equal(C[:,0,1],C[:,1,0]),'SOURCE_BLOCK_EXACT_SYMMETRY')
    min_det=None
    for c in C:
        aa,bb,cc=(Fraction.from_float(float(c[0,0])),Fraction.from_float(float(c[0,1])),Fraction.from_float(float(c[1,1])))
        det=aa*cc-bb*bb
        if not (aa>0 and det>0):
            ensure(False,'SOURCE_BLOCK_SPD',failed_block_index=int(len(stages)),a=str(aa),det=str(det))
        if min_det is None or det<min_det: min_det=det
    record('SOURCE_BLOCK_SPD','PASS',block_count=4756,
           min_determinant_exact=str(min_det))
    G=bm(B).T@bm(B)
    R,rg=inverse_cert(G,'SPIN_GRAM')
    record('SPIN_GRAM_SPD','PASS',**rg,exact_reason='B^T B is positive semidefinite and proved invertible')
    F=bm(W)@bm(H)
    J=F@bm(B)
    Fstar=F-(J@R@bm(B).T)
    A=Fstar@bm(X)
    z=Fstar@bm(y)
    S=source_covariance(Fstar,C)
    # Exact S is symmetric from the certified exact source blocks. The
    # interval row sum encloses every entry of S-I; no symmetrization is used.
    E=S-bm(np.eye(88))
    delta=bound_inf(E)
    ensure(delta<1.0,'SOURCE_COVARIANCE_SPECTRAL_INFLATION',delta_upper=delta,
           reason='symmetric S-I has spectral norm at most max absolute row sum')
    G1=A.T@A; G0=Ball(A.c[:,:3],A.r[:,:3]).T@Ball(A.c[:,:3],A.r[:,:3])
    R1,r1=inverse_cert(G1,'FULL13_GRAM')
    R0,r0=inverse_cert(G0,'E1_GRAM')
    record('COMPLETE_IMAGES','PASS',q_full=13,q_E1=3,k=10,
           argument='Exact Gram matrices are PSD and independently proved invertible',full13=r1,E1=r0)
    A0=Ball(A.c[:,:3],A.r[:,:3])
    T1=interval_stat(z,A,R1)
    T0=interval_stat(z,A0,R0)
    Delta=T0-T1
    t1=scalar(T1); t0i=scalar(T0); dl=scalar(Delta)
    ensure(t1[0]>=0 and t0i[0]>=0 and dl[0]>=0,'NONNEGATIVE_STATISTIC_ENCLOSURES',
           T_full=t1,T_E1=t0i,Delta=dl)
    a_lower=Fraction.from_float(dl[0])/(Fraction(1)+Fraction.from_float(delta))
    p,pmeta=sf_even_upper(a_lower,10,EXP_TERMS_10)
    pq,pqmeta=sf_even_upper(Fraction(QUANTILE_Q),88,EXP_TERMS_88)
    ensure(pq<=Fraction(1,20),'MEAN_BALL_QUANTILE',q_upper=QUANTILE_Q,
           sf88_upper=upward_decimal(pq),**pqmeta)
    eta=float(inflate(np.linalg.norm(z.r[:,0])))
    # sqrt is correctly rounded under the stated IEEE premise; two nextafter
    # steps and FUDGE cover the displayed radius arithmetic.
    rad=float(inflate(math.sqrt(float(inflate((1+delta)*QUANTILE_Q)))+eta))
    record('DELTA_CONDITIONAL_TAIL','PASS',p_upper=upward_decimal(p),argument_lower_decimal=float(a_lower),
           null='matching exact E1 finite Gaussian/C0 source law',**pmeta)
    record('ARBITRARY_MEAN_BALL','PASS',q_upper=QUANTILE_Q,center_error_norm_upper=eta,
           displayed_radius_upper=rad,coverage_lower='0.95 under exact finite Gaussian/C0 source law')
    FHy=F@bm(y)
    Wd=bm(W)@bm(d)
    WD=bm(W)@bm(D)
    oldC=bm(W)@bm((Cd+Cd.T)/2)@bm(W).T
    profile_balls={
      'z_star_minus_WHy':z-FHy,
      'z_star_minus_Wd':z-Wd,
      'A_star_minus_WD':A-WD,
      'S_star_minus_W_symCd_WT':S-oldC,
      'Fstar_minus_F':Fstar-F
    }
    corrections={name:summarize(ball) for name,ball in profile_balls.items()}
    all_balls=dict(F=F,J=J,spin_Gram=G,spin_inverse=R,Fstar=Fstar,
                   A_star=A,z_star=z,S_star=S,full_Gram=G1,E1_Gram=G0,
                   **profile_balls)
    arrays={}
    for name,ball in all_balls.items():
        arrays[name+'_center']=ball.c
        arrays[name+'_radius']=ball.r
    np.savez_compressed(ROOT/'INTERVALS.npz',**arrays)
    # Algebraic identity H_star B=0 is exact, not inferred from a residual.
    record('SPIN_NULL','PASS',identity='(I-B(B^T B)^-1B^T)B=0 exactly',
           Frobenius_nearest='Euclidean source-coordinate convention')
    elapsed=time.monotonic()-t0
    return dict(status='CANDIDATE_CERTIFICATE_REQUIRES_INDEPENDENT_REVIEW',elapsed_internal_seconds=elapsed,
      source_law='Y~N(X beta+B omega, blockdiag(C_i)); beta and omega unrestricted',
      quotient='H_star=H(I-B(B^T B)^-1B^T) exact dyadic archived operator',
      fixed_W=True,full13_q=13,E1_q=3,k=10,
      delta_upper=delta,T_full=t1,T_E1=t0i,Delta=dl,
      conditional_E1_Delta_p_upper=upward_decimal(p),
      arbitrary_mean_ball=dict(q_upper=QUANTILE_Q,coverage_lower='0.95 conditional',
          center='z_star point entries in CENTER.npy',center_error_norm_upper=eta,radius_upper=rad),
      corrections=corrections,source_covariance=summarize(S),source_design=summarize(A),
      source_observation=summarize(z),
      full_interval_profiles='INTERVALS.npz',
      limitations=['actual cross-source covariance UNKNOWN','selection-induced Gaussian law UNKNOWN',
       'unrounded analytic pair geometry and bin clearance UNKNOWN','physical significance/coverage NOT_ESTABLISHED',
       'no df75/85 probability values','original 17/42 alternate18/42 and R9 UNKNOWN unchanged'],
      controls=dict(full_rank_exact_Gram='PASS',source_blocks='PASS',spin_null_algebraic='PASS'),
      stages=stages,center_z=z.c[:,0])

if __name__=='__main__':
    metadata=dict(packet_id=PACKET,task_id='R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE',
      input_identity='sha256:'+EXPECT_INPUT,agent_id='/root/rc_b20cec4107786152',
      requested_model='gpt-6-sol',requested_effort='high',observed_runtime='UNKNOWN',
      source_array_sha256='sha256:'+EXPECT_ARRAY,
      backend=dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),
       IEEE_premises='binary64 RN, gradual underflow, no fast-math reassociation beyond 2n dot operations',
       gamma='gamma_(2n)=2n*2^-53/(1-2n*2^-53)',bound_arithmetic_inflation=FUDGE,
       minimum_nonzero_operand=1e-150,exp_terms_10=EXP_TERMS_10,exp_terms_88=EXP_TERMS_88,
       quantile_q=QUANTILE_Q))
    try:
        out=main()
        center=out.pop('center_z')
        np.save(ROOT/'CENTER.npy',center)
        metadata.update(out)
    except BaseException as e:
        metadata.update(status='HOLD',failure_type=type(e).__name__,failure=str(e),stages=stages)
        print('FIRST_FAILURE',repr(e),file=sys.stderr)
    (ROOT/'RESULT.json').write_text(json.dumps(metadata,indent=2,default=str)+'\n')
    print(json.dumps({k:metadata.get(k) for k in ['status','failure','delta_upper','Delta','conditional_E1_Delta_p_upper']},default=str))
    sys.exit(0 if metadata['status'].startswith('CANDIDATE_') else 2)
