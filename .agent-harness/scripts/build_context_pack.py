#!/usr/bin/env python3
"""Build the bounded Tier-0 shared-context delivery view.

Write-if-content-changed (audit H7): when the injected Tier-0 sources are
unchanged, neither CONTEXT_INDEX.json nor CONTEXT_PACK.md is rewritten.
Reference-only assignment inputs do not rotate the global context version.
"""
from __future__ import annotations

from _harness import (
    context_entries,
    dump_json,
    load_json,
    render_context_pack,
    root,
    utc_now,
)


def main() -> None:
    repo = root()
    harness = repo / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"
    index = load_json(index_path)
    try:
        version, entries, pack_entries = context_entries(repo, index)
    except (OSError, UnicodeError, ValueError) as exc:
        raise SystemExit(f"Cannot build context view: {exc}") from None

    out = harness / "generated" / "CONTEXT_PACK.md"
    if out.is_symlink():
        raise SystemExit("Refusing to replace a symlinked generated context view.")

    expected = render_context_pack(
        version,
        str(index.get("built_at", "")),
        pack_entries,
        repo,
    )
    unchanged = (
        index.get("context_version") == version
        and index.get("file_hashes") == dict(entries)
        and out.is_file()
        and out.read_text(encoding="utf-8") == expected
    )
    if unchanged:
        print(f"Unchanged {out.relative_to(repo)} (no files rewritten)")
        print(f"context_version={version}")
        return

    index["context_version"] = version
    index["built_at"] = utc_now()
    index["file_hashes"] = dict(entries)
    dump_json(index_path, index)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_context_pack(
            version,
            index["built_at"],
            pack_entries,
            repo,
        ),
        encoding="utf-8",
    )
    print(f"Built {out.relative_to(repo)}")
    print(f"context_version={version}")


if __name__ == "__main__":
    main()
