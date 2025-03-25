#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from matplotlib.collections import LineCollection
from datetime import datetime, date
from utils import read_baseline_table, str2date
import glob
import pdb


def main():
    args = get_args()
    baselinetab = args.baselinetable
    mintbase = args.mintempbase
    maxtbase = args.maxtempbase
    minpbase = args.minpbase
    maxpbase = args.maxpbase
    startdate = str2date(args.startdate) if args.startdate else date(1990,1,1)
    enddate = str2date(args.enddate) if args.enddate else datetime.today().date()
    slcdir = args.slcdir
    current_network = args.current_network
    exclude_intf = args.exclude_intf
    outfile = args.outfile

    if slcdir:
        slcs = glob.glob(f'{slcdir}/*.SLC')
        orb_dict = {slc.split("_")[-2]:Path(slc).stem for slc in slcs}

    data = read_baseline_table(baselinetab)
    
    fig, ax = plt.subplots(figsize=(12,8))

    yearfrac = data['aligned_time'].to_numpy()
    bperp = data.Bperp.to_numpy()
    sat_orb = data.sat_orb.to_numpy()
    xmin, xmax = yearfrac.min(), yearfrac.max()
    ymin, ymax = bperp.min(), bperp.max()

    # if I give a previous intf.in
    pairs_current_network = list()
    current_ifgs = list()
    if current_network:
        with open(current_network, 'r') as ifgs:
            print(f'Reading current network: {current_network}')
            for pair in ifgs:
                current_ifgs.append(pair)
                master, slave = pair.strip().split(":")
                orbmaster = master.split("_")[-2]
                orbslave = slave.split("_")[-2]
                row_master = data.loc[data.sat_orb == orbmaster]
                row_slave = data.loc[data.sat_orb == orbslave]
                bperp1, bperp2 = row_master['Bperp'].values[0], row_slave['Bperp'].values[0]
                p1 = [row_master['aligned_time'].values[0], bperp1]
                p2 = [row_slave['aligned_time'].values[0], bperp2]
                pairs_current_network.append([p1,p2])

    intf_in = list()
    pairs = list()
    
    # Making network
    for im1, im2 in sorted(combinations(data.sat_orb.to_list(), 2)):
        row_im1 = data.loc[data.sat_orb == im1]
        row_im2 = data.loc[data.sat_orb == im2]
        bperp1, bperp2 = row_im1['Bperp'].values[0], row_im2['Bperp'].values[0]
        t1, t2 = row_im1['aligned_days'].values[0], row_im2['aligned_days'].values[0]
        dt1 = row_im1['date_dt'].values[0]
        if dt1 > startdate and dt1 <= enddate:
            if t1 < t2 and t2 - t1 < maxtbase and t2 - t1 >= mintbase:
                if abs(bperp2 - bperp1) < maxpbase and abs(bperp2 - bperp1) >= minpbase:
                    p1 = [row_im1['aligned_time'].values[0], bperp1]
                    p2 = [row_im2['aligned_time'].values[0], bperp2]
                    if slcdir:
                        stem_pair = f'{orb_dict[im1]}:{orb_dict[im2]}'
                        if stem_pair in current_ifgs:
                            print(f'Pair {stem_pair} in {current_ifgs}, skip')
                            continue
                        else:
                            intf_in.append(stem_pair)
                    pairs.append([p1,p2])
    
    # Excluding intf
    if exclude_intf:
        if exclude_intf.exists():
            exclude_ifgs = ifgs_to_exclude(exclude_intf)

    # writing intf.in
    if intf_in:
        with open(outfile, 'w') as f:
            print(f'Writing {outfile}...')
            for intf in intf_in:
                if exclude_intf:
                    if intf not in exclude_ifgs:
                        f.write(f'{intf}\n')
                else:
                    f.write(f'{intf}\n')

        print(f'{outfile} written\n')

    # dates
    if slcdir:
        dates = [orb_dict[orb][14:22]for orb in sat_orb]

    # Making collection from a list of list containing two points
    collection = LineCollection(pairs, colors='orangered', linewidths=0.6, alpha=0.7, linestyle='solid', label='network')
    xticks = np.arange(int(np.floor(xmin)), int(np.ceil(xmax)+1), 0.5)
    yticks = np.arange(ymin - (ymin%50), ymax + (100 - ymax%50), 50)
    ax.scatter(yearfrac, bperp, marker='o', c='blue', s=14)
    ax.add_collection(collection)
    title = f'Num of ifgs: {len(pairs)}'

    if pairs_current_network:
        current_net_collection = LineCollection(pairs_current_network, colors='violet', linewidths=0.6, alpha=0.7, linestyle='dashed', label='current')
        ax.add_collection(current_net_collection)
        title = title + f' - current net ifgs: {len(pairs_current_network)}'
    
    ax.set_title(title)
    ax.set_xlabel(f'Time')
    ax.set_ylabel(f'Baseline (m)')
    ax.tick_params(axis='x', labelrotation=40)
    ax.set_yticks(yticks)
    ax.set_xticks(xticks)
    ax.legend()
    
    # labels
    if slcdir:
        for ix, txt in enumerate(dates):
            ax.annotate(txt, (yearfrac[ix], bperp[ix]), xytext=(2,2), textcoords='offset points', fontsize='x-small')
    else:     
        for ix, txt in enumerate(sat_orb):
            ax.annotate(txt, (yearfrac[ix], bperp[ix]), xytext=(5,5), textcoords='offset points', fontsize='x-small')

    fig.savefig('baseline_table.png')
    plt.show()


def ifgs_to_exclude(intf_file) -> list:
    ifgs_exclude = list()
    with open(intf_file, 'r') as ifgs:
            print(f'Excluding interferograms from: {intf_file}')
            for pair in ifgs:
                ifgs_exclude.append(pair.strip())
    return list(set(ifgs_exclude))


def get_args():
    mess = "Plot selected pairs based on a baseline table with matplotlib." \
    "There is an option to include a previous intf.in and add it on top of your new network of ifgs"

    example = """EXAMPLE:
       plot_network_gmtsar.py -f path/to/baseline_table.dat
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments

    parser.add_argument('-f', '--baselinetable', dest='baselinetable', type=Path, required=True, help='Path to baseline table')
    parser.add_argument('--mint',dest='mintempbase', type=int, default=0, help='Minimum temporal baseline')
    parser.add_argument('--maxt', dest='maxtempbase', type=int, required=True, help='Maximum temporal baseline')
    parser.add_argument('--minb',dest='minpbase', type=int,  default=0, help='Minimum perpendicular baseline')
    parser.add_argument('--maxb', dest='maxpbase', type=int, required=True, help='Maximum perpendicular baseline')
    parser.add_argument('--start', dest='startdate', type=str, help='Start date to create pairs. format: YYYYMMDD')
    parser.add_argument('--end', dest='enddate', type=str, help='End date to create pairs. format: YYYYMMDD' )
    parser.add_argument('--slc', dest='slcdir', type=str, help='Directory of coregistered SLC, optional for writing a intf.in')
    parser.add_argument('--intf', dest='current_network', type=Path, help='Path to intf.in if you have one. It will be plot on top of your network')
    parser.add_argument('--exclude_intf', dest='exclude_intf', default=None, type=Path, help='It will take ifgs from this file to prevent writing them in the new outfile intf.in')
    parser.add_argument('--outfile', type=str, dest='outfile', default='ifgs.in', help='Name for output file with intfs, slcdir needs to be define. Default: ifgs.in')
    return parser.parse_args()


if __name__ == "__main__":
    main()

