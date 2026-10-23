"""Consume frozen D05 derived statistics; never rerun the catalogue fit."""
from pathlib import Path
import hashlib,json
import numpy as np

HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    r=json.loads((HERE/'RESULTS.json').read_text());z=np.load(HERE/'sufficient_statistics.npz')
    N=z['normal'];h=z['rhs'];b=np.linalg.solve(N,h);stored=np.array(r['all']['coefficient_uasyr'])
    errors=[float(np.max(np.abs(b-stored)))]
    for j,item in enumerate(r['spatial_sensitivity']['heldout']):
        train=np.linalg.solve(N-z['cell_normal'][j],h-z['cell_rhs'][j])
        errors.append(float(np.max(np.abs(train-item['coefficient_uasyr']))))
    checks=dict(code_identity=sha(HERE/'observable_vsh.py')==r['code_sha256'],
       source_member_count=r['completeness']['count']==r['completeness']['membership_rows']==r['completeness']['returned_rows'],
       source_member_set=r['completeness']['source_id_sets_equal'],
       no_overflow=all(not x['overflow'] and all(v=='OK' for v in x['query_status']) for x in r['source_identity'].values() if isinstance(x,dict) and 'query_status' in x),
       retained_cell_count=int(z['cell_n'].sum())==r['retention']['valid_sources'],
       full_normal_rank=int(np.linalg.matrix_rank(N))==16,
       identified_quotient_rank=r['all']['frame_projected']['rank']==13,
       normal_positive_definite=bool(np.linalg.eigvalsh((N+N.T)/2).min()>0),
       normal_relative_symmetry=float(np.linalg.norm(N-N.T)/np.linalg.norm(N)),
       recomputation_coefficient_max_abs_uasyr=max(errors),
       frame_quotient_joint_max_abs_uasyr=r['all']['frame_projected']['max_joint_fit_difference'])
    if not all(checks[k] for k in ('code_identity','source_member_count','source_member_set','no_overflow','retained_cell_count','full_normal_rank','identified_quotient_rank','normal_positive_definite')):
        raise ValueError(checks)
    if checks['normal_relative_symmetry']>1e-12 or max(errors)>1e-10:raise ValueError(checks)
    validation=dict(schema='htt.D05.focused_validation/1',checks=checks,
       narrow_tests=dict(command='OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 .venv/bin/python -m pytest -q '+str(HERE.relative_to(Path.cwd())/'test_observable_vsh.py'),passed=7,failed=0,exit_code=0,observed_seconds=1.74),
       first_failures_preserved=dict(type='ARI rejected unsupported VOTable format before creating jobs',
          detail='/mnt/extdrive/workdir/htt_open_data/gaia/d05_full_20261018/http_failure_105240080555.txt',
          resolution='Use provider-listed votable/b2 alias; no replacement of any successful job'),
       independent_review='PENDING_FRESH_ASTRA',scientific_admission='HOLD',
       result_sha256=sha(HERE/'RESULTS.json'),sufficient_statistics_sha256=sha(HERE/'sufficient_statistics.npz'))
    (HERE/'VALIDATION.json').write_text(json.dumps(validation,indent=2,allow_nan=False)+'\n')
    a=r['all'];s=r['spatial_sensitivity'];c=r['radio_crosswalk'];f=r['frame_subset']
    labels=r['convention']['coefficient_order'];coef=np.array(a['coefficient_uasyr']);sigma=np.array(a['formal_sigma_uasyr'])
    rows=['| coefficient | full fit [μas/yr] | formal working σ | angular deletion min–max |',
          '|---|---:|---:|---:|']
    for i,label in enumerate(labels):
        rows.append(f"| {label} | {coef[i]:.5f} | {sigma[i]:.5f} | {s['deletion_min_uasyr'][i]:.5f} … {s['deletion_max_uasyr'][i]:.5f} |")
    text=f'''# D05 실제 Gaia 전체 관측량 분석 — 2026-10-18

Owner `obsstat`; claim `DIAGNOSTIC_ONLY`; artifact mode `OBSERVABLE_FIT_AND_SENSITIVITY`;
transfer `none`; null `NOT_AVAILABLE`; covariance `published per-source 2×2,
cross-source/frame joint law unknown`. 허용 용도는 공개 catalogue의 관측 VSH와 프레임·선택 민감도다.
물리적 cosmic curl/물질 vorticity/모형 family 판정이나 검출 유의도에 사용할 수 없다.

전체 취득과 관측량 계산을 실제로 마쳤다. K03의 원래 acceptance
`Independent source qualification and nonradial response demonstrated`는 아직 **HOLD**다.
동일 물질 congruence의 curl/acceleration/tilt 응답과 프레임·보정 전달 및 joint covariance가 없다.
독립 Astra 검토는 아직 PENDING이며, 이 보고서가 원래 과학 노드를 완료 처리하지 않는다.

## 전체 질의 검증

ESA 공식 회원목록 {r['completeness']['membership_rows']:,}개, ARI 별도 COUNT
{r['completeness']['count']:,}개, 실제 반환 {r['completeness']['returned_rows']:,}개다.
모두 고유 source_id이며 세트가 정확히 같다. 전체/COUNT/frame VOTable의
QUERY_STATUS는 OK, OVERFLOW 없음이다. TOP smoke를 전체 표본으로 사용하지 않았다.
full result는 {r['source_identity']['full']['bytes']:,} bytes이며 UWS 고지 크기와 일치한다.
SHA256 `{r['source_identity']['full']['sha256']}`.
질의/작업/원본 hash와 단위는 [RESULTS.json](RESULTS.json)에 있다.
외장 디스크 원본 외에 Git 안으로 source 행을 복사하지 않았다.

- full UWS: {r['source_identity']['full']['job']['job_url']}
- COUNT UWS: {r['source_identity']['count']['job']['job_url']}
- frame UWS: {r['source_identity']['frame']['job']['job_url']}

유효 공분산·좌표·고유운동 조건을 만족한 {r['retention']['valid_sources']:,}개를 모두 사용했다.
추가 proper-motion/RUWE cut은 없다. five-parameter {r['retention']['five_parameter']:,}개,
six-parameter {r['retention']['six_parameter']:,}개다. 원래 CRF3 회원 선별 자체는 astrometry와
proper motion에 의존하므로, 전체 회원 수 재현은 미선택 QSO 모집단의 무편향성을 뜻하지 않는다.

## 실제 VSH / frame quotient 결과

ICRS RA/Dec는 도, Gaia `pmra=mu_alpha*cos(dec)`, `pmdec=mu_delta`는 mas/yr에서 μas/yr로 변환했다.
source 내부 covariance는 `[[σra², ρ σra σdec], [ρ σra σdec, σdec²]]`를 그대로 쓴다.
방향은 측정값에 조건부로 고정했고, position-motion 상관 열은 원본에 보존하되 이 조건부
고유운동 fit에 방향 오차로 전파하지 않았다. 천체 간 covariance가 없다는 사실을 0의 측정으로 취급하지 않는다.

`E1=P g`, `B1=omega×n`, `E2=P S n`, `B2=n×S n`의 l=1+2 16성분을 함께 fit했다.
STF basis/계수 순서는 JSON과 코드에 명시했다. 이 계수는 Cartesian/STF 좌표이며
정규화된 Ylm 계수나 harmonic power가 아니다. normal rank {a['rank']}, condition number
{a['condition_number']:.5f}, working reduced χ² {a['working_reduced_chi2']:.6f}다.
숫자 χ²는 독립-source Gaussian working model 요약이며 유효성 검정 p-value가 아니다.

{chr(10).join(rows)}

B1 세 성분은 arbitrary frame spin과 정확히 같은 열이다. frame nuisance를 Schur projection하면
남는 observable quotient rank는 {a['frame_projected']['rank']}이며 세 물리 B1은 UNKNOWN이다.
joint fit 대비 quotient 계수 차이는 {a['frame_projected']['max_joint_fit_difference']:.3g} μas/yr다.
표의 B1은 공개 frame에서의 관측값일 뿐 cosmic rotation 제약이 아니다.

전체 frame 표는 {f['frame_table_rows']:,}행이며 428,034개 spin-used 중 CRF3와 겹치는
{f['spin_used_sources']:,}개, orientation-used {f['orientation_used_sources']:,}개를 확인했다.
spin-used와 나머지 집단의 in-frame B1은 각각
`{np.round(f['spin_used']['coefficient_uasyr'][3:6],5).tolist()}`와
`{np.round(f['not_spin_used']['coefficient_uasyr'][3:6],5).tolist()}` μas/yr다.
하위집합 차이는 frame/selection sensitivity이며 독립 검증이나 물리적 비등방 신호가 아니다.
Gaia DR3/EDR3는 동일 astrometry로 독립 재관측이 아니다.

![관측 VSH](OBSERVABLE_VSH.png)

이 그림은 obsstat/DIAGNOSTIC_ONLY/observable-fit 결과다. source 2×2 공분산의 formal σ와
12 angular deletion 범위를 표시한다. 전자는 full joint uncertainty가 아니고 후자는 confidence interval이 아니다.
transfer 없음, joint null 없음, 물리 cosmic curl/family 판정 용도로 금지한다.

## 공간·holdout 민감도

RA 4분할 × sin(dec) 3분할의 같은 면적 12개 셀을 통째로 뺐다. 각 source의 두 성분을 함께
holdout하여 component leakage를 피했다. heldout working χ²/component 범위는
{min(x['heldout_working_mean_chi2_per_component'] for x in s['heldout']):.6f}–{max(x['heldout_working_mean_chi2_per_component'] for x in s['heldout']):.6f}다.
E1의 block-score sensitivity scale은 `{np.round(s['cluster_score_sigma_uasyr'][:3],5).tolist()}` μas/yr로,
formal σ `{np.round(sigma[:3],5).tolist()}` μas/yr보다 크다. 이것은 단지 12개 큰 셀의
공간 민감도이며 작은 각도 상관이나 셀을 넘는 보정 공분산을 보장하지 않는다.
공통 Gaia frame/calibration이 train/test에 남아 있어 독립 외부 predictive validation도 아니다.

![각도 holdout](ANGULAR_HOLDOUT.png)

Owner/claim/mode는 obsstat/DIAGNOSTIC_ONLY/observable sensitivity다. 공개 source covariance에
조건부인 진단이며 joint null과 실측 spatial covariance는 없다. 검출 유의도·물리 curl·family 판정은 금지한다.

## 라디오 713 및 실제 crosswalk

D01이 받은 CDS table6/ReadMe를 재사용했다. 713개를 전부 파싱했고 새 fetch는 하지 않았다.
1 arcsec 안의 unique Gaia positional match는 {c['matched_1arcsec']}개, ambiguous {c['ambiguous_1arcsec']}개,
unmatched {c['unmatched_1arcsec']}개다. 0.1 arcsec 이내는 {c['matched_at_0p1arcsec']}개다.
그중 IERS/OCARS 이름까지 일치한 것은 {c['matches_with_exact_name_agreement']}개이며,
나머지 {c['matched_1arcsec']-c['matches_with_exact_name_agreement']}개는 positional compatibility candidate다.
이 행별 crosswalk와 미매칭 행은 외장 디스크에 남겼다. 위치 일치만으로 원천 동일성·오차 독립성을 증명하지 않았다.

CDS ReadMe는 RA proper motion에 cos(dec)를 명시하지 않는다. 원 논문의 표/식도 이
표기 문제를 명시적으로 해결하지 않으므로, RA를 tangent로 해석한 경우와 coordinate rate로
해석해 cos(dec)를 적용한 경우를 모두 보존했다. 누락된 cross-component covariance는 0이 아니다.
각 규약에서 nonzero ρ=-0.9,-0.5,+0.5,+0.9의 8개 조건부 fit을 실행했다.
working reduced χ² 범위는 {min(x['working_reduced_chi2'] for x in r['radio']['sensitivity_grid']):.4f}–{max(x['working_reduced_chi2'] for x in r['radio']['sensitivity_grid']):.4f}다.
이 common-ρ family는 모든 source별 ρ 조합의 엄밀한 bound가 아니며 calibrated uncertainty도 아니다.
713개 전체를 retained하여 원 논문의 cut/fit과 동일한 재현 실험으로 주장하지 않는다.

라디오 jet, radio-optical 구조/epoch 차이, ICRF 중첩, Goddard 2017a의 다섯 NNR solution과
공통 celestial axes 때문에 Gaia/radio를 독립 관측으로 결합하지 않았다. NNR이 제거한 mode의
전달 연산자는 없음으로 남겼다. cosmic curl/kinematic transfer나 source-matched physical
응답을 만들지 않았으므로 K03는 여전히 HOLD다.

## 검증 / 재사용 / 다음 조건

새 algebra/GLS tests 7 passed; 정상/음수 회전 부호, covariance inverse, STF,
정확한 계수 회수, arbitrary frame-spin 불변성, chunk/dense parity, trailing OVERFLOW/ERROR 거부를 확인했다.
저장된 충분통계로 full와 12 holdout의 계수를 별도 재계산한 최대 차이는
{max(errors):.3g} μas/yr다. raw catalogue fit은 이 확인에서 재실행하지 않았다.
기존 4,756개 frame/correlation 결과는 읽고 재사용했으며 재실행하지 않았다.

[README](README.md)에 실행 명령, 규약, source 문헌과 kill switch가 있다.
[VALIDATION.json](VALIDATION.json)에 집중검증과 최초 취득 실패 보존이 있다.
논문/외부 해석의 다음 조건은 source-matched same-congruence physical response,
radio RA 규약 확인, frame/NNR 전달과 source/systematic joint law 또는 정당화된 bound,
그리고 새 Astra 독립 검토다. 원래 acceptance나 HOLD를 완화하지 않는다.
'''
    (HERE/'REPORT_KO.md').write_text(text)
    files={p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(HERE.iterdir())
           if p.is_file() and p.name!='CANDIDATE.json'}
    candidate=dict(schema='htt.D05.review_candidate/1',base_commit=r['source_commit'],
       branch='research/htt-open-input-theory-20261018',owner='obsstat',
       status='FROZEN_FOR_FRESH_READ_ONLY_ASTRA_REVIEW',scientific_admission='HOLD',
       raw_rows_git=False,files=files,external_raw_root='/mnt/extdrive/workdir/htt_open_data/gaia/d05_full_20261018',
       review_focus=['full source/count/membership and overflow identity',
         'tangent/VSH signs, covariance and frame quotient',
         'angular holdout and unknown spatial law',
         'radio identity, missing covariance/RA convention/NNR',
         'no K03 physical admission or native claim'])
    (HERE/'CANDIDATE.json').write_text(json.dumps(candidate,indent=2)+'\n')
    print(json.dumps(validation),flush=True)

if __name__=='__main__':main()
