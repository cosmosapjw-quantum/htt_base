"""R108 SQ-LIE-FLUX: Codazzi flux map sign, ranks, blind directions and the published payload."""
from __future__ import annotations

import numpy as np
import pytest

from scripts.r108.frame_lie_flux import (angle2d, blind_flux_report, codazzi_div_map, codazzi_flux_map,
                                          family_algebras, map_spectrum, wald)


def _vi19(n2: float, n3: float):
    from bass.background.bianchi_types import build_bianchi_algebra
    # build_bianchi_algebra('VI_h', a_twist, n1, n3) puts a on x and n on (y, z); h = a^2/(n1 n3)
    a = np.sqrt(-n2 * n3) / 3.0
    return build_bianchi_algebra("VI_h", a_twist=a, n1=n2, n3=n3)


def test_map_equals_production_divergence_matrix_and_sign_convention():
    from bass.background.bianchi_types import build_bianchi_algebra
    from bass.background.convention_bridge import LEVI_CIVITA_3D, exact_momentum_divergence
    from bass.background.geometry import build_geometry, div_pstf2, pstf_rank2
    from bass.background.tilted_bianchi_state import momentum_constraint_map
    rng = np.random.default_rng(3)
    for alg in family_algebras().values():
        M = codazzi_div_map(alg.a, alg.n)
        assert np.max(abs(M - momentum_constraint_map(alg).matrix)) == 0.0
    alg = build_bianchi_algebra("VI_h", a_twist=2e-4, n1=3e-4, n3=-1.2e-3)
    geom = build_geometry(alg)
    for _ in range(10):
        s = rng.normal(size=(3, 3)); s = pstf_rank2(s + s.T)
        d = exact_momentum_divergence(s, alg.a, alg.n, a_sign=1)
        assert np.allclose(d, div_pstf2(s, geom.Gamma), rtol=1e-12, atol=1e-18)
        q_route = 3.0 * s @ alg.a - np.einsum("ijk,jd,kd->i", LEVI_CIVITA_3D, s, alg.n)
        assert np.allclose(q_route, -d, rtol=1e-12, atol=1e-18)  # Physical flux equals minus the geometric divergence.


def _stf5(sigma):
    from common.stf_metric_bridge import orthonormal_to_stf_matrix
    B = np.column_stack([orthonormal_to_stf_matrix(e, convention="kinematic_response").ravel() for e in np.eye(5)])
    x, *_ = np.linalg.lstsq(B, np.asarray(sigma, float).ravel(), rcond=None)
    assert np.allclose(B @ x, np.asarray(sigma, float).ravel(), rtol=0, atol=1e-14 * max(1.0, np.max(abs(sigma))))
    return x


def test_published_flux_map_is_production_sign():
    """Review-2 FRAME-2: kappa q = M s5 with M = -D holds on an admissible production state."""
    from bass.background.tilted_bianchi_state import momentum_constraint_map
    from bass.transport.coupled_einstein_boltzmann import build_early_family_state
    for alg in family_algebras().values():
        assert np.array_equal(codazzi_flux_map(alg.a, alg.n), -momentum_constraint_map(alg).matrix)
    for fam in ("VI_-1/9", "VI_h", "V"):
        state, _, _ = build_early_family_state(fam, epsilon=1e-5)
        M = codazzi_flux_map(state.algebra.a, state.algebra.n)
        kq = state.kappa * state.total_matter.q
        lhs = M @ _stf5(state.sigma_ab)
        scale = max(float(np.linalg.norm(lhs)), float(np.linalg.norm(kq)), 1e-300)
        assert np.linalg.norm(lhs - kq) <= 1e-10 * scale, fam      # production: kappa q = M s5
        if np.linalg.norm(kq) > 0:
            assert np.linalg.norm(lhs + kq) >= 1.0 * scale, fam     # the opposite sign fails


def test_blind_flux_report_lists_every_left_null_vector():
    """Review-2 FRAME-4: rank-0 maps report a 3-dimensional blind subspace, rank-2 maps one direction."""
    algs = family_algebras()
    for name in ("FLRW", "I"):
        alg = algs[name]
        M = codazzi_flux_map(alg.a, alg.n)
        rep = blind_flux_report(M, alg.a, alg.n, map_spectrum(M))
        assert rep["blind_flux_dimension"] == 3 and "blind_flux_direction" not in rep
        B = np.asarray(rep["blind_flux_basis"])
        assert B.shape == (3, 3) and np.allclose(B @ B.T, np.eye(3), atol=1e-14)
    alg = algs["VI_-1/9"]
    M = codazzi_flux_map(alg.a, alg.n)
    rep = blind_flux_report(M, alg.a, alg.n, map_spectrum(M))
    assert rep["blind_flux_dimension"] == 1 and len(rep["blind_flux_basis"]) == 1
    assert np.allclose(rep["blind_flux_direction"], rep["blind_flux_basis"][0], atol=0)
    for name in ("V", "VII_h(+1)", "VII_h(-1)", "VI_h", "IX"):
        alg = algs[name]
        M = codazzi_flux_map(alg.a, alg.n)
        rep = blind_flux_report(M, alg.a, alg.n, map_spectrum(M))
        assert rep["blind_flux_dimension"] == 0 and rep["blind_flux_basis"] == []


@pytest.fixture(scope="module")
def payload(tmp_path_factory):
    from scripts.r108.frame_lie_flux import REGISTRY_JSON, run
    if not REGISTRY_JSON.exists():
        pytest.skip("registry JSON not built")
    return run(tmp_path_factory.mktemp("lie_flux") / "LIE_FLUX_FRAMES.json")


def _keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield f"{prefix}/{k}"
            yield from _keys(v, f"{prefix}/{k}")


def test_radio_proxy_is_never_a_frame_velocity(payload):
    """Review-2 FRAME-1: the R65 proxy is not published as a velocity, a flux candidate or a scale row."""
    assert set(payload["candidate_flux_directions"]) == {"cf4_matter_in_cmb_frame"}
    assert set(payload["codazzi"]["flux_scale_table"]["rows"]) == {"cf4"}
    assert not [k for k in payload["measured_differences"] if "radio" in k]
    assert "radio" not in payload["frames"]
    proxy = payload["radio_count_dipole_proxy"]
    assert "not a physical speed measurement" in " ".join(proxy["r65_meaning"])
    for blk in (proxy, payload["radio_proxy_comparisons"]):
        assert not [k for k in _keys(blk) if "kms" in k or "speed" in k]
    assert payload["radio_proxy_comparisons"]
    for k, v in payload["radio_proxy_comparisons"].items():
        assert k.startswith("radio_count_dipole_proxy_minus_cmb_xy_alpha_")
        assert "not a physical speed measurement" in v["meaning"]
    assert payload["blocked"]["radio_frame_velocity"]["status"] == "BLOCKED"
    assert payload["labels"]["radio_frame_velocity"] == "BLOCKED"


def test_current_payload_codazzi_convention_and_physical_ic_sign(payload):
    """Review-2 FRAME-2/FRAME-4 on the published payload."""
    cod = payload["codazzi"]
    assert cod["convention_used"].startswith("production: kappa q_i = (M s5)_i with M = -D")
    for fam, e in cod["families"].items():
        assert e["max_abs_M_plus_production_divergence_matrix"] == 0.0, fam
        assert "M_div_codazzi_tilt_rhs_convention" not in e
        assert e["blind_flux_dimension"] == 3 - e["rank"] == len(e["blind_flux_basis"]), fam
    for source in cod["production_sign_sources"]:
        assert source["lines"], source["needle"]
    audit = cod["sign_convention_audit"]
    state = audit["production_state_VI_-1/9_eps1e-5"]
    assert state["production_residual_div_plus_kappa_q_rel"] < 1e-10
    assert state["constraints_helper_residual_rel"] < 1e-10
    ic = audit["initial_conditions_projection_VI_h_full_rank"]
    assert ic["production_residual_div_plus_kappa_q_rel"] < 1e-10
    assert abs(ic["div_sigma_minus_kappa_q_rel"] - 2.0) < 1e-10
    assert payload["code_sha256"]["scripts/r108/frame_lie_flux.py"] and payload["git"]["head"]


def test_family_ranks():
    ranks = {k: map_spectrum(codazzi_div_map(a.a, a.n))["rank"] for k, a in family_algebras().items()}
    assert ranks["FLRW"] == 0 and ranks["I"] == 0
    for k in ("V", "VII_h(+1)", "VII_h(-1)", "VI_h", "IX"):
        assert ranks[k] == 3, k
    assert ranks["VI_-1/9"] == 2


@pytest.mark.parametrize("n2,n3", [(3e-4, -1.2e-3), (0.01, -0.0225), (1.0, -1.0), (2.0, -0.5), (0.3, -7.0)])
def test_vi19_blind_direction_closed_form(n2, n3):
    alg = _vi19(n2, n3)
    M = codazzi_div_map(alg.a, alg.n)
    sp = map_spectrum(M)
    assert sp["rank"] == 2
    ell = np.asarray(sp["left_null_directions"][0])
    expect = np.array([0.0, np.sqrt(n2), np.sqrt(-n3)]); expect /= np.linalg.norm(expect)
    assert abs(abs(ell @ expect) - 1.0) < 1e-12
    assert np.linalg.norm(ell @ M) <= 1e-12 * np.linalg.norm(M)
    assert abs(ell @ alg.a) <= 1e-12 * np.linalg.norm(alg.a)
    # sign of the convention does not move the blind direction
    ell2 = np.asarray(map_spectrum(-M)["left_null_directions"][0])
    assert abs(abs(ell2 @ ell) - 1.0) < 1e-12


def test_generic_vi_h_is_full_rank():
    from bass.background.bianchi_types import build_bianchi_algebra
    for h in (-0.05, -0.5, -0.2):
        n2, n3 = 1.0, -2.0
        alg = build_bianchi_algebra("VI_h", a_twist=np.sqrt(h * n2 * n3), n1=n2, n3=n3)  # h = a^2/(n1 n3)
        assert map_spectrum(codazzi_div_map(alg.a, alg.n))["rank"] == 3


def test_helpers():
    assert wald([3.0, 4.0], np.eye(2)) == pytest.approx(25.0)
    assert angle2d([1, 0], [0, 2]) == pytest.approx(90.0)
