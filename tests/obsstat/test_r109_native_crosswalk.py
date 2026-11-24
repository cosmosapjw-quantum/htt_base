import json
from collections import Counter

from scripts.r109.node_crosswalk import BASE, DIRECT, OUT, REGISTRIES, RELATED, digest


def test_crosswalk_preserves_published_states_edges_and_six_plus_seven():
    out = json.loads((OUT/"NODE_CROSSWALK.json").read_bytes())
    canonical = json.loads((BASE/REGISTRIES["R78"][0]).read_bytes())
    old = {n["id"]:n for n in canonical["nodes"]}
    assert len(out["nodes"]) == len(old) == 60
    assert {r["id"] for r in out["nodes"]} == set(old)
    for node in out["nodes"]:
        original = old[node["id"]]
        assert node["canonical_state"] == original["state"]
        assert node["depends_on"] == original["depends_on"]
    assert out["counts"]["edges"] == len(canonical["edges"]) == 129
    assert list(out["six_papers"]) == canonical["papers"]
    assert [(x["id"],x["axes"]) for x in out["seven_cross_routes"]] == [
        (x["id"],x["axes"]) for x in canonical["seven_R77_PHY_combinations"]]
    assert out["counts"]["scientific_promotions"] == 0


def test_receipts_bound_to_real_material_and_commander_results():
    out = json.loads((OUT/"NODE_CROSSWALK.json").read_bytes())
    for name in ("commander","material"):
        r = out["evidence"][name]
        assert digest((BASE/r["path"]).read_bytes()) == r["sha256"]
    b = out["evidence"]["atlas"]
    assert len(b["commit"]) == 40 and b["cases"] >= 12
    grouped = Counter(r["r109"] for r in out["nodes"])
    assert grouped["direct_scoped_numerical"] == len(DIRECT)
    assert grouped["upstream_relevance_only"] == len(RELATED)
    assert grouped == out["counts"]["R109_coverage"]
    assert next(r for r in out["nodes"] if r["id"]=="B03")["canonical_state"] == "pending"
