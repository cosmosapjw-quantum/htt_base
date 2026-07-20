"""PR-174 runner: SW-only ray-integration mechanics card producer.

Modes:
  --preflight  verify spec presence, firewall, and zero production consumers
  --write      produce docs/generated/pr174_result_card.json (+ mutation report)
  --check      recompute and byte-compare both artifacts (read-only)

hypothesis_only / public_use=false / ceiling roadmap_rescue_v1:C1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.pr174_sw_ray_tracer import (  # noqa: E402
    Pr174Config,
    run_mechanics,
    run_mutation_battery,
)

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr174_spec.yaml"
MODULE = REPO / "htt/src/common/pr174_sw_ray_tracer.py"
OUTPUTS = {
    "result": REPO / "docs/generated/pr174_result_card.json",
    "mutations": REPO / "docs/generated/pr174_mutation_report.json",
}

FORBIDDEN_IMPORT_SUBSTRINGS = (
    "likelihood",
    "posterior",
    "bayes",
    "emcee",
    "cobaya",
    "camb",
    "classy",
    "healpy",
    "bessel",
    "bass.los",
    "bass.spectrum",
)

# The spec's allowed_imports whitelist, enforced on top-level module names.
ALLOWED_TOP_LEVEL_IMPORTS = frozenset(
    {"math", "json", "hashlib", "dataclasses", "typing", "numpy", "pathlib",
     "__future__"}
)

# Directories that are not production import surfaces: virtualenvs, VCS and
# build state, archived code, test trees, data workdirs, and doc trees.
CONSUMER_SCAN_EXCLUDED_PARTS = frozenset(
    {"venv", ".venv", ".git", "__pycache__", ".lake", "legacy", "tests",
     "workdir", "node_modules"}
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module_import_hits(module: Path) -> list[dict]:
    """AST scan: import statements, dynamic-import calls, and whitelist."""
    import ast

    hits: list[dict] = []
    tree = ast.parse(module.read_text())
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        elif isinstance(node, ast.Call):
            func = node.func
            dynamic = (
                (isinstance(func, ast.Name) and func.id == "__import__")
                or (
                    isinstance(func, ast.Attribute)
                    and func.attr in {"import_module", "__import__"}
                )
            )
            if dynamic:
                hits.append(
                    {
                        "line": node.lineno,
                        "text": "dynamic import call",
                        "token": "dynamic_import",
                    }
                )
            continue
        else:
            continue
        for name in names:
            lowered = name.lower()
            for token in FORBIDDEN_IMPORT_SUBSTRINGS:
                if token in lowered:
                    hits.append(
                        {"line": node.lineno, "text": name, "token": token}
                    )
            top_level = name.split(".")[0]
            if top_level not in ALLOWED_TOP_LEVEL_IMPORTS:
                hits.append(
                    {
                        "line": node.lineno,
                        "text": name,
                        "token": "outside_allowed_imports_whitelist",
                    }
                )
    return hits


def firewall_scan(
    module: Path = MODULE, scan_roots: tuple[Path, ...] | None = None
) -> dict:
    """AST import scan of the module + repo-wide production consumer scan.

    ``module``/``scan_roots`` are overridable ONLY so the guard tests can
    demonstrate the scan detects injected violations; production calls
    use the defaults (the whole repository minus excluded parts).
    """
    import_hits = _module_import_hits(module)
    consumers = []
    roots = scan_roots if scan_roots is not None else (REPO,)
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            rel = (
                path.relative_to(REPO).as_posix()
                if path.is_relative_to(REPO)
                else str(path)
            )
            parts = set(Path(rel).parts)
            if parts & CONSUMER_SCAN_EXCLUDED_PARTS:
                continue
            if path == MODULE or path == Path(__file__).resolve():
                continue
            text = path.read_text(errors="replace")
            if "pr174_sw_ray_tracer" in text:
                consumers.append(rel)
    return {
        "forbidden_import_hits": import_hits,
        "production_consumers": consumers,
        "consumer_scan_scope": "repository_wide_minus_excluded_parts",
        "consumer_scan_excluded_parts": sorted(CONSUMER_SCAN_EXCLUDED_PARTS),
        "pass": not import_hits and not consumers,
    }


def build_payloads() -> dict[str, dict]:
    config = Pr174Config()
    firewall = firewall_scan()
    if not firewall["pass"]:
        raise SystemExit(
            "PR-174 firewall violation: " + json.dumps(firewall, sort_keys=True)
        )
    spec_sha = _sha(SPEC)
    spec_text = SPEC.read_text()
    baseline = None
    for line in spec_text.splitlines():
        if line.startswith("baseline_commit:"):
            baseline = line.split(":", 1)[1].strip()
    mechanics = run_mechanics(config)
    battery = run_mutation_battery(config)
    metadata = {
        "owner": "COMMON",
        "implementation_scope": ["common"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "hypothesis_only",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": config.config_hash(),
        "spec_sha256": spec_sha,
        "generating_command": (
            "env PYTHONHASHSEED=0 venv/bin/python -B "
            "scripts/codex_harness/run_pr174_sw_ray_tracer.py --write"
        ),
        "git_commit": baseline,
        "git_commit_semantics": (
            "baseline commit pinned by the frozen spec at generation time; "
            "kept byte-stable by construction so --check stays commit-independent"
        ),
        "runtime_identity": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "platform": sys.platform,
        },
        "runtime_identity_semantics": (
            "artifact float bytes depend on this runtime (numpy leggauss "
            "nodes and float arithmetic); a runtime change is expected to "
            "fail --check visibly and requires a disclosed regeneration"
        ),
    }
    result_card = {
        "schema": "htt.pr174.result_card.v1",
        "pr_id": "PR-174",
        "metadata": metadata,
        "firewall": firewall,
        "mechanics": mechanics,
        "forbidden_claims_reaffirmed": [
            "no likelihood, family, or geometry claim",
            "no native/external transfer or Boltzmann-solution claim",
            "no observable prediction, detection, anisotropy, or isotropy claim",
            "no mixing with the FLRW LoS Bessel path",
            "an analytic mismatch never selects the physically correct side",
            "no promotion beyond roadmap_rescue_v1:C1 hypothesis_only",
        ],
    }
    mutation_report = {
        "schema": "htt.pr174.mutation_report_card.v1",
        "pr_id": "PR-174",
        "metadata": metadata,
        "battery": battery,
    }
    return {"result": result_card, "mutations": mutation_report}


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.preflight:
        firewall = firewall_scan()
        report = {
            "spec_present": SPEC.exists(),
            "spec_sha256": _sha(SPEC) if SPEC.exists() else None,
            "firewall": firewall,
            "ok": SPEC.exists() and firewall["pass"],
        }
        print(json.dumps(report, sort_keys=True))
        return 0 if report["ok"] else 1

    payloads = build_payloads()
    if args.write:
        for key, path in OUTPUTS.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(_render(payloads[key]))
            print(f"wrote {path.relative_to(REPO)}")
        return 0

    failures = []
    for key, path in OUTPUTS.items():
        if not path.exists():
            failures.append(f"missing artifact: {path.relative_to(REPO)}")
            continue
        if path.read_bytes() != _render(payloads[key]):
            failures.append(f"artifact differs under --check: {path.relative_to(REPO)}")
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(
        json.dumps(
            {
                "mode": "check",
                "ok": True,
                "read_only": True,
                "terminal": payloads["result"]["mechanics"]["terminal"],
                "all_mutations_killed": payloads["mutations"]["battery"]["all_killed"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
