from __future__ import annotations

import inspect
from dataclasses import is_dataclass

import pytest

from bass.inference import PosteriorSample, run_posterior
from bass.inference.__main__ import build_parser, main


@pytest.mark.skip(reason="pending FB-11.2 implementation — skeleton only")
def test_fb112_emcee_driver_skeleton_contract() -> None:
    assert is_dataclass(PosteriorSample)

    signature = inspect.signature(run_posterior)
    assert signature.parameters["seed"].default is inspect._empty
    assert signature.parameters["n_walkers"].default == 64
    assert signature.parameters["n_steps"].default == 5000
    assert signature.parameters["burnin"].default == 1000
    assert signature.parameters["parallel"].default is False

    doc = run_posterior.__doc__ or ""
    assert "byte-identical" in doc
    assert "parallel=False" in doc

    parser = build_parser()
    option_strings = {option for action in parser._actions for option in action.option_strings}
    assert "--config" in option_strings
    assert "--seed" in option_strings
    assert callable(main)
