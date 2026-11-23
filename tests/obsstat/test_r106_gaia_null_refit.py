"""R106 Gaia null refit helpers: R104 exclusion rule, per-null ranks, composition expectation,
per-source z-linear frame leak, pinned inputs and code identity."""
from hashlib import sha256

import numpy as np
from numpy.testing import assert_allclose
import pytest

from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as m


def _influence_case(offset=0.0):
    meas = np.full((2, 16), offset)
    one = np.full((10, 2, 16), offset)
    one[3, 0, 6] += 5.0   # row-0 E2 top: patch 3
    one[4, 0, 12] += 6.0  # row-0 B2 top: patch 4 (also the row-0 E2+B2 top)
    one[3, 1, 7] += 9.0   # row-1 E2 top: patch 3, equal to the row-0 E2 pick -> take the next one
    one[5, 1, 8] += 2.0   # row-1 E2 second: patch 5
    one[6, 1, 13] += 3.0  # row-1 B2 top: patch 6
    one[9, 0, 3] += 50.0  # a large spin shift must not enter any E2/B2 rule
    return meas, one


@pytest.mark.parametrize("offset", [0.0, 2.5])
def test_select_exclusion_rule_variants_and_distinctness(offset):
    meas, one = _influence_case(offset)
    assert m.select_exclusion(meas, one, "E2") == (3, 5)
    assert m.select_exclusion(meas, one, "B2") == (4, 6)
    assert m.select_exclusion(meas, one, "EB") == (3, 4)


def test_null_rank_gives_permutation_p_only_for_exchangeable_nulls():
    x = np.arange(1, 1001, dtype=float)
    r = m.null_rank(x, 995.5, True)
    assert (r["draws_ge_observed"], r["rank_of_observed_from_top"], r["rank_out_of"]) == (5, 6, 1001)
    assert r["exact_conditional_permutation_p"] == pytest.approx(6 / 1001)
    assert m.null_rank(x, 2000.0, True)["exact_conditional_permutation_p"] == pytest.approx(1 / 1001)
    rank_only = m.null_rank(x, 2000.0, False)
    assert rank_only["exact_conditional_permutation_p"] is None and rank_only["draws_ge_observed"] == 0
    assert rank_only["null_max"] == 1000.0


def test_expected_shell_means_is_the_permutation_expectation():
    rng = np.random.default_rng(106)
    n = 600
    shell = rng.integers(0, 4, n)
    strata = rng.integers(0, 5, n)
    x = rng.normal(size=n) + 0.3 * shell + strata
    exact = m.expected_shell_means(x, shell, strata)
    mc = np.zeros(4)
    ndraw = 3000
    for _ in range(ndraw):
        lab = m.permute_within(shell, strata, rng)
        mc += [x[lab == k].mean() for k in range(4)]
    assert_allclose(exact, mc / ndraw, atol=0.01)
    assert_allclose(m.expected_shell_means(x, shell, np.zeros(n, int)), np.full(4, x.mean()), rtol=1e-12)
    assert_allclose(m.expected_shell_means(x, shell, shell), [x[shell == k].mean() for k in range(4)], rtol=1e-12)


def test_permute_within_keeps_label_counts_per_stratum():
    rng = np.random.default_rng(3)
    labels, strata = rng.integers(0, 4, 500), rng.integers(0, 7, 500)
    lab = m.permute_within(labels, strata, rng)
    for s in range(7):
        assert np.array_equal(np.bincount(lab[strata == s], minlength=4), np.bincount(labels[strata == s], minlength=4))


def test_frame_at_shell_medians_is_annihilated_but_per_source_frame_leaks_as_predicted():
    rng = np.random.default_rng(11)
    n = 4800
    shell = np.repeat(np.arange(4), n // 4)
    patch = np.tile(np.arange(6), n // 6)
    z = shell * 0.6 + 0.4 + rng.uniform(-0.25, 0.25, n) ** 2 * (1 + shell)  # skewed within each shell
    zmed = np.array([np.median(z[shell == k]) for k in range(4)])
    w = g.curvature_rows(zmed)
    X = rng.normal(size=(n, 2, 16)) * (1 + 0.5 * rng.random((n, 1, 1)) * z[:, None, None])
    Y = rng.normal(size=(n, 2))
    keep = np.arange(6)
    f0, s0 = m.group_normal(X, Y, shell, patch)
    y0 = m.curvature(f0, s0, w, keep)
    _, s_med = m.group_normal(X, m.inject_rhs(X, Y, m.frame_coefficients(zmed[shell])), shell, patch)
    _, s_src = m.group_normal(X, m.inject_rhs(X, Y, m.frame_coefficients(z)), shell, patch)
    leak_med = m.curvature(f0, s_med, w, keep) - y0
    leak_src = m.curvature(f0, s_src, w, keep) - y0
    assert np.max(np.abs(leak_med)) < 1e-9
    assert np.max(np.abs(leak_src)) > 1e-3
    Fz, _ = m.group_normal(X * np.sqrt(z)[:, None, None], Y, shell, patch)
    Z = m.effective_redshift_operator(f0[:, keep].sum(1), Fz[:, keep].sum(1))
    slope16 = np.zeros(16)
    slope16[:6] = m.FRAME_SLOPE
    assert_allclose(m.analytic_frame_leak(Z, w, slope16).reshape(-1), leak_src, atol=1e-9 * np.max(np.abs(leak_src)))


def test_pinned_inputs_fail_closed(tmp_path, monkeypatch):
    f = tmp_path / "pinned.bin"
    f.write_bytes(b"r106")
    assert m.check_pinned(f, sha256(b"r106").hexdigest(), "x") == sha256(b"r106").hexdigest()
    with pytest.raises(ValueError):
        m.check_pinned(f, "0" * 64, "x")
    monkeypatch.setattr(m, "FULL_JOIN", tmp_path / "missing.npz")
    with pytest.raises(FileNotFoundError):
        m.excluded_quaia_ids({"all_join_ids": np.array([1])})
    monkeypatch.setattr(m, "FULL_JOIN", f)
    with pytest.raises(ValueError):
        m.excluded_quaia_ids({"all_join_ids": np.array([1])})


def test_code_identity_hashes_script_and_imported_modules():
    ident = m.code_identity()
    assert ident["script"] == "scripts/r106/gaia_null_refit.py"
    assert ident["script_sha256"] == m.sha_file(m.__file__)
    for mod in ("scripts/r103/gaia_frame_curvature.py", "scripts/r105/gaia_frame_parity.py", "scripts/r69/gaia_e2_b2.py"):
        assert ident["module_sha256"][mod] == m.sha_file(m.REPO / mod)
