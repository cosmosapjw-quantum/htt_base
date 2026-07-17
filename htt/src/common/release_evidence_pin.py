"""Literal-only PR-122 fixed-point trust-root fields.

This module deliberately contains no imports, functions, classes, or runtime
lookups.  The graph-bound verifier constructs and validates the typed pin from
this exact literal mapping.  The mapping remains an explicit commit-reviewed
trust root outside the verifier -> graph -> verifier hash cycle; it is process
configuration, never scientific evidence or independent authorization.
"""

DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS = {
    "graph_path": "docs/generated/pr122_claim_evidence_graph.json",
    "graph_file_sha256": "38f4f77ea90cfeae59533fb2cd4545cc214704a667eac14663f6c86fe61e550d",
    "graph_ref": "d247b6344648bd8b5d6fc7ce8d7e9e0774556af298814ecdd11b227aec47c535",
    "receipt_path": "docs/generated/pr122_release_receipt.json",
    "receipt_file_sha256": "a68dbe2fccd06255def8836f04925978b516f0b0228fc9bf623c49193160ab33",
    "receipt_id": "944801886c25e0f9d11f93ddfa978c01aa49c0706c33dab44ee44e467926848d",
    "parent_receipt_path": "docs/generated/pr122_parent_receipt.json",
    "parent_receipt_file_sha256": "91ef021b17cadd26cc8654cb46e791fe09aed7025e48a9c84bb20e3c380c7f7f",
    "parent_receipt_id": "b80ff061514d47207e15caf8807bd52b03875578b3dcab5f015f085df4d926f0",
    "closure_path": "docs/generated/pr122_claim_closure_report.json",
    "closure_file_sha256": "1bf97aa38c132fe360c49bdb61e5ac92681fda851fd13d987139dafdf90305e5",
    "artifact_manifest_path": "docs/generated/pr122_artifact_manifest.json",
    "artifact_manifest_file_sha256": "a96d714c517c55ab7e9128088cc88913dfdd011012583cac1c2f8a227ebaa10f",
    "authority_registry_ref": "23802d0d5ea9625098961366f533c04b1b4e81b45ef694cbbc941b8d79e308b9",
}

__all__ = ["DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS"]
