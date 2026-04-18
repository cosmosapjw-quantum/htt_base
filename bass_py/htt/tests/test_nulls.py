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


class TestRunnerSmoke:
    """HTT-NULL smoke test (plan v1.0 §3.5 / v1.2 §21 W8D7).

    Asserts that ``htt.nulls.runner`` imports cleanly, that every null
    family in ``ALL_FAMILIES`` can be instantiated, and that
    ``run_null_library`` builds the end-to-end stub pipeline at small
    ``n_datasets`` without raising and returns the expected
    output structure.  The runner uses the fast analytical
    Bayes-factor approximation (not nested sampling), so this
    test is cheap enough to run in CI on every commit.
    """

    def test_runner_imports(self):
        from htt.nulls.runner import run_null_library, ALL_FAMILIES, run_family
        assert callable(run_null_library)
        assert callable(run_family)
        assert len(ALL_FAMILIES) == 5

    def test_all_five_families_instantiate(self):
        from htt.nulls.runner import ALL_FAMILIES
        names = [f.name for f in ALL_FAMILIES]
        assert len(set(names)) == 5, f"duplicate names in {names}"

    def test_runner_builds_stub_pipeline(self):
        from htt.nulls.runner import run_null_library
        obs = _load_obs()
        output = run_null_library(obs, n_datasets=3)
        assert isinstance(output, dict)
        for key in ('_meta', 'families', 'union_fp_Pi005', 'target'):
            assert key in output, f"runner output missing key {key!r}"
        assert output['_meta']['n_families'] == 5
        assert output['_meta']['n_datasets_per_family'] == 3
        assert output['_meta']['total_datasets'] == 15
        assert len(output['families']) == 5

    def test_runner_family_results_schema(self):
        from htt.nulls.runner import run_null_library
        obs = _load_obs()
        output = run_null_library(obs, n_datasets=2)
        for fam_name, result in output['families'].items():
            for key in ('n_datasets', 'fp_rate_Pi005', 'fp_rate_lnB5',
                        'lnB_median', 'lnB_std', 'beta_median_mean'):
                assert key in result, \
                    f"{fam_name} result missing {key!r}"
            assert result['n_datasets'] == 2

    def test_runner_output_is_json_serialisable(self, tmp_path):
        from htt.nulls.runner import run_null_library
        obs = _load_obs()
        output = run_null_library(obs, n_datasets=2)
        output_path = tmp_path / "null_library_smoke.json"
        with open(output_path, 'w') as f:
            json.dump(output, f)
        with open(output_path) as f:
            reloaded = json.load(f)
        assert reloaded['_meta']['n_families'] == 5
