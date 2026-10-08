"""Independent Sage exact calculus and ordered-real certificate for CAS-13-C02."""
from sage.all import AA, QQ, PolynomialRing, RealField

P = PolynomialRing(QQ, names=("a", "b", "r", "m4", "x"))
a, b, r, m4, x = P.gens()
K = P.fraction_field()
F = K((x**4 - a**4) / (x**3 - a**3))
G = K((b**4 - x**4) / (b**3 - x**3))
Fd = K(x**2 * (3*a**2 + 2*a*x + x**2) / (a**2 + a*x + x**2)**2)
Gd = K(x**2 * (3*b**2 + 2*b*x + x**2) / (b**2 + b*x + x**2)**2)
assert F.derivative(x) == Fd
assert G.derivative(x) == Gd

F_b = K((b**4-a**4)/(b**3-a**3))
chord = K(a**4 + (r**3-a**3)*F_b)
target_lower = K((m4-a**4)/(r**3-a**3))
target_upper = K((b**4-m4)/(b**3-r**3))
assert K(target_lower-F(x=r)) == K((m4-r**4)/(r**3-a**3))
assert K(F_b-target_lower) == K((chord-m4)/(r**3-a**3))
assert K(target_upper-G(x=a)) == K((chord-m4)/(b**3-r**3))
assert K(G(x=r)-target_upper) == K((m4-r**4)/(b**3-r**3))

print("Sage exact rational-function derivative and bracketing identities PASS")
print("ORDERED-REAL CERTIFICATE: 0<a<r<b, r^3=m3, r^4<m4<chord.")
print("Fd,Gd positive: x>0 and each displayed numerator/denominator factor positive.")
print("All four bracket differences are positive; continuity and strict increase")
print("give unique u in (r,b), d in (a,r) by IVT.")
print("A3=u^3-a^3>r^3-a^3>0 and B3=b^3-d^3>b^3-r^3>0;")
print("therefore 0<wu=(r^3-a^3)/A3<1 and")
print("0<wb=(r^3-d^3)/B3<1. Weights normalize by construction.")
print("Singular identities plus A3,B3>0 give exact third/fourth moments.")
print("BOUNDARY CERTIFICATE: at m4=r^4, both bracketing targets equal")
print("F(r),G(r), hence u,d tend to r and weights tend to 1,0; delta_r.")
print("For every feasible measure, set z=y^3>0: (z^(4/3))''")
print("=(4/9)z^(-2/3)>0. Strict Jensen equality at m4=m3^(4/3)")
print("forces z=m3 almost surely, hence the unique measure is delta_r.")
print("At m4=chord, u tends to b, d tends to a; both mixtures become")
print("(1-lambda)delta_a+lambda delta_b, lambda=(r^3-a^3)/(b^3-a^3).")
print("The strict secant inequality for z^(4/3) on [a^3,b^3]")
print("forces chord equality to have support only at endpoints;")
print("the m3 equation fixes lambda uniquely.")
print("If m3 tends to a^3 or b^3, every probability measure on [a,b]")
print("with that third moment converges weakly to the endpoint Dirac:")
print("mass outside epsilon-neighborhood is bounded by the third-moment")
print("gap divided by its positive endpoint separation. No 0/0 substitution.")

Qx = PolynomialRing(QQ, "t")
t = Qx.gen()
Rf = RealField(300)
examples = [
    ("interior", QQ(20)),
    ("near_dirac", QQ(16) + QQ(1)/10**8),
    ("near_chord", QQ(293)/13 - QQ(1)/10**8),
]
for label, m4v in examples:
    av, bv, m3v, rv = QQ(1), QQ(3), QQ(8), AA(2)
    assert rv**3 == m3v and rv**4 < m4v < QQ(293)/13
    lower_poly = (m4v-av**4)*(t**3-av**3)-(m3v-av**3)*(t**4-av**4)
    upper_poly = (bv**4-m4v)*(bv**3-t**3)-(bv**3-m3v)*(bv**4-t**4)
    lower_roots = [z for z, mult in lower_poly.roots(AA) if rv < z < bv]
    upper_roots = [z for z, mult in upper_poly.roots(AA) if av < z < rv]
    assert len(lower_roots) == len(upper_roots) == 1
    uv, dv = lower_roots[0], upper_roots[0]
    wu = (m3v-av**3)/(uv**3-av**3)
    wb = (m3v-dv**3)/(bv**3-dv**3)
    assert 0 < wu < 1 and 0 < wb < 1
    assert (1-wu)*av**3+wu*uv**3 == m3v
    assert (1-wu)*av**4+wu*uv**4 == m4v
    assert (1-wb)*dv**3+wb*bv**3 == m3v
    assert (1-wb)*dv**4+wb*bv**4 == m4v
    print(f"{label}: u={Rf(uv)}, d={Rf(dv)}, wu={Rf(wu)}, wb={Rf(wb)}")
print("CAS-13-C02 Sage exact real algebra and algebraic-root vectors PASS")
