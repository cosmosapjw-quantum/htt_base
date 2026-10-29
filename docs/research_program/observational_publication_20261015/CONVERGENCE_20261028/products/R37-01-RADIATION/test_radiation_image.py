"""Focused falsifiers for the R37 finite conditional image."""
import importlib.util
import csv
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r37_image", HERE / "radiation_image.py")
image = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image)


def test_common_carrier_saved_draws():
    core = image.load_core()
    n, w = core.sphere_rule(24, 49)
    t = image.sky(core, n)
    with np.load(image.NPZ) as source:
        eta = source[f"{image.CASE}_eta_test"][[0, 157, 4095]]
    L, pi, pol = image.responses(core, n, w, t, eta)
    basis = np.column_stack([n, np.einsum("aij,ni,nj->na", core.STF_BASIS, n, n)])
    tbar = w @ t
    for k, e in enumerate(eta):
        bright = (tbar * (1 + t / tbar - 1 + basis @ e))**4
        moments = core.moments(n, w, bright, 1.)
        assert np.max(abs(L[k] - core.response_from_moments(moments))) < image.TOL
        assert np.max(abs(L[k] - core.response_direct(n, w, bright, 1.))) < image.TOL
        assert np.linalg.eigvalsh(L[k])[0] > 0
        assert np.linalg.norm(pol[k]) > 0


def test_physical_image_and_matched_law():
    d = json.loads((HERE / "RADIATION_IMAGE_RESULT.json").read_text())
    L = np.array(d["response"]["full_eigenvalues"])
    assert L[0] > 0 and d["carrier"]["generic_joint_rank"] == 23
    assert d["carrier"]["generic_linear_no_V_rank"] == 20
    assert d["full_common_max_error"] < d["predeclared_tolerance"]
    assert d["polarization_omission"]["norm"] <= d["polarization_omission"]["coercive_upper_bound"]
    assert d["H4_dropped_bias_norm"] > 1e-6
    assert d["carrier"]["fixed_profile_angular_kernel_ranks"] == {
        "full_fixed_profile":15,
        "H4_dropped_retaining_rho_pi_Pstar":11,
        "true_thomson_gain_at_V_zero":6}
    c = d["matched_law"]["coverage_rows"]
    assert len(c) == 20
    assert all(x["cal_N"] == 8191 and x["test_N"] == 4096 for x in c)
    full = [x for x in c if x["method"] == "full"]
    common = [x for x in c if x["method"] == "common_carrier"]
    for a, b in zip(full, common):
        assert a["direction"] == b["direction"]
        assert abs(a["joint_event_radius"]-b["joint_event_radius"]) < image.TOL
        assert a["joint_direction_target_coverage_test"] == b["joint_direction_target_coverage_test"]
        assert abs(a["signed_bias"]-b["signed_bias"]) < image.TOL
    # Recompute one support from the shared two-coordinate primitive and check
    # it against the shipped table, including cancellation between its columns.
    U = np.array(d["physical_error"]["U"])
    V = np.array(d["physical_error"]["V"])
    B = .005 * U + image.GAMMA * .01 / 5 * V
    core = image.load_core()
    n, w = core.sphere_rule(24, 49)
    t = image.sky(core, n)
    L, _, _ = image.responses(core, n, w, t, np.zeros((1, 8)))
    support = np.linalg.norm(np.linalg.solve(L[0], B)[0])
    with (HERE / "SHEAR_SUPPORT.csv").open() as f:
        rows = list(csv.DictReader(f))
    row = next(r for r in rows if r["method"] == "full" and r["direction"] == "STF1" and float(r["epsilon_R"]) == .005 and float(r["epsilon_P"]) == .01)
    assert abs(support-float(row["physical_support"])) < image.TOL
    assert support <= np.abs(np.linalg.solve(L[0], B)[0]).sum()


def test_shared_joint_event_rejects_old_marginal_counterexample():
    d = json.loads((HERE / "RADIATION_IMAGE_RESULT.json").read_text())
    event = d["matched_law"]["joint_event"]
    assert event["old_five_marginal_full_joint_test_hits"] == 3389
    assert event["simultaneous_centered_test_hits"] == 3888
    assert event["simultaneous_centered_test_coverage"] >= .94
    core = image.load_core()
    n, w = core.sphere_rule(24, 49)
    t = image.sky(core, n)
    with np.load(image.NPZ) as source:
        eta = source[f"{image.CASE}_eta_test"]
    L, pi, pol = image.responses(core, n, w, t, eta)
    R = np.asarray(d["target"]["R_tau_center"])
    rho = np.trace(L, axis1=1, axis2=2) * (3/8)
    law = {"full":image.shear(L,pi,pol,R,"full"),
           "H4_dropped_closure":image.shear(image.h4_dropped_response(core,rho,pi),pi,pol,R,"full"),
           "unpolarized":image.shear(L,pi,pol,R,"unpolarized")}
    law["common_carrier"] = law["full"]
    scale = np.asarray(event["common_scales"])
    score = np.maximum.reduce([np.max(abs(law[mode]-np.asarray(d["centers"][mode]))/scale,axis=1)
                               for mode in law])
    assert int(np.sum(score <= event["threshold"])) == 3888
    old = np.all(abs(law["full"]-np.asarray(d["target"]["STF5_shear"])) <= scale,axis=1)
    assert int(np.sum(old)) == 3389


def test_true_gain_fibre_is_not_the_H4_closure():
    d = json.loads((HERE / "RADIATION_IMAGE_RESULT.json").read_text())
    core = image.load_core()
    n, w = core.sphere_rule(24, 49)
    t = image.sky(core, n)
    ranks, witness, _, _ = image.gain_fibre_witness(core,n,w,t**4,np.asarray(d["target"]["R_tau_center"]))
    assert ranks["true_thomson_gain_at_V_zero"] == 6
    assert ranks["H4_dropped_retaining_rho_pi_Pstar"] == 11
    assert witness["minimum_brightness"] > 0
    assert witness["M_max_difference"] < image.TOL
    assert witness["member_separation_norm"] > 1e-5
    assert np.allclose(witness["member_shears"],d["true_gain_only_identified_set"]["member_shears"],atol=image.TOL)
