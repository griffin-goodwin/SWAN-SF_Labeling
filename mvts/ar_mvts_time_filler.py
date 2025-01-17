from os.path import join

import pandas as pd
from flare_hist_creator import list_ar_mvts, read_mvts
from config_util import read_config_map

ar_mvts_dir_path = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #
out_folder = read_config_map()['DEFAULT']['MVTS_TEMP_DIR'] #'../new-data-loc/'


def initialize():
    """This script gets the MVTS from the active regions and fixes the timestamps
        to have 12 minute cadence. This is simply a reindexing operation. Input and
        output folders are specified above using ar_mvts_dir_path and out_folder variables.
        We read the input files from former and write it to the latter.
    """
    sharp_files = list_ar_mvts(ar_mvts_dir_path)

    ar_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    total_final_rows = 0
    total_rows = 0

    for sharp_file in sharp_files:
        print(('Processing ' + str(sharp_file)))

        file_path = join(ar_mvts_dir_path, sharp_file)
        ar_no = str(sharp_file).rstrip('.csv')

        try:
            mvts_df = read_mvts(file_path, fix_index=True)
            # print 'Mvts DF size: ', mvts_df.shape[0]

            if is_correct_length(mvts_df):
                print('\tLength is correct, keep going...')
            else:
                print('\tLength of original TS: ', mvts_df.shape[0])
                total_rows += mvts_df.shape[0]

                mvts_df = fix_ar_timestamps(mvts_df)
                print('\t\tafter reindex: ', mvts_df.shape[0])

                total_final_rows += mvts_df.shape[0]

                # mvts_df.to_csv('{0}{1}_fixed.csv'.format(out_folder, ar_no), sep='\t')

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
    print("Total original rows:" , total_rows)
    print("Total final rows:", total_final_rows)

def fix_ar_timestamps(mvts_df, freq='12 minutes'):
    df_size = mvts_df.shape[0]
    actual_count = 1 + (mvts_df.index.values[df_size - 1] - mvts_df.index.values[0]) / pd.Timedelta(freq)

    new_index = pd.date_range(start=mvts_df.index.values[0], end=mvts_df.index.values[mvts_df.shape[0] - 1],
                              freq='12min')

    new_index_count = 1 + (new_index.values[len(new_index) - 1] - new_index.values[0]) / pd.Timedelta(freq)
    if actual_count == new_index_count:
        # print actual_count, new_index_count
        new_df = mvts_df.reindex(index=new_index)
        new_df.index.names = ['Timestamp']
        return new_df
    else:
        raise ValueError('Index sizes do not match. AR timestamps could not be fixed!')
        return None


def is_correct_length(mvts_df, freq='12 minutes'):
    df_size = mvts_df.shape[0]
    actual_count = 1 + (mvts_df.index.values[df_size - 1] - mvts_df.index.values[0]) / pd.Timedelta(freq)
    return df_size == actual_count


if __name__ == "__main__":
    initialize()
