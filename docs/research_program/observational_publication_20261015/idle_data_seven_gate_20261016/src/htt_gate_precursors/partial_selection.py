"""S04 externally specified selection-odds sensitivity, not fitted astrophysics."""
from __future__ import annotations
from math import isfinite


def _valid(p):
    if not isfinite(p) or not 0<=p<=1:
        raise ValueError('probability outside [0,1]')


def selected_event_odds_interval(p:float,gamma:float):
    """Given selected:event-relative-non-event odds ratio in [1/Gamma,Gamma].

    Sharp for unrestricted two-cell reweighting under this assumed ratio bound.
    Gamma is NOT inferred from CF4 observational files.
    """
    _valid(p)
    if not isfinite(gamma) or gamma<1:raise ValueError('Gamma >= 1 required')
    return p/(p+gamma*(1-p)), gamma*p/(gamma*p+1-p)


def bounded_unknown_exceedance(known_tail:float,unknown_mass:float,gamma:float):
    """Outer bounds with unrestricted completion and a supplied Gamma bound.

    Original parent measure total weight=1, event p in [a,a+u].
    Restriction to physically possible completion may sharpen interval.
    """
    _valid(known_tail);_valid(unknown_mass)
    if known_tail+unknown_mass>1+1e-12:raise ValueError('mass >1')
    lo=selected_event_odds_interval(known_tail,gamma)[0]
    hi=selected_event_odds_interval(min(1,known_tail+unknown_mass),gamma)[1]
    return lo,hi
