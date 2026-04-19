"""A3: Tests for BASS-calibrated D₂ transfer function.

Verifies:
1. bass_shear_to_D2 returns the correct power-law values
2. The scaling slope matches BASS direct computation
3. AniCLASS and BASS give same scaling exponent (~1.0)
4. The comparison function documents the amplitude offset
5. The evidence likelihood is NOT changed (still uses AniCLASS)
"""
import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
for _p in [_root, _root + "/htt", _root + "/bass"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pytest


class TestBASSShearToD2:
    """BASS-calibrated power-law D₂(Σ²)."""

    def test_import(self):
        from htt.core.evidence_models_R03a import bass_shear_to_D2
        assert callable(bass_shear_to_D2)

    def test_power_law_at_1e6(self):
        """D₂(Σ²=10⁻⁶) ≈ 18 μK² from BASS."""
        from htt.core.evidence_models_R03a import bass_shear_to_D2
        D2 = bass_shear_to_D2(1e-6)
        assert 10 < D2 < 30, f"D₂ = {D2:.1f}, expected ~18"

    def test_power_law_at_1e4(self):
        """D₂(Σ²=10⁻⁴) ≈ 1500 μK² from BASS."""
        from htt.core.evidence_models_R03a import bass_shear_to_D2
        D2 = bass_shear_to_D2(1e-4)
        assert 500 < D2 < 3000, f"D₂ = {D2:.1f}"

    def test_monotonically_increasing(self):
        """D₂ increases with Σ²."""
        from htt.core.evidence_models_R03a import bass_shear_to_D2
        S2_arr = np.geomspace(1e-10, 1e-3, 20)
        D2_arr = bass_shear_to_D2(S2_arr)
        assert np.all(np.diff(D2_arr) > 0)

    def test_array_input(self):
        """Accepts numpy arrays."""
        from htt.core.evidence_models_R03a import bass_shear_to_D2
        S2 = np.array([1e-8, 1e-6, 1e-4])
        D2 = bass_shear_to_D2(S2)
        assert D2.shape == (3,)
        assert np.all(D2 > 0)

    def test_zero_gives_zero(self):
        """D₂(0) = 0 (no shear → no quadrupole)."""
        from htt.core.evidence_models_R03a import bass_shear_to_D2
        assert bass_shear_to_D2(0) == 0.0


class TestBASSScalingMatch:
    """BASS and AniCLASS have the same scaling exponent."""

    def test_bass_slope_near_unity(self):
        """BASS fit slope ≈ 0.955, close to the expected ~1.0."""
        from htt.core.evidence_models_R03a import _BASS_D2_SLOPE
        assert 0.9 < _BASS_D2_SLOPE < 1.1

    def test_aniclass_slope_near_unity(self):
        """AniCLASS D₂ ∝ Σ² (linear in Σ²), so slope = 1.0."""
        from htt.core.evidence_models_R03a import shear_to_D2
        S2_a = 1e-8; S2_b = 1e-6
        D2_a = shear_to_D2(S2_a); D2_b = shear_to_D2(S2_b)
        slope = np.log10(D2_b / D2_a) / np.log10(S2_b / S2_a)
        assert 0.9 < slope < 1.1, f"AniCLASS slope = {slope:.3f}"

    def test_slopes_agree_within_10pct(self):
        """BASS and AniCLASS slopes agree within 10%."""
        from htt.core.evidence_models_R03a import _BASS_D2_SLOPE, shear_to_D2
        S2_a = 1e-8; S2_b = 1e-6
        D2_a = shear_to_D2(S2_a); D2_b = shear_to_D2(S2_b)
        ani_slope = np.log10(D2_b / D2_a) / np.log10(S2_b / S2_a)
        assert abs(_BASS_D2_SLOPE - ani_slope) < 0.1


class TestBASSvsAniCLASSComparison:
    """The comparison function correctly documents the offset."""

    def test_comparison_returns_dict(self):
        from htt.core.evidence_models_R03a import bass_vs_aniclass_comparison
        c = bass_vs_aniclass_comparison(1e-6)
        assert isinstance(c, dict)
        assert 'D2_bass_uK2' in c
        assert 'D2_aniclass_uK2' in c
        assert 'ratio_ani_over_bass' in c

    def test_aniclass_much_larger(self):
        """AniCLASS D₂ ≫ BASS D₂ at Σ² = 10⁻⁶ (expected ~10¹³×)."""
        from htt.core.evidence_models_R03a import bass_vs_aniclass_comparison
        c = bass_vs_aniclass_comparison(1e-6)
        assert c['ratio_ani_over_bass'] > 1e10
        assert c['log10_ratio'] > 10

    def test_note_explains_mismatch(self):
        """The note field explains why the mismatch is expected."""
        from htt.core.evidence_models_R03a import bass_vs_aniclass_comparison
        c = bass_vs_aniclass_comparison(1e-6)
        assert 'expected' in c['note'].lower()
        assert 'scaling' in c['note'].lower()


class TestEvidenceLikelihoodUnchanged:
    """The evidence_models likelihood still uses AniCLASS (NOT BASS)."""

    def test_shear_to_D2_unchanged(self):
        """shear_to_D2 at Σ²=10⁻⁶ returns AniCLASS value (not BASS)."""
        from htt.core.evidence_models_R03a import shear_to_D2, bass_shear_to_D2
        D2_likelihood = shear_to_D2(1e-6)
        D2_bass = bass_shear_to_D2(1e-6)
        # The likelihood function must give the AniCLASS value, not BASS
        assert D2_likelihood > D2_bass * 1e10, \
            "shear_to_D2 should return AniCLASS calibration, not BASS"

    def test_predicted_observables_uses_shear_to_D2(self):
        """The model's predicted_observables calls shear_to_D2, not bass_shear_to_D2."""
        import inspect
        from htt.core.evidence_models_R03a import _OrthBase
        src = inspect.getsource(_OrthBase)
        assert 'shear_to_D2' in src
        assert 'bass_shear_to_D2' not in src
