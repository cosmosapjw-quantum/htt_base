__all__ = [
    "ExecutableCampaignEvidence",
    "ExecutableCheckEvidence",
    "build_type_i_reionization_probe_evidence",
    "build_type_i_runtime_validation_evidence",
    "type_i_reionization_probe_payload",
    "type_i_runtime_validation_payload",
]


def __getattr__(name: str) -> object:
    if name in __all__:
        from bass.validation import ver2_campaign_evidence as _evidence

        return getattr(_evidence, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
