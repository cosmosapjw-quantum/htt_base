"""Host direct supporting algebra, explicitly not independent CAS admission."""
import json
import sympy as s
t=s.symbols('t',positive=True)
qd,g,d,cd,c,e=s.symbols('qd g d cd c e',real=True)
checks={
 'P1_normalized_coefficients':all(s.simplify(x)==0 for x in (
    (-qd+g+3*d/7)/t-(-qd/t+g/t+3*d/(7*t)),
    (3*cd/t+c-6*e/(5*t))/t-(3*cd/t**2+c/t-6*e/(5*t**2)))),
 'P2_mock6_squared_norms':sum(x*x for x in (1,2,1,2,1,2,1,2))==20 and s.sqrt(8)**2==8 and s.sqrt(5)**2==5 and s.sqrt(3)**2==3,
 'J1_set_logic_and_allocation':s.Rational(1)-4*s.Rational(1,80)==s.Rational(19,20),
}
a,b,c=s.symbols('a b c')
checks['J1_set_logic_and_allocation'] &= s.simplify_logic(s.Equivalent(a & (b|c),(a&b)|(a&c))) is s.true
v=s.eye(8)[:,7];R=s.eye(8)[:4,:];K=s.eye(8)
checks['V08_fixture_ray']=R*v==s.zeros(4,1) and K*v==v and (v.T*v)[0]==1
assert all(checks.values())
print(json.dumps({'checks':checks,'versions':{'sympy':s.__version__}}))
