# Independent SageMath/Singular axis: proof scope

Contract: R8-ORBIT-RANK-JOINT-JET-V1, SHA-256 5ff7f84db01b6871f74f7c60b5c36430a4cae93735466e277bd9c4019ab22723.

## O1: generic weighted combination, fixed scaling fixtures

For each common R, let a and b be the nonnegative quadrupole and octopole residual norms. The contract admits the component spectral inequalities a>=bQ and b>=bO as named Hoffman-Wielandt/Mirsky lemmas. Set eQ=a-bQ>=0 and eO=b-bO>=0. Multiplication of the desired squared inequality by positive q0^2 o0^2 gives exactly

    o0^2 eQ(2 bQ+eQ) + q0^2 eO(2 bO+eO) >= 0.

The script verifies this polynomial identity and its nonnegative coefficients. The right invariant lower bound is independent of R. Taking monotone square roots and then the infimum over common R proves O1; simultaneous attainability of separate blocks is never assumed. Compactness of SO(3) and continuity give the stated minimum if required.

For Q=diag(-1,0,1), Q'=2Q, the squared eigenvalue gap and the R=I residual both equal 2. For the full symmetric rank-three octopole, the script constructs all 27 coordinates, verifies STF traces, obtains S=diag(6,2,2) and norm squared 10. Scaling by 2 makes the squared singular-value gap and the R=I residual both equal 10. Those matching lower/feasible upper values prove the two fixed minima. Zero and repeated spectra are retained. The relative-alignment example is a fixed counterexample: the Q stabilizer consists of diagonal sign matrices, hence fixes diagonal S, while the rational rotated S has a nonzero off-diagonal entry. No common zero residual exists; compactness gives strictly positive joint distance despite vanishing spectral bounds.

## O2: generic rational/polynomial identities and the chart bound

For arbitrary real nonzero quaternion u=(w,x,y,z), define n=u.u>0 and the homogeneous quadratic matrix H written in verify.py. Both Sage and a separate Singular process verify H^T H=n^2 I and det(H)=n^3 exactly. Thus H/n is a proper rotation for every such u.

For chart a=0, u=(1,x) and s=1+x.x, quotient differentiation gives

    J = [E-u x^T/s]/sqrt(s),
    J^T J = I/s - xx^T/s^2.

The latter is checked as a rational-function identity. For arbitrary real direction v, the exact positive slack is

    ||v||^2/s - ||Jv||^2 = (x.v)^2/s^2 >= 0.

Hence ||J||op<=1/sqrt(s). On a rectangular cell C, s>=1+sum dist(0,Cj)^2=mC^2. The center-to-point line lies in C, has length at most ||h||, and its spherical image length is at most ||h||/mC. The admitted quaternion double-cover angular lemma supplies the angle bound min(pi,2||h||/mC). Permuting the four coordinates covers all charts. Every unit quaternion has a maximal absolute component; change global sign so it is positive and divide other components by it, giving chart coordinates in [-1,1]. Ties cause overlaps, not omissions. For grid spacing 1/m, half widths are 1/(2m), mC>=1, and radius<=sqrt(3)/m<7/(4m), the last comparison verified by 49/16-3=1/16>0. Positive integer m is the implied grid domain. No floating enclosure implementation or cell optimizer is certified.

## O3: generic inclusive comparison and finite-rank argument

Given Li<=si<=Ui and L0<=s0<=U0:

* Li>=U0 implies si-s0=(si-Li)+(Li-U0)+(U0-s0)>=0.
* si>=s0 implies Ui-L0=(Ui-si)+(si-s0)+(s0-L0)>=0.

Each sum is a polynomial with nonnegative coefficients in three nonnegative slack variables, checked exactly. These implications compare the binary indicators pointwise, including equality; summing and dividing by positive M proves pminus<=p<=pplus. The kth-order-score enclosure follows coordinatewise monotonicity: raising any coordinate cannot lower its kth order statistic. More explicitly, if lower kth exceeded exact kth, the k entries at most the exact kth would also have lower coordinates at most it, a contradiction; apply the same argument to upper coordinates.

For inclusive rank calibration, fix any multiset of M scores and integer t. Let A be the entries whose inclusive descending rank is <=t. If A is nonempty, take an entry with minimal score in A. Every entry in A is at least that score, so this entry's inclusive rank is at least |A|; thus |A|<=t. Exchangeable fixed permutation-equivariant scores make the distinguished row uniform under label permutation, proving P(p<=alpha)<=floor(M alpha)/M<=alpha. Since pplus>=p pathwise, rejection based on pplus is contained in exact rejection even at an observation-directed numerical stopping time for this fixed statistic. These are explicit combinatorial arguments; enumeration of 3^5 tuples is only additional finite corroboration.

Integer threshold checks establish M=1000 k=32, possible count<=49 for rejection and certain count>=50 for nonrejection; M=301 k=18 gives 14 and 15. The exact scalar fixture and inclusive-tie counterexample are separate fixed checks. No actual observational sampling-law or exchangeability admission is made.

## J2: fixed rational support and Gaussian-marginal counterexample

The support obligation is explicitly the registered rational fixture B=(3,4)^T/5, V=4. Exact arithmetic establishes rank(B)=rank(C)=1, B^T B=1, C=4BB^T, Cplus=B B^T/4 and all four Penrose equations. For r=2B, z=Bplus r=2 and reduced/original quadratics both equal 1. For n=(-4,3)^T/5, B^T n=0 and ||n||=1. Thus roff=r+n is off support although projection gives the same quadratic. This is an exact fixture, not a generic floating-rank guarantee.

Construct Z~N(0,1) and an independent equal-probability sign S, then X=Z,Y=SZ. This construction is valid for all real arguments t,u. The joint MGF is [exp((t+u)^2/2)+exp((t-u)^2/2)]/2. Exact symbolic substitutions show standard-normal marginal MGFs; exact differentiation shows E[XY]=0 and E[X^2Y^2]=3. A joint Gaussian with this covariance I would have product MGF and mixed fourth moment 1. Hence the joint is not Gaussian despite Gaussian marginals and known covariance. This uses the standard normal MGF and uniqueness/differentiation facts, not a Monte Carlo fixture or an assumed conclusion.

## Execution and limitation record

SageMath 10.9 and Singular 4.3.2 match the contract. The first script attempt failed on an unsorted Sage eigenvalue list; its source/transcript are retained. Sorting before comparison corrected a verifier ordering error without changing the mathematical target, fixtures, tolerances or assumptions. The second execution passes 27 checks. No sibling results, production implementation or old R7 evidence were read. This author shares the broad Codex/LLM environment with the team, so engine independence should not be described as independent human authorship. Native profile replacement is dispatch plumbing only. The stale hook run/HEAD refers to another checkout; the registered R8 assignment and actual worktree context index agree and no shared pointer was changed.
