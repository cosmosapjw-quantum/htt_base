# Wolfram Engine + xAct axis: exact CAS-01 component proof

The mathematical inputs are the frozen EXECUTION_CONTRACT.json and
cas/COMMON_SPEC.md. The independent source is axis.wl. run.py records full
Wolfram stdout/stderr, argv, cwd, exit, versions, source/input hashes, and
component results in AXIS_RESULT.json. The failed first execution transcript
is retained: a malformed local S matrix and an ambiguous Wolfram $Version
symbol were implementation errors corrected before the successful execution.
No sibling derivation or result was read.

The signature is (-,+,+,+). All Q and B indices are covariant; u is a future
unit vector, U=c u with c>0, and Q_ab is derivative first. Set
b_a=B_ab u^b. The xAct rule b_a u^a=0 follows from B(u,u)=0 and introduces
no new physical condition. W is antisymmetric and spatial.

For C01, xAct reduces u^a u^b [S_ab+S(u,u)g_ab] to
S(u,u)(1-1)=0. Under S ↦ S+αg, S(u,u) changes by -α, so B is unchanged.
For an arbitrary symmetric T, put
P(n)=T_00-2T_0i n_i+T_ij n_i n_j. If P vanishes for every unit n, it
vanishes at ±e_i; these six evaluations force T_0i=0 and T_ii=-T_00.
The three directions (e_i+e_j)/√2 force T_ij=0 for i<j. Wolfram solves
these nine exact linear equations and obtains T=-T_00 g. It independently
substitutes that solution into P and reduces the residual to zero under
n·n=1. Universal vanishing implies the nine sampled equations, so this is
a proof of the full null-cone kernel, not an inference from a numerical grid.

For C02, xAct expands Q_ab=B_ab+b_a u_b-u_a b_b+W_ab. The last three
terms are skew, hence sym(Q)=B. Contracting the second slot with u gives
Q_ab u^b=b_a-b_a=0; contracting the first gives u^a Q_ab=2b_b and
A_b=2c b_b. If B denotes sym(∇u) instead of sym(∇U), then
A_b=2c² B_ab u^a. The xAct spatial projection uses the mixed projectors
with their proper index variance:
D_ab=h^c{}_a h^d{}_b B_cd=B_ab+u_a b_b+u_b b_a.
Its trace is θ=h^ab B_ab=g^ab B_ab because B(u,u)=0, and
σ_ab=D_ab-θ h_ab/3 is spatial and tracefree. Both xAct residuals are zero.
An independent observer-frame matrix has arbitrary spatial symmetric,
mixed, and skew components. It verifies these identities and the convention
W_ij=ε_ijk ω_k, which implies W x=-ω×x.

For C03, take u=(1,0,0,0), K=(-1,n), n·n=1. Since B_00=0 and
A_i=2c B_0i,
B(K,K)=B_ij n_i n_j-2B_0i n_i
       =θ/3+σ_ij n_i n_j-A_i n_i/c.
For generic S with S_00=h0, S_0i=-h1_i/2, and symmetric tracefree
S_ij=h2_ij, direct multiplication yields
S(K,K)=h0+h1·n+h2:nn. Wolfram checks both polynomial residuals and
B(K,K)-S(K,K)=0 on the null cone.

For C04, define v^b=u^b+c^(-1)g^(bd)Q_ad x^a and N=√[-g(v,v)].
The positive root gives N(0)=1 and (v/N)(0)=u. Its derivative is
∂_a N|0=-c^(-1)u^d Q_ad=0 by Q u=0. The quotient rule then yields
∂_a(v^b/N)|0=c^(-1)g^(bd)Q_ad. xAct checks the arbitrary-unit
contraction and normalization correction; Mathematica independently
differentiates the four-component expression and gets the full target
matrix. The identity is tensorial, so the rest-frame calculation and
abstract contraction cover every future unit u. This is a local jet
result, with no source-reaching flow inferred from it.

The executed Wolfram run passed contracted finite/local components
C01–C04. Jacobi vertex Taylor and screen-invariance ODE arguments remain
OPEN. Smooth source extension/local-flow construction remains OPEN.
Scientific admission is NOT_EVALUATED.
