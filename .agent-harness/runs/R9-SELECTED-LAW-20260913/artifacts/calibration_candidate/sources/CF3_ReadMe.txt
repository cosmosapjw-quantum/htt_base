J/AJ/152/50              Cosmicflows-3 catalog (CF3)              (Tully+, 2016)
================================================================================
Cosmicflows-3.
    Tully R.B., Courtois H.M., Sorce J.G.
   <Astron. J., 152, 50-50 (2016)>
   =2016AJ....152...50T    (SIMBAD/NED BibCode)
================================================================================
ADC_Keywords: Clusters, galaxy ; Galaxy catalogs ; Velocity dispersion ;
              Space velocities ; Morphology ; Cross identifications
Keywords: catalogs - galaxies: distances and redshifts -
          large-scale structure of universe

Abstract:
    The Cosmicflows database of galaxy distances that in the second
    edition contained 8188 entries is now expanded to 17669 entries. The
    major additions are 2257 distances that we have derived from the
    correlation between galaxy rotation and luminosity with photometry at
    3.6{mu}m obtained with the Spitzer Space Telescope and 8885 distances
    based on the Fundamental Plane methodology from the Six Degree Field
    Galaxy Survey collaboration. There are minor augmentations to the Tip
    of the Red Giant Branch and Type Ia supernova compilations. A
    zero-point calibration of the supernova luminosities gives a value for
    the Hubble Constant of 76.2+/-3.4+/-2.7 (+/-rand.+/-sys.)km/s/Mpc.
    Alternatively, a restriction on the peculiar velocity monopole term
    representing global infall/outflow implies H_0_=75+/-2km/s/Mpc.

Description:
    Cosmicflows-3 is a compendium of galaxy distance that builds on two
    earlier releases (Tully et al. 2008, Cat. J/ApJ/676/184; Tully et al.
    2013, Cat. J/AJ/146/86) and draws on both original material and
    information from the literature.

    Table2 gives summary group information for 11508 nests, 1704 with two
    or more distances and 9804 singles. The Virgo Cluster (nest 100002)
    has the most galaxies with measured distances with 161. There are 125
    groups with 10 or more galaxies with distances. Table3 couples the
    individual and group information. In this table, a row is dedicated to
    each of the 17669 galaxies with distance measurements. The first 41
    columns provide information on the specific galaxy, including
    distances from alternative sources. Then the last 30 columns give
    information on the associated nest, drawn from Table2. The material in
    these latter columns is the same for every member of a given nest.

File Summary:
--------------------------------------------------------------------------------
 FileName    Lrecl    Records    Explanations
--------------------------------------------------------------------------------
ReadMe          80          .    This file
table2.dat     197      11508    Summary group properties
table3.dat     406      17669    Individual galaxy properties
--------------------------------------------------------------------------------

See also:
 VII/259 : 6dF galaxy survey final redshift release (Jones+, 2009)
 VII/237 : HYPERLEDA. I. Catalog of galaxies (Paturel+, 2003)
 VII/233 : The 2MASS Extended sources (IPAC/UMass, 2003-2006)
 VII/155 : Third Reference Cat. of Bright Galaxies (RC3) (de Vaucouleurs+ 1991)
 VII/84  : Groups of Galaxies. III. The CfA Survey (Geller+ 1983)
 VII/86  : Groups of Galaxies. I. Nearby Groups (Huchra+ 1982)
 J/AJ/149/171     : 2MASS galaxy group catalog (Tully, 2015)
 J/MNRAS/445/2677 : Peculiar velocities in 6dFGS (Springob+, 2014)
 J/MNRAS/443/1231 : 6dF Galaxy Survey: Fundamental Plane data (Campbell+, 2014)
 J/AJ/146/86      : Cosmicflows-2 catalog (Tully+, 2013)
 J/ApJS/199/26    : The 2MASS Redshift Survey (2MRS) (Huchra+, 2012)
 J/MNRAS/416/2840 : The 2M++ galaxy redshift catalogue (Lavaux+, 2011)
 J/MNRAS/412/2498 : Galaxy groups and clouds in local universe (Makarov+, 2011)
 J/AJ/138/332     : LEDA CMD/tip of the red giant branch (Jacobs+, 2009)
 J/ApJ/676/184    : Peculiar motion away from the Local Void (Tully+, 2008)
 J/ApJ/655/790    : Groups of galaxies in 2MASS survey (Crook+, 2007)
 http://edd.ifa.hawaii.edu/ : Extragalactic Distance Database

Byte-by-byte Description of file: table2.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label  Explanations
--------------------------------------------------------------------------------
   1-  6  I6    ---     Nest   [100001/400002]?=0 2MASS "nest" group
                                identification (Tully 2015, Cat. J/AJ/149/171)
   8- 10  I3    ---  o_<DM>    [1/161] Number of galaxies in group with distance
                                measures (N_d_^gp^)
  12- 16  F5.2  mag    <DM>    [18.4/38.5] Weighted average group distance
                                modulus (<{mu}>^gp^)
  18- 21  F4.2  mag  e_<DM>    [0.02/0.54] One standard deviation uncertainty
                                in <DM> ({epsilon}_{mu}_^gp^)
  23- 27  F5.1  Mpc    <Dist>  [0/494.3] Luminosity distance to group; weighted
                                average of distance moduli
  29- 33  A5    ---     Abell  Abell Cluster identification (ASxxx are
                                from the southern supplement list)
  35- 43  A9    ---     GName  Alternative name for group or cluster
  45- 47  I3    ---     Npv    [1/197] Number of galaxies in group with
                                positions and velocities in the 2MRS catalog
                                (Huchra et al. 2012, Cat. J/ApJS/199/26) (N_v_)
  49- 55  I7    ---     PGC1   [14/9003164] Principal Galaxies Catalog
                                identifier of brightest group member
  57- 62  F6.2  deg     GLON   Group Galactic longitude (Glon^gp^)
  64- 69  F6.2  deg     GLAT   Group Galactic latitude (Glat^gp^)
  71- 78  F8.4  deg     SGLON  Group Supergalactic longitude (SGL^gp^) (G1)
  80- 87  F8.4  deg     SGLAT  Group Supergalactic latitude (SGB^gp^) (G1)
  89- 93  F5.2  [Lsun]  logLKs [0/14.43] Log summed Ks luminosity of group
                                (LogL^gp^) (G2)
  95-100  F6.2  ---     CF     [0/118.1] Luminosity selection function
                                correction factor (cf)
 102-105  I4    km/s    sigP   [0/2303] Projected velocity dispersion
                                ({sigma}_p_) (G3)
 107-113  F7.4  Mpc     R2t    [0/84] Projected second turnaround radius
                                (R_2t_) (G4)
 115-119  I5    km/s   <HV>    [-376/29980] Group heliocentric velocity
                                (V_h_^gp^)
 121-125  I5    km/s   <Vgsr>  [-189/29883] Group velocity in Galactic standard
                                of rest (V_gsr_^gp^) (G5)
 127-131  I5    km/s   <Vls>   [-158/29882] Group velocity in Local Sheet
                                standard of rest (Tully et al. 2008,
                                Cat. J/ApJ/676/184) (V_ls_^gp^)
 133-137  I5    km/s   <Vcmb>  [-669/29820] Group velocity in CMB standard of
                                rest (Fixsen et al. 1996ApJ...473..576F)
                                (V_cmb_^gp^)
 139-143  I5    km/s   <Vcmba> [-668/32110] Group velocity in CMB standard of
                                rest, adjusted (V_mod_^gp^) (G6)
 145-148  I4    km/s    sigma  [0/2401]? RMS group velocity dispersion (V_rms_)
 150-158  F9.3  TMsun   Mvir   [0/29467] Group mass from virial theorem
                                (M_12_^bw^) (G7)
 160-169  F10.4 TMsun   Mlum   [0/24401] Group mass from luminosity
                                (M_12_^L^) (G8)
 171-174  I4    ---     LDC    [3/1538]?=0 Low density group identifier
                                (Crook et al. 2007, Cat. J/ApJ/655/790)
 176-179  I4    ---     HDC    [2/1258]?=0 High density group identifier
                                (Crook et al. 2007, Cat. J/ApJ/655/790)
 181-184  I4    ---     2M++   [0/4715]?=0 Group identifier from 2MASS++ catalog
                                (Lavaux & Hudson 2011, Cat. J/MNRAS/416/2840)
 186-192  I7    ---     MK2011 [0/5067059] Group identifier from MK2011 catalog
                                (Makarov & Karachentsev 2011,
                                Cat. J/MNRAS/412/2498) (M&K)
 194-197  I4    ---     Icnt   [0/2941]? Internal reference identifier
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table3.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label  Explanations
--------------------------------------------------------------------------------
   1-  7  I7    ---     PGC    [4/9003164] Principal Galaxies Catalog number
                                (Makarov et al. 2014A&A...570A..13M)
   9- 14  F6.2  Mpc     Dist   [0.05/517.7] Luminosity distance measurement
                                for the individual galaxy (d) (1)
      16  I1    ---   o_Dist   [1/7] Numbers of sources of distance measures
                                for the individual galaxy (N_d_)
  18- 22  F5.2  mag     DM     [18.4/38.6] Luminosity distance modulus for
                                the individual galaxy (<{mu}>) (1)
  24- 27  F4.2  mag   e_DM     [0.1/0.6] One standard deviation uncertainty
                                in DM ({epsilon}_{mu}_) (2)
  29- 41  A13   ---   r_Dist   Source of distance (3)
  43- 47  F5.2  mag     DM-CF2 [18.48/38.6]?=0 Distance Modulus from CF2 (Tully
                                et al. 2013, Cat. J/AJ/146/86) ({mu}_cf2_)
  49- 52  F4.2  mag   e_DM-CF2 [0.1/0.6]?=0 One standard deviation uncertainty
                                in DM-CF2 ({epsilon}^cf2^_{mu}_)
  54- 60  A7    ---     SN     Supernova identification
      62  I1    ---   o_SN     [1/5]?=0 Number of separate analyses of the
                                supernova (N_sn_)
  64- 68  F5.2  mag     DM-N   [30.73/38.5]?=0 Luminosity distance modulus of
                                supernova averaged over all contributions
                                ({mu}_sn_)
  70- 74  F5.2  mag     DM-I   [26.68/36.8]?=0 Luminosity distance modulus
                                determined from the Tully-Fisher correlation
                                using Spitzer [3.6] band photometry ({mu}_spit_)
  76- 79  F4.2  mag   e_DM-I   [0.45/0.54]?=0 One standard deviation uncertainty
                                in DM-I ({epsilon}^spit^_{mu}_)
                                (0.45 or 0.54) (4)
  81- 85  F5.2  mag     DM-P   [29.86/38.47]?=0 Luminosity distance modulus from
                                6dFGS (Springob et al. 2014,
                                Cat. J/MNRAS/445/2677) ({mu}_6df_) (5)
  87- 90  F4.2  mag   e_DM-P   [0.5]?=0 One standard deviation uncertainty in
                                DM-P ({epsilon}^6df^_{mu}_)
  92- 94  F3.1  ---     Mt     [0/4]? 6dFGS morphology type code (Campbell et
                                al. 2014, Cat. J/MNRAS/443/1231) (M_t_)
  96- 97  I2    h       RAh    Hour of Right Ascension (J2000)
  98- 99  I2    min     RAm    Minute of Right Ascension (J2000)
 100-103  F4.1  s       RAs    Second of Right Ascension (J2000)
     105  A1    ---     DE-    Sign of the Declination (J2000)
 106-107  I2    deg     DEd    Degree of Declination (J2000)
 108-109  I2    arcmin  DEm    Arcminute of Declination (J2000)
 110-111  I2    arcsec  DEs    Arcsecond of Declination (J2000)
 113-120  F8.4  deg     GLON   Galaxy Galactic longitude (Glon)
 122-129  F8.4  deg     GLAT   Galaxy Galactic latitude (Glat)
 131-138  F8.4  deg     SGLON  Galaxy Supergalactic longitude (SGL)
 140-147  F8.4  deg     SGLAT  Galaxy Supergalactic latitude (SGB)
 149-152  F4.1  ---     MType  [-5/10] Morphological type; RC3 numeric code
                                (Makarov et al. 2014A&A...570A..13M) (Ty)
 154-158  F5.3  mag     Ab     [0.019/8.8] Reddening at B band (Schlafly &
                                Finkbeiner 2011ApJ...737..103S) (A_sf_)
 160-164  F5.2  mag     Bmag   [0/22.1] Total B magnitude from LEDA (B_t_)
 166-170  F5.2  mag     Ksmag  [-1.8/18.8]?=0 2MASS Ks magnitude with
                                corrections from Lavaux & Hudson 2011
                                (Cat. J/MNRAS/416/2840) (K_s_)
 172-176  I5    km/s    HV     [-376/34770] Heliocentric Velocity (V_h_)
 178-182  I5    km/s    Vgsr   [-339/34591] Velocity in Galactic standard of
                                rest (V_gsr_) (G5)
 184-188  I5    km/s    Vls    [-373/34545] Velocity in Local Sheet standard
                                of rest (Tully et al. 2008, Cat. J/ApJ/676/184)
                                (V_ls_)
 190-194  I5    km/s    Vcmb   [-669/34755] Velocity in CMB standard of rest
                                (Fixsen et al. 1996ApJ...473..576F) (V_cmb_)
 196-200  I5    km/s    Vcmba  [-668/37849] Velocity in CMB standard of rest,
                                adjusted (V_mod_) (G6)
 202-211  A10   ---     Name   Galaxy common name
 213-218  I6    ---     Nest   [100001/400002]?=0 2MASS "nest" group
                                identification (Tully 2015, Cat. J/AJ/149/171)
 220-222  I3    ---  o_<DM>    [1/161] Number of galaxies in group with
                                distance measures (N_d_^gp^)
 224-228  F5.2  mag    <DM>    [18.4/38.5] Luminosity distance modulus to group;
                                weighted over all contributions (<{mu}>^gp^)
 230-233  F4.2  mag  e_<DM>    [0.02/0.54] One standard deviation uncertainty
                                in <DM> ({epsilon}^gp^_{mu}_)
 235-239  F5.1  Mpc    <Dist>  [0/494.3] Luminosity distance to group; weighted
                                average of distance moduli (d^gp^)
 241-245  A5    ---     Abell  Abell Cluster identification (ASxxx are from
                                the southern supplement list)
 247-255  A9    ---     GName  Alternative name for group or cluster
 257-259  I3    ---     Npv    [1/197] Number of galaxies in group with
                                positions and velocities in the 2MRS catalog
                                (Huchra et al. 2012, Cat. J/ApJS/199/26) (N_v_)
 261-267  I7    ---     PGC1   [14/9003164] Principal Galaxies Catalog
                                identifier of brightest group member
 269-274  F6.2  deg     GGLON  Group Galactic longitude (Glon^gp^)
 276-281  F6.2  deg     GGLAT  Group Galactic latitude (Glat^gp^)
 283-290  F8.4  deg     GSGLON Group Supergalactic longitude (SGL^gp^) (G1)
 292-299  F8.4  deg     GSGLAT Group Supergalactic latitude (SGB^gp^) (G1)
 301-305  F5.2 [Lsun]   logLKs [6.8/14.5]?=0 Log summed Ks luminosity of group
                                (LogL^gp^) (G2)
 307-312  F6.2  ---     CF     [1/118.1]? Luminosity selection function
                                correction factor (cf)
 314-317  I4    km/s    sigP   [0/2303]? Projected velocity dispersion
                                ({sigma}_p_) (G3)
 319-323  F5.3  Mpc     R2t    [0.024/6.3]?=0 Projected second turnaround
                                radius (R_2t_) (G4)
 325-329  I5    km/s   <HV>    [-376/29980] Group heliocentric velocity
                                (V_h_^gp^)
 331-335  I5    km/s   <Vgsr>  [-189/29883] Group velocity in Galactic
                                standard of rest (V_gsr_^gp^) (G5)
 337-341  I5    km/s   <Vls>   [-158/29882] Group velocity in Local Sheet
                                standard of rest (Tully et al. 2008,
                                Cat. J/ApJ/676/184) (V_ls_^gp^)
 343-347  I5    km/s   <Vcmb>  [-669/29820] Group velocity in CMB standard of
                                rest (Fixsen et al. 1996ApJ...473..576F)
                                (V_cmb_^gp^)
 349-353  I5    km/s   <Vcmba> [-668/32110] Group velocity in CMB standard of
                                rest, adjusted (V_mod_^gp^) (G6)
 355-358  I4    km/s    sigma  [0/2401]? Group velocity dispersion (V_rms_)
 360-368  F9.3  TMsun   Mvir   [0.013/29466.7]?=0 Group mass from virial
                                theorem (M_12_^bw^) (G7)
 370-378  F9.3  TMsun   Mlum   [0.001/24400.1]?=0 Group mass from luminosity
                                (M_12_^L^) (G8)
 380-383  I4    ---     LDC    [3/1538]?=0 Low density group identifier
                                (Crook et al. 2007, Cat. J/ApJ/655/790)
 385-388  I4    ---     HDC    [2/1258]?=0 High density group identifier
                                (Crook et al. 2007, Cat. J/ApJ/655/790)
 390-393  I4    ---     2M++   [0/4715]?=0 Group identifier from 2MASS++ catalog
                                (Lavaux & Hudson 2011, Cat. J/MNRAS/416/2840)
 395-401  I7    ---     MK2011 [0/5067059]?=0 Group identifier from MK2011
                                catalog (Makarov & Karachentsev 2011,
                                Cat. J/MNRAS/412/2498) (M&K)
 403-406  I4    ---     Icnt   [1/2941]?=0 Internal reference identifier
--------------------------------------------------------------------------------
Note (1): Weighted average if more than one source.
Note (2): Different from CF2 (Tully et al. 2013, Cat. J/AJ/146/86) entry where
     the fractional error in distance is quoted.
Note (3): Source of distance determinations is defined as follows:
     C = Cepheid Period-Luminosity Relation (PLR) distance;
     T = Tip of the Red Giant Branch (TRGB) distance from an HST observation and
         reduced in a standard way (Jacobs et al. 2009, Cat. J/AJ/138/332);
     L = Tip of the Red Giant Branch (TRGB) distance from literature;
     M = High quality miscellaneous (RR Lyr, Horizontal Branch, Eclipsing
         Binary, Maser) distance;
     S = Surface Brightness Fluctuation (SBF) measurement;
     N = Type Ia supernovae (SNIa) distance measurement in the host galaxy;
     H = Tully-Fisher relation (TFR) distance based on optical photometry,
         as reported in CF2 (Tully et al. 2013, Cat. J/AJ/146/86);
     I = Tully-Fisher relation (TFR) distance based on photometry at 3.6{mu}m
         with Spitzer Space Telescope;
     F = Fundamental Plane measurement from the ENEAR, EFAR, or SMAC experiments
         as reported in CF2 (Tully et al. 2013, Cat. J/AJ/146/86);
     P = Fundamental Plane measurement from 6dFGS, (Springob et al. 2014,
         Cat. J/MNRAS/445/2677).
Note (4): Standard deviation uncertainty is defined as follows:
     0.45 = From color corrected relation;
     0.54 = Color information lacking.
Note (5): Fundamental Plane with Cosmicflows-3 zero point.
--------------------------------------------------------------------------------

Global Notes:
Note (G1): Luminosity weighted by 2MASS K_s_ magnitude.
Note (G2): Log summed K_s_ luminosity of group is adjusted by correction factor
     for lost light (Tully 2015, Cat. J/AJ/149/171). Assumed distance given by
     group velocity <Vcmda> and H_0_=75.
Note (G3): Value anticipated by corrected intrinsic luminosity
     (Tully 2015AJ....149...54T).
Note (G4): Value anticipated by corrected intrinsic luminosity
     (Tully 2015AJ....149...54T). Assumed distance given by group velocity
     <Vcmda> and H_0_=75.
Note (G5): Velocity in Galactic standard of rest, assuming a circular velocity
     at Sun of 239km/s; total velocity 251km/s toward l=90,b=0
     (van der Marel et al. 2012ApJ...753....8V).
Note (G6): Velocity in CMB standard of rest adjusted in accordance with a
     cosmological model with {Omega}_matter_=0.27 and {Omega}_{Lambda}_=0.73.
Note (G7): Group mass from virial theorem with bi-weight dispersion and radius
     parameters (Tully 2015, Cat. J/AJ/149/171). Assumed distance given by group
     velocity <Vcmda> and H_0_=75.
Note (G8): Group mass based on corrected luminosity and M/L prescription
     (Tully 2015, Cat. J/AJ/149/171). Assumed distance given by group velocity
     <Vcmda> and H_0_=75.
--------------------------------------------------------------------------------

History:
    From electronic version of the journal

================================================================================
(End)                 Prepared by [AAS]; Sylvain Guehenneux [CDS]    31-Mar-2017
