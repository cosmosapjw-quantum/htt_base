"""Cobaya Theory adapter for frame-aware kinematic and shear response.

Phase C of HTT-R38 Observational Convergence.
"""
from __future__ import annotations

import math
from typing import Any, Mapping
import numpy as np
from cobaya.theory import Theory

from common.kinematic_response import (
    KinematicFrameState,
    KinematicResponseModel,
    STF_BASIS,
)

class KinematicResponseTheory(Theory):
    """Cobaya Theory calculating multi-probe kinematic, dipole, and shear responses."""

    def initialize(self):
        """Set up internal constants and reference values."""
        self.c_km_s = 299792.458
        self.stf_basis = STF_BASIS

    def get_requirements(self):
        """No external CAMB/Boltzmann requirements needed for kinematic carrier."""
        return {}

    def calculate(self, state: dict[str, Any], want_derived: bool = True, **params_values_dict):
        """Calculate state given sample parameters."""
        p = params_values_dict
        
        # Extract 3-vectors (assuming units of 10^-3 if scaled, or raw dimensionless)
        scale = 1e-3 if "beta_RO_x_milli" in p else 1.0
        
        if "beta_RO_x_milli" in p:
            bro = np.array([p["beta_RO_x_milli"], p["beta_RO_y_milli"], p["beta_RO_z_milli"]]) * 1e-3
            brm = np.array([p.get("beta_RM_x_milli", 0.0), p.get("beta_RM_y_milli", 0.0), p.get("beta_RM_z_milli", 0.0)]) * 1e-3
            dint = np.array([p.get("d_int_x_milli", 0.0), p.get("d_int_y_milli", 0.0), p.get("d_int_z_milli", 0.0)]) * 1e-3
        else:
            bro = np.array([p.get("beta_RO_x", 0.00123), p.get("beta_RO_y", 0.0), p.get("beta_RO_z", 0.0)])
            brm = np.array([p.get("beta_RM_x", 0.0), p.get("beta_RM_y", 0.0), p.get("beta_RM_z", 0.0)])
            dint = np.array([p.get("d_int_x", 0.0), p.get("d_int_y", 0.0), p.get("d_int_z", 0.0)])
            
        bmo = bro - brm
        d_cmb = bro + dint
        
        # 5 STF shear amplitudes (units of 10^-5 if milli/micro, or dimensionless)
        if any(f"sigma_{i}_micro" in p for i in range(1, 6)):
            stf = np.array([p.get(f"sigma_{i}_micro", 0.0) for i in range(1, 6)]) * 1e-5
        else:
            stf = np.array([p.get(f"sigma_{i}", 0.0) for i in range(1, 6)])
            
        e1 = np.array([p.get("e1_x", 0.0), p.get("e1_y", 0.0), p.get("e1_z", 0.0)])
        b1 = np.array([p.get("b1_x", 0.0), p.get("b1_y", 0.0), p.get("b1_z", 0.0)])
        
        frame_state = KinematicFrameState(
            beta_RO=bro,
            beta_RM=brm,
            beta_MO=bmo,
            d_int=dint,
            stf_shear_amplitudes=stf,
            e1_polar_vector=e1,
            b1_axial_vector=b1,
        )
        model = KinematicResponseModel(frame_state)
        
        # Provide to Cobaya state
        state["kinematic_model"] = model
        state["beta_RO"] = bro
        state["beta_MO"] = bmo
        state["d_CMB"] = d_cmb
        state["stf_shear"] = stf
        
        # Derived parameters for post-processing and chains
        if want_derived:
            state["derived"] = {
                "beta_RO_amp": float(np.linalg.norm(bro)),
                "beta_MO_amp": float(np.linalg.norm(bmo)),
                "d_CMB_amp": float(np.linalg.norm(d_cmb)),
                "d_int_amp": float(np.linalg.norm(dint)),
                "sigma_shear_amp": float(np.linalg.norm(stf)),
            }

    def get_can_support_params(self):
        """Declare which input parameters are supported by this theory."""
        params = []
        for v in ["beta_RO", "beta_RM", "d_int"]:
            for comp in ["x", "y", "z"]:
                params.append(f"{v}_{comp}")
                params.append(f"{v}_{comp}_milli")
        for i in range(1, 6):
            params.append(f"sigma_{i}")
            params.append(f"sigma_{i}_micro")
        for v in ["e1", "b1"]:
            for comp in ["x", "y", "z"]:
                params.append(f"{v}_{comp}")
        return params

    def get_can_provide_params(self):
        """Declare which derived parameters can be provided by this theory."""
        return [
            "beta_RO_amp",
            "beta_MO_amp",
            "d_CMB_amp",
            "d_int_amp",
            "sigma_shear_amp",
        ]

    def get_param(self, p):
        """Return derived parameter value from current state."""
        return self._current_state["derived"].get(p, 0.0)

    def get_kinematic_model(self) -> KinematicResponseModel:
        return self._current_state["kinematic_model"]

