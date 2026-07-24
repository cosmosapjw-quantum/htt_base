"""PR-212 gates: frame functor + Frobenius gate."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if entry not in sys.path: sys.path.insert(0, entry)
from common.revival_defect_bundle import Frame  # noqa: E402
from common.revival_frame_functor import (  # noqa: E402
    REGISTRY, FrameFunctorError, assemble, is_hypersurface_orthogonal,
    orthogonal_hypersurface_gauss_curvature)
CARD = REPO/"docs/generated/pr212_result_card.json"

def test_frobenius_zero_vs_vortical():
    assert is_hypersurface_orthogonal(0.0)
    assert not is_hypersurface_orthogonal(1e-6)

def test_gauss_curvature_defined_only_when_orthogonal():
    assert orthogonal_hypersurface_gauss_curvature(0.0, 0.7) == 0.7
    with pytest.raises(FrameFunctorError):
        orthogonal_hypersurface_gauss_curvature(1e-6, 0.7)

def test_same_frame_assembly_ok():
    assert assemble([REGISTRY["sigma_ab"], REGISTRY["W2_n"]]) == Frame.NORMAL

def test_n_shear_u_w2_without_bridge_rejected():
    with pytest.raises(FrameFunctorError):
        assemble([REGISTRY["sigma_ab"], REGISTRY["W2_u"]])

def test_bridged_cross_frame_ok():
    assert assemble(
        [REGISTRY["sigma_ab"], REGISTRY["W2_u"]], bridged=True
    ) is Frame.NORMAL

def test_truthy_bridge_flag_is_not_registration():
    with pytest.raises(FrameFunctorError, match="registered bridge"):
        assemble([REGISTRY["sigma_ab"], REGISTRY["W2_u"]], bridged="yes")

def test_unregistered_frame_pair_rejected_even_when_bridge_requested():
    with pytest.raises(FrameFunctorError, match="no registered bridge"):
        assemble([REGISTRY["sigma_ab"], REGISTRY["A_v"]], bridged=True)

def test_card_check_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "FRAME_FUNCTOR_FROBENIUS_GATE_CERTIFIED_PR187_CONSISTENT"
