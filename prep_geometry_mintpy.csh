#!/bin/csh -f
#
if ($#argv < 3) then
   echo ""
   echo "Usage: geometry_mintpy.csh trans.dat master.PRM corr_ll.grd reso.meters"
   echo ""
   echo " Returns incidence_angle, azimuth and height. This in preparation for GMTSAR-Mintpy processing"
   echo " A geocoded product from intf must be included, it can be corr or phase ll"
   echo " Run script inside topo folder"
   echo ""
   echo "Example: geometry_mintpy.csh trans.dat master.PRM ../intf/corr_ll.grd 50"
   echo ""
   exit 1
endif

set trans_dat = $1
set masterPRM = $2
ln -s $3 grid_ll.grd
set pix_m = $4

foreach f ($trans_dat $masterPRM "grid_ll.grd")
    if (! -e $f ) then
        echo "$f does not exist"
        exit
    endif
end

# getting topo LL from trans.dat
gmt gmtconvert $trans_dat -o3,4,2 -bi5d  > lle

# trans.dat is range, azimuth, elevation, lon, lat

echo ""
echo "CALCULATION OF LOOK VECTORS ENU"
echo ""
# Getting look E, look N and look U
SAT_look $masterPRM < lle > topo.lltn # SAT_look returns: lon, lat, elev, look_E, look_N, look_U

# Block median / mean

set incs = `m2s.csh $pix_m lle`	
set R = `gmt gmtinfo lle -Iincs[1]`

gmt blockmedian topo.lltn $R -I$incs[1] -i0,1,3 -r -V -Glook_E.grd
gmt blockmedian topo.lltn $R -I$incs[1] -i0,1,4 -r -V -Glook_N.grd
gmt blockmedian topo.lltn $R -I$incs[1] -i0,1,5 -r -V -Glook_U.grd
gmt blockmedian lle $R -I$incs[1] -r -V -Gtopo_ll.grd

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
gmt grdsample topo_ll.grd -Gheight.grd -I$xinc/$yinc -R$x0/$x1/$y0/$y1 -V

echo "Done"

# Clean up
rm look_*
rm grid_ll.grd
rm lle
rm topo_ll.grd
rm inc.grd
rm azi.grd

