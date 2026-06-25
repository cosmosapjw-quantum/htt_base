"""Bridge Bianchi-I tilt moments into the canonical HTT multicomponent schema."""
from __future__ import annotations

import numpy as np
from bass.background.bi_continuation import SpeciesPrimitive, tilt_moments
from htt.common.multicomponent_blocks import BlockSpec, StateBlock, MulticomponentState
from htt.common.stf_canonical import stf_to_coeffs


def bianchi_i_moment_state(species, H: float, kappa: float = 1.0,
                           sigma: np.ndarray | None = None,
                           epoch: str = 'unspecified') -> MulticomponentState:
    moments = tilt_moments(tuple(species), H=H, kappa=kappa)
    blocks = [
        StateBlock(BlockSpec('J_tilt', 'vector', 'dimensionless', 'normal_orthonormal',
                             'n^a', 'multispecies_tilt_flux', epoch, 'odd'), moments.J),
        StateBlock(BlockSpec('Pi_tilt', 'stf2', 'dimensionless', 'normal_orthonormal',
                             'n^a', 'multispecies_tilt_second_moment', epoch, 'even',
                             'canonical_stf'), stf_to_coeffs(moments.Pi)),
        StateBlock(BlockSpec('Omega_tilt', 'scalar', 'dimensionless', 'normal_orthonormal',
                             'n^a', 'multispecies_tilt_trace', epoch, 'even'),
                   np.array([moments.Omega_tilt])),
    ]
    if sigma is not None:
        blocks.append(StateBlock(BlockSpec('sigma', 'stf2', 'inverse_time', 'normal_orthonormal',
                                           'n^a', 'geometry', epoch, 'even', 'canonical_stf'),
                                 stf_to_coeffs(np.asarray(sigma, dtype=float))))
    return MulticomponentState(blocks, metadata={
        'branch': 'restricted_bianchi_i_multifluid',
        'metric_signature': '(-,+,+,+)',
        'c_internal': 1,
        'kappa': kappa,
        'H': H,
    })
