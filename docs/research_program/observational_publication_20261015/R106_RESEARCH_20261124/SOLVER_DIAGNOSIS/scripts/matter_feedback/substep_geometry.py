"""Photon substep depths in the cell ending at the first 48-cell common endpoint.

Diagnostic only: rebuilds the Picard-0 opacity history (no baryon-history
callbacks, exactly as the solver's first iteration) on each N_eval grid and
applies the repo _optical_substeps with min 2 / cap 1.0.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

from bass.transport import coupled_einstein_boltzmann as cs
from bass.recombination.reionization import ReionizationParameters
from bass.recombination.tilted_hyrec import integrate_tilted_recombination, load_hyrec_atomic_tables

out = {}
tbl = load_hyrec_atomic_tables()
cosmo = cs._load_default_cosmo()
reion = ReionizationParameters(z_reion_H=7.67, delta_z_H=0.5, z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True)
N0 = -math.log1p(cs.Z_INITIAL)
for n in (48, 96, 192, 384, 768, 1536):
    N_eval = np.linspace(N0, 0.0, 2 * n + 1)
    hist = integrate_tilted_recombination(
        np.expm1(-N_eval), h=float(cosmo.h), t_cmb0=float(cosmo.T_cmb), omega_b=float(cosmo.Omega_b),
        omega_m=float(cosmo.Omega_m), omega_r=float(cosmo.Omega_r), omega_lambda=float(cosmo.Omega_Lambda),
        y_he=float(cosmo.Y_He), n_h0_m3=float(cosmo.n_H_today), tables=tbl, reionization=reion,
        mode="tilted_physical")
    op = hist.opacity_history()
    rows = {}
    for label, k in (("first", 1), ("second", 2)):
        cell = k * (n // 48) - 1
        a, b = float(N_eval[2 * cell]), float(N_eval[2 * cell + 2])
        u, d = cs._optical_substeps(op, a, b, 2, 1.0)
        dN = (b - a) * np.diff(u)
        rows[label] = {"cell": cell, "n_substeps": len(d), "depths": d.tolist(), "last_depth": float(d[-1]),
                       "last_dN": float(dN[-1]), "rate_at_end": float(op.rate(b)),
                       "dlnrate_dN_at_end": float((math.log(op.rate(b)) - math.log(op.rate(b - 1e-4))) / 1e-4)}
    out[n] = rows
    print(n, {k: (v["n_substeps"], round(v["last_depth"], 4), v["last_dN"], round(v["rate_at_end"], 3),
                  round(v["dlnrate_dN_at_end"], 3)) for k, v in rows.items()}, flush=True)
Path(sys.argv[1]).write_text(json.dumps(out, indent=1) + "\n")
