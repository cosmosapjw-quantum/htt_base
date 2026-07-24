"""COMMON-A tests — contracts (INDEPENDENT_TRACKS_PLAN §2.6)."""
from __future__ import annotations

import numpy as np
import pytest

from common.contracts import (
    ArtifactManifest,
    DirectionalSummary,
    DynestyResult,
    MockCalibrationReport,
    PreferredAxis,
    RuntimeReductionDecision,
    SkySelectionConfig,
    SkySupport,
    SolverCoreOutput,
    StatusSnapshotEntry,
    ObservableVector,
)


def _axis(**overrides) -> PreferredAxis:
    base = dict(
        l_deg=264.0,
        b_deg=48.0,
        label="test",
        source="fiducial_posterior",
        weight_mode="native",
        selection_mode="mock_calibrated",
        production_allowed=True,
        provenance_hash="deadbeef",
    )
    base.update(overrides)
    return PreferredAxis(**base)


class TestPreferredAxisContract:
    def test_roundtrips_fiducial_fields(self):
        ax = _axis()
        assert ax.production_allowed is True
        assert ax.provenance_hash == "deadbeef"

    def test_rejects_bad_source(self):
        with pytest.raises(ValueError, match="source"):
            _axis(source="bogus")

    def test_rejects_bad_weight_mode(self):
        with pytest.raises(ValueError, match="weight_mode"):
            _axis(weight_mode="bogus")

    def test_rejects_bad_selection_mode(self):
        with pytest.raises(ValueError, match="selection_mode"):
            _axis(selection_mode="bogus")

    def test_is_frozen(self):
        ax = _axis()
        with pytest.raises(Exception):
            ax.production_allowed = False  # type: ignore[misc]


def _manifest(**overrides) -> ArtifactManifest:
    base = dict(
        artifact_id="bass.run.lowell.v0",
        artifact_path="artifacts/bass/run.json",
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="cfg",
        input_hashes=["in1", "in2"],
        code_version="0.0-test",
        schema_version="ver2-v0",
    )
    base.update(overrides)
    return ArtifactManifest(**base)


class TestSkySelectionConfigInvariants:
    def test_fiducial_config_ok(self):
        cfg = SkySelectionConfig(
            zoa_half_angle_deg=20.0,
            production_mode=True,
            allow_uniform_fallback=False,
            require_mock_calibration=True,
        )
        assert cfg.production_mode is True

    def test_production_blocks_uniform_fallback(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            SkySelectionConfig(
                zoa_half_angle_deg=20.0,
                production_mode=True,
                allow_uniform_fallback=True,
            )

    def test_production_requires_mock_calibration(self):
        with pytest.raises(ValueError, match="mock calibration"):
            SkySelectionConfig(
                zoa_half_angle_deg=20.0,
                production_mode=True,
                require_mock_calibration=False,
            )

    def test_rejects_out_of_range_retention(self):
        with pytest.raises(ValueError, match="min_retention_fraction"):
            SkySelectionConfig(zoa_half_angle_deg=20.0, min_retention_fraction=1.5)

    def test_rejects_non_power_of_two_nside(self):
        with pytest.raises(ValueError, match="power of two"):
            SkySelectionConfig(zoa_half_angle_deg=20.0, nside=96)


class TestVer2BarrierContracts:
    def test_artifact_manifest_accepts_valid_owner_scope(self):
        manifest = _manifest()
        assert manifest.owner == "BASS"
        assert manifest.implementation_scope == "bass_py"

    def test_artifact_manifest_rejects_unknown_owner(self):
        with pytest.raises(ValueError, match="Unknown owner"):
            _manifest(owner="UNKNOWN")

    def test_runtime_reduction_decision_owner_is_bass_only(self):
        decision = RuntimeReductionDecision(
            owner="BASS",
            allow_reduction=False,
            source_status="adequate",
            propagation_status="pending",
            reason="sigma floor not met",
        )
        assert decision.owner == "BASS"

    def test_runtime_reduction_decision_rejects_non_bass_owner(self):
        with pytest.raises(ValueError, match="must be 'BASS'"):
            RuntimeReductionDecision(
                owner="TSC",
                allow_reduction=False,
                source_status="adequate",
                propagation_status="pending",
                reason="owner drift",
            )

    def test_status_snapshot_requires_source_commit(self):
        with pytest.raises(ValueError, match="source_commit"):
            StatusSnapshotEntry(
                artifact_id="status.bass",
                owner="BASS",
                implementation_scope="bass_py",
                claim_tier="conditional",
                implemented=True,
                smoke_tested=False,
                production_validated=False,
                manuscript_used=False,
                source_commit="",
            )

    def test_solver_core_output_requires_metadata_keys(self):
        with pytest.raises(ValueError, match="missing required keys"):
            SolverCoreOutput(
                alm_T=None,
                alm_E=None,
                alm_B=None,
                map_T=None,
                map_Q=None,
                map_U=None,
                deterministic_template=None,
                anisotropic_covariance=None,
                metadata={"bianchi_type": "I"},
                manifest=_manifest(),
            )

    def test_observable_vector_requires_channels(self):
        with pytest.raises(ValueError, match="channels must be non-empty"):
            ObservableVector(
                ell_max=8,
                channels=tuple(),
                cl={},
                alm_features={},
                biposh=None,
                template_fit=None,
                covariance_features=None,
                scan_volume={},
                sky_support=SkySupport(
                    selection_mode="mock_calibrated",
                    sky_support_hash="sky",
                    mask_hash="mask",
                    mock_coverage_status="ok",
                ),
                manifest=_manifest(),
            )

    @pytest.mark.parametrize("ell_max", [2.9, True])
    def test_observable_vector_requires_integral_ell_max(self, ell_max):
        with pytest.raises(ValueError, match="ell_max must be an integer"):
            ObservableVector(
                ell_max=ell_max,
                channels=("TT",),
                cl={},
                alm_features={},
                biposh=None,
                template_fit=None,
                covariance_features=None,
                scan_volume={},
                sky_support=SkySupport(
                    selection_mode="mock_calibrated",
                    sky_support_hash="sky",
                    mask_hash="mask",
                    mock_coverage_status="ok",
                ),
                manifest=_manifest(),
            )

    def test_observable_vector_normalizes_numpy_integer_ell_max(self):
        vector = ObservableVector(
            ell_max=np.int64(8),
            channels=("TT",),
            cl={},
            alm_features={},
            biposh=None,
            template_fit=None,
            covariance_features=None,
            scan_volume={},
            sky_support=SkySupport(
                selection_mode="mock_calibrated",
                sky_support_hash="sky",
                mask_hash="mask",
                mock_coverage_status="ok",
            ),
            manifest=_manifest(),
        )

        assert vector.ell_max == 8
        assert type(vector.ell_max) is int


class TestDirectionalSummary:
    def test_stores_four_channels(self):
        s = DirectionalSummary(
            raw={"tag": "raw"},
            zoa_masked={"tag": "zoa"},
            selection_aware={"tag": "sel"},
            mock_calibrated={"tag": "mock"},
        )
        assert s.raw["tag"] == "raw"
        assert s.mock_calibrated["tag"] == "mock"


class TestDynestyResult:
    def test_shape_mismatch_rejected(self):
        samples = np.zeros((10, 3))
        with pytest.raises(ValueError, match="logwt"):
            DynestyResult(
                samples=samples, logwt=np.zeros(5), logz=0.0, ncall=100, config={},
            )

    def test_requires_2d_samples(self):
        with pytest.raises(ValueError, match="2-D"):
            DynestyResult(
                samples=np.zeros(10), logwt=np.zeros(10),
                logz=0.0, ncall=10, config={},
            )


class TestMockCalibrationReport:
    def test_coverage_out_of_range_rejected(self):
        with pytest.raises(ValueError, match="coverage_68"):
            MockCalibrationReport(
                bias_amp=0.0, bias_direction_deg=0.0, coverage_68=1.5,
                credible_radius_deg=10.0, n_mock=100,
            )

    def test_negative_credible_radius_rejected(self):
        with pytest.raises(ValueError, match="credible_radius_deg"):
            MockCalibrationReport(
                bias_amp=0.0, bias_direction_deg=0.0, coverage_68=0.68,
                credible_radius_deg=-1.0, n_mock=100,
            )

    def test_zero_n_mock_rejected(self):
        with pytest.raises(ValueError, match="n_mock"):
            MockCalibrationReport(
                bias_amp=0.0, bias_direction_deg=0.0, coverage_68=0.68,
                credible_radius_deg=10.0, n_mock=0,
            )
