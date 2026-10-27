(* Loop B; exact incoming-sky boost and second-order blackbody closure.
   Lightweight algebra only. No ODE/native Boltzmann solver. *)
Clear[b,dx,dy,dz,nx,ny,nz,t,gg,hh,x];
ga=1/Sqrt[1-t^2 b^2];
ni={nx,ny,ga(nz-t b)}/(ga(1-t b nz));
dop=1/(ga(1-t b nz));
temp=Normal[Series[dop(1+t {dx,dy,dz}.ni),{t,0,2}]];
ex=1+t(b nz+dx nx+dy ny+dz nz)+
 t^2(b^2 nz^2-b^2/2-b dz+2 b nz(dx nx+dy ny+dz nz));
br={0,0,b}; dr={dx,dy,dz};
mat=Outer[Times,br,dr]+Outer[Times,dr,br]-
 2/3(br.dr)IdentityMatrix[3];
jac=D[Flatten[mat],{{dx,dy,dz}}];
gram=Simplify[Transpose[jac].jac];
inv=Simplify[(IdentityMatrix[3]-DiagonalMatrix[{0,0,1/4}]).mat.br/b^2-dr];
ff=1/(Exp[x]-1); gf=-x D[ff,x];
hf=x^2 D[ff,{x,2}]+2 x D[ff,x];
checks={Simplify[temp-ex],gram,inv,
 Simplify[-x D[gf,x]-gf-hf],
 Simplify[hf/gf-(x Coth[x/2]-2)]};
checks
