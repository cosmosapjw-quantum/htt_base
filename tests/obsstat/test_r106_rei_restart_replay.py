"""R106 REI restart replay: review-correction helpers (provenance, window, clock/H check, age convention)."""
import json
import math

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scripts.r106 import rei_restart_replay as rr


def test_tree_digest_is_content_and_name_sensitive(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.rs").write_text("fn a() {}\n")
    (tmp_path / "src" / "b.rs").write_text("fn b() {}\n")
    first = rr.tree_digest(tmp_path / "src")
    assert first["n_files"] == 2 and set(first["files"]) == {"a.rs", "b.rs"}
    assert rr.tree_digest(tmp_path / "src")["sha256"] == first["sha256"]
    (tmp_path / "src" / "b.rs").write_text("fn b() { 1; }\n")
    changed = rr.tree_digest(tmp_path / "src")
    assert changed["sha256"] != first["sha256"] and changed["files"]["a.rs"] == first["files"]["a.rs"]
    (tmp_path / "src" / "b.rs").rename(tmp_path / "src" / "c.rs")
    assert rr.tree_digest(tmp_path / "src")["sha256"] != changed["sha256"]


def test_find_line_returns_one_based_line_or_none(tmp_path):
    path = tmp_path / "axbi_driver.rs"
    path.write_text("fn validate() {\n    || !(4.0..20.0).contains(&self.end_zbar)\n}\n")
    hit = rr.find_line(path, "!(4.0..20.0).contains(&self.end_zbar)")
    assert hit["line"] == 2 and hit["text"].startswith("|| !(4.0..20.0)")
    assert rr.find_line(path, "end_zbar < 4") is None


def _checkpoint():
    return {"a": 0.2, "wall_elapsed_s": 7584.829919261, "max_newton_residual": 9.973559115085753e-12,
            "last_error": 3.995062437941356e-06, "counts": [312237, 936768, 19, 0, 6563796, 312256]}


RETURN_TEXT = """status=COMPLETE_REPRESENTED_INTERVAL
a=0.2
accepted=312237
attempts=936768
comparisons=312256
rejections=19
rhs_evaluations=6563796
wall_s=7584.829919261
max_newton_residual=0.000000000009973559115085753
last_error=0.000003995062437941356
residuals=(1.5187850976872141e-13, 7.353680040074473e-8)
result=Ok(())
"""


def test_content_binding_exact_and_detects_any_field_change():
    ret = rr.parse_kv(RETURN_TEXT)
    assert ret["result"] == "Ok(())"
    assert rr.parse_residual_pair(ret["residuals"]) == (1.5187850976872141e-13, 7.353680040074473e-08)
    native = (1.5187850976872141e-13, 7.353680040074473e-08)
    ok = rr.content_binding(ret, _checkpoint(), native)
    assert ok["all_equal"] and len(ok["fields_equal"]) == 11
    bad_count = dict(ret, rejections="20")
    assert not rr.content_binding(bad_count, _checkpoint(), native)["fields_equal"]["rejections"]
    bad_res = rr.content_binding(ret, _checkpoint(), (native[0], math.nextafter(native[1], 1.0)))
    assert not bad_res["all_equal"] and not bad_res["fields_equal"]["residual_energy_equals_native_recomputed"]


def test_flrw_q0_age_matches_analytic_matter_and_radiation_limits():
    h0 = rr.H0
    a_lo, a_hi = 1e-8, 1.0 / 21.0
    matter = rr.flrw_q0_age(a_hi, a_lo, h0=h0, om=1.0, or_=0.0, ol=0.0)
    assert_allclose(matter, 2.0 / (3.0 * h0) * (a_hi**1.5 - a_lo**1.5), rtol=1e-11)
    radiation = rr.flrw_q0_age(a_hi, a_lo, h0=h0, om=0.0, or_=1e-4, ol=0.0)
    assert_allclose(radiation, (a_hi**2 - a_lo**2) / (2.0 * h0 * math.sqrt(1e-4)), rtol=1e-11)
    # default parameters are the lock's q=0 FLRW law; adding radiation lowers the age below matter-only
    assert rr.flrw_q0_age(a_hi) < rr.flrw_q0_age(a_hi, om=rr.OM, or_=0.0, ol=rr.OL)


def _state(accepted, attempts, rejects, rhs, comparisons, next_dln_a=1.25e-5):
    return {"accepted": accepted, "attempts": attempts, "rejects": rejects, "rhs_evaluations": rhs,
            "comparisons": comparisons, "next_dln_a": next_dln_a}


def test_replay_window_constant_step_and_rejection_detection():
    a0, step = 0.199, 1.25e-5
    lna = math.log(a0) + step * np.arange(11)
    lna[-1] = lna[-2] + 0.6 * step                     # endpoint-clipped final step
    start = _state(100, 300, 19, 2100, 101)
    refs = [_state(105, 315, 19, 2205, 106), _state(110, 330, 19, 2310, 111)]
    w = rr.replay_window(start, refs, np.exp(lna), 1000, [])
    assert w["accepted_steps_replayed"] == 10 and w["rejections_in_window"] == 0
    assert w["attempts_per_accepted_step"] == 3.0 and w["fraction_of_run_accepted_steps"] == 0.01
    assert w["regime"] == "CONSTANT_STEP_NO_REJECTION_ENDPOINT_CLIPPED_FINAL_STEP"
    assert_allclose(w["final_step_over_next_dln_a"], 0.6, rtol=1e-9)
    assert w["branches_not_exercised"] == ["adaptive reject branch", "step-size change branch"]
    rejected = [_state(105, 316, 20, 2205, 107), _state(110, 331, 20, 2310, 112)]
    assert rr.replay_window(start, rejected, np.exp(lna), 1000, [])["regime"].startswith("NOT_CONSTANT")
    with pytest.raises(ValueError):
        rr.replay_window(start, refs, np.exp(lna[:-1]), 1000, [])


def test_headline_residual_zero_only_when_every_field_bitwise_equal():
    ref = {"accepted": 5, "a": 0.2, "energy_residual_eV_per_H": 7e-8, "ledgers": [1.0, 2.0], "photons": [3.0],
           "wall_elapsed_s": 1.0}
    same = rr.diff_report(dict(ref), ref)
    head = rr.headline_residual({"x": same})
    assert head["all_bitwise_equal"] and head["max_abs_difference_any_field"] == 0.0
    assert head["includes_ledgers_photons_energy_residual"] and "wall_elapsed_s" not in head["fields_compared"]
    moved = rr.diff_report(dict(ref, ledgers=[1.0, math.nextafter(2.0, 3.0)]), ref)
    head = rr.headline_residual({"x": same, "y": moved})
    assert not head["all_bitwise_equal"] and head["unequal_fields"] == ["y:ledgers"]
    assert head["max_abs_difference_any_field"] > 0.0


def test_clock_h_consistency_is_a_clock_check_not_a_tau_check():
    # de Sitter clock: t = (N - N0)/H exactly, n_e ~ a^-3; both forms equal the analytic integral.
    H = 2.0e-17
    N = np.linspace(math.log(1 / 21), math.log(0.2), 4001)
    frame = {"a": np.exp(N), "time_s": (N - N[0]) / H, "H_per_s": np.full_like(N, H),
             "ne_proper_cm3": 2.4e-5 * (0.2 / np.exp(N)) ** 3}
    out = rr.clock_h_consistency(frame)
    k = rr.C_SI * rr.SIGMA_T_SI * 2.4e-5 * 1e6 * 0.2**3 / H
    exact = k * (math.exp(-3 * N[0]) - math.exp(-3 * N[-1])) / 3
    assert abs(out["clock_H_consistency"]["relative_native_rows"]) < 1e-12
    assert_allclose(out["int_c_sigmaT_ne_over_H_dN"]["richardson"], exact, rtol=1e-12)
    assert_allclose(out["int_c_sigmaT_ne_over_H_dN"]["cubic_spline"], exact, rtol=1e-11)
    assert abs(out["quadrature_error_estimate"]["dN_form_native_rows_minus_richardson_relative"]) > 1e-9
    # A wrong n_e normalisation changes both forms identically: the consistency check cannot see it.
    wrong = rr.clock_h_consistency(dict(frame, ne_proper_cm3=2 * frame["ne_proper_cm3"]))
    assert_allclose(wrong["clock_H_consistency"]["relative_native_rows"],
                    out["clock_H_consistency"]["relative_native_rows"], atol=1e-14)
    assert rr.cubic_spline_integral([1.0, 2.0, 3.0, 4.0], [0.0, 1.0, 1.0, 2.0]) is None


def test_recorder_drop_capture_and_rustc_info(tmp_path):
    rec = rr.Recorder(tmp_path)
    rec.append({"tag": "replay_ZERO", "return_code": 0})
    rec.append({"tag": "analyze_old", "return_code": 0})
    rec.drop(("analyze_",))
    assert [r["tag"] for r in rec.records()] == ["replay_ZERO"]
    r = rec.capture(["true"], "analyze_true")
    assert r.returncode == 0 and rec.records()[-1]["tag"] == "analyze_true"
    with pytest.raises(RuntimeError):
        rec.capture(["false"], "analyze_false")
    assert rr.rustc_of_cached_build(tmp_path) is None
    (tmp_path / ".rustc_info.json").write_text(json.dumps(
        {"outputs": {"1": {"stdout": "___\nlib___.rlib\n"}, "2": {"stdout": "rustc 1.0.0 (abc 2020-01-01)\nhost: x\n"}}}))
    assert rr.rustc_of_cached_build(tmp_path).startswith("rustc 1.0.0")


def test_crate_imports_reads_plain_and_grouped_paths():
    text = "use crate::coupled_primary::Thing;\nuse crate::{ForwardError, hhe_events::Eos, igm_rates};\n"
    assert rr.crate_imports(text) == {"coupled_primary", "ForwardError", "hhe_events", "igm_rates"}
