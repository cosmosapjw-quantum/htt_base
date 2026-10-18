"""Assemble numerical report and small review receipt from completed outputs."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    target = HERE/'REPORT_KO.md'
    receipt = HERE/'EXECUTION_RECEIPT.json'
    if target.exists() or receipt.exists(): raise FileExistsError('CREATE_ONLY_CLOSEOUT')
    r = json.loads((HERE/'results/V02_FINITE_RESPONSE.json').read_text())
    check = json.loads((HERE/'results/V02_ANALYTIC_GENERATOR_CHECK.json').read_text())
    c = r['controls']
    rows = ['| 방향 | beta | finite 주입 norm (microK) | finite-linear (microK) | ell6..16 누출 (microK) | 잘못된 beam 순서 차이 (microK) |',
            '|---|---:|---:|---:|---:|---:|']
    for x in r['experiments']:
        rows.append('| '+x['label']+' | '+format(x['speed'], '.6g')+' | '+
                    ' | '.join(format(x[k], '.9g') for k in ('injection_norm_microK', 'finite_minus_linear_norm_microK',
                         'finite_mode_leakage_ell6_16_to_fit2_5_microK', 'wrong_boost_after_beam_delta_microK'))+' |')
    generic = [x for x in r['experiments'] if x['label'] == 'generic']
    low, high = min(x['remainder_over_beta_squared_microK'] for x in generic), max(x['remainder_over_beta_squared_microK'] for x in generic)
    report = f'''# V02: 실제 T source에 묶인 finite delivered-fit counterfactual

obsstat / C0 / DIAGNOSTIC_ONLY / non-claim-bearing. Fresh independent review 전
author 단계이며 original V02의 완료 또는 과학적 admission을 선언하지 않는다.

원래 objective는 “Inject finite local observer boost through the actual processed
Planck source”, output은 “local response columns with covariance/error envelopes”,
acceptance는 “Matched mask/beam/input and mode leakage”이다. 이 기준을 변경하거나
full physical-null qualification을 V02의 추가 gate로 만들지 않았다.

원본 NPZ의 SMICA_FULL masked-fit ell2..5 계수로 유한 source를 **정의**했다.
이를 실제 SMICA INT_BEAM의 같은 ell2..5 항으로 나눈 뒤 exact scalar finite
Lorentz pullback → 실제 INT_BEAM 1회 → RING64 합성 → 실제 T26846 mask →
ell0..5 동시 OLS → ell2..5 유지 순서로 처리했다. 원본 계수가 intrinsic sky
계수라는 가정, 알려지지 않은 물리 monopole/high modes의 zero filling은 없다.
좌표는 outward, beta=v/c, metric(-,+,+,+), signed perturbation의 Doppler weight1이다.
세부 정의와 식, 출처 및 acceptance mapping은 METHOD_AND_ACCEPTANCE.md에 있다.

## 실제 실행 결과

실제 common/HM/OE TMASK를 native에서 AND하고 parent coverage>=0.995 및
기존 K1 confidence>0.5를 적용해 {r['mask']['pixels']:,}개 RING64 support를 재구성했다.
mask SHA256: `{r['mask']['sha256']}`.

{chr(10).join(rows)}

generic 방향은 (1,2,3)/sqrt(14)라는 설계점이다. beta=.00123은 주입 크기이며
관측 solar velocity를 추정한 값이 아니다. generic remainder/beta²는 위 유한
주입점에서 {low:.9g}–{high:.9g} microK 범위이다. 원본 범위 밖의 source에 대한
보편적 remainder bound로 해석하지 않는다.

이 finite masked map의 32x3 local derivative geometric singular values는
{', '.join(format(x, '.10g') for x in r['geometric_response']['singular_values_microK_per_beta'])}
microK/beta이다. 수치 rank는 {r['geometric_response']['rank_numerical']}이지만 covariance-whitened
rank가 아니며 foreground/calibration nuisance 전체를 제거한 물리 rank는 UNKNOWN이다.
pixel monopole/dipole만 실제 selected design에서 FWL로 quotient했다.

## 검증과 오차 진단

- unchanged 원본 T ell6..16 leakage matrix 최대 차이: {c['original_mode_leakage_max_abs_delta']:.9g}.
- beta=0 원본 retained coefficient replay 최대 차이: {c['zero_beta_fit_replay_max_microK']:.9g} microK.
- FWL quotient vs simultaneous fit 최대 차이: {c['nuisance_FWL_vs_joint_fit_max_microK_per_beta']:.9g} microK/beta.
- h=1e-5 vs 5e-6 finite-difference operator 차이: {c['derivative_h1e5_vs_h5e6_operator_delta_microK_per_beta']:.9g} microK/beta.
- unchanged analytic generator vs saved derivative 상대 operator 차이: {check['relative_operator_delta']:.9g}.
- 주입 전체의 32x64 vs 48x96 quadrature 최대 retained 차이: {max(x['quadrature_32_vs48_delta_microK'] for x in r['experiments']):.9g} microK.
- ell12 vs ell16 cutoff 최대 retained 차이: {max(x['cutoff12_vs16_delta_microK'] for x in r['experiments']):.9g} microK.

위 quadrature/cutoff 비교는 empirical numerical diagnostics이며 certified
infinite-tail bound 또는 physical sampling covariance가 아니다. response columns,
주입·remainder·누출·잘못된 beam 순서 차이는 NPZ에 함께 보존했다.
초기 새 unit-test의 두 roundoff 실패는 FIRST_FAILURE.txt의 raw output에 남겼다.
최종 focused tests는 8 PASS; 전체 repository suite는 NOT_RUN이다.

## 원래 acceptance에 대한 정확한 범위

source archive·actual TMASK·actual INT_BEAM·masked finite leakage가 연결된
finite counterfactual과 pixel monopole/dipole-projected local columns를 계산했다.
단, 실제 released Planck frequency/component-separation/calibration processing에
upstream observer injection을 운반하는 응답은 이 source fit만으로 정해지지 않는다.
이를 보충할 실제 bandpass/frequency response와 processing/frame mapping은 제공되지
않았다. 물리 response uncertainty와 covariance는 UNKNOWN으로 남겼다.

native-child masked averaging은 로컬에서 실행할 수 있는 별도 연산이다.
이번 RING64-centre counterfactual에서는 NOT_RUN이며 external missing input으로
기록하지 않는다. 기존 L01 finite response가 해당 확장을 지원한다.
physical source의 미지 high modes, polarization 및 upstream processing remainder는
유한 source 정의로 제한되거나 bound되었다고 주장하지 않는다.

Matched signal/noise/foreground law는 downstream 통계 해석의 제한이며 V02의
새 acceptance gate가 아니다. fresh reviewer가 원래 acceptance와 실제 지원되는
source 범위를 판단해야 한다. V03 global-history response, local/global inference,
physical observer velocity, likelihood/p-value, native solver 결과는 생성하지 않았다.

## Runtime 및 산출물

실행 {r['seconds']:.3f}s; Python {r['runtime']['python']}, NumPy {r['runtime']['numpy']},
SciPy {r['runtime']['scipy']}, healpy {r['runtime']['healpy']}; BLAS/OMP/MKL 각2 threads.
requested gpt-6.1-sol/high; observed model/effort UNKNOWN. source byte identities와
실제 beam 값은 generated result JSON에 있다. claim-bearing publication은 없으며
child commit/push도 하지 않았다. parent의 다른 lane 파일은 수정하지 않았다.

![Finite counterfactual diagnostics](results/V02_FINITE_RESPONSE.png)

그림은 위 생성 결과만 사용한다. 실제 mask/beam 아래 유한 주입, linearization
remainder, high-mode leakage 및 geometric singular values를 보여준다. covariance,
physical velocity 또는 local/global 식별 claim은 담지 않는다.
'''
    with target.open('x') as stream: stream.write(report)
    files = [p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and p != receipt]
    payload = {'schema':'htt.V02_counterfactual_execution_receipt/1', 'owner':'obsstat','claim_tier':'C0',
               'status':'EXECUTED_PENDING_FRESH_INDEPENDENT_REVIEW',
               'scope':'Finite SMICA_FULL delivered-fit source counterfactual, actual T26846 support and INT_BEAM',
               'tests':{'focused_distinct':8,'result':'PASS','initial_result':'2 FAIL, 6 PASS; raw FIRST_FAILURE.txt',
                        'whole_repository':'NOT_RUN'},
               'actual_source_experiment_runs':1, 'new_native_child_processing':False,
               'analytic_oracle':'UNCHANGED_GIT_SOURCE_CHECK_EXECUTED',
               'fresh_independent_review':'PARENT_TO_ASSIGN', 'publication':'NO_CHILD_COMMIT_OR_PUSH',
               'runtime':r['runtime'], 'seconds':r['seconds'],
               'original_acceptance':'Matched mask/beam/input and mode leakage',
               'original_node_completion':'NOT_SELF_ADMITTED', 'physical_uncertainty':'UNKNOWN',
               'files':[{'path':str(p.relative_to(HERE)), 'bytes':p.stat().st_size,
                         'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
    with receipt.open('x') as stream: json.dump(payload, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps({'report':str(target),'receipt':str(receipt),'files':len(files)}))


if __name__ == '__main__': main()
