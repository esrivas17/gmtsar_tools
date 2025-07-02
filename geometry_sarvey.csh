#!/bin/csh -f
#
if ($#argv < 2) then
   echo ""
   echo "Usage: geometry_sarvey.csh path/to/topo"
   echo ""
   echo " Creates grd files for latitude, longitude, incidence, azimuth and slantRange"
   echo " topo folder must contain: trans.dat, topo_ra.grd and master.PRM"
   echo ""
   echo "Example: geometry_sarvey.csh path/to/topo"
   echo ""
   exit 1
endif

cd $1

set trans = "trans.dat"
set toporad = "topo_ra.grd"
set masterPRM = "master.PRM"

foreach f ($trans $toporad $masterPRM)
    if (! -e $f ) then
        echo "$f does not exist"
    endif
end


# NOTE: trans.dat is binary: (r a topo lon lat)

# Parameters from toporad
set x0 = `gmt grdinfo $toporad -C | awk '{print $2}'`
set x1 = `gmt grdinfo $toporad -C | awk '{print $3}'`
set y0 = `gmt grdinfo $toporad -C | awk '{print $4}'`
set y1 = `gmt grdinfo $toporad -C | awk '{print $5}'`

# Getting Height
set toporad_full = 'topo_ra_full.grd'
gmt grdsample $toporad -G$toporad_full -I1/1 -R$x0/$x1/$y0/$y1

# Getting longitude and latitude
gmt surface $trans -i0,1,3 -b15d -I1/1 -R$x0/$x1/$y0/$y1 -T.50 -Glongitude.grd
gmt surface $trans -i0,1,4 -b15d -I1/1 -R$x0/$x1/$y0/$y1 -T.50 -Glatitude.grd

# Use SAT_look for getting look_E, look_N, look_U
gmt gmtconvert trans.dat -o3,4,2 -bi5d > llt.txt
SAT_look $masterPRM -bod < llt.xyz > topo.lltn 

# Block median / mean - Look angles (ENU) come with low sampling and in lon lat coordinates
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,3 -r -V -GlE_ll.grd
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,4 -r -V -GlN_ll.grd
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,5 -r -V -GlU_ll.grd

# Back to radar coordinates
proj_ll2ra.csh trans.dat lE_ll.grd lE_ra.grd
proj_ll2ra.csh trans.dat lN_ll.grd lN_ra.grd
proj_ll2ra.csh trans.dat lU_ll.grd lU_ra.grd

# Making interpolation with surface based on data from previous step 
# This step can take a bit of a while, depending of the extension of your data
gmt grd2xyz lE_ra.grd|gmt surface -I1/1 -R$x0/$x1/$y0/$y1 -T.5 -GlookE.grd
gmt grd2xyz lN_ra.grd|gmt surface -I1/1 -R$x0/$x1/$y0/$y1 -T.5 -GlookN.grd
gmt grd2xyz lU_ra.grd|gmt surface -I1/1 -R$x0/$x1/$y0/$y1 -T.5 -GlookU.grd

# Incidence angle
gmt grdmath lookE.grd lookN.grd HYPOT lookU.grd ATAN2 R2D = incdeg.grd
gmt grdmath lookE.grd lookN.grd HYPOT lookU.grd ATAN2 = inc.grd

# Azimuth angle
gmt grdmath lookE.grd lookN.grd ATAN2 R2D = azideg.grd
gmt grdmath lookE.grd lookN.grd ATAN2 = azi.grd

# Calculation of Slant Range from law of sines using height, earth radius, incidence and look angles
set earthRadius = `grep earth_radius $masterPRM|awk -F= '{print $1}'`
set SC_height = `grep SC_height $masterPRM|awk -F= '{print $1}'` # Spacecraft (SC) height
set totalHeight = `echo "$earthRadius + $SC_height"|bc`

gmt grdmath $totalHeight PI inc.grd SUB SIN DIV = R2.grd
gmt grdmath $earth_radius R2.grd DIV ASIN = lookAngle.grd
gmt grdmath inc.grd lookAngle.grd SUB = rangeAngle.grd
gmt grdmath rangeAngle.grd SIN R2.grd MUL = slantRange.grd

# clean up
rm l*_ll.grd
rm l*_ra.grd
rm llt.txt
rm R2.grd lookAngle.grd rangeAngle.grd

cd ..