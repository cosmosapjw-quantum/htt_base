"""L1 oracle for the R47/R48 Bianchi-I endpoint temperature map
   T(n)/Tbar = [n^T exp(-2B) n]^(-1/2),  B symmetric trace-free.
SYNTHETIC checks only (no Planck data). Run: python3 L1_bianchi_I_endpoint_oracle.py  (needs scipy>=1.15 for sph_harm_y, healpy, sympy)
Independent of the repo's own implementation (self-contained)."""
import json, math, warnings
import numpy as np, sympy as sp
from scipy.linalg import expm
from scipy.special import sph_harm_y
warnings.filterwarnings("ignore")
rng = np.random.default_rng(20261110)
out = {}

def Tmap(B, n):                       # n: (...,3)
    E = expm(-2.0 * B)
    return np.einsum("...i,ij,...j->...", n, E, n) ** -0.5

def gl_sphere(N):
    x, w = np.polynomial.legendre.leggauss(N)
    th = np.arccos(x); ph = np.arange(2 * N) * (2 * np.pi / (2 * N))
    TH, PH = np.meshgrid(th, ph, indexing="ij")
    W = np.outer(w, np.full(2 * N, 2 * np.pi / (2 * N)))
    n = np.stack([np.sin(TH) * np.cos(PH), np.sin(TH) * np.sin(PH), np.cos(TH)], -1)
    return TH, PH, n, W

def randB(scale):
    A = rng.normal(size=(3, 3)); A = 0.5 * (A + A.T); A -= np.trace(A) / 3 * np.eye(3)
    return scale * A / np.linalg.norm(A)

# 1. direct derivation check of the map from conserved covariant momentum (algebra, numeric):
#    E*^2 = g^{ij} p_i p_j, g^{ij}=a^-2 exp(-2B)  =>  T_obs = T* E0/E* = a* T* [n^T e^{-2B} n]^(-1/2)
B0 = randB(0.1); n0 = rng.normal(size=3); n0 /= np.linalg.norm(n0); a_s = 1 / 1090.0
Estar = math.sqrt((1 / a_s**2) * n0 @ expm(-2 * B0) @ n0)
out["derivation_numeric_T_over_Tbar_err"] = float(abs(1.0 / (a_s * Estar) - Tmap(B0, n0)))

# 2. CAS: series coefficients of (1+x)^(-1/2), x = n^T e^{-2B} n - 1, in u_k = n^T B^k n (weight k)
e = sp.symbols("e"); u1, u2, u3 = sp.symbols("u1 u2 u3")
x = -2 * e * u1 + 2 * e**2 * u2 - sp.Rational(4, 3) * e**3 * u3        # n^T e^{-2eB} n - 1
ser = sp.series((1 + x) ** sp.Rational(-1, 2), e, 0, 4).removeO()
cas = sp.expand(ser.subs(e, 1))
claimed = u1 - u2 + sp.Rational(3, 2) * u1**2 + sp.Rational(2, 3) * u3 - 3 * u1 * u2 + sp.Rational(5, 2) * u1**3
out["cas_series_of_T_over_Tbar_minus_1_matches_claimed_through_O(B^3)"] = bool(sp.simplify(cas - 1 - claimed) == 0)

# 3. sphere moments for traceless B (CAS-free exact tensor contraction vs GL quadrature)
_, _, n, W = gl_sphere(64)
B = randB(0.3); tr = lambda k: float(np.trace(np.linalg.matrix_power(B, k)))
u = lambda k: np.einsum("...i,ij,...j->...", n, np.linalg.matrix_power(B, k), n)
avg = lambda f: float((f * W).sum() / (4 * np.pi))
mom = {"<u1>": (avg(u(1)), 0.0), "<u2>": (avg(u(2)), tr(2) / 3), "<u1^2>": (avg(u(1)**2), 2 * tr(2) / 15),
       "<u3>": (avg(u(3)), tr(3) / 3), "<u1u2>": (avg(u(1) * u(2)), 2 * tr(3) / 15), "<u1^3>": (avg(u(1)**3), 8 * tr(3) / 105)}
out["sphere_moments_max_abs_err"] = float(max(abs(a - b) for a, b in mom.values()))

# 4. monopole expansion and error scaling
B1 = randB(1.0); rows = []
for eps in (0.2, 0.1, 0.05, 0.025):
    Be = eps * B1; m = avg(Tmap(Be, n)) - 1.0
    c2 = -2 / 15 * np.trace(Be @ Be); c3 = 4 / 315 * np.trace(Be @ Be @ Be)
    rows.append((eps, m - c2, m - c2 - c3))
out["monopole_resid_after_2nd_order"] = [[r[0], float(r[1])] for r in rows]
out["monopole_resid_after_3rd_order"] = [[r[0], float(r[2])] for r in rows]
out["monopole_resid_3rd_order_scaling_ratio_expect_16"] = [float(rows[i][2] / rows[i + 1][2]) for i in range(3)]

# 5. parity: odd multipoles vanish; ell content scaling a_l ~ eps^ceil(l/2)
TH, PH, n, W = gl_sphere(96)
def alm_power(Bm, lmax=8):
    T = Tmap(Bm, n) - 1.0; P = {}
    for l in range(1, lmax + 1):
        s = 0.0
        for m in range(-l, l + 1):
            Y = sph_harm_y(l, m, TH, PH)
            s += abs((T * np.conj(Y) * W).sum()) ** 2
        P[l] = math.sqrt(s)
    return P
P1 = alm_power(0.1 * B1); P2 = alm_power(0.05 * B1)
out["odd_ell_amplitude_max"] = float(max(P1[l] for l in (1, 3, 5, 7)))
out["even_ell_amplitude_eps0.1"] = {str(l): float(P1[l]) for l in (2, 4, 6, 8)}
out["even_ell_scaling_ratio_eps_halved_vs_expected"] = {str(l): [float(P1[l] / P2[l]), 2 ** math.ceil(l / 2)] for l in (2, 4, 6, 8)}

# 6. rotation covariance (exact) and rotation invariance of C_l
Q, _ = np.linalg.qr(rng.normal(size=(3, 3))); Q *= np.sign(np.linalg.det(Q))
nn = rng.normal(size=(500, 3)); nn /= np.linalg.norm(nn, axis=1)[:, None]
out["rotation_pointwise_T_QBQT(Qn)_minus_T_B(n)_max"] = float(np.max(np.abs(Tmap(Q @ B1 @ Q.T, nn @ Q.T) - Tmap(B1, nn))))
Pr = alm_power(0.1 * (Q @ B1 @ Q.T))
out["rotation_Cl_invariance_max_rel"] = float(max(abs(Pr[l] - P1[l]) / P1[l] for l in (2, 4, 6, 8)))
out["parity_T_n_equals_T_minus_n_max"] = float(np.max(np.abs(Tmap(B1, nn) - Tmap(B1, -nn))))

# 7. quadrature convergence of a_2m power and monopole
ref = None; conv = []
for N in (8, 12, 16, 24, 32, 64, 128):
    TH_, PH_, n_, W_ = gl_sphere(N); T_ = Tmap(0.3 * B1, n_) - 1.0
    s = 0.0
    for m in range(-2, 3):
        s += abs((T_ * np.conj(sph_harm_y(2, m, TH_, PH_)) * W_).sum()) ** 2
    conv.append((N, math.sqrt(s), float((T_ * W_).sum() / (4 * np.pi))))
ref = conv[-1]
out["quadrature_convergence_B=0.3"] = [[c[0], float(abs(c[1] - ref[1]) / ref[1]), float(abs(c[2] - ref[2]))] for c in conv[:-1]]

# 8. adversarial limits
lam, V = np.linalg.eigh(0.8 * B1)
out["eigenvector_exactness_T_equals_exp(lambda)_max_err"] = float(max(abs(Tmap(0.8 * B1, V[:, i]) - math.exp(lam[i])) for i in range(3)))
big = 1.5 * B1; Tb = Tmap(big, n)
out["positivity_and_range_large_B"] = {"min_T": float(Tb.min()), "max_T": float(Tb.max()),
        "exp_lambda_min": float(math.exp(np.linalg.eigvalsh(big)[0])), "exp_lambda_max": float(math.exp(np.linalg.eigvalsh(big)[-1]))}
out["zero_B_limit_max_dev"] = float(np.max(np.abs(Tmap(np.zeros((3, 3)), nn) - 1)))
Bs = 1e-4 * B1; lin = nn @ np.zeros(3)
out["small_B_leading_order_err_vs_u1"] = float(np.max(np.abs(Tmap(Bs, nn) - 1 - np.einsum("ki,ij,kj->k", nn, Bs, nn))))

# 9. pixel-vs-harmonic oracle with healpy (C_l from pixel map via anafast vs GL-quadrature C_l)
import healpy as hp
Bp = 0.1 * B1; Cl_q = {}
TH, PH, n, W = gl_sphere(128); Tq = Tmap(Bp, n) - 1.0
for l in range(0, 9):
    s = sum(abs((Tq * np.conj(sph_harm_y(l, m, TH, PH)) * W).sum()) ** 2 for m in range(-l, l + 1))
    Cl_q[l] = s / (2 * l + 1)
pix = []
for nside in (16, 32, 64, 128):
    v = hp.pix2vec(nside, np.arange(hp.nside2npix(nside)))
    mp = Tmap(Bp, np.stack(v, -1)) - 1.0
    cl = hp.anafast(mp, lmax=8, iter=3, use_pixel_weights=False)
    pix.append((nside, [float(abs(cl[l] - Cl_q[l]) / Cl_q[l]) for l in (2, 4, 6, 8)]))
out["pixel_vs_harmonic_rel_err_Cl_l=2,4,6,8"] = {str(k): v for k, v in pix}
import scipy, healpy
out["versions"] = {"numpy": np.__version__, "scipy": scipy.__version__, "sympy": sp.__version__, "healpy": healpy.__version__}
out["scope"] = "SYNTHETIC full-sky noiseless map; no mask/beam/noise/foreground; temperature only"
print(json.dumps(out, indent=1))
