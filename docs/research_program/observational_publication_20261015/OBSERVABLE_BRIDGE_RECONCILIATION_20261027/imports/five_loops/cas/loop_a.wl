(* LOOP A: exact STF identities. Spatial orthonormal triad; unit propagation e.
   This is a finite algebra check, not xAct or a four-axis CAS verdict. *)
ClearAll["Global`*"];
id = IdentityMatrix[3]; e = {x,y,z};
s = {{a,b,d},{b,f,g},{d,g,-a-f}};
stf[m_] := (m+Transpose[m])/2-Tr[m] id/3;
outer = Outer[Times,e,e]; pi = outer-id/3;
e4 = Table[e[[i]] e[[j]] e[[k]] e[[l]]-
 (id[[i,j]] e[[k]] e[[l]]+id[[i,k]] e[[j]] e[[l]]+
  id[[i,l]] e[[j]] e[[k]]+id[[j,k]] e[[i]] e[[l]]+
  id[[j,l]] e[[i]] e[[k]]+id[[k,l]] e[[i]] e[[j]])/7+
 (id[[i,j]] id[[k,l]]+id[[i,k]] id[[j,l]]+id[[i,l]] id[[j,k]])/35,
 {i,3},{j,3},{k,3},{l,3}];
contract = Table[Sum[e4[[i,j,k,l]] s[[k,l]],{k,3},{l,3}],{i,3},{j,3}];
l = 8 s/15+10 stf[s.pi]/7-contract;
ldirect = 2 stf[s.outer]-stf[outer] (e.s.e);
reduce[p_] := Last[PolynomialReduce[Expand[p],{x^2+y^2+z^2-1},{x,y,z}]];
identityRemainder = Map[reduce,l-ldirect,{2}];
energyRemainder = reduce[Tr[s.l]-(2 (s.e).(s.e)-(e.s.e)^2)];
wrongCoefficientRemainder = Map[reduce,(8 s/15+2 stf[s.pi]/7-contract)-ldirect,{2}];
(* Exact quadrupolar distribution rho/(4 Pi)(1+b0(z^2-1/3)). *)
pibar = DiagonalMatrix[{-2,-2,4}] rho b0/45;
sxz = {{0,0,k},{0,0,0},{k,0,0}};
lxz = FullSimplify[8 rho sxz/15+10 stf[sxz.pibar]/7];
commutator = FullSimplify[pibar.sxz-sxz.pibar];
(* Pure-dipole absolute Planck-temperature test, d0 in z direction. *)
rhoRatio = Integrate[(1+d0 mu)^4,{mu,-1,1}]/2;
piZZRatio = Integrate[(1+d0 mu)^4 (mu^2-1/3),{mu,-1,1}]/2;
planckCheck = FullSimplify[piZZRatio-(4/5+4 d0^2/35) (2 d0^2/3)];
<|"identity_remainder"->identityRemainder,"energy_remainder"->energyRemainder,
 "wrong_coefficient_is_identically_zero"->And@@(#===0& /@Flatten[wrongCoefficientRemainder]),
 "quadrupole_xz_operator"->lxz,"pi_s_commutator"->commutator,
 "dipole_planck_rho_ratio"->rhoRatio,"dipole_planck_piZZ_ratio"->piZZRatio,
 "dipole_planck_check"->planckCheck|>
(* B_e <= Identity on STF2: by rotational covariance choose e=z. *)
upperGap = FullSimplify[Tr[s.s]-(2 (s.{0,0,1}).(s.{0,0,1})-
 ({0,0,1}.s.{0,0,1})^2)];
(* Expected: a^2+2 b^2+f^2 >=0 for real entries. *)
upperGap
