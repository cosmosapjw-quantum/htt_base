"""
bass/recombination/recombination_ingest.py  (Week 8-01)
=======================================================

Parse and interpolate recombination reference tables (e.g., from HyRec-2)
and expose them as callable interpolators for downstream BASS modules.

Scope
-----
- Input: CSV file with 5 columns (z, x_e, T_m, tau_dot, kappa) plus
  optional `# key = value` header metadata lines
- Output: RecombinationTable (frozen container) and RecombinationInterp
  (callable shape-preserving interpolators)
- Visibility function: g(z) = τ̇(z) × exp(−κ(z))
- Physical validation: x_e ∈ [0, 1.2], κ monotonically non-decreasing
  with z, τ̇ non-negative, z ascending
- Test fixtures: synthetic tanh + real HyRec-2 Planck 2018 table

Not in scope (deferred)
-----------------------
- Reionization bump (W8-02 scope; added on top of recombination x_e)
- η(z) conversion — requires cosmology choice, handled separately in
  integrator layer
- Derivative fields dτ̇/dz, dg/dz — callers compute as needed from
  the spline objects
- HyRec-2 binary subprocess integration — tables are pre-generated

Physics references
------------------
- Lee & Ali-Haïmoud 2020 (arXiv:2007.14114) — HyRec-2 paper
- Ali-Haïmoud & Hirata 2011 (arXiv:1011.3758) — HyRec paper
- Document §4.1 (textbook framework, visibility-based source at
  recombination)
- MASTER_PROMPT_LIST_bass_py_v1.2.md §4 W8-01

Design notes
------------
- CSV header supports arbitrary `# key = value` lines. Keys and values
  are stripped and stored in a metadata dict. Non-conforming comment
  lines are ignored (stored as raw) to accept hand-written headers.
- PCHIP interpolation via scipy.interpolate.PchipInterpolator. This
  preserves monotone optical-depth tables and avoids nonphysical
  negative opacity/visibility overshoot.
- Out-of-range z queries raise ValueError — no silent extrapolation
  to avoid downstream numerical silent failures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from scipy.interpolate import PchipInterpolator


# ============================================================================
# Section 1 - Parsed header metadata
# ============================================================================

def parse_recombination_header(
    lines: List[str],
) -> Tuple[Dict[str, str], List[str]]:
    """Extract `# key = value` pairs from header comment lines.

    Input
    -----
    lines : list of raw comment lines (those starting with '#'), with
        the leading '#' already stripped OR left as-is (both tolerated).

    Returns
    -------
    metadata : dict[str, str]
        All `key = value` pairs found, with keys lower-cased and
        whitespace-stripped. Values are stored as raw strings.
    unparsed : list[str]
        Comment lines that did not match `key = value` format, for
        round-trip preservation of free-form header text.

    Examples
    --------
    >>> parse_recombination_header([
    ...     "# h = 0.6735837",
    ...     "# Source: HyRec-2",
    ...     "# Omega_b = 0.04941",
    ... ])
    ({'h': '0.6735837', 'omega_b': '0.04941'},
     ['Source: HyRec-2'])
    """
    metadata: Dict[str, str] = {}
    unparsed: List[str] = []
    for line in lines:
        stripped = line.lstrip("#").strip()
        if not stripped:
            continue
        if "=" in stripped:
            key, _, value = stripped.partition("=")
            key = key.strip().lower()
            value = value.strip()
            if key and value:
                metadata[key] = value
                continue
        unparsed.append(stripped)
    return metadata, unparsed


# ============================================================================
# Section 2 - RecombinationTable container
# ============================================================================

@dataclass(frozen=True)
class RecombinationTable:
    """Immutable container for a parsed recombination reference table.

    Attributes
    ----------
    z : np.ndarray, shape (N,)
        Redshift grid, strictly ascending.
    x_e : np.ndarray, shape (N,)
        Free electron fraction (typically in [0, 1.2]; includes He
        over-ionization near onset).
    T_m : np.ndarray, shape (N,)
        Matter temperature in Kelvin.
    tau_dot : np.ndarray, shape (N,)
        Conformal Thomson opacity dτ/dη in 1/Mpc.
    kappa : np.ndarray, shape (N,)
        Optical depth ∫_0^z dτ from today to z (dimensionless).
    metadata : dict
        Parsed `key = value` pairs from header.
    source_path : str, optional
        Source file path, for provenance tracing.
    """
    z: np.ndarray
    x_e: np.ndarray
    T_m: np.ndarray
    tau_dot: np.ndarray
    kappa: np.ndarray
    metadata: Dict[str, str] = field(default_factory=dict)
    source_path: Optional[str] = None

    def __post_init__(self) -> None:
        # Shape consistency
        n = self.z.shape[0]
        for name, arr in [
            ("x_e", self.x_e), ("T_m", self.T_m),
            ("tau_dot", self.tau_dot), ("kappa", self.kappa),
        ]:
            if arr.shape != (n,):
                raise ValueError(
                    f"{name} shape {arr.shape} != z shape ({n},)"
                )
        # Finite check
        for name, arr in [
            ("z", self.z), ("x_e", self.x_e), ("T_m", self.T_m),
            ("tau_dot", self.tau_dot), ("kappa", self.kappa),
        ]:
            if not np.all(np.isfinite(arr)):
                raise ValueError(
                    f"{name} contains non-finite values"
                )
        # z monotonic ascending
        if np.any(np.diff(self.z) <= 0):
            raise ValueError(
                "z must be strictly ascending"
            )

    @property
    def n_points(self) -> int:
        return self.z.shape[0]

    @property
    def z_min(self) -> float:
        return float(self.z[0])

    @property
    def z_max(self) -> float:
        return float(self.z[-1])


# ============================================================================
# Section 3 - CSV loader
# ============================================================================

EXPECTED_COLUMNS = ["z", "x_e", "T_m", "tau_dot", "kappa"]


def load_recombination_table(
    path: Union[str, Path],
) -> RecombinationTable:
    """Parse a CSV recombination table with optional header metadata.

    Format:
      - Header lines starting with '#' (parsed as `# key = value`)
      - Single CSV column-name line (case-insensitive):
            z,x_e,T_m,tau_dot,kappa
      - Data rows with 5 comma-separated floats

    Raises
    ------
    FileNotFoundError, ValueError on format errors, schema mismatch,
    or validation failure.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"recombination table not found: {path}")

    header_comment_lines: List[str] = []
    column_line: Optional[str] = None
    data_lines: List[str] = []

    with path.open("r") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                header_comment_lines.append(line)
                continue
            if column_line is None:
                column_line = stripped
                continue
            data_lines.append(stripped)

    if column_line is None:
        raise ValueError(f"no data in {path}")

    # Validate schema
    col_names = [c.strip().lower() for c in column_line.split(",")]
    expected = [c.lower() for c in EXPECTED_COLUMNS]
    if col_names != expected:
        raise ValueError(
            f"column schema mismatch in {path}: got {col_names}, "
            f"expected {expected}"
        )

    if not data_lines:
        raise ValueError(f"no data rows in {path}")

    # Parse data
    try:
        arr = np.array(
            [[float(x) for x in row.split(",")] for row in data_lines],
            dtype=float,
        )
    except ValueError as exc:
        raise ValueError(f"failed to parse data in {path}: {exc}") from exc

    if arr.shape[1] != 5:
        raise ValueError(
            f"expected 5 columns, got {arr.shape[1]} in {path}"
        )

    # Sort by z ascending (tolerate input order)
    order = np.argsort(arr[:, 0])
    arr = arr[order]

    metadata, _unparsed = parse_recombination_header(header_comment_lines)
    return RecombinationTable(
        z=arr[:, 0].copy(),
        x_e=arr[:, 1].copy(),
        T_m=arr[:, 2].copy(),
        tau_dot=arr[:, 3].copy(),
        kappa=arr[:, 4].copy(),
        metadata=metadata,
        source_path=str(path),
    )


# ============================================================================
# Section 4 - Physical validation
# ============================================================================

# Physical bounds for validation.
X_E_MIN = 0.0
# Upper bound accounts for first He ionization boost (at z ≳ 2500,
# HeII-HeI transition; peak x_e ≈ 1.16 includes both H and He electrons).
X_E_MAX = 1.20
T_M_MIN_K = 0.0
T_M_MAX_K = 1.0e6  # generous bound
TAU_DOT_MIN = 0.0
KAPPA_MIN = 0.0


def validate_recombination_table(
    table: RecombinationTable,
) -> List[str]:
    """Validate physical reasonableness of a recombination table.

    Returns a list of error strings. Empty list means all checks pass.

    Checks
    ------
    1. x_e ∈ [X_E_MIN, X_E_MAX]
    2. T_m ∈ [T_M_MIN_K, T_M_MAX_K]
    3. τ̇ ≥ 0 everywhere
    4. κ ≥ 0 everywhere
    5. κ monotonically non-decreasing with z (optical depth accumulates)
    """
    errors: List[str] = []

    if np.any(table.x_e < X_E_MIN) or np.any(table.x_e > X_E_MAX):
        errors.append(
            f"x_e out of [{X_E_MIN}, {X_E_MAX}] range: "
            f"min={table.x_e.min():.4e}, max={table.x_e.max():.4e}"
        )
    if np.any(table.T_m < T_M_MIN_K) or np.any(table.T_m > T_M_MAX_K):
        errors.append(
            f"T_m out of [{T_M_MIN_K}, {T_M_MAX_K}] range: "
            f"min={table.T_m.min():.4e}, max={table.T_m.max():.4e}"
        )
    if np.any(table.tau_dot < TAU_DOT_MIN):
        errors.append(
            f"tau_dot has negative entries: min={table.tau_dot.min():.4e}"
        )
    if np.any(table.kappa < KAPPA_MIN):
        errors.append(
            f"kappa has negative entries: min={table.kappa.min():.4e}"
        )
    # kappa monotonically non-decreasing (tolerance for spline noise)
    dkappa = np.diff(table.kappa)
    if np.any(dkappa < -1e-10):
        idx = int(np.argmin(dkappa))
        errors.append(
            f"kappa not monotonically increasing at z~{table.z[idx]:.1f} "
            f"(dkappa={dkappa[idx]:.2e})"
        )
    return errors


# ============================================================================
# Section 5 - Shape-preserving interpolators
# ============================================================================

@dataclass(frozen=True)
class RecombinationInterp:
    """Shape-preserving interpolators for all 4 derived quantities.

    Queries outside [z_min, z_max] raise ValueError (no silent
    extrapolation). Use `query_*` methods to access values; each method
    accepts scalar or array z and returns matching shape.
    """
    table: RecombinationTable
    _spline_x_e: PchipInterpolator
    _spline_T_m: PchipInterpolator
    _spline_tau_dot: PchipInterpolator
    _spline_kappa: PchipInterpolator

    def _check_in_range(self, z: np.ndarray) -> None:
        if np.any(z < self.table.z_min) or np.any(z > self.table.z_max):
            raise ValueError(
                f"z out of table range [{self.table.z_min}, "
                f"{self.table.z_max}]: got min={np.min(z)}, "
                f"max={np.max(z)}"
            )

    def query_x_e(self, z: Union[float, np.ndarray]) -> np.ndarray:
        z_arr = np.atleast_1d(np.asarray(z, dtype=float))
        self._check_in_range(z_arr)
        result = self._spline_x_e(z_arr)
        return result if np.ndim(z) > 0 else float(result[0])

    def query_T_m(self, z: Union[float, np.ndarray]) -> np.ndarray:
        z_arr = np.atleast_1d(np.asarray(z, dtype=float))
        self._check_in_range(z_arr)
        result = self._spline_T_m(z_arr)
        return result if np.ndim(z) > 0 else float(result[0])

    def query_tau_dot(self, z: Union[float, np.ndarray]) -> np.ndarray:
        z_arr = np.atleast_1d(np.asarray(z, dtype=float))
        self._check_in_range(z_arr)
        result = self._spline_tau_dot(z_arr)
        return result if np.ndim(z) > 0 else float(result[0])

    def query_kappa(self, z: Union[float, np.ndarray]) -> np.ndarray:
        z_arr = np.atleast_1d(np.asarray(z, dtype=float))
        self._check_in_range(z_arr)
        result = self._spline_kappa(z_arr)
        return result if np.ndim(z) > 0 else float(result[0])

    def query_visibility(
        self,
        z: Union[float, np.ndarray],
    ) -> np.ndarray:
        """Visibility function g(z) = τ̇(z) × exp(−κ(z)).

        g peaks at the surface of last scattering (z ≈ 1089).
        """
        tau_dot = self.query_tau_dot(z)
        kappa = self.query_kappa(z)
        return tau_dot * np.exp(-kappa)


def build_interpolators(
    table: RecombinationTable,
) -> RecombinationInterp:
    """Construct monotone-safe interpolators from a RecombinationTable.

    Uses scipy.interpolate.PchipInterpolator so positive opacity and
    monotone optical-depth tables do not acquire spline overshoot between
    grid points.
    """
    return RecombinationInterp(
        table=table,
        _spline_x_e=PchipInterpolator(table.z, table.x_e),
        _spline_T_m=PchipInterpolator(table.z, table.T_m),
        _spline_tau_dot=PchipInterpolator(table.z, table.tau_dot),
        _spline_kappa=PchipInterpolator(table.z, table.kappa),
    )


# ============================================================================
# Section 6 - Synthetic fixture generator (for tests)
# ============================================================================

def make_synthetic_tanh_table(
    z_min: float = 1.0,
    z_max: float = 3000.0,
    n_points: int = 500,
    z_transition: float = 1089.0,
    transition_width: float = 100.0,
) -> RecombinationTable:
    """Generate a synthetic tanh-profile recombination table for tests.

    Not physically accurate — just a smooth monotone x_e(z) with the
    correct qualitative shape (high at high z, low at low z, transition
    near recombination). τ̇ and κ are derived from a simplified model
    suitable for unit tests.

    Used in test fixtures where we don't want to depend on the full
    HyRec reference table.
    """
    z = np.linspace(z_min, z_max, n_points)
    # x_e: tanh profile, near 1.0 at high z, near 0 at low z
    x_e = 0.5 * (1.0 + np.tanh((z - z_transition) / transition_width))
    # T_m: rough proportional to T_cmb = 2.725 × (1+z) [simplified]
    T_m = 2.725 * (1.0 + z)
    # τ̇: proportional to x_e × (1+z)²  (schematic: a × n_e ∝ (1+z)²)
    # normalized so τ̇(1089) ≈ 0.05 /Mpc
    tau_dot = x_e * (1.0 + z) ** 2 * 0.05 / (
        0.5 * (1090.0) ** 2
    )
    # κ: cumulative trapezoid integration of τ̇ × (dummy conversion)
    # For synthetic data, use a simple proportionality constant.
    kappa_integrand = tau_dot * 1.0e-2  # arbitrary scale
    kappa = np.zeros_like(z)
    for i in range(1, len(z)):
        kappa[i] = kappa[i - 1] + 0.5 * (
            kappa_integrand[i] + kappa_integrand[i - 1]
        ) * (z[i] - z[i - 1])

    return RecombinationTable(
        z=z, x_e=x_e, T_m=T_m, tau_dot=tau_dot, kappa=kappa,
        metadata={"source": "synthetic_tanh",
                  "z_transition": str(z_transition)},
    )


# ============================================================================
# Section 7 - Derived diagnostics
# ============================================================================

def find_last_scattering_redshift(
    interp: RecombinationInterp,
    target_kappa: float = 1.0,
    z_hint: float = 1089.0,
) -> float:
    """Find z such that κ(z) = target_kappa (default 1.0 = last scattering).

    Uses scipy.optimize.brentq on the interpolator. Raises ValueError
    if target_kappa is outside the tabulated range.
    """
    from scipy.optimize import brentq

    kappa_min = float(interp.table.kappa[0])
    kappa_max = float(interp.table.kappa[-1])
    if target_kappa < kappa_min or target_kappa > kappa_max:
        raise ValueError(
            f"target_kappa={target_kappa} outside table range "
            f"[{kappa_min:.3e}, {kappa_max:.3e}]"
        )

    def f(z: float) -> float:
        return float(interp.query_kappa(z)) - target_kappa

    # Guard against negative integrand noise at endpoints
    z_lo = interp.table.z_min
    z_hi = interp.table.z_max
    if f(z_lo) > 0 or f(z_hi) < 0:
        raise ValueError(
            "kappa does not bracket target_kappa in the table"
        )
    return float(brentq(f, z_lo, z_hi))


def find_visibility_peak(
    interp: RecombinationInterp,
    z_search_lo: float = 800.0,
    z_search_hi: float = 1400.0,
    n_samples: int = 2000,
) -> Tuple[float, float]:
    """Find (z_peak, g_peak) of the visibility function g = τ̇ exp(−κ).

    Dense sampling + parabolic refinement via quadratic fit around the
    coarse maximum.
    """
    # Clip search to table range
    z_search_lo = max(z_search_lo, interp.table.z_min)
    z_search_hi = min(z_search_hi, interp.table.z_max)
    if z_search_lo >= z_search_hi:
        raise ValueError(
            f"invalid search range [{z_search_lo}, {z_search_hi}]"
        )
    z_grid = np.linspace(z_search_lo, z_search_hi, n_samples)
    g_grid = interp.query_visibility(z_grid)
    idx = int(np.argmax(g_grid))
    if idx == 0 or idx == len(z_grid) - 1:
        return float(z_grid[idx]), float(g_grid[idx])
    # Parabolic fit around three neighbors
    x0, x1, x2 = z_grid[idx - 1], z_grid[idx], z_grid[idx + 1]
    y0, y1, y2 = g_grid[idx - 1], g_grid[idx], g_grid[idx + 1]
    denom = (x0 - x1) * (x0 - x2) * (x1 - x2)
    if abs(denom) < 1e-30:
        return float(x1), float(y1)
    a = (x2 * (y1 - y0) + x1 * (y0 - y2) + x0 * (y2 - y1)) / denom
    b = (x2 * x2 * (y0 - y1) + x1 * x1 * (y2 - y0) + x0 * x0 * (y1 - y2)) / denom
    if a >= 0:  # not a maximum
        return float(x1), float(y1)
    z_peak = -b / (2.0 * a)
    g_peak = float(interp.query_visibility(z_peak))
    return float(z_peak), g_peak
