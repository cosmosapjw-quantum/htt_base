"""Pytest plugin for deterministic, selector-bound execution evidence.

The plugin records what pytest actually collected and reached.  It does not
turn a passing test run into scientific authority; consumers must still bind
the resulting JSON to a claim closure and an authorized receipt.
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import platform
import site
import sys
from types import ModuleType
from typing import Any

import pytest

from common.evidence_graph import EvidenceGraphError, load_literal_release_pin_fields


SCHEMA_VERSION = "common.pytest_execution_evidence.v2"
ENVIRONMENT_SCHEMA_VERSION = "common.pytest_execution_environment.v1"
_OUTPUT_OPTION = "--evidence-output"
_EXCLUDED_IMPORT_ORIGINS: tuple[dict[str, object], ...] = ()
_PIN_MODULE = "common.release_evidence_pin"
_PIN_SOURCE = Path(__file__).with_name("release_evidence_pin.py")
load_literal_release_pin_fields(_PIN_SOURCE)


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _normalized_invocation(args: tuple[str, ...]) -> list[str]:
    """Redact only the output destination while retaining exact selectors."""

    normalized: list[str] = []
    skip_next = False
    for raw in args:
        if skip_next:
            normalized.append("<evidence-output>")
            skip_next = False
            continue
        if raw == _OUTPUT_OPTION:
            normalized.append(raw)
            skip_next = True
            continue
        if raw.startswith(f"{_OUTPUT_OPTION}="):
            normalized.append(f"{_OUTPUT_OPTION}=<evidence-output>")
            continue
        normalized.append(raw)
    if skip_next:
        raise pytest.UsageError(f"{_OUTPUT_OPTION} requires a path")
    return normalized


def _path_locator(path: Path, root: Path) -> dict[str, str]:
    """Return a host-path-free locator for one execution-environment path."""

    resolved = path.resolve(strict=False)
    sitecustomize = importlib.util.find_spec("sitecustomize")
    python_config_root = (
        None
        if sitecustomize is None or sitecustomize.origin is None
        else Path(sitecustomize.origin).resolve().parent
    )
    roots = (
        ("repo", root),
        ("python_base_prefix", Path(sys.base_prefix).resolve()),
        ("python_prefix", Path(sys.prefix).resolve()),
        ("python_config", python_config_root),
    )
    for scope, anchor in roots:
        if anchor is None:
            continue
        try:
            relative = resolved.relative_to(anchor)
        except ValueError:
            continue
        return {"scope": scope, "path": relative.as_posix() or "."}
    # External locations are disclosed without embedding a machine- or
    # tmp-directory-specific absolute path.  Authoritative consumers reject
    # this scope; the row is still useful in a failed diagnostic receipt.
    return {"scope": "external_untrusted", "path": resolved.name or "<root>"}


def _source_path(path: Path) -> Path:
    """Prefer source bytes to cache bytes when an import exposes ``.pyc``."""

    if path.suffix == ".pyc":
        try:
            candidate = Path(importlib.util.source_from_cache(str(path)))
        except (NotImplementedError, ValueError):
            return path
        if candidate.is_file():
            return candidate
    return path


def _file_binding(path: Path, root: Path) -> dict[str, str]:
    source = _source_path(path.resolve(strict=False))
    locator = _path_locator(source, root)
    if not source.is_file() or source.is_symlink():
        return {**locator, "sha256": "MISSING"}
    return {**locator, "sha256": _sha256_file(source)}


def _selector_paths(config: pytest.Config) -> list[dict[str, str]]:
    root = Path(str(config.rootpath)).resolve()
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for selector in config.args:
        raw_path = str(selector).split("::", 1)[0]
        path = Path(raw_path)
        resolved = (
            path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
        )
        if not resolved.is_file():
            continue
        locator = _path_locator(resolved, root)
        identity = f"{locator['scope']}:{locator['path']}"
        if identity in seen:
            continue
        seen.add(identity)
        rows.append({**locator, "sha256": _sha256_file(resolved)})
    return sorted(rows, key=lambda row: (row["scope"], row["path"]))


def _plugin_source(plugin: object) -> Path | None:
    target: object = plugin if isinstance(plugin, ModuleType) else type(plugin)
    raw = getattr(target, "__file__", None)
    if raw is None:
        try:
            raw = inspect.getsourcefile(target) or inspect.getfile(target)
        except (OSError, TypeError):
            return None
    return Path(str(raw))


def _plugin_inventory(config: pytest.Config, root: Path) -> list[dict[str, object]]:
    rows: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for _registration_name, plugin in config.pluginmanager.list_name_plugin():
        if plugin is None:
            continue
        if isinstance(plugin, ModuleType):
            module = str(getattr(plugin, "__name__", ""))
            qualname = "<module>"
        else:
            module = type(plugin).__module__
            qualname = type(plugin).__qualname__
        source = _plugin_source(plugin)
        if not module or not qualname or source is None:
            continue
        binding = _file_binding(source, root)
        key = (module, qualname, binding["scope"], binding["path"])
        rows[key] = {
            "module": module,
            "qualname": qualname,
            "source": binding,
        }
    return [rows[key] for key in sorted(rows)]


def _conftest_inventory(config: pytest.Config, root: Path) -> list[dict[str, str]]:
    plugins = getattr(config.pluginmanager, "_conftest_plugins", ())
    rows: dict[tuple[str, str], dict[str, str]] = {}
    for plugin in plugins:
        source = _plugin_source(plugin)
        if source is None:
            continue
        binding = _file_binding(source, root)
        rows[(binding["scope"], binding["path"])] = binding
    return [rows[key] for key in sorted(rows)]


def _import_origin_inventory(root: Path) -> list[dict[str, object]]:
    """Bind every loaded file-backed module in the hermetic path roots."""

    rows: dict[tuple[str, str, str], dict[str, object]] = {}
    pin_path = root / "htt/src/common/release_evidence_pin.py"
    if pin_path.is_symlink() or not pin_path.is_file():
        raise pytest.UsageError(
            "the literal-only release pin is missing or non-regular"
        )
    try:
        load_literal_release_pin_fields(pin_path)
    except EvidenceGraphError as exc:
        raise pytest.UsageError(
            "the literal-only release pin source is invalid"
        ) from exc
    pin_resolved = pin_path.resolve()
    for name, module in tuple(sys.modules.items()):
        if not isinstance(name, str) or not name:
            continue
        if name == _PIN_MODULE:
            raise pytest.UsageError(
                "the literal-only release pin module must not be imported"
            )
        raw = getattr(module, "__file__", None)
        if raw is None:
            continue
        source = _source_path(Path(str(raw)))
        if source.exists() and source.resolve() == pin_resolved:
            raise pytest.UsageError(
                "the literal-only release pin source must not be loaded under an alias"
            )
        binding = _file_binding(Path(str(raw)), root)
        key = (name, binding["scope"], binding["path"])
        rows[key] = {"module": name, "source": binding}
    return [rows[key] for key in sorted(rows)]


def _bytecode_policy(root: Path) -> dict[str, object]:
    """Require a source-only interpreter rooted at an empty external cache."""

    if not sys.dont_write_bytecode:
        raise pytest.UsageError("authoritative evidence requires -B")
    raw_prefix = sys.pycache_prefix
    if not isinstance(raw_prefix, str) or not raw_prefix:
        raise pytest.UsageError(
            "authoritative evidence requires an isolated -X pycache_prefix"
        )
    prefix = Path(raw_prefix)
    if not prefix.is_absolute() or prefix.is_symlink() or not prefix.is_dir():
        raise pytest.UsageError(
            "authoritative pycache prefix must be an absolute regular directory"
        )
    resolved = prefix.resolve()
    for forbidden in (
        root,
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
    ):
        try:
            resolved.relative_to(forbidden)
        except ValueError:
            continue
        raise pytest.UsageError(
            "authoritative pycache prefix must be external to repo and interpreters"
        )
    if any(prefix.iterdir()):
        raise pytest.UsageError(
            "authoritative pycache prefix is not empty under source-only execution"
        )
    loaded_cache_files: list[str] = []
    for module in tuple(sys.modules.values()):
        raw = getattr(module, "__cached__", None)
        if raw is None:
            continue
        cached = Path(str(raw))
        if cached.exists() or cached.is_symlink():
            loaded_cache_files.append(cached.name)
    if loaded_cache_files:
        raise pytest.UsageError("authoritative execution loaded bytecode cache files")
    return {
        "dont_write_bytecode": True,
        "pycache_prefix_status": "isolated_empty_external",
        "loaded_cache_files": [],
    }


def _json_safe(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_safe(nested) for key, nested in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    return str(value)


def _environment_contract(config: pytest.Config) -> dict[str, object]:
    root = Path(str(config.rootpath)).resolve()
    sys_path_rows = [
        _path_locator(Path(entry) if entry else Path.cwd(), root) for entry in sys.path
    ]
    ini_path = getattr(config, "inipath", None)
    ini_binding = None if ini_path is None else _file_binding(Path(ini_path), root)
    ini_values = _json_safe(dict(config.inicfg))
    hidden_pythonpath = os.environ.get("PYTHONPATH")
    contract: dict[str, object] = {
        "schema_version": ENVIRONMENT_SCHEMA_VERSION,
        "interpreter": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
            "cache_tag": str(getattr(sys.implementation, "cache_tag", "")),
            "executable": _file_binding(Path(sys.executable), root),
            "isolated": bool(sys.flags.isolated),
            "safe_path": bool(getattr(sys.flags, "safe_path", sys.flags.isolated)),
            "user_site_enabled": bool(site.ENABLE_USER_SITE),
        },
        "sys_path": sys_path_rows,
        "pytest": {
            "version": pytest.__version__,
            "rootdir": ".",
            "import_mode": str(config.getoption("importmode")),
            "config_file": ini_binding,
            "config_values": ini_values,
            "config_values_sha256": _sha256_bytes(_canonical_bytes(ini_values)),
            "plugins": _plugin_inventory(config, root),
            "conftests": _conftest_inventory(config, root),
        },
        "import_origins": _import_origin_inventory(root),
        "excluded_import_origins": [dict(row) for row in _EXCLUDED_IMPORT_ORIGINS],
        "bytecode_policy": _bytecode_policy(root),
        "startup_policy": {
            "no_site": bool(sys.flags.no_site),
            "automatic_pth_processing": "disabled_by_no_site",
            "pyvenv_cfg_activation": "disabled_by_no_site",
        },
        "hidden_controls": {
            "pytest_addopts": os.environ.get("PYTEST_ADDOPTS"),
            "pytest_plugins": os.environ.get("PYTEST_PLUGINS"),
            "pytest_disable_plugin_autoload": os.environ.get(
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD"
            ),
            "pythonpath_status": (
                "unset"
                if not hidden_pythonpath
                else (
                    "ignored_by_isolated_mode"
                    if bool(sys.flags.isolated)
                    else "effective_unbound"
                )
            ),
        },
    }
    contract["environment_ref"] = _sha256_bytes(_canonical_bytes(contract))
    return contract


class _EvidenceRecorder:
    def __init__(self, config: pytest.Config, output: Path) -> None:
        self.config = config
        self.output = output
        self.collected_ids: list[str] = []
        self.call_reports: dict[str, str] = {}
        self.executed_ids: set[str] = set()
        self.failed_ids: set[str] = set()
        self.skipped_ids: set[str] = set()
        self.xfailed_ids: set[str] = set()
        self.xpassed_ids: set[str] = set()

    @pytest.hookimpl
    def pytest_collection_finish(self, session: pytest.Session) -> None:
        self.collected_ids = [item.nodeid for item in session.items]

    @pytest.hookimpl
    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        # A setup or teardown failure is still execution evidence for this
        # node and must dominate an otherwise-passing call phase.
        self.executed_ids.add(report.nodeid)
        if report.failed:
            self.failed_ids.add(report.nodeid)
        was_xfail = getattr(report, "wasxfail", None)
        if was_xfail:
            if report.skipped:
                self.xfailed_ids.add(report.nodeid)
            elif report.passed:
                self.xpassed_ids.add(report.nodeid)
        elif report.skipped:
            self.skipped_ids.add(report.nodeid)
        if report.when == "call":
            self.call_reports[report.nodeid] = report.outcome

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(
        self, session: pytest.Session, exitstatus: int | pytest.ExitCode
    ) -> None:
        collected = list(self.collected_ids)
        if len(collected) != len(set(collected)):
            raise pytest.UsageError("collected pytest node IDs are not unique")
        executed_ids = sorted(self.executed_ids)
        passed_ids = sorted(
            nodeid
            for nodeid, outcome in self.call_reports.items()
            if outcome == "passed"
            and nodeid not in self.failed_ids
            and nodeid not in self.xfailed_ids
            and nodeid not in self.xpassed_ids
        )
        failed_ids = sorted(self.failed_ids - self.xfailed_ids - self.xpassed_ids)
        skipped_ids = sorted(self.skipped_ids - self.xfailed_ids)
        xfailed_ids = sorted(self.xfailed_ids)
        xpassed_ids = sorted(self.xpassed_ids)
        normalized_argv = _normalized_invocation(
            tuple(str(arg) for arg in self.config.invocation_params.args)
        )
        selectors = [str(value) for value in self.config.args]
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "runner": "pytest",
            "runner_version": pytest.__version__,
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": sys.platform,
            "rootdir": ".",
            "selector_argv": selectors,
            "normalized_invocation_argv": normalized_argv,
            "selector_hash": _sha256_bytes(_canonical_bytes(selectors)),
            "selector_inputs": _selector_paths(self.config),
            "environment_contract": _environment_contract(self.config),
            "collected_node_ids": collected,
            "collected_node_ids_hash": _sha256_bytes(_canonical_bytes(collected)),
            "executed_node_ids": executed_ids,
            "executed_node_ids_hash": _sha256_bytes(_canonical_bytes(executed_ids)),
            "passed_node_ids": passed_ids,
            "failed_node_ids": failed_ids,
            "skipped_node_ids": skipped_ids,
            "xfailed_node_ids": xfailed_ids,
            "xpassed_node_ids": xpassed_ids,
            "counts": {
                "collected": len(collected),
                "executed": len(executed_ids),
                "passed": len(passed_ids),
                "failed": len(failed_ids),
                "skipped": len(skipped_ids),
                "xfailed": len(xfailed_ids),
                "xpassed": len(xpassed_ids),
            },
            "exit_status": int(exitstatus),
            "process_result": (
                "passed"
                if int(exitstatus) == int(pytest.ExitCode.OK) and bool(passed_ids)
                else "failed"
            ),
            "caveats": [
                "test execution evidence is process evidence only",
                "skipped and xfailed tests are not counted as passed authority",
                "scientific status is not inferred from this receipt",
            ],
        }
        payload["content_sha256"] = _sha256_bytes(_canonical_bytes(payload))
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.output.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("claim-evidence")
    group.addoption(
        _OUTPUT_OPTION,
        action="store",
        default=None,
        metavar="PATH",
        help="write deterministic selector/collection/execution evidence JSON",
    )


def pytest_configure(config: pytest.Config) -> None:
    raw = config.getoption(_OUTPUT_OPTION)
    if raw:
        config.pluginmanager.register(
            _EvidenceRecorder(config, Path(str(raw)).resolve()),
            "common-pytest-execution-evidence-recorder",
        )
