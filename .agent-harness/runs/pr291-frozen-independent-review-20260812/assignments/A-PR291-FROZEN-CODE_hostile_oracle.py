#!/usr/bin/env python3
"""Assignment-local hostile oracle for frozen PR-291 review.

This is deliberately outside the candidate tree.  It invokes only public or
explicitly bound runner helpers against disposable paths and reports a compact
machine-readable verdict.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import types


ROOT = Path(__file__).resolve().parents[4]
BASE = "06ac20605ebc371b0f97ad6e91c802a51a9bf764"
CANDIDATE = "67076abbfce5e6bf549f1282c95729bfe89b4be8"
SEAL = ROOT / ".prguard/runtime/PR291_VALIDATED_CANDIDATE_SEAL.json"
RECEIPT = ROOT / "docs/research_program/post_pr275/data_runs/cf4/PR291_NONEXECUTION_RECEIPT.json"
RUNNER = ROOT / "scripts/codex_harness/run_pr291_cf4_lane.py"


def _run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True)


def _expect_failure(label: str, fn) -> None:
    try:
        fn()
    except RuntimeError:
        return
    raise AssertionError(f"{label}: unsafe path was accepted")


def _load_runner():
    script_dir = str(RUNNER.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location("pr291_review_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise AssertionError("runner loader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    outcomes: dict[str, str] = {}
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    assert seal["base_sha"] == BASE
    assert seal["candidate_sha"] == CANDIDATE
    assert _run("git", "merge-base", BASE, CANDIDATE).strip() == BASE
    assert _run("git", "rev-parse", CANDIDATE + "^{tree}").strip() == seal["candidate_tree_sha"]
    digest = hashlib.sha256(
        subprocess.check_output(
            ["git", "diff", "--full-index", BASE, CANDIDATE], cwd=ROOT
        )
    ).hexdigest()
    assert digest == seal["diff_sha256"]
    outcomes["candidate_and_exact_base"] = "pass"

    ast.parse(RUNNER.read_text(encoding="utf-8"), feature_version=(3, 10))
    outcomes["python_310_parse"] = "pass"

    runner = _load_runner()
    fake = types.ModuleType("common.observed_lane_activation")
    before = sys.modules.get("common.observed_lane_activation")
    sys.modules["common.observed_lane_activation"] = fake
    try:
        first = runner._encoded(runner._build(ROOT))
        second = runner._encoded(runner._build(ROOT))
        assert first == second == RECEIPT.read_bytes()
        assert sys.modules["common.observed_lane_activation"] is fake
    finally:
        if before is None:
            sys.modules.pop("common.observed_lane_activation", None)
        else:
            sys.modules["common.observed_lane_activation"] = before
    payload = json.loads(first)
    assert payload["terminal"] == "BLOCKED_PREDECESSOR_FINAL_SUCCESS"
    assert payload["observed_data_executed"] is False
    assert payload["numeric_outputs_written"] == []
    outcomes["preloaded_module_and_deterministic_nonexecution"] = "pass"

    with tempfile.TemporaryDirectory(prefix="pr291-hostile-") as temporary:
        root = Path(temporary) / "root"
        root.mkdir()
        parent = root / "receipts"
        parent.mkdir()
        observed = root / "observed-results"
        output = parent / "receipt.json"
        runner._validate_output_destinations(
            root=root, output=output, observed_result_directory=observed,
            require_existing=False,
        )
        outcomes["regular_parent"] = "pass"

        outside = Path(temporary) / "outside"
        outside.mkdir()
        (root / "link-parent").symlink_to(outside, target_is_directory=True)
        _expect_failure(
            "symlink_parent",
            lambda: runner._validate_output_destinations(
                root=root, output=root / "link-parent" / "r.json",
                observed_result_directory=observed, require_existing=False,
            ),
        )
        _expect_failure(
            "escape_traversal",
            lambda: runner._validate_output_destinations(
                root=root, output=root / ".." / "outside" / "r.json",
                observed_result_directory=observed, require_existing=False,
            ),
        )
        outcomes["parent_link_and_escape_traversal"] = "pass"

        target = outside / "linked.json"
        target.write_text("x", encoding="ascii")
        os.link(target, output)
        _expect_failure(
            "hardlink_output",
            lambda: runner._validate_output_destinations(
                root=root, output=output, observed_result_directory=observed,
                require_existing=False,
            ),
        )
        output.unlink()
        os.mkfifo(output)
        _expect_failure(
            "fifo_output",
            lambda: runner._validate_output_destinations(
                root=root, output=output, observed_result_directory=observed,
                require_existing=False,
            ),
        )
        output.unlink()
        outcomes["hardlink_and_fifo_output"] = "pass"

        observed.mkdir()
        _expect_failure(
            "observed_directory",
            lambda: runner._validate_output_destinations(
                root=root, output=output, observed_result_directory=observed,
                require_existing=False,
            ),
        )
        observed.rmdir()
        atomic = b'{"deterministic":true}\n'
        runner._atomic_write(
            output, atomic, root=root, observed_result_directory=observed
        )
        info = output.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
        assert output.read_bytes() == atomic
        outcomes["observed_absence_and_atomic_write"] = "pass"

    print(json.dumps({"oracle": "A-PR291-FROZEN-CODE", "outcomes": outcomes}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
