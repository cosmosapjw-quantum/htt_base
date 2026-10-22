"""Ancillary exact check of G16-A normalization constants (not a Lean target, not the sympy axis verdict)."""
import sympy as sp
pi, G = sp.pi, sp.symbols('Gamma', nonnegative=True)
mass = 3 * (sp.Rational(4, 3) * pi)                       # dim * vol(B^3) = toSphere univ
c = sp.Rational(3, 8) / pi                                 # gain coefficient 3/(8 pi)
th, ph = sp.symbols('theta phi')
area = sp.integrate(sp.integrate(sp.sin(th), (th, 0, pi)), (ph, 0, 2 * pi))
gain = sp.simplify(c * sp.sqrt(mass) * sp.sqrt(mass))      # sqrt(m) * |c| * sqrt(m)
full = sp.simplify(G * (1 + gain))
gain_norm = sp.simplify(sp.Rational(3, 2) * 1)            # normalized measure: c=3/2, mass=1
coeff_eq = sp.simplify(sp.Rational(3, 2) / (4 * pi) - c)  # normalized operator identity
print({"mass": str(mass), "polar_area": str(area), "gain": str(gain), "full": str(full),
       "gain_normalized": str(gain_norm), "operator_identity_residual": str(coeff_eq), "sympy": sp.__version__})
assert sp.simplify(mass - 4 * pi) == 0 and sp.simplify(area - 4 * pi) == 0
assert gain == sp.Rational(3, 2) and sp.simplify(full - sp.Rational(5, 2) * G) == 0 and coeff_eq == 0
