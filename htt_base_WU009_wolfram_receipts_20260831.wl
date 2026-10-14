
(* htt_base PMG-WU-009 finite-dimensional algebra receipts
   Date: 2026-08-31
   This script checks reconstructed algebraic identities. It is not an xAct
   replay of the unavailable original P01-P27 dossier. *)

ClearAll["Global`*"];

Print["1. Krylov/Vandermonde"];
v = {x1, x2, x3};
K = Transpose[{v, {l1 x1, l2 x2, l3 x3},
                  {l1^2 x1, l2^2 x2, l3^2 x3}}];
Print[Factor[Det[K]]];

Print["2. Tracefree Cayley-Hamilton and cubic discriminant"];
vals = {a, b, -a - b};
p[k_] := Total[vals^k];
Print[FullSimplify[Table[
  vals[[i]]^3 - (p[2]/2) vals[[i]] - p[3]/3, {i, 3}]]];
Print[Factor[p[3]^2 - p[2]^3/6]];

Print["3. Moment Gram determinant"];
m3 = q2 m1/2 + q3 m0/3;
m4 = q2 m2/2 + q3 m1/3;
gram = {{m0,m1,m2},{m1,m2,m3},{m2,m3,m4}};
Print[Factor[Det[gram]]];

Print["4. STF3 boost response identity"];
Q = {{q11,q12,q13},{q12,q22,q23},{q13,q23,-q11-q22}};
beta = {b1,b2,b3};
qb = Q.beta;
U = Table[
  beta[[aa]] Q[[bb,cc]] + beta[[bb]] Q[[aa,cc]]
  + beta[[cc]] Q[[aa,bb]]
  - (2/5) (KroneckerDelta[aa,bb] qb[[cc]]
          + KroneckerDelta[aa,cc] qb[[bb]]
          + KroneckerDelta[bb,cc] qb[[aa]]),
  {aa,3},{bb,3},{cc,3}];
contraction = Table[
  Sum[U[[aa,bb,cc]] Q[[bb,cc]],{bb,3},{cc,3}],{aa,3}];
q2Q = Tr[Q.Q];
Print[FullSimplify[contraction - (q2Q beta + (6/5) Q.Q.beta)]];
normU = Sum[U[[aa,bb,cc]]^2,{aa,3},{bb,3},{cc,3}];
Print[FullSimplify[
  normU - (3 q2Q beta.beta + (18/5) beta.(Q.Q).beta)]];

Print["5. Sharp response condition number"];
kappa[t_] := (16 t^2 + 22 t + 16)/(10 t^2 + 10 t + 16);
Print[Factor[D[kappa[t], t]]];
Print[{kappa[4], kappa[1], Limit[kappa[t],t->Infinity]}];
Print[Maximize[{Max[
    (Total[{aa,bb,-aa-bb}^2] + (6/5){aa,bb,-aa-bb}^2)]/
  Min[(Total[{aa,bb,-aa-bb}^2] + (6/5){aa,bb,-aa-bb}^2)],
  Total[{aa,bb,-aa-bb}^2] == 1}, {aa,bb}, Reals]];

Print["6. Angular factors l=2,3"];
qpoly = 3 Cos[th]^2 - 1;
qint = Integrate[qpoly^2 Sin[th],{th,0,Pi},{ph,0,2 Pi}];
opoly = Cos[th]^3 - (3/5) Cos[th];
oint = Integrate[opoly^2 Sin[th],{th,0,Pi},{ph,0,2 Pi}];
Print[{qint, qint/6, oint, oint/(2/5)}];

Print["7. Inverse-square Gaussian local singularity"];
Print[Assuming[{sigma>0, Element[mu,Reals]},
  Limit[y^2 Exp[-(y-mu)^2/(2 sigma^2)]/y^2, y->0]]];
