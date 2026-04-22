# 10. Symbolic Automation and Numerical Verification
## frozen-constant derivation / independent verification / cross-check results

---

## 0. purpose

이 문서는 v5 design pack에서 formerly unresolved placeholder 대상이었던 식과 상수들을
Python 기반 **symbolic derivation + independent numerical verification** 으로 재검산한 결과를 기록한다.

여기서의 원칙은 다음과 같다.

1. symbolic derivation은 **SymPy** 를 사용한다.
2. numerical verification은 **mpmath/numpy-style direct evaluation** 을 사용한다.
3. 두 코드는 서로 다른 계산 경로를 사용한다.
4. cross-check script는 symbolic 결과와 numerical 결과를 함께 읽고 pass/fail을 판정한다.
5. Type VIII open case도 포함한다.

---

## 1. verification bundle contents

`verification/` 아래에는 다음 파일이 들어 있다.

- `resolved_lookup_manifest.py`
- `symbolic_verify.py`
- `numeric_verify.py`
- `crosscheck.py`
- `run_all_verifications.py`
- `symbolic_results.json`
- `numeric_results.json`
- `crosscheck_results.json`
- `run_all_stdout.json`

---

## 2. what is proven symbolically

### 2.1 class-B parameter bridges

SymPy가 아래 식을 자동으로 단순화하여 0으로 만든다.

- VI\(_h\):
  \[
  h=-\left(\frac{1-q}{1+q}\right)^2,
  \qquad
  q=\frac{1-\sqrt{-h}}{1+\sqrt{-h}}
  \]
- VII\(_h\):
  \[
  h=p^2
  \]

또한 branch limit도 자동으로 도출된다.

- Type III special branch:
  \[
  q=0 \Rightarrow h=-1
  \]
- Type VI\(_0\) limit:
  \[
  q=1 \Rightarrow h=0
  \]

### 2.2 Type VIII continuous/discrete-series checks

SymPy는 Type VIII continuous measure
\[
\rho^{\rm cont}_{VIII}(\mu,s)
=
\frac{1}{(2\pi)^2}
\frac{s\sinh(2\pi s)}{\cosh(2\pi s)+\cos(2\pi\mu)}
\]
에 대해

- \(\mu=0\) reduction
  \[
  \rho^{\rm cont}_{VIII}(0,s)
  =
  \frac{1}{(2\pi)^2}s\tanh(\pi s)
  \]
- \(\mu=1/2\) reduction
  \[
  \rho^{\rm cont}_{VIII}\!\left(\frac12,s\right)
  =
  \frac{1}{(2\pi)^2}s\coth(\pi s)
  \]
- \(\mu\to-\mu\) evenness
  \[
  \rho^{\rm cont}_{VIII}(-\mu,s)=\rho^{\rm cont}_{VIII}(\mu,s)
  \]

를 모두 0-identities로 검산한다.

### 2.3 HEALPix packed-index formula

SymPy는 m-major packed order
\[
\mathrm{idx}(\ell,m;\ell_{\max})
=
\frac{m(2\ell_{\max}+1-m)}{2}+\ell
\]
가 block-offset derivation과 정확히 일치함을 보이고,
전체 coefficient 수가
\[
\frac{(\ell_{\max}+1)(\ell_{\max}+2)}{2}
\]
임도 자동으로 확인한다.

### 2.4 4th-order finite-difference stencil derivation

SymPy가 moment-matching linear system을 풀어 다음 stencil을 자동 유도한다.

1차 도함수:
\[
f'_i=\frac{f_{i-2}-8f_{i-1}+8f_{i+1}-f_{i+2}}{12h}
\]

2차 도함수:
\[
f''_i=\frac{-f_{i-2}+16f_{i-1}-30f_i+16f_{i+1}-f_{i+2}}{12h^2}
\]

### 2.5 VI\(_h\) negative-q density positivity rewrite

SymPy는
\[
\cos^2 k-q\sin^2 k
\]
를 \(q=-u\), \(u>0\) 에 대해
\[
u\sin^2 k + \cos^2 k
\]
로 rewrite하여 positivity check에 쓸 수 있게 만든다.

---

## 3. independent numerical verification

independent numerical code는 SymPy를 쓰지 않고 직접 수치 평가한다.

### 3.1 class-B map roundtrip
max abs error:
- `1.421e-14`

### 3.2 Type VIII special-case reduction
max abs error:
- `1.354e-73`

또한 sampled domain에서 continuous measure minimum value:
- `2.195e-13`

즉 sampled domain에서 nonnegative다.

### 3.3 finite-difference exactness
random polynomial tests에서 max abs error:
- `6.964e-75`

### 3.4 positivity checks
numerical script는 다음도 함께 검사한다.

- Type IV: \(1+k_1\ge0\) for \(k_1\ge0\)
- Type VI\(_h\), \(q<0\): \(\cos^2k-q\sin^2k>0\)
- Type VII\(_h\): \(|k|\ge0\)

---

## 4. symbolic ↔ numerical cross-check verdict

crosscheck result:
```json
{
  "symbolic_zero_checks": {
    "VI_h_compose_q_to_h": true,
    "VI_h_compose_h_to_q": true,
    "VII_h_identity": true,
    "typeVIII_even_reduction": true,
    "typeVIII_odd_reduction": true,
    "typeVIII_mu_evenness": true,
    "healpix_offset_identity": true,
    "healpix_triangle_count": true
  },
  "numeric_bounds": {
    "classB_max_abs_err": 1.4210854715202004e-14,
    "typeVIII_specialcase_max_abs_err": 1.3535210224463053e-73,
    "fd_max_abs_err": 6.964452166884196e-75,
    "typeVIII_min_val": 2.194695200206879e-13
  },
  "crosscheck_pass": true
}
```

판정:
- symbolic zero-checks: **all pass**
- numerical bounds: **all within tolerance**
- final cross-check: **pass = True**

---

## 5. documentary consequence for the design pack

이 결과는 다음을 뜻한다.

1. formerly unresolved placeholder 대상이었던 class-B bridge, intrinsic-family backend constants, Type VIII measure, collocation defaults, HYREC-like adapter contract, HEALPix packing rule은 이제 **frozen formula set** 으로 간주한다.
2. implementation agent는 더 이상 이 항목들을 추측으로 채우면 안 된다.
3. 새로운 unresolved item이 생기면, 먼저 같은 형식의 frozen addendum과 symbolic/numerical verification bundle을 추가해야 한다.

---

## 6. one-line summary

이 문서는  
**frozen backend constants가 문헌 의존 진술에 머물지 않고, symbolic derivation과 independent numerical verification을 모두 통과했다는 것을 기록하는 verification authority note** 다.
