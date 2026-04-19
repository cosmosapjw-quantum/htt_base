from __future__ import annotations

import inspect

import pytest

from bass.inference import ess, geweke, r_hat, trace_plot_data


@pytest.mark.skip(reason="pending FB-11.4 implementation — skeleton only")
def test_fb114_diagnostics_skeleton_contract() -> None:
    assert list(inspect.signature(r_hat).parameters) == ["samples"]
    assert list(inspect.signature(ess).parameters) == ["samples"]
    assert inspect.signature(geweke).parameters["first"].default == 0.1
    assert inspect.signature(geweke).parameters["last"].default == 0.5
    assert list(inspect.signature(trace_plot_data).parameters) == ["samples"]

    rhat_doc = r_hat.__doc__ or ""
    geweke_doc = geweke.__doc__ or ""
    assert "1.01" in rhat_doc
    assert "|z| < 2" in geweke_doc
