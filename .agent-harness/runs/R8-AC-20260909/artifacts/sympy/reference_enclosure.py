"""Independent exact-input spectral/identity reference; no production imports.

This encloses the SO(3) minimum, not a globally tight solution. Input floats
denote their exact binary64 values. Symbolic cubic root isolation shares the
SymPy engine with production, but this module imports no production arithmetic.
"""
from fractions import Fraction
from functools import lru_cache
from itertools import combinations
import hashlib
import math
from pathlib import Path

import sympy as sp

BITS = 256
SCALE = Fraction(1, 100000)


def _coordinate(v):
    if isinstance(v, (Fraction, sp.Rational, int)):
        return Fraction(v)
    # Preserve source binary64, rather than reinterpret decimal text.
    f = float(v)
    if not math.isfinite(f):
        raise ValueError('reference requires finite exact source coordinates')
    return Fraction.from_float(f)


def _key(row):
    q, o = row
    return tuple(_coordinate(q[i][j]) for i in range(3) for j in range(3)) + tuple(
        _coordinate(o[i][j][k]) for i in range(3) for j in range(3) for k in range(3))


def _sqrt_interval(x):
    x = Fraction(x)
    if x < 0:
        raise ValueError('negative radicand')
    d = 2**BITS
    # Integer inequalities certify floor(sqrt(x)*d), including rational x.
    k = math.isqrt(x.numerator*d*d // x.denominator)
    lo = Fraction(k, d)
    hi = lo if lo*lo == x else Fraction(k+1, d)
    assert lo*lo <= x <= hi*hi
    return lo, hi


def _spectrum(matrix):
    # Independently build the cubic coefficients through trace invariants.
    t = sp.Symbol('lambda', real=True)
    a = sp.Matrix(matrix)
    if a != a.T:
        raise ValueError('symmetric tensor reference requires exact symmetry')
    polynomial = sp.Poly(t**3-sp.trace(a)*t**2+
                         (sp.trace(a)**2-sp.trace(a*a))*t/2-a.det(), t)
    raw = sp.polys.polytools.intervals(polynomial, eps=sp.Rational(1, 2**BITS))
    roots = []
    for interval, multiplicity in raw:
        roots.extend([(Fraction(interval[0]), Fraction(interval[1]))]*multiplicity)
    if len(roots) != 3:
        raise ValueError('reference did not isolate three real roots with multiplicity')
    return tuple(roots)


@lru_cache(maxsize=4096)
def _row_spectra(key):
    q = [key[3*i:3*i+3] for i in range(3)]
    a = [key[9+9*i:9+9*i+9] for i in range(3)]
    gram = [[sum(a[i][k]*a[j][k] for k in range(9)) for j in range(3)] for i in range(3)]
    singular = []
    for lo, hi in _spectrum(gram):
        # Gram is PSD exactly; intersect root enclosure with [0,+inf).
        if hi < 0:
            raise ValueError('PSD Gram acquired a negative isolated root')
        singular.append((_sqrt_interval(max(lo,0))[0], _sqrt_interval(hi)[1]))
    return _spectrum(q), tuple(singular)


def reference_pair(row_a, row_b, qscale=SCALE, oscale=SCALE):
    """Return exact Fraction lower/upper with independent enclosure metadata."""
    qscale, oscale = Fraction(qscale), Fraction(oscale)
    if qscale <= 0 or oscale <= 0:
        raise ValueError('positive scales required')
    a,b = _key(row_a),_key(row_b)
    sa,sb = _row_spectra(a),_row_spectra(b)
    lower_square = Fraction(0)
    for block,scale in enumerate((qscale,oscale)):
        for left,right in zip(sa[block],sb[block]):
            gap = max(Fraction(0),left[0]-right[1],right[0]-left[1])
            lower_square += (gap/scale)**2
    identity_square = sum((x-y)**2 for x,y in zip(a[:9],b[:9]))/qscale**2
    identity_square += sum((x-y)**2 for x,y in zip(a[9:],b[9:]))/oscale**2
    lo = _sqrt_interval(lower_square)[0]
    hi = _sqrt_interval(identity_square)[1]
    assert 0 <= lo <= hi
    return {'lo':lo,'hi':hi,'source_sha256':hashlib.sha256(repr((a,b,qscale,oscale)).encode()).hexdigest(),
            'method':'INDEPENDENT_256_BIT_EXACT_CUBIC_SPECTRAL_LOWER_IDENTITY_SO3_UPPER',
            'precision_bits':BITS,'scope':'EXACT_BINARY64_COMPUTED_TENSOR_STATISTIC_ONLY',
            'upper_witness':((1,0,0),(0,1,0),(0,0,1)),
            'globally_tight':False,'shared_primitive':'SymPy real polynomial root isolation'}


def validate_first_pairs(rows, initialized_bounds, count=100):
    """Compare lexicographic first pairs; fail if initializer loses inclusion.

    Interval inclusion is a tested relation for these registered inputs, not
    an automatic relation between all independently valid distance intervals.
    """
    if type(count) is not int or count < 1:
        raise ValueError('positive deterministic pair count required')
    evidence = []
    for i,j in combinations(range(len(rows)),2):
        if len(evidence) == count:
            break
        ref = reference_pair(rows[i],rows[j])
        lower,upper = map(_coordinate,initialized_bounds[i][j])
        enclosed = lower <= ref['lo'] <= ref['hi'] <= upper
        overlap = max(lower,ref['lo']) <= min(upper,ref['hi'])
        evidence.append({'pair':[i,j],'enclosed':enclosed,'overlap':overlap,
            'input_sha256':ref['source_sha256'],
            'reference_lower':str(ref['lo']),'reference_upper':str(ref['hi']),
            'production_lower':str(lower),'production_upper':str(upper)})
    return {'status':'PASS' if evidence and all(e['enclosed'] and e['overlap'] for e in evidence) else 'FAIL',
            'pairs_requested':count,'pairs_checked':len(evidence),'checks':evidence,
            'reference_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope':'INITIALIZED_PAIR_ENCLOSURES_ON_EXACT_SUPPLIED_COORDINATES; NOT GLOBAL_ORBIT_OPTIMIZATION',
            'bits':BITS,'sympy_version':sp.__version__}
