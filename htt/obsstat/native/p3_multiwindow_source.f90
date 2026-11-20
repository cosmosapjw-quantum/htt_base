! R83 source-coherent 4-window H03 information and unprofiled cross-blocks.
! Source inputs X(N,9), W(N,4), y(N), sigma(N) are C-contiguous row major.
! Output F(4,9,9), score(4,9), G(36,36) are C-contiguous row major.
! G_jk = X^T diag(w_j*w_k*sigma^2) X; covariance is F_j^-1 G_jk F_k^-1.
! No cross-source PV/calibration or real physical H(z,n) inference.
subroutine htt_p3_multiwindow_source_v1(n,X,w,y,sigma,threads,F,score,G,status) &
 bind(C,name="htt_p3_multiwindow_source_v1")
 use iso_c_binding,only:c_int64_t,c_int32_t,c_int,c_double
 implicit none
 integer(c_int64_t),value,intent(in)::n
 integer(c_int32_t),value,intent(in)::threads
 real(c_double),intent(in)::X(*),w(*),y(*),sigma(*)
 real(c_double),intent(out)::F(*),score(*),G(*)
 integer(c_int),intent(out)::status
 integer(c_int64_t)::i
 integer::j,k,a,b,t
 integer,parameter::jj(10)=(/0,0,0,0,1,1,1,2,2,3/)
 integer,parameter::kk(10)=(/0,1,2,3,1,2,3,2,3,3/)
 real(c_double)::local(9,9),right(9),v,wa,wb,si,yi,xi
 status=0_c_int
 if(n<=9.or.threads<1.or.threads>32)then
    status=1_c_int
    return
 end if
 !$omp parallel do default(shared) private(j,i,a,b,local,right,v,yi,xi) schedule(static) num_threads(threads)
 do j=0,3
   local=0.0_c_double
   right=0.0_c_double
   do i=0_c_int64_t,n-1_c_int64_t
     v=w(4*i+j+1)
     yi=y(i+1)
     do a=1,9
       xi=X(9*i+a)
       right(a)=right(a)+v*xi*yi
       do b=a,9
         local(a,b)=local(a,b)+v*xi*X(9*i+b)
       end do
     end do
   end do
   do a=1,9
     score(9*j+a)=right(a)
     do b=a,9
       F(j*81+(a-1)*9+b)=local(a,b)
       F(j*81+(b-1)*9+a)=local(a,b)
     end do
   end do
 end do
 !$omp end parallel do
 !$omp parallel do default(shared) private(t,j,k,i,a,b,local,wa,wb,si,v,xi) schedule(static) num_threads(threads)
 do t=1,10
   j=jj(t)
   k=kk(t)
   local=0.0_c_double
   do i=0_c_int64_t,n-1_c_int64_t
     wa=w(4*i+j+1)
     wb=w(4*i+k+1)
     si=sigma(i+1)
     v=wa*wb*si*si
     do a=1,9
       xi=X(9*i+a)
       do b=a,9
         local(a,b)=local(a,b)+v*xi*X(9*i+b)
       end do
     end do
   end do
   do a=1,9
     do b=a,9
       G((j*9+a-1)*36+(k*9+b))=local(a,b)
       G((j*9+b-1)*36+(k*9+a))=local(a,b)
       G((k*9+a-1)*36+(j*9+b))=local(a,b)
       G((k*9+b-1)*36+(j*9+a))=local(a,b)
     end do
   end do
 end do
 !$omp end parallel do
end subroutine htt_p3_multiwindow_source_v1
