from __future__ import annotations

import inspect
from dataclasses import is_dataclass

import pytest

from bass.inference import BayesFactorResult, bayes_factor


@pytest.mark.skip(reason="pending FB-11.3 implementation — skeleton only")
def test_fb113_bayes_factor_skeleton_contract() -> None:
    assert is_dataclass(BayesFactorResult)

    signature = inspect.signature(bayes_factor)
    assert list(signature.parameters) == ["posterior_A", "posterior_B"]

    doc = bayes_factor.__doc__ or ""
    assert "thermodynamic integration" in doc
    assert "dynesty" in doc
