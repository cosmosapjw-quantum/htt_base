# Appendix E. A local radiation model behind the kinematical bounds

## E.1 Why state the radiation model?

Section 6 uses restrictions on shear and vorticity that depend on radiation multipoles and their derivatives. A small temperature anisotropy at one event does not determine those derivatives. To separate the physical premise from the mathematical deduction, this appendix specifies a sufficient first-order collisionless-radiation model and derives the two bounds used in the report. The result is conditional on the model and its derivative envelopes. It is not a converse theorem reconstructing spacetime from one sky, nor a proof of every version of the almost-Ehlers–Geren–Sachs programme.

The model is local to an expanding, nearly isotropic region. All equations in this appendix are equations of the retained first-order system. Products of two perturbations, including a first-order spatial density gradient times a first-order radiation anisotropy, are omitted. The expansion below does not imply an error-controlled nonlinear bound at a specified finite perturbation amplitude. Such a statement would require bounds on the discarded terms.

We use the geodesic congruence and geometric rate convention of Section 5. Spatial distances and the parameter along the unit observer have length units; multiplying rates by c converts them to inverse-time rates. The energy density rho, energy-flux coordinate q_a and anisotropic stress pi_ab below all have energy-density units in the decomposition relative to a unit observer. The physical energy flux is c q_a. The symbol q_a in this appendix is not the unit quadrupole q_ab used elsewhere.

## E.2 Brightness, multipoles and the transport equation

Let e be a unit propagation direction in the observer's rest space. It is the negative of the outward sky direction n. Let I(x,e) be the frequency-integrated radiation brightness, normalised so that its angular integral is the radiation energy density. A possible definition is a positive constant times the integral of E_gamma cubed times the scalar photon occupation number over positive energy; the constant fixes units and cancels in the ratios below. We assume the energy boundary terms vanish when integrating the collisionless transport equation.

Define the radiation moments by

\[
\rho=\int I\,d\Omega,\qquad q_a=\int I e_a\,d\Omega,\qquad
\pi_{ab}=\int I e_{\langle a}e_{b\rangle}\,d\Omega,
\qquad
\xi_{abc}=\int I e_{\langle a}e_be_{c\rangle}\,d\Omega.
\tag{E.1}
\]

At first order, a direction-dependent Planck temperature has brightness proportional to its fourth power. More explicitly, changing variable from photon energy to E_gamma divided by k_B T in the Planck integral gives I proportional to T to the fourth power; expanding that power gives a factor four multiplying the fractional temperature anisotropy. Write the propagation-direction multipoles as vartheta_A and use

\[
I=\frac{\rho}{4\pi}\left[1+4\vartheta_a e^a
+4\vartheta_{ab}e^ae^b+4\vartheta_{abc}e^ae^be^c+\cdots\right].
\tag{E.2}
\]

Each tensor with at least two indices is STF. The outward-temperature multipoles differ by the factor (-1) to the multipole order, so their full norms agree. The angular integrals in Lemma 3.2 now give

\[
q_a=\frac43\rho\vartheta_a,\qquad
\pi_{ab}=\frac8{15}\rho\vartheta_{ab},\qquad
\xi_{abc}=\frac8{35}\rho\vartheta_{abc}.
\tag{E.3}
\]

For example, the dipole uses the second angular moment 4 pi delta_ab divided by three; the quadrupole and octupole use exactly the trace-free pairings already proved in Section 3. Higher multipoles do not contribute to these lower moments at linear order because the corresponding harmonic sectors are orthogonal.

The local first-order brightness equation of the model is

\[
\dot I+e^aD_a I+\frac43\Theta I
+4\bar I\,\sigma_{ab}e^ae^b=0,
\qquad \bar I=\frac{\bar\rho}{4\pi}.
\tag{E.4}
\]

Here a bar on rho or I denotes the isotropic background, not a unit tensor. The equation follows from frequency-integrated collisionless Liouville transport as follows. At zeroth order the photon energy redshifts at rate -Theta divided by three; at first order the additional rate is -sigma_ab e^a e^b. Multiplying the energy-derivative term of the occupation-number equation by E_gamma cubed and integrating by parts yields the factor four. The angular-direction drift acts on an isotropic background brightness and therefore gives no first-order term there; its action on an anisotropy would be a product of first-order quantities. Geodesicity removes the acceleration-redshift term. The derivative of the anisotropy itself is retained in the first two terms of Eq. (E.4). This specifies the transport approximation rather than appealing to an unnamed temperature–geometry rule.

The energy redshift used in this derivation can also be checked directly. For an affine photon geodesic, p^b nabla_b p^a equals zero and E_gamma equals -c p_a u^a. Differentiating the latter gives a contraction of p^a p^b with nabla_b u_a. Substituting Eq. (5.3), using a geodesic observer and the symmetric photon product, removes acceleration and vorticity and leaves the isotropic expansion plus sigma_ab e^a e^b. Parameterising the ray by the observer-frame path length yields the rate just stated. Thus no Einstein field equation is needed for these two local kinematical estimates once the observer and radiation model are fixed. Additional curvature conclusions of the broader almost-isotropy programme require additional equations.

## E.3 The three moment equations

Integrate Eq. (E.4) against 1, e_a and e_<a e_b>. The result is

\[
\dot\rho+\frac43\Theta\rho+D^a q_a=0,
\tag{E.5}
\]

\[
\dot q_{\langle a\rangle}+\frac43\Theta q_a
+\frac13D_a\rho+D^b\pi_{ab}=0,
\tag{E.6}
\]

\[
\dot\pi_{\langle ab\rangle}+\frac43\Theta\pi_{ab}
+\frac8{15}\bar\rho\sigma_{ab}
+\frac25D_{\langle a}q_{b\rangle}+D^c\xi_{abc}=0.
\tag{E.7}
\]

The coefficient two fifths in Eq. (E.7) is important. The fully symmetric third angular moment satisfies

\[
\int I e_a e_b e_c\,d\Omega
=\xi_{abc}+\frac15(h_{ab}q_c+h_{ac}q_b+h_{bc}q_a).
\tag{E.8}
\]

Its trace determines the one-fifth coefficient. Subtracting one third h_ab times the flux and then differentiating gives the streaming contribution two fifths D_<a q_b> plus the divergence of xi. The shear coefficient comes from four times the isotropic fourth angular moment contracted with an STF2 tensor, giving eight fifteenths times rho. Thus every coefficient of the retained equations follows from the angular moments already proved in the report.

When a first-order quantity multiplies rho, we may replace rho by its background value at this order. Equation (E.5) consequently supplies the background relation dot(rho) equals minus four thirds Theta rho in such products. This does not remove the first-order divergence of flux from the full monopole equation.

## E.4 The derivative envelopes used here

At every point of the domain where the conclusion is intended, suppose rho is positive, Theta is positive and

\[
\|\vartheta_{A_\ell}\|\le\epsilon_\ell,\qquad
\|\dot\vartheta_{ab}\|\le\Theta\epsilon_2^*,\qquad
\|D_a\vartheta_b\|\le\Theta\epsilon_1',\qquad
\|D_d\vartheta_{abc}\|\le\Theta\epsilon_3'.
\tag{E.9}
\]

All tensor norms are full spatial Frobenius norms. In addition, set C_ab equal to D_[a vartheta_b] and assume

\[
\|\dot C_{ab}\|\le\Theta^2\epsilon_1^{\prime *},
\qquad
\|D_{[a}D^c\vartheta_{b]c}\|
\le\Theta^2\epsilon_2^{\prime\prime}.
\tag{E.10}
\]

Dots in these formulas include the indicated spatial projections. The second double-prime envelope in Eq. (E.10) bounds the explicitly written differentiated-divergence operator. It is not silently equated to the full norm of an uncontracted second derivative. A stronger uncontracted derivative bound may imply it with a dimension-dependent operator factor, which must then be retained. Equations (E.9)–(E.10) are an explicit sufficient derivative prescription for this appendix. Their applicability must be supplied by the physical model; they are not inferred from the local powers C_ell.

This precision matters. Naming an epsilon a derivative bound does not determine which contraction or norm it bounds. The amplitude-only specialisation below assumes the displayed operator envelopes themselves satisfy the scale restrictions. It does not claim those restrictions for every smooth almost-isotropic radiation field.

## E.5 Shear estimate

Take norms in Eq. (E.7) and apply Eq. (E.3). The background product rule gives

\[
\|\dot\pi\|
\le\frac8{15}\rho\Theta
\left(\epsilon_2^*+\frac43\epsilon_2\right),
\qquad
\frac43\Theta\|\pi\|\le\frac8{15}\rho\Theta\frac43\epsilon_2.
\tag{E.11}
\]

Orthogonal STF projection does not enlarge a norm. Furthermore,

\[
\|D^c\vartheta_{abc}\|\le\sqrt3\,\|D_d\vartheta_{abc}\|.
\tag{E.12}
\]

For each free pair a,b, this is Cauchy–Schwarz on the sum over the three contracted index values, followed by summation over a,b. Substitution into Eq. (E.7) therefore proves the sufficient estimate

\[
\frac{\|\sigma\|}{\Theta}
\le\frac83\epsilon_2+\epsilon_2^*+\epsilon_1'
+\frac{3\sqrt3}{7}\epsilon_3'
\le\frac83\epsilon_2+\epsilon_2^*+5\epsilon_1'
+\frac97\epsilon_3'.
\tag{E.13}
\]

The final inequality deliberately uses a less sharp positive bound to recover the coefficient combination retained in Section 6. The passage from one to five in the dipole term is a valid weakening, not the value of the quadrupole streaming coefficient. Cancellation of the background expansion terms before the norm estimate would yield a stronger bound in this particular first-order model; no optimality of Eq. (E.13) is asserted.

## E.6 Vorticity estimate

With the vorticity convention of Eq. (5.2), a scalar f satisfies

\[
D_{[a}D_{b]}f=-\omega_{ab}\dot f.
\tag{E.14}
\]

To derive the identity, differentiate the rest-space projection h_b{}^c in D_a D_b f. Antisymmetrisation kills the symmetric spacetime second derivative of a scalar. The surviving projected derivative of u_b is D_[a u_b] times dot(f), equal to minus omega_ab dot(f) under the stated index convention.

The first-order commutator for the flux is

\[
D_{[a}\dot q_{b]}=(D_{[a}q_{b]})^{\displaystyle\cdot}
+\frac13\Theta D_{[a}q_{b]}.
\tag{E.15}
\]

For the retained nearly isotropic background this follows from the projected derivative definition: differentiating a spatial covector gradient along the flow differentiates two spatial basis factors, whereas taking a spatial derivative after the covector time derivative differentiates one. Their difference is H_g times that gradient. Corrections involving shear, vorticity, acceleration or a spatial gradient of Theta multiplied by the first-order flux are higher order in this model. The same result can be checked in comoving coordinates of the background metric, where the relevant spatial connection in the time direction is H_g times the identity.

Antisymmetrise the spatial derivative of Eq. (E.6). Products q_a D_b Theta are second order. Put Q_ab equal to D_[a q_b]. Using Eqs. (E.14)–(E.15) and the background monopole equation gives

\[
\frac49\Theta\rho\,\omega_{ab}
=-\dot Q_{ab}-\frac53\Theta Q_{ab}
-D_{[a}D^c\pi_{b]c}.
\tag{E.16}
\]

Now Q_ab equals four thirds rho C_ab at retained order. Applying the product rule, Eq. (E.10), and the norm-decreasing property of antisymmetrisation gives

\[
\|Q\|\le\frac43\rho\Theta\epsilon_1',
\qquad
\|\dot Q\|\le\frac43\rho\Theta^2
\left(\epsilon_1^{\prime *}+\frac43\epsilon_1'\right),
\tag{E.17}
\]

\[
\|D_{[a}D^c\pi_{b]c}\|
\le\frac8{15}\rho\Theta^2\epsilon_2^{\prime\prime}.
\tag{E.18}
\]

Terms in which a density derivative multiplies a temperature anisotropy have been omitted at the specified perturbative order. Divide the norm bound from Eq. (E.16) by Theta and insert Eqs. (E.17)–(E.18). All coefficients are then explicit:

\[
\frac{\|\omega_{ab}\|}{\Theta}
\le
\frac94\frac43\left(\frac43+\frac53\right)\epsilon_1'
+\frac94\frac43\epsilon_1^{\prime *}
+\frac94\frac8{15}\epsilon_2^{\prime\prime}
=9\epsilon_1'+3\epsilon_1^{\prime *}
+\frac65\epsilon_2^{\prime\prime}.
\tag{E.19}
\]

This is the second derivative-envelope combination used in Section 6, now with the precise derivative operator in its hypothesis.

## E.7 Amplitude ceilings and the scope of the conclusion

Finally adopt, as maintained characteristic-scale assumptions,

\[
\epsilon_2^*\le\epsilon_2/3,\quad
\epsilon_1'\le\epsilon_1/3,\quad
\epsilon_3'\le\epsilon_3/3,\quad
\epsilon_1^{\prime *}\le\epsilon_1/9,\quad
\epsilon_2^{\prime\prime}\le\epsilon_2/9.
\tag{E.20}
\]

Equations (E.13) and (E.19) then give the two amplitude bounds of Eq. (6.3), in non-strict form. Strict inequalities require strict envelope premises or a strict slack at one of the corresponding bounding steps; weak assumptions alone do not prove a strict conclusion. The closed outer bodies used for inference are consequently valid with the non-strict version. No saturation observation is implied.

The derivation is internally complete for the stated first-order model, moment definitions, commutators and derivative envelopes. Its physical premises remain premises: geodesic fundamental observers, collisionless thermodynamic radiation, the retained perturbation order, a positive expanding background and the specified all-domain derivative controls. Their general validity does not follow from the algebra, and the complete nonlinear Einstein–Liouville almost-isotropy theorem is not claimed. What is obtained is the self-contained sufficient branch needed to understand the report's radial physical constraints, with every conversion and contraction shown.
