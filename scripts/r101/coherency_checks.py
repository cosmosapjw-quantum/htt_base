"""Numerical controls for the R101 forced Thomson substep.

Run with OPENBLAS_NUM_THREADS=1 and PYTHONPATH=.:htt:htt/src at repository
root. Optionally pass --legacy-polarization with the recovered BASS file.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
from time import perf_counter

import numpy as np
import scipy
from scipy.linalg import expm

from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.collision.test_coherency import dense_collision, r100_affine_comparison, sky_grid
from bass.transport.test_stokes_fourier import fourier_convergence
from scripts.r101.coherency_history import REFERENCE, recombination_case


def _timing(f, count):
    f()
    samples = []
    for _ in range(5):
        start = perf_counter()
        for _ in range(count):
            f()
        samples.append((perf_counter()-start)/count)
    return float(np.median(samples))


def smooth_circular_resolution():
    # For V(n)=exp(k h.n), (4pi)^(-1) int n V dOmega = i_1(k) h.
    k = 3.4
    h = np.array([2., 1., -.7])
    h /= np.linalg.norm(h)
    t = .8
    i1 = (k*np.cosh(k)-np.sinh(k))/k**2
    rows = []
    for size in (3, 4, 6, 8, 12):
        _, _, n, w, u, v = sky_grid(size)
        op = ThomsonCoherencyPropagator(n,w.ravel(),u,v)
        s = np.zeros((len(n),4))
        s[:,3] = np.exp(k*(n@h))
        expected = np.exp(-t)*s[:,3] + 3*(np.exp(-.5*t)-np.exp(-t))*i1*(n@h)
        rows.append({"n_theta":size, "n_dir": len(n),
                     "max_V_error": float(np.max(abs(op.advance(s,t)[:,3]-expected)))})
    return rows


def dense_stiffness():
    _, _, n, w, u, v = sky_grid(4)
    op = ThomsonCoherencyPropagator(n,w.ravel(),u,v)
    s = np.random.default_rng(1).normal(size=(len(n),4))
    C = dense_collision(n,w.ravel(),u,v)
    rows = []
    for t in (1e-8, .1, 1, 100, 1e4):
        reference = expm(t*C) @ s.ravel()
        rows.append({"delta_tau":t,"max_dense_expm_error":float(np.max(abs(op.advance(s,t).ravel()-reference))),
            "native_step_seconds": _timing(lambda:op.advance(s,t),40),
            "dense_new_exponential_and_action_seconds": _timing(lambda:expm(t*C) @ s.ravel(), 3)})
    return rows


def linear_cost():
    result = []
    for size in (4, 8, 16, 32, 64):
        _, _, n, w, u, v = sky_grid(size)
        op = ThomsonCoherencyPropagator(n, w.ravel(), u, v)
        s = np.random.default_rng(8).normal(size=(len(n),4))
        result.append({"n_theta":size, "n_dir":len(n),
            "cached_operator_array_bytes": int(sum(x.nbytes for x in vars(op).values())),
            "equivalent_full_dense_float64_bytes": 8*(4*len(n))**2,
            "exact_step_seconds":_timing(lambda:op.advance(s,10.),20)})
    return result


def old_carrier_comparison(path):
    data = Path(path).read_bytes()
    expected = "44a2eb306d8870e70d6cb46c8f481bb30e58f64ffee4b9a055a0157a23e79e95"
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise ValueError("legacy source identity differs from recovered BASS ee298e24 polarization.py")
    spec = importlib.util.spec_from_file_location("recovered_bass_polarization", path)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    _,_,n,w,u,v = sky_grid(7)
    op = ThomsonCoherencyPropagator(n,w.ravel(),u,v)
    s = np.random.default_rng(2026).normal(size=(len(n),4))
    screen = np.stack((u,v),axis=1)
    def encode(sky):
        I,Q,U,V = sky.T
        # The legacy real carrier encodes the imaginary antisymmetric part in
        # real antisymmetric slots. Its V=J21-J12, consistent with J_uv=(U-iV)/2.
        d = .5*np.stack((I+Q,U-V,U+V,I-Q),axis=1).reshape(-1,2,2)
        return screen.swapaxes(1,2) @ d @ screen
    J = encode(s)
    rows = []
    for t in (0., 1e-12, .8, 13., 1e4):
        old = legacy.collide(n,w.ravel(),J,t)
        rows.append({"delta_tau":t,"max_carrier_error":float(np.max(abs(encode(op.advance(s,t))-old)))})
    return {"sha256": digest,"commit":"ee298e24a6bac85bb11a81393f37499a8b0ddbe3","comparisons":rows}


def checks(reference, legacy_path):
    case = recombination_case(reference)
    modes = case.pop("alm")
    case["number_of_signed_harmonic_slots"] = sum(len(v) for v in modes.values())
    case["final_channel_norms"] = {ch: float(np.linalg.norm(np.array(vals)[:,2:])) for ch,vals in modes.items()}
    case["signed_V_dipole"] = [row for row in modes["V"] if row[0] == 1]
    errors, count = r100_affine_comparison()
    fourier_case = recombination_case(reference, k_per_mpc=[.03, -.015, .011])
    fourier_refined = recombination_case(reference, k_per_mpc=[.03, -.015, .011], substeps=2)
    fourier_alm = fourier_case.pop("alm")
    fine_alm = fourier_refined["alm"]
    fourier_case["max_harmonic_change_on_time_refinement"] = max(
        float(np.max(np.linalg.norm(np.asarray(values)[:,2:]-np.asarray(fine_alm[c])[:,2:],axis=1)))
        for c,values in fourier_alm.items())
    fourier_case["final_channel_norms"] = {
        c:float(np.linalg.norm(np.asarray(values)[:,2:])) for c,values in fourier_alm.items()}
    result = {
        "python":platform.python_version(), "numpy":np.__version__, "scipy":scipy.__version__,
        "r100_collision_plus_affine_at_zero_angular_advection":{"ell_max":6,"number_of_slots":count,"max_error":errors},
        "resolution_against_analytic_unbandlimited_sky": smooth_circular_resolution(),
        "stiffness_32_directions":dense_stiffness(),"cost":linear_cost(),
        "timing_method":"median of 5 repeated batches, setup excluded, dense comparison recomputes exponential at each requested depth",
        "HyRec_recombination_case":case, "HyRec_flat_Fourier_case":fourier_case,
        "fourier_streaming_collision":fourier_convergence(),
    }
    if legacy_path is not None:
        result["old_basis_free_polarization"] = old_carrier_comparison(legacy_path)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--legacy-polarization", type=Path)
    args = parser.parse_args()
    print(json.dumps(checks(args.reference, args.legacy_polarization), indent=2, allow_nan=False))
