"""Exact independent algebra-falsifier bodies executed in checks.log.

Saved after execution for reproducibility; no extra execution occurred on saving.
Standard library only. No data acquisition, integration, ODE, or old campaign.
"""
import math

# Exact boosted stress-energy tensor, differentiated about zero amplitude.
em, er = 0.9999, 0.0001
R = 3 * em / (4 * er)
b = [.2, -.3, .4]
step = 1e-8
for a in [.01, .2, 1.]:
    def T(amp):
        out = [[0.] * 4 for _ in range(4)]
        for e, w, beta in [
            (em / a**3, 0, [amp*x/a for x in b]),
            (er / a**4, 1/3, [-amp*R*x for x in b]),
        ]:
            gamma = 1 / math.sqrt(1 - sum(x*x for x in beta))
            U = [gamma] + [gamma*x for x in beta]
            for i in range(4):
                for j in range(4):
                    out[i][j] += e*(1+w)*U[i]*U[j] + (
                        e*w*(-1 if i == 0 else 1) if i == j else 0)
        return out
    plus, minus = T(step), T(-step)
    linear = max(abs((plus[i][j]-minus[i][j])/(2*step))
                 for i in range(4) for j in range(4))
    assert linear/(em/a**3+4*er/(3*a**4)) < 1e-5, (a, linear)
print('Independent exact stress-energy centered derivative: total linear perturbation vanishes under compensation (three scale factors).')

# Einstein-de Sitter formal limit, independent of candidate's two-fluid formula.
for z in [1e-3, .03, .5, 2]:
    y = 1+z
    A = y/(2*y**1.5*(1-y**-.5))
    history = y-z*A
    ratio = 2*y**1.5-3*y+1
    assert abs(history/A-ratio) < 1e-12
    dz = 1e-5*z
    ff = lambda x: 2*(1+x)**1.5-3*(1+x)+1
    fd = (ff(z+dz)-ff(z-dz))/(2*dz)
    assert abs(fd-(3*math.sqrt(y)-3)) < 2e-7
print('Independent EdS endpoint/kernel ratio and derivative check passed (formal limit only).')

# Source-model redshift inversion solved as a quadratic, not with the candidate K.
c = 299792.458
u0, gradient, k, z0 = 120., 20000., .7, .04
zobs = (1+z0)*(1+(u0+gradient*z0)/c)-1

def zsolve(amplitude):
    B = gradient+amplitude*k
    C = c+u0+amplitude+B
    constant = c+u0+amplitude-c*(1+zobs)
    return -2*constant/(C+math.sqrt(C*C-4*B*constant))

def mu(amplitude):
    z = zsolve(amplitude)
    return 5*math.log10((1+z)*c/70*z)+25

D = c+u0+gradient*z0+(1+z0)*gradient
expected = -5/math.log(10)*(1+(1+z0)/z0)*(1+k*z0)/D
measured = (mu(.01)-mu(-.01))/.02
frozen = -5/math.log(10)*(1+(1+z0)/z0)*(1+k*z0)/(c+u0+gradient*z0)
assert abs(measured-expected) < 1e-10
assert abs(frozen-expected)/abs(expected) > .05
print('Independent quadratic distance-root differentiation passed; dropping radial gradient produces >5% error in this finite witness.')
