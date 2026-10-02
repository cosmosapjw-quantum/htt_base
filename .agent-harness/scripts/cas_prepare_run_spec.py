#!/usr/bin/env python3
"""Expand opt-in Python scripts into a legacy CAS run spec without executing it.

Run from the repository root with --contract, --run-spec and a new --out path,
then pass that output to cas_gate.py run-adjudicate. The source-bound adjudicator
remains unchanged. Legacy argv specs are validated and copied byte-for-byte.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from _harness import load_json, root
from cas_gate import _required_axes, _validate_run_spec


def prepare_run_spec(
    repo: Path, run_spec: object, required: list[str]
) -> tuple[dict, list[str]]:
    """Return legacy JSON and errors, leaving the caller's input untouched."""
    repo = repo.resolve()
    if not isinstance(run_spec, dict) or not isinstance(run_spec.get("axes"), dict):
        _, errors = _validate_run_spec(repo, run_spec, required)
        return {}, errors
    prepared = copy.deepcopy(run_spec)
    for axis, entry in prepared["axes"].items():
        if not isinstance(entry, dict) or "python_script" not in entry:
            continue
        if "argv" in entry or "shell" in entry:
            return {}, [f"axes.{axis} must select python_script without argv or shell"]
        script = entry["python_script"]
        if not isinstance(script, str) or not script or "\x00" in script:
            return {}, [f"axes.{axis}.python_script must be a repo-relative .py file"]
        relative = Path(script)
        path = (repo / relative).resolve()
        if (relative.is_absolute() or not path.is_relative_to(repo)
                or path.suffix != ".py" or not path.is_file()):
            return {}, [f"axes.{axis}.python_script must be an existing repo-relative .py file"]
        if axis == "sage_singular":
            argv = ["sage", "-python", "-B", str(path)]
        else:
            python = repo / "venv" / "bin" / "python"
            interpreter = str(python) if axis == "sympy" and python.is_file() else sys.executable
            argv = [interpreter, "-B", str(path)]
        del entry["python_script"]
        entry["argv"] = argv
        entry.setdefault("cwd", ".")
    # The original adjudicator owns schema, axes, cwd confinement, timeout,
    # shell prohibition and independent-command validation.
    _, errors = _validate_run_spec(repo, prepared, required)
    return prepared, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--run-spec", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="new output file; never overwritten")
    args = parser.parse_args()
    repo = (args.repo_root or root()).resolve()
    try:
        contract = load_json(repo / args.contract)
        required = _required_axes(contract)
        source = (repo / args.run_spec).read_bytes()
        run_spec = json.loads(source)
        prepared, errors = prepare_run_spec(repo, run_spec, required)
        if errors:
            raise ValueError("; ".join(errors))
        output = source if prepared == run_spec else (json.dumps(prepared, indent=2) + "\n").encode("utf-8")
        with (repo / args.out).open("xb") as handle:
            handle.write(output)
    except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as exc:
        print(f"run-spec preparation failed: {exc}", file=sys.stderr)
        return 2
    print(f"Prepared legacy run spec: {repo / args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
