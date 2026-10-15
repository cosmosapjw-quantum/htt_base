"""Source admission and non-duplication regression for three HTT science lineages."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
STUDY=PUB/"legacy_modern_obs_integration_20261015"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_archived_user_original_legacy_byte_identities_preserved():
    ledger=json.loads((STUDY/"ORIGINAL_LEGACY_SOURCE_LINEAGE.json").read_text())
    assert len(ledger["authoritative_generated_source_ledger"])==8
    for item in ledger["authoritative_generated_source_ledger"]:
        p=ROOT/item["snapshotted"]
        assert p.is_file(),p
        assert p.stat().st_size==item["size_bytes"]
        assert sha(p)==item["SHA256"]
    assert ledger["scalar_F4_vs_MIO_F_not_identical"]
    assert ledger["MES_physical_no_automatic_import"]


def test_PR531_PR532_independent_science_is_source_typed_not_product_multiplied():
    x=json.loads((STUDY/"INDEPENDENT_OBSERVATION_PR_CROSSWALK.json").read_text())
    assert len(x["source_results"])==11
    assert x["scientific_joint_likelihood_admitted"] is False
    assert {j["PR"] for j in x["source_results"]}=={"PR531","PR532"}
    assert all(len(j["sha256"])==64 and len(j["exact_ref"])==40 for j in x["source_results"])
    deps={tuple(z["channels"]):z["dependence"] for z in x["pairwise_policies"]}
    assert deps[("PR531_SMICA_SCATTER","OUR_FFP10_CMB_999_NOISE_300")]=="EXACT_SHARED_COMPACT_FFP10_K1_CACHE"
    assert deps[("PR532_PLANCK_9_PRODUCTS","OUR_PLANCK_9_TEMP")]=="SAME_PHYSICAL_SKY"
    assert deps[("PR532_CF4_24_SN","OUR_CF4_35970_GROUPS")].startswith("SAME_CF4_CATALOGUE")


def test_exact_source_F4_parity_and_normalizer_discrepancy_have_receipts():
    path=STUDY/"results"
    t=json.loads((path/"observed_planck_l23_exact_F4_v1/result.json").read_text())
    a=t["per_actual_same_sky_processing"]["SMICA_FULL"]
    p=json.loads((path/"planck_parity_source_v1/result.json").read_text())
    assert p["physical_sky_count"]==1 and p["product_processing_count"]==9
    assert abs(p["same_sky_sources"]["SMICA_FULL"]["total_cross"]-
               a["deltaF4_coupling_l2_l3"])<2e-24
    assert p["max_abs_parity_forbidden_moment"]<1e-25
    diff=json.loads((path/"source_mes_legacy_modern_v1/result.json").read_text())
    assert diff["source_processing_case_count"]==9
    assert diff["physical_ranking_of_bounds"]=="WITHHELD"
    assert min(diff["vorticity_old_over_new_norm_squared_ratio_minmax"])>300
    assert t["calibrated_null_p"]=="NOT_ADMITTED"


def test_bundle_lineage_map_and_DAG_retain_scoped_physical_gates():
    m=json.loads((STUDY/"THREE_LINEAGE_INTEGRATION_MAP.json").read_text())
    assert len(m["source_lineages"])==3
    for item in m["evidence"]:
        p=Path(item["file"])
        assert p.is_file() and sha(p)==item["sha256"]
        assert item["bytes"]==p.stat().st_size
    r=json.loads((STUDY/"INTEGRATION_REPLAY_RECEIPT.json").read_text())
    assert len(r["replay_pairs"])==4
    assert all(x["science_json_equal_ignoring_runtime_only"] for x in r["replay_pairs"])
    dag=json.loads((PUB/"PUBLICATION_DAG.json").read_text())
    byid={n["id"]:n for n in dag["nodes"]}
    assert byid["S02"]["state"]=="completed_scoped"
    assert byid["S02"]["existing_evidence"]
    assert all(byid[x]["state"]=="pending" for x in ("L02","H02"))
    assert all(p["publication_status"]=="NOT_READY_TO_SUBMIT" for p in dag["papers"])
