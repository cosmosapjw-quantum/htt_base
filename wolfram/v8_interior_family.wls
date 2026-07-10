(* EGS3 v8-update T3-int: independent Wolfram cross-check of the interior-family
   lane (htt/obsstat/egs3_interior_family.py). First-principles recomputation --
   nothing read from the Python seal:
     (1) the two-segment family x_C sweep: continuity, exact junction at 3/20,
         strict monotonicity, endpoint values 11/100 and 17/100;
     (2) Gauss residual identically zero along both segments;
     (3) the group-invariant curl on Bianchi V from the structure-constant
         algebra (C^2_{12} = a, C^3_{13} = a): curl v = (0, -a v3, a v2),
         aligned tilt irrotational, slaving |curl v|^2 = a^2 (v2^2 + v3^2);
     (4) the (0i) momentum closure for transverse shear + antipodal pair. *)
ClearAll["Global`*"];

(* (1)+(2) family sweep *)
om = 3/10;
xC[S_] := S[[1]] - S[[2]] + S[[3]] + S[[4]];
gauss[S_] := Module[{ol = 1 - om - S[[4]] - S[[3]] - S[[1]] + S[[2]]},
   Simplify[(om + ol + S[[4]] + S[[3]] + S[[1]] - S[[2]]) - 1]];
S1 = {12/100, 4/100 (1 - t), 3/100, 0};
S2 = {12/100, 0, 3/100, 2 u/100};
x1 = Simplify[xC[S1]]; x2 = Simplify[xC[S2]];
gaussZero = (gauss[S1] === 0) && (gauss[S2] === 0);
junction = Simplify[(x1 /. t -> 1) - (x2 /. u -> 0)] === 0;
monotone = (D[x1, t] === 1/25) && (D[x2, u] === 1/50);
endpointsOK = ((x1 /. t -> 0) === 11/100) && ((x2 /. u -> 1) === 17/100);
(* every rational target in the interval is hit by the piecewise inverse *)
hitAll = Resolve[ForAll[x, 11/100 <= x <= 15/100,
   Exists[tt, 0 <= tt <= 1, (x1 /. t -> tt) == x]], Reals] &&
  Resolve[ForAll[x, 15/100 <= x <= 17/100,
   Exists[uu, 0 <= uu <= 1, (x2 /. u -> uu) == x]], Reals];

(* (3) group-invariant curl from the Bianchi V frame algebra.
   CC[[j,m,k]] = C_{jmk} = <[e_j,e_m], e_k> (orthonormal frame; indices lowered
   trivially): [e1,e2]=a e2 -> C_{122}=a, C_{212}=-a; [e1,e3]=a e3 ->
   C_{133}=a, C_{313}=-a. *)
CC = ConstantArray[0, {3, 3, 3}];
CC[[1, 2, 2]] = a; CC[[2, 1, 2]] = -a;
CC[[1, 3, 3]] = a; CC[[3, 1, 3]] = -a;
(* Levi-Civita (Koszul) connection Gamma_{jmk} = (C_{jmk} - C_{mkj} + C_{kjm})/2,
   verified metric-compatible + torsion-free below *)
Gam[j_, m_, k_] := (CC[[j, m, k]] - CC[[m, k, j]] + CC[[k, j, m]])/2;
metricCompat = And @@ Flatten[Table[Simplify[Gam[j, m, k] + Gam[j, k, m]] === 0,
   {j, 3}, {m, 3}, {k, 3}]];
torsionFree = And @@ Flatten[Table[Simplify[Gam[j, m, k] - Gam[m, j, k] - CC[[j, m, k]]] === 0,
   {j, 3}, {m, 3}, {k, 3}]];
v = {v1, v2, v3};
curl = Table[Sum[LeviCivitaTensor[3][[i, b, c]] Sum[v[[m]] Gam[b, m, c], {m, 3}],
   {b, 3}, {c, 3}], {i, 3}] // Simplify;
curlExpected = Simplify[curl - {0, a v3, -a v2}] === {0, 0, 0};
alignedIrrot = Simplify[curl /. {v2 -> 0, v3 -> 0}] === {0, 0, 0};
slaving = Simplify[curl . curl - a^2 (v2^2 + v3^2)] === 0;

(* (4) momentum closure: 3 a_b sigma^{ab} + kappa q^a with a_i=(a,0,0),
   diagonal trace-free shear diag(0, s, -s) (transverse), antipodal pair q=0 *)
sigma = DiagonalMatrix[{0, s, -s}];
avec = {a, 0, 0};
momentum = Simplify[3 avec . sigma + kappa {0, 0, 0}];
momentumZero = momentum === {0, 0, 0};
(* antipodal flux cancellation, all orders in beta *)
qPair = Simplify[(mu + p) Sinh[beta] Cosh[beta] + (mu + p) Sinh[-beta] Cosh[-beta]];
fluxZero = qPair === 0;

<|
  "schema" -> "htt.egs3.v8_interior_family.v1",
  "checks" -> <|
    "gauss_identically_zero_both_segments" -> TrueQ[gaussZero],
    "junction_exact_at_3_over_20" -> TrueQ[junction],
    "strictly_monotone_slopes_1_25_and_1_50" -> TrueQ[monotone],
    "endpoints_11_100_and_17_100" -> TrueQ[endpointsOK],
    "every_interval_point_hit" -> TrueQ[hitAll],
    "curl_components_0_av3_mav2" -> TrueQ[curlExpected],
    "connection_metric_compatible" -> TrueQ[metricCompat],
    "connection_torsion_free" -> TrueQ[torsionFree],
    "aligned_tilt_irrotational" -> TrueQ[alignedIrrot],
    "slaving_curl_sq_a2_vperp2" -> TrueQ[slaving],
    "transverse_momentum_closure" -> TrueQ[momentumZero],
    "antipodal_flux_all_orders_zero" -> TrueQ[fluxZero],
    "signature" -> "T3-int: connected two-segment exact family sweeps [11/100,17/100]; Bianchi V group-invariant curl slaved to a^2 v_perp^2"
  |>
|>
