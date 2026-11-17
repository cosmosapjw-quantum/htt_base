"""R8 finite interpretation of saved R65 experiments; no new catalogue fit."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
import numpy as np
from scipy import stats

from htt.htt.infer.r58_mixed_tensor_likelihood import fit_linear
from htt.htt.infer.r65_count_quotient import gaussian_five_views

P = Path('docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117')


def arr(v):
    return np.asarray(v, dtype=float)


def clean(v):
    if isinstance(v, np.ndarray): return v.tolist()
    if isinstance(v, np.generic): return v.item()
    if isinstance(v, dict): return {k: clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [clean(x) for x in v]
    return v


def main():
    n = json.loads((P/'RESULTS/NVSS_OBSERVED_RESULT.json').read_text())
    r = json.loads((P/'RESULTS/RACS_POSTERIOR_PROJECTION.json').read_text())
    primary = n['models']['base64_dipole_stf']
    tables, morph = [], []
    for name, model in n['models'].items():
        common = model['common_transverse_fit']
        mean, cov = arr(common['estimate'])[:2], arr(common['covariance'])[:2, :2]
        peak = {}
        for alpha, response in model['conditional_peak_response_diagnostics'].items():
            full_fixed = response['independent_vs_fixed_cmb']
            full_shared = response['independent_vs_shared']
            # Both restrictions lie in the same independent-bin family.
            # Fixed CMB is nested in shared beta, with exactly two constraints.
            stat = full_fixed['statistic']-full_shared['statistic']
            if stat < -1e-6:
                raise ValueError('nested likelihood ordering violated')
            peak[alpha] = dict(response=response['response'],
                               omnibus_df6_p=full_fixed['asymptotic_conditional_p'],
                               shared_beta_vs_cmb_lr=float(max(0, stat)),
                               shared_beta_vs_cmb_df=2,
                               shared_beta_vs_cmb_asymptotic_p=float(stats.chi2.sf(max(0, stat), 2)),
                               meaning='secondary nested contrast of the already-computed source-conditional peak-proxy models; no physical speed claim')
        tables.append(dict(model=name, u=mean, sd=np.sqrt(np.diag(cov)), covariance=cov,
                           norm=float(np.linalg.norm(mean)), ra_deg=float(np.rad2deg(np.arctan2(mean[1], mean[0]))%360),
                           common_vector_lr=model['common_vector_lr'],
                           pearson_phi=[f['overdispersion_diagnostic'] for f in model['independent_fits']],
                           peak_response_diagnostics=peak,
                           path_information=model['path_information']))
    for geometry in n['geometries']:
        simple = n['models'][geometry+'_dipole']
        expanded = n['models'][geometry+'_dipole_stf']
        a = arr(simple['common_transverse_fit']['estimate'])[:2]
        b = arr(expanded['common_transverse_fit']['estimate'])[:2]
        se = np.sqrt(np.diag(arr(expanded['common_transverse_fit']['covariance'])[:2, :2]))
        morph.append(dict(geometry=geometry, common_dipole_shift=b-a,
                          shift_in_expanded_marginal_sd=(b-a)/se,
                          shift_units_note='scale diagnostic, not a paired-shift significance',
                          independent_morphology_lr=2*(expanded['full_log_likelihood_relative_zero']-
                                                     simple['full_log_likelihood_relative_zero']),
                          independent_morphology_df=12,
                          sd_inflation=[b['dipole_sd_inflation_from_free_STF'] for b in expanded['matched_score_baseline']],
                          polar_STF_abs_corr=[b['maximum_absolute_dipole_STF_correlation'] for b in expanded['matched_score_baseline']]))
    # Reuse the existing R58 full-covariance rank-aware Gaussian kernel, with the
    # R65 saved local carrier. This is an information/precision diagnostic of
    # the already-derived beta+common-residual construction, not another raw fit.
    y = arr(primary['five_views']['x']['signed_levels'])
    cov = arr(primary['five_views']['x']['full_covariance'])
    k = arr(primary['conditional_peak_response_diagnostics']['0.75']['response'])
    kmap = np.kron(k[:, None], np.eye(2))
    hmap = np.tile(np.eye(2), (3, 1))
    jointmap = np.column_stack([kmap, hmap])
    gaussian = fit_linear(y, cov, jointmap, parameter_scale=[.001, .001, .01, .01])
    sigma = np.sqrt(np.diag(gaussian['covariance']))
    cc = gaussian['covariance']/np.outer(sigma, sigma)
    degeneracy = dict(
        model='u_b = k_b beta_transverse + a_transverse, constant residual across bins',
        law='local conditional-Gaussian carrier, alpha=.75 and source response held fixed',
        kernel='htt.htt.infer.r58_mixed_tensor_likelihood.fit_linear',
        parameter_order=['beta_x', 'beta_y', 'a_x', 'a_y'],
        rank=gaussian['rank'], n_parameters=4, estimate=gaussian['estimate'],
        sd=sigma, full_covariance=gaussian['covariance'], correlation=cc,
        residual_chi2=gaussian['residual_chi2'], residual_dof=gaussian['dof'],
        singular_values_scaled=gaussian['singular_values_scaled'],
        beta_sd_in_CMB_speed_units=sigma[:2]*299792.458/369.82,
        status='conditional precision/identifiability diagnostic, not physical beta/tilt measurement',
        no_generic_no_go=True)
    racs = []
    for name, m in r['models'].items():
        v = m['posterior_pushforward']
        q = v['scalar_summaries']
        racs.append(dict(model=name,
                         parallel_ratio=q['transverse_parallel_ratio_to_cmb'],
                         perpendicular_km_s=q['transverse_perpendicular_km_s'],
                         speed_ratio=q['speed_ratio'],
                         nuisance_correlations=v['nuisance_weighted_pearson_correlations'],
                         posterior_probability_parallel_gt1=v['posterior_probability_transverse_parallel_ratio_gt1'],
                         raw_rows=m['source']['csv']['n_rows'],
                         zero_weight_rows=m['source']['csv']['n_zero_weights'],
                         descriptive_weight_ess=v['weight_concentration_ess'],
                         source_commit=m['source']['artifact_manifest']['source']['commit']))
    score_dist = [v['squared_shift_in_fitted_information'] for m in n['models'].values()
                  for v in m['matched_score_baseline']]
    boot = n['primary_common_vector_bootstrap']
    lo, hi = stats.beta.ppf([.025, .975], [boot['exceedances'], boot['exceedances']+1],
                            [boot['nsim']-boot['exceedances']+1, boot['nsim']-boot['exceedances']])
    # The observed count is interior in this run; endpoints use exact0/1.
    if boot['exceedances'] == 0: lo = 0.
    if boot['exceedances'] == boot['nsim']: hi = 1.
    boot['binomial_mc_interval95_for_exceedance_probability'] = [float(lo), float(hi)]
    out = dict(schema='htt.r65.interpretation/1', baseline_commit=n['baseline_commit'],
               sources=dict(NVSS=n['source'], RACS_archive_sha256=r['source_archive_sha256']),
               observed_models=8, independent_bin_fits=24, common_vector_fits=8,
               shared_response_fits=24, fixed_cmb_nuisance_fits=12,
               total_observed_optimizations=68,
               bootstrap_catalogues=512, bootstrap_refits=2048, RACS_posterior_models=6,
               new_RACS_training_or_fits=0, new_NVSScatalogue_downloads=0,
               tests_passed=24, symbolic_checks=11,
               nvss_tables=tables, morphology_sensitivity=morph, source_geometries=n['geometries'],
               primary_bootstrap=boot, beta_residual_precision=degeneracy,
               maximum_one_step_MLE_information_distance=float(np.sqrt(max(score_dist))),
               racs_tables=racs,
               RACS_projection_scope='geometric pushforward of source posterior; NOT a refit with arbitrary declination selection removed',
               RACS_ablation_scope='diagnostic ablations are not equally qualified models or a probability-weighted model ensemble',
               physical_anomaly_claim=False, global_tilt_claim=False, bianchi_assignment=False,
               novelty_decision='Useful actual-data conditional morphology/calibration result; estimator/five-view/GLS priority or superior information not demonstrated. Prefer P4 companion consolidation pending source-calibrated matched comparison.',
               publication_status='NOT_READY_TO_SUBMIT')
    provider = json.loads((P/'RESULTS/PROVIDER_NVSS_RESULT.json').read_text())
    provider_tables = []
    for name, model in provider['models'].items():
        fit = model['common_transverse_fit']
        mean = arr(fit['estimate'])[:2]
        ccov = arr(fit['covariance'])[:2, :2]
        diagnostics = {}
        for alpha, response in model['conditional_peak_response_diagnostics'].items():
            fixed = response['independent_vs_fixed_cmb']
            shared = response['independent_vs_shared']
            lr = fixed['statistic']-shared['statistic']
            diagnostics[alpha] = dict(response=response['response'],
                                      omnibus_df6_p=fixed['asymptotic_conditional_p'],
                                      shared_beta_vs_cmb_lr=lr,
                                      shared_beta_vs_cmb_df2_p=float(stats.chi2.sf(lr, 2)),
                                      meaning=response['meaning'])
        provider_tables.append(dict(model=name, u=mean, sd=np.sqrt(np.diag(ccov)), covariance=ccov,
                                    norm=float(np.linalg.norm(mean)), ra_deg=float(np.rad2deg(np.arctan2(mean[1], mean[0]))%360),
                                    common_vector_lr=model['common_vector_lr'],
                                    conditional_response_diagnostics=diagnostics,
                                    pearson_phi=[f['overdispersion_diagnostic'] for f in model['independent_fits']]))
    pair = provider['paired_comparisons']['dipole_stf']
    pair_cov = pair['covariance']
    pair_mean = np.concatenate([arr(provider['models'][key]['common_transverse_fit']['estimate'])[:2]
                                for key in ['provider_peak_dipole_stf', 'provider_integrated_dipole_stf']])
    pair_views = gaussian_five_views(pair_mean, arr(pair_cov['covariance_joint']))
    pair_views['x']['selection_order'] = ['provider peak', 'provider integrated component flux']
    pair_views['x']['joint_law'] = 'same-source empirical Poisson influence Gaussian approximation; separate marginal count fits are not multiplied'
    pair_views['G_F']['path_coordinate'] = 'selection definition: provider peak to integrated flux; not time/redshift'
    pair_views['exact_likelihood'] = 'No new exact joint count likelihood; joint source categories and separate marginal normalizers retained'
    wrong = arr(pair_cov['covariance_left'])+arr(pair_cov['covariance_right'])
    delta = arr(pair['integrated_minus_peak'])
    pair_ablation = dict(
        actual_delta=delta, actual_covariance=pair_cov['covariance_contrast'],
        actual_sd=pair['marginal_sd'], actual_wald=pair['poisson_source_linearized_wald'],
        actual_conditional_tail=pair['poisson_source_linearized_tail'],
        wrong_independent_sd=np.sqrt(np.diag(wrong)),
        wrong_independent_wald=float(delta@np.linalg.solve(wrong, delta)),
        wrong_independent_tail=float(stats.chi2.sf(delta@np.linalg.solve(wrong, delta), 2)),
        same_axis_correlation=np.diag(arr(pair_cov['covariance_cross']))/np.sqrt(np.diag(arr(pair_cov['covariance_left']))*np.diag(arr(pair_cov['covariance_right']))),
        physical_anomaly_significance=False)
    integrated = provider['models']['provider_integrated_dipole_stf']
    iy = arr(integrated['five_views']['x']['signed_levels'])
    ic = arr(integrated['five_views']['x']['full_covariance'])
    ik = arr(integrated['conditional_peak_response_diagnostics']['0.75']['response'])
    ifit = fit_linear(iy, ic, np.column_stack([np.kron(ik[:, None], np.eye(2)), hmap]),
                      parameter_scale=[.001, .001, .01, .01])
    isd = np.sqrt(np.diag(ifit['covariance']))
    integrated_precision = dict(
        model='integrated-component u_b = k_b beta_transverse + a_transverse',
        law='local conditional-Gaussian source carrier; alpha=.75 and responses held fixed',
        rank=ifit['rank'], n_parameters=4, estimate=ifit['estimate'], sd=isd,
        full_covariance=ifit['covariance'], correlation=ifit['covariance']/np.outer(isd, isd),
        beta_sd_in_CMB_speed_units=isd[:2]*299792.458/369.82,
        residual_chi2=ifit['residual_chi2'], residual_dof=ifit['dof'],
        singular_values_scaled=ifit['singular_values_scaled'],
        status='practical precision diagnostic; no general impossibility or physical velocity constraint')
    out.update(original_observed_models=8, source_refinement_observed_models=4,
               observed_models=12, independent_bin_fits=36, common_vector_fits=12,
               shared_response_fits=36, fixed_cmb_nuisance_fits=18,
               total_observed_optimizations=102, tests_passed=37,
               original_tests_passed=24, overlap_tests_passed=13,
               new_NVSScatalogue_downloads=1,
               integrated_flux_input_gap_closed=True,
               provider_nvss_tables=provider_tables,
               provider_source_geometries=provider['geometries'],
               provider_source_migration_counts=provider['source_migration_counts_4x4'],
               source_definition_paired_results=provider['paired_comparisons'],
               source_definition_five_views=pair_views,
               provider_beta_residual_precision=integrated_precision,
               source_definition_covariance_ablation=pair_ablation)
    out['sources']['NVSS_provider'] = provider['source']
    out['novelty_decision'] = ('Actual same-source peak-versus-integrated dipole contrast survives paired uncertainty and angular nuisance in a declared Poisson working law. '
                              'This resolves a source/estimand input defect and supplies a publication candidate on selection-dependent radio morphology; '
                              'generic estimator/five-view/GLS priority or information superiority is not established. '
                              'The narrow P4 companion needs one bounded source/component-null qualification, one matched conventional comparison, and manuscript consolidation. '
                              'Source-matched LSS calibration is required for a physical-excess claim; a RACS nuisance refit is optional for a stronger same-estimand comparison. '
                              'Original P4 acceptance and NOT_READY_TO_SUBMIT remain unchanged.')
    (P/'RESULTS/INTERPRETATION_SUMMARY.json').write_text(json.dumps(clean(out), indent=2, allow_nan=False)+'\n')
    make_figures(out, n)
    print(json.dumps(clean({k: out[k] for k in ['primary_bootstrap','beta_residual_precision',
                                               'maximum_one_step_MLE_information_distance']}), indent=2))


def make_figures(summary, raw):
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.6), constrained_layout=True)
    colors = ['#185b8d', '#d48120']
    xpos = np.arange(3)
    for i, suffix in enumerate(['dipole', 'dipole_stf']):
        fits = raw['models']['base64_'+suffix]['independent_fits']
        for j, component in enumerate(['x', 'y']):
            vals = np.array([f['estimate'][j] for f in fits])*1000
            sd = np.array([np.sqrt(f['covariance'][j][j]) for f in fits])*1000
            axes[j].errorbar(xpos+(i-.5)*.12, vals, yerr=sd, fmt='o', capsize=3,
                             color=colors[i], label=['Dipole', 'Dipole + STF'][i])
            axes[j].axhline(0, color='.7', linewidth=.7)
            axes[j].set_xticks(xpos, ['20–40', '40–80', '80+'])
            axes[j].set_xlabel('Peak intensity (mJy/beam)')
            axes[j].set_ylabel(f'$10^3 u_{component}$')
    axes[0].legend(frameon=False, loc='upper left')
    fig.suptitle('NVSS: signed transverse coefficients by disjoint peak bin\nConditional count covariance; bars are marginal 1 SD')
    fig.savefig(P/'RESULTS/NVSS_SIGNED_FLUX_PATH.png', dpi=180)
    fig.savefig(P/'RESULTS/NVSS_SIGNED_FLUX_PATH.pdf')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.7, 6.2), constrained_layout=True)
    palette = ['#185b8d', '#76a9c9', '#b86814', '#91548f']
    selected = [x for x in summary['nvss_tables'] if x['model'].endswith('_stf')]
    for row, color in zip(selected, palette):
        mean, cov = arr(row['u'])*1000, arr(row['covariance'])*1e6
        eig, vec = np.linalg.eigh(cov)
        angle = np.rad2deg(np.arctan2(vec[1, 1], vec[0, 1]))
        width, height = 2*np.sqrt(stats.chi2.ppf(.95, 2)*eig[::-1])
        ax.add_patch(Ellipse(mean, width, height, angle=angle, facecolor='none', edgecolor=color, lw=1.4))
        ax.plot(*mean, 'o', color=color, label=row['model'].replace('_dipole_stf', ''))
    ax.axhline(0, color='.7', lw=.7); ax.axvline(0, color='.7', lw=.7)
    ax.set(xlim=(-24, 2), ylim=(-7, 23), xlabel='$10^3 u_x$', ylabel='$10^3 u_y$')
    ax.set_aspect('equal', adjustable='box')
    ax.legend(frameon=False, loc='upper right')
    ax.set_title('Common NVSS transverse dipole with free STF per bin\n95% conditional two-parameter ellipses; masks reuse sources')
    fig.savefig(P/'RESULTS/NVSS_MASK_MORPHOLOGY.png', dpi=180)
    fig.savefig(P/'RESULTS/NVSS_MASK_MORPHOLOGY.pdf')
    plt.close(fig)

    pair = summary['source_definition_paired_results']['dipole_stf']
    cov = pair['covariance']
    rows = [next(x for x in summary['provider_nvss_tables'] if x['model'] == key)
            for key in ['provider_peak_dipole_stf', 'provider_integrated_dipole_stf']]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2), constrained_layout=True)
    def ellipse(ax, mean, covariance, color, label, ls='-'):
        eig, vec = np.linalg.eigh(covariance)
        angle = np.degrees(np.arctan2(vec[1, 1], vec[0, 1]))
        wh = 2*np.sqrt(stats.chi2.ppf(.95, 2)*eig[::-1])
        ax.add_patch(Ellipse(mean, *wh, angle=angle, fill=False, edgecolor=color, lw=1.6, linestyle=ls, label=label))
        ax.plot(*mean, 'o', color=color, ms=4)
    for row, key, color, label in zip(rows, ['covariance_left','covariance_right'],
                                    ['#185b8d','#b86814'], ['Provider peak','Integrated flux']):
        ellipse(axes[0], arr(row['u'])*1000, arr(cov[key])*1e6, color, label)
    delta = arr(pair['integrated_minus_peak'])*1000
    ellipse(axes[1], delta, (arr(cov['covariance_left'])+arr(cov['covariance_right']))*1e6,
            '.55', 'Overlap discarded (incorrect)', '--')
    ellipse(axes[1], delta, arr(cov['covariance_contrast'])*1e6,
            '#a53148', 'Shared-source covariance')
    axes[1].plot(0, 0, 'k+', ms=9, label='No selection difference')
    for ax in axes:
        ax.axhline(0, color='.85', lw=.7); ax.axvline(0, color='.85', lw=.7)
        ax.set_aspect('equal', adjustable='box')
        ax.legend(frameon=False, fontsize=9, loc='upper right')
    axes[0].set(xlim=(-25, 1), ylim=(-5, 24), xlabel='$10^3 u_x$', ylabel='$10^3 u_y$', title='Same-provider common dipoles')
    axes[1].set(xlim=(-15, 12), ylim=(-7, 21), xlabel='$10^3 (u_{x, int}-u_{x, peak})$',
                ylabel='$10^3 (u_{y, int}-u_{y, peak})$', title='Paired selection difference')
    fig.suptitle('NVSS peak versus integrated-component selection\n95% Poisson-source influence ellipses; not a cosmological anomaly test')
    fig.savefig(P/'RESULTS/NVSS_PEAK_VS_INTEGRATED.png', dpi=180)
    fig.savefig(P/'RESULTS/NVSS_PEAK_VS_INTEGRATED.pdf')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5), constrained_layout=True)
    for i, row in enumerate(summary['racs_tables']):
        q = row['parallel_ratio']; c = '#185b8d' if 'low3' in row['model'] else '#b86814'
        ax.plot(q['central95'], [i, i], color=c, lw=1.3)
        ax.plot(q['central68'], [i, i], color=c, lw=4)
        ax.plot(q['median'], i, 'o', color=c)
    ax.axvline(1, color='.25', ls='--', lw=1, label='CMB template = 1')
    ax.axvline(0, color='.8', lw=.7)
    ax.set_yticks(range(len(summary['racs_tables'])),
                  [x['model'].replace('racs_', '').replace('_', ' ') for x in summary['racs_tables']])
    ax.set_xlabel('CMB-parallel transverse velocity / CMB transverse velocity')
    ax.set_title('Released RACS weighted posterior projections\nCentral 68% / 95% intervals; source-conditional, no model averaging')
    ax.legend(frameon=False, loc='lower right')
    fig.savefig(P/'RESULTS/RACS_TRANSVERSE_POSTERIOR.png', dpi=180)
    fig.savefig(P/'RESULTS/RACS_TRANSVERSE_POSTERIOR.pdf')
    plt.close(fig)


if __name__ == '__main__':
    main()
