"""Source authority comparison of historical R2 and modern geodesic MES."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest

from obsstat.legacy_mes_channel_comparison import (
    compare_branch,LegacyMesChannelError
)

ROOT=Path(__file__).resolve().parents[2]
STUDY=ROOT/"docs/research_program/observational_publication_20261015/legacy_modern_obs_integration_20261015"


class _OriginalFake:
    def bounds_from_epsilon(self,eps1,eps2,eps3,*,frame_correction):
        assert not frame_correction
        bs=5*eps1/3+3*eps2+3*eps3/7
        bw=3*eps1/4+2*eps2+2*eps3/7
        return {"B_sigma":bs,"B_omega":bw,"B_accel":3*eps1/4+eps2+3*eps3/14}


def test_legacy_symbolic_branch_coefficient_witness():
    r=compare_branch(0.,2e-5,3e-5,_OriginalFake())
    assert r["exact_numerical_Bsigma_agreement"]
    assert r["historical_R2_legacy_Bomega"]==pytest.approx(2*2e-5+2*3e-5/7)
    assert r["current_geodesic_Bomega"]==pytest.approx((2/15)*2e-5)
    assert r["historical_over_current_W2_ratio"]>100
    assert r["source_physical_equivalence"].startswith("NOT_ADMITTED")
    assert r["physical_bound_status"]=="WITHHELD"


def test_legacy_R2_real_source_archive_bytes_and_theorem_contract():
    from run_htt_legacy_mes_channel_compare import get_adapter
    obj=get_adapter()
    root=STUDY/"inputs/r2_htt"
    assert hashlib.sha256((root/"htt/bounds.py").read_bytes()).hexdigest()=="1c304927fe9f26636cda6cfadf647d439d9d6f7d5b5ca0900559338f5078c76d"
    assert hashlib.sha256((root/"htt/ssot.py").read_bytes()).hexdigest()=="45ed08cf2fd9649e049c88cb50a3ced8d069fc07efb85c1ead398e3a6e8b8ad8"
    e1,e2,e3=0.,1.070e-5,2.186e-5
    r=compare_branch(e1,e2,e3,obj)
    assert r["exact_numerical_Bsigma_agreement"]
    assert r["historical_over_current_W2_ratio"]>300
    assert r["historical_R2_legacy_Baccel"]>0
    assert r["current_geodesic_A"]=="ZERO_STRUCTURAL_IN_REGISTERED_GEODESIC_LANE"


def test_actual_observed_case_source_identity_and_no_posterior_promotion():
    from run_htt_legacy_mes_channel_compare import get_adapter
    obj=get_adapter()
    p=ROOT/"docs/research_program/observational_publication_20261015/results/S02_real_planck_typed_partial_v1/result.json"
    j=json.loads(p.read_text())
    assert j["source_sky_realization_count"]==1
    assert len(j["per_same_sky_source"])==9
    for name,row in j["per_same_sky_source"].items():
        q=row["conditional_source_mes"]
        r=compare_branch(0.,q["eps2_source_projection"],
                            q["eps3_source_projection"],obj)
        assert 1.5*r["historical_R2_legacy_Bsigma"]**2==pytest.approx(q["U_sigma"],rel=3e-14)
        assert r["historical_over_current_W2_ratio"]>100
    with pytest.raises(LegacyMesChannelError):
        compare_branch(-1.,0.,0.,obj)
