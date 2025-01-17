import datetime
from os.path import join

import config_util

import numpy as np
import pandas as pd
from flare_hist_creator import list_ar_mvts, read_mvts

ar_mvts_dir_path = config_util.read_config_map()['DEFAULT']['INPUT_MVTS'] #'../new-data-loc/'
sharp_header_dir_path = config_util.read_config_map()['DEFAULT']['SHARP_HEADERS'] #'../sharps-headers/'
out_folder = config_util.read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'


def initialize():
    """ This function reads the AR MVTS files and the corresponding SHARP header
        Gets four location attributes that are minimum and maximum latitude and longitude
        Adds them to the AR MVTS data.
    """
    sharp_files = list_ar_mvts(ar_mvts_dir_path)

    ar_count = 0
    header_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    for sharp_file in sharp_files:
        print(('Processing ' + str(sharp_file)))

        file_path = join(ar_mvts_dir_path, sharp_file)
        try:

            mvts_df = read_mvts(file_path, fix_index=True)
            ar_count = ar_count + 1
            ar_no = str(sharp_file).rstrip('.csv')

            # if 'LAT_MIN' in mvts_df.columns:
            #     print('\tLocation attributes are already there.. skipping..')
            #     mvts_df.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')
            #     continue
            print('Mvts DF size: ', mvts_df.shape[0])

            header_file_path = join(sharp_header_dir_path, ar_no + '.txt')  # string:[header directory string, AR number string, file extension]
            header_df = read_sharp_header(header_file_path)
            header_count = header_count + 1

            if header_df.shape[0] == mvts_df.shape[0]:
                print("Sizes match, go on!")

                get_location_attributes_from_header(header_df, mvts_df)

                mvts_df.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')
                # if ar_count > 0: break
            else:
                print("Sizes do not match!, we have a problem.")
                break

        except IOError as e:
            print((getattr(e, 'message', repr(e))))
            print((getattr(e, 'message', str(e))))
            io_err_cnt = io_err_cnt + 1
        except pd.errors.EmptyDataError as ede:
            print((getattr(ede, 'message', repr(ede))))
            print((getattr(ede, 'message', str(ede))))
            data_err_cnt = data_err_cnt + 1
        # except ValueError as ve:
        #     print((getattr(ve, 'message', repr(ve))))
        #     print((getattr(ve, 'message', str(ve))))
        #     val_err_cnt = val_err_cnt + 1

    print(("Processed {0} AR time series".format(ar_count)))
    print(("\tFound {0} SHARP header files for AR time series".format(header_count)))
    print(("\tIOError Count: {0}\tEmpty Data Error Count:{1}\tValue Error Count: {2}".format(io_err_cnt, data_err_cnt,
                                                                                             val_err_cnt)))

def get_location_attributes_from_header(header_df, mvts_df):
    lat_min_s = []
    lat_max_s = []
    lon_min_s = []
    lon_max_s = []
    quality_s = []
    crpix1_s = []
    crpix2_s = []
    imcrpix1_s = []
    imcrpix2_s = []
    cdelt1_s = []
    dsun_obs_s = []
    crval2_s = []
    crlt_obs_s = []


    for mvts_i in mvts_df.index.values:
        try:
            row = header_df.iloc[header_df.index.get_loc(mvts_i, method='nearest', tolerance=pd.Timedelta('6 minute'))]
            lat_min_s.append(row['LAT_MIN'])
            lat_max_s.append(row['LAT_MAX'])
            lon_min_s.append(row['LON_MIN'])
            lon_max_s.append(row['LON_MAX'])
            quality_s.append(row['QUALITY'])
            crpix1_s.append(row['CRPIX1'])
            crpix2_s.append(row['CRPIX2'])
            imcrpix1_s.append(row['IMCRPIX1'])
            imcrpix2_s.append(row['IMCRPIX2'])
            cdelt1_s.append(row['CDELT1'])
            dsun_obs_s.append(row['DSUN_OBS'])

            crlt_obs_s.append(row['CRLT_OBS'])
            crval2_s.append(row['CRVAL2'])

            n = row.name
        except KeyError: # means it was not available
            n = pd.NaT
            lat_min_s.append(np.nan)
            lat_max_s.append(np.nan)
            lon_min_s.append(np.nan)
            lon_max_s.append(np.nan)
            quality_s.append(np.nan)
            crpix1_s.append(np.nan)
            crpix2_s.append(np.nan)
            imcrpix1_s.append(np.nan)
            imcrpix2_s.append(np.nan)
            cdelt1_s.append(np.nan)
            dsun_obs_s.append(np.nan)

            crlt_obs_s.append(np.nan)
            crval2_s.append(np.nan)

    print("Size of series", len(lat_min_s), len(lat_max_s), len(lon_min_s), len(lon_max_s), len(quality_s))

    mvts_df['LAT_MIN'] = pd.Series(lat_min_s).values
    mvts_df['LAT_MAX'] = pd.Series(lat_max_s).values
    mvts_df['LON_MIN'] = pd.Series(lon_min_s).values
    mvts_df['LON_MAX'] = pd.Series(lon_max_s).values
    mvts_df['QUALITY'] = pd.Series(quality_s).values

    mvts_df['CRPIX1'] = pd.Series(crpix1_s).values
    mvts_df['CRPIX2'] = pd.Series(crpix2_s).values
    mvts_df['IMCRPIX1'] = pd.Series(imcrpix1_s).values
    mvts_df['IMCRPIX2'] = pd.Series(imcrpix2_s).values

    mvts_df['CDELT1'] = pd.Series(cdelt1_s).values
    mvts_df['DSUN_OBS'] = pd.Series(dsun_obs_s).values

    mvts_df['CRLT_OBS'] = pd.Series(crlt_obs_s).values
    mvts_df['CRVAL2'] = pd.Series(crval2_s).values

    # mvts_df['SHNARN'] = pd.Series(noaa_ars).values


def get_attributes_from_header(header_df, mvts_df):
    lat_min_s = []
    lat_max_s = []
    lon_min_s = []
    lon_max_s = []
    for mvts_i in mvts_df.index.values:
        try:
            row = header_df.iloc[header_df.index.get_loc(mvts_i, method='nearest', tolerance=pd.Timedelta('6 minute'))]
            lat_min_s.append(row['LAT_MIN'])
            lat_max_s.append(row['LAT_MAX'])
            lon_min_s.append(row['LON_MIN'])
            lon_max_s.append(row['LON_MAX'])
            n = row.name
        except KeyError:
            n = pd.NaT
            lat_min_s.append(np.nan)
            lat_max_s.append(np.nan)
            lon_min_s.append(np.nan)
            lon_max_s.append(np.nan)
    mvts_df['LAT_MIN'] = pd.Series(lat_min_s).values
    mvts_df['LAT_MAX'] = pd.Series(lat_max_s).values
    mvts_df['LON_MIN'] = pd.Series(lon_min_s).values
    mvts_df['LON_MAX'] = pd.Series(lon_max_s).values


def read_sharp_header(path):
    # read the header data frame from the given path
    headerdf = pd.read_csv(path, sep='\t', index_col='DATE__OBS', parse_dates=True)

    print('Header DF size: ', headerdf.shape[0])

    # small hack to match the date format of mvts_df to header_df, can use an update
    hdf_index = headerdf.index.tolist()
    # update the index by removing the seconds and further off
    updated_ind = pd.to_datetime([datetime.datetime(ts.year, ts.month, ts.day, ts.hour, ts.minute) for ts in hdf_index])
    headerdf.index = updated_ind

    # return necessary columns from the header, this might add more columns from header
    return headerdf[['LAT_MIN', 'LAT_MAX', 'LON_MIN', 'LON_MAX', 'QUALITY',
                     'CRPIX1', 'CRPIX2', 'IMCRPIX1', 'IMCRPIX2', 'CDELT1',
                     'DSUN_OBS', 'CRLT_OBS', 'CRVAL2']]


if __name__ == "__main__":
    initialize()
