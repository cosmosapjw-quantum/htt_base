#!/usr/bin/env python3
"""Deterministic supplied-model integration fixture. Never opens a catalogue."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT/'htt', ROOT/'htt/htt', ROOT/'htt/src'):
    sys.path.insert(0, str(path))

import numpy as np
from common.relativistic_kinematics import four_velocity, lorentz_boost, intercept_velocity, hubble_tensor_lift
from common.typefree_functionals import FunctionalSpec, FunctionalRecord, ratio_value, strict_exceedance
from htt.infer.endpoint_cosmography import (
    EndpointObservations, DistanceTreatment, FiniteDistanceRemainder,
    RemainderKind, fit_endpoint_cosmography, endpoint_log_likelihood,
)
from htt.infer.functional_pushforward import posterior_functional_image


def run_fixture():
    count = 72; index = np.arange(count)
    nz = 1-2*(index+.5)/count; phi = index*math.pi*(3-math.sqrt(5))
    directions = np.column_stack((np.sqrt(1-nz*nz)*np.cos(phi), np.sqrt(1-nz*nz)*np.sin(phi), nz))
    distance = 10+(17*index)%91
    beta = np.array([.02, -.01, .005]); u = four_velocity(beta)
    inv = lorentz_boost(-beta)
    b = inv.T@np.diag([0., 65., 70., 75.])@inv
    h0 = b[0, 0]+np.trace(b[1:, 1:])/3
    h1 = -2*b[0, 1:]; q = b[1:, 1:]-np.eye(3)*np.trace(b[1:, 1:])/3
    # Construct through the tensor contraction, independent of endpoint_design.
    redshift = u[0]-1+directions@u[1:]+distance/299792.458*(h0+directions@h1+np.einsum('ni,ij,nj->n', directions, q, directions))
    modes = np.cos(index/7)
    covariance = 1e-8*(np.diag(1+index/count)+.2*np.outer(modes, modes))
    ids = tuple(f"synthetic:{i}" for i in index)
    obs = EndpointObservations(
        row_ids=ids, directions=directions, redshift=redshift, area_distance_mpc=distance,
        covariance=covariance, covariance_row_ids=ids, support_mask=np.ones(count, dtype=bool),
        source_congruence="synthetic geodesic U", observer_frame="synthetic O", redshift_frame="synthetic O",
        direction_frame="O tetrad Cartesian", redshift_correction_source="NATIVE_OBSERVER_NO_CORRECTION",
        distance_treatment=DistanceTreatment.FIXED_INDEPENDENT_AREA_DISTANCE,
        distance_source="synthetic exact area distance", selection_source="fixed synthetic design",
        covariance_source="analytic known dense Gaussian covariance",
        remainder=FiniteDistanceRemainder(RemainderKind.EXACT_ZERO_ASSUMED, "exact truncated synthetic model"),
        geodesic_source=True)
    fit = fit_endpoint_cosmography(obs)
    coef = fit.coefficients
    fit_q = np.array([[coef[8], coef[10], coef[11]], [coef[10], coef[9], coef[12]], [coef[11], coef[12], -coef[8]-coef[9]]])
    intercept_u = intercept_velocity(coef[0], coef[1:4], tolerance=1e-9)
    lift = hubble_tensor_lift(coef[4], coef[5:8], fit_q, geodesic=True)
    spec = FunctionalSpec("synthetic.ratio-input.v1", ("value",), (1,), 0, "even", "scalar", "1", "O", "t0", "toy", "raw", "exact", "synthetic")
    # Separate finite toy posterior, not samples inferred from the GLS fit.
    records = (FunctionalRecord("toy:a", spec, [1], [1]), FunctionalRecord("toy:b", spec, [1], [0]))
    image = posterior_functional_image(records, lambda r: ratio_value(r.values, r.reference),
        weights=(.25, .75), joint_id="declared-two-atom-toy-posterior", conditioning_domain_id="toy-given",
        target_domain_id="ratio-including-undefined", definition_id="synthetic.ratio.v1")
    tail = strict_exceedance(image, 0.)
    errors = {"intercept_u_max_abs": float(np.max(np.abs(intercept_u-u))),
              "slope_u_max_abs": float(np.max(np.abs(lift.source_u-u))),
              "symmetric_gradient_max_abs": float(np.max(np.abs(lift.symmetric_gradient-b)))}
    if max(errors.values()) > 1e-8 or tail.undefined_mass != .75:
        raise RuntimeError("synthetic acceptance failed")
    return {"status": "SYNTHETIC_PRE_DATA_INTEGRATION_PASSED", "real_data_executed": False,
            "scientific_admission": False, "data_readiness": "NOT_ESTABLISHED",
            "source": "deterministic local tensor jet; exact truncated response",
            "coefficient_count": len(coef), "design_rank": fit.design_rank,
            "scaled_condition_number": fit.scaled_condition_number,
            "log_likelihood_at_nominal_fit": endpoint_log_likelihood(obs, coef),
            "recovery_errors": errors,
            "toy_posterior": {"independent_of_endpoint_fit": True, "known_tail_mass": tail.lower,
                              "upper_tail_mass": tail.upper, "undefined_mass": tail.undefined_mass},
            "I2": "DEFENDED_CONDITIONAL", "I3": "HOLD_INPUT_INCOMPLETE"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run_fixture(); text = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text, encoding='utf-8')
    print(text, end='')


if __name__ == '__main__':
    main()
