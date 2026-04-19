"""
Phase 5: Tilt history tracking.

Given a background evolution from BASS, extract β(z) and v_tilt(z).
"""
import numpy as np
from dataclasses import dataclass, field

__all__ = ['TiltHistory', 'extract_tilt_history']

@dataclass(frozen=True)
class TiltHistory:
    z_arr: np.ndarray
    beta_arr: np.ndarray
    v_tilt_arr: np.ndarray    # km/s
    status: str = 'EXPLORATORY'

    @property
    def beta_today(self) -> float:
        return float(self.beta_arr[-1])

    @property
    def v_tilt_today(self) -> float:
        return float(self.v_tilt_arr[-1])


def extract_tilt_history(bg_history) -> TiltHistory:
    """Extract tilt history from a BASS background evolution."""
    z = bg_history.z_arr
    beta = bg_history.y_arr[:, 4]  # 5th component is β
    c_kms = 2.998e5  # km/s
    v_tilt = np.tanh(beta) * c_kms
    return TiltHistory(z_arr=z, beta_arr=beta, v_tilt_arr=v_tilt)
