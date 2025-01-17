import os
import pandas as pd

def read_samples_to_map(dir_path):
    data = {}
    
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        df = read_sample(file_path)
        data[file] = df
        
    return data

def read_sample(path):
    return pd.read_pickle(path)


def write_sample_to_csv(path):
    sample = read_sample(path)
    csv_sample_path = path + '.csv'
    sample.to_csv(csv_sample_path, sep='\t')
    
def write_samples_to_csv(dir_path):
    
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        print(file_path)
        try:
            df = read_sample(file_path)
        except KeyError, e:
            print("There is a key error when reading pickles. Filename: " + file_path )
        except:
            print("There is another error when reading pickles..")
            
        write_sample_to_csv(file_path)
        


# sample_path = '/home/baydin2/workspace/flareprediction2017/output-dir-UNDER/all/2017-09-28T14:44:09/test_f/1'
# write_sample_to_csv(sample_path)

# dir_path_csv = '/home/baydin2/workspace/flareprediction2017/output-dir-UNDER/all/2017-09-28T14:44:09/test_f/'
# write_samples_to_csv(dir_path_csv)


# 
# data_dir = '/home/baydin2/workspace/flareprediction2017/output-dir/2017-09-28T12:30:23/'
# 
# test_f_dir = os.path.join(data_dir, 'test_f')
# test_nf_dir = os.path.join(data_dir, 'test_nf')
# training_f_dir = os.path.join(data_dir, 'training_f')
# training_nf_dir = os.path.join(data_dir, 'training_nf')
# 
# training_f = read_samples_to_map(training_f_dir)
# training_nf = read_samples_to_map(training_nf_dir)
# testing_f = read_samples_to_map(test_f_dir)
# testing_nf = read_samples_to_map(test_nf_dir)




    
