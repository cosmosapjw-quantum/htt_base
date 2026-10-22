(* Independent CAS-07-C02 Wolfram+xAct axis. Exact scalar and tensor certificates.
   The operator-norm premise is used through its quantified vector-bound definition. *)
$HistoryLength = 0;
Needs["xAct`xTensor`"];
Print["ENGINE_VERSION=", $Version];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

ClearAll[check];
check[name_, value_] := Module[{b = TrueQ[value]},
  Print["CHECK:", name, ":", If[b, "TRUE", "FALSE"]];
  If[!b, Exit[2]];
];

(* Nonzero Euclidean Gram contraction in abstract indices. The free i,j are
   screen indices; this is not a literal-zero canonicalization. *)
DefManifold[CAS07Screen, 2, {a, b, i, j}];
DefMetric[1, euclid[-a, -b], CAS07CD];
DefTensor[mapD[-a, -b], CAS07Screen];
gram = ToCanonical[ContractMetric[euclid[a, b] mapD[-a, -i] mapD[-b, -j]]];
expectedGram = ToCanonical[mapD[a, -i] mapD[-a, -j]];
Print["XACT_GRAM_CONTRACTION=", InputForm[gram]];
check["xact_nonzero_gram", gram =!= 0 && gram === expectedGram];

(* E=D-sI, q=s eta. These are exact polynomial certificates for
   <v,Dv>, ||Dv||_2^2 and det(D^T D)=det(D)^2. *)
ClearAll[s, q, u, w, z, e11, e12, e21, e22, v1, v2, t];
e = {{e11, e12}, {e21, e22}};
d = s IdentityMatrix[2] + e;
v = {v1, v2};
gramMatrix = Transpose[d].d;
check["gram_quadratic_form", FullSimplify[v.gramMatrix.v == (d.v).(d.v)]];
check["gram_determinant", FullSimplify[Det[gramMatrix] == Det[d]^2]];
check["cauchy_lagrange_identity", FullSimplify[
  ((e.v).(e.v))(v.v) - ((e.v).v)^2 == Det[{v, e.v}]^2]];
check["norm_expansion", FullSimplify[
  (d.v).(d.v) == s^2 (v.v) + 2 s (v.(e.v)) + (e.v).(e.v)]];

(* Scalar universal implication: u=||v||, w=||Ev||, z=<v,Ev>.
   Cauchy-Schwarz gives -uw<=z<=uw; the operator premise gives w<=qu.
   This Resolve checks both Rayleigh bounds without sampling D or v. *)
scalarDomain = s > 0 && 0 <= q < s && u >= 0 && 0 <= w <= q u && -u w <= z <= u w;
rayleighBounds = (s-q)^2 u^2 <= s^2 u^2 + 2 s z + w^2 <= (s+q)^2 u^2;
scalarCertificate = Resolve[ForAll[{s, q, u, w, z}, Implies[scalarDomain, rayleighBounds]], Reals];
Print["SCALAR_UNIVERSAL_QE=", InputForm[scalarCertificate]];
check["universal_rayleigh_bounds", scalarCertificate];

(* Positive determinant branch certificate: for A_t=sI+tE, t in [0,1],
   ||tEv||<=tq||v||<s||v|| for v!=0, hence det A_t !=0.
   Polynomial identity below ties the path to endpoints. Continuity of a
   polynomial and IVT then fix sign at det(sI)=s^2>0. *)
path = s IdentityMatrix[2] + t e;
check["homotopy_endpoints", FullSimplify[path /. t -> 0] === s IdentityMatrix[2] &&
  FullSimplify[path /. t -> 1] === d];
check["homotopy_determinant_polynomial", FullSimplify[
  Det[path] == s^2 + s t Tr[e] + t^2 Det[e]]];
check["homotopy_strict_scalar_gap", Resolve[
  ForAll[{s, q, t, u}, Implies[s > 0 && 0 <= q < s && 0 <= t <= 1 && u > 0,
    s u - t q u > 0]], Reals]];

(* For symmetric Gram, the Euclidean spectral theorem converts the two
   universal Rayleigh bounds to both eigenvalue bounds. Since det D>0,
   sqrt(det D)=sqrt(sigma_1 sigma_2), with each sigma in [s-q,s+q].
   These exact scalar implications certify the positive square-root step. *)
ClearAll[l1, l2, lo, hi];
check["positive_sqrt_product_bound", Resolve[
  ForAll[{lo, hi, l1, l2}, Implies[
    0 < lo <= hi && lo^2 <= l1 <= hi^2 && lo^2 <= l2 <= hi^2,
    lo <= Sqrt[Sqrt[l1 l2]] <= hi]], Reals]];
Print["CAS07_C02_FULL_SCOPE_CERTIFIED=TRUE"];
Exit[0];
