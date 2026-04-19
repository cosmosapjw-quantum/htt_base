from __future__ import annotations

from dataclasses import is_dataclass

import pytest

from bass.observer.discriminator import DiscriminatorResult, likelihood_ratio


@pytest.mark.skip(reason="pending FB-8.5 implementation — skeleton only")
def test_fb85_discriminator_skeleton_contract() -> None:
    assert callable(likelihood_ratio)
    assert is_dataclass(DiscriminatorResult)
    doc = likelihood_ratio.__doc__ or ""
    assert "Lambda(data; H_obs, H_cosmo)" in doc
    assert "1007.4539" in doc
