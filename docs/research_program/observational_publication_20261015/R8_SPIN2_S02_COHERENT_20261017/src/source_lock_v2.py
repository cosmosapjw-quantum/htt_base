"""Opt-in v2 Planck PR3 PMASK source lock with independently compared reference.

This is a local/reference bytes contract, NOT publisher-signed provenance or an
observational-physics qualification. Historical v1 SHA metadata stays unchanged.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fits_source_identity import (
    HEX64, SourceIdentityError, audit_source_files, digest_file,
    inspect_planck_pmask, semantic_compare_pmask,
)

LOCK_PATH = Path(__file__).resolve().parents[1] / "research" / "OE_SOURCE_LOCK_V2.json"
# These two sources were already independently admitted under the immutable v1
# contract. Reusing those proofs needs NO repeated ~200-MB reference downloads.
EXISTING_V1_PINS = {
    "common": "c967e45449596c561c940d7ca0d494f1a26d947e6b5a9ef44185fdbf93b036d4",
    "HM": "33226759f339c099818968f777013984f97d5ec2c04e1816f61ae72930b40296",
}
V2_ACCEPTED = {
    "ORIGINAL_V1_LOCK_REUSED_GEOMETRY_ONLY",
    "V2_REFERENCE_LOCK_ADMITTED_GEOMETRY_ONLY",
}


def load_v2_manifest(path=LOCK_PATH):
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if manifest.get("schema") != "htt.planck_pr3_pmask_source_lock/2":
        raise ValueError("UNSUPPORTED_V2_LOCK_SCHEMA")
    source = manifest.get("expected_sha256")
    if not isinstance(source, dict) or set(source) != {"common", "HM", "OE"}:
        raise ValueError("V2_LOCK_KEY_SET_MISMATCH")
    if any(not isinstance(x, str) or HEX64.fullmatch(x) is None for x in source.values()):
        raise ValueError("MALFORMED_V2_LOCK_DIGEST")
    if any(source[k] != h for k, h in EXISTING_V1_PINS.items()):
        raise ValueError("V2_MANIFEST_MUST_REUSE_COMMON_HM_V1_PINS")
    old = manifest.get("historical_v1_OE_sha256")
    if old != "1b2b4138f791b739938485fa0ebcac5f462e04aac3900":
        raise ValueError("HISTORICAL_V1_LOCK_MISMATCH")
    if manifest.get("reference_qualification") != "USER_REPORTED_IRSA_DOWNLOAD__NOT_PUBLISHER_SIGNED":
        raise ValueError("V2_LOCK_UNSUPPORTED_PROVENANCE_TYPE")
    return manifest


def qualify_v2(root, reference_root, *, names, expected_sha, expected_size, nside=2048):
    """Reuse v1-qualified common/HM; qualify ONLY new OE with an independent reference.

    v1 originals do not need a second ~200 MB download. OE local and reference
    paths must be non-aliasing files, byte SHA pinned and PMASK-equal. The tool
    does NOT authenticate a claim that the reference was fetched from NASA/IRSA.
    """
    if set(names) != {"common", "HM", "OE"}:
        raise ValueError("V2_REQUIRES_THREE_CANONICAL_MASK_KEYS")
    if any(expected_sha[k] != v for k, v in EXISTING_V1_PINS.items()):
        raise ValueError("V2_COMMON_HM_PINS_NOT_REUSABLE")
    report = audit_source_files(root, names, expected_sha, expected_size)
    base = Path(root) / "planck/PR3/masks"
    ref_base = None if reference_root is None else Path(reference_root) / "planck/PR3/masks"
    for label, filename in names.items():
        entry = report[label]
        entry["source_lock"] = "v2"
        entry["scientific_status"] = "P2_L01_NOT_READY_FOR_PHYSICAL_CLAIM"
        entry["admission"] = "NOT_ADMITTED"
        entry["structural_status"] = "NOT_EVALUATED"
        if entry["byte_status"] != "BYTE_IDENTICAL":
            entry["reference_status"] = "LOCAL_BYTES_NOT_PINNED"
            continue
        local = base / filename
        try:
            inspect_planck_pmask(local, nside=nside)
        except (KeyError, OSError, ValueError) as exc:
            entry["structural_status"] = "STRUCTURAL_MISMATCH"
            entry["structure_diagnostic"] = str(exc)
            entry["reference_status"] = "LOCAL_FITS_LAYOUT_INVALID"
            continue
        entry["structural_status"] = "PLANCK_PMASK_LAYOUT_VALID"
        if label in EXISTING_V1_PINS:
            entry["reference_status"] = "UNCHANGED_V1_BYTE_LOCK_REUSED"
            entry["semantic_status"] = "NOT_REQUIRED_FOR_V1_BYTE_IDENTITY"
            entry["admission"] = "ORIGINAL_V1_LOCK_REUSED_GEOMETRY_ONLY"
            continue
        entry["provenance_status"] = "REFERENCE_ORIGIN_USER_REPORTED__NOT_INDEPENDENTLY_AUTHENTICATED"
        entry["semantic_status"] = "SEMANTIC_NOT_EVALUATED"
        entry["reference_status"] = "REFERENCE_ROOT_REQUIRED" if ref_base is None else "REFERENCE_NOT_EVALUATED"
        if ref_base is None:
            continue
        ref = ref_base / filename
        entry["reference_path"] = str(ref)
        if not ref.is_file() or ref.is_symlink():
            entry["reference_status"] = "REFERENCE_MISSING_OR_SYMLINK"
            continue
        if local.resolve() == ref.resolve() or os.path.samefile(local, ref):
            entry["reference_status"] = "REFERENCE_ALIASES_LOCAL_FILE"
            continue
        if expected_size is not None and ref.stat().st_size != expected_size:
            entry["reference_status"] = "REFERENCE_SIZE_MISMATCH"
            continue
        rh = digest_file(ref)
        entry["reference_observed_sha256"] = rh
        if rh.lower() != expected_sha[label].lower():
            entry["reference_status"] = "REFERENCE_SHA_MISMATCH"
            continue
        try:
            inspect_planck_pmask(ref, nside=nside)
            comparison = semantic_compare_pmask(local, ref, nside=nside)
        except (KeyError, OSError, ValueError) as exc:
            entry["reference_status"] = "REFERENCE_FITS_LAYOUT_INVALID"
            entry["reference_diagnostic"] = str(exc)
            continue
        entry["semantic_status"] = comparison["semantic_status"]
        entry["semantic_comparison"] = comparison
        if comparison["semantic_status"] != "SEMANTIC_EQUIVALENT_PMASK":
            entry["reference_status"] = "REFERENCE_PMASK_SEMANTIC_MISMATCH"
            continue
        entry["reference_status"] = "REFERENCE_BYTE_IDENTICAL_TO_PINNED_SOURCE"
        entry["admission"] = "V2_REFERENCE_LOCK_ADMITTED_GEOMETRY_ONLY"
    return report


def require_v2_admission(receipt):
    if any(v["admission"] not in V2_ACCEPTED
           for v in receipt.values()):
        raise SourceIdentityError({k: {**v, "byte_status":
            v["byte_status"] if v["byte_status"] != "BYTE_IDENTICAL"
            else v["reference_status"]} for k, v in receipt.items()})
    return {k: {"path": v["path"], "sha256": v["observed_sha256"],
                "source_size_bytes": v["source_size_bytes"]} for k, v in receipt.items()}
