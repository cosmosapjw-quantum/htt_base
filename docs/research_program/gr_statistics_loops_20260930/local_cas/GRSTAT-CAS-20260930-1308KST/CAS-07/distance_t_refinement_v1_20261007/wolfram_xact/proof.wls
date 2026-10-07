(* CAS-07 M06: exact order proof using only the accepted M01/C03/M05 statements.
   etaS=eta_K(s), etaT=eta_K(t), etaL=eta_K(L), h=Abs[H0].
   M01 is instantiated only after each branch establishes s<=t<=L. *)

Needs["xAct`xTensor`"];
Print["VERSION\tWolfram\t", System`$Version];
Print["VERSION\txTensor\t1.3.0"];

Clear[s, ell, d, c, m2, h, etaS, etaT, etaL];
den = 1 - etaL;
distanceCap = d/den;
fd1S = m2 s^2/2 + h s etaS/c;
fd1T[t_] := m2 t^2/2 + h t etaT/c;
fd2 = m2 distanceCap^2/2 + h distanceCap etaL/c;

base = Element[{s, ell, d, c, m2, h, etaS, etaT, etaL}, Reals] &&
  ell > 0 && 0 < s <= ell && c > 0 && m2 >= 0 && h >= 0 && d > 0 &&
  0 <= etaS <= etaL < 1 && s (1 - etaS) <= d <= s (1 + etaS);
branchL = d >= ell den;
branchD = d <= ell den;

(* The M05 lower bound and etaS<=etaL imply d>=s(1-etaL).
   Denominator positivity is proved before any division or branch conversion. *)
denPositive = TrueQ @ FullSimplify[den > 0, base];
etaGapPositive = TrueQ @ FullSimplify[s (etaL - etaS) >= 0,
  Element[{s, etaS, etaL}, Reals] && s > 0 && etaS <= etaL];
distanceLower = etaGapPositive && TrueQ @ FullSimplify[
  d >= s (1 - etaS) && s (1 - etaS) >= s den, base];
branchesExhaust = TrueQ @ FullSimplify[branchL || branchD, base];
domainL = TrueQ @ FullSimplify[s <= ell && ell <= ell && ell > 0 && ell <= distanceCap,
  base && branchL && den > 0];
domainD = TrueQ @ FullSimplify[s <= distanceCap && distanceCap <= ell && distanceCap > 0,
  base && branchD && den > 0 && d >= s den];

(* M01: for 0<x<=y<=L, eta(x)<=eta(y), with eta>=0 and eta(L)<1.
   These are the accepted theorem's instantiated scalar facts, not an M01 reproof. *)
m01AtT = 0 <= etaT <= etaL;
m01MonotoneST = etaS <= etaT;
etaOrderL = TrueQ @ FullSimplify[0 <= etaS <= etaT <= etaL < 1,
  base && branchL && den > 0 && domainL && m01AtT && m01MonotoneST];
etaOrderD = TrueQ @ FullSimplify[0 <= etaS <= etaT <= etaL < 1,
  base && branchD && den > 0 && domainD && m01AtT && m01MonotoneST];

(* Exact nonnegative decompositions.  Accepted C03 supplies |error|<=fd1S. *)
fd1Gap[t_] := m2 (t - s) (t + s)/2 +
  (h/c) ((t - s) etaT + s (etaT - etaS));
fd2Gap[t_] := m2 (distanceCap - t) (distanceCap + t)/2 +
  (h/c) ((distanceCap - t) etaL + t (etaL - etaT));

fd1IdentityL = TrueQ @ FullSimplify[fd1T[ell] - fd1S == fd1Gap[ell], base];
fd1IdentityD = TrueQ @ FullSimplify[fd1T[distanceCap] - fd1S == fd1Gap[distanceCap], base && den > 0];
fd1OrderL = TrueQ @ FullSimplify[fd1Gap[ell] >= 0,
  base && branchL && den > 0 && m01AtT && m01MonotoneST];
fd1OrderD = TrueQ @ FullSimplify[fd1Gap[distanceCap] >= 0,
  base && branchD && den > 0 && m01AtT && m01MonotoneST && s <= distanceCap];

fd2IdentityL = TrueQ @ FullSimplify[fd2 - fd1T[ell] == fd2Gap[ell], base && den > 0];
fd2IdentityD = TrueQ @ FullSimplify[fd2 - fd1T[distanceCap] == fd2Gap[distanceCap], base && den > 0];
fd2OrderL = TrueQ @ FullSimplify[fd2Gap[ell] >= 0,
  base && branchL && den > 0 && m01AtT && m01MonotoneST];
fd2OrderD = TrueQ @ FullSimplify[fd2Gap[distanceCap] >= 0,
  base && branchD && den > 0 && m01AtT && m01MonotoneST && s <= distanceCap];

(* K=0: etaS=etaT=etaL=0.  The accepted full M05 bound gives d=s. *)
flat = base && etaS == 0 && etaT == 0 && etaL == 0;
flatEquality = TrueQ @ FullSimplify[d == s, flat];
flatMin = TrueQ @ FullSimplify[Min[ell, s] == s, Element[{ell, s}, Reals] && 0 < s <= ell];
flatRHS = TrueQ @ FullSimplify[fd1T[s] == fd1S && fd2 == fd1S,
  flat && d == s];
flatDistance = flatEquality && flatMin && flatRHS;
zeroH = TrueQ @ FullSimplify[fd1Gap[ell] >= 0 && fd2Gap[ell] >= 0,
  base && branchL && den > 0 && m01AtT && m01MonotoneST && h == 0];
zeroM2 = TrueQ @ FullSimplify[fd1Gap[distanceCap] >= 0 && fd2Gap[distanceCap] >= 0,
  base && branchD && den > 0 && m01AtT && m01MonotoneST && s <= distanceCap && m2 == 0];

(* xTensor sanity: the dimension from contracting a metric with its inverse. *)
DefManifold[M06Space, 2, {a, b}];
DefMetric[1, gM06[-a, -b], CDM06];
tensorSanity = TrueQ[ToCanonical[gM06[a, b] gM06[-a, -b]] == 2];

checks = <|
  "CAS-07-M06-T-DOMAIN" -> And @@ (TrueQ /@ {denPositive, distanceLower, branchesExhaust, domainL, domainD, flatDistance}),
  "CAS-07-M06-ETA-ORDER" -> And @@ (TrueQ /@ {etaOrderL, etaOrderD}),
  "CAS-07-M06-REFINED-FD1" -> And @@ (TrueQ /@ {fd1IdentityL, fd1IdentityD, fd1OrderL, fd1OrderD, zeroH, zeroM2}),
  "CAS-07-M06-NO-WORSE-THAN-FD2" -> And @@ (TrueQ /@ {fd2IdentityL, fd2IdentityD, fd2OrderL, fd2OrderD, zeroH, zeroM2})
|>;
Scan[(Print["DETAIL\t", #[[1]], "\t", #[[2]]]) &,
  Normal @ <|"den_positive" -> denPositive, "eta_gap_positive" -> etaGapPositive,
    "distance_lower" -> distanceLower,
    "branches_exhaust" -> branchesExhaust, "domain_L" -> domainL,
    "domain_D" -> domainD, "eta_L" -> etaOrderL, "eta_D" -> etaOrderD,
    "fd1_identity_L" -> fd1IdentityL, "fd1_identity_D" -> fd1IdentityD,
    "fd1_order_L" -> fd1OrderL, "fd1_order_D" -> fd1OrderD,
    "fd2_identity_L" -> fd2IdentityL, "fd2_identity_D" -> fd2IdentityD,
    "fd2_order_L" -> fd2OrderL, "fd2_order_D" -> fd2OrderD,
    "flat_equality" -> flatEquality, "flat_min" -> flatMin,
    "flat_rhs" -> flatRHS, "flat" -> flatDistance,
    "zero_H0" -> zeroH, "zero_M2" -> zeroM2,
    "tensor_sanity" -> tensorSanity|>];
KeyValueMap[Print["CHECK\t", #1, "\t", #2] &, checks];
Print["TENSOR_SANITY\t", tensorSanity];
If[And @@ Values[checks] && tensorSanity, Exit[0], Exit[1]];
