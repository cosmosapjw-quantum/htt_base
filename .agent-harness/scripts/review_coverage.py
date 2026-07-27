#!/usr/bin/env python3
"""Validate a reviewer coverage matrix against an immutable candidate."""
from __future__ import annotations

import argparse
import json

from _harness import root
from publication_integrity import (
    PublicationIntegrityError,
    load_publication_policy,
    read_repo_json,
    validate_candidate_seal_payload,
    validate_review_coverage_payload,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", required=True)
    parser.add_argument("--seal", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--assignment-id", required=True)
    parser.add_argument("--risk-tier", choices=["R0", "R1", "R2", "R3"], required=True)
    parser.add_argument(
        "--structural-only",
        action="store_true",
        help="validate a blocking first verdict without declaring publication readiness",
    )
    args = parser.parse_args()
    repo = root()
    try:
        _, _, coverage = read_repo_json(
            repo, args.coverage, field="review coverage"
        )
        _, _, seal = read_repo_json(repo, args.seal, field="candidate seal")
        policy_ref = seal.get("integration_policy")
        if not isinstance(policy_ref, dict):
            raise PublicationIntegrityError("candidate seal lacks integration_policy")
        _, policy = load_publication_policy(
            repo,
            policy_ref.get("path"),
            expected_sha256=str(policy_ref.get("sha256") or ""),
        )
        errors = validate_candidate_seal_payload(seal, repo=repo)
        errors.extend(
            validate_review_coverage_payload(
                coverage,
                seal=seal,
                policy=policy,
                run_id=args.run_id,
                assignment_id=args.assignment_id,
                risk_tier=args.risk_tier,
                require_ready=not args.structural_only,
                repo=repo,
            )
        )
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
        if errors:
            raise SystemExit(1)
    except PublicationIntegrityError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
