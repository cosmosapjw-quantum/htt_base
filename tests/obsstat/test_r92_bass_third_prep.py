"""R92 BASS/high-l third-loop preparation: source coverage and claim boundaries."""
from pathlib import Path
import json
import sqlite3
import hashlib
import zipfile
import pytest
from sympy.physics.wigner import wigner_3j
from scripts.r92 import prepare_third_loop as r
from scripts.r92.high_ell_gaunt_oracle import examine

@pytest.fixture(scope="module")
def outputs():
    return {name:json.loads((r.OUT/name).read_text()) for name in (
      "SCANNED_ROOTS_AND_ARCHIVES.json",
      "CURATED_BASS_BIANCHI_SOURCES.json",
      "GITHUB_REPO_PROVENANCE.json",
      "HIGH_ELL_L2_GAUNT_CONSTRUCTION.json",
      "BASS_NATIVE_AND_TRANSFER_READINESS.json"
    )}

def test_original_R78_immutable():
    assert r.sha(r.R78)=="90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
    dag=json.loads(r.R78.read_text())
    assert len(dag["nodes"])==60 and len(dag["edges"])==129
    assert dag["next_action_id"]=="SQ-CF4"

def test_all_seven_roots_and_private_complete_index(outputs):
    d=outputs["SCANNED_ROOTS_AND_ARCHIVES.json"]
    assert len(d["root_metrics"])==7
    assert d["total_files"]==92127
    assert d["full_private_search_entries"]==256138
    assert d["private_index_not_in_repo"]
    assert Path(d["private_search_db"]).is_file()

def test_full_private_search_index_count_and_archive_members():
    j=outputs_stub=None
    db=r.PRIVATE/"R92_SEARCH_INDEX.sqlite"
    con=sqlite3.connect(db)
    try:
        assert con.execute("select count(*) from files").fetchone()[0]==256138
        assert dict(con.execute("select source_type,count(*) from files group by source_type").fetchall())=={
            "physical_file":92127,"archive_member":164011}
        assert con.execute("select count(*) from file_fts where file_fts match 'thomson'").fetchone()[0]>100
    finally:
        con.close()

def test_753_of_754_archive_members_and_exact_failure(outputs):
    j=outputs["SCANNED_ROOTS_AND_ARCHIVES.json"]
    assert j["archive_files"]==754
    assert j["archive_indexed_total"]==753
    assert j["archive_current_unreadable"]==1
    assert "THERM01_STAGE_C" in j["unreadable_reason_codes"][0]["archive"]
    assert j["large_tar_secondpass_members"]==534

def test_legal_archive_indexed_without_extraction():
    assert not any((r.OUT/name).exists() for name in ("R92_SEARCH_INDEX.sqlite","R92_DEEP_INDEX_20261121.files.jsonl.gz"))
    assert (r.PRIVATE/"R92_DEEP_INDEX_20261121.archive_members.jsonl.gz").is_file()

def test_curated_real_sources_have_exact_sha_and_size(outputs):
    j=outputs["CURATED_BASS_BIANCHI_SOURCES.json"]
    assert len(j["curated_source_files"])==40
    rootmap=r.ROOTS
    for item in j["curated_source_files"]:
        p=(r.HTT if item["root_id"]=="HTT_ACTIVE" else rootmap[item["root_id"]])/item["relative_path"]
        assert p.is_file()
        assert p.stat().st_size==item["bytes"]
        assert r.sha(p)==item["sha256"]
    assert j["original_dossier_copyright_scope"].startswith("only metadata")

def test_selected_dossier_pdfs_are_eight_distinct_and_page_grounded(outputs):
    j=outputs["CURATED_BASS_BIANCHI_SOURCES.json"]
    pdf=[x for x in j["curated_source_files"] if x["root_id"]==0]
    assert len(pdf)==8
    assert all(x["pages"]>5 for x in pdf)
    assert max(x["pages"] for x in pdf)==92

def test_selected_archive_members_have_hashed_raw_contents(outputs):
    j=outputs["CURATED_BASS_BIANCHI_SOURCES.json"]
    assert len(j["archive_members_sampled_and_content_hashed"])==6
    for item in j["archive_members_sampled_and_content_hashed"]:
        p=r.ROOTS[item["root_id"]]/item["archive"]
        with zipfile.ZipFile(p) as z:
            data=z.read(item["member"])
        assert len(data)==item["bytes"]
        assert hashlib.sha256(data).hexdigest()==item["sha256"]

def test_9_github_repos_htt_active_truncated_and_recovered_locally(outputs):
    j=outputs["GITHUB_REPO_PROVENANCE.json"]
    assert len(j["public_related"])==9
    h=next(x for x in j["public_related"] if x["name"]=="htt_base")
    assert any(v["api_tree_truncated"] for v in h["branches"])
    assert j["htt_active_branch_local_full_tree_count"]==34068
    assert j["htt_api_truncation_recovered_by_local_git_tree"]
    assert next(x for x in j["public_related"] if x["name"]=="cosmo_lab")["status"].startswith("PRIVATE_")

def test_gaunt_l2_parity_triangle_strict_selection(outputs):
    t=outputs["HIGH_ELL_L2_GAUNT_CONSTRUCTION.json"]
    assert len(t["exact_checks"])==4
    for row in t["exact_checks"]:
        ell=row["l"]
        for x in row["cells"]:
            lprime=x["lp"]
            expected=(abs(lprime-ell)<=2 and (lprime-ell)%2==0)
            assert bool(wigner_3j(ell,2,lprime,0,0,0)!=0)==expected
            assert (x["threej_000"]!="0")==expected

def test_gaunt_higher_multipole_count_increases_not_fisher():
    j=examine()
    p=j["offdiagonal_l_to_lplus2_M0_mode_count"]
    assert p["ell_le_16"]<p["ell_le_64"]<p["ell_le_128"]
    assert j["mode_count_is_not_Fisher_information"] is True
    assert j["physical_Bianchi_polarized_all_m_transfer_replaced"] is False

def test_bass_model_order_lmax6_and_native_not_ready(outputs):
    d=outputs["BASS_NATIVE_AND_TRANSFER_READINESS.json"]
    assert d["BASS_hierarchy_supported_Lmax"]==6
    assert d["BASS_high_l_l4_pytest_bass_env"]=={"pass":1,"fail":1,
          "failure":"Installed native bianchi_rustcore lacks rayon_thread_pool_size; not a physics sign mismatch"}
    assert d["BASS_polarization_pure_numpy_pytest"]=={"pass":3,"fail":0}
    assert d["isolated_matching_wheel_symbol"] is True
    assert d["isolated_matching_wheel_test_status"]=="FAIL"
    assert d["third_loop_bianchi_high_ell_ready"] is False
    assert d["bass_or_htt_installed_packages_changed"] is False

def test_third_loop_preparation_not_science_60pass():
    g=examine()
    assert g["cosmological_significance"]=="UNQUALIFIED_TOY_SOURCE_SHAPE"
    report=(r.OUT/"ASSESSMENT_THIRD_LOOP_KO.md").read_text()
    assert "NOT" in report
    assert "3차" in report
    assert "256,138" in report
    assert (r.OUT/"THIRD_LOOP_HANDOFF_KO.md").is_file()

def test_prepare_outputs_content_stable_without_mutation(outputs):
    fresh=r.build()
    for name,s in fresh.items():
        assert (r.OUT/name).read_bytes()==s.encode("utf8")
