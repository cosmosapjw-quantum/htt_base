"""PMG-WU-002 one-way MES premise-normalization contracts."""

from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "htt" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from common.statistical_foundations import (
    AnchorConditioning,
    registered_geodesic_mes_anchors,
)


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _anchor():
    return registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=2.0e-6,
        eps3=5.0e-6,
        attribution="explicit SAG residual eps1=0 contract fixture",
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )["sigma"]


def test_same_channel_normalization_is_dimension_preserving_and_information_neutral() -> None:
    """Catch a normalizer that fabricates support or changes coordinate dimension."""

    api = importlib.import_module("common.mes_premise_normalization")
    anchor = _anchor()
    report = api.normalize_mes_premise(
        numerator=(2.0, -4.0, 1.0),
        numerator_channel_key=anchor.channel_key,
        numerator_identity=_sha("directional-numerator"),
        anchor=anchor,
    )

    assert type(report) is api.MesPremiseNormalizer
    assert report.normalized_values == pytest.approx(
        tuple(value / anchor.value for value in (2.0, -4.0, 1.0))
    )
    assert len(report.normalized_values) == 3
    assert report.channel_key == anchor.channel_key
    assert report.creates_direction is False
    assert report.creates_shape is False
    assert report.creates_information is False
    assert report.creates_response is False
    assert report.physical_state_constructed is False
    assert api.MesPremiseNormalizer.from_payload(report.to_payload()) == report


def test_normalization_refuses_scalar_or_cross_channel_premise() -> None:
    api = importlib.import_module("common.mes_premise_normalization")
    anchor = _anchor()
    with pytest.raises(api.MesPremiseNormalizationError, match="sequence"):
        api.normalize_mes_premise(
            numerator=0.2458,
            numerator_channel_key=anchor.channel_key,
            numerator_identity=_sha("scalar-premise"),
            anchor=anchor,
        )
    with pytest.raises(api.MesPremiseNormalizationError, match="channel"):
        api.normalize_mes_premise(
            numerator=(1.0,),
            numerator_channel_key=("different", "channel"),
            numerator_identity=_sha("cross-channel-premise"),
            anchor=anchor,
        )


def test_payload_replay_refuses_information_creation_flag() -> None:
    api = importlib.import_module("common.mes_premise_normalization")
    anchor = _anchor()
    report = api.normalize_mes_premise(
        numerator=(1.0,),
        numerator_channel_key=anchor.channel_key,
        numerator_identity=_sha("sealed-premise"),
        anchor=anchor,
    )
    payload = report.to_payload()
    payload["creates_information"] = True
    with pytest.raises(api.MesPremiseNormalizationError, match="claim boundary"):
        api.MesPremiseNormalizer.from_payload(payload)
