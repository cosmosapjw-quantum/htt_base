"""Emit a bounded TSC active-service bundle and policy ledger."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from common.contracts import ArtifactManifest
from tsc.integration import (
    active_service_bundle_to_json,
    active_service_bundle_to_markdown,
    build_active_service_bundle_from_samples,
)
from tsc.reports import (
    overlay_to_policy_ledger_json,
    overlay_to_policy_ledger_markdown,
)


def _manifest(*, artifact_id: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/tsc/{artifact_id.replace('.', '_')}.json",
        owner="TSC",
        implementation_scope="tsc",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="ver2_tsc_active_service.py",
        git_commit="demo",
        config_hash="demo",
        input_hashes=["demo:seed"],
        code_version="0.0-demo",
        schema_version="ver2-v1",
    )


def _demo_bundle(*, claim_limited: bool) -> object:
    mu, weights = np.polynomial.legendre.leggauss(32)
    weights = weights / np.sum(weights)
    theta = 1.0 + 0.10 * mu
    if claim_limited:
        return build_active_service_bundle_from_samples(
            chart="one_field",
            theta_samples=theta.tolist(),
            directions=mu.tolist(),
            weights=weights.tolist(),
            manifest=_manifest(artifact_id="tsc.active.service.claim_limited"),
            laguerre_n_ge_2_norm=0.1,
            onefield_residual=None,
            trace_residual_q_tr=0.1,
            spin2_residual=0.2,
            jacobian_singular_values=[0.1, 0.2],
            propagation_status_by_channel={
                "TT": "validated",
                "EE": "validated",
                "TE": "validated",
            },
            propagator_norm_bound=3.0,
            required_channels=("TT",),
        )
    return build_active_service_bundle_from_samples(
        chart="one_field",
        theta_samples=theta.tolist(),
        directions=mu.tolist(),
        weights=weights.tolist(),
        manifest=_manifest(artifact_id="tsc.active.service.pending"),
        laguerre_n_ge_2_norm=0.1,
        onefield_residual=0.1,
        trace_residual_q_tr=0.1,
        spin2_residual=0.2,
        jacobian_singular_values=[0.1, 0.2],
        propagation_status_by_channel={"TT": "validated", "EE": "pending", "TE": "pending"},
        propagator_norm_bound=3.0,
    )


def _write_outputs(bundle: object, output_dir: Path) -> tuple[Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_json = output_dir / "tsc_active_service_bundle.json"
    bundle_md = output_dir / "tsc_active_service_bundle.md"
    policy_json = output_dir / "tsc_policy_ledger.json"
    policy_md = output_dir / "tsc_policy_ledger.md"
    bundle_json.write_text(
        active_service_bundle_to_json(bundle),  # type: ignore[arg-type]
        encoding="utf-8",
    )
    bundle_md.write_text(
        active_service_bundle_to_markdown(bundle),  # type: ignore[arg-type]
        encoding="utf-8",
    )
    policy_json.write_text(
        overlay_to_policy_ledger_json(bundle.overlay),  # type: ignore[attr-defined]
        encoding="utf-8",
    )
    policy_md.write_text(
        overlay_to_policy_ledger_markdown(bundle.overlay),  # type: ignore[attr-defined]
        encoding="utf-8",
    )
    return bundle_json, bundle_md, policy_json, policy_md


def _check(*, claim_limited: bool) -> int:
    bundle = _demo_bundle(claim_limited=claim_limited)
    payload = json.loads(active_service_bundle_to_json(bundle))  # type: ignore[arg-type]
    policy = payload["overlay_policy_ledger"]
    blockers = tuple(payload["publication_blockers"])
    if policy["advisory_only"] is not True:
        print("[FAIL] TSC active-service export check: advisory_only flag missing")
        return 1
    if claim_limited and not any(
        str(blocker).startswith("claim_ceiling_insufficient:")
        for blocker in blockers
    ):
        print("[FAIL] TSC active-service export check: claim ceiling blocker missing")
        return 1
    if not claim_limited and not any(
        str(blocker).startswith("propagation_pending:")
        for blocker in blockers
    ):
        print("[FAIL] TSC active-service export check: pending propagation blocker missing")
        return 1
    mode = "claim-limited" if claim_limited else "pending"
    print(
        "[PASS] TSC active-service export check "
        f"(mode={mode}, publication_ready={payload['publication_ready']})"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--policy-json", action="store_true")
    parser.add_argument("--policy-markdown", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--claim-limited-demo", action="store_true")
    parser.add_argument("--write-dir", type=Path)
    args = parser.parse_args(argv)

    claim_limited = bool(args.claim_limited_demo)
    if args.check:
        return _check(claim_limited=claim_limited)

    bundle = _demo_bundle(claim_limited=claim_limited)
    if args.write_dir is not None:
        outputs = _write_outputs(bundle, args.write_dir)
        for path in outputs:
            print(path.as_posix())
        return 0
    if args.policy_json:
        sys.stdout.write(
            overlay_to_policy_ledger_json(bundle.overlay) + "\n"  # type: ignore[attr-defined]
        )
        return 0
    if args.policy_markdown:
        sys.stdout.write(
            overlay_to_policy_ledger_markdown(bundle.overlay) + "\n"  # type: ignore[attr-defined]
        )
        return 0
    if args.markdown:
        sys.stdout.write(active_service_bundle_to_markdown(bundle) + "\n")  # type: ignore[arg-type]
        return 0
    payload = active_service_bundle_to_json(bundle)  # type: ignore[arg-type]
    if args.json:
        sys.stdout.write(payload + "\n")
        return 0
    data = json.loads(payload)
    mode = "claim-limited" if claim_limited else "pending"
    print(
        "TSC active-service export: "
        f"mode={mode} publication_ready={data['publication_ready']} "
        f"blockers={len(data['publication_blockers'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
