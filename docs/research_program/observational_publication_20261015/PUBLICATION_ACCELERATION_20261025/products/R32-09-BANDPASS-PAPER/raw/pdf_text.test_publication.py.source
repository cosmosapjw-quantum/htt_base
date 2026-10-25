"""Source-binding and retained-statistics integration checks, without upstream solves."""
import json
from pathlib import Path
import pytest
import publication

ROOT = Path(__file__).resolve().parent


def test_cached_rank_scope_and_all_six_branches():
    inputs, bindings = publication.load_inputs(ROOT)
    assert inputs['bounded_RESULT.json']['source_sha256'] == bindings['R31_RESULT.json']['sha256']
    stats = publication.summarize(inputs)
    assert len(stats['budget_rows']) == 6
    assert len(stats['r33_rows']) == 24
    assert stats['common_min'] < stats['common_max']
    assert stats['raw_min'] > stats['common_max']
    assert stats['r33_min_angle'] < stats['nominal_F1_angle']


def test_altered_cached_source_is_rejected(tmp_path):
    source = tmp_path/'data.json'
    source.write_text('{}')
    (tmp_path/'SOURCE_BINDINGS.json').write_text(json.dumps({
        'test': {'local_path': 'data.json', 'sha256': '0'*64}}))
    with pytest.raises(ValueError, match='source identity mismatch'):
        publication.load_inputs(tmp_path)


def test_wrong_r31_target_scope_fails_closed():
    inputs, _ = publication.load_inputs(ROOT)
    name = publication.consumer.BRANCHES[0]
    inputs['R31_RESULT.json']['branches'][name]['F1']['full24_identified_target_rank'] = 0
    with pytest.raises(ValueError, match='rank scope changed'):
        publication.summarize(inputs)


def test_wrong_extension_row_scope_is_rejected():
    inputs, _ = publication.load_inputs(ROOT)
    inputs['R33_check_RESULT.json']['branches'].pop(next(iter(inputs['R33_check_RESULT.json']['branches'])))
    with pytest.raises(ValueError, match='twelve paired'):
        publication.summarize(inputs)
