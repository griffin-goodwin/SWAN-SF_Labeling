import random
import shutil
from os import listdir, makedirs
from os.path import isfile, isdir, join

climaRatios = {'FL': 0.14, 'NF': 0.86}

instances_dir_path = './test/instances_O12.0L0.0P24.0/'
undersampled_ = './test/CLUS/'
OBS_LIMIT = 70  # degrees
K = 5
random.seed(13)


def initialize():
    d = instances_dir_path
    for partition_path in [join(d, o) for o in listdir(d) if isdir(join(d, o))]:
        undersample_partition(partition_path)
        # break


def undersample_partition(partition_path):
    subfolder = partition_path.split('/')[-1]
    print('STATS for ', subfolder)

    fli_list = list_mvts_files(join(partition_path, 'FL'))
    get_fl_stats(fli_list)
    count_fl = len(fli_list)
    fli_list = [join(partition_path, 'FL', ifile) for ifile in fli_list]

    desired_nf_count = int(count_fl * (climaRatios['NF'] / climaRatios['FL'])) + 1
    nfi_files = list_mvts_files(join(partition_path, 'NF'))
    print_original_nf_stats(nfi_files)
    random.shuffle(nfi_files)
    us_nfi_list = nfi_files[0:desired_nf_count]
    get_nf_stats(us_nfi_list)
    us_nfi_list = [join(partition_path, 'NF', ifile) for ifile in us_nfi_list]

    # print(us_nfi_list[0:5])

    copy_files(us_nfi_list, join(undersampled_, subfolder, 'NF'))
    copy_files(fli_list, join(undersampled_, subfolder, 'FL'))


def get_fl_stats(fli_list):
    icountM = 0
    icountX = 0
    for ifile in fli_list:
        if ifile.startswith('M'):
            icountM += 1
        elif ifile.startswith('X'):
            icountX += 1
    print('Number of X class instances in undersampled:', icountX)
    print('Number of M class instances in undersampled:', icountM)


def get_nf_stats(fli_list):
    icountC = 0
    icountB = 0
    icountN = 0
    for ifile in fli_list:
        if ifile.startswith('C'):
            icountC += 1
        elif ifile.startswith('B'):
            icountB += 1
        elif ifile.startswith('N'):
            icountN += 1
    print('Number of C class instances in undersampled:', icountC)
    print('Number of B class instances in undersampled:', icountB)
    print('Number of flare-quiet class instances in undersampled:', icountN)


def print_original_nf_stats(nfi_files):
    C = 0
    B = 0
    FQ = 0
    for i in nfi_files:
        if i.startswith('C'):
            C = C + 1
        if i.startswith('B'):
            B = B + 1
        if i.startswith('N'):
            FQ = FQ + 1

    print('Original C instances: ', C, ' B instances:', B, ' FL Quiet:', FQ)


def copy_files(source_path_list, out_folder):
    create_folder(out_folder)

    print(out_folder)
    for ifile in source_path_list:
        shutil.copy2(ifile, out_folder)


def get_instance_count(path):
    return len(list_mvts_files(path))


def list_mvts_files(ar_mvts_path):
    """Gets the files in the ar_mvts_path (active region multivariate time series) and returns the list of mvts file
    names """
    return [f for f in listdir(ar_mvts_path) if isfile(join(ar_mvts_path, f))]


def create_folder(_path):
    try:
        makedirs(_path)
        print('Folder created', _path)
    except OSError:
        if (not isdir(_path)):
            raise


if __name__ == "__main__":
    initialize()
