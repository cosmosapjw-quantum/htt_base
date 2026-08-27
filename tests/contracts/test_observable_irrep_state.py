"""PMG-WU-001 contracts for observer/data-space irreducible states."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
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


def _available_block(api, *, ell: int = 2):
    if ell == 2:
        return api.ObservableIrrepBlock(
            ell=2,
            spin=0,
            representation="REAL_SPHERICAL_HARMONIC_5",
            parity="EVEN",
            components=(1.0, -2.0, 3.0, -4.0, 5.0),
            support_kind="REAL_HARMONIC_CARRIER",
            support_identity="sha256:test-real-harmonic-carrier-l2",
        )
    return api.ObservableIrrepBlock(
        ell=3,
        spin=0,
        representation="REAL_SPHERICAL_HARMONIC_7",
        parity="ODD",
        components=(1.0, -2.0, 3.0, -4.0, 5.0, -6.0, 7.0),
        support_kind="REAL_HARMONIC_CARRIER",
        support_identity="sha256:test-real-harmonic-carrier-l3",
    )


def _state(api, *blocks):
    selected = blocks or (_available_block(api),)
    return api.ObservableIrrepState(
        blocks=selected,
        frame="GALACTIC",
        basis="ORTHONORMAL_CONDON_SHORTLEY_REAL",
        units="microK_CMB",
        source_identity="sha256:planck-smica-row",
        operator_identity="sha256:joint-cutsky-operator",
        row_identity="SMICA_OBSERVED",
    )


def test_available_observable_irrep_state_roundtrips_with_exact_identity() -> None:
    """Catch payload aliasing, noncanonical replay, or identity loss."""

    api = _api()
    state = _state(api, _available_block(api), _available_block(api, ell=3))

    payload = state.to_payload()
    assert payload["schema"] == "HTT_OBSERVABLE_IRREP_STATE_V1"
    assert payload["semantic_layer"] == "OBSERVER_DATA_SPACE"
    assert payload["claim_ceiling"] == "diagnostic_only_observer_space"
    assert payload["blocks"][0]["components"] == [1.0, -2.0, 3.0, -4.0, 5.0]
    assert payload["blocks"][1]["parity"] == "ODD"
    assert payload["content_id"] == state.content_id

    replayed = api.observable_irrep_state_from_payload(payload)
    assert type(replayed) is api.ObservableIrrepState
    assert replayed == state
    assert replayed.content_id == state.content_id
    assert replayed.to_payload() == payload

    payload["blocks"][0]["components"][0] = 999.0
    assert state.to_payload()["blocks"][0]["components"][0] == 1.0


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"ell": 3}, "ell"),
        ({"spin": 1}, "spin"),
        ({"parity": "ODD"}, "parity"),
        ({"components": (1.0, 2.0, 3.0, 4.0)}, "dimension"),
    ],
)
def test_representation_refuses_wrong_ell_spin_parity_or_dimension(
    overrides: dict[str, object],
    message: str,
) -> None:
    """Catch an irrep label whose component shape or O(3) metadata drifted."""

    api = _api()
    kwargs: dict[str, object] = {
        "ell": 2,
        "spin": 0,
        "representation": "REAL_SPHERICAL_HARMONIC_5",
        "parity": "EVEN",
        "components": (1.0, -2.0, 3.0, -4.0, 5.0),
        "support_kind": "REAL_HARMONIC_CARRIER",
        "support_identity": "sha256:test-real-harmonic-carrier-l2",
    }
    kwargs.update(overrides)
    with pytest.raises(api.ObservableIrrepStateError, match=message):
        api.ObservableIrrepBlock(**kwargs)


def test_typed_absence_roundtrips_without_a_numeric_fallback() -> None:
    """Catch an undefined irrep block being silently zero-filled."""

    api = _api()
    absence = api.ObservableIrrepAbsence(
        reason="shape is undefined at zero amplitude",
        stratum="ZERO_AMPLITUDE",
    )
    block = api.ObservableIrrepBlock(
        ell=3,
        spin=0,
        representation="CARTESIAN_STF3_7",
        parity="ODD",
        components=absence,
        support_kind="REGISTERED_STF_PROJECTION",
        support_identity="sha256:test-stf3-degenerate-projection",
    )
    state = _state(api, block)

    payload = state.to_payload()
    block_payload = payload["blocks"][0]
    assert block_payload["availability"] == "ABSENT"
    assert block_payload["components"] is None
    assert block_payload["absence"]["stratum"] == "ZERO_AMPLITUDE"

    replayed = api.observable_irrep_state_from_payload(payload)
    assert type(replayed.blocks[0].components) is api.ObservableIrrepAbsence
    assert replayed.blocks[0].components.reason == absence.reason


def test_scalar_refusal_and_physical_claim_refusal_are_fail_closed() -> None:
    """Catch scalar-to-STF fabrication or observer-to-physical promotion."""

    api = _api()
    with pytest.raises(api.ObservableIrrepStateError, match="components"):
        api.ObservableIrrepBlock(
            ell=2,
            spin=0,
            representation="CARTESIAN_STF2_5",
            parity="EVEN",
            components=74 / 301,
            support_kind="REGISTERED_STF_PROJECTION",
            support_identity="sha256:direct-scalar-must-still-fail",
        )
    with pytest.raises(api.ObservableIrrepStateError, match="blocks"):
        api.ObservableIrrepState(
            blocks=98 / 301,
            frame="GALACTIC",
            basis="ORTHONORMAL_CONDON_SHORTLEY_REAL",
            units="microK_CMB",
            source_identity="sha256:scalar-row",
            operator_identity="sha256:scalar-operator",
            row_identity="SCALAR_ONLY",
        )
    with pytest.raises(api.ObservableIrrepStateError, match="representation"):
        api.ObservableIrrepBlock(
            ell=2,
            spin=0,
            representation="PHYSICAL_SHEAR_STF2",
            parity="EVEN",
            components=(1.0, 2.0, 3.0, 4.0, 5.0),
            support_kind="REGISTERED_STF_PROJECTION",
            support_identity="sha256:forbidden-physical-label",
        )

    payload = _state(api).to_payload()
    payload["claim_ceiling"] = "physical_shear"
    with pytest.raises(api.ObservableIrrepStateError, match="claim ceiling"):
        api.observable_irrep_state_from_payload(payload)

    payload = _state(api).to_payload()
    payload["physical_source"] = "vorticity"
    with pytest.raises(api.ObservableIrrepStateError, match="keys"):
        api.observable_irrep_state_from_payload(payload)


def test_dimension_correct_scalar_padding_cannot_claim_irrep_support() -> None:
    """Catch a scalar padded to five numbers and relabelled as an STF block."""

    api = _api()
    scalar_anchor = 74 / 301
    with pytest.raises(api.ObservableIrrepStateError, match="support_kind"):
        api.ObservableIrrepBlock(
            ell=2,
            spin=0,
            representation="CARTESIAN_STF2_5",
            parity="EVEN",
            components=(scalar_anchor, 0.0, 0.0, 0.0, 0.0),
        )
    with pytest.raises(api.ObservableIrrepStateError, match="support"):
        api.ObservableIrrepBlock(
            ell=2,
            spin=0,
            representation="CARTESIAN_STF2_5",
            parity="EVEN",
            components=(scalar_anchor, 0.0, 0.0, 0.0, 0.0),
            support_kind="SCALAR_ONLY",
            support_identity="sha256:mes-scalar-padding",
        )


def test_block_and_state_are_frozen_and_detect_identity_drift() -> None:
    """Catch mutation after construction from masquerading under the old ID."""

    api = _api()
    block = _available_block(api)
    state = _state(api, block)

    with pytest.raises(FrozenInstanceError):
        state.row_identity = "OTHER"  # type: ignore[misc]

    object.__setattr__(block, "components", (0.0,) * 5)
    with pytest.raises(api.ObservableIrrepStateError, match="identity drifted"):
        block.to_payload()

    object.__setattr__(state, "row_identity", "OTHER")
    with pytest.raises(api.ObservableIrrepStateError, match="identity drifted"):
        state.to_payload()
