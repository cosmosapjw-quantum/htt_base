# Measurement error, moving selection and robust physical-response contrasts

Exploratory analytic result; owner dossier_theory_r2; physical input pending; HOLD unchanged.

## 1. Fixed-label observation law

Use a common physical observer/frame and fixed ray or population labels x on a finite measure space. Let Aθ(x)≥0 be the source weight. In the dossier affine observation this is `(-N_s·l)D_A²` times any angular/population measure; an event catalogue also needs its proper-rate clock. A is not an empirically known CF4 completeness function.

Let tθ(x) be the true measured coordinate, rθ(y|x) a normalized observation-error density, and Sθ(y)∈[0,1] the acceptance in measured coordinates. Define

Kθ(x)=∫Sθ(y)rθ(y|x)dy,
Zθ=∫Aθ Kθ dx,
Nθ=∫Aθ(x)∫Sθ(y)rθ(y|x)gθ(y,x)dy dx,
μθ=Nθ/Zθ.

For a latent-coordinate statistic hθ(x), set gθ(y,x)=hθ(x), so Nθ=∫AθKθhθ dx. All subsequent h formulas use this specialization. For an observed statistic dependent on y, use the full N expression: replacing its joint kernel by h(x)K(x) would discard measurement-error correlations.

Assume integrable dominating functions for all differentiated products, fixed labels/endpoints, Zθ>0, and a differentiable declared parameter family. Differentiating the full expression is constructive and does not need an ODE solver or an inverse redshift slope. Moving physical endpoints add the ordinary endpoint terms of dossier `vii:finite_bin_tangent`; they must not also be placed in A a second time.

## 2. Selected mean and the missing normalizer response

For the latent-coordinate statistic,

μθ' = Zθ⁻¹∫[AθKθ hθ' + (hθ−μθ)(Aθ'Kθ+AθKθ')]dx. (1)

Proof: N'=∫(A'Kh+AK'h+AKh'), Z'=∫(A'K+AK'), and μ'=(N'−μZ')/Z. A detector response evaluated after parameter changes must contribute K'; a selected law also contributes −μ Z'/Z. Either omitted term can rotate or scale an inferred response column.

Where A,K>0, (1) is E_S[h']+Cov_S(h, ∂θ log A+∂θ log K). The integral version is primary because a score may be singular at zero acceptance. The dossier bound on an unnormalized count does not by itself control μ: selection probability must stay bounded away from zero.

For fixed Z lower bound z*>0 and |h|≤H, a direct response bound is

|μ'| ≤ E_S[|h'|] + (2H/z*)[||A'||₁ + ||A||₁||K'||∞]. (2)

It follows from K≤1 and |h−μ|≤2H. This is a bound conditional on actual A', h', error/selection derivative and selected mass. It supplies no physical response from unknown inputs.

## 3. A sharp measured bin becomes a smooth finite response

Let Y=t+σ ε with ε standard normal, σ>0, and acceptance l≤Y≤u. Then

K(t;l,u,σ)=Φ((u−t)/σ)−Φ((l−t)/σ),
∂t K=[φ((l−t)/σ)−φ((u−t)/σ)]/σ,
∂t² K=[(l−t)φ((l−t)/σ)−(u−t)φ((u−t)/σ)]/σ³.

The useful uniform bounds are

|∂t K|≤1/(σ√(2π)),
|∂t² K|≤2/(σ²√(2πe)). (3)

The first uses that two nonnegative pdf values lie between 0 and 1/√(2π); the second uses sup |vφ(v)|=1/√(2πe). Thus finite coordinate changes Δt have |ΔK|≤min(1,|Δt|/(σ√(2π))), and the acceptance linearization remainder is ≤Δt²/(σ²√(2πe)). The latter is uniform only over fixed positive σ or a domain σ≥σ*>0. If a non-Gaussian observation kernel is supplied, use its actual convolved response derivative instead of assuming Gaussian tails.

Moving numerical edges and variable error widths give U=(u−t)/σ, L=(l−t)/σ and

K'=φ(U)[(u'−t')/σ−Uσ'/σ]−φ(L)[(l'−t')/σ−Lσ'/σ]. (4)

This makes an observer-frame selection change explicit. For fixed endpoints, inserting K(z) in the dossier affine law yields ∫[A'K+AK_z z']dλ. No 1/(dz/dλ) occurs; folds are harmless under the majorant assumptions. A Gaussian measurement convolution has noncompact tails rather than the dossier's finite-support W, so integrability must be checked on the finite physical label domain (or separately in tails). Smooth measurement uncertainty is not evidence that empirical completeness is known.

## 4. Finite selected-observable discrepancy

Compare models 0 and 1 on the same labels. Suppose ||A1−A0||₁≤eA, ||A0||₁≤M, ||K1−K0||∞≤eK, and Z0,Z1≥z*>0. Their accepted-weight L1 difference is

B=||A1K1−A0K0||₁≤eA+M eK. (5)

Indeed split `(A1−A0)K1+A0(K1−K0)`. For h0 in [a,b] and sup |h1−h0|≤eh,

|μ1−μ0|≤eh+(b−a)B/z*. (6)

Proof: write μ1−μ0=Z1⁻¹∫A1K1(h1−h0)+Z1⁻¹∫(h0−μ0)(A1K1−A0K0). Since μ0∈[a,b], |h0−μ0|≤b−a. If only vector norm ||h||≤H is known, replace the range b−a by 2H.

It is enough to know Z0 and B<Z0; then Z1≥Z0−B and z*=Z0−B is constructive. If B≥Z0, this theorem cannot certify a ratio error, even when its unnormalized count bound is finite. This is a local failure to bound normalization, not a cosmological no-go.

For fixed sharp acceptance without measurement smoothing, the dossier swept-boundary estimate gives eK weighted by actual boundary-strip mass, not by an indicator Lipschitz constant. In (5), replace M eK with ∫A0|K1−K0|; if only accepted labels in a swept strip can change, this is at most the actual A0-measure of that strip. A finite empirical catalogue gives an exact retained-weight strip count; it does not estimate omitted population mass.

## 5. Shared calibration must be normalized at the catalogue level

Let η be a shared calibration variable with preselection prior p(η), and, conditional on η, let independent slots have unnormalized observed densities fi(di|η,θ) and probabilities Zi(η,θ)=∫selected fi(di|η,θ)ddi. Conditional on all slots selected, the likelihood is

Lpre(d|θ)= [∫p(η)∏i fi(di|η,θ)dη] / [∫p(η)∏i Zi(η,θ)dη]. (7)

Its selected η prior is proportional to p(η)∏Zi(η,θ). A different generative experiment draws η from a declared prior AFTER slot selection; that law is

Lslot(d|θ)=∫p_slot(η)∏i[fi(di|η,θ)/Zi(η,θ)]dη. (8)

The laws agree if p_slot is precisely the θ-dependent selected prior implied by (7). Reusing the same numerical p in both formulas generally changes the law. Neither formula can replace a physical shared calibration/selection law missing from E2.

Derivative of the first law is

∂θ log Lpre = E_{η|d,θ}[∑∂θ log fi] − E_{η|all selected,θ}[∑∂θ log Zi], (9)

provided p is θ independent; if not, add its score to both expectations. This is a finite quadrature calculation over existing conditional models. Catalogue count modeling, object-overlap dependence and unknown population selection require additional terms; independent-slot formulas do not cover them.

## 6. Robust rank through a fixed nuisance contrast

Suppose a declared linearized observable has mean Rθ+Lγ and nominal SPD covariance C0. Physical units must be fixed: choose a nonsingular parameter scale D and use θ=Dα. Let U have orthonormal columns spanning the orthogonal complement of col(C0^(-1/2)L), and set T=UᵀC0^(-1/2). Then TL=0 and TC0Tᵀ=I. All matrices are finite, and no changing pseudoinverse is differentiated.

For nominal M0=TR0D and actual response R=R0+E, assume ||TED||op≤εR. Let actual covariance obey `(1−δ)C0 ≼ C ≼ (1+δ)C0`, 0≤δ<1. Define σmin(M)=inf_{||v||=1}||Mv|| over parameter vectors; it is zero automatically if the number of contrast rows is less than the parameter dimension. Then

σmin(TRD)≥max(0,σmin(M0)−εR),
λmin[(TRD)ᵀ(TCTᵀ)^(-1)(TRD)]≥[max(0,σmin(M0)−εR)]²/(1+δ). (10)

Proof: for each unit v, ||(M0+TED)v||≥||M0v||−εR. Loewner ordering gives TCTᵀ≼(1+δ)I and inverse ordering gives its inverse ≽I/(1+δ). Multiply and take the Rayleigh infimum. If contrast-column error budgets ej are supplied, εR≤sqrt(∑ej²) by Frobenius norm is a conservative executable conversion. The criterion σmin(M0)>εR is a sufficient robust local-response separation condition for this fixed design.

When the response uncertainty set is the complete unstructured operator ball ||ΔM||≤εR, the worst possible σmin is exactly max(0,σmin(M0)−εR): subtract up to εR along a minimizing singular pair. Physical response families may be much more restricted, so failure of (10) does not prove their nonidentifiability.

If actual nuisance is L+ΔL, TL=0 leaves leakage TΔLγ. A finite bias certificate needs a bound on ||γ|| and ||TΔL|| or an expanded nuisance space. An unbounded unknown nuisance cannot be quietly included in εR. Finite parameter remainders also need the physical Hessian budget from dossier `v:observable_hessian`; rank of an endpoint proxy alone cannot certify global tilt/history separation.

## Scope and next physical data

Equations (1)–(10) close an analytic selection-normalization/error-transport subproblem. Implementation should consume A/A', actual observation-error and selection kernels, common nuisance laws, selected mass margins, R0 and quantified E, covariance envelopes, parameter units/scales and frame/processing identities. Missing quantities remain UNKNOWN. No native transfer, global-tilt column, physical MES denominator/ceiling, Jacobi remainder, actual survey completeness or Bianchi family inference is produced.

## Physics/math audit verdict

Applied materialized project skills `htt-physics-math-audit`, `htt-scientific-code-validation`, `htt-claim-firewall`, and `htt-statistical-hardening`. The current native runtime paragraphs override the skills' historical CUH telemetry command; no historical service was reconstructed. Evidence is the dossier/current handoff and existing CF4 summaries identified in Dossier_MAP. Proposed use is an analytic response/normalizer/error consumer, not a production admission. Parent remains the sole production writer and must obtain separate independent review.

| Item | Status | Scope / kill switch |
|---|---|---|
| Current/clock/frame conventions | Conditional | Signature −+++ and length-valued affine λ; detector-frame changes and physical tilt must remain distinct. A mismatch invalidates physical use. |
| Gaussian signs and normalization | Checked | Wolfram residuals zero; selected-mean finite-difference error 4.24e−14. Gaussian noise is a declared kernel, not an empirical finding. |
| Dimensional check | Pass within declaration | K dimensionless; K_t has inverse-coordinate units; K_tt inverse-coordinate squared; μ has h units; parameter scale D fixes response units. |
| No-tilt/no-variation limit | Analytic | A'=K'=h'=0 gives μ'=0. A passive matched-frame change leaves counts invariant only with the dossier detector matching. |
| Zero selected mass | Explicit failure | Z=0 undefined; B≥Z0 does not certify finite ratio error. |
| Sharp zero-noise limit | Explicit failure | σ→0 removes uniform derivative control; replace it with an actual boundary-strip law or smooth detector. |
| Redshift folds | Conditional regularity | Affine-label formula has no inverse redshift slope; requires integrable majorants and valid image branches. |
| Rank-deficient response | Conditional | σmin definition uses parameter dimension; q<p has σmin=0. Failure of lower bound is not physical/global no-go. |
| Unknown nuisance/physical response | Open blocker | No bounds or zero filling are inferred. A nuisance-space error with unbounded γ defeats finite bias certification. |
| Summary experiments | Conditional diagnostic | Existing scenario arithmetic only; no raw-data refit. Both failed quadrature scenarios retained in result output. |

Tests/artifacts used: Wolfram first/second derivative identities and corrected selected-mean finite difference; `summary_experiments.py` run under `/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python`, Python 3.12.14, cwd `/workspace/scratch/ef61c9590364`, exit 0. The standalone script only reads source summaries and prints JSON. No production package/module code or unrelated ledger changed. Safe claim: analytic finite-response and normalizer transport conditional on supplied physical/error/population inputs. Fatal full-admission blockers remain the missing E1/E2 physical and empirical laws. Claim-tier recommendation: EXPLORATORY_ANALYTIC / CONDITIONAL_DIAGNOSTIC; HOLD unchanged.
