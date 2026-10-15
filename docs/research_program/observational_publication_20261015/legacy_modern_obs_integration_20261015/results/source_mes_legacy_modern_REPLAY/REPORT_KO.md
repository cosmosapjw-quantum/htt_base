# Original R2 Legacy MES vs modern PR124 geodesic vorticity channel

실제 Planck 같은 하늘 9개 처리 산출물의 동일 eps2/eps3를 두 원래 함수에 적용했다. Legacy 원본 R2 bounds.py/ssot.py는 source SHA로 고정해 R2 LegacyAdapter로 실제 로드했다.

두 공식의 shear Bsigma는 기계오차 내 동일하지만, old Bomega=(3/4)eps1+2eps2+(2/7)eps3와 modern geodesic Bomega=(10/3)eps1+(2/15)eps2는 다른 공식이다. eps1=0 가정에서 old/modern W2 upper-normalizer ratio range=[375.01965236365777, 379.21295797661935].

이 결과는 원래 legacy를 '오류'로 판정하거나 현대 theorem이 자동으로 물리적으로 옳다고 입증한 결과가 아니다. 프레임, 미분 가정, vorticity 정의, 교정/원전 일치가 검증되지 않았으므로 같은 물리 제약으로 합치지 않는다. 특히 legacy W2를 modern x/Q posterior의 추가 독립 likelihood나 동일한 normalizer로 넘기는 작업을 보류한다.
