"""PR-248 typed-anchor and numerical-provenance contract tests."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from common.nt2_bracket_authority import require_bracket_agreement
from common.statistical_foundations import (
    AnchorAuthorityKind,
    AnchorConditioning,
    AnchorStatus,
    MESAnchorSpec,
    StatisticalFoundationError,
    quarantined_shear_anchors,
    registered_geodesic_mes_anchors,
)
from htt.core.ssot import (
    C,
    D_ell_from_eps,
    eps_ell,
    eps_ell_legacy_dl_as_cl,
)
from htt.obsstat.egs3_psd_cone import bracket_shell_from_a2a3


REPO = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("ell", "d_ell", "expected"),
    (
        (2, 225.9, 3.5596680056232764e-6),
        (3, 936.9, 6.065226435204114e-6),
    ),
)
def test_dl_conversion_uses_external_value_anchor(
    ell: int, d_ell: float, expected: float
) -> None:
    observed = eps_ell(d_ell, ell)
    assert observed == pytest.approx(expected, rel=0.0, abs=1e-18)
    assert D_ell_from_eps(observed, ell) == pytest.approx(d_ell, rel=1e-15)


def test_legacy_conversion_reproduces_both_known_errors() -> None:
    e2 = eps_ell(C.D2_obs, 2)
    e3 = eps_ell(C.D3_obs, 3)
    assert eps_ell_legacy_dl_as_cl(C.D2_obs, 2) / e2 - 1.0 == pytest.approx(
        -0.022794976194160155
    )
    assert eps_ell_legacy_dl_as_cl(C.D3_obs, 3) / e3 - 1.0 == pytest.approx(
        0.381976597885342
    )


@pytest.mark.parametrize(
    ("value", "ell", "error"),
    (
        (-1.0, 2, ValueError),
        (float("nan"), 2, ValueError),
        (1.0, True, TypeError),
        (1.0, 0, ValueError),
    ),
)
def test_dl_conversion_fails_closed(value: float, ell: int, error: type[Exception]) -> None:
    with pytest.raises(error):
        eps_ell(value, ell)


@pytest.mark.parametrize(
    ("function", "value", "error"),
    (
        (eps_ell, True, TypeError),
        (eps_ell, [1.0, True], TypeError),
        (eps_ell, np.array([], dtype=float), ValueError),
        (D_ell_from_eps, False, TypeError),
        (D_ell_from_eps, [1.0, False], TypeError),
        (D_ell_from_eps, np.array([], dtype=float), ValueError),
    ),
)
def test_dl_conversion_rejects_bool_and_empty_payloads(
    function, value, error: type[Exception]
) -> None:
    with pytest.raises(error):
        function(value, 2)


def _anchors():
    return registered_geodesic_mes_anchors(
        eps1=0.0,
        eps2=C.eps2,
        eps3=C.eps3,
        attribution="SAG residual cosmological dipole",
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )


def test_only_verified_geodesic_numeric_anchors_are_active() -> None:
    anchors = _anchors()
    assert anchors["sigma"].status is AnchorStatus.VERIFIED
    assert anchors["omega"].status is AnchorStatus.VERIFIED
    assert anchors["sigma"].value == pytest.approx(2.6446977390240996e-10)
    assert anchors["omega"].value == pytest.approx(3.3789222980376e-13)
    assert anchors["acceleration"].status is AnchorStatus.NO_MES_ANCHOR
    assert anchors["acceleration"].value is None
    assert anchors["anisotropic_curvature"].status is AnchorStatus.NO_MES_ANCHOR
    assert anchors["anisotropic_curvature"].value is None
    assert all(
        anchor.branch not in {"MES_NG_OMEGA", "MES_NG_ACCEL"}
        for anchor in anchors.values()
    )


def test_forged_or_zero_verified_mes_anchor_cannot_normalize() -> None:
    sigma = _anchors()["sigma"]
    fields = dict(sigma.__dict__)
    fields["value"] = 0.0
    with pytest.raises(StatisticalFoundationError, match="positive"):
        MESAnchorSpec(**fields)

    fields = dict(sigma.__dict__)
    fields["frame"] = "forged frame"
    with pytest.raises(StatisticalFoundationError, match="metadata"):
        MESAnchorSpec(**fields)

    fields = dict(sigma.__dict__)
    fields["branch"] = "MES_NG_SIGMA"
    with pytest.raises(StatisticalFoundationError, match="registered geodesic"):
        MESAnchorSpec(**fields)

    fields = dict(sigma.__dict__)
    fields["value"] = 42.0
    with pytest.raises(StatisticalFoundationError, match="does not match"):
        MESAnchorSpec(**fields)

    fields = dict(sigma.__dict__)
    fields["authority_kind"] = AnchorAuthorityKind.LEGACY
    fields["status"] = AnchorStatus.LEGACY_REPRODUCTION
    legacy = MESAnchorSpec(**fields)
    assert legacy.normalization_allowed is False


def test_anchor_conditioning_and_attribution_are_mandatory() -> None:
    with pytest.raises(StatisticalFoundationError, match="attribution"):
        registered_geodesic_mes_anchors(
            eps1=0.0,
            eps2=C.eps2,
            eps3=C.eps3,
            attribution="",
            conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
        )
    with pytest.raises(StatisticalFoundationError, match="eps1"):
        registered_geodesic_mes_anchors(
            eps1=True,
            eps2=C.eps2,
            eps3=C.eps3,
            attribution="test",
            conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
        )
    with pytest.raises(StatisticalFoundationError, match="conditioning"):
        registered_geodesic_mes_anchors(
            eps1=0.0,
            eps2=C.eps2,
            eps3=C.eps3,
            attribution="test",
            conditioning="REALIZATION_CONDITIONAL",  # type: ignore[arg-type]
        )


def test_frame_correction_and_s2a_ceiling_cannot_normalize_active_results() -> None:
    rows = quarantined_shear_anchors(
        eps1=C.eps1_kin,
        eps2=C.eps2,
        eps3=C.eps3,
        attribution="historical observed dipole",
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )
    assert rows["frame_corrected"].status is AnchorStatus.WITHHELD
    assert rows["frame_corrected"].normalization_allowed is False
    assert "2.69 eps1" in rows["frame_corrected"].withheld_reason
    assert rows["s2a_catwise"].value == 9.25e-6
    assert rows["s2a_catwise"].target_sector == "Sigma2"
    assert rows["s2a_catwise"].normalization_allowed is False


def test_live_likelihood_uses_uncorrected_typed_geodesic_anchor() -> None:
    from htt.core.evidence_models_R03a import (
        BianchiModel,
        BianchiI_orth,
        EPS2,
        EPS3,
        Sig2_max_MES,
        _active_sig2_mes_ceiling,
    )

    eps1 = 0.0
    expected = registered_geodesic_mes_anchors(
        eps1=eps1,
        eps2=EPS2,
        eps3=EPS3,
        attribution="independent test",
        conditioning=AnchorConditioning.REALIZATION_CONDITIONAL,
    )["sigma"].value
    active = _active_sig2_mes_ceiling(eps1)
    legacy_corrected = Sig2_max_MES(1.233e-3)
    assert active == expected
    assert active < legacy_corrected
    midpoint = 0.5 * (active + legacy_corrected)
    assert BianchiModel._mes_ok(midpoint) is False
    assert BianchiModel._mes_ok(-1e-12) is False
    assert BianchiModel._mes_ok(True) is False
    assert BianchiModel._mes_ok(0.0, True) is False
    with pytest.raises(StatisticalFoundationError, match="eps1"):
        _active_sig2_mes_ceiling(True)
    with pytest.raises(StatisticalFoundationError, match="hierarchy"):
        _active_sig2_mes_ceiling(1.233e-3)

    g_only = BianchiI_orth(channels="g")
    above = 2.0 * active
    predicted = g_only.predicted_observables([above])
    assert predicted is not None
    assert np.isfinite(g_only._core_logL(predicted))

    hard = BianchiI_orth(channels="f")
    assert hard.predicted_observables([above]) is None


def test_psd_shell_uses_registered_reciprocal_bracket() -> None:
    a2, a3 = Fraction(1, 1000), Fraction(1, 2000)
    lo, hi = require_bracket_agreement(a2, a3)
    observed = bracket_shell_from_a2a3(float(a2), float(a3))
    assert observed == pytest.approx((float(lo) ** 2, float(hi) ** 2))
    legacy_lower = float(a2) * (4.0 / 21.0) / (1.0 + float(a3 / a2))
    assert float(lo) / legacy_lower == pytest.approx((21.0 / 4.0) ** 2)


def test_legacy_scenario_miskeys_have_explicit_non_cmb_provenance() -> None:
    payload = json.loads(
        (REPO / "htt/workspace/data/obs_defaults.json").read_text(encoding="utf-8")
    )
    assert payload["eps2"] == 1.476e-3
    assert payload["eps3"] == 2.586e-3
    provenance = payload["legacy_fixture_key_provenance"]
    assert "CatWISE eps1" in provenance["eps2"]
    assert "radio eps1" in provenance["eps3"]
    assert "never CMB eps2/eps3" in provenance["allowed_use"]


def test_withdrawn_tilt_normalization_conflict_is_not_reopened() -> None:
    from htt.obsstat.egs3_teff_unification import (
        antipodal_boost_reduction,
        beta_channel_correspondence,
    )

    antipodal = antipodal_boost_reduction()
    single = beta_channel_correspondence()
    assert antipodal["s_squared_equals_t_over_2_plus_t_exact"] is True
    assert single["antipodal_specificity_pin"] is True
    assert single["single_species_R3_coeff"] == "-3/2"
