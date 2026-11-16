#!/usr/bin/env python3
"""Build the two small R54 theory fixtures from CAMB (Planck 2018 parameters).

Outputs (text, diffable, no observational data):
  tests/fixtures/r54/planck18_tau_history.csv     z, tau, x_e
  tests/fixtures/r54/planck18_linear_pk_z0.csv    k_per_Mpc, P_Mpc3
  tests/fixtures/r54/FIXTURE_PROVENANCE.json

tau(z) = int_0^z sigma_T c n_e / ((1+z') H) dz' with n_e = x_e n_H, x_e from the
CAMB recombination + reionization history. Parameters are read from the repo
reference ``data/camb_ref_planck2018.npz`` so that R54 uses the same background
as the existing C_ell reference.

Run only when the fixtures must be regenerated; tests read the committed CSVs
and do not import CAMB.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tests/fixtures/r54"
REF = ROOT / "data/camb_ref_planck2018.npz"

M_H_KG = 1.673575e-27          # hydrogen atom mass
SIGMA_T_M2 = 6.6524587321e-29
C_M_S = 299792458.0
G_SI = 6.67430e-11
MPC_M = 3.0856775814913673e22


def main() -> None:
    import camb

    with np.load(REF, allow_pickle=False) as z:
        par = {k: float(z[k]) for k in ("H0", "ombh2", "omch2", "mnu", "omk", "tau", "As", "ns")}
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=par["H0"], ombh2=par["ombh2"], omch2=par["omch2"], mnu=par["mnu"], omk=par["omk"], tau=par["tau"])
    pars.InitPower.set_params(As=par["As"], ns=par["ns"])
    pars.set_matter_power(redshifts=[0.0], kmax=5.0)
    pars.NonLinear = camb.model.NonLinear_none
    res = camb.get_results(pars)

    # ---- optical depth history
    zz = np.concatenate([[0.0], np.expm1(np.linspace(np.log1p(1e-3), np.log1p(1.0e4), 2400))])
    xe = res.get_background_redshift_evolution(zz, vars=["x_e"], format="array")[:, 0]
    h = par["H0"] / 100.0
    rho_crit = 3.0 * (par["H0"] * 1e3 / MPC_M) ** 2 / (8.0 * np.pi * G_SI)
    n_h0 = (1.0 - pars.YHe) * par["ombh2"] / h**2 * rho_crit / M_H_KG
    hz = res.hubble_parameter(zz) * 1e3 / MPC_M
    dtau_dx = SIGMA_T_M2 * C_M_S * xe * n_h0 * (1.0 + zz) ** 3 / hz          # d tau / d ln(1+z)
    x = np.log1p(zz)
    tau = np.concatenate([[0.0], np.cumsum(0.5 * (dtau_dx[1:] + dtau_dx[:-1]) * np.diff(x))])
    # thin to a compact table: dense through reionization and recombination
    keep = np.unique(np.concatenate([[0], np.arange(1, zz.size, 4), np.where((zz > 4) & (zz < 12))[0],
                                     np.where((zz > 500) & (zz < 2500))[0], [zz.size - 1]]))
    OUT.mkdir(parents=True, exist_ok=True)
    f_tau = OUT / "planck18_tau_history.csv"
    with open(f_tau, "w") as f:
        f.write("z,tau,x_e\n")
        for i in keep:
            f.write(f"{zz[i]:.10e},{tau[i]:.10e},{xe[i]:.8e}\n")

    # ---- linear matter power spectrum at z = 0, Mpc units
    kh, _, pk = res.get_matter_power_spectrum(minkh=1e-5, maxkh=4.0, npoints=260)
    k_mpc, p_mpc3 = kh * h, pk[0] / h**3
    f_pk = OUT / "planck18_linear_pk_z0.csv"
    with open(f_pk, "w") as f:
        f.write("k_per_Mpc,P_Mpc3\n")
        for a, b in zip(k_mpc, p_mpc3):
            f.write(f"{a:.10e},{b:.10e}\n")

    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    prov = {
        "schema": "htt.r54.theory_fixture_provenance/1",
        "generator": "scripts/r54/build_r54_fixtures.py",
        "camb_version": camb.__version__,
        "parameters_source": "data/camb_ref_planck2018.npz",
        "parameters": par | {"YHe": float(pars.YHe)},
        "derived": {"tau_at_z50": float(np.interp(np.log1p(50.0), x, tau)), "z_star_camb": float(res.get_derived_params()["zstar"]),
                    "sigma8": float(res.get_sigma8_0()), "tau_at_zstar": float(np.interp(np.log1p(res.get_derived_params()["zstar"]), x, tau))},
        "files": {f_tau.name: {"sha256": sha(f_tau), "rows": int(keep.size), "columns": ["z", "tau", "x_e"]},
                  f_pk.name: {"sha256": sha(f_pk), "rows": int(k_mpc.size), "columns": ["k_per_Mpc", "P_Mpc3"]}},
        "claim_tier": "THEORY_FIXTURE_NOT_OBSERVATIONAL_DATA",
    }
    (OUT / "FIXTURE_PROVENANCE.json").write_text(json.dumps(prov, indent=1) + "\n")
    print(json.dumps(prov["derived"]))


if __name__ == "__main__":
    main()
