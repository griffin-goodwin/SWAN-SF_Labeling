import json
from os import listdir, makedirs
from os.path import isfile, isdir, join

import numpy as np
import pandas as pd


# THRESHOLD_POINTS = ['M1.0']

def initialize(K=5, ar_mvts_dir_path = '../ARMVTS_all_features/', out_folder = '../partitions/'):
    '''
        Script for moving the data into partitions based on the flare count data frame.
    It checks the ratio of major flares (>M1.0) and moves the active regions to partitions
    based on set breakpoints. Method:


    1. create K buckets of size (let's say N)
    2. group the flares based on their harpnum, sorted on their flare peak time.
    3. start filling the buckets of size N +/- n (where n is N/k)
    4. once you fill all the buckets, now get the maximum of harp end time
        you will get k-1 border time points for samples

    :param K: number of partitions
    :param ar_mvts_dir_path: directory path for input AR MVTS
    :param out_folder: output folder for partitioned data
    :return: None
    '''
    sharp_files = list_ar_mvts(ar_mvts_dir_path)

    ar_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    cdf = create_flare_count_df(ar_count, data_err_cnt, io_err_cnt, sharp_files, val_err_cnt, ar_mvts_dir_path)

    # cdf = pd.read_csv('flare_counts_per_class.csv', index_col=0)
    lfc = np.sum(cdf[['MFLARE', 'XFLARE']]).sum()
    bucket_size = lfc / K

    cdf['st'] = pd.to_datetime(cdf['st'])
    cdf['et'] = pd.to_datetime(cdf['et'])
    cdf = cdf.sort_values(by = ['et'])
    breakpoints = [pd.to_datetime('2010-01-01')]
    temp_bucket = 0
    for index, row in cdf.iterrows():
        # print index, row['st'], row['MFLARE'], row['XFLARE']
        temp_bucket += row['MFLARE'] + row['XFLARE']
        if temp_bucket >= bucket_size-1:
            breakpoints.append( pd.to_datetime(row['st']) )
            temp_bucket = 0
    breakpoints.append(pd.to_datetime('2030-01-01'))
    print('Breakpoints : : : ', breakpoints)

    for i in range(K):
        print('PARTITION', str(i + 1))
        start = breakpoints[i]
        end = breakpoints[i+1]
        print(start,end)
        mask = (cdf['st'] > start) & (cdf['st'] <= end)
        tempdf = cdf.loc[mask]
        print('\t# of ARs with X flares:', tempdf[ (tempdf['XFLARE'] != 0) ].shape[0])
        print('\t# of ARs with M flares:', tempdf[ (tempdf['MFLARE'] != 0) ].shape[0])
        print('\t# of ARs with C flares:', tempdf[ (tempdf['CFLARE'] != 0) ].shape[0])
        print('\t# of ARs with B flares:', tempdf[(tempdf['BFLARE'] != 0)].shape[0])

        print('\t# of ARs with M or X flares:', tempdf[ ((tempdf['MFLARE'] != 0) | (tempdf['XFLARE'] != 0)) ].shape[0])
        print('\t Total # of ARs in this fold:', len(tempdf.index.values))

        print('\n\tTotal # of M class flares:', np.sum(tempdf[['MFLARE']]).sum())
        print('\tTotal # of X class flares:', np.sum(tempdf[['XFLARE']]).sum())
        print('\tTotal # of M or X class flares:', np.sum(tempdf[['MFLARE', 'XFLARE']]).sum())

        print('Creating folders if not exists')
        fold_path = '{0}{1}/'.format(out_folder, 'partition' + str(i+1))
        try:
            makedirs(fold_path)
        except OSError:
            if not isdir(fold_path):
                raise
        print('Writing files')
        for arno in tempdf.index.values:
            ar_path = '{0}{1}.csv'.format(ar_mvts_dir_path, arno)
            ar_out_path = '{0}{1}/{2}.csv'.format(out_folder, 'partition' + str(i+1), arno)
            mvts_df = read_mvts(ar_path, fix_index=True, read_fl_json=False)
            newdf = mvts_df#.loc[start:end]
            newdf.to_csv(ar_out_path, sep='\t')

        print(bucket_size, 'vs', np.sum(tempdf[['MFLARE', 'XFLARE']]).sum())


def create_flare_count_df(ar_count, data_err_cnt, io_err_cnt, ar_mvts_files, val_err_cnt, ar_mvts_dir_path):
    '''
    Create a dataframe for counting flares integrated into AR MVTS. Also saves the dataframe to CSV

    :param ar_count: number of active regions in the folder
    :param data_err_cnt: data error count (for print out)
    :param io_err_cnt: IO error count (for print out)
    :param ar_mvts_files: list of AR MVTS file paths
    :param val_err_cnt: Value error count (for print out)
    :param ar_mvts_dir_path: Directory path for AR MVTS files
    :return: flare count dataframe that shows the number of flares (for each flare class) per each AR MVTS
    '''
    counts_per_mvts = {}
    for mvts_file in ar_mvts_files:
        file_path = join(ar_mvts_dir_path, mvts_file)
        ar_no = str(mvts_file).rstrip('.csv')

        try:
            mvts_df = read_mvts(file_path, fix_index=True)
            hstart = np.min(mvts_df.index.values)
            hend = np.max(mvts_df.index.values)
            info_dict = mvts_df[['BFLARE', 'BFLARE_LOC', 'CFLARE', 'CFLARE_LOC',
                                 'MFLARE', 'MFLARE_LOC', 'XFLARE', 'XFLARE_LOC']].sum(axis=0).to_dict()
            info_dict['st'] = hstart
            info_dict['et'] = hend
            counts_per_mvts[ar_no] = info_dict

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
    cdf = pd.DataFrame.from_dict(data=counts_per_mvts, orient='index')
    cdf.to_csv('flare_counts_per_class.csv') # for the records
    print(("Processed {0} AR time series".format(ar_count)))
    print(("\tIOError Count: {0}\tEmpty Data Error Count:{1}\tValue Error Count: {2}".format(io_err_cnt, data_err_cnt,
                                                                                            val_err_cnt)))
    return cdf


def list_ar_mvts(ar_mvts_path):
    '''
    Given a path for an AR MVTS folder fetch all the files (paths) in that folder.

    :param ar_mvts_path: path for AR MVTS
    :return: a list of file paths
    '''
    """Gets the files in the ar_mvts_path (active region multivariate time series) and returns the list of mvts file
    names """
    return [f for f in listdir(ar_mvts_path) if isfile(join(ar_mvts_path, f))]


def read_mvts(file_path, fix_index=True, silent=True, read_fl_json=True):
    '''
    Reads the AR MVTS files using a given file path.

    :param file_path: File path of the AR MVTS
    :param fix_index: Boolean flag for fixing the index (default True)
    :param silent: Boolean flag for print outs, silent=True prints out nothing (default True)
    :param read_fl_json: Boolean flag for using FlareJSONParser (default True)
    :return: a pandas dataframe object for MVTS
    '''

    if not silent:
        print(("Reading {0}".format(file_path)))

    if read_fl_json:
        mvts_df = pd.read_csv(file_path, index_col='Timestamp', sep='\t', parse_dates=True,
                          converters={'BFLARE_LABEL': FlareJSONParser, 'CFLARE_LABEL': FlareJSONParser,
                                      'MFLARE_LABEL': FlareJSONParser, 'XFLARE_LABEL': FlareJSONParser,
                                      'BFLARE_LABEL_LOC': FlareJSONParser, 'CFLARE_LABEL_LOC': FlareJSONParser,
                                      'MFLARE_LABEL_LOC': FlareJSONParser, 'XFLARE_LABEL_LOC': FlareJSONParser}
                          )
    else:
        mvts_df = pd.read_csv(file_path, index_col='Timestamp', sep='\t', parse_dates=True)

    if fix_index:
        return fix_mvts_index(mvts_df)
    else:
        return mvts_df


def FlareJSONParser(data):
    '''
    JSONParser for the categorical flare information string, which includes flare magnitude (class), flare id, and NOAA
    AR number (e.g. {"magnitude": "B8.0", "id": 177, "NOAA_AR": 11089, "narn_source": "GOES", "verification": "Non-verified"}.
    Returns a formatted string with flare magnitude and flare id separated by '@'.

    :param data: JSON string for flare identification
    :return: A formatted flare info string (format: fl_magnitude@flare_id --> e.g., C1.0@3964)
    '''
    none_str = "{\"magnitude\": \"NF\", \"id\": -1, \"NOAA_AR\": -1}"
    if data == 'None':
        j1 = 'None' #json.loads(none_str)['magnitude']
    else:
        data_arr = data.split(';')
        # print('\t', data_arr)
        json_list = []
        max_fl = 'A1.0'
        max_index = np.nan
        for i in range(len(data_arr)):
            json_list.append(json.loads(data_arr[i]) )
            magnitude = json.loads(data_arr[i])['magnitude']
            if max_fl < magnitude:
                max_fl = magnitude
                max_index = i

        j1 = json_list[max_index]['magnitude'] + '@' + str(json_list[max_index]['id'])
    return j1


def fix_mvts_index(mvts_df):
    '''
    Fix the datetime index for an AR MVTS based on the given format, i.e., %Y%m%d_%H%M%S

    :param mvts_df: input MVTS data frame with a datetime index
    :return: the MVTS data frame with updated index
    '''
    mvts_df.index = pd.to_datetime(mvts_df.index, format="%Y%m%d_%H%M%S")
    return mvts_df


if __name__ == "__main__":
    initialize()



