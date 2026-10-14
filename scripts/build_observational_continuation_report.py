#!/usr/bin/env python3
"""Generate the conditional OA05–OA11 progress report from frozen result JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/observational_analysis_20261014/results'


def load(path):
    return json.loads(path.read_text())


def make_report(output_dir):
    prior=load(BASE/'report/report.json')
    desi=load(BASE/'oa07_flatlcdm/result.json')
    cmb=load(BASE/'oa06_smica_scatter_v2/result.json')
    if (prior['status']!='COMPLETE_REPORT_ONLY' or desi['task']!='OA07'
            or desi['status']!='CONDITIONAL_PHYSICAL_RESPONSE_PROFILE'
            or cmb['task']!='OA06'
            or cmb['status']!='DESCRIPTIVE_SMICA_SIMULATION_SCATTER_PHYSICAL_LAW_HOLD'):
        raise ValueError('report source scope/status mismatch')
    row=min(desi['grid'],key=lambda x:abs(x['Omega_m']-.3))
    if abs(row['Omega_m']-.3)>1e-10:
        raise ValueError('reference Omega_m=0.3 missing')
    count=cmb['selected_pixels'];n=cmb['noise_simulations']
    mle=row['H0_r_d_mle_km_s'];lo=row['H0_r_d_95_lower_km_s'];hi=row['H0_r_d_95_upper_km_s']
    corr=cmb['mean_pairwise_selected_map_correlation']
    split=cmb['half_split_cov_frobenius_relative']
    cond=cmb['noise_condition']
    common=cmb['max_abs_simulation_mean_mode_microK']
    source_paths={
        'OA01':'docs/observational_analysis_20261014/results/desi/analysis.json',
        'OA04':'docs/observational_analysis_20261014/results/report/report.json',
        'OA06':'docs/observational_analysis_20261014/results/oa06_smica_scatter_v2/result.json',
        'OA07':'docs/observational_analysis_20261014/results/oa07_flatlcdm/result.json',
        'OA06_first_candidate':'docs/observational_analysis_20261014/results/oa06_smica_noise/result.json'}
    status={'OA05':'HOLD_EMPIRICAL_GROUP_SELECTION_CALIBRATION_VELOCITY_COVARIANCE_SCALE_REMAINDER',
        'OA06':'PARTIAL_DESCRIPTIVE_SIMULATION_SCATTER_PHYSICAL_LAW_HOLD',
        'OA07':'PARTIAL_CONDITIONAL_FLAT_LCDM_SCALAR_PROFILE',
        'OA08':'SUMMARY_CONDITIONING_ADAPTER_TESTED_ACTUAL_JOINT_LAW_HOLD',
        'OA09':'HOLD_OA08_AND_PHYSICAL_COMPONENT_LAWS',
        'OA10':'POSTERIOR_INTERFACE_TESTED_ACTUAL_POSTERIOR_IMAGE_HOLD',
        'OA11':'PARTIAL_CONDITIONAL_REPORT_FINAL_JOINT_REPORT_HOLD'}
    report={'schema':'htt.observational-continuation/1','owner':'htt',
        'scope':'CONDITIONAL_SCALAR_BAO_AND_CMB_SIMULATION_SCATTER_NOT_JOINT_PHYSICAL_FIT',
        'claim_tier':'C1_FOR_DESI_CONDITIONAL_C0_FOR_CMB_SCATTER',
        'status':status,'sources':source_paths,'desi_reference_omega_m':row['Omega_m'],
        'desi_H0_rd_mle_km_s':mle,'desi_H0_rd_95_pointwise_km_s':[lo,hi],
        'cmb_selected_pixels':count,'cmb_simulations':n,
        'cmb_mean_pairwise_selected_map_correlation':corr,
        'cmb_half_split_cov_frobenius_relative':split,
        'cmb_simulation_scatter_condition':cond,
        'cmb_max_abs_simulation_mean_mode_microK':common,
        'figure_sources':[
            'docs/observational_analysis_20261014/results/oa07_flatlcdm/flatlcdm_profile.pdf',
            'docs/observational_analysis_20261014/results/oa06_smica_scatter_v2/smica_noise_modes.pdf',
            'docs/observational_analysis_20261014/results/report/cf4_coverage.pdf',
            'docs/observational_analysis_20261014/results/report/cmb_same_sky.pdf'],
        'source_identity':'OA01 fixed released H5 SHA256 '+desi['source_sha256']+'; OA06 K1 cache '+cmb['source_cache_sha256'],
        'statistic_vs_bias':'DESI profile is a likelihood inversion conditional on the released summary; CMB covariance is simulation scatter, while spatial correlation and mean pattern do not establish draw dependence or a calibrated bias.',
        'coverage_scope':'DESI pointwise fixed-Gaussian model only; no raw-catalogue or joint frequentist coverage',
        'scientific_admission':'HOLD_FOR_JOINT_FIT_NATIVE_FAMILY_CLAIMS_UNAVAILABLE'}
    output_dir.mkdir(parents=True,exist_ok=False)
    (output_dir/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    md=f'''# HTT observational continuation: conditional results and open physical laws

Source files: `{source_paths['OA01']}`, `{source_paths['OA04']}`, `{source_paths['OA06']}`, and `{source_paths['OA07']}`. The existing OA00–OA04 report and its CF4/CMB figures are reused without re-running their inputs. These results preserve the published source identities and prior HOLD decisions.

## Actual conditional DESI result (OA07 partial)

The retained DESI DR1 BGS Bright `syst` product gives one released Gaussian scalar summary, `qiso={desi['observed_qiso']:.9f} ± {desi['sigma_qiso']:.9f}` at `z_eff={desi['zeff']:.9f}` with `(D_V/r_d)_fid={desi['DV_over_rd_fid']:.9f}`. In the declared flat matter+Lambda FLRW background, `E(z)=sqrt(Omega_m(1+z)^3+1-Omega_m)` and `q_pred=[c/(H0*r_d)] [z I(z)^2/E(z)]^(1/3)/(D_V/r_d)_fid`, with `I(z)=integral_0^z dz/E(z)` and free positive `H0*r_d` in km/s. No sound-horizon calculation or external absolute-scale anchor is inserted.

At fixed `Omega_m=0.30`, the conditional maximum is `H0*r_d={mle:,.2f} km/s`; the pointwise 95% fixed-Gaussian inversion is `[{lo:,.2f}, {hi:,.2f}] km/s`. Every tested `Omega_m` from 0.15 to 0.45 reaches the same maximum by moving `H0*r_d`. Thus this one datum does not identify `Omega_m`, `H0`, or `r_d` separately. The plotted band is **not** a posterior credible region or raw-catalogue coverage statement. The `syst` and overlapping alternative/full-shape products are not multiplied.

![DESI one-datum likelihood ridge](../oa07_flatlcdm/flatlcdm_profile.png)

## Actual SMICA projection and simulation diagnostic (OA06 partial)

The K1 NSIDE64 cache observation and {n} FFP10 SMICA noise maps were each fit on the same {count:,} pixels (`common_mask>0.5`) with the same real `ell=0..5` design, retaining 32 `ell=2..5` coefficients. Injection recovery max absolute error was `{cmb['injection_max_abs_microK']:.3g} microK`; the centered 32×32 simulation-scatter matrix has condition number `{cond:.2f}`. The mean pairwise selected-map spatial correlation is `{corr:.4f}`, the largest absolute simulation mean mode is `{common:.3f} microK`, and first/second-half scatter matrices differ by `{split:.3f}` in relative Frobenius norm. A fixed common spatial pattern can produce these values even with independent draws. The simulation dependence and calibrated zero-mean measurement covariance remain unresolved. The earlier OA06 candidate file is preserved but superseded by this diagnosis.

![SMICA same-operator projection and uncalibrated scatter](../oa06_smica_scatter_v2/smica_noise_modes.png)

## Previously accepted descriptive views (OA02–OA04)

The CF4 coverage figure uses published point summaries and fixed geometric assumptions; it is not an observed latent-distance fit. The CMB same-sky figure compares four reconstruction products and is not four independent skies.

![CF4 descriptive coverage](../report/cf4_coverage.png)

![CMB same-sky reconstruction contrast](../report/cmb_same_sky.png)

## Joint inference boundary

OA05 remains HOLD: the grouped CF4 `DMzp,Vh` pairs lack a sourced selected-group likelihood with velocity error, group/flow covariance, shared calibration and absolute-scale prior, and finite-distance remainder. Table 3 method presence is not a modulus mixing weight. OA06 lacks full map response and foreground/systematic calibration; a physical dipole, angular mean, and omitted-mode control are additionally required for full-field F4. OA07's scalar response is conditional and provides no angular mode.

OA08 now has a typed adapter that retains the original `PUBLISHED_GAUSSIAN_SUMMARY_MODEL_WITH_FIXED_RELEASED_COVARIANCE` target and integrates a supplied shared latent once; its small mixed-law tests pass. An actual CF4/CMB/DESI joint law still needs the missing component responses and a sourced cross-product dependence model. OA09 therefore has no physical joint posterior. OA10 now accepts a typed, source-bound posterior draw measure while keeping the prior scenario-only API's POSTERIOR refusal; no actual OA09 draws exist to push through it. OA11's final physical report is consequently HOLD. This report records the ready conditional science and exact remaining inputs without promoting old proof or native-family status.

## Reproduction

`/home/cosmosapjw/venv/bin/python -B scripts/fit_desi_qiso_flatlcdm.py --output-dir NEW_DESI_DIR` and `/usr/bin/python -B scripts/fit_cmb_smica_noise_modes.py --output-dir NEW_CMB_DIR` generate the new results and standalone plots. `python scripts/build_observational_continuation_report.py --output-dir NEW_REPORT_DIR` regenerates this report from the named JSONs; run `pdflatex -interaction=nonstopmode -halt-on-error -output-directory=NEW_REPORT_DIR NEW_REPORT_DIR/conditional_report.tex` from the repository root. The supported environments and input identities are recorded in source results. No heavy physical fit was launched because its joint measurement law is absent.

Primary context: [DESI DR1 product documentation](https://data.desi.lbl.gov/doc/releases/dr1/vac/full-shape-bao-clustering/), [DESI BAO modelling](https://academic.oup.com/mnras/article/534/1/544/7750629), [Planck component separation](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html), and [CF4 group construction](https://inspirehep.net/files/0509066626daba3d8e951586c658a0a8).
'''
    (output_dir/'report.md').write_text(md)
    tex=r'''\documentclass[11pt]{article}
\usepackage[margin=0.8in]{geometry}
\usepackage{graphicx,amsmath,booktabs,hyperref}
\title{HTT Observational Continuation: Conditional Results and Open Physical Laws}
\author{HTT observational analysis}
\date{14 October 2026}
\begin{document}\maketitle
\begin{abstract}This report uses one released DESI scalar BAO summary and one SMICA simulation diagnostic. It is not a three-probe joint fit, posterior, or native Bianchi-family result.\end{abstract}
\section{DESI scalar physical response}
The retained BGS Bright syst datum is $q_{\rm iso}=@@Q@@\pm@@SIGMA@@$ at $z_{\rm eff}=@@Z@@$. In flat matter--$\Lambda$ FLRW with a free positive $H_0r_d$, $q_{\rm pred}=\frac{c}{H_0r_d}\frac{[zI(z)^2/E(z)]^{1/3}}{(D_V/r_d)_{\rm fid}}$, $I(z)=\int_0^z dz'/E(z')$ and $E(z)^2=\Omega_m(1+z)^3+1-\Omega_m$. At fixed $\Omega_m=0.30$, $H_0r_d=@@MLE@@\,\mathrm{km\,s^{-1}}$ maximizes the conditional Gaussian density, with pointwise 95\% inversion $[@@LO@@,@@HI@@]\,\mathrm{km\,s^{-1}}$. Every displayed $\Omega_m$ attains the same maximum by changing $H_0r_d$; this is no two-parameter posterior or raw-catalogue coverage result.
\begin{figure}[ht]\centering\includegraphics[width=.82\linewidth]{docs/observational_analysis_20261014/results/oa07_flatlcdm/flatlcdm_profile.pdf}\caption{One-datum conditional likelihood ridge. The band is a pointwise released-Gaussian inversion, not a posterior.}\end{figure}
\section{CMB same-operator simulation diagnostic}
One SMICA observation and @@N@@ FFP10 noise maps were projected with the same $\ell=0\ldots5$ real-harmonic fit on @@PIX@@ selected NSIDE64 pixels. The retained 32-mode scatter matrix has condition number @@COND@@. Mean pairwise selected-map spatial correlation is @@CORR@@ and half-sample scatter difference is @@SPLIT@@ in relative Frobenius norm. A fixed common pattern is compatible with independent draws; independence and zero-mean measurement calibration remain unresolved. Foreground, map response and physical sky model remain absent.
\begin{figure}[ht]\centering\includegraphics[width=.9\linewidth]{docs/observational_analysis_20261014/results/oa06_smica_scatter_v2/smica_noise_modes.pdf}\caption{Observed low modes and simulation scatter under one K1 processing path. Error bars exclude foreground and shared simulation components.}\end{figure}
\section{Reused descriptive evidence and joint boundary}
The OA02--OA04 CF4 geometry and same-sky CMB contrasts are reused without recomputation. CF4 published group moduli do not supply the selected latent-distance law, velocity covariance, absolute-scale prior or finite-distance remainder required by OA05. OA08's typed DESI summary adapter and OA10's posterior draw interface are tested, but no actual OA09 joint posterior can be formed from the available physical laws. OA11's final physical report remains HOLD.
\begin{figure}[ht]\centering\includegraphics[width=.46\linewidth]{docs/observational_analysis_20261014/results/report/cf4_coverage.pdf}\hfill\includegraphics[width=.46\linewidth]{docs/observational_analysis_20261014/results/report/cmb_same_sky.pdf}\caption{Previously accepted descriptive views. Left: CF4 coverage under fixed point-summary geometry. Right: correlated reconstructions of one CMB sky. Neither is a physical joint fit.}\end{figure}
\subsection*{Task status and required physical inputs}
\begin{center}\begin{tabular}{lp{.76\linewidth}}\toprule
Task & Current scope and next input\\\midrule
OA05 & HOLD: selected grouped CF4 law, velocity errors and covariance, shared calibration and scale prior, finite-distance remainder.\\
OA06 & Simulation scatter only: processor response, foreground and systematic covariance, physical low-mode transfer and sky prior.\\
OA07 & Conditional scalar profile; no angular response or separate sound-horizon anchor.\\
OA08 & Typed summary-conditioning adapter tested; actual cross-product dependence and component laws absent.\\
OA09--11 & No joint posterior; posterior pushforward interface and this partial report do not close physical inference.\\\bottomrule
\end{tabular}\end{center}
\paragraph{Provenance.}\mbox{}\par
DESI source digest prefix: \texttt{@@DESISHA@@}.\par
SMICA cache digest prefix: \texttt{@@CMBSHA@@}.\par
Full source digests, numerical values and figure sources are bound in report.json and its named inputs. Scientific admission and native family identification remain HOLD.
\end{document}
'''
    repl={'Q':f"{desi['observed_qiso']:.6f}",'SIGMA':f"{desi['sigma_qiso']:.6f}",
        'Z':f"{desi['zeff']:.6f}",'MLE':f'{mle:,.1f}','LO':f'{lo:,.1f}','HI':f'{hi:,.1f}',
        'N':str(n),'PIX':f'{count:,}','COND':f'{cond:.2f}','CORR':f'{corr:.3f}',
        'SPLIT':f'{split:.3f}','DESISHA':desi['source_sha256'][:16],
        'CMBSHA':cmb['source_cache_sha256'].removeprefix('sha256:')[:16]}
    for key,value in repl.items():tex=tex.replace('@@'+key+'@@',value)
    (output_dir/'conditional_report.tex').write_text(tex)
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    report=make_report(args.output_dir)
    print(json.dumps({'output':str(args.output_dir),'status':report['status']}))


if __name__=='__main__':main()
