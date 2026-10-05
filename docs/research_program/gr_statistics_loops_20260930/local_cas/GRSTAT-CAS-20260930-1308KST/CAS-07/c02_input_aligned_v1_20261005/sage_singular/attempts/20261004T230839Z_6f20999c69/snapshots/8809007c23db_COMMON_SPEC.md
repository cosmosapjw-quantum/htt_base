# Neutral mathematical conventions for local CAS

This file specifies inputs and claims to check. It contains no engine result or proof.
All components use signature (-,+,+,+), future u with g(u,u)=-1, U=c u and c>0.
Coordinates x0=c t have length dimension. g=diag(-1,1,1,1) in the stated orthonormal frame.
Indices are raised with g inverse. Q_ab=∇_a U_b is derivative-first; B_ab=(Q_ab+Q_ba)/2.
Q u=0 means Q_ab u^b=0. b_a=B_ab u^b is a covector; A_b=c u^a Q_ab.
u_flat=g u; h_ab=g_ab+u_a u_b and h^a_b=delta^a_b+u^a u_b.
Spatial projections must preserve index variance; a compact hBh uses the matching mixed projectors.
The spatial trace/STF/skew parts define theta, sigma and W. W_ij=epsilon_ijk omega_k with epsilon123=+1,
so W x=-omega cross x. This derivative-first W equals minus c times the book's velocity-first vorticity.
If differentiating unit u instead of physical U, carry the extra c: A_cov=2c^2 sym(∇u)u.

Observer-normalized sourceward K=(-1,n), n.n=1, o.K=1 for observer o=(1,0,0,0).
S00=h0,S0i=-h1_i/2,Sij=h2ij with h2 symmetric tracefree; K^T S K=h0+h1.n+h2:nn.
Absolute vertex Z0=lim(1+z) is not fixed to 1 for a boosted observer. H=c dz/ddA at the vertex.
Source-forward propagation uses L=U+c e, e.u=0 and e.e=1. It is a different direction convention.
Ray derivatives are not observer-time derivatives. dL=(1+z)^2 dA requires reciprocity/transparency.
All norm inequalities use declared positive component/Hilbert norms, never the indefinite Lorentz norm.

For the energy frame T^a_b u^b=-epsilon u^a, rest pressures are p_i and delta=min_i|epsilon+p_i|>0.
D_X=h(∇_X T)u. kappa=8pi G_N/c^4; epsilon and p are energy densities, cs^2=c^2 dp/depsilon.
For TOV use R^a_bcd=∂c Gamma^a_db-∂d Gamma^a_cb+Gamma^a_ce Gamma^e_db-Gamma^a_de Gamma^e_cb
with consistent connection-index convention. Fixed action X=-g^(ab)psi_a psi_b/2>0,
P=Pstar X^s, Pstar>0, s=(1+alpha)/(2alpha), q>0 and Pstar(q^2/2)^s=p0; psi=q x0.

Matrix R in a residual Gram ellipsoid is not a noise covariance. A radiation residual R_rad is separately typed.
The scalar brightness I and its spacetime derivative/collision inputs must be independent supplied quantities.
Generic tensor T used for observables is not silently identified with stress T_ab.

For each task, the contract component list is the exact CAS target. CAS_TASKS.json describes the larger research
claim and explicitly retains analytical obligations. An exact component PASS is not full-theorem formalization.
No scripts, derivations or results from sibling axes or historical evidence may be read before adjudication.
Source hash locators for old proof documents are orchestrator-only identity checks, not blind-worker read permission.
