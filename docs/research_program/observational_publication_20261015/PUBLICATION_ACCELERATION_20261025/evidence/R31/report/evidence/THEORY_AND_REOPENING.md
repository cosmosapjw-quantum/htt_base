# Conditional full-matrix theorem and exact reopening payload

Status: DERIVED CONDITIONALLY, NOT_INDEPENDENTLY_REVIEWED, NOT_NUMERICALLY_EXECUTED. This is a source/theory note, not a dispatch packet. Owner obsstat; C0, non-claim-bearing; no Bianchi transfer. All vectors below retain signed E/B, ell2/3 and cross-coordinate structure.

## Spectral model with units

Let B_nu(T)=2h nu^3/[c^2(exp(h nu/(k_B T))-1)] and b_nu=partial_T B_nu(T_CMB). A source-qualified bandpass response for component k is

    R[i,k] = integral tau[i,k](nu) S_k(nu) dnu
             / integral tau[i,CMB](nu) b_nu dnu .

Frequency is in Hz. Convert HFI cm^-1 to Hz by nu=100 c wavenumber; LFI GHz to Hz by nu=10^9 frequency. Bandpass normalization cancels only when numerator and denominator use the appropriate consistently normalized responses. Polarization gain/efficiency/angle corrections are additional response terms, not inferred from a temperature calibration denominator.

One explicit normalization uses amplitude in K_CMB at a reference frequency. Then

    S_CMB(nu) = b_nu,
    S_sync(nu; beta_s) = b_nus (nu/nus)^(beta_s+2),
    S_dust(nu; beta_d,Td) = b_nud (nu/nud)^beta_d B_nu(Td)/B_nud(Td).

Here beta_s is the Rayleigh-Jeans temperature spectral index; its intensity exponent is beta_s+2. S_k has specific-intensity-per-kelvin units, and R is dimensionless. Under exact common CMB calibration R[i,CMB]=1; unknown gain or polarization efficiency cannot be erased by asserting that equality for the actual map.

At frozen pivots define t=(Td-T0)/T0. The first-order foreground basis is sync, partial_beta_s sync, dust, partial_beta_d dust, partial_t dust. The complete second-order extension adds partial_beta_s^2 sync, partial_beta_d^2 dust, partial_beta_d partial_t dust, partial_t^2 dust. Absorb Taylor factorials into amplitude fields. All amplitudes then have the same K_CMB reference-unit convention. A real line-of-sight/beam/pixel average generally supplies a remainder beyond a finite list. This is the physical moment-expansion construction, without claiming its truncation is exact for these data. [Remazeilles et al. 2021, sections3.1–3.2](https://arxiv.org/html/2006.08628v2)

If every component experiences one common angular operator O, and band responses are spatially constant, then for the complete d=24 coefficient vector

    Y = a s^T + F U,       Y in R^(7 x 24).

The common-operator hypothesis is substantive. In the ideal noiseless model, a scalar spectral weight preserving CMB and annihilating foregrounds exists exactly when a is not in col(F). With P_F=I-F F^+, one choice is w=P_F a/(a^T P_F a). Then w^T a=1 and w^T F=0, and w^T Y=s^T. This algebra uses a declared Euclidean metric, not an estimated covariance. Five first-order foreground columns leave potential spectral room; nine second-order columns may span all seven channels, but the actual rank and whether a lies in their span must be evaluated, never presumed from column count.

## Full response, quotient and partial identification

The source-faithful finite model is more general:

    y = A s + B u + e,

where y is the stacked168 signed observed coordinates, s contains24 target coordinates, u contains all admitted foreground and other nuisance coordinates, and e belongs to a declared joint residual set E. A and B include the instrumental, angular and pixel response. Their domain and source are part of the assertion. An arbitrary nuisance complement is allowed mathematically; it is not silently set to zero scientifically.

Let P=I-B B^+ and M=P A. With e=0, the identified target is the equivalence class s+ker(M). Its dimension is rank(M). A linear functional Ls is identifiable exactly when ker(M) is contained in ker(L).

Proof: two latent pairs produce the same y precisely when A delta_s is in col(B), equivalently P A delta_s=0. L has one value on every such equivalence class exactly when it kills that kernel. If rank(M)=24, H=M^+ P obeys H A=I24 and H B=0, so H y=s. If rank is smaller, a basis of ker(M) is the full signed lost-tensor witness; no missing component is zero-filled.

For a residual set E, the **exact** identified set is

    S(y) = {s : P(y-A s) belongs to P E}.

This follows because P z=0 iff z belongs to col(B), so the remaining discrepancy can be represented by B u. If rank(M)=24, H y-s=H e. For ||P e||_2<=epsilon, ||H y-s||_2<=epsilon/sigma_min(M). For any compact joint set E and direction v, support functions of H E give valid outer directional intervals; their sharpness conditional on the fixed y requires the residual feasibility constraint as well. These are deterministic bounds, not confidence statements.

If E is unrestricted in R168, every s is feasible. A common blackbody-spectrum contaminant with response A is exactly confounded with s and remains so after a foreground quotient. If a joint covariance is later qualified, propagation must use the complete H Sigma H^T, including all channel and E/B/ell cross terms. The observed outer products from R27 do not supply Sigma.

For response uncertainty, do not use nominal rank as uniform identification. The correct set is the union of S(y;A,B,E) over the admitted response family. A uniformly valid quotient must satisfy H A=I and H B=0 for every member, or retain the operator mismatch explicitly in E with an amplitude/domain bound. A singular-value threshold chosen after seeing the matrix cannot supply such a bound.

## Why low-mode beam division is not a matching operator

Even in an idealized circular-beam harmonic model, a retained masked mode has the form

    y[i,alpha] = sum_beta K[alpha,beta] b[i,beta] z[beta].

K includes mask and spin E/B coupling; beta ranges beyond ell2/3. Replacing y[i,alpha] by y[i,alpha]/b[i,alpha] leaves factors b[i,beta]/b[i,alpha] on every coupled beta. It equals a desired common response only if those factors agree on the entire coupled domain. The saved24 entries do not contain the discarded beta amplitudes.

Exact two-mode illustration: write one observed scalar as y=k1 b1 z1+k2 b2 z2 and a desired matched scalar as t=k1 c1 z1+k2 c2 z2. If k1 k2 !=0 and c1 b2-c2 b1 !=0, perturb by (delta_z1,delta_z2)=lambda(k2 b2,-k1 b1). Then delta_y=0 but delta_t=lambda k1 k2(c1 b2-c2 b1), unbounded with lambda. This is a counterexample to a generic post-compression matching claim; it is not a numerical counterexample calibrated to the actual seven released maps. The analogous complete24 criterion is ker(O_old) subset ker(O_new). The actual factorization has not been demonstrated.

## New pre-mask processing: feasible construction and unclosed domain

Let m_i denote each complete delivered map, H_i a declared finite harmonic analysis, J_L a common band selector, D_i a source-supported response correction, S_L a common synthesis, W the shared mask, and P24 the final signed tensor extraction. Define a genuinely new observable

    y_i_new = P24 W S_L D_i J_L H_i m_i.

This needs the cached full maps, not just old24 values. It can be implemented solver-free, and would be a new producer/operator rather than an old producer retry. Under an exact common finite sky domain and known responses, choose D_i so the resulting component response factors into the required common angular operator and spectral coefficients; then the theorem above applies.

For the actual sky m_i=R_i z+n_i, the relevant remainder is

    P24 W S_L D_i J_L H_i R_i (I-J_source,L) z

plus response mismatch, pixel/quadrature error, calibration and spectral truncation. Output low-pass filtering alone does not prove that term zero. Non-diagonal R_i can couple high input modes and temperature to low polarization modes before filtering. An exact finite-bandlimit hypothesis may set it zero **by assumption**; that changes the domain and does not establish an actual-sky bound. Averaged scalar windows or spectrum-transfer matrices do not determine the phase-resolved R_i. [QuickPol](https://www.aanda.org/articles/aa/pdf/2017/02/aa29626-16.pdf)

## Actual-sky reopening contract: source gate only, not numerical dispatch

The next action for the actual-sky route is a bounded source/transport qualification of the public spatial polarized beam route. The separately frozen `SPECTRAL_ONLY_CONTRACT.md` tests only a stipulated common-response spectral model and does not satisfy this gate. Required output before freezing observed-sky numerical execution:

1. Bind PR3 full-mission LFI BPassCorrected30/44/70 and HFI R3.01 full100/143/217/**353-PSB** to actual polarized beam blocks, pixel/scan convention, source version and masks. Read beam file headers/index/official reader semantics first. Establish whether the linked full-mission beam set is applicable to these products; its location under PR3 or the reader's older date alone decides neither way.
2. Identify which gain, polarization efficiency/angle, sidelobe, bandpass-equalization and low-ell mapmaking response terms are included. Supply missing terms or declare a precise approximate response family. Qualify component-specific passband weighting and the CMB conversion denominator; inspect literal HDU/FLAG/units without silently selecting duplicate HFI F100 names or swapping 353 for353PSB.
3. Freeze an angular domain, tensor target and foreground moment list **before fitting values**. Supply a controlled omitted-domain/remainder set, or explicitly freeze a finite-domain conditional hypothesis with claims limited to that hypothesis. No exact bound may be inferred from a small smoothing kernel, a calibration mean, or a beam-error spectrum alone.
4. Freeze complete A/B matrices or a reproducible compact generating procedure and residual controls. Only then decide whether the saved-output route factors through its old operator, or a new pre-mask producer is necessary. Reject a complete24 result if the response rank loses modes; retain the exact kernel instead.
5. Have an independent Astra reviewer assess source/domain qualification. A subsequent lower-tier contract must specify source hashes/paths, numerical tolerances derived from response/numerical bounds, all controls, actual host headroom, one execution envelope and independent checker reserve. None is silently supplied by this note.

Prospective controls include full signed E/B injections across the declared input domain, temperature leakage where applicable, out-of-band response probes justified by the remainder model, unit/PSB/polarization-sign checks, exact zero/unity response limits, rank-deficient and near-singular branches, and independently reconstructed matrix actions. Controls demonstrate the declared operator implementation; they cannot manufacture the physical remainder law.

Accounting ancestry remains `R26-FULL7-STREAMED-SPIN2-QUADRATURE`. The latest examined settled head is `/mnt/extdrive/workdir/htt_open_data/r27_eight_map_actual_scientific_review/ROOT_ACCOUNT_HEAD_AFTER_REVIEW.json`, SHA256 `39f4aae7543a91b00154d414086d049c66e0e51d7f2956b27cf0abf58bcc9432`; its ancestor includes `e3c9f09ea5091290165479d51b291a0a860998c1594e58ac2eea7011e4ad685c`. Original per-account900s lifetime caps and consumed intervals remain unchanged. A parent must refresh live ancestry and freeze any genuinely new operator's costs before ACK; this note creates no account, new cap, ultra allocation, task binding or uncharged science execution.

Current actual-sky stopping result is HOLD_MISSING_QUALIFIED_RESPONSE_AND_DOMAIN, not a universal impossibility of Planck foreground analysis. The independent spectral-only numerical contract can test the finite model's rank without changing that result. No plot is prescribed merely to fill a DAG node.
