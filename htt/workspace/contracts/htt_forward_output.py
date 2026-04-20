"""workspace.contracts.htt_forward_output — `HttForwardOutput` schema.

Frozen dataclass for the model-dependent theory bundle that BASS hands to
HTT. Spec source: `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3 §4.5.2 table
and §10.2 (was `workspace/contracts/bass_to_htt.py` in v3 §10.2 — kept
under a scope-descriptive filename since the v1.2 plan §19.1 consolidates
all three contracts into workspace/contracts/).

Hard rules (v3 §4.5.2):
  * NOT to be interpreted as observational data.
  * Cannot be treated as an adequacy certificate by itself — MIO owns
    adequacy reporting.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Mapping, Sequence, Tuple

import numpy as np
from common.contracts import ArtifactManifest


@dataclass(frozen=True)
class HttForwardOutput:
    """Model-dependent forward theory bundle produced by BASS for HTT ingestion."""

    # Identification
    model_name: str                        # e.g. 'BianchiI_tilt'
    bianchi_type: str                      # 'I' | 'V' | 'VII0' | 'VIIh' | 'IX' | 'FLRW'
    axis_galactic_lb_deg: Tuple[float, float]   # (l, b) of model preferred axis

    # Spectral prediction block (ΛCDM + tilt + shear contributions combined)
    ell: np.ndarray                        # 1-D int array
    C_ell_TT: np.ndarray                   # K^2 (same length as ell)
    C_ell_TE: np.ndarray                   # K^2
    C_ell_EE: np.ndarray                   # K^2

    # Direction-resolved prediction (for HTT directional layer)
    directional_summary: Mapping[str, float]

    # Amplitude parameters used by this forward run (model params, NOT posteriors)
    shear_Sigma2: float                    # s^-2
    tilt_beta: float                       # dimensionless

    # Kernel atlas references consumed (hash only — atlas lives in AtlasEntry)
    atlas_entry_hashes: Sequence[str] = field(default_factory=tuple)

    # Provenance
    generated_by: str = ""
    git_commit: str = ""
    config_hash: str = ""
    manifest: ArtifactManifest | None = None

    def __post_init__(self) -> None:
        ell = np.asarray(self.ell)
        if ell.ndim != 1:
            raise ValueError("HttForwardOutput.ell must be 1-D")
        for name in ("C_ell_TT", "C_ell_TE", "C_ell_EE"):
            arr = np.asarray(getattr(self, name))
            if arr.shape != ell.shape:
                raise ValueError(
                    f"HttForwardOutput.{name} shape {arr.shape} != ell shape {ell.shape}"
                )
        if not (-90.0 <= self.axis_galactic_lb_deg[1] <= 90.0):
            raise ValueError(
                f"HttForwardOutput.axis_galactic_lb_deg[1] (b) out of range: "
                f"{self.axis_galactic_lb_deg[1]}"
            )
        if self.shear_Sigma2 < 0.0:
            raise ValueError("HttForwardOutput.shear_Sigma2 must be non-negative")
        if self.manifest is not None and self.manifest.owner != "BASS":
            raise ValueError(
                "HttForwardOutput.manifest.owner must be 'BASS' "
                f"(got {self.manifest.owner!r})"
            )
