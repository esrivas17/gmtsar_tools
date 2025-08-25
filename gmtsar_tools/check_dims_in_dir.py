#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from gmtsar_tools.utils import grep
import numpy as np
import pdb


def main():
    args = get_args()
    directory = args.dir

    SLCfiles = glob.glob(f'{directory.as_posix()}/*.SLC')

    if len(SLCfiles) == 0:
        raise Exception(f'No SLC files found in directory: {directory}')
    
    count_ok = 0
    count_bad = 0
    slcfiles_bad = list()
    for slcfile in sorted(SLCfiles):
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
            count_bad += 1
            slcfiles_bad.append(slcfile)
            del slc_data
            continue
        else:
            count_ok += 1
            print(f'SLC shape: {slc_data.shape} matches nrows {nlines} and range bins {rgbins}\nFile:{slcfile}\n')
            del slc_data
    
    print(f'SUMMARY: Total SLCs in folder: {len(SLCfiles)}. Num of SLCs with correct sizes: {count_ok}. Num of SLCs with incorrect sizes: {count_bad}')
    if count_bad > 0:
        bad_slcfiles_str = '\n'.join([str(x) for x in slcfiles_bad])
        print(f"SLC files with not matching sizes with PRMs: \n{bad_slcfiles_str}")


def get_args():
    mess = "checks dimensions of SLC based on PRM file in a directory. It needs PRM and SLC files"

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

