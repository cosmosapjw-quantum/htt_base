# Restricted proper-motion response of the compensated homogeneous mode

Date 2026-10-20. Owner `htt`; `DERIVED`, `CONDITIONAL`, `C0`, non-claim-bearing. Requested theory runtime `gpt-6-astra/xhigh`; observed runtime `UNKNOWN`. This is a solver-free candidate for a **part** of K03, not K03 admission or a Gaia/radio likelihood. No existing Gaia or radio campaign was rerun.

Assume the linear compensated dust–radiation IC and frames of [THEORY.md](../theory/THEORY.md), flat FLRW, a dust-following source, $a_o=1$, small physical velocities divided by $c$, line of sight $\boldsymbol n$ from observer to source, and a nonrotating observer tetrad. Let $P_{\boldsymbol n}=I-\boldsymbol n\boldsymbol n^T$, $\chi(z)>0$ the background comoving distance, and observer velocity $\boldsymbol\beta_o=\boldsymbol b+\boldsymbol\ell$. The emitting dust velocity is $\boldsymbol\beta_s=(1+z)\boldsymbol b$. Dots are observer proper-time derivatives at this order.

For a slowly drifting source direction, differentiation of the retarded source–observer comoving separation gives $P_{\boldsymbol n}c(\boldsymbol\beta_s-\boldsymbol\beta_o)/\chi$. The source coordinate velocity $c\beta_s/a_s$ is multiplied by $dt_s/dt_o=a_s$; this cancels the source scale factor. First-order observer aberration adds $P_{\boldsymbol n}\dot{\boldsymbol\beta}_o$. The resulting transverse angular drift is

\[
\boldsymbol\mu(z,\boldsymbol n)=P_{\boldsymbol n}\left[
\left({cz\over\chi}-H_0\right)\boldsymbol b
-{c\over\chi}\boldsymbol\ell+\dot{\boldsymbol\ell}\right]+\boldsymbol r_\mu. \tag{K1}
\]

Here $\dot{\boldsymbol b}=-H_0\boldsymbol b$ follows from the dust velocity first integral. Equivalently define the observer's proper acceleration divided by $c$, $\boldsymbol\alpha=\dot{\boldsymbol\ell}+H_0\boldsymbol\ell$ at this order. Then

\[
\boldsymbol\mu=P_{\boldsymbol n}\left[-\left({c\over\chi}+H_0\right)\boldsymbol\ell
+\left({cz\over\chi}-H_0\right)\boldsymbol b+\boldsymbol\alpha\right]+\boldsymbol r_\mu. \tag{K2}
\]

The units are inverse observer time (radians/time). Geodesic observer motion sets $\alpha=0$; it does **not** set $\dot\ell=0$. The unbounded $\boldsymbol r_\mu$ retains unmodelled physical, source, frame and measurement drift. A distance remainder bound cannot be differentiated into a drift bound. A constant angular clock/spin/NNR response is a separate measurement nuisance, not secretly assigned zero. On a complete equal-depth sphere, $P_{\boldsymbol n}$ applied to a constant vector is an electric dipole/glide and has no magnetic dipole. Real masks and frame calibration can mix these sectors.

There is an ideal three-depth rank result even with free common $\alpha$. For one vector component the radial rows are $[-(c/\chi_j+H_0),\,cz_j/\chi_j-H_0,\,1]$. Add $H_0$ times the third column to the first two, then multiply each row by $\chi_j/c$: the rows become $[-1,z_j,\chi_j/c]$. In an expanding dust/radiation background with $H'(z)>0$, $\chi''(z)=-cH'(z)/H(z)^2<0$. Three distinct positive depths therefore give a nonzero determinant by strict concavity. Two depths cannot identify three vector amplitudes. The finite three-depth determinant check is in `test_compute.py`; this is an ideal radial statement, not actual masked-sky conditioning.

As $z\to0$, $cz/\chi-H_0=H_0(1+q_0)z/2+O(z^2)$, while $c/\chi$ has the local inverse-distance behavior. The compensated IC also requires $R|b|\ll1$ over the chosen interval. These restrictions are not inferred from the rank theorem.

An arbitrary depth-dependent electric glide nuisance $\boldsymbol q(z)$ exactly absorbs the global column under $\boldsymbol q(z)\mapsto\boldsymbol q(z)-[cz/\chi-H_0]\delta\boldsymbol b$. This is a constructive non-identification example. A single common acceleration vector cannot perform that absorption at three qualified depths because of the strict rank result.

The [Hall proper-motion paper](https://arxiv.org/html/1811.05454v3) supplies relevant comoving-distance and observer-aberration kinematics. Its assumption that matter and CMB rest frames coincide is **not** adopted in this tilted subcase. This note derives (K1)–(K2) within its own declared frames; it does not import Hall's statistical or cosmological conclusions.

Original K03 still requires actual proper-motion/NNR/clock response on the observed Gaia/radio support, release-specific frame propagation and their joint errors. Public position covariance, frame-envelope plots or a free glide cannot substitute for that payload. Neither a physical E/B all-$m$ atlas nor native solver output follows from this subcase.
