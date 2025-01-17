import os
import random
import sampling_constants as CONSTANTS

def count_training_samples(flaring_counts, training_months):
    return sum([ flaring_counts[tr_months] for tr_months in training_months ])

def randomly_sample_months(months_list, SAMPLING_RATIO=CONSTANTS.TRAINING_RATIO):
    training_months = set()
    number_of_months = len(months_list)
    while len(training_months) < ( number_of_months * SAMPLING_RATIO):
        random_month_index = random.randint(0, number_of_months - 1)
        training_months.add(months_list[random_month_index])
    return training_months


def create_random_training_months(flaring_counts):
    training_months = set() # total_nonflaring = sum(nonflaring_counts.values())
    months_list = flaring_counts.keys()
    total_flaring = sum(flaring_counts.values())
    
    max_total_flaring = int(total_flaring * CONSTANTS.MAX_FLARING_RATIO_IN_TRAINING)
    min_total_flaring = int(total_flaring * CONSTANTS.MIN_FLARING_RATIO_IN_TRAINING)
    training_flaring_count = -1
    while not (training_flaring_count < max_total_flaring and training_flaring_count > min_total_flaring):
        training_months = randomly_sample_months(months_list, CONSTANTS.TRAINING_RATIO)
        training_flaring_count = count_training_samples(flaring_counts, training_months)
    
#     print("Training flaring count: " + str(training_flaring_count) )
    return training_months


def create_training_testing(ROOT_DIR):
    directories = sorted(os.listdir(ROOT_DIR))
    training_set = []
    flaring_counts = {}
    nonflaring_counts = {}
    
    testing_set = []
    testing_counts = {}
    
    countF = 0
    countN = 0
    
    
    for year in CONSTANTS.SELECTED_YEARS:
        dir_path = os.path.join(ROOT_DIR,year)
        yearly_directories = os.listdir(dir_path)
    
        for month in CONSTANTS.MONTHS_SORTED:
            if(month not in yearly_directories):
                continue
            
            month_dir_path = os.path.join(dir_path,month)
            for file in os.listdir(month_dir_path):
                if "_flare_" in file:
                    countF = countF + 1
                else:
                    countN = countN + 1
            
            flaring_counts[month+year] = countF
            nonflaring_counts[month+year] = countN
            
            ratioF = countF / float(countF+countN)
            ratioN = countN / float(countF+countN)

#             print("" + month + " " + year + "\t" + str(countF) + 
#                   ' (' + "{:4.2f}".format(ratioF) +')\t' + str(countN) + ' (' + 
#                   "{:4.2f}".format(ratioN) +')')
            
            countF = 0
            countN = 0
        
#     print(flaring_counts)
#     print(nonflaring_counts)
    
    number_of_months = len(flaring_counts)
    training_months = create_random_training_months(flaring_counts)
    all_months = flaring_counts.keys()
    testing_months = set(all_months).difference(training_months)
    return (training_months, testing_months, flaring_counts, nonflaring_counts)
    


        