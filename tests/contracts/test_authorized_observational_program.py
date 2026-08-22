from __future__ import annotations

from copy import deepcopy
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest
import yaml

from common.data_identity import evaluate_lane_identity, load_lane_registry


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/codex_harness/run_authorized_observational_program.py"
PR289_TEST = ROOT / "tests/contracts/test_data_identity_registry_v2.py"
REGISTRY = (
    ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", "-C", str(root), *args],
        check=True,
        text=True,
        capture_output=True,
        env={
            "HOME": "/nonexistent",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        },
    )
    return completed.stdout.strip()


@pytest.fixture
def case_factory(tmp_path: Path):
    module = _load("authorized_observational_program", RUNNER)
    pr289 = _load("pr289_identity_helpers", PR289_TEST)
    counter = 0

    def build(worker_source: str = "raise SystemExit(0)\n", *, timeout: int = 5):
        nonlocal counter
        counter += 1
        repo = tmp_path / f"repo-{counter}"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "fixture@example.invalid")
        _git(repo, "config", "user.name", "fixture")
        registry = repo / REGISTRY.relative_to(ROOT)
        registry.parent.mkdir(parents=True)
        shutil.copyfile(REGISTRY, registry)
        worker = repo / "scripts/codex_harness/run_authorized_observational_program.py"
        worker.parent.mkdir(parents=True)
        worker.write_text(worker_source, encoding="utf-8")
        plan = repo / "docs/plan.yaml"
        plan.parent.mkdir(parents=True, exist_ok=True)
        plan.write_text(
            yaml.safe_dump(
                {
                    "attended_execution_plan": {
                        "analysis_plan_id": "plan:PR290-PLANCK-LOWELL-V1",
                        "bayesian_inference": False,
                        "execution_mode": "identity_only",
                        "lane": "PLANCK",
                        "worker_arguments": ["--identity-worker"],
                        "worker_path": "scripts/codex_harness/run_authorized_observational_program.py",
                    }
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        _git(repo, "add", ".")
        _git(repo, "commit", "-qm", "fixture")
        descriptor = pr289._valid_descriptor(tmp_path / f"data-{counter}")
        decision = evaluate_lane_identity(
            registry=load_lane_registry(REGISTRY),
            lane_id="PLANCK",
            descriptor=descriptor,
            inspected_at_utc=pr289.STAMP_A,
        )
        admission = tmp_path / f"admission-{counter}.json"
        admission.write_text(
            json.dumps(decision.as_payload(), sort_keys=True), encoding="ascii"
        )
        output = tmp_path / f"output-{counter}"
        prepared = module.prepare_execution(
            lane="PLANCK",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=output,
            timeout_seconds=timeout,
            root=repo,
        )
        return module, repo, plan, worker, admission, output, prepared

    return build


def test_ATT_001_wrong_confirmation_rejected_before_spawn(
    case_factory, monkeypatch
) -> None:
    module, _, _, _, _, output, prepared = case_factory()
    called = False

    def forbidden(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("worker spawned")

    monkeypatch.setattr(module, "_spawn_worker", forbidden)
    with pytest.raises(module.ObservationalProgramError, match="confirmation"):
        module.execute_prepared(prepared, "sha256:" + "0" * 64)
    assert called is False and not output.exists()


def test_ATT_002_dirty_candidate_is_rejected(case_factory) -> None:
    module, repo, _, worker, admission, output, _ = case_factory()
    worker.write_text("raise SystemExit(0)\n# dirty\n", encoding="utf-8")
    with pytest.raises(module.ObservationalProgramError, match="clean"):
        module.prepare_execution(
            lane="PLANCK",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=output,
            timeout_seconds=5,
            root=repo,
        )


def test_ATT_003_only_PLANCK_is_accepted(case_factory) -> None:
    module, repo, _, _, admission, output, _ = case_factory()
    with pytest.raises(module.ObservationalProgramError, match="PLANCK"):
        module.prepare_execution(
            lane="CF4",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=output,
            timeout_seconds=5,
            root=repo,
        )


def test_ATT_004_noncanonical_PR289_admissions_are_rejected(
    case_factory, tmp_path: Path
) -> None:
    module, repo, _, _, admission, output, _ = case_factory()
    accepted = json.loads(admission.read_text(encoding="ascii"))
    refused = {
        **accepted,
        "status": "REJECTED_NOT_PRESENT",
        "reasons": ["missing"],
        "records": [],
        "lane_admission_bundle_id": None,
    }
    incomplete = deepcopy(accepted)
    incomplete["records"] = incomplete["records"][:-1]
    reordered = deepcopy(accepted)
    assert len(reordered["records"]) >= 2
    reordered["records"] = list(reversed(reordered["records"]))
    wrong_bundle = {**accepted, "lane_admission_bundle_id": "sha256:" + "0" * 64}
    for index, payload in enumerate((refused, incomplete, reordered, wrong_bundle)):
        probe = tmp_path / f"invalid-{index}.json"
        probe.write_text(json.dumps(payload, sort_keys=True), encoding="ascii")
        with pytest.raises(module.ObservationalProgramError, match="admission"):
            module.prepare_execution(
                lane="PLANCK",
                plan_path="docs/plan.yaml",
                admission_path=probe,
                output_dir=output,
                timeout_seconds=5,
                root=repo,
            )


def test_ATT_005_every_frozen_input_changes_the_acceptance_hash(case_factory) -> None:
    module, _, _, _, _, _, prepared = case_factory()
    baseline = prepared["acceptance_payload"]
    fields = (
        "candidate_commit",
        "candidate_tree",
        "admission_decision_sha256",
        "analysis_plan_sha256",
        "worker_sha256",
        "environment_contract_sha256",
        "output_dir",
        "timeout_seconds",
    )
    observed = set()
    for field in fields:
        changed = dict(baseline)
        changed[field] = (
            6 if field == "timeout_seconds" else str(changed[field]) + "-changed"
        )
        observed.add(module.content_hash(changed))
    assert len(observed) == len(fields)
    assert prepared["acceptance_hash"] not in observed


def test_ATT_006_worker_escape_tests_path_and_shell_shape_are_rejected(
    case_factory,
) -> None:
    module, repo, _, _, _, _, _ = case_factory()
    for payload in (
        {"worker_path": "../escape.py"},
        {"worker_path": "tests/worker.py"},
        {"worker_path": "scripts/worker.sh"},
        {"shell": True},
    ):
        with pytest.raises(module.ObservationalProgramError):
            module.validate_plan_values(
                {
                    "analysis_plan_id": "plan:PR290-PLANCK-LOWELL-V1",
                    "bayesian_inference": False,
                    "execution_mode": "identity_only",
                    "lane": "PLANCK",
                    "worker_arguments": ["--identity-worker"],
                    "worker_path": "scripts/codex_harness/run_authorized_observational_program.py",
                    **payload,
                },
                root=repo,
            )


def test_ATT_007_worker_receives_only_the_clean_environment(
    case_factory, monkeypatch
) -> None:
    source = "import json, os\nfrom pathlib import Path\nPath(os.environ['HTT_ATTENDED_OUTPUT_DIR'], 'env.json').write_text(json.dumps(dict(os.environ), sort_keys=True))\n"
    module, _, _, _, _, output, prepared = case_factory(source)
    monkeypatch.setenv("PYTHONPATH", "/tmp/hostile")
    monkeypatch.setenv("LD_PRELOAD", "/tmp/hostile.so")
    monkeypatch.setenv("GIT_OBJECT_DIRECTORY", "/tmp/objects")
    terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
    environment = json.loads((output / "env.json").read_text(encoding="utf-8"))
    assert terminal["state"] == "SUCCEEDED"
    assert set(environment) == set(prepared["environment"])
    assert environment["PYTHONNOUSERSITE"] == "1"


def test_ATT_008_concurrent_output_lock_is_rejected(case_factory) -> None:
    module, _, _, _, _, output, prepared = case_factory()
    output.mkdir(mode=0o700)
    with (output / ".attended.lock").open("a+b") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(module.ObservationalProgramError, match="locked"):
            module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert not (output / "start.json").exists()

    module, _, _, _, _, output, prepared = case_factory()
    output.mkdir(mode=0o700)
    (output / "preexisting.bin").write_bytes(b"not this run")
    with pytest.raises(module.ObservationalProgramError, match="dedicated"):
        module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert not (output / "start.json").exists()

    module, _, _, _, _, output, prepared = case_factory()
    output.mkdir(mode=0o755)
    output.chmod(0o755)
    with pytest.raises(module.ObservationalProgramError, match="0700"):
        module.execute_prepared(prepared, prepared["acceptance_hash"])


def test_ATT_009_timeout_writes_terminal_and_preserves_start(case_factory) -> None:
    module, _, _, _, _, output, prepared = case_factory(
        "import time\ntime.sleep(2)\n", timeout=1
    )
    terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert terminal["state"] == "TIMED_OUT"
    assert json.loads((output / "start.json").read_text())["state"] == "STARTED"
    assert json.loads((output / "terminal.json").read_text()) == terminal


def test_ATT_010_nonzero_and_signal_exits_write_terminal(case_factory) -> None:
    for source, state in (
        ("raise SystemExit(5)\n", "FAILED"),
        ("import os, signal\nos.kill(os.getpid(), signal.SIGTERM)\n", "SIGNALED"),
        (
            "import os\nfrom pathlib import Path\n"
            "Path(os.environ['HTT_ATTENDED_OUTPUT_DIR'], 'bad-link').symlink_to('/tmp')\n",
            "FAILED",
        ),
    ):
        module, _, _, _, _, output, prepared = case_factory(source)
        terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
        assert terminal["state"] == state
        assert (output / "terminal.json").is_file()


def test_ATT_011_success_observes_start_before_worker_and_then_terminal(
    case_factory,
) -> None:
    source = "import os\nfrom pathlib import Path\nout = Path(os.environ['HTT_ATTENDED_OUTPUT_DIR'])\nassert (out / 'start.json').is_file()\n(out / 'worker.ok').write_text('ok')\n"
    module, _, _, _, _, output, prepared = case_factory(source)
    terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert terminal["state"] == "SUCCEEDED"
    assert (output / "start.json").stat().st_mtime_ns <= (
        output / "worker.ok"
    ).stat().st_mtime_ns
    assert (output / "terminal.json").stat().st_mtime_ns >= (
        output / "worker.ok"
    ).stat().st_mtime_ns


def test_ATT_012_preflight_failure_never_spawns_or_opens_data(
    case_factory, monkeypatch
) -> None:
    module, repo, plan, _, admission, output, _ = case_factory()
    with pytest.raises(module.ObservationalProgramError, match="disjoint"):
        module.prepare_execution(
            lane="PLANCK",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=repo.parent,
            timeout_seconds=5,
            root=repo,
        )
    payload = yaml.safe_load(plan.read_text(encoding="utf-8"))
    payload["attended_execution_plan"]["analysis_plan_id"] = "plan:wrong"
    plan.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    _git(repo, "add", "docs/plan.yaml")
    _git(repo, "commit", "-qm", "invalid plan")
    monkeypatch.setattr(
        module, "_spawn_worker", lambda *_a, **_k: pytest.fail("worker spawned")
    )
    with pytest.raises(module.ObservationalProgramError, match="analysis plan"):
        module.prepare_execution(
            lane="PLANCK",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=output,
            timeout_seconds=5,
            root=repo,
        )
    assert not output.exists()


def _science_case(
    case_factory,
    tmp_path: Path,
    *,
    worker_source: str = "raise SystemExit(0)\n",
    timeout: int = 5,
):
    module, repo, plan, _, admission, output, _ = case_factory()
    science_worker = repo / "scripts/observed_runs/run_planck_pr3.py"
    science_worker.parent.mkdir(parents=True, exist_ok=True)
    science_worker.write_text(worker_source, encoding="utf-8")
    payload = yaml.safe_load(plan.read_text(encoding="utf-8"))
    payload["attended_execution_plan"].update(
        {
            "execution_mode": "planck_pr3_lowell_operator",
            "worker_path": "scripts/observed_runs/run_planck_pr3.py",
            "worker_arguments": ["--run-admitted"],
        }
    )
    plan.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "science fixture")
    data_root = tmp_path / f"science-data-{repo.name}"
    data_root.mkdir()
    prepared = module.prepare_execution(
        lane="PLANCK",
        plan_path="docs/plan.yaml",
        admission_path=admission,
        output_dir=output,
        timeout_seconds=timeout,
        data_root=data_root,
        root=repo,
    )
    return module, repo, plan, science_worker, admission, output, data_root, prepared


def test_PR306_science_plan_binds_exact_runtime_data_root_and_worker(
    case_factory, tmp_path: Path
) -> None:
    module, _, _, _, _, _, data_root, prepared = _science_case(case_factory, tmp_path)
    acceptance = prepared["acceptance_payload"]
    assert acceptance["science_execution"] is True
    assert acceptance["data_root"] == str(data_root.resolve())
    assert acceptance["worker_path"] == "scripts/observed_runs/run_planck_pr3.py"
    assert acceptance["science_runtime_contract_sha256"] == module.content_hash(
        prepared["science_runtime_contract"]
    )
    runtime = prepared["science_runtime_contract"]
    assert set(runtime["modules"]) == set(module.SCIENCE_RUNTIME_MODULES)
    assert set(runtime["distributions"]) == set(module.SCIENCE_DISTRIBUTIONS)
    assert all(
        row["origin_sha256"].startswith("sha256:")
        for row in runtime["modules"].values()
    )
    assert runtime["thread_controls"] == module.THREAD_CONTROLS
    assert all(prepared["environment"][key] == "1" for key in module.THREAD_CONTROLS)


def test_PR306_science_runtime_is_rechecked_before_spawn(
    case_factory, tmp_path: Path, monkeypatch
) -> None:
    module, _, _, _, _, output, _, prepared = _science_case(case_factory, tmp_path)
    changed = dict(prepared["science_runtime_contract"])
    changed["python_version"] = "drifted"
    monkeypatch.setattr(module, "_science_runtime_contract", lambda: changed)
    with pytest.raises(module.ObservationalProgramError, match="runtime changed"):
        module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert not output.exists()


def test_PR306_science_data_root_rejects_symlink_components(
    case_factory, tmp_path: Path
) -> None:
    module, repo, _, _, admission, output, data_root, _ = _science_case(
        case_factory, tmp_path
    )
    linked_parent = tmp_path / "linked-science-parent"
    linked_parent.symlink_to(data_root.parent, target_is_directory=True)
    linked_root = linked_parent / data_root.name
    with pytest.raises(module.ObservationalProgramError, match="symlink-based"):
        module.prepare_execution(
            lane="PLANCK",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=output,
            timeout_seconds=5,
            data_root=linked_root,
            root=repo,
        )


def test_PR306_timeout_terminates_the_worker_process_group(case_factory) -> None:
    source = (
        "import os, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
        "Path(os.environ['HTT_ATTENDED_OUTPUT_DIR'], 'child.pid').write_text(str(child.pid))\n"
        "time.sleep(60)\n"
    )
    module, _, _, _, _, output, prepared = case_factory(source, timeout=1)
    terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert terminal["state"] == "TIMED_OUT"
    child_pid = int((output / "child.pid").read_text())
    for _ in range(20):
        if not Path(f"/proc/{child_pid}").exists():
            break
        time.sleep(0.05)
    assert not Path(f"/proc/{child_pid}").exists()


def test_PR306_worker_logs_and_large_outputs_are_stream_hashed(case_factory) -> None:
    source = (
        "import os, sys\n"
        "from pathlib import Path\n"
        "out = Path(os.environ['HTT_ATTENDED_OUTPUT_DIR'])\n"
        "sys.stdout.buffer.write(b'o' * 1048577)\n"
        "sys.stderr.buffer.write(b'e' * 1048579)\n"
        "(out / 'large.bin').write_bytes(b'x' * 2097163)\n"
    )
    module, _, _, _, _, output, prepared = case_factory(source)
    terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert terminal["state"] == "SUCCEEDED"
    assert (output / "stdout.log").stat().st_size == 1048577
    assert (output / "stderr.log").stat().st_size == 1048579
    assert (
        terminal["stdout_sha256"]
        == "sha256:" + hashlib.sha256((output / "stdout.log").read_bytes()).hexdigest()
    )
    assert (
        terminal["output_hashes"]["large.bin"]
        == "sha256:" + hashlib.sha256(b"x" * 2097163).hexdigest()
    )


@pytest.mark.parametrize("terminal_state", ["FAILED", "TIMED_OUT"])
def test_PR306_science_failure_after_data_open_is_recorded_truthfully(
    case_factory, tmp_path: Path, terminal_state: str
) -> None:
    tail = "raise SystemExit(9)\n" if terminal_state == "FAILED" else "time.sleep(60)\n"
    source = (
        "import json, os, time\n"
        "from pathlib import Path\n"
        "marker = Path(os.environ['HTT_ATTENDED_DATA_OPEN_MARKER'])\n"
        "marker.write_text(json.dumps({'state': 'OBSERVED_DATA_OPEN_ATTEMPTED'}))\n"
        + tail
    )
    module, _, _, _, _, output, _, prepared = _science_case(
        case_factory,
        tmp_path,
        worker_source=source,
        timeout=1 if terminal_state == "TIMED_OUT" else 5,
    )
    terminal = module.execute_prepared(prepared, prepared["acceptance_hash"])
    assert terminal["state"] == terminal_state
    assert terminal["observed_data_opened"] is True
    assert terminal["observed_science_executed"] is True
    persisted = json.loads((output / "terminal.json").read_text(encoding="ascii"))
    assert persisted["observed_data_opened"] is True


def test_PR306_unhashable_execution_mode_is_blocked(case_factory) -> None:
    module, repo, plan, _, admission, output, _ = case_factory()
    payload = yaml.safe_load(plan.read_text(encoding="utf-8"))
    payload["attended_execution_plan"]["execution_mode"] = ["identity_only"]
    plan.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    _git(repo, "add", "docs/plan.yaml")
    _git(repo, "commit", "-qm", "invalid execution mode")
    with pytest.raises(module.ObservationalProgramError, match="Planck plans"):
        module.prepare_execution(
            lane="PLANCK",
            plan_path="docs/plan.yaml",
            admission_path=admission,
            output_dir=output,
            timeout_seconds=5,
            root=repo,
        )
