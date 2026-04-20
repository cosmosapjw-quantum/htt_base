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
    ROOT / "htt_forward_output.py",
    ROOT / "mio_certificate.py",
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
