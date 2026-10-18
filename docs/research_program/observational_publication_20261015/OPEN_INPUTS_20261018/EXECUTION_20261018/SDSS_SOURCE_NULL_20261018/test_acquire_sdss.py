"""Meaningful boundary tests with tiny stand-ins; no network or scientific run."""
import unittest

from acquire_sdss import safe_member, validate_response
from inspect_archive import selected_entries


class AcquisitionBoundaries(unittest.TestCase):
    def test_exact_range(self):
        validate_response(206, {"Content-Range": "bytes 0-9/20", "Content-Length": "10"}, 0, 9, 20)

    def test_ignored_range_rejected_before_body(self):
        with self.assertRaisesRegex(ValueError, "body not read"):
            validate_response(200, {"Content-Length": "20"}, 0, 9, 20)

    def test_wrong_range_and_length_rejected(self):
        for headers in ({"Content-Range": "bytes 1-10/20", "Content-Length": "10"},
                        {"Content-Range": "bytes 0-9/20", "Content-Length": "9"}):
            with self.assertRaises(ValueError):
                validate_response(206, headers, 0, 9, 20)

    def test_encoded_response_rejected(self):
        with self.assertRaises(ValueError):
            validate_response(206, {"Content-Range": "bytes 0-9/20", "Content-Length": "10",
                                    "Content-Encoding": "gzip"}, 0, 9, 20)

    def test_extraction_guards(self):
        self.assertEqual(str(safe_member("mock/R19000.0_err_corr", True, 100)), "mock/R19000.0_err_corr")
        for name, regular, size in (("../escape", True, 1), ("/escape", True, 1),
                                    ("mock/link", False, 1), ("huge", True, 2 * 1024**3 + 1)):
            with self.assertRaises(ValueError):
                safe_member(name, regular, size)

    def test_selection_numeric_boxes_y0_not_archive_order(self):
        entries = [{"name": f"mocks/mock_R19{box:03d}.{observer}_err_corr", "size": 100}
                   for box in reversed(range(256)) for observer in reversed(range(8))]
        boxes, selected = selected_entries(entries)
        self.assertEqual(boxes, list(range(256)))
        self.assertEqual([entry["box"] for entry in selected], list(range(64)))
        self.assertTrue(all(entry["observer"] == 0 for entry in selected))
        with self.assertRaises(ValueError):
            selected_entries(entries[:-1])
        with self.assertRaises(ValueError):
            selected_entries(entries + entries[:1])


if __name__ == "__main__":
    unittest.main()
