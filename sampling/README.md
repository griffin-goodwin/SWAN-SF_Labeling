# Sampling, Serialization, and Deserialization

This part of the project samples the data based on a given strategy. It does the following:
(1) It applies random stratified sampling to monthly separated AR samples. 
(2) It samples months based on a given sampling ratio.
(3) After separating testing and training datasets, it balances the datasets as much as possible.
(4) It serializes the flaring and non-flaring active region samples as python pickles (of pandas.DataFrame)
(5) It also has a script for deserialization of the given pickle.

## Configuration

The input and output parameters are given in mock configuration file sampling.constants.py. These include:
(1) ROOT_DIR : Directory where original samples are located (absolute path)
(2) OUTPUT_DIR : Directory where sampled AR data will be located as serialized objects
(3) SELECTED_YEARS : The yearly data that we will select for experiments
(4) TRAINING_RATIO | TESTING_RATIO (testing currently not used)  : Represents the ratio of months that we will include in testing and training 
(5) MAX_FLARING_RATIO_IN_TRAINING: Max Ratio of AR samples in training dataset 
(6) MIN_FLARING_RATIO_IN_TRAINING: Min Ratio of AR samples in training dataset
(7) TRAIN_SAMPLING_STRATEGY: Sampling strategy for training samples
(7) TESTING_SAMPLING_STRATEGY: Sampling strategy for testing samples


## Requirements
Use Anaconda Python 2.7 and it should work.

## How to Run Sampling
To craete a sample, give the necessary input in sampling_constants.py file and run the sampling driver.

```
python sampling_driver.py
```
This will create a serialized dataset in the OUTPUT_DIR (in sampling constants). Directory will be tagged with the current timestamp.
It will also include a metadata file, which shows the original AR sample paths and their corresponding instances.


## How to Deserialize

The deserialization is handled in deserializer.py script. It is utterly simple. 
You need to change the ''data_dir'' argument in that script and point it to your sample directory.
Your directory structure must include four folders: 

```
> ls 
metadata.dat  test_f  test_nf  training_f  training_nf

```
The function read_samples_to_map will read the samples to a map, where keys are the filenames. 
The map values will be DataFrame objects (indexed on DATE__OBS field). 
