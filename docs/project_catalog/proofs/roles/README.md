# 연구제안 정리 후보와 내부 보조명제

과거 연구제안서가 구체적인 증명 목표로 내놓은 항목과 프로젝트 구현·검증에서
보조 역할을 하는 명제를 구별한 검색용 파생 목록이다. **제안 당시의 역할**을
분류하며, 학술적 신규성·참/거짓·최신 버전의 증명 적용성을 새로 판단하지 않는다.
Owner: COMMON. Scope: static historical research-role navigation.

## 먼저 읽을 목록

| 목록 | 출처·버전을 보존한 구간 수 | 내용 |
|---|---:|---|
| [연구제안의 정리·증명 목표](research_proposals.md) | 172 | 구체적인 후보 진술, 가정, 증명 경로·남은 의무의 원문 |
| [내부 보조명제·문헌 이식](auxiliary_propositions.md) | 94 | 내부 보조 선언 93개와 명시적 문헌 이식 1개 |

각 목록에 같은 이름의 CSV·JSON이 있다. [원문 근거](evidence.md)와
[검토 입력](role_evidence.json)에 정확한 파일·행·내용 버전, 제안 의도 및
기존 DB의 원본 레코드 연결을 보존한다. JSON의 `catalog_source_records`는
해당 구간에 시작하는 원본 DB 기록이며, 증명 완료를 승계하는 연결은 아니다.

구체적인 예는 T-A1의 signed comparator 상쇄/비식별성, NT2-A1의 다중 multipole
Fisher–Cramér–Rao 하한, T-P1의 pole 회전 공변성, T-P18의 공통 latent joint region이다.
보조명제에는 `PR257Orbit.mm_assoc`, 고정 예제 `fixed_beta2`, 상태 논리
`completeness_not_promoted` 등이 있다. 심사 보강안의 T7은 원문이
‘문헌 이식’이라고 명시하므로 기존 결과를 사용하는 항목으로 분리했다.

## 두 종류의 건수를 섞지 않기

위 표는 **직접 읽은 명제 구간** 단위다. 아래 표는 이전 증명 목록의
**검색 항목 묶음** 단위다. 같은 구간에서 여러 검색 항목이 나올 수 있고,
이전 목록이 문서 제목만 보유한 경우도 있다. 제안 목표 중
129개 구간에는 시작 위치가 대응하는 기존 검색 항목이 없어,
이번에 원문 구간과 DB 기록을 직접 연결했다. 이들을 빠뜨리거나 문서 전체를
정리 하나로 세지 않는다. 원본 증명 목록과 SQLite는 변경하지 않았다.

| 기존 검색 묶음의 역할 | 묶음 수 |
|---|---:|
| [과거 연구제안의 구체적 정리·증명 후보](research_proposal_candidate.md) | 45 |
| [내부 보조명제·검증 보조정리](internal_auxiliary.md) | 93 |
| [기존 결과를 재사용한 기초·보조명제](supporting_known_result.md) | 0 |
| [제안 후보이면서 보조 역할도 확인](mixed_role.md) | 0 |
| [역할 판단 보류](unresolved.md) | 39,072 |
| [독립 명제가 아닌 검색 조각](non_proposition_hit.md) | 1,072 |

기존 40,282개 묶음 / 104,780개 출처 발생 기록을 모두 보존했다.
[전체 JSON](all_roles.json.gz), [전체 CSV](all_roles.csv.gz), [집계](summary.json)에서 조회할 수 있다.
건수는 수학적으로 독립이거나 새로운 정리 수가 아니다.

## 판정 기준과 한계

- 연구제안 후보는 제안서의 구체적인 진술과 제안 의도가 함께 있는 경우다.
  제안서가 새로운 증명 목표로 내놓은 보조정리도 여기에 들어갈 수 있다.
- 내부 보조명제는 선언·고정 예제·사용 문맥을 읽어 역할을 확인한 항목이다.
  제안 근거를 찾지 못했다는 사실만으로 이 범주에 넣지 않았다.
- 데이터 실행 티켓, 문서 경계 표식, 상태 표기는 정리와 구별한다.
- 같은 ID라도 다른 문서·가정·버전에는 역할을 자동 전파하지 않는다.
  철회·대체 기록도 삭제하지 않는다. 제안 역할과 현재 유효성은 별개다.
- 검토한 58개 내용 버전의
  370개 경로·버전 사본은
  [원문 검토 목록](source_review.json)에 있다. 명시적 후보 문서, 정리 backlog,
  구판 연구계획과 레지스트리, 저장된 증명 근거의 보조 선언을 표적 대조했다.
- **역할 보류 39,072개는 추가 대조가 필요하다.**
  모든 과거 제안·내부 사용 관계의 의미 검토가 완료됐다는 뜻은 아니다.
  ‘연구제안에 없었다’거나 ‘명제가 거짓이다’라는 판단도 아니다.
- R8 원문 포함 여부와 R8 증명 적용성을 구별한다. 기존 증명 분류는 그대로다.
  제안서의 ‘proved/완전 증명’ 문구만으로 새 후보 전체를 증명 확인으로 승격하지 않는다.
  연구 코드·연구 테스트·CAS·Lean은 실행하지 않았다.

## 재생성 및 조회

SQLite 복원이나 외부 원문 다운로드 없이 배포된 목록과 검토 입력으로 재생성한다.

```bash
python3 -S -B scripts/project_catalog.py export --proof-roles /tmp/htt-proof-roles
```

다른 입력 묶음은 `--proof-inputs PATH --role-evidence PATH/role_evidence.json`으로 지정한다.
입력 내용이나 출처 연결이 바뀌면 기존 검토를 재사용하지 않고 오류를 낸다.

```python
import gzip, json
from pathlib import Path
p = Path("docs/project_catalog/proofs/roles")
proposals = json.loads((p / "research_proposals.json").read_text())
print([(r["proposed_id"], r["title"]) for r in proposals
       if "T-P" in (r["proposed_id"] or "")])
with gzip.open(p / "all_roles.json.gz", "rt") as f:
    rows = json.load(f)
print([r["title"] for r in rows if r["role"] == "internal_auxiliary"
       and r["proof_classification"] == "existing_proof_support_confirmed"])
```
