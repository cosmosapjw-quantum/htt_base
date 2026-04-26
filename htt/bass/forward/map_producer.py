"""bass/forward/map_producer.py — Round-16 PR-S12 real-space map producer.

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §3 (closes Round-16 gap
**G10**: ``map_T/Q/U`` typed pass-through has no producer).

Provides:
- :func:`alm_to_map_TQU` — inverse spherical-harmonic transform from
  the BASS real-spherical-harmonic ``a_{ℓm}`` packing (per PSTFTensor
  convention) to HEALPix `T`, `Q`, `U` maps via ``healpy.alm2map`` and
  ``healpy.alm2map_spin``.
- :func:`populate_map_outputs` — wraps
  :class:`bass.common.contracts.SolverCoreOutput`, fills the
  ``map_T/Q/U`` fields, and flips the ``map_output_support`` metadata
  flag from ``"not_implemented"`` to ``"producer_attached"`` per the
  R15-AUDIT-PATCH P-08 contract.

BASS alm convention
-------------------
The internal representation aligns with
:class:`bass.hierarchy.pstf_tensor.PSTFTensor`: a dict mapping
``ell -> ndarray(2ℓ+1)`` of *real* coefficients ordered as
``index = m + ℓ`` for ``m ∈ {-ℓ, …, +ℓ}``. The mapping is sparse: only
the ℓ-multipoles populated by the solver appear as keys. The conversion
to the healpy complex packing follows the standard real ↔ complex
spherical harmonic transformation:

    a^complex_{ℓ, 0}  = a^real_{ℓ, 0}
    a^complex_{ℓ, m}  = ((-1)^m / √2) (a^real_{ℓ, m} − i a^real_{ℓ, -m}),  m > 0

so that the field reconstructed via either basis is identically real
to floating-point precision.

References
----------
- ``docs/V5_ROUND16_03_OBSERVABLES_LAYER.md §3`` — implementation spec.
- Górski et al. 2005 (HEALPix paper) — alm packing convention.
- Wieczorek & Meschede 2018 (SHTOOLS) — real-spherical-harmonic
  conversion.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any

import numpy as np

try:  # healpy is a soft dependency; import lazily so module-level
    # imports stay cheap on installs where the inverse SHT is not used.
    import healpy as hp
except ImportError as exc:  # pragma: no cover - exercised only if absent
    hp = None  # type: ignore[assignment]
    _HEALPY_IMPORT_ERROR: Exception | None = exc
else:
    _HEALPY_IMPORT_ERROR = None

__all__ = [
    "BASS_ALM_REPRESENTATION_KEY",
    "infer_lmax",
    "bass_real_alm_to_healpy_complex",
    "alm_to_map_TQU",
    "populate_map_outputs",
]


#: Magic key used in metadata + alm dicts to declare the BASS convention.
BASS_ALM_REPRESENTATION_KEY = "real_spherical_harmonic_per_ell"


def _require_healpy() -> None:
    if hp is None:
        raise ImportError(
            "bass.forward.map_producer requires `healpy`; install it via "
            "`pip install healpy` or downgrade map_output_support to "
            "'not_implemented' (R15-AUDIT-PATCH P-08 honest envelope)."
        ) from _HEALPY_IMPORT_ERROR


# ──────────────────────────────────────────────────────────────────────
# alm format helpers
# ──────────────────────────────────────────────────────────────────────


def infer_lmax(alm: Mapping[int, np.ndarray]) -> int:
    """Return ``max(alm.keys())``; raises if alm is empty.

    Parameters
    ----------
    alm : Mapping[int, ndarray]
        BASS real-spherical-harmonic alm packing
        (``ell → ndarray(2ℓ+1)``).
    """
    if not alm:
        raise ValueError("infer_lmax called on empty alm mapping")
    return int(max(alm.keys()))


def bass_real_alm_to_healpy_complex(
    alm: Mapping[int, np.ndarray],
    *,
    lmax: int | None = None,
) -> np.ndarray:
    """Convert BASS real ``a_{ℓm}`` to healpy complex 1-D array.

    The output follows healpy's packing:
    ``index = m * (2*lmax + 1 - m) // 2 + ell`` for ``m ∈ [0, lmax]``,
    ``ell ∈ [m, lmax]`` — a flat array of length
    ``(lmax+1) * (lmax+2) // 2``.

    Empty ℓ-slots in ``alm`` (e.g. the photon-T tower starts at ℓ=2)
    are zero-filled in the output.

    Parameters
    ----------
    alm : Mapping[int, ndarray]
        BASS real-spherical-harmonic alm packing.
    lmax : int, optional
        Maximum ℓ to transform; defaults to ``infer_lmax(alm)``.

    Returns
    -------
    ndarray, shape ((lmax+1)*(lmax+2)//2,), complex128
    """
    if lmax is None:
        lmax = infer_lmax(alm) if alm else 0
    sqrt2 = float(np.sqrt(2.0))
    n = (lmax + 1) * (lmax + 2) // 2
    out = np.zeros(n, dtype=np.complex128)
    for ell, real_array in alm.items():
        if ell > lmax:
            continue
        arr = np.asarray(real_array, dtype=np.float64)
        if arr.shape != (2 * ell + 1,):
            raise ValueError(
                f"alm[{ell}] must have shape ({2 * ell + 1},); got {arr.shape!r}"
            )
        # m = 0
        idx0 = 0 * (2 * lmax + 1 - 0) // 2 + ell
        out[idx0] = arr[ell]  # real_array index for m=0
        # m > 0: complex = ((-1)^m / √2) (real_m − i real_{-m})
        for m in range(1, ell + 1):
            idx = m * (2 * lmax + 1 - m) // 2 + ell
            sign = (-1.0) ** m
            re_m = arr[ell + m]   # real_{ℓ, m}
            im_m = arr[ell - m]   # real_{ℓ, -m}
            out[idx] = (sign / sqrt2) * (re_m - 1j * im_m)
    return out


# ──────────────────────────────────────────────────────────────────────
# Inverse SHT
# ──────────────────────────────────────────────────────────────────────


def alm_to_map_TQU(
    *,
    alm_T: Mapping[int, np.ndarray],
    alm_E: Mapping[int, np.ndarray],
    alm_B: Mapping[int, np.ndarray],
    nside: int,
    lmax: int | None = None,
) -> dict[str, np.ndarray]:
    """Inverse SHT producing T, Q, U HEALPix maps.

    The polarisation maps Q, U are produced via the spin-2 inverse
    transform with E and B alm as the (E, B) input pair, matching
    healpy's convention (``hp.alm2map_spin([alm_E, alm_B], …, spin=2)``).

    Parameters
    ----------
    alm_T, alm_E, alm_B : Mapping[int, ndarray]
        BASS real-spherical-harmonic alm packings for T, E, B.
    nside : int
        HEALPix resolution. Must satisfy ``nside`` is a power of 2 and
        ``nside ≥ 1``.
    lmax : int, optional
        Maximum ℓ to transform. Defaults to the max of
        ``infer_lmax(alm_X)`` across the three inputs.

    Returns
    -------
    dict
        ``{'map_T': ndarray, 'map_Q': ndarray, 'map_U': ndarray}`` —
        each array has length ``12 * nside ** 2``.
    """
    _require_healpy()
    if nside < 1:
        raise ValueError(f"nside must be >= 1; got {nside!r}")
    if (nside & (nside - 1)) != 0:
        raise ValueError(f"nside must be a power of 2; got {nside!r}")

    if lmax is None:
        candidates = [
            infer_lmax(a) for a in (alm_T, alm_E, alm_B) if a
        ]
        if not candidates:
            raise ValueError("all alm inputs are empty; cannot infer lmax")
        lmax = max(candidates)

    alm_T_hp = bass_real_alm_to_healpy_complex(alm_T, lmax=lmax)
    alm_E_hp = bass_real_alm_to_healpy_complex(alm_E, lmax=lmax)
    alm_B_hp = bass_real_alm_to_healpy_complex(alm_B, lmax=lmax)

    map_T = hp.alm2map(alm_T_hp, nside, lmax=lmax)
    # Spin-2 alm2map requires lmax ≥ 2 (no spin-2 modes for ℓ < 2). When
    # the requested lmax is below 2 we return zero polarisation maps —
    # the spin-2 sector is identically empty.
    if lmax >= 2:
        map_Q, map_U = hp.alm2map_spin(
            [alm_E_hp, alm_B_hp], nside, spin=2, lmax=lmax, mmax=lmax,
        )
    else:
        npix = 12 * nside * nside
        map_Q = np.zeros(npix, dtype=np.float64)
        map_U = np.zeros(npix, dtype=np.float64)
    return {
        "map_T": np.asarray(map_T, dtype=np.float64),
        "map_Q": np.asarray(map_Q, dtype=np.float64),
        "map_U": np.asarray(map_U, dtype=np.float64),
    }


# ──────────────────────────────────────────────────────────────────────
# SolverCoreOutput integration
# ──────────────────────────────────────────────────────────────────────


def populate_map_outputs(
    output: Any,
    *,
    nside: int = 64,
    lmax: int | None = None,
) -> Any:
    """Return a copy of ``output`` with ``map_T/Q/U`` populated.

    The input ``output`` (a :class:`SolverCoreOutput`) must satisfy:
    - ``alm_T``, ``alm_E``, ``alm_B`` are non-None Mapping[int, ndarray]
      in the BASS real-spherical-harmonic packing.
    - ``metadata['map_output_support'] == 'not_implemented'`` (the only
      supported pre-state — flipping a producer-attached output is a
      no-op caught by the contract).

    The returned copy:
    - Has ``map_T/Q/U`` populated via :func:`alm_to_map_TQU`.
    - Has ``metadata['map_output_support'] = 'producer_attached'``.

    Raises
    ------
    ValueError
        If preconditions are not met or the
        :class:`SolverCoreOutput.__post_init__` contract would reject
        the resulting bundle.
    """
    if not isinstance(output.alm_T, Mapping):
        raise ValueError(
            "populate_map_outputs requires alm_T to be a Mapping[int, ndarray]; "
            f"got {type(output.alm_T).__name__}"
        )
    if not isinstance(output.alm_E, Mapping):
        raise ValueError(
            "populate_map_outputs requires alm_E to be a Mapping[int, ndarray]; "
            f"got {type(output.alm_E).__name__}"
        )
    if not isinstance(output.alm_B, Mapping):
        raise ValueError(
            "populate_map_outputs requires alm_B to be a Mapping[int, ndarray]; "
            f"got {type(output.alm_B).__name__}"
        )
    pre_status = output.metadata.get("map_output_support")
    if pre_status == "producer_attached":
        # Idempotent: returning a copy with the same maps would silently
        # double-attach. Surface this loudly so the audit catches it.
        raise ValueError(
            "map_output_support is already 'producer_attached'; "
            "populate_map_outputs is not idempotent — caller should not "
            "re-invoke on an attached bundle."
        )
    if pre_status != "not_implemented":
        raise ValueError(
            f"map_output_support pre-state {pre_status!r} unrecognised; "
            "expected 'not_implemented' for a fresh producer attach."
        )

    maps = alm_to_map_TQU(
        alm_T=output.alm_T,
        alm_E=output.alm_E,
        alm_B=output.alm_B,
        nside=int(nside),
        lmax=lmax,
    )
    new_metadata = dict(output.metadata)
    new_metadata["map_output_support"] = "producer_attached"
    new_metadata["map_producer_nside"] = int(nside)
    new_metadata["map_producer_lmax"] = (
        int(lmax) if lmax is not None
        else int(max(infer_lmax(output.alm_T),
                     infer_lmax(output.alm_E),
                     infer_lmax(output.alm_B)))
    )
    new_metadata["map_producer_path"] = "bass.forward.map_producer.alm_to_map_TQU"
    return dataclasses.replace(
        output,
        map_T=maps["map_T"],
        map_Q=maps["map_Q"],
        map_U=maps["map_U"],
        metadata=new_metadata,
    )
