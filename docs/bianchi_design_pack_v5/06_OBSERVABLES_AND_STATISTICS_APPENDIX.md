# 06. Observables and Statistics Appendix
## output-only layer / harmonic-first comparison / hard gate before fitting

---

## 0. purpose

이 문서는 solver 본체와 분리된 output/statistics 계층을 다룬다.
이 문서의 존재는 observables-ready 또는 statistics-ready의 증거가 아니다.
오직 gate가 열렸을 때만 출력/비교/통계 계층이 열릴 수 있다.

---

## 1. what belongs here

- primary outputs
- deterministic/stochastic/boost split
- output-only local boost rule
- harmonic-first comparison hierarchy
- archive metadata
- fitting hard stop

Main SSOT가 이미 formalism과 forward model을 담고 있으므로,
이 appendix는 **output-side semantics** 만 다룬다.

---

## 2. mandatory outputs

### harmonic-domain minimum
\[
a_{\ell m}^{T},\qquad a_{\ell m}^{E},\qquad a_{\ell m}^{B}
\]

### optional map-domain once map gate opens
\[
T(\hat n),\qquad Q(\hat n),\qquad U(\hat n)
\]

For low-\(\ell\) Bianchi work, harmonic coefficient output is the primary required layer because deterministic anisotropy can invalidate \(C_\ell\)-only summaries.

---

## 3. mandatory output split

Stored outputs must be separated as

\[
a_{\ell m}
=
a_{\ell m}^{\rm det}
+
a_{\ell m}^{\rm stoch}
+
a_{\ell m}^{\rm boost}.
\]

### design meaning
- `det`: deterministic forward-model anisotropy from the Bianchi background + chosen perturbative response
- `stoch`: stochastic perturbation component
- `boost`: local observer-boost contribution applied only at output stage

This split is mandatory even if one component is zero.

---

## 4. global tilt vs local boost at output

Global tilt belongs to the forward model and is therefore already encoded upstream of the output layer.  
Local observer boost is an output-only transformation.

Therefore:
- global tilt changes the solved model,
- local boost changes only the rendered output.

The output archive must never merge these into one unlabeled object.

---

## 5. comparison hierarchy

### Stage 0
deterministic sanity and known-limit output checks

### Stage 1
harmonic coefficient comparison at \(a_{\ell m}\) level

### Stage 2
map-domain comparison

### Stage 3
covariance-aware likelihood or fitting workflow

A lower stage must be open before a higher stage may be used.

---

## 6. fitting hard stop

No fitting, posterior, evidence, or model comparison is allowed unless all of the following are open:

- exact collision gate
- local boost/global tilt separation gate
- family-specific backend gate for the claimed family branch
- background residual gate
- IC provenance gate
- production cutoff gate
- output split gate

---

## 7. what does not belong in the main SSOT

The following stay here, not in the main SSOT:
- output archive object names
- harmonic ordering metadata
- map archive schema
- comparison-stage metadata
- fitting hard-stop semantics

---

## 8. what this appendix does not claim

This appendix does not claim:
- that outputs are already numerically implemented,
- that statistics fitting is open,
- that \(C_\ell\)-only comparisons are sufficient,
- that local boost may be used to explain global tilt physics.

---

## 9. one-line summary

이 appendix의 목적은  
**solver 본체와 output/statistics를 분리한 채, gate가 열렸을 때 어떤 출력을 어떤 계층으로 비교/저장할지 고정하는 것** 이다.
