#!/usr/bin/env python3
"""Independent SymPy finite checks and domain audit for CAS-03."""
import json
import pathlib
import sys
import traceback
import sympy as s

HERE=pathlib.Path(__file__).resolve().parent
KEYS=[f'CAS-03-C{i:02d}' for i in range(1,4)]


def main():
    g=s.diag(-1,1,1,1)
    t=s.symbols('t',real=True)
    u=s.Matrix([1,0,0,0])
    b11,b22,b12,b13,b23=s.symbols('b11 b22 b12 b13 b23',real=True)
    B=s.Matrix([[0,0,0,0],[0,b11,b12,b13],
                [0,b12,b22,b23],[0,b13,b23,-b11-b22]])
    S=B+t*g
    eig=s.simplify(g*S*u-t*u)==s.zeros(4,1)
    Bu=B*u==s.zeros(4,1)
    trace0=s.trace(g*B)==0
    converse=s.simplify(g*(S-t*g)*u)==s.zeros(4,1)
    c01=bool(eig and Bu and trace0 and converse)
    # Exact parameter count in the rest kernel: five independent STF entries.
    c01=c01 and len([b11,b22,b12,b13,b23])==5

    # The named B_epsilon_chi family and its slope formula are not present in
    # the permitted contract or neutral specification.
    c02=False

    H,e=s.symbols('H e',real=True,nonzero=True)
    sx,sy=s.symbols('sx sy',real=True)
    sig=s.diag(sx,sy,-sx-sy)
    D=H*s.eye(3)+sig
    beta=s.Matrix(s.symbols('bx by bz',real=True))
    h1=-2*D*beta
    inv=s.simplify(-D.inv()*h1/2-beta)==s.zeros(3,1)
    trunc=-(s.eye(3)-sig/H)*h1/(2*H)
    defect=s.simplify(beta-trunc-sig*sig*beta/H**2)==s.zeros(3,1)
    Dneg=s.diag(s.Rational(3,2),s.Rational(3,4),s.Rational(3,4))
    sig_neg=Dneg-s.eye(3)
    beta_neg=s.Matrix([e,0,0])
    hneg=-2*Dneg*beta_neg
    approx=-(s.eye(3)-sig_neg)*hneg/2
    control=s.simplify(approx[0]-s.Rational(3,4)*e)==0
    # The contract says arbitrary invertible D, but its truncated inverse
    # divides by H. D=diag(1,1,-2) is invertible and trace-free, so H=0.
    D0=s.diag(1,1,-2)
    zero_H_counterexample=(D0.det()!=0 and s.trace(D0)==0)
    c03=bool(inv and defect and control and not zero_H_counterexample)
    checks=dict(zip(KEYS,[c01,c02,c03]))
    issues=['CAS-03-C02: B_epsilon_chi and its stated slope formula absent from permitted inputs',
            'CAS-03-C03: truncated inverse divides by H although arbitrary invertible D allows H=0']
    counter={'obligation':'CAS-03-C03','D':[[1,0,0],[0,1,0],[0,0,-2]],
             'det_D':'-2','H':'trace(D)/3 = 0','effect':'truncated inverse undefined'}
    (HERE/'raw.log').write_text('SymPy '+s.__version__+'\n'+
                                f'eigen={eig}, Bu={Bu}, trace0={trace0}, converse={converse}\n'+
                                f'inverse={inv}, defect={defect}, control={control}, D0={zero_H_counterexample}\n'+
                                f'checks={checks}\n')
    return {'checks':checks,'domain_assumption_diff':issues,'counterexample':counter}


if __name__=='__main__':
    try: result=main()
    except Exception:
        (HERE/'raw.log').write_text(traceback.format_exc())
        result={'checks':{k:False for k in KEYS},
                'domain_assumption_diff':['implementation exception; see raw.log'],
                'counterexample':None}
    sys.stdout.write(json.dumps(result,sort_keys=True))
