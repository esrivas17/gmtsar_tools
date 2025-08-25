#!/bin/csh -f
# intflist contains a list of all date1_date2  directories
# This script geocodes unwrap.grd and corr.grd in preparation for loading geocoded products in mintpy
echo $1

foreach line (`cat $1`)
   cd $line
   #ln -s ../../topo/trans.dat .
   proj_ra2ll.csh trans.dat unwrap.grd unwrap_ll.grd
   proj_ra2ll.csh trans.dat corr.grd corr_ll.grd

   cd ..
end
