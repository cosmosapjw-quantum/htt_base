from __future__ import annotations

import ast
import importlib

import numpy as np
import pytest

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    SkySupport,
)


def _manifest() -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="obsstat.test.template_fit",
        artifact_path="memory://obsstat/template-fit",
        owner=Owner.OBSSTAT,
        implementation_scope=ImplementationScope.OBSSTAT,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.template_fit.v1",
        caveats=["diagnostic feature extraction only"],
    )


def _sky_support() -> SkySupport:
    return SkySupport(
        selection_mode="none",
        sky_support_hash="sha256:sky",
        mask_hash="sha256:mask",
        mock_coverage_status="not_statistical",
        coordinate_frame="galactic",
        sky_fraction=1.0,
        completeness_status="full_sky_synthetic",
        pixelization="none",
    )


def _orientation_scan():
    from htt.obsstat.template_fit import OrientationScanMetadata

    return OrientationScanMetadata(
        scan_id="scan://template-fit/test-grid",
        orientation_parameterization="so3_euler_zyz",
        orientation_count=12,
        scan_volume={
            "orientation_parameterization": "so3_euler_zyz",
            "orientation_count": 12,
            "grid_rule": "synthetic_regular_grid",
            "global_local_status": "tracked_not_corrected",
        },
        coordinate_frame="galactic",
        sky_support_status="full_sky_synthetic",
        mask_status="unmasked_synthetic",
        config_hash="sha256:scan-config",
        input_hashes=("sha256:scan-input",),
        best_orientation={"alpha_deg": 0.0, "beta_deg": 45.0, "gamma_deg": 0.0},
    )


def test_template_fit_emits_amplitude_delta_chi2_and_branch_metadata() -> None:
    from htt.obsstat.observable_vector import build_observable_vector
    from htt.obsstat.template_fit import (
        CovarianceAssumption,
        fit_template_diagnostic,
    )

    result = fit_template_diagnostic(
        observed=[1.0, 3.0, 5.0],
        template=[1.0, 1.0, 1.0],
        orientation_scan=_orientation_scan(),
        covariance_assumption=CovarianceAssumption.identity(),
        template_label="monopole-free-test-template",
        config_hash="sha256:fit-config",
        input_hashes=("sha256:fit-input",),
        generating_command="python -m pytest tests/obsstat/test_template_fit.py -q",
        worktree_state="test-clean",
    )
    payload = result.to_feature_payload()

    assert payload["owner"] == "OBSSTAT"
    assert payload["implementation_scope"] == "obsstat"
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["statistic_role"] == "feature_only"
    assert payload["model_role"] == "not_model_input"
    assert payload["transfer_source"] == "none"
    assert payload["config_hash"] == "sha256:fit-config"
    assert payload["input_hashes"] == ["sha256:fit-input"]
    assert payload["generating_command"].startswith("python -m pytest")
    assert payload["worktree_state"] == "test-clean"

    mean_branch = payload["template_mean_branch"]
    assert mean_branch["branch_role"] == "deterministic_template_mean_fit"
    assert mean_branch["amplitude"] == pytest.approx(3.0)
    assert mean_branch["delta_chi2"] == pytest.approx(27.0)
    assert mean_branch["DeltaChi2"] == pytest.approx(27.0)
    assert mean_branch["chi2_without_template"] == pytest.approx(35.0)
    assert mean_branch["chi2_with_template"] == pytest.approx(8.0)
    assert mean_branch["orientation_scan"]["orientation_count"] == 12
    assert mean_branch["orientation_scan"]["scan_volume"]["grid_rule"] == (
        "synthetic_regular_grid"
    )

    covariance_branch = payload["covariance_branch"]
    assert covariance_branch["branch_role"] == "template_weighting_assumption_only"
    assert covariance_branch["covariance_assumption"]["kind"] == "identity"
    assert covariance_branch["covariance_anomaly_status"] == "not_evaluated"
    assert covariance_branch["collapsed_with_template_mean"] is False
    assert payload["branch_separation"]["merged_statistic_allowed"] is False

    vector = build_observable_vector(
        ell_max=4,
        channels=("TT",),
        template_features={"template_fit": payload},
        manifest=_manifest(),
        sky_support=_sky_support(),
    )
    assert vector.template_fit["template_fit"]["template_mean_branch"][
        "DeltaChi2"
    ] == pytest.approx(27.0)


def test_diagonal_and_full_covariance_are_weighting_assumptions_only() -> None:
    from htt.obsstat.template_fit import (
        CovarianceAssumption,
        fit_template_diagnostic,
    )

    kwargs = {
        "observed": [1.0, 3.0],
        "template": [1.0, 2.0],
        "orientation_scan": _orientation_scan(),
        "template_label": "weighted-template",
        "config_hash": "sha256:fit-config",
        "input_hashes": ("sha256:fit-input",),
        "generating_command": "python -m pytest tests/obsstat/test_template_fit.py -q",
        "git_commit": "abc123",
    }
    diagonal = fit_template_diagnostic(
        **kwargs,
        covariance_assumption=CovarianceAssumption.diagonal_inverse_variance(
            [4.0, 1.0],
            covariance_status="diagonal_inverse_variance_supplied",
        ),
    ).to_feature_payload()
    full = fit_template_diagnostic(
        **kwargs,
        covariance_assumption=CovarianceAssumption.full_covariance(
            [[0.25, 0.0], [0.0, 1.0]],
            covariance_status="full_positive_definite_covariance_supplied",
        ),
    ).to_feature_payload()

    for payload in (diagonal, full):
        assert payload["template_mean_branch"]["amplitude"] == pytest.approx(1.25)
        assert payload["template_mean_branch"]["DeltaChi2"] == pytest.approx(12.5)
        assert payload["covariance_branch"]["branch_role"] == (
            "template_weighting_assumption_only"
        )
        assert payload["covariance_branch"]["covariance_anomaly_status"] == (
            "not_evaluated"
        )
        assert "covariance_anomaly_statistic" not in payload["covariance_branch"]
    assert diagonal["covariance_branch"]["covariance_assumption"]["kind"] == (
        "diagonal_inverse_variance"
    )
    assert full["covariance_branch"]["covariance_assumption"]["kind"] == (
        "full_covariance"
    )


def test_off_diagonal_full_covariance_uses_solve_weighting() -> None:
    from htt.obsstat.template_fit import (
        CovarianceAssumption,
        fit_template_diagnostic,
    )

    covariance = np.array([[1.0, 0.25], [0.25, 1.0]], dtype=float)
    observed = np.array([1.0, 3.0], dtype=float)
    template = np.array([1.0, 2.0], dtype=float)
    weighted_observed = np.linalg.solve(covariance, observed)
    weighted_template = np.linalg.solve(covariance, template)
    expected_amplitude = float(np.dot(template, weighted_observed) / np.dot(template, weighted_template))
    expected_delta = float(np.dot(template, weighted_observed) ** 2 / np.dot(template, weighted_template))

    payload = fit_template_diagnostic(
        observed=observed,
        template=template,
        orientation_scan=_orientation_scan(),
        covariance_assumption=CovarianceAssumption.full_covariance(
            covariance,
            covariance_status="full_positive_definite_covariance_supplied",
        ),
        config_hash="sha256:fit-config",
        input_hashes=("sha256:fit-input",),
        generating_command="python -m pytest tests/obsstat/test_template_fit.py -q",
        worktree_state="test-clean",
    ).to_feature_payload()

    assert payload["template_mean_branch"]["amplitude"] == pytest.approx(
        expected_amplitude
    )
    assert payload["template_mean_branch"]["DeltaChi2"] == pytest.approx(
        expected_delta
    )
    assert payload["covariance_branch"]["covariance_assumption"][
        "positive_definite_status"
    ] == "checked_by_cholesky"


def test_template_fit_rejects_invalid_vectors_and_covariance_inputs() -> None:
    from htt.obsstat.template_fit import (
        CovarianceAssumption,
        fit_template_diagnostic,
    )

    base = {
        "observed": [1.0, 2.0],
        "template": [1.0, 1.0],
        "orientation_scan": _orientation_scan(),
        "covariance_assumption": CovarianceAssumption.identity(),
        "config_hash": "sha256:fit-config",
        "input_hashes": ("sha256:fit-input",),
        "generating_command": "python -m pytest tests/obsstat/test_template_fit.py -q",
        "worktree_state": "test-clean",
    }
    with pytest.raises(ValueError, match="same finite one-dimensional shape"):
        fit_template_diagnostic(**{**base, "template": [1.0]})
    with pytest.raises(ValueError, match="template vector must have positive"):
        fit_template_diagnostic(**{**base, "template": [0.0, 0.0]})
    with pytest.raises(ValueError, match="observed vector entries must be finite"):
        fit_template_diagnostic(**{**base, "observed": [1.0, float("nan")]})
    with pytest.raises(ValueError, match="positive finite"):
        CovarianceAssumption.diagonal_inverse_variance([1.0, 0.0])
    with pytest.raises(ValueError, match="positive definite"):
        CovarianceAssumption.full_covariance([[1.0, 2.0], [2.0, 1.0]])


def test_orientation_scan_metadata_is_required_and_overclaim_guarded() -> None:
    from htt.obsstat.template_fit import OrientationScanMetadata

    with pytest.raises(ValueError, match="orientation_count must be positive"):
        OrientationScanMetadata(
            scan_id="scan://bad",
            orientation_parameterization="so3_euler_zyz",
            orientation_count=0,
            scan_volume={
                "orientation_parameterization": "so3_euler_zyz",
                "orientation_count": 0,
                "global_local_status": "tracked_not_corrected",
            },
            coordinate_frame="galactic",
            sky_support_status="full_sky_synthetic",
            mask_status="unmasked_synthetic",
            config_hash="sha256:scan-config",
            input_hashes=("sha256:scan-input",),
        )
    with pytest.raises(ValueError, match="scan_volume missing"):
        OrientationScanMetadata(
            scan_id="scan://bad",
            orientation_parameterization="so3_euler_zyz",
            orientation_count=12,
            scan_volume={"orientation_count": 12},
            coordinate_frame="galactic",
            sky_support_status="full_sky_synthetic",
            mask_status="unmasked_synthetic",
            config_hash="sha256:scan-config",
            input_hashes=("sha256:scan-input",),
        )
    with pytest.raises(ValueError, match="forbidden claim language"):
        OrientationScanMetadata(
            scan_id="scan://bad",
            orientation_parameterization="so3_euler_zyz",
            orientation_count=12,
            scan_volume={
                "orientation_parameterization": "so3_euler_zyz",
                "orientation_count": 12,
                "global_local_status": "tracked_not_corrected",
            },
            coordinate_frame="galactic",
            sky_support_status="full_sky_synthetic",
            mask_status="unmasked_synthetic",
            config_hash="sha256:scan-config",
            input_hashes=("sha256:scan-input",),
            caveats=("posterior-like wording is forbidden here",),
        )


def test_covariance_anomaly_collapse_is_rejected() -> None:
    from htt.obsstat.template_fit import (
        CovarianceAssumption,
        fit_template_diagnostic,
    )

    with pytest.raises(ValueError, match="covariance anomaly"):
        CovarianceAssumption(kind="covariance_anomaly", covariance_status="merged")
    with pytest.raises(ValueError, match="separate OBSSTAT covariance branch"):
        fit_template_diagnostic(
            observed=[1.0, 3.0, 5.0],
            template=[1.0, 1.0, 1.0],
            orientation_scan=_orientation_scan(),
            covariance_assumption=CovarianceAssumption.identity(),
            covariance_anomaly_statistic=0.1,
            config_hash="sha256:fit-config",
            input_hashes=("sha256:fit-input",),
            generating_command="python -m pytest tests/obsstat/test_template_fit.py -q",
            worktree_state="test-clean",
        )


def test_public_diagnostic_constructor_rejects_inconsistent_chi2_fields() -> None:
    from htt.obsstat.template_fit import (
        CovarianceAssumption,
        TemplateFitDiagnostic,
    )

    base = {
        "amplitude": 1.0,
        "delta_chi2": 0.5,
        "chi2_without_template": 1.0,
        "chi2_with_template": 0.5,
        "template_norm_weighted": 1.0,
        "observed_norm_weighted": 1.0,
        "residual_norm_weighted": 0.5,
        "vector_length": 2,
        "orientation_scan": _orientation_scan(),
        "covariance_assumption": CovarianceAssumption.identity(),
        "config_hash": "sha256:fit-config",
        "input_hashes": ("sha256:fit-input",),
        "generating_command": "python -m pytest tests/obsstat/test_template_fit.py -q",
        "worktree_state": "test-clean",
    }

    with pytest.raises(ValueError, match="delta_chi2 must equal"):
        TemplateFitDiagnostic(**{**base, "delta_chi2": 2.0})
    with pytest.raises(ValueError, match="chi-square values must be non-negative"):
        TemplateFitDiagnostic(**{**base, "chi2_with_template": -0.1})
    with pytest.raises(ValueError, match="observed_norm_weighted must equal"):
        TemplateFitDiagnostic(**{**base, "observed_norm_weighted": 1.5})
    with pytest.raises(ValueError, match="residual_norm_weighted must equal"):
        TemplateFitDiagnostic(**{**base, "residual_norm_weighted": 0.25})


def test_template_fit_exports_and_import_boundaries() -> None:
    from htt.obsstat import (
        CovarianceAssumption,
        OrientationScanMetadata,
        TemplateFitDiagnostic,
        fit_template_diagnostic,
    )
    from htt.obsstat.template_fit import TemplateFitDiagnostic as ModuleDiagnostic

    assert TemplateFitDiagnostic is ModuleDiagnostic
    assert OrientationScanMetadata is not None
    assert CovarianceAssumption is not None
    assert fit_template_diagnostic is not None

    from obsstat import TemplateFitDiagnostic as TopLevelDiagnostic

    assert TopLevelDiagnostic is ModuleDiagnostic

    module = importlib.import_module("htt.obsstat.template_fit")
    assert module.TemplateFitDiagnostic is ModuleDiagnostic

    source_path = "htt/obsstat/template_fit.py"
    tree = ast.parse(open(source_path, encoding="utf-8").read())
    forbidden_roots = (
        "htt.htt",
        "htt.infer",
        "htt.likelihood",
        "mio",
        "htt.mio",
        "workspace.contracts.mio_certificate",
    )
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    assert not [
        module_name
        for module_name in imported
        if module_name.startswith(forbidden_roots) or "likelihood" in module_name
    ]
