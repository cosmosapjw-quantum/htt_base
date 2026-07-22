from __future__ import annotations

import numpy as np

from htt_ext.types import PoleDefinition
from .alm import angular_momentum_matrices


def power_tensor(alm: np.ndarray, ell: int) -> np.ndarray:
    a = np.asarray(alm, dtype=np.complex128)
    if a.shape != (2 * ell + 1,):
        raise ValueError("alm has incompatible shape")
    norm = float(np.vdot(a, a).real)
    if norm <= 0:
        raise ValueError("alm norm is zero")
    js = angular_momentum_matrices(ell)
    tensor = np.zeros((3, 3), dtype=float)
    for i in range(3):
        for j in range(3):
            op = (js[i] @ js[j] + js[j] @ js[i]) / 2.0
            tensor[i, j] = float(np.vdot(a, op @ a).real / (ell * (ell + 1) * norm))
    return (tensor + tensor.T) / 2.0


def pole_from_alm(
    alm: np.ndarray,
    ell: int,
    definition: PoleDefinition | str = PoleDefinition.ANISOTROPY_TENSOR,
) -> tuple[np.ndarray, np.ndarray]:
    """Return an unoriented pole and the three power-tensor eigenvalues.

    Poles are axes, not oriented vectors: ``p`` and ``-p`` represent the same
    object.  ``ANISOTROPY_TENSOR`` selects the eigenvector whose eigenvalue is
    farthest from the isotropic value 1/3.  This selects the symmetry axis of a
    zonal m=0 mode and the planarity axis of a sectoral |m|=ell mode.
    """
    definition = PoleDefinition(definition)
    tensor = power_tensor(alm, ell)
    vals, vecs = np.linalg.eigh(tensor)
    if definition == PoleDefinition.MAX_ANGULAR_MOMENTUM:
        idx = int(np.argmax(vals))
    elif definition == PoleDefinition.MIN_ANGULAR_MOMENTUM:
        idx = int(np.argmin(vals))
    elif definition == PoleDefinition.ANISOTROPY_TENSOR:
        idx = int(np.argmax(np.abs(vals - 1.0 / 3.0)))
    else:
        raise NotImplementedError(
            "multipole-vector poles require the optional plugin and may not be "
            "silently substituted"
        )
    pole = np.asarray(vecs[:, idx], dtype=float)
    pole /= np.linalg.norm(pole)
    return pole, vals


def angular_separation_deg(a: np.ndarray, b: np.ndarray, unoriented: bool = True) -> float:
    x = np.asarray(a, dtype=float)
    y = np.asarray(b, dtype=float)
    x /= np.linalg.norm(x)
    y /= np.linalg.norm(y)
    d = float(np.dot(x, y))
    if unoriented:
        d = abs(d)
    return float(np.degrees(np.arccos(np.clip(d, -1.0, 1.0))))


def mean_axis(poles: np.ndarray) -> np.ndarray:
    """Principal unoriented mean axis from a stack of pole vectors."""
    p = np.asarray(poles, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("poles must have shape (n,3)")
    scatter = p.T @ p
    _, vecs = np.linalg.eigh(scatter)
    axis = vecs[:, -1]
    return axis / np.linalg.norm(axis)
