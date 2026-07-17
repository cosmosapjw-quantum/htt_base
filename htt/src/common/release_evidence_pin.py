"""Literal-only PR-122 fixed-point trust-root fields.

This module deliberately contains no imports, functions, classes, or runtime
lookups.  The graph-bound verifier constructs and validates the typed pin from
this exact literal mapping.  The mapping remains an explicit commit-reviewed
trust root outside the verifier -> graph -> verifier hash cycle; it is process
configuration, never scientific evidence or independent authorization.
"""

DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS = {
    "graph_path": "docs/generated/pr122_claim_evidence_graph.json",
    "graph_file_sha256": "c165838b0b7bc3fcab075edb82fe07889145f9b3cda8843efbf60e4bf4beed53",
    "graph_ref": "91957d10546783d6668c22a9adcd29e2f21e35e0e2f351364002db106fac7b32",
    "receipt_path": "docs/generated/pr122_release_receipt.json",
    "receipt_file_sha256": "ea331d6a24ac7c651164c3f33bb5e62d33ad3fa867bb083cb1881c17a36bebdf",
    "receipt_id": "ad8d982be6696a430fcc0b021780a44670d3a8102aff7ddfa59bbf3ca83c91f0",
    "parent_receipt_path": "docs/generated/pr122_parent_receipt.json",
    "parent_receipt_file_sha256": "647baf3321af6cf43f6e9248f096528ba827448f04c20a1a949cd52616d2d2fc",
    "parent_receipt_id": "8aebd24008f65fbc12f4a485b78d9d0a91eefcc51c7b34d0769766bd4859c53a",
    "closure_path": "docs/generated/pr122_claim_closure_report.json",
    "closure_file_sha256": "ad0b9105053c293d939581de2b477e4079274fbecbaf1c2a07460d5bfd6ed94f",
    "artifact_manifest_path": "docs/generated/pr122_artifact_manifest.json",
    "artifact_manifest_file_sha256": "20c3ea6d1c868ffe63089facbe15e76bcfb793db01a5429d817102828a3fd23c",
    "authority_registry_ref": "23802d0d5ea9625098961366f533c04b1b4e81b45ef694cbbc941b8d79e308b9",
}

__all__ = ["DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS"]
