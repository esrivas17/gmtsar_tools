#!/usr/bin/env python
import argparse
from pathlib import Path
from netCDF4 import Dataset as NetCDFFile
import numpy as np
import h5py as h5
import subprocess
from utils import headingFromLED
from mintpy.utils import readfile


"""
geometryRadar.h5 needs : azimuthAngle, height, incidenceAngle, latitude, longitude, shadowMask, slantRangeDistance
"""

grdGeometryFiles = {'azimuthAngle':'azimuth.grd', 'incidenceAngle':'incidence.grd', 'latitude':'latitude.grd', 
                    'longitude':'longitude.grd', 'height':'topo_ra_full.grd', 'slantRangeDistance':'slantRange.grd',
                    'shadowMask':''}

def main(*, topopath: Path):
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

    # Getting metadata
    meta = get_metadata(topopath)

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
        # Metadata
        print(f'Writing Metadata...')
        for key in meta.keys():
            dst.attrs[key] = meta[key]        


def get_metadata(topopath: Path):
    # Check master PRM
    masterPRM = topopath.joinpath('master.PRM')
    if not masterPRM.exists():
        raise Exception('master.PRM seems not to exist. Please check')
    # Read and add parameters to meta
    meta = readfile.read_gmtsar_prm(masterPRM)

    # Check if LED is in folder
    grepOut = subprocess.run(['grep', 'led_file', masterPRM.as_posix()], capture_output=True, text=True)
    LEDfile = topopath.joinpath(grepOut.stdout.split("=")[1].strip())
    if not LEDfile.exists():
        raise Exception('Seems that LED file does not exist. Please check')
    meta['HEADING'] = headingFromLED(LEDfile)
    meta['AZIMUTH_PIXEL_SIZE'] *= int(meta['ALOOKS'])
    meta['RANGE_PIXEL_SIZE'] *= int(meta['RLOOKS'])

    # Getting info from topo, inc and slantrange grd files
    topoInfo = subprocess.run(['gmt', 'grdinfo',  topopath.joinpath('topo_ra_full.grd').as_posix(), '-C'], capture_output=True, text=True)
    meta['starting_azimuth_line'] = topoInfo.stdout.split("\t")[1] #xmin
    meta['XMIN'] = topoInfo.stdout.split("\t")[1] 
    meta['XMAX'] = topoInfo.stdout.split("\t")[2]
    meta['YMIN'] = topoInfo.stdout.split("\t")[3]
    meta['YMAX'] = topoInfo.stdout.split("\t")[4]
    meta['ALOOKS'] = topoInfo.stdout.split("\t")[7] #xinc
    meta['RLOOKS'] = topoInfo.stdout.split("\t")[8] #yinc
    meta['WIDTH'] = topoInfo.stdout.split("\t")[9]
    meta['LENGTH'] = topoInfo.stdout.split("\t")[10]
    incInfo = subprocess.run(['gmt', 'grdinfo',  topopath.joinpath('incidence.grd').as_posix(), '-C', '-L2'], capture_output=True, text=True)
    meta['INCIDENCE_ANGLE'] = float(incInfo.stdout.split("\t")[11]) #incMean
    slantInfo = subprocess.run(['gmt', 'grdinfo',  topopath.joinpath('slantRange.grd').as_posix(), '-C', '-L2'], capture_output=True, text=True)
    meta['SLANT_RANGE_DISTANCE'] = float(slantInfo.stdout.split("\t")[11]) #slantMean
    meta['FILE_TYPE'] = 'geometry'
    meta = readfile.standardize_metadata(meta)
    return meta


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
    args = get_args
    main(topopath=args.topopath)

