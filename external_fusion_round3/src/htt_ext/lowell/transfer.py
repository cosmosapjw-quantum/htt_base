from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ShellTransferKernel:
    """A typed redshift-shell line-of-sight transfer contribution.

    This object does not claim that a source shell is itself an observed CMB sky.
    It stores an additive contribution whose sum must recover the registered total
    transfer under the same harmonic, gauge and normalization convention.
    """

    ell: int
    redshift_edges: tuple[float, ...]
    complex_response: tuple[complex, ...]
    source_name: str
    convention: str

    def __post_init__(self) -> None:
        if self.ell < 1:
            raise ValueError("ell must be >=1")
        if len(self.redshift_edges) != len(self.complex_response) + 1:
            raise ValueError("redshift_edges must have one more entry than responses")
        if any(b <= a for a, b in zip(self.redshift_edges[:-1], self.redshift_edges[1:])):
            raise ValueError("redshift edges must be strictly increasing")
        if not self.source_name or not self.convention:
            raise ValueError("source_name and convention are required")

    def total(self) -> complex:
        return complex(np.sum(np.asarray(self.complex_response, dtype=np.complex128)))

    def cumulative(self) -> np.ndarray:
        return np.cumsum(np.asarray(self.complex_response, dtype=np.complex128))


def integrate_kernel_on_edges(
    z: np.ndarray,
    kernel: np.ndarray,
    edges: np.ndarray,
    *,
    ell: int,
    source_name: str,
    convention: str,
) -> ShellTransferKernel:
    """Trapezoid-integrate a sampled line-of-sight kernel into frozen shells."""
    z = np.asarray(z, dtype=float)
    k = np.asarray(kernel, dtype=np.complex128)
    edges = np.asarray(edges, dtype=float)
    if z.ndim != 1 or k.ndim != 1 or len(z) != len(k):
        raise ValueError("z and kernel must be one-dimensional with equal length")
    if len(z) < 2 or np.any(np.diff(z) <= 0):
        raise ValueError("z must be strictly increasing")
    if edges[0] < z[0] or edges[-1] > z[-1]:
        raise ValueError("edges must lie within sampled z range")
    responses: list[complex] = []
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        # Include both boundary interpolants, then integrate only this shell.
        interior = (z > lo) & (z < hi)
        zz = np.concatenate(([lo], z[interior], [hi]))
        rr = np.concatenate((
            [np.interp(lo, z, k.real) + 1j * np.interp(lo, z, k.imag)],
            k[interior],
            [np.interp(hi, z, k.real) + 1j * np.interp(hi, z, k.imag)],
        ))
        # Avoid double-counting a measure-zero boundary: trapezoid integration is
        # additive across adjacent intervals by construction.
        responses.append(complex(np.trapezoid(rr, zz)))
    return ShellTransferKernel(
        ell=ell,
        redshift_edges=tuple(float(x) for x in edges),
        complex_response=tuple(responses),
        source_name=source_name,
        convention=convention,
    )


def shell_sum_relative_error(shells: ShellTransferKernel, total: complex) -> float:
    denom = max(abs(total), 1e-30)
    return float(abs(shells.total() - total) / denom)


def refinement_difference(coarse: ShellTransferKernel, fine: ShellTransferKernel) -> float:
    if coarse.ell != fine.ell or coarse.source_name != fine.source_name:
        raise ValueError("incompatible kernels")
    denom = max(abs(fine.total()), 1e-30)
    return float(abs(coarse.total() - fine.total()) / denom)
