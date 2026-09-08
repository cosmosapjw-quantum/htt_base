"""Small R8 value types. Numerical enclosures and law admission are separate."""
from dataclasses import dataclass,field
from enum import StrEnum
from fractions import Fraction
import math

class RegionMembership(StrEnum):
    ACCEPT='ACCEPT'
    REJECT='REJECT'
    UNRESOLVED='UNRESOLVED'

@dataclass(frozen=True)
class Bound:
    lo: object
    hi: object
    certificate: dict=field(default_factory=dict)
    def __post_init__(self):
        if math.isnan(self.lo) or math.isnan(self.hi) or self.lo>self.hi:
            raise ValueError('invalid enclosure')

def exact_alpha(alpha):
    if not isinstance(alpha,Fraction) or not 0<alpha<1:
        raise ValueError('alpha must be an exact Fraction strictly between zero and one')
    return alpha
