# Manticore-Local 속도장 경로 재검증

2026-11-24 분석 머신에서 **실현별 시선속도 1,120개를 실제 수신했다**. McAlpine et al.의 공식 VizieR 카탈로그에서 14개 은하단 각각의 MCMC 실현 0–79를 구분할 수 있다. H02의 임의 CF4 창에 투영할 3차원 Manticore 속도 격자는 여전히 미수신이다. [공식 배포 목록](https://digitaltwin.fysik.su.se/data-access.html) · [VizieR 데이터 DOI](https://doi.org/10.26093/cds/vizier/bg-gw-pc) · [R105 경로 기록](../R105_RESEARCH_20261124/MANTICORE_ROUTES_KO.md)

| 확인한 자료 | 실제 바이트와 의미 |
|---|---|
| Manticore-Local 3차원 속도장 | 저자 패키지 최신 공개 버전 2.0.1의 IAP 구성 URL과 `manticore-local/R1024/mcmc_{0,1}/velocity_fields/N256/field.h5`에 각각 Range GET을 재실행했다. 세 요청 모두 TCP 연결 제한 5초에 도달했고 수신량은 0 B였다. Stockholm 데이터 페이지와 저자 튜토리얼은 같은 배포 경로를 안내한다. DataCite에서 Manticore-Local/Manticore Project와 Dataset 유형으로 검색한 3건은 공식 은하단 자료와 다른 연구의 Zenodo 버전 2건이었다. 확인한 범위에서 256³ 격자 독립 미러는 발견되지 않았다. |
| Manticore 실현별 LOS | Harvard VizieR 미러에서 `J/MNRAS/540/716/clusters` 전체 응답 HTTP 200, 149,851 B. `SampleID`는 MCMC 실현 번호이고 `Vpec`은 LOS km/s이다. (은하단, SampleID) 1,120쌍이 모두 고유했다. Abell 119 실현 0, 1의 값은 각각 +105.747, −125.114 km/s이고, 80개 실현의 중앙값은 +166.970 km/s였다. 은하단별로 대응되는 halo의 위치도 실현에 따라 달라진다. 이 표는 고정된 CF4 은하 좌표에서 추출한 속도 사슬과 관측 대상이 다르다. [Harvard TSV](https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=J/MNRAS/540/716/clusters&-out.max=2000) |
| Manticore 파생 LOS 요약 | 메이저 은하 5개에 대한 표 6은 은하 거리 posterior와 동일 가중 Manticore 실현에 걸쳐 요약한 결과다. 예를 들어 UGC 3789의 총 시선속도 중앙값과 중앙 68% 구간은 −45 ± 42 km/s이다. 저자 HTML 980,775 B 수신, SHA-256 `23cc86f7939fc7f659558480e450581026fbb5e3b85eb7719799c1c278e4beab`. 개별 실현 번호는 이 표에서 복원할 수 없다. [Stiskalek & Desmond, 표 6](https://arxiv.org/html/2609.17684v1#S4.T6) |
| 다른 재구성의 적색편이 공간 대조장 | Said의 `pvhub`에서 C15 유래 `2MPP_redshift.txt`의 처음과 중간 각 4,096 B를 HTTP 206으로 수신했다. 총 118,643,392 B, 배포된 Git LFS SHA-256과 응답 ETag가 모두 `cc39a3db9cc02b52afc372bc81d26791c41f81c7991fd118f4388b221c86eecc`다. 파일 전체 해시는 LFS 포인터가 제공한 값이다. 표에는 `sgx,sgy,sgz,vproj_2MPP,vpred_x,vpred_y,vpred_z`가 있다. 실제 중간 행 (0, −14375, −6250)의 LOS 값은 +169.985544 km/s였다. 저자 API는 CMB 프레임 적색편이와 RA/Dec에서 LOS를 돌려준다. 129³ 초은하 좌표 적색편이 공간 표를 C15 평균장 민감도 검사에 사용할 수 있다. 실공간 Cartesian 원본 및 Manticore 사후장과 좌표·제품 계보가 다르다. [저자 배포 커밋](https://github.com/KSaid-1/pvhub/tree/2b016e9ae281aff1b35f3691d293f2d6a9020e13) |

다음 명령은 다운로드 결과의 데이터 행과 실제 LFS 바이트를 검증한다. VizieR 응답의 생성 시각은 변할 수 있으므로 정렬된 과학 행 (은하단명, 실현 번호, 소수 세 자리 LOS)의 SHA-256을 고정했다. Harvard 미러가 간헐적으로 빈 테이블을 HTTP 200으로 반환하는 경우도 관측했다. 분석 머신에는 실제 수신한 149,851 B 표가 `~/Downloads/htt_r109_manticore/clusters_vizier.tsv`에 보관되어 있다.

```bash
python3 - <<'PY'
import hashlib
from pathlib import Path
import time
import requests

url = "https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?-source=J/MNRAS/540/716/clusters&-out.max=2000"
cache = Path.home() / "Downloads/htt_r109_manticore/clusters_vizier.tsv"
def valid(body):
    rows = []
    for line in body.decode("utf8", errors="replace").splitlines():
        f = line.split("\t")
        if len(f) >= 16 and f[15].strip().isdecimal():
            rows.append((f[3].strip(), int(f[15]), float(f[10])))
    plain = ("\n".join(f"{n}\t{i}\t{v:.3f}" for n,i,v in sorted(rows))+"\n").encode()
    return len(rows) == 1120 and hashlib.sha256(plain).hexdigest() == "1403fadce3a9f083870e1f6f2ac70e1e9af810d242ca0ace0810c001844c1246"

if cache.exists():
    assert valid(cache.read_bytes()), "existing cache failed scientific row verification"
else:
    for attempt in range(5):
        resp = requests.get(url, timeout=(5, 15))
        resp.raise_for_status()
        if valid(resp.content):
            cache.parent.mkdir(parents=True, exist_ok=True)
            with cache.open("xb") as f:
                f.write(resp.content)
            break
        time.sleep(1 + attempt)
    else:
        raise RuntimeError("VizieR responded without the 1120 verified rows")
url = "https://media.githubusercontent.com/media/KSaid-1/pvhub/2b016e9ae281aff1b35f3691d293f2d6a9020e13/data/2MPP_redshift.txt"
for offset, digest in [(0, "feb7dd3fe252482d59372c30ca515ff66cb6c80199d53694b688b8b7cd4d98c6"), (59321696, "e6e30b5d2bb05e77be18fdc472dbcdef32a5b9c69883c3fc4608795df5582a6d")]:
    span = f"{offset}-{offset+4095}"
    with requests.get(url, headers={"Range": "bytes="+span, "Accept-Encoding": "identity"}, stream=True, timeout=(5, 12)) as r:
        assert r.status_code == 206 and r.headers["Content-Range"] == f"bytes {span}/118643392"
        assert hashlib.sha256(r.raw.read(4096)).hexdigest() == digest
print("Verified 1120 Manticore cluster LOS rows and two pvhub ranges")
PY
```

H02의 36개 창에서 Manticore 공분산을 계산하려면 IAP가 응답하는 환경에서 기존 `scripts.r103.manticore_cf4_pv fetch`를 사용한다. 버킷·객체 키·ETag를 확인한 후 전송된 원본의 SHA-256 및 격자 구조를 검증하도록 구현돼 있다. 수신한 은하단 표는 14개 대응 은하단의 실현 간 공동 통계와 LOS 부호·단위 검산에 바로 쓸 수 있다.

## 14개 은하단의 실현별 LOS 공분산

같은 SampleID의 14개 속도를 한 벡터로 묶었다. 균일한 80개 실현에 대해 각 은하단의 평균을 빼고 모집단 분모 80을 사용했다. 실제 행렬은 대칭 잔차 0, 수치 계수 14이며, 고유값 범위는 3,613.282–60,917.711 (km/s)²이다. 대각합은 252,034.227 (km/s)²다. Abell 119와 Abell 496 사이 공분산은 +1,449.414 (km/s)², 상관계수는 +0.125835다. 이 수치는 2M++로 제약된 Manticore의 대응 halo 표본에서 얻은 속도 분산이다. CF4 은하에 최근접 halo를 배정하거나 36차원 창에 대입한 적은 없다.

| 실제 분석 머신의 영구 파일 | SHA-256 |
|---|---|
| `/home/cosmosapjw/Downloads/htt_r109_manticore/clusters_vizier.tsv` | 원 수신본 `6e3aefcea1b5e244d1d678a096f4372062ba1549250866a2d572d512d3b170ed`. 은하단명·SampleID 순으로 정렬한 과학 행 `1403fadce3a9f083870e1f6f2ac70e1e9af810d242ca0ace0810c001844c1246`. |
| `/home/cosmosapjw/Downloads/htt_r109_manticore/cluster_los_covariance.tsv` | 이름순 행·열에 매긴 14×14 행렬 `88c79490c9329ac2f5f2aec09c6bfbd1eb7c3f5a07d49837cd723fefbe8d5bd9`. |

```python
from pathlib import Path
import numpy as np

p = Path.home() / "Downloads/htt_r109_manticore/clusters_vizier.tsv"
values = {}
for line in p.read_text().splitlines():
    f = line.split("\t")
    if len(f) >= 16 and f[15].strip().isdecimal():
        key = f[3].strip(), int(f[15])
        assert key not in values
        values[key] = float(f[10])
names = sorted({k for k, i in values})
assert len(names) == 14 and len(values) == 1120
v = np.array([[values[k, i] for k in names] for i in range(80)])
v -= v.mean(axis=0)
cov = v.T @ v / 80
np.testing.assert_allclose(cov, np.loadtxt(p.with_name("cluster_los_covariance.tsv"),
    delimiter="\t", skiprows=1, usecols=range(1, 15)), rtol=1e-11)
print(np.linalg.matrix_rank(cov), np.linalg.eigvalsh(cov)[[0, -1]])
```
