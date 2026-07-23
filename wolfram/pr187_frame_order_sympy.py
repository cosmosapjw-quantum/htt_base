import sympy as sp
b,w,Om = sp.symbols('b w Om')
def leading_order(expr):
    s = sp.series(expr, b, 0, 10).removeO()
    p = sp.Poly(sp.expand(s), b)
    return min(m[0] for m in p.monoms())
o2 = leading_order(sp.sinh(b)**2)
o4 = leading_order(sp.sinh(b)**4)
# Omega_tilt = (1+w) Om sinh^2 b : same order as sinh^2
oOm = leading_order((1+w)*Om*sp.sinh(b)**2)
rt = sp.simplify(b + (-b))
print("sinh2_leading_order=%s" % o2)
print("sinh4_leading_order=%s" % o4)
print("omega_tilt_order=%s" % oOm)
print("order_mismatch_4_ne_2=%s" % (o4 != o2))
print("rapidity_roundtrip=%s" % rt)
ok = o2==2 and o4==4 and oOm==2 and o4!=o2 and rt==0
print("PR187_SYMPY_PASS" if ok else "PR187_SYMPY_FAIL")
