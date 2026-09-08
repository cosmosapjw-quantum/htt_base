import csv
import json
from pathlib import Path
from common.r7_asset_use import intake_inventory, Disposition, verify_selected_sources, PRODUCTS


def test_independent_product_routes_and_exclusion(tmp_path):
    products = tmp_path / "products"
    products.mkdir()
    inventory = tmp_path / "assets.csv"
    with inventory.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "workdir_path"])
        w.writeheader()
        for name in ("wmap_9yr", "union3_release-main", "desi_dr1_fullshape_bgs_bright_v1.2"):
            w.writerow({"name": name, "workdir_path": products})
    result = {r.product_key: r for r in intake_inventory(inventory)}
    assert set(result) == set(PRODUCTS)
    for key in ("wmap9", "union3", "desi_compressed"):
        assert result[key].disposition == Disposition.CONTROL_ONLY
        assert result[key].law_scope is None
    for key in ("pr3_smica", "jwst_sn", "desi_raw"):
        assert result[key].disposition == Disposition.UNAVAILABLE_PRODUCT_OR_LAW
    assert result["pr4_npipe"].product_locator is None


def test_source_dispositions_do_not_couple_donors(tmp_path):
    root = Path(__file__).resolve().parents[2]
    bindings = json.loads((root / "docs/generated/tensor_joint_r7/source_bindings.json").read_text())
    assert verify_selected_sources(root, bindings) == {}
    broken = {"records": [dict(row) for row in bindings["records"]]}
    broken["records"][0]["selected_sha256"] = "0" * 64
    assert set(verify_selected_sources(root, broken)) == {"Q"}
