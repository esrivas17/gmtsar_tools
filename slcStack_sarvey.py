#!/usr/bin/env python
import os
import argparse
from pathlib import Path
import glob
from utils import grep, fracyear2yyyymmdd, try_command, getSlcData, readOldGMTFormat, headingFromLED
import numpy as np
import shutil
import h5py as h5
import subprocess
from mintpy.utils import readfile
import pdb


def main():
    args = get_args()
    slcpath = args.slcpath
    topopath = args.topopath
    skipdates = list() if args.skipdates is None else args.skipdates
    nocorrectflag = args.nocorrectflag
    slcpath = slcpath.resolve()
    topopath = topopath.resolve()

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
    slcs_noDrho = [slcRef]
    slcs_raw = [slcRef]
    bperps = [0]
    dates = [prmRefstartstr]

    # Metadata
    meta = get_metadata(topopath)

    for prm, slc, led in zip(prms, slcs, leds):
        current_cwd = Path().cwd()
        if prm == prmReference:            
            continue

        sc_clock_start = float(grep(prm, 'SC_clock_start'))
        startstr = fracyear2yyyymmdd(sc_clock_start).strftime("%Y%m%d")

        if startstr in skipdates:
            continue

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

        # go to ifg directory
        os.chdir(ifgPath)

        cmd_lst = ["intf.csh", prmReference.split("/")[-1], prm.split("/")[-1], "-topo", str(toporapath)]
        if not try_command(cmd_lst):
            raise  Exception(f"Problem running intf.csh in: {ifgsPath}")

        # Perp baseline while I am in ifgPath directory
        sat_output = subprocess.run(['SAT_baseline', prmReference, prm], capture_output=True, text=True)
        bperp_grep = subprocess.run(['grep', 'B_perpendicular'], input=sat_output.stdout, capture_output=True, text=True)
        bperps.append(float(bperp_grep.stdout.split("=")[-1].strip()))

        # go back in directory
        os.chdir(str(current_cwd))

        # making interferogram between reference and secondary SLCs
        slcSec = getSlcData(slc, prm)
        ifg = slcRef * np.conjugate(slcSec)

        # Read real and imaginary part of interferogram formed from GMTSAR using intf.csh
        realPath = ifgPath.joinpath("real.grd")
        imagPath = ifgPath.joinpath("imag.grd")
        real, _ =  readOldGMTFormat(realPath)
        imag, _ =  readOldGMTFormat(imagPath)
        ifgNoDrho = real+1j*imag
        ifgNoDrho = ifgNoDrho/np.abs(ifgNoDrho) # normalizing to not affect the amplitude

        # Ifg with and without topo phase
        drho = ifg * np.conjugate(ifgNoDrho)
        drho = drho / np.abs(drho)
        slcNoDrho = slcSec * drho # adding drho correction
        slcs_noDrho.append(slcNoDrho)

        # no corrected slcs
        if nocorrectflag:
            slcs_raw.append(slcSec)

        # dates
        dates.append(startstr)

    # slc stack
    slcStack = np.stack(slcs_noDrho)
    bperpStack = np.array(bperps, dtype=np.float32)
    datesStack = np.array(dates, dtype=np.bytes_)
    outfname = 'slcStack.h5'

    # writing corrected SLCs to h5file
    print(f'Writing SLC stack')
    with h5.File(outfname, 'w') as dst:
        # slc
        print(f'Writing SLCs...')
        dst.create_dataset("slc", data=slcStack, dtype=slcStack.dtype, shape=slcStack.shape, chunks=True)
        # Bperp
        print(f'Writing perpendicular baseline...')
        dst.create_dataset("bperp", data=bperpStack, dtype=bperpStack.dtype, shape=bperpStack.shape)       
        # date
        print(f'Writing dates...')
        dst.create_dataset("date", data=datesStack)
        # Metadata
        print(f'Writing Metadata...')
        for key in meta.keys():
            dst.attrs[key] = meta[key]

    print(f'{outfname} written.')

    # removing single master intfs
    print("Removing intf directory...")
    if ifgsPath.is_dir():
        shutil.rmtree(ifgsPath)

    # writing non corrected slcs if flag is true
    if nocorrectflag:
        outfname = 'slcStack_topoearth.h5'
        slcStack_raw = np.stack(slcs_raw)
        print(f'Creating slc stack without removing topo-earth component')
        with h5.File(outfname, 'w') as dst:
            # slc
            print(f'Writing SLCs...')
            dst.create_dataset("slc", data=slcStack_raw, dtype=slcStack_raw.dtype, shape=slcStack_raw.shape, chunks=True)
            # Bperp
            print(f'Writing perpendicular baseline...')
            dst.create_dataset("bperp", data=bperpStack, dtype=bperpStack.dtype, shape=bperpStack.shape)
            # date
            print(f'Writing dates...')
            dst.create_dataset("date", data=datesStack)
            # Metadata
            print(f'Writing Metadata...')
            for key in meta.keys():
                dst.attrs[key] = meta[key]
        print(f'{outfname} written.')


def get_metadata(topopath: Path):
    # Check master PRM
    masterPRM = topopath.joinpath('master.PRM')
    if not masterPRM.exists():
        raise Exception('master.PRM seems not to exist. Please check')
    # Read and add parameters to meta
    meta = readfile.read_gmtsar_prm(masterPRM)

    # Check if LED is in folder
    grepOut = subprocess.run(['grep', 'led_file', masterPRM.as_posix()], capture_output=True, text=True)
    LEDfile = topopath.joinpath(grepOut.stdout.split("=")[1].strip())
    if not LEDfile.exists():
        raise Exception('Seems that LED file does not exist. Please check')
    meta['HEADING'] = headingFromLED(LEDfile)

    # Getting info from topo, inc and slantrange grd files
    topoInfo = subprocess.run(['gmt', 'grdinfo',  topopath.joinpath('topo_ra_full.grd').as_posix(), '-C'], capture_output=True, text=True)
    meta['XMIN'] = topoInfo.stdout.split("\t")[1]
    meta['XMAX'] = topoInfo.stdout.split("\t")[2]
    meta['YMIN'] = topoInfo.stdout.split("\t")[3]
    meta['YMAX'] = topoInfo.stdout.split("\t")[4]
    meta['ALOOKS'] = topoInfo.stdout.split("\t")[7] #xinc
    meta['RLOOKS'] = topoInfo.stdout.split("\t")[8] #yinc
    meta['WIDTH'] = topoInfo.stdout.split("\t")[9]
    meta['LENGTH'] = topoInfo.stdout.split("\t")[10]
    incInfo = subprocess.run(['gmt', 'grdinfo',  topopath.joinpath('incidence.grd').as_posix(), '-C', '-L2'], capture_output=True, text=True)
    incMean = float(incInfo.stdout.split("\t")[11])
    slantInfo = subprocess.run(['gmt', 'grdinfo',  topopath.joinpath('slantRange.grd').as_posix(), '-C', '-L2'], capture_output=True, text=True)
    slantMean = float(slantInfo.stdout.split("\t")[11])
    grepOut = subprocess.run(['grep', 'led_file', masterPRM.as_posix()], capture_output=True, text=True)
    LEDfile = grepOut.stdout.split("=")[1].strip()
    meta['FILE_TYPE'] = 'timeseries'
    meta['AZIMUTH_PIXEL_SIZE'] *= int(meta['ALOOKS'])
    meta['RANGE_PIXEL_SIZE'] *= int(meta['RLOOKS'])
    meta['UNIT'] = 'i'
    meta = readfile.standardize_metadata(meta)
    return meta


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
    parser.add_argument('--skipdates', dest='skipdates', nargs='*', type=str, help='Dates to skip. e.g. 20150101 20160101')
    parser.add_argument('--nocorrect', dest='nocorrectflag', action='store_true', default=False, help='Flag to skip topo-earth phase removal')
    return parser.parse_args()


if __name__ == "__main__":
    main()

