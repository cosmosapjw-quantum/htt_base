"""PR-125 contract tests: canonical frame/order/domain premise contract."""
from __future__ import annotations

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.frame_contract import (
    BackgroundClass,
    Frame,
    FrameBoost,
    FrameContractError,
    HarmonicConvention,
    KinematicState,
    PerturbativeOrder,
    PremiseContract,
    RedshiftDepthConvention,
    UnitsConvention,
    compose_beta,
    flrw_limit,
    legacy_reproduction_contract,
    local_boost_limit,
    no_tilt_limit,
    require_flrw_limit,
    transform_tilt,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _contract(**overrides) -> PremiseContract:
    payload = dict(
        frame=Frame.CMB, perturbative_order=PerturbativeOrder.LINEAR,
        background_class=BackgroundClass.FLRW_FLAT,
        units=UnitsConvention.DIMENSIONLESS_HUBBLE_NORMALIZED,
        harmonic_convention=HarmonicConvention.COMPLEX_SPHERICAL_CAMB,
        redshift_depth_convention=RedshiftDepthConvention.CZ_KM_S,
    )
    payload.update(overrides)
    return PremiseContract(**payload)


def test_unknown_values_fail_closed() -> None:
    for field, value in (
        ("frame", "GALACTOCENTRIC"),
        ("perturbative_order", "THIRD"),
        ("background_class", "BIANCHI_X"),
        ("units", "FURLONGS"),
        ("harmonic_convention", "TESSERAL"),
        ("redshift_depth_convention", "PARSECS"),
    ):
        with pytest.raises(FrameContractError, match="unknown"):
            _contract(**{field: value})


def test_missing_fields_fail_closed_no_defaults() -> None:
    with pytest.raises(FrameContractError, match="missing"):
        PremiseContract.from_payload({"frame": "CMB"})
    with pytest.raises(FrameContractError, match="unknown premise"):
        PremiseContract.from_payload({
            **_contract().as_payload(), "surprise_field": 1,
        })


def test_legacy_reproduction_channel_is_labeled() -> None:
    legacy = legacy_reproduction_contract()
    assert legacy.reproduction_mode is True
    assert _contract().reproduction_mode is False


def test_exact_rapidity_witnesses() -> None:
    b1, b2, b3 = Fraction(1, 3), Fraction(1, 5), Fraction(-2, 9)
    assert compose_beta(compose_beta(b1, b2), b3) == compose_beta(
        b1, compose_beta(b2, b3))
    b12 = compose_beta(b1, b2)
    assert compose_beta(b12, -b12) == 0
    boost = FrameBoost(source=Frame.MATTER, target=Frame.CMB,
                       beta=Fraction(7, 500))
    assert boost.inverse().beta == -boost.beta
    assert boost.then(boost.inverse()).beta == 0
    FrameBoost.validate_pair(boost, boost.inverse())
    with pytest.raises(FrameContractError, match="antisymmetry"):
        FrameBoost.validate_pair(
            boost, FrameBoost(source=Frame.CMB, target=Frame.MATTER,
                              beta=boost.beta))


def test_scalar_alias_firewall() -> None:
    boost = FrameBoost(source=Frame.MATTER, target=Frame.CMB,
                       beta=Fraction(1, 100))
    moved = transform_tilt(Fraction(1, 50), boost, Frame.MATTER, Frame.CMB)
    # REGISTERED subtraction semantics: reading in the target frame
    assert moved == compose_beta(Fraction(1, 50), Fraction(-1, 100))
    # rest in the declared frame reads as -beta in the target frame
    assert transform_tilt(Fraction(0), boost, Frame.MATTER,
                          Frame.CMB) == -boost.beta
    with pytest.raises(FrameContractError, match="scalar alias"):
        transform_tilt(Fraction(1, 50), boost, Frame.NORMAL, Frame.CMB)
    with pytest.raises(FrameContractError, match="same-frame read"):
        transform_tilt(Fraction(1, 50), boost, Frame.MATTER, Frame.MATTER)
    assert transform_tilt(Fraction(1, 50), None, Frame.CMB,
                          Frame.CMB) == Fraction(1, 50)
    with pytest.raises(FrameContractError, match="without a frame transform"):
        transform_tilt(Fraction(1, 50), None, Frame.MATTER, Frame.CMB)


def test_beta_zero_never_implies_flrw() -> None:
    sheared = KinematicState(beta=0, sigma2=Fraction(1, 10**8), w2=0,
                             delta_omega_k=0)
    assert no_tilt_limit(sheared) is True
    assert flrw_limit(sheared) is False
    with pytest.raises(FrameContractError, match="does not imply"):
        require_flrw_limit(sheared)
    assert flrw_limit(KinematicState(beta=0, sigma2=0, w2=0,
                                     delta_omega_k=0)) is True


def test_local_boost_preserves_quadratic_sector() -> None:
    state = KinematicState(beta=Fraction(1, 1000),
                           sigma2=Fraction(3, 10**9),
                           w2=Fraction(1, 10**13),
                           delta_omega_k=Fraction(-1, 10**6))
    boost = FrameBoost(source=Frame.MATTER, target=Frame.LOCAL_OBSERVER,
                       beta=Fraction(9, 8000))
    moved = local_boost_limit(state, boost)
    assert moved.sigma2 == state.sigma2
    assert moved.w2 == state.w2
    assert moved.delta_omega_k == state.delta_omega_k
    assert moved.beta == compose_beta(state.beta, -boost.beta)


def test_generated_graph_binds_every_checked_signature() -> None:
    graph = json.loads(
        (REPO_ROOT / "docs/generated/pr125_theorem_frame_graph.json")
        .read_text(encoding="utf-8"))
    from common.theorem_signatures import load_signature_registry

    registry = load_signature_registry(REPO_ROOT)
    checked = {e.entry_id for e in registry.entries
               if e.signature_status.value == "CHECKED"}
    assert set(graph["bindings"]) == checked
    registry_artifact = json.loads(
        (REPO_ROOT / "docs/generated/pr125_frame_contract_registry.json")
        .read_text(encoding="utf-8"))
    contract_ids = {row["contract_id"]
                    for row in registry_artifact["contracts"].values()}
    for row in graph["bindings"].values():
        assert row["contract_id"] in contract_ids


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr125_frame_contract.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_mutation_report_zero_survivors() -> None:
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr125_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    assert all(m["executed"] and m["killed"] for m in report["mutations"])
