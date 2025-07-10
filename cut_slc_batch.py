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
    current_cwd = Path().cwd()
    prmfiles = [Path(prmf) for prmf in glob.glob('*PRM')]
    print(f'Num of PRM files found: {len(prmfiles)}')
    slcfiles = [prmf.with_suffix('.SLC') for prmf in prmfiles if prmf.with_suffix('.SLC').exists()]
    print(f'Num of SLC files found: {len(slcfiles)}')
    ledfiles = [prmf.with_suffix('.LED') for prmf in prmfiles if prmf.with_suffix('.LED').exists()]
    print(f'Num of LED files found: {len(ledfiles)}')

    if len(prmfiles) != len(slcfiles) != len(ledfiles):
        raise Exception(f'Number of PRM, SLC and LED files do not match')

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

    # Symlinks of LED files
    for ledfile in ledfiles:
        path_savedir.joinpath(ledfile).symlink_to(current_cwd.joinpath(ledfile))

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
