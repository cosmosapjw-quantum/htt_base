"""Independent finite SymPy checks for G03-C exact canonical boost map.

The rational identities are checked on gamma > 0, q < 1, gamma + 1 != 0,
with gamma**2*(1-q)=1 and a*(gamma+1)=gamma**2. The real square-root
branch implications are separately stated in the output.
"""
import sys
import sympy as sp


def eq(name, expression):
    residue = sp.cancel(sp.together(expression))
    if residue != 0:
        raise AssertionError(f"{name}: {residue}")
    print(f"PASS {name}: exact zero")


def main():
    print("Python:", sys.version.replace("\n", " "))
    print("SymPy:", sp.__version__)
    b = sp.Matrix(sp.symbols("b0:3", real=True))
    n = sp.Matrix(sp.symbols("n0:3", real=True))
    d00, d11, d22, d01, d02, d12 = sp.symbols(
        "d00 d11 d22 d01 d02 d12", real=True
    )
    D = sp.Matrix([[d00, d01, d02], [d01, d11, d12], [d02, d12, d22]])
    g, a, q = sp.symbols("gamma a q", real=True)
    q_beta = (b.T * b)[0]
    s = (b.T * D * b)[0]
    L = sp.eye(3) + a * b * b.T
    boost = sp.BlockMatrix([[sp.Matrix([[g]]), g*b.T], [g*b, L]]).as_explicit()
    eta = sp.diag(-1, 1, 1, 1)
    restB = sp.diag(0, 0, 0, 0)
    restB[1:4, 1:4] = D

    # Finite matrix expansion, with q merely a shorthand for beta.beta.
    lorentz = boost.T * eta * boost - eta
    eq("Lorentz 00 coefficient", lorentz[0, 0]
       - (1 - g**2 * (1-q_beta)))
    for i in range(3):
        eq(f"Lorentz 0{i+1} coefficient", lorentz[0, i+1]
           - g*b[i]*(-g + 1 + a*q_beta))
        for j in range(3):
            eq(f"Lorentz {i+1}{j+1} coefficient", lorentz[i+1, j+1]
               - b[i]*b[j]*(-g**2 + 2*a + a**2*q_beta))

    # Check coefficient vanishing in the quotient of the two rational
    # normalization relations, without numerical substitution.
    aq = g-1
    a_from_gamma = g**2/(g+1)
    q_from_gamma = 1-1/g**2
    eq("a*q=gamma-1", (a_from_gamma*q_from_gamma - aq))
    eq("Lorentz 00 normalized", 1-g**2*(1-q_from_gamma))
    eq("Lorentz 0i normalized", -g+1+a_from_gamma*q_from_gamma)
    eq("Lorentz ij normalized", -g**2+2*a_from_gamma+a_from_gamma**2*q_from_gamma)

    # Positive real branch: t=sqrt(1-q)>0, gamma=1/t,
    # a=gamma^2/(gamma+1). Here q=1-t^2 with t>0.
    t = sp.symbols("t", positive=True)
    gt = 1/t
    at = gt**2/(gt+1)
    eq("positive square-root branch gamma^2(1-q)=1", gt**2*(1-(1-t**2))-1)
    eq("positive branch a*q=gamma-1", at*(1-t**2)-(gt-1))
    print("DOMAIN q=beta.beta>=0 and q<1 implies t=sqrt(1-q)>0, gamma=1/t>0, gamma+1>0")

    null = sp.Matrix([-1, *n])
    redshift = -(boost*null)[0]
    eq("redshift sign", redshift-g*(1-(b.T*n)[0]))
    print("DOMAIN n.n=1 for observer-null interpretation; identity is algebraic for all n")

    boostedB = boost.T*restB*boost
    for i in range(3):
        eq(f"symmetric D transformed B0{i+1}", boostedB[0, i+1]
           - g*((D*b)[i]+a*b[i]*s))
        eq(f"dipoleMap component {i}", -2*boostedB[0, i+1]
           + 2*g*((D*b)[i]+a*b[i]*s))
    print("SCOPE fixed real symmetric D, restB=diag(0,D), A(p)=0; exact finite event map")


if __name__ == "__main__":
    main()
