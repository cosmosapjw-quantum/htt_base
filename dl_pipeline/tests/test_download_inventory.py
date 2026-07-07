from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from download_inventory import (
    build_download_inventory,
    extract_named_href,
    sha256_file,
    write_acquisition_manifest,
)


def _case_root(name: str) -> Path:
    root = Path("workdir") / "test_download_inventory" / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_extract_named_href_resolves_matching_filename() -> None:
    html = '<a href="/data/suborbital/ACT/file.tar.gz">file.tar.gz</a>'

    assert extract_named_href(html, "file.tar.gz") == "/data/suborbital/ACT/file.tar.gz"


def test_inventory_counts_missing_and_present_files() -> None:
    root = _case_root("present_missing")
    present = root / "downloads" / "present.bin"
    present.parent.mkdir(parents=True)
    present.write_bytes(b"abc")
    sources = {
        "stage_a": {
            "downloads": [
                {"id": "present", "url": "https://example.test/present", "out": "downloads/present.bin", "expected_size_bytes": 3},
                {"id": "missing", "url": "https://example.test/missing", "out": "downloads/missing.bin", "expected_size_bytes": 7},
            ]
        }
    }

    inventory = build_download_inventory(sources, root, ["stage_a"], probe_network=False)

    rows = {item["item_id"]: item for item in inventory["items"]}
    assert rows["present"]["status"] == "present"
    assert rows["present"]["additional_bytes"] == 0
    assert rows["missing"]["status"] == "needs_download"
    assert inventory["known_additional_bytes"] == 7
    assert inventory["within_cap_for_known_sizes"] is True


def test_inventory_fails_closed_for_known_over_cap() -> None:
    root = _case_root("over_cap")
    sources = {
        "stage_a": {
            "downloads": [
                {"id": "big", "url": "https://example.test/big", "out": "downloads/big.bin", "expected_size_bytes": 11},
            ]
        }
    }

    inventory = build_download_inventory(
        sources,
        root,
        ["stage_a"],
        max_download_bytes=10,
        probe_network=False,
    )

    assert inventory["known_additional_bytes"] == 11
    assert inventory["within_cap_for_known_sizes"] is False


def test_inventory_does_not_invent_page_urls_without_network_probe() -> None:
    root = _case_root("page_no_probe")
    sources = {
        "act_dr6": {
            "downloads": [
                {
                    "id": "sacc",
                    "page": "https://lambda.gsfc.nasa.gov/product/act/page.html",
                    "filename": "dr6_data.tar.gz",
                    "out": "downloads/dr6_data.tar.gz",
                }
            ]
        }
    }

    inventory = build_download_inventory(sources, root, ["act_dr6"], probe_network=False)

    item = inventory["items"][0]
    assert item["url"] is None
    assert item["status"] == "size_unknown"
    assert inventory["unknown_size_count"] == 1


def test_acquisition_manifest_uses_real_hash_metadata() -> None:
    root = _case_root("manifest")
    payload = root / "payload.bin"
    payload.write_bytes(b"science-input")
    manifest = root / "manifest.json"

    write_acquisition_manifest(
        manifest,
        stage="act_dr6",
        source_items=[{"id": "payload", "url": "https://example.test/payload.bin"}],
        local_files=[payload],
        generating_command="fetch.py --stages act_dr6 --approve-downloads",
    )

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["owner"] == "DL_PIPELINE"
    assert data["claim_tier"] == "input_provenance_only"
    assert data["transfer_source"] == "external_public_data"
    assert data["config_hash"] != "not_computed_in_gitless_copy"
    assert data["input_hashes"] == [sha256_file(payload)]
    assert data["null_mock_status"] == "not_evaluated_by_download_stage"
    assert "covariance_null_mock_status" not in data
    assert data["git_worktree_state"]["status"] in {"available", "unavailable"}
