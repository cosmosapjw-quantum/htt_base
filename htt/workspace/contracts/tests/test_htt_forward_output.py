"""CONTRACTS-01 — HttForwardOutput schema tests (INDEPENDENT_TRACKS_PLAN v1.2 §11.1)."""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from common.contracts import ArtifactManifest
from workspace.contracts.htt_forward_output import HttForwardOutput


def _forward(**overrides):
    ell = np.arange(2, 11)
    base = dict(
        model_name="BianchiI_tilt",
        bianchi_type="I",
        axis_galactic_lb_deg=(264.021, 48.253),
        ell=ell,
        C_ell_TT=np.ones_like(ell, dtype=float) * 1e-11,
        C_ell_TE=np.zeros_like(ell, dtype=float),
        C_ell_EE=np.ones_like(ell, dtype=float) * 1e-13,
        directional_summary={"l_deg": 264.02, "b_deg": 48.25, "R": 0.91},
        shear_Sigma2=1.2e-8,
        tilt_beta=1.334e-3,
        atlas_entry_hashes=("atlas_a", "atlas_b"),
        generated_by="bass.spectrum.cl_assembly v0.8",
        git_commit="abc123",
        config_hash="cfg1",
    )
    base.update(overrides)
    return HttForwardOutput(**base)


def test_htt_forward_output_frozen():
    out = _forward()
    with pytest.raises(dataclasses.FrozenInstanceError):
        out.model_name = "BianchiV"  # type: ignore[misc]


def test_htt_forward_output_rejects_shape_mismatch():
    ell = np.arange(2, 11)
    with pytest.raises(ValueError, match="C_ell_TT shape"):
        _forward(C_ell_TT=np.ones(3))


def test_htt_forward_output_rejects_negative_shear():
    with pytest.raises(ValueError, match="shear_Sigma2 must be non-negative"):
        _forward(shear_Sigma2=-1.0)


def test_htt_forward_output_rejects_out_of_range_b():
    with pytest.raises(ValueError, match="axis_galactic_lb_deg"):
        _forward(axis_galactic_lb_deg=(180.0, 120.0))


def test_htt_forward_output_has_no_posterior_field():
    for f in dataclasses.fields(HttForwardOutput):
        assert "posterior" not in f.name.lower(), (
            f"HttForwardOutput must not expose a 'posterior' field "
            f"(found '{f.name}') — it is a model-dependent theory bundle, "
            f"not an inference product."
        )


def test_htt_forward_output_manifest_owner_must_be_bass():
    ell = np.arange(2, 11)
    manifest = ArtifactManifest(
        artifact_id="htt.forward.bad-owner",
        artifact_path="artifacts/htt/forward.json",
        owner="HTT",
        implementation_scope="htt",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["x"],
        code_version="0.0-test",
        schema_version="ver2-v0",
    )
    with pytest.raises(ValueError, match="must be 'BASS'"):
        HttForwardOutput(
            model_name="BianchiI_tilt",
            bianchi_type="I",
            axis_galactic_lb_deg=(264.021, 48.253),
            ell=ell,
            C_ell_TT=np.ones_like(ell, dtype=float) * 1e-11,
            C_ell_TE=np.zeros_like(ell, dtype=float),
            C_ell_EE=np.ones_like(ell, dtype=float) * 1e-13,
            directional_summary={"l_deg": 264.02, "b_deg": 48.25, "R": 0.91},
            shear_Sigma2=1.2e-8,
            tilt_beta=1.334e-3,
            generated_by="bass.spectrum.cl_assembly v0.8",
            git_commit="abc123",
            config_hash="cfg1",
            manifest=manifest,
        )
