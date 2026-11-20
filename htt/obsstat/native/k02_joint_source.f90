! R85 original K02 12D 4-window source sufficient statistics.
! Exact CF4 method-profiled working likelihood, N selected 35970 groups.
! F_j = X^T diag(w_j) X; b_j=X^T diag(w_j)cz;
! raw G_jk = X^T diag(w_j w_k sigma_i^2) X.
! C row-major X(n,12), W(n,4), y(n), sigma(n);
! F(4,12,12), b(4,12), G(48,48). Outputs are raw info
! and NOT a full physical PV/selection covariance. All source loops fixed order.
subroutine htt_r85_k02_joint_source_v1(n,X,w,y,sigma,threads,F,score,G,status) &
 bind(C,name="htt_r85_k02_joint_source_v1")
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
 real(c_double)::local(12,12),corr(12,12),right(12),rcorr(12)
 real(c_double)::z,xi,yi,d,dd,wa,wb
 status=0_c_int
 if(n<20.or.threads<1.or.threads>32)then
    status=1_c_int
    return
 endif
 !$omp parallel do default(shared) private(j,i,a,b,local,corr,right,rcorr,z,xi,yi,d,dd) &
 !$omp schedule(static) num_threads(threads)
 do j=0,3
    local=0.0_c_double
    corr=0.0_c_double
    right=0.0_c_double
    rcorr=0.0_c_double
    do i=0_c_int64_t,n-1_c_int64_t
      z=w(4*i+j+1)
      yi=y(i+1)
      do a=1,12
        xi=X(12*i+a)
        d=z*xi*yi-rcorr(a)
        dd=right(a)+d
        rcorr(a)=(dd-right(a))-d
        right(a)=dd
        do b=a,12
          d=z*xi*X(12*i+b)-corr(a,b)
          dd=local(a,b)+d
          corr(a,b)=(dd-local(a,b))-d
          local(a,b)=dd
        enddo
      enddo
    enddo
    do a=1,12
      score(12*j+a)=right(a)
      do b=a,12
        F(j*144+(a-1)*12+b)=local(a,b)
        F(j*144+(b-1)*12+a)=local(a,b)
      enddo
    enddo
 enddo
 !$omp end parallel do
 !$omp parallel do default(shared) private(t,j,k,i,a,b,local,corr,wa,wb,xi,z,d,dd) &
 !$omp schedule(static) num_threads(threads)
 do t=1,10
   j=jj(t)
   k=kk(t)
   local=0.0_c_double
   corr=0.0_c_double
   do i=0_c_int64_t,n-1_c_int64_t
     wa=w(4*i+j+1)
     wb=w(4*i+k+1)
     z=wa*wb*sigma(i+1)**2
     do a=1,12
       xi=X(12*i+a)
       do b=a,12
         d=z*xi*X(12*i+b)-corr(a,b)
         dd=local(a,b)+d
         corr(a,b)=(dd-local(a,b))-d
         local(a,b)=dd
       enddo
     enddo
   enddo
   do a=1,12
     do b=a,12
       G((12*j+a-1)*48+12*k+b)=local(a,b)
       G((12*j+b-1)*48+12*k+a)=local(a,b)
       G((12*k+a-1)*48+12*j+b)=local(a,b)
       G((12*k+b-1)*48+12*j+a)=local(a,b)
     enddo
   enddo
 enddo
 !$omp end parallel do
end subroutine htt_r85_k02_joint_source_v1
