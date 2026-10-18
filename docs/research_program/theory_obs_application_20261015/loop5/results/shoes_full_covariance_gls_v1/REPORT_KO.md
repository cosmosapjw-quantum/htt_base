# SH0ES 2022 3492×47 joint linear source matrix: 실제 Cholesky GLS

이 계산은 **발표된 동일 SH0ES input의 고정된 원자료 선형 모델**에 대한 numerical fit다.
그룹 CF4와 합친 새로운 H0 또는 추가 독립 거리사다리 관측이 아니다.

Cholesky GLS chi2=3552.75933 for dof=3445
Normal equation relative gradient=1.75202e-16
Normal Fisher condition=2.6271e+07
Official distributed lstsq_results center χ²=3559.579, difference=6.8196431
Largest absolute coefficient discrepancy=0.04961771

**Scientific blocker:** Published reference centres/sigmas in lstsq_results.txt are not byte-identical to simple unregularized Cholesky GLS of current C,L,y. Distinguish actual center file as approximate broad MCMC prior configuration and check upstream algorithm before claiming publication reproduction.

An additive template contained in the 47-dimensional A image has zero profiled Fisher information by construction. The all-rows constant template has its own algebraic information fraction, NOT a physical CF4 common-zero-point prior.
A physical CF4 bridge needs explicit source-matched host/event loading and joint covariance before any cross-catalogue prior transfer.
