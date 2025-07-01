#!/usr/bin/env python

import os
from netCDF4 import Dataset as NetCDFFile
import matplotlib.pyplot as plt
import numpy as np
import argparse
from pathlib import Path
from typing import Union
import pdb

#         colormap = 'terrain'
#         minv = np.min(z) - 100
#         maxv = np.max(z) + 100


def main(*, filepath: Path, cmap: str, minmaxv: list, figsize: tuple, aspect: Union[None, float], title: str, xlabel: str, 
         ylabel: str, llflag: bool, flipy: bool, flipx: bool, showflag: bool=True):
    aspect = aspect if aspect else 'auto'
    vmin, vmax = minmaxv

    if not filepath.exists():
        raise Exception(f'This file does not exist: {filepath}')
    
    if not title:
        title = filepath.name()

    # open grd file
    nc = NetCDFFile(filepath.as_posix())
    if llflag:
        x = nc.variables['lon'][:]
        y = nc.variables['lat'][:]
        z = nc.variables['z'][:]

    else:
        x = nc.variables['x'][:]
        y = nc.variables['y'][:]
        z = nc.variables['z'][:]
        
    if vmin is None and vmax is None:
        vmin = np.min(z)
        vmax = np.max(z)

    # PLOT
    fig, ax = plt.subplots(figsize=figsize, constrained_layout=True)
    im = ax.imshow(z, extent=[np.min(x), np.max(x), np.min(y), np.max(y)], cmap=cmap, 
                       aspect=aspect, interpolation='nearest', vmin=vmin, vmax=vmax)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if flipx:
        plt.gca().invert_xaxis()
    if flipy:
        plt.gca().invert_yaxis()

    if showflag:
        plt.show()
    else:
        return ax


def get_args():
    mess = "View grd files from GMTSAR with matplotlib"

    example = """EXAMPLE:
       grdv.py /path/to/file --ll -v 12 12 -c viridis -t mytitle --aspect 0.2 --figsize 8 8 --flipy --flix
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('grdpath', type=Path, help='Path to grd file')
    # Optional
    parser.add_argument('-v', dest='minmaxv', nargs=2, type=float, default=[None, None], help='min and max values: -5 5')
    parser.add_argument('--ll', dest='llflag', action='store_true', default=False, help='Georeferenced grid (lon, lat)')
    parser.add_argument('--xlabel', dest='xlabel', default='x', type=str, help='x axis label')
    parser.add_argument('--ylabel', dest='ylabel', default='y', type=str, help='y axis label')
    parser.add_argument('-c', '--cmap', dest='cmap', default='jet', help='Cmap, by default jet, terrain for DEM')
    parser.add_argument('-t', '--title', dest='title', type=str, help='Title for plot')
    parser.add_argument('--aspect', dest='aspect', type=float, help='Aspect value, by default auto')
    parser.add_argument('--figsize', dest='figsize', nargs=2, type=int, default=[6, 6], help='figsize, default: 10 10')
    parser.add_argument('--flipy', dest='flipy', action='store_true', default=False, help='Flips Y axis')
    parser.add_argument('--flipx', dest='flipx', action='store_true', default=False, help='Flips X axis')
    return parser.parse_args()



if __name__ == "__main__":
    args = get_args()
    main(filepath=args.grdpath, cmap=args.cmap, minmaxv=args.minmaxv, figsize=tuple(args.figsize), aspect=args.aspect, 
         title=args.title, xlabel=args.xlabel, ylabel=args.ylabel, llflag=args.llflag, flipy=args.flipy, flipx=args.flipx)