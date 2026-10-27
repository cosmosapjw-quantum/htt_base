"""Deterministic, small algebra fixtures; no cosmological solver or observations."""
import json
from pathlib import Path
import numpy as np


def main():
    # Exact product quadrature for independent, zero-mean Rademacher s,nA,nB.
    grid = np.array(np.meshgrid([-1., 1.], [-1., 1.], [-1., 1.])).reshape(3, -1)
    s, n_a, n_b = grid[0], grid[1], 2 * grid[2]
    a, b = s + n_a, s + n_b
    full = (a + b) / 2
    actual = float(np.mean((a - b) * full))
    expected = (1. - 4.) / 2
    assert actual == expected == -1.5

    # A polarization cancellation: complex amplitudes +1 and -1 have zero
    # net reference-frequency polarization but nonzero spectral moments.
    nu = np.array([30., 44., 70., 100., 143., 217., 353.])
    log_ratio = np.log(nu / 100.)
    beta0, delta = 1.5, 0.1
    w = np.array([1.+0j, -1.+0j])
    shifts = np.array([delta, -delta])
    exact = sum(wi * np.exp((beta0 + di) * log_ratio) for wi, di in zip(w, shifts))
    approx2 = sum(wi * np.exp(beta0 * log_ratio) *
                  (1 + di * log_ratio + (di * log_ratio)**2 / 2)
                  for wi, di in zip(w, shifts))
    residual = np.abs(exact - approx2)
    bound = (np.abs(w).sum() * delta**3 / 6 * np.abs(log_ratio)**3 *
             np.exp(beta0 * log_ratio + delta * np.abs(log_ratio)))
    assert np.all(residual <= bound + 1e-14)
    assert np.max(np.abs(exact)) > 0
    output = {
        "fixture_only": True,
        "observations_analyzed": False,
        "native_solver_or_ode_executed": False,
        "shared_sky_nonzero_cross": {"actual": actual, "analytic": expected,
            "conclusion": "nonzero difference x full does not falsify common sky"},
        "complex_moment_cancellation": {
            "net_reference_amplitude": float(abs(w.sum())),
            "total_variation_amplitude": float(abs(w).sum()),
            "max_signal": float(max(abs(exact))),
            "max_remainder": float(max(residual)),
            "max_bound": float(max(bound)),
            "channels_GHz": nu.tolist(),
            "all_channel_bounds_hold": bool(np.all(residual <= bound + 1e-14))},
        "checks_passed": 4}
    path = Path(__file__).with_name("DATA_ATLAS_VALIDATION.json")
    path.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
