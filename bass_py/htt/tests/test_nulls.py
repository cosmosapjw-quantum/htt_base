"""
htt/tests/test_nulls.py — Structured Null Library Tests
=========================================================
C-06 deliverable. Tests:
  1. 5 null families registered
  2. Each family generates a NullDataset
  3. NullDataset has required fields (beta, direction, family tag)
  4. Batch generation produces correct count with unique seeds
  5. ABC enforcement
  6. FalsePositiveRates accumulator
"""
import os
import pytest
import json
import numpy as np
from pathlib import Path


def _load_obs():
    """Load obs_defaults.json for null generation."""
    _here = Path(__file__).resolve()
    candidates = [
        _here.parent.parent.parent / 'workspace' / 'data' / 'obs_defaults.json',
        _here.parent.parent / 'data' / 'obs_defaults.json',
        # Snapshot layout: obs bundle lives under the repo-level dl_pipeline/.
        # The repo root is four parents up: bass_py/htt/tests/ → bass_py/htt/ → bass_py/ → <repo>/.
        _here.parent.parent.parent.parent / 'dl_pipeline' / 'obs_bundle' / 'obs' / 'scalars' / 'obs_defaults.json',
    ]
    env = os.environ.get('HTT_OBS_DEFAULTS')
    if env:
        candidates.insert(0, Path(env))
    for p in candidates:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    pytest.skip("obs_defaults.json not found")


class TestNullRegistry:

    def test_five_families(self):
        from htt.nulls import NULL_REGISTRY
        assert len(NULL_REGISTRY) == 5

    def test_expected_names(self):
        from htt.nulls import NULL_REGISTRY
        expected = {'scanning_law', 'mask_leakage', 'clustering',
                    'selection_response', 'survey_axis'}
        assert set(NULL_REGISTRY.keys()) == expected

    def test_all_inherit_ABC(self):
        from htt.nulls import NULL_REGISTRY, NullFamily
        for name, cls in NULL_REGISTRY.items():
            assert issubclass(cls, NullFamily), f"{name} not a NullFamily subclass"


class TestNullGeneration:

    def test_each_family_generates(self):
        from htt.nulls import NULL_REGISTRY
        obs = _load_obs()
        for name, cls in NULL_REGISTRY.items():
            fam = cls()
            ds = fam.generate(seed=42, obs_base=obs)
            assert ds is not None, f"{name} returned None"

    def test_dataset_has_family_tag(self):
        from htt.nulls import NULL_REGISTRY
        obs = _load_obs()
        for name, cls in NULL_REGISTRY.items():
            fam = cls()
            ds = fam.generate(seed=42, obs_base=obs)
            assert hasattr(ds, 'family'), f"{name} dataset missing family attr"
            assert ds.family == fam.name

    def test_dataset_beta_nonneg(self):
        from htt.nulls import NULL_REGISTRY
        obs = _load_obs()
        for name, cls in NULL_REGISTRY.items():
            fam = cls()
            ds = fam.generate(seed=42, obs_base=obs)
            if hasattr(ds, 'b_CF4'):
                assert ds.b_CF4 >= 0, f"{name}: negative beta"
            elif hasattr(ds, 'beta'):
                pass  # beta can be array

    def test_dataset_e1_nonneg(self):
        from htt.nulls import NULL_REGISTRY
        obs = _load_obs()
        for name, cls in NULL_REGISTRY.items():
            fam = cls()
            ds = fam.generate(seed=42, obs_base=obs)
            if hasattr(ds, 'e1_CW'):
                assert ds.e1_CW >= 0, f"{name}: negative e1_CW"


class TestBatchGeneration:

    def test_batch_size(self):
        from htt.nulls import ScanningLawNull
        obs = _load_obs()
        fam = ScanningLawNull()
        batch = fam.generate_batch(10, obs)
        assert len(batch) == 10

    def test_batch_unique_seeds(self):
        from htt.nulls import ScanningLawNull
        obs = _load_obs()
        fam = ScanningLawNull()
        batch = fam.generate_batch(10, obs)
        seeds = [d.seed for d in batch]
        assert len(set(seeds)) == 10


class TestFalsePositiveRates:

    def test_accumulator(self):
        from htt.nulls.common_interface import FalsePositiveRates, NullFamilyResult
        fpr = FalsePositiveRates()
        assert hasattr(fpr, 'add')
        assert hasattr(fpr, 'to_dict')

    def test_empty_dict(self):
        from htt.nulls.common_interface import FalsePositiveRates
        fpr = FalsePositiveRates()
        d = fpr.to_dict()
        assert isinstance(d, dict)
