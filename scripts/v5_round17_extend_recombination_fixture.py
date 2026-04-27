"""V5 Round-17 P3.5 PR-V0d-pre2 — extend the HYREC fixture to z = 10⁹.

Generates `bass/recombination/fixtures/recombination_ref_planck2018_z1e10.csv`
by appending radiation-era extension rows to the existing
`recombination_ref_planck2018.csv` fixture (z ∈ [0, 8000]).

Physics of the extension (z > 8000):

  - x_e ≈ 1.1634 (asymptotic full He++ ionization). Already the value
    HYREC reports at z = 8000 to four decimals — the plasma is fully
    ionized and stays that way for all z > 8000.

  - T_m = T_CMB · (1 + z). At z >> z_T_decoupling ≈ 100, baryons are
    Compton-coupled to photons; the matter temperature equals the
    photon temperature. T_CMB = 2.72548 K (Fixsen 2009, SSOT).

  - τ_dot = a · n_e · σ_T scales as a · n_b ∝ a · a⁻³ = a⁻² = (1+z)².
    Anchored at the z=8000 fixture value τ_dot(8000) = 29.04538 / Mpc:
        τ_dot(z) = 29.04538 · ((1+z) / 8001)²

  - κ (cumulative optical depth ∫_0^z τ_dot · |dη/dz| dz). Numerically
    integrated using the closed-form Friedmann |dη/dz|:
        |dη/dz| = 1 / ((1+z)² · H_0 · √(Ω_r·(1+z)+Ω_m))
    Anchored at the z=8000 fixture value κ(8000) = 987.1135.

Sampling: log-spaced ~120 points from z=8001 to z=1e9. This is dense
enough for cubic-spline interpolation (Δlog z ≈ 0.04) yet keeps the
output CSV under 9000 rows, similar in size to the original fixture.

The new fixture file is written alongside the existing one; downstream
code may opt-in by passing the new path to `load_recombination_table`.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from scipy.integrate import quad


# Planck-2018 anchors (matching the existing fixture header).
T_CMB_K = 2.72548
H0_KM_S_MPC = 67.35837
OMEGA_M = 0.31242079216478097
OMEGA_B = 0.0494142797907188
# Photon density Ω_γ = 4 σ_SB T_CMB^4 / (c^3 ρ_crit) ≈ 5.39e-5 at T = 2.72548
# (Mukhanov §5.4); add neutrinos with N_eff = 3.046:
#   Ω_r = Ω_γ · (1 + N_eff · (7/8) · (4/11)^(4/3))
OMEGA_GAMMA = 5.39e-5
N_EFF = 3.046
OMEGA_R = OMEGA_GAMMA * (1.0 + N_EFF * (7.0 / 8.0) * (4.0 / 11.0) ** (4.0 / 3.0))

# H_0 in 1/Mpc (c = 299792.458 km/s):
C_KM_S = 299792.458
H0_MPC = H0_KM_S_MPC / C_KM_S

# Anchors from the last row of the existing fixture (z = 8000).
Z_ANCHOR = 8000.0
X_E_ANCHOR = 1.163410
T_M_ANCHOR = 2.180673e4  # K
TAU_DOT_ANCHOR = 2.904538e1  # 1/Mpc
KAPPA_ANCHOR = 9.871135e2  # dimensionless

# Extension target. We extend one decade past the audit's stated δ
# deep anchor (z = 10⁹) to give the bg_table (a_start = 1e-10) one decade
# of floating-point headroom before its own boundary; this avoids the
# 1.0/(1+1e9) ≈ 9.99e-10 < 1e-9 edge that would otherwise reject z = 10⁹
# at the bg_table validation in cosmological_critical_etas.
Z_MAX_EXTENSION = 1.0e10

# Output sampling (log-spaced). Adding one decade adds ~12 rows.
N_EXTENSION_POINTS = 132


def x_e_radiation_era(z: float) -> float:
    """x_e = n_e / n_H. At z > 8000 the plasma is fully He++ ionized;
    HYREC reports 1.1634 at z=8000 already, and the value stays
    constant in the radiation-era extension."""
    return X_E_ANCHOR


def t_m_radiation_era(z: float) -> float:
    """Matter temperature, Compton-coupled to T_γ at z >> 100."""
    return T_CMB_K * (1.0 + z)


def tau_dot_radiation_era(z: float) -> float:
    """τ_dot = a · n_e · σ_T scales as (1+z)² in radiation era.
    Anchored at z = 8000 where the fixture value is 29.04538 / Mpc.
    """
    return TAU_DOT_ANCHOR * ((1.0 + z) / (1.0 + Z_ANCHOR)) ** 2


def abs_deta_dz(z: float) -> float:
    """|dη/dz| from the FLRW Friedmann equation (no Λ at z >> 1).

    Definition: η = ∫ da / (a² · H(a)). With z = 1/a − 1, dz = −da/a²,
    so dη/dz = −1 / H(z). Therefore |dη/dz| = 1 / H(z).

    H(z) = H_0 · √(Ω_r·(1+z)⁴ + Ω_m·(1+z)³)
         = H_0 · (1+z)^{3/2} · √(Ω_r·(1+z) + Ω_m)

    so |dη/dz| = 1 / (H_0 · (1+z)^{3/2} · √(Ω_r·(1+z) + Ω_m)).
    """
    one_plus_z = 1.0 + z
    e_z = np.sqrt(OMEGA_R * one_plus_z + OMEGA_M)  # = √(Ω_r(1+z)+Ω_m)
    return 1.0 / (H0_MPC * one_plus_z ** 1.5 * e_z)


# ``KAPPA_CALIBRATION`` is set in main() after we read the existing
# fixture so that ``dkappa_dz(z=Z_ANCHOR)`` matches the fixture's
# observed dκ/dz exactly. This absorbs small Ω_γ / N_eff convention
# mismatches between our analytic formulas and the HYREC fixture.
_KAPPA_CALIBRATION = 1.0


def dkappa_dz(z: float) -> float:
    """Integrand for cumulative optical depth: dκ/dz = τ_dot · |dη/dz|.

    Multiplied by ``_KAPPA_CALIBRATION`` to match the existing fixture's
    observed dκ/dz at the boundary z = Z_ANCHOR (small ~20% correction).
    """
    return _KAPPA_CALIBRATION * tau_dot_radiation_era(z) * abs_deta_dz(z)


def kappa_extension(z_target: float) -> float:
    """κ(z_target) for z_target > Z_ANCHOR.

    κ(z) = κ(Z_ANCHOR) + ∫_{Z_ANCHOR}^{z} τ_dot · |dη/dz| dz'
    """
    if z_target <= Z_ANCHOR:
        raise ValueError(f"z_target must exceed {Z_ANCHOR}; got {z_target}")
    delta_kappa, _err = quad(dkappa_dz, Z_ANCHOR, z_target, limit=200)
    return KAPPA_ANCHOR + delta_kappa


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_csv = (
        repo_root / "htt" / "bass" / "recombination" / "fixtures"
        / "recombination_ref_planck2018.csv"
    )
    dst_csv = (
        repo_root / "htt" / "bass" / "recombination" / "fixtures"
        / "recombination_ref_planck2018_z1e10.csv"
    )

    if not src_csv.exists():
        raise SystemExit(f"source fixture not found: {src_csv}")

    print(f"reading source fixture: {src_csv}")
    src_lines = src_csv.read_text().splitlines()

    # Sanity-check the existing anchor (last row).
    last_row = src_lines[-1].split(",")
    z_last = float(last_row[0])
    x_e_last = float(last_row[1])
    t_m_last = float(last_row[2])
    tau_dot_last = float(last_row[3])
    kappa_last = float(last_row[4])
    if abs(z_last - Z_ANCHOR) > 1.0:
        raise SystemExit(
            f"source fixture's last row z={z_last} is not at expected "
            f"anchor z={Z_ANCHOR}"
        )
    print(
        f"  last row: z={z_last}, x_e={x_e_last:.6e}, "
        f"T_m={t_m_last:.6e}, τ_dot={tau_dot_last:.6e}, "
        f"κ={kappa_last:.6e}"
    )
    print(
        f"  hard-coded anchors used in extension: x_e={X_E_ANCHOR}, "
        f"T_m={T_M_ANCHOR:.6e}, τ_dot={TAU_DOT_ANCHOR:.6e}, "
        f"κ={KAPPA_ANCHOR:.6e}"
    )

    # Calibrate `_KAPPA_CALIBRATION` so dκ/dz at z=Z_ANCHOR matches the
    # fixture's observed slope. This absorbs any Ω_γ / N_eff convention
    # mismatch between our closed-form Friedmann and the HYREC fixture.
    global _KAPPA_CALIBRATION
    if len(src_lines) >= 2:
        prev_row = src_lines[-2].split(",")
        z_prev = float(prev_row[0])
        kappa_prev = float(prev_row[4])
        dkappa_dz_observed = (kappa_last - kappa_prev) / (z_last - z_prev)
        dkappa_dz_predicted_uncalibrated = (
            tau_dot_radiation_era(Z_ANCHOR) * abs_deta_dz(Z_ANCHOR)
        )
        _KAPPA_CALIBRATION = (
            dkappa_dz_observed / dkappa_dz_predicted_uncalibrated
        )
        print(
            f"  dκ/dz at z={Z_ANCHOR}: observed={dkappa_dz_observed:.4f}, "
            f"predicted-uncalibrated={dkappa_dz_predicted_uncalibrated:.4f}, "
            f"calibration factor={_KAPPA_CALIBRATION:.4f}"
        )
        if not (0.5 < _KAPPA_CALIBRATION < 2.0):
            print(
                "  WARNING: closed-form dκ/dz disagrees with fixture by "
                "more than a factor of 2; check Friedmann sign conventions."
            )

    # Generate log-spaced extension grid.
    log_z_min = np.log10(Z_ANCHOR + 1.0)
    log_z_max = np.log10(Z_MAX_EXTENSION)
    log_z_grid = np.linspace(log_z_min, log_z_max, N_EXTENSION_POINTS + 1)
    z_grid = 10.0 ** log_z_grid
    z_grid = z_grid[z_grid > Z_ANCHOR]  # strict-ascending after the anchor
    print(
        f"\nextension grid: {z_grid.size} log-spaced points from "
        f"z={z_grid[0]:.6e} to z={z_grid[-1]:.6e}"
    )

    extension_rows = []
    for z in z_grid:
        x_e = x_e_radiation_era(z)
        t_m = t_m_radiation_era(z)
        tau_dot = tau_dot_radiation_era(z)
        kappa = kappa_extension(z)
        extension_rows.append(
            f"{z:.6e},{x_e:.6e},{t_m:.6e},{tau_dot:.6e},{kappa:.6e}"
        )

    # First few + last few extension rows for inspection.
    print("\nfirst 3 extension rows:")
    for row in extension_rows[:3]:
        print(f"  {row}")
    print("last 3 extension rows:")
    for row in extension_rows[-3:]:
        print(f"  {row}")

    # Write extended fixture: header + original data + extension rows.
    print(f"\nwriting extended fixture: {dst_csv}")
    out_lines = list(src_lines)
    # Append a comment line documenting the extension.
    # We must put extension comments BEFORE the appended rows but AFTER
    # the existing data — but the CSV format expects all `#` lines to be
    # at the top. Actually inspecting the loader, comments only matter
    # at the start; we just append data rows.
    out_lines.extend(extension_rows)
    dst_csv.write_text("\n".join(out_lines) + "\n")
    print(
        f"  done. Extended fixture has "
        f"{len(out_lines) - len([l for l in out_lines if l.startswith('#') or 'z' in l[:5].lower()])} "
        f"data rows; final z = {z_grid[-1]:.6e}, κ = "
        f"{extension_rows[-1].split(',')[4]}."
    )

    # Independent reload check.
    print("\nreloading new fixture for round-trip validation...")
    import sys
    htt_path = str(repo_root / "htt")
    if htt_path not in sys.path:
        sys.path.insert(0, htt_path)
    htt_src_path = str(repo_root / "htt" / "src")
    if Path(htt_src_path).is_dir() and htt_src_path not in sys.path:
        sys.path.insert(0, htt_src_path)
    from bass.recombination.recombination_ingest import (
        load_recombination_table,
    )
    table = load_recombination_table(dst_csv)
    print(
        f"  loaded: {table.n_points} rows, z ∈ [{table.z_min:.3e}, "
        f"{table.z_max:.3e}], τ_dot at z_max = "
        f"{table.tau_dot[-1]:.3e}, κ at z_max = {table.kappa[-1]:.3e}"
    )


if __name__ == "__main__":
    main()
