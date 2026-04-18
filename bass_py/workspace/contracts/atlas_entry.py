"""workspace.contracts.atlas_entry — `AtlasEntry` schema.

Frozen dataclass for a BASS theory-atlas entry (e.g. the K_ℓ kernel used
by MIO's non-parametric Σ² extraction). Spec source:
`BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3 §4.5.2 table and §10.2 (was
`workspace/contracts/atlas.py` in v3 §10.2 — filename unified with the
other two contracts under v1.2 plan §19.1).

Hard rules (v3 §4.5.2):
  * NOT observational data.
  * Membership in the atlas does NOT confer posterior meaning on any
    specific model — atlas lookup is an interpolation step, not an
    evidence update.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class AtlasEntry:
    """Single row of the BASS theory atlas (K_ℓ kernel or analogue)."""

    atlas_name: str                        # e.g. 'K_ell_v1', 'Sobolev_A1A5_v2'
    bianchi_type: str                      # 'I' | 'V' | 'VII0' | 'VIIh' | 'IX' | 'FLRW'
    parameter_point: Mapping[str, float]   # {'Sigma2': 1.2e-8, 'beta': 1.33e-3, ...}

    # Tabulated output at this parameter point
    ell: np.ndarray
    kernel_values: np.ndarray              # shape == ell.shape
    kernel_name: str                       # e.g. 'K_ell', 'Sobolev_A1'

    # Provenance
    generated_by: str
    git_commit: str
    config_hash: str
    entry_hash: str                        # unique id for this row

    # Optional caveats
    domain_caveats: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        ell = np.asarray(self.ell)
        vals = np.asarray(self.kernel_values)
        if ell.ndim != 1 or vals.ndim != 1:
            raise ValueError("AtlasEntry ell / kernel_values must be 1-D")
        if ell.shape != vals.shape:
            raise ValueError(
                f"AtlasEntry.kernel_values shape {vals.shape} != "
                f"ell shape {ell.shape}"
            )
        if not self.entry_hash:
            raise ValueError("AtlasEntry.entry_hash must be non-empty")
