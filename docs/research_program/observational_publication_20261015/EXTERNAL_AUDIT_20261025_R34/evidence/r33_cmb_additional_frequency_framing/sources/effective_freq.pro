pro effective_freq,beta,nu_center

; Calculates the effective center frequency of each WMAP band
; for diffuse emission (completely filling the beams) with
; specified brightness temperature spectral index beta,
; using parameters from Table 11 of Jarosik et al. 2003, ApJS,
; 145, 413.  The calculation is valid only for -3 < beta < 1.

; Updated 8/10/2012 to apply small correction for bandpass
; drift in K-V bands, so gives results appropriate for
; 9-year WMAP data.

; input 
; beta - brightness temperature spectral index (T ~ nu^beta)

; output
; nu_center - effective WMAP band center frequencies in GHz

nu_avg=[22.29,23.12,32.78,33.12,40.71,40.81,40.16,40.92,59.20,61.10,$
        61.61,60.63,93.60,93.18,93.49,94.27,92.36,93.32,94.24,93.09]

c1=-1.0e-3*[2.43,2.35,1.58,1.85,1.85,1.48,1.58,1.53,2.13,2.00,$
            1.95,2.12,2.02,1.69,1.47,1.37,1.35,1.30,1.67,1.58]

c2=1.0e-3*[2.78,2.83,1.75,2.06,2.10,1.70,1.78,1.78,2.20,2.23,$
           2.22,2.35,2.20,1.82,1.57,1.48,1.44,1.37,1.83,1.68]

; calculate frequency nu0 for which left side of eq (50) of radiometer
;  paper = 1

nu0 = nu_avg*(1.0 + c1*beta + c2*beta*beta)^(1./beta)

if (abs(beta) lt 0.01) then begin

 beta1 = 0.01
 beta2 = -0.01

 nu0_1 = nu_avg*(1.0 + c1*beta1 + c2*beta1*beta1)^(1./beta1)

 nu0_2 = nu_avg*(1.0 + c1*beta2 + c2*beta2*beta2)^(1./beta2)

 nu0 = (nu0_1 + nu0_2)/2.

endif 

; now average nu0 over radiometers for each channel

nu_center=fltarr(5)

nu_center(0) = 0.5*(nu0(0) + nu0(1))

nu_center(1) = 0.5*(nu0(2) + nu0(3))

nu_center(2) = 0.25*(total(nu0(4:7)))

nu_center(3) = 0.25*(total(nu0(8:11)))

nu_center(4) = 0.125*(total(nu0(12:19)))

drift_corr = [0.13, 0.12, 0.11, 0.06, 0]/100.

for i=0,4 do nu_center(i) = nu_center(i)/(1.+drift_corr(i))

end
