#!/usr/bin/env python3
"""Build the Tier-0 shared context pack.

Write-if-content-changed (audit H7): when the hashed shared files are
unchanged, neither CONTEXT_INDEX.json nor CONTEXT_PACK.md is rewritten, so
repeated builds produce zero tracked-file churn and `built_at` only advances
when the content version actually changes.
"""
from __future__ import annotations

from _harness import dump_json, hash_files, load_json, root, utc_now


def render_pack(version: str, built_at: str, entries, repo) -> str:
    chunks = [
        "# Canonical Shared Context Pack",
        "",
        f"Context version: `{version}`",
        f"Built at: `{built_at}`",
        "",
        "This pack contains only the shared Tier-0 context. Assignment-specific context and sibling results are intentionally excluded.",
    ]
    for rel, sha in entries:
        text = (repo / rel).read_text(encoding="utf-8")
        chunks.extend(["", f"---\n\n## Source: `{rel}`\n\nSHA-256: `{sha}`\n", text.rstrip()])
    return "\n".join(chunks).rstrip() + "\n"


def main() -> None:
    repo = root()
    harness = repo / ".agent-harness"
    index_path = harness / "context" / "CONTEXT_INDEX.json"
    index = load_json(index_path)
    files = list(index.get("shared_files", []))
    if not files:
        raise SystemExit("CONTEXT_INDEX.json has no shared_files.")

    missing = [rel for rel in files if not (repo / rel).is_file()]
    if missing:
        raise SystemExit("Missing shared context files:\n" + "\n".join(missing))

    version, entries = hash_files(repo, files)
    out = harness / "generated" / "CONTEXT_PACK.md"

    unchanged = (
        index.get("context_version") == version
        and index.get("file_hashes") == {rel: sha for rel, sha in entries}
        and out.is_file()
        and out.read_text(encoding="utf-8")
        == render_pack(version, str(index.get("built_at", "")), entries, repo)
    )
    if unchanged:
        print(f"Unchanged {out.relative_to(repo)} (no files rewritten)")
        print(f"context_version={version}")
        return

    index["context_version"] = version
    index["built_at"] = utc_now()
    index["file_hashes"] = {rel: sha for rel, sha in entries}
    dump_json(index_path, index)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        render_pack(version, index["built_at"], entries, repo), encoding="utf-8"
    )
    print(f"Built {out.relative_to(repo)}")
    print(f"context_version={version}")


if __name__ == "__main__":
    main()
