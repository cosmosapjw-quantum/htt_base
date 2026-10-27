Clear[b,mu,r,p,mm,aa,bb,qc,jc];
dop=1/(Sqrt[1/(1-b^2)](1-b mu));
mom3=FullSimplify[Integrate[dop^3/2,{mu,-1,1},Assumptions->0<b<1],Assumptions->0<b<1];
mom4=FullSimplify[Integrate[dop^4/2,{mu,-1,1},Assumptions->0<b<1],Assumptions->0<b<1];
ratio=FullSimplify[mom3^4/mom4^3,Assumptions->0<b<1];
aa=(r^4-1)/(r^3-1); bb=1-aa; mstar=-4bb/aa;
rmin=256 r^3(r^2+r+1)^3/(27(r^3+r^2+r+1)^4);
pstar=(3r^2+2r+1)/((r^3+r^2+r+1)(r^2+r+1));
eqs={FullSimplify[ratio-(1-b^2)/(1+b^2/3)^3,Assumptions->0<b<1],
FullSimplify[(1+pstar(r^3-1))-mstar,Assumptions->r>1],
FullSimplify[((1+pstar(r^3-1))^4/(1+pstar(r^4-1))^3)-rmin,Assumptions->r>1],
FullSimplify[(D[mm^4/(aa mm+bb)^3,mm]/.mm->mstar),Assumptions->r>1]};
qc=2Zeta[3]^4/(27Zeta[4]^3); jc=4Zeta[2]/Zeta[3]-3Zeta[3]/Zeta[4];
{eqs,mom3,mom4,Normal[Series[Log[ratio],{b,0,4}]],
Normal[Series[Log[rmin/.r->1+s],{s,0,3}]],N[{qc,jc,-2(123/100000)^2/jc},16]}
