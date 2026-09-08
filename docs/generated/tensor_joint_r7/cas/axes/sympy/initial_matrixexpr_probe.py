import sympy as s
import sys
print(sys.version, flush=True)
print(s.__version__, flush=True)
t=s.symbols('t',real=True)
n,m,r=s.symbols('n m r', integer=True,positive=True)
E=s.MatrixSymbol('E',n,n); A=s.MatrixSymbol('A',n,m); C=s.MatrixSymbol('C',r,n)
K=-t*C*(s.Identity(n)-t*E).inv()*A
print(K.diff(t).subs(t,0).doit())
