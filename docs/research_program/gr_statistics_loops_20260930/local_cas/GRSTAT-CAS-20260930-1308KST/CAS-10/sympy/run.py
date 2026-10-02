#!/usr/bin/env python3
"""Independent SymPy finite algebra and input-sufficiency audit for CAS-10."""
import json
import pathlib
import sys
import traceback
import sympy as s

HERE=pathlib.Path(__file__).resolve().parent
KEYS=[f'CAS-10-C{i:02d}' for i in range(1,5)]


def main():
    u0,u1,u2,u3=u=s.symbols('u0 u1 u2 u3',real=True)
    U=s.Matrix(u);g=s.diag(-1,1,1,1)
    shell=s.groebner([u0*u0-u1*u1-u2*u2-u3*u3-1],*u,domain='EX')
    zero=lambda e:s.expand(shell.reduce(s.expand(e))[1])==0
    q=s.symbols('s00 s01 s02 s03 s11 s12 s13 s22 s23 s33',real=True)
    S=s.Matrix([[q[0],q[1],q[2],q[3]],[q[1],q[4],q[5],q[6]],
                [q[2],q[5],q[7],q[8]],[q[3],q[6],q[8],q[9]]])
    c=s.symbols('c',positive=True)
    h=(U.T*S*U)[0]
    b=(S+h*g)*U
    J=(S*U).T*g*(S*U)
    J=J[0]+h*h
    A=2*c*b
    c02=zero(J-(A.T*g*A)[0]/(4*c*c)) and zero((U.T*b)[0])
    # Positivity/zero iff A=0 follows from positive-definite rest metric.
    # The exact polynomial identity is checked above, with the future shell.
    checks=dict(zip(KEYS,[False,bool(c02),False,False]))
    missing=[
      'CAS-10-C01: the two rational morphology tuples are not in permitted contract/spec',
      'CAS-10-C03: no explicit Gaussian mean vectors or compression map supplied',
      'CAS-10-C04: quintic cutoff and interval are not defined in permitted inputs'
    ]
    (HERE/'raw.log').write_text('SymPy '+s.__version__+'\nJ minus A-square quotient zero: '+str(c02)+'\nchecks '+str(checks)+'\n')
    return {'checks':checks,'domain_assumption_diff':missing,'counterexample':None}


if __name__=='__main__':
    try: result=main()
    except Exception:
        (HERE/'raw.log').write_text(traceback.format_exc())
        result={'checks':{k:False for k in KEYS},'domain_assumption_diff':['implementation exception; see raw.log'],'counterexample':None}
    sys.stdout.write(json.dumps(result,sort_keys=True))
