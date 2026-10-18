import numpy as np
import pytest
import healpy as hp
from source_matched_pilot import (nested_selected_mean, validate_pairs,
                                  component_diagnostics, identity, linear_projector,
                                  ring_stream_selected_mean)
from diagnose_and_plot import sensitivity


@pytest.mark.parametrize("vector", [False, True])
def test_ring_gather_reproduces_original_nested_child_average(vector):
    ni, no = 8, 2
    n = hp.nside2npix(ni)
    ring = np.arange(n, dtype=float)**2 + .125
    nested = hp.reorder(ring, r2n=True)
    window = np.arange(n) % 5 != 0
    selected = np.ones(hp.nside2npix(no), bool)
    source = ring.reshape(-1, 16) if vector else ring
    actual, coverage = nested_selected_mean([source], [window], [selected],
        nside_in=ni, nside_out=no, chunk_parents=7)
    a, w = nested.reshape(-1, 16), window.reshape(-1, 16)
    expected = hp.reorder(np.where(w, a, 0.).sum(axis=1)/w.sum(axis=1), n2r=True)
    np.testing.assert_array_equal(actual[0], expected)
    assert coverage[0] == np.min(w.mean(axis=1))
    # A false claim that RING vectors are NESTED would give the wrong result.
    wrong = hp.reorder(np.where(w, ring.reshape(-1, 16), 0.).sum(axis=1)/w.sum(axis=1), n2r=True)
    assert np.max(np.abs(actual[0]-wrong)) > 100


def test_fixed_support_rejects_invalid_included_child():
    field = np.ones(768)
    field[hp.nest2ring(8, 0)] = np.nan
    with pytest.raises(ValueError, match="INVALID_SOURCE_INSIDE"):
        nested_selected_mean([field], [np.ones(768, bool)], [np.ones(48, bool)],
                             nside_in=8, nside_out=2)


def test_excluded_invalid_child_does_not_change_source_operator():
    field = np.ones(768)
    window = np.ones(768, bool)
    window[0] = False
    field[hp.nest2ring(8, 0)] = np.nan
    actual, _ = nested_selected_mean([field], [window], [np.ones(48, bool)],
                                     nside_in=8, nside_out=2)
    np.testing.assert_array_equal(actual, np.ones((1, 48)))


@pytest.mark.parametrize("wrong", [np.zeros(8, int), np.arange(8)[::-1], np.arange(9), np.arange(8.)])
def test_reused_or_unmatched_noise_rejected(wrong):
    with pytest.raises(ValueError, match="EXACT_EIGHT"):
        validate_pairs(np.arange(8), wrong)


def test_unique_paired_ids_accepted():
    validate_pairs(np.arange(8), np.arange(8))


def test_source_identity_compares_actual_bytes(tmp_path):
    path = tmp_path/"source"
    path.write_bytes(b"immutable")
    source = identity(path)
    path.write_bytes(b"different")
    with pytest.raises(ValueError, match="IMMUTABLE_SOURCE_BYTE_MISMATCH"):
        identity(path, source["sha256"])


def test_joint_pilot_retains_dependence_and_never_inverts_covariance():
    coeff = np.random.default_rng(33).normal(size=(8, 2, 96))*1e-6
    result = component_diagnostics(coeff)
    assert result["independent_pair_rows"] == 8
    assert result["centred_sample_rank"] == 7
    assert result["joint_dimension"] == 96
    assert result["covariance_inverted"] is False
    assert result["p_value"] is None
    np.testing.assert_allclose(result["blocks"]["T"]["sum_norm_microK"],
                               np.linalg.norm(coeff.sum(axis=1)[:, :32], axis=1)*1e6)


def test_heldout_low_design_injection_and_signal_noise_linearity():
    rng = np.random.default_rng(240)
    design = rng.normal(size=(100, 7))
    selected = np.arange(100) % 3 != 0
    op, info = linear_projector(design, selected)
    signal, noise = rng.normal(size=(2, 7))
    np.testing.assert_allclose(op@(design@(signal+noise))[selected], signal+noise,
                               atol=2e-14, rtol=0)
    assert info["identity_max_absolute"] < 1e-14


def test_rank_deficient_design_rejected():
    with pytest.raises(ValueError, match="ORIGINAL_OLS_NOT_IDENTIFIABLE"):
        linear_projector(np.ones((12, 3)), np.ones(12, bool))


def test_noise_only_rescaling_is_amplitude_squared_for_all_fields():
    data = np.zeros((8, 2, 96))
    data[:, 1] = np.arange(96)+1
    result = sensitivity(data)
    for field in ("T", "E", "B"):
        for factor in (.95, 1.05):
            np.testing.assert_allclose(result["fields"][field][str(factor)]["fractional_energy_change_per_id"],
                                       factor**2-1, atol=2e-15)
    assert result["independent_realizations"] == 8
    assert result["p_value"] is None


def test_signal_only_is_invariant_to_noise_rescaling():
    data = np.zeros((8, 2, 96))
    data[:, 0] = np.arange(96)+1
    result = sensitivity(data)
    for field in ("T", "E", "B"):
        for factor in ("0.95", "1.05"):
            assert result["fields"][field][factor]["maximum_absolute_fractional_change"] == 0


def test_zero_reference_energy_is_not_silently_regularized():
    with pytest.raises(ValueError, match="ZERO_REFERENCE_ENERGY"):
        sensitivity(np.zeros((8, 2, 96)))


@pytest.mark.parametrize("vector_width", [1, 1024])
def test_sequential_ring_matches_original_gather_with_actual_vector_layout(vector_width):
    ni, no = 64, 8
    nin, nout = hp.nside2npix(ni), hp.nside2npix(no)
    rng = np.random.default_rng(320)
    # Realistic float32 vector columns, differing native masks and coarse support.
    if vector_width > 1:
        # FITS rows physically interleave three 1024-value vectors: row stride
        # is 3*1024*4 bytes, while each logical field has shape (rows,1024).
        backing = (rng.normal(size=(nin//vector_width, 3, vector_width))*1e-5).astype(">f4")
        fields = [backing[:, j, :] for j in range(3)]
        assert fields[0].strides == (3*vector_width*4, 4)
    else:
        fields = [(rng.normal(size=nin)*1e-5).astype(">f4") for _ in range(3)]
    windows = [rng.random(nin) > cut for cut in (.05, .1, .1)]
    masks = [rng.random(nout) > cut for cut in (.2, .1, .1)]
    expected, coverage = nested_selected_mean(fields, windows, masks, nside_in=ni, nside_out=no)
    actual, actual_coverage = ring_stream_selected_mean(fields, windows, masks,
        nside_in=ni, nside_out=no, chunk_pixels=8192)
    np.testing.assert_allclose(actual, expected, atol=2e-20, rtol=2e-14)
    np.testing.assert_array_equal(actual_coverage, coverage)
    for j, mask in enumerate(masks):
        np.testing.assert_array_equal(actual[j, ~mask], 0)


def test_sequential_matches_gather_on_masked_invalid_counterexample():
    ni, no = 8, 2
    field = np.arange(768, dtype=float)+.25
    window = np.ones(768, bool)
    window[0] = False
    field[hp.nest2ring(ni, 0)] = np.nan
    selected = np.ones(48, bool)
    expected, coverage = nested_selected_mean([field], [window], [selected], nside_in=ni, nside_out=no)
    actual, cov = ring_stream_selected_mean([field], [window], [selected],
        nside_in=ni, nside_out=no, chunk_pixels=128)
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(cov, coverage)
    window[0] = True
    with pytest.raises(ValueError, match="INVALID_SOURCE_INSIDE"):
        ring_stream_selected_mean([field], [window], [selected], nside_in=ni, nside_out=no)


def test_sequential_wrong_fits_chunk_alignment_rejected():
    with pytest.raises(ValueError, match="ALIGN_FITS_VECTOR_ROWS"):
        ring_stream_selected_mean([np.ones((48, 16))], [np.ones(768, bool)], [np.ones(48, bool)],
                                 nside_in=8, nside_out=2, chunk_pixels=127)
