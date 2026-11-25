# R118 cold Thomson spectral moments on accepted BASS histories
BASS commit 9eeedf1a3cfbe1d80a68de77af4339db828ff72f
tree 7749e6145347799085ada9dd26c1b82b9eb6b6aa, remote owner ref verified.
HTT parent c51721caaf501131f27671e5152f0c3246e15ffe.
REC unchanged f67be237187372f4d89fe8c021819a38261b14eb; REI unchanged.

Native Lie harmonic and characteristic ray transport of independent centered
B3, B4, M0, M1, M2 polarized screen tensors. Center xi=log(T/T_emit)+eta.
Exact lower-triangular log moment streaming and binomial boost shifts.
Five independent cold elastic Thomson sources share a 6x6 implicit matrix.
Gain normalization reconstructed on the chosen spectral mesh. New path
uses accepted geometry/depth/velocity, not original bolometric gain sources.
Spectral collision uses angular quadrature even for R116-A continuum histories.
No active spectral feedback or full frequency-resolved atomic source.
Observer boost preserves scalar central variance and Jensen Mellin diagnostic
y_M=(ln(B4/m0)-(4/3)ln(B3/m0))/4; y_M=v/2 only at leading order.
Collision conserves normal-frame photon number and material-frame weighted
energy integral; class A centered number conserved; class B continuity
N'=2 A.F checked by trapezoid with explicit quadrature residual.

237 regular + 3 example tests; 6 new tests. 47 histories: 41 scoped pass
and 6 raw realizability warnings, 12 Bianchi families, 8464 accepted
collision events, 318 legacy numerical TSV comparisons byte identical.
Per-cell relative number/rest-energy defects 1.938e-15/1.843e-15;
class A drift 6.329e-14, class B continuity quadrature 4.020e-10;
observer invariant gap 4.441e-16; B4 integral gap <=1.854e-9 including
different angular representations. Independent dense frequency oracle
648 dimensions, 384 frequency nodes, BE and SDIRK2, B3/B4 component
max 8.216e-15; log input polynomial oracle max 1.499e-15.
Final binary SHA256 607e916ec8a9a13a72832f2970a4742df3f447a407b23277ad57a9f34ddf9d49.

L=4 five low-z runs had negative variance/Jensen/moment Gram values
even though B4 integral differences <1.4e-13. L=8 VIIh still failed
Jensen tolerance; L=12 and L=16 passed. All original warnings resolved
by increasing ONLY spectral band on same accepted histories; no clipping.
Sampled necessary check status UNRESOLVED on failures (tol=1e-9);
not a sufficient moment realizability certificate. Refined L16 versus
independent ray mean variance absolute gaps: stronger I 1.181e-15,
VIIh 8.968e-14. L12->L16 differences <=8.640e-20.
Refined thermal I successive time ratios 3.98273/3.98262/4.00975
(mean variance/mean y_M/B4 integral); cold beta=.2 ratios 4.00425,
4.00429,4.00427. Manufactured cold beta=.85 depth=.15 mean variance
.380878, mean y_M .057113; 2 mean y_M/mean variance=.299902.
No equivalence to thermal SZ or cosmological prediction.

Evidence/scripts: BASS research/r118_cold_spectral_moments/.
Raw workstation histories ~/Downloads/bass_r118_spectral_final
and ~/Downloads/bass_r118_cell_final. Existing unrelated dirty files untouched.
No native independent subagent exposed. No R78 science DAG promotion.
Next R118-B-NONMONOTONE-FREQUENCY-TRANSFER-01: use conservative log-frequency
occupation transport and line-profile collision with sign-changing material
frequency drift rather than extending positive-Sobolev formula by clipping.
Thermal Compton/atomic emission and binding-energy exchange remain separate.
