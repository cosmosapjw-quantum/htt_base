#!/usr/bin/env python3
"""Generate a numerical reboot report from existing result JSON, without refitting."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/observational_reboot_20261014'


def build(out):
    paths={'smica':BASE/'results/smica_pilot/calibration.json',
           'campaign':BASE/'results/synthetic_calibration/campaign.json',
           'response':BASE/'results/response_laboratory/result.json',
           'plan':BASE/'REBOOT_PLAN.json',
           'inventory':BASE/'research/ANALYSIS_OPPORTUNITY_INVENTORY.json'}
    data={k:json.loads(v.read_text()) for k,v in paths.items()}
    p=data['smica'];g=p['global_joint_null'];camp=data['campaign']
    cb=camp['B_fixed_per_replicate']; cr=camp['replicates_fixed']
    cf=camp['global_rejection_frequency']; nf=camp['naive_min_unadjusted_rejection_frequency']
    clo,chi=camp['global_rejection_probability_CP_interval']
    if p['fixed_B']!=240 or p['scientific_admission']['rank_is_confirmatory_physical_planck_p'] is not False:
        raise ValueError('pilot scope or declared calibration count differs')
    if p['scientific_admission']['status']!='EXPLORATORY_RETROSPECTIVE_CONDITIONAL_SIMULATION_MODEL_ONLY':
        raise ValueError('unrecognized scientific scope')
    if len(p['features'])!=4 or len(data['response']['cases'])!=3:
        raise ValueError('expected declared feature/laboratory layout')
    out.mkdir(parents=True,exist_ok=False)
    source={k:{'path':str(v.relative_to(ROOT)),'sha256':hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in paths.items()}
    report={'schema':'htt.reboot-report/1','owner':'htt','claim_tier':'C0',
      'status':'EXECUTED_CONDITIONAL_PILOT_AND_ENABLING_RESEARCH',
      'scientific_scope':p['scientific_admission'],'source_files':source,
      'smica_global_rank':g,'smica_features':p['features'],'synthetic_campaign':camp,
      'response_ranks':[r['rank'] for r in data['response']['cases']],
      'development_tasks':len(data['plan']['tasks']),
      'analysis_opportunities':len(data['inventory']['opportunities']),
      'completed_current_unit':'RB00','remaining':'RB01–RB22 and expanded capability goals; no full physical joint posterior or native family result.'}
    (out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    rows=[];texrows=[]
    for f in p['features']:
        ell=f['name'].split('_')[1];r=f['unadjusted'];a=f['joint_max_adjusted']
        rows.append(f"| {ell} | {f['observed_feature']:.6f} | {r['p_rank_exact']} ({r['p_rank']:.6f}) | {a['p_rank']:.6f} |")
        texrows.append(f"{ell} & {f['observed_feature']:.3f} & {r['p_rank']:.4f} & {a['p_rank']:.4f} \\\\")
    md=f'''# 관측 reboot: 실제 SMICA pilot, 통계 검증과 전체 분석 계획

새 분석은 **선언한 전달 시뮬레이션 모형에 조건부인 탐색적 SMICA 검정**이다. 고정한 네 저차 전력 요약의 global rank는 **{g['p_rank_exact']} = {g['p_rank']:.6f}**다. 이 값은 현재 통계량에서 이례적인 큰 편차를 보여주지 않는다. 모형의 참 확률이나 Bianchi family의 확률은 계산하지 않았다. 과거에 검토한 하늘을 재사용하므로 분석 선택 이력을 제거한 confirmatory 검정으로 해석하지 않는다.

## 실제 자료와 처리

source gate와 실제 SHA256가 일치한 K1 NSIDE64 cache를 사용했다. 관측과 300개의 signal+noise 쌍에 같은 common mask>0.5, 38,413픽셀, ell0–5의 36열 OLS를 적용했다. 각 signal/noise ID는 한 번만 사용했다. 앞 60개는 특징의 평균/표준편차를 정하는 학습, 뒤 240개는 calibration이다. ell2–5의 32실수 계수에서 norm²/(2ell+1)를 계산했다. 이는 **선택된 하늘에서 적합한 계수의 전력 요약**이며 unbiased full-sky C_l 추정량으로 인증하지 않았다.

| ell | 적합 전력 요약 (microK²) | 개별 two-sided rank | joint-max adjusted rank |
|---|---:|---|---:|
{chr(10).join(rows)}

Global score는 학습으로 표준화한 네 absolute departure의 최대다. 검정240개 중 {g['k_ge']}개가 관측 이상이므로 (1+{g['k_ge']})/241을 쓴다. 가능한 최소 rank는 1/241={p['p_rank_resolution']:.6f}다. IID조건부 null tail확률 q의 95% Clopper–Pearson 구간은 [{g['q_interval'][0]:.6f}, {g['q_interval'][1]:.6f}]다. 이 구간은 이미 실현된 rank p의 신뢰구간이 아니며 물리 모형의 정확성에 대한 구간도 아니다.

![SMICA 조건부 pilot](../smica_pilot/joint_null_maximum.png)

Planck release의 독립noise/systematics 설명과 공식 plancklens의 전달 CMB+noise 결합을 근거로 사용했다. 실제 observed sky와 simulation의 동일 법칙, 전경 잔여, 고정 actual-data weight, systematic mean과 처리 반응의 적합성은 아직 검증 대상이다. 원noise 평균을 관측의 bias로 가정해 빼지 않았다. 내부 OLS identity 오차 약2.1e-15는 algebra 검증이며 누락 high-ell leakage나 실제 map response의 검증을 대신하지 않는다.

## legacy와의 비교

과거 K1 p=.039는 다른 마스크/처리/6통계량과999signal+300cyclic-noise 설계의 empirical rank다. 새 p와 통계적 개선량처럼 빼거나 더 작은 값을 선택할 수 없다. 과거 archive p=.078/.079는 legacy 다중 채널(dipole, CF4, D2/D3 scalar summary)의 posterior-predictive discrepancy이고, R8의5비기각/25미해결은 합성 pool 결과다. source별 비교와 C_l/D_l/STF normalization 충돌은 [legacy 재독](../../research/LEGACY_REBOOT_REVIEW.md)에 있다.

## 새 통계 코드의 실제 검증

고정 B={cb}, {cr}회 독립 합성 실험에서 global-max rejection은 {cf:.3f}, 각 marginal을 검사하고 가장 작은 값을 고르는 비보정 절차는 {nf:.3f}였다. Global 95% binomial 구간 [{clo:.5f}, {chi:.5f}]은 nominal {camp["alpha"]:.2f}를 포함한다. 이 캠페인은 한 번 고정한 독립 학습 자료에 조건부다. 이것은 선언한 합성 실험의 구현/오류율 점검이며 Planck에서의 검정 크기를 입증하지 않는다. 정확한 동점 rank, CP coverage, 학습 누출·same-sky ID중복 거부, OLS독립 oracle와 signal+noise cross-term을 별도 테스트했다.

![합성 calibration](../synthetic_calibration/synthetic_calibration_campaign.png)

## local/global 연구 결과

유도한 관측 모형 y=B beta_local+G beta_global+noise에서 covariance whitening과 nuisance 사영을 수행했다. 선언한 합성 행렬에서는 일정 response가 local nuisance에 흡수되어 rank 0, 깊이 response가 rank 3, shell마다 자유로운 nuisance를 허용하면 다시 rank 0이다. 아주 작은 depth response는 full rank를 유지해도 정보가 작다. parameter단위 변경에 따라 nuisance 공간이 사라지지 않도록 정규화했고 회귀로 확인했다. 실제 물리 response의 rank는 다음 단계에서 계산한다.

![반응 식별성 실험](../response_laboratory/response_identifiability.png)

[이론 유도](../../research/THEORY_REBOOT.md)는 endpoint Lorentz/STF response, nuisance quotient, 두-shellrank, 공유sky covariance와 restricted BianchiI shear history를 연결한다. Wolfram과 NumPy 확인은 경량 계산 근거이며 four-axisCAS, 새 strong no-go 또는 native family 판정이 아니다.

## 전체 분석을 계속하는 계획

{report['development_tasks']}개 개발/PR 카드와 {report['analysis_opportunities']}개 추가 분석 기회를 연결했다. 현재 완료는 RB00의 scoped reboot다. 나머지 카드는 실제 관측 법칙·처리 응답·물리 반응·추론과 새로운 결과를 완결하는 일이다. ACT/Planck lensing, SPT/ACT/BK/Planck spectra, CLASS/FFP10/BeyondPlanck polarization, JWST/Union3, SDSSdepth, Gaia 등은 현재 파일과 코드에 근거한 작업 목록에 들어간다. 추가기회 census가 저장소 전체를 완전히 조사했다는 뜻은 아니다.

Codex는 [지속 goal 지시](../../AUTONOMOUS_GOALS_KO.md)를 따라 하나의goal을 마치면 다음readygoal로 이동한다. Native atlas 대기는 non-native 결과/보고서를 막지 않는다. [개발 DAG](../../DEVELOPMENT_DAG_KO.md), [GOALS](../../GOALS.json), [복사용 handoff](../../CODEX_HANDOFF_KO.md)가 실행 진입점이다.

## 근거와 재현

새로 실행한 분석의 수치는 report.json의 source_files와 해당 결과 JSON에서 생성했다. 역사적 수치는 legacy 재독 문서의 각 원본 경로에 연결했다. actual argv/exit와 최초 gate-identity 실패/repair는 ../../evidence에 있다. 그림 제목 수정은 저장feature로 재렌더했으며 통계 결과를 재선택하지 않았다. README의 재현 명령은 새 output 디렉터리를 요구한다. 독립 검토의 범위와 최종코드 identity는 ../../review/INDEPENDENT_REVIEW.md에 있다.
'''
    (out/'report.md').write_text(md)
    tex=r'''\documentclass[11pt]{article}
\usepackage[margin=0.8in]{geometry}
\usepackage{graphicx,booktabs,amsmath,hyperref}
\hypersetup{colorlinks=true,urlcolor=blue}
\title{Observational Reboot: Conditional SMICA Pilot and Research Programme}
\author{HTT observational research}\date{14 October 2026}
\begin{document}\maketitle
\begin{abstract}
We executed a source-bound, retrospective exploratory low-mode SMICA experiment,
a finite-null calibration utility, and a local/global response laboratory.
The global rank is @@RANK@@. It is conditional on a declared delivered-simulation
model, not a confirmatory physical Planck null probability or a Bianchi result.
The continuation covers all feasible analyses in the existing theory, code and data.
\end{abstract}
\section{Executed SMICA experiment}
The K1 NSIDE64 cache was verified against its accepted byte-identity gate.
One observation and 300 separately delivered signal/noise pairs use the identical
38,413-pixel mask and simultaneous 36-column $\ell=0,\ldots,5$ fit. Each simulation
component is used once. Training uses 60 pairs; calibration uses the other 240.
The four features are squared norms of retained real harmonic coefficients divided
by $2\ell+1$. These are selected-sky fitted power summaries in $\mu$K$^2$, not
certified unbiased full-sky power estimates.
\begin{center}\begin{tabular}{rrrr}\toprule
$\ell$ & Power summary & Marginal rank & Max-adjusted rank\\\midrule
@@ROWS@@
\bottomrule\end{tabular}\end{center}
The score is the maximum of four absolute departures standardized using training
only. There are @@K@@ exceedances among 240 calibration rows, giving @@RANK@@.
The rank floor is $1/241$. The 95\% Clopper--Pearson interval $[@@LO@@,@@HI@@]$
concerns the IID conditional null-tail probability, not the realized discrete rank.
\begin{figure}[ht]\centering\includegraphics[width=.9\linewidth]{docs/observational_reboot_20261014/results/smica_pilot/joint_null_maximum.pdf}\caption{Actual SMICA, retrospective conditional delivered-simulation rank. The feature family and current split were fixed before this run, after historical examination of this sky.}\end{figure}
\clearpage
\section{Interpretation and historical comparison}
Planck's release describes independent noise/systematic simulations and linear
separate propagation at fixed actual-data weights. The official plancklens library
adds delivered signal and noise maps. This supports our addition recipe, while
observed-simulation exchangeability, foreground residuals, fixed weights and
systematic means remain physical-model obligations. We did not subtract the
simulation mean as an assumed observed bias. The OLS identity residual near
$2.1\times10^{-15}$ verifies algebra, not omitted-mode leakage.

The old K1 rank 0.039 used another processing/statistic family and 999 signals with
300 cyclically reused noise draws. Archive 0.078/0.079 were posterior-predictive
discrepancies combining dipole, CF4 and scalar D2/D3 summaries. The R8 finite-rank enclosures were synthetic
pools. None is an interchangeable predecessor of this result. The legacy review
also identifies $D_\ell/C_\ell$ and STF normalization differences.

\section{Finite-null implementation checks}
A fixed-$B=@@CB@@$, @@CR@@-repetition correlated-feature experiment returned a @@CF@@
global rejection rate; its 95\% binomial interval is [@@CLO@@,@@CHI@@]. Choosing the
smallest unadjusted marginal rank returned @@NF@@. The campaign is conditional on one fixed independent training sample. This tests the declared synthetic
procedure, not empirical Planck calibration. Tests exercise exact inclusive ties,
binomial interval coverage, disjoint training, same-sky rejection and projection.
\begin{figure}[ht]\centering\includegraphics[width=.93\linewidth]{docs/observational_reboot_20261014/results/synthetic_calibration/synthetic_calibration_campaign.pdf}\caption{Synthetic calibration experiment. Error rates apply to the specified correlated Gaussian generator; the Planck physical law is a separate obligation.}\end{figure}
\clearpage
\section{Local/global response and continued analysis}
For a declared linear Gaussian model $y=B\beta_L+G\beta_G+\epsilon$, nuisance
projection after covariance whitening gives the conditional information
$G_w^T(I-P_{B_w})G_w$. In the synthetic laboratory the constant response has rank 0,
the specified depth response has rank 3, and free shell nuisance gives rank 0.
Full rank can still be arbitrarily weakly informative. Nuisance-column normalization
preserves its span under parameter-unit changes.
\begin{figure}[ht]\centering\includegraphics[width=\linewidth]{docs/observational_reboot_20261014/results/response_laboratory/response_identifiability.pdf}\caption{Specified dimensionless response model with known covariance. This is not an observed velocity or global-tilt estimate.}\end{figure}
The theory note derives endpoint boost/STF response, a nuisance quotient,
two-shell discrimination, shared-sky covariance and a restricted Bianchi-I history.
Small Wolfram and NumPy checks are not four-axis CAS admission or a native atlas.

The 23-card DAG and 20-opportunity inventory cover SMICA, physical dipole and
local/global response, CF4/SDSS depth laws, DESI/Union3/JWST distances, released
lensing and spectra, and polarization controls. Codex must assign concrete goals,
execute and review each ready analysis, publish generated figures/reports and
continue. Missing native inputs block their branch only. Capability discovery
continues beyond this sampled inventory; the present completed unit is RB00.

\section*{Source and reproduction pointers}
Full numerical input hashes and source paths: \texttt{report.json}.
Commands, failures and targeted repairs: the sibling \texttt{evidence} directory.
Independent review, goal queue and copyable handoff are linked from the package README.
Primary source context: Planck 2018IV, \href{https://arxiv.org/abs/1807.06208}{arXiv:1807.06208};
Planck 2018VII, \href{https://arxiv.org/abs/1906.02552}{arXiv:1906.02552};
Dai--Chluba, \href{https://arxiv.org/abs/1403.6117}{arXiv:1403.6117};
Roldan et al., \href{https://arxiv.org/abs/1603.02664}{arXiv:1603.02664};
Saadeh et al., \href{https://arxiv.org/abs/1605.07178}{arXiv:1605.07178}.
See the source registry for exact read scope and methodological limits.
\end{document}
'''
    repl={'RANK':f"{g['p_rank_exact']} = {g['p_rank']:.6f}",'ROWS':'\n'.join(texrows),
          'CB':str(cb),'CR':str(cr),'CF':f'{cf:.3f}','NF':f'{nf:.3f}',
          'CLO':f'{clo:.5f}','CHI':f'{chi:.5f}', 'K':str(g['k_ge']),'LO':f"{g['q_interval'][0]:.6f}",'HI':f"{g['q_interval'][1]:.6f}"}
    for k,v in repl.items():tex=tex.replace('@@'+k+'@@',v)
    (out/'reboot_report.tex').write_text(tex)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args();r=build(args.output_dir)
    print(json.dumps({'status':r['status'],'rank':r['smica_global_rank']['p_rank'],'output':str(args.output_dir)}))
