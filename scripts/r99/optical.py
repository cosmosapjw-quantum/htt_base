"""R99 finite-redshift distance experiment on five actual R98/R49 histories."""
import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import scipy
from scipy.integrate import quad

from scripts.r98 import bianchi_history as r98
from bass.transport.finite_redshift_optics import OpticalHistory, finite_redshift_beams

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research_program/observational_publication_20261015/R99_FIFTH_BLOCKER_RESOLUTION_20261123"
REDSHIFTS = np.array([.01, .025, .04, .06, .08, .1, .5, 1., 2.])
N_MIN = -np.log(3.2)
POSITIVE = np.array([[1,0,0], [0,1,0], [0,0,1], [1,1,1], [-1,2,1], [1,-1,2]], dtype=float)
POSITIVE /= np.linalg.norm(POSITIVE, axis=1)[:, None]
DIRECTIONS = np.concatenate([POSITIVE, -POSITIVE])


def make_history(family, samples):
    _, t = r98.background(family, samples=samples)
    href = float(r98.optics()[0].H_of_z(r98.Z_INITIAL))
    return OpticalHistory(t.N_grid, t.H_grid, t.sigma_ab_grid, t.a_grid, t.n_grid,
                          h_reference_si=href)


def serialize(beams):
    return {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in asdict(beams).items()}


def solve(history, **controls):
    return finite_redshift_beams(history, DIRECTIONS, REDSHIFTS, n_min=N_MIN,
                                 sky_frame="observed", **controls)


def compare(a, b):
    # Directional spread can lie many orders below an angle-independent change.
    da, db = a.angular_distance_mpc, b.angular_distance_mpc
    shape_a = (da - da.mean(axis=0)) / da.mean(axis=0)
    shape_b = (db - db.mean(axis=0)) / db.mean(axis=0)
    return {"max_relative_distance": float(np.max(abs(da/db - 1))),
            "max_abs_fractional_anisotropy_difference": float(np.max(abs(shape_a-shape_b))),
            "max_abs_emission_N_difference": float(np.max(abs(a.emission_N-b.emission_N)))}


def compute():
    start = time.perf_counter()
    families, validation, controls = {}, {}, {}
    coarse_steps = dict(rtol=2e-10, atol=2e-13, max_step=.04)
    fine_steps = dict(rtol=2e-12, atol=2e-15, max_step=.02)
    for family in r98.FAMILIES:
        h = make_history(family, 641)
        beams = solve(h, **coarse_steps)
        row = serialize(beams)
        distance = beams.angular_distance_mpc
        row["peak_to_peak_over_mean_by_z"] = (np.ptp(distance, axis=0)/distance.mean(axis=0)).tolist()
        row["antipodal_max_difference_over_mean_by_z"] = (
            abs(distance[:6] - distance[6:]).max(axis=0)/distance.mean(axis=0)).tolist()
        row["maximum_measured_redshift_residual"] = float(np.max(abs(beams.redshift-REDSHIFTS)))
        if family == "FLRW":
            flat = distance.copy()
            cosmo = r98.optics()[0]
            reference = np.array([quad(lambda x: 1/(cosmo.H_of_z(x)*r98.r97.SEC_PER_MPC),
                                       0, z, epsabs=1e-11)[0]/(1+z) for z in REDSHIFTS])
            validation["flat_r98_vs_reference_cosmology_relative"] = float(np.max(abs(distance/reference-1)))
            test_beta = np.array([.001, -.0006, .0004])
            boosted = solve(h, observer_beta=test_beta, **coarse_steps)
            controls["flat_observer"] = dict(velocity_over_c=test_beta.tolist(), **serialize(boosted))
            # In flat FLRW normal emitter: 1+z_v = (1+z_obs) D_o.
            # Evaluate reference cosmology independently of the ray and spline.
            rin = np.empty_like(distance)
            for i, D in enumerate(boosted.observer_doppler):
                for j, z in enumerate(REDSHIFTS):
                    zv = (1+z)*D - 1
                    rin[i,j] = D * quad(lambda x: 1/(cosmo.H_of_z(x)*r98.r97.SEC_PER_MPC), 0, zv)[0]/(1+zv)
            validation["flat_boost_vs_reference_cosmology_relative"] = float(np.max(abs(boosted.angular_distance_mpc/rin-1)))
        row["distance_minus_same_observed_z_flat_mpc"] = (distance-flat).tolist()
        row["distance_over_flat_minus_one"] = (distance/flat-1).tolist()
        families[family] = row
        if family in ("VII_h", "VI_h"):
            fine = solve(h, **fine_steps)
            refined_history = make_history(family, 1281)
            dense = solve(refined_history, **fine_steps)
            validation[family] = {"optical_tolerance_and_step": compare(beams, fine),
                                  "background_grid_641_to_1281_at_fine_optics": compare(fine, dense)}
        if family == "VI_h":
            # A specified source congruence in the Fermi tetrad, independent of
            # R49 matter velocities. Constant physical direction/speed is a test.
            emitter = np.array([.002, .001, -.001])
            _, traj = r98.background(family, samples=641)
            moving = OpticalHistory(traj.N_grid, traj.H_grid, traj.sigma_ab_grid, traj.a_grid,
                                    traj.n_grid, h_reference_si=h.h_reference_si,
                                    emitter_beta=np.broadcast_to(emitter,(len(traj.N_grid),3)))
            controls["VI_h_emitter"] = dict(velocity_over_c=emitter.tolist(), **serialize(solve(moving, **coarse_steps)))
        print(f"completed {family} at {time.perf_counter()-start:.1f} s", flush=True)

    source_paths = [Path(__file__), ROOT/"htt/bass/transport/finite_redshift_optics.py",
                    ROOT/"htt/bass/transport/general_bianchi_transfer.py",
                    ROOT/"htt/bass/background/convention_bridge.py",
                    ROOT/"htt/bass/background/general_tilted_evolution.py",
                    ROOT/"htt/bass/background/tilted_bianchi_state.py",
                    ROOT/"htt/bass/recombination/reionization.py",
                    ROOT/"scripts/r98/bianchi_history.py", ROOT/"scripts/r97/bianchi_coupled_m_transport.py",
                    OUT/"THEORY_OPTICAL.md", ROOT/"tests/obsstat/test_r99_optical.py",
                    Path(r98.r97.HYREC_CSV)]
    return dict(theory_checkpoint="575ff4811b6a5ae12d7c14bf7cd8ecadef7e58aa",
                scope="conditional homogeneous transparent optical distances; normal emitters/observers unless specified",
                redshifts=REDSHIFTS.tolist(), directions_observed=DIRECTIONS.tolist(),
                direction_sampling="six specified unit sightlines and their antipodes; equal-sample diagnostics",
                n_min=float(N_MIN), initial_r98_shear_amplitude=1e-5, baseline_samples=641,
                h_reference_si=h.h_reference_si, baseline_ode=coarse_steps, fine_ode=fine_steps,
                families=families, frame_controls=controls, validation=validation,
                inputs_sha256={os.path.relpath(p,ROOT):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
                software={"python":sys.version,"numpy":np.__version__,"scipy":scipy.__version__,
                          "platform":platform.platform(),"backend":"NumPy, SciPy DOP853, CubicSpline, Brent",
                          "threads":{k:os.getenv(k) for k in ["OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","OMP_NUM_THREADS"]}},
                runtime_seconds=time.perf_counter()-start)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT/"OPTICAL_RESULTS.json")
    args = parser.parse_args()
    payload = compute()
    args.output.write_text(json.dumps(payload, indent=2, allow_nan=False)+"\n")
