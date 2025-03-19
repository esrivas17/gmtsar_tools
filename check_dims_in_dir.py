#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from functions import grep
import numpy as np
import pdb


def main():
    args = get_args()
    directory = args.dir

    SLCfiles = glob.glob(f'{directory.as_posix()}/*.SLC')

    if len(SLCfiles) == 0:
        raise Exception(f'No SLC files found in directory: {directory}')
    
    for slcfile in SLCfiles:
        prmfile = Path(slcfile).with_suffix('.PRM')
        
        if not prmfile.exists():
            print(f'PRM file for slc: {slcfile} does not exist\n')

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
            print(f'Something wrong reshaping SLC: {slcfile}\nnrows: {nlines} range: {rgbins} SLC shape: {slc_data.shape}\nException: {e}\n')
            del slc_data
            continue
        else:
            print(f'SLC shape: {slc_data.shape} matches nrows {nlines} and range bins {rgbins}\nFile:{slcfile}\n')
            del slc_data


def get_args():
    mess = "checks dimensions of SLC based on PRM file"

    example = """EXAMPLE:
       check_dims_in_dir.py -p path/to/project 
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-d', '--dir', dest='dir', required=True, type=Path, help='Path to directory')
    return parser.parse_args()


if __name__ == "__main__":
    main()

