#!/usr/bin/env python
import argparse
from pathlib import Path
from utils import grep
import numpy as np
import pdb


def main():
    args = get_args()
    slcfile = args.slcfile
    prmfile = args.prmfile

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
        del slc_data
        raise Exception(f'Something wrong reshaping SLC: {slcfile}\nnrows: {nlines} range: {rgbins} SLC shape: {slc_data.shape}\nException: {e}')
    else:
        print(f'SLC shape: {slc_data.shape} matches nrows {nlines} and range bins {rgbins}\n')
        del slc_data
        return True


def get_args():
    mess = "Quick check of SLC dimensions based on PRM file"

    example = """EXAMPLE:
       check_SLC_dim.py -s path/to/slc -p path/to/prm 
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-s', '--slcfile', dest='slcfile', required=True, type=Path, help='Path to SLC file - no symlink')
    parser.add_argument('-p', '--prmfile', dest='prmfile', required=True, type=Path, help='Path to PRM file')

    return parser.parse_args()


if __name__ == "__main__":
    main()

