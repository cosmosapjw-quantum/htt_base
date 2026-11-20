! R81 PHY-01: batched exact source-hemisphere weighted raw moments.
! axes are independent, OpenMP over axes with deterministic per-axis order.
! C row-major n x 3 directions and m x 3 axes, output row-major m x 2 x 11.
! Each hemisphere: [sum_w, sum_w n(3), sum_w nn(6), source_count].
subroutine htt_multi_hemi_v1(n,m,directions,weights,axes,threads,output,status) &
  bind(C,name="htt_multi_hemi_v1")
  use iso_c_binding, only: c_int64_t,c_double,c_int,c_int32_t
  implicit none
  integer(c_int64_t),value,intent(in)::n,m
  integer(c_int32_t),value,intent(in)::threads
  real(c_double),intent(in)::directions(*),weights(*),axes(*)
  real(c_double),intent(out)::output(*)
  integer(c_int),intent(out)::status
  integer(c_int64_t)::i,j
  integer::k,off
  real(c_double)::acc(22),comp(22),vals(11),x,y,z,w,q,t,u
  status=0_c_int
  if(n<=0 .or. m<=0 .or. threads<=0)then
    status=1_c_int
    return
  endif
  !$omp parallel do default(shared) private(j,i,k,off,acc,comp,vals,x,y,z,w,q,t,u) schedule(static) num_threads(threads)
  do j=0_c_int64_t,m-1_c_int64_t
    acc=0.0_c_double
    comp=0.0_c_double
    do i=0_c_int64_t,n-1_c_int64_t
      x=directions(3*i+1);y=directions(3*i+2);z=directions(3*i+3)
      w=weights(i+1)
      q=x*axes(3*j+1)+y*axes(3*j+2)+z*axes(3*j+3)
      if(q>0.0_c_double)then
        off=11
      else
        off=0
      endif
      vals(1)=w
      vals(2)=w*x;vals(3)=w*y;vals(4)=w*z
      vals(5)=w*x*x;vals(6)=w*x*y;vals(7)=w*x*z
      vals(8)=w*y*y;vals(9)=w*y*z;vals(10)=w*z*z
      vals(11)=1.0_c_double
      do k=1,11
        t=vals(k)-comp(off+k)
        u=acc(off+k)+t
        comp(off+k)=(u-acc(off+k))-t
        acc(off+k)=u
      end do
    end do
    do k=1,22
      output(22*j+k)=acc(k)
    end do
  end do
  !$omp end parallel do
end subroutine htt_multi_hemi_v1
