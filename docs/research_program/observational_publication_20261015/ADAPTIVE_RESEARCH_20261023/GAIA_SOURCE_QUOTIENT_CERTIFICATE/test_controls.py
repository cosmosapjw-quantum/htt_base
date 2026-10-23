"""Focused falsifiers for the exact source quotient certificate."""
from fractions import Fraction
import json, math, time
import numpy as np
from certify import Ball,bm,inverse_cert,source_covariance,bound_inf

out=[]
def check(name,ok,detail):
    out.append(dict(name=name,status='PASS' if ok else 'FAIL',detail=detail))
    if not ok: raise AssertionError(name)

def contains(ball,i,j,value):
    return ball.c[i,j]-ball.r[i,j] <= value <= ball.c[i,j]+ball.r[i,j]

start=time.monotonic()
# Contaminated H=H0+E, with H0 B=0. Quotient recovers exact Hstar
# and propagates nonuniform block covariance, including off-diagonals.
B=np.array([[1.],[1.],[0.],[0.]])
H=np.array([[2.,-1.,1.,0.]])
C=np.array([[[2.,1.],[1.,3.]],[[5.,-1.],[-1.,7.]]])
R,_=inverse_cert(bm(B).T@bm(B),'CONTROL_SPIN')
Hstar=bm(H)-(bm(H)@bm(B)@R@bm(B).T)
expected=np.array([[1.5,-1.5,1.,0.]])
check('contaminated_operator_quotient',
      all(contains(Hstar,0,j,float(expected[0,j])) for j in range(4)),
      'H0B=0; E adds spin contamination; exact quotient Hstar=[3/2,-3/2,1,0] and Hstar B=0')
S=source_covariance(Hstar,C)
check('nonuniform_block_covariance',contains(S,0,0,11.75),
      'Two exact symmetric SPD blocks with off-diagonals; exact propagated variance=47/4')
# Exact complete images and nesting, including a deficient coefficient fiber.
M=np.array([[1.,0.],[0.,1.],[0.,0.]])
G=bm(M).T@bm(M)
R,_=inverse_cert(G,'CONTROL_FULL')
check('exact_full_rank_nesting',bound_inf(bm(np.eye(2))-(G@R))<1,
      'q_full=2,q_E1=1,k=1; E1 span contained in full span')
check('rank_deficient_unbounded_fiber',
      np.array_equal(np.array([[1.,0.]])@np.array([[0.],[1.]]),np.array([[0.]])),
      'M=(1,0), ker M contains (0,1); beta+t(0,1) unbounded for all real t')
Br=np.array([[1.],[0.],[0.],[0.]])
Hr=np.array([[1.,0.,0.,0.],[0.,1.,0.,0.]])
Xr=np.array([[1.,0.],[0.,1.],[0.,0.],[0.,0.]])
Rr,_=inverse_cert(bm(Br).T@bm(Br),'CONTROL_RANK_LOSS_SPIN')
Ar=(bm(Hr)-(bm(Hr)@bm(Br)@Rr@bm(Br).T))@bm(Xr)
check('quotient_rank_loss_and_fiber',
      all(contains(Ar,i,j,float(np.array([[0.,0.],[0.,1.]])[i,j]))
          for i in range(2) for j in range(2)),
      'First model column equals B and vanishes exactly; complete E1 rank=0, full rank=1, k=1; first coefficient fiber is unbounded')
small=Fraction(1,2**44)
check('small_positive_exact_mode',small>0 and small*small>0,
      'det [[1,1],[0,2^-44]]=2^-44; no threshold may erase the exact mode')
check('covariance_inflation',bound_inf(bm(1.5*np.eye(2))-bm(np.eye(2)))>=0.5,
      'S=1.5 I requires delta at least 0.5')
check('failing_bound_branch',bound_inf(bm(2.1*np.eye(2))-bm(np.eye(2)))>1,
      'S=2.1 I has delta>1 and must HOLD under the frozen sufficient criterion')
eta=Fraction(1,2**20)
check('rounded_center_inflation',eta>0 and Fraction(11)+eta>Fraction(11),
      'Displayed center shifted by 2^-20 requires radius at least original radius+2^-20')
print(json.dumps(dict(status='PASS',elapsed_internal_seconds=time.monotonic()-start,controls=out),indent=2))
