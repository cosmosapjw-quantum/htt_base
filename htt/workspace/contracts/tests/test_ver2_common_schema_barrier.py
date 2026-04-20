"""VER2-V0 schema barrier tests for workspace contracts."""
from __future__ import annotations

import ast
from pathlib import Path

from workspace.contracts.atlas_entry import AtlasEntry
from workspace.contracts.htt_forward_output import HttForwardOutput
from workspace.contracts.mio_certificate import MioCertificate


ROOT = Path(__file__).resolve().parents[1]
MODULES = [
    ROOT / "atlas_entry.py",
    ROOT / "atlas_entry_lite.py",
    ROOT / "departure_report.py",
    ROOT / "full_cov_mes_report.py",
    ROOT / "htt_forward_output.py",
    ROOT / "mio_certificate.py",
    ROOT / "observable_vector.py",
    ROOT / "tsc_overlay.py",
]
FORBIDDEN_LOCAL_SCHEMA_NAMES = {
    "Owner",
    "ClaimTier",
    "ImplementationScope",
    "ProductionStatus",
    "ArtifactManifest",
}


def _defined_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def test_workspace_contract_modules_do_not_redefine_common_schema_names():
    for module in MODULES:
        names = _defined_names(module)
        assert not (names & FORBIDDEN_LOCAL_SCHEMA_NAMES), (
            f"{module.name} redefines canonical common schema names: "
            f"{sorted(names & FORBIDDEN_LOCAL_SCHEMA_NAMES)}"
        )


def test_manifest_field_is_present_on_cross_package_contracts():
    for contract in (AtlasEntry, HttForwardOutput, MioCertificate):
        field_names = {field.name for field in contract.__dataclass_fields__.values()}
        assert "manifest" in field_names, (
            f"{contract.__name__} must expose a manifest hook under VER2-V0"
        )


def test_thin_wrapper_aliases_point_to_common_contracts():
    from common.contracts import AtlasEntryLite as CanonicalAtlasEntryLite
    from common.contracts import FullCovMESReport as CanonicalFullCovMESReport
    from common.contracts import ObservableVector as CanonicalObservableVector
    from common.contracts import TscAdequacyOverlay as CanonicalTscAdequacyOverlay
    from common.departure_contracts import DepartureReport as CanonicalDepartureReport
    from workspace.contracts.atlas_entry_lite import AtlasEntryLite
    from workspace.contracts.departure_report import DepartureReport
    from workspace.contracts.full_cov_mes_report import FullCovMESReport
    from workspace.contracts.observable_vector import ObservableVector
    from workspace.contracts.tsc_overlay import TscAdequacyOverlay

    assert AtlasEntryLite is CanonicalAtlasEntryLite
    assert DepartureReport is CanonicalDepartureReport
    assert FullCovMESReport is CanonicalFullCovMESReport
    assert ObservableVector is CanonicalObservableVector
    assert TscAdequacyOverlay is CanonicalTscAdequacyOverlay
