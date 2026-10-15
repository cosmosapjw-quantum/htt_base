"""Finite mathematical functionals versus HTT physically unknown sectors."""
import copy
import pytest
from obsstat.publication_functionals import (
    finite_functional_image,FunctionalDomainError,
)


def _atoms():
    # Intentionally SYNTHETIC mathematical joint atoms, not observed posteriors.
    return [
      {"sample_id":"a","weight":2,"congruence":"normal-frame",
       "components":{"Sigma2":.4,"W2":.6,"Omega_tilt":0.,"DeltaOmega_k":-.1},
       "U_sigma":.5,"sector_value":.25,"sector_ceiling":.5,
       "depth_F":{"reference":.5,"comparison":.3}},
      {"sample_id":"b","weight":1,"congruence":"normal-frame",
       "components":{"Sigma2":.4,"W2":.1,"Omega_tilt":.1,"DeltaOmega_k":0.},
       "U_sigma":.4,"sector_value":.1,"sector_ceiling":.4,
       "depth_F":{"reference":.25,"comparison":.5}},
      {"sample_id":"c","weight":1,"congruence":"normal-frame",
       "components":{"Sigma2":None,"W2":.05,"Omega_tilt":None,"DeltaOmega_k":.1},
       "U_sigma":None,"sector_value":None,"sector_ceiling":None,
       "depth_F":{"reference":None,"comparison":None}},
    ]


def run(atoms=None, thresholds=(-.6,0.,1.), floor=.01):
    return finite_functional_image(
       _atoms() if atoms is None else atoms,
       thresholds=thresholds,gf_floor=floor,
       common_congruence="normal-frame",reference_bin="low-z",comparison_bin="high-z")


def test_signed_x_negative_not_clipped_and_Q_shear_anchor_only():
    a=run()
    assert a["samples"][0]["x_C"]==pytest.approx(-.3)
    assert a["samples"][0]["Q"]==pytest.approx(-.6)
    assert a["samples"][1]["x_C"]==pytest.approx(.4)
    assert a["samples"][1]["Q"]==pytest.approx(1.)
    assert a["samples"][2]["Q"] is None
    assert a["claims"]["Q_anchor_is_shear_only_not_total_x_bound"]


def test_strict_exceedance_missing_mass_and_threshold_atom():
    a=run()
    assert a["missing_mass"]["Q"]==pytest.approx(.25)
    assert a["Pi_Q_strict_threshold_outer_intervals"][0]["unconditional_outer_interval"]==pytest.approx([.75,1.])
    assert a["Pi_Q_strict_threshold_outer_intervals"][1]["unconditional_outer_interval"]==pytest.approx([.25,.5])
    assert a["Pi_Q_strict_threshold_outer_intervals"][2]["unconditional_outer_interval"]==pytest.approx([0.,.25])  # Q=1 tie excluded
    assert a["missing_mass"]["F"]==pytest.approx(.25)


def test_f_zero_one_limits_and_gf_floor_interval():
    a=run()
    assert a["samples"][0]["F"]==pytest.approx(.5)
    assert a["samples"][1]["F"]==pytest.approx(.25)
    gr=a["G_F"]["outer_interval"]
    assert gr[0]>0 and gr[1]>=gr[0]
    assert a["G_F"]["point_identified"] is False
    assert a["claims"]["F_4_bolometric_is_not_F"] is True


def test_full_known_mass_has_exact_pi_and_gf():
    arr=_atoms()[:2]
    a=run(arr)
    assert a["G_F"]["point_identified"]
    assert a["missing_mass"]["Q"]==0
    assert all(t["unconditional_outer_interval"][0] == t["unconditional_outer_interval"][1]
               for t in a["Pi_Q_strict_threshold_outer_intervals"])


def test_missing_total_denominator_does_not_renormalize_known_mass():
    arr=_atoms()
    arr[1]["U_sigma"]=0.
    got=run(arr)
    assert got["missing_mass"]["Q"]==pytest.approx(.5)
    assert got["samples"][1]["Q"] is None


def test_frame_mismatch_rejected():
    arr=_atoms();arr[1]["congruence"]="matter"
    with pytest.raises(FunctionalDomainError,match="mixed"):
        run(arr)


def test_duplicate_ids_and_negative_weights_rejected():
    arr=_atoms();arr[1]["sample_id"]="a"
    with pytest.raises(FunctionalDomainError,match="duplicate"):
        run(arr)
    arr=_atoms();arr[1]["weight"]=-1
    with pytest.raises(FunctionalDomainError,match="nonnegative"):
        run(arr)


def test_mio_firewall_and_signed_negative_sector_guard():
    arr=_atoms();arr[0]["owner"]="MIO"
    with pytest.raises(FunctionalDomainError,match="MIO"):
        run(arr)
    arr=_atoms();arr[0]["sector_value"]=-.1
    with pytest.raises(FunctionalDomainError,match="sign-clean"):
        run(arr)


def test_pi_t_monotonicity_and_threshold_duplicate_refused():
    a=run(thresholds=(-1.,-.6,0.,1.,2.))
    lo=[v["unconditional_outer_interval"][0] for v in a["Pi_Q_strict_threshold_outer_intervals"]]
    hi=[v["unconditional_outer_interval"][1] for v in a["Pi_Q_strict_threshold_outer_intervals"]]
    assert lo==sorted(lo,reverse=True) and hi==sorted(hi,reverse=True)
    with pytest.raises(FunctionalDomainError,match="unique"):
        run(thresholds=(0.,0.))


def test_unweighted_and_scaled_weights_same_posterior_distribution():
    arr=_atoms()
    a=run(arr)
    for x in arr:x["weight"]*=7.
    b=run(arr)
    assert a["Pi_Q_strict_threshold_outer_intervals"]==b["Pi_Q_strict_threshold_outer_intervals"]
    assert a["G_F"]["outer_interval"]==pytest.approx(b["G_F"]["outer_interval"])
