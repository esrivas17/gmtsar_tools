#!/usr/bin/env python

from netCDF4 import Dataset as NetCDFFile
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
from matplotlib import path
import numpy as np
import argparse
from pathlib import Path
from typing import Union
import pdb


def main(*, filepath: Path, outfile: Path, cmap: str, figsize: tuple, aspect: Union[None, float], title: str, flipy: bool, flipx: bool, plotmask: bool=True):
    
    aspect = aspect if aspect else 'auto'

    if not filepath.exists():
        raise Exception(f'This file does not exist: {filepath}')
    
    # open grd file
    nc = NetCDFFile(filepath.as_posix())
    x = nc.variables['x']
    y = nc.variables['y']
    z = nc.variables['z'][:]

    vmin = np.min(z)
    vmax = np.max(z)

    # PLOT
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(z, cmap=cmap, aspect=aspect, vmin=vmin, vmax=vmax)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    ax.set_title(title)
    ax.set_xlabel(x.name)
    ax.set_ylabel(y.name)

    if flipx:
        plt.gca().invert_xaxis()
    if flipy:
        plt.gca().invert_yaxis()

    maskSelect = AOIMaskSelector(z, ax, aspect)
    maskSelect.show()
    mask = maskSelect.get_mask()

    # plot mask
    if plotmask:
        fig, ax = plt.subplots(figsize=figsize)
        ax.imshow(mask, aspect=aspect)
        ax.set_title('mask')
        ax.set_xlabel(x.name)
        ax.set_ylabel(y.name)
        plt.show()

    # writing mask as grd file
    with NetCDFFile(outfile.as_posix(), 'w', format='NETCDF4') as dataset:
        startx, endx = x.actual_range
        starty, endy = y.actual_range
        # dimensions
        xdim = dataset.createDimension(x.name, len(x))
        ydim = dataset.createDimension(y.name, len(y))
        # inc
        xinc = np.diff(x[:])[0]
        yinc = np.diff(y[:])[0]
        # variables
        xvar = dataset.createVariable(x.name, x.dtype, x.dimensions)
        yvar = dataset.createVariable(y.name, y.dtype, y.dimensions)
        mask_var = dataset.createVariable('z', 'u1', (ydim,xdim))
        # Pixel node registration
        xvar[:] = np.linspace(startx+xinc/2, endx-xinc/2, len(x))
        yvar[:] = np.linspace(starty+yinc/2, endy-yinc/2, len(y))
        mask_var[:] = mask
        # attributes
        dataset.title = 'Mask'
        dataset.description = f"Mask GRD file from: {filepath.name}"
        dataset.history = "Created " + np.datetime64('today').astype(str)
        mask_var.units = "bool"

    print(f"Data saved to {outfile}")


class AOIMaskSelector:
    def __init__(self, image, ax, aspect):
        self.image = image
        self.image_shape = image.shape
        self.mask = np.zeros(self.image_shape, dtype=int)
        self.ax = ax
        self.aspect = aspect
        self.polygon = None

        # Polygon selector
        self.selector = PolygonSelector(self.ax, self.on_select, useblit=True)
        self.polygon = None

    def on_select(self, verts):
        """Callback when a polygon is selected."""
        self.polygon = np.array(verts)
        self.update_mask()

    def update_mask(self):
        """Create mask based on the selected polygon."""
        if self.polygon is None:
            return 

        # Create a mesh grid of pixel coordinates
        xs = np.arange(self.image_shape[1])
        ys = np.arange(self.image_shape[0])
        xx, yy = np.meshgrid(xs, ys)

        # Flatten and combine into (N,2) coordinate pairs
        points = np.column_stack([xx.ravel(), yy.ravel()])

        # Create a Path object and check which points are inside
        poly_path = path.Path(self.polygon)
        mask_flat = poly_path.contains_points(points)

        # Reshape mask back to the grid shape
        self.mask = mask_flat.reshape(self.image_shape)

        # Update display
        self.ax.imshow(self.mask, aspect=self.aspect, cmap='Reds', alpha=0.5)
        plt.draw()

    def get_mask(self):
        """Returns the final mask after selection."""
        return self.mask

    def show(self):
        """Show the interactive plot."""
        plt.show()


def get_args():
    mess = "generates a mask in NetCDF format based on a grid in range and azimuth coordinates. Optional args for plotting input grid"

    example = """EXAMPLE:
       mask_gmtsar.py path/to/grd -o mask.grd -c viridis --aspect 0.2 --figsize 8 8 --flipy --flix
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('grdpath', type=Path, help='Path to grd file')
    # Optional
    parser.add_argument('-o', '--outfile', dest='outfile', type=Path, default='mask.grd', help='Output file name for mask. default: mask.grd')
    parser.add_argument('-c', '--cmap', dest='cmap', default='jet', help='Cmap, by default jet')
    parser.add_argument('-t', '--title', dest='title', type=str, help='Title for plot')
    parser.add_argument('--aspect', dest='aspect', type=float, help='Aspect value, by default auto')
    parser.add_argument('--figsize', dest='figsize', nargs=2, type=int, default=[6, 6], help='figsize, default: 10 10')
    parser.add_argument('--flipy', dest='flipy', action='store_true', default=False, help='Flips Y axis')
    parser.add_argument('--flipx', dest='flipx', action='store_true', default=False, help='Flips X axis')
    parser.add_argument('--plotmask', dest='plotmask', action='store_true', default=False, help='Shows mask before saving it')
    return parser.parse_args()



if __name__ == "__main__":
    args = get_args()
    main(filepath=args.grdpath, outfile=args.outfile, cmap=args.cmap, figsize=tuple(args.figsize), aspect=args.aspect, 
         title=args.title, flipy=args.flipy, flipx=args.flipx, 
         plotmask=args.plotmask)
