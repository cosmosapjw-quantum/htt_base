"""PMG-WU-002 response-bound observable identification contracts."""

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


def _sha(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def _observable_state():
    api = importlib.import_module("common.observable_irrep_state")
    carrier = api.ObservableIrrepCarrier(
        components=tuple(float(index) for index in range(1, 33)),
        frame="GALACTIC",
        basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
        units="microK_CMB",
        source_identity=_sha("response-source"),
        operator_identity=_sha("response-operator"),
        row_identity="RESPONSE_CONTRACT_ROW",
    )
    block = api.build_real_harmonic_irrep_block(carrier=carrier, ell=2)
    return api.ObservableIrrepState(
        blocks=(block,),
        frame=block.support.frame,
        basis=block.support.basis,
        units=block.support.units,
        source_identity=block.support.source_identity,
        operator_identity=block.support.operator_identity,
        row_identity=block.support.row_identity,
    )


def _bind(api, observable, **updates):
    kwargs = {
        "observable_state": observable,
        "observable_channel_key": ("temperature", "ell2", "real_harmonic"),
        "response_identity": _sha("certified-forward-response"),
        "response_channel_key": ("temperature", "ell2", "real_harmonic"),
        "response_frame": observable.frame,
        "response_basis": observable.basis,
        "response_units": observable.units,
        "response_rank": 2,
        "physical_parameter_dimension": 3,
    }
    kwargs.update(updates)
    return api.bind_response_to_observable_state(**kwargs)


def test_rank_deficient_response_reports_identified_set_not_point() -> None:
    """Catch rank deficiency being silently promoted to point identification."""

    api = importlib.import_module("common.response_bound_observable_state")
    observable = _observable_state()
    bound = _bind(api, observable)

    assert type(bound) is api.ResponseBoundObservableState
    assert bound.response_rank == 2
    assert bound.physical_parameter_dimension == 3
    assert bound.identification_status is api.ResponseIdentificationStatus.IDENTIFIED_SET
    assert bound.point_identification_supported is False
    assert bound.claim_ceiling == "diagnostic_only_response_bound"
    assert api.ResponseBoundObservableState.from_payload(bound.to_payload()) == bound


def test_full_column_rank_is_the_only_point_identification_path() -> None:
    api = importlib.import_module("common.response_bound_observable_state")
    bound = _bind(
        api,
        _observable_state(),
        response_rank=3,
        physical_parameter_dimension=3,
    )
    assert bound.identification_status is api.ResponseIdentificationStatus.POINT_IDENTIFIED
    assert bound.point_identification_supported is True


def test_response_rank_and_payload_point_flag_are_fail_closed() -> None:
    api = importlib.import_module("common.response_bound_observable_state")
    observable = _observable_state()
    with pytest.raises(api.ResponseBindingError, match="rank exceeds"):
        _bind(api, observable, response_rank=6, physical_parameter_dimension=6)
    bound = _bind(api, observable)
    payload = bound.to_payload()
    payload["point_identification_supported"] = True
    with pytest.raises(api.ResponseBindingError, match="point-identification flag"):
        api.ResponseBoundObservableState.from_payload(payload)


@pytest.mark.parametrize(
    ("update", "message"),
    (
        ({"response_channel_key": ("polarization", "ell2")}, "channel"),
        ({"response_frame": "ECLIPTIC"}, "frame"),
        ({"response_basis": "DIFFERENT_BASIS"}, "basis"),
        ({"response_units": "dimensionless"}, "units"),
    ),
)
def test_response_binding_refuses_exact_metadata_mismatch(update, message) -> None:
    """Catch cross-channel or cross-convention response binding."""

    api = importlib.import_module("common.response_bound_observable_state")
    with pytest.raises(api.ResponseBindingError, match=message):
        _bind(api, _observable_state(), **update)
