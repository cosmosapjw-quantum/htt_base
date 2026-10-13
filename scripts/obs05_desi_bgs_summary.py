"""OBS-05 matched DESI BGS summary diagnostics; no physical baseline inference.

Read with the supplied h5py environment. Plot its JSON separately if matplotlib
is available only in another environment. Matching uses (ell, bin edges), never
pair-weighted bin centroids. Array concatenation follows stored labels_values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

SOURCE_DOC = 'https://data.desi.lbl.gov/doc/releases/dr1/vac/full-shape-bao-clustering/'
DEFAULT_ROOT = Path('/mnt/extdrive/workdir/raw/desi_dr1_fullshape_bgs_bright_v1.2')
FILENAME = 'likelihood_correlation-recon-poles_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5'


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blocks(group):
    labels = group['labels_values'][()]
    keys, coords, values = [], [], []
    for label in labels:
        name = label.decode() if isinstance(label, bytes) else str(label)
        block = group[name]
        ell = int(block['meta/ell'][()])
        edges = np.asarray(block['s_edges'][()], dtype=float)
        s = np.asarray(block['s'][()], dtype=float)
        value = np.asarray(block['value'][()], dtype=float)
        if edges.shape != (len(s), 2) or value.shape != s.shape:
            raise ValueError('invalid bin metadata shape')
        if not all(np.all(np.isfinite(a)) for a in (edges, s, value)):
            raise ValueError('nonfinite bin metadata')
        if np.any(edges[:, 0] >= edges[:, 1]):
            raise ValueError('invalid bin edges')
        keys.extend((ell, float(lo), float(hi)) for lo, hi in edges)
        coords.extend(s)
        values.extend(value)
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate ell/edge key')
    return keys, np.asarray(coords), np.asarray(values)


def permutation(source, target):
    if len(source) != len(target) or set(source) != set(target):
        raise ValueError('ell/edge identities do not match')
    lookup = {key: i for i, key in enumerate(source)}
    return np.asarray([lookup[key] for key in target])


def validate_physical_baseline(value):
    """A zero embedded placeholder cannot be supplied as a physical baseline."""
    value = np.asarray(value, dtype=float)
    if value.ndim != 1 or not np.all(np.isfinite(value)) or not np.any(value != 0):
        raise ValueError('physical baseline missing: zero placeholder or invalid vector')
    return value


def read_summary(path):
    import h5py
    with h5py.File(path, 'r') as f:
        data_keys, data_s, data = blocks(f['observable'])
        cov_keys, _, _ = blocks(f['covariance/observable'])
        window_keys, _, _ = blocks(f['window/observable'])
        theory_keys, theory_s, embedded = blocks(f['window/theory'])
        covariance = np.asarray(f['covariance/value'][()], dtype=float)
        window = np.asarray(f['window/value'][()], dtype=float)
        zeff = f['observable'].attrs.get('zeff')
    n, m = len(data_keys), len(theory_keys)
    if covariance.shape != (n, n) or window.shape != (n, m):
        raise ValueError('matrix dimensions do not match metadata')
    canonical_data = sorted(data_keys)
    canonical_theory = sorted(theory_keys)
    dp = permutation(data_keys, canonical_data)
    cp = permutation(cov_keys, canonical_data)
    wp = permutation(window_keys, canonical_data)
    tp = permutation(theory_keys, canonical_theory)
    covariance = covariance[np.ix_(cp, cp)]
    window = window[np.ix_(wp, tp)]
    if not all(np.all(np.isfinite(a)) for a in (data, covariance, window)):
        raise ValueError('nonfinite data or matrices')
    if not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0):
        raise ValueError('covariance is not symmetric')
    np.linalg.cholesky(covariance)  # fail closed: no jitter/pseudoinverse
    return dict(data_keys=canonical_data, theory_keys=canonical_theory,
                data_s=data_s[dp], theory_s=theory_s[tp], data=data[dp],
                covariance=covariance, window=window, embedded=embedded[tp],
                zeff=None if zeff is None else float(zeff))


def diagnostic(summary):
    y, c, w = (summary[k] for k in ('data', 'covariance', 'window'))
    s = summary['theory_s']
    ell = np.asarray([key[0] for key in summary['theory_keys']])
    j = np.zeros((len(s), 3))
    j[ell == 0] = np.column_stack((np.ones(np.sum(ell == 0)),
                                  s[ell == 0] / 100, (s[ell == 0] / 100)**2))
    x = w @ j
    lower = np.linalg.cholesky(c)
    a, yw = np.linalg.solve(lower, x), np.linalg.solve(lower, y)
    u, sv, vt = np.linalg.svd(a, full_matrices=False)
    tol = np.finfo(float).eps * max(a.shape) * sv[0]
    keep = sv > tol
    pinv = (vt[keep].T / sv[keep]) @ u[:, keep].T
    coef = pinv @ yw
    fitted = x @ coef
    residual = y - fitted
    rw = np.linalg.solve(lower, residual)
    estimator = np.linalg.solve(lower.T, pinv.T).T
    coefficient_covariance = estimator @ c @ estimator.T
    g = np.zeros((len(s), 3))
    for column, multipole in enumerate((0, 2, 4)):
        mask = ell == multipole
        g[mask, column] = np.exp(-0.5 * ((s[mask] - 100) / 15)**2)
    response = w @ g
    response_w = np.linalg.solve(lower, response)
    response_projected = response_w - u[:, keep] @ (u[:, keep].T @ response_w)
    return dict(data=y, covariance=c, correlation=c/np.sqrt(np.outer(np.diag(c), np.diag(c))),
                observed_s=summary['data_s'], theory_s=s, theory_ell=ell,
                J=j, X=x, whitened_design=a, singular_values=sv, rank=int(sum(keep)),
                rank_tolerance=float(tol), coefficient_estimate=coef,
                coefficient_covariance=coefficient_covariance, fitted=fitted,
                residual=residual, whitened_residual=rw,
                residual_quadratic_norm=float(rw @ rw),
                residual_dimension=len(y)-int(sum(keep)),
                gaussian_theory_template=g, window_response=response,
                whitened_response_norms=np.linalg.norm(response_w, axis=0),
                nuisance_projected_response_norms=np.linalg.norm(response_projected, axis=0),
                covariance_eigenvalue_range=np.linalg.eigvalsh(c)[[0,-1]])


def jsonable(value):
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, dict): return {k: jsonable(v) for k, v in value.items()}
    return value


def plot_json(path, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    report = json.loads(Path(path).read_text())
    d = report['numerical_outputs']
    s, y, c = map(np.asarray, (d['observed_s'], d['data'], d['covariance']))
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].errorbar(s, s*s*y, yerr=s*s*np.sqrt(np.diag(c)), fmt='o', ms=3, label='GCcomb monopole')
    axes[0].plot(s, s*s*np.asarray(d['fitted']), label='descriptive polynomial through W')
    axes[0].set(xlabel='s [Mpc/h]', ylabel=r'$s^2\xi_0(s)$', title='Conditional summary diagnostic')
    axes[0].legend(fontsize=8)
    im = axes[1].imshow(d['correlation'], origin='lower', vmin=-1, vmax=1, cmap='coolwarm')
    axes[1].set(xlabel='canonical bin index', ylabel='canonical bin index', title='Packaged covariance correlation')
    fig.colorbar(im, ax=axes[1])
    fig.tight_layout()
    for ext in ('png', 'pdf'): fig.savefig(output/f'data_correlation.{ext}')
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    responses = np.asarray(d['window_response'])
    for i, ell in enumerate((0,2,4)): axes[0].plot(s, responses[:,i], label=f'theory ell={ell}')
    axes[0].set(xlabel='s [Mpc/h]', ylabel='W times unit template', title='Preselected radial Gaussian (100, 15)')
    axes[0].legend()
    axes[1].semilogy(range(1,4), d['singular_values'], 'o-')
    axes[1].set(xlabel='singular-value index', ylabel='singular value', title='Whitened descriptive design')
    fig.tight_layout()
    for ext in ('png','pdf'): fig.savefig(output/f'window_response.{ext}')
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plot-json', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.plot_json:
        plot_json(args.plot_json, args.output)
        return
    path = args.source_root/'likelihood'/FILENAME
    summary = read_summary(path)
    expected_data = [(0, float(s), float(s+4)) for s in range(48,152,4)]
    expected_theory = [(ell,float(s),float(s+1)) for ell in (0,2,4) for s in range(200)]
    if summary['data_keys'] != expected_data or summary['theory_keys'] != expected_theory:
        raise ValueError('source violates frozen GCcomb scale-cut/bin contract')
    checksum_list = args.source_root/'likelihood/dr1_vac_dr1_full-shape-bao-clustering_v1.0_data_v12_likelihood.sha256sum'
    entries = [line.split() for line in checksum_list.read_text().splitlines() if line.strip()]
    matches = [parts[0] for parts in entries if len(parts)==2 and parts[1].lstrip('*')==FILENAME]
    actual = sha256(path)
    if matches != [actual]: raise ValueError('immutable source disagrees with local checksum list')
    import h5py
    report = dict(task='OBS-05', owner='split_obsstat_htt', claim_tier='diagnostic-only',
        scope='DESI DR1 v1.2 BGS_BRIGHT-21.5 GCcomb z0.1-0.4 packaged post-reconstruction monopole summary',
        source=dict(path=str(path),sha256=actual, release='DESI DR1 clustering data_v1.2',
            official_documentation=SOURCE_DOC, documentation_checked='2026-10-13',
            checksum_list_path=str(checksum_list),checksum_list_sha256=sha256(checksum_list),
            checksum_status='MATCH_LOCAL_OFFICIAL_NAMED_LIST',remote_checksum_authentication='NOT_INDEPENDENTLY_OBSERVED'),
        environment=dict(python=sys.version,executable=sys.executable,numpy=np.__version__,h5py=h5py.__version__,
            git_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            git_branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
            worktree_state='DIRTY_WITH_OTHER_OWNER_EDITS',script_sha256=sha256(__file__),
            requested_model='gpt-6.1-sol',requested_effort='medium',
            actual_executor_profile='gpt-5.6-terra/medium reused after gpt-6.1-sol capacity rejection',
            observed_runtime='UNKNOWN'),
        matching=dict(identity='ell + exact bin edges', observed_keys=summary['data_keys'], theory_keys=summary['theory_keys'],
            evaluation_coordinates='published pair-weighted s coordinates; these are not identity keys',zeff=summary['zeff']),
        physical_baseline=dict(status='HOLD',embedded_values_all_zero=bool(np.all(summary['embedded']==0)),
            embedded_values_usage='PLACEHOLDERS_ONLY_NEVER_PHYSICAL_BASELINE'),
        component_owners=dict(
            obsstat='HDF5 reader, exact-bin matching, supplied-window feature extraction, and response diagnostics',
            htt='descriptive GLS coefficient estimate, conditional covariance, and residual summaries',
        ),
        design=dict(description='ell0 columns 1, s/100, (s/100)^2; zero ell2/ell4; X=WJ',
            coefficient_units='dimensionless descriptive correlation coefficients',
            template='unit radial Gaussian exp(-0.5*((s-100)/15)^2), separately in ell0,ell2,ell4',
            selection='controller-selected before this run; not ZIP-preregistered; no scan or fitted template amplitude'),
        uncertainty_scope=dict(statistical='M C M^T conditional on fixed W,J and supplied SPD C',
            deterministic_bias='NOT_SUPPLIED; omitted from descriptive fit; never absorbed into C',
            gaussian_law='NOT_VALIDATED',coverage='NOT_CLAIMED',p_value='NOT_COMPUTED',
            remainder_support='For supplied b, coefficient bias=M b; a physical bound is missing'),
        hold_inputs=['physical t(theta) baseline','fiducial cosmology/reconstruction/dilation convention',
            'physical parameter Jacobian and priors','catalogue low-mode forward injection response',
            'deterministic remainder envelope','sampling-law/covariance calibration'],
        caveats=['Polynomial fit is descriptive, not a cosmological baseline or detection.',
            'Summary radial multipole injection does not measure absolute sky-direction or removed catalogue low-mode response.',
            'Residual quadratic norm has no calibrated goodness-of-fit probability.',
            'No native Bianchi family identification or broader scientific admission.'],
        numerical_outputs=diagnostic(summary))
    destination = args.output/'summary.json'
    destination.write_text(json.dumps(jsonable(report),indent=2,allow_nan=False)+'\n')
    d=report['numerical_outputs']
    print(json.dumps(dict(output=str(destination),shape=list(summary['window'].shape),rank=d['rank'],
                         singular_values=d['singular_values'].tolist(),residual_quadratic_norm=d['residual_quadratic_norm'])))

if __name__ == '__main__': main()
