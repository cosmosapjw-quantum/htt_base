"""Literal-only PR-122 fixed-point trust-root fields.

This module deliberately contains no imports, functions, classes, or runtime
lookups.  The graph-bound verifier constructs and validates the typed pin from
this exact literal mapping.  The mapping remains an explicit commit-reviewed
trust root outside the verifier -> graph -> verifier hash cycle; it is process
configuration, never scientific evidence or independent authorization.
"""

DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS = {
    "graph_path": "docs/generated/pr122_claim_evidence_graph.json",
    "graph_file_sha256": "55fcb6546aa9b2cbfc264655d7514a97a6dd08cada96a10eaabcece32cc69940",
    "graph_ref": "ae15e1e624d1b16b47d2e64b494848bded68696f0403a5ad0e3c4bbe0da7bf3f",
    "receipt_path": "docs/generated/pr122_release_receipt.json",
    "receipt_file_sha256": "dcb259977b9c0f2f1a48f36fc6bbc10ab629b1bfcb2f1d85aab2621a4a67bd2e",
    "receipt_id": "e53df027b0d71aaece136a88ff8fb36066680ae78f5a2c68e6eeef3b44966881",
    "parent_receipt_path": "docs/generated/pr122_parent_receipt.json",
    "parent_receipt_file_sha256": "c7d36f3bcca9d0228eb3c0c222e4d00df4e881c3fbfe040b86663c81f782c37a",
    "parent_receipt_id": "4c7bbd1d1adca0ef6a11fe5c1238ca30a2c4d12e8492c5bd1204882f960a3165",
    "closure_path": "docs/generated/pr122_claim_closure_report.json",
    "closure_file_sha256": "d6a49a4d3934e21cb2b55ee8077c1048ab21d2796297c8e70bc8e8b371784774",
    "artifact_manifest_path": "docs/generated/pr122_artifact_manifest.json",
    "artifact_manifest_file_sha256": "9c0305aaae6b83e7b1ea517db38d0c89e1120e7ca4449fd57a876a96302b4cba",
    "authority_registry_ref": "23802d0d5ea9625098961366f533c04b1b4e81b45ef694cbbc941b8d79e308b9",
}

__all__ = ["DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS"]
