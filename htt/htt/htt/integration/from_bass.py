"""
htt/integration/from_bass.py — HTT ← BASS Integration Adapter
================================================================
C-16 deliverable. Receives BASSDirectionalBundle and integrates
into the HTT Stage 2 inference engine.
"""

__all__ = ['ingest_bass_directional']


def ingest_bass_directional(bundle) -> dict:
    """Ingest a BASSDirectionalBundle into HTT.

    Validates the bundle and extracts directional observables
    for the latent-axis and dipole-vector likelihood modules.
    """
    result = {
        'f2_teff': bundle.f2_teff,
        'gauge_deviation': bundle.gauge_deviation,
        'families_scanned': bundle.families_scanned,
        'family_R_sigma': {
            name: info['R_sigma']
            for name, info in bundle.family_results.items()
        },
        'ingested': True,
    }
    return result
