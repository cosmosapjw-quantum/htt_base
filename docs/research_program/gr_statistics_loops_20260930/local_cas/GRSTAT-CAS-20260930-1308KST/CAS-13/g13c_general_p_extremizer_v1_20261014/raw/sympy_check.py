"""Independent sympy/mpmath cross-check for G13-C (ancillary; not a proof)."""
import random, sympy as sp, mpmath as mp
y, p, A, U = sp.symbols('y p A U', positive=True)
fs = [sp.Integer(1), y**3, y**4, y**p]
W = sp.Matrix(4, 4, lambda i, j: sp.diff(fs[j], y, i)).det()
print("W4 - 12p(p-3)(p-4)y^(p+1) =", sp.simplify(W - 12*p*(p-3)*(p-4)*y**(p+1)))
print("W2 =", sp.simplify(sp.Matrix(2, 2, lambda i, j: sp.diff(fs[j], y, i)).det()),
      " W3 =", sp.simplify(sp.Matrix(3, 3, lambda i, j: sp.diff(fs[j], y, i)).det()))
print("(p y^(p-3))'' * 12 y^6 - W =", sp.simplify(sp.diff(p*y**(p-3), y, 2)*12*y**6 - W))
D = 3*(U**4-A**4) - 4*U*(U**3-A**3)
print("interpDet + (U-A)^2(U^2+2AU+3A^2) =", sp.expand(D + (U-A)**2*(U**2+2*A*U+3*A**2)))
P = p*U**(p-3); De = U**p - A**p
c3 = (P*(U**4-A**4) - 4*U*De)/D; c4 = (3*De - (U**3-A**3)*P)/D; c0 = A**p - c3*A**3 - c4*A**4
Q = c0 + c3*y**3 + c4*y**4
print("Q(U)-U^p =", sp.simplify(Q.subs(y, U) - U**p), " Q'(U)-pU^(p-1) =", sp.simplify(sp.diff(Q, y).subs(y, U) - p*U**(p-1)))
# random real-p fibre check
mp.mp.dps = 40
random.seed(20261014)
viol = 0; tested = 0
for _ in range(400):
    a = mp.mpf(random.uniform(0.2, 2)); b = a*mp.mpf(random.uniform(1.05, 3))
    k = random.choice([2, 3, 4]); xs = [mp.mpf(random.uniform(float(a), float(b))) for _ in range(k)]
    ws = [mp.mpf(random.random()) for _ in range(k)]; s = sum(ws); ws = [w/s for w in ws]
    m3 = sum(w*x**3 for w, x in zip(ws, xs)); m4 = sum(w*x**4 for w, x in zip(ws, xs))
    r = mp.cbrt(m3)
    if not (m4 > r**4 + mp.mpf('1e-25')): continue
    f = lambda t: (t**4-a**4)/(t**3-a**3) - (m4-a**4)/(m3-a**3)
    g = lambda t: (b**4-t**4)/(b**3-t**3) - (b**4-m4)/(b**3-m3)
    u = mp.findroot(f, (r, b), solver='anderson'); d = mp.findroot(g, (a, r), solver='anderson')
    wu = (m3-a**3)/(u**3-a**3); wb = (m3-d**3)/(b**3-d**3)
    for pp in [mp.mpf('4.01'), mp.mpf('4.5'), mp.mpf('5.3'), mp.pi*2, mp.mpf('11.7')]:
        mpv = sum(w*x**pp for w, x in zip(ws, xs))
        L = (1-wu)*a**pp + wu*u**pp; Uv = (1-wb)*d**pp + wb*b**pp
        tested += 1
        if not (L <= mpv*(1+mp.mpf('1e-30')) and mpv <= Uv*(1+mp.mpf('1e-30'))): viol += 1
print("random fibre checks (p in {4.01,4.5,5.3,2pi,11.7}):", tested, "violations:", viol)
