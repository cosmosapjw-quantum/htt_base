from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
import importlib.metadata


@dataclass(frozen=True)
class PluginSpec:
    name: str
    import_name: str
    track: str
    role: str
    required_for_core: bool = False


PLUGINS: tuple[PluginSpec, ...] = (
    PluginSpec("CAMB", "camb", "I", "FLRW CMB/source transfer oracle"),
    PluginSpec("CLASS", "classy", "I", "independent FLRW transfer oracle"),
    PluginSpec("GLASS", "glass", "I", "full-sky lightcone and shell mocks"),
    PluginSpec("healpy", "healpy", "I", "HEALPix maps and real-data pole extraction"),
    PluginSpec("NaMaster", "pymaster", "I", "masked spin-0/spin-2 pseudo-Cl baseline"),
    PluginSpec("S2FFT", "s2fft", "I", "differentiable spherical transforms"),
    PluginSpec("S2WAV", "s2wav", "I", "directional spherical wavelets"),
    PluginSpec("PySM3", "pysm3", "I", "foreground simulations"),
    PluginSpec("lenspyx", "lenspyx", "I", "lensed CMB simulation"),
    PluginSpec("sbi", "sbi", "I", "simulation-based posterior baselines"),
    PluginSpec("sbibm", "sbibm", "I", "benchmark task framework"),
    PluginSpec("NumPyro", "numpyro", "I", "independent Bayesian baseline"),
    PluginSpec("CVXPY", "cvxpy", "I", "identified-set and design optimization"),
    PluginSpec("CVXPYlayers", "cvxpylayers", "I", "differentiable optimization"),
    PluginSpec("CCL", "pyccl", "I", "LSS theory and tracer cross-spectra"),
    PluginSpec("pycorr", "pycorr", "I", "survey correlation estimators"),
    PluginSpec("pypower", "pypower", "I", "window-aware survey power spectra"),
    PluginSpec("SACC", "sacc", "I", "summary/covariance exchange"),
    PluginSpec("Firecrown", "firecrown", "I", "external cosmology likelihood framework"),
    PluginSpec("Cobaya", "cobaya", "I", "independent cosmology inference engine"),
    PluginSpec("COFFE", "coffe", "I", "relativistic and wide-angle LSS templates"),
    PluginSpec("Corrfunc", "Corrfunc", "I", "fast pair counts"),
    PluginSpec("JaxPM", "jaxpm", "I", "differentiable particle-mesh mocks"),
    PluginSpec("Snakemake", "snakemake", "I", "content-addressed workflow"),
)


def probe_plugin(spec: PluginSpec) -> dict:
    try:
        module = importlib.import_module(spec.import_name)
        try:
            version = importlib.metadata.version(spec.import_name)
        except importlib.metadata.PackageNotFoundError:
            version = getattr(module, "__version__", "unknown")
        return {**asdict(spec), "available": True, "version": str(version), "error": None}
    except Exception as exc:  # optional dependencies intentionally isolated
        return {**asdict(spec), "available": False, "version": None, "error": repr(exc)}


def probe_all() -> list[dict]:
    return [probe_plugin(p) for p in PLUGINS]
