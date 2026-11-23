# CORAS 방사속도 계산기 재현 빌드

Linux C++11/OpenMP, GNU ar, GSL과 FFTW3 OpenMP를 사용한다. 빌드는 새 디렉터리에서 진행하며, 기존 checkout을 주면 지정된 CORAS 커밋과 Git 트리를 확인한다. --donor를 생략하면 공개 원본을 내려받아 같은 커밋을 checkout한다. 빌드 디렉터리의 상위 경로는 사용자가 쓸 수 있어야 한다.

시스템에 GSL·FFTW 개발 헤더와 라이브러리가 설치된 경우 다음 명령을 사용한다.

```bash
python scripts/r105/coras_build.py --build-dir /tmp/coras-reproduce-01 --jobs 4
```

워크스테이션 검증에는 기존 깨끗한 donor와 사용자 디렉터리에 풀어 둔 GSL 헤더를 사용했다. --gsl-include에는 gsl/ 하위 폴더를 포함하는 상위 include 경로를 준다. 아래 경로를 현재 호스트에 맞게 바꾸고, 결과 디렉터리는 매번 새로운 이름을 쓴다.

```bash
python scripts/r105/coras_build.py \
  --donor /tmp/htt-r105-coras.6PyQAjZp/CORAS \
  --build-dir /tmp/coras-reproduce-02 --jobs 4 \
  --gsl-include /tmp/htt-r105-coras.6PyQAjZp/gsl_dev/usr/include \
  --gsl-link=-l:libgsl.so.27 --gslcblas-link=-l:libgslcblas.so.0
```

FFTW 헤더가 기본 경로 밖에 있으면 --fftw-include를 쓰고, 라이브러리가 별도 경로에 있으면 --lib-dir를 반복한다. 버전 지정 링크는 --fftw-omp-link=-l:libfftw3_omp.so.3 및 --fftw-link=-l:libfftw3.so.3 형태로 줄 수 있다. 비표준 공유 라이브러리는 실행 시 동적 로더에서도 검색되어야 한다.

완료되면 빌드 디렉터리 안에 coras_radial, libcoras.a, build_receipt.json이 생성된다. 영수증은 donor 커밋·트리, 21개 C++ 구현과 헤더, 2MRS 카탈로그 및 기준 스펙트럼 해시, 실제 선택된 GSL·FFTW 헤더 및 공유 라이브러리 해시, 컴파일·링크 명령, 바이너리 SHA-256과 경로를 기록한다. 데이터 분석 시 이 바이너리를 donor가 현재 디렉터리인 상태에서 실행한다. 첫 인수는 CF4 sites 파일이고 둘째 인수는 사전에 만든 출력 디렉터리다. CLI의 인수 순서는 바이너리를 인수 없이 실행해 확인할 수 있다. 사용법 반환 코드 2를 빌드 smoke test로 사용했다.
