import re
import subprocess
import datetime as dt
from datetime import datetime, timedelta
import numpy as np
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

