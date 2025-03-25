#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from utils import grep
import subprocess
import os
import pdb

supported_formats = [".E1", ".E2", ".N1"]
GMTSAR_orbits = '/home/erikr/orbits'

def main():
    args = get_args()
    projdir = args.projdir
    orbitsdir = args.orbitsdir

    rawdir = projdir.joinpath("raw")
    rawfiles = list()

    # Change directory otherwise these commands do not work
    os.chdir(rawdir)

    for format in supported_formats:
        files = glob.glob(f'*{format}')
        rawfiles.extend(files)
    
    
    for rawfile in [Path(x) for x in rawfiles]:
        print(f'File: {rawfile}')
        suffix = rawfile.suffix
        rawstem = rawfile.stem
        if suffix not in supported_formats:
            raise Exception(f'No support for format {suffix} from file {rawfile}')
        elif suffix == '.E1':
            ers1_orbit_dir = orbitsdir.joinpath('ERS/ers1')
            args = ['dump_orbit_ers.pl', rawstem, ers1_orbit_dir.as_posix()]
        elif suffix == '.E2':
            ers2_orbit_dir = orbitsdir.joinpath('ERS/ers2')
            args = ['dump_orbit_ers.pl', rawstem, ers2_orbit_dir.as_posix()]
        elif suffix == '.N1':
            print(f'Envisat orbits not implemented in this script, first use envisat_slc_decode')
            continue
            envisat_orbit_dir = orbitsdir.joinpath('ENVI/Doris')
            args = ['dump_orbit_envi.pl', rawstem, envisat_orbit_dir.as_posix()]
        
        output = subprocess.run(args, capture_output=True, text=True)
        if output.stderr:
            raise Exception(f'Error running dump orbit script: {output.stderr}')
        if output.returncode == 0:
            grep_out = subprocess.run(['grep', 'Case'], input=output.stdout, capture_output=True, text=True)
            case = int(grep_out.stdout.strip().split()[1].split(":")[0])
            if case == 0:
                print(f'Orbit file NOT FOUND -> File: {rawfile}\n')
            elif case == 1:
                grep_case1 = subprocess.run(['grep', 'Orbit'], input=output.stdout, capture_output=True, text=True)
                orbitfile = grep_case1.stdout.strip().split("\n")[-2]
                print(f'One Orbit file found: {orbitfile}\n')
            elif case == 2:
                but_clause = subprocess.run(['grep', 'but no'], input=output.stdout, capture_output=True, text=True)
                if but_clause.stdout:
                    print(f'Seems like {rawfile} needs two orbit files but one file is not continuous')
                    print(f'Run: {" ".join(args)}\n')
                else:
                    grep_case2 = subprocess.run(['grep', 'orbit files'], input=output.stdout, capture_output=True, text=True)
                    orbitfiles = grep_case2.stdout.strip().split()[-2:]
                    print(f'Two files found: {", ".join(orbitfiles)}\n')
            else:
                print(f'No case written')
                print(f'Run: {" ".join(args)}\n')


def get_args():
    mess = "Check orbit files in raw directory for GMTSAR"

    example = """EXAMPLE:
       check_orbits.py -p path/to/projectdir
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('-p', '--projectdir', dest='projdir', required=True, type=Path, help='Path to project directory')
    parser.add_argument('--orbitsdir', dest='orbitsdir', default=GMTSAR_orbits, type=Path, help='Orbits directory for ENVISAT or ERS e.g. /home/rivas/orbits')
    return parser.parse_args()

if __name__ == "__main__":
    main()
