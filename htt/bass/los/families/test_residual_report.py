"""S6 integration tests: full Tier-A residual report + gate bundle.

End-to-end flow:

1. ``build_family_residual_packs`` produces one ``ResidualPack`` per
   family (all 11) on a canonical observer surface.
2. ``family_backend_gate_bundle_from_packs`` aggregates them into a
   single ``GateBundle`` keyed ``family_backend_gate``.
3. The bundle passes when every family pack passes.
4. ``write_family_residual_archive`` serializes the report to JSON.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bass.forward.ver3_output_archive import write_family_residual_archive
from bass.los.families import KNOWN_FAMILIES
from bass.los.families.residual_report import (
    FAMILY_STRUCTURE_FACTORIES,
    build_family_residual_packs,
    default_family_residual_report,
    merge_family_residual_packs,
)
from bass.statistics import ResidualPack
from bass.validation.ver3_gate_stop import (
    GateBundle,
    family_backend_gate_bundle_from_packs,
)


def test_factories_cover_all_known_families():
    assert set(FAMILY_STRUCTURE_FACTORIES) == set(KNOWN_FAMILIES)


def test_default_family_residual_report_produces_one_pack_per_family():
    report = default_family_residual_report()
    assert set(report) == set(KNOWN_FAMILIES)
    for family, pack in report.items():
        assert isinstance(pack, ResidualPack)
        assert pack.family == family


def test_every_family_pack_passes_on_canonical_surface():
    report = default_family_residual_report()
    for family, pack in report.items():
        assert pack.passed is True, (
            f"Family {family} failed: residuals={dict(pack.residual_values)}, "
            f"violated={pack.violated_tolerances}, missing={pack.missing_residuals}"
        )


def test_merge_preserves_namespacing():
    report = default_family_residual_report()
    merged = merge_family_residual_packs(report)
    assert merged.passed is True
    # Every residual key must be family-prefixed.
    for key in merged.residual_values:
        assert ":" in key, f"merged residual '{key}' is not namespaced"


def test_subset_of_families_supported():
    subset = build_family_residual_packs(
        eta_grid_mpc=np.linspace(40.0, 420.0, 65),
        k_grid_mpc=np.array([0.05, 0.08, 0.12]),
        ell_max=6,
        visibility_fn=lambda eta: float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2)),
        source_builder=lambda eta, k: {
            "temperature": float(np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2)),
            "temperature_anisotropy": 0.2,
            "polarization": 0.35,
            "b_mode": 0.0,
        },
        families=("I", "IX"),
    )
    assert set(subset) == {"I", "IX"}


def test_unknown_family_rejected():
    with pytest.raises(KeyError, match="Unknown Bianchi family"):
        build_family_residual_packs(
            eta_grid_mpc=np.linspace(40.0, 420.0, 16),
            k_grid_mpc=np.array([0.05]),
            ell_max=4,
            visibility_fn=lambda eta: 1.0,
            source_builder=lambda eta, k: {"temperature": 0.0},
            families=("NOSUCH",),
        )


# ----- Gate-bundle integration ------------------------------------------


def test_family_backend_gate_bundle_passes_when_all_packs_pass():
    report = default_family_residual_report()
    bundle = family_backend_gate_bundle_from_packs(report)
    assert isinstance(bundle, GateBundle)
    assert bundle.gate_name == "family_backend_gate"
    assert bundle.passed is True
    assert bundle.metadata["family_count"] == len(KNOWN_FAMILIES)
    assert bundle.metadata["missing_families"] == []
    for family, passed in bundle.metadata["per_family_passed"].items():
        assert passed is True, f"per-family flag false for {family}"


def test_family_backend_gate_bundle_fails_on_missing_family():
    report = default_family_residual_report()
    # Drop one family to simulate missing evidence.
    subset = dict(report)
    subset.pop("VIII")
    bundle = family_backend_gate_bundle_from_packs(subset)
    assert bundle.passed is False
    assert "VIII" in bundle.metadata["missing_families"]


def test_family_backend_gate_bundle_fails_on_pack_failure():
    # Construct a fake pack with passed=False and merge it in.
    report = default_family_residual_report()
    subset = dict(report)
    # Replace Type I with a failing payload dict (not a ResidualPack).
    subset["I"] = {
        "family": "I",
        "branch": "base",
        "backend": "forced-failure",
        "residual_values": {"cartesian_anchor_limit": 1.0e3},
        "tolerance": {"cartesian_anchor_limit": 1.0e-6},
        "required_residuals": ["cartesian_anchor_limit"],
        "forbidden_shortcuts": [],
        "forbidden_shortcut_violations": [],
        "metadata": {},
        "passed": False,
        "verification_crosscheck_pass": True,
    }
    bundle = family_backend_gate_bundle_from_packs(subset)
    assert bundle.passed is False


def test_aggregated_residuals_are_family_prefixed():
    report = default_family_residual_report()
    bundle = family_backend_gate_bundle_from_packs(report)
    for key in bundle.residual_summary:
        assert ":" in key


# ----- Output archive sidecar -------------------------------------------


def test_write_family_residual_archive_produces_valid_json(tmp_path: Path):
    report = default_family_residual_report()
    path = write_family_residual_archive(report, tmp_path)
    assert Path(path).is_file()
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    assert payload["summary"]["family_count"] == len(KNOWN_FAMILIES)
    assert payload["summary"]["all_passed"] is True
    assert set(payload["packs"]) == set(KNOWN_FAMILIES)


def test_write_family_residual_archive_accepts_dict_payloads(tmp_path: Path):
    """Serializer also accepts pre-serialized dict payloads for flexibility."""
    payload = {
        "I": {
            "family": "I",
            "branch": "base",
            "backend": "dict-test",
            "residual_values": {"cartesian_anchor_limit": 0.0},
            "tolerance": {"cartesian_anchor_limit": 1.0},
            "required_residuals": ["cartesian_anchor_limit"],
            "forbidden_shortcuts": [],
            "forbidden_shortcut_violations": [],
            "metadata": {},
            "passed": True,
            "verification_crosscheck_pass": True,
        }
    }
    path = write_family_residual_archive(payload, tmp_path, filename="custom.json")
    assert Path(path).name == "custom.json"
    roundtrip = json.loads(Path(path).read_text(encoding="utf-8"))
    assert roundtrip["packs"]["I"]["passed"] is True
