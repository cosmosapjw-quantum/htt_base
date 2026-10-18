"""Create native V02 report/figure/receipt from saved finite output only."""
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

HERE=Path(__file__).resolve().parent
OUT=HERE/'results'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    targets=[OUT/'NATIVE_RESPONSE.png',OUT/'NATIVE_RESPONSE.pdf',HERE/'REPORT_KO.md',HERE/'EXECUTION_RECEIPT.json']
    if any(p.exists() for p in targets):
        raise FileExistsError('CREATE_ONLY_FINALIZATION')
    r=json.loads((OUT/'NATIVE_RESPONSE.json').read_text())
    with np.load(OUT/'NATIVE_RESPONSE.npz',allow_pickle=False) as z:
        residual=z['finite_minus_linear_microK']
        discrepancy=z['native_minus_centre_increment_microK']
        baseline=z['baseline_mismatch_microK']
    fig,axes=plt.subplots(1,3,figsize=(12.5,3.8),constrained_layout=True)
    for i,row in enumerate(r['experiments']):
        axes[0].plot(np.arange(32),residual[i],label=f"|beta|={row['speed']:.6g}")
        axes[1].plot(np.arange(32),discrepancy[i],label=f"|beta|={row['speed']:.6g}")
    axes[0].set(xlabel='retained real coefficient index',ylabel='finite minus J beta [microK]')
    axes[1].set(xlabel='retained real coefficient index',ylabel='native minus centre increment [microK]')
    x=np.arange(3)
    axes[2].bar(x-.18,r['native_jacobian_singular_values_microK_per_beta'],.36,label='native children')
    axes[2].bar(x+.18,r['matched_centre_jacobian_singular_values_microK_per_beta'],.36,label='centre')
    axes[2].set(xticks=x,xticklabels=['1','2','3'],xlabel='geometric singular value index',ylabel='singular value [microK per beta]')
    for a in axes:
        a.grid(alpha=.2);a.legend(fontsize=7)
    fig.suptitle('Defined finite SMICA_FULL source: native-child processing on exact T26846 support\n'
                 'obsstat C0 DIAGNOSTIC; empirical proxy; physical covariance UNKNOWN',fontsize=10)
    for suffix in ('png','pdf'):
        fig.savefig(OUT/('NATIVE_RESPONSE.'+suffix),dpi=180)
    plt.close(fig)
    controls=r['controls']
    lines=['# V02 source-defined finite native-child 처리 확장','',
        'obsstat / C0 / DIAGNOSTIC_ONLY / non-claim-bearing. Author 실행 완료이며 fresh independent review 대기 중이다.',
        '원래 acceptance “Matched mask/beam/input and mode leakage”를 보존했다. 기존 centre candidate의 모든 byte와 일곱 실험을 보존했고 재실행하지 않았다.','',
        '원본 SMICA_FULL saved fit로 정의한 같은 s=a_fit/b_INT를 사용했다. 실제 INT_BEAM 1회 → native2048 합성 → 원래 source-valid 1024-child 평균 → 정확한 T26846 선택 → RING64 centre ell0..5 OLS → ell2..5 유지 순서이다.',
        '원래 producer의 finite(I_STOKES) 및 I_STOKES>-1e20 조건을 실제 native I에서 한 번 확인해 고정했다. 선택 mask는 cache confidence>.5와 TMASK coverage>=.995의 원래 규칙이다.','',
        f"선택 mask SHA256 `{r['mask']['sha256']}`. 선택 parent의 최소 실제 value coverage={r['mask']['minimum_selected_actual_value_coverage']:.12g}; TMASK-valid이지만 I-invalid인 native 수={r['mask']['TMASK_valid_but_I_invalid_count']}.",
        '',f"별도 baseline mismatch ||A_native B_INT s-a_fit||={r['baseline_mismatch_norm_microK']:.12g} microK (최대 절댓값 {r['baseline_mismatch_max_abs_microK']:.12g}). 이 차이를 강제로 0으로 만들거나 source를 재정의하지 않았다. 최종 주입은 a_fit+d_native이다.",'',
        '| beta 크기 | native increment norm (microK) | finite-Jbeta norm (microK) | remainder/beta² (microK) | native-centre increment (microK) |',
        '|---:|---:|---:|---:|---:|']
    for row in r['experiments']:
        lines.append('| '+ ' | '.join(f"{row[k]:.12g}" for k in ('speed','increment_norm_microK','finite_minus_linear_norm_microK','finite_minus_linear_over_beta2_microK','native_minus_matched_centre_increment_norm_microK'))+' |')
    lines += ['', '방향은 (1,2,3)/sqrt(14)라는 설계점이며 velocity 추정값이 아니다. 각 32성분 finite 잔차, 처리 차이, baseline mismatch와 a_fit+d_native는 NPZ에 보존했다.', '',
        'native J geometric singular values (microK/beta): '+', '.join(f'{x:.12g}' for x in r['native_jacobian_singular_values_microK_per_beta'])+'.',
        f"native-centre J operator norm 차이={r['native_minus_centre_jacobian_operator_norm_microK_per_beta']:.12g} microK/beta.",'',
        f"zero increment propagation bound={controls['zero_increment_propagated_bound_microK']:.12g} microK (<=1e-9). FWL/joint 최대 차이={controls['nuisance_FWL_vs_joint_fit_max_microK_per_beta']:.12g} microK/beta (<=1e-8). Constant nuisance retained 최대값={controls['constant_pixel_to_retained_max_microK']:.12g} microK.",
        f"여섯 native field의 direct-realY synthesis 최대 차이={max(x['hp_vs_direct_samples_max_microK'] for x in controls['native_field_controls']):.12g} microK; partially masked parent를 포함한 explicit child-sum 최대 차이={max(x['stream_vs_explicit_child_sum_max_microK'] for x in controls['native_field_controls']):.12g} microK.",'',
        '새 focused tests 4 PASS (1.17s): sine/cosine harmonic 합성, partially masked child reducer 및 constant, joint/FWL 및 monopole, invalid geometry. 전체 repository suite NOT_RUN. Native full map은 여섯 개만 한 번에 하나씩 처리했다. First failure가 있으면 EXECUTION_RAW.log에 보존한다.','',
        '32x64/48x96 quadrature 및 ell12/16 finite coefficient 비교의 propagation envelope는 JSON에 있다. 이는 명시한 유한 coefficient 차이의 비교용 상계이며 infinite Lorentz tail, physical covariance 또는 물리 uncertainty가 아니다.',
        'Physical upstream processing mapping, covariance, identified physical rank는 UNKNOWN이다. 이는 이 정의된 finite operation을 수행할 외부 blocker가 아니다. local/global 분리, posterior, p-value, 물리 velocity 또는 Bianchi-family admission은 없다.','',
        f"실행 {r['seconds']:.3f}s; Python {r['runtime']['python']}, NumPy {r['runtime']['numpy']}, healpy {r['runtime']['healpy']}; BLAS/OMP/MKL 각2 threads. Requested gpt-6.1-sol/high, observed UNKNOWN. Child commit/push 및 DAG 변경 없음.",'',
        '![Native finite diagnostics](results/NATIVE_RESPONSE.png)','',
        '그림 provenance: owner obsstat; category DIAGNOSTIC; C0; transfer empirical_proxy; null NOT_QUALIFIED; covariance UNKNOWN. Allowed use는 저장된 유한 source의 linearization 및 processing 비교이다. 물리 유의도·velocity·local/global rank·geometry/family 식별에 사용하지 않는다. Source는 results/NATIVE_RESPONSE.json 및 NPZ, 생성기는 finalize_native.py이다. 무작위 생성 없는 결정론적 그림이다.','',
        'Fresh read-only reviewer만 PASS_SCOPED_V02_SOURCE_DEFINED_FINITE_NATIVE_PROCESSING 여부를 판단한다. Parent가 그 결정에 따라 원래 V02 node와 다음 READY transition을 처리한다.']
    (HERE/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    files=[]
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.name!='EXECUTION_RECEIPT.json':
            files.append({'path':str(p.relative_to(HERE)),'bytes':p.stat().st_size,'sha256':digest(p)})
    receipt={'schema':'htt.V02_native_extension_execution_receipt/1','owner':'obsstat','claim_tier':'C0',
        'status':'EXECUTED_PENDING_FRESH_INDEPENDENT_REVIEW','scope':r['scope'],
        'original_acceptance':'Matched mask/beam/input and mode leakage',
        'actual_native_runs':1,'native_projected_fields':6,'existing_centre_experiments_rerun':False,
        'existing_centre_bytes_preserved':r['centre_evidence_preserved'],'native_map_run_exit_code':0,
        'raw_log':'EXECUTION_RAW.log','process_session_id':26144,
        'focused_tests':{'result':'4 PASS','seconds':1.17,'command':'.venv/bin/python -B -m pytest -q '+str(HERE/'test_native_processing.py'),
                         'whole_repository':'NOT_RUN'},
        'scientific_command':'.venv/bin/python -B -u '+str(HERE/'native_processing.py'),
        'threads':r['runtime']['threads'],'runtime':r['runtime'],
        'requested_model':r['requested_model'],'requested_effort':r['requested_effort'],
        'observed_model':'UNKNOWN','observed_effort':'UNKNOWN','base_head':r['base_head'],
        'independent_review':'PARENT_ASSIGNED_READ_ONLY_REVIEWER_PENDING',
        'original_node_completion':'NOT_SELF_ADMITTED','physical_upstream_response':'UNKNOWN',
        'physical_covariance':'UNKNOWN','publication':'NO_CHILD_COMMIT_OR_PUSH','files':files}
    (HERE/'EXECUTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'report':'REPORT_KO.md','files':len(files),'native_results_sha256':digest(OUT/'NATIVE_RESPONSE.json'),
                      'receipt_sha256':digest(HERE/'EXECUTION_RECEIPT.json')},indent=2))


if __name__=='__main__':
    main()
