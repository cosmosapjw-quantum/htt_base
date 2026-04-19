"""
bass/recombination/reionization.py  (Week 8-02)
================================================

Reionization tanh model. Extends the W8-01 recombination table with
late-time H and HeII reionization bumps, and re-integrates τ̇, κ on the
extended grid (including z < W8-01 z_min down to z = 0).

Scope
-----
- Tanh parameterization in y = (1+z)^{3/2} space (standard CAMB/CLASS)
- H + HeI simultaneous reionization at z_rei_H ≈ 7.67 (Planck 2018)
- HeII → HeIII second reionization at z_rei_HeII ≈ 3.5 (optional)
- Y_He-consistent amplitudes via f_He = Y_He/(4(1-Y_He))
- Extends z grid downward to include z = 0 (reion era)
- Recomputes τ̇(z) and κ(z) with combined x_e_total
- Planck 2018 τ_reion ≈ 0.054 reproducibility

Equations
---------
  y(z) = (1+z)^{3/2}
  Δy   = (3/2)(1+z_rei)^{1/2} × Δz    [width conversion z → y space]

Hydrogen + HeI combined reionization:
  x_e^{rei,H}(z) = (1 + f_He)/2 × [1 + tanh((y_H - y(z))/Δy_H)]

HeII → HeIII second reionization (optional):
  x_e^{rei,HeII}(z) = f_He/2 × [1 + tanh((y_HeII - y(z))/Δy_HeII)]

with f_He = Y_He / (4(1-Y_He)) (electron count per H for fully ionized He).

Combined:
  x_e_total(z) = x_e_recomb(z) + x_e^{rei,H}(z) + x_e^{rei,HeII}(z)

τ̇ and κ recomputed from x_e_total using W8-01 cosmology.

Physical asymptotic limits
--------------------------
  z → 0     : x_e_total → 1 + 2 f_He ≈ 1.163 (both reionizations done)
  3.5 < z < 7.67 : x_e_total → 1 + f_He ≈ 1.081 (H reion done, HeII pending)
  z > 20    : x_e_total → x_e_recomb only (reion negligible)

Not in scope (deferred)
-----------------------
- Multi-component reionization (additional bumps, e.g. BBH/PBH DM decay)
- Non-tanh (step function, asymmetric) models
- T_m post-reionization heating (set constant from W8-01 baseline)
- Full cosmology dependence: uses the cosmology baked into the input
  recombination table's metadata; caller must ensure consistency

References
----------
- Planck 2018 results VI. Cosmological parameters (τ = 0.054 ± 0.007)
- Lewis 2008 (arXiv:0804.3865, CAMB reionization parameterization)
- Document §4.2 (textbook framework, reionization bump)
- MASTER_PROMPT_LIST_bass_py_v1.2.md §4 W8-02
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Union

import numpy as np

from bass.recombination.recombination_ingest import (
    RecombinationInterp,
    RecombinationTable,
    build_interpolators,
)


# ============================================================================
# Section 1 - Physical constants (for τ̇ recomputation)
# ============================================================================

C_LIGHT = 299792458.0              # m/s
SIGMA_T = 6.6524587321e-29         # m² (Thomson cross section)
M_H = 1.67353272e-27               # kg (H atom mass ≈ m_p)
G_NEWTON = 6.67430e-11             # m³/(kg s²)
MPC_M = 3.0856775814913673e22      # Mpc in meters
H_100 = 100.0 * 1000.0 / MPC_M     # 100 km/s/Mpc in 1/s
SEC_PER_MPC = MPC_M / C_LIGHT      # seconds for light to travel 1 Mpc


# ============================================================================
# Section 2 - Cosmology extraction from W8-01 metadata
# ============================================================================

@dataclass(frozen=True)
class CosmologyForRecombination:
    """Minimal cosmology specification for τ̇ and H(z) computation.

    All fields in standard cosmology units:
      h = H_0 / (100 km/s/Mpc)
      T_cmb : K
      Y_He : mass fraction
      Omega_b, Omega_m, Omega_r, Omega_Lambda : density parameters today
    """
    h: float
    T_cmb: float
    Omega_b: float
    Y_He: float
    Omega_m: float
    Omega_r: float
    Omega_Lambda: float

    def __post_init__(self) -> None:
        if not 0 < self.h < 2:
            raise ValueError(f"h out of reasonable range: {self.h}")
        if not 0 < self.T_cmb < 10:
            raise ValueError(f"T_cmb out of reasonable range: {self.T_cmb}")
        if not 0 < self.Omega_b < 1:
            raise ValueError(f"Omega_b out of range: {self.Omega_b}")
        if not 0 < self.Y_He < 1:
            raise ValueError(f"Y_He out of range: {self.Y_He}")

    @property
    def H_0_SI(self) -> float:
        """H_0 in 1/s."""
        return self.h * H_100

    @property
    def rho_crit_SI(self) -> float:
        """Critical density today in kg/m³."""
        return 3.0 * self.H_0_SI ** 2 / (8.0 * np.pi * G_NEWTON)

    @property
    def n_H_today(self) -> float:
        """Hydrogen number density today in 1/m³."""
        rho_b = self.Omega_b * self.rho_crit_SI
        return rho_b * (1.0 - self.Y_He) / M_H

    @property
    def f_He(self) -> float:
        """Electron count per H nucleus when He is fully ionized:
        f_He = Y_He / (4 (1 - Y_He)). For Y_He=0.245, f_He ≈ 0.0811.
        """
        return self.Y_He / (4.0 * (1.0 - self.Y_He))

    def H_of_z(self, z: Union[float, np.ndarray]) -> np.ndarray:
        """H(z) in 1/s for flat ΛCDM."""
        one_plus_z = 1.0 + np.asarray(z)
        return self.H_0_SI * np.sqrt(
            self.Omega_m * one_plus_z ** 3
            + self.Omega_r * one_plus_z ** 4
            + self.Omega_Lambda
        )


def cosmology_from_metadata(
    metadata: Dict[str, str],
) -> CosmologyForRecombination:
    """Extract CosmologyForRecombination from a W8-01 table's metadata.

    Expected metadata keys (lowercased, as produced by the W8-01
    generator):
      h, t_cmb, omega_b, y_he, omega_m_total, omega_r_total,
      omega_lambda

    Raises KeyError if a required key is missing, or ValueError if
    any value cannot be parsed as a float.
    """
    required = [
        "h", "t_cmb", "omega_b", "y_he",
        "omega_m_total", "omega_r_total", "omega_lambda",
    ]
    missing = [k for k in required if k not in metadata]
    if missing:
        raise KeyError(
            f"cosmology metadata missing required keys: {missing}"
        )

    def _parse(key: str) -> float:
        raw = metadata[key].strip()
        # Strip trailing unit tokens like "K", "eV"
        for unit in [" K", " eV"]:
            if raw.endswith(unit):
                raw = raw[: -len(unit)].strip()
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(
                f"cosmology metadata {key} not parseable: {metadata[key]!r}"
            ) from exc

    return CosmologyForRecombination(
        h=_parse("h"),
        T_cmb=_parse("t_cmb"),
        Omega_b=_parse("omega_b"),
        Y_He=_parse("y_he"),
        Omega_m=_parse("omega_m_total"),
        Omega_r=_parse("omega_r_total"),
        Omega_Lambda=_parse("omega_lambda"),
    )


# ============================================================================
# Section 3 - Reionization parameters
# ============================================================================

@dataclass(frozen=True)
class ReionizationParameters:
    """Tanh reionization bump parameters.

    Attributes
    ----------
    z_reion_H : float
        Midpoint redshift of combined H + HeI → HeII reionization.
        Planck 2018 default: 7.67.
    delta_z_H : float
        Width of H reionization transition in z-space.
        Default 0.5 (CAMB default).
    z_reion_HeII : float
        Midpoint of HeII → HeIII reionization. Default 3.5.
    delta_z_HeII : float
        Width. Default 0.5.
    include_HeII : bool
        Toggle for HeII second reionization. Default True.
    """
    z_reion_H: float = 7.67
    delta_z_H: float = 0.5
    z_reion_HeII: float = 3.5
    delta_z_HeII: float = 0.5
    include_HeII: bool = True

    def __post_init__(self) -> None:
        if self.z_reion_H <= 0 or not np.isfinite(self.z_reion_H):
            raise ValueError(
                f"z_reion_H must be positive finite, got {self.z_reion_H}"
            )
        if self.delta_z_H <= 0:
            raise ValueError(
                f"delta_z_H must be positive, got {self.delta_z_H}"
            )
        if self.include_HeII:
            if (self.z_reion_HeII <= 0
                    or not np.isfinite(self.z_reion_HeII)):
                raise ValueError(
                    f"z_reion_HeII must be positive finite when enabled"
                )
            if self.delta_z_HeII <= 0:
                raise ValueError(
                    f"delta_z_HeII must be positive, got {self.delta_z_HeII}"
                )


def _y_of_z(z: Union[float, np.ndarray]) -> np.ndarray:
    """y(z) = (1+z)^{3/2} — tanh parameterization coordinate."""
    return np.power(1.0 + np.asarray(z, dtype=float), 1.5)


def _delta_y_from_delta_z(z_rei: float, delta_z: float) -> float:
    """Width in y-space corresponding to Δz at z_rei:
       Δy = (dy/dz)|_{z_rei} × Δz = (3/2)(1+z_rei)^{1/2} × Δz.
    """
    return 1.5 * np.sqrt(1.0 + z_rei) * delta_z


# ============================================================================
# Section 4 - x_e_reion(z) pure function
# ============================================================================

def tanh_reionization_xe(
    z: Union[float, np.ndarray],
    reion_params: ReionizationParameters,
    f_He: float,
) -> np.ndarray:
    """Reionization x_e contribution (H + HeI + optional HeII).

    Returns array matching shape of z, or scalar if z is scalar.

    Formula
    -------
    x_e^{rei}(z) = x_e^{rei,H}(z) + x_e^{rei,HeII}(z)

    with each bump:
      x_e^{rei,i}(z) = (amplitude_i / 2) × [1 + tanh((y_i - y(z))/Δy_i)]

    amplitude_H = 1 + f_He  (H⁺ + HeI→HeII, adds 1 e⁻ per H and f_He e⁻ per H)
    amplitude_HeII = f_He    (HeII→HeIII, adds f_He e⁻ per H)

    Sign: at z > z_rei, y > y_rei, (y_rei - y) < 0, tanh → -1,
    (1 + tanh) → 0; no reionization yet. At z < z_rei, reverse,
    full amplitude reached.

    No W3 gate: pure algebra.
    """
    z_arr = np.asarray(z, dtype=float)
    y_z = _y_of_z(z_arr)

    # H + HeI first reionization
    y_H = _y_of_z(reion_params.z_reion_H)
    dy_H = _delta_y_from_delta_z(
        reion_params.z_reion_H, reion_params.delta_z_H,
    )
    amp_H = 1.0 + f_He
    x_e_H = 0.5 * amp_H * (1.0 + np.tanh((y_H - y_z) / dy_H))

    # HeII → HeIII second reionization
    if reion_params.include_HeII:
        y_HeII = _y_of_z(reion_params.z_reion_HeII)
        dy_HeII = _delta_y_from_delta_z(
            reion_params.z_reion_HeII, reion_params.delta_z_HeII,
        )
        amp_HeII = f_He
        x_e_HeII = 0.5 * amp_HeII * (
            1.0 + np.tanh((y_HeII - y_z) / dy_HeII)
        )
    else:
        x_e_HeII = np.zeros_like(z_arr)

    total = x_e_H + x_e_HeII
    return total if np.ndim(z) > 0 else float(total)


# ============================================================================
# Section 5 - Extended τ̇ and κ computation
# ============================================================================

def compute_tau_dot_conformal_Mpc(
    z: np.ndarray,
    x_e: np.ndarray,
    cosmology: CosmologyForRecombination,
) -> np.ndarray:
    """Conformal Thomson opacity τ̇(z) in 1/Mpc.

    τ̇ = a × n_e × σ_T × c  [in SI 1/s, then converted to 1/Mpc]
    n_e(z) = x_e(z) × n_H(0) × (1+z)³
    a(z) = 1 / (1+z)
    """
    n_e = x_e * cosmology.n_H_today * (1.0 + z) ** 3       # 1/m³
    a = 1.0 / (1.0 + z)
    tau_dot_SI = a * n_e * SIGMA_T * C_LIGHT               # 1/s
    return tau_dot_SI * SEC_PER_MPC                        # 1/Mpc


def compute_kappa_from_tau_dot(
    z: np.ndarray,
    tau_dot_Mpc: np.ndarray,
    cosmology: CosmologyForRecombination,
) -> np.ndarray:
    """Optical depth κ(z) = ∫_0^z τ̇/H dz'.

    Using conformal τ̇ and H(z), this integrand is scale-factor free:
    the (1+z) from τ̇_conformal = a × τ̇_physical cancels the (1+z)
    from dt/dz = -1/((1+z)H).

    The z grid is assumed strictly ascending.
    """
    H_SI = cosmology.H_of_z(z)
    H_Mpc = H_SI * SEC_PER_MPC                # 1/Mpc
    integrand = tau_dot_Mpc / H_Mpc           # dimensionless per dz
    # Trapezoidal integration with kappa(z[0]) = 0
    kappa = np.zeros_like(z)
    for i in range(1, len(z)):
        dz = z[i] - z[i - 1]
        kappa[i] = kappa[i - 1] + 0.5 * (
            integrand[i] + integrand[i - 1]
        ) * dz
    return kappa


# ============================================================================
# Section 6 - Extend table with reionization
# ============================================================================

def extend_table_with_reionization(
    recomb_table: RecombinationTable,
    reion_params: ReionizationParameters,
    cosmology: Optional[CosmologyForRecombination] = None,
    z_low: float = 0.0,
    n_low_points: int = 100,
) -> RecombinationTable:
    """Produce a new RecombinationTable that includes reionization.

    Procedure
    ---------
    1. Extract cosmology from recomb_table.metadata if not provided.
    2. Build an extended z grid from `z_low` up to recomb_table.z_max:
         - n_low_points ascending from z_low to just below recomb.z_min
         - recomb_table.z grid unchanged
    3. x_e_recomb on extended grid: interpolated from recomb_table;
       for z < recomb_table.z_min, held constant at the freeze-out value.
    4. x_e_total = x_e_recomb + tanh_reionization_xe(z, reion, f_He)
    5. T_m on extension: held constant at recomb_table.T_m[0] (adiabatic-
       cooled value; T_m is not used in τ̇ calculation but maintained
       for container consistency; physical post-reion T_m ~ 10^4 K is
       not modeled here).
    6. τ̇, κ recomputed on the extended grid using cosmology.

    Returns a new RecombinationTable sharing the metadata of the input
    plus reionization-specific annotations.
    """
    if cosmology is None:
        cosmology = cosmology_from_metadata(recomb_table.metadata)

    # Step 2: Build extended z grid
    z_recomb = recomb_table.z
    if z_low >= z_recomb[0]:
        # No extension needed (or requested z_low is inside table)
        z_ext = z_recomb.copy()
    else:
        # Extension points strictly below z_recomb[0]
        if n_low_points < 2:
            raise ValueError(
                f"n_low_points must be ≥ 2, got {n_low_points}"
            )
        # Log-spaced below z_recomb[0] for better resolution in the
        # reion plateau (z ~ 1 to 10)
        z_ext_low = np.linspace(z_low, z_recomb[0], n_low_points + 1)[:-1]
        # Exclude the exact boundary z_recomb[0] to avoid duplicates
        z_ext = np.concatenate([z_ext_low, z_recomb])

    # Step 3: x_e_recomb on extended grid
    # For z >= z_recomb[0]: use table directly
    # For z < z_recomb[0]: constant extrapolation (freeze-out)
    interp = build_interpolators(recomb_table)
    x_e_recomb_ext = np.zeros_like(z_ext)
    in_table_mask = z_ext >= z_recomb[0]
    x_e_recomb_ext[in_table_mask] = interp.query_x_e(z_ext[in_table_mask])
    x_e_recomb_ext[~in_table_mask] = recomb_table.x_e[0]

    # Step 4: combine with reionization
    x_e_rei = tanh_reionization_xe(z_ext, reion_params, cosmology.f_He)
    x_e_total = x_e_recomb_ext + x_e_rei

    # Step 5: T_m on extended grid (constant below table, from table above)
    T_m_ext = np.zeros_like(z_ext)
    T_m_ext[in_table_mask] = interp.query_T_m(z_ext[in_table_mask])
    T_m_ext[~in_table_mask] = recomb_table.T_m[0]

    # Step 6: recompute τ̇ and κ
    tau_dot_ext = compute_tau_dot_conformal_Mpc(
        z_ext, x_e_total, cosmology,
    )
    kappa_ext = compute_kappa_from_tau_dot(
        z_ext, tau_dot_ext, cosmology,
    )

    # Build annotated metadata
    new_metadata = dict(recomb_table.metadata)
    new_metadata["reionization"] = "tanh"
    new_metadata["z_reion_h"] = str(reion_params.z_reion_H)
    new_metadata["delta_z_h"] = str(reion_params.delta_z_H)
    new_metadata["include_heii"] = str(reion_params.include_HeII)
    if reion_params.include_HeII:
        new_metadata["z_reion_heii"] = str(reion_params.z_reion_HeII)
        new_metadata["delta_z_heii"] = str(reion_params.delta_z_HeII)

    return RecombinationTable(
        z=z_ext,
        x_e=x_e_total,
        T_m=T_m_ext,
        tau_dot=tau_dot_ext,
        kappa=kappa_ext,
        metadata=new_metadata,
        source_path=recomb_table.source_path,
    )


# ============================================================================
# Section 7 - Diagnostics
# ============================================================================

def compute_reionization_tau(
    reionized_table: RecombinationTable,
    z_high_cutoff: float = 30.0,
) -> float:
    """Reionization optical depth τ_reion = κ(z_high_cutoff) − κ(z=0).

    Uses z_high_cutoff ≈ 30 to capture the full reionization plateau
    (both H and HeII bumps) without including recombination
    contribution (which starts at z ~ 1000).

    For Planck 2018 default (z_H=7.67, Δz=0.5, z_HeII=3.5, Δz=0.5,
    Y_He=0.245), this returns τ_reion ≈ 0.0544 ± small corrections
    from the specific x_e_recomb(z < 30) baseline.
    """
    if z_high_cutoff <= reionized_table.z_min:
        raise ValueError(
            f"z_high_cutoff={z_high_cutoff} must be > z_min="
            f"{reionized_table.z_min}"
        )
    if z_high_cutoff > reionized_table.z_max:
        raise ValueError(
            f"z_high_cutoff={z_high_cutoff} must be ≤ z_max="
            f"{reionized_table.z_max}"
        )
    interp = build_interpolators(reionized_table)
    kappa_high = interp.query_kappa(z_high_cutoff)
    kappa_low = float(reionized_table.kappa[0])  # κ at z_low (0 by default)
    return float(kappa_high - kappa_low)


def xe_asymptotic_limits(
    reion_params: ReionizationParameters,
    f_He: float,
) -> Dict[str, float]:
    """Analytical asymptotic x_e values for sanity checks.

    Returns dict with keys:
      high_z   : x_e at z >> z_reion_H (→ 0 reionization contribution)
      between  : x_e between HeII and H reion (after H+HeI, before HeII)
      low_z    : x_e at z << z_reion_HeII (after both reionizations)
    """
    high_z = 0.0  # tanh → -1 at both transitions
    # Between: H+HeI done (contributes 1+f_He), HeII not yet
    between = 1.0 + f_He
    # Low: both done
    low_z = 1.0 + 2.0 * f_He if reion_params.include_HeII else 1.0 + f_He
    return {
        "high_z": high_z, "between": between, "low_z": low_z,
    }
