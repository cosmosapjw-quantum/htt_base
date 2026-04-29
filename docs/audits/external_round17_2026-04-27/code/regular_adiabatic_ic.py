"""FB-5.3 — CAMB-regular adiabatic seed for one perturbative mode.

The returned vector is a perturbation-side extension of the shipped
LB-5 combined state layout:

1. The prefix is the standard ``pack_combined_state`` block
   ``(a, Sigma_+, Sigma_-, photon_T, photon_E, neutrino_reduced)``.
2. Six extra scalars are appended:
   ``(delta_b, theta_b, delta_c, theta_c, eta_cov, Z)``.

This keeps the background / hierarchy prefix byte-compatible with the
existing pack/unpack SSOT while giving FB-5 a place to carry the baryon,
CDM, and metric startup amplitudes that are not part of LB-5's runtime
state vector yet.
"""
from __future__ import annotations

from typing import Final

import numpy as np

from bass.collision.polarization import zero_polarization_hierarchy
from bass.hierarchy.ic import zero_IC
from bass.hierarchy.pack_unpack import (
    NEUTRINO_REDUCED_SIZE,
    combined_total_size,
    pack_combined_state,
    slice_neutrino_reduced,
    unpack_combined_state,
)
from bass.hierarchy.pstf_tensor import zero_hierarchy
from bass.species.constants import default_constants


__all__ = [
    "CAMB_REGULAR_ADIABATIC_EXTRA_LABELS",
    "CAMB_REGULAR_ADIABATIC_EXTRA_SIZE",
    "regular_adiabatic_seed_total_size",
    "infer_regular_adiabatic_seed_L_max",
    "slice_regular_adiabatic_extras",
    "regular_adiabatic_formulae",
    "pack_regular_adiabatic_seed_from_formulae",
    "make_camb_regular_adiabatic_seed",
    "unpack_camb_regular_adiabatic_seed",
    "seed_observables",
]


CAMB_REGULAR_ADIABATIC_EXTRA_LABELS: Final[tuple[str, ...]] = (
    "delta_b",
    "theta_b",
    "delta_c",
    "theta_c",
    "eta_cov",
    "Z",
)
CAMB_REGULAR_ADIABATIC_EXTRA_SIZE: Final[int] = (
    len(CAMB_REGULAR_ADIABATIC_EXTRA_LABELS)
)

_EXTRA_INDEX: Final[dict[str, int]] = {
    name: idx for idx, name in enumerate(CAMB_REGULAR_ADIABATIC_EXTRA_LABELS)
}


def regular_adiabatic_seed_total_size(L_max: int) -> int:
    """Total packed size of the FB-5.3 seed vector."""
    return combined_total_size(L_max) + CAMB_REGULAR_ADIABATIC_EXTRA_SIZE


def infer_regular_adiabatic_seed_L_max(seed_size: int) -> int:
    """Infer ``L_max`` from the packed seed length."""
    if seed_size <= 0:
        raise ValueError(f"seed_size must be positive, got {seed_size}")
    for L_max in range(2, 257):
        if regular_adiabatic_seed_total_size(L_max) == seed_size:
            return L_max
    raise ValueError(
        f"seed_size={seed_size} does not match any supported "
        f"regular-adiabatic layout"
    )


def slice_regular_adiabatic_extras(L_max: int) -> slice:
    """Slice of the appended ``(delta_b, theta_b, delta_c, theta_c, eta, Z)`` block."""
    start = combined_total_size(L_max)
    return slice(start, start + CAMB_REGULAR_ADIABATIC_EXTRA_SIZE)


def _extra_value(extras: np.ndarray, name: str) -> float:
    return float(extras[_EXTRA_INDEX[name]])


def _approx_tau_c(eta_initial: float, a_initial: float) -> float:
    """Early-time TCA startup timescale.

    This is not a recombination solve; it is a deterministic radiation-
    era scaling chosen only to populate the small photon quadrupole / E2
    startup surface in the absence of the full Thomson-rate pipeline.
    """
    return 0.15 * eta_initial / np.sqrt(max(a_initial, 1.0e-30))


def _seed_formulae(
    *,
    k_comoving: float,
    eta_initial: float,
    a_initial: float,
    b_k_sq: float = 1.0,
) -> dict[str, float]:
    """Leading-order regular-adiabatic startup formulas from Lowell §13.2.

    The ``b_k_sq`` keyword is the **linear primordial curvature
    amplitude** ``C ≈ ζ`` of the regular adiabatic mode (Ma-Bertschinger
    1995 §7 eq. 96; Lewis-Challinor 2002 App. C). Despite the historical
    name (which dates to the CAMB Notes ``χ_0 = -1`` geometric ``β²``
    convention), the parameter enters every leading-order seed
    perturbation **linearly** — confirmed by 4 independent external
    audits (Round-12, 2026-04-25, see ``docs/V5_ROUND12_FINDINGS.md``
    if available). The ``_sq`` suffix is misleading nomenclature; the
    public kwarg name is preserved for backward compatibility.

    Conventions:
      - ``b_k_sq = 1.0`` (legacy default): unit-amplitude probe; matches
        the CAMB Notes ``χ_0 = -1`` reference convention.
      - ``b_k_sq = ζ`` (some primordial curvature value): physical
        amplitude. The C_ℓ assembly then pairs ``α(k)`` (the per-unit-ζ
        transfer extracted from this seed) with ``P_R(k) = ⟨ζ²⟩`` per
        the canonical ``C_ℓ = 4π ∫ d ln k · P_R(k) · |α|²``.

    Do NOT pass ``A_s × (k/k_pivot)^(n_s-1)`` here — that is the
    *variance* spectrum, not the linear amplitude. Doing so would
    produce a meaningless seed value that under-runs the linear-
    extraction probe range by ~10⁹.
    """
    constants = default_constants()
    R_nu = constants.Omega_nu_0 / constants.Omega_r_0
    omega = constants.H0_mpc * constants.Omega_m_0 / np.sqrt(
        constants.Omega_r_0
    )

    x = float(k_comoving) * float(eta_initial)
    x2 = x * x
    x3 = x2 * x
    denom = 4.0 * R_nu + 15.0
    # Internal alias clarifies the linear-amplitude semantics. The
    # "B_K_sq" formulas-dict key (line ``"B_K_sq": float(amplitude)``
    # below) is preserved for backward compatibility with any external
    # diagnostic that read it.
    amplitude = float(b_k_sq)

    # V5-RUNTIME Round-11 (R9-D auditor #2 follow-up): the inner factor
    # was originally `(amplitude - 10.0 / denom)` which created a spurious
    # quadratic ``amplitude²`` correction. Replaced with `(1.0 - 10.0 / denom)`
    # so the whole expression is linear in ``amplitude``. Bit-identical to
    # the pre-fix form at ``b_k_sq = 1.0`` (legacy default), since
    # ``(1 - 10/denom) == (amplitude - 10/denom)`` when ``amplitude == 1``.
    # The "10/denom" inner constant matches the CAMB Notes
    # χ_0 = -1 unit-normalization convention; once an arbitrary-amplitude
    # API is exposed via ``b_k_sq``, only the outer ``2 · amplitude`` carries
    # the linear amplitude scaling.
    eta_cov = 2.0 * amplitude * (
        1.0 - (x2 / 12.0) * (1.0 - 10.0 / denom)
    )
    delta_gamma = (
        (amplitude / 3.0) * x2
        - (amplitude / 15.0) * omega * (k_comoving ** 2) * (eta_initial ** 3)
    )
    delta_b = (
        (amplitude / 4.0) * x2
        - (amplitude / 20.0) * omega * (k_comoving ** 2) * (eta_initial ** 3)
    )
    theta_gamma = (amplitude / 27.0) * x3
    theta_nu = (amplitude / 27.0) * ((4.0 * R_nu + 23.0) / denom) * x3
    pi_nu = -amplitude * (4.0 / (3.0 * denom)) * x2
    G_3 = -amplitude * (4.0 / (21.0 * denom)) * x3
    Z = (
        -(amplitude / 2.0) * k_comoving * eta_initial
        + (3.0 * amplitude / 20.0) * omega * k_comoving * (eta_initial ** 2)
    )

    tau_c = _approx_tau_c(eta_initial, a_initial)
    # Sign chosen to match the early-time CAMB convention at the same
    # radiation-era startup point.
    pi_gamma = -(32.0 / 45.0) * k_comoving * tau_c * theta_gamma
    E_2 = 0.25 * pi_gamma

    return {
        "eta_cov": float(eta_cov),
        "delta_gamma": float(delta_gamma),
        "delta_nu": float(delta_gamma),
        "delta_b": float(delta_b),
        "delta_c": float(delta_b),
        "theta_gamma": float(theta_gamma),
        "theta_nu": float(theta_nu),
        "theta_b": float(theta_gamma),
        "theta_c": float(theta_gamma),
        "pi_nu": float(pi_nu),
        "G_3": float(G_3),
        "Z": float(Z),
        "pi_gamma": float(pi_gamma),
        "E_2": float(E_2),
        "R_nu": float(R_nu),
        "omega": float(omega),
        # Legacy key name kept for backward compatibility — reader should
        # interpret as the linear primordial amplitude (NOT a variance).
        "B_K_sq": float(amplitude),
        "tau_c": float(tau_c),
    }


def regular_adiabatic_formulae(
    *,
    k_comoving: float,
    eta_initial: float,
    a_initial: float,
) -> dict[str, float]:
    """Public Lowell-regular startup formulas used by backend-owned seed builders."""
    return _seed_formulae(
        k_comoving=float(k_comoving),
        eta_initial=float(eta_initial),
        a_initial=float(a_initial),
    )


def pack_regular_adiabatic_seed_from_formulae(
    *,
    a_initial: float,
    L_max: int,
    formulas: dict[str, float],
) -> np.ndarray:
    """Pack a Lowell-regular startup vector from precomputed formula values."""
    a_val = float(a_initial)
    if not np.isfinite(a_val) or a_val <= 0.0:
        raise ValueError(
            f"a_initial must be finite and positive, got {a_initial!r}"
        )
    if L_max < 2:
        raise ValueError(
            f"L_max must be >= 2 for the E-mode startup, got L_max={L_max}"
        )
    photon_T = zero_hierarchy(L_max)
    photon_E = zero_polarization_hierarchy(L_max)
    photon_T.tensors[0].components[0] = float(formulas["delta_gamma"]) / 4.0
    photon_T.tensors[1].components[1] = float(formulas["theta_gamma"])
    photon_T.tensors[2].components[2] = float(formulas["pi_gamma"])
    photon_E.E.tensors[2].components[2] = float(formulas["E_2"])
    nu = np.array(
        [
            float(formulas["delta_nu"]),
            float(formulas["theta_nu"]),
            float(formulas["pi_nu"]),
            float(formulas["G_3"]),
        ],
        dtype=np.float64,
    )
    prefix = pack_combined_state(
        a=a_val,
        Sigma_plus=0.0,
        Sigma_minus=0.0,
        photon_T=photon_T,
        photon_E=photon_E,
        neutrino_reduced=nu,
        L_max=L_max,
    )
    extras = np.array(
        [
            float(formulas["delta_b"]),
            float(formulas["theta_b"]),
            float(formulas["delta_c"]),
            float(formulas["theta_c"]),
            float(formulas["eta_cov"]),
            float(formulas["Z"]),
        ],
        dtype=np.float64,
    )
    out = np.empty(prefix.size + CAMB_REGULAR_ADIABATIC_EXTRA_SIZE, dtype=np.float64)
    out[: prefix.size] = prefix
    out[prefix.size :] = extras
    return out


def make_camb_regular_adiabatic_seed(
    *,
    k_comoving: float,
    eta_initial: float,
    a_initial: float,
    L_max: int,
    b_k_sq: float = 1.0,
) -> np.ndarray:
    """Build the FB-5.3 regular-adiabatic startup vector.

    The FLRW-limit formulas follow Lowell §13.2. The photon tower stores
    only the ``m = 0`` slice at startup:

    - ``Π_0(m=0) = delta_gamma / 4``
    - ``Π_1(m=0) = theta_gamma``
    - ``Π_2(m=0) = pi_gamma`` (TCA startup)
    - ``E_2(m=0) = E_2``

    Higher moments remain zero.
    """
    k_val = float(k_comoving)
    eta_val = float(eta_initial)
    a_val = float(a_initial)
    if not np.isfinite(k_val) or k_val < 0.0:
        raise ValueError(
            f"k_comoving must be finite and non-negative, got {k_comoving!r}"
        )
    if not np.isfinite(eta_val) or eta_val <= 0.0:
        raise ValueError(
            f"eta_initial must be finite and positive, got {eta_initial!r}"
        )
    if not np.isfinite(a_val) or a_val <= 0.0:
        raise ValueError(
            f"a_initial must be finite and positive, got {a_initial!r}"
        )
    if L_max < 2:
        raise ValueError(
            f"L_max must be >= 2 for the E-mode startup, got L_max={L_max}"
        )
    if k_val == 0.0:
        prefix = zero_IC(L_max=L_max, a_initial=a_val)
        out = np.zeros(
            prefix.size + CAMB_REGULAR_ADIABATIC_EXTRA_SIZE,
            dtype=np.float64,
        )
        out[: prefix.size] = prefix
        return out

    formulas = _seed_formulae(
        k_comoving=k_val,
        eta_initial=eta_val,
        a_initial=a_val,
        b_k_sq=float(b_k_sq),
    )
    return pack_regular_adiabatic_seed_from_formulae(
        a_initial=a_val,
        L_max=L_max,
        formulas=formulas,
    )


def unpack_camb_regular_adiabatic_seed(
    seed_state: np.ndarray,
    *,
    L_max: int | None = None,
) -> dict[str, object]:
    """Unpack the FB-5.3 seed into structured fields."""
    arr = np.asarray(seed_state, dtype=np.float64)
    if arr.ndim != 1:
        raise ValueError(
            f"seed_state must be 1-D, got shape {arr.shape}"
        )
    if L_max is None:
        L_max = infer_regular_adiabatic_seed_L_max(arr.size)
    expected = regular_adiabatic_seed_total_size(L_max)
    if arr.shape != (expected,):
        raise ValueError(
            f"seed_state shape {arr.shape} != ({expected},) for L_max={L_max}"
        )
    prefix_n = combined_total_size(L_max)
    combined = unpack_combined_state(arr[:prefix_n], L_max=L_max)
    extras = arr[slice_regular_adiabatic_extras(L_max)].copy()
    return {
        "L_max": L_max,
        "combined": combined,
        "extras": extras,
        "delta_b": _extra_value(extras, "delta_b"),
        "theta_b": _extra_value(extras, "theta_b"),
        "delta_c": _extra_value(extras, "delta_c"),
        "theta_c": _extra_value(extras, "theta_c"),
        "eta_cov": _extra_value(extras, "eta_cov"),
        "Z": _extra_value(extras, "Z"),
    }


def seed_observables(
    seed_state: np.ndarray,
    *,
    L_max: int | None = None,
) -> dict[str, float]:
    """Return the named startup observables carried by a packed seed."""
    unpacked = unpack_camb_regular_adiabatic_seed(seed_state, L_max=L_max)
    combined = unpacked["combined"]
    assert combined is not None
    L_max_eff = int(unpacked["L_max"])

    photon_T = combined.photon_T
    photon_E = combined.photon_E.E
    theta_gamma = (
        float(photon_T.tensors[1].components[1]) if L_max_eff >= 1 else 0.0
    )
    pi_gamma = (
        float(photon_T.tensors[2].components[2]) if L_max_eff >= 2 else 0.0
    )
    E_2 = float(photon_E.tensors[2].components[2]) if L_max_eff >= 2 else 0.0
    nu = np.asarray(combined.neutrino_reduced, dtype=np.float64)
    return {
        "a": float(combined.a),
        "Sigma_plus": float(combined.Sigma_plus),
        "Sigma_minus": float(combined.Sigma_minus),
        "delta_gamma": 4.0 * float(photon_T.tensors[0].components[0]),
        "theta_gamma": theta_gamma,
        "pi_gamma": pi_gamma,
        "E_2": E_2,
        "delta_nu": float(nu[0]),
        "theta_nu": float(nu[1]),
        "pi_nu": float(nu[2]),
        "G_3": float(nu[3]),
        "delta_b": float(unpacked["delta_b"]),
        "theta_b": float(unpacked["theta_b"]),
        "delta_c": float(unpacked["delta_c"]),
        "theta_c": float(unpacked["theta_c"]),
        "eta_cov": float(unpacked["eta_cov"]),
        "Z": float(unpacked["Z"]),
    }


# Keep the LB-5 zero-IC anchor reachable from this module; several FB-5
# tests compare their k -> 0 prefix against the shipped background-only
# layout.
_ = zero_IC
_ = slice_neutrino_reduced
_ = NEUTRINO_REDUCED_SIZE
