# R9 revision 2 — source-seeded research question

Owner: HTT/common/MIO by operation; scope: research derivation, bounded numerical experiments, and executable research DAG design. No production inference or proof-registry promotion.

User-authorized delivery: upgrade the R9 program from commit `5e4e899c0dfa2028d81a82ca68ccd11203947470` in place, using the compendium at `d514eabdbd6a464a92ff6e51e1aba91399a054db`, commit/push to `implementation/project-catalog-20260912`, and provide handoff. The catalog branch lacks R9; import that directory from its exact source rather than implying it was already merged.

## Research questions and consumers

1. DEPTH-LAW: For a stacked depth vector Y with known PSD covariance C and fixed feature transports K, derive the complete residual law H C H^T, including cross-step covariances and deterministic support restrictions. Determine what information a contrast-only path loses and whether keeping the initial block restores it. Consumer: R9 response/law adapter, MIO depth path, HTT common-state likelihood. Do not infer a filtration or exchangeability from nested support metadata.
2. FUNCTIONAL-IMAGE: Starting from a valid common confidence region for the state and uncertain anchors, derive simultaneous images for tensor functionals, gauges and directional supports. Separate true-point coverage from whole identified-set coverage and conditional posterior probability. Treat denominator zero/unknown and nonlinear boundary fibres explicitly. Consumer: R9 physical-image and structured report stages.
3. Execute transparent positive and negative controls. Frozen initial design: scalar three-depth C=I; first differences H=[[-1,1,0],[0,-1,1]]; full-correlation duplicate case C=ones(3,3); two-depth correlation rho in {-0.8,0,0.8}; K=1. Check full covariance, dropped cross terms, dropped cross-step terms, support violations, and loss of a common-level mean. Use seed 20260912, 100000 Gaussian draws, alpha=.05, reference numerical tolerance 1e-10, Monte Carlo comparison tolerance .005. No calibration threshold is relaxed after results.
4. Q/O contraction fibre sensitivity is a seed result (compendium §9.3), not a new novelty claim. For unit q, L_q o=o:q, R_q=B_q M_q^-1, eta(v)=3v^T M_q^-1 v: derive linear-functional support over the norm-one fibre and implications for confidence images near eta=1. Keep q fixed in this calculation; uncertain q requires a joint inverse image.

## Evidence and execution boundaries

- Scientific claims require assumptions, argument, counterexample search and independent review. Generic prompted agents are not authenticated independent model profiles. No registered four-axis production claim is admitted in this revision; any required production CAS gate remains blocked until its existing four-axis contract executes.
- The user selected GPT-6 Astra harness v4.0.0. The skill registry supplies exact research/coding archive identities, but this session exposes no Library retrieval tool and the ZIPs are not attached. Do not relabel the available GPT-5.6 harness as GPT-6 or claim the GPT-6 package was loaded. Repository research protocol and skill routing can run; exact GPT-6 package activation remains blocked and must be reported.
- Rovo is coordination context; SciSpace retrieves literature leads; primary papers are separately checked. Wolfram supplies independent small symbolic checks, not xAct/four-axis acceptance.
- R8 historical numerical results and holds, CF4 law quarantine, DESI conditional summary, Union3 scenario and native-provider absence persist. No new cosmological measurement follows from synthetic tests.
- Existing tensor formalism controls over older scalar shorthand: x becomes functional arrays, Q anchor gauge/margin, F directional support, Pi law-tagged exceedance surfaces, G_F typed depth paths. Missing physical providers produce unavailable status, never zero-filled kinematics.

## Completion criteria

Derivations plus reproducible controls and critical review; preserved R9 node IDs with justified added/refined dependencies; product-specific model-to-data contracts and next runnable slice; canonical DAG/status mirrors synchronized; commit and remote readback. Full observational campaign and GPT-6 archive activation must not be reported complete unless actually executed.
