#!/usr/bin/env python3
from glob import glob

from logging import config
import os 
from datetime import datetime
import pdb 
import sys
import itertools
#from networkx import config
import numpy as np
from multiprocessing import Pool
import argparse
import re 
import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np
import subprocess
from datetime import timedelta
import json
import matplotlib.dates as mdates
from contextlib import redirect_stdout
import shutil
import subprocess
try:
    import py_gamma as pg
except ImportError:
    print("py_gamma module not found. Please install it to use this script.")
    sys.exit(1)
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def construct_date1_date2_combinations(config,n_days,date_min,date_max,step1=False):
    date_list = []
    topdir = config['topdir']
    slc_dir = config['slc_dir']
    min_n_days = config['min_n_days']

    no_important_date = True
    if "important_date" in config:
        important_date = config["important_date"]
        no_important_date = False

    if 'rslc_dates' in config:
        rslc_dates = config['rslc_dates'] 
    else:
        rslc_dates = False
    # how to search for yyyymmddT in filename 

    # check if config['rlc_for_dates'] is true, y names.

   
          
    print('Using h5s to find dates')
    search_list = glob(os.path.join(topdir,'h5s','*'))
    date_list = [os.path.split(file)[-1] for file in search_list]
    date_list = [date for date in date_list if 'M' not in date]


                
    date_array = np.array(date_list)
    # remove repeated dates
    date_array = np.unique(date_array)
    # sort date array min to max
    date_array_sorted = np.sort(date_array)
    date_array_sorted = np.sort(date_array)
    
    

 
    # Check if date_list contains repeats
    # If it does, print a warning and exit the program
    # Otherwise, print the list of dates
    if len(date_list) != len(set(date_list)):
        print(bcolors.WARNING+"Warning: The date list contains repeated dates."+bcolors.ENDC)
        #find repeated dates and print the file path to repeated date 
        for date in set(date_list):
            if date_list.count(date) > 1:
                print(f"Repeated date: {date}")

    else:
        print(bcolors.OKGREEN+"The date list is:"+bcolors.ENDC)
        print(date_list) 
    

    if step1 and len(date_array_sorted) ==1:
        print(bcolors.WARNING+"Warning: Less than 2 unique dates found. Please check your data."+bcolors.ENDC)
        dates1 = list(date_array_sorted)
        dates2 = []
        return dates1,dates2
    #print(date_list)    
    # Initialize lists to store paired dates
    dates1 = []
    dates2 = []
    
    # Use itertools.combinations to generate all possible pairs
    combinations = itertools.combinations(date_array_sorted, 2)
    # Ensure each pair is ordered from earliest to latest
    date_pairs = [(min(date1, date2), max(date1, date2)) for date1, date2 in combinations]
    date_pairs = sorted(date_pairs, key=lambda x: datetime.strptime(x[0], '%Y%m%d'))
    for date1, date2 in date_pairs:
        
        # if no_important_date == false, then check if dates span the important date 
        if no_important_date == False:
         
            important_date_dt = datetime.strptime(important_date, '%Y%m%d')
            date1_dt = datetime.strptime(date1, '%Y%m%d')
            date2_dt = datetime.strptime(date2, '%Y%m%d')
            if not (date1_dt < important_date_dt < date2_dt):
                print(f"Skipping pair {date1} - {date2} as it does not span important date {important_date}")
                continue

        if check_dates(date1, date2, date_min, date_max):
            print(f"Checking  pair {date1} - {date2}")
            date1_dt = datetime.strptime(date1, '%Y%m%d')
            date2_dt = datetime.strptime(date2, '%Y%m%d')
    
            # Calculate the difference in days between the two dates
            delta = abs((date2_dt - date1_dt).days)
            if min_n_days <= delta <= n_days:
                dates1.append(date1)
                dates2.append(date2)

            else:
                print(f"Skipping pair {date1} - {date2}")
        

       
    return dates1,dates2
def check_dates(date1_str, date2_str, date_min_str, date_max_str):
    # Define the date format
    date_format = "%Y%m%d"
    
    try:
        # Convert date strings to datetime objects
        date1 = datetime.strptime(date1_str, date_format)
        date2 = datetime.strptime(date2_str, date_format)
        date_min = datetime.strptime(date_min_str, date_format)
        date_max = datetime.strptime(date_max_str, date_format)
        
        # Perform the checks
        is_date1_not_equal_date2 = date1 != date2
        is_date1_before_date2 = date1 < date2
        is_date1_in_range = date_min < date1 < date_max
        is_date2_in_range = date_min < date2 < date_max 
        # Create a dictionary to store the results of the checks
        check_results = {
            "date1": date1_str,
            "date2": date2_str,
            "is_date1_not_equal_date2": is_date1_not_equal_date2,
            "is_date1_before_date2": is_date1_before_date2,
            "is_date1_in_range": is_date1_in_range,
            "is_date2_in_range": is_date2_in_range
        }

        # Write the results to a text file
        with open("date_checks.txt", "a") as file:
            file.write(f"{check_results}\n")
        
        if is_date1_before_date2 and is_date1_in_range and is_date2_in_range and is_date1_not_equal_date2:
            return True
        else:
            return False
            
    except ValueError as e:
        # Handle invalid date formats
        print(f"Error: {e}")
        return False

def validate_dates(dateM, date1, date2):
    # Validate dateM: it must be either an 8-digit string or a list of length 1 containing an 8-digit string.
    if isinstance(dateM, list):
        if len(dateM) == 1 and isinstance(dateM[0], str) and len(dateM[0]) == 8 and dateM[0].isdigit():
            dateM = dateM[0]  # Convert list of length 1 to an 8-digit string
        else:
            raise ValueError("dateM must be a list of length 1 containing an 8-digit string or an 8-digit string.")
    elif isinstance(dateM, str):
        if not (len(dateM) == 8 and dateM.isdigit()):
            raise ValueError("dateM must be an 8-digit string.")
    else:
        raise TypeError("dateM must be either a string or a list of length 1.")

    # Validate that date1 and date2 are lists of equal length and each element is an 8-digit string.
    if not (isinstance(date1, list) and isinstance(date2, list)):
        raise TypeError("date1 and date2 must both be lists.")

    if len(date1) != len(date2):
        raise ValueError("date1 and date2 must be of equal length.")

    for d1, d2 in zip(date1, date2):
        if not (isinstance(d1, str) and isinstance(d2, str) and len(d1) == 8 and len(d2) == 8 and d1.isdigit() and d2.isdigit()):
            raise ValueError("Each element of date1 and date2 must be an 8-digit string.")

    # Return the validated and possibly modified dateM
    return dateM

def h5_to_slc(date,config):
    print('in h5_to_slc')
    slc_dir = config['slc_dir']
    dim_dir = config['dim_dir']
    topdir = config['topdir']
    dateM = config['dateM']
    os.chdir(topdir)

    # check if file has been processed previously and the file is in same orbit direction as master 
    

        
    if os.path.exists(os.path.join(slc_dir,date)):
        print(bcolors.WARNING + f"Skipping {date} as SLC directory already exists"+bcolors.ENDC)
        return
    else:
        os.makedirs(os.path.join(slc_dir,date))
    
    
    date_h5 = glob(os.path.join(topdir,'h5s','*',f'*{date}*h5'))[0]
    print('date_h5:',date_h5)

  

    pg.par_NISAR_RSLC(date_h5,f'{date}',2,'-','L','A','HH',0)

    # Move slc and slc.par files to slc_dir/date/
    #find slc and slc.par files in current directory
    slc_files = glob(f'{date}_LA_HH.slc')
    slc_par_files = glob(f'{date}_LA_HH.slc.par')
    # make slc_dir/date/ if it does not exist
    if not os.path.exists(os.path.join(slc_dir,date)):
        os.makedirs(os.path.join(slc_dir,date))
        
    for slc_file in slc_files:
        shutil.move(slc_file, os.path.join(slc_dir,date,date+'.slc'))
    for slc_par_file in slc_par_files:
        shutil.move(slc_par_file, os.path.join(slc_dir,date,date+'.slc.par'))

    return 
    

def proc_master_slc(config):
    
    dateM = config['dateM']
    topdir = config['topdir']
    slc_dir = config['slc_dir'] 
    os.chdir(topdir)

    if not os.path.exists(slc_dir):
        os.makedirs(slc_dir)

    h5_to_slc(dateM, config)

    # Create master date folder to be used as non-master date
    pg.multi_look(os.path.join(slc_dir,f'{dateM}/{dateM}.slc'),     #input slc
                 os.path.join(slc_dir,f'{dateM}/{dateM}.slc.par'), #input par
                 os.path.join(slc_dir,f'{dateM}/{dateM}.mli'),     # output mli
                 os.path.join(slc_dir,f'{dateM}/{dateM}.mli.par'), #output par
                 config["rlks"], config["azlks"]) 
    
    # Copy slc_dir/{dateM} directory to slc_dir/{dateM}M  and use as master date
    dateMM = f"{dateM}M"
    src_dir = os.path.join(slc_dir, dateM)
    dst_dir = os.path.join(slc_dir, dateMM)

    if os.path.exists(dst_dir):
        print(bcolors.WARNING + f"Directory {dst_dir} already exists. Skipping copy." + bcolors.ENDC)
    else:
        shutil.copytree(src_dir, dst_dir)
        print(bcolors.OKGREEN + f"Copied {src_dir} to {dst_dir}" + bcolors.ENDC)

    return print(bcolors.OKGREEN + 'Master SLC successfully' + bcolors.ENDC)



def dev_proc_slc_to_rslc(date, config):


    print(f"Processing SLC to RSLC for date: {date}")
    # Assign variables
    rlks, azlks, dem, demlat, demlon = config["rlks"], config["azlks"], config["dem"], config["demlat"], config["demlon"]
    npat_r, npat_az, r_init, az_init = config["npat_r"], config["npat_az"], config["r_init"], config["az_init"]
    dateM, topdir, slc_dir, dim_dir = config['dateM'], config['topdir'], config["slc_dir"], config["dim_dir"]
    cleanup = config["cleanup"]
    
    slc_date_dir = os.path.join(slc_dir,date)
    slc_dateM_dir = os.path.join(slc_dir,dateM+'M')

    rslc_dateM_dir = os.path.join(topdir, 'rslc', f'{dateM}M')
    os.makedirs(rslc_dateM_dir, exist_ok=True)


    if os.path.exists(rslc_dateM_dir):
       
        pass
    else:
        shutil.copytree(slc_dateM_dir, rslc_dateM_dir)
            # Redirect stdout to a log file
        log_file = os.path.join(config['topdir'], f'proc_slc_to_rslc_{date}.log')
    os.makedirs(os.path.join(topdir, 'rslc'), exist_ok=True)

    rslc_dir = os.path.join(topdir, 'rslc')

    rslc_date_dir = os.path.join(rslc_dir, date)
    if os.path.exists(rslc_date_dir):
        print(f"Skipping SLC to RSLC for date: {date}")
        return 
    else:
        os.makedirs(rslc_date_dir, exist_ok=True)


    # Coregister SLC to reference SLC using SLC_coreg
    print(bcolors.OKBLUE + 'pg.SLC_coreg()' + bcolors.ENDC)
    # Define file paths
    slc_file = os.path.join(slc_date_dir, f'{date}.slc')
    slc_par_file = os.path.join(slc_date_dir, f'{date}.slc.par')
    rslc_0_file = os.path.join(rslc_date_dir, f'{date}.0.rslc')
    rslc_0_par_file = os.path.join(rslc_date_dir, f'{date}.0.rslc.par')
    rslc_file = os.path.join(rslc_date_dir, f'{date}.rslc')
    rslc_par_file = os.path.join(rslc_date_dir, f'{date}.rslc.par')
    rmli_file = os.path.join(rslc_date_dir, f'{date}.mli')
    rmli_par_file = os.path.join(rslc_date_dir, f'{date}.mli.par')
    ref_slc_file = os.path.join(slc_dateM_dir, f'{dateM}.slc')
    ref_slc_par_file = os.path.join(slc_dateM_dir, f'{dateM}.slc.par')
    hgt_file = os.path.join(slc_dateM_dir, f'{dateM}M.hgt')  # or provide a height map if available
   

    pg.SLC_coreg(
        slc_file,
        slc_par_file,
        rslc_0_file,
        rslc_0_par_file,
        rmli_file,
        rmli_par_file,
        ref_slc_file,
        ref_slc_par_file,
        hgt_file,
        rlks,
        azlks,npoly=1
    )

    pg.SLC_coreg_refine(rslc_0_file,
                        rslc_0_par_file, 
                        rslc_file, 
                        rslc_par_file, 
                        ref_slc_file, 
                        ref_slc_par_file, 
                        rstep=50, azstep=50, rwin=128, azwin=128, n_ovr=2, cc_thres=0.05, offset_img=True
                    )

    dateM_mli_par = pg.ParFile(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'))
    lengthmli= int(dateM_mli_par.get_value('azimuth_lines')) 
    widthmli=int(dateM_mli_par.get_value('range_samples'))

   
    cleanup = config["cleanup"]

    dem_par = pg.ParFile(os.path.join(slc_dir,f'{dateM}M','P.dem_par'))	
    widthdem=int(dem_par.get_value('width'))
    
    pg.geocode_back(os.path.join(rslc_dir,date,f'{date}.mli'),
                        widthmli, 
                        os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}M.lt_fine'), 
                        os.path.join(rslc_dir,date,f'{date}_geocode.mli'), 
                        widthdem, '-', 2, 0)

    return      
def produce_geocode_hgt(
    master_date,
    mli_par_file,
    dem_par_file,
    slc_directory,
    optional_input_file=None,
    raspixavr=1,
    raspixavaz=1
):
    """
    Python version of produce_geocode_hgt.sh.
    Args:
        master_date (str): e.g. '20150708'
        mli_par_file (str): Path to MLI parameter file
        dem_par_file (str): Path to DEM parameter file
        slc_directory (str): Directory to operate in
        optional_input_file (str, optional): Optional input file
        raspixavr (int, optional): Value for rashgt (default 1)
        raspixavaz (int, optional): Value for rashgt (default 1)
    """
    # Change to SLC directory
    if not os.path.isdir(slc_directory):
        raise FileNotFoundError(f"SLC directory does not exist: {slc_directory}")
    os.chdir(slc_directory)

    dateM = f"{master_date}M"

    # Extract width from DEM parameter file
    widthdem = None
    with open(dem_par_file) as f:
        for line in f:
            if line.startswith("width:"):
                widthdem = int(line.split()[1])
            if line.startswith("width:"):    
                break

    if widthdem is None:
        raise ValueError("Could not find 'width:' in DEM parameter file.")

    # Extract range_samples from MLI parameter file
    widthmli = None
    lengthmli = None
    with open(mli_par_file) as f:
        for line in f:
            if line.startswith("range_samples:"):
                widthmli = int(line.split()[1])

            if line.startswith("azimuth_lines:"):
                lengthmli = int(line.split()[1])
            #if widthmli and lengthmli not eqaul to none then break
            if widthmli is not None and lengthmli is not None:
                break

    if widthmli is None:
        raise ValueError("Could not find 'range_samples:' in MLI parameter file.")

    print(f"DEM width: {widthdem}")
    print(f"MLI width (range samples): {widthmli}")

    # Output TIF of DEM
    #pg.rashgt(f"{dateM}.hgt", "-", widthmli, "-", "-", "-", 1, 1, "-", 1.0, 0.35, "-", f"{dateM}.hgt.tif")

    # Geocode back DEM
    pg.geocode_back(f"{dateM}.hgt", widthmli, f"{dateM}.lt_fine", f"{dateM}.hgt.geo", widthdem, "-", 0, 0)

    # Output TIF of geocoded DEM
    #pg.rashgt(f"{dateM}.hgt.geo", "-", widthdem, "-", "-", "-", raspixavr, raspixavaz, "-", 1.0, 0.35, "-", f"{dateM}.hgt.geo.tif")

    pg.data2geotiff(dem_par_file, f"{dateM}.hgt.geo", 2, f"{dateM}.hgt.geotiff.tif")

    # If optional input file is given, run rashgt again with it
    if optional_input_file and optional_input_file != slc_directory:
        print(f"Running rashgt with optional input file: {optional_input_file}")
        #pg.rashgt(f"{dateM}.hgt.geo", optional_input_file, widthdem, "-", "-", "-", 1, 1, "-", 1.0, 0.35, "-", f"{dateM}.mli.hgt.geo.tif")

def produce_lookvectors(config):

    dateM = config['dateM']
    topdir = config['topdir']
    slc_dir = os.path.join(topdir,'slcs')

    dem_par = pg.ParFile(os.path.join(slc_dir,f'{dateM}M','P.dem_par'))	
    widthdem=int(dem_par.get_value('width'))
    lengthdem = int(dem_par.get_value('nlines'))

    dateM_mli_par = pg.ParFile(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'))
    lengthmli= int(dateM_mli_par.get_value('azimuth_lines')) 
    widthmli=int(dateM_mli_par.get_value('range_samples'))

    
    dem = config["dem"]
    demlat = config["demlat"]
    demlon = config["demlon"]

    geodir = os.path.join(topdir,'geo')
    # make the geodir
    if not os.path.exists(geodir):
        os.makedirs(geodir)

    slcMdir = os.path.join(topdir,'slcs',f'{dateM}M')
    slcMpar = os.path.join(slcMdir,f'{dateM}'+'.slc.par')

    u = os.path.join(topdir,'geo','u')
    #orientation angle of n 
    v = os.path.join(topdir,'geo','v')
    #local incidence angle
    inc = os.path.join(topdir,'geo','inc')
    #projection angle
    psi = os.path.join(topdir,'geo','psi')
    #pixel area normalization factor
    pix = os.path.join(topdir,'geo','pix')
    #layover and shadow map
    lsmap = os.path.join(topdir,'geo','ls_map')

    pg.gc_map(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'), #  MLI_par         (input) ISP MLI or SLC image parameter file (slant range geometry)
                '-', 
                os.path.join(f'{topdir}/dem/{dem}.swap.dem_par'), 
                os.path.join(f'{topdir}/dem/{dem}.swap.dem'), 
                os.path.join(topdir,'slcs',f'{dateM}M',f'P.dem_par'), 
                os.path.join(topdir,'slcs',f'{dateM}M',f'P.dem'), 
                os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}M.lt'), 
                demlat, 
                demlon, 
                os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}M.sim_sar'),
                u,
                v,
                inc,
                psi,
                pix,
                lsmap,
                '8',
                '2',
                '')



    [width, length] = [widthmli,lengthmli]
    offpar = '-'

    [demwidth, demlength] =[widthdem,lengthdem]


    dem = os.path.join(slcMdir,'P.dem')
    theta = os.path.join(geodir,'theta')
    phi = os.path.join(geodir,'phi')
    lutfile = os.path.join(slcMdir,f'{dateM}M'+'.lt_fine')
    dempar = os.path.join(slc_dir,f'{dateM}M','P.dem_par')
    dem_par = pg.ParFile(dempar)	
    widthdem=int(dem_par.get_value('width'))
    lengthdem = int(dem_par.get_value('nlines'))



    pg.look_vector(slcMpar,offpar,os.path.join(slc_dir,f'{dateM}M','P.dem_par'),dem,theta,phi)

    pg.geocode(lutfile,theta,demwidth,theta+'.rc',width,length,0,0)

    pg.geocode(lutfile,phi,demwidth,phi+'.rc',width,length,0,0)

    thetarc = np.fromfile(theta+'.rc',dtype=np.float32).byteswap().reshape((int(length),int(width)))
    nanix = thetarc == 0
    thetarc[nanix] = np.nan
    phirc = np.fromfile(phi+'.rc',dtype=np.float32).byteswap().reshape((int(length),int(width)))
    phirc[nanix] = np.nan
    U = np.sin(thetarc)
    E = np.cos(phirc)*np.cos(thetarc)
    N = np.sin(phirc)*np.cos(thetarc)

    U[nanix] = 0
    E[nanix] = 0
    N[nanix] = 0
    U.byteswap().tofile(os.path.join(geodir,'U'))
    E.byteswap().tofile(os.path.join(geodir,'E'))
    N.byteswap().tofile(os.path.join(geodir,'N'))
    os.system('chmod 777 {0}'.format(os.path.join(geodir,'E')))
    os.system('chmod 777 {0}'.format(os.path.join(geodir,'N')))
    os.system('chmod 777 {0}'.format(os.path.join(geodir,'U')))
    os.remove(theta)
    os.remove(theta+'.rc')
    os.remove(phi)
    os.remove(phi+'.rc')


    lat=float(dem_par.get_value('corner_lat')[0])#`awk '$1 == "corner_lat:" {print $2}' ${procdir}/geo/EQA.dem_par`
    lon=float(dem_par.get_value('corner_lon')[0])#`awk '$1 == "corner_lon:" {print $2}' ${procdir}/geo/EQA.dem_par`
    latstep=float(dem_par.get_value('post_lat')[0])#`awk '$1 == "post_lat:" {print $2}' ${procdir}/geo/EQA.dem_par`
    lonstep=float(dem_par.get_value('post_lon')[0])#`awk '$1 == "post_lon:" {print $2}' ${procdir}/geo/EQA.dem_par`
    length_dem=int(dem_par.get_value('nlines')) #`awk '$1 == "nlines:" {print $2}' ${procdir}/geo/EQA.dem_par`
    width_dem=int(dem_par.get_value('width'))#`awk '$1 == "width:" {print $2}' ${procdir}/geo/EQA.dem_par`
    reducfac_dem = max(1, width_dem // 2000)

    lat1 = float(lat) + float(latstep) * (length_dem - 1)  # Subtract one because width starts at zero

    lon1 = float(lon) + float(lonstep) * (width_dem - 1)
    latstep = abs(float(latstep))
    lonstep = abs(float(lonstep))

    # Because no wavelength is reported in master.rmli.par file, we calculated here according to the radar frequency (IN CENTIMETERS)
    # Frequency = (C / Wavelength), Where: Frequency: Frequency of the wave in hertz (hz). C: Speed of light (29,979,245,800 cm/sec (3 x 10^10 approx))
    radar_frequency = float(dateM_mli_par.get_value('radar_frequency')[0])
    wavelength = 29979245800 / radar_frequency


    print("   Geocoding results for lookangles." )
    #psi and incidence

    if os.path.exists(psi):
        pg.geocode_back(psi, width_dem, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.psi'), width_dem, length_dem, 1, 0)
        # pg.data2geotiff(dem_par, os.path.join(geodir, f'{dateM}M.geo.psi'), 2, os.path.join(geodir, f'{dateM}M.geo.psi.tif'), 0.0)

    if os.path.exists(inc):
        pg.geocode_back(inc, width_dem, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.inc'), width_dem, length_dem, 1, 0)
        # pg.data2geotiff(dem_par, os.path.join(geodir, f'{dateM}M.geo.inc'), 2, os.path.join(geodir, f'{dateM}M.geo.inc.tif'), 0.0)

    # E-N-U
    if os.path.exists(os.path.join(geodir, 'E')):
        pg.geocode_back(os.path.join(geodir, 'E'), width, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.E'), width_dem, length_dem, 1, 0)
        pg.data2geotiff(dempar, os.path.join(geodir, f'{dateM}M.geo.E'), 2, os.path.join(geodir, f'{dateM}M.geo.E.tif'), 0.0)

    if os.path.exists(os.path.join(geodir, 'N')):
        pg.geocode_back(os.path.join(geodir, 'N'), width, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.N'), width_dem, length_dem, 1, 0)
        pg.data2geotiff(dempar, os.path.join(geodir, f'{dateM}M.geo.N'), 2, os.path.join(geodir, f'{dateM}M.geo.N.tif'), 0.0)

    if os.path.exists(os.path.join(geodir, 'U')):
        pg.geocode_back(os.path.join(geodir, 'U'), width, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.U'), width_dem, length_dem, 1, 0)
        pg.data2geotiff(dempar, os.path.join(geodir, f'{dateM}M.geo.U'), 2, os.path.join(geodir, f'{dateM}M.geo.U.tif'), 0.0)

    #hgt - not a 'look angle', but useful for LiCSBAS etc
    print('HGT file geocoding')
    if os.path.exists(os.path.join(slcMdir, f'{dateM}M.hgt')):
        print(f"Geocoding {dateM}M.hgt file")
        pg.geocode_back(os.path.join(slcMdir, f'{dateM}M.hgt'), width, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.hgt'), width_dem, length_dem, 1, 0)
        print('Finished geocoding hgt file')
        pg.data2geotiff(dempar, os.path.join(geodir, f'{dateM}M.geo.hgt'), 2, os.path.join(geodir, f'{dateM}M.geo.hgt.tif'), 0.0)
    
    # geocode back mli

    pg.geocode_back(os.path.join(slcMdir,f'{dateM}.mli'),
                        widthmli,
                        os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}M.lt_fine'),
                        os.path.join(slcMdir,f'{dateM}.geo.mli'),
                        widthdem, '-', 2, 0)
    pg.data2geotiff(dempar, os.path.join(slcMdir,f'{dateM}.geo.mli'), 2, os.path.join(slcMdir,f'{dateM}.geo.mli.tif'), 0.0)
    # use pg.SLC_ovr to over sample the rslc
    if os.path.exists(os.path.join(slcMdir, f'{dateM}.hgt')):
        pg.geocode_back(os.path.join(slcMdir, f'{dateM}.hgt'), width, os.path.join(slcMdir, f'{dateM}M.lt_fine'), os.path.join(geodir, f'{dateM}M.geo.hgt'), width_dem, length_dem, 1, 0)
        pg.data2geotiff(dempar, os.path.join(geodir, f'{dateM}M.geo.hgt'), 2, os.path.join(geodir, f'{dateM}M.geo.hgt.tif'), 0.0)

    return



def dem_to_master(config):
    
    # Sort DEM
    #----------------------------------------------------------------------------------#
    print(bcolors.OKBLUE+"Generating DEM files and lookup tables \033[0m"+bcolors.ENDC)
    dateM = config['dateM']
    topdir = config['topdir']
    slc_dir = config['slc_dir'] 
    dim_dir = config['dim_dir'] 
    og_dem_dir = config['og_dem_dir'] 
    dem = config["dem"]
    demlat = config["demlat"]
    demlon = config["demlon"]
    cleanup = config["cleanup"]

    dateM_mli_par = pg.ParFile(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'))
    lengthmli= int(dateM_mli_par.get_value('azimuth_lines')) 
    widthmli=int(dateM_mli_par.get_value('range_samples'))

    os.chdir(topdir)
    # Assign variables in config to be used in future functions 
    config['lengthmli'] = lengthmli
    config['widthmli'] = widthmli

    dem_dir = os.path.join(topdir, 'dem')
    if not os.path.exists(dem_dir):
        os.mkdir(dem_dir)
    else:
        print(bcolors.WARNING + f"DEM directory already exists at {dem_dir}. Skipping DEM generation." + bcolors.ENDC)
        dem_par = pg.ParFile(os.path.join(slc_dir,f'{dateM}M','P.dem_par'))	
        widthdem=int(dem_par.get_value('width'))

        config['widthdem'] = widthdem
        return config

    os.chdir(dem_dir)
    print('Current working directory: ', os.getcwd())
    print('Source DEM directory: ', og_dem_dir)
    dem_files = glob(os.path.join(og_dem_dir,'*',f'{dem}*'))
    print('Found DEM files: ', dem_files)
    for file in dem_files:
        if os.path.exists(os.path.join(topdir,'dem',file.split('/')[-1])):
            print(bcolors.WARNING +f'No sym link for {file}, file already exists' +bcolors.ENDC)
        else:
            print(bcolors.OKBLUE +f'sym link for {file}' +bcolors.ENDC)
            os.symlink(file,os.path.join(topdir,'dem',file.split('/')[-1]))

    print(f"Oversampling DEM {dem} by factor of {demlat} in Latitude and {demlon} in Longitude")

    # Get DEM sizes
    dem_ers_dict,[ncells,nlines,xdim,ydim,west,north] = parse_dem_ers_file(f'{topdir}/dem/{dem}.dem.ers')

    print('no. of cells: ',ncells,', nlines: ',nlines,', xdim: ', xdim, 'ydim: ',ydim, ', west: ',west,', North:', north)
    if None in [ncells, nlines, xdim, ydim, west, north]:sys.exit()

    # 2022 Update way to import DEM and apply geoid correction so relative to ellipsoid
    dem_import_dict = {'input_dem':os.path.abspath(f'{topdir}/dem/{dem}.tif'),
                'bin_dem':f'{topdir}/dem/{dem}.swap.dem',
                'dem_par':f'{topdir}/dem/{dem}.swap.dem_par',
                'input_type':0, # 0: GeoTIFF / GDAL supported raster format (default)
                'priority':1,
                'geoid': f'/gws/smf/j04/nceo_geohazards/software/GAMMA/20251203/DIFF/scripts/egm2008-5.dem',
                'geoid_par':f'/gws/smf/j04/nceo_geohazards/software/GAMMA/20251203/DIFF/scripts/egm2008-5.dem_par', 
                'geoid_type':0}

    # 2022 Update way to import DEM and apply geoid correction so relative to ellipsoid
    # dem_import $topdir/dem/$dem.tif $dem.swap.dem $dem.swap.dem_par 0 1 /apps/applications/gamma/$gammaver/2/default/DIFF/scripts/egm2008-5.dem /apps/applications/gamma/$gammaver/2/default/DIFF/scripts/egm2008-5.dem_par 0

    print(bcolors.OKBLUE+'Using py_gamma: pg.dem_import'+ bcolors.ENDC)
    pg.dem_import(dem_import_dict.get('input_dem'),#(input) input DEM in original format
                dem_import_dict.get('bin_dem'),#(output) DEM in binary format (float, enter - for none)
                dem_import_dict.get('dem_par'),#DEM_par     (input/output) DEM parameter file corresponding to output DEM
                dem_import_dict.get('input_type'),
                dem_import_dict.get('priority'),
                dem_import_dict.get('geoid'),
                dem_import_dict.get('geoid_par'),
                dem_import_dict.get('geoid_type'))

     # Look-up table
    print(bcolors.OKBLUE +' pg.gc_map() '+bcolors.ENDC)
    #----------------------------------------------------------------------------------#
    pg.gc_map(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'), #  MLI_par         (input) ISP MLI or SLC image parameter file (slant range geometry)
              '-', 
              os.path.join(topdir,'dem',dem_import_dict['dem_par']), 
              os.path.join(topdir,'dem',dem_import_dict['bin_dem']), 
              os.path.join(topdir,'slcs',f'{dateM}M',f'P.dem_par'), 
              os.path.join(topdir,'slcs',f'{dateM}M',f'P.dem'), 
              os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}M.lt'), 
              demlat, 
              demlon, 
              os.path.join(topdir,'slcs',f'{dateM}M/{dateM}M.sim_sar'),
              os.path.join(topdir,'slcs',f'{dateM}M','u'),
              os.path.join(topdir,'slcs',f'{dateM}M','v'),
              os.path.join(topdir,'slcs',f'{dateM}M','inc'),
              os.path.join(topdir,'slcs',f'{dateM}M','psi')
              )


    # Open parameter file    
    dem_par = pg.ParFile(os.path.join(slc_dir,f'{dateM}M','P.dem_par'))	
    widthdem=int(dem_par.get_value('width'))

    config['widthdem'] = widthdem
    pg.rasmph(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}M.sim_sar'),widthdem , '-', '-', '-', '-')

    
    pg.create_diff_par(os.path.join(slc_dir,f'{dateM}M',f'{dateM}.mli.par'),
                       '-', 
                       os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.diff_par'),
                       1,
                       0)
    
    #Geocoding lookup table correction using offset polynomials from the DIFF parameter file
    
    pg.gc_map_fine(os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.lt'), #geocoding lookup table
                   widthdem, #width of lookup table (samples)
                   os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.diff_par'), #DIFF/GEO parameter file containing fine registration polynomial coefficients
                   os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.lt_fine'), # (output) refined geocoding lookup table
                   1) #1: simulated image reference (default)


    
    # Forward transformation with a geocoding look-up table. For each image point defined in 
    # coordinate system A, the lookup table contains the corresponding coordinates in system B. 
    # The program geocode is used to resample the data in coordinate system A into the coordinates of system B.
    print(
        f"DEM width (widthdem): {widthdem}, "
        f"MLI width (widthmli): {widthmli}, "
        f"MLI length (lengthmli): {lengthmli}"
    )
    
    pg.geocode(os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.lt_fine'),  #      lookup_table  (input) lookup table containing pairs of real-valued output data coordinates
               os.path.join(slc_dir,f'{dateM}M','P.dem'),             #   data_in   (input) data file (format as specified by format_flag parameter)
               widthdem,            #   width_in  width of input data file and gc_map lookup table
               os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.hgt'),      #   data_out  (output) output data file
               widthmli,            #   width_out width of output data file
               lengthmli,                 #lengthmli,
               2,                    
               0)                  
    
    pg.geocode(os.path.join(topdir,'slcs',f'{dateM}M/{dateM}M.lt_fine'),  #      lookup_table  (input) lookup table containing pairs of real-valued output data coordinates
               os.path.join(topdir,'slcs',f'{dateM}M/{dateM}M.sim_sar'),             #   data_in   (input) data file (format as specified by format_flag parameter)
               widthdem,            #   width_in  width of input data file and gc_map lookup table
               os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.sim_sar.sar'),      #   data_out  (output) output data file
               widthmli,            #   width_out width of output data file
               lengthmli,                 #lengthmli,
               2,                   
               0)   
    pg.geocode(os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.lt_fine'),  #      lookup_table  (input) lookup table containing pairs of real-valued output data coordinates
               os.path.join(slc_dir,f'{dateM}M','P.dem'),             #   data_in   (input) data file (format as specified by format_flag parameter)
               widthdem,            #   width_in  width of input data file and gc_map lookup table
               os.path.join(slc_dir,f'{dateM}M',f'{dateM}M.hgt_no_ovr'),      #   data_out  (output) output data file
               widthmli,            #   width_out width of output data file
               lengthmli,                 #lengthmli,
               2,                   
               0)      
    produce_geocode_hgt(dateM,os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'),os.path.join(topdir,'slcs',f'{dateM}M',f'P.dem_par'),os.path.join(topdir,'slcs',f'{dateM}M'),os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli'))
    
    # if cleanup:
    #     im_fp = os.path.join(topdir,'slcs',f'{dateM}M/{dateM}M.lt_fine')
    #     im_tif_fp = os.path.join(topdir,'slcs',f'{dateM}M/{dateM}M.lt_fine.tif')
    #     im_png_fp = os.path.join(topdir,'slcs',f'{dateM}M/{dateM}M.lt_fine.png')
    #     im_width = widthdem

    #     pg.rasmph_pwr24(im_fp, os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli'),im_width,  1, 1, 0, 1, 1, 0.8, .35, 1, im_tif_fp)
    #     #pg.rasmph(im_fp,im_width,'-',rlks,azlks,0.5,'-','-',im_tif_fp,'-')
    #     print(bcolors.OKGREEN,'5. Look-up table fine IMAGE PRINT: ',im_png_fp,bcolors.ENDC)
    #     pg.run_cmd('convert', im_tif_fp, '-transparent', 'black', im_png_fp)
        

        



    os.chdir(topdir)



    return config

def parse_dem_ers_file(filepath):

    with open(filepath, 'r') as file:
        data = {}
        current_section = data
        section_stack = []
        
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):  # skip empty lines and comments
                continue
            
            if " Begin" in line:
                section_name = line.replace(" Begin", "").strip()
                new_section = {}
                current_section[section_name] = new_section
                section_stack.append(current_section)
                current_section = new_section
            elif " End" in line:
                current_section = section_stack.pop()
            else:
                if "=" in line:
                    key, value = map(str.strip, line.split("=", 1))
                    current_section[key] = value.strip('"')

    dem_ers_dict = data['DatasetHeader']
    ncells = int(dem_ers_dict['RasterInfo']['NrOfCellsPerLine'])#run_command(f"grep NrOfCellsPerLine {topdir}/dem/{dem}.dem.ers | awk '{{print $3}}'").strip()
    nlines = int(dem_ers_dict['RasterInfo']['NrOfLines'])#run_command(f"grep NrOfLines {topdir}/dem/{dem}.dem.ers | awk '{{print $3}}'").strip()
    xdim = float(dem_ers_dict['RasterInfo']['CellInfo']['Xdimension'])#run_command(f"grep Xdimension {topdir}/dem/{dem}.dem.ers | awk '{{printf \"%.11f\\n\", $3}}'").strip()
    ydim = float(dem_ers_dict['RasterInfo']['CellInfo']['Ydimension'])#run_command(f"grep Ydimension {topdir}/dem/{dem}.dem.ers | awk '{{printf \"%.11f\\n\", -$3}}'").strip()
    west = float(dem_ers_dict['RasterInfo']['RegistrationCoord']['Eastings'])#run_command(f"grep Eastings {topdir}/dem/{dem}.dem.ers | awk '{{printf \"%.11f\\n\", $3}}'").strip()
    north = float(dem_ers_dict['RasterInfo']['RegistrationCoord']['Northings'])#run_command(f"grep Northings {topdir}/dem/{dem}.dem.ers | awk '{{print $3}}'").strip()

    output_list = [ncells,nlines,xdim,ydim,west,north]

    return data, output_list
def baseline_relative_to_master(date,config):
    import subprocess as subp
    from datetime import datetime



    # Assign variables
    rlks = config["rlks"]
    azlks = config["azlks"]
    dem = config["dem"]
    demlat = config["demlat"]
    demlon = config["demlon"]
    npat_r = config["npat_r"]
    npat_az = config["npat_az"]
    r_init = config["r_init"]
    az_init = config["az_init"]
    dateM = config['dateM']
    topdir = config['topdir']
    slc_dir = config["slc_dir"]
    dim_dir = config["dim_dir"]
    rslc_dir = os.path.join(topdir,'rslc')
    # Output baseline relative to master

    # check if baselines file exists in topdir
    if os.path.exists(os.path.join(topdir,'baselines')):
        print('baselines file exists')
    else:
        # make empty file 
        open(os.path.join(topdir,'baselines'),'a').close()

   
    basecall = f"base_orbit {os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.slc.par')} {os.path.join(topdir,'rslc',date,date+'.rslc.par')} - | grep perpendicular | gawk '{{print $5}}'"
                                                              
    
    print(bcolors.OKBLUE + f'Calculating baseline using command: {basecall}'+bcolors.ENDC)
    
    btemp = date_diff_days(dateM, date)
    try:
        bperp = subp.check_output(basecall, shell=True).decode('utf-8')
        # check if bperp is empty
        if bperp.strip() == '':
            raise ValueError('bperp is empty')
        print(bcolors.OKGREEN + f'Baseline perpendicular for {date} relative to {dateM} is {bperp.strip()} meters'+bcolors.ENDC)

        # calculate difference in days between dateM and date 
        
        with open(os.path.join(topdir,'baselines'),'a') as f:
            f.write(f'{dateM} {date} {bperp.strip()} {btemp}\n')
    except Exception as e:
        print(bcolors.FAIL + f'Error calculating baseline for {date}: {e}'+bcolors.ENDC)
        with open(os.path.join(topdir,'baselines'),'a') as f:
            f.write(f'{dateM} {date} 9999 {btemp}\n')
def date_diff_days(d1, d2):
    fmt = "%Y%m%d"  # matches '20210101'
    dt1 = datetime.strptime(d1, fmt)
    dt2 = datetime.strptime(d2, fmt)
    return (dt2 - dt1).days


def proc_if(date1,date2,config):


    # Assign variables
    rlks = config["rlks"]
    azlks = config["azlks"]
    dem = config["dem"]
    demlat = config["demlat"]
    demlon = config["demlon"]
    npat_r = config["npat_r"]
    npat_az = config["npat_az"]
    r_init = config["r_init"]
    az_init = config["az_init"]
    dateM = config['dateM']
    topdir = config['topdir']
    slc_dir = config["slc_dir"]
    dim_dir = config["dim_dir"]
    

    dateM_mli_par = pg.ParFile(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'))
    lengthmli= int(dateM_mli_par.get_value('azimuth_lines')) 
    widthmli=int(dateM_mli_par.get_value('range_samples'))

   
    cleanup = config["cleanup"]

    dem_par = pg.ParFile(os.path.join(slc_dir,f'{dateM}M','P.dem_par'))	
    widthdem=int(dem_par.get_value('width'))
    
    if os.path.exists(os.path.join(topdir,'ifgms',f'{date1}-{date2}')):
        print(bcolors.WARNING + f"Directory {topdir}/ifgms/{date1}-{date2} already exists. Skipping processing." + bcolors.ENDC)
        return False
    
    os.makedirs(os.path.join(topdir,'ifgms',f'{date1}-{date2}'),exist_ok = True)
    ifgm_dir = os.path.join(topdir,'ifgms',f'{date1}-{date2}')
    rslc_dir = os.path.join(topdir,'rslc')
    
    file_list = []
    for pattern in [[f'{dateM}M','*.lt*'],[f'{dateM}M','*.mli*'], [f'{dateM}M','*.hgt'], [f'{dateM}M','P.*']]:
        print(bcolors.OKBLUE+f'{os.path.join(slc_dir,pattern[0],pattern[1])}'+bcolors.ENDC)
        for files in glob(os.path.join(slc_dir,pattern[0],pattern[1])):
            file_list.append(files)
    for pattern in [[date1,f'{date1}*.rslc*'],[date2,f'{date2}*.rslc*']]:
        print(bcolors.OKBLUE+f'{os.path.join(slc_dir,pattern[0],pattern[1])}'+bcolors.ENDC)
        for files in glob(os.path.join(rslc_dir,pattern[0],pattern[1])):
            file_list.append(files)
    
    for file in file_list:
        if os.path.exists(os.path.join(ifgm_dir,file.split('/')[-1])):
            print(bcolors.WARNING +f'No sym link for {file}, file already exists' +bcolors.ENDC)
       
        else:
            print(bcolors.OKBLUE +f'sym link for {file}' +bcolors.ENDC)
            os.symlink(file,os.path.join(ifgm_dir,file.split('/')[-1]))

        # pg.geocode(os.path.join(ifgm_dir,f'{dateM}M.lt_fine'),
        #            os.path.join(ifgm_dir,f'P.dem'),
        #            widthdem, 
        #            os.path.join(ifgm_dir,f'{dateM}M.hgt'),
        #            widthmli,lengthmli,2,0)
    
    pg.create_offset(os.path.join(ifgm_dir,f'{date1}.rslc.par'),
                     os.path.join(ifgm_dir,f'{date2}.rslc.par'),
                     os.path.join(ifgm_dir, f'{date1}_{date2}.off'),
                     1, rlks, azlks, 0)

    pg.phase_sim_orb(os.path.join(ifgm_dir,f'{date1}.rslc.par'),
                     os.path.join(ifgm_dir, f'{date2}.rslc.par'),
                     os.path.join(ifgm_dir, f'{date1}_{date2}.off'),
                     os.path.join(ifgm_dir, f'{dateM}M.hgt'),
                     os.path.join(ifgm_dir, f'{date1}_{date2}.sim_unw'),
                     os.path.join(slc_dir,f'{dateM}M', f'{dateM}.slc.par'),
                     '-', '-', 1, 1)

    pg.SLC_diff_intf(os.path.join(ifgm_dir,f'{date1}.rslc'),
                     os.path.join(ifgm_dir,f'{date2}.rslc'),
                     os.path.join(ifgm_dir,f'{date1}.rslc.par'),
                     os.path.join(ifgm_dir,f'{date2}.rslc.par'),
                     os.path.join(ifgm_dir, f'{date1}_{date2}.off'),
                     os.path.join(ifgm_dir, f'{date1}_{date2}.sim_unw'),
                     os.path.join(ifgm_dir, f'{date1}-{date2}.diff'),
                     rlks, azlks, 0, 0, 0.2, 1, 1)
    


      
    pg.base_init(os.path.join(ifgm_dir,f'{date2}.rslc.par'),
                    os.path.join(ifgm_dir,f'{date1}.rslc.par'), 
                    os.path.join(ifgm_dir,f'{date1}_{date2}.off'), 
                    os.path.join(ifgm_dir,f'{date1}-{date2}.diff'), 
                    os.path.join(ifgm_dir,f'{date1}-{date2}.base'), 0)
        
    #Computation of baseline components normal and parallel to look vector.       
    # pg.rasmph_pwr(os.path.join(ifgm_dir,f'{date1}-{date2}.diff'), 
    #               os.path.join(slc_dir,f'{dateM}M',f'{dateM}.mli'),
    #               widthmli, 1, 1, 0, '-', '-', 1., .20, 1,
    #               os.path.join(ifgm_dir,f'{date1}-{date2}.diff.tif'))    
    
    
    base_perp_file =os.path.join(ifgm_dir,f'{date1}_{date2}.base.perp')
    with open(base_perp_file, 'w') as file:
        with redirect_stdout(file):
             pg.base_perp(os.path.join(ifgm_dir,f'{date1}-{date2}.base'), 
                          os.path.join(slc_dir,date2,f'{date2}.slc.par'), 
                          os.path.join(ifgm_dir,f'{date1}_{date2}.off'))
    
    
    # Calculate bperp
    with open(base_perp_file, 'r') as file:
        lines = file.readlines()[17:]

        bperp_values = []
        for line in lines:
            # if line in lines is empty, contains 'user time', 'system time', 'elapsed time' or only contains whitespace, skip it
            if not line or 'user time' in line or 'system time' in line or 'elapsed time' in line or not line.strip():
                continue
            else:
                try:
                    bperp_values.append(float(line.split()[7]))
                except IndexError:
                    print(f"Skipping line due to insufficient values: {line.strip()}")
                
    if not bperp_values:
        print(f"No bperp values found for {date1} and {date2}. Skipping.")
    else:

        bperp = int(sum(bperp_values) / len(bperp_values)) 
    

        # Get bperp1 and bperp2
        bperp1 = subprocess.check_output(f'grep {date1} {topdir}/slcs/{dateM}.b_perp | awk \'(NR==1){{print $2}}\'', shell=True).decode().strip()
        bperp2 = subprocess.check_output(f'grep {date2} {topdir}/slcs/{dateM}.b_perp | awk \'(NR==1){{print $2}}\'', shell=True).decode().strip()
        sm = int(datetime.strptime(dateM, "%Y%m%d").timestamp())
        s1 = int(datetime.strptime(date1, "%Y%m%d").timestamp())
        s2 = int(datetime.strptime(date2, "%Y%m%d").timestamp())
        # Calculate number of days
        ndays12 = (s2 - s1) / 86400
        ndays1 = (sm - s1) / 86400
        ndays2 = (sm - s2) / 86400
        try:
            with open(f'{topdir}/b.perp', 'a') as file:
                file.write(f'{date1} {date2} {bperp} {ndays12:.1f} {ndays1:.1f} {ndays2:.1f} {bperp1} {bperp2}\n')
        except Exception as e: 
            print(f"Error writing bperp values to file: {e}")

    #Adaptive interferogram filter using the power spectral density
    pg.adf(os.path.join(ifgm_dir,f'{date1}-{date2}.diff'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.smcc'),
           widthmli, 0.3, 64, 7, '-', 0, '-', 0.2)
    
    #Adaptive interferogram filter using the power spectral density    
    pg.adf(os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm2'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.smcc2'), 
           widthmli, 0.4, 32, 7, '-',0, '-', 0.2)
    

 
    #Adaptive interferogram filter using the power spectral density    
    pg.adf(os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm2'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm3'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'), 
           widthmli, 0.5, 16, 7, '-', 0, '-', 0.2)
    
    pg.rasmph_pwr(os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm3'), 
                  os.path.join(rslc_dir,f'{date2}',f'{date2}.mli'),
                  widthmli, '-', '-', '-', '-','-', 
                  os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm3.tif'),
                   1., .20)
    
    # pg.rascc(os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'), 
    #             os.path.join(rslc_dir,date1,f'{date1}.mli'), 
    #             widthmli, 1, 1, 0, '-', '-', 0.1, 0.9, 1.0, .35, 1,
    #             os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'+'.tif'))
    
    #plot_backup_diff(date1,date2,config)

    if cleanup:
        for file in [f'{date1}-{date2}.diff_sm', f'{date1}-{date2}.smcc', f'{date1}-{date2}.diff_sm2', f'{date1}-{date2}.smcc2']:
            try:
                os.remove(os.path.join(ifgm_dir, file))
            except Exception as e:
                print(f'ERROR removing {file}: {e}')

    return True

def proc_unw(date1,date2,config):

    # Assign variables
    rlks = config["rlks"]
    azlks = config["azlks"]
    dem = config["dem"]
    demlat = config["demlat"]
    demlon = config["demlon"]
    npat_r = config["npat_r"]
    npat_az = config["npat_az"]
    r_init = config["r_init"]
    az_init = config["az_init"]
    dateM = config['dateM']
    topdir = config['topdir']
    slc_dir = config["slc_dir"]
    dim_dir = config["dim_dir"]
    rslc_dir = os.path.join(topdir,'rslc')
    
    dem_par = pg.ParFile(os.path.join(slc_dir,f'{dateM}M','P.dem_par'))	
    widthdem=int(dem_par.get_value('width'))
    config['widthdem'] = widthdem

    dateM_mli_par = pg.ParFile(os.path.join(topdir,'slcs',f'{dateM}M',f'{dateM}.mli.par'))
    lengthmli= int(dateM_mli_par.get_value('azimuth_lines')) 
    widthmli=int(dateM_mli_par.get_value('range_samples'))

    ifgm_dir = os.path.join(topdir,'ifgms',f'{date1}-{date2}')
    # Coherence
    # Do on unsmoothed interferogram
    # Window currently at 5x5. (also triangular weighting - difference not investigated)
    # coherence estimation from normalized interferogram and co-registered intensity images
        
    pg.cc_wave(os.path.join(ifgm_dir,f'{date1}-{date2}.diff'), 
               os.path.join(rslc_dir,date1,f'{date1}.mli'), 
               os.path.join(rslc_dir,date2,f'{date2}.mli'), 
               os.path.join(ifgm_dir,f'{date1}-{date2}.cc'), 
               widthmli, 5, 5, 1)


    ###############
    # UNWRAPPING
    ########## MCF

	# Phase unwrapping mask
	# Be careful with what you are using as Coherence (smoothed or original) to mask

    # Phase unwrapping mask
    pg.rascc_mask(os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'),
                  os.path.join(rslc_dir,date1, f'{date1}.mli'), widthmli, 1, 1, 0, 1, 1, 0.5, 0.0, 0.1, 0.9, 1.0, 0.20, 1, 
                  os.path.join(ifgm_dir,f'{date1}-{date2}.mask.ras'))
    # Unwrap Minimum Cost Function
    pg.mcf(os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm3'),
           os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'), 
           os.path.join(ifgm_dir,f'{date1}-{date2}.mask.ras'),
           os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm.unw'), 
            widthmli, 
            0, 
            '-', '-', '-', '-', 
            npat_r, npat_az, '-',
            r_init, az_init, 1)

   
    
    #disrmg f'{date1}-{date2}.diff_sm.unw {date1}.rslc.mli widthmli 1 1 0 1.0 1. .20 0. &

    # Geocode unwrapped
    pg.geocode_back(os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm.unw'), widthmli, 
                    os.path.join(ifgm_dir,f'{dateM}M.lt_fine'), 
                    os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm.unw.geo'), widthdem, '-', 0) 

    pg.geocode_back(os.path.join(ifgm_dir,f'{date1}-{date2}.cc'), 
                        widthmli, 
                        os.path.join(ifgm_dir,f'{dateM}M.lt_fine'), 
                        os.path.join(ifgm_dir,f'{date1}-{date2}.cc.geo'),
                        widthdem, '-', 2)
    pg.geocode_back(os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'), 
                        widthmli, 
                        os.path.join(ifgm_dir,f'{dateM}M.lt_fine'), 
                        os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3.geo'),
                        widthdem, '-', 2)
    #data2geotiff ${procdir}/$geodir/EQA.dem_par ${procdir}/$GEOCDIR/${ifg}/${ifg}.geo.cc 2 ${procdir}/$GEOCDIR/${ifg}/${ifg}.geo.cc.orig.tif 0.0
    #gdal_translate -of GTiff -ot Byte -scale 0 1 0 255 -co COMPRESS=DEFLATE -co PREDICTOR=2 ${procdir}/$GEOCDIR/${ifg}/${ifg}.geo.cc.orig.tif ${procdir}/$GEOCDIR/${ifg}/${ifg}.geo.cc.tif
    # optional_plots = True
    # if optional_plots:
    #     if os.path.exists(os.path.join(rslc_dir,date2,f'{date2}_geocode.mli')):
    #         pass
    #     else:
    #         # if not os.path.exists(os.path.join(rslc_dir, f'{dateM}M.lt_fine')):
    #         #     os.symlink(os.path.join(ifgm_dir, f'{dateM}M.lt_fine'), os.path.join(rslc_dir, f'{dateM}M.lt_fine'))
    #         print('HERE: Geocoding mli')
            
    #         pg.geocode_back(os.path.join(rslc_dir,date2,f'{date2}.mli'),
    #                     widthmli, 
    #                     os.path.join(ifgm_dir,f'{dateM}M.lt_fine'), 
    #                     os.path.join(rslc_dir,date2,f'{date2}_geocode.mli'), 
    #                     widthdem, '-', 2, 0)
            


    #     pg.rascc(os.path.join(ifgm_dir,f'{date1}-{date2}.cc.geo'), 
    #                 os.path.join(rslc_dir,date2,f'{date2}_geocode.mli'), 
    #                 widthdem, 1, 1, 0, 10, 10, 0.1, 0.9, 1.0, .35, 1,
    #                 os.path.join(ifgm_dir,f'{date1}-{date2}.cc.geo.tif'))

    #     pg.rasrmg(os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm.unw.geo'), 
    #                 os.path.join(rslc_dir,date2,f'{date2}_geocode.mli'), 
    #                 widthdem, 1, 1, 0, 1, 1, 1., 1., .20, 0, 1, os.path.join(ifgm_dir,f'{date1}-{date2}.diff_sm.unw.geo.tif'))


    #     pg.rascc(os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'), 
    #                 os.path.join(rslc_dir,date2,f'{date2}.mli'), 
    #                 widthmli, 1, 1, 0, 10, 10, 0.1, 0.9, 1.0, .35, 1,
    #                 os.path.join(ifgm_dir,f'{date1}-{date2}.smcc3'+'.tif'))
    return 


