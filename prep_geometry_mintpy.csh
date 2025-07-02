#!/bin/csh -f
#
if ($#argv < 4) then
   echo ""
   echo "Usage: geometry_mintpy.csh trans.dat topo_ra.grd master.PRM corr_ll.grd"
   echo ""
   echo " Returns incidence_angle, azimuth and topo_ll_resample. This in preparation for GMTSAR-Mintpy processing"
   echo " A geocoded product from intf must be included, it can be corr or phase ll"
   echo " Run script inside topo folder"
   echo ""
   echo "Example: geometry_mintpy.csh trans.dat topo_ra.grd master.PRM ../intf/corr_ll.grd "
   echo ""
   exit 1
endif

set trans_dat = $1
set toporad = $2
set masterPRM = $3
set topoll = topo_ll.grd
ln -s $4 grid_ll.grd

foreach f ($trans_dat $toporad $masterPRM "grid_ll.grd")
    if (! -e $f ) then
        echo "$f does not exist"
        exit
    endif
end

# getting topo LL
proj_ra2ll.csh $trans_dat $toporad $topoll

# Topo LL to XYZ or ASCII
gmt grd2xyz $topoll > topo_ll.xyz

# trans.dat is range, azimuth, elevation, lon, lat

echo ""
echo "CALCULATION OF LOOK VECTORS ENU"
echo ""
# Getting look E, look N and look U
SAT_look $masterPRM < topo_ll.xyz > topo.lltn # SAT_look returns: lon, lat, elev, look_E, look_N, look_U

# Block median / mean
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,3 -r -V -Glook_E.grd
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,4 -r -V -Glook_N.grd
gmt blockmedian topo.lltn `gmt info topo.lltn -I0.08333333333` -I.00083333333333 -i0,1,5 -r -V -Glook_U.grd

echo ""
echo "CALCULATION OF INCIDENCE AND AZIMUTH ANGLES"
echo ""
# Incidence angle
gmt grdmath look_E.grd look_N.grd HYPOT look_U.grd ATAN2 R2D = inc.grd -V

# Azimuth angle
gmt grdmath look_E.grd look_N.grd ATAN2 R2D = azi.grd -V

# Resample
set x0 = `gmt grdinfo grid_ll.grd -C | awk '{print $2}'`
set x1 = `gmt grdinfo grid_ll.grd -C | awk '{print $3}'`
set y0 = `gmt grdinfo grid_ll.grd -C | awk '{print $4}'`
set y1 = `gmt grdinfo grid_ll.grd -C | awk '{print $5}'`
set zmax = `gmt grdinfo grid_ll.grd -C | awk '{print $6}'`
set xinc = `gmt grdinfo grid_ll.grd -C | awk '{print $8}'`
set yinc = `gmt grdinfo grid_ll.grd -C | awk '{print $9}'`

echo ""
echo "RESAMPLING INCIDENCE, AZIMUTH AND TOPO"
echo ""
gmt grdsample inc.grd -Gincidence.grd -I$xinc/$yinc -R$x0/$x1/$y0/$y1 -V
gmt grdsample azi.grd -Gazimuth.grd -I$xinc/$yinc -R$x0/$x1/$y0/$y1 -V
gmt grdsample $topoll -Gtopo_ll_resample.grd -I$xinc/$yinc -R$x0/$x1/$y0/$y1 -V

echo "Done"

# Clean up
rm look_*
rm grid_ll.grd
rm topo_ll.xyz
rm inc.grd
rm azi.grd

