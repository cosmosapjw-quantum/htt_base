"""Source/output isolation and missing-library regressions for the CORAS build."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.r105 import coras_build as builder


class TestCorasBuild(unittest.TestCase):
    def test_existing_output_and_donor_not_changed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            donor=root/"source"
            donor.mkdir()
            self.assertRaises(ValueError,builder.prepare_build,donor/"build",donor)
            self.assertRaises(ValueError,builder.prepare_build,root,donor)
            self.assertFalse((donor/"build").exists())
            output=root/"output"
            output.mkdir()
            self.assertRaises(FileExistsError,builder.prepare_build,output,donor)
            path,source=builder.prepare_build(root/"new",donor)
            self.assertEqual(source,donor)
            self.assertTrue(path.is_dir())

    def test_missing_runtime_fails(self):
        with patch("subprocess.check_output",return_value="libgsl.so.27 => not found"):
            self.assertRaises(RuntimeError,builder.track_runtime,Path("/unused"))
