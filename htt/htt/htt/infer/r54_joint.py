"""R54-L06 joint frame tomography in precision form.

A probe enters a block as (F, t) with -2 ln L = theta^T F theta - 2 t^T theta + const for a linear Gaussian model
y = J theta + noise(C): F = J^T C^-1 J, t = J^T C^-1 y, plus q0 = y^T C^-1 y for chi2 bookkeeping. Probes add by
summing (F, t, q0, n_data). A singular block is reported with its null directions and is never regularised (gate MG-L07).

  linear_probe          (F, t, q0, n) of one probe
  add_probes            sum of probes on one parameter vector
  block_identification  scaled-eigenvalue rank and null directions of a block precision (r54_tensor_five_view.identify)
  constrained_chi2      chi2 at the GLS optimum of a linear sub-model theta = L phi (transport hypothesis), with dof
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from htt.htt.infer import r54_tensor_five_view as fv


def linear_probe(y: np.ndarray, cov: np.ndarray, design: np.ndarray, name: str) -> dict:
    y, cov, design = np.asarray(y, float), np.asarray(cov, float), np.asarray(design, float)
    if design.shape[0] != y.size or cov.shape != (y.size, y.size):
        raise ValueError(f"probe {name}: shape mismatch")
    lc = np.linalg.cholesky(0.5 * (cov + cov.T))
    a = np.linalg.solve(lc, design)
    b = np.linalg.solve(lc, y)
    return {"name": name, "F": a.T @ a, "t": a.T @ b, "q0": float(b @ b), "n": int(y.size)}


def add_probes(probes: Sequence[dict]) -> dict:
    if not probes:
        raise ValueError("no probe")
    k = probes[0]["F"].shape[0]
    if any(p["F"].shape != (k, k) for p in probes):
        raise ValueError("probes act on different parameter vectors")
    return {"name": "+".join(p["name"] for p in probes), "F": sum(p["F"] for p in probes), "t": sum(p["t"] for p in probes),
            "q0": float(sum(p["q0"] for p in probes)), "n": int(sum(p["n"] for p in probes))}


def block_identification(f: np.ndarray, scale: np.ndarray | None, names: Sequence[str]) -> dict:
    """Rank and null directions of a block precision; the matrix is used as given (no regularisation)."""
    fs = np.asarray(f, float)
    ident = fv.identify(fs, scale)
    null = [{"direction": ident.null_basis[:, j].tolist(),
             "dominant_coordinates": [names[i] for i in np.argsort(-np.abs(ident.null_basis[:, j]))[:3]]} for j in range(ident.null_basis.shape[1])]
    return {"rank": ident.rank, "dim": ident.dim, "scaled_eigenvalues": list(ident.eigenvalues_scaled), "null_directions": null,
            "scale": None if scale is None else np.asarray(scale, float).tolist(), "identified": ident.rank == ident.dim}


def constrained_chi2(block: dict, link: np.ndarray, label: str, scale: np.ndarray | None = None) -> dict:
    """chi2 = q0 - t_phi^T F_phi^-1 t_phi for theta = L phi (L full column rank, F_phi positive definite); dof = n - dim(phi).

    ``scale`` gives typical sizes of the phi coordinates for the identification check (mixed-unit blocks)."""
    link = np.asarray(link, float)
    if link.shape[1] == 0:
        return {"hypothesis": label, "chi2": block["q0"], "dof": block["n"], "phi": [], "phi_cov": []}
    f_phi = link.T @ block["F"] @ link
    t_phi = link.T @ block["t"]
    ident = fv.identify(f_phi, scale)
    if ident.rank < ident.dim:
        raise ValueError(f"hypothesis {label}: parameters not identified (rank {ident.rank} of {ident.dim}); not regularised")
    phi = np.linalg.solve(f_phi, t_phi)
    return {"hypothesis": label, "chi2": float(block["q0"] - t_phi @ phi), "dof": int(block["n"] - link.shape[1]),
            "phi": phi.tolist(), "phi_cov": np.linalg.inv(f_phi).tolist()}
