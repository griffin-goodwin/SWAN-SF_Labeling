###GLOBAL VARIABLES
ROOT_DIR = '/home/berkay/workspace/flareprediction2017/training-data/'
OUTPUT_DIR = '/home/berkay/workspace/flareprediction2017/output-dir'


# SELECTED_YEARS = ['2010','2011','2012','2013','2014','2015','2016', '2017']
SELECTED_YEARS = ['2016','2017']
TRAINING_RATIO = 0.67
TESTING_RATIO = 0.33
MAX_FLARING_RATIO_IN_TRAINING = 0.75
MIN_FLARING_RATIO_IN_TRAINING = 0.60
MONTHS_SORTED = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

TRAIN_SAMPLING_STRATEGY = 'Undersampling' #'Oversampling'
TEST_SAMPLING_STRATEGY = 'Undersampling' #'Oversampling'
