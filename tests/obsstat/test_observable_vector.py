from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    ObservableVector as CanonicalObservableVector,
    Owner,
    SkySupport,
)


def _manifest(owner: Owner = Owner.OBSSTAT) -> ArtifactManifest:
    scope = (
        ImplementationScope.OBSSTAT
        if owner is Owner.OBSSTAT
        else ImplementationScope.HTT
    )
    return ArtifactManifest(
        artifact_id="obsstat.test.observable_vector",
        artifact_path="memory://obsstat/test",
        owner=owner,
        implementation_scope=scope,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by="tests.obsstat",
        git_commit="test",
        config_hash="sha256:test-config",
        input_hashes=["sha256:test-input"],
        code_version="test",
        schema_version="obsstat.observable_vector.v1",
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


def _external_transfer_metadata() -> dict[str, object]:
    return {
        "transfer_source": "external_transfer",
        "family": "external-template",
        "valid_range": {"k_min": 1.0e-4, "k_max": 0.2, "ell_min": 2, "ell_max": 4},
        "observable_kind": "template",
        "normalization": "unit_norm",
        "calibration_status": "external_calibrated",
        "caveats": ["external transfer metadata for obsstat packaging test"],
    }


def test_obsstat_reexports_canonical_observable_vector_contract() -> None:
    from htt.obsstat import ObservableVector
    from htt.obsstat.observable_vector import ObservableVector as ModuleVector

    assert ObservableVector is CanonicalObservableVector
    assert ModuleVector is CanonicalObservableVector


def test_obsstat_manifest_helper_is_diagnostic_only_and_copies_inputs() -> None:
    from htt.obsstat import obsstat_manifest

    input_hashes = ["sha256:input"]
    caveats = ["diagnostic feature extraction only"]
    stats = {"alm": {"convention": "complex_alm"}}

    manifest = obsstat_manifest(
        artifact_id="obsstat.test.manifest",
        artifact_path="memory://obsstat/manifest",
        config_hash="sha256:config",
        input_hashes=input_hashes,
        caveats=caveats,
        statistics_definitions=stats,
    )
    input_hashes.append("sha256:mutated")
    caveats.append("mutated")

    assert manifest.owner is Owner.OBSSTAT
    assert manifest.implementation_scope is ImplementationScope.OBSSTAT
    assert manifest.claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    assert manifest.input_hashes == ["sha256:input"]
    assert manifest.caveats == ["diagnostic feature extraction only"]
    assert manifest.statistics_definitions == stats


def test_build_observable_vector_holds_required_feature_blocks() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    vector = build_observable_vector(
        ell_max=4,
        channels=("TT", "TE", "EE", "BiPoSH"),
        cl={"TT": [1.0, 0.5]},
        alm_features={"T": {"lmax": 4, "convention": "complex_alm"}},
        template_features={"global_tilt_template": {"norm": 0.2}},
        covariance_features={"diag_cl": {"rank": 5}},
        scalar_features={"x": 0.1, "Q": 0.2},
        morphology_features={"axis_coherence": 0.3},
        null_features={
            "p_value": 0.8,
            "null_ensemble_ref": "mock://nulls",
            "look_elsewhere_status": "tracked",
        },
        biposh_features={"A_20": 0.01},
        scan_volume={"ell_range": [2, 4]},
        sky_support=_sky_support(),
        manifest=_manifest(),
    )

    assert isinstance(vector, CanonicalObservableVector)
    assert vector.manifest.owner is Owner.OBSSTAT
    assert vector.manifest.implementation_scope is ImplementationScope.OBSSTAT
    assert vector.manifest.claim_tier is ClaimTier.DIAGNOSTIC_ONLY
    assert vector.alm_features["alm"]["T"]["convention"] == "complex_alm"
    assert vector.alm_features["scalar_features"]["x"] == 0.1
    assert vector.alm_features["morphology_features"]["axis_coherence"] == 0.3
    assert vector.alm_features["null_features"]["null_ensemble_ref"] == "mock://nulls"
    assert vector.template_fit["global_tilt_template"]["norm"] == 0.2
    assert vector.covariance_features["diag_cl"]["rank"] == 5
    assert vector.biposh["A_20"] == 0.01


def test_null_pvalues_require_null_and_look_elsewhere_provenance() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="null_ensemble_ref"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            null_features={"p_value": 0.2},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="null_ensemble_ref"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            scalar_features={"nested": {"pvalue_tail": 0.03}},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="null_ensemble_ref"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            scalar_features={"pvalue_tail": 0.03},
            null_features={
                "null_ensemble_ref": "",
                "look_elsewhere_status": "tracked",
            },
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="look_elsewhere_status"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            scalar_features={"pvalue_tail": 0.03},
            null_features={
                "null_ensemble_ref": "mock://obsstat-nulls",
                "look_elsewhere_status": "not_tracked",
            },
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    vector = build_observable_vector(
        ell_max=2,
        channels=("TT",),
        scalar_features={"nested": {"pvalue_tail": 0.03}},
        null_features={
            "null_ensemble_ref": "mock://obsstat-nulls",
            "look_elsewhere_status": "tracked",
        },
        manifest=_manifest(),
        sky_support=_sky_support(),
    )

    assert vector.alm_features["scalar_features"]["nested"]["pvalue_tail"] == 0.03


def test_obsstat_rejects_inference_or_family_identification_payload_keys() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="forbidden inference key"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            scalar_features={"posterior_odds": 1.2},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="forbidden inference key"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            null_features={"mio": {"certificate": "diagnostic-only"}},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="family identification"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            morphology_features={"identified_family": "VII_h"},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="family identification"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            morphology_features={"detected_geometry": "Bianchi VII_h"},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="family identification"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            morphology_features={
                "summary": "Bianchi family identified as VII_h"
            },
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="family identification"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            biposh_features={"family_rank": ["VII_h"]},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )


def test_transfer_derived_features_require_transfer_source_metadata() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="transfer_source"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            template_features={"transfer_derived": True},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="transfer_source"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            template_features={"branch": {"transfer_derived": True}},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="transfer_source"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            scalar_features={"branch": {"transfer_derived": True}},
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    with pytest.raises(ValueError, match="native transfer source"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            template_features={
                "transfer_derived": True,
                "transfer_source": "native_solver",
            },
            manifest=_manifest(),
            sky_support=_sky_support(),
        )

    vector = build_observable_vector(
        ell_max=2,
        channels=("TT",),
        template_features={
            **_external_transfer_metadata(),
            "branch": {"transfer_derived": True},
        },
        manifest=_manifest(),
        sky_support=_sky_support(),
    )

    assert vector.template_fit["transfer_source"] == "external_transfer"
    assert vector.template_fit["branch"]["transfer_derived"] is True

    scalar_vector = build_observable_vector(
        ell_max=2,
        channels=("TT",),
        scalar_features={
            **_external_transfer_metadata(),
            "branch": {"transfer_derived": True},
        },
        manifest=_manifest(),
        sky_support=_sky_support(),
    )

    assert scalar_vector.alm_features["scalar_features"]["branch"][
        "transfer_derived"
    ] is True


def test_obsstat_builder_requires_obsstat_owned_manifest() -> None:
    from htt.obsstat.observable_vector import build_observable_vector

    with pytest.raises(ValueError, match="OBSSTAT-owned manifest"):
        build_observable_vector(
            ell_max=2,
            channels=("TT",),
            manifest=_manifest(Owner.HTT),
            sky_support=_sky_support(),
        )


def test_obsstat_module_does_not_import_inference_or_mio_certificate() -> None:
    source_path = Path("htt/obsstat/observable_vector.py")
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
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
        module
        for module in imported
        if module.startswith(forbidden_roots) or "likelihood" in module
    ]


def test_obsstat_import_has_no_inference_or_mio_side_effects() -> None:
    before = set(sys.modules)

    importlib.import_module("htt.obsstat.observable_vector")

    loaded = set(sys.modules) - before
    assert not [
        module
        for module in loaded
        if module.startswith(("mio", "htt.mio", "htt.htt.infer"))
        or "likelihood" in module
        or "mio_certificate" in module
    ]
