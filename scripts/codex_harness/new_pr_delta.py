#!/usr/bin/env python3
"""Generate standardized PR delta/review artifacts from the DAG backlog."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from string import Template
from typing import Mapping, Sequence

import yaml

DEFAULT_BACKLOG = Path("docs/codex_handoff/pr_backlog.yaml")
DEFAULT_TEMPLATE = Path("docs/PR_DELTAS/TEMPLATE.md")
DEFAULT_OUTPUT_DIR = Path("docs/PR_DELTAS")


def load_pr_card(backlog_path: str | Path, pr_id: str) -> dict[str, object]:
    """Return a PR card from a machine-readable backlog."""

    path = Path(backlog_path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path} must contain a YAML mapping")
    prs = payload.get("prs")
    if not isinstance(prs, list):
        raise ValueError(f"{path} must contain a prs list")
    for raw in prs:
        if isinstance(raw, Mapping) and raw.get("id") == pr_id:
            return dict(raw)
    raise KeyError(f"{pr_id} not found in {path}")


def render_pr_delta(
    pr_card: Mapping[str, object],
    *,
    web_check_status: str = "pending",
    template_path: str | Path = DEFAULT_TEMPLATE,
) -> str:
    """Render a PR delta from a card and strict Markdown template."""

    template = Template(Path(template_path).read_text(encoding="utf-8"))
    owner = _canonical_owner(str(pr_card.get("owner", "UNKNOWN")))
    substitutions = {
        "pr_id": _required_str(pr_card, "id"),
        "title": _required_str(pr_card, "title"),
        "owner": owner,
        "implementation_scope": _implementation_scope(owner),
        "depends": _format_list_inline(pr_card.get("depends"), empty="none"),
        "level": str(pr_card.get("level", "unknown")),
        "scope": str(pr_card.get("scope", "unknown")),
        "risk": str(pr_card.get("risk", "unknown")),
        "files": _format_bullets(pr_card.get("files")),
        "tests": _format_bullets(pr_card.get("tests")),
        "dod": _format_bullets(pr_card.get("dod")),
        "kill": str(pr_card.get("kill", "none")),
        "web_check_status": web_check_status,
    }
    return template.substitute(substitutions).rstrip() + "\n"


def target_path(output_dir: str | Path, pr_id: str) -> Path:
    """Return the default PR delta output path."""

    return Path(output_dir) / f"{pr_id.lower()}.md"


def write_pr_delta(
    pr_card: Mapping[str, object],
    *,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
    template_path: str | Path = DEFAULT_TEMPLATE,
    web_check_status: str = "pending",
    force: bool = False,
) -> Path:
    """Write a rendered PR delta and refuse accidental overwrites."""

    out = target_path(output_dir, _required_str(pr_card, "id"))
    if out.exists() and not force:
        raise FileExistsError(f"{out} already exists; pass --force to overwrite")
    content = render_pr_delta(
        pr_card,
        web_check_status=web_check_status,
        template_path=template_path,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a standardized PR_DELTA Markdown artifact."
    )
    parser.add_argument("pr_id", help="PR id from the DAG backlog, e.g. PR-022.")
    parser.add_argument(
        "--backlog",
        type=Path,
        default=DEFAULT_BACKLOG,
        help="Machine-readable PR backlog YAML.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE,
        help="Markdown template containing $pr_id and related placeholders.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for the generated PR delta.",
    )
    parser.add_argument(
        "--web-check-status",
        choices=("pending", "done", "skipped"),
        default="pending",
        help="Recorded web/doc verification status.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the target path and rendered content without writing.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing generated PR delta.",
    )
    args = parser.parse_args(argv)
    try:
        card = load_pr_card(args.backlog, args.pr_id)
        out = target_path(args.dir, _required_str(card, "id"))
        content = render_pr_delta(
            card,
            web_check_status=args.web_check_status,
            template_path=args.template,
        )
        if args.dry_run:
            print(out)
            print(content, end="")
            return 0
        if out.exists() and not args.force:
            raise FileExistsError(f"{out} already exists; pass --force to overwrite")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(out)
        return 0
    except (FileExistsError, KeyError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _required_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"PR card missing non-empty {key}")
    return value


def _format_list_inline(value: object, *, empty: str) -> str:
    if value is None:
        return empty
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        items = [str(item) for item in value]
        return ", ".join(items) if items else empty
    return str(value)


def _format_bullets(value: object) -> str:
    if value is None:
        return "- none"
    if isinstance(value, str):
        return f"- {value}"
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        items = [str(item) for item in value]
        return "\n".join(f"- `{item}`" for item in items) if items else "- none"
    return f"- {value}"


def _canonical_owner(owner: str) -> str:
    value = owner.strip()
    if value == "TSC":
        return "TSC_LEGACY"
    if value == "BASS_PY":
        return "BASS"
    if value == "MANUSCRIPT":
        return "COMMON"
    return value


def _implementation_scope(owner: str) -> str:
    return {
        "COMMON": "common",
        "HTT": "htt",
        "MIO": "mio",
        "BASS": "bass_py",
        "OBSSTAT": "obsstat",
        "TSC_LEGACY": "tsc_legacy",
    }.get(owner, "unknown")


if __name__ == "__main__":
    raise SystemExit(main())
