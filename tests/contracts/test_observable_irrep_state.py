"""PMG-WU-001 contracts for observer/data-space irreducible states."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import hashlib
import importlib
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "htt" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _api():
    try:
        return importlib.import_module("common.observable_irrep_state")
    except ModuleNotFoundError as exc:
        pytest.fail(
            "ObservableIrrepState public API is not implemented",
            pytrace=False,
        )
        raise AssertionError("unreachable") from exc


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _carrier(api, *, row_identity: str = "SMICA_OBSERVED"):
    return api.ObservableIrrepCarrier(
        components=tuple(float(index) for index in range(1, 33)),
        frame="GALACTIC",
        basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
        units="microK_CMB",
        source_identity=_sha("planck-smica-row"),
        operator_identity=_sha("joint-cutsky-operator"),
        row_identity=row_identity,
    )


def _harmonic_block(api, *, ell: int = 2, carrier=None):
    selected = carrier if carrier is not None else _carrier(api)
    return api.build_real_harmonic_irrep_block(carrier=selected, ell=ell)


def _stf_block(api, *, ell: int = 2, parent=None, components=None):
    selected_parent = parent if parent is not None else _harmonic_block(api, ell=ell)
    if components is None:
        dimension = 5 if ell == 2 else 7
        components = tuple(float((-1) ** index * (index + 1)) for index in range(dimension))
    return api.build_cartesian_stf_irrep_block(
        parent=selected_parent,
        components=components,
        basis=f"CARTESIAN_STF{ell}_{2 * ell + 1}_ORTHONORMAL_V1",
        projection_identity=_sha(f"harmonic-to-stf-l{ell}-projection"),
    )


def _state(api, *blocks, **overrides):
    selected = blocks or (_harmonic_block(api),)
    support = selected[0].support
    kwargs = {
        "blocks": selected,
        "frame": support.frame,
        "basis": support.basis,
        "units": support.units,
        "source_identity": support.source_identity,
        "operator_identity": support.operator_identity,
        "row_identity": support.row_identity,
    }
    kwargs.update(overrides)
    return api.ObservableIrrepState(**kwargs)


def test_complete_carrier_builds_harmonic_blocks_and_roundtrips_exactly() -> None:
    """Catch scalar padding, carrier slicing drift, or payload identity loss."""

    api = _api()
    carrier = _carrier(api)
    assert len(carrier.layout) == 32
    assert carrier.layout[:5] == (
        (2, 0, "real"),
        (2, 1, "real"),
        (2, 1, "imag"),
        (2, 2, "real"),
        (2, 2, "imag"),
    )

    l2 = _harmonic_block(api, ell=2, carrier=carrier)
    l3 = _harmonic_block(api, ell=3, carrier=carrier)
    state = _state(api, l2, l3)

    assert l2.components == (1.0, 2.0, 3.0, 4.0, 5.0)
    assert l3.components == tuple(float(index) for index in range(6, 13))
    payload = state.to_payload()
    assert payload["schema"] == "HTT_OBSERVABLE_IRREP_STATE_V1"
    assert payload["semantic_layer"] == "OBSERVER_DATA_SPACE"
    assert payload["claim_ceiling"] == "diagnostic_only_observer_space"
    assert payload["blocks"][0]["support"]["kind"] == "REAL_HARMONIC_CARRIER"
    assert payload["blocks"][0]["support"]["support_identity"] == carrier.content_id
    assert payload["content_id"] == state.content_id

    replayed = api.observable_irrep_state_from_payload(payload)
    assert type(replayed) is api.ObservableIrrepState
    assert replayed == state
    assert replayed.content_id == state.content_id
    assert replayed.to_payload() == payload

    payload["blocks"][0]["components"][0] = 999.0
    assert state.to_payload()["blocks"][0]["components"][0] == 1.0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("ell", 3, "ell"),
        ("spin", 1, "spin"),
        ("parity", "ODD", "parity"),
        ("components", [1.0, 2.0, 3.0, 4.0], "dimension"),
    ],
)
def test_block_replay_refuses_wrong_ell_spin_parity_or_dimension(
    field: str,
    value: object,
    message: str,
) -> None:
    """Catch an irrep label whose component shape or O(3) metadata drifted."""

    api = _api()
    payload = _harmonic_block(api).to_payload()
    payload[field] = value
    with pytest.raises(api.ObservableIrrepStateError, match=message):
        api.ObservableIrrepBlock.from_payload(payload)


def test_stf_projection_requires_harmonic_parent_and_roundtrips_typed_absence() -> None:
    """Catch an STF block not bound to a retained harmonic parent/projection."""

    api = _api()
    parent = _harmonic_block(api, ell=3)
    absence = api.ObservableIrrepAbsence(
        reason="shape is undefined at zero amplitude",
        stratum="ZERO_AMPLITUDE",
    )
    block = _stf_block(api, ell=3, parent=parent, components=absence)
    state = _state(api, block)

    payload = state.to_payload()
    block_payload = payload["blocks"][0]
    assert block_payload["availability"] == "ABSENT"
    assert block_payload["components"] is None
    assert block_payload["absence"]["stratum"] == "ZERO_AMPLITUDE"
    assert block_payload["support"]["kind"] == "REGISTERED_STF_PROJECTION"
    assert block_payload["support"]["parent_irrep_content_id"] == parent.content_id

    replayed = api.observable_irrep_state_from_payload(payload)
    assert type(replayed.blocks[0].components) is api.ObservableIrrepAbsence
    assert replayed.blocks[0].components.reason == absence.reason


def test_scalar_refusal_and_physical_claim_refusal_are_fail_closed() -> None:
    """Catch scalar-to-STF fabrication or observer-to-physical promotion."""

    api = _api()
    with pytest.raises(api.ObservableIrrepStateError, match="carrier"):
        api.build_real_harmonic_irrep_block(carrier=74 / 301, ell=2)
    with pytest.raises(api.ObservableIrrepStateError, match="parent"):
        api.build_cartesian_stf_irrep_block(
            parent=74 / 301,
            components=(74 / 301, 0.0, 0.0, 0.0, 0.0),
            basis="CARTESIAN_STF2_5_ORTHONORMAL_V1",
            projection_identity=_sha("fake-scalar-projection"),
        )
    with pytest.raises(api.ObservableIrrepStateError, match="factory-built"):
        api.ObservableIrrepBlock(
            ell=2,
            spin=0,
            representation="CARTESIAN_STF2_5",
            parity="EVEN",
            components=(1.0, 2.0, 3.0, 4.0, 5.0),
            support=None,
        )
    with pytest.raises(api.ObservableIrrepStateError, match="blocks"):
        api.ObservableIrrepState(
            blocks=98 / 301,
            frame="GALACTIC",
            basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
            units="microK_CMB",
            source_identity=_sha("scalar-row"),
            operator_identity=_sha("scalar-operator"),
            row_identity="SCALAR_ONLY",
        )

    payload = _state(api).to_payload()
    payload["blocks"][0]["representation"] = "PHYSICAL_SHEAR_STF2"
    with pytest.raises(api.ObservableIrrepStateError, match="representation"):
        api.observable_irrep_state_from_payload(payload)

    payload = _state(api).to_payload()
    payload["claim_ceiling"] = "physical_shear"
    with pytest.raises(api.ObservableIrrepStateError, match="claim ceiling"):
        api.observable_irrep_state_from_payload(payload)

    payload = _state(api).to_payload()
    payload["physical_source"] = "vorticity"
    with pytest.raises(api.ObservableIrrepStateError, match="keys"):
        api.observable_irrep_state_from_payload(payload)


def test_complete_carrier_and_projection_identities_are_strict_and_content_bound() -> None:
    """Catch arbitrary prose identities masquerading as retained support."""

    api = _api()
    with pytest.raises(api.ObservableIrrepStateError, match="32"):
        api.ObservableIrrepCarrier(
            components=(74 / 301,) + (0.0,) * 4,
            frame="GALACTIC",
            basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
            units="microK_CMB",
            source_identity=_sha("scalar-row"),
            operator_identity=_sha("scalar-operator"),
            row_identity="SCALAR_ONLY",
        )

    parent = _harmonic_block(api)
    with pytest.raises(api.ObservableIrrepStateError, match="sha256"):
        api.build_cartesian_stf_irrep_block(
            parent=parent,
            components=(1.0, 2.0, 3.0, 4.0, 5.0),
            basis="CARTESIAN_STF2_5_ORTHONORMAL_V1",
            projection_identity="sha256:not-a-content-identity",
        )

    carrier_payload = _carrier(api).to_payload()
    carrier_payload["components"][0] = -999.0
    with pytest.raises(api.ObservableIrrepStateError, match="content identity"):
        api.ObservableIrrepCarrier.from_payload(carrier_payload)

    block_payload = parent.to_payload()
    block_payload["support"]["support_identity"] = _sha("unrelated-carrier")
    with pytest.raises(api.ObservableIrrepStateError, match="content identity|support"):
        api.ObservableIrrepBlock.from_payload(block_payload)


def test_state_refuses_cross_row_operator_basis_or_units_block_grafting() -> None:
    """Catch a valid block being relabelled under unrelated state metadata."""

    api = _api()
    block = _harmonic_block(api)
    for field, value in (
        ("row_identity", "OTHER_ROW"),
        ("operator_identity", _sha("other-operator")),
        ("basis", "OTHER_BASIS"),
        ("units", "dimensionless"),
    ):
        with pytest.raises(api.ObservableIrrepStateError, match="support metadata"):
            _state(api, block, **{field: value})

    stf = _stf_block(api, parent=block)
    with pytest.raises(api.ObservableIrrepStateError, match="support metadata"):
        _state(api, block, stf)


def test_block_support_receipt_and_state_are_frozen_and_detect_identity_drift() -> None:
    """Catch mutation after construction from masquerading under an old ID."""

    api = _api()
    block = _harmonic_block(api)
    state = _state(api, block)

    with pytest.raises(FrozenInstanceError):
        state.row_identity = "OTHER"  # type: ignore[misc]

    object.__setattr__(block.support, "row_identity", "OTHER")
    with pytest.raises(api.ObservableIrrepStateError, match="identity drifted"):
        block.to_payload()

    block = _harmonic_block(api)
    object.__setattr__(block, "components", (0.0,) * 5)
    with pytest.raises(api.ObservableIrrepStateError, match="identity drifted|component"):
        block.to_payload()

    object.__setattr__(state, "row_identity", "OTHER")
    with pytest.raises(api.ObservableIrrepStateError, match="identity drifted"):
        state.to_payload()
