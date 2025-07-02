#!/usr/bin/env python
import os
import argparse
from pathlib import Path
from netCDF4 import Dataset as NetCDFFile
import numpy as np
import h5py as h5


"""
geomtryRadar.h5 needs : azimuthAngle, height, incidenceAngle, latitude, longitude, shadowMask, slantRangeDistance
"""

grdGeometryFiles = {'azimuthAngle':'azimuth.grd', 'incidenceAngle':'incidence.grd', 'latitude':'latitude.grd', 
                    'longitude':'longitude.grd', 'height':'topo_ra_full.grd', 'slantRangeDistance':'slantRange.grd',
                    'shadowMask':''}

def main():
    args = get_args()
    topopath = args.topopath
    topopath = topopath.resolve()

    # Check dimensions for first dataset and set it as reference
    geomf = list(grdGeometryFiles.values())[0]
    dims = NetCDFFile(topopath.joinpath(geomf).as_posix()).variables['z'].shape
    print(f'Geometry dataset dimensions: {dims}')

    for grdfile in grdGeometryFiles.values():
        if not grdfile:
            continue
        filepath = topopath.joinpath(grdfile)
        grddims = NetCDFFile(filepath.as_posix()).variables['z'].shape
        if grddims != dims:
                raise Exception(f'File: {grdfile} dimensions: {grddims} do not match with dataset dimensions: {dims}\nPlease Check')


    #   writing to h5file
    print(f'Writing geometryRadar.h5 stack')
    with h5.File('geometryRadar.h5', 'w') as dst:
        for dset, grdfile in grdGeometryFiles.items():
            print(f'Writing {dset}...')
            if dset == 'shadowMask':
                data = np.zeros(dims, dtype=bool)
                dst.create_dataset(dset, data=data, dtype=data.dtype, shape=data.shape, chunks=True, compression='lzf')
            else:
                filepath = topopath.joinpath(grdfile)
                nc = NetCDFFile(filepath.as_posix())
                data = nc.variables['z'][:]
                dst.create_dataset(dset, data=data, dtype=data.dtype, shape=data.shape, chunks=True, compression='lzf')



def get_args():
    mess = "makes geometry stack from GMTSAR topo folder to process with SARvey"

    example = """EXAMPLE:
     geometry_sarvey.py path/to/topo
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('topopath', type=Path, help='Path to topo directory')

    return parser.parse_args()


if __name__ == "__main__":
    main()

