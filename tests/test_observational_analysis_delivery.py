"""Focused regressions for released-summary plotting and preparation."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import quad


ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analysis = load_script("analyze_desi_bao_summary")
preparation = load_script("prepare_observational_analysis")


def payload():
    return {"likelihood_name": "gaussian_likelihood", "parameter": "qiso",
            "observed": [1.02], "covariance": [[0.0004]], "window": [[1.0]],
            "zeff": 0.3, "DV_over_rd_fid": 8.0, "source_id": "SYNTHETIC_TEST_ONLY"}


def test_gaussian_likelihood_affine_propagation_and_interval():
    result, curve = analysis.analyze_payload(payload())
    m = result["measurement"]
    assert m["DV_over_rd"] == pytest.approx(8.16)
    assert m["DV_over_rd_sigma"] == pytest.approx(.16)
    assert m["DV_over_rd_variance"] == pytest.approx(.0256)
    assert result["conditional_intervals"][1]["coverage"] == .95
    assert result["conditional_intervals"][1]["qiso"] == pytest.approx([.9808007203, 1.0591992797])
    q = curve["qiso_prediction"]
    expected = -.5 * ((1.02-q)**2/.0004 + np.log(2*np.pi*.0004))
    np.testing.assert_allclose(curve["log_sampling_density_q_at_observed"], expected, atol=1e-13)
    np.testing.assert_allclose(curve["relative_likelihood"], np.exp(-.5*((1.02-q)/.02)**2), atol=1e-13)
    assert np.max(curve["relative_likelihood"]) == 1.0


def test_observed_density_jacobian_normalizes_without_parameter_jacobian():
    from scipy.stats import norm
    f, q, sigma = 8., 1.02, .02
    integrate = quad(lambda d: np.exp(analysis.log_density_in_dv(norm.logpdf(d/f,q,sigma),f)),
                     f*(q-10*sigma), f*(q+10*sigma))[0]
    assert integrate == pytest.approx(1., abs=1e-11)
    _, curve = analysis.analyze_payload(payload())
    transformed = curve["log_sampling_density_D_at_observed"]
    np.testing.assert_allclose(np.exp(transformed-transformed.max()),curve["relative_likelihood"],atol=1e-13)


@pytest.mark.parametrize("field,value", [("window",[[2.]]),("covariance",[[0.]]),
    ("covariance",[[-.1]]),("observed",[float("nan")]),("DV_over_rd_fid",float("inf")),
    ("zeff",0.),("parameter","alpha")])
def test_invalid_summary_rejected(field,value):
    data=payload(); data[field]=value
    with pytest.raises((ValueError, KeyError)):
        analysis.analyze_payload(data)


def test_positive_parameter_interval_boundary():
    data=payload();data["observed"]=[.001]
    result,_=analysis.analyze_payload(data)
    interval=result["conditional_intervals"][1]
    assert interval["qiso"][0] == 0
    assert interval["lower_endpoint_included"] is False


def test_source_binding_and_output_preservation(tmp_path):
    wrong=tmp_path/"wrong.h5";wrong.write_bytes(b"NOT_A_RELEASE")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        analysis.run(wrong,tmp_path/"new")
    assert not (tmp_path/"new").exists()
    out=tmp_path/"existing";out.mkdir();(out/"keep").write_text("original")
    with pytest.raises(FileExistsError):
        analysis.run(wrong,out)
    assert (out/"keep").read_text()=="original"


def test_preparation_does_not_promote_input_availability(tmp_path):
    (tmp_path/"runner.py").write_text("")
    (tmp_path/"data").write_text("unvalidated")
    product={"id":"demo","scope":"DIAGNOSTIC_ONLY","inputs":["data"],
             "entrypoint":"runner.py","runtime":"py","arguments":[],
             "scientific_fit_status":"HOLD_PHYSICAL_INPUTS","next_physical_inputs":["calibration"]}
    result=preparation.build_preparation(tmp_path,{"products":[product],"tasks":[]},
                                       {"py":{"executable":"python","available":True}},tmp_path/"run")
    assert result["products"][0]["runnable_input_check"] is True
    assert result["products"][0]["scientific_fit_status"]=="HOLD_PHYSICAL_INPUTS"
    (tmp_path/"data").unlink()
    result=preparation.build_preparation(tmp_path,{"products":[product],"tasks":[]},
                                       {"py":{"executable":"python","available":True}},tmp_path/"run")
    assert result["products"][0]["runnable_input_check"] is False


def test_current_runtime_classification():
    import sys
    ok=preparation.probe_runtime(sys.executable,["json"],ROOT)
    assert ok["status"]=="PYTHON_PASS"
    missing=preparation.probe_runtime(sys.executable,["htt_test_missing_dependency_9d6f"],ROOT)
    assert missing["status"]=="PACKAGE_MISSING"
