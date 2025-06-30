import re
import subprocess
import datetime as dt
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path
import struct
import pdb


def grep(pathfile, parameter):
    output = list()
    try:
        string = subprocess.check_output(['grep', parameter, pathfile])
    except:
        return output
    else:
        string = string.decode('utf-8').strip()
        list_string = re.split(r"\s{1,}", string)
        for element in list_string:
            try:
                float(element)
            except:
                pass
            else:
                output.append(element)

    if len(output) == 1:
        output = output[0]

    return output

def str2date(strdate: str) -> dt.date:
    if len(strdate) != 8:
        raise Exception(f'String can not be changed to datetime format: {strdate}')
    else:
        return dt.date(int(strdate[:4]), int(strdate[4:6]), int(strdate[6:]))
    

def try_command(cmd_list):
    try:
        r = subprocess.check_call(cmd_list)
    except subprocess.CalledProcessError as e:
        print(f'Command: {" ".join(cmd_list)} FAILED\nException: {e}')
        return False
    else:
        if r != 0:
            print(f'Problem found in running: {" ".join(cmd_list)}')
            return False
        else:
            return True


def run_command(cmd_list, check=False):
        try:
            r = subprocess.run(cmd_list, check=check)
        except subprocess.CalledProcessError as e:
            print(f'Command: {" ".join(cmd_list)} FAILED\nException: {e}')
            return False
        else:
            return True


def fracyear2yyyymmdd(fracyear: float):
    """
    Converts yyyyddd.dddd to yyyymmdd
    """
    year = int(fracyear//1000)
    day_year = int(fracyear%1000)
    datet = datetime(year, 1, 1) + timedelta(days=day_year - 1)
    return datet.date()

def read_baseline_table(baselinetab: Path):
    data = pd.read_csv(baselinetab, sep=" ", header=None, dtype={0:str})
    rows, cols = data.shape
    print(f"Data with {rows} rows")
    if cols == 5:
        data.columns = ["sat_orb", "aligned_time", "aligned_days", "Bpl", "Bperp"]
    elif cols == 7:
        data.columns = ["sat_orb", "aligned_time", "aligned_days", "Bpl", "Bperp", "xshift", "yshift"]
    else:
        raise Exception(f"Unexpected number of columns: {data.columns}")
    
    data['date_dt'] = data.aligned_time.apply(fracyear2yyyymmdd)
    data['aligned_time'] = data.aligned_time.apply(lambda x: (x%1000)/365.25 + int(x/1000))
    dfsorted = data.sort_values(by='date_dt')
    return dfsorted

def getSlcData(slcPath, prmPath):
    #Get rows and columns
    nlines = int(grep(prmPath, 'num_lines'))
    rgbins = int(grep(prmPath, 'num_rng_bins'))
    # read slc and reshape
    slc_data = np.fromfile(slcPath, dtype=np.int16)
    slc_data = slc_data.astype(np.float32).view(np.complex64)
    try:
        slc_data = slc_data.reshape((nlines,rgbins))
    except ValueError as e:
        print(f'Problem reshaping slc. PRM file: {prmPath}\nException: {e}')
        return -1
    else:
        return slc_data
                        
def readOldGMTFormat(grd, offset=892):
    """
    Function to read real.grd and imag.grd that have the old style native grid format with an offset of 892
    and format defined in:
    https://docs.generic-mapping-tools.org/6.2/cookbook/file-formats.html
    """
    parms = ["n_columns", "n_rows", "registration", "x_min", "x_max", "y_min", "y_max", "z_min", "z_max", 
             "x_inc", "y_inc", "z_scale_factor", "z_add_offset", "x_units", "y_units", "z_units", "title", "command", "remark"]
    
    strparms = ["x_units", "y_units", "z_units", "title", "command", "remark"]]

    fmt = '=3i 10d 80s 80s 80s 80s 320s 160s'
    if struct.calcsize(fmt) != offset:
        raise Exception(f"Header offset seems to be different from defined structure")
    
    # Headers
    with open(grd, "rb") as f:
        headerBytes = f.read(offset)

    headerTup = struct.unpack(fmt, headerBytes)
    headerDict = {k:v for k,v in zip(parms,headerTup)}

    # decoding string parameters
    for parm in strparms:
        if parm in headerDict.keys():
            headerDict[parm] = headerDict[parm].decode('ascii').strip('\x00')

    # Getting and reshaping data
    data = np.fromfile(grd, dtype=np.float32, offset=offset)
    data = data.reshape((headerDict['n_rows'], headerDict['n_columns']))

    return data, headerDict