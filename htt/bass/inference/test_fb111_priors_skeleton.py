from __future__ import annotations

import inspect
from dataclasses import is_dataclass

import pytest

from bass.inference import (
    Prior,
    prior_direction,
    prior_observer_boost,
    prior_rapidity,
    prior_structure_constants,
    prior_Sigma_mnu,
)


@pytest.mark.skip(reason="pending FB-11.1 implementation — skeleton only")
def test_fb111_priors_skeleton_contract() -> None:
    assert is_dataclass(Prior)

    rapidity_signature = inspect.signature(prior_rapidity)
    assert rapidity_signature.parameters["label"].default is inspect._empty
    assert rapidity_signature.parameters["sigma"].kind is inspect.Parameter.KEYWORD_ONLY

    structure_signature = inspect.signature(prior_structure_constants)
    assert structure_signature.parameters["bianchi_type"].default is inspect._empty

    assert len(inspect.signature(prior_direction).parameters) == 0
    assert len(inspect.signature(prior_Sigma_mnu).parameters) == 0
    assert len(inspect.signature(prior_observer_boost).parameters) == 0

    sigma_doc = prior_Sigma_mnu.__doc__ or ""
    observer_doc = prior_observer_boost.__doc__ or ""
    assert "Planck 2018 VI" in sigma_doc
    assert "Kosowsky" in observer_doc
