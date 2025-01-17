import os
import sampler as smp
import sampling_constants as CONSTANTS
import dataset_creator as DSC
import pandas as pd
import numpy as np
import random
import copy
import csv

def sample_and_serialize():
    training_months, testing_months, flaring_counts, nonflaring_counts = smp.create_training_testing(CONSTANTS.ROOT_DIR)
#     print sum(flaring_counts.values())
#     print sum(nonflaring_counts.values())
    global log_list_
    log_list_ = []
    tr_flaring_list, tr_nonflaring_list = create_sample_lists_of_month(training_months)
    test_flaring_list, test_nonflaring_list = create_sample_lists_of_month(testing_months)
    write_missing_log(log_list_)

    print 'original tr flaring size: ' + str(len(tr_flaring_list))
    print 'original tr nflaring size: ' + str(len(tr_nonflaring_list))
    print 'original test flaring size: ' + str(len(test_flaring_list))
    print 'original test nflaring size: ' + str(len(test_nonflaring_list))
    if (CONSTANTS.TRAIN_SAMPLING_STRATEGY == 'Oversampling'):
        tr_flaring_list = oversample(tr_flaring_list, len(tr_nonflaring_list))
    elif (CONSTANTS.TRAIN_SAMPLING_STRATEGY == 'Undersampling'):
        tr_nonflaring_list = undersample(tr_nonflaring_list, len(tr_flaring_list))
    if (CONSTANTS.TEST_SAMPLING_STRATEGY == 'Oversampling'):
        test_flaring_list = oversample(test_flaring_list, len(test_nonflaring_list))
    elif (CONSTANTS.TEST_SAMPLING_STRATEGY == 'Undersampling'):
        test_nonflaring_list = undersample(test_nonflaring_list, len(test_flaring_list))
    print 'osampled tr flaring size: ' + str(len(tr_flaring_list))
    print 'osampled tr nflaring size: ' + str(len(tr_nonflaring_list))
    print 'osampled test flaring size: ' + str(len(test_flaring_list))
    print 'osampled test nflaring size: ' + str(len(test_nonflaring_list))
    training_f = create_dataframe_map(tr_flaring_list)
    training_nf = create_dataframe_map(tr_nonflaring_list)
    testing_f = create_dataframe_map(test_flaring_list)
    testing_nf = create_dataframe_map(test_nonflaring_list)
    DSC.serialize_dataset(training_f, training_nf, testing_f, testing_nf)

def oversample(sample_list, desired_count):
    oversampled = []
    oversampled.extend(sample_list)
    s_count = len(sample_list)
    while s_count < desired_count:
        s_index = random.randint(0, len(sample_list) - 1)
        _sample = sample_list[s_index]
        oversampled.append(_sample)
        s_count = s_count + 1
    return oversampled

def undersample(sample_list, desired_count):
    undersampled = copy.deepcopy(sample_list)
    random.shuffle(undersampled)
    return undersampled[:desired_count]
    
def create_sample_lists_of_month(_months):
    flaring_list = []
    nonflaring_list = [] 
    
    f_total_count = 0
    f_valid_count = 0
    
    nf_total_count = 0
    nf_valid_count = 0
    
    
    for month_year in _months:
        month = month_year[0:3]
        year = month_year[3:]
        month_dir_path = os.path.join(CONSTANTS.ROOT_DIR, str(year), str(month))
        for file in os.listdir(month_dir_path):
            full_file_path = os.path.join(month_dir_path, file)
            if isFlaring(file):
                f_total_count = f_total_count + 1
                if sampleValid(full_file_path):
                    f_valid_count = f_valid_count + 1
                    flaring_list.append(full_file_path)
                else:
                    print file
            else:
                nf_total_count = nf_total_count + 1
                if sampleValid(full_file_path):
                    nf_valid_count = nf_valid_count + 1
                    nonflaring_list.append(full_file_path)
    
    
    
    print(f_valid_count, f_total_count)
    print(nf_valid_count, nf_total_count)
    return flaring_list, nonflaring_list

def isFlaring(filename):
    return "_flare_" in filename

def create_dataframe_map(path_list):
    data = {}
    unique_index = 1
    for file_path in path_list:
        df = create_dataframe_from_path(file_path)
        data[str(unique_index)+':'+file_path] = df
        unique_index += 1
    
    return data
    

def create_dataframe_from_path(absolute_csv_path):
    df= pd.read_csv(absolute_csv_path, index_col='DATE__OBS')
    return df 

def sampleValid(file_path):
    sample_df = create_dataframe_from_path(file_path)
    percent_df = percentage_missing(sample_df)
    
    if percent_df.sum().sum() != 0:
        if any( percent_df.sum() > 0 ):
            log_list_.append( [percent_df.sum()[percent_df.sum() > 10], file_path] )
#             print percent_df.sum()[percent_df.sum() > 10], file_path 
        return False
    else:
        return True
#         print(file_path, percent_df.sum().sum())
   
    
def percentage_missing(df):
    """this function will return the percentage of missing values in a DataFrame (per column)"""
    if isinstance(df,pd.DataFrame):
        adict={} #map with keys as columns names and values as percentage of missing values in the columns
        for col in df.columns:
            adict[col]=(np.count_nonzero(df[col].isnull())*100)/len(df[col])
        return pd.DataFrame(adict,index=['percentage'],columns=adict.keys())
    else:
        raise TypeError("can only be used with pandas dataframe")

def write_missing_log(log_list):
    print "I am WRITING NOW"
    with open("log.csv", "wb") as f:
        writer = csv.writer(f)
        writer.writerows(log_list)

    
