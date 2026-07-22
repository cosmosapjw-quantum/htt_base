from __future__ import annotations


def require_camb():
    try:
        import camb  # type: ignore
    except ImportError as exc:
        raise RuntimeError("CAMB is not installed; install the Track-I camb profile") from exc
    return camb


def smoke_cmb_spectrum(lmax: int = 30) -> dict:
    camb = require_camb()
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=67.4, ombh2=0.0224, omch2=0.120)
    pars.InitPower.set_params(As=2.1e-9, ns=0.965)
    pars.set_for_lmax(lmax, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit="muK", raw_cl=True)
    tt = powers["total"][: lmax + 1, 0]
    return {"lmax": lmax, "tt": tt.tolist(), "camb_version": getattr(camb, "__version__", "unknown")}
