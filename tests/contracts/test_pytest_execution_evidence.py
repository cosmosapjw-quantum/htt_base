from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import subprocess
import sys
from types import ModuleType

import pytest

from common.evidence_graph import (
    EvidenceGraphError,
    TestExecution,
    verify_pytest_environment_inputs,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON = REPO_ROOT / "venv/bin/python"
BUILDER = REPO_ROOT / "scripts/codex_harness/build_claim_evidence_graph.py"
PIN_SOURCE = REPO_ROOT / "htt/src/common/release_evidence_pin.py"
SOURCE_ONLY_LAUNCHER = REPO_ROOT / "scripts/codex_harness/run_pr122_source_only.sh"


def _hermetic_pytest_prefix(output: Path) -> list[str]:
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = PYTHON.parent.parent / "lib" / version / "site-packages"
    source_paths = [
        str(REPO_ROOT / "htt/src"),
        str(REPO_ROOT / "htt"),
        str(site_packages),
    ]
    cache = output.parent / f"{output.stem}-pycache"
    cache.mkdir()
    bootstrap = (
        "import os,runpy,sys;"
        f"sys.path[:0]={source_paths!r};"
        "[os.environ.pop(k,None) for k in "
        "('PYTHONPATH','PYTEST_ADDOPTS','PYTEST_PLUGINS')];"
        "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';"
        "sys.argv[0]='pytest';"
        "runpy.run_module('pytest',run_name='__main__')"
    )
    return [
        str(PYTHON),
        "-I",
        "-S",
        "-B",
        "-X",
        f"pycache_prefix={cache}",
        "-c",
        bootstrap,
        "-p",
        "common.pytest_execution_evidence",
        "-p",
        "no:cacheprovider",
        "--import-mode=importlib",
        "--rootdir",
        ".",
        "-c",
        "pytest.ini",
        "-q",
        "--evidence-output",
        str(output),
    ]


def _selector_arg(path: Path) -> str:
    return os.path.relpath(path, REPO_ROOT)


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _reseal_environment_and_receipt(payload: dict[str, object]) -> None:
    environment = payload["environment_contract"]
    assert isinstance(environment, dict)
    environment.pop("environment_ref", None)
    environment["environment_ref"] = hashlib.sha256(
        _canonical_bytes(environment)
    ).hexdigest()
    payload.pop("content_sha256", None)
    payload["content_sha256"] = hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _load_builder():
    spec = importlib.util.spec_from_file_location("pr122_replay_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plugin_binds_actual_selector_collection_and_execution(tmp_path: Path) -> None:
    target = tmp_path / "test_target.py"
    target.write_text(
        "def test_pass():\n    assert True\n\n"
        "def test_skip():\n    import pytest\n    pytest.skip('declared')\n",
        encoding="utf-8",
    )
    output = tmp_path / "receipt.json"
    command = [*_hermetic_pytest_prefix(output), _selector_arg(target)]
    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "common.pytest_execution_evidence.v2"
    environment = payload["environment_contract"]
    assert environment["schema_version"] == "common.pytest_execution_environment.v1"
    assert environment["interpreter"]["isolated"] is True
    assert environment["interpreter"]["safe_path"] is True
    assert environment["pytest"]["import_mode"] == "importlib"
    assert environment["pytest"]["config_file"]["path"] == "pytest.ini"
    assert environment["pytest"]["plugins"]
    assert environment["import_origins"]
    assert environment["bytecode_policy"] == {
        "dont_write_bytecode": True,
        "pycache_prefix_status": "isolated_empty_external",
        "loaded_cache_files": [],
    }
    assert environment["startup_policy"] == {
        "no_site": True,
        "automatic_pth_processing": "disabled_by_no_site",
        "pyvenv_cfg_activation": "disabled_by_no_site",
    }
    assert environment["excluded_import_origins"] == []
    assert "common.release_evidence_pin" not in {
        row["module"] for row in environment["import_origins"]
    }
    assert payload["counts"] == {
        "collected": 2,
        "executed": 2,
        "passed": 1,
        "failed": 0,
        "skipped": 1,
        "xfailed": 0,
        "xpassed": 0,
    }
    assert payload["process_result"] == "passed"
    assert len(payload["collected_node_ids"]) == 2
    assert set(payload["executed_node_ids"]) <= set(payload["collected_node_ids"])
    assert payload["skipped_node_ids"]
    assert str(output) not in payload["normalized_invocation_argv"]
    content_sha = payload.pop("content_sha256")
    assert content_sha == hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def test_zero_collection_is_not_authority(tmp_path: Path) -> None:
    target = tmp_path / "test_empty.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    output = tmp_path / "empty.json"
    result = subprocess.run(
        [*_hermetic_pytest_prefix(output), _selector_arg(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 5
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["counts"]["collected"] == 0
    assert payload["counts"]["executed"] == 0
    assert payload["process_result"] == "failed"


def test_nonexistent_python_selector_cannot_create_authority(tmp_path: Path) -> None:
    output = tmp_path / "nonexistent.json"
    result = subprocess.run(
        [
            *_hermetic_pytest_prefix(output),
            _selector_arg(tmp_path / "does_not_exist.py"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert output.is_file()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["counts"]["collected"] == 0
    assert payload["counts"]["executed"] == 0
    with pytest.raises(EvidenceGraphError):
        TestExecution.from_pytest_evidence(payload)


def test_setup_and_teardown_failures_cannot_be_laundered_as_call_passes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "test_phase_failures.py"
    target.write_text(
        "import pytest\n\n"
        "@pytest.fixture\n"
        "def setup_broken():\n"
        "    raise RuntimeError('setup failed')\n\n"
        "@pytest.fixture\n"
        "def teardown_broken():\n"
        "    yield\n"
        "    raise RuntimeError('teardown failed')\n\n"
        "def test_setup_failure(setup_broken):\n"
        "    assert True\n\n"
        "def test_teardown_failure(teardown_broken):\n"
        "    assert True\n",
        encoding="utf-8",
    )
    output = tmp_path / "phase-failures.json"
    result = subprocess.run(
        [*_hermetic_pytest_prefix(output), _selector_arg(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["counts"]["collected"] == 2
    assert payload["counts"]["executed"] == 2
    assert payload["counts"]["passed"] == 0
    assert payload["counts"]["failed"] == 2
    assert payload["process_result"] == "failed"
    with pytest.raises(EvidenceGraphError, match="nonzero pytest exit_status"):
        TestExecution.from_pytest_evidence(payload)


def test_hermetic_environment_contract_rehashes_live_inputs_and_pr121_lock(
    tmp_path: Path,
) -> None:
    output = tmp_path / "hermetic.json"
    selector = (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_data_only_pin_rejects_noncanonical_trust_root_fields"
    )
    result = subprocess.run(
        [*_hermetic_pytest_prefix(output), selector],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
        env={
            key: value
            for key, value in os.environ.items()
            if key not in {"PYTEST_ADDOPTS", "PYTEST_PLUGINS"}
        },
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    parent = json.loads(
        (REPO_ROOT / "docs/generated/pr121_hermetic_replay_receipt.json").read_text(
            encoding="utf-8"
        )
    )
    environment_ref = verify_pytest_environment_inputs(
        REPO_ROOT,
        payload,
        parent_environment_lock=parent["environment_lock"],
    )
    execution = TestExecution.from_pytest_evidence(payload)
    assert execution.environment_ref == environment_ref
    assert execution.is_authoritative is True

    mismatched_parent = copy.deepcopy(parent["environment_lock"])
    mismatched_parent["python"] = "0.0.0"
    with pytest.raises(EvidenceGraphError, match="mismatches PR-121 lock"):
        verify_pytest_environment_inputs(
            REPO_ROOT,
            payload,
            parent_environment_lock=mismatched_parent,
        )


def test_omitted_pytest_environment_contract_cannot_authorize_receipt(
    tmp_path: Path,
) -> None:
    output = tmp_path / "omitted-environment.json"
    selector = (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_data_only_pin_rejects_noncanonical_trust_root_fields"
    )
    result = subprocess.run(
        [*_hermetic_pytest_prefix(output), selector],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload.pop("environment_contract")
    payload.pop("content_sha256")
    payload["content_sha256"] = hashlib.sha256(_canonical_bytes(payload)).hexdigest()

    with pytest.raises(EvidenceGraphError, match="environment_contract"):
        TestExecution.from_pytest_evidence(payload)


def test_tampered_pytest_environment_or_plugin_binding_fails_live_rehash(
    tmp_path: Path,
) -> None:
    output = tmp_path / "tampered-plugin.json"
    selector = (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_data_only_pin_rejects_noncanonical_trust_root_fields"
    )
    result = subprocess.run(
        [*_hermetic_pytest_prefix(output), selector],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    original = json.loads(output.read_text(encoding="utf-8"))
    substitute = {
        "scope": "repo",
        "path": "pytest.ini",
        "sha256": hashlib.sha256((REPO_ROOT / "pytest.ini").read_bytes()).hexdigest(),
    }

    plugin_payload = copy.deepcopy(original)
    plugins = plugin_payload["environment_contract"]["pytest"]["plugins"]
    plugin = next(
        row for row in plugins if row["module"] == "common.pytest_execution_evidence"
    )
    plugin["source"] = substitute
    plugin_origin = next(
        row
        for row in plugin_payload["environment_contract"]["import_origins"]
        if row["module"] == "common.pytest_execution_evidence"
    )
    plugin_origin["source"] = substitute
    _reseal_environment_and_receipt(plugin_payload)

    # Valid substitute hashes and resealed addresses cannot relabel a data file
    # as the loaded evidence producer.
    TestExecution.from_pytest_evidence(plugin_payload)
    with pytest.raises(EvidenceGraphError, match="canonical source"):
        verify_pytest_environment_inputs(REPO_ROOT, plugin_payload)

    interpreter_payload = copy.deepcopy(original)
    interpreter_payload["environment_contract"]["interpreter"][
        "executable"
    ] = substitute
    _reseal_environment_and_receipt(interpreter_payload)
    TestExecution.from_pytest_evidence(interpreter_payload)
    with pytest.raises(EvidenceGraphError, match="canonical source"):
        verify_pytest_environment_inputs(REPO_ROOT, interpreter_payload)

    host_path_payload = copy.deepcopy(original)
    host_path_payload["normalized_invocation_argv"].append(str(REPO_ROOT))
    host_path_payload.pop("content_sha256")
    host_path_payload["content_sha256"] = hashlib.sha256(
        _canonical_bytes(host_path_payload)
    ).hexdigest()
    with pytest.raises(EvidenceGraphError, match="host-absolute path"):
        TestExecution.from_pytest_evidence(host_path_payload)


def test_arbitrary_pytest_import_origin_exemption_is_rejected(tmp_path: Path) -> None:
    output = tmp_path / "tampered-import-exemption.json"
    selector = (
        "tests/contracts/test_release_evidence_binding.py::"
        "test_data_only_pin_rejects_noncanonical_trust_root_fields"
    )
    result = subprocess.run(
        [*_hermetic_pytest_prefix(output), selector],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["environment_contract"]["excluded_import_origins"].append(
        {
            "module": "common.evidence_graph",
            "source": {
                "scope": "repo",
                "path": "htt/src/common/evidence_graph.py",
            },
            "reason": "caller_requested_exemption",
        }
    )
    _reseal_environment_and_receipt(payload)

    with pytest.raises(EvidenceGraphError, match="exact fixed-point policy"):
        TestExecution.from_pytest_evidence(payload)


def test_ordinary_import_origin_omission_fails_exact_replay() -> None:
    builder = _load_builder()
    original = json.loads(
        (REPO_ROOT / "docs/generated/pr122_test_execution.json").read_text(
            encoding="utf-8"
        )
    )
    tampered = copy.deepcopy(original)
    origins = tampered["environment_contract"]["import_origins"]
    removed = [row for row in origins if row["module"].startswith("numpy")]
    assert removed
    tampered["environment_contract"]["import_origins"] = [
        row for row in origins if not row["module"].startswith("numpy")
    ]
    _reseal_environment_and_receipt(tampered)

    with pytest.raises(EvidenceGraphError, match="exact hermetic replay"):
        builder._assert_exact_pytest_replay(tampered, original)


def test_noncanonical_pytest_pin_exemption_source_cannot_be_hidden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from common import pytest_execution_evidence as plugin

    substitute = tmp_path / "release_evidence_pin.py"
    substitute.write_text("VALUE = 'substitute'\n", encoding="utf-8")
    fake = ModuleType("common.release_evidence_pin")
    fake.__file__ = str(substitute)
    monkeypatch.setitem(sys.modules, "common.release_evidence_pin", fake)

    with pytest.raises(pytest.UsageError, match="must not be imported"):
        plugin._import_origin_inventory(REPO_ROOT)


def test_canonical_pin_path_cannot_mask_replaced_module_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from common import pytest_execution_evidence as plugin

    fake = ModuleType("common.release_evidence_pin")
    fake.__file__ = str(PIN_SOURCE)
    monkeypatch.setitem(sys.modules, "common.release_evidence_pin", fake)

    with pytest.raises(pytest.UsageError, match="must not be imported"):
        plugin._import_origin_inventory(REPO_ROOT)


def test_release_pin_module_is_not_eagerly_imported() -> None:
    from common import pytest_execution_evidence as plugin

    assert "common.release_evidence_pin" not in sys.modules
    plugin._import_origin_inventory(REPO_ROOT)


def test_release_pin_path_alias_cannot_reenter_import_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from common import pytest_execution_evidence as plugin

    fake = ModuleType("attacker.pin_alias")
    fake.__file__ = str(PIN_SOURCE)
    monkeypatch.setitem(sys.modules, "attacker.pin_alias", fake)

    with pytest.raises(pytest.UsageError, match="loaded under an alias"):
        plugin._import_origin_inventory(REPO_ROOT)


def test_fileless_release_pin_object_cannot_hide_under_an_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from common import pytest_execution_evidence as plugin

    fake = ModuleType("common.release_evidence_pin")
    monkeypatch.setitem(sys.modules, "common.release_evidence_pin", fake)

    with pytest.raises(pytest.UsageError, match="must not be imported"):
        plugin._import_origin_inventory(REPO_ROOT)


def test_checked_hash_workspace_pyc_is_bypassed_by_isolated_prefix(
    tmp_path: Path,
) -> None:
    module_root = tmp_path / "module-root"
    module_root.mkdir()
    source = module_root / "victim.py"
    benign_cache = tmp_path / "benign.pyc"
    malicious_cache = tmp_path / "malicious.pyc"
    source.write_text("VALUE = 'BENIGN_SOURCE'\n", encoding="utf-8")
    py_compile.compile(
        str(source),
        cfile=str(benign_cache),
        doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH,
    )
    source.write_text("VALUE = 'MALICIOUS_PYC'\n", encoding="utf-8")
    py_compile.compile(
        str(source),
        cfile=str(malicious_cache),
        doraise=True,
        invalidation_mode=py_compile.PycInvalidationMode.CHECKED_HASH,
    )
    source.write_text("VALUE = 'BENIGN_SOURCE'\n", encoding="utf-8")
    forged = benign_cache.read_bytes()[:16] + malicious_cache.read_bytes()[16:]
    workspace_cache = (
        source.parent / "__pycache__" / f"victim.{sys.implementation.cache_tag}.pyc"
    )
    workspace_cache.parent.mkdir()
    workspace_cache.write_bytes(forged)
    probe = (
        "import sys;"
        f"sys.path.insert(0,{str(module_root)!r});"
        "import victim;print(victim.VALUE)"
    )

    exposed = subprocess.run(
        [str(PYTHON), "-I", "-S", "-B", "-c", probe],
        text=True,
        capture_output=True,
        check=True,
    )
    assert exposed.stdout.strip() == "MALICIOUS_PYC"

    isolated_cache = tmp_path / "isolated-pycache"
    isolated_cache.mkdir()
    isolated = subprocess.run(
        [
            str(PYTHON),
            "-I",
            "-S",
            "-B",
            "-X",
            f"pycache_prefix={isolated_cache}",
            "-c",
            probe,
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    assert isolated.stdout.strip() == "BENIGN_SOURCE"
    assert not list(isolated_cache.rglob("*"))


def test_source_only_launcher_rejects_direct_cli_and_ignores_executable_pth(
    tmp_path: Path,
) -> None:
    direct = subprocess.run(
        [str(PYTHON), str(BUILDER), "--help"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert direct.returncode != 0
    assert "run_pr122_source_only.sh" in direct.stderr
    imported_builder = _load_builder()
    with pytest.raises(SystemExit, match="run_pr122_source_only.sh"):
        imported_builder.main(["--dry-run"])

    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    site_packages = PYTHON.parent.parent / "lib" / version / "site-packages"
    sentinel = tmp_path / "executable-pth-ran.txt"
    pth = site_packages / f"pr122_hostile_{os.getpid()}.pth"
    pth.write_text(
        "import os,pathlib; "
        "p=os.environ.get('PR122_PTH_ATTACK_SENTINEL'); "
        "p and pathlib.Path(p).write_text('executed', encoding='utf-8')\n",
        encoding="utf-8",
    )
    targets = (
        "scripts/codex_harness/build_claim_evidence_graph.py",
        "scripts/check_publication_claim_freeze.py",
        "scripts/build_external_audit_package.py",
    )
    try:
        for target in targets:
            result = subprocess.run(
                [str(SOURCE_ONLY_LAUNCHER), target, "--help"],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
                env={
                    **os.environ,
                    "PATH": str(tmp_path),
                    "TMPDIR": str(tmp_path),
                    "PYTHONPATH": str(tmp_path / "attacker"),
                    "PYTEST_ADDOPTS": "--maxfail=1",
                    "PYTEST_PLUGINS": "attacker_plugin",
                    "PR122_PTH_ATTACK_SENTINEL": str(sentinel),
                },
            )
            assert result.returncode == 0, result.stdout + result.stderr
            assert "usage:" in result.stdout
            assert not sentinel.exists()
    finally:
        pth.unlink(missing_ok=True)
