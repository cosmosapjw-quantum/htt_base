#!/usr/bin/env python3
"""Independent SymPy verification of CAS-14's finite rotation algebra."""
import json
import pathlib
import sys
import traceback
import sympy as s

HERE=pathlib.Path(__file__).resolve().parent
KEYS=[f'CAS-14-C{i:02d}' for i in range(1,4)]


def main():
    x1,x2,x3=x=s.symbols('x1 x2 x3',real=True)
    w1,w2,w3=w=s.symbols('w1 w2 w3',real=True)
    X=s.Matrix(x);O=s.Matrix(w)
    W=s.Matrix([[0,w3,-w2],[-w3,0,w1],[w2,-w1,0]])
    sphere=s.groebner([x1*x1+x2*x2+x3*x3-1],*x,domain='EX')
    zero=lambda e:s.expand(sphere.reduce(s.expand(e))[1])==0
    y=-W*X
    c01=all(s.expand(a)==0 for a in W*X+O.cross(X))
    c01=c01 and all(zero(a) for a in X.cross(y)-(s.eye(3)-X*X.T)*O)
    p=s.eye(3)-X*X.T
    c01=c01 and all(zero(a) for a in p*p-p)

    # Two unit directions, with s0>0 and c0^2+s0^2=1, suffice for full rank.
    c0,s0=s.symbols('c0 s0',real=True)
    a,b=s.symbols('a b',positive=True)
    e1=s.Matrix([1,0,0]);e2=s.Matrix([c0,s0,0])
    G=a*(s.eye(3)-e1*e1.T)+b*(s.eye(3)-e2*e2.T)
    unit=s.groebner([c0*c0+s0*s0-1],c0,s0,domain='EX')
    determinant=s.factor(unit.reduce(s.expand(G.det()))[1])
    expected=a*b*(a+b)*s0*s0
    adj_identity=s.simplify(G*G.adjugate()-G.det()*s.eye(3))==s.zeros(3)
    # v^T G v = a|e1 x v|^2+b|e2 x v|^2. The common
    # kernel is zero when s0 != 0; determinant then is positive.
    v=s.Matrix(s.symbols('v1 v2 v3',real=True))
    psd=s.expand(unit.reduce(s.expand((v.T*G*v)[0]
                   -a*e1.cross(v).dot(e1.cross(v))
                   -b*e2.cross(v).dot(e2.cross(v))))[1])==0
    c02=bool(s.simplify(determinant-expected)==0 and adj_identity and psd)

    dO=s.Matrix(s.symbols('dw1 dw2 dw3',real=True))
    dW=W.subs(dict(zip(w,dO)))
    frob=s.expand(s.trace(dW.T*dW)-2*dO.dot(dO))==0
    # This exact identity is only one part of C03. The general operator
    # perturbation bound needs a separate quantified norm argument.
    checks=dict(zip(KEYS,[bool(c01),c02,False]))
    (HERE/'raw.log').write_text('SymPy '+s.__version__+'\n'+
        f'cross/projector={c01}; determinant={determinant}; adjugate={adj_identity}; PSD={psd}; Frobenius={frob}\n'+
        f'checks={checks}\n')
    return {'checks':checks,
            'domain_assumption_diff':['CAS-14-C03: exact skew/Frobenius identity checked, but quantified least-squares and perturbed-operator norm bounds not established by this finite script'],
            'counterexample':None}


if __name__=='__main__':
    try: result=main()
    except Exception:
        (HERE/'raw.log').write_text(traceback.format_exc())
        result={'checks':{k:False for k in KEYS},'domain_assumption_diff':['implementation exception; see raw.log'],'counterexample':None}
    sys.stdout.write(json.dumps(result,sort_keys=True))
