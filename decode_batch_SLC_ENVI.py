#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from functions import grep
import subprocess
import os
import pdb

ENVI_formats = [".E1", ".E2", ".N1"]

def main():
    args = get_args()
    projdir = args.projdir
    rawdir = projdir.joinpath("raw")

    rawfiles = list()

    for format in ENVI_formats:
        files = glob.glob(f'{rawdir.as_posix()}/*{format}')
        rawfiles.extend(files)

    rawnamefiles = [x.split("/")[-1] for x in rawfiles]

    # Change directory otherwise these commands do not work
    os.chdir(rawdir)
    
    for rawfile in rawnamefiles:
        try:
            envi_args = ['envi_slc_decode', rawfile]
            r = subprocess.check_call(envi_args)
        except subprocess.CalledProcessError as e:
            print(f'command with args: {envi_args} FAILED\nException: {e}')
            continue
        else:
            if r != 0:
                print(f'Problem found in: {envi_args}')



def get_args():
    mess = "Preprocess raw ENVI files for GMTSAR"

    example = """EXAMPLE:
       ENVI_slc_decode_batch.py -p path/to/projectdir
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-p', '--projectdir', dest='projdir', required=True, type=Path, help='Path to project directory')

    return parser.parse_args()

if __name__ == "__main__":
    main()
