"""bass_py.mio — Model-Independent Observatory (MIO) package.

Landed under INDEPENDENT_TRACKS_PLAN v1.2 §12.2 (MIO-BOOT-01, Week 6
Day 1). Parent plan: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md v3.

MIO is the 4th pillar (beside bass / htt / tsc). It produces
*model-independent diagnostic reports* (not posteriors). G19 hard
separation (v3 §4.5.4): an MIO report must never be treated as, nor
combined with, a posterior — see workspace.contracts.MioCertificate
which raises NotImplementedError from as_posterior_bundle().

Subpackages (Week 6+):
  core/            — ceiling-family certification registry used by F24
  coherence/       — HJ-02 directional coherence (HJ-02a lands Week 6 Day 3-5)
  extraction/      — HJ-01 shear extraction (Week 8+, depends on bass_py W11)
  tension/         — HJ-03 Hubble-tension triangulation (Week 9+)
  decomposition/   — HJ-04 class decomposition (Week 10+)
  diagnostics/     — HJ-05 masked-sky + selection caveats (HJ-05a-lite Week 6 Day 7)
  reporting/       — identified/reporting semantic split used by F25
  interface/       — HJ-06 MioCertificate generator API (Week 6 Day 2)
  bridges/         — HJ-07 re-exports of htt modules that are MIO-owned
                      (PR13AM re-export lands Week 6 Day 6)
  formalism/       — signed x_C departure-coordinate metadata (PR-050)

Not a MIO deliverable: posterior operations. Route those via htt.
"""
from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0-w6d1"
