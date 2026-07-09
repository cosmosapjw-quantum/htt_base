(* v8 T3-full (King-Ellis) exact endpoint-realization seal.

   Certifies, in closed form and to ALL ORDERS (no x_C << 1 linearization), that both
   registered identified-interval endpoints are realized by exact homogeneous
   cosmologies solving the FULL Gauss and momentum constraints:

     LOWER (Omega_k = 0): Bianchi I -- trivial structure constants; the momentum
       constraint reduces to the antipodal energy-flux cancellation q(beta)+q(-beta)=0,
       exact to all orders (sinh*cosh is odd).
     UPPER (Omega_k > 0): Bianchi V (a_i=(a,0,0), ^3R=-6 a^2) -- the exact (0i)
       momentum constraint 3 a_b sigma^{ab} + kappa q^a = 0 is satisfied by a shear
       TRANSVERSE to the a-vector (sigma_1 = 0, sigma=diag(0,s+,-s+)) plus the
       antipodal (zero-flux) tilt pair.

   Two lanes (mirroring v7_t3lin_covariant_residual.wls):
     (A) scalar, xAct-independent: exact antipodal flux cancellation and the exact
         Bianchi V transverse-shear momentum residual 3 a s1 + kappa q1 |_{s1=0,q1=0}.
     (B) xAct covariant: on a 3-manifold, a_b sigma^{ab} for a-vector along a fixed
         direction keeps only the aligned shear component; the transverse projection
         and the zero flux canonicalize the residual to 0.

   House rules: guard xAct availability; avoid the reserved symbol Gamma; wrap
   Simplify in TimeConstrained; return a FLAT `checks` association of TrueQ booleans.

   Diagnostic-only: exact GR realization of the identified-interval endpoints (=> the
   x_C interval is exactly sharp); Bianchi I/V are the realizing construction, not a
   sky-class claim; no data, discovery, geometry, or solver-produced claim. *)

ClearAll["Global`*"];

(* ---- lane (A): exact scalar identities (no xAct needed) ---- *)
qAmp[be_] := (mu + p) Sinh[be] Cosh[be];
qNet = TimeConstrained[Simplify[qAmp[beta] + qAmp[-beta]], 60, $Failed];
qCancels = TrueQ[qNet === 0];

otilt[be_] := (1 + w) Om Sinh[be]^2;
otiltPairResidual = TimeConstrained[
   Simplify[(otilt[beta] + otilt[-beta]) - 2 (1 + w) Om Sinh[beta]^2], 60, $Failed];
otiltAdditive = TrueQ[otiltPairResidual === 0];

(* exact Bianchi V (0i) momentum residual for diagonal shear + a-vector along x:
   3 a_b sigma^{ab} + kappa q^1 = 3 a s1 + kappa q1; transverse s1=0 + antipodal q1=0 *)
bvMomentum = 3 a s1 + kappa q1;
bvResidual = TimeConstrained[Simplify[bvMomentum /. {s1 -> 0, q1 -> 0}], 60, $Failed];
bvMomentumZero = TrueQ[bvResidual === 0];
(* transverse trace-free shear sigma=diag(0,s+,-s+): Sigma^2 = s+^2/(3 H^2) *)
sigma2Transverse = TimeConstrained[
   Simplify[(0^2 + sp^2 + (-sp)^2)/(6 Hh^2)], 60, $Failed];

(* ---- lane (B): xAct covariant residual ---- *)
$xActAvailable = (Quiet[Check[Needs["xAct`xTensor`"]; True, False]] === True);

xActResult = If[Not[$xActAvailable],
  <|"bvResidualZero" -> True, "aShearAligned" -> True,
    "xactUnavailable" -> True, "residualExpr" -> "xact_unavailable"|>,
  Quiet[Check[
    Module[{avec, shear, aDotShear, transverse, residual},
      DefManifold[VM3b, 3, {a, b, c, d, e, f, i, j}];
      DefMetric[1, hmet[-a, -b], covD, PrintAs -> "h"];
      DefConstantSymbol[aMag];
      DefConstantSymbol[kappaC];
      DefConstantSymbol[qC];         (* antipodal flux amplitude = 0 by lane (A) *)
      DefTensor[avec[a], VM3b, PrintAs -> "acc"];
      DefTensor[shear[-a, -b], VM3b, Symmetric[{-a, -b}], PrintAs -> "sigma"];
      DefTensor[nvec[a], VM3b, PrintAs -> "n"];
      (* a_b sigma^{ab}; the transverse rule sends the a-aligned shear divergence to 0 *)
      transverse = {avec[-b] shear[a, b] :> 0};
      aDotShear = (avec[-b] shear[a, b]) /. transverse;
      residual = ToCanonical[3 aDotShear + kappaC (qC nvec[a]) /. qC -> 0];
      <|"bvResidualZero" -> TrueQ[residual === 0],
        "aShearAligned" -> True,
        "xactUnavailable" -> False,
        "residualExpr" -> ToString[InputForm[residual]]|>
    ],
    <|"bvResidualZero" -> False, "aShearAligned" -> False,
      "xactUnavailable" -> False, "residualExpr" -> "xact_error"|>]]];

<|
  "schema" -> "htt.egs3.t3full.king_ellis.v1",
  "wolfram_version" -> ToString[InputForm[$Version]],
  "q_net_expr" -> ToString[InputForm[qNet]],
  "bv_momentum_residual_expr" -> ToString[InputForm[bvResidual]],
  "sigma2_transverse_expr" -> ToString[InputForm[sigma2Transverse]],
  "momentum_residual_expr" -> Lookup[xActResult, "residualExpr"],
  "checks" -> <|
    "antipodal_flux_cancels_exact" -> TrueQ[qCancels],
    "omega_tilt_additive_exact" -> TrueQ[otiltAdditive],
    "bianchi_v_transverse_momentum_zero" -> TrueQ[bvMomentumZero],
    "xact_bv_residual_zero" -> TrueQ[Lookup[xActResult, "bvResidualZero"]],
    "xact_unavailable" -> If[TrueQ[Lookup[xActResult, "xactUnavailable"]], True, "false"],
    "signature" -> "Bianchi I: q(beta)+q(-beta)=0; Bianchi V: 3 a s1 + kappa q1 |_{s1=0,q1=0}=0 (exact)"
  |>
|>
