(* EGS3 revisionary redesign: symbolic core for the PSD-cone sector comparator.
   Returns a JSON-serializable Association of boolean checks. Proves, in closed
   form, the three structural identities the redesign rests on:
     (1) the trace functional reproduces the signed summary  x_C = tr(C M) = <c,g>
         for the labelled-eigenbasis comparator M = diag(g);
     (2) the admissible set is a CONVEX CONE (PSD preserved under nonnegative
         scaling and convex combination);
     (3) the NT2-B1 bracket is a CONVEX shell (intersection of the cone with two
         half-spaces in the shear eigendirection) that excludes the FLRW vertex. *)
ClearAll["Global`*"];

(* sectors and signature *)
g  = {s2, w2, ot, ok};                    (* (Sigma^2, W^2, Omega_tilt, Omega_k) *)
c  = {1, -1, 1, 1};
Cmat = DiagonalMatrix[c];
M  = DiagonalMatrix[g];

(* (1) trace identity: tr(C M) equals the dot product <c,g> exactly *)
traceIdentity = Simplify[Tr[Cmat . M] - c . g] === 0;

(* spectrum of M equals g (the sectors ARE the labelled eigenvalues) *)
spectrumIsSectors = Simplify[Diagonal[M] - g] === {0, 0, 0, 0};

(* (2a) cone (positive homogeneity): M >= 0, lambda >= 0  =>  lambda M >= 0.
   For the diagonal comparator, eigenvalues are the entries; nonnegativity is
   preserved by nonnegative scaling. *)
$Assumptions = s2 >= 0 && w2 >= 0 && ot >= 0 && ok >= 0 && lam >= 0;
positiveHomogeneity = Simplify[And @@ Thread[Diagonal[lam M] >= 0]];

(* (2b) convexity: M1, M2 >= 0  =>  t M1 + (1-t) M2 >= 0 for t in [0,1]. *)
M1 = DiagonalMatrix[{a1, b1, c1, d1}];
M2 = DiagonalMatrix[{a2v, b2v, c2v, d2v}];
convexAssume = a1 >= 0 && b1 >= 0 && c1 >= 0 && d1 >= 0 &&
               a2v >= 0 && b2v >= 0 && c2v >= 0 && d2v >= 0 && 0 <= t <= 1;
Mconv = t M1 + (1 - t) M2;
convexCone = Simplify[And @@ Thread[Diagonal[Mconv] >= 0], Assumptions -> convexAssume];

(* (3) cone-shell: {lambdaSigma > sLo} and {lambdaSigma < sHi} are half-spaces;
   their intersection with the PSD cone is convex, and sLo > 0 excludes the
   shear-free vertex (lambdaSigma = 0). lambdaSigma = M[[1,1]] = s2. *)
shellConvex = Resolve[ForAll[{x, y, tt, sLo, sHi},
     Implies[(sLo <= sHi) && (sLo <= x <= sHi) && (sLo <= y <= sHi) && (0 <= tt <= 1),
             sLo <= tt x + (1 - tt) y <= sHi]], Reals];
vertexExcluded = Resolve[ForAll[{sLo, sHi},
     Implies[sLo > 0, Not[sLo < 0 < sHi]]], Reals];

<|
  "schema" -> "htt.egs3.psd_cone.v1",
  "checks" -> <|
    "trace_identity_reconstructs_xc" -> TrueQ[traceIdentity],
    "spectrum_equals_sectors" -> TrueQ[spectrumIsSectors],
    "cone_positive_homogeneity" -> TrueQ[positiveHomogeneity],
    "admissible_set_is_convex_cone" -> TrueQ[convexCone],
    "bracket_shell_is_convex" -> TrueQ[shellConvex],
    "positive_lower_bound_excludes_flrw_vertex" -> TrueQ[vertexExcluded],
    "signature" -> "C = diag(+1,-1,+1,+1); x_C = tr(C M); admissible set = PSD cone"
  |>
|>
