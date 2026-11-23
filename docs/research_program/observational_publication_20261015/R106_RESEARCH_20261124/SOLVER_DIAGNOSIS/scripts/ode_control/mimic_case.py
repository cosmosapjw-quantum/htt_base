"""H5(c) collision-step test: integrate the FLUID photon momentum equation with the photon cell's SDIRK(2,2) scheme.

After a normal solve with the read-only stash variant (bit-identical to R105), the final-Picard Radau
solution y(N) (dense output), opacity history and RHS closures are available. The photon
conserved ratio r = Q_gamma/E_gamma obeys the fluid equation

    dr/dN = G(N, r) + rate(N) c(N, r),    c = (F[1:] - r F[0]) / E,   F = covariant anchor Thomson force,

with geometry, baryon velocity and previous-Picard pi taken from y(N). The mimic applies exactly the
stage structure of _advance_moving_photon_cell to this 3-vector:
  - substep edges/depths from _optical_substeps(opacity, n0, n1, 2, cap) (cap=None -> 2 fixed substeps);
  - collision part scaled by the exact substep depth d_j and evaluated at the stage time
    u_j + c h_j (c = gamma, 1), i.e. baryon velocity at the stage time;
  - gravitational part scaled by h_j*dN and evaluated either at the cell midpoint N_mid (geom='mid',
    as the photon cell does) or at the stage time (geom='stage').
mimic - Radau isolates the photon-cell time discretisation acting on the fluid model; sky - mimic is
then the remaining sky-vs-fluid model difference.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
VARIANT = HERE / "coupled_h5_variant_stash.py"

from bass.collision.moving_thomson import covariant_thomson_four_force  # noqa: E402
from bass.transport import coupled_einstein_boltzmann as repo_solver  # noqa: E402
from scripts.r105.native_optical_refinement import angular_basis  # noqa: E402


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_variant():
    name = "h5_coupled_variant_stash_mod"
    spec = importlib.util.spec_from_file_location(name, VARIANT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    mod.HYREC_REF_CSV = repo_solver.HYREC_REF_CSV
    return mod


class FluidPhotonModel:
    def __init__(self, st):
        self.sol, self.opacity = st["sol"], st["opacity"]
        self.ode_rhs, self.unpack = st["ode_rhs"], st["unpack"]
        self.pg, self.pb = st["photon_idx"], st["baryon_idx"]
        self.offg = 16 + 4 * self.pg
        self.N0, self.N1 = st["N_start"], st["N_end"]

    def y_with(self, N, r):
        y = np.asarray(self.sol.sol(N), dtype=np.float64).copy()
        if r is not None:
            y[self.offg + 1:self.offg + 4] = r
        return y

    def rate(self, N):
        return float(self.opacity.rate(min(max(float(N), self.N0), self.N1)))

    def coll(self, N, r):
        """Thomson part per unit rate: (F[1:] - r F[0]) / E at baryon velocity v_b(N)."""
        y = self.y_with(N, r)
        u = self.unpack(N, y)
        T4, vv = u[11], u[13]
        E = float(T4[self.pg][0, 0])
        rr = T4[self.pg][0, 1:] / E
        F = covariant_thomson_four_force(T4[self.pg], vv[self.pb], clock="conserved_anchor")
        return (F[1:] - rr * F[0]) / E

    def grav(self, N, r):
        """Non-collisional part G = full fluid RHS minus rate * coll at (N, r)."""
        y = self.y_with(N, r)
        full = self.ode_rhs(N, y)[self.offg + 1:self.offg + 4]
        return full - self.rate(N) * self.coll(N, r)


def stage_solve(model, base, gh_dN, gd, N_geom, N_coll, guess):
    """Solve Y = base + gh_dN*G(N_geom, Y) + gd*c(N_coll, Y) by Newton with an FD Jacobian."""
    def resid(Y):
        return Y - base - gh_dN * model.grav(N_geom, Y) - gd * model.coll(N_coll, Y)
    Y = np.array(guess, dtype=np.float64)
    R = resid(Y)
    scale = max(float(np.max(np.abs(Y))), 1e-12)
    eps = 1e-6 * scale
    J = np.empty((3, 3))
    for k in range(3):
        d = np.zeros(3); d[k] = eps
        J[:, k] = (resid(Y + d) - R) / eps
    for _ in range(6):
        dY = np.linalg.solve(J, -R)
        Y = Y + dY
        R = resid(Y)
        if float(np.max(np.abs(dY))) <= 1e-15 * scale:
            break
    return Y, float(np.max(np.abs(R)))


def run_mimic(model, mod, N_eval, n_cells, cap, geom):
    gamma = 1.0 - 1.0 / math.sqrt(2.0)
    r = model.y_with(float(N_eval[0]), None)[model.offg + 1:model.offg + 4].copy()
    out = np.zeros((n_cells, 3))
    nsub = np.zeros(n_cells, dtype=int)
    maxres = 0.0
    for cell in range(n_cells):
        n0, nmid, n1 = float(N_eval[2 * cell]), float(N_eval[2 * cell + 1]), float(N_eval[2 * cell + 2])
        dN = n1 - n0
        u_edges, depths = mod._optical_substeps(model.opacity, n0, n1, 2, cap)
        nsub[cell] = len(depths)
        y = r
        for j, d in enumerate(depths):
            h = u_edges[j + 1] - u_edges[j]
            Ns = [n0 + (u_edges[j] + c * h) * dN for c in (gamma, 1.0)]
            Ng = [nmid, nmid] if geom == "mid" else Ns
            Y1, e1 = stage_solve(model, y, gamma * h * dN, gamma * float(d), Ng[0], Ns[0], y)
            base2 = y + ((1.0 - gamma) / gamma) * (Y1 - y)
            Y2, e2 = stage_solve(model, base2, gamma * h * dN, gamma * float(d), Ng[1], Ns[1], Y1)
            maxres = max(maxres, e1, e2)
            y = Y2
        r = y
        out[cell] = r
    return out, nsub, maxres


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--family", default="VI_-1/9")
    ap.add_argument("--epsilon", type=float, default=2e-4)
    ap.add_argument("--caps", default="1.0,0.5,0.25,0.125,none")
    ap.add_argument("--geoms", default="mid,stage")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mod = load_variant()
    cfg = mod.CoupledSolverConfig(
        n_cells=args.cells, ell_max=4, n_picard=4, max_substep_depth=1.0,
        epsilon=args.epsilon, substeps_per_cell=2, record_history=True, massless_neutrino_fraction=0.0,
    )
    t0 = time.perf_counter()
    res = mod.solve_coupled_einstein_boltzmann(args.family, cfg, lie_op=angular_basis(4, 16))
    solve_wall = time.perf_counter() - t0
    hist = res.history["picard_iterations"][-1]
    st = mod._H5_STASH
    if st.get("picard_idx") != 3:
        raise RuntimeError("stash does not hold the final Picard iteration")
    model = FluidPhotonModel(st)
    N_eval = st["N_eval"]
    if not np.array_equal(N_eval[2::2], hist["N_end"]):
        raise RuntimeError("cell endpoints differ from the recorded history")
    arrays = {k: np.asarray(v) for k, v in hist.items()}
    mimic_meta = {}
    for cap_s in args.caps.split(","):
        cap = None if cap_s == "none" else float(cap_s)
        for geom in args.geoms.split(","):
            t1 = time.perf_counter()
            traj, nsub, maxres = run_mimic(model, mod, N_eval, args.cells, cap, geom)
            key = f"mimic_cap{cap_s}_{geom}"
            arrays[key] = traj
            arrays[key + "_nsub"] = nsub
            mimic_meta[key] = {"cap": cap, "geom": geom, "wall_s": time.perf_counter() - t1,
                               "max_stage_residual": maxres, "total_substeps": int(nsub.sum())}
            print(key, mimic_meta[key], flush=True)
    np.savez(args.output.with_suffix(".npz"), **arrays)
    summary = {
        "schema": "htt.r106.h5_ode_control.mimic.1", "family": args.family, "epsilon": args.epsilon,
        "n_cells": args.cells, "rtol": mod.RADAU_RTOL, "atol": mod.RADAU_ATOL, "solve_wall_s": solve_wall,
        "C2": {ch: float(res.cl_final[ch][2]) for ch in ("T", "E", "B")},
        "max_hamiltonian": float(res.max_hamiltonian_residual), "max_codazzi": float(res.max_codazzi_residual),
        "max_stokes_reality": float(res.max_stokes_reality_err),
        "final_state_sha256": hashlib.sha256(np.ascontiguousarray(res.final_state).tobytes()).hexdigest(),
        "history_sha256": {k: hashlib.sha256(np.ascontiguousarray(np.asarray(v)).tobytes()).hexdigest()
                           for k, v in hist.items()},
        "mimic": mimic_meta,
        "identity": {"variant_sha256": sha(VARIANT), "repo_solver_sha256": sha(repo_solver.__file__),
                     "mimic_case_sha256": sha(__file__), "hyrec_csv_sha256": sha(repo_solver.HYREC_REF_CSV)},
    }
    args.output.with_suffix(".json").write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
