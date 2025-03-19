#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from functions import grep, try_command
import os
import pdb

ERS_ENVI_formats = [".E1", ".E2", ".N1"]

def main():
    args = get_args()
    rawdir = args.rawdir
    rawmaster = args.rawmaster
    
    # Change directory otherwise these commands do not work
    os.chdir(rawdir)

    # Dealing first with master raw file
    if rawmaster:
        masterPRM = Path(rawmaster.with_suffix('.PRM').name)
        if masterPRM.exists():
            earthradius = grep(masterPRM, 'earth_radius')
            if not earthradius:
                    raise Exception(f'Earth radius parameter empty or not found: {earthradius}')
        else:
            masterstem = rawmaster.stem
            slc_decode = ['ENVI_SLC_pre_process', masterstem, '0']
            if not try_command(slc_decode):
                raise Exception(f'Error decoding master raw file: {slc_decode}')
            else:
                earthradius = grep(masterPRM, 'earth_radius')
                if not earthradius:
                    raise Exception(f'Earth radius parameter empty or not found: {earthradius}')
    else:
        earthradius = '0'
    
    print(f'\nEarth Radius: {earthradius}\n')

    rawfiles = list()
    for format in ERS_ENVI_formats:
        files = glob.glob(f'*{format}')
        rawfiles.extend(files)

    if rawmaster:
        rawmaster = rawmaster.name
        rawfiles.remove(rawmaster)


    for rawfile in rawfiles:
        #rawfile = Path(rawfile).parent.joinpath(Path(rawfile).stem).as_posix()
        rawstem = Path(rawfile).stem
        envi_args = ['ENVI_SLC_pre_process', rawstem, earthradius]
        if not try_command(envi_args):
            raise Exception(f'Command: {" ".join(envi_args)} FAILED')




def get_args():
    mess = "Preprocess raw ENVI-ERS files for GMTSAR. This is missing the refocusing needed for ERS, so you better dont use it"

    example = """EXAMPLE:
       preproc_batch_ENVI_SLC.py -r path/to/rawfiles --rawmaster path/to/rawfile
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-r', '--rawdir', dest='rawdir', required=True, type=Path, help='Path to directory of raw files (E1,E2)')
    parser.add_argument('-m', '--rawmaster', dest='rawmaster', default=None, type=Path, help='full path to raw master file (E1 or E2)')

    return parser.parse_args()


if __name__ == "__main__":
    main()

