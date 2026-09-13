J/A+A/602/A100    Merging groups and clusters from the SDSS data (Tempel+, 2017)
================================================================================
Merging groups and clusters of galaxies from the SDSS data.
The catalogue of groups and potentially merging systems.
    Tempel E., Tuvikene T., Kipper R., Libeskind N.I.
    <Astron. Astrophys. 602, A100 (2017)>
    =2017A&A...602A.100T        (SIMBAD/NED BibCode)
================================================================================
ADC_Keywords: Clusters, galaxy ; Fundamental catalog ; Galaxy catalogs
Keywords: Catalogs - galaxies: groups: general - galaxies: clusters: general

Abstract:
    Galaxy groups and clusters are the main tools to test cosmological
    models and to study the environmental effect of galaxy formation. This
    work aims to provide a catalogue of galaxy groups/clusters and
    potentially merging systems based on the SDSS main galaxy survey. We
    identify galaxy groups and clusters using the modified
    friends-of-friends (FoF) group finder that is designed specifically
    for flux-limited galaxy surveys. FoF group membership is refined by
    multimodality analysis to find subgroups and by using the group virial
    radius and escape velocity to expose unbound galaxies. We look for
    merging systems by comparing distances between group centres with
    group radii. The analysis results in a catalogue of 88 662 galaxy
    groups with at least two members. Among them are 6873 systems with at
    least 6 members which we consider as more reliable groups. We find 498
    group mergers with up to six groups.

Description:
    This work is based on catalogue data from the SDSS DR12 (Eisenstein et
    al., 2011AJ....142...72E; Alam et al., 2015ApJS..219...12A). We have
    selected galaxies only from the main contiguous area of the survey
    (the Legacy Survey). The final galaxy sample contains 584449
    entries.

File Summary:
--------------------------------------------------------------------------------
 FileName      Lrecl  Records   Explanations
--------------------------------------------------------------------------------
ReadMe            80        .   This file
table1.dat       659   584449   Catalog of galaxies
table2.dat       295    88662   Catalog of galaxy groups
table3.dat        50      498   Catalog of merging systems
--------------------------------------------------------------------------------

See also:
  J/A+A/525/A157 : SDSS automated morphology classification
                                                        (Huertas-Company+, 2011)

Byte-by-byte Description of file: table1.dat
--------------------------------------------------------------------------------
   Bytes Format Units     Label    Explanations
--------------------------------------------------------------------------------
   1-  6  I6    ---       GalID    [1/584449] Unique galaxy identification
   8- 26  I19   ---       specID   ?=0 SDSS DR10 spectroscopic objectID
                                    (0=missing)
  28- 46  I19   ---       objID    SDSS DR10 photometric objectID
  48- 53  I6    ---       GroupID  [0/88662] Group/cluster id
                                    (0=isolated galaxy)
  57- 59  I3    ---       Ngal     [1/254] Richness of group galaxy belongs
  63- 65  I3    ---       Rank     [1/254] Luminosity rank within its group
  67- 76  F10.6 Mpc       Dist.g   Comoving distance to group centre (G1)
  78- 89  F12.9 ---       zobs     [-0.01/0.21] Observed redshift
  91-102  F12.9 ---       zcmb     [0/0.2] Redshift (CMB rest frame)
 104-115  F12.9 ---     e_zobs     Uncertainty of the redshift
 117-126  F10.6 Mpc       Dist     Comoving distance (G1)
 128-137  F10.6 Mpc       Distcor  Comoving distance, after suppressing the
                                    "finger-of-god" effect (G1)
 139-152  F14.9 deg       RAdeg    Right ascension (J2000)
 154-167  F14.9 deg       DEdeg    Declination (J2000)
 169-182  F14.9 deg       GLON     Galactic longitude
 184-197  F14.9 deg       GLAT     Galactic latitude
 199-212  F14.9 deg       SGLON    Supergalactic longitude
 214-227  F14.9 deg       SGLAT    Supergalactic latitude
 229-242  F14.9 deg       lambda   SDSS survey coordinate, {lambda}
 244-257  F14.9 deg       eta      SDSS survey coordinate, {eta}
 259-269  F11.6 Mpc       Xpos     Cartesian x coordinate (G1)
 271-281  F11.6 Mpc       Ypos     Cartesian y coordinate (G1)
 283-293  F11.6 Mpc       Zpos     Cartesian z coordinate (G1)
 295-305  F11.6 mag       umag     Extinction corrected Petrosian u magnitude
 307-317  F11.6 mag       gmag     Extinction corrected Petrosian g magnitude
 319-329  F11.6 mag       rmag     Extinction corrected Petrosian r magnitude
 331-341  F11.6 mag       imag     Extinction corrected Petrosian i magnitude
 343-353  F11.6 mag       zmag     Extinction corrected Petrosian z magnitude
 355-365  F11.6 mag       uMAG     Absolute magnitude u-band, k+e-corrected (G1)
 367-377  F11.6 mag       gMAG     Absolute magnitude g-band, k+e-corrected (G1)
 379-389  F11.6 mag       rMAG     Absolute magnitude r-band, k+e-corrected (G1)
 391-401  F11.6 mag       iMAG     Absolute magnitude i-band, k+e-corrected (G1)
 403-413  F11.6 mag       zMAG     Absolute magnitude z-band, k+e-corrected (G1)
 415-425  F11.6 mag       k+e.u    k+e-correction (u filter)
 427-437  F11.6 mag       k+e.g    k+e-correction (g filter)
 439-449  F11.6 mag       k+e.r    k+e-correction (r filter)
 451-461  F11.6 mag       k+e.i    k+e-correction (i filter)
 463-473  F11.6 mag       k+e.z    k+e-correction (z filter)
 475-485  F11.6 mag       ext.u    Galactic extinction (u filter)
 487-497  F11.6 mag       ext.g    Galactic extinction (g filter)
 499-509  F11.6 mag       ext.r    Galactic extinction (r filter)
 511-521  F11.6 mag       ext.i    Galactic extinction (i filter)
 523-533  F11.6 mag       ext.z    Galactic extinction (z filter)
 536-546  E11.6 10+10Lsun Lr       Observed luminosity in the r-band (G1)
 548-556  F9.6  ---       w        [1/9.1] Weight factor for the galaxy (1)
 558-565  F8.5  ---       pE       [0/1] Probability of early-type (2)
 567-574  F8.5  ---       pS0      [0/1] Probability of S0 galaxy
 576-583  F8.5  ---       pSa      [0/1] Probability of Sab galaxy
 585-592  F8.5  ---       pSc      [0/1] Probability of Scd galaxy
 594-603  F10.6 Mpc       Dist.e   Distance from survey mask border (G1)
 605-617  F13.8 ---       Den1     Environmental density at scale=1.5Mpc (G2)
 619-631  F13.8 ---       Den2     Environmental density at scale=3Mpc (G2)
 633-645  F13.8 ---       Den4     Environmental density at scale=6Mpc (G2)
 647-659  F13.8 ---       Den8     Environmental density at scale=10Mpc (G2)
--------------------------------------------------------------------------------
Note (1): times Lr was used to calculate the luminosity density field
Note (2): Data is taken from Huertas-Company et al., 2011, Cat. J/A+A/525/A157.
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table2.dat
--------------------------------------------------------------------------------
   Bytes Format Units     Label       Explanations
--------------------------------------------------------------------------------
   1-  6  I6    ---       GroupID     [1/88662] Group/cluster ID
   8- 12  I5    ---       Ngal        [2/254] Richness
  14- 27  F14.9 deg       RAdeg       Right ascension (J2000)
  29- 42  F14.9 deg       DEdeg       Declination (J2000)
  44- 57  F14.9 deg       lambda      SDSS survey coordinate, {lambda}
  59- 72  F14.9 deg       eta         SDSS survey coordinate, {eta}
  74- 84  F11.6 Mpc       Xpos        Cartesian x coordinate (G1)
  86- 96  F11.6 Mpc       Ypos        Cartesian y coordinate (G1)
  98-108  F11.6 Mpc       Zpos        Cartesian z coordinate (G1)
 110-120  F11.8 ---       zcmb        [0/0.2] Redshift (CMB rest frame)
 122-131  F10.6 Mpc       Dist.c      Comoving distance to group center (G1)
 133-144  F12.6 km/s      sig.v       rms radial velocity deviation {sigma}_V_
 146-155  F10.6 Mpc       sig.sky     rms deviation of the distance in plane of
                                       sky from group center {sigma}_sky_ (G1)
 157-166  F10.6 Mpc       Rmax        Maximum radius of the group (G1)
 168-179  E12.5 10+12Msun M200        Estimated mass of the NFW profile group
 181-192  E12.5 Mpc       R200        Radius, where mean density is 200 the
                                       Universe average density
 194-205  E12.5 10+10Lsun Lrgroup     Observed luminosity (G1)
 207-216  F10.6 ---       w           [1/9.1] Weight factor for the group
 218-230  F13.8 ---       Den1        Environment density: 1.5Mpc (G2)
 232-244  F13.8 ---       Den2        Environment density: 3Mpc (G2)
 246-258  F13.8 ---       Den4        Environment density: 6Mpc (G2)
 260-272  F13.8 ---       Den8        Environment density: 10Mpc (G2)
 274-283  F10.6 Mpc       DnearestCl  Distance to the nearest cluster
 285-290  I6    ---       IDnearestCl ID of the nearest cluster
 292-295  I4    ---       IDmerger    ID of the group in merger catalog
--------------------------------------------------------------------------------

Byte-by-byte Description of file: table3.dat
--------------------------------------------------------------------------------
   Bytes Format Units   Label     Explanations
--------------------------------------------------------------------------------
   1-  5  I5    ---     ID        Merging system ID
   7-  8  I2    ---     N         Number of mergers in the system
  10- 15  I6    ---     IDgr1     The 1st ID of the merging group
  17- 22  I6    ---     IDgr2     The 2nd ID of the merging group
  24- 29  I6    ---     IDgr3     The 3rd ID of the merging group
  31- 36  I6    ---     IDgr4     The 4th ID of the merging group
  38- 43  I6    ---     IDgr5     The 5th ID of the merging group
  45- 50  I6    ---     IDgr6     The 6th ID of the merging group
--------------------------------------------------------------------------------

Global Notes:
Note (G1): the cosmology assumes H_0_=67.8km/s/Mpc, {Omega}_m_=0.308 and
     {Omega}_{Lambda}_=0.692. Distances are Mpc, masses in M{sun},
     luminosities in L{sun}, and absolute magnitudes in mag.
Note (G2): Normalised environmental density of the galaxy for the
     smoothing scale of a=1.5,3,6,10Mpc.
--------------------------------------------------------------------------------

Acknowledgements:
    Elmo Tempel, elmo.tempel(at)to.ee

================================================================================
(End)   Rain Kipper, Elmo Tempel [TO], Patricia Vannier [CDS]    06-Apr-2017
