"""Audit P-07 regression: template-card IC promotion guard.

The audit identified that ``_IC_PROVENANCE_STATUS`` was decorative —
families flagged as ``template-card`` (II, III, IV, VI_0, VI_h, VIII)
shared the same FLRW seed factory and could be silently used in
statistics-grade flows. ``ic_provenance_gate_bundle`` now fails closed
on template-card families unless the caller passes
``allow_template_card=True``.

These tests pin the new guard semantics independent of the full
runtime: they construct a minimal stub backend and seed pack so the
gate bundle can be exercised in isolation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

import numpy as np
import pytest

from bass.runtime.gate_fragments import ic_provenance_gate_bundle


@dataclass
class _StubFamilySpec:
    family: str
    ic_provenance_status: str
    preferred_backend: str = "stub_backend"


@dataclass
class _StubTemplateCard:
    allowed_seed_provenance: tuple[str, ...]


@dataclass
class _StubBackend:
    family_spec: _StubFamilySpec
    truncation: Mapping[str, Any] = field(
        default_factory=lambda: {"ell_max": 4, "mode_basis_dim": 1}
    )
    _allowed: tuple[str, ...] = ("isotropic_anchor_continuation", "template_card_family_adapted")

    def template_card(self) -> _StubTemplateCard:
        return _StubTemplateCard(allowed_seed_provenance=self._allowed)


@dataclass
class _StubSeedPack:
    family: str
    branch: str
    seed_mode: str
    chart: str = "stub_chart"
    normalization: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    residual_summary: Mapping[str, Any] = field(
        default_factory=lambda: {"seed_regularity_status": "stub_regular"}
    )


@dataclass
class _StubSeedProjection:
    projection_ready: bool = True
    momentum_residual_before: np.ndarray = field(default_factory=lambda: np.zeros(3))
    momentum_residual_after: np.ndarray = field(default_factory=lambda: np.zeros(3))
    projection_mode: str = "stub_projection"


def _build(family: str, status: str, *, seed_mode: str = "isotropic_anchor_continuation"):
    backend = _StubBackend(
        family_spec=_StubFamilySpec(family=family, ic_provenance_status=status),
    )
    seed_pack = _StubSeedPack(family=family, branch="orthogonal", seed_mode=seed_mode)
    return backend, seed_pack, _StubSeedProjection()


def test_strong_family_passes_without_authorization() -> None:
    backend, seed_pack, projection = _build("I", "strong")
    bundle = ic_provenance_gate_bundle(
        bianchi_type="I",
        branch="orthogonal",
        backend=backend,
        seed_pack=seed_pack,
        seed_projection=projection,
    )
    assert bundle.passed is True
    assert bundle.forbidden_shortcut_checks["no_silent_template_card_ic_promotion"] is True
    assert bundle.metadata["template_card_family"] is False


def test_template_card_family_fails_closed_by_default() -> None:
    backend, seed_pack, projection = _build(
        "VIII", "template-card", seed_mode="template_card_family_adapted"
    )
    bundle = ic_provenance_gate_bundle(
        bianchi_type="VIII",
        branch="orthogonal",
        backend=backend,
        seed_pack=seed_pack,
        seed_projection=projection,
    )
    assert bundle.passed is False, (
        "template-card families must fail the IC provenance gate without explicit "
        "allow_template_card=True authorization"
    )
    assert bundle.forbidden_shortcut_checks["no_silent_template_card_ic_promotion"] is False
    assert bundle.metadata["template_card_family"] is True
    assert bundle.metadata["template_card_authorized"] is False


def test_template_card_family_passes_with_explicit_authorization() -> None:
    backend, seed_pack, projection = _build(
        "VI_0", "template-card", seed_mode="template_card_family_adapted"
    )
    bundle = ic_provenance_gate_bundle(
        bianchi_type="VI_0",
        branch="orthogonal",
        backend=backend,
        seed_pack=seed_pack,
        seed_projection=projection,
        allow_template_card=True,
    )
    assert bundle.passed is True
    assert bundle.forbidden_shortcut_checks["no_silent_template_card_ic_promotion"] is True
    assert bundle.metadata["template_card_authorized"] is True


@pytest.mark.parametrize("family", ["II", "III", "IV", "VI_0", "VI_h", "VIII"])
def test_all_template_card_families_fail_closed(family: str) -> None:
    backend, seed_pack, projection = _build(
        family, "template-card", seed_mode="template_card_family_adapted"
    )
    bundle = ic_provenance_gate_bundle(
        bianchi_type=family,
        branch="orthogonal",
        backend=backend,
        seed_pack=seed_pack,
        seed_projection=projection,
    )
    assert bundle.passed is False
    assert bundle.metadata["ic_provenance_status"] == "template-card"


@pytest.mark.parametrize("family", ["FLRW", "I", "V", "VII_0", "VII_h", "IX"])
def test_all_strong_families_pass_without_authorization(family: str) -> None:
    backend, seed_pack, projection = _build(family, "strong")
    bundle = ic_provenance_gate_bundle(
        bianchi_type=family,
        branch="orthogonal",
        backend=backend,
        seed_pack=seed_pack,
        seed_projection=projection,
    )
    assert bundle.passed is True
    assert bundle.metadata["ic_provenance_status"] == "strong"
