#!/bin/csh -f
#
if ($#argv < 4) then
   echo ""
   echo "Usage: singlemaster_intfs.csh full/path/SLCs /full/path/topo"
   echo ""
   echo " Makes interferograms with first image as reference"
   echo "This is needed to remove drho phase from raw interferograms"
   echo ""
   echo "Example: singlemaster_intfs.csh /path/SLC path/topo"
   echo ""
   exit 1
endif

set slcpath = $1
set topopath = $2
set masterPRM = $3
set slclist = $slcpath/*.PRM
set ref = $slclist[1]


echo ""
echo "Generating interferograms..."
mkdir -p smaster_ifgs

foreach slcf ($slcpath/*.PRM)
    
end



set topoll = topo_ll.grd



echo "Done"

# Clean up
rm look_*
rm grid_ll.grd
rm topo_ll.xyz
rm inc.grd
rm azi.grd

