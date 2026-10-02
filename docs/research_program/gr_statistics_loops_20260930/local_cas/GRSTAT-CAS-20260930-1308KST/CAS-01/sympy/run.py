#!/usr/bin/env python3
"""Independent exact SymPy checks for CAS-01."""
import json
import pathlib
import sys
import traceback
import sympy as s

HERE = pathlib.Path(__file__).resolve().parent
KEYS = [f"CAS-01-C{i:02d}" for i in range(1, 5)]


def main():
    c, a = s.symbols('c a', positive=True)
    u0, u1, u2, u3 = u = s.symbols('u0 u1 u2 u3', real=True)
    U = s.Matrix(u)
    g = s.diag(-1, 1, 1, 1)
    shell = s.groebner([u0*u0-u1*u1-u2*u2-u3*u3-1], *u, domain='EX')
    zero = lambda e: s.expand(shell.reduce(s.expand(e))[1]) == 0
    mz = lambda M: all(zero(e) for e in M)
    q = s.symbols('s00 s01 s02 s03 s11 s12 s13 s22 s23 s33', real=True)
    S = s.Matrix([[q[0],q[1],q[2],q[3]], [q[1],q[4],q[5],q[6]],
                  [q[2],q[5],q[7],q[8]], [q[3],q[6],q[8],q[9]]])
    B = S + (U.T*S*U)[0]*g
    Bs = S+a*g+(U.T*(S+a*g)*U)[0]*g
    b = B*U
    c01a = zero((U.T*B*U)[0]) and mz(Bs-B)
    n1,n2,n3 = n = s.symbols('n1 n2 n3', real=True)
    t = s.symbols('t00 t01 t02 t03 t11 t12 t13 t22 t23 t33', real=True)
    T = s.Matrix([[t[0],t[1],t[2],t[3]], [t[1],t[4],t[5],t[6]],
                  [t[2],t[5],t[7],t[8]], [t[3],t[6],t[8],t[9]]])
    K = s.Matrix([-1,n1,n2,n3])
    sphere = s.groebner([n1*n1+n2*n2+n3*n3-1], *n, domain='EX')
    rem = s.expand(sphere.reduce((K.T*T*K)[0])[1])
    sol = s.solve(s.Poly(rem,*n).coeffs(),t[:-1],dict=True)
    positions = [(0,0),(0,1),(0,2),(0,3),(1,1),(1,2),(1,3),(2,2),(2,3)]
    c01b = len(sol)==1 and all(s.simplify(sol[0][ti]-t[-1]*g[i,j])==0
                                for ti,(i,j) in zip(t[:-1],positions))
    checks = {KEYS[0]:bool(c01a and c01b)}
    P = s.eye(4)+U*(U.T*g)
    z = s.symbols('z01 z02 z03 z12 z13 z23', real=True)
    Z = s.Matrix([[0,z[0],z[1],z[2]],[-z[0],0,z[3],z[4]],
                  [-z[1],-z[3],0,z[5]],[-z[2],-z[4],-z[5],0]])
    W = P.T*Z*P
    uf = g*U
    Q = B+b*uf.T-uf*b.T+W
    A = c*Q.T*U
    theta = s.trace(g*B)
    h = g+uf*uf.T
    sig = P.T*B*P-theta*h/3
    checks[KEYS[1]] = bool(mz(Q*U) and mz((Q+Q.T)/2-B) and mz(A-2*c*b)
                           and mz(sig*U) and zero(s.trace(g*sig)) and mz(sig-sig.T))
    h0 = s.symbols('h0',real=True)
    h1 = s.Matrix(s.symbols('h1x h1y h1z',real=True))
    xx,yy,xy,xz,yz = s.symbols('xx yy xy xz yz',real=True)
    h2 = s.Matrix([[xx,xy,xz],[xy,yy,yz],[xz,yz,-xx-yy]])
    Sr = s.zeros(4); Sr[0,0]=h0
    for i in range(3):
        Sr[0,i+1]=Sr[i+1,0]=-h1[i]/2
        for j in range(3): Sr[i+1,j+1]=h2[i,j]
    ur = s.Matrix([1,0,0,0]); Br=Sr+(ur.T*Sr*ur)[0]*g
    Ar=2*c*Br*ur; nr=s.Matrix(n); Hr=(K.T*Br*K)[0]
    tr=s.trace(g*Br); sig_r=Br[1:4,1:4]-tr*s.eye(3)/3
    target1=h0+(h1.T*nr)[0]+(nr.T*h2*nr)[0]
    target2=tr/3+(nr.T*sig_r*nr)[0]-(Ar[1:4,0].T*nr)[0]/c
    checks[KEYS[2]]=bool(s.expand(sphere.reduce(Hr-target1)[1])==0 and
                          s.expand(sphere.reduce(Hr-target2)[1])==0 and
                          sig_r==h2 and Ar[1:4,0]==-c*h1)
    x=s.symbols('x0 x1 x2 x3',real=True)
    dv=g*Q.T/c
    v=U+dv*s.Matrix(x)
    norm2=-(v.T*g*v)[0]
    origin={xi:0 for xi in x}
    # Exact chain rule for v/sqrt(-g(v,v)) at norm2(0)=1, positive branch.
    dnorm=s.Matrix([[s.diff(norm2,xi).subs(origin) for xi in x]])
    jac=dv-U*dnorm/2
    checks[KEYS[3]]=bool(zero(norm2.subs(origin)-1) and mz(jac-dv))
    (HERE/'raw.log').write_text('SymPy '+s.__version__+'\nsphere remainder '+str(rem)+
                                '\nnull kernel '+str(sol)+'\nchecks '+str(checks)+'\n')
    return {'checks':checks,'domain_assumption_diff':[],'counterexample':None}


if __name__=='__main__':
    try: result=main()
    except Exception:
        (HERE/'raw.log').write_text(traceback.format_exc())
        result={'checks':{k:False for k in KEYS},
                'domain_assumption_diff':['implementation exception; see raw.log'],
                'counterexample':None}
    sys.stdout.write(json.dumps(result,sort_keys=True))
