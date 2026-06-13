"""Depth-resolved local-structure null bank for HTT local/global gates."""
from __future__ import annotations

from htt.nulls.local_boost_depth_null import LocalBoostDepthNull


class ClusteringDipoleDepthNull(LocalBoostDepthNull):
    """Generate a local-structure clustering-dipole depth null bank.

    This reuses the depth/null-bank contract from ``LocalBoostDepthNull`` but
    changes the model label and draw scale. It is still observer-side local
    structure metadata, not a model-dependent inference path.
    """

    null_model_id = "local_structure_clustering_dipole"
    physical_scope = "observer_side_local_structure"
    null_model_scope = "local_structure_depth_null"
    amplitude_multiplier = 0.75
    jitter_multiplier = 1.8


__all__ = ["ClusteringDipoleDepthNull"]
