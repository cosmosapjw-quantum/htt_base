"""Deprecated compatibility alias for the active R03a evidence models.

The historical implementation contained an active channel-c likelihood and is
frozen under ``legacy/cf4_p0/htt_consumers``.  Importers of this deprecated
module now receive the same fail-closed, non-CF4 implementation as
``htt.core.evidence_models_R03a``; no alternate numerical defaults remain.
"""
from htt.core.evidence_models_R03a import *  # noqa: F401,F403
