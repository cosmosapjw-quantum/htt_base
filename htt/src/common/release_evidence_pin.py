"""Literal-only PR-122 fixed-point trust-root fields.

This module deliberately contains no imports, functions, classes, or runtime
lookups.  The graph-bound verifier constructs and validates the typed pin from
this exact literal mapping.  The mapping remains an explicit commit-reviewed
trust root outside the verifier -> graph -> verifier hash cycle; it is process
configuration, never scientific evidence or independent authorization.
"""

DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS = {
    "graph_path": "docs/generated/pr122_claim_evidence_graph.json",
    "graph_file_sha256": "aba2a4285105e85720dc560e08ccbc7f9f6a384f9ffc23e4aa6872d8674e45d6",
    "graph_ref": "86096ceda0436591b4c61b9695ee1172aed2c62a2f4abcbfdca9b04fcea435a3",
    "receipt_path": "docs/generated/pr122_release_receipt.json",
    "receipt_file_sha256": "3c40f202e6e9c46853bea1e03ffffa9881cdffaa210ed480cb2c7be45ec65012",
    "receipt_id": "eda4df392574c5e08a54269b3caea4b1c2f03fba358582636fe2907e9f1bc628",
    "parent_receipt_path": "docs/generated/pr122_parent_receipt.json",
    "parent_receipt_file_sha256": "f141796fe04f5840bfea256174632d62a72875ea7c62cd4fcf1206dfed2db424",
    "parent_receipt_id": "756bf6a094aca545c2e31d301d93417c6d6590447e8d03af01926c49491ea1e7",
    "closure_path": "docs/generated/pr122_claim_closure_report.json",
    "closure_file_sha256": "b29a2129cbad22cdac9cd27df1fa2a1303cb1e8763f8b5e89f39c97085fe7c06",
    "artifact_manifest_path": "docs/generated/pr122_artifact_manifest.json",
    "artifact_manifest_file_sha256": "93113facac0af83de12dac28f0423e2eba0aea9b9b8c3b4ba3750ca8170bcb81",
    "authority_registry_ref": "23802d0d5ea9625098961366f533c04b1b4e81b45ef694cbbc941b8d79e308b9",
}

__all__ = ["DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS"]
