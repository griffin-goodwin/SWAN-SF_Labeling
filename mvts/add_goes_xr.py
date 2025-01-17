from os.path import join

import pandas as pd
import numpy as np
from flare_hist_creator import list_ar_mvts, read_mvts
from config_util import read_config_map

ar_mvts_dir_path = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
out_folder = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
xr_base_path = read_config_map()['DEFAULT']['XRAY_DIR_PATH'] #'../../goes_data_handling/goes_xray/'
xr_integ_path = './infiles/xray_integrated_full.txt'


def initialize():
    """This script adds the GOES Xray series to ar mvts files
    """
    ar_mvts_files = list_ar_mvts(ar_mvts_dir_path)

    ar_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    xrs = read_fixed_integrated_xray_df()

    for sharp_file in ar_mvts_files:
        print(('Processing ' + str(sharp_file)))

        file_path = join(ar_mvts_dir_path, sharp_file)
        ar_no = str(sharp_file).rstrip('.csv')

        try:
            mvts_df = read_mvts(file_path, fix_index=True)
            ar_count = ar_count + 1
            print(mvts_df.shape[0])
            if mvts_df.shape[0] == 0: continue

            start = mvts_df.index.values[0] - np.timedelta64(6, 'm')
            end = mvts_df.index.values[-1] + np.timedelta64(5, 'm')

            xr_slice = xrs.loc[start:end]
            print('xr_slice length:', xr_slice.shape[0])

            b_avg, b_max, b_all, bq_sum, bq_string = get_average_xr_series(xr_slice)
            # mvts_df['XR_AVG'] = b_avg
            mvts_df['XR_MAX'] = b_max
            # mvts_df['XR_ALL'] = b_all
            mvts_df['XR_QUAL'] = bq_sum
            # mvts_df['XR_QUAL_STR'] = bq_string

            print(mvts_df[ mvts_df['XR_QUAL']!=12 ].shape[0])

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

    print(("Processed {0} AR time series".format(ar_count)))
    print(("\tIOError Count: {0}\tEmpty Data Error Count:{1}\tValue Error Count: {2}".format(io_err_cnt, data_err_cnt,
                                                                                             val_err_cnt)))
    print(xrs.shape[0])


def get_average_xr_series(xr_slice):
    bavg = np.array(xr_slice['B_AVG'].values)
    b_trusted = np.array(xr_slice['B_AVG'] != -99999)
    # print(b_trusted)

    bavg12 = [-99999] * int(len(bavg)/12)
    bmax12 = [-99999] * int(len(bavg)/12)
    b_all12 = [ [-99999]*12 ] * int(len(bavg)/12)
    bq_strings = ['000000000000'] * int(len(bavg)/12)
    bq_sums = [0] * int(len(bavg)/12)

    for i in range(0, len(bavg), 12):
        slice12 = bavg[i:i + 12]
        t_slice12 = b_trusted[i:i + 12]
        masked_slice = slice12[t_slice12]

        qual_sum_flag = sum(b_trusted[i:i+12])
        if(qual_sum_flag > 0):
            avg_s12 = sum(masked_slice) / qual_sum_flag
            max_s12 = max(masked_slice)
        else:
            max_s12 = -99999
            avg_s12 = -99999

        qual_string = ''.join(['1' if x else '0' for x in t_slice12])
        s_all12 = ';'.join(str(x) for x in bavg[i:i+12])


        summary_i = int(i / 12)
        bavg12[summary_i] = avg_s12
        bmax12[summary_i] = max_s12
        b_all12[summary_i] = s_all12
        bq_sums[summary_i] = qual_sum_flag
        bq_strings[summary_i] = qual_string

    return bavg12, bmax12, b_all12, bq_sums, bq_strings


def get_date_attributes(_date, attribute=None):
    _year = pd.to_datetime(_date).year
    _month = "{0:0>2}".format( pd.to_datetime(_date).month )
    _day = "{0:0>2}".format( pd.to_datetime(_date).day )
    _hour = "{0:0>2}".format( pd.to_datetime(_date).hour )
    _minute = "{0:0>2}".format( pd.to_datetime(_date).minute )
    if attribute is None:
        return _year, _month, _day, _hour, _minute
    elif attribute == 'year':
        return _year
    elif attribute == 'month':
        return _month
    elif attribute == 'day':
        return _day
    elif attribute == 'hour':
        return _hour
    elif attribute == 'minute':
        return _minute
    else:
        return None


def locate_xray_series(start_date, end_date, _goes='goes15'):
    s_year, s_month, s_day, s_hour, s_minute = get_date_attributes(start_date)
    e_year, e_month, e_day, e_hour, e_minute = get_date_attributes(end_date)
    print(get_date_attributes(start_date))

    start_day = np.datetime64(str(start_date).partition('T')[0])
    end_day = np.datetime64(str(end_date).partition('T')[0])

    _xrs = pd.DataFrame(columns=['A_QUAL_FLAG', 'A_COUNT', 'A_FLUX',
                                 'B_QUAL_FLAG', 'B_COUNT', 'B_FLUX'])
    temp = start_day
    while temp != end_day + np.timedelta64(24, 'h'):
        daily_series = read_xray_series_file(None, None)
        if temp == start_day:
            if temp == end_day:
                return daily_series.loc[start_date:end_date]
            else:
                _xrs = pd.concat([_xrs, daily_series.loc[start_date:]])
        elif temp == end_day:
            _xrs = pd.concat([_xrs, daily_series.loc[:end_date]])
        else:
            _xrs = pd.concat([_xrs, daily_series])

        temp = temp + np.timedelta64(24, 'h')
    return _xrs


def get_xray_df(s_year=2010, e_year=2018, from_prepared=True):
    if from_prepared:
        full_xrs = pd.read_csv('./infiles/full_xrs.csv', parse_dates=True, index_col=0)
        full_xrs.index.name = 'Timestamp'
        return full_xrs
    else:
        full_xrs = pd.DataFrame(columns=['B_QUAL_FLAG', 'B_AVG'])
        for year in range(s_year, e_year+1):
            for month in range(1,13):
                if year == 2018 and month == 12:
                    continue

                xrs_ex = read_xray_series_file(xr_base_path + 'p' + str(year) + str(month).zfill(2) + '.csv')
                xrs_ex = xrs_ex[['B_QUAL_FLAG', 'B_AVG']]
                full_xrs = pd.concat([full_xrs, xrs_ex], sort=True)
        full_xrs = fix_xrs_timestamps(full_xrs)
        full_xrs.to_csv('./infiles/full_xrs.csv')
        return full_xrs

def fix_xrs_timestamps(xrs_df, freq='1 minutes'):
    df_size = xrs_df.shape[0]
    actual_count = 1 + (xrs_df.index.values[df_size - 1] - xrs_df.index.values[0]) / pd.Timedelta(freq)

    new_index = pd.date_range(start=xrs_df.index.values[0], end=xrs_df.index.values[xrs_df.shape[0] - 1],
                              freq='1min')

    new_index_count = 1 + (new_index.values[len(new_index) - 1] - new_index.values[0]) / pd.Timedelta(freq)
    if actual_count == new_index_count:
        # print actual_count, new_index_count
        new_df = xrs_df.reindex(index=new_index)
        new_df.index.names = ['Timestamp']
        return new_df
    else:
        raise ValueError('Index sizes do not match. XRS timestamps could not be fixed!')
        return None


def read_xray_series_file(file_path):
    cnt = 1
    with open(file_path) as fp:
        line = fp.readline()
        while line:
            line = fp.readline()
            if line.strip() == 'data:':
                break
            cnt += 1
    xrs_df = pd.read_csv(file_path, index_col='time_tag', parse_dates=True, skiprows=cnt + 1)  #
    return xrs_df


def read_integrated_xray_df(file_path):
    xrs_df = pd.read_csv(file_path, sep='  ', names=['Timestamp', 'B_AVG'],
                         header=None, engine='python')  #
    xrs_df['Timestamp'] = pd.to_datetime(xrs_df['Timestamp'], format='%d-%b-%Y %H:%M:%S')
    xrs_df.set_index('Timestamp', inplace=True)
    print(xrs_df.info())


    xrs_df.to_csv('./infiles/fixed_all_xrs.csv')
    return xrs_df


def read_fixed_integrated_xray_df():
    xrs_df = pd.read_csv('./infiles/fixed_all_xrs_Jun19.csv', index_col='Timestamp', parse_dates=['Timestamp'])  #
    return xrs_df


if __name__ == "__main__":

    initialize()

