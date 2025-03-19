#!/usr/bin/env python
import argparse
from pathlib import Path
from grdv import main as grdv
import os
import matplotlib.pyplot as plt
from netCDF4 import Dataset as NetCDFFile
import numpy as np
import shutil
import pdb


def main():
    args = get_args()
    intfdir = args.intfdir
    projdir = args.projdir
    flagcont = args.flagcont

    select_intf = projdir.joinpath('intf_selected')
    reject_intf = projdir.joinpath('intf_rejected')

    if select_intf.exists():
        print(f'intf selected folder already exists: {select_intf.name}')
        if flagcont:
            print('Continue...')
        else:
            return 0
    else:
        select_intf.mkdir()
        
    if reject_intf.exists():
        print(f'intf rejected folder already exists: {reject_intf.name}')
        if flagcont:
            print('Continue...')
        else:
            return 0
    else:
        reject_intf.mkdir()

    for intf in intfdir.iterdir():
        if intf.is_dir() and "_" in intf.name:
            phase = intf.joinpath("phase.grd")
            corr = intf.joinpath("corr.grd")
            phasef = intf.joinpath("phasefilt.grd")

            fig, (ax1, ax2, ax3) = plt.subplots(1,3, figsize=(11,5), sharey=True, constrained_layout=True)
            fig.suptitle(f'{intf.name}')
            # Phase
            z, extent = opengrd(phase)
            ax1.imshow(z, extent=extent, cmap='jet', aspect=0.2, interpolation='nearest')
            ax1.set_title('Phase')
            ax1.set_xlabel('x')
            ax1.set_ylabel('y')
            del z
            del extent
            # Phasefilt
            z, extent = opengrd(phasef)
            ax2.imshow(z, extent=extent, cmap='jet', aspect=0.2, interpolation='nearest')
            ax2.set_title('Filtered phase')
            ax2.set_xlabel('x')
            del z
            del extent
            # Coherence
            z, extent = opengrd(corr)
            ax3.imshow(z, extent=extent, cmap='gist_gray', aspect=0.2, interpolation='nearest')
            ax3.set_title('Coherence')
            ax3.set_xlabel('x')
            del z
            del extent
            
            plt.show()

            select = input('select interferogram? (Yes(y)/No(x))')
            if select.lower() == 'y':                
                intf_select = select_intf.joinpath(intf.name)
                intf.rename(intf_select)
                print(f'Interferogram {intf.name} selected.\nMoved to {intf_select}')
            elif select.lower() == 'q':
                exit()
            else:
                intf_discard = reject_intf.joinpath(intf.name)
                intf.rename(intf_discard)
                print(f'Interferogram {intf.name} NOT selected\nMove to {intf_discard}')

    return 0

def opengrd(path: Path):
    nc = NetCDFFile(path.as_posix())
    x = nc.variables['x'][:]
    y = nc.variables['y'][:]
    z = nc.variables['z'][:]
    extent = [np.min(x), np.max(x), np.min(y), np.max(y)]
    del x
    del y
    return z, extent

def get_args():
    mess = "Loops over ifgs in intf folder, plots and you get asked if you want them or not"

    example = """EXAMPLE:
       select_ifgs_gmtsar.py -d path/to/intf   -p project/dir"""

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-d', '--intfdir', dest='intfdir', required=True, type=Path, help='Path to directory interferograms: intf')
    parser.add_argument('-p', '--projdir', dest='projdir', required=True, type=Path, help='Path to project directory')
    parser.add_argument('--cont', dest='flagcont', default=False, action='store_true', help='Continue the selection')
    return parser.parse_args()

if __name__ == "__main__":
    main()
