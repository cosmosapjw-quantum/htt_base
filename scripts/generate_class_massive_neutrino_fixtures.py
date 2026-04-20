#!/usr/bin/env python3
"""Freeze CLASS background fixtures for the FB-9 massive-neutrino tests.

External-code policy: CLASS is used here once to generate frozen NPZ
oracles under ``data/class_massive_neutrino_fixtures/``. Production
code under ``htt/bass`` consumes only the shipped NPZ files.

The fixtures store the total three-species degenerate ``ncdm`` density
and pressure from CLASS, interpolated onto the shared BASS FLRW
background grid. This keeps the runtime regression on the exact same
``(a, eta)`` samples that ``MassiveNeutrinoBackground`` uses.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
HTT_ROOT = REPO_ROOT / "htt"
if str(HTT_ROOT) not in sys.path:
    sys.path.insert(0, str(HTT_ROOT))

from bass.species.background_table import build_flrw_background_table


PLANCK2018 = {
    "h": 0.6736,
    "omega_b": 0.02237,
    "omega_cdm": 0.12,
    "A_s": 2.1e-9,
    "n_s": 0.9649,
    "tau_reio": 0.0544,
}
SIGMA_MNU_VALUES = (0.06, 0.12, 0.24)
N_NCDM = 3
N_UR = 0.00441
T_NCDM_OVER_T_GAMMA = 0.71611
OUTPUT_DIR = REPO_ROOT / "data" / "class_massive_neutrino_fixtures"


def _script_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _class_version() -> str:
    import classy

    return str(getattr(classy, "__version__", "unknown"))


def _precision_settings() -> dict[str, object]:
    return {
        "output": "mPk",
        "P_k_max_1/Mpc": 1.0,
        "z_max_pk": 10.0,
        "background_interpolation": "log(a) onto bass.species FLRW grid",
        "N_ncdm": N_NCDM,
        "N_ur": N_UR,
        "T_ncdm_over_T_gamma": T_NCDM_OVER_T_GAMMA,
        "class_precision_mode": "default background precision",
    }


def _compute_class_background(sigma_mnu: float) -> dict[str, np.ndarray]:
    from classy import Class

    mass_eV = sigma_mnu / N_NCDM
    m_list = ",".join([f"{mass_eV:.8f}"] * N_NCDM)
    t_list = ",".join([f"{T_NCDM_OVER_T_GAMMA:.5f}"] * N_NCDM)

    cosmo = Class()
    cosmo.set(
        {
            **PLANCK2018,
            "N_ur": N_UR,
            "N_ncdm": N_NCDM,
            "m_ncdm": m_list,
            "T_ncdm": t_list,
            "output": "mPk",
            "P_k_max_1/Mpc": 1.0,
            "z_max_pk": 10.0,
        }
    )
    cosmo.compute()
    bg = cosmo.get_background()

    z = np.asarray(bg["z"], dtype=np.float64)
    a = 1.0 / (1.0 + z)
    rho_crit_0 = float(np.asarray(bg["(.)rho_crit"], dtype=np.float64)[-1])
    rho = sum(
        np.asarray(bg[f"(.)rho_ncdm[{idx}]"], dtype=np.float64)
        for idx in range(N_NCDM)
    ) / rho_crit_0
    p = sum(
        np.asarray(bg[f"(.)p_ncdm[{idx}]"], dtype=np.float64)
        for idx in range(N_NCDM)
    ) / rho_crit_0
    order = np.argsort(a)
    return {
        "a": a[order],
        "rho": rho[order],
        "p": p[order],
    }


def _interpolate_onto_bass_grid(
    sigma_mnu: float,
) -> dict[str, np.ndarray | float | str]:
    bg_table = build_flrw_background_table()
    class_bg = _compute_class_background(sigma_mnu)
    a_target = np.asarray(bg_table.a, dtype=np.float64)
    log_a_target = np.log(a_target)
    log_a_class = np.log(np.asarray(class_bg["a"], dtype=np.float64))
    rho = np.interp(log_a_target, log_a_class, np.asarray(class_bg["rho"]))
    p = np.interp(log_a_target, log_a_class, np.asarray(class_bg["p"]))
    mass_eV = sigma_mnu / N_NCDM
    precision_json = json.dumps(_precision_settings(), sort_keys=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    class_version = _class_version()
    script_sha = _script_sha256()
    header = (
        "CLASS massive-neutrino background oracle for FB-9; "
        f"CLASS {class_version}; generated {generated_at}; "
        f"precision={precision_json}; script_sha256={script_sha}"
    )
    return {
        "sigma_mnu_eV": np.float64(sigma_mnu),
        "mass_eV": np.float64(mass_eV),
        "a": a_target,
        "eta": np.asarray(bg_table.eta, dtype=np.float64),
        "rho": rho.astype(np.float64),
        "p": p.astype(np.float64),
        "w": (p / rho).astype(np.float64),
        "class_version": np.asarray(class_version),
        "precision_settings": np.asarray(precision_json),
        "generator_script_sha256": np.asarray(script_sha),
        "provenance_header": np.asarray(header),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="target fixture directory",
    )
    parser.add_argument(
        "--sigma-mnu",
        nargs="*",
        type=float,
        default=list(SIGMA_MNU_VALUES),
        help="Sigma_mnu values in eV (default: 0.06 0.12 0.24)",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(
        "Generating CLASS massive-neutrino fixtures on the shared "
        f"BASS FLRW grid -> {args.out_dir}"
    )
    for sigma_mnu in args.sigma_mnu:
        payload = _interpolate_onto_bass_grid(float(sigma_mnu))
        out_path = args.out_dir / f"{float(sigma_mnu):.2f}.npz"
        np.savez(out_path, **payload)
        print(
            f"  [ok] {out_path.name} "
            f"(mass_eV={float(payload['mass_eV']):.8f}, "
            f"rho_today={float(payload['rho'][-1]):.8e})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
