#!/usr/bin/env python
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations
from matplotlib.collections import LineCollection
from datetime import datetime, timedelta
from functions import read_baseline_table
import glob
import pdb


def main():
    args = get_args()
    baseline_table = args.baseline_table
    intf_dir = args.intf_dir

    data = read_baseline_table(baseline_table)
    fig, ax = plt.subplots(figsize=(12,8))

    yearfrac = data['aligned_time'].to_numpy()
    bperp = data.Bperp.to_numpy()
    sat_orb = data.sat_orb.to_numpy()
    xmin, xmax = yearfrac.min(), yearfrac.max()
    ymin, ymax = bperp.min(), bperp.max()

    pairs = list()
    i = 0
    for intf in intf_dir.iterdir():
        print(f'Intf: {intf}')
        if intf.is_dir() and "_" in intf.name and len(intf.name.split("_")) == 2:
            prms = glob.glob(f'{intf}/*PRM')
            prms.sort(key=lambda x: datetime.strptime(x.split("/")[-1][14:22], "%Y%m%d").date())
            if len(prms) !=2:
                print(f'WARNING: PRM files in: {intf} is different from two\nPRMs: {prms}')
                continue
            masterPRM, slavePRM = prms
            orbmaster = masterPRM.split("/")[-1].split("_")[-2]
            orbslave = slavePRM.split("/")[-1].split("_")[-2]
            row_master = data.loc[data.sat_orb == orbmaster]
            row_slave = data.loc[data.sat_orb == orbslave]
            bperp1, bperp2 = row_master['Bperp'].values[0], row_slave['Bperp'].values[0]
            p1 = [row_master['aligned_time'].values[0], bperp1]
            p2 = [row_slave['aligned_time'].values[0], bperp2]
            pairs.append([p1,p2])
            i += 1

    collection = LineCollection(pairs, colors='darkorange', linewidths=0.6, alpha=0.7, linestyle='solid', label='network')
    xticks = np.arange(int(np.floor(xmin)), int(np.ceil(xmax)+1), 0.5)
    yticks = np.arange(ymin - (ymin%50), ymax + (100 - ymax%50), 50)
    ax.scatter(yearfrac, bperp, marker='o', c='violet', s=14)
    ax.add_collection(collection)
    for ix, txt in enumerate(sat_orb):
            ax.annotate(txt, (yearfrac[ix], bperp[ix]), xytext=(5,5), textcoords='offset points', fontsize='x-small')
    title = f'Num of ifgs: {len(pairs)}'
    ax.set_title(title)
    ax.set_xlabel(f'Time')
    ax.set_ylabel(f'Baseline (m)')
    ax.tick_params(axis='x', labelrotation=40)
    ax.set_yticks(yticks)
    ax.set_xticks(xticks)
    plt.show()



def get_args():
    mess = "Plot network from baseline_table.dat and intf directory"

    example = """EXAMPLE:
       plot_network_from_intf.py path/to/baseline_table.dat path/intf
        """

    parser = argparse.ArgumentParser(description=mess, epilog=example,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Positional arguments
    parser.add_argument('baseline_table', type=Path, help='Path to baseline_table.dat')
    parser.add_argument('intf_dir', type=Path, help='Path to intf directory')
    return parser.parse_args()


if __name__ == "__main__":
    main()

