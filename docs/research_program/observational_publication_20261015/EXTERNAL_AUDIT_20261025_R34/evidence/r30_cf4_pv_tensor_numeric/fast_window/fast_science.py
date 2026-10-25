"""R32 finite Fourier-window evaluator. Import is inert; execute only after GO.

The old science.py remains byte-identical to the accepted direct calculation.
This module changes only its finite window evaluation order. No type-3 error
theorem is inferred from a requested FINUFFT tolerance.
"""
from __future__ import annotations

from fractions import Fraction
import importlib
import math
from pathlib import Path
import sys
import time

import numpy as np

import science as old

ROOT = Path(__file__).resolve().parent
EPS = (1e-9, 1e-12)
U = 2.0 ** -53


class MethodHold(RuntimeError):
    pass


def need(ok, why):
    if not bool(ok):
        raise MethodHold(why)


def exact_reference_expansions(L, refs):
    """Return integer dyadic sums and binary64 expansions with exact equality."""
    unique, inverse = np.unique(refs, return_inverse=True)
    sums = [[0 for _ in unique] for _ in range(5)]
    for p, h in enumerate(inverse):
        for a in range(5):
            v = float(L[a, p])
            need(math.isfinite(v), 'NONFINITE_SAVED_L')
            numerator, denominator = v.as_integer_ratio()
            shift = 1074 - (denominator.bit_length() - 1)
            need(shift >= 0 and denominator & (denominator - 1) == 0,
                 'NON_DYADIC_SAVED_L')
            sums[a][int(h)] += numerator << shift
    expansions = []
    evidence = []
    for a in range(5):
        row = []
        evrow = []
        for h, numerator in enumerate(sums[a]):
            remaining = Fraction(numerator, 1 << 1074)
            terms = []
            while remaining:
                try:
                    term = float(remaining)
                except OverflowError as exc:
                    raise MethodHold('EXACT_REFERENCE_EXPANSION_HOLD overflow') from exc
                need(math.isfinite(term) and term != 0,
                     'EXACT_REFERENCE_EXPANSION_HOLD nonfinite_or_stalled')
                terms.append(term)
                remaining -= Fraction.from_float(term)
                need(len(terms) <= 64, 'EXACT_REFERENCE_EXPANSION_HOLD length')
            need(sum((Fraction.from_float(v) for v in terms), Fraction()) ==
                 Fraction(numerator, 1 << 1074), 'EXACT_REFERENCE_EXPANSION_HOLD equality')
            row.append(tuple(terms))
            evrow.append({'row': int(unique[h]), 'numerator_at_2_minus_1074': str(numerator),
                          'exponent': -1074, 'expansion_hex': [v.hex() for v in terms]})
        expansions.append(row)
        evidence.append(evrow)
    return unique, expansions, evidence


def coefficient_fields(L, nonref, refs, b, expected_columns=35019):
    need(L.shape == (5, len(nonref)) and b.shape[1] == 3 and
         len(nonref) == len(refs) == expected_columns, 'COEFFICIENT_SHAPE')
    need(np.all(np.isfinite(b)), 'NONFINITE_SOURCE_B')
    coeff = (L[:, None, :] * b[nonref].T[None, :, :]).reshape(15, len(nonref))
    need(np.all(np.isfinite(coeff)), 'NONFINITE_SOURCE_COEFFICIENT')
    expected_nonzero=((L[:,None,:]!=0)&(b[nonref].T[None,:,:]!=0)).reshape(15,len(nonref))
    need(not np.any((coeff==0)&expected_nonzero), 'COEFFICIENT_UNDERFLOW_HOLD')
    refs_unique, expansions, evidence = exact_reference_expansions(L, refs)
    q = np.sum(np.abs(coeff), axis=1, dtype=np.longdouble).astype(float)
    need(np.all(np.isfinite(q)), 'NONFINITE_COEFFICIENT_L1')
    return np.ascontiguousarray(coeff, dtype=np.complex128), refs_unique, expansions, evidence, q


def power_two_scales(source_positions):
    scale = np.ones(3)
    for axis in range(3):
        xmax = float(np.max(np.abs(source_positions[:, axis])))
        need(math.isfinite(xmax), 'NONFINITE_COORDINATE')
        if xmax:
            exponent = max(0, math.ceil(math.log2(xmax / (math.pi / 2))))
            scale[axis] = math.ldexp(1.0, exponent)
            while xmax / scale[axis] >= math.pi / 2:
                scale[axis] *= 2.0
    scaled = source_positions / scale
    need(np.all(np.isfinite(scaled)) and np.max(np.abs(scaled)) < math.pi / 2,
         'RESCALE_DOMAIN_HOLD')
    need(np.all((scaled != 0) | (source_positions == 0)), 'RESCALE_UNDERFLOW_HOLD')
    return scale, scaled


def inventory(stages):
    """Exact binary64 key reuse; maps each (band,node,direction) to one target."""
    target = []
    key_to_index = {}
    maps = {}
    for name, order, radial in stages:
        _, _, u, weights = old.angular_rule(order)
        by_band = []
        for band, (lo, hi) in enumerate(old.BANDS):
            k, wk = old.cc_rule(radial, lo, hi)
            indices = np.empty((len(k), len(u)), dtype=np.int64)
            for ik, kval in enumerate(k):
                for iu, direction in enumerate(u):
                    key = (float(kval).hex(), *(float(x).hex() for x in direction))
                    if key not in key_to_index:
                        key_to_index[key] = len(target)
                        target.append((float(kval), *map(float, direction)))
                    indices[ik, iu] = key_to_index[key]
            by_band.append({'k': k, 'radial_weights': wk, 'directions': u,
                            'angular_weights': weights / (4 * math.pi),
                            'target_indices': indices})
        maps[name] = by_band
    target = np.asarray(target, dtype=np.float64)
    need(np.all(np.isfinite(target)) and np.all(target[:, 0] > 0), 'TARGET_DOMAIN')
    return target, maps


def conservative_grid_admission(xscaled, target, scale):
    """Overestimate FFT grid from space-bandwidth extents before Plan allocation.

    The planner may use a different internal grid; the supervisor's measured
    process-tree RSS remains authoritative. This is an admission forecast.
    """
    t = target[:, 1:] * target[:, :1] * scale
    need(np.all(np.isfinite(t)) and np.all((t != 0) | (target[:, 1:] == 0)),
         'TARGET_RESCALE_NONFINITE_OR_UNDERFLOW')
    xspan = np.ptp(xscaled, axis=0)
    tspan = np.ptp(t, axis=0)
    # Type-3 requires a band-limited oversampled grid. Include ample stencil
    # allowance and fifteen fields at both levels, never treating this as a
    # library-specific certified allocation bound.
    dims = np.maximum(32, np.ceil(2 * xspan * tspan / math.pi + 64)).astype(np.int64)
    cells = math.prod(int(d) for d in dims)
    forecast = cells * 16 * 3 + 15 * (len(xscaled) + len(target)) * 16 * 3
    need(forecast < 4 * 1024**3, f'RESOURCE_HOLD grid_forecast_bytes={forecast}')
    return np.ascontiguousarray(t.T), {'grid_dimensions_forecast':dims.tolist(),
                                       'grid_bytes_forecast':int(forecast),
                                       'target_extent':tspan.tolist(),
                                       'source_extent':xspan.tolist()}


def reference_values(target, positions, b, unique, expansions):
    """Compensated direct reference terms; expansions are never rounded to S."""
    out = np.zeros((len(target), 5, 3), dtype=np.complex128)
    xr = positions[unique]
    br = b[unique]
    for start in range(0, len(target), 128):
        sl = slice(start, min(start + 128, len(target)))
        xi = target[sl, 1:] * target[sl, :1]
        phase = xi @ xr.T
        e = np.exp(1j * phase)
        for a in range(5):
            for d in range(3):
                pieces = [e[:, h] * (term * br[h, d])
                          for h in range(len(unique)) for term in expansions[a][h]]
                # math.fsum per real and imaginary component is compensated.
                out[sl, a, d] = [complex(math.fsum(float(v[t].real) for v in pieces),
                                         math.fsum(float(v[t].imag) for v in pieces))
                                 for t in range(len(xi))]
    return out


def run_pair(xscaled, tcols, coeff, target, positions, b, unique, expansions,
             deadline, progress):
    sys.path.insert(0, str(ROOT / '_deps'))
    finufft = importlib.import_module('finufft')
    need(getattr(finufft, '__version__', None) == '2.5.0', 'FINUFFT_VERSION')
    ref = reference_values(target, positions, b, unique, expansions)
    results = []
    timings = []
    for eps in EPS:
        need(time.monotonic() < deadline, 'BUDGET_CONVERGENCE_HOLD before_plan')
        start = time.monotonic()
        plan = finufft.Plan(3, 3, n_trans=15, eps=eps, isign=1,
                           dtype='complex128', nthreads=1, upsampfac=2.0,
                           maxbatchsize=1, showwarn=1, debug=1, fftw=64)
        plan.setpts(xscaled[:, 0], xscaled[:, 1], xscaled[:, 2],
                    tcols[0], tcols[1], tcols[2])
        values = np.asarray(plan.execute(coeff), dtype=np.complex128)
        need(values.shape == (15, len(target)) and np.all(np.isfinite(values)),
             'FINUFFT_OUTPUT_SHAPE_OR_NONFINITE')
        w = np.einsum('td,tad->ta', target[:, 1:],
                      values.T.reshape(len(target), 5, 3) - ref)
        need(np.all(np.isfinite(w)), 'WINDOW_NONFINITE')
        results.append(w)
        timings.append({'eps':eps, 'seconds':time.monotonic()-start,
                        'plan':'type3 3d ntrans15 maxbatchsize1 positive_complex128',
                        'options':{'nthreads':1,'upsampfac':2.0,'maxbatchsize':1,
                                   'showwarn':1,'debug':1,'fftw':64}})
        progress(eps, w, timings[-1])
    return results, timings, ref


def gamma(operations):
    v = operations * U
    need(v < 1, 'ROUNDING_GAMMA_DOMAIN')
    return v / (1 - v)


def roundoff_envelope(target, positions, coeff, q, b, unique, expansions,
                      ref, high):
    """Explicit source/phase/reference bound; excludes FINUFFT internals."""
    # Bounds use absolute sums, rounded upward once. The coefficient product
    # uses two multiplications and reference evaluation uses products plus a
    # compensated sum; gamma bounds here are conservative for the latter.
    reference_scale = np.zeros((5, 3), dtype=float)
    reference_terms=max(sum(len(expansions[a][h]) for h in range(len(unique)))
                        for a in range(5))
    for a in range(5):
        for d in range(3):
            reference_scale[a, d] = math.fsum(abs(v * b[h, d]) for h in range(len(unique))
                                               for v in expansions[a][h])
    q2 = q.reshape(5, 3)
    base = (gamma(4) * q2 + gamma(2 * reference_terms + 8) * reference_scale)
    # Bound separately for every direction and scalar k. Original k*(u.x)
    # and rescaled (k*u*ell)*(x/ell) each incur at most gamma(8) times an
    # absolute dot product; |exp(i p)-exp(i q)| <= |p-q|.
    xmax = np.max(np.abs(positions), axis=0)
    phase = 2 * gamma(8) * target[:, 0] * (np.abs(target[:, 1:]) @ xmax)
    need(np.all(np.isfinite(phase)), 'ROUNDING_PHASE_NONFINITE')
    vector = np.abs(target[:, 1:])
    roundoff = vector @ base.T + phase[:, None] * (vector @ (q2 + reference_scale).T)
    # Include final three-term projection roundoff and guard subnormals.
    roundoff += gamma(8) * (vector @ (q2 + reference_scale).T)
    roundoff += np.nextafter(0.0, 1.0) * 4096
    need(np.all(np.isfinite(roundoff)), 'ROUNDING_BOUND_NONFINITE')
    ratio=(vector @ (q2+reference_scale).T) / np.maximum(abs(high), np.finfo(float).tiny)
    finite_ratio=ratio[np.isfinite(ratio)]
    return np.nextafter(roundoff, np.inf), {'q_ad':q2.tolist(),
          'reference_abs_scales':reference_scale.tolist(),
          'target_cancellation_ratio_max':float(np.max(finite_ratio)) if finite_ratio.size else None,
          'target_cancellation_ratio_nonfinite_count':int(np.sum(~np.isfinite(ratio))),
          'global_rigorous_type3_error_enclosure':'NOT_ESTABLISHED'}


def spectral_and_bound(w, error, indices, weights):
    z = w[indices]
    e = error[indices]
    A = np.einsum('t,ta,tb->ab', weights, z, z.conj()).real
    B = np.einsum('t,ta,tb->ab', weights, abs(z), e) + \
        np.einsum('t,ta,tb->ab', weights, e, abs(z)) + \
        np.einsum('t,ta,tb->ab', weights, e, e)
    return A, np.nextafter(B, np.inf)


def joint_bound(bounds, k, radial, amp):
    out = np.zeros((15, 15), dtype=float)
    for matrix, kval, weight in zip(bounds, k, radial):
        smooth = np.exp(-.5 * (kval * old.RADII / old.H)**2)
        out += weight * old.power(kval, amp) / (2 * math.pi**2) * \
               np.kron(np.outer(smooth, smooth), matrix)
    return np.nextafter(out, np.inf)


def stage_from_windows(stage_map, high, error, amp):
    joints=[]; bounds=[]; spectra=[]
    for band in stage_map:
        matrices=[]; errors=[]
        for idx, weights in zip(band['target_indices'],
                                [band['angular_weights']] * len(band['k'])):
            A, B = spectral_and_bound(high, error, idx, weights)
            matrices.append(A); errors.append(B)
        matrices=np.stack(matrices); errors=np.stack(errors)
        joints.append(old.joint_from_spectral(matrices, band['k'],band['radial_weights'],amp))
        bounds.append(joint_bound(errors,band['k'],band['radial_weights'],amp))
        spectra.append((matrices,errors))
    return joints,bounds,spectra
