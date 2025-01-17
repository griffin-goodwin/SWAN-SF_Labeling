import os
from datetime import datetime
import sampling_constants as CONSTANTS



def serialize_map(training_f, map_output_dir):
    if not os.path.exists(map_output_dir):
        os.makedirs(map_output_dir)
    for key in training_f.iterkeys():
        df_val = training_f[key]
        file_path = os.path.join(map_output_dir, key.split(':')[0])
        df_val.to_pickle(file_path)
    

def serialize_dataset(training_f, training_nf, testing_f, testing_nf):
    if not os.path.exists(CONSTANTS.OUTPUT_DIR):
        os.makedirs(CONSTANTS.OUTPUT_DIR)
    
    output_dir = os.path.join(CONSTANTS.OUTPUT_DIR, 'T'.join(str(datetime.now())[:19].split()) )
    print(output_dir)
    os.makedirs(output_dir)
    
    with open(output_dir + "/metadata.dat","a+") as f:
        for item in training_f.iterkeys():
            f.write("TRAINING-F  %s\n" % item)
        for item in training_nf.iterkeys():
            f.write("TRAINING-NF %s\n" % item)
        for item in testing_f.iterkeys():
            f.write("TESTING-F %s\n" % item)
        for item in testing_nf.iterkeys():
            f.write("TESTING-NF %s\n" % item)
    
    
    training_f_path = os.path.join(output_dir, 'training_f')
    serialize_map(training_f, training_f_path)
    
    training_nf_path = os.path.join(output_dir, 'training_nf')
    serialize_map(training_nf, training_nf_path)
    
    testing_f_path = os.path.join(output_dir, 'test_f')
    serialize_map(testing_f, testing_f_path)
    
    testing_nf_path = os.path.join(output_dir, 'test_nf')
    serialize_map(testing_nf, testing_nf_path)

    