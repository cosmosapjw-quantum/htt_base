# R116: grid-free continuum harmonic Thomson cold bolometric collision

BASS pin 4c58712012542340155fbb9c813ab898693b3204
(tree eb80604c4fcb9e084afd71cab418b598a44b83a8).
Owner branch research/r109-native-nonlinear-sky-20261124; verified remote.
Source and complete receipts: BASS research/r116_continuum_collision/.
Theory parent HTT 188ca33d0813082ce23c6ce7a6d9419ef942c540.
Final binary sha256 68303e729caa85477b988a89c7b66e3656105bccee78f1bbe97df3d8b8463d91.
REC and REI unchanged.

Implemented R115 T3 as an opt-in harmonic-continuum route. Constant complex
dyad boost matrix K gives exact low-rank adjoint; rank-one Gaunt Doppler
multiplication, padded CG rational resolvents, six-dimensional implicit gain
and discrete recoil. Projection only after both SDIRK stages. Stage source
replay uses continuum gain (no quadrature normalization). Grid is retained
for sampled positivity, microphysics and output, not collision assembly.
Per-inverse residual gate is not a full forward error certificate.
No small-beta expansion; finite work band <=256.

226 Rust tests + 3 example tests pass on final binary source. 32 primary
short CLI cases + 4 extra cases pass. 12 Bianchi families: max LoS relative
L2 gap vs refined grid 5.903e-15, direct 5.677e-15; scaled Cl gap 3.649e-15.
Time refinement VIstar ratio 3.99969438. W20->28 LoS identical in one case.
Strong Bianchi I beta=(0.3,-0.1,0.2) L=16 grid comparison 9.787e-15.
L8/16/24 vs L32: 1.213e-15/0/0 in the short strong LoS case.
Diagnostic grid 24x48->40x80: LoS bytes identical in tested I case.
Six legacy output TSVs byte identical vs R114 binary.
Thin equilibrium 2000 cells drift 8.574e-12 before repair -> 2.220e-22.
All 12 types and applicable h invariant; exact values in ACCEPTANCE.json.
Full data: BASS RESULTS.json, EXTRA.json, logs and scripts.

Performance negative: median 17.61x slower than grid in small-family smoke,
strong case 114.64x slower. Keep as opt-in accuracy/reference route.
No long recombination history, high-l convergence or global positivity
certificate. Native subagent unavailable; independent existing numerical
ray oracle + self-review. No production dispatch/inference changes, no
R78 scientific promotion. Next R116-REC-SPECIES-THERMAL-01 in parallel with
R116-T3-RESOLVENT-ACCEL-01; use stable axial direct solves/cached kernels
for efficiency and verify long-depth/high-l separately.
