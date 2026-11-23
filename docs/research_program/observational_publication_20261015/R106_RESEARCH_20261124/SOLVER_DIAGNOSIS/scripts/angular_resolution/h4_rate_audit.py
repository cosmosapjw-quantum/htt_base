"""R106 H4 structural audit: Galerkin sky moment rates vs the exact radiation conservation law.

For a fixed bolometric Stokes state Theta (I proportional to 1+4 Theta, photon momentum -n)
and a fixed VI_-1/9 geometry, the repo photon cell integrates
    dTheta/dN = (M_Lie + M_bolo) Theta - P[n.sigma_N.n] + kappa (C Theta + e).
With R = int (1+4 Theta) k k dOmega, k = (1,-n), its zeroth-row moment rate is
    G^{0b} = -4 R^{0b} + int 4 (dTheta/dN) k^0 k^b dOmega.
The fluid ODE integrates the exact law
    dR^{0b}/dN = -(Gamma^a_{ca} R^{cb} + Gamma^b_{ca} R^{ac})/H + kappa F^b(R, v_b).
The geometric and collision parts are compared separately and as d(q/E)/dN.
Any nonzero difference beyond roundoff would be an angular-discretization source of the
sky/fluid dipole mismatch (H4). States carry random ell<=L content so that truncation
coupling through ell>=3 would show up if present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from bass.background.convention_bridge import build_structure_tensor_with_sign
from bass.background.geometry import pstf_rank2
from bass.background.tilted_bianchi_state import build_4d_bianchi_connection
from bass.transport import coupled_einstein_boltzmann as live
from bass.transport.general_lie_stokes import (
    GeneralLieStokesOperator, LieGeometry, stokes_maps_to_vector, vector_to_stokes_maps,
)
from bass.transport.moving_collision_stage import MovingCollisionStage, initial_radiation_stokes
from bass.collision.moving_thomson import covariant_thomson_four_force

HERE = Path(__file__).resolve().parent


def moment_tensor(op, vec, *, affine):
    """int (affine + 4 x) k k dOmega on the operator's own exact GL grid."""
    sky = vector_to_stokes_maps(np.asarray(vec), op.idx, L=op.L, n_gl_theta=op.n_gl_theta)
    I = sky[..., 0].real.ravel()
    n = op._grid[2].reshape(-1, 3)
    w = op._grid[3].ravel() * ((1.0 if affine else 0.0) + 4.0 * I)
    k4 = np.column_stack([np.ones(len(n)), -n])
    return np.einsum("n,ni,nj->ij", w, k4, k4)


def random_real_state(op, rng, amp):
    shape = (*op._grid[0].shape, 4)
    return stokes_maps_to_vector(amp * rng.standard_normal(shape), op.idx, op.dim, L=op.L, n_gl_theta=op.n_gl_theta)


def audit(op, geom_scale, beta_scale, seed, moving_cls=MovingCollisionStage):
    st, _, _ = live.build_early_family_state("VI_-1/9", epsilon=2e-4, curvature=3e-4)
    H = float(st.H)
    sig = geom_scale * np.asarray(st.sigma_ab, dtype=float)
    a = geom_scale * np.asarray(st.algebra.a, dtype=float)
    nmat = geom_scale * np.asarray(st.algebra.n, dtype=float)
    sigN, aN, nN = pstf_rank2(sig / H), a / H, nmat / H
    geom = LieGeometry(sigN, aN, nN)
    C = build_structure_tensor_with_sign(a, nmat, a_sign=1)
    Gamma4 = build_4d_bianchi_connection(H, sig, C)
    rng = np.random.default_rng(seed)
    v_r = 1e-5 * np.array([1.0, -0.5, 0.25]) * 2.0
    theta = initial_radiation_stokes(op, v_r) + random_real_state(op, rng, 1e-3)
    beta = beta_scale * np.array([0.7, -0.4, 0.3])
    R = moment_tensor(op, theta, affine=True)
    # Geometric part
    rate_g = (op.base_operator(geom) + op.bolometric_redshift_operator(geom)) @ theta \
        + op.shear_source_vector(sigN, amplitude=1.0)
    G_g = -4.0 * R[0] + moment_tensor(op, rate_g, affine=False)[0]
    E_g = -(np.einsum("aca,cb->b", Gamma4, R) + np.einsum("bca,ac->b", Gamma4, R)) / H
    # Collision part per unit conserved-anchor depth
    mv = moving_cls(op, beta)
    rate_c = mv.apply(theta) + mv.emission
    G_c = moment_tensor(op, rate_c, affine=False)[0]
    E_c = covariant_thomson_four_force(R, beta, clock="conserved_anchor")

    def q_over_E_rate(T0, dT0):
        return (dT0[1:] - (T0[1:] / T0[0]) * dT0[0]) / T0[0]

    out = {"L": op.L, "rings": op.n_gl_theta, "geom_scale": geom_scale, "beta": beta.tolist(), "seed": seed,
           "R00": float(R[0, 0]), "q_over_E": (R[0, 1:] / R[0, 0]).tolist()}
    for name, G, E in (("geometric", G_g, E_g), ("collision", G_c, E_c)):
        dqE_G, dqE_E = q_over_E_rate(R[0], G), q_over_E_rate(R[0], E)
        out[name] = {
            "galerkin_dT0": G.tolist(), "exact_dT0": E.tolist(),
            "abs_diff_dT0": float(np.max(np.abs(G - E))),
            "scale_dT0": float(np.max(np.abs(E))),
            "dqE_galerkin": dqE_G.tolist(), "dqE_exact": dqE_E.tolist(),
            "dqE_abs_diff": float(np.max(np.abs(dqE_G - dqE_E))),
            "dqE_rel_diff": float(np.max(np.abs(dqE_G - dqE_E)) / max(np.max(np.abs(dqE_E)), 1e-300)),
        }
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("r106_h4_moving_hiquad", HERE / "variant/moving_collision_stage_hiquad.py")
    hq = importlib.util.module_from_spec(spec); sys.modules[spec.name] = hq; spec.loader.exec_module(hq)
    hq.RINGS = 64
    rows = []
    cases = [(4, 16), (6, 16), (8, 16), (4, 24), (4, 32), (4, 64), (12, 20)]
    for L, rings in cases:
        op = GeneralLieStokesOperator(L, n_gl_theta=rings)
        for gscale in (1.0, 1e3):
            for bscale in (1.5e-5, 1e-2):
                rows.append(audit(op, gscale, bscale, seed=L * 100 + rings))
        if (L, rings) == (4, 16):
            for bscale in (1.5e-5, 1e-2):
                r = audit(op, 1.0, bscale, seed=416, moving_cls=hq.MovingCollisionStage)
                r["moving_kernel_rings"] = 64
                rows.append(r)
    payload = {"schema": "htt.r106.h4_rate_audit.1",
               "sha256": {"driver": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                          "repo_solver": hashlib.sha256(Path(live.__file__).read_bytes()).hexdigest()},
               "rows": rows}
    args.output.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")
    for r in rows:
        g, c = r["geometric"], r["collision"]
        print(f"L={r['L']:2d} rings={r['rings']:2d} kr={r.get('moving_kernel_rings', r['rings']):2d} "
              f"gs={r['geom_scale']:.0e} |b|={np.linalg.norm(r['beta']):.1e}  "
              f"geom dT0 diff/scale={g['abs_diff_dT0']:.3e}/{g['scale_dT0']:.3e} dqE rel={g['dqE_rel_diff']:.3e} | "
              f"coll dT0 diff/scale={c['abs_diff_dT0']:.3e}/{c['scale_dT0']:.3e} dqE rel={c['dqE_rel_diff']:.3e}")


if __name__ == "__main__":
    main()
