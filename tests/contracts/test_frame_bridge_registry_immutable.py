from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.frame_typed_algebra import (  # noqa: E402
    Bridge,
    FrameTypeError,
    Typed,
    bridge,
    register_bridge,
)


def test_caller_cannot_register_an_unreviewed_frame_conversion() -> None:
    value = Typed("Sigma2", Fraction(1, 10), "n")
    with pytest.raises(FrameTypeError, match="runtime bridge registration"):
        register_bridge(Bridge("n", "obs", remainder_order=0, note="self-issued"))
    with pytest.raises(FrameTypeError, match="no registered bridge"):
        bridge(value, "obs")


def test_caller_cannot_overwrite_a_canonical_bridge() -> None:
    with pytest.raises(FrameTypeError, match="runtime bridge registration"):
        register_bridge(Bridge("u", "n", remainder_order=0, note="overwritten"))
    converted = bridge(Typed("W2", Fraction(1, 100), "u"), "n")
    assert converted.frame == "n"


def test_only_canonical_directions_remain_available() -> None:
    observer = Typed("A_v", Fraction(1, 1000), "obs", order=1)
    matter = bridge(observer, "u")
    normal = bridge(matter, "n")
    assert (matter.frame, normal.frame) == ("u", "n")
    with pytest.raises(FrameTypeError, match="no registered bridge"):
        bridge(normal, "u")
