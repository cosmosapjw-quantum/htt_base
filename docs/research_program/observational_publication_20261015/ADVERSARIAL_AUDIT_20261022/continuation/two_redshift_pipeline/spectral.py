"""A22-04 finite spectral photon experiment and four-parameter template refit."""
from pathlib import Path
import hashlib
import json
import math

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
H_PLANCK, C_MS, C_KMS = 6.62607015e-34, 299792458., 299792.458
G_MAG = 5 / np.log(10.)
BANDS = [(400., 500.), (500., 650.), (650., 800.)]
PHASE = np.array([-8., -2., 4., 12., 20.])
P0 = np.array([np.log(2e-15), .35, .08, 3.])
BETA = np.array([.03, -.02, .01])
LIMITS = dict(spectral_relative=1e-10, integration_relative=1e-10,
              fit_relative=1e-9, amplitude_mag=1e-8, shape=1e-7,
              peak_days=1e-6, jacobian_relative_rank=1e-10)


def doppler(n, beta):
    n, b = np.asarray(n, float), np.asarray(beta, float)
    if n.shape != (3,) or b.shape != (3,) or not np.isfinite([n, b]).all() or not np.isclose(n @ n, 1, atol=1e-13, rtol=0):
        raise ValueError('finite unit sourceward direction and beta required')
    b2 = b @ b
    if not 0 <= b2 < 1:
        raise ValueError('subluminal beta required')
    gamma = 1 / np.sqrt(1-b2)
    return gamma * (1 + b @ n)


def spectrum(phase, wavelength, x1, color):
    p, w = np.broadcast_arrays(phase, wavelength)
    if not np.isfinite(p).all() or not np.isfinite(w).all() or np.any((w < 250) | (w > 1000)):
        raise ValueError('spectral fixture domain 250..1000 nm')
    result = (np.exp(-.5*(p/16)**2) * (w/550)**(-1.3)
              * (1 + .32*np.exp(-.5*((w-430-.7*p)/25)**2))
              * (1 + x1*(p/30 + .3*(w/550-1))) * np.exp(color*(w/550-1)))
    if not np.isfinite(result).all() or np.any(result <= 0):
        raise ValueError('nonpositive spectral flux')
    return result


def flux(times, wavelength, z, params):
    if not np.isfinite(z) or z <= -1:
        raise ValueError('1+zHEL must be positive, blueshift permitted')
    logx, x1, color, t0 = params
    return np.exp(logx)/(1+z) * spectrum((times-t0)/(1+z), wavelength/(1+z), x1, color)


def photons(times, z, params, order=128, transform=None):
    nodes, weights = leggauss(order)
    values = []
    for lo, hi in BANDS:
        w = (lo+hi)/2 + nodes*(hi-lo)/2
        t = np.asarray(times)[:, None]
        f = flux(t, w, z, params) if transform is None else transform(t, w)
        values.append(np.sum(f*w*1e-9/(H_PLANCK*C_MS)*weights, axis=-1)*(hi-lo)/2)
    return np.stack(values, axis=1)


def chi_eds(z):
    if np.any(np.asarray(z) <= 0):
        raise ValueError('positive comparison zD required')
    # Scale 2c/H0 cancels in every residual ratio; this dimensionless chi is explicit.
    return 1 - 1/np.sqrt(1+np.asarray(z))


def radial_ratio(beta_speed, projection):
    b, q = np.asarray(beta_speed), np.asarray(projection)
    if not np.isfinite(b).all() or not np.isfinite(q).all() or np.any((b < 0) | (b >= 1)) or np.any(abs(q) > b):
        raise ValueError('radial correction domain')
    return np.sqrt((1-q*q)/(1-b*b))


def run_case(z, n):
    delta = doppler(n, BETA)
    zp = (1+z)/delta - 1
    times = P0[3] + (1+z)*PHASE
    tp = times / delta
    transformed = lambda t, w: delta**3 * flux(delta*t, delta*w, z, P0)
    obs = photons(tp, z, P0, transform=transformed)
    expected = P0.copy()
    expected[0] += 2*np.log(delta)
    expected[3] /= delta
    exact = photons(tp, zp, expected)
    high = photons(tp, z, P0, order=256, transform=transformed)
    objective = lambda p: ((photons(tp, zp, p)-obs)/obs).ravel()
    initial = P0 + np.array([.01, .02, -.01, .1])
    fit = least_squares(objective, initial, bounds=([-40, -.5, -.5, -10], [-25, 1., .5, 10]),
                        xtol=1e-13, ftol=1e-13, gtol=1e-13, max_nfev=300)
    sv = np.linalg.svd(fit.jac, compute_uv=False)
    rank = int(np.sum(sv > LIMITS['jacobian_relative_rank']*sv[0]))
    kappa = -2.5/np.log(10)*(fit.x[0]-P0[0]) + G_MAG*np.log(delta)
    raw = -2.5*np.log10(obs/photons(times, z, P0)) + G_MAG*np.log(delta)
    no_wave = photons(tp, z, P0, transform=lambda t,w: delta**3*flux(delta*t, w, z, P0))
    no_time = photons(tp, z, P0, transform=lambda t,w: delta**3*flux(t, delta*w, z, P0))
    checks = dict(spectral_relative=float(np.max(abs(exact/obs-1))),
                  integration_relative=float(np.max(abs(high/obs-1))),
                  fit_relative=float(np.max(abs(fit.fun))), amplitude_mag=float(abs(kappa)),
                  shape=float(np.max(abs(fit.x[1:3]-expected[1:3]))),
                  peak_days=float(abs(fit.x[3]-expected[3])))
    m0=-2.5/np.log(10)*P0[0];m1=-2.5/np.log(10)*fit.x[0]
    paired=(m1-G_MAG*np.log((1+zp)*chi_eds(z)))-(m0-G_MAG*np.log((1+z)*chi_eds(z)))
    if abs(paired-kappa)>1e-10:raise ArithmeticError('paired two-redshift residual identity')
    if not fit.success or rank != 4 or any(not np.isfinite(v) or v > LIMITS[k] for k,v in checks.items()):
        raise ArithmeticError('frozen spectral/refit acceptance failed: '+str(checks))
    return dict(zHEL=z, zHEL_transformed=float(zp), direction=list(n), doppler=float(delta),
                fitted_params=fit.x.tolist(), expected_params=expected.tolist(), checks=checks,
                jacobian_singular_values=sv.tolist(), kappa_amplitude_mag=float(kappa),
                paired_residual_difference_mag=float(paired), paired_identity_error_mag=float(paired-kappa),
                raw_band_kappa_mag=raw.tolist(),
                negative_controls=dict(missing_wavelength_relative=float(np.max(abs(no_wave/obs-1))),
                                       missing_time_relative=float(np.max(abs(no_time/obs-1)))))


def main():
    dirs = [np.eye(3)[0], np.eye(3)[1], np.array([1.,2.,3.])/np.sqrt(14), -np.eye(3)[0]]
    cases = [run_case(z, n) for z in (.02, .08, .3) for n in dirs]
    b = 369.82/C_KMS
    gamma = 1/np.sqrt(1-b*b)
    zgrid = np.geomspace(.005, .5, 60)
    eta_bound = (1+zgrid)*(gamma-1)
    dR_bound = -G_MAG*np.log(chi_eds(zgrid+eta_bound)/chi_eds(zgrid))
    witness_eta = 1.02*(np.sqrt(1+b*b)-1)
    witness_dR = -G_MAG*np.log(chi_eds(.02+witness_eta)/chi_eds(.02))
    # Fixed measured data: only trial zD changes. This is a different experiment.
    derivative_checks = []
    for z in (.02, .08, .3):
        eps = 1e-7
        num = -G_MAG*(np.log(chi_eds((1+z)*np.exp(eps)-1))-np.log(chi_eds((1+z)*np.exp(-eps)-1)))/(2*eps)
        exact = -G_MAG*(1+z)*.5*(1+z)**(-1.5)/chi_eds(z)
        derivative_checks.append(dict(z=z, numerical=float(num), analytic=float(exact), relative_error=float(abs(num/exact-1))))
    if max(x['relative_error'] for x in derivative_checks) > 1e-7:
        raise ArithmeticError('fixed-data trial derivative failed')
    source = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/source_null_20261018/genmag_SALT2.c')
    result = dict(owner='htt', claim_tier='C0_DERIVED_CONDITIONAL', transfer_source='none',
                  scope='finite synthetic spectral template + source-qualified radial Lorentz correction component',
                  cases=cases, thresholds=LIMITS, units='wavelength nm; phase day; photon rate m^-2 s^-1; magnitude mag',
                  source_convention=dict(snana_path=str(source), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), lines=[2649,2659,2844,2845,2897,2898]),
                  donor_blob='c518cdd0dcdd3ca628c71f6dd9e6a75e174ba805',
                  radial_component=dict(speed_kms=369.82, beta=b, gamma_minus_one=gamma-1,
                                        z=zgrid.tolist(), eta_upper=eta_bound.tolist(), EdS_dR_lower_mag=dR_bound.tolist(),
                                        witness_z=.02, witness_eta=witness_eta, witness_dR_mag=witness_dR),
                  fixed_data_derivative=derivative_checks,
                  paired_identity='delta R=kappa-(5/ln10)ln[chi(zD+eta)/chi(zD)]',
                  empirical_kappa_total='UNKNOWN: SALT2-B22/BBC/global alpha,beta,host,bias/MW responses',
                  empirical_eta_total='UNKNOWN: source-matched PV/group/reference-map derivative',
                  caveats=['Synthetic exact template is not observed SALT2 standardization.',
                           'Radial correction component is bounded with source-PV factor held covariantly fixed; total tube remains UNKNOWN.',
                           'EdS is an analytic comparison fixture, not a fitted cosmology or full GR response.',
                           'V04/H04 physical acceptance and all paper submission states remain open.'])
    (HERE/'RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10,4))
    for j,z in enumerate((.02,.08,.3)):
        vals = np.array([c['raw_band_kappa_mag'] for c in cases if c['zHEL']==z]).ravel()
        ax[0].plot(np.full(len(vals),j), vals, '.', label=f'z={z}')
    ax[0].axhline(0,color='k',lw=.5)
    ax[0].set(xticks=[0,1,2],xticklabels=['.02','.08','.3'],xlabel='source zHEL',ylabel='raw fixed-band defect (mag)')
    ax[1].semilogx(zgrid, dR_bound*1000)
    ax[1].set(xlabel='comparison zD',ylabel='radial correction lower defect (mmag)')
    fig.suptitle('Finite spectral refit / conditional radial correction; empirical total UNKNOWN')
    fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(HERE/f'SPECTRAL.{ext}',dpi=160)
    plt.close(fig)
    print(json.dumps(dict(cases=len(cases), max_amplitude_mag=max(c['checks']['amplitude_mag'] for c in cases), witness_dR_mag=witness_dR)))


if __name__ == '__main__':
    main()
