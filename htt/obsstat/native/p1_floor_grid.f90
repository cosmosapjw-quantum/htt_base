! R82 conditional apparent anchor-floor 2048 coupled source contrast.
! Output C row-major (na,nf,3,3): strict>1, exact tie==1, weighted mean.
! Input q C contiguous row-major n×4, weights n, anchors na, floors nf.
subroutine htt_p1_floor_grid_v1(n,na,nf,q,w,anchors,floors,threads,out,status) &
 bind(C,name="htt_p1_floor_grid_v1")
 use iso_c_binding, only: c_int64_t,c_int32_t,c_int,c_double
 use, intrinsic :: ieee_arithmetic, only: ieee_is_finite
 implicit none
 integer(c_int64_t),value,intent(in)::n,na,nf
 integer(c_int32_t),value,intent(in)::threads
 real(c_double),intent(in)::q(*),w(*),anchors(*),floors(*)
 real(c_double),intent(out)::out(*)
 integer(c_int),intent(out)::status
 integer(c_int64_t)::ix,ia,ifr,i
 integer::j,k
 real(c_double)::values(3,3),comp(3,3),summand(3,3)
 real(c_double)::cut,denom,ratio,tt,ss,wi
 status=0
 if(n<=0 .or. na<=0 .or. nf<=0 .or. threads<1)then
   status=1;return
 end if
 !$omp parallel do default(shared) private(ix,ia,ifr,i,j,k,values,comp,summand,cut,denom,ratio,tt,ss,wi) &
 !$omp schedule(static) num_threads(threads)
 do ix=0_c_int64_t,na*nf-1_c_int64_t
   ia=ix/nf
   ifr=mod(ix,nf)
   cut=anchors(ia+1)*floors(ifr+1)
   values=0.0_c_double
   comp=0.0_c_double
   do i=0_c_int64_t,n-1_c_int64_t
     wi=w(i+1)
     denom=max(q(4*i+1),cut)
     do j=1,3
       ratio=max(q(4*i+j+1),cut)/denom
       summand(j,1)=0.0_c_double
       summand(j,2)=0.0_c_double
       if(ratio>1.0_c_double)summand(j,1)=wi
       if(ratio==1.0_c_double)summand(j,2)=wi
       summand(j,3)=wi*ratio
     end do
     do j=1,3
       do k=1,3
         tt=summand(j,k)-comp(j,k)
         ss=values(j,k)+tt
         comp(j,k)=(ss-values(j,k))-tt
         values(j,k)=ss
       end do
     end do
   end do
   do j=1,3
     do k=1,3
       out(ix*9+(j-1)*3+k)=values(j,k)
     end do
   end do
 end do
 !$omp end parallel do
end subroutine htt_p1_floor_grid_v1
