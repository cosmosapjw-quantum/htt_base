! R84 source-conditional three-band NVSS sky-axis occupancy and beta score.
! C row-major n(N,3), w(N,3), score(N,3,3), axes(M,3).
! Output (M,3,4) per axis/band: [F, dF_dbeta_x,y,z].
! All inputs are source-computed within ring-profiling coefficients, not raw counts.
! Parallel only across independent axes, each axis Kahan accumulates fixed
! source pixel order. This is NOT a physical Lorentz radio-map transfer.
subroutine htt_p4_masked_source_score_v1(n,m,directions,axes,w,score,threads,output,status) &
 bind(C,name="htt_p4_masked_source_score_v1")
 use iso_c_binding,only:c_int64_t,c_int32_t,c_int,c_double
 implicit none
 integer(c_int64_t),value,intent(in)::n,m
 integer(c_int32_t),value,intent(in)::threads
 real(c_double),intent(in)::directions(*),axes(*),w(*),score(*)
 real(c_double),intent(out)::output(*)
 integer(c_int),intent(out)::status
 integer(c_int64_t)::ia,i
 integer::j,k,idx
 real(c_double)::acc(12),err(12),val(12),delta,tmp,proj
 status=0
 if(n<=0.or.m<=0.or.threads<1.or.threads>32)then
   status=1
   return
 end if
 !$omp parallel do default(shared) private(ia,i,j,k,idx,acc,err,val,delta,tmp,proj) &
 !$omp schedule(static) num_threads(threads)
 do ia=0_c_int64_t,m-1_c_int64_t
   acc=0.0_c_double
   err=0.0_c_double
   do i=0_c_int64_t,n-1_c_int64_t
     proj=directions(3*i+1)*axes(3*ia+1)+ &
          directions(3*i+2)*axes(3*ia+2)+ &
          directions(3*i+3)*axes(3*ia+3)
     if(proj>0.0_c_double)then
       do j=0,2
         val(4*j+1)=w(3*i+j+1)
         val(4*j+2)=score(9*i+3*j+1)
         val(4*j+3)=score(9*i+3*j+2)
         val(4*j+4)=score(9*i+3*j+3)
       end do
       do k=1,12
         delta=val(k)-err(k)
         tmp=acc(k)+delta
         err(k)=(tmp-acc(k))-delta
         acc(k)=tmp
       end do
     endif
   end do
   do k=1,12
     output(12*ia+k)=acc(k)
   end do
 end do
 !$omp end parallel do
end subroutine htt_p4_masked_source_score_v1
