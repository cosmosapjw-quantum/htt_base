import copy

import pytest

from scripts.r99 import program_preparation as prep


def sources():
    return prep.read(prep.DAG), prep.read(prep.PREVIOUS/prep.FILE), prep.read(prep.BASE/"PUBLICATION_DAG.json")["nodes"]


def test_actual_60_node_closure_and_preserved_42():
    dag, old, original = sources()
    closure = prep.verify_contract(dag,old,original)
    assert len(closure) == 60 and len(dag["edges"]) == 129
    assert closure["SQ-CF4"] == {"D01","D02","M01","A01"}
    assert {"D01","M01","M02","A06"} <= closure["H06"]
    assert sum(n["state"]=="completed_scoped" for n in dag["nodes"])==18


def test_reject_mutated_scientific_acceptance_and_propagation():
    dag, old, original = sources()
    altered = copy.deepcopy(dag)
    altered["nodes"][0]["acceptance"] += " relaxed"
    with pytest.raises(ValueError,match="original 42"):
        prep.verify_contract(altered,old,original)
    row = next(n for n in old["nodes"] if n["id"]=="H06")
    row["all_blockers_including_dependencies"].remove("D01")
    with pytest.raises(ValueError,match="inherited blocker"):
        prep.verify_contract(dag,old,original)


def test_check_detects_saved_overlay_drift_and_science_fails_closed(tmp_path,monkeypatch):
    data={"nodes":[{"id":"SQ-CF4","science_status":"SCIENCE_BLOCKED","original_state":"ready_scoped",
          "changed_obligations":[],"direct_blockers":["D01"],"all_blockers_including_dependencies":["D01"],
          "preparation_packages":[]}],"blockers":{},"counts":{},"next_id":"SQ-CF4"}
    monkeypatch.setattr(prep,"build",lambda:data)
    monkeypatch.setattr(prep,"OUT",tmp_path)
    assert prep.main(["prepare"])==0
    assert prep.main(["--check"])==0
    assert prep.main(["science","--node","SQ-CF4"])==3
    (tmp_path/prep.FILE).write_text("{}")
    with pytest.raises(ValueError,match="saved execution preparation"):
        prep.main(["--check"])
