#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from functions import grep
import subprocess
import os
import shutil
import pdb

ENVI_formats = [".E1", ".E2", ".N1"]

def main():
    args = get_args()
    masterfile = args.masterfile
    projdir = args.projdir
    xcorr2 = args.xcorr2

    SLCdir = projdir.joinpath('SLC')
    rawdir = projdir.joinpath('raw')


    rawfiles = list() 

    for format in ENVI_formats:
        files = glob.glob(f'{rawdir.as_posix()}/*{format}')
        rawfiles.extend(files)

    # Remove master from rawfiles
    referencefiles = [x.split("/")[-1] for x in rawfiles if x.split("/")[-1] != masterfile.name]

    # Check if SLC, LED and PRM exists for master
    masterSLC = rawdir.joinpath(masterfile.with_suffix('.SLC'))
    masterLED = rawdir.joinpath(masterfile.with_suffix('.LED'))
    masterPRM = rawdir.joinpath(masterfile.with_suffix('.PRM'))
    if not masterSLC.exists():
        raise Exception(f'Master {masterSLC.as_posix()} does not exist')
    if not masterLED.exists(): 
        raise Exception(f'Master {masterLED.as_posix()} does not exist')
    if not masterPRM.exists(): 
        raise Exception(f'Master {masterPRM.as_posix()} does not exist')
    
    if not SLCdir.exists():
        SLCdir.mkdir()
    
    # Copy and symlinks to SLC
    refmasterSLC = SLCdir.joinpath(masterSLC.name)
    refmasterLED = SLCdir.joinpath(masterLED.name)
    refmasterPRM = SLCdir.joinpath(masterPRM.name)
    shutil.copy(masterPRM, refmasterPRM)
    if not refmasterSLC.is_symlink():
        refmasterSLC.symlink_to(masterSLC)
    if not refmasterLED.is_symlink():
        refmasterLED.symlink_to(masterLED)

    for reference in referencefiles:
        reference = Path(reference)
        rawslc = rawdir.joinpath(reference.with_suffix('.SLC'))
        rawled = rawdir.joinpath(reference.with_suffix('.LED'))
        rawprm = rawdir.joinpath(reference.with_suffix('.PRM'))
        if not rawslc.exists(): 
            raise Exception(f'{rawslc.as_posix()} does not exist')
        if not rawled.exists(): 
            raise Exception(f'{rawled.as_posix()} does not exist')
        if not rawprm.exists(): 
            raise Exception(f'{rawprm.as_posix()} does not exist')

        # copy PRM file to SLC and symlink for LED and SLC
        refSLC = SLCdir.joinpath(rawslc.name)
        refLED = SLCdir.joinpath(rawled.name)
        refPRM = SLCdir.joinpath(rawprm.name)

        if refPRM.exists():
            refPRM.unlink()
            shutil.copy(rawprm, refPRM)
        else:
            shutil.copy(rawprm, refPRM)

        if not refSLC.is_symlink():
            refSLC.symlink_to(rawslc)
        if not refLED.is_symlink():
            refLED.symlink_to(rawled)

        # Change directory to run xcorr
        os.chdir(SLCdir)
        # XCORR
        print("="*40,"\nxcorr...\n")
        if xcorr2:
            print(f'Using xcorr2..')
            xcorr_args = ['xcorr2', refmasterPRM.name, refPRM.name, '-xsearch', '128', '-ysearch', '128', '-nx', '20', '-ny', '50']
        else:
            xcorr_args = ['xcorr', refmasterPRM.name, refPRM.name, '-xsearch', '128', '-ysearch', '128', '-nx', '20', '-ny', '50']
        print(f'Arguments: {" ".join(xcorr_args)}')
        if not try_command(xcorr_args):
            raise Exception(f'Command: {" ".join(xcorr_args)} FAILED')

        # FITOFFSET
        print("="*40,"\nfitoffset...\n")
        fitoffset_args = ['fitoffset.csh', '2', '2', 'freq_xcorr.dat', '18', '>>', refPRM.name]        
        print(f'Arguments: {" ".join(fitoffset_args)}')        
        if not try_command(fitoffset_args):
            raise Exception(f'Command: {" ".join(fitoffset_args)} FAILED')

        # RESAMP
        print("="*40,"\nresamp...\n")
        resamp_refPRM = refPRM.name + "resamp"
        resamp_refSLC = refSLC.name + "resamp"
        resamp_args = ['resamp', refmasterPRM.name, refPRM.name, resamp_refPRM , resamp_refSLC, '4']
        print(f'Arguments: {" ".join(resamp_args)}')        

        # interpolation method: 1-nearest; 2-bilinear; 3-biquadratic; 4-bisinc
        if not try_command(resamp_args):
            raise Exception(f'Command: {" ".join(resamp_args)} FAILED')

        # RENAME
        print("renaming...")
        refSLC.unlink()
        #Path(resamp_refSLC).rename(refSLC)
        #Path(resamp_refPRM).rename(refPRM)

        # Copy Resampled PRM and SLC to a different folder
        print('Copying resampled PRM and SLCs to a different folder\n')
        coregSLCs = projdir.joinpath('coregSLC')
        if not coregSLCs.exists():
            coregSLCs.mkdir()
        # Copying files to coregSLC folder
        coregSLCresamp = coregSLCs.joinpath(resamp_refSLC.removesuffix('resamp'))
        coregPRMresamp = coregSLCs.joinpath(resamp_refPRM.removesuffix('resamp'))
        resampSLC = SLCdir.joinpath(resamp_refSLC)
        resampPRM = SLCdir.joinpath(resamp_refPRM)
        shutil.copy(resampSLC, coregSLCresamp)
        shutil.copy(resampPRM, coregPRMresamp)

        print(f'Coregistration DONE on slave: {reference}\n')


def try_command(command_list):
    try:
        r = subprocess.check_call(command_list)
    except subprocess.CalledProcessError as e:
        print(f'command with args: {command_list} FAILED\nException: {e}')
        return False
    else:
        if r != 0:
            print(f'Problem found in: {command_list}')
            return False
        else:
            return True
        

def get_args():
    mess = "Align ENVI SLCs"

    example = """EXAMPLE:
       align_ENVI_SLC_batch.py -r path/to/rawfiles
        """
    # xcorr2: https://github.com/cuihaoleo/gmtsar_optimize
    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-d', '--projdir', dest='projdir', required=True, type=Path, help='Project directory -  full path')
    parser.add_argument('-m', '--masterfile', dest='masterfile', required=True, type=Path, help='Master file name with suffix -  No full path')
    parser.add_argument('--xcorr2', dest='xcorr2', action='store_true', default=False, help='Option to use xcorr2 if installed')
    return parser.parse_args()

if __name__ == "__main__":
    main()
