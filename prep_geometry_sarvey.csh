#!/bin/csh -f
#
if ($#argv < 1) then
   echo ""
   echo "Usage: geometry_sarvey.csh path/to/topo"
   echo ""
   echo " Creates grd files for latitude, longitude, incidence, azimuth and slantRange"
   echo " topo folder must contain: trans.dat, topo_ra.grd and master.PRM"
   echo " topo_ra.grd and trans.dat is produced by dem2topo_ra.csh"
   echo ""
   echo "Example: geometry_sarvey.csh path/to/topo"
   echo ""
   exit 1
endif

cd $1

set trans = "trans.dat"
set toporad = "topo_ra.grd"
set masterPRM = "master.PRM"

if (! -e $masterPRM ) then
    echo "$masterPRM does not exist. Please check"
    exit 1
endif

if (! -e "dem.grd" ) then
    echo "dem-grd does not exist. Run make_dem.csh"
    exit 1
endif

# || or, && and
if (! -e $toporad || ! -e $trans) then
    echo ""
    echo "$toporad or $trans do not exist. Run dem2topo_ra.csh"
    echo ""
    dem2topo_ra.csh $masterPRM dem.grd 0
endif


# NOTE: trans.dat is binary: (r a topo lon lat)

# Parameters from toporad
set x0 = `gmt grdinfo $toporad -C | awk '{print $2}'`
set x1 = `gmt grdinfo $toporad -C | awk '{print $3}'`
set y0 = `gmt grdinfo $toporad -C | awk '{print $4}'`
set y1 = `gmt grdinfo $toporad -C | awk '{print $5}'`

echo ""
echo "GETTING TOPO_RA FULL RESOLUTION"
echo ""
# Getting Topo rad
set toporad_full = 'topo_ra_full.grd'
gmt grdsample $toporad -G$toporad_full -I1/1 -R$x0/$x1/$y0/$y1 -V

# Getting longitude and latitude
echo ""
echo "OBTAINING LONGITUDE AND LATITUDE"
echo ""
gmt surface $trans -i0,1,3 -b15d -I1/1 -R$x0/$x1/$y0/$y1 -r -T.50 -Glongitude.grd -V
gmt surface $trans -i0,1,4 -b15d -I1/1 -R$x0/$x1/$y0/$y1 -r -T.50 -Glatitude.grd -V


echo ""
echo "CALCULATION OF LOOK VECTORS ENU"
echo ""
# Use SAT_look for getting look_E, look_N, look_U
gmt gmtconvert $trans -o3,4,2 -bi5d > llt.xyz
SAT_look $masterPRM < llt.xyz > topo.lltn

# Block median / mean - Look angles (ENU) come with low sampling and in lon lat coordinates
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,3 -r -V -GlE_ll.grd
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,4 -r -V -GlN_ll.grd
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,5 -r -V -GlU_ll.grd

echo ""
echo "PROJECT LOOK VECTOR BACK TO RADAR COORDINATES"
echo ""
# Back to radar coordinates
proj_ll2ra.csh trans.dat lE_ll.grd lE_ra.grd
proj_ll2ra.csh trans.dat lN_ll.grd lN_ra.grd
proj_ll2ra.csh trans.dat lU_ll.grd lU_ra.grd

echo ""
echo "INTERPOLATION OF LOOK VECTORS ENU"
echo ""
# Making interpolation with surface based on data from previous step 
# This step can take a bit of a while, depending of the extension of your data
gmt grd2xyz lE_ra.grd|gmt surface -I1/1 -R$x0/$x1/$y0/$y1 -T.5 -GlookE.grd -r -V
gmt grd2xyz lN_ra.grd|gmt surface -I1/1 -R$x0/$x1/$y0/$y1 -T.5 -GlookN.grd -r -V
gmt grd2xyz lU_ra.grd|gmt surface -I1/1 -R$x0/$x1/$y0/$y1 -T.5 -GlookU.grd -r -V

echo ""
echo "CALCULATING INCIDENCE AND AZIMUTH ANGLES"
echo ""
# Incidence angle
gmt grdmath lookE.grd lookN.grd HYPOT lookU.grd ATAN2 R2D = incidence.grd # In degrees
gmt grdmath lookE.grd lookN.grd HYPOT lookU.grd ATAN2 = inc.grd -V

# Azimuth angle
gmt grdmath lookE.grd lookN.grd ATAN2 R2D = azimuth.grd

echo ""
echo "CALCULATING SLANT RANGE"
echo ""
# Calculation of Slant Range from law of sines using height, earth radius, incidence and look angles
# https://en.wikipedia.org/wiki/Law_of_sines
set earthRadius = `grep earth_radius $masterPRM|awk -F= '{print $2}'`
set SC_height = `grep -w SC_height $masterPRM|awk -F= '{print $2}'` # Spacecraft (SC) height
set totalHeight = `echo "$earthRadius + $SC_height"|bc`

gmt grdmath $totalHeight PI inc.grd SUB SIN DIV = R2.grd -V
gmt grdmath $earthRadius R2.grd DIV ASIN = lookAngle.grd -V
gmt grdmath inc.grd lookAngle.grd SUB = rangeAngle.grd -V
gmt grdmath rangeAngle.grd SIN R2.grd MUL = slantRange.grd -V

# clean up
rm rap
rm l*_ll.grd
rm l*_ra.grd
rm llt.xyz
rm R2.grd lookAngle.grd rangeAngle.grd
rm ll*
rm topo.lltn
rm look*.grd
rm inc.grd
cd ..