#!/usr/bin/env python3
"""Create or verify an exact Git candidate seal without publishing."""
from __future__ import annotations

import argparse
import json

from _harness import root
from publication_integrity import (
    PublicationIntegrityError,
    build_candidate_seal,
    read_repo_json,
    runtime_output_path,
    validate_candidate_seal_payload,
    write_json_exclusive,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--change-set", required=True)
    create.add_argument("--publication-group", required=True)
    create.add_argument("--target-ref", default=None)
    create.add_argument("--candidate-ref", default="HEAD")
    create.add_argument("--integration-policy", required=True)
    create.add_argument("--output", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--seal", required=True)
    args = parser.parse_args()
    repo = root()

    try:
        if args.command == "create":
            seal = build_candidate_seal(
                repo,
                change_set_id=args.change_set,
                publication_group_id=args.publication_group,
                target_ref=args.target_ref,
                candidate_ref=args.candidate_ref,
                integration_policy_path=args.integration_policy,
            )
            output = runtime_output_path(
                repo, args.output, field="candidate seal output"
            )
            write_json_exclusive(output, seal)
            print(json.dumps({"ok": True, "seal": args.output, **seal}, indent=2))
            return
        _, _, seal = read_repo_json(repo, args.seal, field="candidate seal")
        errors = validate_candidate_seal_payload(seal, repo=repo)
        print(
            json.dumps(
                {
                    "ok": not errors,
                    "seal": args.seal,
                    "seal_sha256": seal.get("seal_sha256"),
                    "errors": errors,
                },
                indent=2,
            )
        )
        if errors:
            raise SystemExit(1)
    except PublicationIntegrityError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
