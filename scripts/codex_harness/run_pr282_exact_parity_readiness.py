#!/usr/bin/env python3
"""Portable build/check/test runner for PR-282 exact parity readiness."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr282_spec.yaml"
OUTPUT = ROOT / "docs/generated/pr282_exact_parity_readiness_receipt.json"
BOUND_SOURCES = (
    "docs/research_program/post_pr275/pr282_spec.yaml",
    "docs/research_program/vector_tensor/proofs/PILLAR_S_CORE_PROOFS_V1.yaml",
    "htt/obsstat/exact_parity_readiness.py",
    "htt/obsstat/egs3_evalue_merge.py",
    "htt/src/common/vector_tensor_statistical_foundations.py",
    "scripts/codex_harness/run_pr282_exact_parity_readiness.py",
    "tests/obsstat/test_exact_parity_readiness.py",
    "tests/contracts/test_pillar_s_core.py",
)


def _activate_sources() -> None:
    for path in reversed((ROOT / "htt", ROOT / "htt/src")):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
    )


def _render(payload: object) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _build_artifact() -> dict[str, Any]:
    _activate_sources()
    from obsstat.exact_parity_readiness import (
        PASS_TOKEN,
        build_parity_readiness_receipt,
        validate_parity_readiness_receipt,
    )

    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    receipt = build_parity_readiness_receipt(spec)
    errors = validate_parity_readiness_receipt(receipt, spec)
    if errors:
        raise RuntimeError("invalid recomputed readiness receipt: " + "; ".join(errors))
    if receipt["terminal"]["g3_outcome"] != PASS_TOKEN:
        raise RuntimeError(
            "registered PR-282 execution did not pass G3: "
            + json.dumps(receipt["terminal"], sort_keys=True)
        )
    source_bindings = [
        {
            "path": relative,
            "sha256": _sha256_bytes((ROOT / relative).read_bytes()),
        }
        for relative in BOUND_SOURCES
    ]
    unsigned = {
        "schema": "htt.pr282.exact_parity_execution_artifact.v1",
        "artifact_id": "PR282-EXACT-PARITY-READINESS",
        "owner": "OBSSTAT",
        "contributors": ["COMMON"],
        "scope": "synthetic executable P-equivariance method readiness",
        "claim_tier": "diagnostic_only",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "synthetic_diagnostic",
        "transfer_source": "none",
        "sky_support_status": "synthetic_reflection_paired_support",
        "mask_status": "synthetic_fixed_under_registered_reflection",
        "weighting_status": "synthetic_fixed_under_registered_reflection",
        "covariance_status": "not_used_by_exact_h2_execution",
        "null_mock_status": "not_used_by_exact_h2_execution",
        "observed_data_executed": False,
        "public_use": False,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "source_bindings": source_bindings,
        "readiness_receipt": receipt,
        "generating_command": (
            "python3 -B scripts/codex_harness/"
            "run_pr282_exact_parity_readiness.py build"
        ),
        "generation_identity": {
            "mode": "EXACT_BOUND_SOURCE_HASHES",
            "git_or_worktree_identity": "EXTERNAL_CANDIDATE_SEAL_REQUIRED",
            "reason": (
                "Embedding the commit or tree that contains this artifact would be circular; "
                "acceptance binds the candidate in the external seal and review run plan."
            ),
        },
        "assumptions": receipt["assumptions"],
        "caveats": [
            "H1 and H3 remain separate unestablished premises",
            "mask deconvolution is not executed",
            "synthetic method readiness only; no observed data or family claim",
        ],
    }
    return {**unsigned, "artifact_content_sha256": _canonical_sha256(unsigned)}


def _pytest(paths: tuple[str, ...]) -> int:
    env = dict(os.environ)
    for key in (
        "PYTHONHOME",
        "PYTEST_ADDOPTS",
        "PYTEST_PLUGINS",
        "PYTHONSTARTUP",
    ):
        env.pop(key, None)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT / "htt/src"), str(ROOT / "htt")))
    command = [
        sys.executable,
        "-B",
        "-m",
        "pytest",
        "-p",
        "no:cacheprovider",
        "-q",
        *paths,
    ]
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    modes = {"build", "check", "focused", "adjacent", "pr272"}
    if len(args) != 1 or args[0] not in modes:
        print(
            "usage: run_pr282_exact_parity_readiness.py "
            "{build|check|focused|adjacent|pr272}",
            file=sys.stderr,
        )
        return 2
    mode = args[0]
    if mode == "focused":
        return _pytest(("tests/obsstat/test_exact_parity_readiness.py",))
    if mode == "adjacent":
        return _pytest(
            (
                "tests/contracts/test_pillar_s_core.py",
                "tests/obsstat/test_alm_conventions.py",
                "tests/obsstat/test_biposh_features.py",
            )
        )
    if mode == "pr272":
        return _pytest(
            (
                "tests/contracts/test_pillar_s_inference.py",
                "-k",
                (
                    "pr282_relocation or "
                    "preregistration_bytes_and_input_hashes or "
                    "registry_generator_is_deterministic"
                ),
            )
        )

    artifact = _build_artifact()
    rendered = _render(artifact)
    if mode == "build":
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(rendered)
        print(f"wrote {OUTPUT.relative_to(ROOT)} sha256={_sha256_bytes(rendered)}")
        return 0
    if not OUTPUT.is_file():
        print(f"missing generated receipt: {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
        return 1
    actual = OUTPUT.read_bytes()
    if actual != rendered:
        print(
            "generated PR-282 receipt is stale: "
            f"expected={_sha256_bytes(rendered)} actual={_sha256_bytes(actual)}",
            file=sys.stderr,
        )
        return 1
    print(f"ok {OUTPUT.relative_to(ROOT)} sha256={_sha256_bytes(actual)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
