#!/usr/bin/env python
import argparse
from pathlib import Path
import glob
from utils import grep
import numpy as np
import matplotlib.pyplot as plt
import pdb


def main():
    args = get_args()
    directory = args.directory
    filepath = args.filepath
    showflag = args.showflag
    savedir = args.savedir
    band = args.band
    overwriteflag = args.overwrite

    if band is None:
        band = ['phase', 'magnitude', 'normmagnitude']
    else:
        band = [band]

    if not savedir.exists():
        savedir.mkdir()
    
    if directory:
        if not directory.exists():
            raise Exception(f"SLC directory: {directory} does not exist")
    
        slcfiles = glob.glob(f'{directory.as_posix()}/*.SLC')
        slcfiles = sorted([Path(x) for x in slcfiles])

        slcfiles_exceptions = list()
        count = 0
        count_badfiles = 0
        totalslcs = len(slcfiles)
        for slcfile in slcfiles:
            prmfile = slcfile.with_suffix('.PRM')
            r = plot_slc(slcfile, prmfile, savedir, band, showflag, overwriteflag)
            if r != 0:
                slcfiles_exceptions.append(slcfile)
                count_badfiles += 1
                print(f"Something wrong with plot_slc function\nArguments: {slcfile, prmfile, savedir}. Skipping...")
            else:
                count += 1
        print(f"SUMMARY: Num of SLCs: {totalslcs}. Num of plots creates: {count}. Num of dates with issues: {count_badfiles}")
        if count_badfiles > 0:
            bad_slcfiles_str = '\n'.join([str(x) for x in slcfiles_exceptions])
            print(f"SLC files with issues: \n{bad_slcfiles_str}")
        return 0
    
    elif filepath:
        if filepath.suffix != '.SLC':
            raise(f'File path seems not to be a SLC file: {filepath}')

        prmfile = filepath.with_suffix('.PRM')
        r = plot_slc(filepath, prmfile, savedir, band, showflag, overwriteflag)
        if r != 0:
            raise Exception(f"Something wrong with plot_slc function\nArguments: {filepath, prmfile, savedir}")

        return 0
    else:
        raise Exception(f'Why I am here?')


def plot_slc(slcfile:Path, prmfile:Path, savedir:Path, bands: list, showflag=False, overwriteflag=False):
    if 'phase' in bands:
        phasefilename = savedir.joinpath(slcfile.stem + '_pha.png')
        if phasefilename.exists():
            print(f'File: {phasefilename} already exists')
            if overwriteflag:
                print("Overwriting plot...")
                plotphase = True
            else:
                plotphase = False
        else:
            plotphase =True
    else:
        plotphase = False

    if 'magnitude' in bands:
        magnitudefilename = savedir.joinpath(slcfile.stem + '_mag.png')
        if magnitudefilename.exists():
            print(f'File: {magnitudefilename} already exists')
            if overwriteflag:
                print("Overwriting plot...")
                plotmagn = True
            else:
                plotmagn = False
        else:
            plotmagn =True
    else:
        plotmagn = False

    if 'normmagnitude' in bands:
        normalizedmagfilename = savedir.joinpath(slcfile.stem + '_norm.png')
        if normalizedmagfilename.exists():
            print(f'File: {normalizedmagfilename} already exists')
            if overwriteflag:
                print("Overwriting plot...")
                plotnormmag = True
            else:
                plotnormmag = False
        else:
            plotnormmag =True
    else:
        plotnormmag = False

    if not any([plotphase, plotmagn, plotnormmag]):
        print(f'Skipping plots..')
        return 0
    
    slcstem = slcfile.stem
    print(f'PRM file: {prmfile}')
    #Get rows and columns
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

    # Reshape SLC
    slc_data = np.fromfile(slcfile, dtype=np.int16)
    slc_data = slc_data.astype(np.float32).view(np.complex64)
    try:
        slc_data = slc_data.reshape((nlines,rgbins))
    except ValueError as e:
        print(f'Problem reshaping slc. PRM file: {prmfile}\nException: {e}')
        return -1
    phase = np.angle(slc_data)
    magnitude = np.abs(slc_data)
    magnitude_log = np.log1p(magnitude)

    print("="*20,"Plotting","="*20)

    # Phase
    if plotphase:
        fig_phase, ax_phase = plt.subplots(1,1, figsize=(10,8))
        cax_phase = ax_phase.imshow(phase, cmap="hsv", vmin=-np.pi, vmax=np.pi, aspect="auto")
        ax_phase.set_title(f'Phase: {slcstem}')
        ax_phase.set_ylabel('Range')
        ax_phase.set_xlabel('Azimuth')
        fig_phase.colorbar(cax_phase, ax=ax_phase, label='rad')
        fig_phase.savefig(f'{phasefilename}')
        print(f'Phase plot save as: {phasefilename}')

    # Magnitude
    if plotmagn:
        fig_mag, ax_mag = plt.subplots(1,1, figsize=(10,8))
        vmin, vmax = np.percentile(magnitude_log, [1, 99])  # Clip 1st and 99th percentile
        cax_mag = ax_mag.imshow(magnitude_log, cmap="gray", aspect="auto", vmin=vmin, vmax=vmax)
        ax_mag.set_title(f'Magnitude: {slcstem}')
        ax_mag.set_ylabel('Range')
        ax_mag.set_xlabel('Azimuth')
        fig_mag.colorbar(cax_mag, ax=ax_mag)
        fig_mag.savefig(f'{magnitudefilename}')
        print(f'Magnitude plot save as: {magnitudefilename}')

    # Normalized Magnitude
    if plotnormmag:
        norm_magnitude = magnitude / magnitude.max()  # Scale between 0 and 1
        norm_magnitude_log = np.log1p(norm_magnitude * 1000)  # Scale to improve visibility
        fig_nmag, ax_nmag = plt.subplots(1,1, figsize=(10,8))
        cax_nmag = ax_nmag.imshow(norm_magnitude_log, cmap="gray", aspect="auto")
        ax_nmag.set_title(f'Normalized Magnitude: {slcstem}')
        ax_nmag.set_ylabel('Range')
        ax_nmag.set_xlabel('Azimuth')
        fig_nmag.colorbar(cax_nmag, ax=ax_nmag)
        fig_nmag.savefig(f'{normalizedmagfilename}')
        print(f'Normalized magnitude plot save as: {normalizedmagfilename}\n')

    if showflag:
        plt.show()
    else:
        plt.close()

    return 0
    
    # 
    # Creating figure
    #fig, axs = plt.subplots(3,3,figsize=(10, 8),constrained_layout=True, sharex=True, sharey=True)
    #fig.suptitle(f'Cumulative displacements')


def get_args():
    mess = "Plots Magnitude, Normalize Magnitude and Phase from SLCs in directory. Each SLC must have a PRM file, optionally to plot one single SLC"

    example = """EXAMPLE:
       plot_slc.py -d path/to/directory --savedir /path/to/save
       plot_slc.py -f path/to/file --savedir /path/to/save 
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    inputgroup = parser.add_mutually_exclusive_group(required=True)
    inputgroup.add_argument('-d', '--directory', dest='directory', type=Path, help='Path to directory with SLCs and PRMs')
    inputgroup.add_argument('-f', '--filepath', dest='filepath', type=Path, help='Path to SLC file')
    parser.add_argument('-s', '--savedir', type=Path, dest='savedir', help='Path to directory to save figures')
    parser.add_argument('--showflag', action='store_true', default=False, help='show flag')
    parser.add_argument('--band', dest='band', choices=['phase', 'magnitude', 'normmagnitude'], default=None, help='Choose what to plot, choices: phase, magnitude, normmagnitude. By default it plots the 3 f them')
    parser.add_argument('--ow', dest='overwrite', action='store_true', default=False, help='If set overwrites plots, default False')
    return parser.parse_args()


if __name__ == "__main__":
    main()

