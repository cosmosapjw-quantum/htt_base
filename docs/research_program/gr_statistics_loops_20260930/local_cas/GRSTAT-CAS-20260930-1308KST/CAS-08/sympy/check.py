#!/usr/bin/python3
"""Independent finite GLS projector and decision-logic checks for CAS-08."""
import json,itertools
import sympy as s
checks={f'CAS-08-C{i:02d}':False for i in range(1,4)};gaps=[]
try:
 # For every SPD C choose W=C^{-1/2}. Let A=WF. Moore-Penrose
 # identities AA+ A=A, (AA+)^T=AA+, (AA+)²=AA+ prove the claim
 # independently of rank. Verify all rank strata in a rational example.
 C=s.diag(4,9,16); W=s.diag(s.Rational(1,2),s.Rational(1,3),s.Rational(1,4))
 strata=[s.zeros(3,2),s.Matrix([[1,2],[0,0],[0,0]]),s.Matrix([[1,0],[0,2],[0,0]])]
 c1=True;c2=True
 for F in strata:
  A=W*F; P=s.eye(3)-A*A.pinv()
  c1 &= (W*C*W.T==s.eye(3) and P==P.T and P*P==P and P*A==s.zeros(3,F.cols) and P.rank()==3-F.rank())
  # z=Pz+(I-P)z, with Aβ in range A, so minβ||z-Aβ||²=||Pz||².
  z=s.Matrix([2,3,5]); beta=A.pinv()*z
  c2 &= (s.simplify((z-A*beta).dot(z-A*beta)-(P*z).dot(P*z))==0 and P*W*C*W.T*P.T==P)
 checks['CAS-08-C01']=bool(c1)
 checks['CAS-08-C02']=bool(c2)
 # Under the true complete model, null rejection with nonempty full
 # feasibility implies true point lies outside the inverted confidence set.
 # Exhaust all finite confidence/full/null sets on a 3-point universe.
 universe=set(range(3));logic=True
 subsets=[{i for i in range(3) if mask>>i&1} for mask in range(8)]
 for full,conf,null in itertools.product(subsets,repeat=3):
  feasible=full&conf;nullfeas=feasible&null
  state=(0 if not feasible else (1 if not nullfeas else (2 if feasible<=null else 3)))
  logic &= state in (0,1,2,3)
  for truth in full&null:
   if feasible and not nullfeas and truth in conf:logic=False
 checks['CAS-08-C03']=bool(logic)
 gaps.append('Probability calibration and measurable projection remain outside these finite checks, as stated in contract.')
except Exception as exc:gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
