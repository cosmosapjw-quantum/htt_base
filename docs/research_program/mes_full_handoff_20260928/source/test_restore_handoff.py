#!/usr/bin/env python3
"""Small synthetic archive acceptance tests; no scientific runtime is used."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).with_name("restore_handoff.py")
ROLES = ["research_backup", "early_archive_backup", "catalog_backup", "i1_checkpoint", "i2_checkpoint"]


class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        for role in ROLES:
            with zipfile.ZipFile(self.bundle / f"{role}.zip", "w") as z:
                z.writestr(f"{role}/result.txt", f"Evidence for {role}\n")
        self.write_manifest()

    def tearDown(self):
        self.temporary.cleanup()

    def write_manifest(self):
        files = []
        for role in ROLES:
            path = self.bundle / f"{role}.zip"
            files.append({"path": path.name, "role": role,
                          "size_bytes": path.stat().st_size,
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        (self.bundle / "DELIVERY_MANIFEST.json").write_text(
            json.dumps({"schema_version": 1, "files": files}), encoding="utf-8")

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), "--bundle-root", str(self.bundle), *arguments],
                              text=True, capture_output=True, check=False)

    def restore_cli(self, *arguments):
        return self.run_cli("--restore", "--destination", str(self.root / "restored"), *arguments)

    def test_verify_default_performs_no_restore(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "VERIFIED_ARCHIVE_BYTES_ONLY")
        self.assertFalse((self.root / "restored").exists())

    def test_valid_restore_keeps_nested_archive_opaque(self):
        nested = b"a preserved opaque zip payload, never interpreted"
        with zipfile.ZipFile(self.bundle / "early_archive_backup.zip", "w") as z:
            z.writestr("history/older.zip", nested)
        self.write_manifest()
        result = self.restore_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        restored = self.root / "restored"
        self.assertEqual((restored / "early_archive_backup/history/older.zip").read_bytes(), nested)
        self.assertEqual((restored / "checkpoints/I2/i2_checkpoint/result.txt").read_text(),
                         "Evidence for i2_checkpoint\n")
        self.assertFalse((restored / "catalog_exports").exists())
        receipt = json.loads((restored / "RESTORE_RECEIPT.json").read_text())
        self.assertEqual(receipt["status"], "RESTORED")
        self.assertFalse(receipt["database_restored"])

    def test_hash_mismatch_rejected_before_destination_created(self):
        path = self.bundle / "research_backup.zip"
        content = bytearray(path.read_bytes())
        content[-1] ^= 1
        path.write_bytes(content)
        result = self.restore_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("SHA-256 mismatch", result.stderr)
        self.assertFalse((self.root / "restored").exists())

    def test_existing_destination_is_preserved(self):
        restored = self.root / "restored"
        restored.mkdir()
        (restored / "user.txt").write_text("Do not change")
        result = self.restore_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing overwrite", result.stderr)
        self.assertEqual((restored / "user.txt").read_text(), "Do not change")
        self.assertEqual(len(list(restored.iterdir())), 1)

    def test_archive_path_traversal_rejected(self):
        with zipfile.ZipFile(self.bundle / "research_backup.zip", "w") as z:
            z.writestr("../escape.txt", "escape")
        self.write_manifest()
        result = self.restore_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Unsafe relative path", result.stderr)
        self.assertFalse((self.root / "escape.txt").exists())
        self.assertFalse((self.root / "restored").exists())

    def test_archive_symlink_rejected(self):
        entry = zipfile.ZipInfo("link")
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(self.bundle / "research_backup.zip", "w") as z:
            z.writestr(entry, "/etc/passwd")
        self.write_manifest()
        result = self.restore_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Non-regular archive member", result.stderr)

    def test_case_collision_rejected(self):
        with zipfile.ZipFile(self.bundle / "research_backup.zip", "w") as z:
            z.writestr("Case.txt", "one")
            z.writestr("case.txt", "two")
        self.write_manifest()
        result = self.restore_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Duplicate archive member", result.stderr)

    def test_catalog_explicit_two_level_only(self):
        portable = self.root / "portable.zip"
        with zipfile.ZipFile(portable, "w") as z:
            z.writestr("exports/schema.sql", "CREATE TABLE evidence(id INTEGER);")
            z.writestr("exports/files.jsonl.gz", b"opaque gzip payload")
        with zipfile.ZipFile(self.bundle / "catalog_backup.zip", "w") as z:
            z.write(portable, "history/HTT_CATALOG_SCAN_57ecfe21_PORTABLE.zip")
        self.write_manifest()
        result = self.restore_cli("--catalog")
        self.assertEqual(result.returncode, 0, result.stderr)
        restored = self.root / "restored"
        self.assertTrue((restored / "catalog_exports/exports/schema.sql").is_file())
        self.assertEqual((restored / "catalog_exports/exports/files.jsonl.gz").read_bytes(),
                         b"opaque gzip payload")

    def test_database_file_rejected(self):
        with zipfile.ZipFile(self.bundle / "research_backup.zip", "w") as z:
            z.writestr("huge.sqlite", b"database must not be unpacked")
        self.write_manifest()
        result = self.restore_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("Database extraction is disabled", result.stderr)

    def test_restore_requires_explicit_destination(self):
        result = self.run_cli("--restore")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--restore requires --destination", result.stderr)

    def test_second_payload_publish_failure_never_publishes_success_receipt(self):
        spec = importlib.util.spec_from_file_location("restore_failure_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        destination = self.root / "restored"
        roles = {role: self.bundle / f"{role}.zip" for role in ROLES}
        original_rename, original_iterdir = os.rename, Path.iterdir
        payload_moves = 0

        def receipt_first_if_present(path):
            entries = list(original_iterdir(path))
            # Directory enumeration order is unspecified. Exercise the order
            # that would expose a prematurely written success receipt first.
            return iter(sorted(entries, key=lambda entry:
                               (entry.name != "RESTORE_RECEIPT.json", entry.name)))

        def fail_second_payload(source, target):
            nonlocal payload_moves
            if Path(source).name != "RESTORE_RECEIPT.json":
                payload_moves += 1
                if payload_moves == 2:
                    raise OSError("injected second payload publication failure")
            return original_rename(source, target)

        with patch.object(Path, "iterdir", receipt_first_if_present), \
                patch.object(module.os, "rename", fail_second_payload):
            with self.assertRaises(module.HandoffError) as raised:
                module.restore(roles, destination, False, {})
        stages = list(self.root.glob(".restored.incomplete-*"))
        self.assertEqual(len(stages), 1)
        self.assertEqual(payload_moves, 2)
        self.assertTrue(destination.is_dir())
        self.assertFalse((destination / "RESTORE_RECEIPT.json").exists())
        self.assertIn(str(stages[0]), str(raised.exception))
        self.assertIn(str(destination), str(raised.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
