#!/usr/bin/env python3
from nisar_gamma_functions import *

def main():
    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(description="A script to process nisar slcs to IF.")
    # Add arguments
    parser.add_argument('config_file', type=str, help='config file')
    args = parser.parse_args()
    # Directory organisations 
    topdir = os.getcwd()

    print(f"Processing in {topdir}")
    
    # Load the config file
    with open(args.config_file, 'r') as f:
        config = json.load(f)

    config['topdir'] = topdir
    slc_dir = os.path.join(topdir, 'slcs')
    config['slc_dir'] = slc_dir
    config['dim_dir'] = os.path.join(topdir,'*')
    config['og_dem_dir'] = os.path.join(topdir,'..','dem')
    dateM = config['dateM']
    ndays = config['n_days']
    min_n_days = config['min_n_days']
    date_min = config['dateS']
    date_max = config['dateE']
    cleanup = config['cleanup']
    # Call the function to validate and possibly update dateM
    #try:
   

    dates1,dates2=construct_date1_date2_combinations(config,ndays,date_min,date_max,step1=True)
    
    if dates2 == []:
        print(bcolors.WARNING+"Warning: Less than 2 unique dates found. Please check your data."+bcolors.ENDC)
        
        unique_dates = dates1
    else:    
        # print date pairs 
        for d1, d2 in zip(dates1, dates2):
            print(f"Date pair: {d1} - {d2}")


        unique_dates = list(set(dates1 + dates2)) # Create a list of unique dates
        if len(unique_dates) == 0:
            print("No unique dates found. Exiting.")
            sys.exit(1)
        dateM = validate_dates(dateM, dates1, dates2)
    

        print('Number of unique dates to process: ',len(unique_dates))
        


        if dateM not in unique_dates:
            unique_dates.append(dateM)
        # Sort unique_dates in chronological order
        unique_dates = sorted(unique_dates, key=lambda x: datetime.strptime(x, "%Y%m%d"))

        
    

    print('Writing to:',os.path.join(topdir, 'log_proc_dim_to_slc.txt'))
    # Use multiprocessing to run dim_to_slc for all unique dates
    
    with Pool(4) as pool:
        pool.starmap(h5_to_slc, [(date, config) for date in unique_dates])
        # close pool to prevent new tasks and wait for all current tasks to finish
        pool.close()
        pool.join()


      

        



if __name__ == "__main__":
    main()

