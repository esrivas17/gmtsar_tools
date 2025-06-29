#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from utils import grep, fracyear2yyyymmdd
import numpy as np
import matplotlib.pyplot as plt
import pdb


def main():
    args = get_args()
    slcpath = args.slcpath
    topopath = args.topopath

    slcs = sorted(glob.glob(f'str({slcpath})/*.SLC'))
    leds = sorted(glob.glob(f'str({slcpath})/*.LED'))
    prms = sorted(glob.glob(f'str({slcpath})/*.PRM'))

    if len(slcs) != len(leds) != len(prms):
        raise Exception(f"Inconsistent number of SLCs: {len(slcs)}, LEDs: {len(leds)}, and PRMs: {len(prms)} files")

    # topo rad
    toporapath = topopath.joinpath("topo_ra.grd")

    # Making the oldest date as reference
    prmReference = sorted([str(x) for x in slcpath.iterdir() if x.suffix == '.PRM'], key=lambda x: float(grep(x, 'SC_clock_start')))[0]
    prmRefstartstr = fracyear2yyyymmdd(float(grep(prmReference, 'SC_clock_start'))).strftime("%Y%m%d")

    # create intf directory
    ifgsPath = Path("smaster_ifgs")
    if not ifgsPath.exists():
        ifgsPath.mkdir()

    for prm, slc, led in zip(prms, slcs, leds):
        if prm == prmReference:
            continue

        sc_clock_start = float(grep(prm, 'SC_clock_start'))
        startstr = fracyear2yyyymmdd(sc_clock_start).strftime("%Y%m%d")
        intfstr = f'{prmRefstartstr}_{startstr}'

        # creates folders
        ifgPath = ifgsPath.joinpath(intfstr)
        if not ifgPath.exists():
            ifgPath.mkdir()
        else:
            print(f'Ifg folder: {ifgPath.as_posix()} exists')
        # symlinks: PRM, SLC, LED, topo_ra
        ifgPath.resolve().joinpath(prm.split("/")[-1]).symlink_to(prm)
        ifgPath.resolve().joinpath(slc.split("/")[-1]).symlink_to(slc)
        ifgPath.resolve().joinpath(led.split("/")[-1]).symlink_to(led)
        ifgPath.resolve().joinpath(toporapath.name).symlink_to(toporapath.as_posix())
           
            

                                                                  
    # list of slcs
    
    # reads prm and makes reasonable names for intf folders
    # creates folders and symlinks for prms, leds, slcs and topo_ra.grd
    # loop over each folder and run a intf.csh script 
    # or give full path to script and cd and run and go back


def get_args():
    mess = "makes slcstack from GMTSAR SLCs to process with SARvey"

    example = """EXAMPLE:
       slcStack_sarvey.py -s path/to/coregistered_slc -t path/to/topo
       slcStack_sarvey.py -f path/to/file --savedir /path/to/save 
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-slc', type=Path, dest='slcpath', required=True, help='Path to coregistered SLC directory')
    parser.add_argument('-topo', type=Path, dest='topopath', required=True, help='Path to topo directory')

    return parser.parse_args()


if __name__ == "__main__":
    main()

