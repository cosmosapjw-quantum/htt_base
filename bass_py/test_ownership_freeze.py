"""
test_ownership_freeze.py — repo root  (Week 3 Day 5b, merged v4.1)
===================================================================

Executable invariants enforcing the v4.1 MERGED ownership model.

Per `BASS_PY_INTEGRATION_v4_1_MERGED.md` §2 and `CANONICAL_DECISION_DESIGN.md`
§4.3, the ownership architecture is:

    bass/     →  runtime, background geometry, transport, collision (future),
                 tilt policy, validation. Sole allow/block owner.
    tsc/      →  Paper I Teff chart: charts, diagnostics, admissibility.
                 Pure mathematical layer; no runtime decisions.

The tests in this file enforce the boundary by walking Python ASTs and
inspecting import statements across the repository. Violations show up as
test failures long before they propagate into divergent validation logic.

Test classes (5):
  1. TestDirectoryStructure     — expected packages exist, __init__.py present
  2. TestBASSRuntimeOwnership   — bass/runtime/ alone owns allow/block surface
  3. TestTSCDoesNotOwnRuntime   — tsc/ modules never import bass/runtime/*
  4. TestSpecVersionConsistency — SPEC_VERSION pinned identically across modules
  5. TestPackageImportsResolve  — every module/test loads without error
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from typing import Iterable, List, Set, Tuple

import pytest


ROOT = Path(__file__).parent


# ============================================================================
# Section 1 - Helpers: walk ASTs, collect imports
# ============================================================================

def _iter_py_files(root: Path, *, exclude_tests: bool = False) -> Iterable[Path]:
    """Yield all .py files under `root`, optionally skipping test modules."""
    for p in root.rglob("*.py"):
        if p.name == "__init__.py":
            continue
        if exclude_tests and p.name.startswith("test_"):
            continue
        yield p


def _collect_imports(path: Path) -> Set[str]:
    """Return the set of fully-qualified imported names from a .py file.

    Collects both `import X.Y.Z` and `from X.Y import Z` forms. For the
    latter, the string returned is `X.Y.Z`.
    """
    tree = ast.parse(path.read_text(), filename=str(path))
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue  # relative import with no module; skip
            for alias in node.names:
                names.add(f"{node.module}.{alias.name}")
    return names


# ============================================================================
# Test Class 1 - Directory structure
# ============================================================================

class TestDirectoryStructure:
    """Expected subdirectories exist with __init__.py scaffolding."""

    EXPECTED_PACKAGES = (
        "bass",
        "bass/background",
        "bass/transport",
        "bass/tilt",
        "bass/validation",
        "bass/runtime",
        "bass/observational",
        "bass/collision",
        "tsc",
        "tsc/charts",
        "tsc/diagnostics",
        "tsc/admissibility",
    )

    @pytest.mark.parametrize("pkg", EXPECTED_PACKAGES)
    def test_package_directory_exists(self, pkg):
        d = ROOT / pkg
        assert d.is_dir(), f"{pkg} directory missing"

    @pytest.mark.parametrize("pkg", EXPECTED_PACKAGES)
    def test_package_has_init(self, pkg):
        init = ROOT / pkg / "__init__.py"
        assert init.is_file(), f"{pkg}/__init__.py missing"

    def test_no_stale_top_level_solver_modules(self):
        # After the freeze, solver modules must not live at repo root.
        # precision_dashboard and conftest are allowed; test_ownership_freeze
        # is this file. Everything else at root should not be a solver file.
        allowed_at_root = {
            "precision_dashboard.py",
            "conftest.py",
            "test_precision_dashboard.py",
            "test_ownership_freeze.py",
        }
        root_py = {p.name for p in ROOT.glob("*.py")}
        stray = root_py - allowed_at_root
        assert not stray, f"unexpected root-level .py files: {sorted(stray)}"


# ============================================================================
# Test Class 2 - BASS runtime is sole allow/block owner
# ============================================================================

class TestBASSRuntimeOwnership:
    """bass/runtime/canonical_decision.py alone constructs CanonicalDecision
    and emits ValidationLabel. No other module may do so."""

    def test_CanonicalDecision_constructed_only_in_bass_runtime(self):
        """Only bass/runtime/canonical_decision.py should name the
        CanonicalDecision class in a `from ... import CanonicalDecision`
        that is then *constructed*. Other modules may import it for type
        hints or introspection, which is allowed.

        Stronger proxy: only bass/runtime/ modules and tests may reference
        `CanonicalDecision(` (constructor call) outside of tests.
        """
        offending: List[Tuple[Path, int]] = []
        for py in _iter_py_files(ROOT, exclude_tests=True):
            # Allow the module that defines it
            if "bass/runtime" in str(py):
                continue
            # Allow the dashboard at repo root — but only if it does not
            # construct CanonicalDecision. Check source for `CanonicalDecision(`.
            text = py.read_text()
            for lineno, line in enumerate(text.splitlines(), start=1):
                if "CanonicalDecision(" in line and "test_" not in py.name:
                    offending.append((py, lineno))
        assert offending == [], (
            f"Non-bass/runtime modules construct CanonicalDecision: {offending}"
        )

    def test_ValidationLabel_value_construction_only_in_bass_runtime(self):
        """ValidationLabel(...) construction (i.e., parsing a string value
        back into the enum) must stay inside bass/runtime/. Downstream
        readers should reference members like ValidationLabel.BETA_POLICY_BLOCK
        without calling the enum constructor.
        """
        offending: List[Tuple[Path, int]] = []
        for py in _iter_py_files(ROOT, exclude_tests=True):
            if "bass/runtime" in str(py):
                continue
            text = py.read_text()
            for lineno, line in enumerate(text.splitlines(), start=1):
                # Constructor call pattern: `ValidationLabel(` followed by
                # a string/variable, not `ValidationLabel.XXX` member access.
                # We look for `ValidationLabel(` and exclude comments / docs.
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if "ValidationLabel(" in line:
                    offending.append((py, lineno))
        assert offending == [], (
            f"Non-bass/runtime modules construct ValidationLabel: {offending}"
        )

    def test_tsc_modules_do_not_import_canonical_decision(self):
        """TSC layer must not import bass.runtime.canonical_decision."""
        tsc_offending: List[Tuple[str, str]] = []
        for py in _iter_py_files(ROOT / "tsc", exclude_tests=True):
            imports = _collect_imports(py)
            for imp in imports:
                if "bass.runtime.canonical_decision" in imp:
                    tsc_offending.append((str(py), imp))
        assert tsc_offending == [], (
            f"TSC modules leak bass.runtime.canonical_decision: {tsc_offending}"
        )

    def test_tsc_modules_do_not_import_validation_labels(self):
        """TSC layer must not import bass.runtime.validation_labels."""
        tsc_offending: List[Tuple[str, str]] = []
        for py in _iter_py_files(ROOT / "tsc", exclude_tests=True):
            imports = _collect_imports(py)
            for imp in imports:
                if "bass.runtime.validation_labels" in imp:
                    tsc_offending.append((str(py), imp))
        assert tsc_offending == [], (
            f"TSC modules leak bass.runtime.validation_labels: {tsc_offending}"
        )


# ============================================================================
# Test Class 3 - TSC never imports bass/runtime/*
# ============================================================================

class TestTSCDoesNotOwnRuntime:
    """Global: no tsc/ module (source, not test) imports anything from
    bass/runtime/*, bass/tilt/*, or bass/validation/*."""

    FORBIDDEN_BASS_PREFIXES = (
        "bass.runtime",
        "bass.tilt",
        "bass.validation",
    )

    def test_tsc_source_never_imports_bass_runtime_family(self):
        """TSC → bass/runtime, bass/tilt, bass/validation imports forbidden.

        P2-W4-01 CLOSED (W4D5): the former whitelist entry for
        `tsc/charts/boost_perturbative.py` importing Prop 5 boost coefficients
        from `bass.validation.channel_routing` has been retired. The
        coefficients now live in `tsc/charts/boost_coefficients.py`, and
        `channel_routing.py` re-exports them for backward compatibility.

        This test now runs with **zero whitelist exceptions**.
        """
        offending: List[Tuple[str, str]] = []
        for py in _iter_py_files(ROOT / "tsc", exclude_tests=True):
            imports = _collect_imports(py)
            for imp in imports:
                for prefix in self.FORBIDDEN_BASS_PREFIXES:
                    if imp == prefix or imp.startswith(prefix + "."):
                        offending.append((str(py), imp))
        assert offending == [], (
            f"TSC source imports forbidden bass/* layer "
            f"(no whitelist remaining after P2-W4-01 closure): {offending}"
        )

    def test_bass_transport_and_background_are_tsc_free(self):
        """bass/transport/ and bass/background/ are pure BASS concerns; they
        must not depend on tsc/* either. (The tsc ↛ bass direction from §2 is
        the strong one; bass ↛ tsc is a softer invariant but still enforced
        for these two subpackages to keep background + transport portable.)
        """
        offending: List[Tuple[str, str]] = []
        for sub in ("bass/background", "bass/transport"):
            for py in _iter_py_files(ROOT / sub, exclude_tests=True):
                imports = _collect_imports(py)
                for imp in imports:
                    if imp == "tsc" or imp.startswith("tsc."):
                        offending.append((str(py), imp))
        assert offending == [], (
            f"bass/background or bass/transport imports tsc: {offending}"
        )


# ============================================================================
# Test Class 4 - SPEC_VERSION consistency
# ============================================================================

class TestSpecVersionConsistency:
    """SPEC_VERSION pins must match between canonical_decision and the
    L0 dashboard baseline."""

    def test_canonical_decision_spec_version(self):
        from bass.runtime.canonical_decision import SPEC_VERSION
        assert SPEC_VERSION == "v1.0-w3d1"

    def test_dashboard_spec_version(self):
        from precision_dashboard import L0_DASHBOARD_VERSION
        assert L0_DASHBOARD_VERSION == "v1.0-w3d5a"

    def test_versions_share_v1_0_family(self):
        from bass.runtime.canonical_decision import SPEC_VERSION
        from precision_dashboard import L0_DASHBOARD_VERSION
        # Both must begin with "v1.0-" — a shape convention, not a
        # requirement of identical strings.
        assert SPEC_VERSION.startswith("v1.0-")
        assert L0_DASHBOARD_VERSION.startswith("v1.0-")


# ============================================================================
# Test Class 5 - Package imports resolve cleanly
# ============================================================================

class TestPackageImportsResolve:
    """Smoke check: every module at its final v4.1 path imports without error."""

    BASS_MODULES = (
        "bass.background.bianchi_types",
        "bass.background.einstein_bianchi",
        "bass.transport.shear_sources",
        "bass.transport.ray_transport",
        "bass.transport.multipole_hierarchy",
        "bass.transport.implicit_hierarchy",
        "bass.transport.bianchi_i_hierarchy",
        "bass.tilt.baryon_only_policy",
        "bass.validation.comparator_policy",
        "bass.validation.channel_routing",
        "bass.runtime.canonical_decision",
        "bass.runtime.validation_labels",
        "bass.runtime.sigma_floor",
        "bass.observational.planck_mes_bounds",
        "bass.observational.beta_threshold",
        "bass.collision.thomson_tensor",
    )

    TSC_MODULES = (
        "tsc.charts.laguerre_basis",
        "tsc.charts.forward_F_to_T",
        "tsc.charts.boost_perturbative",
        "tsc.charts.boost_coefficients",
        "tsc.charts.inverse_T_to_F",
        "tsc.charts.inverse_T_to_F_mc",
        "tsc.diagnostics.tangency",
        "tsc.diagnostics.species_tangency",
        "tsc.diagnostics.spherical_quadrature",
        "tsc.diagnostics.entropy_invariants",
        "tsc.admissibility.realizability",
    )

    @pytest.mark.parametrize("modname", BASS_MODULES)
    def test_bass_module_imports(self, modname):
        mod = importlib.import_module(modname)
        assert mod is not None

    @pytest.mark.parametrize("modname", TSC_MODULES)
    def test_tsc_module_imports(self, modname):
        mod = importlib.import_module(modname)
        assert mod is not None

    def test_precision_dashboard_imports(self):
        import precision_dashboard as mod
        assert mod.L0_DASHBOARD_VERSION.startswith("v1.0-")
