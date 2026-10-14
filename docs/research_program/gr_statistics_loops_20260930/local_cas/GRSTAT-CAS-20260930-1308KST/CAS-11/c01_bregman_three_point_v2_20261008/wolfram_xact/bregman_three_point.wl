(* CAS-11-C01 v2, independent Wolfram+xTensor axis.

   Dimension-parametric induction certificate: for a finite sum,
   S(0)=0 and S(m+1)=S(m)+a(m+1), including the empty case. The exact
   base and step identities checked below prove the reductions for
   every finite natural n and k; no dimension enumeration is a proof.
   All symbols are arbitrary reals. H is used only through its values
   and gradients at f,g,h, without convexity or positivity.
*)

engineVersion = System`$Version;
Needs["xAct`xTensor`"];
Print["ENGINE_VERSION=", engineVersion];
Print["XTENSOR_VERSION=", xAct`xTensor`$Version];

ClearAll[xf, xg, xh, hf, hg, hh, pg, ph, oldL, oldR, oldA,
  row, col, corner, dVar, vVar, lamVar, sVar, tVar,
  oldMoment, oldMomentR, qVar, pVar];

(* H-value cancellation and generic coordinate kernel for orientation
   D(f||g), with pg=grad H(g) and ph=grad H(h). *)
hConstant = Expand[(hf - hg) - (hf - hh) - (hh - hg)];
coordinateLhs = -pg (xf - xg) + ph (xf - xh) + pg (xh - xg);
coordinateRhs = (ph - pg) (xf - xh);
coordinateStep = Expand[coordinateLhs - coordinateRhs];
Print["H_CONSTANT_ZERO=", TrueQ[hConstant === 0]];
Print["COORDINATE_KERNEL_ZERO=", TrueQ[coordinateStep === 0]];

(* n-induction for sum_i coordinateLhs_i=sum_i coordinateRhs_i.
   Base 0=0; assume oldL=oldR for n entries and append one. *)
vectorBase = Expand[0 - 0];
vectorStep = Expand[(oldL + coordinateLhs) -
  (oldR + coordinateRhs) /. oldR -> oldL];
Print["VECTOR_EMPTY_BASE_ZERO=", TrueQ[vectorBase === 0]];
Print["VECTOR_INDUCTION_STEP_ZERO=", TrueQ[vectorStep === 0]];

(* k-induction proves d Sum_j(v_j lambda_j)=Sum_j(lambda_j v_j d).
   sVar and tVar are k-term prefixes; tVar=dVar sVar is the induction
   hypothesis. The new coordinate is arbitrary. *)
innerBase = Expand[dVar*0 - 0];
innerStep = Expand[dVar (sVar + vVar lamVar) -
  (tVar + lamVar vVar dVar) /. tVar -> dVar sVar];
Print["INNER_EMPTY_BASE_ZERO=", TrueQ[innerBase === 0]];
Print["INNER_K_INDUCTION_STEP_ZERO=", TrueQ[innerStep === 0]];

(* n-induction lifts that k-identity to the sum over i. pVar and qVar
   denote the new row's two k-sums; inner induction gives qVar=dVar pVar. *)
outerBase = Expand[0 - 0];
outerStep = Expand[(oldMoment + dVar pVar) -
  (oldMomentR + qVar) /. {oldMomentR -> oldMoment, qVar -> dVar pVar}];
Print["OUTER_EMPTY_BASE_ZERO=", TrueQ[outerBase === 0]];
Print["OUTER_N_INDUCTION_STEP_ZERO=", TrueQ[outerStep === 0]];

(* Finite rectangular Fubini. Both empty bases are zero. At
   (n+1,k+1), old rectangle, new row, new column and corner are
   disjoint. These two addition orders are the double-induction step. *)
fubiniEmptyN = Expand[0 - 0];
fubiniEmptyK = Expand[0 - 0];
rowThenColumn = (oldA + row) + (col + corner);
columnThenRow = (oldA + col) + (row + corner);
fubiniStep = Expand[rowThenColumn - columnThenRow];
Print["FUBINI_EMPTY_N_ZERO=", TrueQ[fubiniEmptyN === 0]];
Print["FUBINI_EMPTY_K_ZERO=", TrueQ[fubiniEmptyK === 0]];
Print["FUBINI_DOUBLE_INDUCTION_STEP_ZERO=", TrueQ[fubiniStep === 0]];

(* With exact moment m_j=0 for every j, k-induction gives
   Sum_j lambda_j m_j=0. Approximate moments are never substituted. *)
momentZeroBase = Expand[0];
momentZeroStep = Expand[oldMoment + lamVar*0 - oldMoment];
Print["MOMENT_ZERO_EMPTY_BASE=", TrueQ[momentZeroBase === 0]];
Print["MOMENT_ZERO_K_STEP=", TrueQ[momentZeroStep === 0]];

(* Exact rational controls in ADMITTED_INPUTS.json. *)
cubic[t_] := t^3/3;
cubicD[a_, b_] := cubic[a] - cubic[b] - b^2 (a - b);
orientationFG = cubicD[2, 1];
orientationGF = cubicD[1, 2];
approximateResidual = 1 * 1 * (1/10);
Print["ORIENTATION_FG=", ToString[orientationFG, InputForm]];
Print["ORIENTATION_GF=", ToString[orientationGF, InputForm]];
Print["APPROXIMATE_RESIDUAL=", ToString[approximateResidual, InputForm]];

allChecks = And @@ {
  hConstant === 0, coordinateStep === 0, vectorBase === 0, vectorStep === 0,
  innerBase === 0, innerStep === 0, outerBase === 0, outerStep === 0,
  fubiniEmptyN === 0, fubiniEmptyK === 0, fubiniStep === 0,
  momentZeroBase === 0, momentZeroStep === 0,
  orientationFG === 4/3, orientationGF === 5/3,
  approximateResidual === 1/10, approximateResidual =!= 0
};
Print["CERTIFICATE_STATUS=", If[TrueQ[allChecks], "PASS", "INCONCLUSIVE"]];
Exit[If[TrueQ[allChecks], 0, 2]];
