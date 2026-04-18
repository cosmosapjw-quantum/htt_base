"""
Fair-ish wallclock benchmark: CAMB vs bass_rs (bass_phase1_snapshot).

Target: compute scalar TT C_ℓ up to ℓ=2500 for Planck 2018 cosmology,
matching the workload of `perf_probe_default_track_a` in bass_rs.

Not a correctness comparison (bass_rs has a known D_200 blow-up in the
default_track_a config, being optimized separately).  This is strictly a
wallclock-per-identical-workload benchmark on the current desktop.
"""

import time
import statistics as stats
import sys

import camb

# ── Planck 2018 TT,TE,EE,lowE+lensing best-fit (matches bass_rs.VisibilityParams::planck2018) ──
PARAMS = dict(
    H0=67.36,
    ombh2=0.02237,
    omch2=0.12,
    mnu=0.06,
    omk=0.0,
    tau=0.0544,
    As=2.1e-9,
    ns=0.9649,
)
LMAX = 2500


def run_once(accuracy: float = 1.0) -> float:
    """One full CAMB spectrum computation.  Returns wall seconds."""
    pars = camb.CAMBparams()
    pars.set_cosmology(**{k: PARAMS[k] for k in ("H0", "ombh2", "omch2", "mnu", "omk", "tau")})
    pars.InitPower.set_params(As=PARAMS["As"], ns=PARAMS["ns"])
    # Scalar TT only; no lensing, no tensors — matches bass_rs scalar FLRW path
    pars.set_for_lmax(LMAX, lens_potential_accuracy=0)
    pars.WantTensors = False
    pars.DoLensing = False
    pars.set_accuracy(AccuracyBoost=accuracy, lSampleBoost=accuracy, lAccuracyBoost=accuracy)

    t0 = time.perf_counter()
    results = camb.get_results(pars)
    # .get_total_cls returns TT, EE, BB, TE up to lmax, in μK²
    totCL = results.get_total_cls(LMAX, CMB_unit="muK")
    t1 = time.perf_counter()

    # sanity check: D_ℓ = ℓ(ℓ+1)C_ℓ/(2π) at ℓ=2 should be O(1000) μK²
    # CAMB returns D_ℓ directly in get_total_cls (multiplied by the 2π factor).
    dl2 = totCL[2, 0]  # TT at ℓ=2, units: μK²
    dl200 = totCL[200, 0]
    return t1 - t0, dl2, dl200


def main():
    n_warmup = 1
    n_runs = 5
    print(f"CAMB {camb.__version__}, lmax={LMAX}")
    print(f"  warmup={n_warmup}, runs={n_runs}")
    print()

    # Warm up
    for _ in range(n_warmup):
        run_once()

    for boost_label, boost in [("default (1.0)", 1.0), ("boost 2.0", 2.0)]:
        times = []
        d2 = d200 = 0.0
        for _ in range(n_runs):
            dt, d2, d200 = run_once(boost)
            times.append(dt)
        mean = stats.mean(times)
        stdev = stats.stdev(times) if len(times) > 1 else 0.0
        print(f"  accuracy={boost_label:15s}: {mean:.3f} ± {stdev:.3f} s  "
              f"(D_2={d2:.1f} μK², D_200={d200:.1f} μK²)")


if __name__ == "__main__":
    main()
