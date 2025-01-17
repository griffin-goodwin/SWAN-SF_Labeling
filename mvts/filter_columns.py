from os.path import join

import numpy as np
import pandas as pd
from flare_hist_creator import list_ar_mvts, read_mvts
from config_util import read_config_map

ar_mvts_dir_path = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
out_folder = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'
COLUMNS = ['TOTUSJH', 'TOTBSQ', 'TOTPOT', 'TOTUSJZ', 'ABSNJZH', 'SAVNCPP',
           'USFLUX', 'TOTFZ', 'MEANPOT', 'EPSZ', 'MEANSHR', 'SHRGT45', 'MEANGAM',
           'MEANGBT', 'MEANGBZ', 'MEANGBH', 'MEANJZH', 'TOTFY', 'MEANJZD', 'MEANALP',
           'TOTFX', 'EPSY', 'EPSX', 'R_VALUE',
           #'RBZ_VALUE', 'RBT_VALUE', 'RBP_VALUE', 'FDIM', 'BZ_FDIM', 'BT_FDIM', 'BP_FDIM',
           'CRVAL1', 'CRLN_OBS', 'CRLT_OBS', 'CRVAL2', 'HC_ANGLE', 'SPEI', 'IS_TMFI',
           'LAT_MIN', 'LON_MIN', 'LAT_MAX', 'LON_MAX', 'QUALITY',
           'BFLARE', 'BFLARE_LABEL', 'CFLARE', 'CFLARE_LABEL', 'MFLARE', 'MFLARE_LABEL', 'XFLARE', 'XFLARE_LABEL',
           'BFLARE_LOC', 'BFLARE_LABEL_LOC', 'CFLARE_LOC', 'CFLARE_LABEL_LOC', 'MFLARE_LOC',
           'MFLARE_LABEL_LOC', 'XFLARE_LOC', 'XFLARE_LABEL_LOC', 'XR_MAX', 'XR_QUAL']


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
            mvts_df = mvts_df[COLUMNS]

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



if __name__ == "__main__":
    initialize()
