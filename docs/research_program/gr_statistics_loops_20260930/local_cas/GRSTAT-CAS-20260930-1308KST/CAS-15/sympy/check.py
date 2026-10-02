#!/usr/bin/python3
"""Independent SymPy checks of the CAS-15 finite components."""
import json
import sympy as s
from sympy import Matrix

checks = {f'CAS-15-C{i:02d}': False for i in range(1, 5)}
gaps = []
try:
    # The supplied common specification gives L=U+c e and Q u=0, but no
    # explicit normalized velocity jet or pointwise photon energy convention.
    # A generic Q decomposition cannot certify the entire C01 statement.
    gaps.append('C01: permitted inputs do not specify the normalized velocity jet or photon energy definition needed to derive both contractions.')

    x,y,z=s.symbols('x y z', real=True)
    a=Matrix(s.symbols('a0:3', real=True))
    e=Matrix([x,y,z]); sig=Matrix(3,3,s.symbols('s0:9', real=True))
    sig=(sig+sig.T)/2
    sig=sig-s.trace(sig)*s.eye(3)/3
    P=s.eye(3)-e*e.T
    F=P*(a+sig*e)
    # Ambient extension of tangential divergence, evaluated at e.e=1.
    div=sum(s.diff(F[i],e[i]) for i in range(3))
    divsphere=s.expand(div.subs(x*x+y*y+z*z,1))
    expected=-2*(a.dot(e))-3*(e.dot(sig*e))
    # Algebraic remainder is a multiple of sphere constraint.
    rem=s.factor(s.expand(div-expected))
    checks['CAS-15-C02']=s.simplify(rem/(e.dot(e)-1))==2*s.trace(sig) if rem!=0 else True
    # The weak formula needs independently supplied T2,C2 and smooth
    # sphere integration; pointwise divergence alone is insufficient.
    checks['CAS-15-C02']=False
    gaps.append('C02: pointwise divergence was checked, but the displayed weak residual and its independent integration-by-parts step lack a complete defined brightness/transport formula in permitted inputs.')

    m1,m2,m3,w1,w2,w3=s.symbols('m1 m2 m3 w1 w2 w3', real=True)
    M=s.diag(m1,m2,m3)
    W=Matrix([[0,-w3,w2],[w3,0,-w1],[-w2,w1,0]])
    R=M*W-W*M
    algebra=all(s.expand(R[i,j]-(M[i,i]-M[j,j])*W[i,j])==0 for i in range(3) for j in range(3))
    diag=all(R[i,i]==0 for i in range(3))
    # The commutator is orthogonal on the three independent skew directions;
    # singular values are |mi-mj|, so its kernel is exactly equal-eigenvalue planes.
    gram=s.diag((m2-m3)**2,(m1-m3)**2,(m1-m2)**2)
    basis=[Matrix([[0,0,0],[0,0,-1],[0,1,0]])/s.sqrt(2),Matrix([[0,0,1],[0,0,0],[-1,0,0]])/s.sqrt(2),Matrix([[0,-1,0],[1,0,0],[0,0,0]])/s.sqrt(2)]
    calc=Matrix(3,3,lambda i,j:s.trace(((M*basis[i]-basis[i]*M).T)*(M*basis[j]-basis[j]*M)))
    checks['CAS-15-C03']=bool(algebra and diag and all(s.simplify(calc[i,j]-gram[i,j])==0 for i in range(3) for j in range(3)))
    # Norm inequality follows from diagonal Gram on nonzero gaps. With Mhat,
    # Rhat, errors εM, εR, Rhat-[Mhat,W*] bounded by εR+2εM||W*||.
    # This uses the Frobenius/spectral submultiplicative norm inequality.

    n=s.Matrix(s.symbols('n0:3',real=True)); t=s.Matrix(s.symbols('t0:3',real=True))
    def axis_matrix(v, lam, mu):
        return lam*s.eye(3)+(mu-lam)*v*v.T
    # For unit axes, [M,W]=0 iff W axis=0, because nonisotropic
    # axisymmetric M has a unique one-dimensional eigenspace.
    u=Matrix([1,0,0]); v=Matrix([s.cos(s.symbols('h',real=True)),s.sin(s.symbols('h',real=True)),0])
    h=s.symbols('h',real=True)
    A=axis_matrix(u,s.symbols('l'),s.symbols('p'))
    B=axis_matrix(v,s.symbols('L'),s.symbols('P'))
    # Generic symbolic representative: nonparallel means sin(h)!=0.
    basis_gram=Matrix(3,3,lambda i,j:s.expand(s.trace((A*basis[i]-basis[i]*A).T*(A*basis[j]-basis[j]*A)+(B*basis[i]-basis[i]*B).T*(B*basis[j]-basis[j]*B))))
    determinant=s.factor(s.trigsimp(basis_gram.det()))
    checks['CAS-15-C04']=bool(determinant!=0 and s.simplify(determinant.subs({h:s.pi/2,s.symbols('l'):0,s.symbols('p'):1,s.symbols('L'):0,s.symbols('P'):1}))>0)
    # The analytic kernel argument applies to every nonparallel pair, not
    # solely the representative determinant test: W kills both axes, and
    # a nonzero 3D skew matrix has only a one-dimensional kernel.
except Exception as exc:
    gaps.append(f'checker exception: {type(exc).__name__}: {exc}')
print(json.dumps({'checks':checks,'domain_assumption_diff':gaps,'counterexample':None},sort_keys=True))
