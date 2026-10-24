#!/usr/bin/env python3
"""Prospective exact-product SMICA child; controller supplies a sealed GO.

This file is source preparation only until a controller seals final INPUT,
latest cumulative account head, packet, ACK and passing format controls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
CONTRACT_SHA = "38bcd5ec436826c85b9507cf30cd0ae51c2899bcee8644a6db383c7f7fe28ff0"
KNOWLEDGE_SHA = "2d0dcfe98ab58a62fdca85f5c8efe85e65128223f6c9914bdfa845c1eb121f30"
TEMPLATE_SHA = "a91f755a5d43b008cff6f53c084ca501e2565ce3696c7b76ab10c76437a868d7"
PATH_BINDING_SHA = "ab8267d96c785e6e1248039e0b7582938c093178c342a73440e1b2096320e259"
OPERATOR_SHA = "7c76fe22d9dee0c2fdb3c7cde6073f3d038700f18dd19f9b1c1eb727290b69ee"
DECODER_SHA = "ecccebc39c4814546552b9fbc6b6ed798cc644fec1f6616a26003fda17932216"
MATH_SHA = "b64af9d883eba3f4f967daaf8c92eb8fc3e8b4b6fee0542ce7f251fe92e1cfca"
COMPONENT = "R26-SMICA-EXACT-PR3-IMPLICIT-ROW-PROJECTION"
ACCOUNTS = ("30", "44", "70", "100", "143", "217", "353", "SMICA")
SOURCE_DIR = Path("/mnt/extdrive/workdir/htt_open_data/r26_seven_frequency_consumption_framing/SMICA_contract")
OPERATOR = Path("/mnt/extdrive/workdir/htt_open_data/r26_streamed_spin2_numeric/streamed_operator.py")
DECODER = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/obsstat/planck_lowell_irrep_projection.py")
MATH = Path("/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/full7_math.py")


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sealed(path, digest):
    if sha(path) != digest:
        raise RuntimeError("SOURCE_OR_INPUT_SEAL_DRIFT " + str(path))
    return Path(path)


def sealed_ref(ref):
    path = sealed(ref["path"], ref["sha256"])
    if "bytes" in ref and path.stat().st_size != ref["bytes"]:
        raise RuntimeError("SOURCE_OR_INPUT_SIZE_DRIFT " + str(path))
    return path


def _load_json(path, digest):
    return json.loads(sealed(path, digest).read_text())


def validate_go(args):
    """Small-source and accounting checks only; no numerical imports or map reads."""
    input_path = sealed(args.input, args.input_sha)
    packet_path = sealed(args.packet, args.packet_sha)
    cfg = json.loads(input_path.read_text())
    packet = json.loads(packet_path.read_text())
    contract = _load_json(SOURCE_DIR / "CONTRACT.json", CONTRACT_SHA)
    _load_json(SOURCE_DIR / "SOURCE_KNOWLEDGE.json", KNOWLEDGE_SHA)
    _load_json(SOURCE_DIR / "INPUT_TEMPLATE.json", TEMPLATE_SHA)
    binding = _load_json(SOURCE_DIR / "CONTROLLER_OUTPUT_PATH_BINDING.json", PATH_BINDING_SHA)
    if binding.get("controller_owned_output_directory") != str(HERE):
        raise RuntimeError("OUTPUT_PATH_BINDING_DRIFT")
    if (cfg.get("component_id") != COMPONENT or cfg.get("no_launch_from_template") is True
            or cfg.get("contract", {}).get("sha256") != CONTRACT_SHA
            or cfg.get("source_knowledge", {}).get("sha256") != KNOWLEDGE_SHA
            or cfg.get("source_product") != contract["production_source"]
            or cfg.get("production_profile") != contract["production_header_profile"]
            or cfg.get("source_profile_id") != contract["source_profile_id"]
            or cfg.get("controller_output_directory") != str(HERE)):
        raise RuntimeError("ACTUAL_FINAL_INPUT_REQUIRED")
    source_hashes = cfg.get("implementation_source_seals", {}).get("sha256")
    if not isinstance(source_hashes, dict) or set(source_hashes) != {
        "smica_implicit_reader.py", "project_smica.py", "test_format_controls.py",
        "run_smica.py"}:
        raise RuntimeError("IMPLEMENTATION_SOURCE_SEALS_REQUIRED")
    for name, digest in source_hashes.items():
        sealed(HERE / name, digest)
    for path, digest in ((OPERATOR, OPERATOR_SHA), (DECODER, DECODER_SHA), (MATH, MATH_SHA)):
        sealed(path, digest)
    old = contract["numerics"]
    for key in ("frozen_input", "support", "validity", "kernel", "math", "decoder"):
        sealed_ref(old[key])
    for ref in contract["seven_handoff_seals"].values():
        sealed_ref(ref)
    head_ref = cfg.get("latest_account_head", {})
    if head_ref.get("status") != "SEALED_LATEST_POST_SEVEN_HEAD":
        raise RuntimeError("LATEST_ACCOUNT_HEAD_NOT_SEALED")
    head = json.loads(sealed_ref(head_ref).read_text())
    totals = head.get("cumulative_charged_seconds")
    if (not isinstance(totals, dict) or set(totals) != set(ACCOUNTS)
            or totals != head_ref.get("cumulative_charged_seconds")):
        raise RuntimeError("LATEST_EIGHT_ACCOUNT_TOTALS_REQUIRED")
    for key in ACCOUNTS:
        value = totals[key]
        if (not isinstance(value, (int, float)) or not 0 <= value < 900
                or value < contract["accounting"]["snapshot_cumulative_charged_seconds"][key]):
            raise RuntimeError("CUMULATIVE_ACCOUNT_DRIFT " + key)
    if (packet.get("packet_id") is None or packet.get("task_id") != COMPONENT
            or packet.get("input_identity") != "sha256:" + args.input_sha
            or packet.get("launch_performed") is not True
            or packet.get("actual_go") is not True
            or packet.get("latest_account_head") != head_ref):
        raise RuntimeError("GENUINE_CONTROLLER_PACKET_GO_REQUIRED")
    ack_ref = packet.get("controller_ack")
    if not isinstance(ack_ref, dict):
        raise RuntimeError("CONTROLLER_ACK_REQUIRED")
    ack = json.loads(sealed_ref(ack_ref).read_text())
    if (ack.get("status") != "CONTROLLER_ACTUAL_DISPATCH_ACKNOWLEDGED"
            or ack.get("phase") != "smica_exact_product"
            or ack.get("packet_id") != packet["packet_id"]
            or ack.get("input_sha256") != args.input_sha
            or ack.get("actual_go") is not True
            or ack.get("latest_account_head") != head_ref
            or not ack.get("one_use_attempt_id")
            or ack.get("source_sha256") != source_hashes):
        raise RuntimeError("CONTROLLER_ACK_BINDING_DRIFT")
    if cfg.get("scientific_admission") != "HOLD":
        raise RuntimeError("SCIENTIFIC_CLAIM_BOUNDARY")
    return cfg, contract, head_ref, packet["packet_id"]


def validate_child_start(args, cfg, contract):
    if args.internal_fd is None or not args.attempt_id:
        raise RuntimeError("DIRECT_NATIVE_CHILD_FORBIDDEN")
    token = os.read(args.internal_fd, 128).decode("ascii")
    os.close(args.internal_fd)
    if token != args.attempt_id:
        raise RuntimeError("NATIVE_CHILD_TOKEN_DRIFT")
    receipt_path = HERE / "run/RAW_RECEIPT.json"
    ledger = json.loads(receipt_path.read_text())
    marker = ledger.get("native", {})
    if (ledger.get("stage") != "NATIVE_STARTED"
            or marker.get("status") != "STARTED"
            or marker.get("attempt_id") != args.attempt_id
            or marker.get("pid") != os.getpid()
            or marker.get("parent_pid") != os.getppid()
            or ledger.get("input_sha256") != args.input_sha):
        raise RuntimeError("NATIVE_CHILD_PARENT_OR_MARKER")
    receipt = json.loads(sealed(args.control_receipt, args.control_receipt_sha).read_text())
    if (receipt.get("status") != "PASS"
            or receipt.get("component_id") != COMPONENT
            or receipt.get("source_profile_id") != contract["source_profile_id"]
            or receipt.get("source_sha256") != cfg["implementation_source_seals"]["sha256"]):
        raise RuntimeError("FORMAT_CONTROLS_NOT_BOUND")


def project_with_reader(product, support_nest, *, parent_nside=64, reader=None):
    """Two sealed passes and the exact project_twice comparisons with injection."""
    import numpy as np
    from streamed_operator import project_pass, bound_math, REPO
    if reader is None:
        from smica_implicit_reader import selected_chunks as reader
    first = project_pass(product, support_nest, chunk_rows=131072,
                         parent_nside=parent_nside, reader=reader)
    second = project_pass(product, support_nest, chunk_rows=131071,
                          parent_nside=parent_nside, reader=reader)
    c = first["canonical24"]
    tol = 1e-12 + 1e-9 * np.abs(c)
    for name, comparison in (("SPLIT_BLOCK_REDUCTION", first["alternate24"]),
                             ("INDEPENDENT_HALF_AMPLITUDE", 2 * first["half24"]),
                             ("SECOND_PARTITION", second["canonical24"]),
                             ("SECOND_SPLIT_REDUCTION", second["alternate24"]),
                             ("SECOND_HALF_AMPLITUDE", 2 * second["half24"])):
        if not np.all(np.abs(c - comparison) <= tol):
            raise RuntimeError(name)
    if first["selected_native_pixels"] != second["selected_native_pixels"]:
        raise RuntimeError("PARTITION_SELECTED_COUNT_DRIFT")
    if c.shape != (24,) or not np.isfinite(c).all():
        raise RuntimeError("NONFINITE_OR_WRONG_24_CARRIER")
    tensors = bound_math().decode_stf(c, REPO)
    controls = {"main_rows": 131072, "second_rows": 131071,
                "main_blocks": first["block_count"],
                "second_blocks": second["block_count"],
                "selected_native_pixels": first["selected_native_pixels"],
                "nonzero_native_pixels": first["nonzero_native_pixels"],
                "main_gamma": first["gamma"], "second_gamma": second["gamma"],
                "main_l1_plus": first["l1_plus"].tolist(),
                "main_l1_minus": first["l1_minus"].tolist(),
                "second_l1_plus": second["l1_plus"].tolist(),
                "second_l1_minus": second["l1_minus"].tolist(),
                "main_reduction_bound24": first["reduction_bound24"].tolist(),
                "second_reduction_bound24": second["reduction_bound24"].tolist(),
                "split_max_abs": float(np.max(np.abs(c - first["alternate24"]))),
                "half_max_abs": float(np.max(np.abs(c - 2 * first["half24"]))),
                "partition_max_abs": float(np.max(np.abs(c - second["canonical24"])))}
    return c, tensors, controls


def _write_json(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def native(cfg, contract, head_ref, packet_id):
    import numpy as np
    from threadpoolctl import threadpool_info
    sys.path.insert(0, str(OPERATOR.parent))
    with np.load(sealed_ref(contract["numerics"]["support"]), allow_pickle=False) as z:
        support = z["s7_mask_nest64"].copy()
    if (support.shape != (49152,) or support.dtype != np.bool_
            or int(np.count_nonzero(support)) != 30021):
        raise RuntimeError("FROZEN_S7_SUPPORT_DRIFT")
    carrier, tensors, controls = project_with_reader(cfg["source_product"], support)
    pools = threadpool_info()
    if any(int(pool.get("num_threads", 0)) != 1 for pool in pools):
        raise RuntimeError("LOADED_NUMERICAL_THREADPOOL_CAP")
    threads_line = next(line for line in Path("/proc/self/status").read_text().splitlines()
                        if line.startswith("Threads:"))
    if int(threads_line.split()[1]) != 1:
        raise RuntimeError("NATIVE_PROCESS_THREAD_CAP")
    if controls["selected_native_pixels"] != 30741504:
        raise RuntimeError("S7_SELECTED_NATIVE_PIXEL_COUNT_DRIFT")
    if any(not np.isfinite(t).all() for t in tensors):
        raise RuntimeError("NONFINITE_STF")
    run = HERE / "run"
    run.mkdir(exist_ok=True)
    carrier_file = run / "CARRIER_SMICA_EXACT_IMPLICIT.npz"
    if carrier_file.exists():
        raise RuntimeError("ONE_USE_CARRIER_ALREADY_EXISTS")
    np.savez_compressed(carrier_file, canonical24=carrier, E2=tensors[0],
                        E3=tensors[1], B2=tensors[2], B3=tensors[3])
    _write_json(run / "CONTROL_SMICA_EXACT_IMPLICIT.json", controls)
    labels = ([f"E2:{m}" for m in ("0", "1Re", "1Im", "2Re", "2Im")]
              + [f"E3:{m}" for m in ("0", "1Re", "1Im", "2Re", "2Im", "3Re", "3Im")]
              + [f"B2:{m}" for m in ("0", "1Re", "1Im", "2Re", "2Im")]
              + [f"B3:{m}" for m in ("0", "1Re", "1Im", "2Re", "2Im", "3Re", "3Im")])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.bar(range(24), carrier, color=["#356b96"] * 12 + ["#ad6940"] * 12)
    ax.axhline(0, color="black", linewidth=.8)
    ax.set_xticks(range(24), labels, rotation=70, ha="right")
    ax.set_ylabel("Signed canonical coordinate [K_CMB]")
    ax.set_title("PR3 SMICA delivered-map signed24; original selected S7 support")
    fig.text(.01, .01, "Exact-product implicit-row compatibility assumption; descriptive comparator only.", fontsize=8)
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(run / "SMICA_SIGNED24.png", dpi=170)
    plt.close(fig)
    _write_json(run / "RESULT.json", {
        "schema": "htt.smica_exact_implicit_candidate/1",
        "status": "CANDIDATE_REVIEW_REQUIRED", "scientific_admission": "HOLD",
        "component_id": COMPONENT, "packet_id": packet_id,
        "source_profile_id": contract["source_profile_id"],
        "map_header_sha256": "a25bdcde564d4e6041011c497584d2884518252126e172dc35f460f130b25f26",
        "source_product": cfg["source_product"],
        "source_interpretation": "Qualified exact PR3 R3.00 full-map row p is implicit nested pixel p; four indexing cards absent. This is product compatibility, not modern HEALPix format compliance.",
        "harmonic_convention": "Galactic COSMO K_CMB; m0 real then sqrt(2) Re and -sqrt(2) Im for m>0; E2[5], E3[7], B2[5], B3[7].",
        "support": contract["numerics"]["support"],
        "loaded_numerical_threadpools": pools,
        "observed_process_threads_after_projection": 1,
        "account_base": head_ref,
        "carrier": str(carrier_file),
        "control": str(run / "CONTROL_SMICA_EXACT_IMPLICIT.json"),
        "figure": str(run / "SMICA_SIGNED24.png"),
        "claim_scope": "Delivered-map descriptive signed24 comparator only; no native solver, family identification, calibrated Pi or physical F."})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--input-sha", required=True)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--packet-sha", required=True)
    parser.add_argument("--control-receipt", required=True)
    parser.add_argument("--control-receipt-sha", required=True)
    parser.add_argument("--internal-fd", type=int)
    parser.add_argument("--attempt-id")
    args = parser.parse_args()
    cfg, contract, head_ref, packet_id = validate_go(args)
    validate_child_start(args, cfg, contract)
    native(cfg, contract, head_ref, packet_id)


if __name__ == "__main__":
    main()
