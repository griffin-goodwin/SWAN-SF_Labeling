from os import listdir, makedirs
from os.path import isfile, isdir, join

import json
import numpy as np
import pandas as pd
from config_util import read_config_map

mvts_files_dir = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
flare_file_path = read_config_map()['DEFAULT']['FLARE_FILE_PATH'] #'../sharps-headers/'
output_merged_sharp_path = read_config_map()['DEFAULT']['OUTPUT_DIR'] #'../new-data-loc/'


noaa_map_path = read_config_map()['DEFAULT']['NOAA_MAP_PATH'] #'./infiles/all_harps_with_noaa_ars.txt'
noaa_map = False  # global variable
downloads_noaa_map = False  # global variable


def initialize():
    global noaa_map
    noaa_map = get_harp_to_noaa_map()
    fdf = get_flare_dataframe(flare_file_path)
    problems = ''
    ar_non_flaring = 0
    ar_flaring = 0
    ar_non_flaring_loc = 0
    ar_flaring_loc = 0
    ar_no_matching_noaa = 0

    noaa_matching_flare_ids = []
    loc_matching_flare_ids = []
    noaa_matching_ars = []
    loc_matching_ars = []

    ar_matched_flares_only_loc = []
    ar_matched_flares_only_noaa = []

    fl2ar_noaa_map = {}
    fl2ar_loc_map = {}

    mvts_files = list_ar_mvts(mvts_files_dir)
    for mvts_file in mvts_files:
        print(('Processing ' + str(mvts_file)))
        noaa_no = match_harp_to_noaa(mvts_file.strip('.csv'))
        if noaa_no is None:
            ar_no_matching_noaa = ar_no_matching_noaa + 1
        print(('\tMatching NOAA numbers {}'.format(str(noaa_no))))

        # read mvts and create the dataframe
        mvts_df = read_mvts(join(mvts_files_dir, mvts_file))
        mvts_df_loc = get_mvts_location_parameters(mvts_df)
        # ar_start_time = np.min(mvts_df_loc.index.values)

        # get matching flares based on the noaa number
        matching_flares = search_flares_with_noaa_no(fdf, noaa_no)
        print(('\tMatching flares with NOAA No {}'.format(str(matching_flares['goes_class'].values))))

        # get matching flares based on the locations
        matching_flares_loc = search_flares_with_location(fdf, mvts_df_loc)
        print(('\tMatching flares on location {}'.format(str(matching_flares_loc['goes_class'].values))))

        try:
            create_flare_history_series(mvts_df, matching_flares, noaa_no)
            create_flare_history_series_loc(mvts_df, matching_flares_loc, noaa_no)
            write_mvts(output_merged_sharp_path, mvts_file, mvts_df)
            # break
        except Exception as e:
            print(e)
            problems = problems + "\n There was a problem with AR at {0}".format(mvts_file) + e
            print(("\tThere was a problem with AR at {0}".format(mvts_file)))

        ####THIS PART IS ALL FOR STATS
        if matching_flares.empty:
            ar_non_flaring = ar_non_flaring + 1
        else:
            ar_flaring = ar_flaring + 1
            noaa_matching_ars.append(mvts_file)

        if matching_flares_loc.empty:
            ar_non_flaring_loc = ar_non_flaring_loc + 1
        else:
            ar_flaring_loc = ar_flaring_loc + 1
            loc_matching_ars.append(mvts_file)

        noaa_matching_flare_ids.extend(matching_flares.index.values)
        loc_matching_flare_ids.extend(matching_flares_loc.index.values)

        for fl_id in matching_flares.index.values:
            numbers = mvts_file + ': ('
            if noaa_no is not None:
                numbers = numbers + ", ".join(str(x) for x in noaa_no)
            numbers = numbers + ')'

            if fl_id in fl2ar_noaa_map:
                fl2ar_noaa_map.get(fl_id).add(numbers)
            else:
                fl2ar_noaa_map[fl_id] = {numbers}

        for fl_id in matching_flares_loc.index.values:
            numbers = mvts_file + ': ('
            if noaa_no is not None:
                numbers = numbers + ", ".join(str(x) for x in noaa_no)
            numbers = numbers + ')'

            if fl_id in fl2ar_loc_map:
                fl2ar_loc_map.get(fl_id).add(numbers)
            else:
                fl2ar_loc_map[fl_id] = {numbers}

        if matching_flares.empty and (not matching_flares_loc.empty):  # NOAA Number finds no flares, location does
            ar_matched_flares_only_loc.extend(matching_flares_loc.index.values)

        if matching_flares_loc.empty and (not matching_flares.empty):  # Location cannot find anything, NOAA number does
            ar_matched_flares_only_noaa.extend(matching_flares.index.values)

        ####END PART FOR STATS

    print(('Number of active regions with matching flares: {0}'.format(ar_flaring)))
    print(('Number of active regions with no matching flares: {0}'.format(ar_non_flaring)))
    print(('Number of active regions with no matching NOAA no: {0}'.format(ar_no_matching_noaa)))

    print(('Number of active regions with matching flares (with location): {0}'.format(ar_flaring_loc)))
    print(('Number of active regions with no matching flares (with location): {0}'.format(ar_non_flaring_loc)))

    print(len(noaa_matching_flare_ids))
    print(len(loc_matching_flare_ids))

    print(('Number of matching flares using NOAA Numbers: {0}'.format(len(set(noaa_matching_flare_ids)))))
    print(('Number of matching flares using locations: {0}'.format(len(set(loc_matching_flare_ids)))))

    loc_matching_flare_ids.extend(noaa_matching_flare_ids)
    all_matched_flares = set(loc_matching_flare_ids)
    # problems = problems + "\nThere was a problem with AR at {0}".format(file_path)

    print(('Number of distinct matching flares using loc or NOAA numbers: {0}'.format(len(set(all_matched_flares)))))

    print(list(set(noaa_matching_ars) - set(loc_matching_ars)))
    print(len(list(set(noaa_matching_ars) - set(loc_matching_ars))))

    print(list(set(loc_matching_ars) - set(noaa_matching_ars)))
    print(len(list(set(loc_matching_ars) - set(noaa_matching_ars))))

    print(('Problems::' + problems))
    fl2ar_noaa = pd.DataFrame.from_dict(data=fl2ar_noaa_map, orient='index')
    fl2ar_loc = pd.DataFrame.from_dict(data=fl2ar_loc_map, orient='index')
    fl2ar_noaa.to_csv('./output/flare_to_ar_noaa.csv')
    fl2ar_loc.to_csv('./output/flare_to_ar_loc.csv')

    fdf['HARPNUM'] = fdf['noaa_active_region'].apply(match_noaa_to_harp)

    fdf[fdf.index.isin(ar_matched_flares_only_noaa)].to_csv('./output/ar_matched_flares_only_noaa.csv')
    fdf[~fdf.index.isin(noaa_matching_flare_ids)].to_csv('./output/non_matched_flares_using_noaa.csv')

    fdf[fdf.index.isin(ar_matched_flares_only_loc)].to_csv('./output/ar_matched_flares_only_loc.csv')
    fdf[~fdf.index.isin(loc_matching_flare_ids)].to_csv('./output/non_matched_flares_using_loc.csv')

    non_matched_flares = fdf[~fdf.index.isin(all_matched_flares)]
    non_matched_flares.to_csv('./output/non_ar_matched.csv')


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


def get_harp_to_noaa_map():
    """Downloads the harp to noaa map, and reads it as csv in local"""
    if downloads_noaa_map:  # if True download, else, use what's already there in noaa_map_path
        download_harp_to_noaa()
        from time import sleep
        sleep(2)  # sleep 2 seconds so you can grab the map from the net

    try:
        return pd.read_csv(noaa_map_path, sep=' ', index_col='HARPNUM')
    except IOError:
        print(("harp to noaa map file (at {0}) does not exist".format(noaa_map_path)))
        print("Set downloads_noaa_map to True. Exiting now...")
        import sys
        sys.exit(1)


def download_harp_to_noaa():
    """Downloads to harp to noaa map from JSOC"""
    import requests
    print('Beginning file download with requests')
    url = 'http://jsoc.stanford.edu/doc/data/hmi/harpnum_to_noaa/all_harps_with_noaa_ars.txt'
    r = requests.get(url)

    with open(noaa_map_path, 'wb') as f:
        f.write(r.content)

    # Retrieve HTTP meta-data
    if r.status_code == 200:
        print((r.headers['content-type']))
        print((r.encoding))
    else:
        print('NOAA to HARP matching cannot be done, file not downloaded. terminating')
        exit()


def write_mvts(folder_path, file_name, df):
    """Writes back the given mvts dataframe to a specified location using comma as delimiter"""
    try:
        makedirs(folder_path)
    except OSError:
        if not isdir(folder_path):
            raise

    print(("Writing to " + str(folder_path + file_name)))
    df.to_csv(folder_path + file_name, sep='\t', na_rep='NaN')


def create_history_series(ar_times, fl_info_, harp_assoc_noaa_no, is_location_based=False):
    """Creates and individual history series by matching the ar times and peak times of flares"""

    print(fl_info_)
    goes_ars = fl_info_['noaa_active_region'].values
    ssw_ars = fl_info_['ssw_ar'].values
    hinode_ars = fl_info_['hinode_ar'].values

    peak_times = pd.to_datetime(fl_info_['peak_time']).values
    fl_goes_class = fl_info_['goes_class'].values
    pv_list = fl_info_['primary_verified'].values
    sv_list = fl_info_['secondary_verified'].values
    flare_ids = fl_info_.index.tolist()

    history_series = np.zeros(len(ar_times))  # initiate empty array
    history_labels = np.array(['None' for _ in range(len(ar_times))], dtype=object)

    for index in range(len(peak_times)):
        peak_time = peak_times[index]
        goes_class = fl_goes_class[index]
        fl_id = flare_ids[index]

        primary_verified = pv_list[index]
        secondary_verified = sv_list[index]

        goes_arn = goes_ars[index]
        ssw_arn = ssw_ars[index]
        h_arn = hinode_ars[index]

        print((fl_id, goes_class, goes_arn, ssw_arn, h_arn))

        fl_narn, narn_src = determine_fl_noaa_ar_number(goes_arn, h_arn, harp_assoc_noaa_no, ssw_arn)
        if not is_location_based:
            if fl_narn == -1:
                continue

        v_info = 'Non-verified'
        if primary_verified:
            v_info = 'Primary'
        elif secondary_verified:
            v_info = 'Secondary'

        for i in range(len(ar_times) - 1):
            if ar_times[i] <= peak_time and peak_time < ar_times[i + 1]:
                # print (ar_times[i],peak_time,ar_times[i + 1])
                history_series[i] += 1
                if history_labels[i] == 'None':
                    history_labels[i] = json.dumps({'magnitude':goes_class, 'id':fl_id,
                                                    'NOAA_AR':int(fl_narn), 'narn_source':narn_src, 'verification':v_info})
                else:
                    history_labels[i] = history_labels[i] + ';' + json.dumps({'magnitude':goes_class, 'id':fl_id,
                                                                    'NOAA_AR':int(fl_narn), 'narn_source':narn_src, 'verification':v_info})
                    # + goes_class + '@' + str(fl_id)
                continue

    return history_series, history_labels


def determine_fl_noaa_ar_number(goes_arn, h_arn, harp_assoc_noaa_no, ssw_arn):

    # there is a selected hierarchy on NOAA AR number matching.
    # First source we look at is GOES, if there exists a GOES AR number (goes_arn),
    #   then we check if it is equal to (or is in) harp_assoc_noaa_no.
    #       If so we use GOES as the source; if not we do nothing
    # If GOES originated AR number does not exists, then we check Hinode ARN (h_arn)
    #   If it exists and if it is equal to (or is in) harp_assoc_noaa_no
    #       we use Hinode-XRT is the source, if not we do nothing
    # If both GOES and Hinode are missing, then we use SSW.

    narn_src = 'Unknown'
    fl_narn = -1

    if type(harp_assoc_noaa_no) is list:  # if there are multiple noaa active region numbers associated to harp
        if not np.isnan(goes_arn):  # if there is an AR number in GOES records
            if goes_arn in harp_assoc_noaa_no:
                fl_narn = goes_arn
                narn_src = 'GOES'
            else:
                fl_narn = -1
                narn_src = None
        else:
            if not np.isnan(h_arn):  # if there is an AR number in Hinode-XRT records
                if h_arn in harp_assoc_noaa_no:
                    fl_narn = h_arn
                    narn_src = 'XRT'
                else:
                    fl_narn = -1
                    narn_src = None
            else:  # if both goes and hinode originated AR numbers are missing, then use SSW
                if ssw_arn in harp_assoc_noaa_no:
                    fl_narn = ssw_arn
                    narn_src = 'SSW'
                else:
                    fl_narn = -1
                    narn_src = None

    else:  # if there is only one harp associated noaa active region number
        if not np.isnan(goes_arn):  # if there is an AR number in GOES records
            if goes_arn == harp_assoc_noaa_no:
                fl_narn = goes_arn
                narn_src = 'GOES'
            else:
                fl_narn = -1
                narn_src = None
        else:
            if not np.isnan(h_arn):  # if there is an AR number in Hinode-XRT records
                if h_arn == harp_assoc_noaa_no:
                    fl_narn = h_arn
                    narn_src = 'XRT'
                else:
                    fl_narn = -1
                    narn_src = None
            else:
                if ssw_arn == harp_assoc_noaa_no:
                    fl_narn = ssw_arn
                    narn_src = 'SSW'
                else:
                    fl_narn = -1
                    narn_src = None
    return fl_narn, narn_src


def create_flare_history_series(df, matching_flares, noaa_no):
    """Creates the history series for B, C, M, and X class flares"""
    if matching_flares.empty:
        print("\t\tI cannot find any matching flares...")
        # return empty arrays for history and labels
        zero_fl_counts = np.zeros(len(df.index.values))
        none_labels = np.array(['None' for _ in range(len(df.index.values))], dtype=object)
        df['BFLARE'] = zero_fl_counts
        df['BFLARE_LABEL'] = none_labels
        df['CFLARE'] = zero_fl_counts
        df['CFLARE_LABEL'] = none_labels
        df['MFLARE'] = zero_fl_counts
        df['MFLARE_LABEL'] = none_labels
        df['XFLARE'] = zero_fl_counts
        df['XFLARE_LABEL'] = none_labels
    else:
        # print(matching_flares)
        print(('\t\tCreating history series from ...' + str(matching_flares['goes_class'].values) + ' flares'))

        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'B',
                                               {'count': 'BFLARE', 'label': 'BFLARE_LABEL'})
        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'C',
                                               {'count': 'CFLARE', 'label': 'CFLARE_LABEL'})
        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'M',
                                               {'count': 'MFLARE', 'label': 'MFLARE_LABEL'})
        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'X',
                                               {'count': 'XFLARE', 'label': 'XFLARE_LABEL'})


def create_flare_history_series_loc(df, matching_flares, noaa_no):
    """Creates the history series for B, C, M, and X class flares"""
    if matching_flares.empty:
        print("\t\tI cannot find any matching flares...")
        # return empty arrays for history and labels
        zero_fl_counts = np.zeros(len(df.index.values))
        none_labels = np.array(['None' for _ in range(len(df.index.values))], dtype=object)
        df['BFLARE_LOC'] = zero_fl_counts
        df['BFLARE_LABEL_LOC'] = none_labels
        df['CFLARE_LOC'] = zero_fl_counts
        df['CFLARE_LABEL_LOC'] = none_labels
        df['MFLARE_LOC'] = zero_fl_counts
        df['MFLARE_LABEL_LOC'] = none_labels
        df['XFLARE_LOC'] = zero_fl_counts
        df['XFLARE_LABEL_LOC'] = none_labels
    else:
        print(('\t\tCreating location-based history series from ...{0} flares'.format(
            str(matching_flares['goes_class'].values))))

        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'B',
                                          {'count': 'BFLARE_LOC', 'label': 'BFLARE_LABEL_LOC'}, is_loc_based=True)
        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'C',
                                          {'count': 'CFLARE_LOC', 'label': 'CFLARE_LABEL_LOC'}, is_loc_based=True)
        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'M',
                                          {'count': 'MFLARE_LOC', 'label': 'MFLARE_LABEL_LOC'}, is_loc_based=True)
        df = append_flare_history_label_series(df, matching_flares, noaa_no, 'X',
                                          {'count': 'XFLARE_LOC', 'label': 'XFLARE_LABEL_LOC'}, is_loc_based=True)


def append_flare_history_label_series(df, matching_flares, noaa_no, fl_class, column_labels, is_loc_based=False):
    fl_ = search_flares_with_class(matching_flares, fl_class)[['peak_time', 'goes_class', 'noaa_active_region', 'ssw_ar',
                                                            'hinode_ar', 'primary_verified', 'secondary_verified']]
    fl_count_series, fl_label_series = create_history_series(df.index.values, fl_, noaa_no, is_loc_based)
    df[column_labels['count']] = fl_count_series
    df[column_labels['label']] = fl_label_series
    return df


def list_ar_mvts(ar_mvts_path):
    """Gets the files in the ar_mvts_path (active region multivariate time series) and returns the list of mvts file
    names """
    return [f for f in listdir(ar_mvts_path) if isfile(join(ar_mvts_path, f))]


def read_mvts(file_path, fix_index=True, silent=True):
    # type: (basestring) -> pd.DataFrame
    """Reads and mvts using a given file path, sets the index to DATE__OBS and parses dates"""
    if not silent:
        print(("Reading {0}".format(file_path)))
    mvts_df = pd.read_csv(file_path, index_col='Timestamp', sep='\t', parse_dates=True)
    if fix_index:
        return fix_mvts_index(mvts_df)
    else:
        return mvts_df


def fix_mvts_index(mvts_df):
    mvts_df.index = pd.to_datetime(mvts_df.index, format="%Y%m%d_%H%M%S")
    return mvts_df


def get_mvts_location_parameters(mvts_df):
    return mvts_df[['LAT_MIN', 'LON_MIN', 'LAT_MAX', 'LON_MAX']]


def get_flare_dataframe(file_path):
    """Reads the flare dataframe given in flare file path, downloaded using our script"""
    df = pd.read_csv(file_path, delimiter=',', parse_dates=['start_time', 'end_time', 'peak_time'])
    df = df.set_index('flare_id')

    return fix_noaa_ar_numbers(df)


def fix_noaa_ar_numbers(df):
    """ Replace the noaa ar numbers that are zero with the nan's
        :param df: flare data frame
        :return: noaa numbers fixed flare data frame
    """
    df.loc[df['noaa_active_region'] == 0, 'noaa_active_region'] = np.nan
    df.loc[df['noaa_active_region'] <= 10000, 'noaa_active_region'] = df.loc[df['noaa_active_region'] <= 10000, 'noaa_active_region'] + 10000
    return df


def search_flares_with_noaa_no(df, noaa_numbers):
    # type: (pd.DataFrame, list) -> pd.DataFrame
    """Searches the flare DataFrame using a list of noaa numbers, and returns a subset dataframe"""
    if noaa_numbers is None:
        return df[df['noaa_active_region'] == -1]  # return empty flare data frame
    else:
        return df[(df['noaa_active_region'].isin(noaa_numbers)) | (df['ssw_ar'].isin(noaa_numbers)) |
                    (df['hinode_ar'].isin(noaa_numbers))]


def search_flares_with_location(df, mvts_df_loc):
    # type: (pd.DataFrame, list) -> pd.DataFrame
    """Searches the flare DataFrame (df) using the location parameters from an active region mvts df,
     and returns a subset dataframe where there are matching flares based on the location"""

    mvts_df_loc = mvts_df_loc[~pd.isnull(mvts_df_loc['LAT_MIN'])]

    # first do temporal filtering on flare data frame
    ar_start_time = np.min(mvts_df_loc.index.values)
    ar_end_time = np.max(mvts_df_loc.index.values)

    # find overlapping flares by checking: fl_end >= ar_start and fl_start <= ar_end
    subset_df = df[df['end_time'] >= ar_start_time]
    subset_df = subset_df[subset_df['start_time'] <= ar_end_time]

    # then apply the location filter on goes locations
    flares_inside_ar = []
    for flare_i, row in subset_df.iterrows():
        # print 'Searching for ',flare_i,'\n',row
        flare_st = row['start_time']
        flare_lat = row['fl_lat']
        flare_lon = row['fl_lon']

        ts_row = mvts_df_loc.iloc[mvts_df_loc.index.get_loc(flare_st, method='nearest')]

        lat_min = ts_row['LAT_MIN']
        lat_max = ts_row['LAT_MAX']
        lon_min = ts_row['LON_MIN']
        lon_max = ts_row['LON_MAX']

        # print 'Lat:',lat_min,',',lat_max
        # print 'Lon:', lon_min, ',',lon_max
        DISTANCE_THRESHOLD = 0
        if (lat_min - DISTANCE_THRESHOLD) <= flare_lat <= (lat_max + DISTANCE_THRESHOLD):
            if (lon_min - DISTANCE_THRESHOLD) <= flare_lon <= (lon_max + DISTANCE_THRESHOLD):
                flares_inside_ar.append(flare_i)

    # then apply the location filter on aia locations
    # print subset_df.shape[0]
    subset_df = subset_df[subset_df.index.isin(flares_inside_ar)]
    # print subset_df.shape[0]

    return subset_df


def search_flares_with_class(df, fl_class):
    """Searches the flare dataframe using flare class (prefix search),
         and returns a subset dataframe
         fl_class variable can be a prefix (B, or C1, or C2. or C2.3) """
    return df[df['goes_class'].str.startswith(fl_class)]


if __name__ == "__main__":
    initialize()
