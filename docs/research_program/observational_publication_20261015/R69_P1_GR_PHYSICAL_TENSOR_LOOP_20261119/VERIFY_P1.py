"""Exploratory R69-P1 physical harmonic checks; unweighted actual CF4 positions only.

Not a source-calibrated physical likelihood or observational cosmology detection.
Run: OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B <this-file>
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from numpy.polynomial.legendre import leggauss, legval

RAW = Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
K = 5.0 / np.log(10.0)
E = np.array([
    np.diag([1, -1, 0]) / np.sqrt(2),
    np.diag([1, 1, -2]) / np.sqrt(6),
    np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]]) / np.sqrt(2),
    np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]]) / np.sqrt(2),
    np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]]) / np.sqrt(2),
])


def stf(a):
    return (a + a.T) / 2 - np.trace(a) * np.eye(3) / 3


def p4(n, s):
    sn = np.einsum("ni,ij,nj->n", n, s, n)
    return sn * sn - (4 / 7) * np.einsum("ni,ij,nj->n", n, stf(s @ s), n) - (2 / 15) * np.trace(s @ s)


def p3(n, d, s):
    dn = n @ d
    sn = np.einsum("ni,ij,nj->n", n, s, n)
    return dn * sn - (2 / 5) * n @ (s @ d)


def read_cf4():
    rows = []
    for line in RAW.open():
        try:
            dist = float(line[21:26])
            l = np.deg2rad(float(line[101:109]))
            b = np.deg2rad(float(line[110:118]))
            if dist > 0 and np.isfinite(dist + l + b):
                rows.append((dist, np.cos(l) * np.cos(b), np.sin(l) * np.cos(b), np.sin(b)))
        except (IndexError, ValueError):
            pass
    a = np.asarray(rows, float)
    assert a.shape == (38053, 4), a.shape
    return a


def geometry(a, low, high):
    a = a[(a[:, 0] >= low) & (a[:, 0] < high)]
    r, n = a[:, 0], a[:, 1:]
    angular = np.column_stack([np.ones(len(n)), n, np.einsum("ni,aij,nj->na", n, E, n)])
    radial = (100 / r)[:, None] * n
    x = np.column_stack([angular, radial])
    xn = x / np.linalg.norm(x, axis=0)[None, :]
    eig = np.linalg.eigvalsh(xn.T @ xn)
    rank = int(np.count_nonzero(eig > 1e-12 * eig[-1]))
    s = np.diag([-.01, -.01, .02])
    q = np.einsum("ni,ij,nj->n", n, s, n)
    template = .5 * K * p4(n, s)
    # Projection with l<=2 nuisance, no assumption of isotropic CF4 coverage.
    projected = template - angular @ np.linalg.solve(angular.T @ angular, angular.T @ template)
    jac = []
    for t in E:
        u = stf((s @ t + t @ s) / 2)
        qt = np.einsum("ni,ij,nj->n", n, t, n)
        jac.append(K * (q * qt - (4 / 7) * np.einsum("ni,ij,nj->n", n, u, n) -
                        (2 / 15) * np.trace(s @ t)))
    jac = np.column_stack(jac)
    jac -= angular @ np.linalg.solve(angular.T @ angular, angular.T @ jac)
    ej = np.linalg.eigvalsh(jac.T @ jac)
    assert rank == 12
    assert np.count_nonzero(ej > 1e-11 * ej[-1]) == 5
    return {
        "n": len(a), "rank_12": rank, "column_normalized_condition": float(np.sqrt(eig[-1] / eig[0])),
        "synthetic_l4_template_rms_mmag": float(np.sqrt(np.mean(template**2)) * 1000),
        "synthetic_l4_after_lower_multipole_projection_rms_mmag": float(np.sqrt(np.mean(projected**2)) * 1000),
        "synthetic_local_l4_jac_rank": 5,
        "synthetic_local_l4_jac_condition": float(np.sqrt(ej[-1] / ej[0])),
    }


def main():
    rng = np.random.default_rng(43)
    n = rng.normal(size=(12000, 3))
    n /= np.linalg.norm(n, axis=1)[:, None]
    s = np.diag([-.01, -.01, .02])
    d = np.array([.012, -.017, .02])
    u = n @ d + np.einsum("ni,ij,nj->n", n, s, n)
    m0 = np.dot(d, d) / 3 + 2 * np.trace(s @ s) / 15
    m1 = (4 / 5) * n @ (s @ d)
    m2 = np.einsum("ni,ij,nj->n", n, stf(np.outer(d, d)) + (4 / 7) * stf(s @ s), n)
    m3, m4 = 2 * p3(n, d, s), p4(n, s)
    residual = float(np.max(np.abs(u**2 - (m0 + m1 + m2 + m3 + m4))))
    assert residual < 2e-15
    assert np.allclose(p4(n, s), p4(n, -s), atol=1e-15)
    nodes, w = leggauss(500)
    def legendre_c(y, ell):
        return (2 * ell + 1) / 2 * float(np.dot(w * y, legval(nodes, [0] * ell + [1])))
    ax = []
    for coeff in [.01, .03, .1]:
        truth = legendre_c(-K * np.log1p(coeff * (nodes**2 - 1 / 3)), 4)
        pred = (4 * K / 35) * coeff**2
        ax.append({"s": coeff, "predicted_l4_mmag": pred*1000, "exact_l4_mmag": truth*1000})
        assert abs(truth - pred) < 6e-5
    a = read_cf4()
    out = {"source": str(RAW), "source_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
           "total_groups": len(a), "quadratic_harmonic_max_residual": residual,
           "axisymmetric_l4": ax,
           "40_400_Mpc": geometry(a,40,400),
           "80_220_Mpc": geometry(a,80,220),
           "scope": "ACTUAL survey direction/radius geometry with SYNTHETIC signal, NO physical shear estimate or p-value"}
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    main()
