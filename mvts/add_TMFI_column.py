from os.path import join

import numpy as np
import pandas as pd
from bokeh.colors.groups import yellow

from flare_hist_creator import list_ar_mvts, read_mvts
from config_util import read_config_map

ar_mvts_dir_path = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
out_folder = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
OBS_LIMIT = 70  # degrees or read_config_map()['DEFAULT']['OBS_LIMIT']


def initialize():
    """This script gets the MVTS and checks if the location of the AR is inside the
        trusted observation limit (specified by OBS_LIMIT, default is 70 degrees).
        It adds a boolean column (isTMFI - is trusted magnetic field information)
        to each MVTS if |CRVAL1 - CRLN_OBS| < OBS_LIMIT.
    """

    ar_mvts_files = list_ar_mvts(ar_mvts_dir_path)

    ar_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    for sharp_file in ar_mvts_files:
        print(('Processing ' + str(sharp_file)))

        file_path = join(ar_mvts_dir_path, sharp_file)
        ar_no = str(sharp_file).rstrip('.csv')

        try:
            mvts_df = read_mvts(file_path, fix_index=True)

            mvts_df['HC_ANGLE'] = mvts_df.apply(get_hc_angle, axis=1)
            mvts_df['SPEI'] = mvts_df.apply(check_SPEI, axis=1)
            mvts_df['IS_TMFI'] = (mvts_df['SPEI']) & (mvts_df['QUALITY'] == 0)

            ar_count = ar_count + 1

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


# An easiear way to calculate the Heliocentric angle of a SHARP patch center:

# READ the following keywords from the FITS header (one of Br, Bt or Bp only):
# CRVAL1 = Carrington Longitude at the center of patch
# CRVAL2 = Carrington Latitude at the center of patch
# CRLN_OBS = Carrington Longitude of the Observer (at center of solar disk)
# CRLT_OBS = Carrington Latitude of the Observer (at center of solar disk)

def great_circle_distance(x, y):
    # Calculates the great circle distance (central angle) between
    # Point1: [lat, long]
    # Point2: [lat, long]  = [0, 0] if the angle is required wrt disk center
    # On the surface of a sphere with radius r
    # INPUT UNIT: DEGREES

    x = x * np.pi / 180
    y = y * np.pi / 180

    dlong = x[1] - y[1]
    den = np.sin(x[0]) * np.sin(y[0]) + np.cos(x[0]) * np.cos(y[0]) * np.cos(dlong)
    num = (np.cos(y[0]) * np.sin(dlong)) ** 2 + (
                np.cos(x[0]) * np.sin(y[0]) - np.sin(x[0]) * np.cos(y[0]) * np.cos(dlong)) ** 2

    # Calculate the great circle distance:
    sig = np.arctan2(np.sqrt(num), den) * 180 / np.pi
    return sig
    # print("Heliocentric Angle of point at ", x * 180 / np.pi, " [lat,long] is ", sig, "degrees")


def heliocentric_angle(CRVAL1, CRVAL2, CRLN_OBS, CRLT_OBS):
    # Calculate the Stonyhurst Latitude and Longitude:
    longitude = CRVAL1 - CRLN_OBS
    latitude = CRVAL2 - CRLT_OBS
    x = np.array([latitude, longitude])
    y = np.array([0., 0.])

    return great_circle_distance(x, y)


# # TEST:
# CRVAL1 = 90.
# CRVAL2 = 45.
# CRLN_OBS = 0.
# CRLT_OBS = 0.

# heliocentric_angle(CRVAL1, CRVAL2, CRLN_OBS, CRLT_OBS)
# Function to calculate radial heliocentric angle of any coordinate on image:
def get_hc_angle(row):
    crval1 = row['CRVAL1']
    crval2 = row['CRVAL2']
    crln_obs = row['CRLN_OBS']
    crlt_obs = row['CRLT_OBS']

    hc_angle =  heliocentric_angle(crval1, crval2, crln_obs, crlt_obs)
    # row['HC_ANGLE'] = hc_angle
    return hc_angle

def check_SPEI(row):
    return row['HC_ANGLE'] < 70

if __name__ == "__main__":
    initialize()
