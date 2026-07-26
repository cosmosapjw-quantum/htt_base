#!/usr/bin/env python3
"""Provider adapter that denies ordinary-agent publication mutations."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from publication_integrity import (
    PublicationIntegrityError,
    classify_provider_payload,
    read_json_bytes,
)


def _deny(
    provider: str, reason: str, *, legacy_antigravity: bool = False
) -> int:
    message = (
        f"PUBLICATION_FIREWALL: {reason}. Ordinary agent workspaces stop at "
        "local commits/candidate reports; use the credential-isolated external publisher."
    )
    if provider == "codex":
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": message,
                    },
                    "systemMessage": message,
                }
            )
        )
        return 0
    if provider == "antigravity":
        if legacy_antigravity:
            print(message, file=sys.stderr)
            return 2
        print(json.dumps({"decision": "deny", "reason": message}))
        return 0
    print(message, file=sys.stderr)
    return 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider", choices=["codex", "claude", "antigravity"], required=True
    )
    args = parser.parse_args()
    try:
        payload: Any = read_json_bytes(
            sys.stdin.buffer.read(),
            field="provider hook payload",
        )
    except PublicationIntegrityError as exc:
        raise SystemExit(_deny(args.provider, f"malformed hook payload: {exc}"))
    if not isinstance(payload, dict):
        raise SystemExit(_deny(args.provider, "hook payload is not an object"))
    legacy_antigravity = (
        args.provider == "antigravity"
        and "tool_args" in payload
        and "toolCall" not in payload
    )
    try:
        denied, reason = classify_provider_payload(payload, provider=args.provider)
    except PublicationIntegrityError as exc:
        denied, reason = True, str(exc)
    if denied:
        raise SystemExit(
            _deny(
                args.provider,
                reason,
                legacy_antigravity=legacy_antigravity,
            )
        )
    if args.provider == "antigravity" and not legacy_antigravity:
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
