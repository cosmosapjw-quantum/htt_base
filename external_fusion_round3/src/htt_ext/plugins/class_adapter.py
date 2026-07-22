from __future__ import annotations


def require_classy():
    try:
        from classy import Class  # type: ignore
    except ImportError as exc:
        raise RuntimeError("CLASS/classy is not installed; install the Track-I class profile") from exc
    return Class


def smoke_background(z: float = 1.0) -> dict:
    Class = require_classy()
    cosmo = Class()
    cosmo.set({"h": 0.674, "omega_b": 0.0224, "omega_cdm": 0.120, "output": "mPk", "P_k_max_h/Mpc": 1.0})
    cosmo.compute()
    out = {"z": z, "H_Mpc_inv": float(cosmo.Hubble(z)), "angular_distance_Mpc": float(cosmo.angular_distance(z))}
    cosmo.struct_cleanup()
    cosmo.empty()
    return out
