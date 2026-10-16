import sys
from pathlib import Path
import pytest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from spin2_parity_oracle import diagonal_spin2_response

def test_full_sky_spin2_eb_zero():
    q=diagonal_spin2_response(0.)
    assert np.isclose(q['abs_E_to_B_amplitude'],0,atol=1e-14)

def test_true_nonsymmetric_mask_spin2_leak():
    for eps in (0.1,0.2,0.5):
        q=diagonal_spin2_response(eps)
        assert np.isclose(q['abs_E_to_B_amplitude'],2*eps/3,atol=1e-14)
        assert q['spin_plus_response']<q['spin_minus_response']

def test_synthetic_mask_negativity_refused():
    with pytest.raises(ValueError):diagonal_spin2_response(1.001)
