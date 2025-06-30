#!/usr/bin/env python
import os
import argparse
from pathlib import Path
import glob
from utils import grep, fracyear2yyyymmdd, try_command, getSlcData, readOldGMTFormat
import numpy as np
import shutil
import h5py as h5
import subprocess
import pdb


def main():
    args = get_args()
    slcpath = args.slcpath
    topopath = args.topopath

    slcs = sorted(glob.glob(f'{str(slcpath)}/*.SLC'))
    leds = sorted(glob.glob(f'{str(slcpath)}/*.LED'))
    prms = sorted(glob.glob(f'{str(slcpath)}/*.PRM'))

    if len(slcs) != len(leds) != len(prms):
        raise Exception(f"Inconsistent number of SLCs: {len(slcs)}, LEDs: {len(leds)}, and PRMs: {len(prms)} files")

    # topo rad
    toporapath = topopath.joinpath("topo_ra.grd")

    # Making the oldest date as reference
    prmReference = sorted([str(x) for x in slcpath.iterdir() if x.suffix == '.PRM'], key=lambda x: float(grep(x, 'SC_clock_start')))[0]
    prmRefstartstr = fracyear2yyyymmdd(float(grep(prmReference, 'SC_clock_start'))).strftime("%Y%m%d")
    slcReference = prmReference.split(".")[0]+".SLC"
    ledReference = prmReference.split(".")[0]+".LED"
    slcRef = getSlcData(slcReference, prmReference)

    # create intf directory
    ifgsPath = Path("smaster_ifgs")
    if not ifgsPath.exists():
        ifgsPath.mkdir()

    # Lists of data
    slc_corrected = [slcRef]
    bperps = [0]
    dates = [prmRefstartstr]


    for prm, slc, led in zip(prms, slcs, leds):
        current_cwd = Path().cwd()
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
        ifgPath.resolve().joinpath(prmReference.split("/")[-1]).symlink_to(prmReference)
        ifgPath.resolve().joinpath(slcReference.split("/")[-1]).symlink_to(slcReference)
        ifgPath.resolve().joinpath(ledReference.split("/")[-1]).symlink_to(ledReference)

        os.chdir(ifgPath)
        cmd_lst = ["intf.csh", prmReference.split("/")[-1], prm.split("/")[-1], "-topo", str(toporapath)]
        if not try_command(cmd_lst):
            raise  Exception(f"Problem running intf.csh in: {ifgsPath}")
        os.chdir(str(current_cwd))

        # making interferogram
        slcSec = getSlcData(slc, prm)
        ifg = slcRef * np.conjugate(slcSec)

        # Real and Imag parts of ifg
        realPath = ifgPath.joinpath("real.grd")
        imagPath = ifgPath.joinpath("imag.grd")

        # Read real and imaginary part of interferogram formed from GMTSAR using intf.csh
        real, _ =  readOldGMTFormat(realPath)
        imag, _ =  readOldGMTFormat(imagPath)
        ifgNoDrho = real+1j*imag

        drho = ifg * np.conjugate(ifgNoDrho)
        slcNoDrho = slcSec * np.conjugate(drho)
        slc_corrected.append(slcNoDrho)

        # Perp baseline
        sat_output = subprocess.run(['SAT_baseline', prmReference, prm], capture_output=True, text=True)
        bperp_grep = subprocess.run(['grep', 'B_perpendicular'], input=sat_output.stdout, capture_output=True, text=True)
        bperps.append(float(bperp_grep.stdout.split("=")[-1].strip()))

        # dates
        dates.append(startstr)


    # slc stack
    slcStack = np.stack(slc_corrected)
    bperpStack = np.array(bperps, dtype=np.float32)
    datesStack = np.array(dates, dtype=np.bytes_)

    # writing to h5file
    print(f'Writing SLC stack')
    with h5.File('slcStack.h5', 'w') as dst:
        # slc
        print(f'Writing SLCs...')
        dst.create_dataset("slc", data=slcStack, dtype=slcStack.dtype, shape=slcStack.shape, chunks=True)
        # Bperp
        dst.create_dataset("bperp", data=bperpStack, dtype=bperpStack.dtype, shape=bperpStack.shape)       
        # date
        dst.create_dataset("date", data=datesStack)
        #for key in metadata.keys():
         #   dst.attrs[key] = metadata[key]

    print(f'slcStack.h5 written.')

    # removing single master intfs
    print("Removing intf directory...")
    if ifgPath.is_dir():
        shutil.rmtree(ifgPath)


def get_args():
    mess = "makes slcstack from GMTSAR SLCs to process with SARvey"

    example = """EXAMPLE:
       slcStack_sarvey.py -s path/to/coregistered_slc -t path/to/topo
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-slc', type=Path, dest='slcpath', required=True, help='Path to coregistered SLC directory')
    parser.add_argument('-topo', type=Path, dest='topopath', required=True, help='Path to topo directory')

    return parser.parse_args()


if __name__ == "__main__":
    main()

