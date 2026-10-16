import pytest
from htt_gate_precursors.partial_selection import selected_event_odds_interval,bounded_unknown_exceedance


def test_no_selection_distortion_returns_prior():
    for p in [.0,.1,.5,.9,1]:
        assert selected_event_odds_interval(p,1)==pytest.approx((p,p))


def test_sharp_relative_odds_range():
    low,high=selected_event_odds_interval(.2,2)
    assert low==pytest.approx(1/9)
    assert high==pytest.approx(1/3)


def test_known_and_unknown_mass_outer_envelope():
    lo,hi=bounded_unknown_exceedance(.3,.5,2)
    assert lo==pytest.approx(.3/(.3+2*.7))
    assert hi==pytest.approx(2*.8/(2*.8+.2))


def test_unknown_100_percent_is_trivial_without_source():
    assert bounded_unknown_exceedance(0,1,10)==pytest.approx((0,1))


def test_reject_unbound_gamma_and_bad_mass():
    with pytest.raises(ValueError):selected_event_odds_interval(.4,.99)
    with pytest.raises(ValueError):bounded_unknown_exceedance(.7,.5,2)
