! R79: optional ISO_C_BINDING streaming hemisphere moments (Gaussian/source
! geometry only). Input dirs[i,3] must be contiguous C row-major, unit length.
! Output two blocks of ten: sum_w, sum_wn(3), sum_wnn(xx,xy,xz,yy,yz,zz).
subroutine htt_hemisphere_moments_v1(n, dirs, weights, axis, moments, status) &
    bind(C, name="htt_hemisphere_moments_v1")
  use iso_c_binding, only: c_int64_t, c_double, c_int
  implicit none
  integer(c_int64_t), value, intent(in) :: n
  real(c_double), intent(in) :: dirs(*), weights(*), axis(3)
  real(c_double), intent(out) :: moments(20)
  integer(c_int), intent(out) :: status
  real(c_double) :: acc(20), compensation(20), vals(10)
  real(c_double) :: x, y, z, w, projection, kahan_y, temporary
  integer(c_int64_t) :: i
  integer :: j, target, base
  acc = 0.0_c_double
  compensation = 0.0_c_double
  moments = 0.0_c_double
  status = 0_c_int
  if (n <= 0_c_int64_t) then
    status = 1_c_int
    return
  end if
  do i = 0_c_int64_t, n-1_c_int64_t
    x = dirs(3*i+1)
    y = dirs(3*i+2)
    z = dirs(3*i+3)
    w = weights(i+1)
    if (w < 0.0_c_double) then
      status = 2_c_int
      return
    end if
    projection = x*axis(1) + y*axis(2) + z*axis(3)
    if (projection > 0.0_c_double) then
      base=10
    else
      base=0
    end if
    vals(1)=w
    vals(2)=w*x
    vals(3)=w*y
    vals(4)=w*z
    vals(5)=w*x*x
    vals(6)=w*x*y
    vals(7)=w*x*z
    vals(8)=w*y*y
    vals(9)=w*y*z
    vals(10)=w*z*z
    do j=1,10
      target=base+j
      kahan_y=vals(j)-compensation(target)
      temporary=acc(target)+kahan_y
      compensation(target)=(temporary-acc(target))-kahan_y
      acc(target)=temporary
    end do
  end do
  moments=acc
end subroutine htt_hemisphere_moments_v1
