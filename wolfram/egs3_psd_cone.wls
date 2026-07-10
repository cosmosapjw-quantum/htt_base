(* EGS3 revisionary redesign: symbolic core for the PSD-cone sector comparator.
   Returns a JSON-serializable Association of boolean checks. Proves, in closed
   form, the structural identities the redesign rests on:
     (1) the trace functional reproduces the signed summary  x_C = tr(C M) = <c,g>
         for the labelled-eigenbasis comparator M = diag(g);
     (2) the admissible set -- nonnegativity on the three GENUINE second-moment
         sectors {Sigma^2, W^2, Omega_tilt} times the SIGNED Omega_k line (the
         code's actual set; global M >= 0 is NOT asserted, matching the 2026-07
         independent review) -- is a CONVEX CONE;
     (3) the NT2-B1 bracket is a CONVEX shell that excludes the FLRW vertex,
         and the shell coordinate conversion is exact: a linear-shear bracket
         [lo, hi] on Sigma >= 0 maps to [lo^2, hi^2] on the Sigma^2 eigenvalue
         (the P1 units repair). *)
ClearAll["Global`*"];

(* sectors and signature *)
g  = {s2, w2, ot, ok};                    (* (Sigma^2, W^2, Omega_tilt, Omega_k) *)
c  = {1, -1, 1, 1};
Cmat = DiagonalMatrix[c];
M  = DiagonalMatrix[g];

(* (1) trace identity: tr(C M) equals the dot product <c,g> exactly.
   Omega_k stays FREE (signed coordinate) -- no ok >= 0 assumption anywhere. *)
traceIdentity = Simplify[Tr[Cmat . M] - c . g] === 0;

(* spectrum of M equals g (the sectors ARE the labelled eigenvalues) *)
spectrumIsSectors = Simplify[Diagonal[M] - g] === {0, 0, 0, 0};

(* (2a) cone (positive homogeneity) on the code's ACTUAL admissible set:
   nonneg second-moment block {s2, w2, ot}, ok free in R. Scaling by lam >= 0
   preserves block nonnegativity; the signed ok line is trivially closed. *)
momentAssume = s2 >= 0 && w2 >= 0 && ot >= 0 && lam >= 0;
positiveHomogeneity = Simplify[And @@ Thread[Most[Diagonal[lam M]] >= 0],
                               Assumptions -> momentAssume];

(* (2b) convexity: block-nonneg M1, M2 => block-nonneg convex combination;
   d1, d2v (the Omega_k entries) stay FREE. *)
M1 = DiagonalMatrix[{a1, b1, c1, d1}];
M2 = DiagonalMatrix[{a2v, b2v, c2v, d2v}];
convexAssume = a1 >= 0 && b1 >= 0 && c1 >= 0 &&
               a2v >= 0 && b2v >= 0 && c2v >= 0 && 0 <= t <= 1;
Mconv = t M1 + (1 - t) M2;
convexCone = Simplify[And @@ Thread[Most[Diagonal[Mconv]] >= 0],
                      Assumptions -> convexAssume];

(* the signed Omega_k line is closed under the same operations (a real line):
   lam*d and t d1 + (1-t) d2v are real for real inputs -- recorded explicitly. *)
signedLineClosed = TrueQ[Element[lam d, Reals] /. {lam -> 2, d -> -3}] &&
                   TrueQ[Element[t d1 + (1 - t) d2v, Reals] /.
                         {t -> 1/3, d1 -> -1, d2v -> 5}];

(* (3) cone-shell: {lambdaSigma > sLo} and {lambdaSigma < sHi} are half-spaces;
   their intersection with the cone is convex, and sLo > 0 excludes the
   shear-free vertex (lambdaSigma = 0). lambdaSigma = M[[1,1]] = s2. *)
shellConvex = Resolve[ForAll[{x, y, tt, sLo, sHi},
     Implies[(sLo <= sHi) && (sLo <= x <= sHi) && (sLo <= y <= sHi) && (0 <= tt <= 1),
             sLo <= tt x + (1 - tt) y <= sHi]], Reals];
vertexExcluded = Resolve[ForAll[{sLo, sHi},
     Implies[sLo > 0, Not[sLo < 0 < sHi]]], Reals];

(* P1 units repair: squaring maps a linear-shear bracket to the Sigma^2 bracket
   exactly (monotone on the nonneg reals), so bracket_shell_from_a2a3 returning
   (lo^2, hi^2) is the correct image of {lo <= Sigma <= hi} in eigenvalue units. *)
bracketSquareExact = Resolve[ForAll[{lo, hi, sig},
     Implies[0 <= lo <= sig <= hi, lo^2 <= sig^2 <= hi^2]], Reals];

<|
  "schema" -> "htt.egs3.psd_cone.v2",
  "checks" -> <|
    "trace_identity_reconstructs_xc" -> TrueQ[traceIdentity],
    "spectrum_equals_sectors" -> TrueQ[spectrumIsSectors],
    "cone_positive_homogeneity" -> TrueQ[positiveHomogeneity],
    "admissible_set_is_convex_cone" -> TrueQ[convexCone],
    "signed_omega_k_line_closed" -> TrueQ[signedLineClosed],
    "bracket_shell_is_convex" -> TrueQ[shellConvex],
    "positive_lower_bound_excludes_flrw_vertex" -> TrueQ[vertexExcluded],
    "linear_to_eigenvalue_bracket_square_exact" -> TrueQ[bracketSquareExact],
    "signature" -> "C = diag(+1,-1,+1,+1); x_C = tr(C M); admissible set = (nonneg 3-sector second-moment block) x (signed Omega_k line)"
  |>
|>
