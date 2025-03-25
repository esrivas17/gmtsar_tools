#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from utils import grep, run_command
import os
import pdb

suffix = "_CUT"

def main():
    args = get_args()
    directory = args.directory
    savedir = args.savedir
    cutrange = args.cutrange

    if not savedir.exists():
        savedir.mkdir()

    # Go to SLC directory
    os.chdir(directory)
    prmfiles = glob.glob('*PRM')
    num_prmfiles = len(prmfiles)
    print(f'Num of PRM files found: {num_prmfiles}')
    prmfiles = [Path(prmf) for prmf in prmfiles if Path(prmf).with_suffix('.SLC').exists()]
    num_slcfiles = len(prmfiles)
    print(f'Num of SLC files found: {num_slcfiles}')

    print("Cutting SLCs..\n")
    for prmfile in prmfiles:
        newstem = prmfile.stem + suffix
        #newprm = '../' + savedir.joinpath(newstem).as_posix()
        print(f'File: {prmfile}')
        slccut_args = ['cut_slc', prmfile.as_posix(), newstem, "/".join(cutrange)]
        if not run_command(slccut_args, check=False):
            raise Exception(f'Sth wrong from slc_cut command. Args: {" ".join(slccut_args)}')
        print('\n')
        
    cutprms = [Path(x) for x in glob.glob(f'*{suffix}*PRM')]
    cutslcs = [Path(x) for x in glob.glob(f'*{suffix}*SLC')]

    path_savedir = Path.cwd().parent.joinpath(savedir)
    if path_savedir == directory:
        raise Exception(f'We are not saving cut files in same directory')
    
    # Moving files to Savedir
    print(f"Moving files to: {path_savedir}")
    for cutprm, cutslc in zip(cutprms, cutslcs):
        newcutprm = "_".join(cutprm.stem.split("_")[:-1]) + cutprm.suffix
        newcutslc = "_".join(cutslc.stem.split("_")[:-1]) + cutslc.suffix
        cutprm.rename(path_savedir.joinpath(newcutprm))
        cutslc.rename(path_savedir.joinpath(newcutslc))

    print("Done")
    return 0


def get_args():
    mess = "Cut SLCs in folder and save them in a given directory, it makes use of cut_slc from GMTSAR"

    example = """EXAMPLE:
       cut_slc_batch.py -d path/to/projectdir -s /save/dir -c 200 2000 500 12000
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-d', '--directory', dest='directory', required=True, type=Path, help='Path to directory with SLCs to cut')
    parser.add_argument('-s', '--savedir', dest='savedir', required=True, type=Path, help='Path to directory to save cut SLCs')
    parser.add_argument('-c', '--cut', dest='cutrange', required=True, nargs=4, type=str, help='Cut range: xmin xmax ymin ymax')
    return parser.parse_args()

if __name__ == "__main__":
    main()
