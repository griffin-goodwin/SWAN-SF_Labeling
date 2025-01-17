from os.path import join

import numpy as np
import pandas as pd
from flare_hist_creator import list_ar_mvts, read_mvts

ar_mvts_dir_path = '../annotated-new-data/'
out_folder = '../annotated-new-data2/'
CUSTOM_DATE_START = pd.to_datetime('2000-01-01')
CUSTOM_DATE_END = pd.to_datetime('2000-01-01')

def initialize():
    sharp_files = list_ar_mvts(ar_mvts_dir_path)

    ar_count = 0
    ar_out_of_range = 0
    ar_full_in_range = 0
    ar_partial_in_range = 0

    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    for sharp_file in sharp_files:
        # print('Processing ' + str(sharp_file))

        file_path = join(ar_mvts_dir_path, sharp_file)
        ar_no = str(sharp_file).rstrip('.csv')

        try:
            mvts_df = read_mvts(file_path, fix_index=True)

            if mvts_df.loc[CUSTOM_DATE_START:CUSTOM_DATE_END].shape[0] == 0:
                ar_out_of_range += 1
                mvts_df.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')
            else:
                newdf = mvts_df[~((mvts_df.index.get_level_values(0) >= CUSTOM_DATE_START) & (mvts_df.index.get_level_values(0) <= CUSTOM_DATE_END))]
                if newdf.shape[0] == 0:
                    ar_full_in_range += 1 # do nothing
                else:
                    ar_partial_in_range += 1
                    newdf.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')
                    print(ar_no, mvts_df.shape[0], 'vs', newdf.shape[0], np.min(newdf.index), np.max(newdf.index))
            ar_count = ar_count + 1

            # mvts_df.to_csv('{0}{1}.csv'.format(out_folder, ar_no), sep='\t')
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
    print(('AR out of range: {0}'.format(ar_out_of_range)))
    print(('AR fully in range: {0}'.format(ar_full_in_range)))
    print(('AR partially in range: {0}'.format(ar_partial_in_range)))
    print(("\tIOError Count: {0}\tEmpty Data Error Count:{1}\tValue Error Count: {2}".format(io_err_cnt, data_err_cnt,
                                                                                             val_err_cnt)))



if __name__ == "__main__":
    initialize()
