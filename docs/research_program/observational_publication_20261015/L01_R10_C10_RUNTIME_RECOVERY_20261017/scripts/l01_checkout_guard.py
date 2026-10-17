"""Fail-closed checkout preflight for HTT L01 stacked GitHub research branches.

Read-only: validates the exact checked-out commit and executable imports before
any computation or network data acquisition. It never changes Git configuration.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

EXPECTED_REF = "origin/research/htt-sixpaper-p2-l01-r10c10-runtime-recovery-20261017"
PROGRAMME = Path("docs/research_program/observational_publication_20261015")
BASE = PROGRAMME / "L01_R8_C8_TWO_MASK_STABILITY_20261017"
PRIOR = PROGRAMME / "R8_SPIN2_S02_COHERENT_20261017"
REQUIRED = (
    BASE / "src" / "l01_repo_imports.py",
    BASE / "src" / "l01_mask_difference_stability.py",
    BASE / "src" / "l01_r9c9_same_sky_beam.py",
    BASE / "src" / "l01_smica_fits_integrity.py",
    BASE / "src" / "fetch_planck_pr3_smica.py",
    BASE / "tests" / "conftest.py",
    PRIOR / "src" / "l01_k_spectral_certificate.py",
    PRIOR / "tests" / "test_l01_k_certificate.py",
)

class CheckoutError(RuntimeError):
    """A typed failure indicating stale/dirty/untrusted checkout."""


def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args],
                       capture_output=True, text=True, check=False)
    if p.returncode:
        raise CheckoutError("GIT_UNAVAILABLE_OR_UNTRUSTED: " +
                            (p.stderr.strip() or f"git exit {p.returncode}"))
    return p.stdout.strip()


def check_checkout(root: Path, expected_ref: str = EXPECTED_REF,
                   *, smoke: bool = True) -> dict:
    root = Path(root).resolve()
    if expected_ref != EXPECTED_REF:
        raise CheckoutError("UNEXPECTED_BRANCH_REF: select pinned publication branch")
    actual_root = Path(git(root, "rev-parse", "--show-toplevel")).resolve()
    if actual_root != root:
        raise CheckoutError(f"NOT_GIT_TOPLEVEL: actual={actual_root} supplied={root}")
    actual = git(root, "rev-parse", "HEAD")
    try:
        expected = git(root, "rev-parse", "--verify", f"{expected_ref}^{{commit}}")
    except CheckoutError as exc:
        raise CheckoutError("EXPECTED_REMOTE_REF_UNAVAILABLE__FETCH_FROM_REPO_FIRST") from exc
    if actual != expected:
        raise CheckoutError(f"STALE_CHECKOUT_HEAD actual={actual} expected={expected}; "+
                            "Do not execute the old worktree. Create a fresh user-owned worktree.")
    dirty = git(root, "status", "--porcelain", "--untracked-files=normal")
    if dirty:
        raise CheckoutError("DIRTY_WORKTREE__PRESERVE_LOCAL_CHANGES: " +
                            repr(dirty.splitlines()[:5]))
    missing = [str(rel) for rel in REQUIRED if not (root / rel).is_file()]
    if missing:
        raise CheckoutError("INCOMPLETE_STACKED_CHECKOUT_MISSING: " + ", ".join(missing))
    checks = {}
    if smoke:
        scripts = {
            "c8": (BASE / "src" / "l01_mask_difference_stability.py", "--spectral-receipt"),
            "c9": (BASE / "src" / "l01_r9c9_same_sky_beam.py", "--c8-receipt"),
            "download": (BASE / "src" / "fetch_planck_pr3_smica.py", "--attempts"),
        }
        for key, (script, option) in scripts.items():
            proc = subprocess.run([sys.executable, str(root / script), "--help"],
                                  cwd=root, capture_output=True, text=True,
                                  check=False, timeout=30)
            if proc.returncode or option not in proc.stdout:
                raise CheckoutError(
                    f"STAGE_SCRIPT_IMPORT_OR_CLI_FAILURE:{key}: " +
                    (proc.stderr.strip() or "missing " + option))
            checks[key] = "IMPORT_AND_OPTION_VERIFIED"
    return {"schema": "htt.L01_checkout_gate/1",
            "status": "PASS_EXACT_HEAD_CLEAN_IMPORTS",
            "worktree": str(root), "head": actual, "remote_ref": expected_ref,
            "smoke": checks, "data_download": "NOT_RUN"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--worktree", type=Path, default=Path.cwd())
    ap.add_argument("--expected-ref", default=EXPECTED_REF)
    args = ap.parse_args(argv)
    try:
        result = check_checkout(args.worktree, args.expected_ref)
    except (CheckoutError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"schema": "htt.L01_checkout_gate/1", "status": "BLOCKED",
                          "error": str(exc), "next_action":
                          "FETCH_NEW_BRANCH_AND_CREATE_FRESH_USER_OWNED_WORKTREE"},
                         indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
