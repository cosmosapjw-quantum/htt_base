"""Keep current context updates independent of sealed historical context."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "context_isolation_harness", REPO / ".agent-harness/scripts/_harness.py"
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HARNESS)


class ContextIsolationTests(unittest.TestCase):
    def test_repository_packs_match_their_sources(self) -> None:
        for prefix in ("", "CURRENT_"):
            with self.subTest(prefix=prefix):
                index = HARNESS.load_json(
                    REPO / f".agent-harness/context/{prefix}CONTEXT_INDEX.json"
                )
                version, entries, pack_entries = HARNESS.context_entries(REPO, index)
                self.assertEqual(index["context_version"], version)
                self.assertEqual(index["file_hashes"], dict(entries))
                pack = (
                    REPO / f".agent-harness/generated/{prefix}CONTEXT_PACK.md"
                ).read_text(encoding="utf-8")
                self.assertEqual(
                    pack,
                    HARNESS.render_context_pack(
                        version, index["built_at"], pack_entries, REPO, current=bool(prefix)
                    ),
                )
                self.assertLessEqual(len(pack), index["max_injected_chars"])
                self.assertLessEqual(len(pack), 12000)
                if not prefix:
                    self.assertEqual(HARNESS.load_validated_context_pack(REPO, index), pack)

    def test_current_source_edit_preserves_frozen_pack(self) -> None:
        frozen = HARNESS.load_json(REPO / ".agent-harness/context/CONTEXT_INDEX.json")
        current = HARNESS.load_json(REPO / ".agent-harness/context/CURRENT_CONTEXT_INDEX.json")
        self.assertTrue(set(frozen["shared_files"]).isdisjoint(current["shared_files"]))
        # Copy only actual sealed sources and views, rather than inventing a fixture
        # whose paths or hashes could conceal a shared-source regression.
        files = set(frozen["shared_files"] + current["shared_files"])
        files.add(".agent-harness/generated/CONTEXT_PACK.md")
        with tempfile.TemporaryDirectory() as directory:
            overlay = Path(directory)
            for rel in files:
                target = overlay / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(REPO / rel, target)
            original = HARNESS.load_validated_context_pack(overlay, frozen)
            source = overlay / current["shared_files"][0]
            source.write_text(source.read_text(encoding="utf-8") + "\nCurrent-only edit.\n", encoding="utf-8")
            changed_version, _, _ = HARNESS.context_entries(overlay, current)
            self.assertNotEqual(changed_version, current["context_version"])
            self.assertEqual(HARNESS.load_validated_context_pack(overlay, frozen), original)


if __name__ == "__main__":
    unittest.main()
