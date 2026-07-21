"""PR-210 gates: typed DefectBundle + defect-identity seal + bridge gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.revival_defect_bundle import (  # noqa: E402
    BridgeReceipt,
    BundleError,
    ComponentState,
    Epoch,
    Frame,
    combine,
    comparator_value,
)

CARD = REPO / "docs/generated/pr210_result_card.json"
E = Epoch(redshift=0.0)


def _g(frame=Frame.NORMAL, epoch=E):
    return ComponentState(0.02, 0.005, 0.01, -0.003, frame, epoch)


def test_comparator_value_matches_master_identity():
    assert abs(comparator_value(_g()) - 0.022) < 1e-15


def test_negative_magnitude_rejected():
    with pytest.raises(BundleError):
        ComponentState(-1, 0, 0, 0, Frame.NORMAL, E).validate()


def test_frame_mix_without_bridge_rejected():
    with pytest.raises(BundleError):
        combine([_g(Frame.NORMAL), _g(Frame.MATTER)])


def test_epoch_mix_rejected():
    with pytest.raises(BundleError):
        combine([_g(), ComponentState(0.01, 0, 0.001, 0, Frame.NORMAL, Epoch(redshift=1.0))])


def test_certified_bridge_allows_frame_mix():
    b = BridgeReceipt("B", Frame.MATTER, Frame.NORMAL, {}, "CERTIFIED", "prov")
    val = combine([_g(Frame.NORMAL), _g(Frame.MATTER)], (b,))
    assert isinstance(val, float)


def test_uncertified_bridge_rejected():
    b = BridgeReceipt("B", Frame.MATTER, Frame.NORMAL, {}, "PENDING", "")
    with pytest.raises(BundleError):
        combine([_g(Frame.NORMAL), _g(Frame.MATTER)], (b,))


def test_signed_delta_omega_k_allowed():
    # negative DeltaOmega_k is admissible (signed carrier), unlike magnitudes
    g = ComponentState(0.02, 0.005, 0.01, -0.5, Frame.NORMAL, E)
    assert comparator_value(g) < 0


def test_card_seal_and_check_stable():
    if not CARD.exists():
        pytest.skip("card not yet written")
    card = json.loads(CARD.read_text())
    assert card["result"]["defect_identity_seal"]["seal_pass"] is True
    assert card["terminal"] == "TYPED_DEFECT_BUNDLE_CONSTITUTION_CERTIFIED"
    assert card["metadata"]["independence_gate"] == "OPEN"
