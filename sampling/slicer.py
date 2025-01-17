

# once you have all those segments set up
# start creating slices from each mvts
# get every possible slice and target
#   when doing that (for non-flaring samples) check with no flares.

import json
from os import listdir, makedirs
from os.path import isfile, isdir, join

import numpy as np
import pandas as pd

non_matched_flares = './infiles/non_matched_flares_using_noaa.csv'
mvts_folds = './test/'
filtered_folder_name = 'filtered'

OBS_LENGTH = 5 * 12 # time series length  (x 12 minutes) - e.g. 5 --> 1 hour, 60 --> 12 hours
LATENCY = 5 * 0  # latency period         (x 12 minutes) - e.g. 5 --> 1 hour, 60 --> 12 hours
PRED_LENGTH = 5 * 24  # prediction window (x 12 minutes) - e.g. 5 --> 1 hour, 60 --> 12 hours
STEP_FOR_SAMPLING = 5 # slices every hour when 5 (make it 1 if you want 12 minutes)
CLEAR_WINDOW_LENGTH = 5 * 6 # if used, creates a clear window buffer for non flaring samples
USE_CLEAR_WINDOW = False

skipped_for_shadow_flares = 0
skipped_for_loqu_xray = 0
skipped_for_tmfi = 0
skipped_for_clear_window = 0
skipped_for_non_pv_flares = 0

def initialize():
    d = mvts_folds
    for fold_path in [join(d, o) for o in listdir(d) if isdir(join(d, o))]:
        if 'instances_' in fold_path:
            continue
        else:
            process_folds(fold_path)
        # break


def process_folds(ar_mvts_dir_path):
    if USE_CLEAR_WINDOW:
        samples_path = 'instances_O{0}L{1}P{2}C{3}'.format(str(int(OBS_LENGTH / 5)), str(int(LATENCY / 5)),
                                                        str(int(PRED_LENGTH / 5)), str(int(CLEAR_WINDOW_LENGTH / 5)) )
    else:
        samples_path = 'instances_O{0}L{1}P{2}'.format(str(int(OBS_LENGTH / 5)), str(int(LATENCY / 5)), str(int(PRED_LENGTH / 5)))
    subfolder = ar_mvts_dir_path.split('/')[-1]
    fl_path = join(mvts_folds, samples_path, subfolder, 'FL')
    filtered_path = join(mvts_folds, samples_path, subfolder, filtered_folder_name)
    nf_path = join(mvts_folds, samples_path, subfolder, 'NF')
    print((fl_path, nf_path))

    try:
        makedirs(fl_path)
        makedirs(filtered_path)
        makedirs(nf_path)
    except OSError:
        if (not isdir(fl_path)) or (not isdir(nf_path)):
            raise

    ar_mvts_files = list_ar_mvts(ar_mvts_dir_path)
    non_matched_fl_df = pd.read_csv(non_matched_flares, parse_dates=['peak_time'])
    non_matched_fl_df = non_matched_fl_df[non_matched_fl_df['goes_class'] > 'M']

    ar_count = 0
    io_err_cnt = 0
    data_err_cnt = 0
    val_err_cnt = 0

    for ar_mvts in ar_mvts_files:
        print(('Processing ' + str(ar_mvts)))
        file_path = join(ar_mvts_dir_path, ar_mvts)
        ar_no = str(ar_mvts).rstrip('.csv')

        try:
            mvts_df = read_mvts(file_path, fix_index=True)
            create_slices(mvts_df, non_matched_fl_df, ar_no, fl_path, nf_path, filtered_path, use_clear_window=USE_CLEAR_WINDOW)
            ar_count += 1
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
    print(('Filtered due to non-matched large flares {0}'.format(skipped_for_shadow_flares)))
    print(('Filtered due to low quality xray information {0}'.format(skipped_for_loqu_xray)))
    print(('Filtered due to excessive not-trusted magnetic field information {0}'.format(skipped_for_tmfi)))
    print(('Filtered due to large flares in clear window {0}'.format(skipped_for_clear_window)))
    print(('Filtered due to non-verified flares {0}'.format(skipped_for_non_pv_flares)))

    print(("\tIOError Count: {0}\tEmpty Data Error Count:{1}\tValue Error Count: {2}".format(io_err_cnt, data_err_cnt, val_err_cnt)))


def create_slices(df, shadowdf, arno, fl_path, nf_path, filtered_path, use_clear_window=False):
    # Global variables for stats keeping
    global skipped_for_shadow_flares
    global skipped_for_loqu_xray
    global skipped_for_tmfi
    global skipped_for_clear_window
    global skipped_for_non_pv_flares

    # iterate through an AR MVTS file with steps (STEPS FOR SAMPLING)
    for i in range(0, df.shape[0] - (OBS_LENGTH+LATENCY), STEP_FOR_SAMPLING):
        # determined observation window
        # and get timestamps of start and end time for the observation as a string to be used for saving files
        observation = df[i:(i+OBS_LENGTH)].copy()
        obs_start = str(observation.index.values[0])[:19]
        obs_end = str(observation.index.values[-1])[:19]

        # FILTER 1: SKIP THE OBSERVATIONS THAT HAVE 10% OR MORE LOW QUALITY MAGNETIC FIELD INFORMATION
        # If less than 90% of observations are coming from non-trusted MF info regions
        if observation[ observation['IS_TMFI'] ].shape[0] < observation.shape[0]*0.9:
            skipped_for_tmfi = skipped_for_tmfi + 1
            filename = '{0}_ar{1}_s{2}_e{3}'.format('TMFI_Filtered', arno, obs_start, obs_end)
            observation.to_csv('{0}/{1}.csv'.format(filtered_path, filename), sep='\t')
            continue

        # determine the prediction window from obs_length, latency and prediction window length
        pw_start_index = i + OBS_LENGTH + LATENCY
        pw_end_index = min(i + OBS_LENGTH + LATENCY + PRED_LENGTH, df.shape[0])
        pred_window = df[pw_start_index:pw_end_index].copy()

        # Check if the instance has a large flare associated with it
        if pred_window[['MFLARE', 'XFLARE']].sum().sum() == 0:  # if there are no M or X class flares

            # FILTER 2: NON MATCHED FLAERS -- there are a few reported flares that does not have any correspondences
            #           with any active region. If there is a non-matched flare during the prediction window, discard
            #           the non-flaring instance, as it may be associated with a non-matched flare.
            # get the shadow flares from non-matched flares without locations
            sf = shadowdf[((pred_window.index.values[0] < shadowdf['peak_time']) & (
                        shadowdf['peak_time'] < pred_window.index.values[-1]))]
            if sf.shape[0] != 0:  # if there is a non matched flare skip this non-flaring sample
                # TODO change filenames etc and save this to another folder
                nm_fl_info = str(sf['goes_class'].iloc[0]) + '@' + str(sf['peak_time'].iloc[0])
                filename = '{0}_nmfl_{4}_ar{1}_s{2}_e{3}'.format("NONMATCHED_FL_Filter", arno, obs_start, obs_end, nm_fl_info)
                observation.to_csv('{0}/{1}.csv'.format(filtered_path, filename), sep='\t')
                skipped_for_shadow_flares += 1
                continue

            #FILTER 3: LOW QUALITY XRAY -- there are long time intervals where the X-ray readings were low quality
            #          and we do not know if there exists a major flare or not during these time intervals. Therefore,
            #          if more than 10% of X-ray readings were not of high-quality, we discard the non-flaring instance
            #          as it may be associated with a flare that we do not know
            if pred_window[pred_window['XR_QUAL'] == 0].shape[0] > 0.1 * pred_window.shape[0]:  # no quality xray reads over 10% of data
                skipped_for_loqu_xray += 1
                filename = '{0}_ar{1}_s{2}_e{3}'.format("XRAY_QUAL_Filter", arno, obs_start, obs_end)
                observation.to_csv('{0}/{1}.csv'.format(filtered_path, filename), sep='\t')
                continue

            # [OPTIONAL] FILTER 4: CLEAR WINDOWS FOR MAJOR FLARING ACTIVITY
            # if clear windows are instructed to be used, then determine the clear window interval
            # and check for flares there
            if use_clear_window:
                cw_start_index = max(i + OBS_LENGTH + LATENCY - CLEAR_WINDOW_LENGTH, 0)
                cw_end_index = min(i + OBS_LENGTH + LATENCY + PRED_LENGTH + CLEAR_WINDOW_LENGTH, df.shape[0])
                clear_window = df[cw_start_index:cw_end_index].copy()
                # if the clear window has a large flare, even though prediction window does not, skip the instance
                if clear_window[['MFLARE', 'XFLARE']].sum().sum() != 0:
                    skipped_for_clear_window = skipped_for_clear_window + 1
                    filename = '{0}_ar{1}_s{2}_e{3}'.format("CLEAR_WINDOW_Filter", arno, obs_start, obs_end)
                    observation.to_csv('{0}/{1}.csv'.format(filtered_path, filename), sep='\t')
                    continue

            # save the non-flaring instance
            BC_flares = list(pred_window[pred_window['CFLARE_LABEL'] != 'None']['CFLARE_LABEL'].values)
            BC_flares.extend(list(pred_window[pred_window['BFLARE_LABEL'] != 'None']['BFLARE_LABEL'].values))
            verifiedBC = [fl for fl in BC_flares if fl.endswith('Primary') or fl.endswith('Secondary')]
            if len(verifiedBC) > 0:  # then we know there is a verified B or C class flare here, create a NF instance
                max_BC = max(verifiedBC)
            else: # there are no primary verified B&C class flares, save it as flare quiet (FQ)
                max_BC = 'FQ'

            filename = '{0}_ar{1}_s{2}_e{3}'.format(max_BC, arno, obs_start, obs_end)
            observation.to_csv('{0}/{1}.csv'.format(nf_path, filename), sep='\t')

        else:  # if there are M or X class flares
            MX_flares = list(pred_window[pred_window['MFLARE_LABEL'] != 'None']['MFLARE_LABEL'].values)
            MX_flares.extend(list(pred_window[pred_window['XFLARE_LABEL'] != 'None']['XFLARE_LABEL'].values))
            # allMX = allM
            verified_MX = [fl for fl in MX_flares if fl.endswith('Primary') or fl.endswith('Secondary')]

            # [OPTIONAL] FILTER 5: if the associated large flare(s) are non primary-verified, filter them out
            if len(verified_MX) > 0:  #then we know there is a verified flare here, create a valid instance
                max_target = max(verified_MX)
                filename = '{0}_ar{1}_s{2}_e{3}'.format(max_target, arno, obs_start, obs_end)
                observation.to_csv('{0}/{1}.csv'.format(fl_path, filename), sep='\t')
            else: #there are only non-verified flares, save them to another folder
                skipped_for_non_pv_flares = skipped_for_non_pv_flares + 1
                max_target = max(MX_flares)
                filename = '{0}_fl_{4}_ar{1}_s{2}_e{3}'.format("NON_VERIFIED_Filter", arno, obs_start, obs_end, max_target)
                observation.to_csv('{0}/{1}.csv'.format(filtered_path, filename), sep='\t')


def list_ar_mvts(ar_mvts_path):
    """Gets the files in the ar_mvts_path (active region multivariate time series) and returns the list of mvts file
    names """
    return [f for f in listdir(ar_mvts_path) if isfile(join(ar_mvts_path, f))]

def FlareJSONParser(data):
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
            verification = json.loads(data_arr[i])['verification']
            narn_source = json.loads(data_arr[i])['narn_source']
            if max_fl < magnitude:
                max_fl = magnitude
                max_index = i

        j1 = json_list[max_index]['magnitude'] + '@' + str(json_list[max_index]['id']) + ':' + verification
        # print('\t', data_arr, '\t', j1, verification, narn_source)
    return j1

def read_mvts(file_path, fix_index=True, silent=True):
    # type: (basestring) -> pd.DataFrame
    """Reads and mvts using a given file path, sets the index to DATE__OBS and parses dates"""
    if not silent:
        print(("Reading {0}".format(file_path)))
    mvts_df = pd.read_csv(file_path, index_col='Timestamp', sep='\t', parse_dates=True,
                          converters={'BFLARE_LABEL': FlareJSONParser, 'CFLARE_LABEL': FlareJSONParser,
                                      'MFLARE_LABEL': FlareJSONParser, 'XFLARE_LABEL': FlareJSONParser,
                                      'BFLARE_LABEL_LOC': FlareJSONParser, 'CFLARE_LABEL_LOC': FlareJSONParser,
                                      'MFLARE_LABEL_LOC': FlareJSONParser, 'XFLARE_LABEL_LOC': FlareJSONParser}
                          )

    if fix_index:
        return fix_mvts_index(mvts_df)
    else:
        return mvts_df


def fix_mvts_index(mvts_df):
    mvts_df.index = pd.to_datetime(mvts_df.index, format="%Y%m%d_%H%M%S")
    return mvts_df



if __name__ == "__main__":
    initialize()
