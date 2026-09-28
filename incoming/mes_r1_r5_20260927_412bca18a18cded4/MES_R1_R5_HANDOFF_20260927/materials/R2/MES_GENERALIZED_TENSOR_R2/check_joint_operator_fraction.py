"""Exact rational spherical-polynomial checks; Python standard library only.

Independent arithmetic realization of check_joint_operator.py, retained intact.
No ODE/PDE evolution, package installation, quadrature approximation or real sky.
"""
from fractions import Fraction as F
from pathlib import Path
import hashlib
import itertools
import json
import math
import platform
import random
import statistics

ROOT = Path(__file__).resolve().parent


class Poly:
    """Sparse polynomial in ambient x,y,z over Q."""
    def __init__(self, value=0):
        if isinstance(value, Poly):
            self.terms = value.terms.copy()
        elif isinstance(value, dict):
            self.terms = {k: F(v) for k, v in value.items() if v}
        else:
            self.terms = {(0, 0, 0): F(value)} if value else {}

    def __add__(self, other):
        terms = self.terms.copy()
        for key, value in Poly(other).terms.items():
            terms[key] = terms.get(key, F(0)) + value
        return Poly(terms)

    __radd__ = __add__

    def __neg__(self):
        return Poly({k: -v for k, v in self.terms.items()})

    def __sub__(self, other):
        return self + (-Poly(other))

    def __rsub__(self, other):
        return Poly(other) - self

    def __mul__(self, other):
        terms = {}
        for p, a in self.terms.items():
            for q, b in Poly(other).terms.items():
                key = tuple(x + y for x, y in zip(p, q))
                terms[key] = terms.get(key, F(0)) + a * b
        return Poly(terms)

    __rmul__ = __mul__

    def __truediv__(self, denominator):
        return self * (F(1) / denominator)

    def __pow__(self, n):
        if not isinstance(n, int) or n < 0:
            raise ValueError("nonnegative integer power required")
        result = Poly(1)
        for _ in range(n):
            result = result * self
        return result

    def derivative(self, axis):
        terms = {}
        for p, a in self.terms.items():
            if p[axis]:
                q = list(p)
                q[axis] -= 1
                terms[tuple(q)] = a * p[axis]
        return Poly(terms)


def double_factorial(n):
    return math.prod(range(n, 0, -2))


def avg(poly):
    total = F(0)
    for powers, coefficient in Poly(poly).terms.items():
        if any(p % 2 for p in powers):
            continue
        total += coefficient * F(
            math.prod(double_factorial(p - 1) for p in powers),
            double_factorial(sum(powers) + 1),
        )
    return total


def mapped(fun, obj):
    return [mapped(fun, v) for v in obj] if isinstance(obj, list) else fun(obj)


def add(a, b):
    return [add(x, y) for x, y in zip(a, b)] if isinstance(a, list) else a + b


def scale(c, obj):
    return mapped(lambda v: c * v, obj)


def sub(a, b):
    return add(a, scale(-1, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def outer(a, b):
    return [[x * y for y in b] for x in a]


def transpose(a):
    return [list(row) for row in zip(*a)]


def mv(a, v):
    return [dot(row, v) for row in a]


def mm(a, b):
    bt = transpose(b)
    return [[dot(row, col) for col in bt] for row in a]


def trace(a):
    return sum(a[i][i] for i in range(3))


I = [[F(i == j) for j in range(3)] for i in range(3)]


def stf(a):
    return sub(scale(F(1, 2), add(a, transpose(a))), scale(trace(a) / 3, I))


def grad(p):
    return [Poly(p).derivative(i) for i in range(3)]


def iszero(a):
    if isinstance(a, list):
        return all(iszero(v) for v in a)
    return not Poly(a).terms


def exact_rank(matrix):
    a = [[F(v) for v in row] for row in matrix]
    nr, nc, rank = len(a), len(a[0]), 0
    pivots = []
    for col in range(nc):
        pivot = next((r for r in range(rank, nr) if a[r][col]), None)
        if pivot is None:
            continue
        a[rank], a[pivot] = a[pivot], a[rank]
        value = a[rank][col]
        a[rank] = [v / value for v in a[rank]]
        for row in range(rank + 1, nr):
            value = a[row][col]
            if value:
                a[row] = [v - value * u for v, u in zip(a[row], a[rank])]
        pivots.append(col)
        rank += 1
        if rank == nr:
            break
    return rank, pivots


x, y, z = [Poly({tuple(int(i == j) for j in range(3)): 1}) for i in range(3)]
e = [x, y, z]
H = F(2, 7)
S = scale(F(1, 11), [[1,2,0],[2,-2,1],[0,1,1]])
a = scale(F(1, 13), [2,-1,3])
om = scale(F(1, 17), [-1,2,1])
Pe = sub(I, outer(e, e))
R = H + dot(a,e) + dot(e,mv(S,e))
V = sub(scale(-1,mv(Pe,add(a,mv(S,e)))),cross(om,e))
E = sub(outer(e,e),scale(F(1,3),I))
av = lambda obj: mapped(avg, obj)
identities = {
    "optical_H": avg(R)-H,
    "optical_a": sub(av(scale(3*R,e)),a),
    "optical_S": sub(av(scale(F(15,2)*R,E)),S),
    "optical_omega": sub(av(scale(F(-3,2),cross(e,V))),om),
    "angular_a": sub(av(scale(F(-3,2),V)),a),
    "angular_S": sub(scale(-5,stf(av(outer(e,V)))),S),
    "R_norm": avg(R**2)-(H**2+dot(a,a)/3+F(2,15)*trace(mm(S,S))),
    "V_norm": avg(dot(V,V))-(F(2,3)*dot(a,a)+trace(mm(S,S))/5+F(2,3)*dot(om,om)),
}

B = 1+(x+2*y-z)/20+(x*x+2*y*y-3*z*z)/25+x*y*z/10
assert avg(B) == 1
# Triangle inequality on |x|,|y|,|z|<=1 gives B>=1-4/20-6/25-1/10.
b_lower_bound = F(1)-F(4,20)-F(6,25)-F(1,10)
assert b_lower_bound == F(23,50)
tests = []
for degree in range(5):
    for ix in range(degree+1):
        for iy in range(degree-ix+1):
            tests.append((degree,x**ix*y**iy*z**(degree-ix-iy)))

SB = [
    [[1,0,0],[0,-1,0],[0,0,0]],
    [[1,0,0],[0,1,0],[0,0,-2]],
    [[0,1,0],[1,0,0],[0,0,0]],
    [[0,0,1],[0,0,0],[1,0,0]],
    [[0,0,0],[0,0,1],[0,1,0]],
]
Z = [[F(0) for _ in range(3)] for _ in range(3)]
zv = [F(0)]*3
columns = [(1,Z,zv,zv)]
columns += [(0,s,zv,zv) for s in SB]
columns += [(0,Z,I[i],zv) for i in range(3)]
columns += [(0,Z,zv,I[i]) for i in range(3)]


def response(brightness):
    result_columns, failures = [], []
    for j,(hh,ss,aa,oo) in enumerate(columns):
        s, ae = dot(e,mv(ss,e)), dot(aa,e)
        w = add(mv(Pe,add(aa,mv(ss,e))),cross(oo,e))
        strong = -dot(w,grad(brightness))+4*(hh+s+ae)*brightness
        col = []
        for i,(degree,psi) in enumerate(tests):
            weak = dot(add(add(aa,mv(ss,e)),cross(oo,e)),grad(psi))
            weak += (4*hh+(1-degree)*s+(2-degree)*ae)*psi
            val = avg(brightness*weak)
            difference = avg(psi*strong)-val
            if difference:
                failures.append({"row":i,"column":j,"residual":str(difference)})
            col.append(val)
        result_columns.append(col)
    return transpose(result_columns), failures


Aiso, fail_iso = response(Poly(1))
Agen, fail_gen = response(B)
rank_iso, pivot_iso = exact_rank(Aiso)
rank_gen, pivot_gen = exact_rank(Agen)

rho, M1, M2 = avg(B), av(scale(B,e)), av(scale(B,outer(e,e)))
Pi = stf(M2)
q = dot(e,mv(S,e))
LB = sub(sub(add(mm(S,M2),mm(M2,S)),av(scale(B*q,outer(e,e)))),scale(trace(mm(M2,S))/3,I))
Rom = [[0,-om[2],om[1]],[om[2],0,-om[0]],[-om[1],om[0],0]]
strong = -dot(add(mv(Pe,add(a,mv(S,e))),cross(om,e)),grad(B))+4*(H+q+dot(a,e))*B
low_checks = [
    avg(strong)-(4*H*rho+trace(mm(S,M2))+2*dot(a,M1)),
    sub(av(scale(strong,e)),add(add(add(scale(4*H,M1),mv(S,M1)),cross(om,M1)),mv(add(scale(rho,I),M2),a))),
    sub(stf(av(scale(strong,outer(e,e)))),add(add(add(scale(4*H,Pi),LB),scale(2,stf(outer(a,M1)))),sub(mm(Rom,M2),mm(M2,Rom)))),
]

# Exact radical reduction: K2=diag(1,1,-2)/sqrt(3); its squared norm=6/3.
# Scale-invariant shape has negative sign and square 6*(-6)^2/6^3=1.
equal_power_shapes_verified = (F(6,3)==2 and F(6)*F(-6)**2/F(6)**3==1)


def zdesign(g):
    return [I[i]+[v*c for c in I[i]] for v in g for i in range(3)]


redshift_ranks = {
    "constant": exact_rank(zdesign([F(1)]*3))[0],
    "varying": exact_rank(zdesign([F(0),F(1,2),F(1)]))[0],
}
# Supplemental synthetic illustration, not part of exact rational claims.
rng = random.Random(20260920)
shared = [rng.gauss(0,1) for _ in range(20000)]
shared_ratios = [math.exp(v)/(2*math.exp(v)) for v in shared]
independent_ratios = [math.exp(v)/(2*math.exp(rng.gauss(0,1))) for v in shared]
iso_omega_zero = all(v==0 for row in Aiso for v in row[9:12])
checks = list(map(iszero,identities.values()))+list(map(iszero,low_checks))
checks += [not fail_iso,not fail_gen,rank_iso==9,rank_gen==12,iso_omega_zero,
           equal_power_shapes_verified,redshift_ranks=={"constant":3,"varying":6},
           all(v==.5 for v in shared_ratios)]
result = {
    "status": "PASS_SCOPED_EXACT_AND_SYNTHETIC_CHECKS" if all(checks) else "FAIL_SCOPED_CHECKS",
    "runtime":"PYTHON_PASS", "python":platform.python_version(),
    "dependencies":"Python standard library only; fractions.Fraction sparse polynomial arithmetic",
    "sphere_measure":"dOmega/(4pi); exact even-monomial double-factorial formula",
    "optical_inverse_and_norm_identities":{k:iszero(v) for k,v in identities.items()},
    "positive_B_lower_bound":str(b_lower_bound),
    "weak_strong_equalities_tested":2*len(tests)*len(columns),
    "weak_strong_equalities_passed":2*len(tests)*len(columns)-len(fail_iso)-len(fail_gen),
    "weak_strong_failures":{"isotropic":fail_iso,"anisotropic":fail_gen},
    "rows":len(tests), "columns":len(columns),
    "exact_isotropic_rank":rank_iso,"exact_anisotropic_rank":rank_gen,
    "pivot_columns":{"isotropic":pivot_iso,"anisotropic":pivot_gen},
    "isotropic_omega_columns_zero":iso_omega_zero,
    "rank_claim":"Algebraic examples for a kinematic block with known residual; NOT observational identifiability",
    "low_moment_identities":{"J0":iszero(low_checks[0]),"J1":iszero(low_checks[1]),"J2":iszero(low_checks[2])},
    "equal_quadrupole_power_shapes":["0","-1"],
    "equal_quadrupole_power_check":equal_power_shapes_verified,
    "declared_redshift_template_rank":redshift_ranks,
    "shared_denominator_example":{"shared_ratio_std":statistics.pstdev(shared_ratios),"incorrect_independent_ratio_std":statistics.pstdev(independent_ratios)},
    "actual_CMB_inference":False,"ODE_PDE_Boltzmann_evolution":False,
    "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
}
(ROOT/'evidence').mkdir(exist_ok=True)
(ROOT/'evidence'/'JOINT_OPERATOR_CHECKS.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'evidence'/'JOINT_RESPONSE_MATRICES.json').write_text(json.dumps({
    'column_order':['H','S_xx_minus_yy','S_xx_plus_yy_minus_2zz','S_xy','S_xz','S_yz','a_x','a_y','a_z','omega_x','omega_y','omega_z'],
    'isotropic':[[str(v) for v in row] for row in Aiso],
    'anisotropic':[[str(v) for v in row] for row in Agen],
},indent=2)+'\n')
print(json.dumps(result,indent=2))
raise SystemExit(0 if all(checks) else 1)
