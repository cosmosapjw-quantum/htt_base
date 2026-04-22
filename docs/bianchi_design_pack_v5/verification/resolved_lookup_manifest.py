
"""
Frozen lookup manifest for the low-ell Bianchi v5 design pack.

This file is intentionally code-readable and documentation-friendly.
It contains only formulas and metadata that the symbolic and numerical
verification scripts are allowed to consume.
"""

FROZEN = {
    "classB": {
        "h_definition": "h = a**2 / (n2*n3)",
        "VI_h_canonical_gauge": {"n1": 0, "n2": 1, "n3": -1, "a": "sqrt(-h)"},
        "VII_h_canonical_gauge": {"n1": 0, "n2": 1, "n3": 1, "a": "sqrt(h)"},
        "VI_h_q_to_h": "h = -((1-q)/(1+q))**2",
        "VI_h_h_to_q": "q = (1-sqrt(-h))/(1+sqrt(-h))",
        "VII_h_p_to_h": "h = p**2",
        "VII_h_h_to_p": "p = sqrt(h)",
    },
    "plancherel": {
        "II": {
            "K": "R\\{0}",
            "k0": "(0,k)",
            "rho": "Abs(k)",
            "nudot": "Abs(k)",
        },
        "III": {
            "K": "R x {±1}",
            "k0": "(k2,k1)",
            "rho": "exp(-r)",
            "nudot": "1",
        },
        "IV": {
            "K": "R_+ x {±1}",
            "k0": "(k2, k2*k1)",
            "rho": "exp(-2*r)*(1+k1)",
            "nudot": "1+k1",
        },
        "VI0": {
            "K": "R_+ x Z4",
            "k0": "R_pi/2^k2 (1,k1)",
            "nudot": "1",
        },
        "VIh_q_positive": {
            "K": "R_+ x Z4",
            "k0": "R_pi/2^k2 (1,k1)",
            "nudot": "q**(k2 mod 2)",
        },
        "VIh_q_negative": {
            "K": "S1",
            "k0": "(cos(k), sin(k))",
            "nudot": "cos(k)**2 - q*sin(k)**2",
        },
        "VIIh": {
            "K": "(-exp(pi*p),-1] U [1,exp(pi*p))",
            "k0": "(k,0)",
            "rho": "exp(-2*p*r)*Abs(k)",
            "nudot": "Abs(k)",
        },
        "VIII_cont": {
            "labels": "(mu,s), -1/2 <= mu < 1/2, s>=0",
            "measure": "(2*pi)**(-2) * s*sinh(2*pi*s)/(cosh(2*pi*s)+cos(2*pi*mu))",
        },
        "VIII_disc": {
            "labels": "D_lambda^±, lambda>=1/2",
            "measure": "(2*pi)**(-2) * (lam - 1/2)",
        },
    },
    "solvable_scalar_ode": {
        "equation": (
            "h33*Pzz + I*(kC.T*F*(hcol3+h3row.T))*Pz "
            "- (lam + kC.T*F*h22*F.T*kC - I*h3row*F.T*M.T*kC)*P"
        ),
        "shift_rule": "P_{lam,k,r}(z) = P_{lam,k}(z-r)",
    },
    "fd4": {
        "weights": {"w0": "h/2", "wi": "h", "wN": "h/2"},
        "d1": "(f[i-2]-8*f[i-1]+8*f[i+1]-f[i+2])/(12*h)",
        "d2": "(-f[i-2]+16*f[i-1]-30*f[i]+16*f[i+1]-f[i+2])/(12*h**2)",
        "bcl": "(-3*f0+4*f1-f2)/(2*h)",
        "bcr": "(3*fN-4*fN1+fN2)/(2*h)",
    },
    "healpix": {
        "index": "idx(l,m,lmax) = m*(2*lmax+1-m)/2 + l",
        "ordering": "m-major",
    },
    "hyrec_adapter": {
        "nH": "(1-Y_He)*rho_b/m_H",
        "ne": "xe*nH",
        "kappa_dot": "a*ne*sigma_T*c",
        "tau_prime": "-kappa_dot",
        "g": "kappa_dot*exp(-tau)",
    },
}
