from __future__ import annotations

import importlib
import ast
from pathlib import Path

import pytest

from common.contracts import (
    ArtifactManifest,
    BundleKind,
    ClaimTier,
    ImplementationScope,
    Owner,
    owner_can_emit_bundle,
)


REPO_ROOT = Path(__file__).resolve().parents[2]

_ALLOWED_ACTIVE_TSC_IMPORTS = {
    "htt/htt/htt/infer/likelihood_scope_guard.py": {
        "tsc.adapters.htt_inference.HttTscCaveatBundle",
        "tsc.adapters.htt_inference.overlay_to_htt_caveats",
    },
    "htt/mio/interface/mio_certificate.py": {
        "tsc.adapters.mio_certificate.overlay_to_mio_fields",
    },
    "htt/mio/bridges/preliminary_results.py": {
        "tsc.adapters.mio_certificate.MioTscAdequacyFields",
        "tsc.adapters.mio_certificate.overlay_to_mio_fields",
    },
    "htt/bass/runtime/canonical_decision.py": {
        "tsc.diagnostics.tangency.TangencyResult",
    },
    "htt/bass/hierarchy/aux_state.py": {
        "tsc.diagnostics.tangency.TangentKind",
        "tsc.diagnostics.tangency.compute_D_diagnostic",
    },
    "htt/bass/hierarchy/closure.py": {
        "tsc.diagnostics.tangency.TangentKind",
        "tsc.diagnostics.tangency.compute_D_diagnostic",
    },
    "htt/bass/likelihood/htt_decomposition.py": {
        "tsc.diagnostics.tangency.TangencyResult",
    },
    "htt/bass/likelihood/planck2018_flrw_match.py": {
        "tsc.diagnostics.tangency.TangencyResult",
        "tsc.diagnostics.tangency.TangentKind",
    },
    "htt/bass/validation/channel_routing.py": {
        "tsc.charts.boost_coefficients.PROP5_COEFF_DIPOLE_FROM_QUADRUPOLE",
        "tsc.charts.boost_coefficients.PROP5_COEFF_QUADRUPOLE_FROM_DIPOLE",
        "tsc.charts.boost_coefficients.PROP5_COEFF_OCTUPOLE_FROM_QUADRUPOLE",
        "tsc.charts.boost_coefficients.boost_mixing_matrix",
        "tsc.charts.boost_coefficients.boost_additive_velocity_terms",
        "tsc.charts.boost_coefficients.apply_boost_to_teff",
    },
}


def _manifest(*, owner: str | Owner = "TSC") -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id="tsc.legacy.overlay",
        artifact_path="artifacts/tsc/legacy_overlay.json",
        owner=owner,
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="diagnostic_only",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["input"],
        code_version="0.0-test",
        schema_version="pr030",
    )


def _tsc_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "tsc" or alias.name.startswith("tsc."):
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            if node.module == "tsc" or node.module.startswith("tsc."):
                for alias in node.names:
                    imports.add(f"{node.module}.{alias.name}")
    return imports


def test_tsc_import_surface_preserves_legacy_contract_names() -> None:
    tsc = importlib.import_module("tsc")

    assert tsc.TSC_LEGACY_IMPORT_COMPATIBLE is True
    assert tsc.TSC_ACTIVE_SCIENCE_OWNER is False
    assert tsc.TSC_OWNER is Owner.TSC_LEGACY
    assert tsc.TSC_IMPLEMENTATION_SCOPE is ImplementationScope.TSC_LEGACY
    assert tsc.TSC_ALLOWED_BUNDLE_KIND is BundleKind.LEGACY_REPRODUCTION
    assert "TSC_ACTIVE_SCIENCE_OWNER" in tsc.__all__
    assert "ALLOWED_COMBINED_LABELS" in tsc.__all__


def test_tsc_legacy_package_reexports_the_boundary_metadata() -> None:
    tsc_legacy = importlib.import_module("tsc_legacy")

    assert tsc_legacy.TSC_OWNER is Owner.TSC_LEGACY
    assert tsc_legacy.TSC_IMPLEMENTATION_SCOPE is ImplementationScope.TSC_LEGACY
    assert tsc_legacy.TSC_ALLOWED_BUNDLE_KIND is BundleKind.LEGACY_REPRODUCTION
    assert tsc_legacy.TSC_ACTIVE_SCIENCE_OWNER is False
    assert "legacy reproduction" in tsc_legacy.TSC_DEPRECATION_CAVEAT
    assert "not posterior-producing" in tsc_legacy.TSC_DEPRECATION_CAVEAT


def test_tsc_legacy_manifest_helper_accepts_only_legacy_owner_scope() -> None:
    tsc_legacy = importlib.import_module("tsc_legacy")

    manifest = _manifest()

    assert manifest.owner is Owner.TSC_LEGACY
    assert manifest.implementation_scope is ImplementationScope.TSC_LEGACY
    assert tsc_legacy.assert_legacy_reproduction_manifest(manifest) is manifest

    with pytest.raises(ValueError, match="TSC legacy artifacts"):
        tsc_legacy.assert_legacy_reproduction_manifest(
            _manifest(owner=Owner.COMMON),
        )


def test_tsc_can_only_emit_legacy_reproduction_bundle_kind() -> None:
    assert owner_can_emit_bundle(Owner.TSC_LEGACY, BundleKind.LEGACY_REPRODUCTION)
    assert not owner_can_emit_bundle(Owner.TSC_LEGACY, BundleKind.POSTERIOR)
    assert not owner_can_emit_bundle(
        Owner.TSC_LEGACY,
        BundleKind.DIAGNOSTIC_CERTIFICATE,
    )
    assert not owner_can_emit_bundle(Owner.TSC_LEGACY, BundleKind.TRANSFER_ATLAS)
    assert not owner_can_emit_bundle(
        Owner.TSC_LEGACY,
        BundleKind.OBSERVABLE_FEATURES,
    )
    assert not owner_can_emit_bundle(Owner.TSC_LEGACY, BundleKind.COMMON_CONTRACT)


def test_deprecation_docs_exist_and_downclaim_tsc_status() -> None:
    readme = REPO_ROOT / "htt" / "tsc_legacy" / "README.md"
    deprecation_doc = REPO_ROOT / "docs" / "deprecation" / "tsc_legacy.md"

    readme_text = readme.read_text(encoding="utf-8")
    deprecation_text = deprecation_doc.read_text(encoding="utf-8")
    combined = f"{readme_text}\n{deprecation_text}"

    assert "TSC_LEGACY" in combined
    assert "legacy reproduction" in combined
    assert "diagnostic-only" in combined
    assert "not a native solver" in combined
    assert "not HTT evidence" in combined
    assert "not a MIO certificate" in combined
    assert "not family identification" in combined
    assert "full solver" not in combined
    assert "posterior owner" not in combined
    assert "truth certificate" not in combined


def test_legacy_import_has_no_deprecation_warning_by_default() -> None:
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        importlib.reload(importlib.import_module("tsc"))
        importlib.reload(importlib.import_module("tsc_legacy"))

    assert [warning for warning in caught if warning.category is DeprecationWarning] == []


def test_legacy_manifest_helper_rejects_stronger_claim_tiers() -> None:
    tsc_legacy = importlib.import_module("tsc_legacy")
    manifest = ArtifactManifest(
        artifact_id="tsc.legacy.invalid",
        artifact_path="artifacts/tsc/invalid.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier=ClaimTier.VALIDATED,
        production_status="diagnostic_only",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["input"],
        code_version="0.0-test",
        schema_version="pr030",
    )

    with pytest.raises(ValueError, match="conditional or diagnostic_only"):
        tsc_legacy.assert_legacy_reproduction_manifest(manifest)


def test_active_mio_htt_bass_tsc_imports_are_legacy_or_caveat_only() -> None:
    scanned_roots = [
        REPO_ROOT / "htt" / "htt" / "htt",
        REPO_ROOT / "htt" / "mio",
        REPO_ROOT / "htt" / "bass",
    ]
    actual: dict[str, set[str]] = {}
    for root in scanned_roots:
        for path in root.rglob("*.py"):
            if path.name.startswith("test_") or "tests" in path.parts:
                continue
            imports = _tsc_imports(path)
            if imports:
                actual[path.relative_to(REPO_ROOT).as_posix()] = imports

    assert actual == _ALLOWED_ACTIVE_TSC_IMPORTS
