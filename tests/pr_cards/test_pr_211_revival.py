"""PR-211 gates: W2 convention successor + signed split + PR-186 cross-ref."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.revival_w2_convention import (  # noqa: E402
    FROZEN_W2_MAX,
    assert_dual_identity,
    crossref_pr186,
    force_psd_would_lose_sign,
    w2_ceiling,
    w2_from_tensor,
    w2_from_vector,
)

CARD = REPO / "docs/generated/pr211_result_card.json"


def test_tensor_equals_vector_form():
    H, ov = 70.0, 1.7e-6
    assert abs(w2_from_tensor(2 * ov, H) - w2_from_vector(ov, H)) < 1e-18


def test_dual_identity_holds_and_wrong_form_breaks_it():
    H, ov = 70.0, 1.7e-6
    assert_dual_identity(2 * ov, ov, H)  # holds
    # the retired /H^2 vector form is exactly 3x the correct one
    assert abs((ov / H**2) / w2_from_vector(ov, H) - 3.0) < 1e-12


def test_ceiling_is_three_halves_bsq():
    assert abs(w2_ceiling(2.0) - 6.0) < 1e-15


def test_psd_forcing_of_signed_curvature_detected():
    assert force_psd_would_lose_sign(-0.004) is True
    assert force_psd_would_lose_sign(0.004) is False


def test_pr186_frozen_anchor_unchanged():
    xref = crossref_pr186()
    assert xref["frozen_W2_max"] == FROZEN_W2_MAX
    assert xref["cas_five_axis_pass"] is True
    assert xref["ratio_is_three"] is True


def test_card_terminal_and_check_stable():
    if not CARD.exists():
        pytest.skip("card not yet written")
    card = json.loads(CARD.read_text())
    assert card["metadata"]["disposition"] == "LITERAL_RESCUE"
    assert card["result"]["pr186_crossref"]["frozen_unchanged"] is True
    assert card["terminal"] == "W2_CONVENTION_SUCCESSOR_CERTIFIED_PR186_FROZEN_UNCHANGED"
