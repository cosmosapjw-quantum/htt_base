__all__ = [
    "ExecutableCampaignEvidence",
    "ExecutableCheckEvidence",
    "build_representative_family_sweep_evidence",
    "build_type_i_reionization_probe_evidence",
    "build_type_i_runtime_validation_evidence",
    "GATE_LADDER",
    "GateBundle",
    "GateDecision",
    "collect_gate_bundles",
    "hard_gate_before_fitting",
    "make_gate_bundle",
    "score_branch_readiness",
    "summarize_gate_status",
    "FamilyReadinessRow",
    "PublicationClaimDecision",
    "PublicationClaimError",
    "assert_publication_claim_allowed",
    "build_family_readiness_manifest",
    "evaluate_publication_claim",
    "representative_family_sweep_payload",
    "type_i_reionization_probe_payload",
    "type_i_runtime_validation_payload",
]


def __getattr__(name: str) -> object:
    if name in __all__:
        if name in {
            "GATE_LADDER",
            "GateBundle",
            "GateDecision",
            "collect_gate_bundles",
            "hard_gate_before_fitting",
            "make_gate_bundle",
            "score_branch_readiness",
            "summarize_gate_status",
        }:
            from bass.validation import ver3_gate_stop as _gate_stop

            return getattr(_gate_stop, name)
        if name in {
            "FamilyReadinessRow",
            "PublicationClaimDecision",
            "PublicationClaimError",
            "assert_publication_claim_allowed",
            "build_family_readiness_manifest",
            "evaluate_publication_claim",
        }:
            from bass.validation import publication_readiness as _publication

            return getattr(_publication, name)
        from bass.validation import ver2_campaign_evidence as _evidence

        return getattr(_evidence, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
