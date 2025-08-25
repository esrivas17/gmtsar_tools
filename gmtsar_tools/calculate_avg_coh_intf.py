#!/usr/bin/env python
import argparse
from pathlib import Path
from gmtsar_tools.utils import grep
import glob
import numpy as np
import os
import pdb
import subprocess
import pandas as pd
from datetime import datetime
from netCDF4 import Dataset as NetCDFFile


def main():
    args = get_args()
    intf_dir = args.intfdir
    cutrange = args.cutrange
    x1, x2, y1, y2 = cutrange

    intfs_dir = glob.glob(f'{intf_dir.as_posix()}/*_*')
    intfs_dir = [Path(x) for x in intfs_dir]
    
    dates12, dates1, dates2 = list(), list(), list()
    corrs, tbases, bperps = list(), list(), list()
    cwd = os.getcwd()
    for intf in intfs_dir:
        os.chdir(os.getcwd() + '/' + intf.as_posix())
        prms = glob.glob('*PRM')
        prms.sort(key=lambda x: datetime.strptime(x[14:22], "%Y%m%d").date())
        if len(prms) !=2:
            #raise Exception(f'There are not two PRMs in intf: {intf}')
            print(f'There are not two PRMs in intf: {intf}... continue')
            os.chdir('../..')
            continue
        date1, date2 = intf.name.split("_")
        dates12.append(f'{date1}_{date2}')
        nc = NetCDFFile('corr.grd')
        corrs.append(np.nanmean(nc.variables['z'][y1:y2,x1:x2]))
        d1 = datetime.strptime(date1, '%Y%j').date()
        d2 = datetime.strptime(date2, '%Y%j').date()
        sat_output = subprocess.run(['SAT_baseline', prms[0], prms[1]], capture_output=True, text=True)
        bperp_grep = subprocess.run(['grep', 'B_perpendicular'], input=sat_output.stdout, capture_output=True, text=True)
        bperp = float(bperp_grep.stdout.split("=")[-1].strip())
        bperps.append(bperp)
        tbases.append((d2-d1).days)
        dates1.append(date1)
        dates2.append(date2)
        os.chdir('../..')

    df = pd.DataFrame({
    'date12': dates12,
    'date1': dates1,
    'date2': dates2,
    'avgCoherence': corrs,
    'TBase': tbases,
    'PBase': bperps,
    })

    # calculate average per day
    date_coh_avg = df.groupby('date1')['avgCoherence'].mean().to_numpy()
    date_coh_df = pd.DataFrame({'date': list(set(dates1)), 'avgCoh': date_coh_avg})
    print(date_coh_df)
    
    df.to_csv('avgCoherence.txt', sep='\t', index=False)
    date_coh_df.to_csv('CohperDay.txt', sep='\t', index=False)
    

def get_args():
    mess = "calculates average of coherence (corr) given window"

    example = """EXAMPLE:
       calculate_avg_coh_intf.py -d directory/path -r 300/2000/600/9000
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-d', '--intfdir', dest='intfdir', required=True, type=Path, help='Path to intf directory')
    parser.add_argument('-r', '--range', dest='cutrange', required=True, nargs=4, type=int, help='Cut range: xmin xmax ymin ymax')

    return parser.parse_args()


if __name__ == "__main__":
    main()
