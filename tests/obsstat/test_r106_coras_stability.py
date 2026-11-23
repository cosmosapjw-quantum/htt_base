"""R106 CORAS stability helpers: subspace angles, quadratic definitions, residual mean, axes, provenance, writes."""
import json

import numpy as np
import pytest
from numpy.testing import assert_allclose

from scripts.r105 import coras_reduce as cr
from scripts.r106 import coras_stability as cs


def _geometry(rng, p=cs.P):
    a = rng.normal(size=(p, p))
    return {"observed": rng.normal(size=p), "measurement_cov": a @ a.T / p + np.eye(p)}


def test_principal_angles_identity_and_orthogonal():
    q, _ = np.linalg.qr(np.random.default_rng(106).normal(size=(36, 6)))
    assert_allclose(cs.angles(q[:, :3], q[:, :3]), [0, 0, 0], atol=1e-6)
    assert_allclose(cs.angles(q[:, :1], q[:, 1:2]), [90.0], atol=1e-9)


def test_leading_modes_sorted():
    rng = np.random.default_rng(7)
    x = rng.normal(size=(40, 36)) * np.linspace(1, 3, 36)
    vals, vecs = cs.leading(np.cov(x.T), 3)
    assert np.all(np.diff(vals) <= 0) and vecs.shape == (36, 3)


def test_symmetric_frobenius_is_symmetric_and_matches_split_diagnostic():
    rng = np.random.default_rng(3)
    x = rng.normal(size=(64, 36)) * np.linspace(0.5, 2, 36)
    a, b = np.array_split(x, 2)
    ca, cb = cr.cov(a), cr.cov(b)
    assert cs.sym_rel_frobenius(ca, cb) == pytest.approx(cs.sym_rel_frobenius(cb, ca), rel=1e-14)
    assert cs.sym_rel_frobenius(ca, cb) == pytest.approx(cr.split_diagnostic(x)["symmetric_relative_frobenius"], rel=1e-14)
    assert cr.rel_diff(ca, cb) != pytest.approx(cr.rel_diff(cb, ca), rel=1e-6)  # the asymmetric R105 metric
    assert cs.sym_rel_frobenius(ca, ca) == 0.0


def test_describe_quadratic_definitions_and_no_hartlap():
    rng = np.random.default_rng(11)
    g = _geometry(rng)
    mean = rng.normal(size=36) * 0.1
    draws = rng.normal(size=(80, 36)) * 0.3 + 0.2  # nonzero residual mean
    d = cs.describe(draws, mean, g)
    c, rbar = cr.cov(draws), draws.mean(0)
    obs, meas = g["observed"], g["measurement_cov"]
    q = lambda r, m: float(r @ np.linalg.solve(m, r))
    assert d["quadratic_obs_minus_analytic_mean_meas_plus_sample_cov"] == pytest.approx(q(obs - mean, meas + c), rel=1e-10)
    assert d["quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov"] == pytest.approx(
        q(obs - mean - rbar, meas + c), rel=1e-10)
    assert d["quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov_inflated"] == pytest.approx(
        q(obs - mean - rbar, meas + c * (1 + 1 / 80)), rel=1e-10)
    assert d["quadratic_obs_minus_ensemble_mean_meas_only"] == pytest.approx(q(obs - mean - rbar, meas), rel=1e-10)
    assert not any("hartlap" in k for k in d)
    assert np.all(np.diff(d["leading_eigenvalues"]) <= 0)
    # Symmetric draws have zero residual mean: both definitions coincide.
    sym = np.vstack([draws - rbar, -(draws - rbar)])
    e = cs.describe(sym, mean, g)
    assert e["quadratic_obs_minus_analytic_mean_meas_plus_sample_cov"] == pytest.approx(
        e["quadratic_obs_minus_ensemble_mean_meas_plus_sample_cov"], rel=1e-12)


def test_residual_mean_detects_monopole_offset():
    rng = np.random.default_rng(5)
    n = 60
    draws = rng.normal(size=(n, 36))
    draws[:, 0] -= 1.0
    site = {s: np.array([-1.0 + rng.normal(), rng.normal()]) for s in range(n)}
    bins = [dict(radius_Mpch=[0., 60.], n_sites=3), dict(radius_Mpch=[60., 100.], n_sites=4)]
    rm = cs.residual_mean(draws, site, bins, np.random.default_rng(1))
    assert rm["largest_abs_z"][0][0] == 0 and rm["largest_abs_z"][0][1] < -5
    assert rm["per_coefficient"][0]["component"] == "monopole" and rm["per_coefficient"][9]["shell"] == 1
    assert rm["per_coefficient"][0]["sign_flip_p"] == pytest.approx(rm["sign_flip_p_resolution"])
    assert rm["shell_monopoles"]["indices"] == [0, 9, 18, 27]
    assert rm["shell_monopoles"]["hotelling"]["T2"] > 25
    assert rm["site_mean_by_radius"][0]["z"] < -5 and abs(rm["site_mean_by_radius"][1]["z"]) < 4
    assert 0 <= rm["full_36_hotelling"]["share_of_T2_from_trailing_pcs_beyond_10"] <= 1


def test_mc_debias_matches_hartlap_for_sample_only_and_unity_when_measurement_dominates():
    rng = np.random.default_rng(2)
    c = np.diag(np.linspace(1, 2, 36))
    r = {"r": rng.normal(size=36)}
    out = cs.mc_debias(r, np.eye(36) * 1e6, c, 200, 300, np.random.default_rng(4))["r"]
    assert out["debias_factor_truth_over_mean"] == pytest.approx(1.0, abs=1e-5)
    ref = out["sample_only_reference"]
    assert ref["mc_factor"] == pytest.approx(ref["hartlap"], rel=0.03)


def test_subspace_identifies_gap_and_statement():
    rng = np.random.default_rng(9)
    scale = np.r_[np.full(3, 4.0), np.linspace(1.0, 0.8, 33)]
    x = rng.normal(size=(200, 36)) * scale
    sub = cs.subspace(x[:100], x[100:], x, 40, np.random.default_rng(1))
    wa, ua = sub.pop("_pooled")
    assert sub["largest_pooled_gap_k"] == 3
    assert set(sub["principal_angles_deg_by_k"]) == {f"k{k}" for k in range(1, 9)}
    k3 = sub["permutation_null"]["largest_angle_by_k"]["k3"]
    assert k3["null_q05_q50_q95"][1] < 30 and 0 <= k3["fraction_null_ge_observed"] <= 1
    obs = {"pooled": float(wa[0] / wa[2])}
    sub["degenerate_block_check"] = cs.degenerate_block_check(wa, ua, 3, (100, 200), 30, obs, np.random.default_rng(2))
    st = cs.subspace_statement(sub, obs, 100, 200)
    assert st["stable_leading_subspace_dim"] == 3 and "3-dimensional" in st["text"]


def test_axis_compare_identical_and_scaled_runs():
    rng = np.random.default_rng(12)
    g = _geometry(rng)
    d = {s: rng.normal(size=36) * 0.05 for s in range(1, 41)}
    mean = np.zeros(36)
    same = cs.axis_compare(mean, d, {"mean": mean, "draws": dict(d)}, g, 50, np.random.default_rng(1))
    assert same["per_seed_difference_rms_norm"] == 0.0 and same["conditional_mean_change_norm"] == 0.0
    assert same["trace_ratio_other_over_base"]["point"] == pytest.approx(1.0)
    assert same["quadratic_matched_seeds"]["analytic_mean_definition"]["shift"]["point"] == 0.0
    assert same["classification"] == "not_resolved_by_paired_bootstrap"
    assert_allclose(same["leading8_principal_angles_deg"], 0.0, atol=1e-5)
    scaled = cs.axis_compare(mean, d, {"mean": mean, "draws": {s: 1.1 * v for s, v in d.items()}}, g, 50,
                             np.random.default_rng(1))
    assert scaled["trace_ratio_other_over_base"]["point"] == pytest.approx(1.21)
    assert scaled["classification"] == "resolved_truncation_systematic"
    assert scaled["convergence_beyond_tested_value"] == "untested"


def test_write_json_is_atomic_and_no_clobber(tmp_path):
    out = tmp_path / "x.json"
    assert cs.write_json(out, {"a": 1})[0] == "created"
    assert cs.write_json(out, {"a": 1})[0] == "identical_existing"
    with pytest.raises(FileExistsError):
        cs.write_json(out, {"a": 2})
    assert json.loads(out.read_text()) == {"a": 1}
    status, digest = cs.write_json(out, {"a": 2}, supersede=True)
    assert status.startswith("superseded_sha256:") and json.loads(out.read_text()) == {"a": 2}
    assert digest == cs.sha256_file(out)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["x.json"]


def _fake_run(tmp_path, first=1, last=4):
    rng = np.random.default_rng(21)
    n_sites = 6
    theta, phi = rng.uniform(0.2, 2.9, n_sites), rng.uniform(0, 6.0, n_sites)
    ng = np.column_stack((np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)))
    ids = np.arange(1, n_sites + 1)
    radius = np.array([20., 50., 70., 90., 120., 160.])
    geometry = dict(ids=ids, radius=radius, ng=ng, weights=rng.normal(size=(36, n_sites)))
    run = tmp_path / "run"
    run.mkdir()
    sites = run / "sites.tsv"
    np.savetxt(sites, np.column_stack([ids, radius, theta, phi]), fmt=["%d", "%.17g", "%.17g", "%.17g"], delimiter="\t")
    out = {}
    for name in ["mean.tsv", *(f"residual_{s}.tsv" for s in range(first, last + 1))]:
        (run / name).write_text("".join(f"{i}\t{float(v)!r}\n" for i, v in zip(ids, rng.normal(size=n_sites))))
        out[name] = cr._sha(run / name)
    hexa = "0" * 64
    rec = dict(first=first, last=last, groups=n_sites, donor_commit="45ab25635aa32869ce207511d556ea257ab8a591",
               config=dict(radial=36, ell=8, fft=24, smoothing_Mpch=15.0, growth_fsigma8=0.405,
                           external_bulk_galactic_kms=[95, -172, 28]),
               input_sha256={"data/2MRS_group_member_catalog.dat": hexa, "data/CosmicEmu_spectrum_Planck18.dat": hexa},
               source_sha256=hexa, binary_sha256=hexa, sites_sha256=cr._sha(sites), output_sha256=out)
    (run / "run.json").write_text(json.dumps(rec))
    return run, geometry


def test_load_records_run_file_and_rejects_stale_draws(tmp_path):
    run, geometry = _fake_run(tmp_path)
    x = cs.load(run, geometry)
    assert sorted(x["draws"]) == [1, 2, 3, 4] and x["draws"][1].shape == (36,)
    assert x["run_file"]["seed_range"] == [1, 4] and x["run_file"]["run_json_sha256"] == cr._sha(run / "run.json")
    assert [b["n_sites"] for b in x["site_bins"]] == [2, 2, 1, 1]
    (run / "residual_5.tsv").write_text((run / "residual_4.tsv").read_text())
    with pytest.raises(ValueError, match="stale"):
        cs.load(run, geometry)


def test_fft_probe_pairs_only_fft_differences():
    rng = np.random.default_rng(1)

    def run(fft, shift):
        cfg = dict(radial=24, ell=4, fft=fft)
        return dict(identity=dict(config=cfg), run_file={}, draws={s: rng.normal(size=36) * 0.1 + shift for s in range(30)})

    out = cs.fft_probe([run(16, -0.5), run(24, 0.0)])
    assert len(out["fft_only_pairs"]) == 1 and out["fft_only_pairs"][0]["welch_z"][0] < -5


def test_analysis_command_drops_only_the_write_mode_flag():
    assert cs.analysis_command(["py", "-m", "m", "--output", "x.json", "--supersede"]) == ["py", "-m", "m", "--output",
                                                                                        "x.json"]
