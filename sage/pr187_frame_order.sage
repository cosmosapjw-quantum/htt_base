var('b w Om')
def leading_order(expr):
    t = expr.taylor(b, 0, 12)
    for k in range(13):
        if t.coefficient(b, k) != 0:
            return k
    return None
o2 = leading_order(sinh(b)^2)
o4 = leading_order(sinh(b)^4)
oOm = leading_order((1+w)*Om*sinh(b)^2)
rt = (b + (-b)).simplify_full()
print("sinh2_leading_order=%s" % o2)
print("sinh4_leading_order=%s" % o4)
print("omega_tilt_order=%s" % oOm)
print("order_mismatch_4_ne_2=%s" % (o4 != o2))
print("rapidity_roundtrip=%s" % rt)
ok = o2==2 and o4==4 and oOm==2 and o4!=o2 and rt==0
print("PR187_SAGE_PASS" if ok else "PR187_SAGE_FAIL")
