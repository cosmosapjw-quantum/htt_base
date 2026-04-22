
import json
from pathlib import Path
import sympy as sp

OUT = {}

def simplify_zero(expr):
    return sp.simplify(sp.factor(sp.expand(expr)))

def derive_classB_maps():
    q, h, p = sp.symbols('q h p', real=True)
    a = sp.symbols('a', positive=True, real=True)
    # VI_h: h = a^2/(1 * -1) = -a^2 and q = (1-a)/(1+a)
    q_expr = (1 - a)/(1 + a)
    h_expr = -a**2
    h_of_q = simplify_zero(h_expr.subs(a, (1-q)/(1+q)) + ((1-q)/(1+q))**2)
    q_of_h = simplify_zero(q - (1-sp.sqrt(-h))/(1+sp.sqrt(-h)))
    compose_1 = simplify_zero((-((1-q_expr)/(1+q_expr))**2) - h_expr)
    compose_2 = simplify_zero(((1-sp.sqrt(-(-a**2)))/(1+sp.sqrt(-(-a**2)))) - q_expr)

    # VII_h: h = p^2
    vii_direct = simplify_zero(p**2 - p**2)

    OUT["classB"] = {
        "VI_h_compose_q_to_h": str(compose_1),
        "VI_h_compose_h_to_q": str(sp.simplify(compose_2)),
        "VII_h_identity": str(vii_direct),
        "TypeIII_branch_h": str(sp.simplify((-((1-sp.Integer(0))/(1+sp.Integer(0)))**2))),
        "VI0_limit_h": str(sp.simplify(-((1-sp.Integer(1))/(1+sp.Integer(1)))**2)),
    }

def derive_typeVIII_reductions():
    s, mu, lam = sp.symbols('s mu lam', real=True)
    rho = (sp.Integer(1)/(2*sp.pi)**2) * s*sp.sinh(2*sp.pi*s)/(sp.cosh(2*sp.pi*s)+sp.cos(2*sp.pi*mu))
    rho0 = sp.simplify(sp.together(rho.subs(mu, 0)))
    rho_half = sp.simplify(sp.together(rho.subs(mu, sp.Rational(1,2))))
    target0 = (sp.Integer(1)/(2*sp.pi)**2) * s * sp.tanh(sp.pi*s)
    target_half = (sp.Integer(1)/(2*sp.pi)**2) * s * sp.coth(sp.pi*s)

    OUT["typeVIII"] = {
        "mu_even_reduction": str(sp.simplify(rho0 - target0)),
        "mu_odd_reduction": str(sp.simplify(rho_half - target_half)),
        "mu_parity_evenness": str(sp.simplify(rho.subs(mu, -mu) - rho)),
        "disc_threshold": str(sp.simplify(((sp.Integer(1)/(2*sp.pi)**2) * (lam-sp.Rational(1,2))).subs(lam, sp.Rational(1,2)))),
    }

def derive_healpix_index():
    ell, m, lmax = sp.symbols('ell m lmax', integer=True, nonnegative=True)
    j = sp.symbols('j', integer=True, nonnegative=True)
    block_offset = sp.summation(lmax - j + 1, (j, 0, m-1))
    block_offset = sp.simplify(block_offset)
    packed = sp.simplify(m*(2*lmax + 1 - m)/2 + ell)
    expected = sp.simplify(block_offset + (ell - m))
    diff = sp.simplify(expected - packed)
    total = sp.summation(lmax - m + 1, (m, 0, lmax))
    OUT["healpix"] = {
        "offset_difference": str(diff),
        "total_coeffs_minus_triangle": str(sp.simplify(total - (lmax+1)*(lmax+2)/2)),
    }

def derive_fd4_weights():
    h = sp.symbols('h', nonzero=True)
    x = sp.symbols('x')
    offsets = [-2, -1, 1, 2]
    a,b,c,d = sp.symbols('a b c d')
    coeffs = [a,b,c,d]
    eqs = []
    # exactness for monomials 1,x,x^2,x^3 at x=0
    for n in range(4):
        poly = x**n
        lhs = sum(coeffs[j] * poly.subs(x, offsets[j]*h) for j in range(4))
        rhs = sp.diff(poly, x).subs(x,0)
        eqs.append(sp.Eq(lhs, rhs))
    sol = sp.solve(eqs, [a,b,c,d], dict=True)[0]
    d1 = [sp.simplify(sol[v]) for v in [a,b,c,d]]

    a,b,c,d,e = sp.symbols('a b c d e')
    coeffs2 = [a,b,c,d,e]
    offsets2 = [-2,-1,0,1,2]
    eqs2 = []
    for n in range(5):
        poly = x**n
        lhs = sum(coeffs2[j] * poly.subs(x, offsets2[j]*h) for j in range(5))
        rhs = sp.diff(poly, x, 2).subs(x,0)
        eqs2.append(sp.Eq(lhs, rhs))
    sol2 = sp.solve(eqs2, [a,b,c,d,e], dict=True)[0]
    d2 = [sp.simplify(sol2[v]) for v in [a,b,c,d,e]]

    OUT["fd4"] = {
        "d1_weights": [str(sp.simplify(w)) for w in d1],
        "d2_weights": [str(sp.simplify(w)) for w in d2],
    }

def derive_vi_negative_density_positivity():
    q, k = sp.symbols('q k', real=True)
    dens = sp.cos(k)**2 - q*sp.sin(k)**2
    # substitute q=-u, u>0
    u = sp.symbols('u', positive=True, real=True)
    dens_u = sp.simplify(dens.subs(q, -u))
    OUT["vi_negative_density"] = {
        "rewritten": str(dens_u),
    }

def main():
    derive_classB_maps()
    derive_typeVIII_reductions()
    derive_healpix_index()
    derive_fd4_weights()
    derive_vi_negative_density_positivity()

    outpath = Path(__file__).with_name("symbolic_results.json")
    outpath.write_text(json.dumps(OUT, indent=2))
    print(json.dumps(OUT, indent=2))

if __name__ == "__main__":
    main()
