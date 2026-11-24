"""R108 SQ-FRAME: catalogue frame registry tests (boost/inverse identity per release; no unmeasured beta)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from obsstat import publication_frame_kinematics as pfk
from obsstat.catalogue_frame_registry import (
    C_KM_S, CatalogueRelease, FrameRegistry, UnmeasuredBetaError, VelocityReference,
    galactic_unit_vector, planck2018_solar_dipole_reference,
)
from scripts.r108.frame_registry_build import fit_frame_velocity, predict_to

REPO = Path(__file__).resolve().parents[2]
REGISTRY_JSON = REPO / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME/CATALOGUE_FRAME_REGISTRY.json"


def _sphere(n: int) -> np.ndarray:
    k = np.arange(n); z = 1 - 2 * (k + 0.5) / n; phi = (np.pi * (3 - np.sqrt(5))) * k
    return np.stack([np.sqrt(1 - z * z) * np.cos(phi), np.sqrt(1 - z * z) * np.sin(phi), z], axis=-1)


def _synthetic_registry() -> FrameRegistry:
    reg = FrameRegistry()
    reg.register_reference(planck2018_solar_dipole_reference())
    reg.register_reference(VelocityReference(
        key="synthetic_fast", moving_frame="A", rest_frame="B", beta_galactic=(0.2, -0.3, 0.1),
        status="published", locator="synthetic test reference, not data"))
    reg.register_release(CatalogueRelease(
        release_id="SYN", name="synthetic", position_frame="ICRS", epoch="J2000", equinox="J2000",
        redshift_frames=("helio", "cmb"), velocity_reference_keys=("synthetic_fast",), conversion_status="registered",
        locators=(("epoch", "x"), ("position_frame", "x"), ("redshift_frames", "x"), ("velocity_reference", "x"))))
    reg.register_release(CatalogueRelease(
        release_id="PLANCK_SYN", name="supplies the Planck 2018 dipole", position_frame="Galactic", epoch="n/a",
        equinox="n/a", redshift_frames=("cmb",), velocity_reference_keys=("planck2018_solar_dipole",),
        conversion_status="registered",
        locators=(("epoch", "x"), ("position_frame", "x"), ("redshift_frames", "x"), ("velocity_reference", "x"))))
    reg.register_reference(VelocityReference(
        key="syn_helio_to_release_cmb", moving_frame="solar_system_barycentre", rest_frame="SYNH_CMB_frame",
        beta_galactic=(-1e-4, -7e-4, 9e-4), status="recovered_from_release", locator="synthetic test reference, not data",
        formula="linear_cz_sum"))
    reg.register_release(CatalogueRelease(
        release_id="SYNH", name="heliocentric + release-CMB velocities", position_frame="ICRS", epoch="J2000",
        equinox="J2000", redshift_frames=("helio", "release cmb"), velocity_reference_keys=("syn_helio_to_release_cmb",),
        conversion_status="registered",
        locators=(("epoch", "x"), ("position_frame", "x"), ("redshift_frames", "x"), ("velocity_reference", "x"))))
    return reg


def _registries():
    regs = [("synthetic", _synthetic_registry())]
    if REGISTRY_JSON.exists():
        regs.append(("R108_json", FrameRegistry.from_json(REGISTRY_JSON)))
    return regs


def test_planck_reference_matches_published_speed_and_direction():
    ref = planck2018_solar_dipole_reference()
    speed = float(np.linalg.norm(ref.beta)) * C_KM_S
    assert abs(speed - 369.82) < 0.01  # Planck 2018 I: 369.82 +- 0.11 km/s
    n = ref.beta / np.linalg.norm(ref.beta)
    assert np.allclose(n, galactic_unit_vector(264.021, 48.253), atol=1e-14)
    assert ref.status == "published" and "Planck 2018" in ref.locator


@pytest.mark.parametrize("name,reg", _registries())
def test_velocity_boost_inverse_identity_per_release(name, reg):
    rng = np.random.default_rng(108)
    pairs = list(reg.releases_with_conversions())
    assert pairs, "every registry must carry at least one registered conversion"
    for rid, key in pairs:
        for _ in range(50):
            b = rng.normal(size=3); b *= rng.uniform(0, 0.5) / np.linalg.norm(b)
            back = reg.velocity_to_rest(key, reg.velocity_to_moving(key, b, release_id=rid), release_id=rid)
            assert np.max(abs(back - b)) <= 1e-12, (rid, key)
            assert np.allclose(reg.velocity_to_moving(key, b, release_id=rid), pfk.relative_beta(b, reg.beta(key)),
                               atol=0, rtol=0)


@pytest.mark.parametrize("name,reg", _registries())
def test_photon_boost_inverse_identity_per_release(name, reg):
    n = _sphere(400)
    z = np.linspace(0.0, 5.0, len(n))
    for rid, key in reg.releases_with_conversions():
        zr, nr = reg.photon_to_rest(key, z, n, release_id=rid)
        zb, nb = reg.photon_to_moving(key, zr, nr, release_id=rid)
        assert np.max(abs(zb - z)) <= 1e-12, (rid, key)
        assert np.max(abs(nb - n)) <= 1e-12, (rid, key)
        assert np.max(abs(np.linalg.norm(nr, axis=1) - 1)) <= 1e-12


def test_exact_photon_transform_first_order_and_aberration():
    reg = _synthetic_registry()
    key = "planck2018_solar_dipole"
    b = reg.beta(key)
    n = _sphere(200)
    z = np.full(len(n), 0.02)
    zr, nr = reg.photon_to_rest(key, z, n, release_id="PLANCK_SYN")
    first = (1.0 + z) * (1.0 + n @ b) - 1.0  # first order in beta at fixed z
    assert np.max(abs(zr - first)) < 2.0 * float(b @ b) * 1.03
    # the linear cz sum used by CF3/CF4 differs from the exact transform at first order: z (beta . n)
    lin = z + n @ b
    assert np.max(abs((zr - lin) - z * (n @ b))) < 2.0 * float(b @ b) * 1.03
    # aberration: angle to the apex obeys cos t_C = (cos t_S - beta)/(1 - beta cos t_S)
    bb = np.linalg.norm(b); bh = b / bb
    cs = n @ bh
    cc = nr @ bh
    assert np.max(abs(cc - (cs - bb) / (1 - bb * cs))) < 1e-14


def test_no_unmeasured_beta_gate():
    reg = _synthetic_registry()
    with pytest.raises(TypeError):
        reg.velocity_to_moving(np.array([0.001, 0, 0]), [0, 0, 0], release_id="SYN")
    with pytest.raises(TypeError):
        reg.photon_to_rest([0.001, 0.0, 0.0], 0.1, [1.0, 0.0, 0.0], release_id="SYN")
    with pytest.raises(TypeError):  # the release whose data are transformed is required
        reg.velocity_to_moving("synthetic_fast", [0, 0, 0])
    with pytest.raises(TypeError):
        reg.photon_to_rest("synthetic_fast", 0.1, [1.0, 0.0, 0.0])
    with pytest.raises(UnmeasuredBetaError):
        reg.velocity_to_moving("not_registered", [0, 0, 0], release_id="SYN")
    with pytest.raises(UnmeasuredBetaError):
        VelocityReference(key="x", moving_frame="a", rest_frame="b", beta_galactic=(0.001, 0, 0),
                          status="assumed", locator="a fiducial value")
    with pytest.raises(UnmeasuredBetaError):
        VelocityReference(key="x", moving_frame="a", rest_frame="b", beta_galactic=(0.001, 0, 0),
                          status="published", locator="")
    with pytest.raises(UnmeasuredBetaError):
        reg.register_release(CatalogueRelease(
            release_id="BAD", name="bad", position_frame="ICRS", epoch="J2000", equinox="J2000",
            redshift_frames=("x",), velocity_reference_keys=("missing_key",), conversion_status="registered",
            locators=(("epoch", "x"), ("position_frame", "x"), ("redshift_frames", "x"), ("velocity_reference", "x"))))
    reg.register_release(CatalogueRelease(
        release_id="NOSTATE", name="cmb only", position_frame="ICRS", epoch="J2000", equinox="J2000",
        redshift_frames=("cmb",), velocity_reference_keys=(), conversion_status="beta_not_stated",
        locators=(("epoch", "x"), ("position_frame", "x"), ("redshift_frames", "x"))))
    with pytest.raises(UnmeasuredBetaError):
        reg.release_reference("NOSTATE", "planck2018_solar_dipole")
    with pytest.raises(UnmeasuredBetaError):
        reg.release_reference("SYN", "planck2018_solar_dipole")  # registered, but not this release's velocity


def _all_transforms(reg, key, rid):
    z, n = 0.05, np.array([0.0, 0.6, 0.8])
    return {
        "velocity_to_moving": lambda: reg.velocity_to_moving(key, [1e-3, 0, 0], release_id=rid),
        "velocity_to_rest": lambda: reg.velocity_to_rest(key, [1e-3, 0, 0], release_id=rid),
        "photon_to_rest": lambda: reg.photon_to_rest(key, z, n, release_id=rid),
        "photon_to_moving": lambda: reg.photon_to_moving(key, z, n, release_id=rid),
        "photon_to_rest_exact": lambda: reg.photon_to_rest(key, z, n, formula="exact_relativistic", release_id=rid),
    }


@pytest.mark.parametrize("status", ["beta_not_stated", "not_applicable"])
def test_every_transformation_of_an_unregistered_release_raises(status):
    """Review-2 FRAME-3: the release-level status is enforced by every transform, for every registered key."""
    reg = _synthetic_registry()
    reg.register_release(CatalogueRelease(
        release_id="NOCONV", name="no conversion", position_frame="ICRS", epoch="J2000", equinox="J2000",
        redshift_frames=("cmb",), velocity_reference_keys=(), conversion_status=status,
        locators=(("epoch", "x"), ("position_frame", "x"), ("redshift_frames", "x"))))
    for key in reg.references:
        for name, call in _all_transforms(reg, key, "NOCONV").items():
            with pytest.raises(UnmeasuredBetaError):
                call()
    for name, call in _all_transforms(reg, "planck2018_solar_dipole", "UNKNOWN_RELEASE").items():
        with pytest.raises(UnmeasuredBetaError):
            call()


def test_external_reference_needs_a_supplier_release_and_a_stated_input_frame():
    reg = _synthetic_registry()
    # Planck dipole applied to heliocentric data of SYNH: input frame (barycentre) is stated by SYNH
    zr, _ = reg.photon_to_rest("planck2018_solar_dipole", 0.05, [0.0, 0.6, 0.8], release_id="SYNH")
    zr_own, _ = reg.photon_to_rest("planck2018_solar_dipole", 0.05, [0.0, 0.6, 0.8], release_id="PLANCK_SYN")
    assert np.array_equal(zr, zr_own)
    b = reg.velocity_to_rest("planck2018_solar_dipole", [1e-3, 0, 0], release_id="SYNH")
    assert np.allclose(b, pfk.relative_beta(np.array([1e-3, 0, 0]), -reg.beta("planck2018_solar_dipole")), atol=0, rtol=0)
    # to_moving would need SYNH data in the Planck CMB frame, which SYNH does not state
    for call in (lambda: reg.photon_to_moving("planck2018_solar_dipole", 0.05, [0.0, 0.6, 0.8], release_id="SYNH"),
                 lambda: reg.velocity_to_moving("planck2018_solar_dipole", [1e-3, 0, 0], release_id="SYNH")):
        with pytest.raises(UnmeasuredBetaError):
            call()
    # a frame of SYN ('A') is not the barycentre: the Planck dipole cannot act on SYN data
    with pytest.raises(UnmeasuredBetaError):
        reg.photon_to_rest("planck2018_solar_dipole", 0.05, [0.0, 0.6, 0.8], release_id="SYN")
    # a registered reference that no registered release states is refused as an external key
    reg.register_reference(VelocityReference(
        key="orphan", moving_frame="solar_system_barycentre", rest_frame="X", beta_galactic=(1e-4, 0, 0),
        status="published", locator="synthetic orphan reference"))
    with pytest.raises(UnmeasuredBetaError):
        reg.photon_to_rest("orphan", 0.05, [0.0, 0.6, 0.8], release_id="SYNH")
    with pytest.raises(ValueError):
        reg.conversion_reference("SYNH", "planck2018_solar_dipole", "sideways")


def test_committed_registry_has_no_unmeasured_beta():
    if not REGISTRY_JSON.exists():
        pytest.skip("registry JSON not built")
    payload = json.loads(REGISTRY_JSON.read_text())
    reg = FrameRegistry.from_dict(payload["registry"])
    allowed = {"published", "recovered_from_release", "measured_repository_estimate"}
    for rid, rel in reg.releases.items():
        if rel.conversion_status == "registered":
            assert rel.velocity_reference_keys
            for k in rel.velocity_reference_keys:
                ref = reg.references[k]
                assert ref.status in allowed and len(ref.locator) > 20
        else:
            assert not rel.velocity_reference_keys
            for k in reg.references:
                with pytest.raises(UnmeasuredBetaError):
                    reg.release_reference(rid, k)
                for name, call in _all_transforms(reg, k, rid).items():
                    with pytest.raises(UnmeasuredBetaError):
                        call()
    # the (release, key) pairs used by frame_cf4_joint.py and frame_lie_flux.py
    cf4 = "CF4_groups_J_ApJ_944_94_table4"
    assert reg.releases[cf4].conversion_status == "registered"
    reg.conversion_reference(cf4, "cf4_t4_helio_to_cmb", "to_rest")
    reg.conversion_reference(cf4, "cf4_t4_helio_to_cmb", "to_moving")
    reg.conversion_reference(cf4, "planck2018_solar_dipole", "to_rest")
    with pytest.raises(UnmeasuredBetaError):
        reg.conversion_reference(cf4, "planck2018_solar_dipole", "to_moving")
    # every recovered reference reproduces the release at integer-rounding level
    for key, rec in payload["frame_velocity_recovery"].items():
        f = rec["fits"][rec["selected_formula"]]
        assert (key in reg.references) == bool(rec["accepted_as_release_beta"])
        if key in reg.references:
            assert f["residual_rms_kms"] < 1.0


def test_fit_frame_velocity_recovers_synthetic_beta():
    rng = np.random.default_rng(7)
    n = rng.normal(size=(4000, 3)); n /= np.linalg.norm(n, axis=1)[:, None]
    vh = rng.uniform(500, 30000, len(n))
    beta = galactic_unit_vector(264.14, 48.26) * (371.0 / C_KM_S)
    for formula in ("linear_cz_sum", "exact_relativistic"):
        vt = np.round(predict_to(np.round(vh), n, beta, formula))
        out = fit_frame_velocity(np.round(vh), vt, n, formula=formula)
        est = np.array(out["beta_galactic"]); cov = np.array(out["covariance_galactic"])
        d = est - beta
        assert float(d @ np.linalg.solve(cov, d)) < 16.0
        assert out["residual_rms_kms"] < 0.5 and out["n_clipped"] == 0
    # wrong formula leaves a z-dependent residual when the data were made with the exact one
    vt = np.round(predict_to(np.round(vh), n, beta, "exact_relativistic"))
    lin = fit_frame_velocity(np.round(vh), vt, n, formula="linear_cz_sum")
    ex = fit_frame_velocity(np.round(vh), vt, n, formula="exact_relativistic")
    assert ex["residual_rms_kms"] < lin["residual_rms_kms"]
