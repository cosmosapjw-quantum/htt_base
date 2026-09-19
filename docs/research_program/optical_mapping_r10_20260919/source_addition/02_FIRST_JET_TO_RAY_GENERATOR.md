# Exact first-jet -> ray-generator map

For a massless ray k^a=E(u^a+e^a),

D_gamma ln E
= -(theta/3 + A.e + sigma:ee),

D_gamma e^{<a>}
= -s^a_b A^b
  -eta^a_bc omega^c e^b
  -s^a_b sigma^b_c e^c.

Define

H(e)=theta/3+A.e+sigma:ee,
V^a(e)=-s^a_b A^b-eta^a_bc omega^c e^b-s^a_b sigma^b_c e^c.

Let Phi(e)=A.e+(1/2)sigma:ee. Then

V=-grad_S2 Phi + omega x e.

Exact sphere identities:

div_S2 V = 2 A.e + 3 sigma:ee,
curl_S2 V = 2 omega.e.

Explicit inverse:

theta = 3/(4pi) ∫H dOmega,
A_a = 3/(4pi) ∫H e_a dOmega,
sigma_ab = 15/(8pi) ∫H e_<a e_b> dOmega,
omega_a = 3/(8pi) ∫[e x V]_a dOmega.

Equivalent V-only E-mode inverses:

A_a = 3/(8pi) ∫(div V)e_a dOmega,
sigma_ab = 5/(8pi) ∫(div V)e_<a e_b> dOmega.

Thus the combined response is injective on all 12 independent components of ∇u.

Statistically, discretize the sky and use the same response operator with mask, covariance
and nuisance projection. Structural rank is checked before whitening; practical conditioning
is checked only after a declared physical/covariance metric.
