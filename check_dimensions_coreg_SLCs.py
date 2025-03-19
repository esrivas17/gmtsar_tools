#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from functions import grep
import numpy as np
import pdb


def main():
    args = get_args()
    projdir = args.projdir
    masterfile = args.masterfile
    SLCdir = args.slcdir
    
    if not SLCdir:
        SLCdir = projdir.joinpath('SLC')
    
    rawdir = projdir.joinpath('raw')
    # Check if PRM and SLC exists for master
    masterSLCfile = rawdir.joinpath(masterfile.with_suffix('.SLC').name)
    masterPRMfile = rawdir.joinpath(masterfile.with_suffix('.PRM').name)

    if not masterSLCfile.exists():
        raise Exception(f'{masterSLCfile} does not exist')
    if not masterPRMfile.exists():
        raise Exception(f'{masterPRMfile} does not exist')
    
    # Check dimensions for master
    check_dimensions(masterSLCfile, masterPRMfile)

    PRMfiles = glob.glob(f'{SLCdir.as_posix()}/*.PRM')
    SLCfiles = glob.glob(f'{SLCdir.as_posix()}/*.SLC')
    LEDfiles = glob.glob(f'{SLCdir.as_posix()}/*.LED')

    if len(PRMfiles) != len(SLCfiles) != len(LEDfiles):
        raise Exception(f'Number of files between SLC, PRM and LED does not match')

    if SLCdir.joinpath(masterPRMfile.name).as_posix() in PRMfiles:
        PRMfiles.remove(SLCdir.joinpath(masterPRMfile.name).as_posix())

    for slave_stem in [Path(x.removesuffix('.PRM')) for x in PRMfiles]:
        SLCslave = slave_stem.with_suffix('.SLC')
        PRMslave = slave_stem.with_suffix('.PRM')
        nlines = grep(PRMslave, 'num_lines')
        rgbins = grep(PRMslave, 'num_rng_bins')
        print(f'Dimensions of slaves according to PRM file -> nrows {nlines} range {rgbins}')
        if not check_dimensions(SLCslave, masterPRMfile):
            raise Exception(f'Slave: {slave_stem} dimensions do not match')


def check_dimensions(slcfile, prmfile):
    nlines = grep(prmfile, 'num_lines')
    rgbins = grep(prmfile, 'num_rng_bins')

    if not nlines:
        raise Exception(f'Error getting nlines: {nlines} from PRM file: {prmfile}')
    else:
        nlines = int(nlines)

    if not rgbins:
        raise Exception(f'Error getting range lines: {rgbins} from PRM file: {prmfile}')
    else:
        rgbins = int(rgbins)

    try:
        slc_data = np.fromfile(slcfile, dtype=np.int16)
        slc_data = slc_data.astype(np.float32).view(np.complex64)
        slc_data = slc_data.reshape((nlines,rgbins))
    except Exception as e:
        raise Exception(f'Something wrong reshaping SLC: {slcfile}\nnrows: {nlines} range: {rgbins} SLC shape: {slc_data.shape}\nException: {e}')
    else:
        print(f'SLC shape: {slc_data.shape} matches nrows {nlines} and range bins {rgbins}\n')
        del slc_data
        return True


def get_args():
    mess = "checks dimensions of SLC based on PRM file"

    example = """EXAMPLE:
       check_dimensions_coreg_SLCs.py -p path/to/project 
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-p', '--projectdir', dest='projdir', required=True, type=Path, help='Path to project directory')
    parser.add_argument('-m', '--masterfile', dest='masterfile', required=True, type=Path, help='Master file name with suffix -  No full path')
    parser.add_argument('--slcdir', dest='slcdir', type=Path, help='Path to SLC directory to check - Optional')

    return parser.parse_args()


if __name__ == "__main__":
    main()

