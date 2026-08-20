#!/usr/bin/env python3
"""Run PR-280 declarative profiles without promoting scientific claims."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
for _source_root in (
    REPO_ROOT / "htt/src",
    REPO_ROOT / "htt",
    REPO_ROOT / "htt/htt",
):
    if str(_source_root) not in sys.path:
        sys.path.insert(0, str(_source_root))

from common.harness_profiles_v4 import (  # noqa: E402
    HarnessProfile,
    HarnessProfileError,
    load_profile_manifest,
    make_smoke_binding_record,
    sha256_file,
)
from common.evidence_graph import TestExecution  # noqa: E402


MANIFEST = REPO_ROOT / "docs/research_program/post_pr275/harness_profiles_v4.yaml"
DEFAULT_VENV_PYTHON = REPO_ROOT / "venv/bin/python"
SOURCE_ROOTS = (
    REPO_ROOT / "htt/src",
    REPO_ROOT / "htt",
    REPO_ROOT / "htt/htt",
    REPO_ROOT,
)
CHANGED_DIFF_FILTER = "ACDMRTUXB"


def default_python() -> str:
    if DEFAULT_VENV_PYTHON.is_file():
        return str(DEFAULT_VENV_PYTHON)
    return sys.executable


def _receipt_python() -> str:
    """Prefer a prefix-owned pytest installation for authoritative receipts."""

    if DEFAULT_VENV_PYTHON.is_file():
        return str(DEFAULT_VENV_PYTHON)
    common_dir = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if common_dir.returncode == 0:
        shared_python = Path(common_dir.stdout.strip()).parent / "venv/bin/python"
        if shared_python.is_file():
            return str(shared_python)
    return sys.executable


def _clean_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name == "PYTHONPATH" or name.startswith("PYTEST_"):
            environment.pop(name, None)
    return environment


def _ordinary_pytest_command(profile: HarnessProfile, python: str) -> list[str]:
    return profile.pytest_command(python)


def _ordinary_pytest_environment() -> dict[str, str]:
    environment = _clean_environment()
    environment["PYTHONPATH"] = os.pathsep.join(str(path) for path in SOURCE_ROOTS)
    return environment


def _hermetic_pytest_command(
    profile: HarnessProfile,
    *,
    python: str,
    evidence_output: Path,
    cache_dir: Path,
) -> list[str]:
    path_probe = subprocess.run(
        [
            python,
            "-c",
            (
                "import json,sys;"
                "print(json.dumps({'sys_path':sys.path,'prefix':sys.prefix,"
                "'exec_prefix':sys.exec_prefix}))"
            ),
        ],
        cwd=REPO_ROOT,
        env=_clean_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if path_probe.returncode != 0:
        raise HarnessProfileError("cannot resolve dependency paths for isolated profile")
    try:
        path_contract = json.loads(path_probe.stdout)
    except json.JSONDecodeError as exc:
        raise HarnessProfileError("Python dependency path probe is malformed") from exc
    if not isinstance(path_contract, dict):
        raise HarnessProfileError("Python dependency path probe is malformed")
    raw_paths = path_contract.get("sys_path")
    prefix = path_contract.get("prefix")
    exec_prefix = path_contract.get("exec_prefix")
    if not isinstance(raw_paths, list) or not all(
        isinstance(value, str) for value in raw_paths
    ) or not isinstance(prefix, str) or not isinstance(exec_prefix, str):
        raise HarnessProfileError("Python dependency path probe is malformed")
    dependency_paths: list[str] = []
    for value in raw_paths:
        if not value:
            continue
        candidate = Path(value)
        if not candidate.is_absolute() or not candidate.exists():
            continue
        resolved = candidate.resolve()
        try:
            resolved.relative_to(REPO_ROOT.resolve())
        except ValueError:
            rendered = str(resolved)
            if rendered not in dependency_paths:
                dependency_paths.append(rendered)
    bootstrap_paths = [*(str(path) for path in SOURCE_ROOTS), *dependency_paths]
    bootstrap = (
        "import os,runpy,sys;"
        f"sys.prefix={prefix!r};sys.exec_prefix={exec_prefix!r};"
        f"sys.path[:]=list(dict.fromkeys({bootstrap_paths!r}+sys.path));"
        "[os.environ.pop(k,None) for k in "
        "('PYTHONPATH','PYTEST_ADDOPTS','PYTEST_PLUGINS')];"
        "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';"
        "sys.argv[0]='pytest';"
        "runpy.run_module('pytest',run_name='__main__')"
    )
    return [
        python,
        "-I",
        "-S",
        "-B",
        "-X",
        f"pycache_prefix={cache_dir}",
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
        "-o",
        "addopts=",
        *profile.pytest_args,
        "--evidence-output",
        str(evidence_output),
        *profile.selectors,
    ]


def _git_identity() -> tuple[str, str]:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if status.returncode != 0 or status.stdout:
        raise HarnessProfileError(
            "authoritative profile evidence requires a clean committed worktree"
        )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    return commit, tree


def _repo_output_path(raw: str, label: str) -> Path:
    relative = Path(raw)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or any(part in {"", "."} for part in relative.parts)
    ):
        raise HarnessProfileError(f"{label} must be repository-relative")
    path = REPO_ROOT / relative
    try:
        path.resolve(strict=False).relative_to(REPO_ROOT.resolve())
    except ValueError as exc:
        raise HarnessProfileError(f"{label} escapes the repository") from exc
    current = REPO_ROOT
    for part in relative.parts[:-1]:
        current /= part
        if current.is_symlink():
            raise HarnessProfileError(f"{label} has a symlinked parent")
    if path.exists() or path.is_symlink():
        raise HarnessProfileError(f"{label} already exists: {relative}")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _verify_generated_evidence(python: str, evidence_path: Path) -> None:
    verifier = (
        "import json,sys;from pathlib import Path;"
        "from common.evidence_graph import "
        "verify_pytest_selector_inputs,verify_pytest_environment_inputs;"
        "payload=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'));"
        "root=Path(sys.argv[2]);"
        "verify_pytest_selector_inputs(root,payload);"
        "verify_pytest_environment_inputs(root,payload)"
    )
    completed = subprocess.run(
        [python, "-B", "-c", verifier, str(evidence_path), str(REPO_ROOT)],
        cwd=REPO_ROOT,
        env=_ordinary_pytest_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise HarnessProfileError(
            "generated pytest evidence failed same-interpreter validation: "
            + completed.stderr.strip()
        )


def _run_pytest_profile(
    profile: HarnessProfile,
    *,
    python: str,
    dry_run: bool,
    waiver_id: str | None,
    evidence_output: str | None,
    binding_output: str | None,
    pr_id: str | None,
) -> int:
    if evidence_output is None and (binding_output is not None or pr_id is not None):
        raise HarnessProfileError(
            "binding output and PR identity require an evidence output"
        )
    if binding_output is None and pr_id is not None:
        raise HarnessProfileError("PR identity requires a binding output")
    if waiver_id is not None:
        if profile.waiver_policy != "registered_non_receipt":
            raise HarnessProfileError(f"profile {profile.profile_id} forbids waivers")
        if evidence_output is not None or binding_output is not None:
            raise HarnessProfileError("waived runs cannot emit receipt evidence")
    if evidence_output is None:
        command = _ordinary_pytest_command(profile, python)
        print(shlex.join(command), flush=True)
        if dry_run:
            return 0
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=_ordinary_pytest_environment(),
            check=False,
        )
        return completed.returncode
    if not profile.receipt_eligible or waiver_id is not None:
        raise HarnessProfileError(f"profile {profile.profile_id} is not receipt eligible")
    if binding_output is not None and (
        not profile.smoke_status_eligible or not pr_id
    ):
        raise HarnessProfileError(
            "binding output requires the smoke profile and a PR identity"
        )
    evidence_path = _repo_output_path(evidence_output, "evidence output")
    binding_path = (
        None
        if binding_output is None
        else _repo_output_path(binding_output, "binding output")
    )
    if binding_path is not None and binding_path == evidence_path:
        raise HarnessProfileError("evidence and binding outputs must be distinct")
    commit, tree = _git_identity()
    with tempfile.TemporaryDirectory(prefix="htt-pr280-pycache-") as tmp:
        cache_dir = Path(tmp) / "cache"
        cache_dir.mkdir()
        command = _hermetic_pytest_command(
            profile,
            python=python,
            evidence_output=evidence_path,
            cache_dir=cache_dir,
        )
        print(shlex.join(command), flush=True)
        if dry_run:
            return 0
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=_clean_environment(),
            check=False,
        )
    if completed.returncode != 0:
        return completed.returncode
    payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    execution = TestExecution.from_pytest_evidence(payload)
    _verify_generated_evidence(python, evidence_path)
    if not execution.is_authoritative:
        raise HarnessProfileError("generated execution evidence is not authoritative")
    if binding_path is not None:
        relative_evidence = evidence_path.relative_to(REPO_ROOT).as_posix()
        manifest = load_profile_manifest(MANIFEST, repo_root=REPO_ROOT)
        record = make_smoke_binding_record(
            pr_id=str(pr_id),
            profile_id=profile.profile_id,
            manifest=manifest,
            evidence_path=relative_evidence,
            evidence_sha256=sha256_file(evidence_path),
            candidate_commit=commit,
            candidate_tree=tree,
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        )
        binding_path.write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


def _run_import_probe(
    profile: HarnessProfile,
    *,
    python: str,
    dry_run: bool,
    output: str | None,
) -> int:
    import_specs = [tuple(value.split("=", 1)) for value in profile.modules]
    probe = (
        "import hashlib,importlib,inspect,json,pathlib,sys;"
        f"root=pathlib.Path({str(REPO_ROOT)!r}).resolve();"
        f"sys.path[:0]={[str(REPO_ROOT), *(str(path) for path in SOURCE_ROOTS)]!r};"
        f"specs={import_specs!r};"
        "rows=[];"
        "\nfor name,relative in specs:\n"
        " module=importlib.import_module(name)\n"
        " raw=inspect.getsourcefile(module) or getattr(module,'__file__',None)\n"
        " path=pathlib.Path(raw).resolve() if raw else None\n"
        " expected=(root/relative).resolve()\n"
        " ok=bool(path and path==expected and path.is_file() and not path.is_symlink())\n"
        " rows.append({'module':name,'expected_source':relative,'source':str(path) if path else None,'sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path and path.is_file() else None,'source_layout':ok})\n"
        "print(json.dumps({'schema_version':'htt.active_import_provenance.v1','python_executable':sys.executable,'python_version':sys.version.split()[0],'isolated':bool(sys.flags.isolated),'rows':rows,'all_source_layout':all(r['source_layout'] for r in rows),'authority':'source_layout_import_diagnostic_only'},sort_keys=True))"
    )
    # The import lane proves exact repository origins, not dependency isolation.
    # Keep the selected interpreter's declared site packages available so a
    # source checkout without a local venv can still import modules such as
    # ``common``; every repository-owned target is then checked byte-for-byte.
    command = [python, "-B", "-c", probe]
    print(shlex.join(command), flush=True)
    if dry_run:
        return 0
    output_path = None if output is None else _repo_output_path(output, "probe output")
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=_clean_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    if completed.returncode != 0:
        return completed.returncode
    payload = json.loads(completed.stdout)
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_path is None:
        print(rendered, end="")
    else:
        output_path.write_text(rendered, encoding="utf-8")
    return 0 if payload["all_source_layout"] else 1


def _tool_status(tool: str, python: str) -> dict[str, object]:
    kind, separator, value = tool.partition(":")
    if not separator or not value:
        raise HarnessProfileError(f"malformed tool probe: {tool}")
    if kind == "executable":
        resolved = shutil.which(value)
        return {"tool": tool, "available": resolved is not None, "identity": resolved}
    if kind == "python-module":
        completed = subprocess.run(
            [
                python,
                "-B",
                "-c",
                (
                    "import importlib.metadata as md,importlib.util,json,sys;"
                    "name=sys.argv[1];spec=importlib.util.find_spec(name);"
                    "print(json.dumps({'origin':None if spec is None else spec.origin,"
                    "'version':None if spec is None else md.version(name)}));"
                    "sys.exit(0 if spec else 1)"
                ),
                value,
            ],
            cwd=REPO_ROOT,
            env=_clean_environment(),
            text=True,
            capture_output=True,
            check=False,
        )
        details: object = value
        if completed.returncode == 0:
            try:
                details = json.loads(completed.stdout)
            except json.JSONDecodeError:
                details = {"module": value, "probe_output": "malformed"}
        return {
            "tool": tool,
            "available": completed.returncode == 0,
            "identity": details,
        }
    if kind == "env-path":
        raw = os.environ.get(value)
        path = None if raw is None else Path(raw)
        return {
            "tool": tool,
            "available": bool(path and path.exists() and not path.is_symlink()),
            "identity": value,
        }
    if kind == "repo-path":
        path = REPO_ROOT / value
        return {
            "tool": tool,
            "available": path.exists() and not path.is_symlink(),
            "identity": value,
        }
    raise HarnessProfileError(f"unknown tool probe kind: {kind}")


def _run_tool_probe(
    profile: HarnessProfile,
    *,
    python: str,
    dry_run: bool,
    output: str | None,
) -> int:
    if dry_run:
        print("probe " + " ".join(profile.tools))
        return 0
    output_path = None if output is None else _repo_output_path(output, "probe output")
    rows = [_tool_status(tool, python) for tool in profile.tools]
    payload = {
        "schema_version": "htt.formal_tool_availability.v1",
        "profile_id": profile.profile_id,
        "axis_status": "AVAILABLE" if all(row["available"] for row in rows) else "UNAVAILABLE",
        "authority": "tool_availability_only_not_cas_validation",
        "tools": rows,
    }
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output_path is None:
        print(rendered, end="")
    else:
        output_path.write_text(rendered, encoding="utf-8")
    return 0 if payload["axis_status"] == "AVAILABLE" else 3


def _run_profile(args: argparse.Namespace) -> int:
    manifest = load_profile_manifest(MANIFEST, repo_root=REPO_ROOT)
    profile = manifest.profile(args.profile_id)
    python = args.python or (
        _receipt_python()
        if profile.kind == "pytest" and args.evidence_output is not None
        else default_python()
    )
    if profile.kind == "pytest":
        if args.output is not None:
            raise HarnessProfileError("pytest profiles use --evidence-output, not --output")
        return _run_pytest_profile(
            profile,
            python=python,
            dry_run=args.dry_run,
            waiver_id=args.waiver_id,
            evidence_output=args.evidence_output,
            binding_output=args.binding_output,
            pr_id=args.pr_id,
        )
    if any((args.waiver_id, args.evidence_output, args.binding_output, args.pr_id)):
        raise HarnessProfileError("non-pytest probes cannot emit execution receipts")
    if profile.kind == "import_probe":
        return _run_import_probe(
            profile, python=python, dry_run=args.dry_run, output=args.output
        )
    return _run_tool_probe(
        profile, python=python, dry_run=args.dry_run, output=args.output
    )


def _focused(args: argparse.Namespace) -> int:
    for profile_id in ("smoke", "active-import"):
        nested = argparse.Namespace(
            profile_id=profile_id,
            python=args.python,
            dry_run=args.dry_run,
            waiver_id=None,
            evidence_output=None,
            binding_output=None,
            pr_id=None,
            output=None,
        )
        result = _run_profile(nested)
        if result != 0:
            return result
    return 0


def _check() -> int:
    manifest = load_profile_manifest(MANIFEST, repo_root=REPO_ROOT)
    print(
        json.dumps(
            {
                "schema_version": manifest.manifest_id,
                "manifest_sha256": manifest.sha256,
                "profile_count": len(manifest.profiles),
                "claim_ceiling": "diagnostic_only",
            },
            sort_keys=True,
        )
    )
    return 0


def _list_profiles() -> int:
    manifest = load_profile_manifest(MANIFEST, repo_root=REPO_ROOT)
    for profile_id in sorted(manifest.profiles):
        profile = manifest.profile(profile_id)
        print(
            f"{profile_id}\t{profile.kind}\t"
            f"smoke_status_eligible={str(profile.smoke_status_eligible).lower()}\t"
            f"waiver_policy={profile.waiver_policy}"
        )
    return 0


def _changed_profiles(base: str) -> int:
    commands = (
        [
            "git",
            "diff",
            "--name-only",
            f"--diff-filter={CHANGED_DIFF_FILTER}",
            "-z",
            f"{base}...HEAD",
        ],
        [
            "git",
            "diff",
            "--name-only",
            f"--diff-filter={CHANGED_DIFF_FILTER}",
            "-z",
            "HEAD",
        ],
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
    )
    paths_set: set[str] = set()
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise HarnessProfileError(f"cannot resolve changed surface from {base}")
        paths_set.update(
            raw.decode("utf-8")
            for raw in completed.stdout.split(b"\0")
            if raw
        )
    paths = tuple(sorted(paths_set))
    manifest = load_profile_manifest(MANIFEST, repo_root=REPO_ROOT)
    print(
        json.dumps(
            {
                "schema_version": "htt.changed_surface_selection.v4",
                "base": base,
                "paths": paths,
                "profiles": manifest.profiles_for_paths(paths),
                "includes_worktree": True,
                "ruleset_mutation": "not_performed_requires_G-CI-H",
                "claim_ceiling": "diagnostic_only",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("list")
    changed = sub.add_parser("changed")
    changed.add_argument("--base", required=True)
    profile = sub.add_parser("profile")
    profile.add_argument("profile_id")
    profile.add_argument("--python")
    profile.add_argument("--dry-run", action="store_true")
    profile.add_argument("--waiver-id")
    profile.add_argument("--evidence-output")
    profile.add_argument("--binding-output")
    profile.add_argument("--pr-id")
    profile.add_argument("--output")
    focused = sub.add_parser("focused")
    focused.add_argument("--python")
    focused.add_argument("--dry-run", action="store_true")
    package = sub.add_parser("package")
    package.add_argument("--python")
    package.add_argument("--dry-run", action="store_true")
    sub.add_parser("inventory-check")
    sub.add_parser("inventory-structure-check")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "check":
            return _check()
        if args.command == "list":
            return _list_profiles()
        if args.command == "changed":
            return _changed_profiles(args.base)
        if args.command == "focused":
            return _focused(args)
        if args.command == "package":
            args.profile_id = "package"
            args.waiver_id = None
            args.evidence_output = None
            args.binding_output = None
            args.pr_id = None
            args.output = None
            return _run_profile(args)
        if args.command == "inventory-check":
            from common.failure_inventory_v4 import validate_inventory_artifacts

            validate_inventory_artifacts(REPO_ROOT)
            print("PR-280 inventory artifacts valid")
            return 0
        if args.command == "inventory-structure-check":
            from common.failure_inventory_v4 import validate_inventory_artifacts

            receipt = validate_inventory_artifacts(
                REPO_ROOT, require_closeout_acceptance=False
            )
            print(
                "PR-280 inventory artifacts structurally valid; "
                f"active_core_count={receipt['active_core_count']}"
            )
            return 0
        return _run_profile(args)
    except (HarnessProfileError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"PR-280 harness error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
