from os.path import join

import numpy as np
import pandas as pd
from flare_hist_creator import list_ar_mvts, read_mvts
from config_util import read_config_map

ar_mvts_dir_path = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
out_folder = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
OBS_LIMIT = 70  # degrees or read_config_map()['DEFAULT']['OBS_LIMIT']
noaa_map_path = read_config_map()['DEFAULT']['NOAA_MAP_PATH'] #'./infiles/all_harps_with_noaa_ars.txt'
noaa_map = None
NOAA_ARS_PATH = read_config_map()['DEFAULT']['NOAA_ARS_PATH'] # './infiles/noaa_ars_plages.csv'

def initialize():
    """This script gets the MVTS and checks if the location of the AR is inside the
        trusted observation limit (specified by OBS_LIMIT, default is 70 degrees).
        It adds a boolean column (isTMFI - is trusted magnetic field information)
        to each MVTS if |CRVAL1 - CRLN_OBS| < OBS_LIMIT.
    """
    global noaa_map
    ar_mvts_files = list_ar_mvts(ar_mvts_dir_path)


    noaa_ar = get_noaa_ar_df(NOAA_ARS_PATH)
    noaa_map = get_harp_to_noaa_map()


    ar_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0
    ar_count_without_noaa_number = 0

    for sharp_file in ar_mvts_files:
        print(('Processing ' + str(sharp_file)))

        file_path = join(ar_mvts_dir_path, sharp_file)
        ar_no = str(sharp_file).rstrip('.csv')
        noaa_no = match_harp_to_noaa(ar_no)
        if noaa_no is None:
            ar_count_without_noaa_number = ar_count_without_noaa_number + 1
            mvts_df = read_mvts(file_path, fix_index=True)
            mvts_df['NOAA_AR'] = ""
            mvts_df.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')

            continue
        print(('\tMatching NOAA numbers from SHARPs {}'.format(str(noaa_no))))

        try:
            mvts_df = read_mvts(file_path, fix_index=True)
            print("Len: ", mvts_df.shape[0])
            get_attributes_from_header(noaa_ar, mvts_df)

            mvts_df.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')
            # if ar_count > 10: break

        except IOError as e:
            print((getattr(e, 'message', repr(e))))
            print((getattr(e, 'message', str(e))))
            io_err_cnt = io_err_cnt + 1
        except pd.errors.EmptyDataError as ede:
            print((getattr(ede, 'message', repr(ede))))
            print((getattr(ede, 'message', str(ede))))
            data_err_cnt = data_err_cnt + 1
        except ValueError as ve:
            print(('Value error for {0}!'.format(ar_no)))
            print((getattr(ve, 'message', repr(ve))))
            print((getattr(ve, 'message', str(ve))))
            val_err_cnt = val_err_cnt + 1

    print('Number of MVTS with no matching NOAA numbers: ', ar_count_without_noaa_number)
    print(("Processed {0} AR time series".format(ar_count)))
    print(("\tIOError Count: {0}\tEmpty Data Error Count:{1}\tValue Error Count: {2}".format(io_err_cnt, data_err_cnt,
                                                                                             val_err_cnt)))


def get_noaa_ar_df(file_path):
    noaa_ar = pd.read_csv(file_path)
    noaa_ar = noaa_ar.rename(columns={'Unnamed: 0': 'id'})
    noaa_ar = noaa_ar.set_index("id")
    noaa_ar['year'] = noaa_ar['year'].astype(str)
    noaa_ar['month'] = noaa_ar['month'].astype(str)
    noaa_ar['day'] = noaa_ar['day'].astype(str)
    noaa_ar['ar_time'] = pd.to_datetime(noaa_ar[['year', 'month', 'day']].apply(lambda x: '-'.join(x), axis=1))
    return noaa_ar



def get_attributes_from_header(noaa_ars, mvts_df):
    anar_s = [] # associated noaa active region series

    for mvts_i in mvts_df.index.values:

        arm_lat_min = mvts_df['LAT_MIN'].loc[mvts_i]
        arm_lat_max = mvts_df['LAT_MAX'].loc[mvts_i]
        arm_lon_min = mvts_df['LON_MIN'].loc[mvts_i]
        arm_lon_max = mvts_df['LON_MAX'].loc[mvts_i]

        rec_st = mvts_i - np.timedelta64(12, 'h')
        rec_et = mvts_i + np.timedelta64(12, 'h')

        candidate_ars = noaa_ars[(noaa_ars['ar_time'] >= rec_st) & (noaa_ars['ar_time'] < rec_et)]
        # print(candidate_ars)

        anar_temp = []
        for ar_index in candidate_ars.index.values:
            ar_no = candidate_ars['noaa_ar_no'].loc[ar_index]
            ar_lon = candidate_ars[['central_meridian_dist']].loc[ar_index].values[0]
            ar_lat = candidate_ars[['latitude']].loc[ar_index].values[0]
            ar_time = candidate_ars[['ar_time']].loc[ar_index].values[0]

            ar_lon, ar_lat = find_noaa_centroid(mvts_i, ar_lon, ar_lat, ar_time)

            if (arm_lat_max+3 >= ar_lat) and (ar_lat+3 >= arm_lat_min):
                if (arm_lon_max+3 >= ar_lon) and (ar_lon+3 >= arm_lon_min):
                    anar_temp.append(ar_no)

        anar_s.append(';'.join(str(nn) for nn in anar_temp))

    # print(anar_s, len(anar_s))
    mvts_df['NOAA_AR'] = pd.Series(anar_s).values


def find_noaa_centroid(rec_t, ar_lon, ar_lat, ar_time):
    """
    :param rec_t: time of the record from ar mvts
    :param ar_lon: longitude of noaa active region
    :param ar_lat: latitude of noaa active region
    :param ar_time: timestamp of noaa active region
    :return: the noaa centroid (lat, lon) at rec_t given its ar_time and locations
    """
    t_diff_day = (ar_time - rec_t) / pd.Timedelta('1 day')
    # print(rec_t, ar_time, t_diff_day)
    return ar_lon + calculate_lon_delta(ar_lat, -t_diff_day), ar_lat


def calculate_lon_delta(lat_degree, day):
    alpha = 14.11
    beta = -1.7
    gamma = -2.35

    velocity_in_deg = alpha + beta * (np.sin(np.deg2rad(lat_degree))) ** 2 + gamma * (np.sin(np.deg2rad(lat_degree))) ** 4
    delta_lon = velocity_in_deg * day
    return delta_lon

def get_harp_to_noaa_map():
    try:
        return pd.read_csv(noaa_map_path, sep=' ', index_col='HARPNUM')
    except IOError:
        print(("harp to noaa map file (at {0}) does not exist".format(noaa_map_path)))
        print("Set downloads_noaa_map to True. Exiting now...")
        import sys
        sys.exit(1)

def match_noaa_to_harp(noaa):
    """Gets the NOAA number and returns the HARPNUMs as a list of integers"""
    global noaa_map
    if noaa != noaa:  # check for nan
        return None
    try:
        # noaa = 11545.0
        harpnums = noaa_map[noaa_map['NOAA_ARS'].apply(lambda x: str(int(noaa)) in x.split(','))].index.values
        return harpnums
    except KeyError:
        return None

def match_harp_to_noaa(harp):
    """Gets the HARP identifier and returns the noaa_ar_no's (id) as a list of integers"""
    global noaa_map
    if harp != harp:  # check for nan
        return None
    try:
        noaa_nums = noaa_map.loc[[int(harp)]]['NOAA_ARS'].values[0].split(',')
        return [int(no) for no in noaa_nums]
    except KeyError:
        return None

if __name__ == "__main__":
    initialize()
