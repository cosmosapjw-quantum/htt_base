"""mio.coherence — directional-coherence diagnostics (HJ-02).

HJ-02a (Week 6 Day 3-5) lands `directional.py` with the 5-probe
resultant-vector SSOT (CMB / CatWISE / Radio / CF4pp / BiPoSH).

HJ-02b (Week 11 Day 3-4) lands `redshift_binned.py` — z-binned
probe directions + total-drift statistic + permutation p-value.
Builds on HJ-02a (same 5 probes, now tagged with z_eff).

Full HJ-02 (per-channel + time-integrated) is deferred to a later
phase pending bass_py inputs.
"""
from __future__ import annotations

from .directional import (  # noqa: F401
    ARTEFACT_FILENAME as DIRECTIONAL_ARTEFACT_FILENAME,
    DirectionalProbe,
    STANDARD_PROBES,
    coherence_chi2,
    emit_directional_coherence_artefact,
    isotropy_pvalue,
    pairwise_separations,
    resultant_vector,
    to_mio_certificate as to_directional_mio_certificate,
)
from .redshift_binned import (  # noqa: F401
    ARTEFACT_FILENAME as REDSHIFT_ARTEFACT_FILENAME,
    DEFAULT_Z_BINS,
    EXACT_ENUMERATION_MAX_PERMUTATIONS,
    RedshiftBinnedProbe,
    STANDARD_Z_PROBES,
    ZBinResult,
    assign_probes_to_bins,
    drift_pvalue,
    emit_redshift_coherence_artefact,
    pairwise_bin_separations,
    per_bin_resultants,
    to_mio_certificate as to_redshift_mio_certificate,
    total_drift_deg,
)

__all__ = [
    "DEFAULT_Z_BINS",
    "DIRECTIONAL_ARTEFACT_FILENAME",
    "DirectionalProbe",
    "EXACT_ENUMERATION_MAX_PERMUTATIONS",
    "REDSHIFT_ARTEFACT_FILENAME",
    "RedshiftBinnedProbe",
    "STANDARD_PROBES",
    "STANDARD_Z_PROBES",
    "ZBinResult",
    "assign_probes_to_bins",
    "coherence_chi2",
    "drift_pvalue",
    "emit_directional_coherence_artefact",
    "emit_redshift_coherence_artefact",
    "isotropy_pvalue",
    "pairwise_bin_separations",
    "pairwise_separations",
    "per_bin_resultants",
    "resultant_vector",
    "to_directional_mio_certificate",
    "to_redshift_mio_certificate",
    "total_drift_deg",
]
